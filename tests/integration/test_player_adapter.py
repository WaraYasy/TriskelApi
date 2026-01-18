"""
Tests de integración para el adapter de Players con Firestore.

Prueba la interacción entre el adapter y el mock de Firestore.
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from app.domain.players.adapters.firestore_repository import FirestorePlayerRepository
from app.domain.players.schemas import PlayerCreate, PlayerUpdate
from app.domain.players.models import Player, PlayerStats


@pytest.mark.integration
@pytest.mark.requires_firebase
class TestFirestorePlayerRepository:
    """Tests para el repositorio de Players con Firestore"""

    @pytest.fixture
    def repository(self, mock_firestore_client):
        """Repositorio con mock de Firestore"""
        with patch('app.domain.players.adapters.firestore_repository.get_firestore_client', return_value=mock_firestore_client):
            repo = FirestorePlayerRepository()
            return repo

    def test_create_player(self, repository, mock_firestore_client):
        """Crear jugador en Firestore"""
        # Configurar mocks
        mock_doc_ref = MagicMock()
        mock_firestore_client.collection.return_value.document.return_value = mock_doc_ref

        # Ejecutar
        player_data = PlayerCreate(username="test_player", email="test@example.com")
        result = repository.create(player_data)

        # Verificar
        assert result.username == "test_player"
        assert result.email == "test@example.com"

        # Verificar que se llamó a Firestore
        mock_firestore_client.collection.assert_called_with('players')
        mock_doc_ref.set.assert_called_once()

    def test_get_by_id_exists(self, repository, mock_firestore_client, sample_player):
        """Obtener jugador por ID que existe"""
        # Configurar mock
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = sample_player.to_dict()

        mock_firestore_client.collection.return_value.document.return_value.get.return_value = mock_doc

        # Ejecutar
        result = repository.get_by_id(sample_player.player_id)

        # Verificar
        assert result is not None
        assert result.username == sample_player.username

    def test_get_by_id_not_found(self, repository, mock_firestore_client):
        """Obtener jugador que no existe"""
        # Configurar mock
        mock_doc = MagicMock()
        mock_doc.exists = False

        mock_firestore_client.collection.return_value.document.return_value.get.return_value = mock_doc

        # Ejecutar
        result = repository.get_by_id("nonexistent-id")

        # Verificar
        assert result is None

    def test_update_player(self, repository, mock_firestore_client, sample_player):
        """Actualizar jugador existente"""
        # Configurar mocks
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = sample_player.to_dict()

        mock_doc_ref = MagicMock()
        mock_doc_ref.get.return_value = mock_doc

        mock_firestore_client.collection.return_value.document.return_value = mock_doc_ref

        # Ejecutar
        update_data = PlayerUpdate(total_playtime_seconds=10000)
        result = repository.update(sample_player.player_id, update_data)

        # Verificar
        assert result is not None
        mock_doc_ref.update.assert_called_once()

    @pytest.mark.edge_case
    def test_delete_player(self, repository, mock_firestore_client):
        """Eliminar jugador"""
        # Configurar mock
        mock_doc_ref = MagicMock()
        mock_firestore_client.collection.return_value.document.return_value = mock_doc_ref

        # Ejecutar
        result = repository.delete("player-123")

        # Verificar
        assert result is True
        mock_doc_ref.delete.assert_called_once()
