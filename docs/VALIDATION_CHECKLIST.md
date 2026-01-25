# ✅ Checklist de Validación - Triskel API

Use este documento para validar que su integración de API está completa y funcionando correctamente.

---

## 📋 Validación de Configuración Inicial

### Setup Básico
- [ ] Base URL: `https://triskel-api.railway.app` (o tu URL custom)
- [ ] Headers configured: `X-Player-ID`, `X-Player-Token`, `Content-Type: application/json`
- [ ] CORS habilitado en el servidor para tu dominio
- [ ] Credenciales Firebase configuradas

### Documentación Completada
- [ ] Leído [README.md](./README.md)
- [ ] Leído [GAME_INTEGRATION_API.md](./GAME_INTEGRATION_API.md) - Sección "Cómo Hacer Llamadas"
- [ ] Leído [GAME_INTEGRATION_API.md](./GAME_INTEGRATION_API.md) - Sección "Retomar Partida"
- [ ] Revisado [QUICK_REFERENCE.md](./QUICK_REFERENCE.md)
- [ ] Revisado [UNITY_QUICK_START.md](./UNITY_QUICK_START.md) (si usas Unity)

---

## 🔐 Validación de Autenticación

### Registro de Jugador
- [ ] POST `/v1/players` funciona
  - [ ] Username y password enviados correctamente
  - [ ] Response devuelve `player_id`
  - [ ] Token guardado localmente (PlayerPrefs/LocalStorage)

### Login
- [ ] POST `/v1/players/login` funciona
  - [ ] Username y password enviados
  - [ ] Response devuelve `player_id` y `player_token`
  - [ ] Response devuelve **`active_game_id`** (¡importante!)
  - [ ] Credenciales guardadas para calls posteriores

### Perfil
- [ ] GET `/v1/players/me` funciona
  - [ ] Headers `X-Player-ID` y `X-Player-Token` correctos
  - [ ] Response devuelve datos del jugador

---

## 🎮 Validación de Partidas - Nueva Partida

### Crear Nueva Partida
- [ ] POST `/v1/games` funciona
  - [ ] Respuesta contiene `game_id` único
  - [ ] Respuesta contiene `status: "in_progress"`
  - [ ] Respuesta contiene `current_level: "hub_central"`
  - [ ] Respuesta contiene campos vacíos:
    - [ ] `levels_completed: []`
    - [ ] `relics: []`
    - [ ] `choices: {}`
    - [ ] `metrics: {}`

### Cargar Partida Nueva
- [ ] GET `/v1/games/{game_id}` devuelve estado inicial
  - [ ] `total_time_seconds: 0`
  - [ ] `completion_percentage: 0`
  - [ ] `boss_defeated: false`

---

## ♻️ Validación de Partidas - Retomar Partida

### Flujo de Detección
- [ ] Login devuelve `active_game_id` (si hay partida activa)
- [ ] Si `active_game_id` no null:
  - [ ] GET `/v1/games/{active_game_id}` se llama automáticamente
  - [ ] Respuesta se usa para restaurar estado

### Restauración de Estado - Nivel
- [ ] `current_level` se carga correctamente
  - [ ] Nivel aparece en el menú de juego
  - [ ] Jugador está en posición correcta

### Restauración de Estado - Inventario
- [ ] `relics` array se restaura
  - [ ] [ ] Lirio aparece si está en array
  - [ ] [ ] Hacha aparece si está en array
  - [ ] [ ] Manto aparece si está en array

### Restauración de Estado - Decisiones
- [ ] `choices` object se restaura
  - [ ] Diálogos muestran decisiones previas como "ya completada"
  - [ ] No se permite cambiar decisiones tomadas
  - [ ] Decisiones `null` son opcionales

### Restauración de Estado - Tiempo
- [ ] `total_time_seconds` se muestra
  - [ ] Cronómetro inicia con tiempo acumulado
  - [ ] Minutos = total_time_seconds / 60

