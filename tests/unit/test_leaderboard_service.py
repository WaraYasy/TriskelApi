"""
Tests unitarios para el servicio de Leaderboard.

Prueba la lógica de negocio del LeaderboardService.
"""

import pytest

from app.domain.leaderboard.models import LeaderboardType
from app.domain.leaderboard.service import (
    LEADERBOARD_DESCRIPTIONS,
    LEADERBOARD_NAMES,
    LeaderboardService,
)


@pytest.mark.unit
class TestLeaderboardServiceGet:
    """Tests para obtener leaderboards"""

    def test_get_leaderboard_exists(
        self,
        mock_leaderboard_repository,
        mock_player_repository,
        mock_game_repository,
        sample_leaderboard,
    ):
        """Obtener leaderboard que existe"""
        mock_leaderboard_repository.get_by_type.return_value = sample_leaderboard

        service = LeaderboardService(
            repository=mock_leaderboard_repository,
            player_repo=mock_player_repository,
            game_repo=mock_game_repository,
        )
        result = service.get_leaderboard(LeaderboardType.SPEEDRUN)

        assert result == sample_leaderboard
        mock_leaderboard_repository.get_by_type.assert_called_once_with(
            LeaderboardType.SPEEDRUN
        )

    def test_get_leaderboard_not_found(
        self,
        mock_leaderboard_repository,
        mock_player_repository,
        mock_game_repository,
    ):
        """Retornar None si leaderboard no existe"""
        mock_leaderboard_repository.get_by_type.return_value = None

        service = LeaderboardService(
            repository=mock_leaderboard_repository,
            player_repo=mock_player_repository,
            game_repo=mock_game_repository,
        )
        result = service.get_leaderboard(LeaderboardType.SPEEDRUN)

        assert result is None

    def test_get_all_leaderboards_info(
        self,
        mock_leaderboard_repository,
        mock_player_repository,
        mock_game_repository,
    ):
        """Obtener información de todos los tipos de leaderboard"""
        service = LeaderboardService(
            repository=mock_leaderboard_repository,
            player_repo=mock_player_repository,
            game_repo=mock_game_repository,
        )
        result = service.get_all_leaderboards_info()

        # Verificar que incluye todos los tipos
        assert len(result) == 4
        ids = [lb["leaderboard_id"] for lb in result]
        assert "speedrun" in ids
        assert "moral_good" in ids
        assert "moral_evil" in ids
        assert "completions" in ids

        # Verificar estructura
        for lb in result:
            assert "leaderboard_id" in lb
            assert "name" in lb
            assert "description" in lb


@pytest.mark.unit
class TestLeaderboardServiceRefresh:
    """Tests para recalcular leaderboards"""

    def test_refresh_all_leaderboards_no_players(
        self,
        mock_leaderboard_repository,
        mock_player_repository,
        mock_game_repository,
    ):
        """Recalcular leaderboards sin jugadores elegibles"""
        # Sin jugadores con partidas completadas
        mock_player_repository.get_all.return_value = []

        service = LeaderboardService(
            repository=mock_leaderboard_repository,
            player_repo=mock_player_repository,
            game_repo=mock_game_repository,
        )
        result = service.refresh_all_leaderboards()

        # Verificar que se actualizaron los 4 leaderboards
        assert len(result) == 4
        assert "speedrun" in result
        assert "moral_good" in result
        assert "moral_evil" in result
        assert "completions" in result

        # Verificar que se guardaron (aunque vacíos)
        assert mock_leaderboard_repository.save.call_count == 4

    def test_refresh_all_leaderboards_with_players(
        self,
        mock_leaderboard_repository,
        mock_player_repository,
        mock_game_repository,
        sample_player,
        completed_game,
    ):
        """Recalcular leaderboards con jugadores elegibles"""
        # Jugador con partida completada
        mock_player_repository.get_all.return_value = [sample_player]
        mock_game_repository.get_by_player.return_value = [completed_game]

        service = LeaderboardService(
            repository=mock_leaderboard_repository,
            player_repo=mock_player_repository,
            game_repo=mock_game_repository,
        )
        result = service.refresh_all_leaderboards()

        # Verificar que se actualizaron los 4 leaderboards
        assert len(result) == 4

        # Verificar que se guardaron
        assert mock_leaderboard_repository.save.call_count == 4

    def test_refresh_filters_players_without_completions(
        self,
        mock_leaderboard_repository,
        mock_player_repository,
        mock_game_repository,
        sample_player,
        new_player,
    ):
        """Solo incluir jugadores con games_completed > 0"""
        # sample_player tiene games_completed=6, new_player tiene 0
        mock_player_repository.get_all.return_value = [sample_player, new_player]
        mock_game_repository.get_by_player.return_value = []

        service = LeaderboardService(
            repository=mock_leaderboard_repository,
            player_repo=mock_player_repository,
            game_repo=mock_game_repository,
        )
        service.refresh_all_leaderboards()

        # Verificar que get_by_player solo se llamó para sample_player
        # (se llama 4 veces por los 4 tipos de leaderboard)
        calls = mock_game_repository.get_by_player.call_args_list
        player_ids_called = [call[0][0] for call in calls]

        # Solo sample_player tiene games_completed > 0
        assert all(pid == sample_player.player_id for pid in player_ids_called)


@pytest.mark.unit
class TestLeaderboardNames:
    """Tests para constantes de nombres"""

    def test_all_types_have_names(self):
        """Todos los tipos tienen nombre definido"""
        for lb_type in LeaderboardType:
            assert lb_type in LEADERBOARD_NAMES
            assert isinstance(LEADERBOARD_NAMES[lb_type], str)
            assert len(LEADERBOARD_NAMES[lb_type]) > 0

    def test_all_types_have_descriptions(self):
        """Todos los tipos tienen descripción definida"""
        for lb_type in LeaderboardType:
            assert lb_type in LEADERBOARD_DESCRIPTIONS
            assert isinstance(LEADERBOARD_DESCRIPTIONS[lb_type], str)
            assert len(LEADERBOARD_DESCRIPTIONS[lb_type]) > 0


@pytest.mark.unit
class TestLeaderboardModels:
    """Tests para modelos de leaderboard"""

    def test_leaderboard_entry_valid(self, sample_leaderboard_entry):
        """Entrada de leaderboard válida"""
        assert sample_leaderboard_entry.rank == 1
        assert sample_leaderboard_entry.value == 3600.0
        assert sample_leaderboard_entry.username == "test_player"

    def test_leaderboard_valid(self, sample_leaderboard):
        """Leaderboard válido"""
        assert sample_leaderboard.leaderboard_id == LeaderboardType.SPEEDRUN
        assert len(sample_leaderboard.entries) == 1

    def test_leaderboard_to_dict(self, sample_leaderboard):
        """Conversión a diccionario para Firestore"""
        data = sample_leaderboard.to_dict()

        assert data["leaderboard_id"] == "speedrun"
        assert "updated_at" in data
        assert "entries" in data
        assert len(data["entries"]) == 1

    def test_leaderboard_from_dict(self, sample_leaderboard):
        """Creación desde diccionario de Firestore"""
        from app.domain.leaderboard.models import Leaderboard

        data = sample_leaderboard.to_dict()
        restored = Leaderboard.from_dict(data)

        assert restored.leaderboard_id == sample_leaderboard.leaderboard_id
        assert len(restored.entries) == len(sample_leaderboard.entries)
