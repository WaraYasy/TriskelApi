"""Schemas (DTOs) para la API de Events.

Modelos de entrada y salida para los endpoints de eventos.

Autor: Mandrágora
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from app.core.exceptions import ValidationException
from app.core.validators import validate_level_name


class EventCreate(BaseModel):
    """Datos para crear un evento de gameplay.

    Los eventos son inmutables, solo se crean, no se actualizan.

    Attributes:
        game_id (str): ID de la partida.
        player_id (str): ID del jugador.
        event_type (str): Tipo de evento.
        level (str): Nivel del juego.
        data (Dict[str, Any]): Datos adicionales del evento.
    """

    game_id: str
    player_id: str
    event_type: str
    level: str
    data: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v: str) -> str:
        """Valida que el tipo de evento sea uno de los permitidos."""
        valid_types = [
            "player_death",
            "level_start",
            "level_end",
            "npc_interaction",
            "item_collected",
            "checkpoint_reached",
            "boss_encounter",
            "custom_event",
        ]
        if v not in valid_types:
            raise ValueError(f"Tipo de evento '{v}' no válido. Válidos: {', '.join(valid_types)}")
        return v

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        """Valida que el nivel sea uno de los 5 niveles válidos."""
        try:
            validate_level_name(v)
        except ValidationException as e:
            raise ValueError(str(e))
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "game_id": "abc-123",
                "player_id": "xyz-789",
                "event_type": "player_death",
                "level": "senda_ebano",
                "data": {"position": {"x": 150.5, "y": 200.3}, "cause": "fall"},
            }
        }


class EventBatchCreate(BaseModel):
    """Datos para crear múltiples eventos en una sola petición.

    Optimización: Unity puede enviar múltiples eventos acumulados
    para reducir número de requests HTTP.

    Attributes:
        events (List[EventCreate]): Lista de eventos a crear (1-100).
    """

    events: List[EventCreate] = Field(..., min_length=1, max_length=100)

    class Config:
        json_schema_extra = {
            "example": {
                "events": [
                    {
                        "game_id": "abc-123",
                        "player_id": "xyz-789",
                        "event_type": "player_death",
                        "level": "senda_ebano",
                        "data": {"position": {"x": 150.5, "y": 200.3}, "cause": "fall"},
                    },
                    {
                        "game_id": "abc-123",
                        "player_id": "xyz-789",
                        "event_type": "checkpoint_reached",
                        "level": "senda_ebano",
                        "data": {"checkpoint_id": "checkpoint_1"},
                    },
                ]
            }
        }


class EventFilter(BaseModel):
    """Filtros para buscar eventos.

    Todos los campos son opcionales, se combinan con AND.

    Attributes:
        game_id (Optional[str]): Filtrar por partida.
        player_id (Optional[str]): Filtrar por jugador.
        event_type (Optional[str]): Filtrar por tipo de evento.
        level (Optional[str]): Filtrar por nivel.
        start_time (Optional[datetime]): Fecha inicio.
        end_time (Optional[datetime]): Fecha fin.
        limit (int): Límite de resultados (1-1000).
    """

    game_id: Optional[str] = None
    player_id: Optional[str] = None
    event_type: Optional[str] = None
    level: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int = Field(default=100, ge=1, le=1000)

    class Config:
        json_schema_extra = {
            "example": {"game_id": "abc-123", "event_type": "player_death", "limit": 50}
        }
