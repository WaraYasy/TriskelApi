"""
API REST para Auth

TODO: Implementar endpoints de autenticación.

Endpoints sugeridos:
- POST /auth/login - Login con username/password
- POST /auth/refresh - Renovar access token con refresh token
- POST /auth/logout - Invalidar tokens
- GET /auth/me - Obtener info del usuario autenticado
- POST /admin/users - Crear nuevo admin (solo admin)
- GET /admin/audit - Ver logs de auditoría (solo admin)

Ejemplo de login:
POST /auth/login
{"username": "admin", "password": "secret"}

Response:
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "user": {
    "id": 1,
    "username": "admin",
    "role": "admin"
  }
}

Después, el dashboard usa el access_token en cada petición:
Authorization: Bearer eyJhbGc...
"""
pass
