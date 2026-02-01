"""
API REST para Events

Endpoints de FastAPI para gestionar eventos de gameplay.

Reglas de acceso:
- POST /v1/events: Jugador autenticado (crear eventos propios)
- POST /v1/events/batch: Jugador autenticado (crear eventos propios)
- GET /v1/events/game/{game_id}: Solo si es tu partida o con API Key
- GET /v1/events/player/{player_id}: Solo si es tu ID o con API Key

Autor: Mandrágora

"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.middleware.rate_limit import EVENT_CREATE_LIMIT, limiter

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
    """Verifica que el usuario tenga permisos para crear un evento.

    Reglas:
    - Admin (API Key): puede crear eventos para cualquier jugador.
    - Jugador autenticado: solo puede crear eventos para sí mismo.

    Args:
        request (Request): Request de FastAPI con estado de autenticación.
        event_data (EventCreate): Datos del evento a crear.

    Raises:
        HTTPException: Si no tiene permisos (403).
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
    """Verifica permisos para crear batch de eventos.

    Args:
        request (Request): Request de FastAPI.
        batch_data (EventBatchCreate): Batch de eventos.

    Raises:
        HTTPException: Si algún evento no tiene permisos (403).
    """
    for event_data in batch_data.events:
        check_event_creation_access(request, event_data)


def check_game_events_access(request: Request, game_id: str) -> None:
    """Verifica permisos para ver eventos de una partida.

    Reglas:
    - Admin (API Key): puede ver eventos de cualquier partida.
    - Jugador autenticado: solo puede ver eventos de sus partidas.

    Args:
        request (Request): Request de FastAPI.
        game_id (str): ID de la partida.

    Raises:
        HTTPException: Si no tiene permisos (403).
        HTTPException: Si la partida no existe (404).
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
    """Verifica permisos para ver eventos de un jugador.

    Reglas:
    - Admin (API Key): puede ver eventos de cualquier jugador.
    - Jugador autenticado: solo puede ver sus propios eventos.

    Args:
        request (Request): Request de FastAPI.
        player_id (str): ID del jugador.

    Raises:
        HTTPException: Si no tiene permisos (403).
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
    """Dependency que provee el repositorio de Events.

    Returns:
        EventRepository: Repositorio instanciado.
    """
    return EventRepository()


def get_event_service(
    repository: EventRepository = Depends(get_event_repository),
) -> EventService:
    """Dependency que provee el servicio de Events.

    Args:
        repository (EventRepository): Repositorio inyectado.

    Returns:
        EventService: Servicio instanciado.
    """
    return EventService(repository=repository)


# ==================== ENDPOINTS ====================


