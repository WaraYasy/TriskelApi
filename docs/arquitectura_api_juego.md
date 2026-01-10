# ARQUITECTURA API - Backend del Juego (Python + ADAT)

## 1. VISIÓN GENERAL

### 1.1. Stack Tecnológico
- **Framework API**: FastAPI (REST API)
- **Framework Web**: Flask (Dashboard)
- **Base de Datos**: Firebase Firestore
- **ORM/Modelado**: Pydantic para validación + Modelos propios
- **Visualización**: Plotly + Pandas
- **Migraciones**: Alembic (para futuras migraciones)
- **Logging**: Python logging module

### 1.2. Arquitectura en Capas

```
┌─────────────────────────────────────────────┐
│           CLIENTE (Godot/Unity)             │
└──────────────────┬──────────────────────────┘
                   │ HTTP/REST
┌──────────────────▼──────────────────────────┐
│         API LAYER (FastAPI)                 │
│  - Endpoints REST                           │
│  - Validación de entrada                    │
│  - Manejo de errores                        │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│      SERVICE LAYER (Lógica de Negocio)     │
│  - Cálculo de métricas                      │
│  - Validaciones complejas                   │
│  - Orquestación de operaciones              │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│    REPOSITORY LAYER (Acceso a Datos)       │
│  - Abstracción de Firebase                  │
│  - Operaciones CRUD                         │
│  - Queries complejas                        │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│         FIREBASE FIRESTORE                  │
│  - Persistencia de datos                    │
└─────────────────────────────────────────────┘

         ┌─────────────────────┐
         │  DASHBOARD (Flask)  │
         │  - Visualización    │
         │  - Plotly Charts    │
         │  - Pandas Analysis  │
         └─────────────────────┘
```

---

## 2. MODELO DE DATOS

### 2.1. Colecciones en Firestore

#### 2.1.1. `players` (Jugadores)
```json
{
  "player_id": "string (UUID)",
  "username": "string",
  "email": "string (opcional)",
  "created_at": "timestamp",
  "last_login": "timestamp",
  "total_playtime_seconds": "integer",
  "games_played": "integer",
  "games_completed": "integer",
  
  // Estadísticas globales (se actualizan con cada partida)
  "stats": {
    "total_good_choices": "integer",
    "total_bad_choices": "integer",
    "total_deaths": "integer",
    "favorite_relic": "string (lirio|hacha|manto|null)",
    "best_speedrun_seconds": "integer|null",
    "moral_alignment": "float (-1.0 a 1.0)"
  }
}
```

#### 2.1.2. `games` (Partidas)
```json
{
  "game_id": "string (UUID)",
  "player_id": "string (FK a players)",
  "started_at": "timestamp",
  "ended_at": "timestamp | null",
  "status": "string (in_progress|completed|abandoned)",
  "completion_percentage": "float (0-100)",
  "total_time_seconds": "integer",
  
  // Progreso de niveles
  "levels_completed": ["string"],
  "current_level": "string | null",
  
  // Decisiones morales
  "choices": {
    "senda_ebano": "string (forzar|sanar|null)",
    "fortaleza_gigantes": "string (destruir|construir|null)",
    "aquelarre_sombras": "string (ocultar|revelar|null)"
  },
  
  // Reliquias obtenidas
  "relics": ["string"],
  
  // Resultado final
  "boss_defeated": "boolean",
  "npcs_helped": ["string"],
  
  // Métricas de gameplay (se actualizan desde eventos)
  "metrics": {
    "total_deaths": "integer",
    "time_per_level": {
      "hub_central": "integer (segundos)",
      "senda_ebano": "integer",
      "fortaleza_gigantes": "integer",
      "aquelarre_sombras": "integer",
      "claro_almas": "integer"
    },
    "deaths_per_level": {
      "hub_central": "integer",
      "senda_ebano": "integer",
      "fortaleza_gigantes": "integer",
      "aquelarre_sombras": "integer",
      "claro_almas": "integer"
    }
  }
}
```

