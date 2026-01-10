# 🎮 Triskel API

API REST y Dashboard Web para el videojuego **Triskel: La Balada del Último Guardián**.

Desarrollado por **Mandrágora** para Colegio Hogwarts de Magia y Hechicería.

## 📖 Guías Rápidas

- 🚀 **[Desplegar en Railway](docs/RAILWAY_DEPLOYMENT.md)** - Guía completa de despliegue en producción
- 🎮 **[Integrar con Unity](docs/UNITY_INTEGRATION.md)** - Conecta tu juego Unity con la API
- 🔐 **[Claves de Seguridad](docs/SECURITY_KEYS.md)** - Diferencia entre SECRET_KEY y API_KEY
- 📚 **[Documentación Completa](docs/README.md)** - Índice de toda la documentación

---

## 🏗️ Arquitectura

- **FastAPI** - API REST para el juego (Unity/Godot)
- **Flask** - Dashboard web para analytics
- **Firebase Firestore** - Base de datos NoSQL
- **MariaDB** - Base de datos SQL (autenticación admin - futuro)
- **Arquitectura Hexagonal** - Ports & Adapters para desacoplamiento

---

## 📦 Instalación

### **1. Clonar el Repositorio**
```bash
git clone <repo-url>
cd Triskel-API
```

### **2. Crear Entorno Virtual (Recomendado)**
```bash
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### **3. Instalar Dependencias**
```bash
pip install -r requirements.txt
```

Esto instalará:
- ✅ FastAPI + Uvicorn (API REST)
- ✅ Flask + Plotly (Dashboard)
- ✅ Firebase Admin SDK
- ✅ Pandas (análisis de datos)

### **4. Configurar Firebase**
Coloca tu archivo de credenciales en:
```
config/firebase-credentials.json
```

### **5. Variables de Entorno**

Para **desarrollo local**, copia `.env.example` a `.env`:
```bash
cp .env.example .env
```

Variables **obligatorias** para desarrollo:
```bash
SECRET_KEY=triskel_secret_key_desarrollo_local_change_in_production
API_KEY=triskel_admin_api_key_desarrollo_local_change_in_production
```

Las credenciales de Firebase se cargan automáticamente desde `config/firebase-credentials.json` en desarrollo.

**Nota:** Para desplegar en **Railway/Producción**, consulta la [Guía de Despliegue](docs/RAILWAY_DEPLOYMENT.md).

---

## 🚀 Ejecutar

### **Modo Desarrollo**
```bash
python3 -m uvicorn app.main:app --reload
```

### **Modo Producción**
```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

---

## 🌐 Endpoints

### **API REST (FastAPI)**
```
http://localhost:8000/              → Info de la API
http://localhost:8000/docs          → Swagger UI (documentación)
http://localhost:8000/health        → Health check
```

#### **Players**
```
POST   /v1/players              → Crear jugador
GET    /v1/players/{id}         → Obtener jugador
GET    /v1/players              → Listar jugadores
PATCH  /v1/players/{id}         → Actualizar jugador
DELETE /v1/players/{id}         → Eliminar jugador
```

#### **Games**
```
POST   /v1/games                        → Crear partida
GET    /v1/games/{id}                   → Obtener partida
GET    /v1/games/player/{player_id}    → Partidas de un jugador
POST   /v1/games/{id}/level/start      → Iniciar nivel
POST   /v1/games/{id}/level/complete   → Completar nivel
PATCH  /v1/games/{id}                   → Actualizar partida
DELETE /v1/games/{id}                   → Eliminar partida
```

### **Dashboard Web (Flask)**
```
http://localhost:8000/web/                  → Landing page
http://localhost:8000/web/dashboard/        → Dashboard principal
http://localhost:8000/web/dashboard/players → Análisis de jugadores
http://localhost:8000/web/dashboard/games   → Análisis de partidas
http://localhost:8000/web/dashboard/choices → Decisiones morales
```

---

## 🔐 Autenticación

### **Para Jugadores (API REST)**
Todos los endpoints (excepto `POST /v1/players`) requieren headers:
```
X-Player-ID: <player_id>
X-Player-Token: <player_token>
```

El token se obtiene al crear un jugador:
```bash
curl -X POST http://localhost:8000/v1/players \
  -H "Content-Type: application/json" \
  -d '{"username": "player1", "email": "player1@example.com"}'

# Response:
{
  "player_id": "abc-123",
  "username": "player1",
  "player_token": "xyz-789"  # ⭐ Guardar este token
}
```

