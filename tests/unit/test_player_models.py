"""
Tests unitarios para modelos de Players.

Prueba la validación de Pydantic y lógica del modelo.
"""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.domain.players.models import Player, PlayerStats


@pytest.mark.unit
class TestPlayerStats:
    """Tests para el modelo PlayerStats"""

    def test_create_default_stats(self):
        """Crear stats con valores por defecto"""
        stats = PlayerStats()

        assert stats.total_good_choices == 0
        assert stats.total_bad_choices == 0
        assert stats.total_deaths == 0
        assert stats.favorite_relic is None
        assert stats.best_speedrun_seconds is None
        assert stats.moral_alignment == 0.0

    def test_create_stats_with_values(self):
        """Crear stats con valores personalizados"""
        stats = PlayerStats(
            total_good_choices=10,
            total_bad_choices=5,
            total_deaths=20,
            favorite_relic="lirio",
            best_speedrun_seconds=3600,
            moral_alignment=0.5,
        )

        assert stats.total_good_choices == 10
        assert stats.total_bad_choices == 5
        assert stats.total_deaths == 20
        assert stats.favorite_relic == "lirio"
        assert stats.best_speedrun_seconds == 3600
        assert stats.moral_alignment == 0.5

    @pytest.mark.edge_case
    def test_moral_alignment_boundaries(self):
        """Validar límites de moral alignment"""
        # Límite inferior válido
        stats_min = PlayerStats(moral_alignment=-1.0)
        assert stats_min.moral_alignment == -1.0

        # Límite superior válido
        stats_max = PlayerStats(moral_alignment=1.0)
        assert stats_max.moral_alignment == 1.0

        # Valor fuera de rango (debe fallar)
        with pytest.raises(ValidationError) as exc_info:
            PlayerStats(moral_alignment=-1.1)
        assert "greater than or equal to -1" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            PlayerStats(moral_alignment=1.1)
        assert "less than or equal to 1" in str(exc_info.value)

    @pytest.mark.edge_case
    def test_negative_values_rejected(self):
        """Rechazar valores negativos en campos que deben ser >= 0"""
        # total_good_choices negativo
        with pytest.raises(ValidationError):
            PlayerStats(total_good_choices=-1)

        # total_bad_choices negativo
        with pytest.raises(ValidationError):
            PlayerStats(total_bad_choices=-1)

        # total_deaths negativo
        with pytest.raises(ValidationError):
            PlayerStats(total_deaths=-5)

        # best_speedrun_seconds negativo
        with pytest.raises(ValidationError):
            PlayerStats(best_speedrun_seconds=-100)

    @pytest.mark.edge_case
    def test_invalid_relic_rejected(self):
        """Rechazar reliquias inválidas"""
        with pytest.raises(ValidationError) as exc_info:
            PlayerStats(favorite_relic="espada")
        assert "Reliquia inválida" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            PlayerStats(favorite_relic="")
        assert "Reliquia inválida" in str(exc_info.value)

    def test_valid_relics_accepted(self):
        """Aceptar las 3 reliquias válidas"""
        stats_lirio = PlayerStats(favorite_relic="lirio")
        assert stats_lirio.favorite_relic == "lirio"

        stats_hacha = PlayerStats(favorite_relic="hacha")
        assert stats_hacha.favorite_relic == "hacha"

        stats_manto = PlayerStats(favorite_relic="manto")
        assert stats_manto.favorite_relic == "manto"

        # None también es válido
        stats_none = PlayerStats(favorite_relic=None)
        assert stats_none.favorite_relic is None


