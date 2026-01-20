"""
Modelos de dominio para Sessions

Una sesion representa un periodo continuo de tiempo que el jugador
esta jugando (desde que abre el juego hasta que lo cierra).
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field, computed_field


class Platform(str, Enum):
    """Plataformas soportadas"""

    WINDOWS = "windows"
    ANDROID = "android"


class GameSession(BaseModel):
    """
    Entidad principal: Sesion de Juego.

    Representa un periodo continuo en el que un jugador esta
    conectado al juego.

    Attributes:
        session_id: ID unico de la sesion (UUID)
        player_id: ID del jugador (FK obligatorio)
        game_id: ID de la partida asociada (FK obligatorio)
        started_at: Momento de inicio de la sesion
        ended_at: Momento de fin (None si activa)
        platform: Plataforma del cliente (windows/android)
    """

    session_id: str = Field(default_factory=lambda: f"s-{uuid4()}")
    player_id: str  # FK obligatorio
    game_id: str  # FK obligatorio
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: Optional[datetime] = None
    platform: Platform

    @computed_field
    @property
    def duration_seconds(self) -> int:
        """
        Calcula la duracion de la sesion en segundos.

        Si la sesion esta activa (ended_at=None), calcula
        hasta el momento actual.
        """
        end_time = self.ended_at or datetime.now(timezone.utc)
        # Asegurar que ambos datetime tengan timezone
        start = self.started_at
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=timezone.utc)
        delta = end_time - start
        return max(0, int(delta.total_seconds()))

    @property
    def is_active(self) -> bool:
        """Indica si la sesion sigue activa"""
        return self.ended_at is None

    def to_dict(self) -> dict:
        """Convierte la sesion a diccionario para Firestore"""
        data = self.model_dump()
        data["started_at"] = self.started_at
        if self.ended_at:
            data["ended_at"] = self.ended_at
        # platform como string para Firestore
        data["platform"] = self.platform.value
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "GameSession":
        """Crea una sesion desde diccionario de Firestore"""
        # Convertir platform string a enum si es necesario
        if isinstance(data.get("platform"), str):
            data["platform"] = Platform(data["platform"])
        return cls(**data)