### Restauración de Estado - Métricas
- [ ] `metrics` se restauran
  - [ ] Muertes por nivel mostradas correctamente
  - [ ] Tiempo por nivel mostrado correctamente

### Restauración de Estado - Progreso
- [ ] `levels_completed` se marca
  - [ ] Niveles completados no pueden reiniciarse
  - [ ] Barra de progreso muestra `completion_percentage`

---

## 🎬 Validación de Niveles

### Iniciar Nivel
- [ ] POST `/v1/games/{game_id}/level/start` funciona
  - [ ] Level_id enviado correctamente
  - [ ] Response devuelve `status: "level_started"`
  - [ ] Session tracking iniciado

### Completar Nivel
- [ ] POST `/v1/games/{game_id}/level/complete` funciona
  - [ ] Level_id y metricas enviadas (deaths, time_spent)
  - [ ] Response actualiza `levels_completed`
  - [ ] Response actualiza `metrics`
  - [ ] Response actualiza `total_time_seconds`

### Niveles Opcionales
- [ ] Senda Ébano (senda_ebano) - Decisión moral funcionando
- [ ] Fortaleza Gigantes (fortaleza_gigantes) - Decisión moral funcionando
- [ ] Aquelarre Sombras (aquelarre_sombras) - Decisión moral funcionando

---

## 🏁 Validación de Finalización

### Completar Juego
- [ ] POST `/v1/games/{game_id}/complete` funciona
  - [ ] Todos los niveles completados
  - [ ] Response devuelve `status: "completed"`
  - [ ] Response devuelve `completion_percentage: 100`

### Post-Finalización
- [ ] GET `/v1/games/{game_id}` devuelve `status: "completed"`
- [ ] Menú principal muestra botón "NUEVA PARTIDA" en siguiente login
- [ ] `active_game_id` es null en siguiente login

---

## 📊 Validación de Sesiones

### Inicio de Sesión
- [ ] POST `/v1/sessions` funciona
  - [ ] game_id enviado
  - [ ] platform enviado (windows/android)
  - [ ] Response devuelve `session_id`
  - [ ] Response devuelve `started_at`

### Fin de Sesión
- [ ] PATCH `/v1/sessions/{session_id}/end` funciona
  - [ ] Response devuelve `ended_at`
  - [ ] Response devuelve `duration_seconds`
  - [ ] Se ejecuta al cerrar juego

### Seguimiento de Playtime
- [ ] Cada sesión se registra por plataforma
- [ ] Tiempo total se suma entre sesiones

---

## 📡 Validación de Eventos

### Crear Evento Individual
- [ ] POST `/v1/events` funciona
  - [ ] event_type enviado (choice, death, checkpoint, etc.)
  - [ ] game_id enviado
  - [ ] timestamp enviado
  - [ ] metadata enviado (según tipo de evento)

### Crear Eventos en Batch
- [ ] POST `/v1/events/batch` funciona
  - [ ] Array de eventos enviado
  - [ ] Todos los eventos se registran
  - [ ] Response devuelve lista de event_ids

### Tipos de Eventos
- [ ] `choice` - Decisión moral registrada
- [ ] `death` - Muerte del jugador
- [ ] `checkpoint` - Progreso guardado
- [ ] `interaction` - NPC interaction
- [ ] `game_start` - Inicio de juego
- [ ] `game_end` - Fin de juego
- [ ] `level_start` - Inicio de nivel
- [ ] `level_complete` - Nivel completado

---

## 🛡️ Validación de Manejo de Errores

### Errores de Autenticación
- [ ] 401 cuando X-Player-ID/Token inválidos
  - [ ] Mensaje de error claro
  - [ ] Opción de re-login presentada

### Errores de Validación
- [ ] 400 cuando datos inválidos
  - [ ] Campo requerido faltante
  - [ ] Tipo de dato incorrecto
  - [ ] Valor fuera de rango

