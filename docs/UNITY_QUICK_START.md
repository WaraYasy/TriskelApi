# Quick Start - Integración de Triskel API en Unity

Una guía rápida para implementar la integración de Triskel API en tu proyecto de Unity.

## 1. Instalación y Configuración

### Paso 1: Crear el cliente API

```csharp
using UnityEngine;
using UnityEngine.Networking;
using System.Collections;
using System.Text;

public class TriskelAPIClient : MonoBehaviour
{
    private string baseURL = "http://localhost:8000";  // Cambiar en producción
    private string playerID;
    private string playerToken;
    
    // Guardar credenciales de forma persistente
    private void OnEnable()
    {
        playerID = PlayerPrefs.GetString("PlayerID", "");
        playerToken = PlayerPrefs.GetString("PlayerToken", "");
    }
    
    private void SaveCredentials()
    {
        PlayerPrefs.SetString("PlayerID", playerID);
        PlayerPrefs.SetString("PlayerToken", playerToken);
        PlayerPrefs.Save();
    }
}
```

## 2. Registro y Login

### Crear Cuenta

```csharp
public IEnumerator Register(string username, string password, string email = "")
{
    string url = baseURL + "/v1/players";
    
    var data = new { username, password, email };
    string json = JsonUtility.ToJson(data);
    byte[] bodyRaw = Encoding.UTF8.GetBytes(json);
    
    using (UnityWebRequest request = new UnityWebRequest(url, "POST"))
    {
        request.uploadHandler = new UploadHandlerRaw(bodyRaw);
        request.downloadHandler = new DownloadHandlerBuffer();
        request.SetRequestHeader("Content-Type", "application/json");
        
        yield return request.SendWebRequest();
        
        if (request.result == UnityWebRequest.Result.Success)
        {
            var response = JsonUtility.FromJson<AuthResponse>(request.downloadHandler.text);
            playerID = response.player_id;
            playerToken = response.player_token;
            SaveCredentials();
            
            Debug.Log($"Registro exitoso! ID: {playerID}");
        }
        else
        {
            Debug.LogError($"Error en registro: {request.error}");
        }
    }
}
```

### Login

```csharp
public IEnumerator Login(string username, string password)
{
    string url = baseURL + "/v1/players/login";
    
    var data = new { username, password };
    string json = JsonUtility.ToJson(data);
    byte[] bodyRaw = Encoding.UTF8.GetBytes(json);
    
    using (UnityWebRequest request = new UnityWebRequest(url, "POST"))
    {
        request.uploadHandler = new UploadHandlerRaw(bodyRaw);
        request.downloadHandler = new DownloadHandlerBuffer();
        request.SetRequestHeader("Content-Type", "application/json");
        
        yield return request.SendWebRequest();
        
        if (request.result == UnityWebRequest.Result.Success)
        {
            var response = JsonUtility.FromJson<LoginResponse>(request.downloadHandler.text);
            playerID = response.player_id;
            playerToken = response.player_token;
            SaveCredentials();
            
            // ✨ IMPORTANTE: Verificar si hay partida activa
            if (!string.IsNullOrEmpty(response.active_game_id))
            {
                Debug.Log($"Partida activa encontrada: {response.active_game_id}");
                // Luego cargarla con LoadGame()
            }
            else
            {
                Debug.Log("No hay partida activa");
            }
        }
        else
        {
            Debug.LogError($"Error en login: {request.error}");
        }
    }
}

[System.Serializable]
public class LoginResponse
{
    public string player_id;
    public string player_token;
    public string username;
    public string active_game_id;  // ← Aquí está la pista de partida activa
}

[System.Serializable]
public class AuthResponse
{
    public string player_id;
    public string player_token;
    public string username;
}
```

## 3. Crear Nueva Partida