#### 2.1.3. `game_events` (Eventos del juego)
```json
{
  "event_id": "string (UUID)",
  "game_id": "string (FK a games)",
  "player_id": "string (FK a players)",
  "timestamp": "timestamp",
  "event_type": "string",
  "level": "string",
  "data": "object (JSON flexible según tipo de evento)"
}
```

**Tipos de eventos completos**:
- `level_start` - Inicio de nivel
- `level_complete` - Nivel completado
- `player_death` - Muerte del jugador
- `choice_made` - Elección moral tomada
- `relic_obtained` - Reliquia conseguida
- `boss_defeated` - Boss final derrotado
- `boss_phase_change` - Cambio de fase del boss
- `npc_interaction` - Interacción con NPC
- `dialog_triggered` - Diálogo activado
- `dash_used` - Habilidad dash utilizada
- `pause_game` - Juego pausado
- `resume_game` - Juego reanudado

**Ejemplos detallados de `data`**:
```json
// level_start
{ "level_name": "senda_ebano" }

// level_complete
{ "level_name": "senda_ebano", "time_seconds": 245, "deaths": 3 }

// player_death
{ "cause": "fall", "position": {"x": 150, "y": 200} }

// choice_made
{ "choice": "sanar", "alignment": "good", "level": "senda_ebano" }

// relic_obtained
{ "relic": "lirio", "level": "senda_ebano" }

// boss_phase_change
{ "phase": 2, "boss_health_percentage": 65.5 }

// npc_interaction
{ "npc_type": "fantasma", "interaction_type": "help" }

// dash_used
{ "position": {"x": 120, "y": 180}, "direction": "right" }
```

#### 2.1.4. `sessions` (Sesiones de juego)
```json
{
  "session_id": "string (UUID)",
  "player_id": "string (FK a players)",
  "game_id": "string (FK a games)",
  "started_at": "timestamp",
  "ended_at": "timestamp | null",
  "duration_seconds": "integer",
  "platform": "string (windows|mac|linux|web)",
  "game_version": "string",
  "ip_address": "string (opcional, para analytics)"
}
```

#### 2.1.5. `leaderboards` (Clasificaciones)
```json
{
  "leaderboard_id": "string",
  "category": "string (speedrun|moral_good|moral_evil|completion_rate|perfectionist)",
  "updated_at": "timestamp",
  "entries": [
    {
      "rank": "integer",
      "player_id": "string",
      "username": "string",
      "value": "number",
      "game_id": "string",
      "achieved_at": "timestamp"
    }
  ]
}
```
*Nota: Se recalcula periódicamente (cada hora) mediante una función programada*

---

## 3. ENDPOINTS DE LA API

### 3.1. Gestión de Jugadores

#### `POST /api/players`
**Descripción**: Crear un nuevo jugador
**Request Body**:
```json
{
  "username": "string (min 3, max 20)",
  "email": "string | null (opcional)"
}
```
**Response**: `201 Created`
```json
{
  "player_id": "uuid",
  "username": "string",
  "email": "string | null",
  "created_at": "timestamp"
}
```

#### `GET /api/players/{player_id}`
**Descripción**: Obtener información de un jugador
**Response**: `200 OK`
```json
{
  "player_id": "uuid",
  "username": "string",
  "created_at": "timestamp",
  "stats": { ... }
}
```

#### `GET /api/players/{player_id}/stats`
**Descripción**: Obtener estadísticas completas del jugador
**Response**: `200 OK`
```json
{
  "global_stats": { ... },
  "games_history": [ ... ],
  "achievements": [ ... ],
  "moral_profile": {
    "alignment": "float",
    "good_choices_percentage": "float",
    "favorite_approach": "string"
  }
}
```

---

### 3.2. Gestión de Partidas

#### `POST /api/games`
**Descripción**: Iniciar una nueva partida
**Request Body**:
```json
{
  "player_id": "uuid"
}
```
**Response**: `201 Created`
```json
{
  "game_id": "uuid",
  "player_id": "uuid",
  "started_at": "timestamp",
  "status": "in_progress"
}
```

