"""
Tests unitarios para el servicio de Sessions.

Prueba la lógica de negocio del SessionService.
"""

import pytest

from app.domain.sessions.models import Platform
from app.domain.sessions.schemas import SessionCreate
from app.domain.sessions.service import SessionService


@pytest.mark.unit
class TestSessionServiceStart:
    """Tests para iniciar sesiones"""

    def test_start_session_success(
        self,
        mock_session_repository,
        mock_player_repository,
        mock_game_repository,
        sample_player,
        active_game,
        sample_session,
    ):
        """Iniciar sesión exitosamente"""
        # Configurar mocks
        mock_player_repository.get_by_id.return_value = sample_player
        mock_game_repository.get_by_id.return_value = active_game
        mock_session_repository.close_stale_sessions.return_value = 0
        mock_session_repository.create.return_value = sample_session

        # Ejecutar
        service = SessionService(
            repository=mock_session_repository,
            player_repo=mock_player_repository,
            game_repo=mock_game_repository,
        )
        session_data = SessionCreate(game_id=active_game.game_id, platform=Platform.WINDOWS)
        result = service.start_session(sample_player.player_id, session_data)

        # Verificar
        assert result == sample_session
        mock_player_repository.get_by_id.assert_called_once()
        mock_game_repository.get_by_id.assert_called_once()
        mock_session_repository.create.assert_called_once()

    @pytest.mark.edge_case
    def test_start_session_player_not_found(
        self,
        mock_session_repository,
        mock_player_repository,
        mock_game_repository,
    ):
        """Rechazar iniciar sesión si jugador no existe"""
        # Configurar mock: jugador no existe
        mock_player_repository.get_by_id.return_value = None

        # Ejecutar y verificar
        service = SessionService(
            repository=mock_session_repository,
            player_repo=mock_player_repository,
            game_repo=mock_game_repository,
        )
        session_data = SessionCreate(game_id="some-game", platform=Platform.WINDOWS)

        with pytest.raises(ValueError) as exc_info:
            service.start_session("nonexistent-player", session_data)

        assert "no encontrado" in str(exc_info.value).lower()
        mock_session_repository.create.assert_not_called()

    @pytest.mark.edge_case
    def test_start_session_game_not_found(
        self,
        mock_session_repository,
        mock_player_repository,
        mock_game_repository,
        sample_player,
    ):
        """Rechazar iniciar sesión si partida no existe"""
        # Configurar mocks
        mock_player_repository.get_by_id.return_value = sample_player
        mock_game_repository.get_by_id.return_value = None

        # Ejecutar y verificar
        service = SessionService(
            repository=mock_session_repository,
            player_repo=mock_player_repository,
            game_repo=mock_game_repository,
        )
        session_data = SessionCreate(game_id="nonexistent-game", platform=Platform.WINDOWS)

        with pytest.raises(ValueError) as exc_info:
            service.start_session(sample_player.player_id, session_data)

        assert "no encontrada" in str(exc_info.value).lower()
        mock_session_repository.create.assert_not_called()

    @pytest.mark.edge_case
    def test_start_session_game_not_owned(
        self,
        mock_session_repository,
        mock_player_repository,
        mock_game_repository,
        sample_player,
        active_game,
    ):
        """Rechazar iniciar sesión si partida no pertenece al jugador"""
        # Modificar game para que pertenezca a otro jugador
        active_game.player_id = "other-player-id"

        # Configurar mocks
        mock_player_repository.get_by_id.return_value = sample_player
        mock_game_repository.get_by_id.return_value = active_game

        # Ejecutar y verificar
        service = SessionService(
            repository=mock_session_repository,
            player_repo=mock_player_repository,
            game_repo=mock_game_repository,
        )
        session_data = SessionCreate(game_id=active_game.game_id, platform=Platform.WINDOWS)

        with pytest.raises(ValueError) as exc_info:
            service.start_session(sample_player.player_id, session_data)

        assert "no pertenece" in str(exc_info.value).lower()
        mock_session_repository.create.assert_not_called()

    def test_start_session_closes_stale_sessions(
        self,
        mock_session_repository,
        mock_player_repository,
        mock_game_repository,
        sample_player,
        active_game,
        sample_session,
    ):
        """Iniciar sesión cierra sesiones huérfanas previas"""
        # Configurar mocks
        mock_player_repository.get_by_id.return_value = sample_player
        mock_game_repository.get_by_id.return_value = active_game
        mock_session_repository.close_stale_sessions.return_value = 2  # 2 cerradas
        mock_session_repository.create.return_value = sample_session

        # Ejecutar
        service = SessionService(
            repository=mock_session_repository,
            player_repo=mock_player_repository,
            game_repo=mock_game_repository,
        )
        session_data = SessionCreate(game_id=active_game.game_id, platform=Platform.WINDOWS)
        service.start_session(sample_player.player_id, session_data)

        # Verificar que se llamó close_stale_sessions
        mock_session_repository.close_stale_sessions.assert_called_once_with(
            sample_player.player_id
        )


