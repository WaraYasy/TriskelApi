# Documentación de Triskel-API

Bienvenido a la documentación de Triskel-API. Aquí encontrarás toda la información necesaria para desplegar, usar e integrar la API.

## 🚀 Integración del Juego (Comienza aquí)

**📍 COMIENZA AQUÍ:** Lee [INDICE_COMPLETO.md](./INDICE_COMPLETO.md) para una guía visual de toda la documentación y navegación.

**Para integrar el juego con la API, lee estos archivos en orden:**

1. **[GAME_INTEGRATION_API.md](./GAME_INTEGRATION_API.md)** ⭐ **PRINCIPAL**
   - Cómo hacer llamadas HTTP a la API
   - Endpoints completos con ejemplos
   - Flujo de login, partidas y sesiones
   - **Sección especial: "Retomar Partida"** (¡lo más importante!)
   - Ejemplos en C# y Python

2. **[QUICK_REFERENCE.md](./QUICK_REFERENCE.md)** - Referencia rápida
   - Tabla de todos los endpoints
   - Cuerpos de request y response
   - Códigos de error y soluciones
   - Tipos de eventos disponibles
   - Decisiones morales y niveles

3. **[UNITY_QUICK_START.md](./UNITY_QUICK_START.md)** - Guía práctica para Unity
   - Implementación paso a paso en Unity C#
   - Código listo para copiar y usar
   - Cómo retomar partidas en Unity
   - Menú principal con detectar partida activa
   - Guardado automático de progreso

4. **[RESUMEGAME_FLOWCHART.md](./RESUMEGAME_FLOWCHART.md)** - Diagramas visuales
   - Flujos de primer inicio vs reabrir
   - Árbol de decisión del menú
   - Secuencia de llamadas API
   - Checklist de implementación
   - Errores comunes a evitar

### Índice de Documentación

### 📦 Despliegue

- **[RAILWAY_DEPLOYMENT.md](./RAILWAY_DEPLOYMENT.md)** - Guía completa para desplegar la API en Railway
  - Variables de entorno obligatorias y opcionales
  - Configuración de CORS para Unity y Web
  - Pasos detallados de despliegue
  - Solución de problemas comunes
  - Checklist de despliegue

- **[SECURITY_KEYS.md](./SECURITY_KEYS.md)** - Guía sobre las claves de seguridad
  - Diferencia entre SECRET_KEY y API_KEY
  - Para qué sirve cada una
  - Cómo generarlas y configurarlas
  - Mejores prácticas de seguridad

### 🎮 Integración con Unity

- **[UNITY_INTEGRATION.md](./UNITY_INTEGRATION.md)** - Guía antigua (ver UNITY_QUICK_START.md)
  - Configuración para Unity Nativo vs WebGL
  - Ejemplos de código C# completos
  - Endpoints principales y cómo usarlos
  - Flujo completo de integración
  - Debugging y errores comunes

## Inicio Rápido

### Para Integrar el Juego

1. **Lee primero:** [GAME_INTEGRATION_API.md](./GAME_INTEGRATION_API.md)
   - Especialmente la sección "Cómo Hacer Llamadas a la API"
   - Y "Retomar Partida (Lo Más Importante)"

2. **Copia código:** [UNITY_QUICK_START.md](./UNITY_QUICK_START.md)
   - Clase `TriskelAPIClient` lista para usar
   - Métodos para login, crear partida, cargar partida, etc.

3. **Implementa en tu proyecto Unity:**
   ```csharp
   // Crear cuenta
   yield return apiClient.Register("jugador123", "password123");
   
   // Login
   yield return apiClient.Login("jugador123", "password123");
   
   // Cargar partida activa
   if (tienePartidaActiva) {
       yield return apiClient.LoadGame(gameID);
   }
   ```

4. **Mantén esta tabla a mano:** [QUICK_REFERENCE.md](./QUICK_REFERENCE.md)

### Para Desplegar en Railway

1. Lee [RAILWAY_DEPLOYMENT.md](./RAILWAY_DEPLOYMENT.md)
2. Genera las claves necesarias:
   ```bash
   openssl rand -hex 32  # SECRET_KEY
   openssl rand -hex 32  # API_KEY
   cat config/firebase-credentials.json | base64 -w 0  # FIREBASE_CREDENTIALS_BASE64
   ```
3. Configura las variables en Railway
4. Despliega

### Para Conectar Unity

1. Lee [GAME_INTEGRATION_API.md](./GAME_INTEGRATION_API.md)
2. Copia la clase `TriskelAPIClient` desde [UNITY_QUICK_START.md](./UNITY_QUICK_START.md)
3. Actualiza la `baseURL` con tu URL de la API
4. Úsala en tu código


