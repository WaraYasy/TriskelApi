"""
Tests unitarios para el servicio de Games.

Prueba la lógica de negocio del GameService.
"""

from datetime import datetime

import pytest

from app.domain.games.schemas import GameCreate, GameUpdate, LevelComplete, LevelStart
from app.domain.games.service import GameService


@pytest.mark.unit
class TestGameServiceCreate:
    """Tests para crear partidas"""

    def test_create_game_success(
        self,
        mock_game_repository,
        mock_player_repository,
        mock_player_service,
        sample_player,
        new_game,
    ):
        """Crear partida exitosamente"""
        # Configurar mocks
        mock_player_repository.get_by_id.return_value = sample_player
        mock_game_repository.get_active_game.return_value = None  # Sin partida activa
        mock_game_repository.create.return_value = new_game

        # Ejecutar
        service = GameService(mock_game_repository, mock_player_repository, mock_player_service)
        game_data = GameCreate(player_id=sample_player.player_id)
        result = service.create_game(game_data)

        # Verificar
        assert result == new_game
        mock_player_repository.get_by_id.assert_called_once()
        mock_game_repository.get_active_game.assert_called_once()
        mock_game_repository.create.assert_called_once()

    @pytest.mark.edge_case
    def test_create_game_player_not_found(
        self, mock_game_repository, mock_player_repository, mock_player_service
    ):
        """Rechazar crear partida si jugador no existe"""
        # Configurar mock: jugador no existe
        mock_player_repository.get_by_id.return_value = None

        # Ejecutar y verificar
        service = GameService(mock_game_repository, mock_player_repository, mock_player_service)
        game_data = GameCreate(player_id="nonexistent-player")

        with pytest.raises(ValueError) as exc_info:
            service.create_game(game_data)

        assert "no encontrado" in str(exc_info.value).lower()
        mock_game_repository.create.assert_not_called()

    @pytest.mark.edge_case
    def test_create_game_already_has_active_game(
        self,
        mock_game_repository,
        mock_player_repository,
        mock_player_service,
        sample_player,
        active_game,
        new_game,
    ):
        """Auto-cierra partida anterior si jugador ya tiene una activa"""
        # Configurar mocks
        mock_player_repository.get_by_id.return_value = sample_player
        mock_game_repository.get_active_game.return_value = active_game
        mock_game_repository.update.return_value = active_game
        mock_game_repository.create.return_value = new_game

        # Ejecutar
        service = GameService(mock_game_repository, mock_player_repository, mock_player_service)
        game_data = GameCreate(player_id=sample_player.player_id)
        result = service.create_game(game_data)

        # Verificar que se cerró la partida anterior automáticamente
        mock_game_repository.update.assert_called_once()
        update_call = mock_game_repository.update.call_args[0]
        assert update_call[0] == active_game.game_id  # ID de partida a actualizar
        assert update_call[1].status == "abandoned"  # Estado de cierre

        # Verificar que se creó la nueva partida
        assert result == new_game
        mock_game_repository.create.assert_called_once()


@pytest.mark.unit
class TestGameServiceLevels:
    """Tests para inicio y completado de niveles"""

    def test_start_level_success(
        self,
        mock_game_repository,
        mock_player_repository,
        mock_player_service,
        active_game,
    ):
        """Iniciar nivel exitosamente"""
        # Configurar mocks
        mock_game_repository.get_by_id.return_value = active_game
        mock_game_repository.start_level.return_value = active_game

        # Ejecutar
        service = GameService(mock_game_repository, mock_player_repository, mock_player_service)
        level_data = LevelStart(level="aquelarre_sombras")
        result = service.start_level(active_game.game_id, level_data)

        # Verificar
        assert result == active_game
        mock_game_repository.start_level.assert_called_once()

    @pytest.mark.edge_case
    def test_start_level_game_not_active(
        self,
        mock_game_repository,
        mock_player_repository,
        mock_player_service,
        completed_game,
    ):
        """Rechazar iniciar nivel si partida no está activa"""
        # Configurar mock: partida completada (no activa)
        mock_game_repository.get_by_id.return_value = completed_game

        # Ejecutar y verificar
        service = GameService(mock_game_repository, mock_player_repository, mock_player_service)
        level_data = LevelStart(level="senda_ebano")

        with pytest.raises(ValueError) as exc_info:
            service.start_level(completed_game.game_id, level_data)

        assert "no está activa" in str(exc_info.value).lower()
        mock_game_repository.start_level.assert_not_called()

    def test_complete_level_success(
        self,
        mock_game_repository,
        mock_player_repository,
        mock_player_service,
        active_game,
    ):
        """Completar nivel exitosamente"""
        # Configurar mocks
        mock_game_repository.get_by_id.return_value = active_game
        mock_game_repository.complete_level.return_value = active_game

        # Ejecutar
        service = GameService(mock_game_repository, mock_player_repository, mock_player_service)
        level_data = LevelComplete(level="fortaleza_gigantes", time_seconds=300, deaths=2)
        result = service.complete_level(active_game.game_id, level_data)

        # Verificar
        assert result == active_game
        mock_game_repository.complete_level.assert_called_once()

    @pytest.mark.edge_case
    def test_complete_boss_level_marks_defeated(
        self,
        mock_game_repository,
        mock_player_repository,
        mock_player_service,
        active_game,
    ):
        """Completar nivel final marca boss_defeated=True"""
        # Configurar mocks
        mock_game_repository.get_by_id.return_value = active_game
        mock_game_repository.complete_level.return_value = active_game
        mock_game_repository.update.return_value = active_game

        # Ejecutar
        service = GameService(mock_game_repository, mock_player_repository, mock_player_service)
        level_data = LevelComplete(
            level="claro_almas", time_seconds=600, deaths=5  # Nivel final (boss)
        )
        service.complete_level(active_game.game_id, level_data)

        # Verificar que se actualizó boss_defeated
        update_calls = mock_game_repository.update.call_args_list
        assert len(update_calls) > 0

        # Verificar que el update incluye boss_defeated=True
        boss_update = update_calls[0][0][1]
        assert boss_update.boss_defeated is True


