"""
Modelos de dominio para Events

TODO: Implementar modelos de eventos de gameplay.

Eventos a registrar:
- player_death: Muerte del jugador (con posición y causa)
- level_start: Inicio de nivel
- level_end: Fin de nivel
- npc_interaction: Interacción con NPC
- item_collected: Item recogido
- custom_event: Eventos personalizados

Estructura sugerida:
class GameEvent(BaseModel):
    event_id: str
    game_id: str
    player_id: str
    timestamp: datetime
    event_type: str  # Tipo de evento
    level: str  # Nivel donde ocurrió
    data: dict  # Datos específicos del evento
"""
pass
