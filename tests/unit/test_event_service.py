"""
Tests unitarios para el servicio de Events.

Prueba la lógica de negocio del EventService.
"""

import pytest
from unittest.mock import MagicMock

from app.domain.events.service import EventService
from app.domain.events.schemas import EventCreate, EventBatchCreate


@pytest.fixture
def mock_event_service_setup(mock_event_repository, sample_player):
    """Setup completo del EventService con mocks"""
    service = EventService(mock_event_repository)

    # Mock player repository
    service.player_repo = MagicMock()
    service.player_repo.get_by_id.return_value = sample_player

    # Mock game repository
    service.game_repo = MagicMock()

    return service


@pytest.mark.unit
class TestEventServiceCreate:
    """Tests para crear eventos"""

    def test_create_event_success(self, mock_event_service_setup, sample_event, player_id, game_id):
        """Crear evento exitosamente"""
        service = mock_event_service_setup

        # Configurar mock
        service.repository.create.return_value = sample_event

        # Ejecutar
        event_data = EventCreate(
            game_id=game_id,
            player_id=player_id,
            event_type="player_death",
            level="senda_ebano",
            data={"cause": "fall"},
        )
        result = service.create_event(event_data)

        # Verificar
        assert result == sample_event
        service.player_repo.get_by_id.assert_called_once_with(player_id)
        service.repository.create.assert_called_once()

    @pytest.mark.edge_case
    def test_create_event_player_not_found(self, mock_event_repository, player_id, game_id):
        """Rechazar evento si jugador no existe"""
        service = EventService(mock_event_repository)
        service.player_repo = MagicMock()
        service.player_repo.get_by_id.return_value = None  # Jugador no existe

        # Ejecutar y verificar
        event_data = EventCreate(
            game_id=game_id,
            player_id=player_id,
            event_type="player_death",
            level="senda_ebano",
        )

        with pytest.raises(ValueError) as exc_info:
            service.create_event(event_data)

        assert "no encontrado" in str(exc_info.value).lower()
        service.repository.create.assert_not_called()


@pytest.mark.unit
class TestEventServiceBatch:
    """Tests para creación batch de eventos"""

    def test_create_batch_success(self, mock_event_service_setup, player_id, game_id, sample_event):
        """Crear batch de eventos exitosamente"""
        service = mock_event_service_setup

        # Configurar mock
        service.repository.create_batch.return_value = [sample_event, sample_event]

        # Ejecutar
        batch_data = EventBatchCreate(
            events=[
                EventCreate(
                    game_id=game_id,
                    player_id=player_id,
                    event_type="player_death",
                    level="senda_ebano",
                ),
                EventCreate(
                    game_id=game_id,
                    player_id=player_id,
                    event_type="level_start",
                    level="fortaleza_gigantes",
                ),
            ]
        )
        result = service.create_batch(batch_data)

        # Verificar
        assert len(result) == 2
        service.repository.create_batch.assert_called_once()

    @pytest.mark.edge_case
    def test_create_batch_validates_unique_players(self, mock_event_repository, sample_player):
        """Validar jugadores únicos solo una vez en batch"""
        service = EventService(mock_event_repository)
        service.player_repo = MagicMock()
        service.player_repo.get_by_id.return_value = sample_player

        # 3 eventos del mismo jugador
        batch_data = EventBatchCreate(
            events=[
                EventCreate(
                    game_id="game-1",
                    player_id=sample_player.player_id,
                    event_type="player_death",
                    level="senda_ebano",
                ),
                EventCreate(
                    game_id="game-1",
                    player_id=sample_player.player_id,
                    event_type="level_start",
                    level="fortaleza_gigantes",
                ),
                EventCreate(
                    game_id="game-1",
                    player_id=sample_player.player_id,
                    event_type="level_end",
                    level="fortaleza_gigantes",
                ),
            ]
        )

        service.repository.create_batch.return_value = []
        service.create_batch(batch_data)

        # Debe validar el jugador solo 1 vez (no 3)
        assert service.player_repo.get_by_id.call_count == 1


@pytest.mark.unit
class TestEventServiceQuery:
    """Tests para búsqueda de eventos"""

    def test_get_event_by_id(self, mock_event_repository, sample_event):
        """Obtener evento por ID"""
        mock_event_repository.get_by_id.return_value = sample_event

        service = EventService(mock_event_repository)
        result = service.get_event(sample_event.event_id)

        assert result == sample_event

    def test_get_game_events(self, mock_event_repository, sample_event, game_id):
        """Obtener eventos de una partida"""
        mock_event_repository.get_by_game.return_value = [sample_event]

        service = EventService(mock_event_repository)
        result = service.get_game_events(game_id)

        assert len(result) == 1
        mock_event_repository.get_by_game.assert_called_once_with(game_id, 1000)

    def test_get_player_events(self, mock_event_repository, sample_event, player_id):
        """Obtener eventos de un jugador"""
        mock_event_repository.get_by_player.return_value = [sample_event]

        service = EventService(mock_event_repository)
        result = service.get_player_events(player_id)

        assert len(result) == 1
        mock_event_repository.get_by_player.assert_called_once_with(player_id, 1000)

    def test_query_events_with_filters(
        self, mock_event_repository, sample_event, player_id, game_id
    ):
        """Búsqueda de eventos con filtros múltiples"""
        mock_event_repository.query_events.return_value = [sample_event]

        service = EventService(mock_event_repository)
        result = service.query_events(
            game_id=game_id,
            player_id=player_id,
            event_type="player_death",
            level="senda_ebano",
        )

        assert len(result) == 1
        mock_event_repository.query_events.assert_called_once()
