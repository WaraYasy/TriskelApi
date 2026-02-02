# Guía de Flujo de Juego - Integración Unity

Guía para implementar correctamente el flujo de partidas y decisiones morales desde Unity.

## 1. Flujo Completo de una Partida

### 1.1 Crear Partida
```http
POST /v1/games
Headers:
  X-Player-Token: <token_del_jugador>
Body:
  {}
```

La API automáticamente:
- Usa el player_id del token
- Cierra cualquier partida activa anterior como "abandoned"
- Crea nueva partida con `started_at` = ahora

### 1.2 Iniciar un Nivel
```http
POST /v1/games/{game_id}/level/start
Headers:
  X-Player-Token: <token_del_jugador>
Body:
  {
    "level": "senda_ebano"
  }
```

**IMPORTANTE en Unity:**
```csharp
// Guardar timestamp cuando inicia el nivel
private float levelStartTime;

void OnLevelStart() {
    levelStartTime = Time.time;
}
```

### 1.3 Completar un Nivel

**Calcular tiempo en Unity:**
```csharp
void OnLevelComplete() {
    int timeSeconds = Mathf.RoundToInt(Time.time - levelStartTime);

    // IMPORTANTE: Verificar que el tiempo sea > 0
    if (timeSeconds <= 0) {
        Debug.LogWarning("Tiempo inválido, forzando a 1 segundo");
        timeSeconds = 1;
    }

    SendLevelComplete(timeSeconds);
}
```

**Llamada a la API:**
```http
POST /v1/games/{game_id}/level/complete
Headers:
  X-Player-Token: <token_del_jugador>
Body:
  {
    "level": "senda_ebano",
    "time_seconds": 245,        // ⚠️ DEBE SER > 0
    "deaths": 3,
    "choice": "sanar",          // REQUERIDO para niveles con decisión moral
    "relic": "lirio"            // Solo si el nivel da reliquia
  }
```

## 2. Decisiones Morales

### 2.1 Niveles con Decisión Moral

| Nivel | Decisión Buena | Decisión Mala |
|-------|---------------|---------------|
| `senda_ebano` | `"sanar"` | `"forzar"` |
| `fortaleza_gigantes` | `"construir"` | `"destruir"` |
| `aquelarre_sombras` | `"revelar"` | `"ocultar"` |

### 2.2 Implementación en Unity

```csharp
public class MoralChoice {
    public enum Level {
        SendaEbano,
        FortalezaGigantes,
        AquelarreSombras
    }

    public enum Choice {
        // Senda del Ébano
        Sanar,      // Buena
        Forzar,     // Mala

        // Fortaleza de Gigantes
        Construir,  // Buena
        Destruir,   // Mala

        // Aquelarre de Sombras
        Revelar,    // Buena
        Ocultar     // Mala
    }

    public static string GetChoiceString(Choice choice) {
        return choice.ToString().ToLower();
    }

    public static string GetLevelString(Level level) {
        switch(level) {
            case Level.SendaEbano: return "senda_ebano";
            case Level.FortalezaGigantes: return "fortaleza_gigantes";
            case Level.AquelarreSombras: return "aquelarre_sombras";
            default: return "";
        }
    }
}

// Ejemplo de uso
void OnPlayerMakesChoice(MoralChoice.Choice playerChoice) {
    string choiceValue = MoralChoice.GetChoiceString(playerChoice);
    // choiceValue será: "sanar", "forzar", "construir", etc.

    // Incluir en el payload de complete level
    levelCompleteData.choice = choiceValue;
}
```

## 3. Errores Comunes

### 3.1 Tiempo en 0 o Negativo
```
❌ ERROR: "El tiempo debe ser mayor a 0 segundos"
```

**Causa:** Unity no está midiendo el tiempo correctamente o está enviando 0.

**Solución:**
```csharp
// MAL ❌
int timeSeconds = 0; // Siempre falla

// BIEN ✅
float levelStartTime = Time.time;
// ... jugador completa nivel ...
int timeSeconds = Mathf.Max(1, Mathf.RoundToInt(Time.time - levelStartTime));
```

### 3.2 Decisión Moral Faltante
```
⚠️ WARNING: "El nivel 'senda_ebano' requiere una decisión moral pero no se recibió"
```

**Causa:** El campo `choice` es `null` en un nivel que requiere decisión moral.

**Solución:**
```csharp
// MAL ❌
{
    "level": "senda_ebano",
    "time_seconds": 245,
    "deaths": 3
    // Falta "choice"
}

// BIEN ✅
{
    "level": "senda_ebano",
    "time_seconds": 245,
    "deaths": 3,
    "choice": "sanar"  // ✓ Decisión incluida
}
```

### 3.3 Decisión Moral Inválida
```
❌ ERROR: "Elección 'ayudar' no válida para 'senda_ebano'. Válidas: forzar, sanar"
```

**Causa:** Valor incorrecto en el campo `choice`.

**Solución:** Usar exactamente los valores documentados (minúsculas, sin espacios).

## 4. Validaciones de la API

### 4.1 time_seconds
- ✅ Mayor a 0
- ✅ Menor a 86400 (24 horas)
- ❌ 0 o negativo → ERROR
- ❌ Mayor a 24 horas → ERROR

