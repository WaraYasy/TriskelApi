# Referencia Rápida de Endpoints - Cuerpos de Request/Response

Una referencia rápida de todos los cuerpos (payloads) de las peticiones y respuestas más importantes de la API.

## Autenticación

### Login
```
POST /v1/players/login

REQUEST:
{
  "username": "jugador123",
  "password": "contraseña123"
}

RESPONSE (200):
{
  "player_id": "550e8400-e29b-41d4-a716-446655440000",
  "player_token": "abc-def-token-secreto",
  "username": "jugador123",
  "active_game_id": "game-uuid-123"  ← Importante: detecta partida activa
}

ERROR (401):
{
  "detail": "Usuario o contraseña incorrectos"
}
```

### Registro
```
POST /v1/players

REQUEST:
{
  "username": "nuevo_jugador",
  "password": "contraseña123",
  "email": "jugador@email.com"  ← Opcional
}

RESPONSE (201):
{
  "player_id": "550e8400-e29b-41d4-a716-446655440000",
  "player_token": "abc-def-token-secreto",
  "username": "nuevo_jugador"
}
```

### Obtener Perfil (Validar sesión)
```
GET /v1/players/me
Headers:
  X-Player-ID: 550e8400-e29b-41d4-a716-446655440000
  X-Player-Token: abc-def-token

RESPONSE (200):
{
  "player_id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "jugador123",
  "email": "jugador@email.com",
  "total_playtime_seconds": 7200,
  "games_played": 5,
  "games_completed": 3,
  "stats": {
    "total_good_choices": 10,
    "total_bad_choices": 5,
    "total_deaths": 20,
    "favorite_relic": "lirio",
    "best_speedrun_seconds": 2400,
    "moral_alignment": 0.33
  }
}
```

---

## Partidas

### Crear Nueva Partida
```
POST /v1/games
Headers:
  X-Player-ID: 550e8400-e29b-41d4-a716-446655440000
  X-Player-Token: abc-def-token

REQUEST:
{}

RESPONSE (201):
{
  "game_id": "game-uuid-123",
  "player_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "in_progress",
  "current_level": "hub_central",
  "started_at": "2024-01-20T10:00:00Z",
  "ended_at": null,
  "total_time_seconds": 0,
  "completion_percentage": 0.0,
  "levels_completed": [],
  "relics": [],
  "boss_defeated": false,
  "npcs_helped": [],
  "choices": {
    "senda_ebano": null,
    "fortaleza_gigantes": null,
    "aquelarre_sombras": null
  },
  "metrics": {
    "total_deaths": 0,
    "time_per_level": {},
    "deaths_per_level": {}
  }
}
```

### Cargar Partida Existente (RETOMAR)
```
GET /v1/games/{game_id}
Headers:
  X-Player-ID: 550e8400-e29b-41d4-a716-446655440000
  X-Player-Token: abc-def-token

RESPONSE (200):
{
  "game_id": "game-uuid-123",
  "player_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "in_progress",
  "current_level": "senda_ebano",        ← Nivel donde estaba
  "started_at": "2024-01-20T10:00:00Z",
  "ended_at": null,
  "total_time_seconds": 1200,             ← Tiempo acumulado (20 min)
  "completion_percentage": 33.3,
  "levels_completed": ["hub_central"],    ← Niveles ya hechos
  "relics": ["lirio"],                    ← Reliquias obtenidas
  "boss_defeated": false,
  "npcs_helped": [],
  "choices": {
    "senda_ebano": "sanar",               ← Decisión ya tomada
    "fortaleza_gigantes": null,
    "aquelarre_sombras": null
  },
  "metrics": {
    "total_deaths": 5,                    ← Muertes en esta partida
    "time_per_level": {
      "hub_central": 120,
      "senda_ebano": 1080
    },
    "deaths_per_level": {
      "hub_central": 0,
      "senda_ebano": 5
    }
  }
}
```

### Guardar Progreso (Durante el juego)
```
PATCH /v1/games/{game_id}
Headers:
  X-Player-ID: 550e8400-e29b-41d4-a716-446655440000
  X-Player-Token: abc-def-token

REQUEST:
{
  "current_level": "senda_ebano",
  "total_time_seconds": 1500,
  "status": "in_progress"
}

RESPONSE (200):
{
  "game_id": "game-uuid-123",
  "current_level": "senda_ebano",
  "total_time_seconds": 1500,
  "status": "in_progress",
  ... otros campos
}
```

