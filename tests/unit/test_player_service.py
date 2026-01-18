"""
Tests unitarios para el servicio de Players.

Prueba la lógica de negocio del PlayerService.
"""

import pytest

from app.domain.players.service import PlayerService
from app.domain.players.schemas import PlayerCreate, PlayerUpdate
from app.domain.games.models import Game, GameChoices, GameMetrics


@pytest.mark.unit
class TestPlayerServiceCreate:
    """Tests para crear jugadores"""

    def test_create_player_success(self, mock_player_repository, new_player):
        """Crear jugador exitosamente"""
        # Configurar mocks
        mock_player_repository.get_by_username.return_value = (
            None  # Username disponible
        )
        mock_player_repository.create.return_value = new_player

        # Ejecutar
        service = PlayerService(mock_player_repository)
        player_data = PlayerCreate(username="new_player", email="new@example.com")
        result = service.create_player(player_data)

        # Verificar
        assert result == new_player
        mock_player_repository.get_by_username.assert_called_once_with("new_player")
        mock_player_repository.create.assert_called_once_with(player_data)

    @pytest.mark.edge_case
    def test_create_player_duplicate_username(
        self, mock_player_repository, sample_player
    ):
        """Rechazar username duplicado"""
        # Configurar mock: username ya existe
        mock_player_repository.get_by_username.return_value = sample_player

        # Ejecutar y verificar excepción
        service = PlayerService(mock_player_repository)
        player_data = PlayerCreate(username="test_player")

        with pytest.raises(ValueError) as exc_info:
            service.create_player(player_data)

        assert "ya existe" in str(exc_info.value)
        assert "test_player" in str(exc_info.value)

        # Verificar que NO se llamó a create
        mock_player_repository.create.assert_not_called()


@pytest.mark.unit
class TestPlayerServiceGet:
    """Tests para obtener jugadores"""

    def test_get_player_exists(self, mock_player_repository, sample_player, player_id):
        """Obtener jugador que existe"""
        # Configurar mock
        mock_player_repository.get_by_id.return_value = sample_player

        # Ejecutar
        service = PlayerService(mock_player_repository)
        result = service.get_player(player_id)

        # Verificar
        assert result == sample_player
        mock_player_repository.get_by_id.assert_called_once_with(player_id)

    def test_get_player_not_found(self, mock_player_repository):
        """Obtener jugador que no existe"""
        # Configurar mock
        mock_player_repository.get_by_id.return_value = None

        # Ejecutar
        service = PlayerService(mock_player_repository)
        result = service.get_player("nonexistent-id")

        # Verificar
        assert result is None
        mock_player_repository.get_by_id.assert_called_once()

    def test_get_all_players_default_limit(self, mock_player_repository, sample_player):
        """Listar jugadores con límite por defecto"""
        # Configurar mock
        mock_player_repository.get_all.return_value = [sample_player]

        # Ejecutar
        service = PlayerService(mock_player_repository)
        result = service.get_all_players()

        # Verificar
        assert len(result) == 1
        assert result[0] == sample_player
        mock_player_repository.get_all.assert_called_once_with(limit=100)

    def test_get_all_players_custom_limit(self, mock_player_repository):
        """Listar jugadores con límite personalizado"""
        # Configurar mock
        mock_player_repository.get_all.return_value = []

        # Ejecutar
        service = PlayerService(mock_player_repository)
        service.get_all_players(limit=50)

        # Verificar
        mock_player_repository.get_all.assert_called_once_with(limit=50)