```csharp
public IEnumerator CreateGame()
{
    string url = baseURL + "/v1/games";
    
    using (UnityWebRequest request = new UnityWebRequest(url, "POST"))
    {
        request.uploadHandler = new UploadHandlerRaw(new byte[] { });
        request.downloadHandler = new DownloadHandlerBuffer();
        request.SetRequestHeader("Content-Type", "application/json");
        SetAuthHeaders(request);
        
        yield return request.SendWebRequest();
        
        if (request.result == UnityWebRequest.Result.Success)
        {
            var gameData = JsonUtility.FromJson<GameResponse>(request.downloadHandler.text);
            string gameID = gameData.game_id;
            
            Debug.Log($"Partida creada: {gameID}");
            
            // Iniciar sesión de tracking
            yield return StartSession(gameID, "windows");
        }
    }
}
```

## 4. Retomar Partida (LO MÁS IMPORTANTE)

```csharp
public IEnumerator LoadGame(string gameID)
{
    string url = baseURL + "/v1/games/" + gameID;
    
    using (UnityWebRequest request = UnityWebRequest.Get(url))
    {
        SetAuthHeaders(request);
        
        yield return request.SendWebRequest();
        
        if (request.result == UnityWebRequest.Result.Success)
        {
            var gameData = JsonUtility.FromJson<GameResponse>(request.downloadHandler.text);
            
            Debug.Log($"Partida cargada!");
            Debug.Log($"  Nivel: {gameData.current_level}");
            Debug.Log($"  Tiempo: {gameData.total_time_seconds}s");
            Debug.Log($"  Reliquias: {string.Join(", ", gameData.relics)}");
            Debug.Log($"  Progreso: {gameData.completion_percentage}%");
            
            // ✨ RESTAURAR EL JUEGO
            RestoreGameState(gameData);
            
            // Iniciar sesión de tracking
            yield return StartSession(gameID, "windows");
        }
        else
        {
            Debug.LogError($"Error cargando partida: {request.error}");
        }
    }
}

void RestoreGameState(GameResponse gameData)
{
    // 1. Cargar el nivel
    LevelManager.LoadLevel(gameData.current_level);
    
    // 2. Restaurar inventario
    InventoryManager.Clear();
    foreach (string relic in gameData.relics)
    {
        InventoryManager.AddRelic(relic);
    }
    
    // 3. Mostrar tiempo en UI
    UIManager.PlaytimeDisplay.SetSeconds(gameData.total_time_seconds);
    
    // 4. Mostrar estadísticas
    UIManager.StatsPanel.SetDeaths(gameData.metrics.total_deaths);
    UIManager.ProgressBar.SetCompletion(gameData.completion_percentage);
    
    // 5. Marcar decisiones anteriores
    if (gameData.choices.senda_ebano != null)
        DialogueManager.MarkChoiceComplete("senda_ebano");
    if (gameData.choices.fortaleza_gigantes != null)
        DialogueManager.MarkChoiceComplete("fortaleza_gigantes");
    if (gameData.choices.aquelarre_sombras != null)
        DialogueManager.MarkChoiceComplete("aquelarre_sombras");
    
    // 6. Posicionar jugador
    Player player = FindObjectOfType<Player>();
    if (player != null)
    {
        player.transform.position = LevelManager.GetSpawnPoint();
        player.ResetHealth();
    }
}

[System.Serializable]
public class GameResponse
{
    public string game_id;
    public string status;
    public string current_level;
    public int total_time_seconds;
    public float completion_percentage;
    public string[] levels_completed;
    public string[] relics;
    public GameChoicesData choices;
    public GameMetricsData metrics;
    public bool boss_defeated;
}

[System.Serializable]
public class GameChoicesData
{
    public string senda_ebano;
    public string fortaleza_gigantes;
    public string aquelarre_sombras;
}

[System.Serializable]
public class GameMetricsData
{
    public int total_deaths;
}
```

## 5. Guardar Progreso (Durante el juego)

