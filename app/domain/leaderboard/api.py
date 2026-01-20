"""
API REST para Leaderboard

Endpoints de FastAPI para consultar rankings.

Reglas de acceso:
- GET /v1/leaderboard: Publico (listar tipos disponibles)
- GET /v1/leaderboard/{type}: Publico (ver ranking especifico)
- POST /v1/admin/leaderboard/refresh: Solo admin (forzar recalculo)
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request

from .models import LeaderboardType
from .repository import LeaderboardRepository
from .schemas import LeaderboardListResponse, LeaderboardResponse, RefreshResponse
from .service import LEADERBOARD_NAMES, LeaderboardService

# Router de FastAPI (endpoints publicos)
router = APIRouter(prefix="/v1/leaderboard", tags=["Leaderboard"])

# Router admin separado
admin_router = APIRouter(prefix="/v1/admin/leaderboard", tags=["Admin - Leaderboard"])


# ==================== DEPENDENCY INJECTION ====================


def get_leaderboard_repository() -> LeaderboardRepository:
    """Dependency que provee el repositorio de Leaderboard"""
    return LeaderboardRepository()


def get_leaderboard_service(
    repository: LeaderboardRepository = Depends(get_leaderboard_repository),
) -> LeaderboardService:
    """Dependency que provee el servicio de Leaderboard"""
    return LeaderboardService(repository=repository)


# ==================== ENDPOINTS PUBLICOS ====================


@router.get("", response_model=LeaderboardListResponse)
def list_leaderboards(
    service: LeaderboardService = Depends(get_leaderboard_service),
):
    """
    Listar todos los tipos de leaderboard disponibles.

    Endpoint publico - no requiere autenticacion.

    Returns:
        LeaderboardListResponse: Lista de leaderboards con info basica
    """
    leaderboards = service.get_all_leaderboards_info()
    return LeaderboardListResponse(leaderboards=leaderboards)


@router.get("/{leaderboard_type}", response_model=LeaderboardResponse)
def get_leaderboard(
    leaderboard_type: str,
    service: LeaderboardService = Depends(get_leaderboard_service),
):
    """
    Obtener un leaderboard especifico con sus rankings.

    Endpoint publico - no requiere autenticacion.

    Args:
        leaderboard_type: Tipo de leaderboard (speedrun, moral_good, moral_evil, completions)
        service: Servicio inyectado

    Returns:
        LeaderboardResponse: Leaderboard completo con entradas

    Raises:
        HTTPException 400: Si el tipo no es valido
        HTTPException 404: Si el leaderboard no tiene datos
    """
    # Validar tipo
    try:
        lb_type = LeaderboardType(leaderboard_type)
    except ValueError:
        valid_types = [t.value for t in LeaderboardType]
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de leaderboard invalido. Validos: {', '.join(valid_types)}",
        )

    leaderboard = service.get_leaderboard(lb_type)

    if not leaderboard:
        raise HTTPException(
            status_code=404,
            detail=f"Leaderboard '{leaderboard_type}' no encontrado. "
            "Puede que aun no se haya calculado.",
        )

    return LeaderboardResponse(
        leaderboard_id=leaderboard.leaderboard_id.value,
        leaderboard_name=LEADERBOARD_NAMES[leaderboard.leaderboard_id],
        updated_at=leaderboard.updated_at,
        entries=leaderboard.entries,
        total_entries=len(leaderboard.entries),
    )


# ==================== ENDPOINTS ADMIN ====================


@admin_router.post("/refresh", response_model=RefreshResponse)
def refresh_leaderboards(
    request: Request,
    service: LeaderboardService = Depends(get_leaderboard_service),
):
    """
    Forzar recalculo de todos los leaderboards.

    SOLO ADMIN - Requiere API Key o JWT de administrador.

    Este endpoint es util para:
    - Pruebas de desarrollo
    - Forzar actualizacion inmediata
    - Recuperacion de errores del scheduler

    Args:
        request: Request de FastAPI
        service: Servicio inyectado

    Returns:
        RefreshResponse: Confirmacion con leaderboards actualizados

    Raises:
        HTTPException 403: Si no es admin
    """
    is_admin = getattr(request.state, "is_admin", False)

    if not is_admin:
        raise HTTPException(
            status_code=403,
            detail="Este endpoint solo esta disponible para administradores",
        )

    updated = service.refresh_all_leaderboards()

    return RefreshResponse(
        message="Leaderboards actualizados correctamente",
        leaderboards_updated=updated,
        updated_at=datetime.now(timezone.utc),
    )