@pytest.mark.unit
class TestPlayer:
    """Tests para el modelo Player"""

    def test_create_player_minimal(self):
        """Crear jugador con datos mínimos requeridos"""
        player = Player(username="test_player", password_hash="test_hash")

        assert player.username == "test_player"
        assert player.email is None
        assert player.games_played == 0
        assert player.games_completed == 0
        assert player.total_playtime_seconds == 0
        assert isinstance(player.stats, PlayerStats)

        # UUIDs generados automáticamente
        assert len(player.player_id) == 36  # UUID v4 format
        assert len(player.player_token) == 36

    def test_create_player_full(self, sample_player):
        """Crear jugador con todos los datos"""
        assert sample_player.username == "test_player"
        assert sample_player.email == "test@example.com"
        assert sample_player.games_played == 10
        assert sample_player.games_completed == 6
        assert sample_player.total_playtime_seconds == 7200
        assert sample_player.stats.total_deaths == 12

    @pytest.mark.edge_case
    def test_games_completed_cannot_exceed_games_played(self):
        """games_completed no puede ser mayor que games_played"""
        with pytest.raises(ValidationError) as exc_info:
            Player(
                username="test",
                password_hash="test_hash",
                games_played=5,
                games_completed=10,  # Mayor que games_played!
            )
        assert "no puede ser mayor que games_played" in str(exc_info.value)

    @pytest.mark.edge_case
    def test_games_completed_equals_games_played(self):
        """games_completed puede ser igual a games_played (100% completado)"""
        player = Player(
            username="perfect_player",
            password_hash="test_hash",
            games_played=10,
            games_completed=10,
        )
        assert player.games_completed == player.games_played

    @pytest.mark.edge_case
    def test_negative_playtime_rejected(self):
        """Rechazar tiempo de juego negativo"""
        with pytest.raises(ValidationError):
            Player(username="test", password_hash="test_hash", total_playtime_seconds=-100)

    @pytest.mark.edge_case
    def test_negative_games_rejected(self):
        """Rechazar contadores de partidas negativos"""
        with pytest.raises(ValidationError):
            Player(username="test", password_hash="test_hash", games_played=-1)

        with pytest.raises(ValidationError):
            Player(username="test", password_hash="test_hash", games_completed=-1)

    def test_player_to_dict(self, sample_player):
        """Convertir Player a diccionario (para Firestore)"""
        player_dict = sample_player.to_dict()

        assert isinstance(player_dict, dict)
        assert player_dict["username"] == "test_player"
        assert player_dict["email"] == "test@example.com"
        assert player_dict["games_played"] == 10
        assert player_dict["games_completed"] == 6

        # Timestamps deben estar presentes
        assert "created_at" in player_dict
        assert "last_login" in player_dict

        # Stats deben estar como dict anidado
        assert isinstance(player_dict["stats"], dict)
        assert player_dict["stats"]["total_deaths"] == 12

    def test_player_from_dict(self, player_dict):
        """Crear Player desde diccionario (de Firestore)"""
        player = Player.from_dict(player_dict)

        assert isinstance(player, Player)
        assert player.username == player_dict["username"]
        assert player.games_played == player_dict["games_played"]

    @pytest.mark.edge_case
    def test_player_with_extreme_playtime(self):
        """Jugador con tiempo de juego extremo (1000 horas)"""
        player = Player(
            username="hardcore_gamer",
            password_hash="test_hash",
            total_playtime_seconds=3_600_000,
        )  # 1000 horas
        assert player.total_playtime_seconds == 3_600_000

    @pytest.mark.edge_case
    def test_player_with_many_games(self):
        """Jugador con muchas partidas"""
        player = Player(
            username="veteran",
            password_hash="test_hash",
            games_played=1000,
            games_completed=750,
        )
        assert player.games_played == 1000
        assert player.games_completed == 750

    def test_timestamps_auto_generated(self):
        """Timestamps se generan automáticamente"""
        player = Player(username="timestamp_test", password_hash="test_hash")

        assert isinstance(player.created_at, datetime)
        assert isinstance(player.last_login, datetime)
        assert player.created_at.tzinfo == timezone.utc
        assert player.last_login.tzinfo == timezone.utc

    def test_player_with_custom_stats(self):
        """Crear jugador con stats personalizadas"""
        custom_stats = PlayerStats(
            total_good_choices=15,
            total_bad_choices=2,
            favorite_relic="hacha",
            moral_alignment=0.88,
        )

        player = Player(username="good_player", password_hash="test_hash", stats=custom_stats)

        assert player.stats.total_good_choices == 15
        assert player.stats.favorite_relic == "hacha"
        assert player.stats.moral_alignment == 0.88
