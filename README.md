# Triskel API

API REST y Dashboard Web para el videojuego **Triskel: La Balada del Ultimo Guardian**.

Desarrollado por **Mandragora** para Colegio Hogwarts de Magia y Hechiceria.

## Guias Rapidas

- [Desplegar en Railway](docs/RAILWAY_DEPLOYMENT.md) - Guia completa de despliegue en produccion
- [Integrar con Unity](docs/UNITY_INTEGRATION.md) - Conecta tu juego Unity con la API
- [Claves de Seguridad](docs/SECURITY_KEYS.md) - Diferencia entre SECRET_KEY y API_KEY
- [Documentacion de API](docs/API.md) - Listado completo de endpoints
- [Coleccion Postman](docs/Triskel-API.postman_collection.json) - Importar en Postman

---

## Arquitectura

- **FastAPI** - API REST para el juego (Unity/Godot)
- **Flask** - Dashboard web para analytics
- **Firebase Firestore** - Base de datos NoSQL
- **MySQL** - Base de datos SQL (autenticacion admin)
- **Arquitectura Hexagonal** - Ports & Adapters para desacoplamiento

---

## Instalacion

### 1. Clonar el Repositorio
```bash
git clone <repo-url>
cd Triskel-API
```

### 2. Crear Entorno Virtual (Recomendado)
```bash
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar Firebase
Coloca tu archivo de credenciales en:
```
config/firebase-credentials.json
```

### 5. Variables de Entorno

Copia `.env.example` a `.env`:
```bash
cp .env.example .env
```

Variables **obligatorias**:
```bash
# Seguridad
SECRET_KEY=tu_clave_secreta_para_sesiones_flask
API_KEY=tu_clave_api_para_administracion
JWT_SECRET_KEY=tu_clave_secreta_para_jwt

# JWT
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Password
BCRYPT_ROUNDS=12
```

---

## Ejecutar

### Modo Desarrollo
```bash
python3 -m uvicorn app.main:app --reload
```

### Modo Produccion
```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

---

## Endpoints Principales

### API REST (FastAPI)

| Ruta | Descripcion |
|------|-------------|
| `GET /` | Informacion de la API |
| `GET /docs` | Documentacion Swagger |
| `GET /health` | Health check |

#### Players
| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| POST | `/v1/players` | Crear jugador |
| GET | `/v1/players/me` | Mi perfil |
| GET | `/v1/players/{id}` | Obtener jugador |
| GET | `/v1/players` | Listar jugadores (admin) |
| PATCH | `/v1/players/{id}` | Actualizar jugador |
| DELETE | `/v1/players/{id}` | Eliminar jugador |

#### Games
| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| POST | `/v1/games` | Crear partida |
| GET | `/v1/games/{id}` | Obtener partida |
| GET | `/v1/games/player/{player_id}` | Partidas de un jugador |
| POST | `/v1/games/{id}/level/start` | Iniciar nivel |
| POST | `/v1/games/{id}/level/complete` | Completar nivel |
| PATCH | `/v1/games/{id}` | Actualizar partida |
| DELETE | `/v1/games/{id}` | Eliminar partida |

#### Events
| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| POST | `/v1/events` | Crear evento |
| POST | `/v1/events/batch` | Crear eventos en lote |
| GET | `/v1/events/game/{game_id}` | Eventos de una partida |
| GET | `/v1/events/player/{player_id}` | Eventos de un jugador |
| GET | `/v1/events/game/{game_id}/type/{type}` | Eventos por tipo |

#### Auth (Administradores)
| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| POST | `/v1/auth/login` | Login administrador |
| POST | `/v1/auth/refresh` | Refrescar token |
| POST | `/v1/auth/logout` | Cerrar sesion |
| GET | `/v1/auth/me` | Mi perfil admin |
| POST | `/v1/auth/change-password` | Cambiar contrasena |
| POST | `/v1/auth/admin/users` | Crear admin |
| GET | `/v1/auth/admin/users` | Listar admins |
| GET | `/v1/auth/admin/users/{id}` | Obtener admin |
| PATCH | `/v1/auth/admin/users/{id}` | Actualizar admin |
| GET | `/v1/auth/admin/audit` | Logs de auditoria |

### Dashboard Web (Flask)

| Ruta | Descripcion |
|------|-------------|
| `/web/` | Landing page |
| `/web/dashboard/` | Dashboard principal |
| `/web/dashboard/players` | Analisis de jugadores |
| `/web/dashboard/games` | Analisis de partidas |
| `/web/dashboard/choices` | Decisiones morales |
| `/web/dashboard/events` | Analisis de eventos |
| `/web/dashboard/advanced` | Dashboard avanzado |
| `/web/dashboard/export` | Exportar datos |
| `/web/admin/login` | Login administrador |
| `/web/admin/dashboard` | Panel de administracion |
| `/web/admin/export` | Exportar datos (admin) |
| `/web/admin/migrations` | Migraciones |

---

## Autenticacion

### 1. Player Token (Jugadores)
```
X-Player-ID: <player_id>
X-Player-Token: <player_token>
```

### 2. JWT Bearer (Administradores)
```
Authorization: Bearer <jwt_token>
```

### 3. API Key (Administracion programatica)
```
X-API-Key: <api_key>
```

---

## Estructura del Proyecto

```
app/
├── domain/                    # Dominios verticales
│   ├── players/              # Jugadores
│   ├── games/                # Partidas
│   ├── events/               # Eventos
│   ├── sessions/             # Sesiones
│   ├── auth/                 # Autenticacion
│   └── web/                  # Dashboard Flask
├── infrastructure/           # Capa de infraestructura
│   └── database/
├── middleware/               # Middlewares
│   ├── auth.py
│   └── security.py
├── core/                     # Servicios compartidos
└── main.py                   # Aplicacion principal
```

---

## Stack Tecnologico

| Componente | Tecnologia | Version |
|------------|------------|---------|
| API Framework | FastAPI | 0.109.0 |
| Web Framework | Flask | 3.0.0 |
| Server | Uvicorn | 0.27.0 |
| Base de Datos | Firebase Firestore | 6.4.0 |
| Visualizaciones | Plotly | 5.18.0 |
| Datos | Pandas | 2.1.4 |
| HTTP Client | httpx | 0.25.2 |
| Production Server | Gunicorn | 21.2.0 |

---

## Documentacion

- [Documentacion de API](docs/API.md) - Listado completo de endpoints con ejemplos
- [Coleccion Postman](docs/Triskel-API.postman_collection.json) - Importar en Postman
- [Railway Deployment](docs/RAILWAY_DEPLOYMENT.md) - Desplegar en produccion
- [Unity Integration](docs/UNITY_INTEGRATION.md) - Integrar con Unity

---

## Estado del Proyecto

### Implementado
- Arquitectura hexagonal
- Dominio Players (completo)
- Dominio Games (completo)
- Dominio Events (completo)
- Sistema de autenticacion JWT
- Dashboard web con Analytics
- Exportacion de datos (CSV/JSON)
- Audit logs
- Logging estructurado
- Documentacion Swagger

### Por Implementar
- Dominio Sessions
- Leaderboards
- Tests automatizados

---

## Equipo

- **Empresa**: Mandragora
- **Cliente**: Colegio Hogwarts de Magia y Hechiceria
- **Videojuego**: Triskel: La Balada del Ultimo Guardian
- **Fecha**: Enero 2026

---

## Licencia

Propiedad de Mandragora. Todos los derechos reservados.
