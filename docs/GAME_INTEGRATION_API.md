# Triskel API - Guia de Integracion para el Juego

**Version:** 2.0
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

> **IMPORTANTE:** Guarda `player_id` y `player_token` cuando crees cuenta o hagas login. Son las credenciales para todas las peticiones posteriores.

---

## 1. JUGADORES

### 1.1 Crear Cuenta (Registro)

Crea un nuevo jugador con username y contraseña. Si el username ya existe, retorna error.

```
POST /v1/players
```

**Headers:** Ninguno (endpoint publico)

#### Request Body

| Campo      | Tipo     | Requerido | Restricciones        | Descripcion         |
|------------|----------|-----------|----------------------|---------------------|
| `username` | `string` | Si        | 3-20 caracteres      | Nombre de usuario   |
| `password` | `string` | Si        | 6-100 caracteres     | Contraseña          |
| `email`    | `string` | No        | Formato email valido | Email del jugador   |

```json
{
  "username": "jugador123",
  "password": "mi_password_seguro",
  "email": "jugador@email.com"
}
```

#### Response (201 Created)

| Campo          | Tipo     | Descripcion                              |
|----------------|----------|------------------------------------------|
| `player_id`    | `string` | UUID unico del jugador                   |
| `username`     | `string` | Nombre de usuario                        |
| `player_token` | `string` | Token secreto - **GUARDAR EN EL JUEGO** |

```json
{
  "player_id": "123e4567-e89b-12d3-a456-426614174000",
  "username": "jugador123",
  "player_token": "abc-def-token-secreto"
}
```

#### Errores

| Codigo | Descripcion                     |
|--------|---------------------------------|
| 400    | Username ya existe o invalido   |

---

### 1.2 Login

Inicia sesión con username y contraseña. Si las credenciales son incorrectas, retorna error.

```
POST /v1/players/login
```

**Headers:** Ninguno (endpoint publico)

#### Request Body

| Campo      | Tipo     | Requerido | Restricciones    | Descripcion      |
|------------|----------|-----------|------------------|------------------|
| `username` | `string` | Si        | 3-20 caracteres  | Nombre de usuario|
| `password` | `string` | Si        | 6-100 caracteres | Contraseña       |

```json
{
  "username": "jugador123",
  "password": "mi_password_seguro"
}
```

#### Response (200 OK)

| Campo            | Tipo      | Descripcion                                   |
|------------------|-----------|-----------------------------------------------|
| `player_id`      | `string`  | UUID unico del jugador                        |
| `username`       | `string`  | Nombre de usuario                             |
| `player_token`   | `string`  | Token secreto - **GUARDAR EN EL JUEGO**       |
| `active_game_id` | `string?` | ID de partida activa (null si no hay ninguna) |

```json
{
  "player_id": "123e4567-e89b-12d3-a456-426614174000",
  "username": "jugador123",
  "player_token": "abc-def-token-secreto",
  "active_game_id": "game-456-xyz"
}
```

> **NOTA:** Si `active_game_id != null`, el jugador tiene una partida en progreso que puede continuar.

#### Errores

| Codigo | Descripcion                        |
|--------|------------------------------------|
| 401    | Usuario o contraseña incorrectos   |

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

```json
{
  "player_id": "123e4567-e89b-12d3-a456-426614174000",
  "username": "jugador123",
  "password_hash": "$2b$12$...",
  "email": "jugador@email.com",
  "player_token": "abc-def-token",
  "created_at": "2024-01-01T12:00:00Z",
  "last_login": "2024-01-10T18:30:00Z",
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

> **NOTA:** El campo `password_hash` nunca debe mostrarse al jugador, es solo para uso interno.

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
  "total_playtime_seconds": 9000
}
```

#### Response (200 OK)

Retorna el objeto `Player` completo actualizado.

---

## 2. PARTIDAS

### 2.1 Crear Partida

Crea una nueva partida para el jugador autenticado.

```
POST /v1/games
```

#### Headers

```
X-Player-ID: {player_id}
X-Player-Token: {player_token}
```

#### Request Body

Vacio `{}` (el player_id se obtiene del token de autenticacion)