#### `GET /api/games/{game_id}`
**Descripción**: Obtener información de una partida
**Response**: `200 OK`

#### `PATCH /api/games/{game_id}`
**Descripción**: Actualizar estado de una partida
**Request Body**:
```json
{
  "status": "completed | abandoned",
  "ended_at": "timestamp",
  "final_stats": { ... }
}
```

#### `POST /api/games/{game_id}/level/start`
**Descripción**: Registrar inicio de un nivel
**Request Body**:
```json
{
  "level": "string (hub_central|senda_ebano|fortaleza_gigantes|aquelarre_sombras|claro_almas)"
}
```
**Response**: `200 OK`

#### `POST /api/games/{game_id}/level/complete`
**Descripción**: Registrar completado de un nivel
**Request Body**:
```json
{
  "level": "string",
  "time_seconds": "integer",
  "deaths": "integer",
  "choice": "string | null",
  "relic": "string | null"
}
```
**Response**: `200 OK`

---

### 3.3. Registro de Eventos

#### `POST /api/events`
**Descripción**: Registrar un evento de juego
**Request Body**:
```json
{
  "game_id": "uuid",
  "event_type": "string",
  "level": "string",
  "data": { ... }
}
```
**Response**: `201 Created`

**Event Types completos**:
- `level_start` - Inicio de nivel
- `level_complete` - Nivel completado
- `player_death` - Muerte del jugador
- `choice_made` - Elección moral tomada
- `relic_obtained` - Reliquia conseguida
- `boss_defeated` - Boss final derrotado
- `boss_phase_change` - Cambio de fase del boss
- `npc_interaction` - Interacción con NPC
- `dialog_triggered` - Diálogo activado
- `dash_used` - Habilidad dash utilizada
- `pause_game` - Juego pausado
- `resume_game` - Juego reanudado
- `checkpoint_reached` - Punto de control alcanzado

#### `POST /api/events/batch`
**Descripción**: Registrar múltiples eventos en batch (para sincronización offline)
**Request Body**:
```json
{
  "events": [
    { "game_id": "uuid", "event_type": "string", ... },
    ...
  ]
}
```

---

### 3.4. Consultas y Rankings

#### `GET /api/leaderboards/{category}`
**Descripción**: Obtener ranking por categoría
**Query Params**:
- `limit`: integer (default 100)
- `offset`: integer (default 0)

**Categories**:
- `speedrun` - Tiempo más rápido en completar el juego
- `moral_good` - Jugadores con mejor alineación moral
- `moral_evil` - Jugadores con peor alineación moral
- `completion_rate` - Mayor tasa de completado
- `perfectionist` - Sin muertes

**Response**: `200 OK`
```json
{
  "category": "string",
  "entries": [
    {
      "rank": "integer",
      "player_id": "uuid",
      "username": "string",
      "value": "number",
      "achieved_at": "timestamp"
    }
  ],
  "total": "integer"
}
```

#### `GET /api/analytics/levels/{level_name}`
**Descripción**: Obtener estadísticas agregadas de un nivel
**Response**: `200 OK`
```json
{
  "level_name": "string",
  "total_attempts": "integer",
  "completion_rate": "float",
  "average_time_seconds": "float",
  "average_deaths": "float",
  "moral_choices_distribution": {
    "good": "integer",
    "bad": "integer"
  },
  "death_heatmap": [ ... ]
}
```

#### `GET /api/analytics/moral-choices`
**Descripción**: Distribución global de elecciones morales
**Response**: `200 OK`

---

### 3.5. Sesiones

#### `POST /api/sessions`
**Descripción**: Iniciar una sesión de juego
**Request Body**:
```json
{
  "player_id": "uuid",
  "game_id": "uuid",
  "platform": "string (windows|mac|linux|web)",
  "game_version": "string"
}
```
**Response**: `201 Created`
```json
{
  "session_id": "uuid",
  "player_id": "uuid",
  "game_id": "uuid",
  "started_at": "timestamp"
}
```

