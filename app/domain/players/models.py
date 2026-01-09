"""
Modelos de dominio para Players

Estas son las ENTIDADES de negocio (objetos que representan conceptos reales).
Solo contienen lógica de dominio, no validaciones de API.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import uuid4


class PlayerStats(BaseModel):
    """
    Estadísticas globales del jugador.

    Se calculan a partir de todas las partidas completadas.
    """
    total_good_choices: int = 0  # Decisiones morales buenas
    total_bad_choices: int = 0   # Decisiones morales malas
    total_deaths: int = 0         # Muertes acumuladas
    favorite_relic: Optional[str] = None  # lirio | hacha | manto
    best_speedrun_seconds: Optional[int] = None  # Mejor tiempo completando el juego
    moral_alignment: float = 0.0  # De -1.0 (malo) a 1.0 (bueno)


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
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: datetime = Field(default_factory=datetime.utcnow)

    # Estadísticas acumuladas
    total_playtime_seconds: int = 0
    games_played: int = 0
    games_completed: int = 0
    stats: PlayerStats = Field(default_factory=PlayerStats)

    def to_dict(self) -> dict:
        """
        Convierte el Player a diccionario para guardar en Firestore.

        Returns:
            dict: Representación del jugador para la BD
        """
        data = self.model_dump()
        # Los datetime se guardan tal cual (Firestore los maneja)
        data['created_at'] = self.created_at
        data['last_login'] = self.last_login
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
