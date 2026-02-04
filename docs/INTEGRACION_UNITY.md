# Guía de Integración Triskel API - Unity
¡Holi! Aquí tienes una guía completa para integrar tu proyecto Unity con la API REST de Triskel/Mandrágora.

## Configuración Inicial

### URL Base
```
Producción: https://triskel.up.railway.app
```

### Autenticación
Todas las requests deben incluir el header:
```
X-API-Key: [tu_api_key]
```

### Cliente HTTP en Unity
Recomendamos usar `UnityWebRequest` para todas las peticiones HTTP.

```csharp
using UnityEngine;
using UnityEngine.Networking;
using System.Collections;

public class TriskelAPIClient : MonoBehaviour
{
    private const string BASE_URL = "https://triskel.up.railway.app";
    private const string API_KEY = "TU_API_KEY_AQUI";

    private IEnumerator SendRequest(string endpoint, string method, string jsonBody = null)
    {
        string url = BASE_URL + endpoint;
        UnityWebRequest request = new UnityWebRequest(url, method);

        // Headers
        request.SetRequestHeader("X-API-Key", API_KEY);
        request.SetRequestHeader("Content-Type", "application/json");

        // Body (si es POST/PUT)
        if (jsonBody != null)
        {
            byte[] bodyRaw = System.Text.Encoding.UTF8.GetBytes(jsonBody);
            request.uploadHandler = new UploadHandlerRaw(bodyRaw);
        }

        // Response handler
        request.downloadHandler = new DownloadHandlerBuffer();

        yield return request.SendWebRequest();

        if (request.result == UnityWebRequest.Result.Success)
        {
            Debug.Log("Response: " + request.downloadHandler.text);
            // Procesar respuesta...
        }
        else
        {
            Debug.LogError("Error: " + request.error);
        }
    }
}
```

---

## Flujo de Integración

### 1. Registro de Jugador

**Endpoint:** `POST /v1/players`

```json
{
  "username": "player_name",
  "password": "secure_password",
  "email": "optional@email.com"
}
```

**Respuesta:**
```json
{
  "player_id": "uuid",
  "username": "player_name",
  "player_token": "uuid",
  "created_at": "2026-02-04T10:00:00Z",
  "total_playtime_seconds": 0,
  "games_played": 0,
  "games_completed": 0
}
```

**Ejemplo Unity:**
```csharp
public IEnumerator RegisterPlayer(string username, string password)
{
    string json = JsonUtility.ToJson(new {
        username = username,
        password = password,
        email = ""
    });

    yield return StartCoroutine(SendRequest("/v1/players", "POST", json));
}
```

---

### 2. Login de Jugador

**Endpoint:** `POST /v1/players/login`

```json
{
  "username": "player_name",
  "password": "secure_password"
}
```

**Respuesta:** Mismo objeto Player con `player_token` actualizado.

---

### 3. Iniciar Partida

**Endpoint:** `POST /v1/games`

```json
{
  "player_id": "uuid-del-jugador"
}
```

**Respuesta:**
```json
{
  "game_id": "uuid-de-la-partida",
  "player_id": "uuid-del-jugador",
  "status": "in_progress",
  "started_at": "2026-02-04T10:00:00Z",
  "total_time_seconds": 0,
  "levels_completed": [],
  "current_level": null,
  "choices": {
    "senda_ebano": null,
    "fortaleza_gigantes": null,
    "aquelarre_sombras": null
  },
  "relics": [],
  "boss_defeated": false
}
```

**IMPORTANTE:** Guarda el `game_id` - lo necesitarás para todas las operaciones posteriores.

---

### 4. Iniciar Nivel

**Endpoint:** `POST /v1/games/{game_id}/start_level`

```json
{
  "level": "senda_ebano"
}
```

**¿Qué hace?**
- Guarda el timestamp de inicio del nivel
- Actualiza `current_level`