## Estructura del Proyecto

```
Triskel-API/
├── app/                          # Código de la aplicación
│   ├── config/                   # Configuración
│   │   └── settings.py          # ⭐ Variables de entorno
│   ├── domain/                   # Lógica de negocio
│   │   ├── players/             # Gestión de jugadores
│   │   ├── games/               # Gestión de partidas
│   │   └── web/                 # Dashboard web
│   ├── infrastructure/          # Infraestructura
│   │   └── database/
│   │       └── firebase_client.py  # ⭐ Conexión a Firebase
│   └── main.py                  # ⭐ Aplicación principal
├── docs/                        # Documentación
│   ├── README.md               # Este archivo
│   ├── RAILWAY_DEPLOYMENT.md   # Guía de despliegue
│   └── UNITY_INTEGRATION.md    # Guía de Unity
├── config/
│   └── firebase-credentials.json  # Credenciales Firebase (no commitear)
├── .env                         # Variables locales (no commitear)
├── .env.example                 # Plantilla de variables
├── railway.json                 # Configuración Railway
├── Procfile                     # Comando de inicio
├── requirements.txt             # Dependencias Python
└── runtime.txt                  # Versión Python
```

## Tecnologías

- **Framework:** FastAPI (API REST) + Flask (Dashboard Web)
- **Base de Datos:** Firebase Firestore
- **Despliegue:** Railway
- **Lenguaje:** Python 3.11
- **Cliente:** Unity (C#)

## Variables de Entorno

### Obligatorias en Producción

| Variable | Descripción | Cómo generarla |
|----------|-------------|----------------|
| `SECRET_KEY` | Clave secreta para operaciones de seguridad | `openssl rand -hex 32` |
| `API_KEY` | Clave API para acceso administrativo | `openssl rand -hex 32` |
| `FIREBASE_CREDENTIALS_BASE64` | Credenciales Firebase en base64 | `cat config/firebase-credentials.json \| base64 -w 0` |

### Opcionales

| Variable | Descripción | Valor por defecto |
|----------|-------------|-------------------|
| `CORS_ORIGINS` | Orígenes permitidos (separados por comas) | `*` (desarrollo) / `""` (producción) |
| `LOG_LEVEL` | Nivel de logs | `DEBUG` (desarrollo) / `INFO` (producción) |

### No Configurables (Automáticas)

| Variable | Descripción | Valor |
|----------|-------------|-------|
| `APP_NAME` | Nombre de la aplicación | `Triskel-API` (hardcodeado) |
| `DEBUG` | Modo debug | Detectado automáticamente |
| `PORT` | Puerto de la aplicación | Proporcionado por Railway |
| `ENVIRONMENT` | Entorno de ejecución | Detectado automáticamente |

## Endpoints Principales

- `GET /` - Información de la API
- `GET /health` - Health check
- `GET /docs` - Documentación interactiva (Swagger)
- `POST /v1/players` - Crear jugador
- `GET /v1/players/me` - Obtener perfil del jugador
- `POST /v1/games` - Iniciar partida
- `PATCH /v1/games/{game_id}/complete` - Finalizar partida
- `GET /web/` - Dashboard web (Flask)

## Autenticación

La API usa dos métodos de autenticación:

1. **API Key** (Administradores)
   - Header: `X-API-Key: <tu-api-key>`
   - Acceso total a todos los endpoints

2. **Player Auth** (Jugadores)
   - Headers: `X-Player-ID` y `X-Player-Token`
   - Acceso solo a recursos propios del jugador

## Soporte

Si tienes problemas:

1. **Despliegue:** Consulta [RAILWAY_DEPLOYMENT.md](./RAILWAY_DEPLOYMENT.md)
2. **Integración Unity:** Consulta [UNITY_INTEGRATION.md](./UNITY_INTEGRATION.md)
3. **Errores de la API:** Revisa los logs en Railway
4. **API Docs:** Visita `https://tu-api.railway.app/docs`

## Contribuir

Para contribuir al proyecto:

1. Clona el repositorio
2. Crea una rama feature: `git checkout -b feature/nueva-funcionalidad`
3. Haz commit de tus cambios: `git commit -m "Añadir nueva funcionalidad"`
4. Push a la rama: `git push origin feature/nueva-funcionalidad`
5. Crea un Pull Request

## Licencia

[Especificar licencia del proyecto]

---

Documentación actualizada: 2025-01-10
