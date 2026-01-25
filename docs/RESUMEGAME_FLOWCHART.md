# Diagrama de Flujo - Retomar Partida

Una visualización clara de cómo funciona retomar una partida en Triskel.

## Flujo General: Primer Inicio vs Reabrir

```
┌─────────────────────────────────────────────────────────────────┐
│                      PRIMERA VEZ (Día 1)                         │
└─────────────────────────────────────────────────────────────────┘

Presiona "Jugar"
    ↓
¿Tienes cuenta?
    ├─ NO → POST /v1/players (Registro)
    │        └─ Guarda: player_id, player_token
    │
    └─ SÍ → POST /v1/players/login (Login)
             └─ Guarda: player_id, player_token

Credenciales guardadas localmente ✓

¿Hay partida activa?
    └─ NO → Mostrar "NUEVA PARTIDA"

Usuario selecciona "NUEVA PARTIDA"
    ↓
POST /v1/games
    ├─ Crear game_id
    ├─ Guarda: game_id (localmente)
    └─ status = "in_progress"

POST /v1/sessions
    ├─ Crear session_id
    └─ Guarda: session_id (localmente)

Comienza juego en hub_central ✓


┌─────────────────────────────────────────────────────────────────┐
│              CIERRA LA APLICACIÓN (después de 1h)                │
└─────────────────────────────────────────────────────────────────┘

Presiona salir del juego
    ↓
PATCH /v1/games/{game_id}
    └─ Guardar: total_time_seconds=3600, current_level="senda_ebano"

PATCH /v1/sessions/{session_id}/end
    └─ Registrar fin de sesión

Aplicación cierra ✓
PERO el servidor tiene:
    • game_id
    • Estado actual (nivel, tiempo, reliquias)


┌─────────────────────────────────────────────────────────────────┐
│                 REABRE LA APLICACIÓN (Día 2)                    │
└─────────────────────────────────────────────────────────────────┘

Presiona "Jugar"
    ↓
¿Tengo player_id y player_token guardados?
    └─ SÍ ✓ → POST /v1/players/login
              └─ active_game_id = "game-123" ← ¡AQUÍ ESTÁ LA PISTA!

¿Hay partida activa?
    └─ SÍ → Mostrar "CONTINUAR PARTIDA" + "NUEVA PARTIDA"

Usuario selecciona "CONTINUAR PARTIDA"
    ↓
GET /v1/games/{active_game_id}
    
    Respuesta contiene:
    {
      "game_id": "game-123",
      "current_level": "senda_ebano",    ← Dónde estaba
      "total_time_seconds": 3600,         ← Tiempo jugado
      "levels_completed": ["hub_central"], ← Ya completó
      "relics": ["lirio"],                 ← Tiene esto
      "choices": {
        "senda_ebano": "sanar",            ← Ya eligió esto
        ...
      }
    }

EN EL JUEGO:
    1. Cargar nivel: "senda_ebano"
    2. Restaurar inventario: agregar "lirio"
    3. Mostrar tiempo: 1:00:00
    4. Mostrar estadísticas
    5. Marcar "senda_ebano" como completada
    6. Colocar jugador al inicio del nivel

POST /v1/sessions
    └─ Iniciar nuevo tracking para esta sesión

Continúa jugando ✓
```

## Diagrama Detallado: Cargar Estado

```
┌──────────────────────────────────────────────────────────────────┐
│           GET /v1/games/{game_id} - Respuesta JSON              │
└──────────────────────────────────────────────────────────────────┘

{
  "game_id": "550e8400-e29b-41d4-a716-446655440000",
  
  ┌─ INFORMACIÓN DE PROGRESO ─┐
  │ "current_level": "senda_ebano"
  │ "levels_completed": ["hub_central"]
  │ "completion_percentage": 33.3
  └──────────────────────────┘
         ↓ (En el juego)
         ├─ LevelManager.LoadLevel("senda_ebano")
         └─ Mostrar progreso: 33.3%
  
  ┌─ INVENTARIO ─┐
  │ "relics": ["lirio"]
  └───────────────┘
         ↓ (En el juego)
         ├─ InventoryManager.Clear()
         └─ InventoryManager.AddRelic("lirio")
  
  ┌─ TIEMPO ─┐
  │ "total_time_seconds": 1200
  └────────────┘
         ↓ (En el juego)
         └─ UIManager.SetTime(1200)  // Mostrar 20:00
  
  ┌─ DECISIONES ─┐
  │ "choices": {
  │   "senda_ebano": "sanar",      ← Ya hizo esto
  │   "fortaleza_gigantes": null,
  │   "aquelarre_sombras": null
  │ }
  └────────────┘
         ↓ (En el juego)
         ├─ DialogueManager.MarkAsComplete("senda_ebano")
         └─ NPC: "Ya veo que elegiste sanar..."
  
  ┌─ ESTADÍSTICAS ─┐
  │ "metrics": {
  │   "total_deaths": 5,
  │   "time_per_level": { ... }
  │ }
  └─────────────────┘
         ↓ (En el juego)
         └─ UIManager.Stats.Show(5 muertes)
  
  ┌─ JEFE ─┐
  │ "boss_defeated": false
  └──────────┘
         ↓ (En el juego)
         ├─ if (boss_defeated) then SKIP boss
         └─ else Jefe sigue disponible
}
```

