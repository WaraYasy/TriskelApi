<div align="center">
  <img src="app/domain/web/static/img/triskel_logo.png" alt="Triskel Logo" width="600"/>

  # Triskel API

  ### API REST y Dashboard de Administración para el videojuego
  **La Balada del Último Guardián**

  <p align="center">
    <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python 3.10+"/>
    <img src="https://img.shields.io/badge/FastAPI-0.109.0-009688.svg" alt="FastAPI"/>
    <img src="https://img.shields.io/badge/Flask-3.0.0-000000.svg" alt="Flask"/>
    <img src="https://img.shields.io/badge/Firebase-Firestore-FFCA28.svg" alt="Firebase"/>
    <img src="https://img.shields.io/badge/PostgreSQL-13+-336791.svg" alt="PostgreSQL"/>
    <img src="https://img.shields.io/badge/License-Proprietary-red.svg" alt="License"/>
  </p>

  <p align="center">
    <strong>Desarrollado por Mandrágora | Enero 2026</strong>
  </p>
</div>

---

## 📑 Tabla de Contenidos

- [Características](#-características)
- [Arquitectura](#-arquitectura)
- [Stack Tecnológico](#-stack-tecnológico)
- [Instalación](#-instalación)
- [Configuración](#-configuración)
- [Endpoints](#-endpoints)
- [Autenticación](#-autenticación)
- [Dashboard Web](#-dashboard-web)
- [Cache y Actualización de Datos](#-cache-y-actualización-de-datos)
- [Migraciones](#-migraciones)
- [Despliegue](#-despliegue)
- [Testing](#-testing)
- [Documentación](#-documentación)
- [Equipo](#-equipo)

---

## ✨ Características

- **🚀 API REST de Alto Rendimiento**: FastAPI con validación automática y documentación interactiva
- **📊 Dashboard de Analytics**: Visualizaciones en tiempo real con Plotly
- **⚡ Cache Inteligente con Redis**: Métricas cacheadas para respuestas ultra-rápidas
- **🔐 Autenticación Multi-Nivel**: JWT, API Keys y tokens de jugador
- **💾 Base de Datos Híbrida**: Firestore para datos del juego + PostgreSQL para administración
- **📈 Telemetría Avanzada**: Sistema completo de tracking de eventos
- **🎮 Integración Unity**: SDK simplificado para el cliente del juego
- **🔄 Sistema de Migraciones**: Gestión visual de esquemas de base de datos
- **📦 Exportación de Datos**: Descarga de datasets en CSV/JSON (Firestore) o CSV+JSON (SQL)
- **🎨 Tema Claro/Oscuro**: Dashboard adaptable con diseño moderno

---

## 🏗️ Arquitectura

El proyecto sigue una **arquitectura hexagonal** (Ports & Adapters) que separa la lógica de negocio de la infraestructura.

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENTE (Unity)                          │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FASTAPI (API Gateway)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  /v1/players │  │   /v1/games  │  │  /v1/events  │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└─────────┼──────────────────┼──────────────────┼─────────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CAPA DE DOMINIO (Lógica)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Players    │  │    Games     │  │    Events    │          │
│  │   Domain     │  │   Domain     │  │   Domain     │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└─────────┼──────────────────┼──────────────────┼─────────────────┘
          │                  │                  │
          └──────────────────┴──────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│               CAPA DE INFRAESTRUCTURA (Adapters)                 │
│  ┌─────────────────┐  ┌──────────────┐  ┌─────────────────┐    │
│  │    Firebase     │  │  PostgreSQL  │  │     Redis       │    │
│  │   Firestore     │  │     (SQL)    │  │    (Cache)      │    │
│  │ (Datos Juego)   │  │   (Auth)     │  │  (Métricas)     │    │
│  └─────────────────┘  └──────────────┘  └─────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FLASK (Dashboard Web)                         │
│  /web/            /web/analytics/         /web/admin/            │
│  Landing Page     Estadísticas            Panel Admin            │
└─────────────────────────────────────────────────────────────────┘
```

### Estructura del Proyecto

```
Triskel-API/
├── app/
│   ├── main.py                      # Punto de entrada FastAPI
│   ├── config/
│   │   └── settings.py              # Configuración (Pydantic)
│   ├── core/                        # Servicios compartidos
│   │   ├── logger.py
│   │   ├── exceptions.py
│   │   └── validators.py
│   ├── domain/                      # Dominios de negocio
│   │   ├── players/
│   │   │   ├── models.py
│   │   │   ├── service.py
│   │   │   ├── repository.py
│   │   │   └── routes.py
│   │   ├── games/
│   │   │   ├── models.py
│   │   │   ├── service.py
│   │   │   └── routes.py
│   │   ├── events/
│   │   │   ├── models.py
│   │   │   ├── service.py
│   │   │   └── routes.py
│   │   ├── auth/
│   │   │   ├── models.py            # SQLAlchemy models
│   │   │   ├── service.py
│   │   │   └── routes.py
│   │   └── web/                     # Dashboard Flask
│   │       ├── app.py               # Aplicación Flask
│   │       ├── analytics/           # Analytics endpoints
│   │       │   ├── routes.py
│   │       │   └── service.py
│   │       ├── static/              # CSS, JS, imágenes
│   │       └── templates/           # HTML templates
│   ├── infrastructure/
│   │   └── database/
│   │       ├── firebase_client.py   # Cliente Firestore
│   │       └── sql_client.py        # SQLAlchemy engine
│   └── middleware/
│       └── auth.py                  # Middleware de autenticación
├── alembic/                         # Migraciones SQL
│   └── versions/
├── config/                          # Credenciales
│   └── firebase-credentials.json
├── docs/                            # Documentación adicional
├── tests/                           # Tests unitarios e integración
└── requirements.txt
```

---

## 🛠️ Stack Tecnológico

| Componente | Tecnología | Versión | Propósito |
|------------|------------|---------|-----------|
| **API Framework** | FastAPI | 0.109.0 | API REST de alto rendimiento |
| **Web Framework** | Flask | 3.0.0 | Dashboard de administración |
| **Base de Datos NoSQL** | Firebase Firestore | 6.4.0 | Datos del juego (players, games, events) |
| **Base de Datos SQL** | PostgreSQL | 13+ | Autenticación de administradores |
| **ORM** | SQLAlchemy | 2.0.25 | Mapeo objeto-relacional |
| **Migraciones** | Alembic | 1.13.1 | Control de versiones de BD |
| **Autenticación** | python-jose | 3.3.0 | JWT tokens |
| **Hashing** | passlib (bcrypt) | 1.7.4 | Hash de contraseñas |
| **Validación** | Pydantic | 2.5.0 | Validación de datos |
| **Visualizaciones** | Plotly | 5.18.0 | Gráficos interactivos |
| **Cache** | Redis | 7.0+ | Cache de métricas y sesiones |
| **ASGI Server** | Uvicorn | 0.27.0 | Servidor de desarrollo |
| **WSGI Server** | Gunicorn | 21.2.0 | Servidor de producción |

---

## 🚀 Instalación

### Requisitos Previos

- Python 3.10 o superior
- PostgreSQL 13+ (opcional, para autenticación admin)
- Redis 7.0+ (opcional, para cache de analytics)
- Cuenta de Firebase con Firestore habilitado
- Git

### Pasos de Instalación

```bash
# 1. Clonar el repositorio
git clone <tu-repo-url>
cd Triskel-API

# 2. Crear entorno virtual
python3 -m venv venv

# 3. Activar entorno virtual
# Linux/macOS:
source venv/bin/activate
# Windows:
# venv\Scripts\activate

# 4. Instalar dependencias
pip install -r requirements.txt

# 5. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales

# 6. (Opcional) Ejecutar migraciones de PostgreSQL
alembic upgrade head

# 7. Iniciar el servidor
uvicorn app.main:app --reload
```

El servidor estará disponible en:
- **API REST**: http://localhost:8000
- **Documentación Swagger**: http://localhost:8000/docs
- **Dashboard Web**: http://localhost:8000/web/

---

## ⚙️ Configuración

### Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto:

```bash
# ===== SEGURIDAD (OBLIGATORIO) =====
SECRET_KEY=tu_clave_secreta_muy_segura_aqui
API_KEY=api_key_para_unity_y_scripts
JWT_SECRET_KEY=jwt_secret_diferente_del_secret_key

# ===== FIREBASE (OBLIGATORIO) =====
# Opción 1: Ruta local (desarrollo)
FIREBASE_CREDENTIALS_PATH=config/firebase-credentials.json

# Opción 2: Base64 (producción/Railway)
# FIREBASE_CREDENTIALS_BASE64=<tu_json_de_credenciales_en_base64>

# ===== POSTGRESQL (Opcional - Solo para auth admin) =====
DB_HOST=localhost
DB_PORT=5432
DB_NAME=triskel_db
DB_USER=postgres
DB_PASSWORD=tu_password_de_postgres

# ===== REDIS (Opcional - Cache de analytics) =====
# Desarrollo local
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=  # Dejar vacío para desarrollo local
REDIS_DB=0

# Producción (Railway auto-inyecta REDIS_URL si agregas addon)
# REDIS_URL=redis://default:password@host:port

# ===== CONFIGURACIÓN ADICIONAL =====
# Entorno (development/production)
ENVIRONMENT=development

# URL base de la API (auto-detectada en Railway)
# API_BASE_URL=https://tu-dominio.railway.app
```

### Obtener Credenciales de Firebase

1. Ve a [Firebase Console](https://console.firebase.google.com/)
2. Selecciona tu proyecto
3. Ve a **Configuración del Proyecto** (⚙️) → **Cuentas de servicio**
4. Click en **Generar nueva clave privada**
5. Guarda el JSON descargado en `config/firebase-credentials.json`

Para producción (Railway), convierte el JSON a Base64:

```bash
# Linux/macOS
base64 -w 0 config/firebase-credentials.json

# Windows (PowerShell)
[Convert]::ToBase64String([IO.File]::ReadAllBytes("config\firebase-credentials.json"))
```

---

## 📡 Endpoints

### API REST (FastAPI)

**Base URL**: `/api/v1`

#### 🎮 Players

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| `POST` | `/players` | Crear nuevo jugador | API Key |
| `GET` | `/players/me` | Obtener jugador actual | Player Token |
| `GET` | `/players/{id}` | Obtener jugador por ID | API Key |
| `PATCH` | `/players/{id}` | Actualizar jugador | Player Token |

#### 🎲 Games

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| `POST` | `/games` | Crear nueva partida | Player Token |
| `GET` | `/games/{id}` | Obtener partida | Player Token |
| `POST` | `/games/{id}/level/start` | Iniciar nivel | Player Token |
| `POST` | `/games/{id}/level/complete` | Completar nivel | Player Token |
| `POST` | `/games/{id}/choice` | Registrar decisión moral | Player Token |
| `POST` | `/games/{id}/death` | Registrar muerte | Player Token |
| `POST` | `/games/{id}/relic` | Recoger reliquia | Player Token |
| `POST` | `/games/{id}/end` | Finalizar partida | Player Token |

#### 📊 Events

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| `POST` | `/events` | Crear evento único | Player Token |
| `POST` | `/events/batch` | Crear eventos en lote | Player Token |
| `GET` | `/events/game/{game_id}` | Obtener eventos de partida | API Key |

#### 🔐 Auth

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| `POST` | `/auth/login` | Login administrador | None |
| `POST` | `/auth/refresh` | Refrescar JWT token | JWT |
| `GET` | `/auth/me` | Información del admin actual | JWT |

**Documentación Interactiva**: http://localhost:8000/docs

---

## 🔐 Autenticación

El sistema soporta **3 tipos de autenticación**:

### 1. 🎮 Player Token (Jugadores)

Para endpoints de jugadores y partidas:

```http
X-Player-ID: player_12345
X-Player-Token: abc123token
```

**Obtención**: Se genera automáticamente al crear un jugador con `POST /v1/players`

### 2. 🛡️ JWT Bearer (Administradores)

Para endpoints administrativos:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Obtención**: Login en `/v1/auth/login` o `/web/admin/login`

### 3. 🔑 API Key (Automatización)

Para scripts y herramientas:

```http
X-API-Key: tu_api_key_aqui
```

**Configuración**: Define `API_KEY` en `.env`

---

## 🎨 Dashboard Web

**Base URL**: `/web`

El dashboard proporciona visualizaciones en tiempo real y herramientas de administración.

### Páginas Disponibles

| Ruta | Descripción | Acceso |
|------|-------------|--------|
| `/web/` | Landing page con métricas destacadas | Público |
| `/web/analytics/` | Dashboard principal con estadísticas globales | Público |
| `/web/analytics/players` | Análisis detallado de jugadores | Público |
| `/web/analytics/games` | Análisis de partidas y progresión | Público |
| `/web/analytics/choices` | Distribución de decisiones morales | Público |
| `/web/analytics/events` | Timeline de eventos del sistema | Público |
| `/web/analytics/advanced` | Métricas avanzadas y KPIs | Público |
| `/web/admin/login` | Login de administrador | Público |
| `/web/admin/export` | Exportar datos a CSV/JSON | Admin |
| `/web/admin/migrations` | Gestión de migraciones de BD | Admin |

### Características del Dashboard

- ✨ **Tema Claro/Oscuro**: Switch automático según preferencia del sistema
- 📊 **Gráficos Interactivos**: Plotly con zoom, pan y tooltips
- 📈 **Métricas en Tiempo Real**: Actualización automática cada 30 segundos
- 📥 **Exportación Flexible**: Descarga de datos en CSV o JSON
- 🎮 **Análisis de Gameplay**: Muertes, reliquias, decisiones morales, progresión
- 👥 **Perfiles de Jugador**: Estadísticas individuales y alineación moral

---

## 🔄 Cache y Actualización de Datos

### Sistema de Cache con Redis

El dashboard utiliza **Redis** para cachear métricas y reducir la carga en las bases de datos.

#### Configuración de Redis

**Desarrollo Local:**
```bash
# Instalar Redis
# macOS:
brew install redis
brew services start redis

# Ubuntu/Debian:
sudo apt install redis-server
sudo systemctl start redis

# Windows:
# Descargar desde https://github.com/microsoftarchive/redis/releases
```

**Variables de Entorno:**
```bash
# Redis (Opcional - usa cache local si no está disponible)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=  # Dejar vacío para desarrollo local
REDIS_DB=0

# Railway automáticamente inyecta REDIS_URL si agregas Redis addon
# REDIS_URL=redis://default:password@host:port
```

**Producción (Railway):**
1. En tu proyecto de Railway, click en "New"
2. Selecciona "Database" → "Add Redis"
3. Railway automáticamente inyecta `REDIS_URL`
4. El sistema detecta y usa Redis automáticamente

### Actualización de Datos

#### Tiempo de Cache

| Tipo de Métrica | TTL (Time To Live) | Actualización |
|-----------------|-------------------|---------------|
| **Métricas Globales** | 5 minutos | Automática en background |
| **Estadísticas de Jugadores** | 10 minutos | On-demand (al acceder) |
| **Distribución de Decisiones** | 15 minutos | Automática |
| **Timeline de Eventos** | 30 segundos | Tiempo casi real |
| **Datos de Partidas** | 3 minutos | Automática |

#### Invalidación de Cache

El cache se invalida automáticamente cuando:
- ✅ Se completa una partida nueva
- ✅ Se registra una decisión moral
- ✅ Se crea un nuevo jugador
- ✅ Expira el TTL configurado

#### Actualización Manual

**Desde el Dashboard:**
- Cada página tiene un botón de "Actualizar" (🔄)
- Click para forzar recarga de datos (bypassing cache)

**Desde la API:**
```python
# Endpoint para invalidar cache (Admin)
DELETE /api/v1/cache/analytics
```

**Desde CLI (Redis):**
```bash
# Limpiar todo el cache de analytics
redis-cli FLUSHDB

# Limpiar claves específicas
redis-cli DEL analytics:global_metrics
redis-cli DEL analytics:player_stats
```

### Fallback sin Redis

Si Redis **no está disponible**:
- ✅ El sistema funciona normalmente
- ✅ Las métricas se calculan en tiempo real (sin cache)
- ⚠️ Mayor latencia en dashboard (2-5 segundos)
- ⚠️ Mayor carga en Firestore/PostgreSQL

El logger mostrará:
```
[WARN] Redis no disponible. Usando cálculo directo sin cache.
```

### Monitoreo de Cache

**Verificar estado de Redis:**
```bash
# Desde terminal
redis-cli ping
# Respuesta: PONG

# Ver estadísticas
redis-cli INFO stats

# Ver claves en uso
redis-cli KEYS analytics:*
```

**Desde Python:**
```python
from app.infrastructure.cache.redis_client import redis_client

# Verificar conexión
if redis_client.ping():
    print("✓ Redis conectado")
else:
    print("✗ Redis no disponible")
```

---

## 🔄 Migraciones

El sistema usa **Alembic** para gestionar cambios en el esquema de PostgreSQL.

### Comandos CLI

```bash
# Ver revisión actual
alembic current

# Ver historial de migraciones
alembic history --verbose

# Aplicar todas las migraciones pendientes
alembic upgrade head

# Revertir última migración
alembic downgrade -1

# Revertir a una revisión específica
alembic downgrade <revision_id>

# Crear nueva migración desde modelos
alembic revision --autogenerate -m "descripción del cambio"
```

### Gestión Visual (Dashboard)

Accede a **`/web/admin/migrations`** para:

- 🔍 Ver estado de conexión a la base de datos
- 📜 Historial completo de migraciones (aplicadas y pendientes)
- ⬆️ Aplicar migraciones con confirmación
- ⬇️ Revertir migraciones (rollback)
- ✅ Validación automática antes de ejecutar

> **Nota**: Crear migraciones es trabajo de desarrollo local. El dashboard de producción solo aplica/revierte migraciones existentes.

### Flujo de Trabajo Recomendado

```
[Desarrollo Local]
    ├─ Modificar modelos en app/domain/auth/models.py
    ├─ alembic revision --autogenerate -m "descripción"
    ├─ Revisar script generado en alembic/versions/
    ├─ Probar localmente: alembic upgrade head
    └─ Git commit + push

[Producción]
    └─ Dashboard muestra "X migraciones pendientes"
        └─ Click en "Aplicar Migraciones"
        └─ Base de datos actualizada ✓
```

---

## 🐳 Despliegue

### Railway (Recomendado)

Railway detecta automáticamente FastAPI y maneja el despliegue.

1. **Conectar Repositorio**:
   - Inicia sesión en [Railway](https://railway.app/)
   - Click en "New Project" → "Deploy from GitHub repo"
   - Selecciona el repositorio de Triskel-API

2. **Configurar Variables de Entorno**:
   ```
   SECRET_KEY=<genera con: openssl rand -hex 32>
   API_KEY=<clave para Unity>
   JWT_SECRET_KEY=<diferente al SECRET_KEY>
   FIREBASE_CREDENTIALS_BASE64=<credenciales de Firebase en base64>

   # PostgreSQL (Railway Addon automático)
   DATABASE_URL=${DATABASE_URL}  # Auto-inyectada por Railway
   ```

3. **Agregar Bases de Datos** (Opcional):

   **PostgreSQL** (para autenticación admin):
   - En tu proyecto de Railway, click en "New"
   - Selecciona "Database" → "Add PostgreSQL"
   - Railway automáticamente inyecta `DATABASE_URL`

   **Redis** (para cache de analytics):
   - En tu proyecto de Railway, click en "New"
   - Selecciona "Database" → "Add Redis"
   - Railway automáticamente inyecta `REDIS_URL`

4. **Deploy Automático**:
   - Railway detecta `requirements.txt` y `uvicorn`
   - Cada push a `main` despliega automáticamente
   - URL pública: `https://tu-proyecto.up.railway.app`

### Docker

```bash
# Build de la imagen
docker build -t triskel-api .

# Ejecutar contenedor
docker run -p 8000:8000 \
  --env-file .env \
  --name triskel-api \
  triskel-api

# O con Docker Compose
docker-compose up -d
```

### Manual (VPS)

```bash
# 1. Instalar dependencias del sistema
sudo apt update
sudo apt install python3.10 python3.10-venv postgresql

# 2. Clonar y configurar
git clone <repo-url> /var/www/triskel-api
cd /var/www/triskel-api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Configurar .env (ver sección de configuración)

# 4. Ejecutar con systemd
sudo cp triskel-api.service /etc/systemd/system/
sudo systemctl enable triskel-api
sudo systemctl start triskel-api

# 5. Configurar Nginx como proxy inverso
sudo nano /etc/nginx/sites-available/triskel-api
```

---

## 🧪 Testing

```bash
# Ejecutar todos los tests
pytest

# Con cobertura
pytest --cov=app --cov-report=html --cov-report=term

# Tests específicos
pytest tests/unit/
pytest tests/integration/

# Test de un módulo específico
pytest tests/unit/test_players.py

# Ver reporte de cobertura
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Estructura de Tests

```
tests/
├── unit/                  # Tests unitarios (lógica aislada)
│   ├── test_players.py
│   ├── test_games.py
│   └── test_events.py
├── integration/           # Tests de integración (BD, APIs)
│   ├── test_api.py
│   └── test_database.py
└── conftest.py            # Fixtures compartidos
```

---

## 📚 Documentación

| Documento | Descripción |
|-----------|-------------|
| [API.md](docs/API.md) | Referencia completa de endpoints con ejemplos |
| [UNITY_INTEGRATION.md](docs/UNITY_INTEGRATION.md) | Guía de integración con Unity |
| [RAILWAY_DEPLOYMENT.md](docs/RAILWAY_DEPLOYMENT.md) | Tutorial de despliegue en Railway |
| [SECURITY_KEYS.md](docs/SECURITY_KEYS.md) | Generación y gestión de claves |
| [CLAUDE.md](CLAUDE.md) | Instrucciones para Claude Code (desarrollo) |

---

## 📊 Estado del Proyecto

### ✅ Implementado

- ✓ Arquitectura hexagonal (Ports & Adapters)
- ✓ Dominio Players (CRUD completo + validaciones)
- ✓ Dominio Games (gestión de partidas, niveles, decisiones)
- ✓ Dominio Events (tracking completo + batch processing)
- ✓ Sistema de autenticación JWT multi-nivel
- ✓ Dashboard web con 7 páginas de analytics
- ✓ 15+ visualizaciones interactivas con Plotly
- ✓ Exportación de datos (CSV/JSON para Firestore, CSV+JSON para SQL)
- ✓ Sistema de migraciones con UI (Alembic)
- ✓ Tema claro/oscuro adaptable
- ✓ Audit logs y tracking de eventos
- ✓ Cache con Redis (fallback automático si no disponible)
- ✓ Exportación de admin users y audit logs

### 🚧 En Desarrollo

- ⏳ Dominio Sessions (sesiones de juego persistentes)
- ⏳ Leaderboards en tiempo real
- ⏳ Tests automatizados completos (>80% cobertura)
- ⏳ Webhooks para notificaciones

### 🔮 Roadmap Futuro

- 💡 Sistema de achievements/logros
- 💡 Replay system (reproducir partidas)
- 💡 A/B testing framework
- 💡 Análisis predictivo con ML
- 💡 API GraphQL alternativa

---


## 📄 Licencia

**Propiedad de Mandrágora. Todos los derechos reservados.**

Este proyecto es privado y confidencial. No se permite la reproducción, distribución o uso sin autorización explícita.

---

<div align="center">
  <p>
    <strong>✦ Hecho por Mandrágora ✦</strong>
  </p>
  <p>
    <a href="https://github.com/GaizkaDM">Gaizka</a> •
    <a href="https://github.com/UnaiZugaza">Unai</a> •
    <a href="https://github.com/WaraYasy">Wara</a>
  </p>
</div>