#### `PATCH /api/sessions/{session_id}/end`
**Descripción**: Finalizar una sesión de juego
**Response**: `200 OK`
```json
{
  "session_id": "uuid",
  "duration_seconds": "integer",
  "ended_at": "timestamp"
}
```

---

## 4. MÉTRICAS A GUARDAR

### 4.1. Métricas por Nivel

Para cada nivel:

1. **Tiempo de completado** (segundos)
2. **Número de muertes**
3. **Elección moral tomada** (buena/mala/neutral)
4. **Intentos hasta completar**
5. **Posiciones de muerte** (x, y) para heatmap
6. **Interacciones con elementos del nivel**
7. **Uso de habilidades** (dashes, reliquias)
8. **Tiempo de primera visita vs revisitas**
9. **Rutas tomadas** (puntos de interés visitados)

### 4.2. Métricas Globales del Jugador

1. **Perfil moral**:
   - Porcentaje de elecciones buenas vs malas
   - Alineación moral (-1 a 1)
   - Consistencia en elecciones
   - Evolución moral a lo largo de partidas
2. **Rendimiento**:
   - Tiempo total de juego
   - Tasa de completado
   - Promedio de muertes por nivel
   - Mejor speedrun personal
   - Mejora entre partidas
3. **Progresión**:
   - Niveles completados
   - Reliquias obtenidas
   - Boss derrotado (sí/no)
   - Logros desbloqueados
4. **Engagement**:
   - Número de sesiones
   - Duración promedio de sesión
   - Días desde última partida
   - Tasa de abandono por nivel
   - Horarios de juego preferidos

### 4.3. Métricas del Boss Final

1. **Tiempo de supervivencia** (segundos)
2. **NPCs que ayudan** (basado en elecciones morales previas)
3. **Dificultad percibida** (según nivel de ayuda)
4. **Número de intentos hasta victoria**
5. **Fases alcanzadas**
6. **Patrones de esquiva** (para análisis de skill)
7. **Daño total recibido**

---

## 5. ESTRUCTURA DEL PROYECTO

```
backend/
│
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI + Flask integrados
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py         # Variables de entorno
│   │   └── firebase.py         # Inicialización Firebase
│   │
│   ├── models/                 # Modelos Pydantic
│   │   ├── __init__.py
│   │   ├── player.py
│   │   ├── game.py
│   │   ├── event.py
│   │   ├── session.py
│   │   └── leaderboard.py
│   │
│   ├── repositories/           # Acceso a Firebase (DAO)
│   │   ├── __init__.py
│   │   ├── base_repository.py
│   │   ├── player_repository.py
│   │   ├── game_repository.py
│   │   ├── event_repository.py
│   │   ├── session_repository.py
│   │   └── leaderboard_repository.py
│   │
│   ├── services/               # Lógica de negocio
│   │   ├── __init__.py
│   │   ├── player_service.py
│   │   ├── game_service.py
│   │   ├── event_service.py
│   │   ├── session_service.py
│   │   ├── analytics_service.py
│   │   ├── leaderboard_service.py
│   │   └── metrics_calculator.py
│   │
│   ├── api/                    # Endpoints FastAPI
│   │   ├── __init__.py
│   │   ├── dependencies.py     # Inyección de dependencias
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── players.py
│   │   │   ├── games.py
│   │   │   ├── events.py
│   │   │   ├── sessions.py
│   │   │   ├── leaderboards.py
│   │   │   └── analytics.py
│   │   └── middlewares/
│   │       ├── __init__.py
│   │       ├── error_handler.py
│   │       ├── logging_middleware.py
│   │       └── cors_middleware.py
│   │
│   ├── dashboard/              # Flask Dashboard
│   │   ├── __init__.py
│   │   ├── app.py
│   │   ├── routes.py
│   │   ├── charts/
│   │   │   ├── __init__.py
│   │   │   ├── player_charts.py
│   │   │   ├── level_charts.py
│   │   │   ├── moral_charts.py
│   │   │   └── performance_charts.py
│   │   ├── templates/
│   │   │   ├── base.html
│   │   │   ├── index.html
│   │   │   ├── players.html
│   │   │   ├── games.html
│   │   │   ├── analytics.html
│   │   │   └── leaderboards.html
│   │   └── static/
│   │       ├── css/
│   │       │   └── style.css
│   │       └── js/
│   │           └── dashboard.js
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── validators.py
│   │   ├── exceptions.py
│   │   └── logger.py
│   │
│   └── migrations/             # Alembic migrations (futuro)
│       ├── env.py
│       ├── script.py.mako
│       └── versions/
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_repositories/
│   ├── test_services/
│   └── test_api/
│
├── docs/
│   ├── api_documentation.md
│   └── database_schema.md
│
├── scripts/
│   ├── init_firestore.py
│   └── seed_data.py
│
├── requirements.txt
├── requirements-dev.txt
├── .env.example
├── .gitignore
├── alembic.ini
└── README.md
```