#### Response (201 Created)

```json
{
  "game_id": "game-123-abc",
  "player_id": "123e4567-e89b-12d3-a456-426614174000",
  "current_level": "hub_central",
  "status": "in_progress",
  "relics": [],
  "choices": {
    "senda_ebano": null,
    "fortaleza_gigantes": null,
    "aquelarre_sombras": null
  },
  "metrics": {
    "total_deaths": 0,
    "levels_completed": 0
  },
  "progress": {
    "levels_unlocked": ["hub_central"]
  },
  "total_time_seconds": 0,
  "created_at": "2024-01-10T18:30:00Z",
  "last_played_at": "2024-01-10T18:30:00Z"
}
```

---

### 2.2 Obtener Partida

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

| Parametro | Tipo     | Descripcion     |
|-----------|----------|-----------------|
| `game_id` | `string` | ID de la partida|

#### Response (200 OK)

Retorna el objeto `Game` completo.

---

### 2.3 Iniciar Nivel

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

| Campo   | Tipo     | Requerido | Descripcion                        |
|---------|----------|-----------|------------------------------------|
| `level` | `string` | Si        | Nombre del nivel (ver constantes)  |

```json
{
  "level": "senda_ebano"
}
```

#### Response (200 OK)

Retorna el objeto `Game` actualizado.

---

### 2.4 Completar Nivel

Marca el nivel como completado y guarda las decisiones/reliquias obtenidas.

```
POST /v1/games/{game_id}/level/complete
```

#### Headers

```
X-Player-ID: {player_id}
X-Player-Token: {player_token}
```

#### Request Body

| Campo          | Tipo      | Requerido | Descripcion                                        |
|----------------|-----------|-----------|---------------------------------------------------|
| `level`        | `string`  | Si        | Nombre del nivel completado                        |
| `time_seconds` | `integer` | Si        | Tiempo en segundos para completar el nivel         |
| `deaths`       | `integer` | Si        | Numero de muertes en este nivel (>= 0)            |
| `relic`        | `string`  | No        | Reliquia obtenida: "lirio", "hacha" o "manto"     |
| `choice`       | `string`  | No        | Decision moral tomada (depende del nivel)         |

```json
{
  "level": "senda_ebano",
  "time_seconds": 245,
  "deaths": 3,
  "relic": "lirio",
  "choice": "sanar"
}
```

#### Response (200 OK)

Retorna el objeto `Game` actualizado.

---

### 2.5 Actualizar Partida (Guardar Progreso)

Actualiza el estado de una partida.

```
PATCH /v1/games/{game_id}
```

#### Headers

```
X-Player-ID: {player_id}
X-Player-Token: {player_token}
```

#### Request Body (todos los campos opcionales)

| Campo                  | Tipo       | Descripcion                                  |
|------------------------|------------|----------------------------------------------|
| `current_level`        | `string`   | Nivel actual                                 |
| `status`               | `string`   | Estado: "in_progress", "completed", "failed" |
| `total_time_seconds`   | `integer`  | Tiempo total de juego en segundos            |
| `relics`               | `string[]` | Reliquias obtenidas                          |
| `choices`              | `object`   | Decisiones morales tomadas                   |
| `metrics.total_deaths` | `integer`  | Muertes acumuladas                           |
| `progress`             | `object`   | Progreso del jugador                         |

```json
{
  "current_level": "fortaleza_gigantes",
  "total_time_seconds": 1200,
  "metrics": {
    "total_deaths": 5
  }
}
```

#### Response (200 OK)

Retorna el objeto `Game` completo actualizado.

---

### 2.6 Completar Juego

Marca la partida como completada y actualiza las estadisticas del jugador.

```
POST /v1/games/{game_id}/complete
```

#### Headers

```
X-Player-ID: {player_id}
X-Player-Token: {player_token}
```

#### Request Body

Vacio `{}` - No se requieren campos adicionales.

```json
{}
```

#### Response (200 OK)

Retorna el objeto `Game` actualizado con:
- `status`: "completed"
- `ended_at`: Timestamp de finalizacion
- Estadisticas del jugador actualizadas automaticamente

---

