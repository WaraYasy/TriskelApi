"""
Schemas (DTOs) para la API de Games

Modelos de entrada y salida para los endpoints de partidas.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class GameCreate(BaseModel):
    """
    Datos necesarios para crear una partida nueva.

    Solo se pide el player_id, todo lo demás se inicializa automáticamente.
    """
    player_id: str

    class Config:
        json_schema_extra = {
            "example": {
                "player_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }


class GameUpdate(BaseModel):
    """
    Datos que se pueden actualizar de una partida.

    Todos los campos son opcionales.
    """
    status: Optional[str] = None
    ended_at: Optional[datetime] = None
    completion_percentage: Optional[float] = None
    total_time_seconds: Optional[int] = None
    current_level: Optional[str] = None
    boss_defeated: Optional[bool] = None

    class Config:
        json_schema_extra = {
            "example": {
                "status": "completed",
                "completion_percentage": 100.0,
                "boss_defeated": True
            }
        }


class LevelStart(BaseModel):
    """
    Datos al iniciar un nivel.

    Solo necesita el nombre del nivel.
    """
    level: str  # hub_central | senda_ebano | fortaleza_gigantes | aquelarre_sombras | claro_almas

    class Config:
        json_schema_extra = {
            "example": {
                "level": "senda_ebano"
            }
        }


class LevelComplete(BaseModel):
    """
    Datos al completar un nivel.

    Incluye métricas, decisión moral (si aplica) y reliquia (si aplica).
    """
    level: str        # Nombre del nivel completado
    time_seconds: int  # Tiempo que tardó en completar
    deaths: int        # Número de muertes en el nivel
    choice: Optional[str] = None  # Decisión moral (si el nivel tiene)
    relic: Optional[str] = None   # Reliquia obtenida (si el nivel da una)

    class Config:
        json_schema_extra = {
            "example": {
                "level": "senda_ebano",
                "time_seconds": 245,
                "deaths": 3,
                "choice": "sanar",
                "relic": "lirio"
            }
        }
