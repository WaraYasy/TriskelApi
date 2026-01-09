"""
Service para Auth

TODO: Implementar lógica de negocio de autenticación.

Responsabilidades:
- Hashear passwords con bcrypt antes de guardar
- Validar credenciales en login
- Generar JWT tokens (access + refresh)
- Validar y renovar tokens
- Registrar auditoría de acciones
- Verificar permisos por rol

Seguridad crítica:
- NUNCA retornar password_hash al cliente
- SIEMPRE hashear passwords
- Validar tokens en cada petición protegida
- Rate limiting para prevenir brute force
"""
pass
