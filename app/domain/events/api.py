"""
API REST para Events

TODO: Implementar endpoints para eventos de gameplay.

Endpoints sugeridos:
- POST /v1/events - Crear un evento
- POST /v1/events/batch - Crear múltiples eventos (optimización)
- GET /v1/events/game/{game_id} - Obtener eventos de una partida
- GET /v1/events/player/{player_id} - Obtener eventos de un jugador
- GET /v1/events/game/{game_id}/type/{event_type} - Filtrar por tipo

Ejemplo de uso desde Unity:
POST /v1/events
{
  "game_id": "abc-123",
  "player_id": "xyz-789",
  "event_type": "player_death",
  "level": "senda_ebano",
  "data": {
    "position": {"x": 150.5, "y": 200.3},
    "cause": "fall"
  }
}
"""
pass
