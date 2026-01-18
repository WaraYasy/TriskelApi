"""
Fixtures y configuración compartida para todos los tests.

Este archivo contiene:
- Fixtures de datos de prueba (players, games, events)
- Mocks de Firebase y SQL
- Cliente de prueba de FastAPI
- Utilidades de testing
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.domain.auth.service import AuthService
from app.domain.events.models import GameEvent
from app.domain.games.models import Game, GameChoices, GameMetrics
from app.domain.players.models import Player, PlayerStats

# =============================================================================
# FIXTURES DE TIEMPO
# =============================================================================


@pytest.fixture
def fixed_datetime():
    """Timestamp fijo para tests deterministas"""
    return datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def past_datetime():
    """Timestamp del pasado (1 hora atrás)"""
    return datetime.now(timezone.utc) - timedelta(hours=1)


@pytest.fixture
def future_datetime():
    """Timestamp del futuro (1 hora adelante)"""
    return datetime.now(timezone.utc) + timedelta(hours=1)


# =============================================================================
# FIXTURES DE PLAYERS
# =============================================================================


@pytest.fixture
def player_id():
    """ID único para un jugador de prueba"""
    return str(uuid4())


@pytest.fixture
def player_token():
    """Token único para autenticación de jugador"""
    return str(uuid4())


@pytest.fixture
def sample_player_stats() -> PlayerStats:
    """Estadísticas de jugador con valores realistas"""
    return PlayerStats(
        total_good_choices=5,
        total_bad_choices=3,
        total_deaths=12,
        favorite_relic="lirio",
        best_speedrun_seconds=3600,
        moral_alignment=0.25,
    )


@pytest.fixture
def sample_player(player_id, player_token, fixed_datetime, sample_player_stats) -> Player:
    """Jugador completo con estadísticas"""
    return Player(
        player_id=player_id,
        username="test_player",
        email="test@example.com",
        player_token=player_token,
        created_at=fixed_datetime,
        last_login=fixed_datetime,
        total_playtime_seconds=7200,
        games_played=10,
        games_completed=6,
        stats=sample_player_stats,
    )


@pytest.fixture
def new_player(player_id, player_token, fixed_datetime) -> Player:
    """Jugador recién creado sin estadísticas"""
    return Player(
        player_id=player_id,
        username="new_player",
        email="new@example.com",
        player_token=player_token,
        created_at=fixed_datetime,
        last_login=fixed_datetime,
        total_playtime_seconds=0,
        games_played=0,
        games_completed=0,
        stats=PlayerStats(),
    )


@pytest.fixture
def player_dict(sample_player) -> Dict[str, Any]:
    """Diccionario de jugador (formato Firestore)"""
    return sample_player.to_dict()


# =============================================================================
# FIXTURES DE GAMES
# =============================================================================


@pytest.fixture
def game_id():
    """ID único para una partida de prueba"""
    return str(uuid4())


@pytest.fixture
def sample_game_choices() -> GameChoices:
    """Decisiones morales de una partida"""
    return GameChoices(
        senda_ebano="sanar",  # bueno
        fortaleza_gigantes="construir",  # bueno
        aquelarre_sombras=None,  # no decidido aún
    )


@pytest.fixture
def sample_game_metrics() -> GameMetrics:
    """Métricas de una partida"""
    return GameMetrics(
        total_deaths=8,
        time_per_level={"senda_ebano": 1200, "fortaleza_gigantes": 1500},
        deaths_per_level={"senda_ebano": 3, "fortaleza_gigantes": 5},
    )


@pytest.fixture
def active_game(
    game_id, player_id, fixed_datetime, sample_game_choices, sample_game_metrics
) -> Game:
    """Partida en progreso"""
    return Game(
        game_id=game_id,
        player_id=player_id,
        started_at=fixed_datetime,
        ended_at=None,
        status="in_progress",
        completion_percentage=66.67,
        total_time_seconds=2700,
        levels_completed=["senda_ebano", "fortaleza_gigantes"],
        current_level="aquelarre_sombras",
        choices=sample_game_choices,
        relics=["lirio", "hacha"],
        boss_defeated=False,
        npcs_helped=["aldeano_1", "anciano"],
        metrics=sample_game_metrics,
    )


@pytest.fixture
def completed_game(game_id, player_id, fixed_datetime) -> Game:
    """Partida completada exitosamente"""
    ended_at = fixed_datetime + timedelta(hours=1)
    return Game(
        game_id=game_id,
        player_id=player_id,
        started_at=fixed_datetime,
        ended_at=ended_at,
        status="completed",
        completion_percentage=100.0,
        total_time_seconds=3600,
        levels_completed=["senda_ebano", "fortaleza_gigantes", "aquelarre_sombras"],
        current_level=None,
        choices=GameChoices(
            senda_ebano="sanar",
            fortaleza_gigantes="construir",
            aquelarre_sombras="revelar",
        ),
        relics=["lirio", "hacha", "manto"],
        boss_defeated=True,
        npcs_helped=["aldeano_1", "anciano", "guardian"],
        metrics=GameMetrics(
            total_deaths=5,
            time_per_level={
                "senda_ebano": 1200,
                "fortaleza_gigantes": 1500,
                "aquelarre_sombras": 900,
            },
            deaths_per_level={
                "senda_ebano": 2,
                "fortaleza_gigantes": 2,
                "aquelarre_sombras": 1,
            },
        ),
    )


@pytest.fixture
def new_game(game_id, player_id, fixed_datetime) -> Game:
    """Partida recién creada"""
    return Game(
        game_id=game_id,
        player_id=player_id,
        started_at=fixed_datetime,
        status="in_progress",
        completion_percentage=0.0,
        total_time_seconds=0,
    )


@pytest.fixture
def game_dict(active_game) -> Dict[str, Any]:
    """Diccionario de partida (formato Firestore)"""
    return active_game.to_dict()


# =============================================================================
# FIXTURES DE EVENTS
# =============================================================================


@pytest.fixture
def event_id():
    """ID único para un evento de prueba"""
    return str(uuid4())


@pytest.fixture
def sample_event(event_id, game_id, player_id, fixed_datetime) -> GameEvent:
    """Evento de muerte de jugador"""
    return GameEvent(
        event_id=event_id,
        game_id=game_id,
        player_id=player_id,
        timestamp=fixed_datetime,
        event_type="player_death",
        level="senda_ebano",
        data={"position": {"x": 150.5, "y": 200.3}, "cause": "fall", "health": 0},
    )


@pytest.fixture
def level_start_event(event_id, game_id, player_id, fixed_datetime) -> GameEvent:
    """Evento de inicio de nivel"""
    return GameEvent(
        event_id=event_id,
        game_id=game_id,
        player_id=player_id,
        timestamp=fixed_datetime,
        event_type="level_start",
        level="fortaleza_gigantes",
        data={"previous_level": "senda_ebano", "player_health": 100},
    )


@pytest.fixture
def event_dict(sample_event) -> Dict[str, Any]:
    """Diccionario de evento (formato Firestore)"""
    return sample_event.to_dict()


# =============================================================================
# MOCKS DE FIREBASE
# =============================================================================


@pytest.fixture
def mock_firestore_client():
    """Mock del cliente de Firestore"""
    mock_client = MagicMock()

    # Mock de colección
    mock_collection = MagicMock()
    mock_client.collection.return_value = mock_collection

    # Mock de documento
    mock_doc_ref = MagicMock()
    mock_collection.document.return_value = mock_doc_ref

    # Mock de stream (para queries)
    mock_collection.stream.return_value = []

    return mock_client


@pytest.fixture
def mock_firestore_document():
    """Mock de un documento de Firestore"""
    mock_doc = MagicMock()
    mock_doc.id = str(uuid4())
    mock_doc.exists = True
    mock_doc.to_dict.return_value = {}
    return mock_doc


# =============================================================================
# MOCKS DE SQL DATABASE
# =============================================================================


@pytest.fixture
def mock_db_session():
    """Mock de sesión de base de datos SQL"""
    mock_session = MagicMock()
    mock_session.add = MagicMock()
    mock_session.commit = MagicMock()
    mock_session.rollback = MagicMock()
    mock_session.refresh = MagicMock()
    mock_session.query = MagicMock()
    return mock_session


# =============================================================================
# MOCKS DE REPOSITORIES
# =============================================================================


@pytest.fixture
def mock_player_repository():
    """Mock del repositorio de jugadores"""
    mock_repo = MagicMock()
    # Los repositorios son síncronos, no async
    mock_repo.create.return_value = None
    mock_repo.get_by_id.return_value = None
    mock_repo.get_by_username.return_value = None
    mock_repo.update.return_value = None
    mock_repo.delete.return_value = False
    mock_repo.get_all.return_value = []
    return mock_repo


@pytest.fixture
def mock_game_repository():
    """Mock del repositorio de partidas"""
    mock_repo = MagicMock()
    # Los repositorios son síncronos, no async
    mock_repo.create.return_value = None
    mock_repo.get_by_id.return_value = None
    mock_repo.get_by_player.return_value = []
    mock_repo.get_active_game.return_value = None
    mock_repo.update.return_value = None
    mock_repo.delete.return_value = False
    mock_repo.start_level.return_value = None
    mock_repo.complete_level.return_value = None
    return mock_repo


@pytest.fixture
def mock_event_repository():
    """Mock del repositorio de eventos"""
    mock_repo = MagicMock()
    # Los repositorios son síncronos, no async
    mock_repo.create.return_value = None
    mock_repo.create_batch.return_value = []
    mock_repo.get_by_id.return_value = None
    mock_repo.get_by_game.return_value = []
    mock_repo.get_by_player.return_value = []
    mock_repo.get_by_type.return_value = []
    mock_repo.query_events.return_value = []
    return mock_repo


@pytest.fixture
def mock_player_service():
    """Mock del servicio de Players"""
    mock_service = MagicMock()
    mock_service.update_player_stats_after_game.return_value = None
    mock_service.create_player.return_value = None
    mock_service.get_player.return_value = None
    mock_service.update_player.return_value = None
    return mock_service


# =============================================================================
# FIXTURES DE AUTENTICACIÓN
# =============================================================================


@pytest.fixture
def admin_user_data():
    """Datos de usuario administrador"""
    return {
        "id": 1,
        "username": "admin",
        "email": "admin@example.com",
        "role": "admin",
        "is_active": True,
    }


@pytest.fixture
def admin_jwt_token(admin_user_data):
    """Token JWT válido de administrador"""
    service = AuthService(repository=None)
    return service.create_access_token(
        user_id=admin_user_data["id"],
        username=admin_user_data["username"],
        role=admin_user_data["role"],
    )


@pytest.fixture
def expired_jwt_token():
    """Token JWT expirado (para tests de autenticación)"""
    AuthService(repository=None)
    # Crear token con expiración negativa
    from datetime import timedelta

    from jose import jwt

    from app.config.settings import settings

    payload = {
        "user_id": 1,
        "username": "admin",
        "role": "admin",
        "type": "access",
        "exp": datetime.utcnow() - timedelta(hours=1),  # Expirado hace 1 hora
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


@pytest.fixture
def api_key():
    """API Key válida para tests"""
    from app.config.settings import settings

    return settings.api_key


# =============================================================================
# FIXTURES DE API CLIENT
# =============================================================================


@pytest.fixture
def api_client():
    """Cliente de prueba para FastAPI"""
    from app.main import app

    return TestClient(app)


@pytest.fixture
def authenticated_api_client(api_client, admin_jwt_token):
    """Cliente autenticado con JWT"""
    api_client.headers = {"Authorization": f"Bearer {admin_jwt_token}"}
    return api_client


@pytest.fixture
def player_api_client(api_client, player_id, player_token):
    """Cliente autenticado como jugador"""
    api_client.headers = {"X-Player-ID": player_id, "X-Player-Token": player_token}
    return api_client


# =============================================================================
# UTILIDADES DE TESTING
# =============================================================================


@pytest.fixture
def assert_valid_uuid():
    """Helper para validar que un string es un UUID válido"""

    def _assert(value: str) -> bool:
        try:
            uuid4()
            # Intenta convertir a UUID
            from uuid import UUID

            UUID(value)
            return True
        except (ValueError, AttributeError):
            return False

    return _assert


@pytest.fixture
def assert_recent_timestamp():
    """Helper para validar que un timestamp es reciente (últimos 5 minutos)"""

    def _assert(timestamp: datetime) -> bool:
        now = datetime.now(timezone.utc)
        diff = abs((now - timestamp).total_seconds())
        return diff < 300  # 5 minutos

    return _assert


# =============================================================================
# CONFIGURACIÓN DE PYTEST
# =============================================================================


def pytest_configure(config):
    """Configuración global de pytest"""
    # Registrar marcadores personalizados
    config.addinivalue_line("markers", "unit: Tests unitarios de lógica de negocio")
    config.addinivalue_line("markers", "integration: Tests de integración con adapters")
    config.addinivalue_line("markers", "e2e: Tests end-to-end de flujos completos")
    config.addinivalue_line("markers", "slow: Tests que tardan más de 1 segundo")
    config.addinivalue_line("markers", "security: Tests de seguridad y validación")
