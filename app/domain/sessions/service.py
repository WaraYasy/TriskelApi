"""
Service para Sessions

TODO: Implementar lógica de negocio de sesiones.

Responsabilidades:
- Validar que player_id y game_id existen
- Calcular duration_seconds al terminar sesión
- Validar que no haya sesiones duplicadas activas
- Cerrar sesiones automáticamente si quedan abiertas

Flujo típico:
1. Unity abre -> POST /v1/sessions (inicia sesión)
2. Unity cierra -> PATCH /v1/sessions/{id}/end (termina sesión)
3. Si Unity crashea, sesión queda abierta (se puede cerrar automáticamente)
"""

pass