---

## 6. DEPENDENCIAS

### requirements.txt (Producción)
```txt
# API Framework
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
pydantic-settings==2.1.0

# Dashboard
flask==3.0.0
jinja2==3.1.3

# Firebase
firebase-admin==6.4.0

# Visualización
plotly==5.18.0
pandas==2.1.4
numpy==1.26.3

# ORM (opcional, para estructuración)
sqlalchemy==2.0.25

# Migraciones
alembic==1.13.1

# Validación y utilidades
python-dotenv==1.0.0
python-multipart==0.0.6
email-validator==2.1.0

# Logging
python-json-logger==2.0.7

# Cache (opcional)
redis==5.0.1

# CORS
fastapi-cors==0.0.6
```

### requirements-dev.txt (Desarrollo)
```txt
-r requirements.txt

# Testing
pytest==7.4.4
pytest-asyncio==0.23.3
pytest-cov==4.1.0
httpx==0.26.0

# Code quality
black==23.12.1
flake8==7.0.0
mypy==1.8.0
isort==5.13.2

# Development
ipython==8.19.0
```

---

## 7. VALIDACIONES

### 7.1. Validaciones de Entrada

**Players**:
- `username`: 3-20 caracteres, alfanumérico + guiones bajos
- `email`: formato email válido (opcional, validado con email-validator)

**Games**:
- `player_id`: debe existir en Firebase
- `status`: enum válido (in_progress, completed, abandoned)
- `choices`: valores permitidos por nivel

**Events**:
- `event_type`: debe estar en lista de tipos válidos
- `game_id`: debe existir y tener status `in_progress`
- `timestamp`: no puede ser futuro
- `data`: JSON válido según tipo de evento

**Sessions**:
- `platform`: enum válido
- `game_version`: formato semver (x.y.z)

### 7.2. Reglas de Negocio

1. **Un jugador solo puede tener una partida activa** (`status=in_progress`) a la vez
2. **No se pueden registrar eventos de partidas cerradas** (completed o abandoned)
3. **Las elecciones morales solo se pueden hacer una vez por nivel** en cada partida
4. **El boss final requiere las 3 reliquias** antes de poder ser enfrentado
5. **Las sesiones deben asociarse a una partida existente**
6. **No se pueden modificar eventos pasados** (immutabilidad)
7. **El moral_alignment se calcula automáticamente** desde las elecciones

---

## 8. GESTIÓN DE ERRORES

### 8.1. Códigos HTTP

- `200 OK`: Operación exitosa
- `201 Created`: Recurso creado
- `400 Bad Request`: Validación fallida
- `404 Not Found`: Recurso no existe
- `409 Conflict`: Conflicto de estado (ej: partida ya activa)
- `500 Internal Server Error`: Error del servidor

