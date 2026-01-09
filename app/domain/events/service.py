"""
Service para Events

TODO: Implementar lógica de negocio de eventos.

Responsabilidades:
- Validar que game_id y player_id existen antes de crear evento
- Validar tipos de eventos permitidos
- Validar estructura de datos según tipo de evento
- Delegar persistencia al repository

Ejemplo de validación:
- Si event_type="player_death", data debe tener: position{x,y}, cause
- Si event_type="npc_interaction", data debe tener: npc_id, interaction_type
"""
pass