## Árbol de Decisión: Menú Principal

```
                            LOGIN OK
                               │
                               ↓
                   ¿active_game_id != null?
                         /                \
                        /                  \
                      YES                   NO
                       │                    │
                       ↓                    ↓
         GET /v1/games/{game_id}    Mostrar "NUEVA PARTIDA"
                       │                    │
                       ↓                    ↓
         Mostrar opciones:          Usuario selecciona
         • CONTINUAR PARTIDA        "NUEVA PARTIDA"
         • NUEVA PARTIDA                    │
         • ESTADÍSTICAS                     ↓
                       │              POST /v1/games
                       │                    │
           ┌───────────┴───────────┐        │
           ↓                       ↓        ↓
     CONTINUAR            NUEVA PARTIDA   (ambas)
           │                      │        │
           ├─ Cargar estado       ├─ game_id nuevo
           ├─ Restaurar UI        └─ status: in_progress
           └─ Colocar jugador          │
                    │                  ↓
                    │           POST /v1/sessions
                    │                  │
                    └──────┬───────────┘
                           ↓
                    COMIENZA A JUGAR
                           
  • Si CONTINUAR: En senda_ebano con "lirio" y 20 min acumulados
  • Si NUEVA: En hub_central sin reliquias ni tiempo
```

## Secuencia de Llamadas: Flujo Completo

```
DÍA 1: PRIMERA VEZ
───────────────────
┌─ User input: Username + Password
└─ POST /v1/players
   ├─ Response: player_id, player_token
   └─ Guardar en PlayerPrefs

┌─ User input: "Nueva Partida"
└─ POST /v1/games
   ├─ Response: game_id, current_level="hub_central"
   └─ Guardar game_id en PlayerPrefs

┌─ POST /v1/sessions
   ├─ Body: {game_id, platform="windows"}
   └─ Guardar session_id en PlayerPrefs

[JUGADOR JUEGA 1 HORA]

┌─ User input: Cierra aplicación
└─ PATCH /v1/games/{game_id}
   ├─ Body: {total_time_seconds=3600, current_level="senda_ebano"}
   └─ Response: Estado guardado

└─ PATCH /v1/sessions/{session_id}/end
   └─ Registrar fin de sesión


DÍA 2: RETOMA PARTIDA
─────────────────────
┌─ User input: Abre aplicación
├─ Verificar PlayerPrefs: player_id ✓, player_token ✓
│
└─ POST /v1/players/login
   ├─ Body: {username, password}
   ├─ Response: active_game_id = "game-123"
   └─ ¡Detectado! Hay partida en progreso

┌─ GET /v1/players/me
   ├─ Response: Perfil del jugador
   └─ UI: Mostrar botón "CONTINUAR"

┌─ User input: "CONTINUAR PARTIDA"
└─ GET /v1/games/{active_game_id}
   ├─ Response: {
   │   current_level: "senda_ebano",
   │   total_time_seconds: 3600,
   │   relics: ["lirio"],
   │   choices: {senda_ebano: "sanar", ...}
   │ }
   └─ Restaurar TODO esto en el juego

┌─ POST /v1/sessions
   ├─ Body: {game_id, platform="windows"}
   └─ Guardar nuevo session_id

[JUGADOR CONTINÚA DONDE ESTABA]

┌─ [JUGADOR JUEGA OTRO NIVEL]
└─ POST /v1/games/{game_id}/level/complete
   ├─ Body: {level: "senda_ebano", time_seconds: 580, ...}
   └─ Response: levels_completed incluye "fortaleza_gigantes"

[Etc...]
```

## Comparación: Nuevo vs Continuar

```
┌──────────────────────────────────────────────────────────────┐
│                    NUEVA PARTIDA                             │
├──────────────────────────────────────────────────────────────┤
│ current_level: "hub_central"                                 │
│ total_time_seconds: 0                                        │
│ levels_completed: []                                         │
│ relics: []                                                   │
│ choices: {null, null, null}                                  │
│ boss_defeated: false                                         │
│                                                              │
│ ACCIONES EN JUEGO:                                           │
│ • Cargar hub_central                                         │
│ • Inventario vacío                                           │
│ • Mostrar todos los diálogos desde cero                      │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                  CONTINUAR PARTIDA                           │
├──────────────────────────────────────────────────────────────┤
│ current_level: "senda_ebano"                                 │
│ total_time_seconds: 3600                                     │
│ levels_completed: ["hub_central"]                            │
│ relics: ["lirio"]                                            │
│ choices: {sanar: true, null, null}                           │
│ boss_defeated: false                                         │
│                                                              │
│ ACCIONES EN JUEGO:                                           │
│ • Cargar senda_ebano                                         │
│ • Mostrar "lirio" en inventario                              │
│ • Mostrar: "20 minutos jugados"                              │
│ • Mostrar decisión previa en diálogos                        │
│ • Hub_central marcado como completado                        │
└──────────────────────────────────────────────────────────────┘
```