**IMPORTANTE:** Debes llamar a este endpoint **ANTES** de `complete_level` para que el cálculo de tiempo funcione correctamente.

**Ejemplo Unity:**
```csharp
public IEnumerator StartLevel(string gameId, string levelName)
{
    string json = JsonUtility.ToJson(new { level = levelName });
    yield return StartCoroutine(SendRequest($"/v1/games/{gameId}/start_level", "POST", json));
}
```

---

### 5. Completar Nivel

**Endpoint:** `POST /v1/games/{game_id}/complete_level`

```json
{
  "level": "senda_ebano",
  "time_seconds": null,
  "deaths": 3,
  "relic_obtained": "lirio",
  "choice": "sanar"
}
```

**Parámetros:**

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `level` | string | ✅ | Nombre del nivel: `senda_ebano`, `fortaleza_gigantes`, `aquelarre_sombras` |
| `time_seconds` | int | ❌ | **Dejar en null** - La API lo calcula automáticamente desde el timestamp de `start_level` |
| `deaths` | int | ✅ | Número de muertes en el nivel |
| `relic_obtained` | string | ❌ | Reliquia obtenida: `lirio`, `hacha`, `manto` |
| `choice` | string | ❌ | Decisión moral tomada (ver tabla abajo) |

**Decisiones morales por nivel:**

| Nivel | Decisión Buena | Decisión Mala |
|-------|---------------|---------------|
| `senda_ebano` | `"sanar"` | `"forzar"` |
| `fortaleza_gigantes` | `"construir"` | `"destruir"` |
| `aquelarre_sombras` | `"revelar"` | `"ocultar"` |

**¿Qué hace?**
- Calcula el tiempo del nivel (timestamp actual - timestamp de `start_level`)
- Suma el tiempo al `total_time_seconds` de la partida
- Guarda la decisión moral en `game.choices`
- Añade el nivel a `levels_completed`
- Registra muertes y reliquia

**IMPORTANTE:**
- ❌ NO envíes `time_seconds` manualmente - déjalo en `null`
- ✅ La API calcula el tiempo automáticamente con precisión
- ⚠️ Si no llamaste a `start_level` antes, el tiempo será 1 segundo (fallback)

**Ejemplo Unity:**
```csharp
public IEnumerator CompleteLevel(string gameId, string levelName, int deaths, string relic, string choice)
{
    string json = JsonUtility.ToJson(new {
        level = levelName,
        time_seconds = (int?)null,  // Dejar null para cálculo automático
        deaths = deaths,
        relic_obtained = relic,
        choice = choice
    });

    yield return StartCoroutine(SendRequest($"/v1/games/{gameId}/complete_level", "POST", json));
}
```

---

### 6. Completar Partida

**Endpoint:** `POST /v1/games/{game_id}/complete`

```json
{
  "boss_defeated": true
}
```

**¿Qué hace?**
- Marca la partida como `"completed"`
- Establece `ended_at` timestamp
- **🔥 ACTUALIZA LAS ESTADÍSTICAS DEL JUGADOR** (esto es crítico)

**Actualización de stats del jugador:**
```python
# Se ejecuta SOLO cuando completas la partida:
player.games_played += 1
player.games_completed += 1  # Si status == "completed"
player.total_playtime_seconds += game.total_time_seconds
player.stats.total_deaths += game.total_deaths

# Conteo de decisiones morales
player.stats.total_good_choices += (decisiones buenas en esta partida)
player.stats.total_bad_choices += (decisiones malas en esta partida)

# Cálculo de alineación moral: rango -1.0 (malo) a +1.0 (bueno)
player.stats.moral_alignment = (total_good - total_bad) / total_decisiones

# Mejor speedrun (solo si completó)
if game.total_time_seconds < player.stats.best_speedrun_seconds:
    player.stats.best_speedrun_seconds = game.total_time_seconds
```

