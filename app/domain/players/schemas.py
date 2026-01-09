"""
Schemas (DTOs) para la API de Players

Estos son los modelos de ENTRADA y SALIDA de la API REST.
Define qué datos acepta y retorna cada endpoint.
"""
from pydantic import BaseModel, Field
from typing import Optional
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
        json_schema_extra = {
            "example": {
                "username": "player123",
                "email": "player@example.com"
            }
        }


class PlayerUpdate(BaseModel):
    """
    Datos que se pueden actualizar de un jugador.

    Todos los campos son opcionales (solo se actualizan los enviados).
    """
    username: Optional[str] = Field(None, min_length=3, max_length=20)
    email: Optional[str] = None
    total_playtime_seconds: Optional[int] = None
    games_played: Optional[int] = None
    games_completed: Optional[int] = None
    stats: Optional[PlayerStats] = None

    class Config:
        json_schema_extra = {
            "example": {
                "total_playtime_seconds": 7200,
                "games_played": 10
            }
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
                "player_token": "abc-def-token-secret"
            }
        }
