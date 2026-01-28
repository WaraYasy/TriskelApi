"""Modelos de dominio para Leaderboard.

Los leaderboards son tablas de clasificación calculadas periódicamente.

Autor: Mandrágora
"""

from datetime import datetime, timezone
from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class LeaderboardType(str, Enum):
    """Tipos de leaderboard disponibles."""

    SPEEDRUN = "speedrun"  # Menor tiempo = mejor
    MORAL_GOOD = "moral_good"  # Mayor alignment (+1) = mejor
    MORAL_EVIL = "moral_evil"  # Menor alignment (-1) = mejor
    COMPLETIONS = "completions"  # Mayor numero = mejor


class LeaderboardEntry(BaseModel):
    """Entrada individual en un leaderboard.

    Representa la posición de un jugador en la tabla.

    Attributes:
        rank (int): Posición en el ranking (1-100).
        player_id (str): ID del jugador.
        username (str): Nombre del jugador.
        value (float): Valor que determina el ranking.
        game_id (str): ID de la partida donde se logró.
        achieved_at (datetime): Cuándo se logró este valor.
    """

    rank: int = Field(..., ge=1, le=100, description="Posicion en el ranking (1-100)")
    player_id: str = Field(..., description="ID del jugador")
    username: str = Field(..., description="Nombre del jugador")
    value: float = Field(..., description="Valor que determina el ranking")
    game_id: str = Field(..., description="ID de la partida donde se logro")
    achieved_at: datetime = Field(..., description="Cuando se logro este valor")

    class Config:
        json_schema_extra = {
            "example": {
                "rank": 1,
                "player_id": "player-uuid",
                "username": "SpeedRunner99",
                "value": 1234.5,
                "game_id": "game-uuid",
                "achieved_at": "2024-01-15T18:30:00Z",
            }
        }


class Leaderboard(BaseModel):
    """Entidad principal: Leaderboard.

    Contiene el ranking completo de un tipo específico.
    Máximo 100 entradas por leaderboard.

    Attributes:
        leaderboard_id (LeaderboardType): Tipo de leaderboard.
        updated_at (datetime): Última actualización del ranking.
        entries (List[LeaderboardEntry]): Entradas del ranking (max 100).
    """

    leaderboard_id: LeaderboardType = Field(..., description="Tipo de leaderboard")
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Ultima actualizacion del ranking",
    )
    entries: List[LeaderboardEntry] = Field(
        default_factory=list,
        max_length=100,
        description="Entradas del ranking (max 100)",
    )

    def to_dict(self) -> dict:
        """Convierte el leaderboard a diccionario para Firestore.

        Returns:
            dict: Representación del leaderboard para la BD.
        """
        return {
            "leaderboard_id": self.leaderboard_id.value,
            "updated_at": self.updated_at,
            "entries": [entry.model_dump() for entry in self.entries],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Leaderboard":
        """Crea un leaderboard desde diccionario de Firestore.

        Args:
            data (dict): Diccionario con los datos.

        Returns:
            Leaderboard: Instancia del leaderboard.
        """
        # Convertir leaderboard_id string a enum
        if isinstance(data.get("leaderboard_id"), str):
            data["leaderboard_id"] = LeaderboardType(data["leaderboard_id"])

        # Convertir entries a objetos LeaderboardEntry
        if "entries" in data:
            data["entries"] = [LeaderboardEntry(**entry) for entry in data["entries"]]

        return cls(**data)
