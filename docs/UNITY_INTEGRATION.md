# Integración de Unity con Triskel-API

Esta guía te ayudará a conectar tu juego Unity con la API de Triskel desplegada en Railway.

## Configuración según el tipo de build

### Unity Nativo (Desktop, Android, iOS) ✅ RECOMENDADO

Si tu juego es una **aplicación nativa**, la integración es muy simple:

#### Ventajas
- ✅ No requiere configuración CORS
- ✅ Funciona inmediatamente
- ✅ Más seguro
- ✅ Mejor rendimiento

#### Configuración

En tu código Unity (C#):

```csharp
public class TriskelAPIClient
{
    // URL de tu API en Railway
    private const string API_URL = "https://tu-api.railway.app";

    // Para desarrollo local
    // private const string API_URL = "http://localhost:8000";

    public async Task<Player> CreatePlayer(string username)
    {
        string url = $"{API_URL}/v1/players";

        // Crear request body
        var playerData = new { username = username };
        string json = JsonUtility.ToJson(playerData);

        // Hacer request
        using (UnityWebRequest request = UnityWebRequest.Post(url, json, "application/json"))
        {
            await request.SendWebRequest();

            if (request.result == UnityWebRequest.Result.Success)
            {
                return JsonUtility.FromJson<Player>(request.downloadHandler.text);
            }
            else
            {
                Debug.LogError($"Error: {request.error}");
                return null;
            }
        }
    }
}
```

#### Testing

1. **Desarrollo local:**
   - API corriendo en `http://localhost:8000`
   - Unity apuntando a `http://localhost:8000`

2. **Producción:**
   - API desplegada en Railway: `https://tu-api.railway.app`
   - Unity apuntando a `https://tu-api.railway.app`

---

### Unity WebGL ⚠️ Requiere configuración CORS

Si necesitas compilar como **WebGL**, debes configurar CORS:

#### Desventajas
- ⚠️ Requiere configuración CORS en la API
- ⚠️ Más complejo de configurar
- ⚠️ Restricciones del navegador

#### Pasos

1. **Despliega tu build WebGL** en algún servidor:
   - Railway
   - itch.io
   - Netlify
   - Vercel
   - GitHub Pages

2. **Obtén la URL** donde está desplegado (ejemplo: `https://triskel-game.railway.app`)

3. **Configura CORS en Railway:**
   - Ve al dashboard de Railway
   - Añade variable: `CORS_ORIGINS=https://triskel-game.railway.app`
   - Si está en itch.io: `CORS_ORIGINS=https://tu-usuario.itch.io,https://v6p9d9t4.ssl.hwcdn.net`

4. **Usa el mismo código Unity** (el código es idéntico al nativo)

#### Testing Local WebGL

Para probar WebGL localmente:

1. En tu `.env` local, añade:
   ```
   CORS_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
   ```

2. Inicia un servidor local para servir tu build WebGL:
   ```bash
   # Python 3
   python -m http.server 8000

   # Node.js
   npx http-server -p 8000
   ```

3. Abre `http://localhost:8000` en tu navegador

---

## Endpoints Principales

### 1. Crear Jugador

**Endpoint:** `POST /v1/players`

**Body:**
```json
{
  "username": "jugador123"
}
```

**Response:**
```json
{
  "player_id": "abc123",
  "username": "jugador123",
  "token": "xyz789",
  "created_at": "2025-01-10T12:00:00Z"
}
```

**Unity Example:**
```csharp
public async Task<PlayerResponse> CreatePlayer(string username)
{
    string url = $"{API_URL}/v1/players";
    var data = new { username = username };
    string json = JsonUtility.ToJson(data);

    using (UnityWebRequest request = UnityWebRequest.Post(url, json, "application/json"))
    {
        await request.SendWebRequest();
        return JsonUtility.FromJson<PlayerResponse>(request.downloadHandler.text);
    }
}
```

### 2. Obtener Perfil del Jugador

**Endpoint:** `GET /v1/players/me`

**Headers:**
```
X-Player-ID: abc123
X-Player-Token: xyz789
```

**Response:**
```json
{
  "player_id": "abc123",
  "username": "jugador123",
  "created_at": "2025-01-10T12:00:00Z"
}
```

**Unity Example:**
```csharp
public async Task<PlayerProfile> GetPlayerProfile(string playerId, string token)
{
    string url = $"{API_URL}/v1/players/me";

    using (UnityWebRequest request = UnityWebRequest.Get(url))
    {
        // Añadir headers de autenticación
        request.SetRequestHeader("X-Player-ID", playerId);
        request.SetRequestHeader("X-Player-Token", token);

        await request.SendWebRequest();
        return JsonUtility.FromJson<PlayerProfile>(request.downloadHandler.text);
    }
}
```

### 3. Crear Partida

**Endpoint:** `POST /v1/games`

**Headers:**
```
X-Player-ID: abc123
X-Player-Token: xyz789
```

**Body:**
```json
{
  "player_id": "abc123"
}
```

**Response:**
```json
{
  "game_id": "game123",
  "player_id": "abc123",
  "status": "in_progress",
  "started_at": "2025-01-10T12:00:00Z"
}
```

**Unity Example:**
```csharp
public async Task<GameResponse> StartGame(string playerId, string token)
{
    string url = $"{API_URL}/v1/games";
    var data = new { player_id = playerId };
    string json = JsonUtility.ToJson(data);

    using (UnityWebRequest request = UnityWebRequest.Post(url, json, "application/json"))
    {
        request.SetRequestHeader("X-Player-ID", playerId);
        request.SetRequestHeader("X-Player-Token", token);

        await request.SendWebRequest();
        return JsonUtility.FromJson<GameResponse>(request.downloadHandler.text);
    }
}
```

### 4. Finalizar Partida

**Endpoint:** `PATCH /v1/games/{game_id}/complete`

**Headers:**
```
X-Player-ID: abc123
X-Player-Token: xyz789
```

**Body:**
```json
{
  "score": 1500,
  "completed": true
}
```

**Unity Example:**
```csharp
public async Task<GameResponse> CompleteGame(string gameId, int score, string playerId, string token)
{
    string url = $"{API_URL}/v1/games/{gameId}/complete";
    var data = new { score = score, completed = true };
    string json = JsonUtility.ToJson(data);

    using (UnityWebRequest request = UnityWebRequest.Put(url, json))
    {
        request.method = "PATCH";
        request.SetRequestHeader("Content-Type", "application/json");
        request.SetRequestHeader("X-Player-ID", playerId);
        request.SetRequestHeader("X-Player-Token", token);

        await request.SendWebRequest();
        return JsonUtility.FromJson<GameResponse>(request.downloadHandler.text);
    }
}
```

---

## Clase Completa de Ejemplo

Aquí tienes una clase completa que puedes usar en Unity:

```csharp
using System;
using System.Threading.Tasks;
using UnityEngine;
using UnityEngine.Networking;

[Serializable]
public class PlayerResponse
{
    public string player_id;
    public string username;
    public string token;
    public string created_at;
}

[Serializable]
public class GameResponse
{
    public string game_id;
    public string player_id;
    public string status;
    public string started_at;
    public int? score;
}

public class TriskelAPIClient : MonoBehaviour
{
    // Cambiar según el entorno
    private const string API_URL = "https://tu-api.railway.app";
    // private const string API_URL = "http://localhost:8000"; // Para desarrollo local

    private string playerId;
    private string playerToken;

    // Crear jugador
    public async Task<PlayerResponse> CreatePlayer(string username)
    {
        string url = $"{API_URL}/v1/players";
        var data = new { username = username };
        string json = JsonUtility.ToJson(data);

        using (UnityWebRequest request = UnityWebRequest.Post(url, json, "application/json"))
        {
            await request.SendWebRequest();

            if (request.result == UnityWebRequest.Result.Success)
            {
                PlayerResponse response = JsonUtility.FromJson<PlayerResponse>(request.downloadHandler.text);

                // Guardar credenciales
                playerId = response.player_id;
                playerToken = response.token;

                // Guardar en PlayerPrefs para persistencia
                PlayerPrefs.SetString("player_id", playerId);
                PlayerPrefs.SetString("player_token", playerToken);
                PlayerPrefs.Save();

                Debug.Log($"Jugador creado: {response.username}");
                return response;
            }
            else
            {
                Debug.LogError($"Error creando jugador: {request.error}");
                return null;
            }
        }
    }

    // Iniciar partida
    public async Task<GameResponse> StartGame()
    {
        string url = $"{API_URL}/v1/games";
        var data = new { player_id = playerId };
        string json = JsonUtility.ToJson(data);

        using (UnityWebRequest request = UnityWebRequest.Post(url, json, "application/json"))
        {
            request.SetRequestHeader("X-Player-ID", playerId);
            request.SetRequestHeader("X-Player-Token", playerToken);

            await request.SendWebRequest();

            if (request.result == UnityWebRequest.Result.Success)
            {
                GameResponse response = JsonUtility.FromJson<GameResponse>(request.downloadHandler.text);
                Debug.Log($"Partida iniciada: {response.game_id}");
                return response;
            }
            else
            {
                Debug.LogError($"Error iniciando partida: {request.error}");
                return null;
            }
        }
    }

    // Finalizar partida
    public async Task<GameResponse> CompleteGame(string gameId, int score)
    {
        string url = $"{API_URL}/v1/games/{gameId}/complete";
        var data = new { score = score, completed = true };
        string json = JsonUtility.ToJson(data);

        using (UnityWebRequest request = UnityWebRequest.Put(url, json))
        {
            request.method = "PATCH";
            request.SetRequestHeader("Content-Type", "application/json");
            request.SetRequestHeader("X-Player-ID", playerId);
            request.SetRequestHeader("X-Player-Token", playerToken);

            await request.SendWebRequest();

            if (request.result == UnityWebRequest.Result.Success)
            {
                GameResponse response = JsonUtility.FromJson<GameResponse>(request.downloadHandler.text);
                Debug.Log($"Partida completada con puntuación: {score}");
                return response;
            }
            else
            {
                Debug.LogError($"Error completando partida: {request.error}");
                return null;
            }
        }
    }

    // Cargar credenciales guardadas
    public void LoadCredentials()
    {
        playerId = PlayerPrefs.GetString("player_id", "");
        playerToken = PlayerPrefs.GetString("player_token", "");
    }
}
```

---

## Flujo Completo de Ejemplo

```csharp
public class GameManager : MonoBehaviour
{
    private TriskelAPIClient apiClient;
    private string currentGameId;

    async void Start()
    {
        apiClient = GetComponent<TriskelAPIClient>();

        // 1. Intentar cargar credenciales guardadas
        apiClient.LoadCredentials();

        // Si no hay credenciales, crear jugador
        if (string.IsNullOrEmpty(PlayerPrefs.GetString("player_id")))
        {
            await apiClient.CreatePlayer("NuevoJugador123");
        }

        // 2. Iniciar partida
        GameResponse game = await apiClient.StartGame();
        if (game != null)
        {
            currentGameId = game.game_id;
        }
    }

    // Llamar cuando el jugador complete el juego
    public async void OnGameComplete(int finalScore)
    {
        await apiClient.CompleteGame(currentGameId, finalScore);
    }
}
```

---

## Debugging

### Ver todas las peticiones en Unity

```csharp
Debug.Log($"Request URL: {request.url}");
Debug.Log($"Request Method: {request.method}");
Debug.Log($"Response Code: {request.responseCode}");
Debug.Log($"Response Body: {request.downloadHandler.text}");
```

### Errores Comunes

1. **"Connection refused"**
   - La API no está corriendo o la URL es incorrecta
   - Verifica que la API esté desplegada en Railway

2. **CORS Error (solo WebGL)**
   - No has configurado CORS_ORIGINS en Railway
   - La URL en CORS_ORIGINS no coincide con tu dominio WebGL

3. **401 Unauthorized**
   - Headers de autenticación faltantes o incorrectos
   - Verifica que estés enviando X-Player-ID y X-Player-Token

4. **404 Not Found**
   - La ruta del endpoint es incorrecta
   - Verifica la documentación de la API: `https://tu-api.railway.app/docs`

---

## Recursos Adicionales

- **API Docs:** `https://tu-api.railway.app/docs`
- **Health Check:** `https://tu-api.railway.app/health`
- **Documentación Railway:** [docs/RAILWAY_DEPLOYMENT.md](./RAILWAY_DEPLOYMENT.md)

---

## Recomendación Final

**Para Triskel, recomendamos usar Unity Nativo (Desktop/Android/iOS)** en lugar de WebGL:
- ✅ Más simple de configurar
- ✅ Mejor rendimiento
- ✅ No requiere CORS
- ✅ Mejor experiencia de usuario

Solo usa WebGL si es absolutamente necesario que el juego corra en el navegador.