@pytest.mark.unit
class TestSessionServiceEnd:
    """Tests para terminar sesiones"""

    def test_end_session_success(
        self,
        mock_session_repository,
        mock_player_repository,
        mock_game_repository,
        sample_session,
        ended_session,
    ):
        """Terminar sesión exitosamente"""
        # Configurar mocks
        mock_session_repository.get_by_id.return_value = sample_session
        mock_session_repository.end_session.return_value = ended_session

        # Ejecutar
        service = SessionService(
            repository=mock_session_repository,
            player_repo=mock_player_repository,
            game_repo=mock_game_repository,
        )
        result = service.end_session(sample_session.session_id, sample_session.player_id)

        # Verificar
        assert result == ended_session
        mock_session_repository.end_session.assert_called_once()

    @pytest.mark.edge_case
    def test_end_session_not_found(
        self,
        mock_session_repository,
        mock_player_repository,
        mock_game_repository,
    ):
        """Retornar None si sesión no existe"""
        # Configurar mock
        mock_session_repository.get_by_id.return_value = None

        # Ejecutar
        service = SessionService(
            repository=mock_session_repository,
            player_repo=mock_player_repository,
            game_repo=mock_game_repository,
        )
        result = service.end_session("nonexistent", "some-player")

        # Verificar
        assert result is None
        mock_session_repository.end_session.assert_not_called()

    @pytest.mark.edge_case
    def test_end_session_not_owned(
        self,
        mock_session_repository,
        mock_player_repository,
        mock_game_repository,
        sample_session,
    ):
        """Rechazar terminar sesión de otro jugador"""
        # Configurar mock
        mock_session_repository.get_by_id.return_value = sample_session

        # Ejecutar y verificar
        service = SessionService(
            repository=mock_session_repository,
            player_repo=mock_player_repository,
            game_repo=mock_game_repository,
        )

        with pytest.raises(ValueError) as exc_info:
            service.end_session(sample_session.session_id, "other-player-id")

        assert "no pertenece" in str(exc_info.value).lower()
        mock_session_repository.end_session.assert_not_called()

    @pytest.mark.edge_case
    def test_end_session_already_ended(
        self,
        mock_session_repository,
        mock_player_repository,
        mock_game_repository,
        ended_session,
    ):
        """Rechazar terminar sesión ya cerrada"""
        # Configurar mock: sesión ya terminada
        mock_session_repository.get_by_id.return_value = ended_session

        # Ejecutar y verificar
        service = SessionService(
            repository=mock_session_repository,
            player_repo=mock_player_repository,
            game_repo=mock_game_repository,
        )

        with pytest.raises(ValueError) as exc_info:
            service.end_session(ended_session.session_id, ended_session.player_id)

        assert "ya esta cerrada" in str(exc_info.value).lower()
        mock_session_repository.end_session.assert_not_called()


@pytest.mark.unit
class TestSessionServiceGet:
    """Tests para obtener sesiones"""

    def test_get_session_exists(
        self,
        mock_session_repository,
        mock_player_repository,
        mock_game_repository,
        sample_session,
    ):
        """Obtener sesión que existe"""
        mock_session_repository.get_by_id.return_value = sample_session

        service = SessionService(
            repository=mock_session_repository,
            player_repo=mock_player_repository,
            game_repo=mock_game_repository,
        )
        result = service.get_session(sample_session.session_id)

        assert result == sample_session

    def test_get_player_sessions(
        self,
        mock_session_repository,
        mock_player_repository,
        mock_game_repository,
        sample_session,
        ended_session,
        player_id,
    ):
        """Obtener todas las sesiones de un jugador"""
        mock_session_repository.get_by_player.return_value = [
            sample_session,
            ended_session,
        ]

        service = SessionService(
            repository=mock_session_repository,
            player_repo=mock_player_repository,
            game_repo=mock_game_repository,
        )
        result = service.get_player_sessions(player_id)

        assert len(result) == 2
        mock_session_repository.get_by_player.assert_called_once_with(player_id, 100)

    def test_get_game_sessions(
        self,
        mock_session_repository,
        mock_player_repository,
        mock_game_repository,
        sample_session,
        game_id,
    ):
        """Obtener todas las sesiones de una partida"""
        mock_session_repository.get_by_game.return_value = [sample_session]

        service = SessionService(
            repository=mock_session_repository,
            player_repo=mock_player_repository,
            game_repo=mock_game_repository,
        )
        result = service.get_game_sessions(game_id)

        assert len(result) == 1
        mock_session_repository.get_by_game.assert_called_once_with(game_id, 100)

    def test_get_active_session(
        self,
        mock_session_repository,
        mock_player_repository,
        mock_game_repository,
        sample_session,
        player_id,
    ):
        """Obtener sesión activa de un jugador"""
        mock_session_repository.get_active_session.return_value = sample_session

        service = SessionService(
            repository=mock_session_repository,
            player_repo=mock_player_repository,
            game_repo=mock_game_repository,
        )
        result = service.get_active_session(player_id)

        assert result == sample_session
        assert result.is_active is True
