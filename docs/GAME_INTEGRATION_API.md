# Triskel API - Guia de Integracion para el Juego

**Version:** 1.1
**Base URL:** `http://localhost:8000` (desarrollo) | `https://tu-dominio.com` (produccion)

## Indice

1. [Autenticacion](#autenticacion)
2. [Jugadores](#1-jugadores)
3. [Partidas](#2-partidas)
4. [Eventos](#3-eventos)
5. [Constantes y Enums](#4-constantes-y-enums)
6. [Flujo de Integracion](#5-flujo-de-integracion)
7. [Sistema Moral](#6-sistema-moral)
8. [Codigos de Error](#7-codigos-de-error)

---

## Autenticacion

### Headers requeridos para jugadores

Todas las peticiones autenticadas requieren estos headers:

```
X-Player-ID: {player_id}
X-Player-Token: {player_token}
```

> **IMPORTANTE:** Guarda `player_id` y `player_token` cuando hagas login. Son las credenciales para todas las peticiones posteriores.

---

## 1. JUGADORES

### 1.1 Login (Crear o Ingresar) - ENDPOINT PRINCIPAL

Este es el endpoint que debe usar el juego para iniciar sesion. Si el usuario no existe, lo crea automaticamente.

```
POST /v1/players/login
```

**Headers:** Ninguno (endpoint publico)

#### Request Body

| Campo      | Tipo     | Requerido | Restricciones            | Descripcion              |
|------------|----------|-----------|--------------------------|--------------------------|
| `username` | `string` | Si        | 3-20 caracteres          | Nombre de usuario        |
| `email`    | `string` | No        | Formato email valido     | Email del jugador        |

```json
{
  "username": "jugador123",
  "email": "jugador@email.com"
}
```

#### Response (200 OK)

| Campo            | Tipo      | Descripcion                                      |
|------------------|-----------|--------------------------------------------------|
| `player_id`      | `string`  | UUID unico del jugador                           |
| `username`       | `string`  | Nombre de usuario                                |
| `player_token`   | `string`  | Token secreto - **GUARDAR EN EL JUEGO**          |
| `active_game_id` | `string?` | ID de partida activa (null si no hay ninguna)    |
| `is_new_player`  | `boolean` | `true` si se creo nuevo, `false` si ya existia   |

```json
{
  "player_id": "123e4567-e89b-12d3-a456-426614174000",
  "username": "jugador123",
  "player_token": "abc-def-ghi-token-secreto",
  "active_game_id": "game-456-xyz",
  "is_new_player": false
}
```

> **LOGICA:**
> - Si `is_new_player = true`: Usuario nuevo creado
> - Si `is_new_player = false`: Usuario existente, devuelve sus credenciales
> - Si `active_game_id != null`: Tiene una partida en progreso que puede continuar

---

### 1.2 Crear Jugador (Solo Registro)

Crea un nuevo jugador. Falla si el username ya existe.

```
POST /v1/players
```

**Headers:** Ninguno (endpoint publico)

#### Request Body

| Campo      | Tipo     | Requerido | Restricciones       | Descripcion        |
|------------|----------|-----------|---------------------|--------------------|
| `username` | `string` | Si        | 3-20 caracteres     | Nombre de usuario  |
| `email`    | `string` | No        | Formato email valido| Email del jugador  |

```json
{
  "username": "nuevo_jugador",
  "email": "nuevo@email.com"
}
```

#### Response (201 Created)

| Campo          | Tipo     | Descripcion                         |
|----------------|----------|-------------------------------------|
| `player_id`    | `string` | UUID unico del jugador              |
| `username`     | `string` | Nombre de usuario                   |
| `player_token` | `string` | Token secreto - GUARDAR EN EL JUEGO |

```json
{
  "player_id": "123e4567-e89b-12d3-a456-426614174000",
  "username": "nuevo_jugador",
  "player_token": "abc-def-ghi-token-secreto"
}
```

#### Errores

| Codigo | Descripcion                    |
|--------|--------------------------------|
| 400    | Username ya existe o invalido  |

---

### 1.3 Obtener Mi Perfil (Verificar Sesion)

Verifica que las credenciales son validas y obtiene el perfil completo.

```
GET /v1/players/me
```

#### Headers

```
X-Player-ID: {player_id}
X-Player-Token: {player_token}
```

#### Response (200 OK)

| Campo                    | Tipo           | Descripcion                        |
|--------------------------|----------------|------------------------------------|
| `player_id`              | `string`       | UUID del jugador                   |
| `username`               | `string`       | Nombre de usuario                  |
| `email`                  | `string?`      | Email (puede ser null)             |
| `player_token`           | `string`       | Token de autenticacion             |
| `created_at`             | `datetime`     | Fecha de creacion (ISO 8601)       |
| `last_login`             | `datetime`     | Ultimo acceso (ISO 8601)           |
| `total_playtime_seconds` | `integer`      | Tiempo total jugado en segundos    |
| `games_played`           | `integer`      | Numero de partidas iniciadas       |
| `games_completed`        | `integer`      | Numero de partidas completadas     |
| `stats`                  | `PlayerStats`  | Estadisticas agregadas             |

#### PlayerStats (objeto anidado)

| Campo                   | Tipo      | Rango        | Descripcion                             |
|-------------------------|-----------|--------------|----------------------------------------|
| `total_good_choices`    | `integer` | >= 0         | Total decisiones buenas (todas partidas)|
| `total_bad_choices`     | `integer` | >= 0         | Total decisiones malas (todas partidas) |
| `total_deaths`          | `integer` | >= 0         | Muertes acumuladas                      |
| `favorite_relic`        | `string?` | enum         | Reliquia mas recolectada                |
| `best_speedrun_seconds` | `integer?`| >= 0         | Mejor tiempo de completado              |
| `moral_alignment`       | `float`   | -1.0 a 1.0   | Alineacion moral                        |

```json
{
  "player_id": "123e4567-e89b-12d3-a456-426614174000",
  "username": "jugador123",
  "email": "jugador@email.com",
  "player_token": "abc-def-token",
  "created_at": "2026-01-15T10:30:00Z",
  "last_login": "2026-01-18T14:20:00Z",
  "total_playtime_seconds": 7200,
  "games_played": 5,
  "games_completed": 2,
  "stats": {
    "total_good_choices": 4,
    "total_bad_choices": 2,
    "total_deaths": 45,
    "favorite_relic": "lirio",
    "best_speedrun_seconds": 2400,
    "moral_alignment": 0.33
  }
}
```

---

### 1.4 Actualizar Jugador

Actualiza datos del jugador.

```
PATCH /v1/players/{player_id}
```

#### Headers

```
X-Player-ID: {player_id}
X-Player-Token: {player_token}
```

#### Path Parameters

| Parametro   | Tipo     | Descripcion        |
|-------------|----------|--------------------|
| `player_id` | `string` | UUID del jugador   |

#### Request Body (todos los campos son opcionales)

| Campo                    | Tipo          | Restricciones   | Descripcion               |
|--------------------------|---------------|-----------------|---------------------------|
| `username`               | `string`      | 3-20 chars      | Nuevo nombre              |
| `email`                  | `string`      | Formato email   | Nuevo email               |
| `total_playtime_seconds` | `integer`     | >= 0            | Tiempo total jugado       |
| `games_played`           | `integer`     | >= 0            | Partidas jugadas          |
| `games_completed`        | `integer`     | >= 0            | Partidas completadas      |
| `stats`                  | `PlayerStats` | Ver arriba      | Estadisticas              |

```json
{
  "username": "nuevo_nombre",
  "total_playtime_seconds": 9000
}
```

#### Response (200 OK)

Retorna el objeto `Player` completo actualizado.

---

## 2. PARTIDAS

### 2.1 Crear Nueva Partida

Inicia una nueva partida para el jugador.

```
POST /v1/games
```

#### Headers

```
X-Player-ID: {player_id}
X-Player-Token: {player_token}
```

#### Request Body

| Campo       | Tipo     | Requerido | Descripcion        |
|-------------|----------|-----------|-------------------|
| `player_id` | `string` | Si        | UUID del jugador  |

```json
{
  "player_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

#### Response (201 Created) - Objeto Game

| Campo                   | Tipo           | Descripcion                          |
|-------------------------|----------------|--------------------------------------|
| `game_id`               | `string`       | UUID de la partida                   |
| `player_id`             | `string`       | UUID del jugador                     |
| `started_at`            | `datetime`     | Fecha/hora de inicio (ISO 8601)      |
| `ended_at`              | `datetime?`    | Fecha/hora de fin (null si activa)   |
| `status`                | `string`       | Estado: `in_progress`, `completed`, `abandoned` |
| `completion_percentage` | `float`        | Porcentaje completado (0.0-100.0)    |
| `total_time_seconds`    | `integer`      | Tiempo total jugado en segundos      |
| `levels_completed`      | `string[]`     | Lista de niveles completados         |
| `current_level`         | `string?`      | Nivel actual (null si no hay)        |
| `choices`               | `GameChoices`  | Decisiones morales tomadas           |
| `relics`                | `string[]`     | Reliquias recolectadas               |
| `boss_defeated`         | `boolean`      | Si derroto al jefe final             |
| `npcs_helped`           | `string[]`     | NPCs ayudados                        |
| `metrics`               | `GameMetrics`  | Metricas de juego                    |

#### GameChoices (objeto anidado)

| Campo                | Tipo      | Valores validos               |
|----------------------|-----------|-------------------------------|
| `senda_ebano`        | `string?` | `"sanar"` \| `"forzar"` \| null |
| `fortaleza_gigantes` | `string?` | `"construir"` \| `"destruir"` \| null |
| `aquelarre_sombras`  | `string?` | `"revelar"` \| `"ocultar"` \| null |

#### GameMetrics (objeto anidado)

| Campo              | Tipo                   | Descripcion                    |
|--------------------|------------------------|--------------------------------|
| `total_deaths`     | `integer`              | Muertes totales en la partida  |
| `time_per_level`   | `object<string, int>`  | Segundos por nivel             |
| `deaths_per_level` | `object<string, int>`  | Muertes por nivel              |

```json
{
  "game_id": "abc-123-def-456",
  "player_id": "123e4567-e89b-12d3-a456-426614174000",
  "started_at": "2026-01-18T10:00:00Z",
  "ended_at": null,
  "status": "in_progress",
  "completion_percentage": 0.0,
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

#### Errores

| Codigo | Descripcion                              |
|--------|------------------------------------------|
| 403    | Intentas crear partida para otro jugador |
| 404    | Jugador no existe                        |
| 409    | Ya tiene una partida activa              |

---

### 2.2 Obtener Partidas del Jugador

Lista todas las partidas de un jugador.

```
GET /v1/games/player/{player_id}?limit=100
```

#### Headers

```
X-Player-ID: {player_id}
X-Player-Token: {player_token}
```

#### Path Parameters

| Parametro   | Tipo     | Descripcion      |
|-------------|----------|------------------|
| `player_id` | `string` | UUID del jugador |

#### Query Parameters

| Parametro | Tipo      | Default | Rango   | Descripcion          |
|-----------|-----------|---------|---------|----------------------|
| `limit`   | `integer` | 100     | 1-1000  | Maximo de resultados |

#### Response (200 OK)

Array de objetos `Game` (ver estructura en 2.1).

```json
[
  {
    "game_id": "abc-123",
    "player_id": "123e4567",
    "status": "in_progress",
    "current_level": "fortaleza_gigantes",
    "completion_percentage": 40.0,
    "relics": ["lirio"],
    "choices": {
      "senda_ebano": "sanar",
      "fortaleza_gigantes": null,
      "aquelarre_sombras": null
    }
  },
  {
    "game_id": "xyz-789",
    "status": "completed",
    "completion_percentage": 100.0
  }
]
```

> **TIP:** Filtra en tu codigo por `status === "in_progress"` para mostrar solo partidas activas.

---

### 2.3 Obtener Partida por ID

Obtiene los detalles de una partida especifica.

```
GET /v1/games/{game_id}
```

#### Headers

```
X-Player-ID: {player_id}
X-Player-Token: {player_token}
```

#### Path Parameters

| Parametro | Tipo     | Descripcion       |
|-----------|----------|-------------------|
| `game_id` | `string` | UUID de la partida|

#### Response (200 OK)

Objeto `Game` completo (ver estructura en 2.1).

---

### 2.4 Iniciar Nivel

Marca el inicio de un nivel en la partida.

```
POST /v1/games/{game_id}/level/start
```

#### Headers

```
X-Player-ID: {player_id}
X-Player-Token: {player_token}
```

#### Path Parameters

| Parametro | Tipo     | Descripcion        |
|-----------|----------|--------------------|
| `game_id` | `string` | UUID de la partida |

#### Request Body

| Campo   | Tipo     | Requerido | Valores validos                                                        |
|---------|----------|-----------|------------------------------------------------------------------------|
| `level` | `string` | Si        | `hub_central`, `senda_ebano`, `fortaleza_gigantes`, `aquelarre_sombras`, `claro_almas` |

```json
{
  "level": "senda_ebano"
}
```

#### Response (200 OK)

Objeto `Game` actualizado con `current_level` establecido.

---

### 2.5 Completar Nivel

Marca un nivel como completado con sus metricas, decision y reliquia.

```
POST /v1/games/{game_id}/level/complete
```

#### Headers

```
X-Player-ID: {player_id}
X-Player-Token: {player_token}
```

#### Path Parameters

| Parametro | Tipo     | Descripcion        |
|-----------|----------|--------------------|
| `game_id` | `string` | UUID de la partida |

#### Request Body

| Campo          | Tipo      | Requerido | Restricciones | Descripcion                         |
|----------------|-----------|-----------|---------------|-------------------------------------|
| `level`        | `string`  | Si        | enum niveles  | Nivel completado                    |
| `time_seconds` | `integer` | Si        | 0-86400       | Tiempo en segundos (max 24h)        |
| `deaths`       | `integer` | Si        | 0-9999        | Muertes en el nivel                 |
| `choice`       | `string`  | No        | ver tabla     | Decision moral (si aplica al nivel) |
| `relic`        | `string`  | No        | enum relics   | Reliquia obtenida (si aplica)       |

**Decisiones por nivel:**

| Nivel                | Opcion Buena  | Opcion Mala  |
|----------------------|---------------|--------------|
| `senda_ebano`        | `"sanar"`     | `"forzar"`   |
| `fortaleza_gigantes` | `"construir"` | `"destruir"` |
| `aquelarre_sombras`  | `"revelar"`   | `"ocultar"`  |

**Reliquias validas:** `"lirio"`, `"hacha"`, `"manto"`

```json
{
  "level": "senda_ebano",
  "time_seconds": 1234,
  "deaths": 3,
  "choice": "sanar",
  "relic": "lirio"
}
```

#### Response (200 OK)

Objeto `Game` actualizado con:
- Nivel agregado a `levels_completed`
- `choices` actualizado con la decision
- `relics` actualizado con la reliquia
- `metrics` actualizado con tiempo y muertes
- `total_time_seconds` recalculado

---

### 2.6 Actualizar Partida

Actualiza campos de la partida directamente.

```
PATCH /v1/games/{game_id}
```

#### Headers

```
X-Player-ID: {player_id}
X-Player-Token: {player_token}
```

#### Path Parameters

| Parametro | Tipo     | Descripcion        |
|-----------|----------|--------------------|
| `game_id` | `string` | UUID de la partida |

#### Request Body (todos los campos son opcionales)

| Campo                   | Tipo       | Restricciones                               | Descripcion                    |
|-------------------------|------------|---------------------------------------------|--------------------------------|
| `status`                | `string`   | `in_progress`, `completed`, `abandoned`     | Estado de la partida           |
| `ended_at`              | `datetime` | ISO 8601                                    | Fecha/hora de finalizacion     |
| `completion_percentage` | `float`    | 0.0-100.0                                   | Porcentaje completado          |
| `total_time_seconds`    | `integer`  | >= 0                                        | Tiempo total jugado            |
| `current_level`         | `string`   | enum niveles                                | Nivel actual                   |
| `boss_defeated`         | `boolean`  | true/false                                  | Si derroto al jefe             |

```json
{
  "status": "completed",
  "completion_percentage": 100.0,
  "boss_defeated": true
}
```

#### Response (200 OK)

Objeto `Game` actualizado.

---

### 2.7 Eliminar Partida

Elimina una partida permanentemente.

```
DELETE /v1/games/{game_id}
```

#### Headers

```
X-Player-ID: {player_id}
X-Player-Token: {player_token}
```

#### Response (200 OK)

```json
{
  "message": "Partida eliminada correctamente"
}
```

---

## 3. EVENTOS

### 3.1 Crear Evento

Registra un evento de gameplay (muerte, checkpoint, reliquia, etc).

```
POST /v1/events
```

#### Headers

```
X-Player-ID: {player_id}
X-Player-Token: {player_token}
```

#### Request Body

| Campo        | Tipo     | Requerido | Descripcion                    |
|--------------|----------|-----------|--------------------------------|
| `game_id`    | `string` | Si        | UUID de la partida             |
| `player_id`  | `string` | Si        | UUID del jugador               |
| `event_type` | `string` | Si        | Tipo de evento (ver tabla)     |
| `level`      | `string` | Si        | Nivel donde ocurrio            |
| `data`       | `object` | No        | Datos adicionales (flexible)   |

**Tipos de evento validos:**

| event_type           | Descripcion                  | Ejemplo de `data`                              |
|----------------------|------------------------------|------------------------------------------------|
| `player_death`       | Muerte del jugador           | `{"cause": "fall", "position_x": 100}`         |
| `level_start`        | Inicio de nivel              | `{}`                                           |
| `level_end`          | Fin de nivel                 | `{"completed": true}`                          |
| `item_collected`     | Recogio un item/reliquia     | `{"item_type": "relic", "relic_name": "lirio"}`|
| `checkpoint_reached` | Llego a checkpoint           | `{"checkpoint_id": "cp_01"}`                   |
| `boss_encounter`     | Encontro al jefe             | `{"boss_name": "guardian"}`                    |
| `npc_interaction`    | Interactuo con NPC           | `{"npc_id": "anciano", "action": "talk"}`      |
| `custom_event`       | Evento personalizado         | `{"event_name": "game_ending", "ending": 2}`   |

```json
{
  "game_id": "abc-123-def-456",
  "player_id": "123e4567-e89b-12d3-a456-426614174000",
  "event_type": "player_death",
  "level": "senda_ebano",
  "data": {
    "cause": "enemy_attack",
    "enemy_type": "goblin",
    "position_x": 150.5,
    "position_y": 200.3
  }
}
```

#### Response (201 Created)

| Campo        | Tipo       | Descripcion                |
|--------------|------------|----------------------------|
| `event_id`   | `string`   | UUID unico del evento      |
| `game_id`    | `string`   | UUID de la partida         |
| `player_id`  | `string`   | UUID del jugador           |
| `timestamp`  | `datetime` | Momento del evento (UTC)   |
| `event_type` | `string`   | Tipo de evento             |
| `level`      | `string`   | Nivel donde ocurrio        |
| `data`       | `object`   | Datos adicionales          |

```json
{
  "event_id": "evt-789-xyz",
  "game_id": "abc-123-def-456",
  "player_id": "123e4567-e89b-12d3-a456-426614174000",
  "timestamp": "2026-01-18T10:35:22Z",
  "event_type": "player_death",
  "level": "senda_ebano",
  "data": {
    "cause": "enemy_attack",
    "enemy_type": "goblin",
    "position_x": 150.5,
    "position_y": 200.3
  }
}
```

---

### 3.2 Crear Eventos en Batch

Envia multiples eventos en una sola peticion (optimizacion).

```
POST /v1/events/batch
```

#### Headers

```
X-Player-ID: {player_id}
X-Player-Token: {player_token}
```

#### Request Body

| Campo    | Tipo            | Requerido | Restricciones   | Descripcion              |
|----------|-----------------|-----------|-----------------|--------------------------|
| `events` | `EventCreate[]` | Si        | 1-100 elementos | Array de eventos a crear |

```json
{
  "events": [
    {
      "game_id": "abc-123",
      "player_id": "xyz-789",
      "event_type": "player_death",
      "level": "senda_ebano",
      "data": {"cause": "fall"}
    },
    {
      "game_id": "abc-123",
      "player_id": "xyz-789",
      "event_type": "checkpoint_reached",
      "level": "senda_ebano",
      "data": {"checkpoint_id": "cp_02"}
    }
  ]
}
```

#### Response (201 Created)

Array de objetos `GameEvent` creados.

---

### 3.3 Obtener Eventos de una Partida

Lista todos los eventos de una partida.

```
GET /v1/events/game/{game_id}?limit=1000
```

#### Headers

```
X-Player-ID: {player_id}
X-Player-Token: {player_token}
```

#### Path Parameters

| Parametro | Tipo     | Descripcion        |
|-----------|----------|--------------------|
| `game_id` | `string` | UUID de la partida |

#### Query Parameters

| Parametro | Tipo      | Default | Rango    | Descripcion        |
|-----------|-----------|---------|----------|--------------------|
| `limit`   | `integer` | 1000    | 1-1000   | Maximo resultados  |

#### Response (200 OK)

Array de objetos `GameEvent` ordenados por timestamp.

---

### 3.4 Obtener Eventos de un Jugador

Lista todos los eventos de un jugador (todas sus partidas).

```
GET /v1/events/player/{player_id}?limit=1000
```

#### Headers

```
X-Player-ID: {player_id}
X-Player-Token: {player_token}
```

#### Response (200 OK)

Array de objetos `GameEvent`.

---

### 3.5 Obtener Eventos por Tipo

Filtra eventos de una partida por tipo.

```
GET /v1/events/game/{game_id}/type/{event_type}?limit=1000
```

#### Path Parameters

| Parametro    | Tipo     | Descripcion        |
|--------------|----------|--------------------|
| `game_id`    | `string` | UUID de la partida |
| `event_type` | `string` | Tipo de evento     |

#### Response (200 OK)

Array de objetos `GameEvent` filtrados.

---

## 4. CONSTANTES Y ENUMS

### Niveles

| Valor                 | Orden | Descripcion           |
|-----------------------|-------|-----------------------|
| `hub_central`         | 0     | Hub central (inicio)  |
| `senda_ebano`         | 1     | Primer nivel          |
| `fortaleza_gigantes`  | 2     | Segundo nivel         |
| `aquelarre_sombras`   | 3     | Tercer nivel          |
| `claro_almas`         | 4     | Nivel final (jefe)    |

### Estados de Partida

| Valor         | Descripcion              |
|---------------|--------------------------|
| `in_progress` | Partida en curso         |
| `completed`   | Partida completada       |
| `abandoned`   | Partida abandonada       |

### Decisiones Morales

| Nivel                | Buena       | Mala       |
|----------------------|-------------|------------|
| `senda_ebano`        | `sanar`     | `forzar`   |
| `fortaleza_gigantes` | `construir` | `destruir` |
| `aquelarre_sombras`  | `revelar`   | `ocultar`  |

### Reliquias

| Valor   | Nivel donde se obtiene  |
|---------|-------------------------|
| `lirio` | `senda_ebano`           |
| `hacha` | `fortaleza_gigantes`    |
| `manto` | `aquelarre_sombras`     |

### Tipos de Evento

| Valor               | Descripcion             |
|---------------------|-------------------------|
| `player_death`      | Muerte del jugador      |
| `level_start`       | Inicio de nivel         |
| `level_end`         | Fin de nivel            |
| `npc_interaction`   | Interaccion con NPC     |
| `item_collected`    | Item recogido           |
| `checkpoint_reached`| Checkpoint alcanzado    |
| `boss_encounter`    | Encuentro con jefe      |
| `custom_event`      | Evento personalizado    |

---

## 5. FLUJO DE INTEGRACION

### 5.1 Login / Registro

```
INICIO DE APP
    |
    v
POST /v1/players/login
    |
    +-- Guardar player_id, player_token, active_game_id
    |
    v
¿is_new_player?
    |
    +-- true --> Mostrar tutorial/bienvenida
    |
    +-- false --> ¿active_game_id != null?
                      |
                      +-- true --> Preguntar: "¿Continuar partida?"
                      |
                      +-- false --> Menu principal
```

### 5.2 Menu Principal

```
¿Tiene active_game_id del login?
    |
    +-- SI --> Mostrar "Continuar" + "Nueva Partida"
    |
    +-- NO --> Solo mostrar "Nueva Partida"

Si quiere ver historial:
    GET /v1/games/player/{player_id}
```

### 5.3 Durante el Juego

```
INICIAR NIVEL
    |
    v
POST /v1/games/{game_id}/level/start
    |
    v
[GAMEPLAY]
    |
    +-- Muerte --> POST /v1/events (player_death)
    |
    +-- Checkpoint --> POST /v1/events (checkpoint_reached)
    |
    +-- Reliquia --> POST /v1/events (item_collected)
    |
    +-- Pausa/Guardar --> PATCH /v1/games/{game_id} (total_time_seconds)
    |
    v
COMPLETAR NIVEL
    |
    v
POST /v1/games/{game_id}/level/complete
(incluye tiempo, muertes, decision, reliquia)
```

### 5.4 Fin del Juego

```
DERROTAR JEFE FINAL
    |
    v
Calcular final segun choices:
- 3 buenas = Final 1 (mejor)
- 2 buenas = Final 2
- 1 buena  = Final 3
- 0 buenas = Final 4 (peor)
    |
    v
POST /v1/events (custom_event: game_ending)
    |
    v
PATCH /v1/games/{game_id}
{
  "status": "completed",
  "boss_defeated": true,
  "completion_percentage": 100
}
```

### 5.5 Cerrar Sesion

La API no tiene endpoint de logout. En tu juego:

1. Borrar `player_id` y `player_token` del almacenamiento local
2. Redirigir a pantalla de login

---

## 6. SISTEMA MORAL

### Como funciona

La API **almacena** las decisiones pero **no calcula** el final. El calculo lo hace el juego.

### Decisiones almacenadas

Cada partida tiene un objeto `choices`:

```json
{
  "choices": {
    "senda_ebano": "sanar",
    "fortaleza_gigantes": "destruir",
    "aquelarre_sombras": null
  }
}
```

### Calculo del final (implementar en el juego)

```
Decisiones buenas: sanar, construir, revelar
Decisiones malas: forzar, destruir, ocultar

Contar decisiones buenas:

| Total buenas | Final |
|--------------|-------|
| 3            | 1     |
| 2            | 2     |
| 1            | 3     |
| 0            | 4     |
```

### Alineacion moral del jugador

El campo `stats.moral_alignment` es un float de -1.0 a 1.0:

- **1.0** = Totalmente bueno
- **0.0** = Neutral
- **-1.0** = Totalmente malo

Formula:
```
moral_alignment = (good - bad) / (good + bad)
```

---

## 7. CODIGOS DE ERROR

### HTTP Status Codes

| Codigo | Nombre                | Descripcion                                |
|--------|----------------------|--------------------------------------------|
| 200    | OK                   | Exito                                      |
| 201    | Created              | Recurso creado                             |
| 400    | Bad Request          | Datos de entrada invalidos                 |
| 401    | Unauthorized         | Credenciales faltantes o invalidas         |
| 403    | Forbidden            | Sin permisos para este recurso             |
| 404    | Not Found            | Recurso no encontrado                      |
| 409    | Conflict             | Conflicto (ej: ya tiene partida activa)    |
| 422    | Validation Error     | Error de validacion en campos              |
| 500    | Internal Server Error| Error interno del servidor                 |

### Formato de Error

```json
{
  "detail": "Mensaje descriptivo del error"
}
```

### Error de Validacion (422)

```json
{
  "detail": [
    {
      "loc": ["body", "level"],
      "msg": "Nivel 'invalid' no valido. Validos: hub_central, senda_ebano, fortaleza_gigantes, aquelarre_sombras, claro_almas",
      "type": "value_error"
    }
  ]
}
```

---

## Resumen de Endpoints

| Metodo   | Endpoint                                    | Descripcion                    |
|----------|---------------------------------------------|--------------------------------|
| `POST`   | `/v1/players/login`                         | Login/registro (principal)     |
| `POST`   | `/v1/players`                               | Crear jugador                  |
| `GET`    | `/v1/players/me`                            | Mi perfil                      |
| `PATCH`  | `/v1/players/{player_id}`                   | Actualizar jugador             |
| `DELETE` | `/v1/players/{player_id}`                   | Eliminar jugador               |
| `POST`   | `/v1/games`                                 | Crear partida                  |
| `GET`    | `/v1/games/{game_id}`                       | Obtener partida                |
| `GET`    | `/v1/games/player/{player_id}`              | Listar partidas del jugador    |
| `PATCH`  | `/v1/games/{game_id}`                       | Actualizar partida             |
| `POST`   | `/v1/games/{game_id}/level/start`           | Iniciar nivel                  |
| `POST`   | `/v1/games/{game_id}/level/complete`        | Completar nivel                |
| `DELETE` | `/v1/games/{game_id}`                       | Eliminar partida               |
| `POST`   | `/v1/events`                                | Crear evento                   |
| `POST`   | `/v1/events/batch`                          | Crear eventos en batch         |
| `GET`    | `/v1/events/game/{game_id}`                 | Eventos de partida             |
| `GET`    | `/v1/events/player/{player_id}`             | Eventos de jugador             |
| `GET`    | `/v1/events/game/{game_id}/type/{type}`     | Eventos por tipo               |
