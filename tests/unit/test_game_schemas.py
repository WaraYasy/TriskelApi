"""
Tests unitarios para schemas de Games.

Prueba la validación de datos de entrada/salida de la API.
"""

import pytest
from pydantic import ValidationError

from app.domain.games.schemas import GameUpdate, LevelComplete


@pytest.mark.unit
class TestGameUpdate:
    """Tests para el schema GameUpdate"""

    @pytest.mark.edge_case
    def test_invalid_status_rejected(self):
        """Rechazar status inválido"""
        with pytest.raises(ValidationError) as exc_info:
            GameUpdate(status="invalid_status")
        assert "no válido" in str(exc_info.value).lower()

    def test_valid_statuses_accepted(self):
        """Aceptar statuses válidos"""
        for status in ["in_progress", "completed", "abandoned"]:
            update = GameUpdate(status=status)
            assert update.status == status

    @pytest.mark.edge_case
    def test_completion_percentage_boundaries(self):
        """Validar límites de completion_percentage"""
        # Válidos
        GameUpdate(completion_percentage=0.0)
        GameUpdate(completion_percentage=50.0)
        GameUpdate(completion_percentage=100.0)

        # Inválidos
        with pytest.raises(ValidationError):
            GameUpdate(completion_percentage=-0.1)

        with pytest.raises(ValidationError):
            GameUpdate(completion_percentage=100.1)

    @pytest.mark.edge_case
    def test_negative_time_rejected(self):
        """Rechazar tiempo total negativo"""
        with pytest.raises(ValidationError):
            GameUpdate(total_time_seconds=-1)


@pytest.mark.unit
class TestLevelComplete:
    """Tests para el schema LevelComplete"""

    def test_level_complete_valid(self):
        """Completar nivel con datos válidos"""
        data = LevelComplete(
            level="senda_ebano",
            time_seconds=300,
            deaths=5,
            choice="sanar",
            relic="lirio",
        )

        assert data.level == "senda_ebano"
        assert data.time_seconds == 300
        assert data.deaths == 5
        assert data.choice == "sanar"
        assert data.relic == "lirio"

    @pytest.mark.edge_case
    def test_time_boundaries(self):
        """Validar límites de tiempo"""
        # Opcional (None) - se calculará automáticamente
        LevelComplete(level="senda_ebano", time_seconds=None, deaths=0)

        # Mínimo válido (debe ser > 0)
        LevelComplete(level="senda_ebano", time_seconds=1, deaths=0)

        # Máximo (24 horas)
        LevelComplete(level="senda_ebano", time_seconds=86400, deaths=0)

        # Excede máximo
        with pytest.raises(ValidationError):
            LevelComplete(level="senda_ebano", time_seconds=86401, deaths=0)

        # Cero no permitido (debe ser > 0)
        with pytest.raises(ValidationError):
            LevelComplete(level="senda_ebano", time_seconds=0, deaths=0)

        # Negativo
        with pytest.raises(ValidationError):
            LevelComplete(level="senda_ebano", time_seconds=-1, deaths=0)

    @pytest.mark.edge_case
    def test_deaths_boundaries(self):
        """Validar límites de muertes"""
        # Mínimo
        LevelComplete(level="senda_ebano", time_seconds=100, deaths=0)

        # Máximo razonable
        LevelComplete(level="senda_ebano", time_seconds=100, deaths=9999)

        # Excede máximo
        with pytest.raises(ValidationError):
            LevelComplete(level="senda_ebano", time_seconds=100, deaths=10000)

        # Negativo
        with pytest.raises(ValidationError):
            LevelComplete(level="senda_ebano", time_seconds=100, deaths=-1)
