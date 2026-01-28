"""Modelos de dominio para Events.

Representa eventos de gameplay que ocurren durante una partida.
Los eventos son inmutables una vez creados (solo inserción, no actualización).

Autor: Mandrágora
"""

import uuid
from datetime import datetime
from typing import Any, Dict

from pydantic import BaseModel, Field


class GameEvent(BaseModel):
    """Evento de gameplay.

    Un evento representa una acción o suceso que ocurre durante una partida.
    Los eventos son inmutables y se usan para análisis y métricas.

    Tipos de eventos soportados:
    - player_death: Muerte del jugador.
    - level_start: Inicio de nivel.
    - level_end: Fin de nivel.
    - npc_interaction: Interacción con NPC.
    - item_collected: Item recogido.
    - checkpoint_reached: Checkpoint alcanzado.
    - boss_encounter: Encuentro con jefe.
    - custom_event: Eventos personalizados.

    Attributes:
        event_id (str): ID único del evento (UUID).
        game_id (str): ID de la partida donde ocurrió.
        player_id (str): ID del jugador que generó el evento.
        timestamp (datetime): Momento exacto del evento (UTC).
        event_type (str): Tipo de evento (ver tipos soportados).
        level (str): Nivel donde ocurrió el evento.
        data (Dict[str, Any]): Datos específicos del evento (estructura varía por tipo).
    """

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    game_id: str
    player_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_type: str
    level: str
    data: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "123e4567-e89b-12d3-a456-426614174000",
                "game_id": "abc-123",
                "player_id": "xyz-789",
                "timestamp": "2024-01-10T15:30:00Z",
                "event_type": "player_death",
                "level": "senda_ebano",
                "data": {"position": {"x": 150.5, "y": 200.3}, "cause": "fall"},
            }
        }

    def to_dict(self) -> dict:
        """Convierte el evento a diccionario para Firestore."""
        return {
            "event_id": self.event_id,
            "game_id": self.game_id,
            "player_id": self.player_id,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "level": self.level,
            "data": self.data,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GameEvent":
        """Crea un evento desde un diccionario de Firestore."""
        return cls(**data)