@pytest.mark.unit
class TestPlayerServiceUpdate:
    """Tests para actualizar jugadores"""

    def test_update_player_success(
        self, mock_player_repository, sample_player, player_id
    ):
        """Actualizar jugador exitosamente"""
        # Configurar mocks
        updated_player = sample_player.model_copy()
        updated_player.username = "updated_name"

        mock_player_repository.get_by_id.return_value = sample_player
        mock_player_repository.update.return_value = updated_player

        # Ejecutar
        service = PlayerService(mock_player_repository)
        update_data = PlayerUpdate(username="updated_name")
        result = service.update_player(player_id, update_data)

        # Verificar
        assert result == updated_player
        assert result.username == "updated_name"
        mock_player_repository.update.assert_called_once_with(player_id, update_data)

    def test_update_player_not_found(self, mock_player_repository):
        """Actualizar jugador que no existe"""
        # Configurar mock
        mock_player_repository.get_by_id.return_value = None

        # Ejecutar
        service = PlayerService(mock_player_repository)
        update_data = PlayerUpdate(username="new_name")
        result = service.update_player("nonexistent-id", update_data)

        # Verificar
        assert result is None
        mock_player_repository.update.assert_not_called()


@pytest.mark.unit
class TestPlayerServiceDelete:
    """Tests para eliminar jugadores"""

    def test_delete_player_success(self, mock_player_repository):
        """Eliminar jugador exitosamente"""
        # Configurar mock
        mock_player_repository.delete.return_value = True

        # Ejecutar
        service = PlayerService(mock_player_repository)
        result = service.delete_player("player-123")

        # Verificar
        assert result is True
        mock_player_repository.delete.assert_called_once_with("player-123")

    def test_delete_player_not_found(self, mock_player_repository):
        """Eliminar jugador que no existe"""
        # Configurar mock
        mock_player_repository.delete.return_value = False

        # Ejecutar
        service = PlayerService(mock_player_repository)
        result = service.delete_player("nonexistent-id")

        # Verificar
        assert result is False