### Iniciar Nivel
```
POST /v1/games/{game_id}/level/start
Headers:
  X-Player-ID: 550e8400-e29b-41d4-a716-446655440000
  X-Player-Token: abc-def-token

REQUEST:
{
  "level": "senda_ebano"
}

RESPONSE (200):
{
  "game_id": "game-uuid-123",
  "current_level": "senda_ebano",
  "status": "in_progress",
  "message": "Nivel iniciado correctamente"
}
```

### Completar Nivel
```
POST /v1/games/{game_id}/level/complete
Headers:
  X-Player-ID: 550e8400-e29b-41d4-a716-446655440000
  X-Player-Token: abc-def-token

REQUEST:
{
  "level": "senda_ebano",
  "time_seconds": 580,
  "deaths": 5,
  "relic": "lirio",              ← Puede ser null si no hay reliquia
  "choice": "sanar"              ← Decisión moral (buena o mala)
}

RESPONSE (200):
{
  "game_id": "game-uuid-123",
  "current_level": "senda_ebano",
  "status": "in_progress",
  "levels_completed": ["hub_central", "senda_ebano"],
  "relics": ["lirio"],
  "choices": {
    "senda_ebano": "sanar",
    "fortaleza_gigantes": null,
    "aquelarre_sombras": null
  },
  "completion_percentage": 50.0,
  "metrics": {
    "total_deaths": 5,
    "time_per_level": {
      "hub_central": 120,
      "senda_ebano": 580
    },
    "deaths_per_level": {
      "hub_central": 0,
      "senda_ebano": 5
    }
  }
}
```

### Completar Juego
```
POST /v1/games/{game_id}/complete
Headers:
  X-Player-ID: 550e8400-e29b-41d4-a716-446655440000
  X-Player-Token: abc-def-token

REQUEST:
{}

RESPONSE (200):
{
  "game_id": "game-uuid-123",
  "status": "completed",
  "ended_at": "2024-01-20T12:00:00Z",
  "completion_percentage": 100.0,
  "total_time_seconds": 7200,
  "levels_completed": ["hub_central", "senda_ebano", "fortaleza_gigantes", "aquelarre_sombras"],
  "boss_defeated": true,
  "choices": {
    "senda_ebano": "sanar",
    "fortaleza_gigantes": "construir",
    "aquelarre_sombras": "revelar"
  }
}
```

---

## Sesiones

### Iniciar Sesión de Juego
```
POST /v1/sessions
Headers:
  X-Player-ID: 550e8400-e29b-41d4-a716-446655440000
  X-Player-Token: abc-def-token

REQUEST:
{
  "game_id": "game-uuid-123",
  "platform": "windows"           ← "windows" o "android"
}

RESPONSE (201):
{
  "session_id": "s-session-uuid-456",
  "player_id": "550e8400-e29b-41d4-a716-446655440000",
  "game_id": "game-uuid-123",
  "started_at": "2024-01-20T10:00:00Z",
  "ended_at": null,
  "duration_seconds": 0,
  "platform": "windows",
  "is_active": true
}
```

### Terminar Sesión
```
PATCH /v1/sessions/{session_id}/end
Headers:
  X-Player-ID: 550e8400-e29b-41d4-a716-446655440000
  X-Player-Token: abc-def-token

REQUEST:
{}

RESPONSE (200):
{
  "session_id": "s-session-uuid-456",
  "player_id": "550e8400-e29b-41d4-a716-446655440000",
  "game_id": "game-uuid-123",
  "started_at": "2024-01-20T10:00:00Z",
  "ended_at": "2024-01-20T12:00:00Z",
  "duration_seconds": 7200,
  "platform": "windows",
  "is_active": false
}
```

---

## Eventos

### Crear Evento Individual
```
POST /v1/events
Headers:
  X-Player-ID: 550e8400-e29b-41d4-a716-446655440000
  X-Player-Token: abc-def-token

REQUEST:
{
  "game_id": "game-uuid-123",
  "event_type": "player_death",       ← Tipo de evento
  "level": "senda_ebano",
  "data": {                           ← Datos adicionales opcionales
    "enemy_type": "espectro",
    "position_x": 120.5,
    "position_y": 45.2
  }
}

RESPONSE (201):
{
  "event_id": "event-uuid-789",
  "game_id": "game-uuid-123",
  "event_type": "player_death",
  "level": "senda_ebano",
  "timestamp": "2024-01-20T10:30:15Z",
  "data": {...}
}
```

