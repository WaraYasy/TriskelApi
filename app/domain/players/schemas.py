"""Schemas (DTOs) para la API de Players.

Estos son los modelos de ENTRADA y SALIDA de la API REST.
Define qué datos acepta y retorna cada endpoint.

Autor: Mandrágora
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from .models import PlayerStats


class PlayerCreate(BaseModel):
    """Datos necesarios para crear un jugador nuevo.

    Requiere username y password. El email es opcional.
    El ID y token se generan automáticamente.

    Attributes:
        username (str): Nombre de usuario (3-20 caracteres).
        password (str): Contraseña (6-72 caracteres).
        email (Optional[str]): Email opcional.
    """

    username: str = Field(..., min_length=3, max_length=20)
    password: str = Field(..., min_length=6, max_length=72)
    email: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "username": "player123",
                "password": "mi_password_seguro",
                "email": "player@example.com",
            }
        }


class PlayerUpdate(BaseModel):
    """Datos que se pueden actualizar de un jugador.

    Todos los campos son opcionales (solo se actualizan los enviados).

    Attributes:
        username (Optional[str]): Nuevo nombre de usuario.
        email (Optional[str]): Nuevo email.
        total_playtime_seconds (Optional[int]): Nuevo tiempo de juego.
        games_played (Optional[int]): Total partidas jugadas.
        games_completed (Optional[int]): Total partidas completadas.
        stats (Optional[PlayerStats]): Estadísticas actualizadas.
        last_login (Optional[datetime]): Fecha de último login.
    """

    username: Optional[str] = Field(None, min_length=3, max_length=20)
    email: Optional[str] = None
    total_playtime_seconds: Optional[int] = None
    games_played: Optional[int] = None
    games_completed: Optional[int] = None
    stats: Optional[PlayerStats] = None
    last_login: Optional[datetime] = None

    class Config:
        json_schema_extra = {"example": {"total_playtime_seconds": 7200, "games_played": 10}}


class PlayerAuthResponse(BaseModel):
    """Respuesta al crear un jugador.

    El juego debe guardar el player_token para futuras peticiones.

    Attributes:
        player_id (str): ID del jugador.
        username (str): Nombre de usuario.
        player_token (str): Token que el juego debe enviar en headers.
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
    """Datos para login de jugador.

    Attributes:
        username (str): Nombre de usuario.
        password (str): Contraseña.
    """

    username: str = Field(..., min_length=3, max_length=20)
    password: str = Field(..., min_length=6, max_length=72)

    class Config:
        json_schema_extra = {"example": {"username": "player123", "password": "mi_password"}}


class PlayerLoginResponse(BaseModel):
    """Respuesta del login con partida activa opcional.

    Attributes:
        player_id (str): ID del jugador.
        username (str): Nombre de usuario.
        player_token (str): Token de sesión.
        active_game_id (Optional[str]): ID de partida activa si existe.
    """

    player_id: str
    username: str
    player_token: str
    active_game_id: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "player_id": "123e4567-e89b-12d3-a456-426614174000",
                "username": "player123",
                "player_token": "abc-def-token-secret",
                "active_game_id": "game-456-xyz",
            }
        }