@pytest.mark.unit
class TestPlayerStatsUpdate:
    """Tests para actualizar estadísticas después de una partida"""

    def test_update_stats_completed_game(
        self, mock_player_repository, new_player, completed_game, player_id
    ):
        """Actualizar stats después de partida completada"""
        # Configurar mocks
        mock_player_repository.get_by_id.return_value = new_player
        mock_player_repository.update.return_value = new_player

        # Ejecutar
        service = PlayerService(mock_player_repository)
        service.update_player_stats_after_game(player_id, completed_game)

        # Verificar contadores actualizados
        update_call_args = mock_player_repository.update.call_args[0]
        player_update = update_call_args[1]

        assert player_update.games_played == 1
        assert player_update.games_completed == 1
        assert player_update.total_playtime_seconds == 3600
        assert player_update.stats.total_deaths == 5

    def test_update_stats_abandoned_game(
        self, mock_player_repository, new_player, player_id
    ):
        """Actualizar stats después de partida abandonada"""
        # Crear partida abandonada
        abandoned_game = Game(
            game_id="game-123",
            player_id=player_id,
            status="abandoned",
            total_time_seconds=1200,
            metrics=GameMetrics(total_deaths=3),
        )

        # Configurar mocks
        mock_player_repository.get_by_id.return_value = new_player
        mock_player_repository.update.return_value = new_player

        # Ejecutar
        service = PlayerService(mock_player_repository)
        service.update_player_stats_after_game(player_id, abandoned_game)

        # Verificar: partida jugada pero NO completada
        update_call_args = mock_player_repository.update.call_args[0]
        player_update = update_call_args[1]

        assert player_update.games_played == 1
        assert player_update.games_completed == 0  # No cuenta como completada

    @pytest.mark.edge_case
    def test_moral_alignment_all_good_choices(
        self, mock_player_repository, new_player, player_id
    ):
        """Cálculo de alineación moral con todas decisiones buenas"""
        # Partida con todas decisiones buenas
        good_game = Game(
            game_id="game-123",
            player_id=player_id,
            status="completed",
            total_time_seconds=3600,
            choices=GameChoices(
                senda_ebano="sanar",  # bueno
                fortaleza_gigantes="construir",  # bueno
                aquelarre_sombras="revelar",  # bueno
            ),
            metrics=GameMetrics(total_deaths=0),
        )

        # Configurar mocks
        mock_player_repository.get_by_id.return_value = new_player
        mock_player_repository.update.return_value = new_player

        # Ejecutar
        service = PlayerService(mock_player_repository)
        service.update_player_stats_after_game(player_id, good_game)

        # Verificar moral alignment = 1.0 (completamente bueno)
        update_call_args = mock_player_repository.update.call_args[0]
        player_update = update_call_args[1]

        assert player_update.stats.total_good_choices == 3
        assert player_update.stats.total_bad_choices == 0
        assert player_update.stats.moral_alignment == 1.0

    @pytest.mark.edge_case
    def test_moral_alignment_all_bad_choices(
        self, mock_player_repository, new_player, player_id
    ):
        """Cálculo de alineación moral con todas decisiones malas"""
        # Partida con todas decisiones malas
        bad_game = Game(
            game_id="game-123",
            player_id=player_id,
            status="completed",
            total_time_seconds=3600,
            choices=GameChoices(
                senda_ebano="forzar",  # malo
                fortaleza_gigantes="destruir",  # malo
                aquelarre_sombras="ocultar",  # malo
            ),
            metrics=GameMetrics(total_deaths=0),
        )

        # Configurar mocks
        mock_player_repository.get_by_id.return_value = new_player
        mock_player_repository.update.return_value = new_player

        # Ejecutar
        service = PlayerService(mock_player_repository)
        service.update_player_stats_after_game(player_id, bad_game)

        # Verificar moral alignment = -1.0 (completamente malo)
        update_call_args = mock_player_repository.update.call_args[0]
        player_update = update_call_args[1]

        assert player_update.stats.total_good_choices == 0
        assert player_update.stats.total_bad_choices == 3
        assert player_update.stats.moral_alignment == -1.0

    @pytest.mark.edge_case
    def test_moral_alignment_mixed_choices(
        self, mock_player_repository, new_player, player_id
    ):
        """Cálculo de alineación moral con decisiones mixtas"""
        # 2 buenas, 1 mala
        mixed_game = Game(
            game_id="game-123",
            player_id=player_id,
            status="completed",
            total_time_seconds=3600,
            choices=GameChoices(
                senda_ebano="sanar",  # bueno
                fortaleza_gigantes="construir",  # bueno
                aquelarre_sombras="ocultar",  # malo
            ),
            metrics=GameMetrics(total_deaths=0),
        )

        # Configurar mocks
        mock_player_repository.get_by_id.return_value = new_player
        mock_player_repository.update.return_value = new_player

        # Ejecutar
        service = PlayerService(mock_player_repository)
        service.update_player_stats_after_game(player_id, mixed_game)

        # Verificar: (2 - 1) / 3 = 0.333...
        update_call_args = mock_player_repository.update.call_args[0]
        player_update = update_call_args[1]

        assert player_update.stats.total_good_choices == 2
        assert player_update.stats.total_bad_choices == 1
        assert abs(player_update.stats.moral_alignment - 0.333) < 0.01

    @pytest.mark.edge_case
    def test_moral_alignment_no_choices(
        self, mock_player_repository, new_player, player_id
    ):
        """Alineación moral sin decisiones tomadas"""
        # Partida sin decisiones (todos None)
        no_choices_game = Game(
            game_id="game-123",
            player_id=player_id,
            status="abandoned",
            total_time_seconds=100,
            choices=GameChoices(
                senda_ebano=None, fortaleza_gigantes=None, aquelarre_sombras=None
            ),
            metrics=GameMetrics(total_deaths=0),
        )

        # Configurar mocks
        mock_player_repository.get_by_id.return_value = new_player
        mock_player_repository.update.return_value = new_player

        # Ejecutar
        service = PlayerService(mock_player_repository)
        service.update_player_stats_after_game(player_id, no_choices_game)

        # Verificar: moral_alignment se mantiene en 0.0 (neutral)
        update_call_args = mock_player_repository.update.call_args[0]
        player_update = update_call_args[1]

        assert player_update.stats.total_good_choices == 0
        assert player_update.stats.total_bad_choices == 0
        assert player_update.stats.moral_alignment == 0.0

    @pytest.mark.edge_case
    def test_best_speedrun_first_completion(
        self, mock_player_repository, new_player, completed_game, player_id
    ):
        """Primer speedrun establece el record"""
        # Configurar mocks
        mock_player_repository.get_by_id.return_value = new_player
        mock_player_repository.update.return_value = new_player

        # Ejecutar
        service = PlayerService(mock_player_repository)
        service.update_player_stats_after_game(player_id, completed_game)

        # Verificar: primer speedrun
        update_call_args = mock_player_repository.update.call_args[0]
        player_update = update_call_args[1]

        assert player_update.stats.best_speedrun_seconds == 3600

    @pytest.mark.edge_case
    def test_best_speedrun_improved(
        self, mock_player_repository, sample_player, player_id
    ):
        """Mejorar record de speedrun"""
        # Jugador con speedrun existente de 3600s
        sample_player.stats.best_speedrun_seconds = 3600

        # Partida más rápida (2400s)
        faster_game = Game(
            game_id="game-123",
            player_id=player_id,
            status="completed",
            total_time_seconds=2400,
            choices=GameChoices(),
            metrics=GameMetrics(total_deaths=0),
        )

        # Configurar mocks
        mock_player_repository.get_by_id.return_value = sample_player
        mock_player_repository.update.return_value = sample_player

        # Ejecutar
        service = PlayerService(mock_player_repository)
        service.update_player_stats_after_game(player_id, faster_game)

        # Verificar: speedrun mejorado
        update_call_args = mock_player_repository.update.call_args[0]
        player_update = update_call_args[1]

        assert player_update.stats.best_speedrun_seconds == 2400

    @pytest.mark.edge_case
    def test_best_speedrun_not_improved(
        self, mock_player_repository, sample_player, player_id
    ):
        """No actualizar speedrun si no se mejora"""
        # Jugador con speedrun de 3600s
        sample_player.stats.best_speedrun_seconds = 3600

        # Partida más lenta (4800s)
        slower_game = Game(
            game_id="game-123",
            player_id=player_id,
            status="completed",
            total_time_seconds=4800,
            choices=GameChoices(),
            metrics=GameMetrics(total_deaths=0),
        )

        # Configurar mocks
        mock_player_repository.get_by_id.return_value = sample_player
        mock_player_repository.update.return_value = sample_player

        # Ejecutar
        service = PlayerService(mock_player_repository)
        service.update_player_stats_after_game(player_id, slower_game)

        # Verificar: speedrun NO cambia
        update_call_args = mock_player_repository.update.call_args[0]
        player_update = update_call_args[1]

        assert player_update.stats.best_speedrun_seconds == 3600  # Se mantiene

    def test_favorite_relic_updated(
        self, mock_player_repository, new_player, player_id
    ):
        """Actualizar reliquia favorita"""
        game_with_relics = Game(
            game_id="game-123",
            player_id=player_id,
            status="completed",
            total_time_seconds=3600,
            relics=["lirio", "hacha", "manto"],
            choices=GameChoices(),
            metrics=GameMetrics(total_deaths=0),
        )

        # Configurar mocks
        mock_player_repository.get_by_id.return_value = new_player
        mock_player_repository.update.return_value = new_player

        # Ejecutar
        service = PlayerService(mock_player_repository)
        service.update_player_stats_after_game(player_id, game_with_relics)

        # Verificar: última reliquia se marca como favorita
        update_call_args = mock_player_repository.update.call_args[0]
        player_update = update_call_args[1]

        assert player_update.stats.favorite_relic == "manto"  # última

    def test_update_stats_player_not_found(
        self, mock_player_repository, completed_game
    ):
        """Actualizar stats de jugador que no existe"""
        # Configurar mock
        mock_player_repository.get_by_id.return_value = None

        # Ejecutar
        service = PlayerService(mock_player_repository)
        result = service.update_player_stats_after_game(
            "nonexistent-id", completed_game
        )

        # Verificar
        assert result is None
        mock_player_repository.update.assert_not_called()
