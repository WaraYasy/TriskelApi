"""
Modelo Pydantic para Player (Jugador)
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime
from uuid import uuid4


class PlayerStats(BaseModel):
    """Estadísticas globales del jugador"""
    total_good_choices: int = 0
    total_bad_choices: int = 0
    total_deaths: int = 0
    favorite_relic: Optional[str] = None  # lirio|hacha|manto|null
    best_speedrun_seconds: Optional[int] = None
    moral_alignment: float = 0.0  # -1.0 (malo) a 1.0 (bueno)


class PlayerCreate(BaseModel):
    """Modelo para crear un jugador (request)"""
    username: str = Field(..., min_length=3, max_length=20)
    email: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "username": "player123",
                "email": "player@example.com"
            }
        }


class Player(BaseModel):
    """Modelo completo de jugador"""
    player_id: str = Field(default_factory=lambda: str(uuid4()))
    username: str = Field(..., min_length=3, max_length=20)
    email: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: datetime = Field(default_factory=datetime.utcnow)
    total_playtime_seconds: int = 0
    games_played: int = 0
    games_completed: int = 0
    stats: PlayerStats = Field(default_factory=PlayerStats)

    class Config:
        json_schema_extra = {
            "example": {
                "player_id": "123e4567-e89b-12d3-a456-426614174000",
                "username": "player123",
                "email": "player@example.com",
                "created_at": "2024-01-15T10:30:00",
                "last_login": "2024-01-15T10:30:00",
                "total_playtime_seconds": 3600,
                "games_played": 5,
                "games_completed": 2,
                "stats": {
                    "total_good_choices": 10,
                    "total_bad_choices": 5,
                    "total_deaths": 25,
                    "favorite_relic": "lirio",
                    "best_speedrun_seconds": 1800,
                    "moral_alignment": 0.5
                }
            }
        }

    def to_dict(self) -> dict:
        """Convierte el modelo a diccionario para Firestore"""
        data = self.model_dump()
        # Convertir datetime a timestamp para Firestore
        data['created_at'] = self.created_at
        data['last_login'] = self.last_login
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Player":
        """Crea un Player desde un diccionario de Firestore"""
        return cls(**data)


class PlayerUpdate(BaseModel):
    """Modelo para actualizar un jugador"""
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