### Errores de Not Found
- [ ] 404 cuando game_id no existe
  - [ ] Mensaje claro: "Partida no encontrada"
  - [ ] Sugerir crear nueva partida

### Errores de Servidor
- [ ] 500 devuelve mensaje genérico
  - [ ] Sin exponer detalles internos
  - [ ] Reintento después de delay

### Manejo de Timeouts
- [ ] Timeout > 30 segundos = reintentar
- [ ] Timeout > 2 minutos = error al usuario

---

## 🎨 Validación de Integración Unity

### Instalación de Clase
- [ ] TriskelAPIClient copiada en Assets/
- [ ] Namespace correcto (no conflictos)
- [ ] Referencias a UnityWebRequest funcionales

### Métodos Disponibles
- [ ] `Register()` funciona
- [ ] `Login()` funciona y devuelve active_game_id
- [ ] `CreateGame()` funciona
- [ ] `LoadGame()` funciona
- [ ] `RestoreGameState()` funciona
  - [ ] Carga nivel
  - [ ] Restaura inventario
  - [ ] Restaura decisiones
  - [ ] Restaura tiempo

### Menú Principal
- [ ] Botón "NUEVA PARTIDA" crea nueva
- [ ] Botón "CONTINUAR" carga partida activa
- [ ] Detecta automáticamente si hay active_game_id

### Guardado Automático
- [ ] `SaveProgress()` llamado cada 30 segundos
- [ ] Datos se sincronizan correctamente
- [ ] No causa lag perceptible

---

## 📱 Validación de Plataformas

### Windows
- [ ] Juego se ejecuta en Windows
- [ ] Sesiones rastreadas con `platform: "windows"`
- [ ] Datos se guardan correctamente

### Android
- [ ] Juego se ejecuta en Android
- [ ] Sesiones rastreadas con `platform: "android"`
- [ ] Datos se guardan correctamente

### Multiplataforma
- [ ] Guardar en Windows, continuar en Android
- [ ] Guardar en Android, continuar en Windows
- [ ] Datos sincronizados correctamente

---

## 🧮 Validación de Cálculos

### Alineamiento Moral
- [ ] Decisiones registran moral_alignment correctamente
- [ ] Escala: -100 (muy maligno) a 100 (muy benévolo)
- [ ] Impacta eventos y diálogos

### Porcentaje de Completación
- [ ] Formula: (niveles_completados / total_niveles) * 100
- [ ] Se actualiza correctamente después de cada nivel
- [ ] Llega a 100 cuando todos completados

### Métricas de Tiempo
- [ ] time_per_level se suma correctamente
- [ ] total_time_seconds es suma de todos los tiempos
- [ ] No hay overflow en números grandes

### Métricas de Muertes
- [ ] deaths_per_level cuenta correctamente
- [ ] total_deaths es suma de todas las muertes
- [ ] Se resetea al comenzar nuevo nivel

---

## 📚 Validación de Datos Constantes

### Niveles Disponibles
- [ ] [ ] `hub_central`
- [ ] [ ] `senda_ebano`
- [ ] [ ] `fortaleza_gigantes`
- [ ] [ ] `aquelarre_sombras`
- [ ] [ ] Todos aparecen en menú

### Reliquias
- [ ] [ ] `lirio` - Coleccionable
- [ ] [ ] `hacha` - Coleccionable
- [ ] [ ] `manto` - Coleccionable
- [ ] [ ] Se muestran en inventario

### Decisiones Morales
- [ ] Senda Ébano: `sanar` o `destruir`
- [ ] Fortaleza Gigantes: `proteger` o `abandonar`
- [ ] Aquelarre Sombras: `traicionar` o `sacrificar`

### Estados de Partida
- [ ] `in_progress` - Partida activa
- [ ] `completed` - Partida completada
- [ ] `abandoned` - Partida abandonada

