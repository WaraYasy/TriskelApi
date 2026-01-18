"""
Ports (Interfaces) del dominio Players

Define el CONTRATO que debe cumplir cualquier repositorio de Players.
El Service solo conoce esta interfaz, no la implementación concreta.

Esto permite:
- Cambiar de Firestore a otra BD sin tocar el Service
- Crear mocks fácilmente para testing
- Desacoplar lógica de negocio de persistencia
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from .models import Player
from .schemas import PlayerCreate, PlayerUpdate


class IPlayerRepository(ABC):
    """
    Interfaz que define las operaciones de persistencia para Players.

    Cualquier implementación (Firestore, PostgreSQL, Mock) debe
    implementar todos estos métodos.
    """

    @abstractmethod
    def create(self, player_data: PlayerCreate) -> Player:
        """
        Crea y guarda un nuevo jugador.

        Args:
            player_data: Datos del jugador a crear

        Returns:
            Player: Jugador creado con su ID generado
        """
        pass

    @abstractmethod
    def get_by_id(self, player_id: str) -> Optional[Player]:
        """
        Busca un jugador por su ID.

        Args:
            player_id: ID único del jugador

        Returns:
            Player si existe, None si no se encuentra
        """
        pass

    @abstractmethod
    def get_by_username(self, username: str) -> Optional[Player]:
        """
        Busca un jugador por su username.

        Args:
            username: Username del jugador

        Returns:
            Player si existe, None si no se encuentra
        """
        pass

    @abstractmethod
    def get_all(self, limit: int = 100) -> List[Player]:
        """
        Obtiene todos los jugadores (con límite).

        Args:
            limit: Número máximo de jugadores a retornar

        Returns:
            Lista de jugadores
        """
        pass

    @abstractmethod
    def update(self, player_id: str, player_update: PlayerUpdate) -> Optional[Player]:
        """
        Actualiza un jugador existente.

        Args:
            player_id: ID del jugador a actualizar
            player_update: Campos a actualizar

        Returns:
            Player actualizado si existe, None si no se encuentra
        """
        pass

    @abstractmethod
    def delete(self, player_id: str) -> bool:
        """
        Elimina un jugador.

        Args:
            player_id: ID del jugador a eliminar

        Returns:
            True si se eliminó, False si no existía
        """
        pass

    @abstractmethod
    def exists(self, player_id: str) -> bool:
        """
        Verifica si existe un jugador.

        Args:
            player_id: ID del jugador

        Returns:
            True si existe, False si no
        """
        pass

    @abstractmethod
    def count(self) -> int:
        """
        Cuenta el total de jugadores.

        Returns:
            Número total de jugadores en la base de datos
        """
        pass
