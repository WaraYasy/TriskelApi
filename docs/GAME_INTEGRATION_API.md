# Triskel API - Guía de Integración para el Juego

**Versión:** 2.2 (Actualizado 2026-01-25)
**Base URL:** `http://localhost:8000` (desarrollo) | `https://tu-dominio.com` (producción)

## Índice

1. [Cómo Hacer Llamadas (Important!)](#cómo-hacer-llamadas-a-la-api)
2. [Autenticación](#autenticación)
3. [Jugadores](#1-jugadores)
4. [Partidas](#2-partidas)
5. [Sesiones](#3-sesiones)
6. [Eventos](#4-eventos)
7. [Constantes y Enums](#5-constantes-y-enums)
8. [Flujo de Integración](#6-flujo-de-integración)
9. [Retomar Partida (Lo más importante)](#retomar-partida-lo-más-importante)
10. [Sistema Moral](#7-sistema-moral)
11. [Códigos de Error](#8-códigos-de-error)

---

## Cómo Hacer Llamadas a la API

### Estructura básica de una solicitud HTTP

Todas las llamadas siguen este patrón:

```
METHOD /ruta/del/endpoint HTTP/1.1
Host: localhost:8000
Content-Type: application/json
[Headers de autenticación si aplica]

[Body JSON si aplica]
```

### Headers comunes

| Header              | Valor                      | Cuándo usar            |
|---------------------|---------------------------|------------------------|
| `Content-Type`      | `application/json`         | Siempre (excepto GET)  |
| `X-Player-ID`       | UUID del jugador           | Endpoints autenticados |
| `X-Player-Token`    | Token secreto del jugador  | Endpoints autenticados |

### Ejemplo completo en C# (Unity)

```csharp
using UnityEngine;
using System.Collections;

public class TriskelAPIClient : MonoBehaviour
{
    private string playerID;
    private string playerToken;
    private string baseURL = "http://localhost:8000";

    // Login
    public IEnumerator Login(string username, string password)
    {
        string url = baseURL + "/v1/players/login";
        
        var loginData = new { username = username, password = password };
        string jsonBody = JsonUtility.ToJson(loginData);
        
        using (UnityWebRequest request = new UnityWebRequest(url, "POST"))
        {
            request.uploadHandler = new UploadHandlerRaw(System.Text.Encoding.UTF8.GetBytes(jsonBody));
            request.downloadHandler = new DownloadHandlerBuffer();
            request.SetRequestHeader("Content-Type", "application/json");
            
            yield return request.SendWebRequest();
            
            if (request.result == UnityWebRequest.Result.Success)
            {
                var response = JsonUtility.FromJson<LoginResponse>(request.downloadHandler.text);
                playerID = response.player_id;
                playerToken = response.player_token;
                
                Debug.Log("Login exitoso! ID: " + playerID);
            }
        }
    }

    // Cargar partida existente
    public IEnumerator LoadGame(string gameID)
    {
        string url = baseURL + "/v1/games/" + gameID;
        
        using (UnityWebRequest request = UnityWebRequest.Get(url))
        {
            request.SetRequestHeader("X-Player-ID", playerID);
            request.SetRequestHeader("X-Player-Token", playerToken);
            
            yield return request.SendWebRequest();
            
            if (request.result == UnityWebRequest.Result.Success)
            {
                var gameData = JsonUtility.FromJson<GameResponse>(request.downloadHandler.text);
                
                Debug.Log("Partida cargada. Nivel actual: " + gameData.current_level);
                Debug.Log("Tiempo total: " + gameData.total_time_seconds + " segundos");
                Debug.Log("Reliquias: " + string.Join(", ", gameData.relics));
                
                // Restaurar el juego con esta información
                RestoreGameState(gameData);
            }
        }
    }

    void RestoreGameState(GameResponse gameData)
    {
        // Cargar el nivel indicado
        LevelManager.LoadLevel(gameData.current_level);
        
        // Restaurar reliquias en inventario
        foreach (string relic in gameData.relics)
        {
            InventoryManager.AddRelic(relic);
        }
        
        // Restaurar tiempo en UI
        UIManager.SetPlaytime(gameData.total_time_seconds);
    }
}

[System.Serializable]
public class LoginResponse
{
    public string player_id;
    public string player_token;
    public string username;
}

[System.Serializable]
public class GameResponse
{
    public string game_id;
    public string current_level;
    public int total_time_seconds;
    public string[] relics;
    public string[] levels_completed;
    public GameChoices choices;
}

[System.Serializable]
public class GameChoices
{
    public string senda_ebano;
    public string fortaleza_gigantes;
    public string aquelarre_sombras;
}
```

### Ejemplo en Python

```python
import requests
import json

BASE_URL = "http://localhost:8000"

# Login
response = requests.post(
    f"{BASE_URL}/v1/players/login",
    json={"username": "jugador123", "password": "mi_password"}
)
data = response.json()
player_id = data["player_id"]
player_token = data["player_token"]

# Obtener partida activa
headers = {
    "X-Player-ID": player_id,
    "X-Player-Token": player_token
}
response = requests.get(f"{BASE_URL}/v1/games/{game_id}", headers=headers)
game_data = response.json()

print(f"Nivel actual: {game_data['current_level']}")
print(f"Tiempo total: {game_data['total_time_seconds']}s")
print(f"Reliquias: {game_data['relics']}")
```

### Respuestas de la API

Todas las respuestas son JSON:

```json
{
  "status_code": 200,
  "data": { /* objeto solicitado */ },
  "error": null
}
```

Para errores:

```json
{
  "status_code": 400,
  "data": null,
  "error": "Descripción del error"
}
```

---

## Autenticación

### Headers requeridos para jugadores

Todas las peticiones autenticadas requieren estos dos headers:

```
X-Player-ID: {player_id}
X-Player-Token: {player_token}
```

| Header           | Origen              | Duración          | Almacenamiento          |
|------------------|---------------------|-------------------|-------------------------|
| `X-Player-ID`    | Respuesta de login/registro | Indefinida  | PlayerPrefs / LocalStorage |
| `X-Player-Token` | Respuesta de login/registro | Indefinida  | PlayerPrefs / LocalStorage |

⚠️ **CRÍTICO:** Guarda `player_id` y `player_token` de forma persistente. Los necesitarás en CADA sesión del jugador.

---

---

## 1. JUGADORES

### 1.1 Crear Cuenta (Registro)

Crea un nuevo jugador con username y contraseña. Si el username ya existe, retorna error.

**Endpoint:** `POST /v1/players`

**Autenticación:** No requerida (público)

#### Request Body

```json
{
  "username": "jugador123",
  "password": "mi_password_seguro",
  "email": "jugador@email.com"
}
```

| Campo      | Tipo     | Requerido | Restricciones        | Descripción         |
|------------|----------|-----------|----------------------|---------------------|
| `username` | `string` | Sí        | 3-20 caracteres      | Nombre de usuario   |
| `password` | `string` | Sí        | 6-100 caracteres     | Contraseña segura   |
| `email`    | `string` | No        | Formato email válido | Email del jugador   |

#### Response (201 Created)

```json
{
  "player_id": "123e4567-e89b-12d3-a456-426614174000",
  "username": "jugador123",
  "player_token": "abc-def-token-secreto"
}
```

| Campo          | Tipo     | Descripción                                |
|----------------|----------|--------------------------------------------|
| `player_id`    | `string` | UUID único del jugador                     |
| `username`     | `string` | Nombre de usuario confirmado               |
| `player_token` | `string` | Token secreto - **GUARDAR LOCALMENTE**     |

⚠️ **IMPORTANTE:** Guarda `player_id` y `player_token` en almacenamiento local. Los necesitarás en todas las solicitudes posteriores.

#### Errores

| Código | Descripción                     | Solución                              |
|--------|--------------------------------|---------------------------------------|
| 400    | Username ya existe o inválido   | Elige otro username                   |
| 422    | Datos inválidos                 | Verifica el formato de los datos      |

#### Ejemplo cURL

```bash
curl -X POST http://localhost:8000/v1/players \
  -H "Content-Type: application/json" \
  -d '{
    "username": "jugador123",
    "password": "mi_password_seguro",
    "email": "jugador@email.com"
  }'
```

---

### 1.2 Login (Inicio de Sesión)

Inicia sesión con username y contraseña. Retorna las credenciales necesarias para hacer llamadas autenticadas.

**Endpoint:** `POST /v1/players/login`

**Autenticación:** No requerida (público)

#### Request Body

```json
{
  "username": "jugador123",
  "password": "mi_password_seguro"
}
```

| Campo      | Tipo     | Requerido | Restricciones    | Descripción       |
|------------|----------|-----------|------------------|-------------------|
| `username` | `string` | Sí        | 3-20 caracteres  | Nombre de usuario |
| `password` | `string` | Sí        | 6-100 caracteres | Contraseña        |

#### Response (200 OK)

```json
{
  "player_id": "123e4567-e89b-12d3-a456-426614174000",
  "username": "jugador123",
  "player_token": "abc-def-token-secreto",
  "active_game_id": "game-456-xyz"
}
```

| Campo            | Tipo      | Descripción                                        |
|------------------|-----------|-----------------------------------------------------|
| `player_id`      | `string`  | UUID único del jugador                             |
| `username`       | `string`  | Nombre de usuario confirmado                       |
| `player_token`   | `string`  | Token secreto - **GUARDAR LOCALMENTE**             |
| `active_game_id` | `string?` | ID de partida activa (null si no hay activa)       |

🎮 **IMPORTANTE - RETOMAR PARTIDA:** Si `active_game_id` no es null, el jugador tiene una partida en progreso. Usa este ID para obtener el estado actual y permitir que continúe jugando.

#### Errores

| Código | Descripción                  | Solución                   |
|--------|------------------------------|----------------------------|
| 401    | Usuario o contraseña incorrectos | Verifica las credenciales |
| 404    | Usuario no encontrado        | Crea una cuenta primero    |

#### Ejemplo cURL

```bash
curl -X POST http://localhost:8000/v1/players/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "jugador123",
    "password": "mi_password_seguro"
  }'
```

---

### 1.3 Obtener Mi Perfil (Verificar Sesión y Estado Actual)

Valida que las credenciales del jugador son correctas y obtiene toda la información de su perfil, incluyendo estadísticas y progreso.

**Endpoint:** `GET /v1/players/me`

**Autenticación:** Requerida (Player Token)

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

| Campo                   | Tipo     | Descripción                              |
|-------------------------|----------|------------------------------------------|
| `player_id`             | `string` | UUID único del jugador                   |
| `username`              | `string` | Nombre de usuario                        |
| `email`                 | `string` | Email del jugador (si está disponible)   |
| `player_token`          | `string` | Token de autenticación                   |
| `created_at`            | `datetime` | Fecha de creación de cuenta              |
| `last_login`            | `datetime` | Última vez que inició sesión             |
| `total_playtime_seconds`| `integer` | Segundos totales jugados en el juego     |
| `games_played`          | `integer` | Total de partidas iniciadas              |
| `games_completed`       | `integer` | Total de partidas completadas            |
| `stats.total_good_choices` | `integer` | Decisiones morales buenas tomadas        |
| `stats.total_bad_choices`  | `integer` | Decisiones morales malas tomadas         |
| `stats.total_deaths`    | `integer` | Muertes acumuladas en todas las partidas |
| `stats.favorite_relic`  | `string` | Reliquia favorita (lirio, hacha, manto) |
| `stats.best_speedrun_seconds` | `integer` | Tiempo más rápido en completar juego  |
| `stats.moral_alignment` | `float` | Alineación moral (-1.0 a +1.0)          |

#### Errores

| Código | Descripción              | Solución                   |
|--------|--------------------------|----------------------------|
| 401    | Token inválido o expirado | Vuelve a hacer login       |
| 404    | Jugador no encontrado    | Contacta con soporte       |

#### Ejemplo cURL

```bash
curl -X GET http://localhost:8000/v1/players/me \
  -H "X-Player-ID: 123e4567-e89b-12d3-a456-426614174000" \
  -H "X-Player-Token: abc-def-token-secreto"
```

---

### 1.4 Actualizar Perfil del Jugador

Actualiza datos del jugador (email, nombre de usuario, etc).

**Endpoint:** `PATCH /v1/players/{player_id}`

**Autenticación:** Requerida (Player Token)

#### Headers

```
X-Player-ID: {player_id}
X-Player-Token: {player_token}
```

#### Path Parameters

| Parámetro   | Tipo     | Descripción      |
|-------------|----------|------------------|
| `player_id` | `string` | UUID del jugador |

#### Request Body (todos los campos son opcionales)

```json
{
  "username": "nuevo_username",
  "email": "nuevo_email@example.com"
}
```

| Campo   | Tipo     | Restricciones        | Descripción        |
|---------|----------|----------------------|--------------------|
| `username` | `string` | 3-20 caracteres    | Nuevo nombre de usuario |
| `email`    | `string` | Formato email válido | Nuevo email        |

#### Response (200 OK)

Retorna el objeto completo del `Player` actualizado con los nuevos valores.

#### Errores

| Código | Descripción                     | Solución                      |
|--------|--------------------------------|-------------------------------|
| 400    | Datos inválidos                | Verifica el formato de datos  |
| 403    | No tienes permiso              | Solo puedes editar tu perfil  |
| 404    | Jugador no encontrado          | Contacta con soporte          |

---

## 2. PARTIDAS

Las partidas representan una jugada completa del juego desde el inicio hasta el final (o abandono). Cada partida tiene su propio estado, progreso y decisiones.

### 2.1 Crear Partida (Nueva Partida)

Crea una nueva partida para el jugador autenticado. Se inicia en el hub central.

**Endpoint:** `POST /v1/games`

**Autenticación:** Requerida (Player Token)

#### Headers

```
X-Player-ID: {player_id}
X-Player-Token: {player_token}
```

#### Request Body

```json
{}
```

El `player_id` se extrae automáticamente del token de autenticación.

#### Response (201 Created)

```json
{
  "game_id": "550e8400-e29b-41d4-a716-446655440000",
  "player_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "in_progress",
  "current_level": "hub_central",
  "started_at": "2024-01-10T18:30:00Z",
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

| Campo                   | Tipo          | Descripción                                |
|-------------------------|---------------|---------------------------------------------|
| `game_id`               | `string`      | UUID único de la partida                    |
| `player_id`             | `string`      | UUID del jugador propietario                |
| `status`                | `string`      | Estado: "in_progress" (nueva partida)       |
| `current_level`         | `string`      | Nivel actual (siempre "hub_central" para nueva) |
| `started_at`            | `datetime`    | Timestamp de inicio                         |
| `ended_at`              | `datetime?`   | Timestamp de finalización (null si activa)  |
| `total_time_seconds`    | `integer`     | Segundos totales de juego                   |
| `completion_percentage` | `float`       | Porcentaje de completado (0-100)            |
| `levels_completed`      | `string[]`    | Array de niveles completados                |
| `relics`                | `string[]`    | Array de reliquias obtenidas                |
| `boss_defeated`         | `boolean`     | Si ha derrotado al jefe final               |
| `npcs_helped`           | `string[]`    | Array de NPCs ayudados                      |
| `choices`               | `object`      | Decisiones morales por nivel                |
| `metrics`               | `object`      | Métricas de juego (muertes, tiempo, etc)    |

#### Errores

| Código | Descripción              | Solución                |
|--------|--------------------------|-------------------------|
| 401    | No autenticado           | Valida tu token         |
| 500    | Error del servidor       | Contacta con soporte    |

---

### 2.2 Obtener Partida (Cargar Estado Actual)

Obtiene el estado completo de una partida específica. **Este es el endpoint clave para retomar una partida que fue pausada.**

**Endpoint:** `GET /v1/games/{game_id}`

**Autenticación:** Requerida (Player Token)

#### Headers

```
X-Player-ID: {player_id}
X-Player-Token: {player_token}
```

#### Path Parameters

| Parámetro | Tipo     | Descripción     |
|-----------|----------|-----------------|
| `game_id` | `string` | ID de la partida|

#### Response (200 OK)

```json
{
  "game_id": "550e8400-e29b-41d4-a716-446655440000",
  "player_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "in_progress",
  "current_level": "senda_ebano",
  "started_at": "2024-01-10T18:30:00Z",
  "ended_at": null,
  "total_time_seconds": 3600,
  "completion_percentage": 33.3,
  "levels_completed": ["hub_central"],
  "relics": ["lirio"],
  "boss_defeated": false,
  "npcs_helped": [],
  "choices": {
    "senda_ebano": "sanar",
    "fortaleza_gigantes": null,
    "aquelarre_sombras": null
  },
  "metrics": {
    "total_deaths": 5,
    "time_per_level": {
      "hub_central": 120,
      "senda_ebano": 3480
    },
    "deaths_per_level": {
      "hub_central": 0,
      "senda_ebano": 5
    }
  }
}
```

📌 **Para retomar una partida, use esta información:**
- `current_level`: El nivel donde el jugador se quedó
- `total_time_seconds`: Tiempo acumulado (mostrar en UI)
- `relics`: Reliquias que ya ha recolectado
- `choices`: Decisiones ya tomadas (mostrar en diálogos/cinemáticas)
- `metrics`: Muertes y tiempos por nivel (para estadísticas)
- `completion_percentage`: Progreso general de la partida

#### Errores

| Código | Descripción              | Solución                   |
|--------|--------------------------|----------------------------|
| 401    | No autenticado           | Valida tu token            |
| 403    | No tu partida            | Solo puedes ver tus partidas |
| 404    | Partida no encontrada    | ID de partida inválido     |

#### Ejemplo cURL

```bash
curl -X GET http://localhost:8000/v1/games/550e8400-e29b-41d4-a716-446655440000 \
  -H "X-Player-ID: 123e4567-e89b-12d3-a456-426614174000" \
  -H "X-Player-Token: abc-def-token-secreto"
```

---

### 2.3 Actualizar Progreso de Partida (Guardar Progreso)

#### Headers

```
X-Player-ID: {player_id}
X-Player-Token: {player_token}
```

#### Request Body (todos los campos opcionales)

Use este endpoint para guardar el progreso actual mientras el jugador está jugando. Útil para detectar cambios de nivel, guardar puntos de progreso, etc.

```json
{
  "current_level": "fortaleza_gigantes",
  "total_time_seconds": 1200,
  "status": "in_progress",
  "metrics": {
    "total_deaths": 5
  }
}
```

| Campo                   | Tipo       | Descripción                               |
|-------------------------|------------|-------------------------------------------|
| `current_level`         | `string`   | Nivel actual del jugador                  |
| `status`                | `string`   | "in_progress", "completed", o "abandoned" |
| `total_time_seconds`    | `integer`  | Tiempo total jugado hasta ahora           |
| `completion_percentage` | `float`    | Porcentaje de completado (0-100)          |
| `metrics.total_deaths`  | `integer`  | Muertes acumuladas en la partida          |

#### Response (200 OK)

```json
{
  "game_id": "550e8400-e29b-41d4-a716-446655440000",
  "player_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "in_progress",
  "current_level": "fortaleza_gigantes",
  "total_time_seconds": 1200,
  "completion_percentage": 50.0,
  "levels_completed": ["hub_central", "senda_ebano"],
  "relics": ["lirio"],
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

#### Errores

| Código | Descripción              | Solución                   |
|--------|--------------------------|----------------------------|
| 401    | No autenticado           | Valida tu token            |
| 403    | No tu partida            | Solo puedes editar tus partidas |
| 404    | Partida no encontrada    | ID de partida inválido     |

---

### 2.4 Iniciar Nivel

Marca el inicio de un nivel específico en la partida. Llama a este endpoint cuando el jugador entra a un nivel.

**Endpoint:** `POST /v1/games/{game_id}/level/start`

**Autenticación:** Requerida (Player Token)

#### Headers

```
X-Player-ID: {player_id}
X-Player-Token: {player_token}
```

#### Path Parameters

| Parámetro | Tipo     | Descripción     |
|-----------|----------|-----------------|
| `game_id` | `string` | ID de la partida|

#### Request Body

```json
{
  "level": "senda_ebano"
}
```

| Campo   | Tipo     | Requerido | Descripción                        |
|---------|----------|-----------|-----------------------------------|
| `level` | `string` | Sí        | Nombre del nivel a iniciar         |

#### Response (200 OK)

```json
{
  "game_id": "550e8400-e29b-41d4-a716-446655440000",
  "current_level": "senda_ebano",
  "status": "in_progress",
  "message": "Nivel iniciado correctamente"
}
```

---

### 2.5 Completar Nivel

Marca un nivel como completado y registra las decisiones morales, reliquias obtenidas y métricas del nivel.

**Endpoint:** `POST /v1/games/{game_id}/level/complete`

**Autenticación:** Requerida (Player Token)

#### Headers

```
X-Player-ID: {player_id}
X-Player-Token: {player_token}
```

#### Path Parameters

| Parámetro | Tipo     | Descripción     |
|-----------|----------|-----------------|
| `game_id` | `string` | ID de la partida|

#### Request Body

```json
{
  "level": "senda_ebano",
  "time_seconds": 580,
  "deaths": 5,
  "relic": "lirio",
  "choice": "sanar"
}
```

| Campo         | Tipo     | Requerido | Descripción                                 |
|---------------|----------|-----------|---------------------------------------------|
| `level`       | `string` | Sí        | Nombre del nivel completado                 |
| `time_seconds`| `integer`| Sí        | Segundos que tomó completar el nivel        |
| `deaths`      | `integer`| Sí        | Número de muertes en este nivel (>= 0)      |
| `relic`       | `string` | No        | Reliquia obtenida: "lirio", "hacha", "manto"|
| `choice`      | `string` | No        | Decisión moral tomada (buena o mala)        |

#### Response (200 OK)

```json
{
  "game_id": "550e8400-e29b-41d4-a716-446655440000",
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

---

### 2.6 Completar Juego (Partida Terminada)

Marca la partida como completada cuando el jugador llega al final y derrota al jefe. Actualiza automáticamente las estadísticas del jugador.

**Endpoint:** `POST /v1/games/{game_id}/complete`

**Autenticación:** Requerida (Player Token)

#### Headers

```
X-Player-ID: {player_id}
X-Player-Token: {player_token}
```

#### Path Parameters

| Parámetro | Tipo     | Descripción     |
|-----------|----------|-----------------|
| `game_id` | `string` | ID de la partida|

#### Request Body

```json
{}
```

No se requieren parámetros adicionales.

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
| `limit`   | `integer`| 100     | Maximo numero de partidas a retornar         |

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

## 3. SESIONES

Las sesiones representan periodos continuos de tiempo en los que el jugador está activamente jugando (desde que abre el juego hasta que lo cierra). Permiten rastrear métricas como tiempo de juego por plataforma, sesiones concurrentes, y patrones de uso.

### 3.1 Iniciar Sesión de Juego

Inicia una nueva sesión de juego cuando el jugador abre la aplicación.

```
POST /v1/sessions
```

#### Headers

```
X-Player-ID: {player_id}
X-Player-Token: {player_token}
```

#### Request Body

| Campo      | Tipo       | Requerido | Descripcion                           |
|------------|------------|-----------|---------------------------------------|
| `game_id`  | `string`   | Si        | ID de la partida activa               |
| `platform` | `string`   | Si        | Plataforma: "windows" o "android"     |

```json
{
  "game_id": "game-123-abc",
  "platform": "windows"
}
```

#### Response (201 Created)

```json
{
  "session_id": "s-123e4567-e89b-12d3-a456",
  "player_id": "123e4567-e89b-12d3-a456-426614174000",
  "game_id": "game-123-abc",
  "started_at": "2024-01-20T10:30:00Z",
  "ended_at": null,
  "duration_seconds": 0,
  "platform": "windows",
  "is_active": true
}
```

> **NOTA:** La API cierra automáticamente cualquier sesión huérfana (sesiones que quedaron abiertas por crash del cliente) antes de crear una nueva.

---

### 3.2 Terminar Sesión de Juego

Termina una sesión activa cuando el jugador cierra la aplicación.

```
PATCH /v1/sessions/{session_id}/end
```

#### Headers

```
X-Player-ID: {player_id}
X-Player-Token: {player_token}
```

#### Path Parameters

| Parametro    | Tipo     | Descripcion       |
|--------------|----------|-------------------|
| `session_id` | `string` | ID de la sesion   |

#### Request Body

Vacio `{}`

#### Response (200 OK)

```json
{
  "session_id": "s-123e4567-e89b-12d3-a456",
  "player_id": "123e4567-e89b-12d3-a456-426614174000",
  "game_id": "game-123-abc",
  "started_at": "2024-01-20T10:30:00Z",
  "ended_at": "2024-01-20T12:30:00Z",
  "duration_seconds": 7200,
  "platform": "windows",
  "is_active": false
}
```

#### Errores

| Codigo | Descripcion                                |
|--------|--------------------------------------------|
| 400    | La sesión ya está cerrada                  |
| 403    | No tienes permisos para cerrar esta sesión |
| 404    | Sesión no encontrada                       |

---

### 3.3 Obtener Sesiones de un Jugador

Obtiene todas las sesiones de un jugador (ordenadas por más reciente primero).

```
GET /v1/sessions/player/{player_id}
```

#### Headers

```
X-Player-ID: {player_id}
X-Player-Token: {player_token}
```

#### Path Parameters

| Parametro   | Tipo     | Descripcion      |
|-------------|----------|------------------|
| `player_id` | `string` | ID del jugador   |

#### Query Parameters

| Parametro | Tipo      | Default | Descripcion                         |
|-----------|-----------|---------|-------------------------------------|
| `limit`   | `integer` | 100     | Maximo numero de sesiones a retornar|

#### Response (200 OK)

```json
[
  {
    "session_id": "s-123e4567-e89b-12d3-a456",
    "player_id": "123e4567-e89b-12d3-a456-426614174000",
    "game_id": "game-123-abc",
    "started_at": "2024-01-20T10:30:00Z",
    "ended_at": "2024-01-20T12:30:00Z",
    "duration_seconds": 7200,
    "platform": "windows",
    "is_active": false
  },
  {
    "session_id": "s-987e6543-e21b-43c1-b654",
    "player_id": "123e4567-e89b-12d3-a456-426614174000",
    "game_id": "game-123-abc",
    "started_at": "2024-01-19T14:00:00Z",
    "ended_at": "2024-01-19T16:00:00Z",
    "duration_seconds": 7200,
    "platform": "android",
    "is_active": false
  }
]
```

> **NOTA:** Solo puedes ver tus propias sesiones (a menos que seas administrador).

---

### 3.4 Obtener Sesiones de una Partida

Obtiene todas las sesiones asociadas a una partida específica.

```
GET /v1/sessions/game/{game_id}
```

#### Headers

```
X-Player-ID: {player_id}
X-Player-Token: {player_token}
```

#### Path Parameters

| Parametro | Tipo     | Descripcion       |
|-----------|----------|-------------------|
| `game_id` | `string` | ID de la partida  |

#### Query Parameters

| Parametro | Tipo      | Default | Descripcion                         |
|-----------|-----------|---------|-------------------------------------|
| `limit`   | `integer` | 100     | Maximo numero de sesiones a retornar|

#### Response (200 OK)

Array de objetos `SessionResponse` ordenados por fecha de inicio (más reciente primero).

> **NOTA:** Solo puedes ver sesiones de tus propias partidas (a menos que seas administrador).

---

## 4. EVENTOS

### 4.1 Crear Evento

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

### 4.2 Crear Eventos en Batch

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
[
  {
    "event_id": "event-uuid-1",
    "game_id": "game-123",
    "player_id": "550e8400-e29b-41d4-a716-446655440000",
    "event_type": "player_death",
    "level": "senda_ebano",
    "timestamp": "2024-01-20T10:30:15Z",
    "data": null
  },
  {
    "event_id": "event-uuid-2",
    "game_id": "game-123",
    "player_id": "550e8400-e29b-41d4-a716-446655440000",
    "event_type": "level_end",
    "level": "senda_ebano",
    "timestamp": "2024-01-20T10:30:16Z",
    "data": null
  }
]
```

---

### 4.3 Obtener Eventos de una Partida

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
| `limit`   | `integer`| 1000    | Maximo numero de eventos a retornar  |

#### Response (200 OK)

Array de objetos `GameEvent` ordenados por timestamp (mas reciente primero).

---

### 4.4 Obtener Eventos por Tipo

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
| `limit`   | `integer`| 1000    | Maximo numero de eventos a retornar  |

#### Response (200 OK)

Array de objetos `GameEvent` filtrados por tipo.

---

## 5. CONSTANTES Y ENUMS

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

### Plataformas (platform)

| Valor     | Descripcion           |
|-----------|-----------------------|
| `windows` | Cliente de Windows    |
| `android` | Cliente de Android    |

---

## 6. FLUJO DE INTEGRACIÓN

### 6.1 Inicio de Sesión (Login/Registro)

Este es el primer paso. El juego debe obtener y guardar las credenciales del jugador.

```
INICIO DE APP
    |
    v
¿Tengo player_id y player_token guardados localmente?
    |
    +-- NO --> Mostrar pantalla de inicio
    |           |
    |           +-- ¿Usuario tiene cuenta? 
    |           |    |
    |           |    +-- SÍ --> POST /v1/players/login
    |           |    |          Headers: ninguno
    |           |    |          Body: { "username": "...", "password": "..." }
    |           |    |          |
    |           |    |          +-- Guardar player_id y player_token localmente
    |           |    |
    |           |    +-- NO --> POST /v1/players (crear cuenta)
    |           |                Headers: ninguno
    |           |                Body: { "username": "...", "password": "...", "email": "..." }
    |           |                |
    |           |                +-- Guardar player_id y player_token localmente
    |
    +-- SÍ --> GET /v1/players/me (validar sesión)
                Headers: X-Player-ID, X-Player-Token
                |
                +-- Error 401 --> Credenciales inválidas, volver a login
                |
                +-- OK (200) --> Continuar al Menú Principal
```

### 6.2 Menú Principal (Detectar Partida Activa)

Después de validar las credenciales, el juego debe verificar si hay una partida en progreso que el jugador pueda retomar.

```
Credenciales validadas (GET /v1/players/me OK)
    |
    v
Verificar si hay partida activa:
    - En login: revisar campo "active_game_id" de la respuesta
    - En cualquier momento: GET /v1/games/player/{player_id}
    |
    +-- ¿Hay partida activa? (active_game_id != null)
            |
            +-- SÍ --> GET /v1/games/{active_game_id}
            |           |
            |           +-- Cargar el estado completo:
            |           |    - current_level: nivel donde se quedó
            |           |    - total_time_seconds: tiempo acumulado
            |           |    - levels_completed: niveles ya completados
            |           |    - relics: reliquias obtenidas
            |           |    - choices: decisiones ya tomadas
            |           |    - metrics: estadísticas del progreso
            |           |
            |           +-- Mostrar opción "CONTINUAR PARTIDA" + "NUEVA PARTIDA"
            |
            +-- NO --> Solo mostrar "NUEVA PARTIDA"
```

### 6.3 Retomar Partida (Lo más importante para el juego)

**FLUJO PARA CONTINUAR UNA PARTIDA EXISTENTE:**

```
Usuario selecciona "CONTINUAR PARTIDA"
    |
    v
GET /v1/games/{game_id}
    Headers: X-Player-ID, X-Player-Token
    |
    v
Respuesta contiene:
    - current_level: Nivel donde estaba
    - total_time_seconds: Tiempo acumulado
    - levels_completed: Niveles ya hechos
    - relics: Reliquias obtenidas
    - choices: Decisiones previas (para mostrar en diálogos)
    - boss_defeated: Si ya derrotó el jefe
    - completion_percentage: Progreso general
    |
    v
EN EL JUEGO:
    1. Cargar el nivel indicado en "current_level"
    2. Restaurar el estado del jugador (HP, posición inicial, etc.)
    3. Mostrar reliquias obtenidas en UI
    4. Si hay decisiones previas, mostrar las consecuencias en diálogos
    5. Restaurar tiempo total en contador (opcional)
    |
    v
POST /v1/sessions
    Headers: X-Player-ID, X-Player-Token
    Body: { "game_id": "...", "platform": "windows" }
    |
    v
Guardar session_id localmente para después terminar la sesión
    |
    v
COMENZAR A JUGAR en el nivel indicado
```

**Ejemplo de cómo restaurar estado:**

```json
// GET /v1/games/{game_id} responde con:
{
  "game_id": "550e8400-e29b-41d4-a716-446655440000",
  "current_level": "senda_ebano",  // <- Cargar este nivel
  "total_time_seconds": 600,       // <- Mostrar en UI: 10:00 minutos
  "levels_completed": ["hub_central"],  // <- Ya completó hub_central
  "relics": ["lirio"],             // <- Mostrar en inventario
  "choices": {
    "senda_ebano": "sanar",        // <- Ya hizo esta decisión
    "fortaleza_gigantes": null,    // <- Aún no ha llegado aquí
    "aquelarre_sombras": null
  },
  "metrics": {
    "total_deaths": 5,             // <- Mostrar en estadísticas
    "time_per_level": {
      "hub_central": 120,
      "senda_ebano": 480
    }
  }
}
```

### 6.4 Nueva Partida

**FLUJO PARA INICIAR UNA PARTIDA NUEVA:**

```
Usuario selecciona "NUEVA PARTIDA"
    |
    v
POST /v1/games
    Headers: X-Player-ID, X-Player-Token
    Body: {}
    |
    v
Respuesta:
    - game_id: ID única para esta partida
    - current_level: "hub_central"
    - status: "in_progress"
    - total_time_seconds: 0
    - levels_completed: []
    - relics: []
    - choices: { senda_ebano: null, ... }
    |
    v
Guardar game_id localmente
    |
    v
POST /v1/sessions
    Headers: X-Player-ID, X-Player-Token
    Body: { "game_id": "{new_game_id}", "platform": "windows" }
    |
    v
Guardar session_id localmente
    |
    v
Iniciar en hub_central
```

### 6.5 Durante el Juego (Guardar Progreso)

**MIENTRAS EL JUGADOR JUEGA:**

```
Jugador entra a un nivel
    |
    v
POST /v1/games/{game_id}/level/start
    Headers: X-Player-ID, X-Player-Token
    Body: { "level": "senda_ebano" }
    |
    v
[JUGADOR JUEGA]
    |
    +-- Cada 30 segundos o cuando cambia de zona:
    |   PATCH /v1/games/{game_id}
    |   Body: {
    |     "total_time_seconds": <tiempo acumulado>,
    |     "current_level": "senda_ebano"
    |   }
    |
    +-- Registrar eventos importantes (batch cada 30s o 10 eventos):
    |   POST /v1/events/batch
    |   Body: { "events": [
    |     {
    |       "game_id": "...",
    |       "player_id": "...",
    |       "event_type": "player_death",
    |       "level": "senda_ebano",
    |       "data": { "enemy_type": "espectro" }
    |     }
    |   ] }
    |
    v
Jugador completa nivel (toma decisión + obtiene reliquia)
    |
    v
POST /v1/games/{game_id}/level/complete
    Headers: X-Player-ID, X-Player-Token
    Body: {
      "level": "senda_ebano",
      "time_seconds": 580,
      "deaths": 5,
      "relic": "lirio",
      "choice": "sanar"
    }
    |
    v
Respuesta actualiza:
    - levels_completed: ahora incluye "senda_ebano"
    - relics: ahora incluye "lirio"
    - choices.senda_ebano: ahora es "sanar"
    - completion_percentage: 50.0
    |
    v
Continuar con siguiente nivel
```

### 6.6 Completar el Juego

```
Jugador llega al jefe final y lo derrota
    |
    v
POST /v1/games/{game_id}/complete
    Headers: X-Player-ID, X-Player-Token
    Body: {}
    |
    v
API actualiza automáticamente:
    - game.status = "completed"
    - game.ended_at = timestamp actual
    - player.games_completed += 1
    - player.stats.moral_alignment = (buenas - malas) / total
    - player.stats.best_speedrun_seconds = min actual
    |
    v
Mostrar pantalla de créditos/estadísticas
    |
    v
PATCH /v1/sessions/{session_id}/end
    Headers: X-Player-ID, X-Player-Token
    Body: {}
    |
    v
Volver al menú principal
```

### 6.7 Cerrar el Juego (Pausa/Cierre)

```
Jugador pausa o cierra el juego
    |
    v
Si hay cambios:
    PATCH /v1/games/{game_id}
    Body: { "total_time_seconds": <tiempo>, "current_level": "..." }
    |
    v
Si hay sesión activa:
    PATCH /v1/sessions/{session_id}/end
    Body: {}
    |
    v
Limpiar variables locales (pero NO borrar player_id ni player_token)
    |
    v
AL REABRIR:
    - player_id y player_token siguen disponibles
    - GET /v1/players/me para verificar
    - GET /v1/games/{game_id} para restaurar exactamente donde estaba
```

---

## Retomar Partida (Lo Más Importante)

Esta es la funcionalidad clave para permitir que los jugadores **continúen exactamente donde se quedaron**.

### Resumen del proceso

1. **Detectar si hay partida activa** → Login devuelve `active_game_id`
2. **Cargar estado completo** → GET /v1/games/{game_id}
3. **Restaurar juego** → Usar la información para recargar todo
4. **Iniciar sesión tracking** → POST /v1/sessions
5. **Continuar jugando** → Desde el nivel guardado

### Paso 1: Detectar partida activa al iniciar

**Opción A:** Después de login (más eficiente)

```bash
POST /v1/players/login
{
  "username": "jugador123",
  "password": "contraseña"
}
```

La respuesta incluye:
```json
{
  "player_id": "550e8400-e29b-41d4-a716-446655440000",
  "player_token": "abc-def-token",
  "username": "jugador123",
  "active_game_id": "game-uuid-123"
}
```

Si `active_game_id != null`, hay una partida en progreso.

**Opción B:** Consultando el perfil

```bash
GET /v1/players/me
Headers:
  X-Player-ID: 550e8400-e29b-41d4-a716-446655440000
  X-Player-Token: abc-def-token
```

### Paso 2: Cargar el estado completo de la partida

```bash
GET /v1/games/{game_id}
Headers:
  X-Player-ID: 550e8400-e29b-41d4-a716-446655440000
  X-Player-Token: abc-def-token
```

La respuesta contiene TODO lo que necesitas para restaurar el juego:

```json
{
  "game_id": "game-uuid-123",
  "player_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "in_progress",
  
  "current_level": "senda_ebano",
  "levels_completed": ["hub_central"],
  "completion_percentage": 50.0,
  
  "total_time_seconds": 1200,
  "started_at": "2024-01-20T10:00:00Z",
  
  "relics": ["lirio"],
  
  "choices": {
    "senda_ebano": "sanar",
    "fortaleza_gigantes": null,
    "aquelarre_sombras": null
  },
  
  "boss_defeated": false,
  
  "metrics": {
    "total_deaths": 5,
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

### Paso 3: Restaurar el juego (Implementación)

```csharp
void RestoreGameState(GameData gameData)
{
    // 1. Cargar el nivel correcto
    GameManager.CurrentLevel = gameData.current_level;
    LevelManager.LoadLevel(gameData.current_level);
    
    // 2. Restaurar inventario
    foreach (string relic in gameData.relics)
    {
        InventoryManager.AddRelic(relic);
    }
    
    // 3. Mostrar tiempo acumulado
    UIManager.PlaytimeDisplay.SetTime(gameData.total_time_seconds);
    
    // 4. Mostrar estadísticas
    UIManager.DeathCounter.SetDeaths(gameData.metrics.total_deaths);
    
    // 5. Marcar decisiones anteriores como completadas
    DialogueManager.MarkChoiceAsCompleted("senda_ebano", "sanar");
    
    // 6. Restaurar posición
    Player.transform.position = LevelManager.GetLevelSpawnPoint();
    Player.Health = Player.MaxHealth;
}
```

### Paso 4: Iniciar tracking

```bash
POST /v1/sessions
Headers:
  X-Player-ID: 550e8400-e29b-41d4-a716-446655440000
  X-Player-Token: abc-def-token

Body:
{
  "game_id": "game-uuid-123",
  "platform": "windows"
}
```

### Guía de qué información usar

| Información | Dónde usarla | Cómo usarla |
|-------------|-------------|------------|
| `current_level` | Cargar nivel | `LevelManager.LoadLevel(current_level)` |
| `relics` | Inventario | Mostrar cada reliquia |
| `total_time_seconds` | Display tiempo | Mostrar como MM:SS |
| `levels_completed` | Progreso | Marcar completados en mapa |
| `choices` | Diálogos | Si != null, mostrar consecuencia |
| `metrics.total_deaths` | Estadísticas | Mostrar contador |
| `completion_percentage` | Progress bar | Llenar barra |
| `boss_defeated` | Lógica final | Si true, jefe ya derrotado |

### Errores comunes

❌ **MALO:** Restaurar checkpoints internos no guardados
❌ **MALO:** Mostrar reliquias aleatorias nuevas
❌ **MALO:** Repetir diálogos de decisiones anteriores

✅ **BIEN:** Cargar desde inicio del nivel con estado completo
✅ **BIEN:** Mostrar exactamente las reliquias guardadas
✅ **BIEN:** Marcar decisiones como completadas

---

## 7. SISTEMA MORAL

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

## 8. CODIGOS DE ERROR

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
| `POST`   | `/v1/sessions`                              | Iniciar sesión de juego        |
| `PATCH`  | `/v1/sessions/{session_id}/end`             | Terminar sesión de juego       |
| `GET`    | `/v1/sessions/player/{player_id}`           | Sesiones de un jugador         |
| `GET`    | `/v1/sessions/game/{game_id}`               | Sesiones de una partida        |
| `POST`   | `/v1/events`                                | Crear evento                   |
| `POST`   | `/v1/events/batch`                          | Crear eventos en batch         |
| `GET`    | `/v1/events/game/{game_id}`                 | Eventos de partida             |
| `GET`    | `/v1/events/player/{player_id}`             | Eventos de jugador             |
| `GET`    | `/v1/events/game/{game_id}/type/{type}`     | Eventos por tipo               |

---

**Última actualización:** 25 de enero de 2026

**Changelog v2.2:**
- ✨ **Sección completa: "Cómo Hacer Llamadas a la API"** con ejemplos en C# (Unity) y Python
- ✨ **Sección dedicada: "Retomar Partida"** con instrucciones paso a paso
- 📝 Documentación mejorada de endpoints con más detalles
- 🔍 Clarificación sobre cómo restaurar estado del jugador (reliquias, tiempo, decisiones)
- 🎯 Énfasis en el campo `active_game_id` para detectar partidas activas
- 📚 Ejemplos prácticos de respuestas JSON para cada endpoint
- 🛠️ Guía de errores comunes al retomar partidas

**Changelog v2.1:**
- Añadido sistema de sesiones de juego (tracking de tiempo por plataforma)
- Nuevos endpoints: POST /v1/sessions, PATCH /v1/sessions/{id}/end
- Soporte para plataformas Windows y Android
- Cierre automático de sesiones huérfanas

**Changelog v2.0:**
- Sistema de autenticación con password
- Login requiere username + password
- Registro requiere password
- Campo display_name reemplazado por username