```csharp
private float lastSaveTime = 0f;
private const float SAVE_INTERVAL = 30f;  // Guardar cada 30 segundos

void Update()
{
    if (Time.time - lastSaveTime >= SAVE_INTERVAL)
    {
        SaveProgress();
        lastSaveTime = Time.time;
    }
}

void SaveProgress()
{
    StartCoroutine(UpdateGame(new UpdateGameRequest
    {
        current_level = LevelManager.CurrentLevel,
        total_time_seconds = (int)GameTimer.ElapsedSeconds,
        status = "in_progress"
    }));
}

public IEnumerator UpdateGame(UpdateGameRequest update)
{
    string url = baseURL + "/v1/games/" + GameManager.CurrentGameID;
    
    string json = JsonUtility.ToJson(update);
    byte[] bodyRaw = Encoding.UTF8.GetBytes(json);
    
    using (UnityWebRequest request = new UnityWebRequest(url, "PATCH"))
    {
        request.uploadHandler = new UploadHandlerRaw(bodyRaw);
        request.downloadHandler = new DownloadHandlerBuffer();
        request.SetRequestHeader("Content-Type", "application/json");
        SetAuthHeaders(request);
        
        yield return request.SendWebRequest();
        
        if (request.result != UnityWebRequest.Result.Success)
        {
            Debug.LogWarning($"Error guardando progreso: {request.error}");
        }
    }
}

[System.Serializable]
public class UpdateGameRequest
{
    public string current_level;
    public int total_time_seconds;
    public string status;
}
```

## 6. Completar Nivel

```csharp
public IEnumerator CompleteLevel(string levelName, int timeSeconds, int deaths, string relic = null, string choice = null)
{
    string url = baseURL + "/v1/games/" + GameManager.CurrentGameID + "/level/complete";
    
    var data = new { level = levelName, time_seconds = timeSeconds, deaths, relic, choice };
    string json = JsonUtility.ToJson(data);
    byte[] bodyRaw = Encoding.UTF8.GetBytes(json);
    
    using (UnityWebRequest request = new UnityWebRequest(url, "POST"))
    {
        request.uploadHandler = new UploadHandlerRaw(bodyRaw);
        request.downloadHandler = new DownloadHandlerBuffer();
        request.SetRequestHeader("Content-Type", "application/json");
        SetAuthHeaders(request);
        
        yield return request.SendWebRequest();
        
        if (request.result == UnityWebRequest.Result.Success)
        {
            Debug.Log($"Nivel {levelName} completado!");
            
            var response = JsonUtility.FromJson<GameResponse>(request.downloadHandler.text);
            // Actualizar UI con nuevo progreso
        }
    }
}
```

## 7. Completar Juego

```csharp
public IEnumerator CompleteGame()
{
    string url = baseURL + "/v1/games/" + GameManager.CurrentGameID + "/complete";
    
    using (UnityWebRequest request = new UnityWebRequest(url, "POST"))
    {
        request.uploadHandler = new UploadHandlerRaw(new byte[] { });
        request.downloadHandler = new DownloadHandlerBuffer();
        request.SetRequestHeader("Content-Type", "application/json");
        SetAuthHeaders(request);
        
        yield return request.SendWebRequest();
        
        if (request.result == UnityWebRequest.Result.Success)
        {
            Debug.Log("¡Juego completado!");
            // Mostrar pantalla de créditos/estadísticas
            ShowCreditsScreen();
        }
    }
}
```

## 8. Sesiones de Juego