### 4.2 deaths
- ✅ 0 o mayor
- ✅ Menor a 10000
- ❌ Negativo → ERROR

### 4.3 choice
- ✅ Uno de los valores válidos para el nivel
- ✅ `null` si el nivel no tiene decisión moral
- ❌ Valor inválido → ERROR
- ⚠️ `null` en nivel con decisión moral → WARNING (se registra pero no cuenta)

### 4.4 level
- ✅ Uno de: `hub_central`, `senda_ebano`, `fortaleza_gigantes`, `aquelarre_sombras`, `claro_almas`
- ❌ Cualquier otro valor → ERROR

## 5. Logs del Servidor

Cuando se registra correctamente, verás en los logs:

```
🎭 DECISIÓN MORAL: Jugador abc12345... eligió 'sanar' (BUENA) en nivel 'senda_ebano' [Partida: def67890...]

✅ Decisión BUENA detectada: sanar en senda_ebano [Jugador: abc12345...]

📊 Resumen partida def67890...: 1 buenas, 0 malas | Total histórico: 5 buenas, 2 malas [Jugador: abc12345...]

📈 ALINEACIÓN MORAL actualizada: 0.42 → 0.57 (+0.15) [Jugador: abc12345...]
```

Si algo falla:
```
⚠️ DECISIÓN MORAL FALTANTE: El nivel 'senda_ebano' requiere una decisión moral pero no se recibió el campo 'choice'
```

## 6. Ejemplo Completo en Unity (C#)

```csharp
using System;
using UnityEngine;

public class GameAPIManager : MonoBehaviour {
    private string gameId;
    private float levelStartTime;
    private int levelDeaths = 0;

    // Al iniciar nivel
    public void StartLevel(string levelName) {
        levelStartTime = Time.time;
        levelDeaths = 0;

        var data = new { level = levelName };
        StartCoroutine(POST($"/v1/games/{gameId}/level/start", data));
    }

    // Al completar nivel
    public void CompleteLevel(string levelName, string moralChoice = null, string relic = null) {
        // Calcular tiempo (NUNCA 0)
        int timeSeconds = Mathf.Max(1, Mathf.RoundToInt(Time.time - levelStartTime));

        var data = new {
            level = levelName,
            time_seconds = timeSeconds,
            deaths = levelDeaths,
            choice = moralChoice,  // "sanar", "forzar", etc. o null
            relic = relic          // "lirio", "hacha", "manto" o null
        };

        Debug.Log($"Completando nivel: {levelName}, Tiempo: {timeSeconds}s, Muertes: {levelDeaths}, Decisión: {moralChoice ?? "ninguna"}");

        StartCoroutine(POST($"/v1/games/{gameId}/level/complete", data));
    }

    // Al morir en un nivel
    public void OnPlayerDeath() {
        levelDeaths++;
    }

    // Ejemplo: Nivel con decisión moral
    public void OnSendaEbanoComplete(bool playerChoseSanar) {
        string choice = playerChoseSanar ? "sanar" : "forzar";
        CompleteLevel("senda_ebano", choice, "lirio");
    }
}
```

## 7. Testing con Postman/cURL

```bash
# 1. Login
curl -X POST http://localhost:8000/v1/players/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testplayer", "password": "password123"}'

# Guardar el player_token de la respuesta

# 2. Crear partida
curl -X POST http://localhost:8000/v1/games \
  -H "X-Player-Token: <tu_token>"

# Guardar el game_id de la respuesta

# 3. Completar nivel con decisión moral
curl -X POST http://localhost:8000/v1/games/<game_id>/level/complete \
  -H "X-Player-Token: <tu_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "level": "senda_ebano",
    "time_seconds": 245,
    "deaths": 3,
    "choice": "sanar",
    "relic": "lirio"
  }'
```

## 8. Troubleshooting

### El tiempo siempre aparece como 0 en la base de datos

**Diagnóstico:**
1. Verificar que Unity está enviando `time_seconds > 0` en el payload
2. Revisar logs del servidor para ver qué valor se recibe
3. Comprobar que `Time.time` funciona correctamente en Unity

**Fix:**
```csharp
// Añadir logs de debug
Debug.Log($"Level start time: {levelStartTime}");
Debug.Log($"Current time: {Time.time}");
Debug.Log($"Time difference: {Time.time - levelStartTime}");
int timeSeconds = Mathf.Max(1, Mathf.RoundToInt(Time.time - levelStartTime));
Debug.Log($"Sending time_seconds: {timeSeconds}");
```

### Las decisiones morales no se registran

**Diagnóstico:**
1. Verificar que el campo `choice` se está enviando en el JSON
2. Comprobar que el valor es exactamente uno de los válidos (minúsculas)
3. Revisar logs del servidor para ver si hay warnings

**Fix:**
```csharp
// Asegurarse de usar los valores exactos
string[] validChoices = {"sanar", "forzar", "construir", "destruir", "revelar", "ocultar"};

string choice = GetPlayerChoice(); // Tu lógica aquí
if (!Array.Exists(validChoices, c => c == choice)) {
    Debug.LogError($"Invalid choice: {choice}");
    return;
}
```

---

**Última actualización:** 2026-02-02
**Versión API:** v1
