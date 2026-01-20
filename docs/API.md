# Documentacion de API - Triskel

Esta documentacion describe todos los endpoints disponibles en la API de Triskel, sus parametros, respuestas y ejemplos de uso.

**URL Base**: `https://triskel-api.railway.app` (produccion) o `http://localhost:8000` (desarrollo)

---

## Tabla de Contenidos

1. [Autenticacion](#autenticacion)
2. [Endpoints Generales](#endpoints-generales)
3. [Players](#players)
4. [Games](#games)
5. [Events](#events)
6. [Auth (Administradores)](#auth-administradores)
7. [Dashboard Web](#dashboard-web)
8. [Codigos de Estado](#codigos-de-estado)

---

## Autenticacion

La API soporta 3 metodos de autenticacion:

### 1. Player Token (Jugadores)
Para jugadores del videojuego:
```
X-Player-ID: <player_id>
X-Player-Token: <player_token>
```

### 2. JWT Bearer (Administradores)
Para administradores del dashboard:
```
Authorization: Bearer <jwt_token>
```

### 3. API Key (Administracion programatica)
Para scripts y herramientas de administracion:
```
X-API-Key: <api_key>
```

---

## Endpoints Generales

### GET /

Informacion general de la API.

**Autenticacion**: No requiere

**Respuesta**: `200 OK`
```json
{
  "message": "Triskel API - API REST para el videojuego Triskel",
  "version": "1.0.0",
  "docs": "/docs",
  "health": "/health"
}
```

---

### GET /health

Health check para monitoreo.

**Autenticacion**: No requiere

**Respuesta**: `200 OK`
```json
{
  "status": "healthy",
  "timestamp": "2026-01-18T10:30:00Z"
}
```

---

### GET /docs

Documentacion interactiva Swagger UI.

**Autenticacion**: No requiere

**Respuesta**: Interfaz web de Swagger

---

## Players

### POST /v1/players

Crear un nuevo jugador.

**Autenticacion**: No requiere (publico)

**Request Body**:
```json
{
  "username": "player123",
  "email": "player@example.com"  // opcional
}
```

**Validaciones**:
- `username`: 3-20 caracteres, alfanumerico con guiones
- `email`: formato de email valido (opcional)

**Respuesta**: `201 Created`
```json
{
  "player_id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "player123",
  "player_token": "abc-123-xyz-789"
}
```

**⚠️ Importante**: Guardar el `player_token` - es necesario para autenticacion posterior.

**Errores**:
- `400 Bad Request`: Username ya existe o datos invalidos
- `422 Unprocessable Entity`: Formato de datos incorrecto

**Ejemplo cURL**:
```bash
curl -X POST http://localhost:8000/v1/players \
  -H "Content-Type: application/json" \
  -d '{"username": "player123", "email": "player@example.com"}'
```

---

### GET /v1/players/me

Obtener mi perfil (jugador autenticado).

**Autenticacion**: Player Token

**Headers**:
```
X-Player-ID: <player_id>
X-Player-Token: <player_token>
```

**Respuesta**: `200 OK`
```json
{
  "player_id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "player123",
  "email": "player@example.com",
  "created_at": "2026-01-15T10:30:00Z",
  "last_login": "2026-01-18T09:15:00Z",
  "total_playtime_seconds": 3600,
  "games_played": 5,
  "games_completed": 2,
  "stats": {
    "total_good_choices": 4,
    "total_bad_choices": 1,
    "total_deaths": 15,
    "favorite_relic": "lirio",
    "best_speedrun_seconds": 1200,
    "moral_alignment": 0.6
  }
}
```

**Errores**:
- `401 Unauthorized`: Token invalido o expirado
- `404 Not Found`: Jugador no existe

**Ejemplo cURL**:
```bash
curl -X GET http://localhost:8000/v1/players/me \
  -H "X-Player-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -H "X-Player-Token: abc-123-xyz-789"
```

---

### GET /v1/players/{player_id}

Obtener perfil de un jugador especifico.

**Autenticacion**: Admin O jugador autenticado (solo su propio ID)

**Parametros URL**:
- `player_id` (UUID): ID del jugador

**Respuesta**: `200 OK` (mismo formato que `/me`)

**Errores**:
- `403 Forbidden`: No tienes permiso para ver este jugador
- `404 Not Found`: Jugador no existe

**Ejemplo cURL**:
```bash
# Como jugador (solo mi propio ID)
curl -X GET http://localhost:8000/v1/players/550e8400-e29b-41d4-a716-446655440000 \
  -H "X-Player-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -H "X-Player-Token: abc-123-xyz-789"

# Como admin
curl -X GET http://localhost:8000/v1/players/550e8400-e29b-41d4-a716-446655440000 \
  -H "X-API-Key: tu_api_key"
```

---

### GET /v1/players

Listar todos los jugadores.

**Autenticacion**: Solo Admin (API Key o JWT)

**Query Parameters**:
- `limit` (int, default: 100): Numero maximo de jugadores a retornar

**Respuesta**: `200 OK`
```json
{
  "players": [
    {
      "player_id": "550e8400-e29b-41d4-a716-446655440000",
      "username": "player123",
      "created_at": "2026-01-15T10:30:00Z",
      "games_played": 5,
      "games_completed": 2
    },
    // ... mas jugadores
  ],
  "total": 42,
  "limit": 100
}
```

**Errores**:
- `403 Forbidden`: Solo administradores pueden listar jugadores

**Ejemplo cURL**:
```bash
curl -X GET "http://localhost:8000/v1/players?limit=50" \
  -H "X-API-Key: tu_api_key"
```

---

### PATCH /v1/players/{player_id}

Actualizar perfil de un jugador.

**Autenticacion**: Admin O jugador autenticado (solo su propio ID)

**Parametros URL**:
- `player_id` (UUID): ID del jugador

**Request Body** (todos los campos son opcionales):
```json
{
  "username": "nuevo_username",
  "email": "nuevo@example.com"
}
```

**Respuesta**: `200 OK`
```json
{
  "player_id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "nuevo_username",
  "email": "nuevo@example.com",
  "updated_at": "2026-01-18T10:45:00Z"
}
```

**Errores**:
- `400 Bad Request`: Username ya existe o datos invalidos
- `403 Forbidden`: No tienes permiso para editar este jugador
- `404 Not Found`: Jugador no existe

**Ejemplo cURL**:
```bash
curl -X PATCH http://localhost:8000/v1/players/550e8400-e29b-41d4-a716-446655440000 \
  -H "Content-Type: application/json" \
  -H "X-Player-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -H "X-Player-Token: abc-123-xyz-789" \
  -d '{"email": "nuevo@example.com"}'
```

---

### DELETE /v1/players/{player_id}

Eliminar cuenta de jugador.

**Autenticacion**: Admin O jugador autenticado (solo su propio ID)

**Parametros URL**:
- `player_id` (UUID): ID del jugador

**Respuesta**: `200 OK`
```json
{
  "message": "Player deleted successfully",
  "player_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Errores**:
- `403 Forbidden`: No tienes permiso para eliminar este jugador
- `404 Not Found`: Jugador no existe

**Ejemplo cURL**:
```bash
curl -X DELETE http://localhost:8000/v1/players/550e8400-e29b-41d4-a716-446655440000 \
  -H "X-Player-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -H "X-Player-Token: abc-123-xyz-789"
```

---

## Games

### POST /v1/games

Crear una nueva partida.

**Autenticacion**: Player Token

**Request Body** (opcional):
```json
{}
```

> **Nota**: El `player_id` es opcional. Si no se envia, se usa automaticamente el del jugador autenticado.

**Respuesta**: `201 Created`
```json
{
  "game_id": "game-uuid-123",
  "player_id": "550e8400-e29b-41d4-a716-446655440000",
  "started_at": "2026-01-18T10:30:00Z",
  "status": "in_progress",
  "completion_percentage": 0,
  "total_time_seconds": 0,
  "levels_completed": [],
  "current_level": null,
  "choices": {
    "senda_ebano": null,
    "fortaleza_gigantes": null,
    "aquelarre_sombras": null
  },
  "relics": [],
  "boss_defeated": false,
  "npcs_helped": [],
  "metrics": {
    "total_deaths": 0,
    "time_per_level": {},
    "deaths_per_level": {}
  }
}
```

**Errores**:
- `400 Bad Request`: Datos invalidos
- `403 Forbidden`: No puedes crear partidas para otros jugadores
- `404 Not Found`: Jugador no existe

**Ejemplo cURL**:
```bash
curl -X POST http://localhost:8000/v1/games \
  -H "Content-Type: application/json" \
  -H "X-Player-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -H "X-Player-Token: abc-123-xyz-789" \
  -d '{}'
```

---

### GET /v1/games/{game_id}

Obtener datos de una partida.

**Autenticacion**: Admin O dueno de la partida

**Parametros URL**:
- `game_id` (UUID): ID de la partida

**Respuesta**: `200 OK` (mismo formato que POST /v1/games)

**Errores**:
- `403 Forbidden`: No tienes permiso para ver esta partida
- `404 Not Found`: Partida no existe

**Ejemplo cURL**:
```bash
curl -X GET http://localhost:8000/v1/games/game-uuid-123 \
  -H "X-Player-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -H "X-Player-Token: abc-123-xyz-789"
```

---

### GET /v1/games/player/{player_id}

Listar todas las partidas de un jugador.

**Autenticacion**: Admin O jugador autenticado (solo su propio ID)

**Parametros URL**:
- `player_id` (UUID): ID del jugador

**Query Parameters**:
- `limit` (int, default: 100): Numero maximo de partidas

**Respuesta**: `200 OK`
```json
{
  "games": [
    {
      "game_id": "game-uuid-123",
      "started_at": "2026-01-18T10:30:00Z",
      "status": "in_progress",
      "completion_percentage": 40
    },
    // ... mas partidas
  ],
  "total": 5,
  "limit": 100
}
```

**Errores**:
- `403 Forbidden`: No tienes permiso para ver estas partidas

**Ejemplo cURL**:
```bash
curl -X GET "http://localhost:8000/v1/games/player/550e8400-e29b-41d4-a716-446655440000?limit=10" \
  -H "X-Player-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -H "X-Player-Token: abc-123-xyz-789"
```

---

### PATCH /v1/games/{game_id}

Actualizar estado/datos de una partida.

**Autenticacion**: Admin O dueno de la partida

**Parametros URL**:
- `game_id` (UUID): ID de la partida

**Request Body** (todos los campos son opcionales):
```json
{
  "status": "completed",
  "current_level": "fortaleza_gigantes",
  "boss_defeated": true
}
```

**Respuesta**: `200 OK` (datos actualizados de la partida)

**Errores**:
- `400 Bad Request`: Datos invalidos
- `403 Forbidden`: No tienes permiso para editar esta partida
- `404 Not Found`: Partida no existe

**Ejemplo cURL**:
```bash
curl -X PATCH http://localhost:8000/v1/games/game-uuid-123 \
  -H "Content-Type: application/json" \
  -H "X-Player-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -H "X-Player-Token: abc-123-xyz-789" \
  -d '{"status": "completed"}'
```

---

### POST /v1/games/{game_id}/level/start

Registrar inicio de un nivel.

**Autenticacion**: Admin O dueno de la partida

**Parametros URL**:
- `game_id` (UUID): ID de la partida

**Request Body**:
```json
{
  "level": "senda_ebano"
}
```

**Niveles validos**:
- `hub_central`
- `senda_ebano`
- `fortaleza_gigantes`
- `aquelarre_sombras`
- `claro_almas`

**Respuesta**: `200 OK`
```json
{
  "message": "Level started successfully",
  "game_id": "game-uuid-123",
  "level": "senda_ebano",
  "started_at": "2026-01-18T10:45:00Z"
}
```

**Errores**:
- `400 Bad Request`: Nivel invalido
- `403 Forbidden`: No tienes permiso
- `404 Not Found`: Partida no existe

**Ejemplo cURL**:
```bash
curl -X POST http://localhost:8000/v1/games/game-uuid-123/level/start \
  -H "Content-Type: application/json" \
  -H "X-Player-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -H "X-Player-Token: abc-123-xyz-789" \
  -d '{"level": "senda_ebano"}'
```

---

### POST /v1/games/{game_id}/level/complete

Registrar completado de un nivel.

**Autenticacion**: Admin O dueno de la partida

**Parametros URL**:
- `game_id` (UUID): ID de la partida

**Request Body**:
```json
{
  "level": "senda_ebano",
  "time_seconds": 245,
  "deaths": 3,
  "choice": "sanar",
  "relic": "lirio"
}
```

**Campos**:
- `level` (string, requerido): Nivel completado
- `time_seconds` (int, requerido): Tiempo en segundos
- `deaths` (int, requerido): Numero de muertes
- `choice` (string, opcional): Decision tomada
- `relic` (string, opcional): Reliquia obtenida

**Decisiones validas por nivel**:
- **senda_ebano**: `forzar` (malo) | `sanar` (bueno)
- **fortaleza_gigantes**: `destruir` (malo) | `construir` (bueno)
- **aquelarre_sombras**: `ocultar` (malo) | `revelar` (bueno)

**Reliquias validas**:
- `lirio`
- `hacha`
- `manto`

**Respuesta**: `200 OK`
```json
{
  "message": "Level completed successfully",
  "game_id": "game-uuid-123",
  "level": "senda_ebano",
  "completion_percentage": 25,
  "time_seconds": 245,
  "choice": "sanar",
  "relic": "lirio"
}
```

**Errores**:
- `400 Bad Request`: Datos invalidos (nivel, decision o reliquia incorrecta)
- `403 Forbidden`: No tienes permiso
- `404 Not Found`: Partida no existe

**Ejemplo cURL**:
```bash
curl -X POST http://localhost:8000/v1/games/game-uuid-123/level/complete \
  -H "Content-Type: application/json" \
  -H "X-Player-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -H "X-Player-Token: abc-123-xyz-789" \
  -d '{
    "level": "senda_ebano",
    "time_seconds": 245,
    "deaths": 3,
    "choice": "sanar",
    "relic": "lirio"
  }'
```

---

### POST /v1/games/{game_id}/complete

Finalizar una partida (marcarla como completada).

**Autenticacion**: Admin O dueno de la partida

**Parametros URL**:
- `game_id` (UUID): ID de la partida

**Request Body**: Vacio `{}`

**Respuesta**: `200 OK`
```json
{
  "game_id": "game-uuid-123",
  "player_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "ended_at": "2026-01-18T11:30:00Z",
  "completion_percentage": 100,
  "total_time_seconds": 3600
}
```

**Errores**:
- `403 Forbidden`: No tienes permiso para finalizar esta partida
- `404 Not Found`: Partida no existe

**Ejemplo cURL**:
```bash
curl -X POST http://localhost:8000/v1/games/game-uuid-123/complete \
  -H "Content-Type: application/json" \
  -H "X-Player-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -H "X-Player-Token: abc-123-xyz-789" \
  -d '{}'
```

---

### DELETE /v1/games/{game_id}

Eliminar una partida.

**Autenticacion**: Admin O dueno de la partida

**Parametros URL**:
- `game_id` (UUID): ID de la partida

**Respuesta**: `200 OK`
```json
{
  "message": "Partida eliminada correctamente"
}
```

**Errores**:
- `403 Forbidden`: No tienes permiso para eliminar esta partida
- `404 Not Found`: Partida no existe

**Ejemplo cURL**:
```bash
curl -X DELETE http://localhost:8000/v1/games/game-uuid-123 \
  -H "X-Player-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -H "X-Player-Token: abc-123-xyz-789"
```

---

## Events

### POST /v1/events

Crear un evento de gameplay.

**Autenticacion**: Player Token

**Request Body**:
```json
{
  "game_id": "game-uuid-123",
  "player_id": "550e8400-e29b-41d4-a716-446655440000",
  "event_type": "player_death",
  "level": "senda_ebano",
  "data": {
    "position": {"x": 150.5, "y": 200.3},
    "cause": "fall"
  }
}
```

**Campos**:
- `game_id` (UUID, requerido): ID de la partida
- `player_id` (UUID, requerido): ID del jugador
- `event_type` (string, requerido): Tipo de evento
- `level` (string, requerido): Nivel donde ocurrio
- `data` (object, opcional): Datos adicionales del evento

**Tipos de eventos validos**:
- `player_death` - Muerte del jugador
- `level_start` - Inicio de nivel
- `level_end` - Fin de nivel
- `npc_interaction` - Interaccion con NPC
- `item_collected` - Item recolectado
- `checkpoint_reached` - Checkpoint alcanzado
- `boss_encounter` - Encuentro con jefe
- `custom_event` - Evento personalizado

**Respuesta**: `201 Created`
```json
{
  "event_id": "event-uuid-456",
  "game_id": "game-uuid-123",
  "player_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-01-18T10:50:00Z",
  "event_type": "player_death",
  "level": "senda_ebano",
  "data": {
    "position": {"x": 150.5, "y": 200.3},
    "cause": "fall"
  }
}
```

**Errores**:
- `400 Bad Request`: Datos invalidos
- `403 Forbidden`: No puedes crear eventos para otros jugadores

**Ejemplo cURL**:
```bash
curl -X POST http://localhost:8000/v1/events \
  -H "Content-Type: application/json" \
  -H "X-Player-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -H "X-Player-Token: abc-123-xyz-789" \
  -d '{
    "game_id": "game-uuid-123",
    "player_id": "550e8400-e29b-41d4-a716-446655440000",
    "event_type": "player_death",
    "level": "senda_ebano",
    "data": {
      "position": {"x": 150.5, "y": 200.3},
      "cause": "fall"
    }
  }'
```

---

### POST /v1/events/batch

Crear multiples eventos en lote (recomendado para optimizar).

**Autenticacion**: Player Token

**Request Body**:
```json
{
  "events": [
    {
      "game_id": "game-uuid-123",
      "player_id": "550e8400-e29b-41d4-a716-446655440000",
      "event_type": "player_death",
      "level": "senda_ebano",
      "data": {"position": {"x": 150.5, "y": 200.3}, "cause": "fall"}
    },
    {
      "game_id": "game-uuid-123",
      "player_id": "550e8400-e29b-41d4-a716-446655440000",
      "event_type": "checkpoint_reached",
      "level": "senda_ebano",
      "data": {"checkpoint_id": "checkpoint_1"}
    }
  ]
}
```

**Validaciones**:
- Minimo: 1 evento
- Maximo: 100 eventos por batch

**Respuesta**: `201 Created`
```json
{
  "message": "Events created successfully",
  "events_created": 2,
  "event_ids": ["event-uuid-456", "event-uuid-789"]
}
```

**Errores**:
- `400 Bad Request`: Demasiados eventos (>100) o datos invalidos
- `403 Forbidden`: No puedes crear eventos para otros jugadores

**Ejemplo cURL**:
```bash
curl -X POST http://localhost:8000/v1/events/batch \
  -H "Content-Type: application/json" \
  -H "X-Player-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -H "X-Player-Token: abc-123-xyz-789" \
  -d '{
    "events": [
      {
        "game_id": "game-uuid-123",
        "player_id": "550e8400-e29b-41d4-a716-446655440000",
        "event_type": "player_death",
        "level": "senda_ebano",
        "data": {"cause": "fall"}
      }
    ]
  }'
```

---

### GET /v1/events/game/{game_id}

Obtener eventos de una partida.

**Autenticacion**: Admin O dueno de la partida

**Parametros URL**:
- `game_id` (UUID): ID de la partida

**Query Parameters**:
- `limit` (int, default: 1000): Numero maximo de eventos

**Respuesta**: `200 OK`
```json
{
  "events": [
    {
      "event_id": "event-uuid-456",
      "timestamp": "2026-01-18T10:50:00Z",
      "event_type": "player_death",
      "level": "senda_ebano",
      "data": {"position": {"x": 150.5, "y": 200.3}, "cause": "fall"}
    },
    // ... mas eventos
  ],
  "total": 42,
  "limit": 1000
}
```

**Errores**:
- `403 Forbidden`: No tienes permiso para ver estos eventos
- `404 Not Found`: Partida no existe

**Ejemplo cURL**:
```bash
curl -X GET "http://localhost:8000/v1/events/game/game-uuid-123?limit=100" \
  -H "X-Player-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -H "X-Player-Token: abc-123-xyz-789"
```

---

### GET /v1/events/player/{player_id}

Obtener eventos de un jugador (todas sus partidas).

**Autenticacion**: Admin O jugador autenticado (solo su propio ID)

**Parametros URL**:
- `player_id` (UUID): ID del jugador

**Query Parameters**:
- `limit` (int, default: 1000): Numero maximo de eventos

**Respuesta**: `200 OK` (mismo formato que `/events/game/{game_id}`)

**Errores**:
- `403 Forbidden`: No tienes permiso para ver estos eventos

**Ejemplo cURL**:
```bash
curl -X GET "http://localhost:8000/v1/events/player/550e8400-e29b-41d4-a716-446655440000?limit=500" \
  -H "X-Player-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -H "X-Player-Token: abc-123-xyz-789"
```

---

### GET /v1/events/game/{game_id}/type/{event_type}

Obtener eventos de una partida filtrados por tipo.

**Autenticacion**: Admin O dueno de la partida

**Parametros URL**:
- `game_id` (UUID): ID de la partida
- `event_type` (string): Tipo de evento (ver tipos validos arriba)

**Query Parameters**:
- `limit` (int, default: 1000): Numero maximo de eventos

**Respuesta**: `200 OK` (mismo formato que `/events/game/{game_id}`)

**Errores**:
- `400 Bad Request`: Tipo de evento invalido
- `403 Forbidden`: No tienes permiso
- `404 Not Found`: Partida no existe

**Ejemplo cURL**:
```bash
curl -X GET "http://localhost:8000/v1/events/game/game-uuid-123/type/player_death?limit=50" \
  -H "X-Player-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -H "X-Player-Token: abc-123-xyz-789"
```

---

## Auth (Administradores)

### POST /v1/auth/login

Login de administrador.

**Autenticacion**: No requiere (publico)

**Request Body**:
```json
{
  "username": "admin_user",
  "password": "password123456"
}
```

**Respuesta**: `200 OK`
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Errores**:
- `401 Unauthorized`: Credenciales invalidas o cuenta inactiva

**Ejemplo cURL**:
```bash
curl -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin_user",
    "password": "password123456"
  }'
```

---

### POST /v1/auth/refresh

Refrescar access token usando refresh token.

**Autenticacion**: No requiere (usa refresh token)

**Request Body**:
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Respuesta**: `200 OK`
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Errores**:
- `401 Unauthorized`: Refresh token invalido o expirado

**Ejemplo cURL**:
```bash
curl -X POST http://localhost:8000/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."}'
```

---

### POST /v1/auth/logout

Cerrar sesion de administrador.

**Autenticacion**: JWT Bearer Token

**Headers**:
```
Authorization: Bearer <access_token>
```

**Respuesta**: `200 OK`
```json
{
  "message": "Logged out successfully"
}
```

**Ejemplo cURL**:
```bash
curl -X POST http://localhost:8000/v1/auth/logout \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

---

### GET /v1/auth/me

Obtener datos del usuario administrador autenticado.

**Autenticacion**: JWT Bearer Token

**Headers**:
```
Authorization: Bearer <access_token>
```

**Respuesta**: `200 OK`
```json
{
  "id": 1,
  "username": "admin_user",
  "email": "admin@example.com",
  "role": "admin",
  "permissions": ["create_admins", "view_admins", "edit_admins", "view_audit_logs"],
  "is_active": true,
  "created_at": "2026-01-10T09:00:00Z",
  "last_login": "2026-01-18T08:30:00Z"
}
```

**Errores**:
- `401 Unauthorized`: Token invalido o expirado

**Ejemplo cURL**:
```bash
curl -X GET http://localhost:8000/v1/auth/me \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

---

### POST /v1/auth/change-password

Cambiar contrasena de administrador.

**Autenticacion**: JWT Bearer Token

**Request Body**:
```json
{
  "old_password": "password123456",
  "new_password": "newpassword789"
}
```

**Validaciones**:
- `new_password`: minimo 8 caracteres

**Respuesta**: `200 OK`
```json
{
  "message": "Password changed successfully"
}
```

**Errores**:
- `400 Bad Request`: Contrasena actual incorrecta o nueva contrasena invalida
- `401 Unauthorized`: Token invalido

**Ejemplo cURL**:
```bash
curl -X POST http://localhost:8000/v1/auth/change-password \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..." \
  -d '{
    "old_password": "password123456",
    "new_password": "newpassword789"
  }'
```

---

### POST /v1/auth/admin/users

Crear nuevo usuario administrador.

**Autenticacion**: JWT Bearer Token con permiso `create_admins`

**Request Body**:
```json
{
  "username": "new_admin",
  "email": "newadmin@example.com",
  "password": "password123456",
  "role": "support",
  "permissions": ["view_admins"]
}
```

**Roles disponibles**:
- `admin`: Acceso completo
- `support`: Soporte tecnico
- `viewer`: Solo lectura

**Respuesta**: `201 Created`
```json
{
  "id": 2,
  "username": "new_admin",
  "email": "newadmin@example.com",
  "role": "support",
  "permissions": ["view_admins"],
  "is_active": true,
  "created_at": "2026-01-18T11:00:00Z"
}
```

**Errores**:
- `400 Bad Request`: Username o email ya existe
- `403 Forbidden`: No tienes permiso para crear administradores

**Ejemplo cURL**:
```bash
curl -X POST http://localhost:8000/v1/auth/admin/users \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..." \
  -d '{
    "username": "new_admin",
    "email": "newadmin@example.com",
    "password": "password123456",
    "role": "support",
    "permissions": ["view_admins"]
  }'
```

---

### GET /v1/auth/admin/users

Listar usuarios administradores.

**Autenticacion**: JWT Bearer Token con permiso `view_admins`

**Query Parameters**:
- `role` (string, opcional): Filtrar por rol
- `is_active` (bool, opcional): Filtrar por estado activo/inactivo
- `limit` (int, default: 100): Numero maximo de usuarios

**Respuesta**: `200 OK`
```json
{
  "users": [
    {
      "id": 1,
      "username": "admin_user",
      "email": "admin@example.com",
      "role": "admin",
      "is_active": true,
      "created_at": "2026-01-10T09:00:00Z"
    },
    // ... mas usuarios
  ],
  "total": 5,
  "limit": 100
}
```

**Errores**:
- `403 Forbidden`: No tienes permiso

**Ejemplo cURL**:
```bash
curl -X GET "http://localhost:8000/v1/auth/admin/users?role=admin&limit=50" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

---

### GET /v1/auth/admin/users/{user_id}

Obtener datos de un administrador especifico.

**Autenticacion**: JWT Bearer Token con permiso `view_admins`

**Parametros URL**:
- `user_id` (int): ID del usuario administrador

**Respuesta**: `200 OK`
```json
{
  "id": 2,
  "username": "admin_user",
  "email": "admin@example.com",
  "role": "admin",
  "permissions": ["create_admins", "view_admins", "edit_admins"],
  "is_active": true,
  "created_at": "2026-01-10T09:00:00Z",
  "last_login": "2026-01-18T08:30:00Z"
}
```

**Errores**:
- `403 Forbidden`: No tienes permiso
- `404 Not Found`: Usuario no existe

**Ejemplo cURL**:
```bash
curl -X GET http://localhost:8000/v1/auth/admin/users/2 \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

---

### PATCH /v1/auth/admin/users/{user_id}

Actualizar usuario administrador.

**Autenticacion**: JWT Bearer Token con permiso `edit_admins`

**Parametros URL**:
- `user_id` (int): ID del usuario administrador

**Request Body** (todos los campos son opcionales):
```json
{
  "email": "newemail@example.com",
  "role": "viewer",
  "permissions": ["view_admins"],
  "is_active": false
}
```

**Respuesta**: `200 OK` (datos actualizados del usuario)

**Errores**:
- `403 Forbidden`: No tienes permiso
- `404 Not Found`: Usuario no existe

**Ejemplo cURL**:
```bash
curl -X PATCH http://localhost:8000/v1/auth/admin/users/2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..." \
  -d '{"is_active": false}'
```

---

### GET /v1/auth/admin/audit

Obtener logs de auditoria.

**Autenticacion**: JWT Bearer Token con permiso `view_audit_logs`

**Query Parameters**:
- `user_id` (int, opcional): Filtrar por usuario
- `action` (string, opcional): Filtrar por tipo de accion
- `start_date` (ISO datetime, opcional): Fecha inicio
- `end_date` (ISO datetime, opcional): Fecha fin
- `success` (bool, opcional): Filtrar por exito/fallo
- `limit` (int, default: 100): Numero maximo de logs
- `offset` (int, default: 0): Paginacion

**Respuesta**: `200 OK`
```json
{
  "logs": [
    {
      "id": 1,
      "user_id": 1,
      "username": "admin_user",
      "action": "login",
      "resource_type": null,
      "resource_id": null,
      "ip_address": "192.168.1.1",
      "user_agent": "Mozilla/5.0...",
      "details": null,
      "timestamp": "2026-01-18T08:30:00Z",
      "success": true,
      "error_message": null
    },
    // ... mas logs
  ],
  "total": 150,
  "limit": 100,
  "offset": 0
}
```

**Errores**:
- `403 Forbidden`: No tienes permiso

**Ejemplo cURL**:
```bash
curl -X GET "http://localhost:8000/v1/auth/admin/audit?action=login&limit=50" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

---

## Dashboard Web

El dashboard web esta construido con Flask y proporciona una interfaz visual para analizar datos del juego.

### GET /web/

Landing page del portal web.

**Autenticacion**: No requiere

---

### GET /web/dashboard/

Dashboard principal con metricas globales.

**Autenticacion**: No requiere (puede cambiar en produccion)

**Contenido**:
- Total de jugadores
- Total de partidas
- Tasa de completado
- Metricas de engagement
- Graficos de Plotly interactivos

---

### GET /web/dashboard/players

Analisis detallado de jugadores.

**Autenticacion**: No requiere

**Contenido**:
- Distribucion de jugadores nuevos
- Jugadores activos
- Tiempo de juego promedio
- Rankings

---

### GET /web/dashboard/games

Analisis de partidas y progresion.

**Autenticacion**: No requiere

**Contenido**:
- Partidas por estado
- Distribucion de completado
- Niveles mas jugados
- Tiempo promedio por nivel

---

### GET /web/dashboard/choices

Analisis de decisiones morales.

**Autenticacion**: No requiere

**Contenido**:
- Distribucion de decisiones buenas vs malas
- Decisiones por nivel
- Alineamiento moral de jugadores
- Reliquias mas populares

---

### GET /web/dashboard/events

Analisis de eventos de gameplay.

**Autenticacion**: No requiere

**Contenido**:
- Eventos por tipo
- Linea temporal de eventos
- Muertes por nivel
- Heatmaps de posiciones

---

### GET /web/dashboard/export

Pagina de exportacion de datos.

**Autenticacion**: No requiere

**Funcionalidad**:
- Exportar jugadores a CSV/JSON
- Exportar partidas a CSV/JSON
- Exportar eventos a CSV/JSON

---

### GET /web/admin/login

Pagina de login para administradores.

**Autenticacion**: No requiere

---

### GET /web/admin/dashboard

Dashboard de administracion.

**Autenticacion**: Sesion de administrador

---

### GET /web/admin/export

Pagina de exportacion de datos (admin).

**Autenticacion**: Sesion de administrador

---

### POST /web/admin/export/download

Descargar datos exportados en CSV.

**Autenticacion**: Sesion de administrador

**Form Data**:
- `type`: `players` | `games` | `events`

**Respuesta**: Archivo CSV para descargar

---

## Codigos de Estado

### Exitosos
- `200 OK`: Operacion exitosa
- `201 Created`: Recurso creado exitosamente

### Errores del Cliente
- `400 Bad Request`: Datos invalidos o mal formateados
- `401 Unauthorized`: Autenticacion requerida o token invalido
- `403 Forbidden`: No tienes permiso para esta operacion
- `404 Not Found`: Recurso no encontrado
- `422 Unprocessable Entity`: Validacion de datos fallida

### Errores del Servidor
- `500 Internal Server Error`: Error interno del servidor

---

## Notas Adicionales

### Rate Limiting
Actualmente no hay rate limiting implementado, pero se recomienda no hacer mas de 100 requests por segundo.

### Batch Operations
Para eventos, usa siempre `/v1/events/batch` en lugar de crear eventos individuales para mejor rendimiento.

### Timestamps
Todos los timestamps estan en formato ISO 8601 UTC:
```
2026-01-18T10:30:00Z
```

### UUIDs
Los IDs de jugadores, partidas y eventos usan formato UUID v4:
```
550e8400-e29b-41d4-a716-446655440000
```

---

## Soporte

Para mas informacion, consulta:
- [README](../README.md)
- [Documentacion Swagger](http://localhost:8000/docs) (cuando la API este corriendo)
- [Unity Integration](UNITY_INTEGRATION.md)
