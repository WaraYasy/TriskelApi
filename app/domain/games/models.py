"""
Modelos de dominio para Games

Estas son las entidades de negocio que representan partidas del juego.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from uuid import uuid4


class GameChoices(BaseModel):
    """
    Decisiones morales tomadas en cada nivel.

    Cada nivel tiene una decisión binaria (buena/mala).
    None significa que aún no se ha tomado la decisión.
    """
    senda_ebano: Optional[str] = None          # forzar (malo) | sanar (bueno)
    fortaleza_gigantes: Optional[str] = None   # destruir (malo) | construir (bueno)
    aquelarre_sombras: Optional[str] = None    # ocultar (malo) | revelar (bueno)


class GameMetrics(BaseModel):
    """
    Métricas de gameplay de la partida.

    Registra desempeño del jugador por nivel y global.
    """
    total_deaths: int = 0                          # Muertes totales en toda la partida
    time_per_level: Dict[str, int] = Field(default_factory=dict)  # Segundos por nivel
    deaths_per_level: Dict[str, int] = Field(default_factory=dict)  # Muertes por nivel


class Game(BaseModel):
    """
    Entidad principal: Partida.

    Representa una sesión de juego de un jugador.
    Contiene todo el progreso, decisiones y métricas.
    """
    # Identificación
    game_id: str = Field(default_factory=lambda: str(uuid4()))
    player_id: str  # FK al jugador

    # Timestamps
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None

    # Estado
    status: str = "in_progress"  # in_progress | completed | abandoned
    completion_percentage: float = 0.0
    total_time_seconds: int = 0

    # Progreso
    levels_completed: List[str] = Field(default_factory=list)
    current_level: Optional[str] = None

    # Decisiones y reliquias
    choices: GameChoices = Field(default_factory=GameChoices)
    relics: List[str] = Field(default_factory=list)  # lirio, hacha, manto

    # Resultado
    boss_defeated: bool = False
    npcs_helped: List[str] = Field(default_factory=list)

    # Métricas
    metrics: GameMetrics = Field(default_factory=GameMetrics)

    def to_dict(self) -> dict:
        """
        Convierte el Game a diccionario para guardar en Firestore.

        Returns:
            dict: Representación de la partida para la BD
        """
        data = self.model_dump()
        # Los datetime se guardan tal cual
        data['started_at'] = self.started_at
        if self.ended_at:
            data['ended_at'] = self.ended_at
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Game":
        """
        Crea un Game desde un diccionario de Firestore.

        Args:
            data: Diccionario con los datos de la partida

        Returns:
            Game: Instancia de la partida
        """
        return cls(**data)
