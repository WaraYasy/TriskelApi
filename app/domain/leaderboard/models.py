"""
Modelos de dominio para Leaderboard

Los leaderboards son tablas de clasificacion calculadas periodicamente.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class LeaderboardType(str, Enum):
    """Tipos de leaderboard disponibles"""

    SPEEDRUN = "speedrun"  # Menor tiempo = mejor
    MORAL_GOOD = "moral_good"  # Mayor alignment (+1) = mejor
    MORAL_EVIL = "moral_evil"  # Menor alignment (-1) = mejor
    COMPLETIONS = "completions"  # Mayor numero = mejor


class LeaderboardEntry(BaseModel):
    """
    Entrada individual en un leaderboard.

    Representa la posicion de un jugador en la tabla.
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
    """
    Entidad principal: Leaderboard.

    Contiene el ranking completo de un tipo especifico.
    Maximo 100 entradas por leaderboard.
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
        """Convierte el leaderboard a diccionario para Firestore"""
        return {
            "leaderboard_id": self.leaderboard_id.value,
            "updated_at": self.updated_at,
            "entries": [entry.model_dump() for entry in self.entries],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Leaderboard":
        """Crea un leaderboard desde diccionario de Firestore"""
        # Convertir leaderboard_id string a enum
        if isinstance(data.get("leaderboard_id"), str):
            data["leaderboard_id"] = LeaderboardType(data["leaderboard_id"])

        # Convertir entries a objetos LeaderboardEntry
        if "entries" in data:
            data["entries"] = [LeaderboardEntry(**entry) for entry in data["entries"]]

        return cls(**data)
