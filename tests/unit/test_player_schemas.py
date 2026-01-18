"""
Tests unitarios para schemas (DTOs) de Players.

Prueba la validación de datos de entrada/salida de la API.
"""

import pytest
from pydantic import ValidationError

from app.domain.players.models import PlayerStats
from app.domain.players.schemas import PlayerAuthResponse, PlayerCreate, PlayerUpdate


@pytest.mark.unit
class TestPlayerCreate:
    """Tests para el schema PlayerCreate"""

    def test_create_with_username_and_email(self):
        """Crear con username y email válidos"""
        data = PlayerCreate(username="test_player", email="test@example.com")

        assert data.username == "test_player"
        assert data.email == "test@example.com"

    def test_create_with_username_only(self):
        """Crear solo con username (email es opcional)"""
        data = PlayerCreate(username="test_player")

        assert data.username == "test_player"
        assert data.email is None

    @pytest.mark.edge_case
    def test_username_too_short(self):
        """Rechazar username menor a 3 caracteres"""
        with pytest.raises(ValidationError) as exc_info:
            PlayerCreate(username="ab")

        assert "at least 3 characters" in str(exc_info.value)

    @pytest.mark.edge_case
    def test_username_too_long(self):
        """Rechazar username mayor a 20 caracteres"""
        with pytest.raises(ValidationError) as exc_info:
            PlayerCreate(username="a" * 21)

        assert "at most 20 characters" in str(exc_info.value)

    def test_username_minimum_length(self):
        """Username de 3 caracteres exactos (límite mínimo)"""
        data = PlayerCreate(username="abc")
        assert data.username == "abc"

    def test_username_maximum_length(self):
        """Username de 20 caracteres exactos (límite máximo)"""
        username_20 = "a" * 20
        data = PlayerCreate(username=username_20)
        assert data.username == username_20
        assert len(data.username) == 20

    @pytest.mark.edge_case
    def test_missing_username(self):
        """Username es requerido"""
        with pytest.raises(ValidationError) as exc_info:
            PlayerCreate(email="test@example.com")

        assert "username" in str(exc_info.value).lower()
        assert "field required" in str(exc_info.value).lower()

    @pytest.mark.edge_case
    def test_username_with_spaces(self):
        """Username puede contener espacios (no hay validación específica)"""
        data = PlayerCreate(username="test user")
        assert data.username == "test user"

    @pytest.mark.edge_case
    def test_username_with_special_chars(self):
        """Username puede contener caracteres especiales"""
        data = PlayerCreate(username="test_player-123")
        assert data.username == "test_player-123"


@pytest.mark.unit
class TestPlayerUpdate:
    """Tests para el schema PlayerUpdate"""

    def test_update_all_fields_optional(self):
        """Todos los campos son opcionales"""
        # Debe permitir crear sin ningún campo
        data = PlayerUpdate()
        assert data.username is None
        assert data.email is None
        assert data.total_playtime_seconds is None
        assert data.games_played is None
        assert data.games_completed is None
        assert data.stats is None

    def test_update_username_only(self):
        """Actualizar solo username"""
        data = PlayerUpdate(username="new_username")
        assert data.username == "new_username"
        assert data.email is None

    def test_update_stats_only(self):
        """Actualizar solo estadísticas"""
        new_stats = PlayerStats(total_good_choices=10, total_bad_choices=5, moral_alignment=0.33)
        data = PlayerUpdate(stats=new_stats)

        assert data.stats is not None
        assert data.stats.total_good_choices == 10
        assert data.username is None

    def test_update_playtime_and_games(self):
        """Actualizar tiempo de juego y partidas"""
        data = PlayerUpdate(total_playtime_seconds=7200, games_played=10, games_completed=6)

        assert data.total_playtime_seconds == 7200
        assert data.games_played == 10
        assert data.games_completed == 6

    @pytest.mark.edge_case
    def test_update_username_length_validation(self):
        """Validar longitud de username en update"""
        # Username muy corto
        with pytest.raises(ValidationError):
            PlayerUpdate(username="ab")

        # Username muy largo
        with pytest.raises(ValidationError):
            PlayerUpdate(username="a" * 21)

    def test_update_with_all_fields(self):
        """Actualizar todos los campos a la vez"""
        stats = PlayerStats(total_deaths=20)
        data = PlayerUpdate(
            username="updated_user",
            email="updated@example.com",
            total_playtime_seconds=10000,
            games_played=50,
            games_completed=30,
            stats=stats,
        )

        assert data.username == "updated_user"
        assert data.email == "updated@example.com"
        assert data.total_playtime_seconds == 10000
        assert data.games_played == 50
        assert data.games_completed == 30
        assert data.stats.total_deaths == 20

    @pytest.mark.edge_case
    def test_update_with_zero_values(self):
        """Permitir valores en 0 (resetear estadísticas)"""
        data = PlayerUpdate(total_playtime_seconds=0, games_played=0, games_completed=0)

        assert data.total_playtime_seconds == 0
        assert data.games_played == 0
        assert data.games_completed == 0


@pytest.mark.unit
class TestPlayerAuthResponse:
    """Tests para el schema PlayerAuthResponse"""

    def test_create_auth_response(self, player_id, player_token):
        """Crear respuesta de autenticación completa"""
        response = PlayerAuthResponse(
            player_id=player_id, username="test_player", player_token=player_token
        )

        assert response.player_id == player_id
        assert response.username == "test_player"
        assert response.player_token == player_token

    def test_all_fields_required(self):
        """Todos los campos son requeridos"""
        with pytest.raises(ValidationError) as exc_info:
            PlayerAuthResponse(username="test")

        error_msg = str(exc_info.value).lower()
        assert "player_id" in error_msg or "field required" in error_msg

    @pytest.mark.edge_case
    def test_response_with_long_token(self):
        """Permitir tokens largos (UUID)"""
        long_token = "123e4567-e89b-12d3-a456-426614174000"
        response = PlayerAuthResponse(player_id="abc-123", username="test", player_token=long_token)
        assert response.player_token == long_token
