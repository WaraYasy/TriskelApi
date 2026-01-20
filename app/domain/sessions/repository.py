"""
Repositorio para Sessions (acceso directo a Firestore)

Arquitectura SIMPLE (sin ports) como Events.
"""

from datetime import datetime, timezone
from typing import List, Optional

from google.cloud.firestore_v1 import Client
from google.cloud.firestore_v1.base_query import FieldFilter

from app.core.logger import logger
from app.infrastructure.database.firebase_client import get_firestore_client

from .models import GameSession
from .schemas import SessionCreate


class SessionRepository:
    """
    Repositorio de sesiones de juego usando Firestore.

    Las sesiones se crean al iniciar y se actualizan al terminar.
    """

    COLLECTION_NAME = "sessions"

    def __init__(self, db: Optional[Client] = None):
        """Inicializa el repositorio"""
        self.db = db or get_firestore_client()
        self.collection = self.db.collection(self.COLLECTION_NAME)

    def create(self, player_id: str, session_data: SessionCreate) -> GameSession:
        """
        Crea una nueva sesion en Firestore.

        Args:
            player_id: ID del jugador autenticado
            session_data: Datos de la sesion a crear

        Returns:
            GameSession: Sesion creada
        """
        session = GameSession(
            player_id=player_id,
            game_id=session_data.game_id,
            platform=session_data.platform,
        )

        doc_ref = self.collection.document(session.session_id)
        doc_ref.set(session.to_dict())

        logger.info(f"Sesion creada: {session.session_id} para jugador {player_id}")
        return session

    def get_by_id(self, session_id: str) -> Optional[GameSession]:
        """Obtiene una sesion por su ID"""
        doc_ref = self.collection.document(session_id)
        doc = doc_ref.get()

        if not doc.exists:
            return None

        return GameSession.from_dict(doc.to_dict())

    def get_by_player(self, player_id: str, limit: int = 100) -> List[GameSession]:
        """
        Obtiene todas las sesiones de un jugador.

        Args:
            player_id: ID del jugador
            limit: Maximo numero de sesiones a retornar

        Returns:
            Lista de sesiones ordenadas por fecha (mas reciente primero)
        """
        query = (
            self.collection.where(filter=FieldFilter("player_id", "==", player_id))
            .order_by("started_at", direction="DESCENDING")
            .limit(limit)
        )
        docs = query.stream()

        sessions = []
        for doc in docs:
            sessions.append(GameSession.from_dict(doc.to_dict()))

        return sessions

    def get_by_game(self, game_id: str, limit: int = 100) -> List[GameSession]:
        """
        Obtiene todas las sesiones de una partida.

        Args:
            game_id: ID de la partida
            limit: Maximo numero de sesiones a retornar

        Returns:
            Lista de sesiones ordenadas por fecha
        """
        query = (
            self.collection.where(filter=FieldFilter("game_id", "==", game_id))
            .order_by("started_at", direction="DESCENDING")
            .limit(limit)
        )
        docs = query.stream()

        sessions = []
        for doc in docs:
            sessions.append(GameSession.from_dict(doc.to_dict()))

        return sessions

    def get_active_session(self, player_id: str) -> Optional[GameSession]:
        """
        Obtiene la sesion activa de un jugador (si existe).

        Una sesion activa tiene ended_at=None.

        Args:
            player_id: ID del jugador

        Returns:
            GameSession activa o None
        """
        query = (
            self.collection.where(filter=FieldFilter("player_id", "==", player_id))
            .where(filter=FieldFilter("ended_at", "==", None))
            .limit(1)
        )
        docs = query.stream()

        for doc in docs:
            return GameSession.from_dict(doc.to_dict())

        return None

    def end_session(self, session_id: str) -> Optional[GameSession]:
        """
        Finaliza una sesion estableciendo ended_at.

        Args:
            session_id: ID de la sesion a finalizar

        Returns:
            GameSession actualizada o None si no existe
        """
        doc_ref = self.collection.document(session_id)
        doc = doc_ref.get()

        if not doc.exists:
            return None

        ended_at = datetime.now(timezone.utc)
        doc_ref.update({"ended_at": ended_at})

        logger.info(f"Sesion finalizada: {session_id}")
        return self.get_by_id(session_id)

    def close_stale_sessions(self, player_id: str) -> int:
        """
        Cierra sesiones que quedaron abiertas (por crash del cliente).

        Args:
            player_id: ID del jugador

        Returns:
            Numero de sesiones cerradas
        """
        query = self.collection.where(
            filter=FieldFilter("player_id", "==", player_id)
        ).where(filter=FieldFilter("ended_at", "==", None))
        docs = query.stream()

        closed_count = 0
        ended_at = datetime.now(timezone.utc)

        for doc in docs:
            doc.reference.update({"ended_at": ended_at})
            closed_count += 1

        if closed_count > 0:
            logger.warning(
                f"Cerradas {closed_count} sesiones huerfanas del jugador {player_id}"
            )

        return closed_count
