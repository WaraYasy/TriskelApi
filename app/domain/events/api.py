"""
API REST para Events

Endpoints de FastAPI para gestionar eventos de gameplay.

Reglas de acceso:
- POST /v1/events: Jugador autenticado (crear eventos propios)
- POST /v1/events/batch: Jugador autenticado (crear eventos propios)
- GET /v1/events/game/{game_id}: Solo si es tu partida o con API Key
- GET /v1/events/player/{player_id}: Solo si es tu ID o con API Key
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request

# Importar game repository para validar permisos de partida
from ..games.adapters.firestore_repository import FirestoreGameRepository
from .models import GameEvent
from .repository import EventRepository
from .schemas import EventBatchCreate, EventCreate
from .service import EventService

# Router de FastAPI
router = APIRouter(prefix="/v1/events", tags=["Events"])


# ==================== HELPERS ====================


def check_event_creation_access(request: Request, event_data: EventCreate) -> None:
    """
    Verifica que el usuario tenga permisos para crear un evento.

    Reglas:
    - Admin (API Key): puede crear eventos para cualquier jugador
    - Jugador autenticado: solo puede crear eventos para sí mismo

    Args:
        request: Request de FastAPI con estado de autenticación
        event_data: Datos del evento a crear

    Raises:
        HTTPException 403: Si no tiene permisos
    """
    is_admin = getattr(request.state, "is_admin", False)
    authenticated_player_id = getattr(request.state, "player_id", None)

    # Admin puede crear eventos para cualquier jugador
    if is_admin:
        return

    # Jugador solo puede crear eventos para sí mismo
    if event_data.player_id != authenticated_player_id:
        raise HTTPException(status_code=403, detail="Solo puedes crear eventos para ti mismo")


def check_batch_creation_access(request: Request, batch_data: EventBatchCreate) -> None:
    """
    Verifica permisos para crear batch de eventos.

    Args:
        request: Request de FastAPI
        batch_data: Batch de eventos

    Raises:
        HTTPException 403: Si algún evento no tiene permisos
    """
    for event_data in batch_data.events:
        check_event_creation_access(request, event_data)


def check_game_events_access(request: Request, game_id: str) -> None:
    """
    Verifica permisos para ver eventos de una partida.

    Reglas:
    - Admin (API Key): puede ver eventos de cualquier partida
    - Jugador autenticado: solo puede ver eventos de sus partidas

    Args:
        request: Request de FastAPI
        game_id: ID de la partida

    Raises:
        HTTPException 403: Si no tiene permisos
        HTTPException 404: Si la partida no existe
    """
    is_admin = getattr(request.state, "is_admin", False)
    authenticated_player_id = getattr(request.state, "player_id", None)

    # Admin puede ver eventos de cualquier partida
    if is_admin:
        return

    # Verificar que la partida existe y pertenece al jugador
    game_repo = FirestoreGameRepository()
    game = game_repo.get_by_id(game_id)

    if not game:
        raise HTTPException(status_code=404, detail="Partida no encontrada")

    if game.player_id != authenticated_player_id:
        raise HTTPException(
            status_code=403,
            detail="No tienes permisos para ver eventos de esta partida",
        )


def check_player_events_access(request: Request, player_id: str) -> None:
    """
    Verifica permisos para ver eventos de un jugador.

    Reglas:
    - Admin (API Key): puede ver eventos de cualquier jugador
    - Jugador autenticado: solo puede ver sus propios eventos

    Args:
        request: Request de FastAPI
        player_id: ID del jugador

    Raises:
        HTTPException 403: Si no tiene permisos
    """
    is_admin = getattr(request.state, "is_admin", False)
    authenticated_player_id = getattr(request.state, "player_id", None)

    # Admin puede ver eventos de cualquier jugador
    if is_admin:
        return

    # Jugador solo puede ver sus propios eventos
    if player_id != authenticated_player_id:
        raise HTTPException(
            status_code=403,
            detail="No tienes permisos para ver eventos de este jugador",
        )


# ==================== DEPENDENCY INJECTION ====================


def get_event_repository() -> EventRepository:
    """Dependency que provee el repositorio de Events"""
    return EventRepository()


def get_event_service(
    repository: EventRepository = Depends(get_event_repository),
) -> EventService:
    """Dependency que provee el servicio de Events"""
    return EventService(repository=repository)


# ==================== ENDPOINTS ====================


@router.post("", response_model=GameEvent, status_code=201)
def create_event(
    event_data: EventCreate,
    request: Request,
    service: EventService = Depends(get_event_service),
):
    """
    Crear un evento de gameplay.

    Solo puedes crear eventos para ti mismo (a menos que seas admin).

    Args:
        event_data: Datos del evento
        request: Request de FastAPI
        service: Servicio inyectado

    Returns:
        GameEvent: Evento creado

    Raises:
        HTTPException 403: Si intentas crear evento para otro jugador
        HTTPException 404: Si el jugador no existe
    """
    # Verificar permisos
    check_event_creation_access(request, event_data)

    try:
        return service.create_event(event_data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/batch", response_model=List[GameEvent], status_code=201)
def create_batch(
    batch_data: EventBatchCreate,
    request: Request,
    service: EventService = Depends(get_event_service),
):
    """
    Crear múltiples eventos en una sola petición.

    Optimización para Unity: enviar eventos acumulados.
    Solo puedes crear eventos para ti mismo (a menos que seas admin).

    Args:
        batch_data: Batch de eventos
        request: Request de FastAPI
        service: Servicio inyectado

    Returns:
        List[GameEvent]: Lista de eventos creados

    Raises:
        HTTPException 403: Si intentas crear eventos para otro jugador
        HTTPException 404: Si algún jugador no existe
    """
    # Verificar permisos para todos los eventos
    check_batch_creation_access(request, batch_data)

    try:
        return service.create_batch(batch_data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("", response_model=List[GameEvent])
def get_all_events(
    request: Request,
    limit: int = 5000,
    service: EventService = Depends(get_event_service),
):
    """
    Obtener todos los eventos de todos los jugadores (ADMIN ONLY).

    Este endpoint está diseñado para analytics y herramientas de administración.
    Requiere autenticación admin (JWT con rol admin o API Key).

    Args:
        request: Request de FastAPI
        limit: Máximo número de eventos a retornar (default: 5000)
        service: Servicio inyectado

    Returns:
        List[GameEvent]: Lista de todos los eventos

    Raises:
        HTTPException 403: Si no tiene permisos de admin
    """
    # Verificar que es admin
    is_admin = getattr(request.state, "is_admin", False)

    if not is_admin:
        raise HTTPException(
            status_code=403,
            detail="Este endpoint requiere permisos de administrador. Usa API Key o JWT token de admin."
        )

    return service.get_all_events(limit=limit)


@router.get("/game/{game_id}", response_model=List[GameEvent])
def get_game_events(
    game_id: str,
    request: Request,
    limit: int = 1000,
    service: EventService = Depends(get_event_service),
):
    """
    Obtener eventos de una partida.

    Solo puedes ver eventos de tus propias partidas (a menos que seas admin).

    Args:
        game_id: ID de la partida
        request: Request de FastAPI
        limit: Máximo número de eventos
        service: Servicio inyectado

    Returns:
        List[GameEvent]: Lista de eventos ordenados por timestamp

    Raises:
        HTTPException 403: Si intentas ver eventos de otra partida
        HTTPException 404: Si la partida no existe
    """
    # Verificar permisos
    check_game_events_access(request, game_id)

    return service.get_game_events(game_id, limit)


@router.get("/player/{player_id}", response_model=List[GameEvent])
def get_player_events(
    player_id: str,
    request: Request,
    limit: int = 1000,
    service: EventService = Depends(get_event_service),
):
    """
    Obtener eventos de un jugador.

    Solo puedes ver tus propios eventos (a menos que seas admin).

    Args:
        player_id: ID del jugador
        request: Request de FastAPI
        limit: Máximo número de eventos
        service: Servicio inyectado

    Returns:
        List[GameEvent]: Lista de eventos ordenados por timestamp

    Raises:
        HTTPException 403: Si intentas ver eventos de otro jugador
    """
    # Verificar permisos
    check_player_events_access(request, player_id)

    return service.get_player_events(player_id, limit)


@router.get("/game/{game_id}/type/{event_type}", response_model=List[GameEvent])
def get_game_events_by_type(
    game_id: str,
    event_type: str,
    request: Request,
    limit: int = 1000,
    service: EventService = Depends(get_event_service),
):
    """
    Obtener eventos de una partida filtrados por tipo.

    Solo puedes ver eventos de tus propias partidas (a menos que seas admin).

    Args:
        game_id: ID de la partida
        event_type: Tipo de evento a filtrar
        request: Request de FastAPI
        limit: Máximo número de eventos
        service: Servicio inyectado

    Returns:
        List[GameEvent]: Lista de eventos filtrados

    Raises:
        HTTPException 403: Si intentas ver eventos de otra partida
        HTTPException 404: Si la partida no existe
    """
    # Verificar permisos
    check_game_events_access(request, game_id)

    return service.get_events_by_type(event_type, game_id, limit)