### 8.2. Formato de Errores

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Descripción del error",
    "details": {
      "field": "username",
      "issue": "Debe tener entre 3 y 20 caracteres"
    }
  }
}
```

---

## 9. LOGGING

### 9.1. Niveles de Log

- `DEBUG`: Información detallada para desarrollo
- `INFO`: Eventos importantes (partida iniciada, nivel completado)
- `WARNING`: Situaciones inusuales pero no errores
- `ERROR`: Errores que impiden operación
- `CRITICAL`: Fallos del sistema

### 9.2. Formato de Logs

```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "logger": "app.services.game_service",
  "message": "Level completed",
  "context": {
    "player_id": "uuid",
    "game_id": "uuid",
    "level": "senda_ebano",
    "time_seconds": 245
  }
}
```

---

## 10. DASHBOARD (Flask)

### 10.1. Páginas

1. **Home**: Resumen general
   - Jugadores activos hoy
   - Partidas en curso
   - Partidas completadas hoy
   - Gráfico de actividad (última semana)

2. **Players**: Gestión de jugadores
   - Lista paginada
   - Búsqueda por username
   - Filtros: por moral alignment, games played
   - Detalle de jugador individual

3. **Games**: Análisis de partidas
   - Lista de partidas (con filtros)
   - Estadísticas por nivel
   - Distribución de tiempos de completado
   - Tasa de abandono

4. **Analytics**: Métricas avanzadas
   - Heatmap de muertes por nivel
   - Distribución de elecciones morales
   - Funnel de progresión (hub → nivel1 → nivel2 → ...)
   - Comparativa de rendimiento entre niveles
   - Correlación moral alignment vs tiempo

### 10.2. Gráficos Plotly

**Tipos de gráficos**:
- Line charts: actividad a lo largo del tiempo
- Bar charts: distribución de elecciones morales
- Pie charts: porcentaje de completado
- Heatmaps: posiciones de muerte
- Scatter plots: tiempo vs muertes
- Funnel charts: progresión de niveles
- Box plots: distribución de tiempos por nivel

### 10.3. Filtros

Todos los dashboards deben permitir filtrar por:
- Rango de fechas
- Player ID específico
- Nivel
- Estado de partida (completed, abandoned, in_progress)
- Moral alignment

---

## 11. CONSIDERACIONES DE PERFORMANCE

1. **Indexación en Firestore**:
   - `players`: índice en `username`
   - `games`: índice compuesto en `player_id + status`
   - `game_events`: índice compuesto en `game_id + timestamp`

2. **Caché**:
   - Leaderboards: cachear 5 minutos
   - Analytics agregadas: cachear 1 hora
   - Player stats: cachear 30 segundos

3. **Batch operations**:
   - Endpoint `/events/batch` para envío masivo
   - Procesamiento asíncrono de cálculos pesados

4. **Paginación**:
   - Máximo 100 items por request
   - Usar cursor-based pagination para Firestore

---

## 12. SEGURIDAD

1. **API Keys**: Header `X-API-Key` para autenticación básica
2. **Rate Limiting**: 100 requests por minuto por IP
3. **CORS**: Configurar origins permitidos
4. **Validación**: Sanitizar todos los inputs
5. **Firestore Rules**: Reglas estrictas de acceso

---

## 13. DEPLOYMENT

### 13.1. Variables de Entorno (.env)

```env
# Firebase
FIREBASE_PROJECT_ID=tu-proyecto-id
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json

# API
API_HOST=0.0.0.0
API_PORT=8000
API_KEY=tu-api-key-secreta-aqui
API_TITLE=Game Backend API
API_VERSION=1.0.0

# Dashboard
DASHBOARD_SECRET_KEY=tu-secret-key-para-flask
DASHBOARD_DEBUG=True

# Environment
ENVIRONMENT=development
LOG_LEVEL=INFO
ENABLE_CORS=True
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080

# Cache (opcional)
REDIS_URL=redis://localhost:6379/0
CACHE_TTL_SECONDS=300

# Rate Limiting
RATE_LIMIT_ENABLED=True
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD=60