@pytest.mark.unit
class TestGameServiceFinish:
    """Tests para finalizar partidas"""

    def test_finish_game_completed(
        self,
        mock_game_repository,
        mock_player_repository,
        mock_player_service,
        active_game,
    ):
        """Finalizar partida como completada"""
        # Configurar mocks
        completed = active_game.model_copy()
        completed.status = "completed"
        completed.ended_at = datetime.utcnow()

        mock_game_repository.get_by_id.return_value = active_game
        mock_game_repository.update.return_value = completed

        # Ejecutar
        service = GameService(mock_game_repository, mock_player_repository, mock_player_service)
        result = service.finish_game(active_game.game_id, completed=True)

        # Verificar
        assert result == completed
        mock_player_service.update_player_stats_after_game.assert_called_once()

        # Verificar que se llamó update con status="completed"
        update_call_args = mock_game_repository.update.call_args[0]
        game_update = update_call_args[1]
        assert game_update.status == "completed"
        assert game_update.ended_at is not None

    def test_finish_game_abandoned(
        self,
        mock_game_repository,
        mock_player_repository,
        mock_player_service,
        active_game,
    ):
        """Finalizar partida como abandonada"""
        # Configurar mocks
        abandoned = active_game.model_copy()
        abandoned.status = "abandoned"
        abandoned.ended_at = datetime.utcnow()

        mock_game_repository.get_by_id.return_value = active_game
        mock_game_repository.update.return_value = abandoned

        # Ejecutar
        service = GameService(mock_game_repository, mock_player_repository, mock_player_service)
        service.finish_game(active_game.game_id, completed=False)

        # Verificar status="abandoned"
        update_call_args = mock_game_repository.update.call_args[0]
        game_update = update_call_args[1]
        assert game_update.status == "abandoned"

    def test_update_game_triggers_stats_update(
        self,
        mock_game_repository,
        mock_player_repository,
        mock_player_service,
        active_game,
    ):
        """Actualizar partida a completada actualiza stats del jugador"""
        # Configurar mocks
        completed = active_game.model_copy()
        completed.status = "completed"

        mock_game_repository.get_by_id.return_value = active_game
        mock_game_repository.update.return_value = completed

        # Ejecutar
        service = GameService(mock_game_repository, mock_player_repository, mock_player_service)
        update_data = GameUpdate(status="completed")
        service.update_game(active_game.game_id, update_data)

        # Verificar que se actualizaron las stats del jugador
        mock_player_service.update_player_stats_after_game.assert_called_once()

    def test_update_game_no_stats_update_if_in_progress(
        self,
        mock_game_repository,
        mock_player_repository,
        mock_player_service,
        active_game,
    ):
        """Actualizar partida sin cambiar status NO actualiza stats"""
        # Configurar mocks
        mock_game_repository.get_by_id.return_value = active_game
        mock_game_repository.update.return_value = active_game

        # Ejecutar (actualizar completion_percentage, NO status)
        service = GameService(mock_game_repository, mock_player_repository, mock_player_service)
        update_data = GameUpdate(completion_percentage=50.0)
        service.update_game(active_game.game_id, update_data)

        # Verificar que NO se actualizaron las stats
        mock_player_service.update_player_stats_after_game.assert_not_called()


@pytest.mark.unit
class TestGameServiceGet:
    """Tests para obtener partidas"""

    def test_get_game_exists(
        self,
        mock_game_repository,
        mock_player_repository,
        mock_player_service,
        sample_player,
        active_game,
    ):
        """Obtener partida que existe"""
        mock_game_repository.get_by_id.return_value = active_game

        service = GameService(mock_game_repository, mock_player_repository, mock_player_service)
        result = service.get_game(active_game.game_id)

        assert result == active_game

    def test_get_player_games(
        self,
        mock_game_repository,
        mock_player_repository,
        mock_player_service,
        active_game,
        completed_game,
        player_id,
    ):
        """Obtener todas las partidas de un jugador"""
        mock_game_repository.get_by_player.return_value = [active_game, completed_game]

        service = GameService(mock_game_repository, mock_player_repository, mock_player_service)
        result = service.get_player_games(player_id)

        assert len(result) == 2
        mock_game_repository.get_by_player.assert_called_once_with(
            player_id, limit=100, days=None, since=None, until=None
        )


@pytest.mark.unit
class TestGameServiceDelete:
    """Tests para eliminar partidas"""

    def test_delete_game_success(
        self, mock_game_repository, mock_player_repository, mock_player_service
    ):
        """Eliminar partida exitosamente"""
        mock_game_repository.delete.return_value = True

        service = GameService(mock_game_repository, mock_player_repository, mock_player_service)
        result = service.delete_game("game-123")

        assert result is True
        mock_game_repository.delete.assert_called_once_with("game-123")
