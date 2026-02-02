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

**¿Qué hace la API?**
- Guarda el timestamp de inicio del nivel
- Este timestamp se usará para calcular la duración automáticamente

**En Unity (simplificado):**
```csharp
void OnLevelStart() {
    // Solo llama a la API - el servidor guarda el timestamp
    StartLevel("senda_ebano");
}
```

### 1.3 Completar un Nivel

**⭐ NUEVO: Cálculo Automático de Tiempo**

La API ahora **calcula automáticamente** la duración del nivel usando:
- Timestamp de inicio (guardado en `/level/start`)
- Timestamp actual (cuando se llama a `/level/complete`)

**Validaciones de seguridad:**
- ⏱️ Mínimo: 1 segundo
- ⏱️ Máximo: 1 hora (3600s)
- ⚠️ Si el tiempo excede 1 hora → se limita automáticamente

> **Nota:** Como el juego requiere conexión online, el tiempo se mide con precisión.
> El límite de 1 hora es una medida de seguridad contra edge cases.

**Opción 1: Sin enviar tiempo (RECOMENDADO para juegos online) ✅**
```http
POST /v1/games/{game_id}/level/complete
Headers:
  X-Player-Token: <token_del_jugador>
Body:
  {
    "level": "senda_ebano",
    "deaths": 3,
    "choice": "sanar",          // REQUERIDO para niveles con decisión moral
    "relic": "lirio"            // Solo si el nivel da reliquia
    // time_seconds: OMITIDO - se calcula automáticamente
  }
```

**Opción 2: Enviar tiempo manualmente (opcional)**
```http
POST /v1/games/{game_id}/level/complete
Headers:
  X-Player-Token: <token_del_jugador>
Body:
  {
    "level": "senda_ebano",
    "time_seconds": 245,        // Opcional - solo si quieres controlarlo desde Unity
    "deaths": 3,
    "choice": "sanar",
    "relic": "lirio"
  }
```

**En Unity (simplificado):**
```csharp
void OnLevelComplete() {
    // Ya NO necesitas medir el tiempo manualmente
    CompleteLevel("senda_ebano", deaths: playerDeaths, choice: "sanar");
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

### 3.1 Tiempo en 0 o Negativo (RESUELTO ✅)
```
❌ ERROR: "El tiempo debe ser mayor a 0 segundos"
```

**Causa anterior:** Unity enviaba `time_seconds: 0` o no medía correctamente.

**Solución actual:**
```csharp
// SIMPLIFICADO ✅ - No envíes time_seconds, el servidor lo calcula
var data = new {
    level = levelName,
    deaths = levelDeaths,
    choice = moralChoice
    // time_seconds: OMITIDO
};
```

**Si quieres enviarlo manualmente:**
```csharp
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
- ✅ **Opcional** - Se calcula automáticamente si no se envía
- ✅ Mayor a 0 (si se envía manualmente)
- ✅ Menor a 86400 (24 horas) (si se envía manualmente)
- ❌ 0 o negativo → ERROR (solo si se envía manualmente)
- ❌ Mayor a 24 horas → ERROR (solo si se envía manualmente)
- ⏱️ **Cálculo automático**:
  - `tiempo = timestamp_complete - timestamp_start`
  - Mínimo: 1 segundo
  - Máximo: 3600 segundos (1 hora)
  - Se limita automáticamente si excede los rangos

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

### Versión para Juego Online (RECOMENDADA) ⭐

**El servidor calcula el tiempo automáticamente - Unity solo reporta eventos**

```csharp
using System;
using UnityEngine;

public class GameAPIManager : MonoBehaviour {
    private string gameId;
    private int levelDeaths = 0;

    // Al iniciar nivel - Servidor guarda timestamp
    public void StartLevel(string levelName) {
        levelDeaths = 0;

        var data = new { level = levelName };
        StartCoroutine(POST($"/v1/games/{gameId}/level/start", data));

        Debug.Log($"✓ Nivel iniciado: {levelName}");
    }

    // Al completar nivel - Servidor calcula tiempo automáticamente
    public void CompleteLevel(string levelName, string moralChoice = null, string relic = null) {
        var data = new {
            level = levelName,
            // time_seconds: OMITIDO - calculado en servidor (inicio → ahora)
            deaths = levelDeaths,
            choice = moralChoice,  // "sanar", "forzar", etc. o null
            relic = relic          // "lirio", "hacha", "manto" o null
        };

        Debug.Log($"✓ Completando nivel: {levelName} | Muertes: {levelDeaths} | Decisión: {moralChoice ?? "ninguna"}");

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

**Ventajas para juego online:**
- ✅ Sin gestión de tiempo en Unity (más simple)
- ✅ Imposible manipular tiempos desde el cliente
- ✅ Precisión garantizada por el servidor
- ✅ Protección automática contra valores anómalos (1s - 1h)
```

### Versión con Tiempo Manual (Opcional)

Si prefieres controlar el tiempo desde Unity:

```csharp
public class GameAPIManager : MonoBehaviour {
    private string gameId;
    private float levelStartTime;
    private int levelDeaths = 0;

    public void StartLevel(string levelName) {
        levelStartTime = Time.time;
        levelDeaths = 0;
        var data = new { level = levelName };
        StartCoroutine(POST($"/v1/games/{gameId}/level/start", data));
    }

    public void CompleteLevel(string levelName, string moralChoice = null, string relic = null) {
        int timeSeconds = Mathf.Max(1, Mathf.RoundToInt(Time.time - levelStartTime));

        var data = new {
            level = levelName,
            time_seconds = timeSeconds,  // Tiempo manual desde Unity
            deaths = levelDeaths,
            choice = moralChoice,
            relic = relic
        };

        StartCoroutine(POST($"/v1/games/{gameId}/level/complete", data));
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

**Para juegos online (RECOMENDADO):**
No envíes `time_seconds` desde Unity. El servidor lo calcula automáticamente:

```csharp
// Unity NO maneja tiempo - servidor calcula
var data = new {
    level = levelName,
    deaths = levelDeaths,
    choice = moralChoice
    // time_seconds se calcula: timestamp_complete - timestamp_start
};
```

**Verificar en logs del servidor:**
```
⏱️  Tiempo calculado automáticamente: 245s (4 min) para nivel 'senda_ebano'
[Inicio: 2026-02-02 15:30:45, Fin: 2026-02-02 15:34:50]
```

**Si ves tiempo de 1 hora (3600s):**
```
⚠️  Tiempo calculado es 7200s (120 min) - excede límite razonable.
Posible pérdida de conexión. Forzando a 3600s (1 hora).
```

**Causas:**
- El jugador perdió conexión temporal durante el nivel
- El juego se pausó por mucho tiempo

**Solución:**
Como el juego es online, el tiempo debería ser normal. Si esto ocurre frecuentemente, considera:
1. Verificar que el juego se pausa correctamente en pérdida de conexión
2. Revisar la lógica de reconexión
3. Considerar enviar `time_seconds` desde Unity como respaldo

**Flujo correcto:**
```csharp
// 1. Primero iniciar (guarda timestamp en servidor)
StartLevel("senda_ebano");

// ... jugador juega el nivel (requiere conexión) ...

// 2. Luego completar (calcula: ahora - timestamp_inicio)
CompleteLevel("senda_ebano");
```

**Diagnóstico manual (si envías tiempo desde Unity):**
```csharp
Debug.Log($"Level start time: {levelStartTime}");
Debug.Log($"Current time: {Time.time}");
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