**CRÍTICO:** Si el jugador abandona y nunca llamas a este endpoint, sus stats **NO se actualizarán**. Las decisiones morales y el tiempo quedarán registrados en el `Game`, pero no en el `Player`.

**Ejemplo Unity:**
```csharp
public IEnumerator CompleteGame(string gameId, bool bossDefeated)
{
    string json = JsonUtility.ToJson(new { boss_defeated = bossDefeated });
    yield return StartCoroutine(SendRequest($"/v1/games/{gameId}/complete", "POST", json));
}
```

---

### 7. Abandonar Partida

**Endpoint:** `POST /v1/games/{game_id}/abandon`

```json
{}
```

**¿Qué hace?**
- Marca la partida como `"abandoned"`
- Establece `ended_at` timestamp
- **NO actualiza stats del jugador** (solo completas actualizan stats)

---

## Flujo Completo Ejemplo

```csharp
public class GameFlowExample : MonoBehaviour
{
    private string currentGameId;
    private string playerId;

    // 1. Al iniciar el juego
    void Start()
    {
        StartCoroutine(InitializeGame());
    }

    IEnumerator InitializeGame()
    {
        // Login
        yield return StartCoroutine(LoginPlayer("username", "password"));

        // Crear nueva partida
        yield return StartCoroutine(CreateGame(playerId));
    }

    // 2. Al entrar a un nivel
    public void OnLevelStart(string levelName)
    {
        StartCoroutine(StartLevel(currentGameId, levelName));
    }

    // 3. Al completar un nivel
    public void OnLevelComplete(string levelName, int deaths, string relic, string choice)
    {
        StartCoroutine(CompleteLevel(currentGameId, levelName, deaths, relic, choice));
    }

    // 4. Al terminar el juego
    public void OnGameEnd(bool defeated)
    {
        StartCoroutine(CompleteGame(currentGameId, defeated));
    }

    // 5. Si el jugador sale sin terminar
    void OnApplicationQuit()
    {
        StartCoroutine(AbandonGame(currentGameId));
    }
}
```

---

## Decisiones Morales - Referencia Completa

### Senda del Ébano
```json
{
  "level": "senda_ebano",
  "choice": "sanar"    // Buena (+1) - Curar al herido
}
```
```json
{
  "level": "senda_ebano",
  "choice": "forzar"   // Mala (-1) - Obligar a continuar
}
```

### Fortaleza de Gigantes
```json
{
  "level": "fortaleza_gigantes",
  "choice": "construir"   // Buena (+1) - Ayudar a reconstruir
}
```
```json
{
  "level": "fortaleza_gigantes",
  "choice": "destruir"    // Mala (-1) - Destruir las ruinas
}
```

### Aquelarre de Sombras
```json
{
  "level": "aquelarre_sombras",
  "choice": "revelar"   // Buena (+1) - Revelar la verdad
}
```
```json
{
  "level": "aquelarre_sombras",
  "choice": "ocultar"   // Mala (-1) - Ocultar información
}
```

---

## Sistema de Alineación Moral

### Cálculo
```
moral_alignment = (total_good_choices - total_bad_choices) / total_choices
```

### Rangos
| Valor | Categoría | Color | Descripción |
|-------|-----------|-------|-------------|
| 0.6 a 1.0 | Bueno | Verde | Decisiones mayormente buenas |
| 0.2 a 0.6 | Neutral+ | Azul | Tendencia a decisiones buenas |
| -0.2 a 0.2 | Neutral | Gris | Decisiones equilibradas |
| -0.6 a -0.2 | Neutral- | Naranja | Tendencia a decisiones malas |
| -1.0 a -0.6 | Malo | Rojo | Decisiones mayormente malas |

### Ejemplo
```
Jugador hace:
- Senda Ébano: "sanar" (buena)
- Fortaleza: "destruir" (mala)
- Aquelarre: "revelar" (buena)

Resultado: 2 buenas, 1 mala
Cálculo: (2 - 1) / 3 = 0.33
Categoría: Neutral+ (azul)
```