---

## 🚀 Validación de Despliegue

### Variables de Entorno
- [ ] `DATABASE_URL` configurada correctamente
- [ ] `SECRET_KEY` establecida (para JWT)
- [ ] `FIREBASE_CREDENTIALS` path correcto
- [ ] `CORS_ORIGINS` incluye tu frontend

### HTTPS
- [ ] Certificado SSL válido
- [ ] No hay warnings de seguridad
- [ ] Headers de seguridad presentes

### Performance
- [ ] Response < 500ms en conexión normal
- [ ] Puede manejar 100+ requests/segundo
- [ ] No hay memory leaks después de 1 hora

---

## 📊 Validación de Reportes

### Analíticos
- [ ] Total de jugadores aumenta
- [ ] Sesiones se registran correctamente
- [ ] Eventos se almacenan correctamente
- [ ] Decisiones se pueden extraer por nivel

### Debugging
- [ ] Logs en servidor muestran errores
- [ ] Request/response logging habilitado (si necesario)
- [ ] IDs de transacción para debugging

---

## ✨ Validación Final de Integración

### Flujo Completo - Nuevo Jugador
- [ ] 1. Registro successful
- [ ] 2. Login devuelve nuevo player_id
- [ ] 3. Login devuelve `active_game_id: null`
- [ ] 4. Menú muestra solo "NUEVA PARTIDA"
- [ ] 5. Nueva partida creada
- [ ] 6. Juego inicia

### Flujo Completo - Retomar Partida
- [ ] 1. Cierre juego normalmente
- [ ] 2. Re-abra aplicación
- [ ] 3. Login devuelve mismo `active_game_id`
- [ ] 4. GET /games/{id} carga estado
- [ ] 5. Menú muestra "CONTINUAR" destacado
- [ ] 6. Click continuar restaura nivel exactamente como estaba

### Flujo Completo - Completar Juego
- [ ] 1. Todos los niveles completados
- [ ] 2. POST /complete funciona
- [ ] 3. Status cambia a "completed"
- [ ] 4. Siguiente login muestra `active_game_id: null`
- [ ] 5. Menú muestra solo "NUEVA PARTIDA"

---

## 🐛 Validación de Edge Cases

### Partida Incompleta
- [ ] Guardar sin completar nivel
- [ ] Cargar mantiene estado parcial
- [ ] No hay corrupción de datos

### Múltiples Sesiones
- [ ] Abrir en Windows
- [ ] Sin cerrar, abrir en Android (mismo navegador/cuenta)
- [ ] Estado se sincroniza o maneja error correctamente

### Conexión Perdida
- [ ] API inaccesible durante juego
- [ ] Datos locales se usan
- [ ] Sincronización cuando reconecta

### Datos Corruptos
- [ ] Algún campo inválido en respuesta
- [ ] Mostrar error amigable, no crash
- [ ] Permitir volver a intentar

---

## 📝 Checklist Final

- [ ] Todos los items anteriores completados
- [ ] Juego se ejecuta sin errores
- [ ] Prueba en dispositivo real (no solo emulador)
- [ ] Conexión a internet requerida
- [ ] Datos se guardan en Firestore
- [ ] Siguiente sesión restaura correctamente
- [ ] Documentación completada

---

## 🎉 Validación Exitosa

Si todos los items están marcados:

✅ **Tu integración de Triskel API es correcta y lista para producción**

---

## 📞 Si Algo No Funciona

1. **Verifica headers:** X-Player-ID, X-Player-Token, Content-Type
2. **Verifica URLs:** Base URL, endpoints, game_ids
3. **Verifica permisos:** CORS habilitado, credenciales válidas
4. **Revisa logs:** Servidor debe mostrar qué salió mal
5. **Consulta QUICK_REFERENCE.md:** Códigos de error y soluciones

---

**Última actualización:** 25 de enero de 2026
