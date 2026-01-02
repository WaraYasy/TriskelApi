"""
Modelo Pydantic para Game (Partida)
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from uuid import uuid4


class GameChoices(BaseModel):
    """Decisiones morales en cada nivel"""
    senda_ebano: Optional[str] = None  # forzar|sanar|null
    fortaleza_gigantes: Optional[str] = None  # destruir|construir|null
    aquelarre_sombras: Optional[str] = None  # ocultar|revelar|null


class GameMetrics(BaseModel):
    """Métricas de gameplay"""
    total_deaths: int = 0
    time_per_level: Dict[str, int] = Field(default_factory=dict)
    deaths_per_level: Dict[str, int] = Field(default_factory=dict)


class GameCreate(BaseModel):
    """Modelo para crear una partida (request)"""
    player_id: str

    class Config:
        json_schema_extra = {
            "example": {
                "player_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }


class Game(BaseModel):
    """Modelo completo de partida"""
    game_id: str = Field(default_factory=lambda: str(uuid4()))
    player_id: str
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    status: str = "in_progress"  # in_progress|completed|abandoned
    completion_percentage: float = 0.0
    total_time_seconds: int = 0

    # Progreso
    levels_completed: List[str] = Field(default_factory=list)
    current_level: Optional[str] = None

    # Decisiones y reliquias
    choices: GameChoices = Field(default_factory=GameChoices)
    relics: List[str] = Field(default_factory=list)

    # Resultado
    boss_defeated: bool = False
    npcs_helped: List[str] = Field(default_factory=list)

    # Métricas
    metrics: GameMetrics = Field(default_factory=GameMetrics)

    class Config:
        json_schema_extra = {
            "example": {
                "game_id": "123e4567-e89b-12d3-a456-426614174000",
                "player_id": "player-uuid",
                "started_at": "2024-01-15T10:30:00",
                "status": "in_progress",
                "current_level": "senda_ebano",
                "levels_completed": ["hub_central"],
                "relics": ["lirio"]
            }
        }

    def to_dict(self) -> dict:
        """Convierte el modelo a diccionario para Firestore"""
        data = self.model_dump()
        data['started_at'] = self.started_at
        if self.ended_at:
            data['ended_at'] = self.ended_at
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Game":
        """Crea un Game desde un diccionario de Firestore"""
        return cls(**data)


class GameUpdate(BaseModel):
    """Modelo para actualizar una partida"""
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
    """Modelo para iniciar un nivel"""
    level: str  # hub_central|senda_ebano|fortaleza_gigantes|aquelarre_sombras|claro_almas

    class Config:
        json_schema_extra = {
            "example": {
                "level": "senda_ebano"
            }
        }


class LevelComplete(BaseModel):
    """Modelo para completar un nivel"""
    level: str
    time_seconds: int
    deaths: int
    choice: Optional[str] = None  # Elección moral (si aplica)
    relic: Optional[str] = None  # Reliquia obtenida (si aplica)

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