### 2.7 Listar Partidas del Jugador

Obtiene todas las partidas de un jugador.

```
GET /v1/games/player/{player_id}
```

#### Headers

```
X-Player-ID: {player_id}
X-Player-Token: {player_token}
```

#### Query Parameters

| Parametro | Tipo     | Default | Descripcion                                  |
|-----------|----------|---------|----------------------------------------------|
| `status`  | `string` | -       | Filtrar por estado: "in_progress", "completed", "failed" |
| `limit`   | `integer`| 10      | Maximo numero de partidas a retornar         |

#### Response (200 OK)

```json
[
  {
    "game_id": "game-123",
    "status": "completed",
    "total_time_seconds": 3600,
    ...
  },
  {
    "game_id": "game-456",
    "status": "in_progress",
    "current_level": "aquelarre_sombras",
    ...
  }
]
```

---

### 2.8 Eliminar Partida

Elimina una partida del jugador.

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

Registra un evento de gameplay.

```
POST /v1/events
```

#### Headers

```
X-Player-ID: {player_id}
X-Player-Token: {player_token}
```

#### Request Body

| Campo        | Tipo     | Requerido | Descripcion                        |
|--------------|----------|-----------|------------------------------------|
| `game_id`    | `string` | Si        | ID de la partida                   |
| `player_id`  | `string` | Si        | ID del jugador                     |
| `event_type` | `string` | Si        | Tipo de evento (ver constantes)    |
| `level`      | `string` | No        | Nivel donde ocurrio                |
| `data`       | `object` | No        | Datos adicionales del evento       |

```json
{
  "game_id": "game-123-abc",
  "player_id": "550e8400-e29b-41d4-a716-446655440000",
  "event_type": "player_death",
  "level": "senda_ebano",
  "data": {
    "enemy_type": "espectro",
    "position_x": 120.5,
    "position_y": 45.2
  }
}
```

#### Response (201 Created)

Retorna el objeto `GameEvent` creado.

---

### 3.2 Crear Eventos en Batch

Crea multiples eventos de una sola vez (mejor rendimiento).

```
POST /v1/events/batch
```

#### Headers

```
X-Player-ID: {player_id}
X-Player-Token: {player_token}
```

#### Request Body

| Campo    | Tipo       | Requerido | Descripcion           |
|----------|------------|-----------|-----------------------|
| `events` | `array`    | Si        | Array de eventos      |

```json
{
  "events": [
    {
      "game_id": "game-123",
      "player_id": "550e8400-e29b-41d4-a716-446655440000",
      "event_type": "player_death",
      "level": "senda_ebano"
    },
    {
      "game_id": "game-123",
      "player_id": "550e8400-e29b-41d4-a716-446655440000",
      "event_type": "level_end",
      "level": "senda_ebano"
    }
  ]
}
```

#### Response (201 Created)

```json
{
  "created_count": 2,
  "events": [ /* array de eventos creados */ ]
}
```

---

### 3.3 Obtener Eventos de una Partida

Obtiene todos los eventos de una partida especifica.

```
GET /v1/events/game/{game_id}
```

#### Headers

```
X-Player-ID: {player_id}
X-Player-Token: {player_token}
```

#### Query Parameters

| Parametro | Tipo     | Default | Descripcion                          |
|-----------|----------|---------|--------------------------------------|
| `limit`   | `integer`| 100     | Maximo numero de eventos a retornar  |

#### Response (200 OK)

Array de objetos `GameEvent` ordenados por timestamp (mas reciente primero).

---

### 3.4 Obtener Eventos por Tipo

Obtiene eventos de una partida filtrados por tipo.

```
GET /v1/events/game/{game_id}/type/{event_type}
```

#### Headers

```
X-Player-ID: {player_id}
X-Player-Token: {player_token}
```

#### Path Parameters

| Parametro    | Tipo     | Descripcion            |
|--------------|----------|------------------------|
| `game_id`    | `string` | ID de la partida       |
| `event_type` | `string` | Tipo de evento filtrar |

#### Query Parameters

| Parametro | Tipo     | Default | Descripcion                          |
|-----------|----------|---------|--------------------------------------|
| `limit`   | `integer`| 100     | Maximo numero de eventos a retornar  |

