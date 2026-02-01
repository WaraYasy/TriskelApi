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

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.middleware.rate_limit import GAME_CREATE_LIMIT, limiter

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
@limiter.limit(GAME_CREATE_LIMIT)
def create_game(
    request: Request,
    game_data: GameCreate,
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
    limit: int = Query(default=100, ge=1, le=500, description="Máximo de partidas a retornar"),
    days: Optional[int] = Query(
        default=None, ge=1, le=90, description="Filtrar últimos N días (máx 90)"
    ),
    since: Optional[str] = Query(
        default=None, description="Filtrar desde fecha ISO (ej: 2026-01-25)"
    ),
    until: Optional[str] = Query(default=None, description="Filtrar hasta fecha ISO"),
    service: GameService = Depends(get_game_service),
):
    """Obtener todas las partidas de todos los jugadores (ADMIN ONLY).

    Este endpoint está diseñado para analytics y herramientas de administración.
    Requiere autenticación admin (JWT con rol admin o API Key).

    OPTIMIZACIÓN: Límite reducido de 1000 → 100 por defecto (máx 500).
    Se recomienda usar filtros de fecha para reducir costos de Firestore.

    Examples:
        GET /games?days=7              → Últimos 7 días
        GET /games?days=30&limit=50    → Últimos 30 días, máx 50
        GET /games?since=2026-01-01    → Desde 1 de enero

    Args:
        request (Request): Request de FastAPI.
        limit (int): Máximo número de partidas a retornar (default: 100, máx: 500).
        days (int, optional): Filtrar últimos N días (1-90).
        since (str, optional): Filtrar desde fecha ISO 8601.
        until (str, optional): Filtrar hasta fecha ISO 8601.
        service (GameService): Servicio inyectado.

    Returns:
        List[Game]: Lista de todas las partidas filtradas.

    Raises:
        HTTPException: Si no tiene permisos de admin (403) o formato de fecha inválido (400).
    """
    # Verificar que es admin
    is_admin = getattr(request.state, "is_admin", False)

    if not is_admin:
        raise HTTPException(
            status_code=403,
            detail="Este endpoint requiere permisos de administrador. Usa API Key o JWT token de admin.",
        )

    # Parsear fechas si se proporcionaron
    since_date = None
    until_date = None

    if since:
        try:
            since_date = datetime.fromisoformat(since.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Formato de fecha 'since' inválido. Usa ISO 8601: YYYY-MM-DD o YYYY-MM-DDTHH:MM:SS",
            )

    if until:
        try:
            until_date = datetime.fromisoformat(until.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Formato de fecha 'until' inválido. Usa ISO 8601: YYYY-MM-DD o YYYY-MM-DDTHH:MM:SS",
            )

    return service.get_all_games(limit=limit, days=days, since=since_date, until=until_date)


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
    limit: int = Query(default=50, ge=1, le=200, description="Máximo de partidas a retornar"),
    days: Optional[int] = Query(default=None, ge=1, le=90, description="Filtrar últimos N días"),
    since: Optional[str] = Query(default=None, description="Filtrar desde fecha ISO"),
    until: Optional[str] = Query(default=None, description="Filtrar hasta fecha ISO"),
    service: GameService = Depends(get_game_service),
):
    """Obtener todas las partidas de un jugador con filtros opcionales.

    Solo puedes ver tus propias partidas, a menos que uses API Key (admin).

    Examples:
        GET /games/player/{id}?days=7      → Últimos 7 días
        GET /games/player/{id}?days=30     → Último mes
        GET /games/player/{id}?since=2026-01-01  → Desde enero

    Args:
        player_id (str): ID del jugador.
        request (Request): Request de FastAPI.
        limit (int): Máximo número de partidas a retornar (default: 50, máx: 200).
        days (int, optional): Filtrar últimos N días (1-90).
        since (str, optional): Filtrar desde fecha ISO 8601.
        until (str, optional): Filtrar hasta fecha ISO 8601.
        service (GameService): Servicio inyectado.

    Returns:
        List[Game]: Lista de partidas filtradas.

    Raises:
        HTTPException: Si intentas ver partidas de otro jugador (403) o formato inválido (400).
    """
    # Verificar permisos (admin o propio jugador)
    check_player_games_access(request, player_id)

    # Parsear fechas si se proporcionaron
    since_date = None
    until_date = None

    if since:
        try:
            since_date = datetime.fromisoformat(since.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de fecha 'since' inválido")

    if until:
        try:
            until_date = datetime.fromisoformat(until.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de fecha 'until' inválido")

    return service.get_player_games(
        player_id, limit=limit, days=days, since=since_date, until=until_date
    )


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


@router.get("/count")
def count_games(
    request: Request,
    player_id: Optional[str] = Query(default=None, description="Filtrar por jugador"),
    status: Optional[str] = Query(
        default=None, description="Filtrar por estado (in_progress, completed, abandoned)"
    ),
    days: Optional[int] = Query(default=None, ge=1, le=365, description="Filtrar últimos N días"),
    since: Optional[str] = Query(default=None, description="Filtrar desde fecha ISO"),
    until: Optional[str] = Query(default=None, description="Filtrar hasta fecha ISO"),
    service: GameService = Depends(get_game_service),
):
    """Cuenta partidas de forma eficiente usando Firestore aggregation.

    Este endpoint usa count aggregation de Firestore en lugar de traer
    todos los documentos, lo que lo hace mucho más eficiente y económico.

    REQUIERE API KEY (admin only).

    Examples:
        GET /games/count                    → Total de partidas
        GET /games/count?days=30            → Partidas de últimos 30 días
        GET /games/count?player_id=abc      → Partidas de un jugador
        GET /games/count?status=completed   → Partidas completadas

    Args:
        request (Request): Request de FastAPI.
        player_id (str, optional): Filtrar por jugador.
        status (str, optional): Filtrar por estado.
        days (int, optional): Filtrar últimos N días.
        since (str, optional): Filtrar desde fecha ISO 8601.
        until (str, optional): Filtrar hasta fecha ISO 8601.
        service (GameService): Servicio inyectado.

    Returns:
        JSON: {"count": int, "filters": dict}

    Raises:
        HTTPException: Si no eres admin (403) o formato de fecha inválido (400).
    """
    # Solo admin puede contar partidas globales
    if not getattr(request.state, "is_admin", False):
        raise HTTPException(status_code=403, detail="Requiere permisos de administrador")

    # Parsear fechas si se especificaron
    since_date = None
    until_date = None

    if since:
        try:
            since_date = datetime.fromisoformat(since.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de fecha 'since' inválido")

    if until:
        try:
            until_date = datetime.fromisoformat(until.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de fecha 'until' inválido")

    # Contar partidas con filtros
    count = service.count_games(
        player_id=player_id,
        status=status,
        days=days,
        since=since_date,
        until=until_date,
    )

    # Retornar count con información de filtros aplicados
    return {
        "count": count,
        "filters": {
            "player_id": player_id,
            "status": status,
            "days": days,
            "since": since,
            "until": until,
        },
    }
