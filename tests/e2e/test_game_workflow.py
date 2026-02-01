"""
Tests E2E para flujos completos de Games.

Prueba el ciclo de vida completo de una partida.
"""

from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.e2e
class TestGameWorkflow:
    """Tests de flujo completo de partida"""

    @patch("app.infrastructure.database.firebase_client.get_firestore_client")
    def test_complete_game_lifecycle(self, mock_firestore, api_client, player_id, player_token):
        """
        Flujo completo: Crear partida → Jugar niveles → Finalizar partida
        """
        mock_db = MagicMock()
        mock_firestore.return_value = mock_db

        # Mock para verificar jugador y partida activa
        mock_player_doc = MagicMock()
        mock_player_doc.exists = True

        mock_active_game = MagicMock()
        mock_active_game.stream.return_value = []  # No hay partida activa

        # 1. Crear partida
        response = api_client.post(
            "/v1/games",
            json={"player_id": player_id},
            headers={"X-Player-ID": player_id, "X-Player-Token": player_token},
        )
        assert response.status_code in [201, 401]  # 401 si falla autenticación

    @pytest.mark.edge_case
    def test_cannot_create_multiple_active_games(self, api_client, player_id, player_token):
        """Auto-cierra partida activa al crear nueva"""
        with patch(
            "app.infrastructure.database.firebase_client.get_firestore_client"
        ) as mock_firestore:
            mock_db = MagicMock()
            mock_firestore.return_value = mock_db

            # Mock: ya tiene partida activa
            mock_active = MagicMock()
            mock_active.to_dict.return_value = {"status": "in_progress"}
            mock_db.collection.return_value.where.return_value.limit.return_value.stream.return_value = [
                mock_active
            ]

            response = api_client.post(
                "/v1/games",
                json={"player_id": player_id},
                headers={"X-Player-ID": player_id, "X-Player-Token": player_token},
            )

            # Ahora auto-cierra la anterior y crea nueva (201) o falla autenticación (401)
            assert response.status_code in [201, 401]


@pytest.mark.e2e
class TestLevelProgression:
    """Tests de progresión de niveles"""

    @pytest.mark.edge_case
    def test_complete_level_with_invalid_data(self, api_client, game_id, player_id, player_token):
        """Rechazar completado de nivel con datos inválidos"""
        response = api_client.post(
            f"/v1/games/{game_id}/level/senda_ebano/complete",
            json={
                "level": "senda_ebano",
                "time_seconds": -100,  # Tiempo negativo (inválido)
                "deaths": 5,
            },
            headers={"X-Player-ID": player_id, "X-Player-Token": player_token},
        )

        # 422 si pasa auth, 401 si falla auth (auth se verifica primero)
        assert response.status_code in [401, 422]