### Crear Eventos en Batch
```
POST /v1/events/batch
Headers:
  X-Player-ID: 550e8400-e29b-41d4-a716-446655440000
  X-Player-Token: abc-def-token

REQUEST:
{
  "events": [
    {
      "game_id": "game-uuid-123",
      "event_type": "player_death",
      "level": "senda_ebano"
    },
    {
      "game_id": "game-uuid-123",
      "event_type": "item_collected",
      "level": "senda_ebano",
      "data": { "item_name": "lirio" }
    },
    {
      "game_id": "game-uuid-123",
      "event_type": "checkpoint_reached",
      "level": "senda_ebano"
    }
  ]
}

RESPONSE (201):
[
  {
    "event_id": "event-uuid-1",
    "game_id": "game-uuid-123",
    "player_id": "550e8400-e29b-41d4-a716-446655440000",
    "event_type": "player_death",
    "level": "senda_ebano",
    "timestamp": "2024-01-20T10:30:15Z",
    "data": null
  },
  ...
]
```

---

## Tipos de Eventos Disponibles

| event_type | Descripción | Datos recomendados |
|------------|-------------|-------------------|
| `player_death` | Jugador murió | `{"enemy_type": "..."}` |
| `level_start` | Inició nivel | - |
| `level_end` | Terminó nivel | - |
| `npc_interaction` | Interacción con NPC | `{"npc_name": "..."}` |
| `item_collected` | Recogió item | `{"item_name": "..."}` |
| `checkpoint_reached` | Llegó a checkpoint | `{"checkpoint_name": "..."}` |
| `boss_encounter` | Encontró jefe | `{"boss_name": "..."}` |
| `choice_made` | Tomó decisión moral | `{"choice": "sanar"}` |

---

## Reliquias Disponibles

| Nombre | Descripción |
|--------|-------------|
| `lirio` | Lirio Plateado (sanar/revelar) |
| `hacha` | Hacha Forjada (construir) |
| `manto` | Manto Espectral (ocultar) |

---

## Decisiones Morales por Nivel

**Senda del Ébano:**
- `sanar` (buena)
- `forzar` (mala)

**Fortaleza de los Gigantes:**
- `construir` (buena)
- `destruir` (mala)

**Aquelarre de las Sombras:**
- `revelar` (buena)
- `ocultar` (mala)

---

## Niveles Disponibles

| Nombre | Descripción |
|--------|-------------|
| `hub_central` | Hub central (inicio) |
| `senda_ebano` | Senda del Ébano |
| `fortaleza_gigantes` | Fortaleza de los Gigantes |
| `aquelarre_sombras` | Aquelarre de las Sombras |
| `claro_almas` | Claro de las Almas (final) |

---

## Códigos de Error Comunes

| Código | Descripción | Solución |
|--------|-------------|----------|
| 400 | Bad Request | Verifica formato JSON |
| 401 | Unauthorized | Verifica player_id y player_token |
| 403 | Forbidden | No tienes permiso (ej: no es tu partida) |
| 404 | Not Found | Recurso no existe (partida, jugador, etc) |
| 422 | Unprocessable Entity | Datos no válidos |
| 500 | Internal Server Error | Error del servidor |

---

## Ejemplos de Flujo Completo

### Flujo: Nuevo Juego
```
1. POST /v1/players/login → Obtener player_id y player_token
2. POST /v1/games → Crear nueva partida, obtener game_id
3. POST /v1/sessions → Iniciar sesión de tracking, obtener session_id
4. → Juego comienza en hub_central
```

### Flujo: Retomar Juego
```
1. POST /v1/players/login → Obtener player_id y player_token
   ├─ Respuesta incluye active_game_id (si hay partida activa)
2. GET /v1/games/{active_game_id} → Cargar estado completo
   ├─ Restaurar current_level
   ├─ Restaurar relics
   ├─ Restaurar choices
   ├─ Restaurar metrics
3. POST /v1/sessions → Iniciar sesión de tracking
4. → Juego continúa en el nivel guardado
```

### Flujo: Jugar y Guardar
```
1. POST /v1/games/{game_id}/level/start
2. [JUGAR]
3. Cada 30 segundos → PATCH /v1/games/{game_id} (guardar progreso)
4. Cuando completa nivel → POST /v1/games/{game_id}/level/complete
5. Cuando abre siguiente nivel → POST /v1/games/{game_id}/level/start
6. Cuando cierra juego → PATCH /v1/sessions/{session_id}/end
```

### Flujo: Completar Juego
```
1. Usuario derrota jefe final
2. POST /v1/games/{game_id}/complete
   ├─ API actualiza status a "completed"
   ├─ API calcula moral_alignment
   ├─ API actualiza player.games_completed
3. PATCH /v1/sessions/{session_id}/end
4. → Mostrar pantalla de créditos/estadísticas
```
