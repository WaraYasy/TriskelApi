# Triskel API

API REST y Dashboard de Administracion para el videojuego **Triskel: La Balada del Ultimo Guardian**.

Desarrollado por **Mandragora** | Enero 2026

---

## Stack Tecnologico

| Componente | Tecnologia | Version |
|------------|------------|---------|
| API Framework | FastAPI | 0.109.0 |
| Dashboard Web | Flask | 3.0.0 |
| Base de Datos NoSQL | Firebase Firestore | 6.4.0 |
| Base de Datos SQL | PostgreSQL + SQLAlchemy | 2.0.25 |
| Migraciones | Alembic | 1.13.1 |
| Autenticacion | JWT (python-jose) | 3.3.0 |
| Visualizaciones | Plotly | 5.18.0 |
| Server | Uvicorn / Gunicorn | 0.27.0 / 21.2.0 |

---

## Instalacion

### Requisitos
- Python 3.10+
- PostgreSQL (opcional, para autenticacion admin)
- Cuenta de Firebase con Firestore habilitado

### Configuracion

```bash
# Clonar repositorio
git clone <repo-url>
cd Triskel-API

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales
```

### Variables de Entorno

```bash
# Seguridad (obligatorias)
SECRET_KEY=tu_clave_secreta
API_KEY=tu_api_key
JWT_SECRET_KEY=tu_jwt_secret

# Firebase
FIREBASE_CREDENTIALS_PATH=config/firebase-credentials.json
# O en produccion:
# FIREBASE_CREDENTIALS_BASE64=<credenciales_en_base64>

# PostgreSQL (para autenticacion admin)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=triskel
DB_USER=postgres
DB_PASSWORD=password
```

### Ejecucion

```bash
# Desarrollo (con hot-reload)
make dev
# o: uvicorn app.main:app --reload

# Produccion
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

---

## Arquitectura

```
Triskel-API/
├── app/
│   ├── main.py                 # Punto de entrada
│   ├── api/                    # Routers FastAPI
│   ├── config/                 # Configuracion
│   ├── core/                   # Servicios compartidos
│   ├── domain/                 # Dominios de negocio
│   │   ├── players/            # Jugadores
│   │   ├── games/              # Partidas
│   │   ├── events/             # Eventos del juego
│   │   ├── auth/               # Autenticacion admin
│   │   └── web/                # Dashboard Flask
│   ├── infrastructure/         # Adapters (BD, APIs)
│   └── middleware/             # Auth, Security
├── alembic/                    # Migraciones SQL
├── config/                     # Credenciales
├── docs/                       # Documentacion
└── tests/                      # Tests
```

---

## Endpoints

### API REST (FastAPI)

**Base URL:** `/v1`

| Recurso | Endpoints |
|---------|-----------|
| Players | `POST /players`, `GET /players/me`, `GET /players/{id}`, `PATCH /players/{id}` |
| Games | `POST /games`, `GET /games/{id}`, `POST /games/{id}/level/start`, `POST /games/{id}/level/complete` |
| Events | `POST /events`, `POST /events/batch`, `GET /events/game/{game_id}` |
| Auth | `POST /auth/login`, `POST /auth/refresh`, `GET /auth/me` |

**Documentacion interactiva:** `/docs` (Swagger UI)

### Dashboard Web (Flask)

**Base URL:** `/web`

| Ruta | Descripcion |
|------|-------------|
| `/web/` | Landing page |
| `/web/dashboard` | Dashboard principal |
| `/web/dashboard/players` | Analisis de jugadores |
| `/web/dashboard/games` | Analisis de partidas |
| `/web/dashboard/choices` | Decisiones morales |
| `/web/dashboard/events` | Eventos del sistema |
| `/web/dashboard/advanced` | Metricas avanzadas |
| `/web/admin/login` | Login administrador |
| `/web/admin/export` | Exportar datos CSV |
| `/web/admin/migrations` | Gestionar migraciones BD |

---

## Autenticacion

### 1. Player Token (Jugadores)
```http
X-Player-ID: <player_id>
X-Player-Token: <player_token>
```

### 2. JWT Bearer (Administradores)
```http
Authorization: Bearer <jwt_token>
```

### 3. API Key (Scripts/Automatizacion)
```http
X-API-Key: <api_key>
```

---

## Migraciones (Alembic)

El sistema usa Alembic para gestionar el esquema de la base de datos SQL.

### Comandos CLI

```bash
# Ver estado actual
alembic current

# Ver historial
alembic history

# Aplicar migraciones pendientes
alembic upgrade head

# Revertir ultima migracion
alembic downgrade -1

# Crear nueva migracion
alembic revision --autogenerate -m "descripcion"
```

### Dashboard Web

Accede a `/web/admin/migrations` para gestionar migraciones visualmente:
- Ver estado de la base de datos
- Historial de migraciones aplicadas/pendientes
- Ejecutar upgrade/downgrade con confirmacion

---

## Testing

```bash
# Ejecutar todos los tests
pytest

# Con cobertura
pytest --cov=app --cov-report=html

# Tests especificos
pytest tests/unit/
pytest tests/integration/
```

---

## Despliegue

### Railway

1. Conectar repositorio en Railway Dashboard
2. Configurar variables de entorno:
   - `SECRET_KEY`, `API_KEY`, `JWT_SECRET_KEY`
   - `FIREBASE_CREDENTIALS_BASE64`
   - Variables de PostgreSQL (si usas addon de Railway)
3. Railway despliega automaticamente en cada push

### Docker

```bash
docker build -t triskel-api .
docker run -p 8000:8000 --env-file .env triskel-api
```

---

## Documentacion Adicional

| Documento | Descripcion |
|-----------|-------------|
| [docs/API.md](docs/API.md) | Referencia completa de endpoints |
| [docs/UNITY_INTEGRATION.md](docs/UNITY_INTEGRATION.md) | Integracion con Unity |
| [docs/RAILWAY_DEPLOYMENT.md](docs/RAILWAY_DEPLOYMENT.md) | Guia de despliegue |
| [docs/SECURITY_KEYS.md](docs/SECURITY_KEYS.md) | Gestion de claves |
| [CLAUDE.md](CLAUDE.md) | Guia para desarrollo con IA |

---

## Estado del Proyecto

### Implementado
- Arquitectura hexagonal (Ports & Adapters)
- Dominio Players (CRUD completo)
- Dominio Games (gestion de partidas)
- Dominio Events (tracking de eventos)
- Sistema de autenticacion JWT
- Dashboard web con visualizaciones
- Exportacion de datos (CSV)
- Sistema de migraciones (Alembic)
- Audit logs

### Pendiente
- Dominio Sessions
- Leaderboards en tiempo real
- Tests automatizados completos

---

## Equipo Mandragora

| Rol | Responsabilidad |
|-----|-----------------|
| Backend Lead | Arquitectura API y Base de Datos |
| Frontend Lead | Dashboard Web y Visualizaciones |
| DevOps | Despliegue e Infraestructura |
| QA Lead | Testing y Calidad |

---

## Licencia

Propiedad de Mandragora. Todos los derechos reservados.
