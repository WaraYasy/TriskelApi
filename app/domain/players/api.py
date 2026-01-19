"""
API REST para Players

Endpoints de FastAPI para gestionar jugadores.
Usa Dependency Injection para desacoplar de implementaciones concretas.

Reglas de acceso:
- POST /v1/players: Público (crear cuenta)
- GET /v1/players/me: Jugador autenticado (ver mi perfil)
- GET /v1/players: Solo API Key (listar todos - admin)
- GET /v1/players/{id}: Solo si es tu ID o con API Key
- PATCH /v1/players/{id}: Solo si es tu ID o con API Key
- DELETE /v1/players/{id}: Solo si es tu ID o con API Key
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request

from app.domain.games.adapters.firestore_repository import FirestoreGameRepository
from app.domain.games.ports import IGameRepository

from .adapters.firestore_repository import FirestorePlayerRepository
from .models import Player
from .ports import IPlayerRepository
from .schemas import PlayerAuthResponse, PlayerCreate, PlayerLoginRequest, PlayerLoginResponse, PlayerUpdate
from .service import PlayerService

# Router de FastAPI
router = APIRouter(prefix="/v1/players", tags=["Players"])


# ==================== HELPERS ====================


def check_player_access(request: Request, target_player_id: str) -> None:
    """
    Verifica que el usuario tenga permisos para acceder al jugador especificado.

    Reglas:
    - Admin (API Key): puede acceder a cualquier jugador
    - Jugador autenticado: solo puede acceder a su propio ID

    Args:
        request: Request de FastAPI con estado de autenticación
        target_player_id: ID del jugador al que se quiere acceder

    Raises:
        HTTPException 403: Si no tiene permisos
    """
    is_admin = getattr(request.state, "is_admin", False)
    authenticated_player_id = getattr(request.state, "player_id", None)

    # Admin puede acceder a cualquier jugador
    if is_admin:
        return

    # Jugador solo puede acceder a su propio ID
    if authenticated_player_id != target_player_id:
        raise HTTPException(
            status_code=403, detail="No tienes permisos para acceder a este jugador"
        )


# ==================== DEPENDENCY INJECTION ====================


def get_player_repository() -> IPlayerRepository:
    """
    Dependency que provee el repositorio de Players.

    Retorna la implementación concreta (Firestore).
    Si queremos cambiar a otra BD, solo cambiamos esto.

    Returns:
        IPlayerRepository: Implementación del repositorio
    """
    return FirestorePlayerRepository()


def get_player_service(
    repository: IPlayerRepository = Depends(get_player_repository),
) -> PlayerService:
    """
    Dependency que provee el servicio de Players.

    Recibe el repository por inyección automática.

    Args:
        repository: Repositorio inyectado por FastAPI

    Returns:
        PlayerService: Servicio configurado
    """
    return PlayerService(repository=repository)


def get_game_repository() -> IGameRepository:
    """
    Dependency que provee el repositorio de Games.

    Returns:
        IGameRepository: Implementación del repositorio
    """
    return FirestoreGameRepository()


# ==================== ENDPOINTS ====================


@router.post("", response_model=PlayerAuthResponse, status_code=201)
def create_player(player_data: PlayerCreate, service: PlayerService = Depends(get_player_service)):
    """
    Crear un nuevo jugador.

    Devuelve player_id y player_token que el juego debe guardar.
    El token se envía en futuras peticiones para autenticación.

    Args:
        player_data: Datos del jugador (username, email)
        service: Servicio inyectado automáticamente

    Returns:
        PlayerAuthResponse: ID, username y token del jugador

    Raises:
        HTTPException 400: Si el username ya existe
    """
    try:
        player = service.create_player(player_data)

        # Retornar solo los datos necesarios para autenticación
        return PlayerAuthResponse(
            player_id=player.player_id,
            username=player.username,
            player_token=player.player_token,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=PlayerLoginResponse)
def login_player(
    login_data: PlayerLoginRequest,
    service: PlayerService = Depends(get_player_service),
    game_repo: IGameRepository = Depends(get_game_repository),
):
    """
    Login o registro idempotente.

    Si el username existe, devuelve las credenciales existentes.
    Si no existe, crea un nuevo jugador.
    También devuelve la partida activa si existe.

    Args:
        login_data: Datos de login (username, email opcional)
        service: Servicio de jugadores inyectado
        game_repo: Repositorio de games inyectado

    Returns:
        PlayerLoginResponse: Credenciales y partida activa si existe
    """
    player, is_new = service.login_or_create(login_data.username, login_data.email)

    # Buscar partida activa
    active_game = game_repo.get_active_game(player.player_id)

    return PlayerLoginResponse(
        player_id=player.player_id,
        username=player.username,
        player_token=player.player_token,
        active_game_id=active_game.game_id if active_game else None,
        is_new_player=is_new,
    )


@router.get(
    "/me",
    response_model=Player,
    responses={
        200: {"description": "Perfil del jugador autenticado"},
        401: {"description": "No autenticado - requiere X-Player-ID y X-Player-Token"},
    },
    summary="Ver mi perfil",
    dependencies=[],
)
def get_my_profile(request: Request):
    """
    Obtener mi propio perfil (jugador autenticado).

    **Requiere autenticación:** X-Player-ID + X-Player-Token

    El middleware ya validó la autenticación y obtuvo el player.
    Simplemente devolvemos el player que ya está en memoria.

    Args:
        request: Request de FastAPI (contiene player del middleware)

    Returns:
        Player: Datos completos del jugador autenticado
    """
    # El middleware ya validó auth y obtuvo el player
    # No necesitamos hacer otra consulta a la BD
    return request.state.player


@router.get("/{player_id}", response_model=Player)
def get_player(
    player_id: str,
    request: Request,
    service: PlayerService = Depends(get_player_service),
):
    """
    Obtener un jugador por ID.

    Solo puedes ver tu propio perfil, a menos que uses API Key (admin).

    Args:
        player_id: ID único del jugador
        request: Request de FastAPI
        service: Servicio inyectado

    Returns:
        Player: Datos completos del jugador

    Raises:
        HTTPException 403: Si intentas ver el perfil de otro jugador
        HTTPException 404: Si el jugador no existe
    """
    # Verificar permisos (admin o propio jugador)
    check_player_access(request, player_id)

    player = service.get_player(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    return player


@router.get("", response_model=List[Player])
def get_all_players(
    request: Request,
    limit: int = 100,
    service: PlayerService = Depends(get_player_service),
):
    """
    Listar todos los jugadores.

    SOLO ADMIN: Requiere API Key (X-API-Key).

    Args:
        request: Request de FastAPI
        limit: Máximo número de jugadores a retornar (default: 100)
        service: Servicio inyectado

    Returns:
        List[Player]: Lista de jugadores

    Raises:
        HTTPException 403: Si no eres admin
    """
    # Solo admin puede listar todos los jugadores
    is_admin = getattr(request.state, "is_admin", False)

    if not is_admin:
        raise HTTPException(
            status_code=403,
            detail="Este endpoint solo está disponible para administradores (requiere X-API-Key)",
        )

    return service.get_all_players(limit=limit)


@router.patch("/{player_id}", response_model=Player)
def update_player(
    player_id: str,
    player_update: PlayerUpdate,
    request: Request,
    service: PlayerService = Depends(get_player_service),
):
    """
    Actualizar un jugador.

    Solo puedes actualizar tu propio perfil, a menos que uses API Key (admin).
    Solo se actualizan los campos enviados (parcial).

    Args:
        player_id: ID del jugador
        player_update: Campos a actualizar
        request: Request de FastAPI
        service: Servicio inyectado

    Returns:
        Player: Jugador actualizado

    Raises:
        HTTPException 403: Si intentas actualizar otro jugador
        HTTPException 404: Si el jugador no existe
    """
    # Verificar permisos (admin o propio jugador)
    check_player_access(request, player_id)

    player = service.update_player(player_id, player_update)
    if not player:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    return player


@router.delete("/{player_id}")
def delete_player(
    player_id: str,
    request: Request,
    service: PlayerService = Depends(get_player_service),
):
    """
    Eliminar un jugador.

    Solo puedes eliminar tu propia cuenta, a menos que uses API Key (admin).

    Args:
        player_id: ID del jugador
        request: Request de FastAPI
        service: Servicio inyectado

    Returns:
        dict: Mensaje de confirmación

    Raises:
        HTTPException 403: Si intentas eliminar otro jugador
        HTTPException 404: Si el jugador no existe
    """
    # Verificar permisos (admin o propio jugador)
    check_player_access(request, player_id)

    deleted = service.delete_player(player_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    return {"message": "Jugador eliminado correctamente"}