---

## Manejo de Errores

### Códigos HTTP comunes

| Código | Significado | Acción |
|--------|-------------|--------|
| 200 | ✅ Éxito | Procesar respuesta |
| 201 | ✅ Creado | Recurso creado exitosamente |
| 400 | ❌ Bad Request | Revisar formato JSON o campos requeridos |
| 401 | ❌ Unauthorized | API Key incorrecta o ausente |
| 404 | ❌ Not Found | ID de partida/jugador no existe |
| 500 | ❌ Server Error | Error interno - reintentar o contactar soporte |

### Ejemplo de manejo en Unity
```csharp
if (request.result != UnityWebRequest.Result.Success)
{
    switch (request.responseCode)
    {
        case 401:
            Debug.LogError("API Key inválida");
            break;
        case 404:
            Debug.LogError("Recurso no encontrado");
            break;
        case 400:
            Debug.LogError("Datos inválidos: " + request.downloadHandler.text);
            break;
        default:
            Debug.LogError($"Error {request.responseCode}: {request.error}");
            break;
    }
}
```

---

## Endpoints Adicionales

### Obtener datos del jugador
```
GET /v1/players/{player_id}
```

### Obtener partida específica
```
GET /v1/games/{game_id}
```

### Listar partidas del jugador
```
GET /v1/games?player_id={player_id}
```

### Enviar evento de telemetría
```
POST /v1/events
```
```json
{
  "game_id": "uuid",
  "event_type": "player_action",
  "event_data": {
    "action": "jump",
    "position": {"x": 10, "y": 5, "z": 3}
  }
}
```

---

## Checklist de Integración

- [ ] Configurar API Key en constante
- [ ] Implementar cliente HTTP con headers correctos
- [ ] Registro/Login de jugadores
- [ ] Crear partida al empezar juego
- [ ] Llamar `start_level` ANTES de cada nivel
- [ ] Llamar `complete_level` AL TERMINAR cada nivel
- [ ] Enviar decisiones morales correctamente
- [ ] Llamar `complete_game` al finalizar
- [ ] Llamar `abandon_game` si el jugador sale
- [ ] Manejo de errores HTTP
- [ ] Logs de debug para troubleshooting

---

## Mejores Prácticas

### ✅ DO
- Llama a `start_level` inmediatamente al cargar la escena del nivel
- Deja `time_seconds` en `null` para cálculo automático
- Guarda el `game_id` en una variable de sesión
- Maneja errores de red con reintentos
- Envía decisiones morales inmediatamente después de tomarlas

### ❌ DON'T
- No calcules el tiempo manualmente en Unity
- No olvides llamar a `complete_game` o `abandon_game`
- No reutilices un `game_id` para múltiples partidas
- No envíes decisiones morales con valores incorrectos
- No llames a `complete_level` sin haber llamado a `start_level` primero

---

## Soporte

**Documentación API:** `https://triskel.up.railway.app/docs`

**Logs del servidor:** Los logs incluyen emojis para facilitar debugging:
- ⏱️ Eventos de tiempo
- 🎭 Decisiones morales
- ✅ Operaciones exitosas
- ❌ Errores
- 📊 Estadísticas

**Dashboard de Analytics:** `https://triskel.up.railway.app/web/dashboard`
- Verifica que las partidas se registren correctamente
- Revisa las estadísticas de jugadores
- Monitorea el leaderboard

---

## Ejemplo Completo - Script Unity

