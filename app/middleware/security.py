"""
Esquemas de seguridad para autenticación

Define los esquemas de seguridad que se muestran en Swagger UI.
Proporciona dependencies para validar autenticación en endpoints.
"""

from typing import Optional, Annotated
from fastapi import HTTPException, Security, Depends
from fastapi.security import APIKeyHeader
from app.config.settings import settings
from app.domain.players.models import Player


# ==================== ESQUEMAS DE SEGURIDAD ====================

# API Key para administradores
api_key_header = APIKeyHeader(
    name="X-API-Key",
    description="API Key para acceso administrativo",
    auto_error=False,  # No lanza error automático, lo manejamos nosotros
)

# Headers para jugadores
player_id_header = APIKeyHeader(
    name="X-Player-ID", description="UUID del jugador", auto_error=False
)

player_token_header = APIKeyHeader(
    name="X-Player-Token", description="Token secreto del jugador", auto_error=False
)


# ==================== DEPENDENCIES DE VALIDACIÓN ====================


def get_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Valida que la API Key sea correcta.

    Returns:
        str: API Key válida

    Raises:
        HTTPException 401: Si la API Key es inválida o no existe
    """
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API Key requerida (header X-API-Key)",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if api_key != settings.api_key:
        raise HTTPException(
            status_code=401,
            detail="API Key inválida",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return api_key


def get_current_player(
    player_id: Optional[str] = Security(player_id_header),
    player_token: Optional[str] = Security(player_token_header),
) -> Player:
    """
    Valida las credenciales del jugador y retorna el Player.

    IMPORTANTE: Esta función hace una consulta a Firestore.
    Si ya tienes el player en request.state (del middleware),
    úsalo directamente en vez de esta dependency.

    Returns:
        Player: Jugador autenticado

    Raises:
        HTTPException 401: Si las credenciales son inválidas
    """
    if not player_id or not player_token:
        raise HTTPException(
            status_code=401,
            detail="Credenciales de jugador requeridas (headers X-Player-ID y X-Player-Token)",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Importar aquí para evitar circular import
    from app.domain.players.adapters.firestore_repository import (
        FirestorePlayerRepository,
    )

    repo = FirestorePlayerRepository()
    player = repo.get_by_id(player_id)

    if not player:
        raise HTTPException(
            status_code=401,
            detail="Player ID inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if player.player_token != player_token:
        raise HTTPException(
            status_code=401,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return player


def get_current_player_or_admin(
    api_key: Optional[str] = Security(api_key_header),
    player_id: Optional[str] = Security(player_id_header),
    player_token: Optional[str] = Security(player_token_header),
) -> tuple[bool, Optional[Player]]:
    """
    Valida que sea admin (API Key) o jugador (Player Token).

    Returns:
        tuple[bool, Optional[Player]]:
            - (True, None) si es admin
            - (False, Player) si es jugador autenticado

    Raises:
        HTTPException 401: Si no hay credenciales válidas
    """
    # Opción 1: Admin con API Key
    if api_key:
        if api_key == settings.api_key:
            return (True, None)  # Es admin
        else:
            raise HTTPException(status_code=401, detail="API Key inválida")

    # Opción 2: Jugador con Player Token
    if player_id and player_token:
        player = get_current_player(player_id, player_token)
        return (False, player)  # Es jugador

    # Sin credenciales
    raise HTTPException(
        status_code=401,
        detail="Autenticación requerida. Usa X-API-Key (admin) o X-Player-ID + X-Player-Token (jugador)",
    )


# ==================== TYPE ALIASES ====================

# Para usar como type hints en endpoints
CurrentPlayer = Annotated[Player, Depends(get_current_player)]
AdminApiKey = Annotated[str, Depends(get_api_key)]
PlayerOrAdmin = Annotated[
    tuple[bool, Optional[Player]], Depends(get_current_player_or_admin)
]
