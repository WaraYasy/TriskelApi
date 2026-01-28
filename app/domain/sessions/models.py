"""Modelos de dominio para Sessions.

Una sesión representa un periodo continuo de tiempo que el jugador
está jugando (desde que abre el juego hasta que lo cierra).

Autor: Mandrágora
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field, computed_field


class Platform(str, Enum):
    """Plataformas soportadas."""

    WINDOWS = "windows"
    ANDROID = "android"


class GameSession(BaseModel):
    """Entidad principal: Sesión de Juego.

    Representa un periodo continuo en el que un jugador está
    conectado al juego.

    Attributes:
        session_id (str): ID único de la sesión (UUID).
        player_id (str): ID del jugador (FK obligatorio).
        game_id (str): ID de la partida asociada (FK obligatorio).
        started_at (datetime): Momento de inicio de la sesión.
        ended_at (Optional[datetime]): Momento de fin (None si activa).
        platform (Platform): Plataforma del cliente (windows/android).
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
        """Calcula la duración de la sesión en segundos.

        Si la sesión está activa (ended_at=None), calcula
        hasta el momento actual.

        Returns:
            int: Duración en segundos.
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
        """Indica si la sesión sigue activa.

        Returns:
            bool: True si está activa (ended_at es None).
        """
        return self.ended_at is None

    def to_dict(self) -> dict:
        """Convierte la sesión a diccionario para Firestore.

        Returns:
            dict: Representación de la sesión para la BD.
        """
        data = self.model_dump()
        data["started_at"] = self.started_at
        if self.ended_at:
            data["ended_at"] = self.ended_at
        # platform como string para Firestore
        data["platform"] = self.platform.value
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "GameSession":
        """Crea una sesión desde diccionario de Firestore.

        Args:
            data (dict): Diccionario con los datos.

        Returns:
            GameSession: Instancia de la sesión.
        """
        # Convertir platform string a enum si es necesario
        if isinstance(data.get("platform"), str):
            data["platform"] = Platform(data["platform"])
        return cls(**data)