#### Response (200 OK)

Array de objetos `GameEvent` filtrados por tipo.

---

## 4. CONSTANTES Y ENUMS

### Niveles (level)

| Valor                  | Descripcion               |
|------------------------|---------------------------|
| `hub_central`          | Hub central (inicio)      |
| `senda_ebano`          | Senda del Ébano           |
| `fortaleza_gigantes`   | Fortaleza de los Gigantes |
| `aquelarre_sombras`    | Aquelarre de las Sombras  |
| `claro_almas`          | Claro de las Almas        |

### Reliquias (relic)

| Valor   | Descripcion                    |
|---------|--------------------------------|
| `lirio` | Lirio Plateado (sanar/revelar) |
| `hacha` | Hacha Forjada (construir)      |
| `manto` | Manto Espectral (ocultar)      |

### Decisiones Morales (choice)

**Senda del Ébano:**
- `sanar` (buena) - Sanar al espíritu
- `forzar` (mala) - Forzar al espíritu

**Fortaleza de los Gigantes:**
- `construir` (buena) - Construir puente
- `destruir` (mala) - Destruir estructura

**Aquelarre de las Sombras:**
- `revelar` (buena) - Revelar verdad
- `ocultar` (mala) - Ocultar secreto

### Estados de Partida (status)

| Valor         | Descripcion                 |
|---------------|-----------------------------|
| `in_progress` | Partida en progreso         |
| `completed`   | Partida completada          |
| `failed`      | Partida fallida/abandonada  |

### Tipos de Eventos (event_type)

| Valor                | Descripcion               |
|----------------------|---------------------------|
| `player_death`       | Muerte del jugador        |
| `level_start`        | Inicio de nivel           |
| `level_end`          | Fin de nivel              |
| `npc_interaction`    | Interaccion con NPC       |
| `item_collected`     | Item recolectado          |
| `checkpoint_reached` | Checkpoint alcanzado      |
| `boss_encounter`     | Encuentro con jefe        |
| `custom_event`       | Evento personalizado      |

---

## 5. FLUJO DE INTEGRACION

### 5.1 Inicio de Sesion

```
INICIO DE APP
    |
    v
¿Tengo player_id y player_token guardados?
    |
    +-- NO --> Mostrar pantalla de inicio
    |           |
    |           +-- ¿Tiene cuenta? --> SI --> POST /v1/players/login
    |           |                              (guardar credenciales)
    |           |
    |           +-- ¿Tiene cuenta? --> NO --> POST /v1/players
    |                                         (crear cuenta y guardar credenciales)
    |
    +-- SI --> GET /v1/players/me (validar sesion)
                |
                +-- Error 401 --> Credenciales invalidas, volver a login
                |
                +-- OK --> Menu principal
```

### 5.2 Menu Principal

```
Credenciales validadas
    |
    v
GET /v1/players/me
    |
    +-- ¿Tiene active_game_id?
            |
            +-- SI --> GET /v1/games/{active_game_id}
            |           Mostrar "Continuar" + "Nueva Partida"
            |
            +-- NO --> Solo mostrar "Nueva Partida"
```

### 5.3 Nueva Partida

```
Usuario selecciona "Nueva Partida"
    |
    v
POST /v1/games
    |
    v
Guardar game_id localmente
    |
    v
Empezar en hub_central
```

### 5.4 Durante el Juego

```
Jugador entra a un nivel
    |
    v
POST /v1/games/{game_id}/level/start
    body: { "level": "senda_ebano" }
    |
    v
[JUGADOR JUEGA EL NIVEL]
    |
    +-- Registrar eventos (batch cada 30s o 10 eventos):
    |   POST /v1/events/batch
    |   body: { "events": [
    |     {"game_id": "...", "player_id": "...", "event_type": "player_death", "level": "senda_ebano"}
    |   ] }
    |
    +-- Guardar progreso cada X minutos:
        PATCH /v1/games/{game_id}
        body: { "total_time_seconds": 1800, "current_level": "..." }
    |
    v
Jugador completa nivel
    |
    v
POST /v1/games/{game_id}/level/complete
    body: {
      "level": "senda_ebano",
      "time_seconds": 245,
      "deaths": 3,
      "relic": "lirio",
      "choice": "sanar"
    }
```

