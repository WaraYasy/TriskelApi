"""
Service para Sessions

Logica de negocio de sesiones de juego.
"""

from typing import List, Optional

from app.core.logger import logger

from ..games.adapters.firestore_repository import FirestoreGameRepository
from ..players.adapters.firestore_repository import FirestorePlayerRepository
from .models import GameSession
from .repository import SessionRepository
from .schemas import SessionCreate


class SessionService:
    """
    Servicio de sesiones de juego.

    Responsabilidades:
    - Validar que player_id y game_id existen
    - Cerrar sesiones huerfanas al iniciar nueva
    - Calcular duracion al terminar
    """

    def __init__(
        self,
        repository: SessionRepository,
        player_repo: Optional[FirestorePlayerRepository] = None,
        game_repo: Optional[FirestoreGameRepository] = None,
    ):
        """Inicializa el servicio con repositorios"""
        self.repository = repository
        self.player_repo = player_repo or FirestorePlayerRepository()
        self.game_repo = game_repo or FirestoreGameRepository()

    def start_session(self, player_id: str, session_data: SessionCreate) -> GameSession:
        """
        Inicia una nueva sesion de juego.

        Validaciones:
        - El jugador debe existir
        - La partida debe existir
        - Cierra sesiones huerfanas previas

        Args:
            player_id: ID del jugador autenticado
            session_data: Datos de la sesion

        Returns:
            GameSession creada

        Raises:
            ValueError: Si el jugador o partida no existen
        """
        # Validar jugador
        player = self.player_repo.get_by_id(player_id)
        if not player:
            raise ValueError(f"Jugador {player_id} no encontrado")

        # Validar partida
        game = self.game_repo.get_by_id(session_data.game_id)
        if not game:
            raise ValueError(f"Partida {session_data.game_id} no encontrada")

        # Validar que la partida pertenece al jugador
        if game.player_id != player_id:
            raise ValueError("La partida no pertenece al jugador")

        # Cerrar sesiones huerfanas
        closed = self.repository.close_stale_sessions(player_id)
        if closed > 0:
            logger.warning(f"Se cerraron {closed} sesiones huerfanas")

        # Crear nueva sesion
        return self.repository.create(player_id, session_data)

    def end_session(self, session_id: str, player_id: str) -> Optional[GameSession]:
        """
        Termina una sesion de juego.

        Args:
            session_id: ID de la sesion a terminar
            player_id: ID del jugador (para validar propiedad)

        Returns:
            GameSession actualizada o None si no existe

        Raises:
            ValueError: Si la sesion no pertenece al jugador o ya esta cerrada
        """
        session = self.repository.get_by_id(session_id)

        if not session:
            return None

        # Validar propiedad
        if session.player_id != player_id:
            raise ValueError("La sesion no pertenece al jugador")

        # Validar que no este ya cerrada
        if not session.is_active:
            raise ValueError("La sesion ya esta cerrada")

        return self.repository.end_session(session_id)

    def get_session(self, session_id: str) -> Optional[GameSession]:
        """Obtiene una sesion por ID"""
        return self.repository.get_by_id(session_id)

    def get_player_sessions(self, player_id: str, limit: int = 100) -> List[GameSession]:
        """Obtiene todas las sesiones de un jugador"""
        return self.repository.get_by_player(player_id, limit)

    def get_game_sessions(self, game_id: str, limit: int = 100) -> List[GameSession]:
        """Obtiene todas las sesiones de una partida"""
        return self.repository.get_by_game(game_id, limit)

    def get_active_session(self, player_id: str) -> Optional[GameSession]:
        """Obtiene la sesion activa de un jugador"""
        return self.repository.get_active_session(player_id)
