"""
Adaptador Firestore para Players

Implementación CONCRETA del repositorio usando Firestore.
Implementa la interfaz IPlayerRepository.
"""

from typing import List, Optional

from google.cloud.firestore_v1 import Client
from google.cloud.firestore_v1.base_query import FieldFilter

from app.core.logger import logger
from app.infrastructure.database.firebase_client import get_firestore_client

from ..models import Player
from ..ports import IPlayerRepository
from ..schemas import PlayerUpdate


class FirestorePlayerRepository(IPlayerRepository):
    """
    Repositorio de Players usando Firestore.

    Esta es la implementación real que habla con la base de datos.
    Implementa todos los métodos definidos en IPlayerRepository.
    """

    COLLECTION_NAME = "players"

    def __init__(self, db: Optional[Client] = None):
        """
        Inicializa el repositorio.

        Args:
            db: Cliente de Firestore (opcional, se obtiene automáticamente)
        """
        self.db = db or get_firestore_client()
        self.collection = self.db.collection(self.COLLECTION_NAME)

    def get_by_id(self, player_id: str) -> Optional[Player]:
        """Obtiene un jugador por su ID"""
        doc_ref = self.collection.document(player_id)
        doc = doc_ref.get()

        if not doc.exists:
            return None

        data = doc.to_dict()
        return Player.from_dict(data)

    def get_by_username(self, username: str) -> Optional[Player]:
        """Obtiene un jugador por su username"""
        # Query en Firestore: WHERE username == X LIMIT 1
        query = self.collection.where(
            filter=FieldFilter("username", "==", username)
        ).limit(1)
        docs = query.stream()

        for doc in docs:
            data = doc.to_dict()
            return Player.from_dict(data)

        return None

    def get_all(self, limit: int = 100) -> List[Player]:
        """Obtiene todos los jugadores (con límite)"""
        docs = self.collection.limit(limit).stream()
        players = []

        for doc in docs:
            data = doc.to_dict()
            players.append(Player.from_dict(data))

        return players

    def update(self, player_id: str, player_update: PlayerUpdate) -> Optional[Player]:
        """
        Actualiza un jugador existente de forma eficiente.

        Solo actualiza los campos que no son None en player_update.
        """
        # Obtener solo los campos que tienen valor (exclude_none=True)
        update_data = player_update.model_dump(exclude_none=True)

        if not update_data:
            # No hay nada que actualizar, retornar el jugador actual
            return self.get_by_id(player_id)

        # Firestore update() falla si el documento no existe
        # Es más eficiente que verificar existencia primero
        try:
            doc_ref = self.collection.document(player_id)
            doc_ref.update(update_data)

            logger.info(
                f"Jugador actualizado: {player_id} - {list(update_data.keys())}"
            )

            # Retornar el jugador actualizado
            return self.get_by_id(player_id)

        except Exception as e:
            # Si el documento no existe, update() lanza excepción
            logger.warning(f"Error actualizando jugador {player_id}: {e}")
            return None

    def delete(self, player_id: str) -> bool:
        """
        Elimina un jugador de Firestore.

        Firestore permite eliminar documentos que no existen sin error,
        así que verificamos existencia primero para retornar el valor correcto.
        """
        doc_ref = self.collection.document(player_id)
        doc = doc_ref.get()

        if not doc.exists:
            logger.warning(f"Intento de eliminar jugador inexistente: {player_id}")
            return False

        doc_ref.delete()
        logger.info(f"Jugador eliminado: {player_id}")
        return True

    def exists(self, player_id: str) -> bool:
        """Verifica si existe un jugador"""
        doc_ref = self.collection.document(player_id)
        return doc_ref.get().exists

    def count(self) -> int:
        """Cuenta el total de jugadores"""
        docs = self.collection.stream()
        return sum(1 for _ in docs)

    def save(self, player: Player) -> Player:
        """
        Guarda un Player ya construido directamente.

        Útil cuando el servicio necesita crear un Player con datos específicos
        (como password hasheado) antes de guardarlo.
        """
        doc_ref = self.collection.document(player.player_id)
        doc_ref.set(player.to_dict())

        logger.info(f"Jugador guardado: {player.player_id} - {player.username}")
        return player