---

## 📁 Estructura del Proyecto

```
app/
├── domain/                    # Dominios verticales
│   ├── players/              # Jugadores (hexagonal)
│   │   ├── api.py           # FastAPI endpoints
│   │   ├── service.py       # Lógica de negocio
│   │   ├── models.py        # Entidades
│   │   ├── schemas.py       # DTOs
│   │   ├── ports.py         # Interfaces
│   │   └── adapters/
│   │       └── firestore_repository.py
│   ├── games/                # Partidas (hexagonal)
│   ├── events/               # Eventos (preparado)
│   ├── sessions/             # Sesiones (preparado)
│   ├── auth/                 # Autenticación (preparado)
│   └── web/                  # Dashboard Flask
│       ├── app.py
│       ├── analytics/        # Métricas
│       ├── templates/
│       └── static/
├── shared/                    # Shared Kernel
│   ├── settings.py
│   ├── firebase_client.py
│   ├── logger.py
│   └── validators.py
├── middleware/
│   └── auth.py
└── main.py                    # Aplicación principal
```

---

## 🧪 Testing

### **Test Manual con cURL**

#### Crear Jugador
```bash
curl -X POST http://localhost:8000/v1/players \
  -H "Content-Type: application/json" \
  -d '{"username": "test_user", "email": "test@example.com"}'
```

#### Crear Partida
```bash
curl -X POST http://localhost:8000/v1/games \
  -H "Content-Type: application/json" \
  -H "X-Player-ID: <player_id>" \
  -H "X-Player-Token: <player_token>" \
  -d '{"player_id": "<player_id>"}'
```

#### Completar Nivel
```bash
curl -X POST http://localhost:8000/v1/games/<game_id>/level/complete \
  -H "Content-Type: application/json" \
  -H "X-Player-ID: <player_id>" \
  -H "X-Player-Token: <player_token>" \
  -d '{
    "level": "senda_ebano",
    "time_seconds": 245,
    "deaths": 3,
    "choice": "sanar",
    "relic": "lirio"
  }'
```

---

## 🔧 Desarrollo

### **Añadir Nuevo Dominio**

1. Crear estructura:
```bash
mkdir -p app/domain/nuevo_dominio/adapters
touch app/domain/nuevo_dominio/{__init__,api,service,models,schemas,ports}.py
```

2. Implementar interfaz en `ports.py`
3. Implementar lógica en `service.py`
4. Implementar adaptador en `adapters/`
5. Crear endpoints en `api.py`
6. Registrar router en `main.py`

---

## 📚 Documentación

### Guías de Despliegue e Integración
- 🚀 **[Railway Deployment](docs/RAILWAY_DEPLOYMENT.md)** - Desplegar API en Railway (Variables, CORS, Troubleshooting)
- 🎮 **[Unity Integration](docs/UNITY_INTEGRATION.md)** - Conectar Unity con la API (Nativo y WebGL)
- 📚 **[Docs Index](docs/README.md)** - Índice completo de documentación

### Arquitectura y Desarrollo
- [REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md) - Resumen de arquitectura
- [app/domain/web/README.md](app/domain/web/README.md) - Documentación del dashboard

---

## 🛠️ Stack Tecnológico

| Componente | Tecnología | Versión |
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

## 📊 Estado del Proyecto

### **Implementado ✅**
- ✅ Arquitectura hexagonal
- ✅ Dominio Players (completo)
- ✅ Dominio Games (completo)
- ✅ Dashboard web (UI base)
- ✅ Autenticación simple
- ✅ Logging estructurado
- ✅ Documentación Swagger

### **Por Implementar 📝**
- 📝 Dominio Events
- 📝 Dominio Sessions
- 📝 Dominio Auth (MariaDB)
- 📝 Analytics funcional (gráficos)
- 📝 Leaderboards
- 📝 Tests automatizados

---

## 👥 Equipo

- **Empresa**: Mandrágora
- **Cliente**: Colegio Hogwarts de Magia y Hechicería
- **Videojuego**: Triskel: La Balada del Último Guardián
- **Fecha**: Enero 2026

---

## 📄 Licencia

Propiedad de Mandrágora. Todos los derechos reservados.
