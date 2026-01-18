"""
Modelos de dominio para Players

Estas son las ENTIDADES de negocio (objetos que representan conceptos reales).
Solo contienen lógica de dominio, no validaciones de API.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime, timezone
from uuid import uuid4


class PlayerStats(BaseModel):
    """
    Estadísticas globales del jugador.

    Se calculan a partir de todas las partidas completadas.
    """

    total_good_choices: int = Field(default=0, ge=0)  # Decisiones morales buenas (>= 0)
    total_bad_choices: int = Field(default=0, ge=0)  # Decisiones morales malas (>= 0)
    total_deaths: int = Field(default=0, ge=0)  # Muertes acumuladas (>= 0)
    favorite_relic: Optional[str] = None  # lirio | hacha | manto
    best_speedrun_seconds: Optional[int] = Field(default=None, ge=0)  # Mejor tiempo (>= 0)
    moral_alignment: float = Field(default=0.0, ge=-1.0, le=1.0)  # De -1.0 (malo) a 1.0 (bueno)

    @field_validator("favorite_relic")
    @classmethod
    def validate_relic(cls, v: Optional[str]) -> Optional[str]:
        """Valida que la reliquia sea una de las permitidas"""
        if v is not None and v not in ["lirio", "hacha", "manto"]:
            raise ValueError(f"Reliquia inválida: {v}. Debe ser: lirio, hacha o manto")
        return v


class Player(BaseModel):
    """
    Entidad principal: Jugador.

    Representa un usuario que juega Triskel.
    Contiene su perfil y estadísticas agregadas de todas sus partidas.
    """

    # Identificación
    player_id: str = Field(default_factory=lambda: str(uuid4()))
    username: str
    email: Optional[str] = None
    player_token: str = Field(default_factory=lambda: str(uuid4()))

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Estadísticas acumuladas
    total_playtime_seconds: int = Field(default=0, ge=0)  # Tiempo total >= 0
    games_played: int = Field(default=0, ge=0)  # Partidas jugadas >= 0
    games_completed: int = Field(default=0, ge=0)  # Partidas completadas >= 0
    stats: PlayerStats = Field(default_factory=PlayerStats)

    @field_validator("games_completed")
    @classmethod
    def validate_games_completed(cls, v: int, info) -> int:
        """Valida que games_completed no sea mayor que games_played"""
        # info.data contiene los valores de los campos ya validados
        games_played = info.data.get("games_played", 0)
        if v > games_played:
            raise ValueError(
                f"games_completed ({v}) no puede ser mayor que games_played ({games_played})"
            )
        return v

    def to_dict(self) -> dict:
        """
        Convierte el Player a diccionario para guardar en Firestore.

        Returns:
            dict: Representación del jugador para la BD
        """
        data = self.model_dump()
        # Los datetime se guardan tal cual (Firestore los maneja)
        data["created_at"] = self.created_at
        data["last_login"] = self.last_login
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Player":
        """
        Crea un Player desde un diccionario de Firestore.

        Args:
            data: Diccionario con los datos del jugador

        Returns:
            Player: Instancia del jugador
        """
        return cls(**data)