## Checklist: Implementación de Retomar Partida

```
DETECCIÓN:
 ☐ Después de login, verificar si active_game_id != null
 ☐ Si es null → mostrar solo "Nueva Partida"
 ☐ Si no es null → mostrar "Continuar" + "Nueva Partida"

CARGA DE ESTADO:
 ☐ GET /v1/games/{game_id}
 ☐ Guardar respuesta en una estructura local
 ☐ Extraer: current_level, relics, choices, total_time_seconds, metrics

RESTAURACIÓN:
 ☐ Cargar el nivel desde: current_level
 ☐ Restaurar inventario: agregar cada relic
 ☐ Mostrar tiempo: total_time_seconds convertido a MM:SS
 ☐ Mostrar muertes: metrics.total_deaths
 ☐ Marcar niveles completados en UI
 ☐ Marcar decisiones completadas (skip diálogos)
 ☐ Posicionar jugador al inicio del nivel (NO en checkpoint)
 ☐ Restaurar vida máxima del jugador

VALIDACIÓN:
 ☐ Si boss_defeated = true → Jefe ya no aparece
 ☐ Si levels_completed incluye nivel → No repetir intro
 ☐ Si choices[nivel] != null → No mostrar diálogo de decisión

TRACKING:
 ☐ POST /v1/sessions con game_id
 ☐ Guardar session_id retornado
 ☐ PATCH /v1/sessions/{session_id}/end al cerrar

GUARDADO:
 ☐ Cada 30s → PATCH /v1/games/{game_id}
 ☐ Enviar: total_time_seconds actual, current_level
 ☐ Al completar nivel → POST /v1/games/{game_id}/level/complete
```

## Errores Comunes a Evitar

```
❌ MALO: Cargar desde checkpoint interno guardado
   ├─ Razón: No sabes dónde está ese checkpoint
   └─ Solución: Cargar desde inicio del nivel

❌ MALO: Mostrar diálogos de decisión nuevamente
   ├─ Razón: El jugador ya los vio
   └─ Solución: Verificar choices[nivel] y saltar

❌ MALO: Dar reliquias nuevas aleatorias
   ├─ Razón: No son las que realmente obtuvo
   └─ Solución: Usar exactamente las del array relics

❌ MALO: Ignorar el tiempo acumulado
   ├─ Razón: Quitas logros de speedrun
   └─ Solución: Mostrar total_time_seconds en UI

❌ MALO: No terminar la sesión anterior
   ├─ Razón: Sesiones huérfanas en la BD
   └─ Solución: Siempre PATCH /v1/sessions/{id}/end

❌ MALO: Perder player_id y player_token
   ├─ Razón: El jugador tendrá que hacer login de nuevo
   └─ Solución: Usar PlayerPrefs.Save() después de guardar
```

## Ejemplo de Restauración Paso a Paso

```
GET /v1/games/game-123
Respuesta:
{
  "current_level": "senda_ebano",
  "total_time_seconds": 1500,
  "relics": ["lirio"],
  "choices": {"senda_ebano": "sanar", ...},
  "levels_completed": ["hub_central"],
  "metrics": {"total_deaths": 5}
}

PASO 1: Cargar Nivel
  LevelManager.LoadLevel("senda_ebano");

PASO 2: Restaurar Inventario
  Inventory.Clear();
  foreach (string relic in ["lirio"]) {
    Inventory.AddRelic(relic);  // Se ve en UI
  }

PASO 3: Mostrar Tiempo
  int minutes = 1500 / 60;  // 25
  int seconds = 1500 % 60;  // 0
  UIManager.PlaytimeLabel.text = "25:00";

PASO 4: Mostrar Estadísticas
  UIManager.DeathCounter.text = "5 Muertes";
  UIManager.ProgressBar.Fill(33.3);

PASO 5: Marcar Nivel Completado
  LevelUI.MarkComplete("hub_central");  // Se ve en mapa
  
PASO 6: Saltar Diálogo si Ya Lo Hizo
  if (gameData.choices["senda_ebano"] == "sanar") {
    DialogueManager.SkipDialogue("senda_ebano_choice");
    NPC.SayLine("Already chose to heal");
  }

PASO 7: Posicionar Jugador
  Player.position = LevelManager.GetSpawnPoint();
  Player.health = Player.maxHealth;

RESULTADO: Jugador está en senda_ebano con lirio, 25 minutos, 
           5 muertes, decisión anterior respetada.
```
