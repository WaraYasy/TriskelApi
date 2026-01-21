"""
API REST para Sessions

Endpoints de FastAPI para gestionar sesiones de juego.

Reglas de acceso:
- POST /v1/sessions: Jugador autenticado (iniciar sesion propia)
- PATCH /v1/sessions/{id}/end: Jugador autenticado (terminar sesion propia)
- GET /v1/sessions/player/{id}: Solo tu ID o admin
- GET /v1/sessions/game/{id}: Solo tus partidas o admin
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request

from ..games.adapters.firestore_repository import FirestoreGameRepository
from .models import GameSession
from .repository import SessionRepository
from .schemas import SessionCreate, SessionResponse
from .service import SessionService

# Router de FastAPI
router = APIRouter(prefix="/v1/sessions", tags=["Sessions"])


# ==================== HELPERS ====================


def check_player_access(request: Request, target_player_id: str) -> None:
    """Verifica permisos para acceder a datos de un jugador"""
    is_admin = getattr(request.state, "is_admin", False)
    authenticated_player_id = getattr(request.state, "player_id", None)

    if is_admin:
        return

    if authenticated_player_id != target_player_id:
        raise HTTPException(
            status_code=403,
            detail="No tienes permisos para acceder a las sesiones de este jugador",
        )


def check_game_access(request: Request, game_id: str) -> None:
    """Verifica permisos para acceder a datos de una partida"""
    is_admin = getattr(request.state, "is_admin", False)
    authenticated_player_id = getattr(request.state, "player_id", None)

    if is_admin:
        return

    # Verificar que la partida pertenece al jugador
    game_repo = FirestoreGameRepository()
    game = game_repo.get_by_id(game_id)

    if not game:
        raise HTTPException(status_code=404, detail="Partida no encontrada")

    if game.player_id != authenticated_player_id:
        raise HTTPException(
            status_code=403,
            detail="No tienes permisos para ver sesiones de esta partida",
        )


def session_to_response(session: GameSession) -> SessionResponse:
    """Convierte GameSession a SessionResponse"""
    return SessionResponse(
        session_id=session.session_id,
        player_id=session.player_id,
        game_id=session.game_id,
        started_at=session.started_at,
        ended_at=session.ended_at,
        duration_seconds=session.duration_seconds,
        platform=session.platform.value,
        is_active=session.is_active,
    )


# ==================== DEPENDENCY INJECTION ====================


def get_session_repository() -> SessionRepository:
    """Dependency que provee el repositorio de Sessions"""
    return SessionRepository()


def get_session_service(
    repository: SessionRepository = Depends(get_session_repository),
) -> SessionService:
    """Dependency que provee el servicio de Sessions"""
    return SessionService(repository=repository)


# ==================== ENDPOINTS ====================


@router.post("", response_model=SessionResponse, status_code=201)
def start_session(
    session_data: SessionCreate,
    request: Request,
    service: SessionService = Depends(get_session_service),
):
    """
    Iniciar una nueva sesion de juego.

    Requiere autenticacion de jugador.
    Cierra automaticamente sesiones huerfanas previas.

    Args:
        session_data: Datos de la sesion (game_id, platform)
        request: Request de FastAPI
        service: Servicio inyectado

    Returns:
        SessionResponse: Sesion creada

    Raises:
        HTTPException 400: Si la partida no existe o no pertenece al jugador
        HTTPException 401: Si no esta autenticado
    """
    player_id = getattr(request.state, "player_id", None)

    if not player_id:
        raise HTTPException(
            status_code=401, detail="Autenticacion de jugador requerida"
        )

    try:
        session = service.start_session(player_id, session_data)
        return session_to_response(session)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{session_id}/end", response_model=SessionResponse)
def end_session(
    session_id: str,
    request: Request,
    service: SessionService = Depends(get_session_service),
):
    """
    Terminar una sesion de juego activa.

    Solo puedes terminar tus propias sesiones.

    Args:
        session_id: ID de la sesion a terminar
        request: Request de FastAPI
        service: Servicio inyectado

    Returns:
        SessionResponse: Sesion finalizada con duracion calculada

    Raises:
        HTTPException 400: Si la sesion ya esta cerrada o no te pertenece
        HTTPException 404: Si la sesion no existe
    """
    player_id = getattr(request.state, "player_id", None)
    is_admin = getattr(request.state, "is_admin", False)

    # Admin puede cerrar cualquier sesion
    if is_admin:
        session = service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Sesion no encontrada")
        player_id = session.player_id

    if not player_id:
        raise HTTPException(status_code=401, detail="Autenticacion requerida")

    try:
        session = service.end_session(session_id, player_id)
        if not session:
            raise HTTPException(status_code=404, detail="Sesion no encontrada")
        return session_to_response(session)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/player/{player_id}", response_model=List[SessionResponse])
def get_player_sessions(
    player_id: str,
    request: Request,
    limit: int = 100,
    service: SessionService = Depends(get_session_service),
):
    """
    Obtener sesiones de un jugador.

    Solo puedes ver tus propias sesiones (a menos que seas admin).

    Args:
        player_id: ID del jugador
        request: Request de FastAPI
        limit: Maximo numero de sesiones
        service: Servicio inyectado

    Returns:
        Lista de sesiones ordenadas por fecha (mas reciente primero)
    """
    check_player_access(request, player_id)

    sessions = service.get_player_sessions(player_id, limit)
    return [session_to_response(s) for s in sessions]


@router.get("/game/{game_id}", response_model=List[SessionResponse])
def get_game_sessions(
    game_id: str,
    request: Request,
    limit: int = 100,
    service: SessionService = Depends(get_session_service),
):
    """
    Obtener sesiones de una partida.

    Solo puedes ver sesiones de tus propias partidas (a menos que seas admin).

    Args:
        game_id: ID de la partida
        request: Request de FastAPI
        limit: Maximo numero de sesiones
        service: Servicio inyectado

    Returns:
        Lista de sesiones de la partida
    """
    check_game_access(request, game_id)

    sessions = service.get_game_sessions(game_id, limit)
    return [session_to_response(s) for s in sessions]
