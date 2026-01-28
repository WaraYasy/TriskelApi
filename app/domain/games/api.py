"""API REST para Games.

Endpoints de FastAPI para gestionar partidas.

Reglas de acceso:
- POST /v1/games: Jugador autenticado (crear partida propia).
- GET /v1/games/{id}: Solo si es tu partida o con API Key.
- GET /v1/games/player/{player_id}: Solo si es tu ID o con API Key.
- PATCH /v1/games/{id}: Solo si es tu partida o con API Key.
- POST /v1/games/{id}/level/*: Solo si es tu partida o con API Key.
- DELETE /v1/games/{id}: Solo si es tu partida o con API Key.

Autor: Mandrágora
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request

from ..players.adapters.firestore_repository import FirestorePlayerRepository

# Importar dependencies de Players (Games depende de Players)
from ..players.ports import IPlayerRepository
from ..players.service import PlayerService
from .adapters.firestore_repository import FirestoreGameRepository
from .models import Game
from .ports import IGameRepository
from .schemas import GameCreate, GameUpdate, LevelComplete, LevelStart
from .service import GameService

# Router de FastAPI
router = APIRouter(prefix="/v1/games", tags=["Games"])


# ==================== HELPERS ====================


def check_game_access(request: Request, game: Game, service: GameService) -> None:
    """Verifica que el usuario tenga permisos para acceder a la partida especificada.

    Reglas:
    - Admin (API Key): puede acceder a cualquier partida.
    - Jugador autenticado: solo puede acceder a sus propias partidas.

    Args:
        request (Request): Request de FastAPI con estado de autenticación.
        game (Game): Partida a la que se quiere acceder.
        service (GameService): Servicio de games (no usado pero mantenido para consistencia).

    Raises:
        HTTPException: Si no tiene permisos (403).
    """
    is_admin = getattr(request.state, "is_admin", False)
    authenticated_player_id = getattr(request.state, "player_id", None)

    # Admin puede acceder a cualquier partida
    if is_admin:
        return

    # Jugador solo puede acceder a sus propias partidas
    if game.player_id != authenticated_player_id:
        raise HTTPException(
            status_code=403, detail="No tienes permisos para acceder a esta partida"
        )


def check_player_games_access(request: Request, target_player_id: str) -> None:
    """Verifica que el usuario tenga permisos para ver las partidas de un jugador.

    Reglas:
    - Admin (API Key): puede ver partidas de cualquier jugador.
    - Jugador autenticado: solo puede ver sus propias partidas.

    Args:
        request (Request): Request de FastAPI con estado de autenticación.
        target_player_id (str): ID del jugador cuyas partidas se quieren ver.

    Raises:
        HTTPException: Si no tiene permisos (403).
    """
    is_admin = getattr(request.state, "is_admin", False)
    authenticated_player_id = getattr(request.state, "player_id", None)

    # Admin puede ver partidas de cualquier jugador
    if is_admin:
        return

    # Jugador solo puede ver sus propias partidas
    if authenticated_player_id != target_player_id:
        raise HTTPException(
            status_code=403,
            detail="No tienes permisos para ver las partidas de este jugador",
        )


# ==================== DEPENDENCY INJECTION ====================


def get_game_repository() -> IGameRepository:
    """Dependency que provee el repositorio de Games.

    Returns:
        IGameRepository: Repositorio instanciado.
    """
    return FirestoreGameRepository()


def get_player_repository() -> IPlayerRepository:
    """Dependency que provee el repositorio de Players.

    Returns:
        IPlayerRepository: Repositorio instanciado.
    """
    return FirestorePlayerRepository()


def get_player_service(
    player_repository: IPlayerRepository = Depends(get_player_repository),
) -> PlayerService:
    """Dependency que provee el servicio de Players.

    Args:
        player_repository (IPlayerRepository): Repositorio inyectado.

    Returns:
        PlayerService: Servicio instanciado.
    """
    return PlayerService(repository=player_repository)


def get_game_service(
    game_repository: IGameRepository = Depends(get_game_repository),
    player_repository: IPlayerRepository = Depends(get_player_repository),
    player_service: PlayerService = Depends(get_player_service),
) -> GameService:
    """Dependency que provee el servicio de Games.

    Games depende de Players para:
    - Verificar que el jugador existe al crear partida.
    - Actualizar stats del jugador al terminar partida.

    Args:
        game_repository (IGameRepository): Repositorio de juegos.
        player_repository (IPlayerRepository): Repositorio de jugadores.
        player_service (PlayerService): Servicio de jugadores.

    Returns:
        GameService: Servicio instanciado.
    """
    return GameService(
        game_repository=game_repository,
        player_repository=player_repository,
        player_service=player_service,
    )


# ==================== ENDPOINTS ====================


@router.post("", response_model=Game, status_code=201)
def create_game(
    game_data: GameCreate,
    request: Request,
    service: GameService = Depends(get_game_service),
):
    """Iniciar una nueva partida.

    Reglas:
    - El jugador debe existir.
    - No puede tener otra partida activa.
    - Solo puedes crear partidas para ti mismo (a menos que seas admin).

    Args:
        game_data (GameCreate): Datos de la partida (player_id opcional, se usa el autenticado).
        request (Request): Request de FastAPI.
        service (GameService): Servicio inyectado.

    Returns:
        Game: Partida creada.

    Raises:
        HTTPException: Si intentas crear partida para otro jugador (403).
        HTTPException: Si el jugador no existe (404).
        HTTPException: Si ya tiene partida activa (409).
    """
    is_admin = getattr(request.state, "is_admin", False)
    authenticated_player_id = getattr(request.state, "player_id", None)

    # Si no se envía player_id, usar el del jugador autenticado
    if game_data.player_id is None:
        game_data.player_id = authenticated_player_id

    # Verificar que el jugador autenticado puede crear partida para este player_id
    if not is_admin and game_data.player_id != authenticated_player_id:
        raise HTTPException(status_code=403, detail="Solo puedes crear partidas para ti mismo")

    try:
        return service.create_game(game_data)
    except ValueError as e:
        # Distinguir tipo de error
        if "no encontrado" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        else:
            raise HTTPException(status_code=409, detail=str(e))


@router.get("", response_model=List[Game])
def get_all_games(
    request: Request,
    limit: int = 1000,
    service: GameService = Depends(get_game_service),
):
    """Obtener todas las partidas de todos los jugadores (ADMIN ONLY).

    Este endpoint está diseñado para analytics y herramientas de administración.
    Requiere autenticación admin (JWT con rol admin o API Key).

    Args:
        request (Request): Request de FastAPI.
        limit (int): Máximo número de partidas a retornar (default: 1000).
        service (GameService): Servicio inyectado.

    Returns:
        List[Game]: Lista de todas las partidas.

    Raises:
        HTTPException: Si no tiene permisos de admin (403).
    """
    # Verificar que es admin
    is_admin = getattr(request.state, "is_admin", False)

    if not is_admin:
        raise HTTPException(
            status_code=403,
            detail="Este endpoint requiere permisos de administrador. Usa API Key o JWT token de admin.",
        )

    return service.get_all_games(limit=limit)


@router.get("/{game_id}", response_model=Game)
def get_game(game_id: str, request: Request, service: GameService = Depends(get_game_service)):
    """Obtener una partida por ID.

    Solo puedes ver tus propias partidas, a menos que uses API Key (admin).

    Args:
        game_id (str): ID de la partida.
        request (Request): Request de FastAPI.
        service (GameService): Servicio inyectado.

    Returns:
        Game: Partida completa.

    Raises:
        HTTPException: Si intentas ver la partida de otro jugador (403).
        HTTPException: Si la partida no existe (404).
    """
    game = service.get_game(game_id)

    if not game:
        raise HTTPException(status_code=404, detail="Partida no encontrada")

    # Verificar permisos (admin o propia partida)
    check_game_access(request, game, service)

    return game


@router.get("/player/{player_id}", response_model=List[Game])
def get_player_games(
    player_id: str,
    request: Request,
    limit: int = 100,
    service: GameService = Depends(get_game_service),
):
    """Obtener todas las partidas de un jugador.

    Solo puedes ver tus propias partidas, a menos que uses API Key (admin).

    Args:
        player_id (str): ID del jugador.
        request (Request): Request de FastAPI.
        limit (int): Máximo número de partidas a retornar.
        service (GameService): Servicio inyectado.

    Returns:
        List[Game]: Lista de partidas.

    Raises:
        HTTPException: Si intentas ver partidas de otro jugador (403).
    """
    # Verificar permisos (admin o propio jugador)
    check_player_games_access(request, player_id)

    return service.get_player_games(player_id, limit=limit)


@router.patch("/{game_id}", response_model=Game)
def update_game(
    game_id: str,
    game_update: GameUpdate,
    request: Request,
    service: GameService = Depends(get_game_service),
):
    """Actualizar una partida.

    Solo puedes actualizar tus propias partidas, a menos que uses API Key (admin).

    Args:
        game_id (str): ID de la partida.
        game_update (GameUpdate): Campos a actualizar.
        request (Request): Request de FastAPI.
        service (GameService): Servicio inyectado.

    Returns:
        Game: Partida actualizada.

    Raises:
        HTTPException: Si intentas actualizar la partida de otro jugador (403).
        HTTPException: Si la partida no existe (404).
    """
    # Primero obtener la partida para verificar permisos
    game = service.get_game(game_id)

    if not game:
        raise HTTPException(status_code=404, detail="Partida no encontrada")

    # Verificar permisos (admin o propia partida)
    check_game_access(request, game, service)

    # Proceder con la actualización
    updated_game = service.update_game(game_id, game_update)

    return updated_game


@router.post("/{game_id}/level/start", response_model=Game)
def start_level(
    game_id: str,
    level_data: LevelStart,
    request: Request,
    service: GameService = Depends(get_game_service),
):
    """Registrar inicio de un nivel.

    Solo puedes iniciar niveles en tus propias partidas, a menos que uses API Key (admin).

    Args:
        game_id (str): ID de la partida.
        level_data (LevelStart): Datos del nivel a iniciar.
        request (Request): Request de FastAPI.
        service (GameService): Servicio inyectado.

    Returns:
        Game: Partida actualizada.

    Raises:
        HTTPException: Si intentas modificar la partida de otro jugador (403).
        HTTPException: Si la partida no existe (404).
        HTTPException: Si la partida no está activa (400).
    """
    # Primero obtener la partida para verificar permisos
    game = service.get_game(game_id)

    if not game:
        raise HTTPException(status_code=404, detail="Partida no encontrada")

    # Verificar permisos (admin o propia partida)
    check_game_access(request, game, service)

    # Proceder con iniciar el nivel
    try:
        updated_game = service.start_level(game_id, level_data)
        return updated_game
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{game_id}/level/complete", response_model=Game)
def complete_level(
    game_id: str,
    level_data: LevelComplete,
    request: Request,
    service: GameService = Depends(get_game_service),
):
    """Registrar completado de un nivel.

    Solo puedes completar niveles en tus propias partidas, a menos que uses API Key (admin).

    Actualiza:
    - Niveles completados
    - Métricas (tiempo, muertes)
    - Decisión moral (si aplica)
    - Reliquia obtenida (si aplica)
    - Porcentaje de completado

    Args:
        game_id (str): ID de la partida.
        level_data (LevelComplete): Datos del nivel completado.
        request (Request): Request de FastAPI.
        service (GameService): Servicio inyectado.

    Returns:
        Game: Partida actualizada.

    Raises:
        HTTPException: Si intentas modificar la partida de otro jugador (403).
        HTTPException: Si la partida no existe (404).
        HTTPException: Si la partida no está activa (400).
    """
    # Primero obtener la partida para verificar permisos
    game = service.get_game(game_id)

    if not game:
        raise HTTPException(status_code=404, detail="Partida no encontrada")

    # Verificar permisos (admin o propia partida)
    check_game_access(request, game, service)

    # Proceder con completar el nivel
    try:
        updated_game = service.complete_level(game_id, level_data)
        return updated_game
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{game_id}/complete", response_model=Game)
def complete_game(
    game_id: str,
    request: Request,
    service: GameService = Depends(get_game_service),
):
    """Finalizar una partida (marcarla como completada).

    Solo puedes finalizar tus propias partidas, a menos que uses API Key (admin).

    Args:
        game_id (str): ID de la partida.
        request (Request): Request de FastAPI.
        service (GameService): Servicio inyectado.

    Returns:
        Game: Partida actualizada con status="completed".

    Raises:
        HTTPException: Si intentas finalizar la partida de otro jugador (403).
        HTTPException: Si la partida no existe (404).
    """
    game = service.get_game(game_id)

    if not game:
        raise HTTPException(status_code=404, detail="Partida no encontrada")

    check_game_access(request, game, service)

    updated_game = service.finish_game(game_id, completed=True)
    return updated_game


@router.delete("/{game_id}")
def delete_game(game_id: str, request: Request, service: GameService = Depends(get_game_service)):
    """Eliminar una partida.

    Solo puedes eliminar tus propias partidas, a menos que uses API Key (admin).

    Args:
        game_id (str): ID de la partida.
        request (Request): Request de FastAPI.
        service (GameService): Servicio inyectado.

    Returns:
        dict: Mensaje de confirmación.

    Raises:
        HTTPException: Si intentas eliminar la partida de otro jugador (403).
        HTTPException: Si la partida no existe (404).
    """
    # Primero obtener la partida para verificar permisos
    game = service.get_game(game_id)

    if not game:
        raise HTTPException(status_code=404, detail="Partida no encontrada")

    # Verificar permisos (admin o propia partida)
    check_game_access(request, game, service)

    # Proceder con la eliminación
    service.delete_game(game_id)

    return {"message": "Partida eliminada correctamente"}