# Analytics
ENABLE_ANALYTICS=True
ANALYTICS_BATCH_SIZE=100
```

### 13.2. Integración API + Dashboard

Montar Flask dentro de FastAPI:

```python
# main.py
from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware
from app.dashboard.app import create_dashboard_app

app = FastAPI()

# ... routes de la API ...

# Montar dashboard en /dashboard
dashboard_app = create_dashboard_app()
app.mount("/dashboard", WSGIMiddleware(dashboard_app))
```

---

## 14. PRÓXIMOS PASOS

1. **Fase 1**: Setup del proyecto
   - Configurar estructura de carpetas
   - Inicializar Firebase
   - Crear modelos Pydantic

2. **Fase 2**: Capa de datos
   - Implementar repositories
   - Testear conexión con Firestore

3. **Fase 3**: Lógica de negocio
   - Implementar services
   - Crear calculadores de métricas

4. **Fase 4**: API REST
   - Implementar endpoints
   - Validaciones y error handling
   - Testing

5. **Fase 5**: Dashboard
   - Crear templates
   - Implementar gráficos Plotly
   - Integrar con API

6. **Fase 6**: Testing y deployment
   - Tests unitarios y de integración
   - Documentación
   - Deploy

---

## 15. EJEMPLOS DE FLUJOS

### 15.1. Flujo de una Partida Completa

```
1. POST /api/players                    → Crear jugador
2. POST /api/games                      → Iniciar partida
3. POST /api/sessions                   → Iniciar sesión
4. POST /api/games/{id}/level/start     → Empezar Hub Central
5. POST /api/events                     → Ver diario
6. POST /api/events                     → Ver mapa
7. POST /api/games/{id}/level/start     → Empezar Senda del Ébano
8. POST /api/events                     → Muerte del jugador
9. POST /api/events                     → Elección moral (sanar)
10. POST /api/events                    → Reliquia obtenida (lirio)
11. POST /api/games/{id}/level/complete → Completar Senda del Ébano
12. ... repetir para Fortaleza y Aquelarre ...
13. POST /api/games/{id}/level/start    → Empezar Claro de las Almas
14. POST /api/events                    → Boss fase 1
15. POST /api/events                    → Boss fase 2
16. POST /api/events                    → Boss derrotado
17. POST /api/games/{id}/level/complete → Completar boss
18. PATCH /api/games/{id}               → Marcar partida completed
19. PATCH /api/sessions/{id}/end        → Finalizar sesión
```

### 15.2. Consulta del Dashboard

```
1. GET /dashboard/analytics/levels/senda_ebano
2. Servicio obtiene datos de Firestore
3. Pandas procesa y agrega datos
4. Plotly genera gráficos
5. Flask renderiza template con gráficos
```

---

## 16. MÉTRICAS ESPECÍFICAS POR NIVEL

### Hub Central
- Tiempo total de permanencia
- Número de visitas al diario
- Número de visitas al mapa
- Tiempo hasta elegir primera misión
- Frecuencia de retornos entre niveles

### Senda del Ébano
- Elección moral (Forzar vs Sanar)
- Tiempo hasta encontrar los fantasmas
- Muertes por agua profunda
- Rutas tomadas (superior vs inferior)
- Uso del Lirio (número de veces)
- Tiempo de resolución del dilema

### Fortaleza de los Gigantes
- Elección moral (Destruir vs Construir)
- Tiempo de resolución del puzzle
- Daño recibido por gigantes
- Uso del Hacha
- Intentos en el puzzle de la columna
- Zonas más transitadas

### Aquelarre de Sombras
- Elección moral (Ocultar vs Revelar)
- Número de detecciones por sombras
- Tiempo total en modo invisible
- Uso del Manto
- Patrones de movimiento (sigilo vs directo)
- Cristales iluminados

### Claro de las Almas
- Tiempo de supervivencia total
- Proyectiles esquivados vs recibidos
- NPCs que aparecen (según elecciones previas)
- Fases del boss alcanzadas
- Intentos hasta victoria
- Patrones de movimiento durante esquiva
- Daño total recibido por fase