### 5.5 Completar el Juego

```
Jugador llega al final
    |
    v
POST /v1/games/{game_id}/complete
    body: {}
    |
    v
API actualiza automaticamente:
    - game.status = "completed"
    - game.ended_at = timestamp actual
    - player.games_completed += 1
    - player.stats (moral_alignment, total_deaths, best_speedrun, etc.)
    |
    v
Mostrar pantalla de creditos/estadisticas
```

---

## 6. SISTEMA MORAL

### Calculo de Alineacion Moral

La alineación moral (`moral_alignment`) se calcula con la formula:

```
moral_alignment = (total_good_choices - total_bad_choices) / (total_good_choices + total_bad_choices)
```

**Rango:** -1.0 (completamente malo) a +1.0 (completamente bueno)

**Ejemplos:**
- 3 buenas, 0 malas → `(3 - 0) / (3 + 0) = 1.0` (santo)
- 0 buenas, 3 malas → `(0 - 3) / (0 + 3) = -1.0` (demonio)
- 2 buenas, 1 mala → `(2 - 1) / (2 + 1) = 0.33` (bueno)
- 1 buena, 2 malas → `(1 - 2) / (1 + 2) = -0.33` (malo)

### Finales basados en Alineacion

| Final | Condicion            | Descripcion                 |
|-------|----------------------|-----------------------------|
| 1     | moral_alignment > 0  | Final bueno (redención)     |
| 2     | moral_alignment == 0 | Final neutral (equilibrio)  |
| 3     | moral_alignment < 0  | Final malo (corrupción)     |

---

## 7. CODIGOS DE ERROR

| Codigo | Descripcion                                |
|--------|--------------------------------------------|
| 400    | Bad Request - Datos invalidos              |
| 401    | Unauthorized - Credenciales incorrectas    |
| 403    | Forbidden - Sin permisos                   |
| 404    | Not Found - Recurso no encontrado          |
| 500    | Internal Server Error - Error del servidor |

---

## Resumen de Endpoints

| Metodo   | Endpoint                                    | Descripcion                    |
|----------|---------------------------------------------|--------------------------------|
| `POST`   | `/v1/players`                               | Crear cuenta (registro)        |
| `POST`   | `/v1/players/login`                         | Login con username y password  |
| `GET`    | `/v1/players/me`                            | Mi perfil                      |
| `PATCH`  | `/v1/players/{player_id}`                   | Actualizar jugador             |
| `DELETE` | `/v1/players/{player_id}`                   | Eliminar jugador               |
| `POST`   | `/v1/games`                                 | Crear partida                  |
| `GET`    | `/v1/games/{game_id}`                       | Obtener partida                |
| `GET`    | `/v1/games/player/{player_id}`              | Listar partidas del jugador    |
| `PATCH`  | `/v1/games/{game_id}`                       | Actualizar partida             |
| `POST`   | `/v1/games/{game_id}/level/start`           | Iniciar nivel                  |
| `POST`   | `/v1/games/{game_id}/level/complete`        | Completar nivel                |
| `POST`   | `/v1/games/{game_id}/complete`              | Completar juego                |
| `DELETE` | `/v1/games/{game_id}`                       | Eliminar partida               |
| `POST`   | `/v1/events`                                | Crear evento                   |
| `POST`   | `/v1/events/batch`                          | Crear eventos en batch         |
| `GET`    | `/v1/events/game/{game_id}`                 | Eventos de partida             |
| `GET`    | `/v1/events/player/{player_id}`             | Eventos de jugador             |
| `GET`    | `/v1/events/game/{game_id}/type/{type}`     | Eventos por tipo               |

---

**Ultima actualizacion:** 2026-01-20
**Changelog v2.0:**
- Sistema de autenticación con password
- Eliminado endpoint de registro de dispositivo
- Login requiere username + password
- Registro (POST /v1/players) requiere password
- Eliminado campo display_name (se usa username)
