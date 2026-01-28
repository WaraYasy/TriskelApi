"""Schemas (DTOs) para la API de Sessions.

Modelos de entrada y salida para los endpoints de sesiones.

Autor: Mandrágora
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from .models import Platform


class SessionCreate(BaseModel):
    """Datos para iniciar una sesión de juego.

    player_id se obtiene del middleware de autenticación.

    Attributes:
        game_id (str): ID de la partida activa.
        platform (Platform): Plataforma del cliente.
    """

    game_id: str = Field(..., description="ID de la partida activa")
    platform: Platform = Field(..., description="Plataforma del cliente")

    class Config:
        json_schema_extra = {"example": {"game_id": "abc-123-xyz", "platform": "windows"}}


class SessionEnd(BaseModel):
    """Datos para finalizar una sesión.

    Por ahora vacío, pero puede extenderse para incluir
    métricas de cierre o razón de finalización.
    """

    pass


class SessionResponse(BaseModel):
    """Respuesta con datos de sesión.

    Incluye todos los campos de GameSession más campos calculados.

    Attributes:
        session_id (str): ID único de la sesión.
        player_id (str): ID del jugador.
        game_id (str): ID de la partida.
        started_at (datetime): Fecha de inicio.
        ended_at (Optional[datetime]): Fecha de fin.
        duration_seconds (int): Duración en segundos.
        platform (str): Plataforma.
        is_active (bool): Si la sesión está activa.
    """

    session_id: str
    player_id: str
    game_id: str
    started_at: datetime
    ended_at: Optional[datetime]
    duration_seconds: int
    platform: str
    is_active: bool

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "s-123e4567-e89b-12d3-a456",
                "player_id": "player-uuid-here",
                "game_id": "game-uuid-here",
                "started_at": "2024-01-20T10:30:00Z",
                "ended_at": "2024-01-20T12:30:00Z",
                "duration_seconds": 7200,
                "platform": "windows",
                "is_active": False,
            }
        }


class SessionListResponse(BaseModel):
    """Respuesta paginada con lista de sesiones.

    Attributes:
        sessions (List[SessionResponse]): Lista de sesiones.
        total (int): Total de sesiones encontradas.
    """

    sessions: List[SessionResponse]
    total: int

    class Config:
        json_schema_extra = {"example": {"sessions": [], "total": 0}}
