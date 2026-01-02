"""
Repositorio para operaciones CRUD de Players en Firestore
"""
from typing import Optional, List
from google.cloud.firestore_v1 import Client
from app.models.player import Player, PlayerCreate, PlayerUpdate
from app.firebase import get_firestore_client


class PlayerRepository:
    """Repositorio para gestionar jugadores en Firestore"""

    COLLECTION_NAME = "players"

    def __init__(self, db: Optional[Client] = None):
        """
        Inicializa el repositorio

        Args:
            db: Cliente de Firestore (opcional, se obtiene automáticamente si no se provee)
        """
        self.db = db or get_firestore_client()
        self.collection = self.db.collection(self.COLLECTION_NAME)

    def create(self, player_data: PlayerCreate) -> Player:
        """
        Crea un nuevo jugador en Firestore

        Args:
            player_data: Datos del jugador a crear

        Returns:
            Player creado con su ID
        """
        # Crear el objeto Player completo
        player = Player(
            username=player_data.username,
            email=player_data.email
        )

        # Guardar en Firestore
        doc_ref = self.collection.document(player.player_id)
        doc_ref.set(player.to_dict())

        print(f"✅ Jugador creado: {player.player_id} - {player.username}")
        return player

    def get_by_id(self, player_id: str) -> Optional[Player]:
        """
        Obtiene un jugador por su ID

        Args:
            player_id: ID del jugador

        Returns:
            Player si existe, None si no se encuentra
        """
        doc_ref = self.collection.document(player_id)
        doc = doc_ref.get()

        if not doc.exists:
            return None

        data = doc.to_dict()
        return Player.from_dict(data)

    def get_by_username(self, username: str) -> Optional[Player]:
        """
        Obtiene un jugador por su username

        Args:
            username: Username del jugador

        Returns:
            Player si existe, None si no se encuentra
        """
        query = self.collection.where("username", "==", username).limit(1)
        docs = query.stream()

        for doc in docs:
            data = doc.to_dict()
            return Player.from_dict(data)

        return None

    def get_all(self, limit: int = 100) -> List[Player]:
        """
        Obtiene todos los jugadores (con límite)

        Args:
            limit: Número máximo de jugadores a retornar

        Returns:
            Lista de jugadores
        """
        docs = self.collection.limit(limit).stream()
        players = []

        for doc in docs:
            data = doc.to_dict()
            players.append(Player.from_dict(data))

        return players

    def update(self, player_id: str, player_update: PlayerUpdate) -> Optional[Player]:
        """
        Actualiza un jugador existente

        Args:
            player_id: ID del jugador
            player_update: Datos a actualizar

        Returns:
            Player actualizado si existe, None si no se encuentra
        """
        doc_ref = self.collection.document(player_id)
        doc = doc_ref.get()

        if not doc.exists:
            return None

        # Obtener solo los campos que no son None
        update_data = player_update.model_dump(exclude_none=True)

        if not update_data:
            # No hay nada que actualizar
            return self.get_by_id(player_id)

        # Actualizar en Firestore
        doc_ref.update(update_data)

        print(f"✅ Jugador actualizado: {player_id}")

        # Retornar el jugador actualizado
        return self.get_by_id(player_id)

    def delete(self, player_id: str) -> bool:
        """
        Elimina un jugador

        Args:
            player_id: ID del jugador

        Returns:
            True si se eliminó, False si no se encontró
        """
        doc_ref = self.collection.document(player_id)
        doc = doc_ref.get()

        if not doc.exists:
            return False

        doc_ref.delete()
        print(f"✅ Jugador eliminado: {player_id}")
        return True

    def exists(self, player_id: str) -> bool:
        """
        Verifica si existe un jugador

        Args:
            player_id: ID del jugador

        Returns:
            True si existe, False si no
        """
        doc_ref = self.collection.document(player_id)
        return doc_ref.get().exists

    def count(self) -> int:
        """
        Cuenta el total de jugadores

        Returns:
            Número total de jugadores
        """
        docs = self.collection.stream()
        return sum(1 for _ in docs)
