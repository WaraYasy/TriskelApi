"""Repositorio para Leaderboard (acceso directo a Firestore).

Cada leaderboard es un documento con el ID igual a su tipo.

Autor: Mandrágora
"""

from typing import List, Optional

from google.cloud.firestore_v1 import Client

from app.core.logger import logger
from app.infrastructure.database.firebase_client import get_firestore_client

from .models import Leaderboard, LeaderboardType


class LeaderboardRepository:
    """Repositorio de leaderboards usando Firestore.

    Estructura en Firestore:
    - Collection: leaderboards.
    - Documents: speedrun, moral_good, moral_evil, completions.
    """

    COLLECTION_NAME = "leaderboards"

    def __init__(self, db: Optional[Client] = None):
        """Inicializa el repositorio."""
        self.db = db or get_firestore_client()
        self.collection = self.db.collection(self.COLLECTION_NAME)

    def get_by_type(self, leaderboard_type: LeaderboardType) -> Optional[Leaderboard]:
        """Obtiene un leaderboard por su tipo.

        Args:
            leaderboard_type (LeaderboardType): Tipo de leaderboard.

        Returns:
            Optional[Leaderboard]: Leaderboard o None si no existe.
        """
        doc_ref = self.collection.document(leaderboard_type.value)
        doc = doc_ref.get()

        if not doc.exists:
            return None

        return Leaderboard.from_dict(doc.to_dict())

    def get_all(self) -> List[Leaderboard]:
        """Obtiene todos los leaderboards.

        Returns:
            List[Leaderboard]: Lista de todos los leaderboards.
        """
        docs = self.collection.stream()

        leaderboards = []
        for doc in docs:
            leaderboards.append(Leaderboard.from_dict(doc.to_dict()))

        return leaderboards

    def save(self, leaderboard: Leaderboard) -> Leaderboard:
        """Guarda o actualiza un leaderboard.

        Args:
            leaderboard (Leaderboard): Leaderboard a guardar.

        Returns:
            Leaderboard: Leaderboard guardado.
        """
        doc_ref = self.collection.document(leaderboard.leaderboard_id.value)
        doc_ref.set(leaderboard.to_dict())

        logger.info(
            f"Leaderboard {leaderboard.leaderboard_id.value} actualizado "
            f"con {len(leaderboard.entries)} entradas"
        )
        return leaderboard

    def initialize_all(self) -> None:
        """Inicializa todos los leaderboards vacíos si no existen.

        Útil para el primer despliegue.
        """
        for lb_type in LeaderboardType:
            if not self.get_by_type(lb_type):
                empty_lb = Leaderboard(leaderboard_id=lb_type, entries=[])
                self.save(empty_lb)
                logger.info(f"Leaderboard {lb_type.value} inicializado")