```csharp
using UnityEngine;
using UnityEngine.Networking;
using System.Collections;
using System.Collections.Generic;

[System.Serializable]
public class PlayerData
{
    public string player_id;
    public string username;
    public string player_token;
}

[System.Serializable]
public class GameData
{
    public string game_id;
    public string player_id;
    public string status;
}

public class TriskelAPI : MonoBehaviour
{
    private const string BASE_URL = "https://triskel.up.railway.app";
    private const string API_KEY = "TU_API_KEY_AQUI";

    private string currentPlayerId;
    private string currentGameId;

    // Login
    public IEnumerator Login(string username, string password)
    {
        string json = JsonUtility.ToJson(new { username, password });

        using (UnityWebRequest request = UnityWebRequest.Post($"{BASE_URL}/v1/players/login", json, "application/json"))
        {
            request.SetRequestHeader("X-API-Key", API_KEY);

            yield return request.SendWebRequest();

            if (request.result == UnityWebRequest.Result.Success)
            {
                PlayerData player = JsonUtility.FromJson<PlayerData>(request.downloadHandler.text);
                currentPlayerId = player.player_id;
                Debug.Log($"Login exitoso: {player.username}");
            }
            else
            {
                Debug.LogError($"Login fallido: {request.error}");
            }
        }
    }

    // Crear partida
    public IEnumerator CreateGame()
    {
        string json = JsonUtility.ToJson(new { player_id = currentPlayerId });

        using (UnityWebRequest request = UnityWebRequest.Post($"{BASE_URL}/v1/games", json, "application/json"))
        {
            request.SetRequestHeader("X-API-Key", API_KEY);

            yield return request.SendWebRequest();

            if (request.result == UnityWebRequest.Result.Success)
            {
                GameData game = JsonUtility.FromJson<GameData>(request.downloadHandler.text);
                currentGameId = game.game_id;
                Debug.Log($"Partida creada: {currentGameId}");
            }
            else
            {
                Debug.LogError($"Error creando partida: {request.error}");
            }
        }
    }

    // Iniciar nivel
    public IEnumerator StartLevel(string levelName)
    {
        string json = JsonUtility.ToJson(new { level = levelName });

        using (UnityWebRequest request = UnityWebRequest.Post($"{BASE_URL}/v1/games/{currentGameId}/start_level", json, "application/json"))
        {
            request.SetRequestHeader("X-API-Key", API_KEY);

            yield return request.SendWebRequest();

            if (request.result == UnityWebRequest.Result.Success)
            {
                Debug.Log($"Nivel iniciado: {levelName}");
            }
            else
            {
                Debug.LogError($"Error iniciando nivel: {request.error}");
            }
        }
    }

    // Completar nivel
    public IEnumerator CompleteLevel(string levelName, int deaths, string relic, string choice)
    {
        string json = JsonUtility.ToJson(new {
            level = levelName,
            time_seconds = (int?)null,
            deaths = deaths,
            relic_obtained = relic,
            choice = choice
        });

        using (UnityWebRequest request = UnityWebRequest.Post($"{BASE_URL}/v1/games/{currentGameId}/complete_level", json, "application/json"))
        {
            request.SetRequestHeader("X-API-Key", API_KEY);

            yield return request.SendWebRequest();

            if (request.result == UnityWebRequest.Result.Success)
            {
                Debug.Log($"Nivel completado: {levelName}");
            }
            else
            {
                Debug.LogError($"Error completando nivel: {request.error}");
            }
        }
    }

    // Completar juego
    public IEnumerator CompleteGame(bool bossDefeated)
    {
        string json = JsonUtility.ToJson(new { boss_defeated = bossDefeated });

        using (UnityWebRequest request = UnityWebRequest.Post($"{BASE_URL}/v1/games/{currentGameId}/complete", json, "application/json"))
        {
            request.SetRequestHeader("X-API-Key", API_KEY);

            yield return request.SendWebRequest();

            if (request.result == UnityWebRequest.Result.Success)
            {
                Debug.Log("Juego completado - Stats actualizados");
            }
            else
            {
                Debug.LogError($"Error completando juego: {request.error}");
            }
        }
    }
}
```

---

**Versión:** 1.0
**Fecha:** Febrero 2026
**Mantenido por:** Equipo Mandrágora