```csharp
private string currentSessionID;

public IEnumerator StartSession(string gameID, string platform = "windows")
{
    string url = baseURL + "/v1/sessions";
    
    var data = new { game_id = gameID, platform };
    string json = JsonUtility.ToJson(data);
    byte[] bodyRaw = Encoding.UTF8.GetBytes(json);
    
    using (UnityWebRequest request = new UnityWebRequest(url, "POST"))
    {
        request.uploadHandler = new UploadHandlerRaw(bodyRaw);
        request.downloadHandler = new DownloadHandlerBuffer();
        request.SetRequestHeader("Content-Type", "application/json");
        SetAuthHeaders(request);
        
        yield return request.SendWebRequest();
        
        if (request.result == UnityWebRequest.Result.Success)
        {
            var response = JsonUtility.FromJson<SessionResponse>(request.downloadHandler.text);
            currentSessionID = response.session_id;
            Debug.Log($"Sesión iniciada: {currentSessionID}");
        }
    }
}

public IEnumerator EndSession()
{
    if (string.IsNullOrEmpty(currentSessionID))
        yield break;
    
    string url = baseURL + "/v1/sessions/" + currentSessionID + "/end";
    
    using (UnityWebRequest request = new UnityWebRequest(url, "PATCH"))
    {
        request.uploadHandler = new UploadHandlerRaw(new byte[] { });
        request.downloadHandler = new DownloadHandlerBuffer();
        request.SetRequestHeader("Content-Type", "application/json");
        SetAuthHeaders(request);
        
        yield return request.SendWebRequest();
        
        if (request.result == UnityWebRequest.Result.Success)
        {
            Debug.Log("Sesión terminada");
        }
    }
}

[System.Serializable]
public class SessionResponse
{
    public string session_id;
    public string game_id;
    public bool is_active;
    public int duration_seconds;
}
```

## 9. Helper: Establecer Headers de Autenticación

```csharp
private void SetAuthHeaders(UnityWebRequest request)
{
    request.SetRequestHeader("X-Player-ID", playerID);
    request.SetRequestHeader("X-Player-Token", playerToken);
}
```

## 10. Menú Principal - Flujo Completo

```csharp
public class MainMenu : MonoBehaviour
{
    private TriskelAPIClient apiClient;
    
    async void OnLoginButtonClicked(string username, string password)
    {
        // 1. Login
        yield return apiClient.Login(username, password);
        
        // 2. Verificar si hay partida activa
        string activeGameID = PlayerPrefs.GetString("ActiveGameID", "");
        
        if (!string.IsNullOrEmpty(activeGameID))
        {
            // Hay partida en progreso
            ShowMenuWithContinueOption(activeGameID);
        }
        else
        {
            // Sin partida activa
            ShowMenuOnlyNew();
        }
    }
    
    void OnContinueButtonClicked()
    {
        string gameID = PlayerPrefs.GetString("ActiveGameID");
        yield return apiClient.LoadGame(gameID);
        SceneManager.LoadScene("GameScene");
    }
    
    void OnNewGameButtonClicked()
    {
        yield return apiClient.CreateGame();
        SceneManager.LoadScene("GameScene");
    }
}
```

## Checklist de Implementación

- [ ] Crear clase `TriskelAPIClient`
- [ ] Implementar login/registro con guardado de credenciales
- [ ] Implementar `LoadGame()` para retomar partidas
- [ ] Implementar `RestoreGameState()` para restaurar UI y estado
- [ ] Implementar `SaveProgress()` llamado cada 30s
- [ ] Implementar `CompleteLevel()` al terminar cada nivel
- [ ] Implementar sesiones (start/end)
- [ ] Probar flujo completo: Login → Nueva Partida → Jugar → Guardar → Cerrar → Reabrir → Continuar

## URLs Importantes

| Ambiente  | URL                        |
|-----------|----------------------------|
| Desarrollo| http://localhost:8000      |
| Producción| https://tu-dominio.com     |
| Swagger   | {BASE_URL}/docs            |

## Sugerencias

- Usa `PlayerPrefs` para guardar `player_id` y `player_token` de forma persistente
- Implementa reintentos si la conexión falla
- Muestra un indicador de "Guardando..." mientras se actualiza el progreso
- Usa corrutinas para manejar las peticiones HTTP asincrónicas
- Captura errores 401 para volver a la pantalla de login
