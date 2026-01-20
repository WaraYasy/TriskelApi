"""
Schemas (DTOs) para la API de Players

Estos son los modelos de ENTRADA y SALIDA de la API REST.
Define qué datos acepta y retorna cada endpoint.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from .models import PlayerStats


class PlayerCreate(BaseModel):
    """
    Datos necesarios para crear un jugador nuevo.

    Solo se pide username y email (opcional).
    El ID y token se generan automáticamente.
    """

    username: str = Field(..., min_length=3, max_length=20)
    email: Optional[str] = None

    class Config:
        json_schema_extra = {"example": {"username": "player123", "email": "player@example.com"}}


class PlayerUpdate(BaseModel):
    """
    Datos que se pueden actualizar de un jugador.

    Todos los campos son opcionales (solo se actualizan los enviados).
    """

    username: Optional[str] = Field(None, min_length=3, max_length=20)
    display_name: Optional[str] = Field(None, min_length=1, max_length=30)
    email: Optional[str] = None
    total_playtime_seconds: Optional[int] = None
    games_played: Optional[int] = None
    games_completed: Optional[int] = None
    stats: Optional[PlayerStats] = None
    last_login: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {"display_name": "GuerreroOscuro", "total_playtime_seconds": 7200}
        }


class PlayerAuthResponse(BaseModel):
    """
    Respuesta al crear un jugador.

    El juego debe guardar el player_token para futuras peticiones.
    """

    player_id: str
    username: str
    player_token: str  # Token que el juego debe enviar en headers

    class Config:
        json_schema_extra = {
            "example": {
                "player_id": "123e4567-e89b-12d3-a456-426614174000",
                "username": "player123",
                "player_token": "abc-def-token-secret",
            }
        }


class PlayerLoginRequest(BaseModel):
    """Datos para login/registro de jugador"""

    username: str = Field(..., min_length=3, max_length=20)
    email: Optional[str] = None


class PlayerLoginResponse(BaseModel):
    """Respuesta del login con partida activa opcional"""

    player_id: str
    username: str
    display_name: str
    player_token: str
    active_game_id: Optional[str] = None
    is_new_player: bool


class DeviceRegisterResponse(BaseModel):
    """
    Respuesta al registrar un dispositivo (sin username).

    El juego debe guardar player_id y player_token en almacenamiento local.
    Si se pierde, no hay forma de recuperar la cuenta.
    """

    player_id: str
    player_token: str
    display_name: str
    is_new_player: bool = True

    class Config:
        json_schema_extra = {
            "example": {
                "player_id": "550e8400-e29b-41d4-a716-446655440000",
                "player_token": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
                "display_name": "Druida_A7B3",
                "is_new_player": True,
            }
        }
