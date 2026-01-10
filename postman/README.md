# Colección de Postman - Triskel API (Players)

## Descripción

Esta carpeta contiene la colección de Postman completa y documentada para los endpoints del dominio **Players** de la API de Triskel.

## Archivos

- `Triskel-Players-API.postman_collection.json` - Colección principal con todos los endpoints

## Cómo Importar la Colección

### Método 1: Importar desde Postman Desktop

1. Abre Postman
2. Haz clic en **Import** (botón superior izquierdo)
3. Selecciona el archivo `Triskel-Players-API.postman_collection.json`
4. Haz clic en **Import**

### Método 2: Drag & Drop

1. Abre Postman
2. Arrastra el archivo JSON directamente a la ventana de Postman

## Configuración Inicial

### Variables de Colección

La colección incluye variables pre-configuradas:

| Variable | Valor por Defecto | Descripción |
|----------|------------------|-------------|
| `baseUrl` | `http://localhost:8000` | URL base de la API |
| `apiKey` | `triskel_admin_api_key_desarrollo_2024` | API Key de administrador |
| `playerId` | *(vacío)* | Se auto-completa al crear un jugador |
| `playerToken` | *(vacío)* | Se auto-completa al crear un jugador |

### Editar Variables (Opcional)

Si tu API corre en otro puerto o host:

1. Haz clic derecho en la colección → **Edit**
2. Ve a la pestaña **Variables**
3. Modifica `baseUrl` según tu configuración
4. Guarda los cambios

## Flujo de Trabajo Recomendado

### 1. Crear un Jugador

Ejecuta el request: **Public Endpoints → Create Player**

- No requiere autenticación
- Las variables `playerId` y `playerToken` se guardarán automáticamente
- Guarda estos valores para futuras sesiones

### 2. Ver Tu Perfil

Ejecuta: **Player Authentication → Get My Profile**

- Usa las credenciales auto-guardadas
- Verifica que la autenticación funciona correctamente

### 3. Actualizar Datos

Ejecuta: **Player Authentication → Update Player**

- Modifica el body con los datos que quieras actualizar
- Solo se actualizan los campos enviados

### 4. Listar Todos (Admin)

Ejecuta: **Admin Only → List All Players**

- Usa la API Key de administrador
- Ve todos los jugadores del sistema

## Estructura de la Colección

```
Triskel API - Players
├── Public Endpoints
│   └── Create Player (POST /v1/players)
├── Player Authentication
│   ├── Get My Profile (GET /v1/players/me)
│   ├── Get Player by ID (GET /v1/players/{id})
│   ├── Update Player (PATCH /v1/players/{id})
│   └── Delete Player (DELETE /v1/players/{id})
└── Admin Only
    ├── List All Players (GET /v1/players)
    ├── Get Any Player by ID (Admin)
    ├── Update Any Player (Admin)
    └── Delete Any Player (Admin)
```

## Autenticación

### Tipo 1: Sin Autenticación (Público)

Solo para crear jugadores:
```
POST /v1/players
```

### Tipo 2: Autenticación de Jugador

Headers requeridos:
```
X-Player-ID: {tu-player-id}
X-Player-Token: {tu-player-token}
```

**Permisos:** Solo puedes acceder a tu propio perfil.

### Tipo 3: Autenticación de Administrador

Header requerido:
```
X-API-Key: triskel_admin_api_key_desarrollo_2024
```

**Permisos:** Acceso total a todos los jugadores.

## Tests Automáticos

Cada request incluye tests automáticos que verifican:

- ✅ Código de respuesta correcto
- ✅ Estructura de datos válida
- ✅ Campos requeridos presentes
- ✅ Auto-guardado de variables

Puedes ver los resultados en la pestaña **Test Results** después de ejecutar un request.

## Ejemplos de Uso

### Crear un Jugador

```json
POST /v1/players
{
  "username": "jugador_nuevo",
  "email": "nuevo@triskel.com"
}
```

**Respuesta:**
```json
{
  "player_id": "123e4567-e89b-12d3-a456-426614174000",
  "username": "jugador_nuevo",
  "player_token": "abc-def-token-secret"
}
```

### Actualizar Estadísticas

```json
PATCH /v1/players/{playerId}
Headers: X-Player-ID, X-Player-Token
{
  "total_playtime_seconds": 7200,
  "games_played": 10,
  "games_completed": 5,
  "stats": {
    "total_good_choices": 20,
    "total_bad_choices": 5,
    "favorite_relic": "lirio",
    "moral_alignment": 0.6
  }
}
```

## Errores Comunes

### 401 Unauthorized
- Verifica que los headers `X-Player-ID` y `X-Player-Token` estén presentes
- Asegúrate de que las variables estén configuradas correctamente

### 403 Forbidden
- No tienes permisos para acceder a ese recurso
- Verifica que estés usando tu propio `player_id`
- O usa la API Key de administrador si corresponde

### 404 Not Found
- El jugador no existe
- Verifica que el `player_id` sea correcto

### 422 Unprocessable Entity
- Datos inválidos en el body
- Revisa la documentación de cada campo

## Documentación Adicional

- **API Docs (Swagger):** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health

## Soporte

Si encuentras problemas con la colección:

1. Verifica que la API esté corriendo: `http://localhost:8000/health`
2. Revisa las variables de colección
3. Consulta la documentación en `/docs`
4. Revisa los logs de la API

---

**Versión:** 2.0.0
**Última actualización:** 2026-01-10
**Compatibilidad:** Postman v10+
