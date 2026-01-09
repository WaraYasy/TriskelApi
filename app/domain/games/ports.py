"""
Ports (Interfaces) del dominio Games

Define el contrato que debe cumplir cualquier repositorio de Games.
"""
from abc import ABC, abstractmethod
from typing import Optional, List
from .models import Game
from .schemas import GameCreate, GameUpdate, LevelStart, LevelComplete


class IGameRepository(ABC):
    """
    Interfaz para las operaciones de persistencia de Games.

    Cualquier implementación (Firestore, PostgreSQL, Mock) debe
    implementar todos estos métodos.
    """

    @abstractmethod
    def create(self, game_data: GameCreate) -> Game:
        """
        Crea y guarda una nueva partida.

        Args:
            game_data: Datos de la partida a crear

        Returns:
            Game: Partida creada con su ID generado
        """
        pass

    @abstractmethod
    def get_by_id(self, game_id: str) -> Optional[Game]:
        """
        Busca una partida por su ID.

        Args:
            game_id: ID único de la partida

        Returns:
            Game si existe, None si no
        """
        pass

    @abstractmethod
    def get_by_player(self, player_id: str, limit: int = 100) -> List[Game]:
        """
        Obtiene todas las partidas de un jugador.

        Args:
            player_id: ID del jugador
            limit: Máximo número de partidas a retornar

        Returns:
            Lista de partidas del jugador
        """
        pass

    @abstractmethod
    def get_active_game(self, player_id: str) -> Optional[Game]:
        """
        Obtiene la partida activa de un jugador (si existe).

        Una partida activa tiene status="in_progress".
        Regla de negocio: Solo puede haber una partida activa por jugador.

        Args:
            player_id: ID del jugador

        Returns:
            Game si tiene partida activa, None si no
        """
        pass

    @abstractmethod
    def update(self, game_id: str, game_update: GameUpdate) -> Optional[Game]:
        """
        Actualiza una partida existente.

        Args:
            game_id: ID de la partida
            game_update: Campos a actualizar

        Returns:
            Game actualizado si existe, None si no
        """
        pass

    @abstractmethod
    def start_level(self, game_id: str, level_data: LevelStart) -> Optional[Game]:
        """
        Registra el inicio de un nivel.

        Actualiza el campo current_level.

        Args:
            game_id: ID de la partida
            level_data: Datos del nivel iniciado

        Returns:
            Game actualizado si existe, None si no
        """
        pass

    @abstractmethod
    def complete_level(self, game_id: str, level_data: LevelComplete) -> Optional[Game]:
        """
        Registra la completación de un nivel.

        Actualiza:
        - levels_completed (añade el nivel)
        - metrics (tiempo, muertes)
        - choices (decisión moral si aplica)
        - relics (reliquia obtenida si aplica)
        - completion_percentage

        Args:
            game_id: ID de la partida
            level_data: Datos del nivel completado

        Returns:
            Game actualizado si existe, None si no
        """
        pass

    @abstractmethod
    def delete(self, game_id: str) -> bool:
        """
        Elimina una partida.

        Args:
            game_id: ID de la partida

        Returns:
            True si se eliminó, False si no existía
        """
        pass
