"""Schemas (DTOs) para la API de Leaderboard.

Modelos de entrada y salida para los endpoints de rankings.

Autor: Mandrágora
"""

from datetime import datetime
from typing import List

from pydantic import BaseModel, Field

from .models import LeaderboardEntry


class LeaderboardResponse(BaseModel):
    """Respuesta con un leaderboard completo.

    Attributes:
        leaderboard_id (str): ID del leaderboard.
        leaderboard_name (str): Nombre legible.
        updated_at (datetime): Fecha de última actualización.
        entries (List[LeaderboardEntry]): Lista de entradas.
        total_entries (int): Total de entradas.
    """

    leaderboard_id: str
    leaderboard_name: str = Field(..., description="Nombre legible del leaderboard")
    updated_at: datetime
    entries: List[LeaderboardEntry]
    total_entries: int

    class Config:
        json_schema_extra = {
            "example": {
                "leaderboard_id": "speedrun",
                "leaderboard_name": "Speedrun - Mejor Tiempo",
                "updated_at": "2024-01-20T06:00:00Z",
                "entries": [
                    {
                        "rank": 1,
                        "player_id": "uuid-1",
                        "username": "FastPlayer",
                        "value": 1800,
                        "game_id": "game-1",
                        "achieved_at": "2024-01-19T15:00:00Z",
                    }
                ],
                "total_entries": 1,
            }
        }


class LeaderboardListResponse(BaseModel):
    """Lista de leaderboards disponibles.

    Attributes:
        leaderboards (List[dict]): Lista de leaderboards con info básica.
    """

    leaderboards: List[dict] = Field(..., description="Lista de leaderboards con info basica")

    class Config:
        json_schema_extra = {
            "example": {
                "leaderboards": [
                    {
                        "leaderboard_id": "speedrun",
                        "name": "Speedrun - Mejor Tiempo",
                        "description": "Jugadores mas rapidos en completar el juego",
                    },
                    {
                        "leaderboard_id": "moral_good",
                        "name": "Guardian del Bien",
                        "description": "Jugadores con mayor alineacion positiva",
                    },
                ]
            }
        }


class RefreshResponse(BaseModel):
    """Respuesta al forzar recálculo de leaderboards.

    Attributes:
        message (str): Mensaje de estado.
        leaderboards_updated (List[str]): IDs de leaderboards actualizados.
        updated_at (datetime): Fecha de actualización.
    """

    message: str
    leaderboards_updated: List[str]
    updated_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Leaderboards actualizados correctamente",
                "leaderboards_updated": [
                    "speedrun",
                    "moral_good",
                    "moral_evil",
                    "completions",
                ],
                "updated_at": "2024-01-20T12:00:00Z",
            }
        }