@router.post("", response_model=GameEvent, status_code=201)
@limiter.limit(EVENT_CREATE_LIMIT)
def create_event(
    request: Request,
    event_data: EventCreate,
    service: EventService = Depends(get_event_service),
):
    """Crear un evento de gameplay.

    Solo puedes crear eventos para ti mismo (a menos que seas admin).

    Args:
        event_data (EventCreate): Datos del evento.
        request (Request): Request de FastAPI.
        service (EventService): Servicio inyectado.

    Returns:
        GameEvent: Evento creado.

    Raises:
        HTTPException: Si intentas crear evento para otro jugador (403).
        HTTPException: Si el jugador no existe (404).
    """
    # Verificar permisos
    check_event_creation_access(request, event_data)

    try:
        return service.create_event(event_data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/batch", response_model=List[GameEvent], status_code=201)
@limiter.limit(EVENT_CREATE_LIMIT)
def create_batch(
    request: Request,
    batch_data: EventBatchCreate,
    service: EventService = Depends(get_event_service),
):
    """Crear múltiples eventos en una sola petición.

    Optimización para Unity: enviar eventos acumulados.
    Solo puedes crear eventos para ti mismo (a menos que seas admin).

    Args:
        batch_data (EventBatchCreate): Batch de eventos.
        request (Request): Request de FastAPI.
        service (EventService): Servicio inyectado.

    Returns:
        List[GameEvent]: Lista de eventos creados.

    Raises:
        HTTPException: Si intentas crear eventos para otro jugador (403).
        HTTPException: Si algún jugador no existe (404).
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
    limit: int = Query(default=100, ge=1, le=500, description="Máximo de eventos a retornar"),
    days: Optional[int] = Query(
        default=1, ge=1, le=30, description="Filtrar últimos N días (default: 1, máx: 30)"
    ),
    since: Optional[str] = Query(default=None, description="Filtrar desde fecha ISO"),
    until: Optional[str] = Query(default=None, description="Filtrar hasta fecha ISO"),
    service: EventService = Depends(get_event_service),
):
    """Obtener todos los eventos de todos los jugadores (ADMIN ONLY).

    Este endpoint está diseñado para analytics y herramientas de administración.
    Requiere autenticación admin (JWT con rol admin o API Key).

    OPTIMIZACIÓN CRÍTICA: Límite reducido de 5000 → 100 por defecto (máx 500).
    Por defecto filtra últimos 1 día. Events son MUY numerosos, usar filtros de fecha.

    Examples:
        GET /events?days=1         → Últimas 24 horas (default)
        GET /events?days=7         → Última semana
        GET /events?since=2026-01-25&limit=200  → Desde fecha específica

    Args:
        request (Request): Request de FastAPI.
        limit (int): Máximo de eventos (default: 100, máx: 500).
        days (int): Filtrar últimos N días (default: 1, máx: 30).
        since (str, optional): Filtrar desde fecha ISO 8601.
        until (str, optional): Filtrar hasta fecha ISO 8601.
        service (EventService): Servicio inyectado.

    Returns:
        List[GameEvent]: Lista de todos los eventos filtrados.

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
            raise HTTPException(status_code=400, detail="Formato de fecha 'since' inválido")

    if until:
        try:
            until_date = datetime.fromisoformat(until.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de fecha 'until' inválido")

    return service.get_all_events(limit=limit, days=days, since=since_date, until=until_date)


@router.get("/game/{game_id}", response_model=List[GameEvent])
def get_game_events(
    game_id: str,
    request: Request,
    limit: int = Query(default=500, ge=1, le=1000, description="Máximo de eventos"),
    days: Optional[int] = Query(default=None, ge=1, le=90, description="Filtrar últimos N días"),
    since: Optional[str] = Query(default=None, description="Filtrar desde fecha ISO"),
    until: Optional[str] = Query(default=None, description="Filtrar hasta fecha ISO"),
    service: EventService = Depends(get_event_service),
):
    """Obtener eventos de una partida con filtros opcionales.

    Solo puedes ver eventos de tus propias partidas (a menos que seas admin).

    Examples:
        GET /events/game/{id}              → Últimos 500 eventos
        GET /events/game/{id}?days=1       → Última sesión
        GET /events/game/{id}?limit=100    → Primeros 100

    Args:
        game_id (str): ID de la partida.
        request (Request): Request de FastAPI.
        limit (int): Máximo de eventos (default: 500, máx: 1000).
        days (int, optional): Filtrar últimos N días.
        since (str, optional): Filtrar desde fecha ISO 8601.
        until (str, optional): Filtrar hasta fecha ISO 8601.
        service (EventService): Servicio inyectado.

    Returns:
        List[GameEvent]: Lista de eventos ordenados por timestamp.

    Raises:
        HTTPException: Si intentas ver eventos de otra partida (403).
        HTTPException: Si la partida no existe (404) o formato de fecha inválido (400).
    """
    # Verificar permisos
    check_game_events_access(request, game_id)

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

    return service.get_game_events(
        game_id, limit=limit, days=days, since=since_date, until=until_date
    )


@router.get("/player/{player_id}", response_model=List[GameEvent])
def get_player_events(
    player_id: str,
    request: Request,
    limit: int = Query(default=200, ge=1, le=500, description="Máximo de eventos"),
    days: Optional[int] = Query(default=None, ge=1, le=90, description="Filtrar últimos N días"),
    since: Optional[str] = Query(default=None, description="Filtrar desde fecha ISO"),
    until: Optional[str] = Query(default=None, description="Filtrar hasta fecha ISO"),
    service: EventService = Depends(get_event_service),
):
    """Obtener eventos de un jugador con filtros opcionales.

    Solo puedes ver tus propios eventos (a menos que seas admin).

    Examples:
        GET /events/player/{id}           → Últimos 200 eventos
        GET /events/player/{id}?days=7    → Última semana
        GET /events/player/{id}?limit=50  → Primeros 50

    Args:
        player_id (str): ID del jugador.
        request (Request): Request de FastAPI.
        limit (int): Máximo de eventos (default: 200, máx: 500).
        days (int, optional): Filtrar últimos N días.
        since (str, optional): Filtrar desde fecha ISO 8601.
        until (str, optional): Filtrar hasta fecha ISO 8601.
        service (EventService): Servicio inyectado.

    Returns:
        List[GameEvent]: Lista de eventos ordenados por timestamp.

    Raises:
        HTTPException: Si intentas ver eventos de otro jugador (403) o formato inválido (400).
    """
    # Verificar permisos
    check_player_events_access(request, player_id)

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

    return service.get_player_events(
        player_id, limit=limit, days=days, since=since_date, until=until_date
    )


@router.get("/game/{game_id}/type/{event_type}", response_model=List[GameEvent])
def get_game_events_by_type(
    game_id: str,
    event_type: str,
    request: Request,
    limit: int = 1000,
    service: EventService = Depends(get_event_service),
):
    """Obtener eventos de una partida filtrados por tipo.

    Solo puedes ver eventos de tus propias partidas (a menos que seas admin).

    Args:
        game_id (str): ID de la partida.
        event_type (str): Tipo de evento a filtrar.
        request (Request): Request de FastAPI.
        limit (int): Máximo número de eventos.
        service (EventService): Servicio inyectado.

    Returns:
        List[GameEvent]: Lista de eventos filtrados.

    Raises:
        HTTPException: Si intentas ver eventos de otra partida (403).
        HTTPException: Si la partida no existe (404).
    """
    # Verificar permisos
    check_game_events_access(request, game_id)

    return service.get_events_by_type(event_type, game_id, limit)
