# Triskel API

API REST para el videojuego Triskel/Mandrágora. Gestiona jugadores, partidas, eventos de telemetría y un dashboard de administración.

## Stack Tecnológico

- **API**: FastAPI 0.109.0 + Uvicorn
- **Dashboard**: Flask 3.0.0 (montado en `/web`)
- **Base de datos NoSQL**: Firebase Firestore (datos del juego)
- **Base de datos SQL**: PostgreSQL con SQLAlchemy 2.0 (autenticación admin)
- **Migraciones**: Alembic
- **Autenticación**: JWT (python-jose) + bcrypt

## Estructura del Proyecto

```
app/
├── main.py                      # Punto de entrada FastAPI
├── config/settings.py           # Variables de entorno (Pydantic)
├── core/                        # Logger, excepciones, validadores
├── infrastructure/database/
│   ├── firebase_client.py       # Conexión Firestore
│   └── sql_client.py            # Conexión SQLAlchemy
├── domain/                      # Arquitectura hexagonal por dominios
│   ├── auth/                    # Autenticación admin (SQL)
│   ├── players/                 # Jugadores (Firestore)
│   ├── games/                   # Partidas (Firestore)
│   ├── events/                  # Telemetría (Firestore)
│   ├── leaderboard/             # Rankings
│   ├── sessions/                # Sesiones de juego
│   └── web/                     # Dashboard Flask
│       ├── admin/routes.py      # Panel admin + migraciones
│       ├── analytics/           # Estadísticas
│       └── migrations/          # Servicio de migraciones
└── middleware/auth.py           # Middleware de autenticación
```

## Migraciones de Base de Datos (Alembic)

Alembic es el control de versiones para la base de datos SQL. Permite evolucionar el esquema de forma controlada y reversible.

### ¿Para qué sirve?

- **Historial de cambios**: Cada modificación en las tablas queda registrada
- **Sincronización**: Todos los entornos (local, producción) tienen el mismo esquema
- **Rollback**: Si algo falla, puedes revertir al estado anterior

### Comandos CLI (desarrollo local)

```bash
# Ver revisión actual
alembic current

# Ver historial
alembic history

# Aplicar todas las migraciones pendientes
alembic upgrade head

# Revertir última migración
alembic downgrade -1

# Crear nueva migración desde modelos
alembic revision --autogenerate -m "descripción del cambio"
```

### Dashboard Web (`/web/admin/migrations`)

Interfaz visual para gestionar migraciones (requiere rol admin).

| Desde la web puedes | Desde la web NO puedes |
|---------------------|------------------------|
| Ver estado de conexión | Crear nuevas migraciones |
| Ver historial de migraciones | Modificar modelos |
| Aplicar migraciones (upgrade) | Generar código |
| Revertir migraciones (downgrade) | |

> **Nota**: Crear migraciones es trabajo de desarrollo. El dashboard de producción solo aplica/revierte migraciones existentes.

### Flujo de trabajo típico

```
[Desarrollo local]
    ├─ Modificas modelo en app/domain/auth/models.py
    ├─ alembic revision --autogenerate -m "cambio"
    ├─ Pruebas localmente
    └─ Git push

[Producción / Railway]
    └─ Dashboard muestra "1 migración pendiente"
        └─ Click "Aplicar Migraciones"
        └─ BD actualizada ✓
```

### Crear nueva migración (ejemplo)

1. Modifica los modelos en `app/domain/auth/models.py`:
   ```python
   class AdminUser(Base):
       ...
       phone = Column(String(20), nullable=True)  # Nuevo campo
   ```

2. Genera la migración:
   ```bash
   alembic revision --autogenerate -m "añadir phone a admin_users"
   ```

3. Revisa el script generado en `alembic/versions/`

4. Aplica localmente: `alembic upgrade head`

5. Commit y push → En producción, usa el dashboard para aplicar

## Variables de Entorno

```env
# Firebase (obligatorio)
FIREBASE_CREDENTIALS_BASE64=<base64-json>

# PostgreSQL (para auth/migraciones)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=triskel_db
DB_USER=postgres
DB_PASSWORD=password

# Seguridad
SECRET_KEY=clave-secreta
API_KEY=api-key-para-juego
JWT_SECRET_KEY=jwt-secret-diferente
```

## Ejecutar

```bash
# Desarrollo
uvicorn app.main:app --reload

# Producción
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## Endpoints principales

- `GET /docs` - Documentación Swagger
- `GET /web/` - Dashboard web
- `GET /web/admin/migrations` - Panel de migraciones
- `POST /api/v1/auth/login` - Login admin
- `GET /api/v1/players` - Listar jugadores
- `GET /api/v1/games` - Listar partidas
