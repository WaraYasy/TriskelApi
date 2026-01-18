# Triskel API - Guia de Integracion para el Juego

## Indice

1. [Autenticacion](#autenticacion)
2. [Jugadores](#1-jugadores)
3. [Partidas](#2-partidas)
4. [Eventos](#3-eventos)
5. [Constantes y Enums](#4-constantes-y-enums)
6. [Flujo de Integracion](#5-flujo-de-integracion)
7. [Sistema Moral](#6-sistema-moral)

---

## Autenticacion

### Headers requeridos para jugadores

Todas las peticiones autenticadas requieren estos headers:

```
X-Player-ID: {player_id}
X-Player-Token: {player_token}
```

> **IMPORTANTE:** Guarda `player_id` y `player_token` cuando crees un jugador. Son las credenciales para todas las peticiones posteriores.

---

## 1. JUGADORES

### 1.1 Crear Jugador (Registro)

Crea un nuevo jugador. Si el usuario ya existe, debes usar las credenciales guardadas.

```
POST /v1/players
```

#### Request Body

| Campo      | Tipo     | Requerido | Descripcion                    |
|------------|----------|-----------|--------------------------------|
| `username` | `string` | Si        | Nombre de usuario (3-20 chars) |
| `email`    | `string` | No        | Email del jugador              |

```json
{
  "username": "jugador123",
  "email": "jugador@email.com"
}
```

#### Response (201 Created)

| Campo          | Tipo     | Descripcion                              |
|----------------|----------|------------------------------------------|
| `player_id`    | `string` | UUID unico del jugador                   |
| `username`     | `string` | Nombre de usuario                        |
| `player_token` | `string` | Token secreto - GUARDAR EN EL JUEGO      |

```json
{
  "player_id": "123e4567-e89b-12d3-a456-426614174000",
  "username": "jugador123",
  "player_token": "abc-def-ghi-token-secreto"
}
```

---

### 1.2 Obtener Mi Perfil (Verificar Sesion)

Verifica que las credenciales guardadas son validas y obtiene el perfil.

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
| `email`                  | `string\|null` | Email (opcional)                   |
| `created_at`             | `datetime`     | Fecha de creacion                  |
| `last_login`             | `datetime`     | Ultimo acceso                      |
| `total_playtime_seconds` | `integer`      | Tiempo total jugado en segundos    |
| `games_played`           | `integer`      | Numero de partidas iniciadas       |
| `games_completed`        | `integer`      | Numero de partidas completadas     |
| `stats`                  | `PlayerStats`  | Estadisticas agregadas (ver abajo) |

#### PlayerStats (objeto anidado)

| Campo                  | Tipo           | Descripcion                            |
|------------------------|----------------|----------------------------------------|
| `total_good_choices`   | `integer`      | Total decisiones buenas (todas partidas) |
| `total_bad_choices`    | `integer`      | Total decisiones malas (todas partidas)  |
| `total_deaths`         | `integer`      | Muertes acumuladas                     |
| `favorite_relic`       | `string\|null` | Reliquia mas recolectada               |
| `best_speedrun_seconds`| `integer\|null`| Mejor tiempo de completado             |
| `moral_alignment`      | `float`        | Alineacion moral (-1.0 a 1.0)          |

```json
{
  "player_id": "123e4567-e89b-12d3-a456-426614174000",
  "username": "jugador123",
  "email": "jugador@email.com",
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

### 1.3 Actualizar Jugador

Actualiza datos del jugador (campos opcionales).

```
PATCH /v1/players/{player_id}
```

#### Headers

```
X-Player-ID: {player_id}
X-Player-Token: {player_token}
```

#### Request Body (todos opcionales)

| Campo                    | Tipo          | Descripcion                   |
|--------------------------|---------------|-------------------------------|
| `username`               | `string`      | Nuevo nombre (3-20 chars)     |
| `email`                  | `string`      | Nuevo email                   |
| `total_playtime_seconds` | `integer`     | Tiempo total jugado           |
| `games_played`           | `integer`     | Partidas jugadas              |
| `games_completed`        | `integer`     | Partidas completadas          |
| `stats`                  | `PlayerStats` | Estadisticas (ver arriba)     |

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

#### Response (201 Created)

| Campo                   | Tipo           | Descripcion                          |
|-------------------------|----------------|--------------------------------------|
| `game_id`               | `string`       | UUID de la partida                   |
| `player_id`             | `string`       | UUID del jugador                     |
| `started_at`            | `datetime`     | Fecha/hora de inicio                 |
| `ended_at`              | `datetime\|null`| Fecha/hora de fin (null si activa)  |
| `status`                | `string`       | Estado de la partida                 |
| `completion_percentage` | `float`        | Porcentaje completado (0-100)        |
| `total_time_seconds`    | `integer`      | Tiempo total jugado                  |
| `levels_completed`      | `string[]`     | Lista de niveles completados         |
| `current_level`         | `string\|null` | Nivel actual                         |
| `choices`               | `GameChoices`  | Decisiones tomadas (ver abajo)       |
| `relics`                | `string[]`     | Reliquias recolectadas               |
| `boss_defeated`         | `boolean`      | Si derroto al jefe final             |
| `npcs_helped`           | `string[]`     | NPCs ayudados                        |
| `metrics`               | `GameMetrics`  | Metricas de juego (ver abajo)        |

#### GameChoices (objeto anidado)

| Campo               | Tipo           | Valores validos           |
|---------------------|----------------|---------------------------|
| `senda_ebano`       | `string\|null` | `"sanar"` \| `"forzar"`   |
| `fortaleza_gigantes`| `string\|null` | `"construir"` \| `"destruir"` |
| `aquelarre_sombras` | `string\|null` | `"revelar"` \| `"ocultar"` |

#### GameMetrics (objeto anidado)

| Campo             | Tipo                    | Descripcion                    |
|-------------------|-------------------------|--------------------------------|
| `total_deaths`    | `integer`               | Muertes totales en la partida  |
| `time_per_level`  | `object<string, int>`   | Segundos por nivel             |
| `deaths_per_level`| `object<string, int>`   | Muertes por nivel              |

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

#### Query Parameters

| Parametro | Tipo      | Default | Descripcion                  |
|-----------|-----------|---------|------------------------------|
| `limit`   | `integer` | 100     | Maximo de resultados         |

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
    },
    ...
  },
  {
    "game_id": "xyz-789",
    "status": "completed",
    ...
  }
]
```

> **TIP:** Filtra por `status === "in_progress"` para mostrar solo partidas activas.

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

#### Request Body

| Campo   | Tipo     | Requerido | Descripcion                |
|---------|----------|-----------|----------------------------|
| `level` | `string` | Si        | Nombre del nivel a iniciar |

**Niveles validos:** `hub_central`, `senda_ebano`, `fortaleza_gigantes`, `aquelarre_sombras`, `claro_almas`

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

#### Request Body

| Campo          | Tipo      | Requerido | Descripcion                           |
|----------------|-----------|-----------|---------------------------------------|
| `level`        | `string`  | Si        | Nivel completado                      |
| `time_seconds` | `integer` | Si        | Tiempo en segundos (0-86400)          |
| `deaths`       | `integer` | Si        | Muertes en el nivel (0-9999)          |
| `choice`       | `string`  | No        | Decision moral (si aplica al nivel)   |
| `relic`        | `string`  | No        | Reliquia obtenida (si aplica)         |

**Decisiones por nivel:**

| Nivel               | Opciones de `choice`        |
|---------------------|----------------------------|
| `senda_ebano`       | `"sanar"` o `"forzar"`     |
| `fortaleza_gigantes`| `"construir"` o `"destruir"`|
| `aquelarre_sombras` | `"revelar"` o `"ocultar"`  |

**Reliquias validas:** `lirio`, `hacha`, `manto`

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

#### Request Body (todos opcionales)

| Campo                   | Tipo       | Descripcion                              |
|-------------------------|------------|------------------------------------------|
| `status`                | `string`   | `"in_progress"`, `"completed"`, `"abandoned"` |
| `ended_at`              | `datetime` | Fecha/hora de finalizacion               |
| `completion_percentage` | `float`    | Porcentaje (0-100)                       |
| `total_time_seconds`    | `integer`  | Tiempo total (>= 0)                      |
| `current_level`         | `string`   | Nivel actual                             |
| `boss_defeated`         | `boolean`  | Si derroto al jefe                       |

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

#### Response (204 No Content)

Sin cuerpo de respuesta.

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

| event_type           | Descripcion                  | Ejemplo de `data`                        |
|----------------------|------------------------------|------------------------------------------|
| `player_death`       | Muerte del jugador           | `{"cause": "fall", "position_x": 100}`   |
| `level_start`        | Inicio de nivel              | `{}`                                     |
| `level_end`          | Fin de nivel                 | `{"completed": true}`                    |
| `item_collected`     | Recogio un item/reliquia     | `{"item_type": "relic", "relic_name": "lirio"}` |
| `checkpoint_reached` | Llego a checkpoint           | `{"checkpoint_id": "cp_01"}`             |
| `boss_encounter`     | Encontro al jefe             | `{"boss_name": "guardian"}`              |
| `npc_interaction`    | Interactuo con NPC           | `{"npc_id": "anciano", "action": "talk"}`|
| `custom_event`       | Evento personalizado         | `{"event_name": "game_ending", "ending_number": 2}` |

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

| Campo    | Tipo            | Requerido | Descripcion                    |
|----------|-----------------|-----------|--------------------------------|
| `events` | `EventCreate[]` | Si        | Array de eventos (1-100)       |

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

```json
{
  "created": 2,
  "events": [
    {"event_id": "evt-001", ...},
    {"event_id": "evt-002", ...}
  ]
}
```

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

#### Query Parameters

| Parametro | Tipo      | Default | Descripcion          |
|-----------|-----------|---------|----------------------|
| `limit`   | `integer` | 1000    | Maximo resultados    |

#### Response (200 OK)

Array de objetos `GameEvent`.

---

### 3.4 Obtener Eventos por Tipo

Filtra eventos de una partida por tipo.

```
GET /v1/events/game/{game_id}/type/{event_type}?limit=1000
```

#### Ejemplo

```
GET /v1/events/game/abc-123/type/player_death?limit=100
```

#### Response (200 OK)

Array de objetos `GameEvent` filtrados.

---

## 4. CONSTANTES Y ENUMS

### Niveles

| Valor                 | Descripcion           |
|-----------------------|-----------------------|
| `hub_central`         | Hub central (inicio)  |
| `senda_ebano`         | Primer nivel          |
| `fortaleza_gigantes`  | Segundo nivel         |
| `aquelarre_sombras`   | Tercer nivel          |
| `claro_almas`         | Nivel final (jefe)    |

### Estados de Partida

| Valor         | Descripcion              |
|---------------|--------------------------|
| `in_progress` | Partida en curso         |
| `completed`   | Partida completada       |
| `abandoned`   | Partida abandonada       |

### Decisiones Morales

| Nivel               | Buena       | Mala       |
|---------------------|-------------|------------|
| `senda_ebano`       | `sanar`     | `forzar`   |
| `fortaleza_gigantes`| `construir` | `destruir` |
| `aquelarre_sombras` | `revelar`   | `ocultar`  |

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
+-- Tiene credenciales guardadas? --+
|                                    |
| NO                                 | SI
v                                    v
POST /v1/players                GET /v1/players/me
(crear usuario)                 (verificar sesion)
    |                                |
    v                                v
Guardar player_id              OK? Continuar
y player_token                 Error? Borrar credenciales
localmente                           y crear nuevo
```

### 5.2 Menu Principal

```
GET /v1/games/player/{player_id}
    |
    v
Filtrar por status === "in_progress"
    |
    +-- Tiene partidas activas? --+
    |                              |
    | NO                           | SI
    v                              v
Mostrar solo                  Mostrar lista de
"Nueva Partida"               partidas + "Nueva"
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
    +-- Evento de muerte? --> POST /v1/events (player_death)
    |
    +-- Checkpoint? --> POST /v1/events (checkpoint_reached)
    |
    +-- Recogio reliquia? --> POST /v1/events (item_collected)
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
- 3 buenas = Final 1
- 2 buenas = Final 2
- 1 buena  = Final 3
- 0 buenas = Final 4
    |
    v
POST /v1/events
{
  "event_type": "custom_event",
  "level": "claro_almas",
  "data": {
    "event_name": "game_ending",
    "ending_number": 2
  }
}
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

La API no tiene endpoint de logout. Simplemente:

1. Borrar `player_id` y `player_token` del almacenamiento local
2. Redirigir a pantalla de inicio/login

---

## 6. SISTEMA MORAL

### Como funciona

La API **almacena** las decisiones pero **no calcula** el final. El calculo lo hace el juego.

### Decisiones almacenadas

Cada partida tiene un objeto `choices`:

```json
{
  "choices": {
    "senda_ebano": "sanar",        // buena
    "fortaleza_gigantes": "destruir", // mala
    "aquelarre_sombras": null        // aun no tomada
  }
}
```

### Calculo del final (en el juego)

```
Contar decisiones buenas:
- "sanar" = +1
- "construir" = +1
- "revelar" = +1

Total buenas | Final
-------------|-------
3            | 1 (mejor)
2            | 2
1            | 3
0            | 4 (peor)
```

### Alineacion moral del jugador

El campo `stats.moral_alignment` del jugador es un float de -1.0 a 1.0:

- **1.0** = Totalmente bueno
- **0.0** = Neutral
- **-1.0** = Totalmente malo

Se calcula con la formula:

```
moral_alignment = (total_good_choices - total_bad_choices) / (total_good_choices + total_bad_choices)
```

---

## Errores Comunes

### 401 Unauthorized

```json
{
  "detail": "Credenciales invalidas"
}
```

**Causa:** Headers `X-Player-ID` o `X-Player-Token` incorrectos o faltantes.

### 404 Not Found

```json
{
  "detail": "Jugador no encontrado"
}
```

**Causa:** El `player_id` no existe.

### 422 Validation Error

```json
{
  "detail": [
    {
      "loc": ["body", "level"],
      "msg": "Nivel 'invalid_level' no valido",
      "type": "value_error"
    }
  ]
}
```

**Causa:** Datos de entrada invalidos (nivel incorrecto, decision invalida, etc).

---

## Base URL

```
Produccion: https://tu-dominio.com
Desarrollo: http://localhost:8000
```

Todos los endpoints tienen el prefijo `/v1/`.
