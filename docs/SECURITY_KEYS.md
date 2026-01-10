# Claves de Seguridad - Guía Completa

Esta guía explica las diferentes claves de seguridad que usa Triskel-API y para qué sirve cada una.

---

## Resumen Rápido

| Clave | Uso | Quién la usa | Cómo se usa |
|-------|-----|--------------|-------------|
| **`SECRET_KEY`** | Seguridad interna de Flask | Flask (dashboard web) | Automática (firma cookies/sesiones) |
| **`API_KEY`** | Autenticación de administradores | Tu dashboard, scripts, herramientas | Manual (header `X-API-Key`) |

**Ambas son obligatorias** y deben tener **valores diferentes**.

---

## 1. SECRET_KEY - Seguridad Interna de Flask

### ¿Qué es?

Una clave criptográfica que Flask usa internamente para proteger las sesiones y cookies del dashboard web.

### ¿Para qué sirve?

- **Firmar cookies de sesión**: Flask usa esta clave para firmar cookies, evitando que usuarios malintencionados las modifiquen
- **Protección CSRF**: Se usa para generar tokens anti-CSRF en formularios
- **Datos de sesión**: Protege los datos de sesión almacenados en cookies
- **Mensajes flash**: Asegura la integridad de mensajes entre requests

### ¿Dónde se usa en Triskel-API?

- En el dashboard web Flask: [app/domain/web/app.py:43](../app/domain/web/app.py#L43)
- Flask la usa **automáticamente** cuando alguien accede a `/web/dashboard/`

### ¿Cómo se usa?

**NO necesitas enviarla** en ningún request. Flask la usa internamente de forma automática.

```python
# Flask usa SECRET_KEY automáticamente
# Cuando un usuario visita: https://api.railway.app/web/dashboard/
# Flask firma la cookie de sesión con SECRET_KEY
```

### Ejemplo de uso interno

```python
# Esto es lo que Flask hace internamente (tú NO necesitas hacer esto)
from flask import session

@app.route('/login')
def login():
    session['user_id'] = 123  # Flask firma esto con SECRET_KEY automáticamente
    return "Logged in"
```

### ¿Quién la necesita?

- **Flask internamente** (nadie más)
- Los usuarios del dashboard web **no la ven ni la usan**

---

## 2. API_KEY - Autenticación de Administradores

### ¿Qué es?

Una clave de autenticación que los **administradores** deben enviar en cada request para tener acceso completo a la API.

### ¿Para qué sirve?

- **Autenticación administrativa**: Identifica requests como provenientes de un administrador confiable
- **Acceso completo**: Da acceso a **todos** los endpoints de la API
- **Bypass de restricciones**: No necesita ser un jugador específico para acceder a datos

### ¿Dónde se usa en Triskel-API?

- En el middleware de autenticación: [app/middleware/auth.py:57](../app/middleware/auth.py#L57)
- Se valida en cada request a endpoints `/v1/*`

### ¿Cómo se usa?

Los administradores **deben enviarla manualmente** en el header `X-API-Key` de cada request.

```bash
# Ejemplo: Listar TODOS los jugadores (solo admins)
curl -H "X-API-Key: tu-api-key-aqui" \
  https://api.railway.app/v1/players
```

```python
# Ejemplo desde Python
import requests

headers = {
    "X-API-Key": "tu-api-key-aqui"
}

response = requests.get(
    "https://api.railway.app/v1/players",
    headers=headers
)
```

```javascript
// Ejemplo desde JavaScript (tu dashboard web)
fetch('https://api.railway.app/v1/players', {
  headers: {
    'X-API-Key': 'tu-api-key-aqui'
  }
})
```

### ¿Quién la necesita?

- Tu **dashboard web** cuando consulta la API
- **Scripts de administración**
- **Herramientas internas** de tu equipo
- **NO** los jugadores individuales (ellos usan `X-Player-Token`)

---

## Comparación Visual

```
┌─────────────────────────────────────────────────────────────┐
│                    ARQUITECTURA TRISKEL                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🎮 Unity (Jugador Individual)                              │
│     Request → API                                           │
│     Headers: X-Player-ID + X-Player-Token                   │
│     ❌ No usa API_KEY                                        │
│     ❌ No usa SECRET_KEY                                     │
│                                                             │
│  👨‍💼 Dashboard Web (Administrador)                           │
│     1. Usuario accede a /web/dashboard/                     │
│        → Flask usa SECRET_KEY (automático, invisible)       │
│                                                             │
│     2. Dashboard consulta API REST                          │
│        Request → API                                        │
│        Headers: X-API-Key (manual, explícito)               │
│        ✅ Usa API_KEY                                        │
│                                                             │
│  🛠️ Scripts de Admin                                        │
│     Request → API                                           │
│     Headers: X-API-Key                                      │
│     ✅ Usa API_KEY                                           │
│     ❌ No usa SECRET_KEY                                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Generación de Claves

Genera **valores diferentes** para cada clave:

```bash
# Genera SECRET_KEY (para Flask)
openssl rand -hex 32
# Ejemplo: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a1b2c3d4e5f6

# Genera API_KEY (para autenticación admin)
openssl rand -hex 32
# Ejemplo: z9y8x7w6v5u4t3s2r1q0p9o8n7m6l5k4j3i2h1g0f9e8d7c6b5a4z9y8x7w6v5u4
```

**IMPORTANTE:** No uses las mismas claves para ambas variables.

---

## Configuración en Railway

En el dashboard de Railway, configura ambas variables:

```bash
SECRET_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a1b2c3d4e5f6
API_KEY=z9y8x7w6v5u4t3s2r1q0p9o8n7m6l5k4j3i2h1g0f9e8d7c6b5a4z9y8x7w6v5u4
```

---

## Configuración Local (Desarrollo)

En tu archivo `.env`:

```bash
# Claves para desarrollo local (NUNCA uses estas en producción)
SECRET_KEY=triskel_secret_key_desarrollo_local_change_in_production
API_KEY=triskel_admin_api_key_desarrollo_local_change_in_production
```

**Nota:** En desarrollo puedes usar valores simples, pero en **producción** usa claves generadas con `openssl rand -hex 32`.

---

## Preguntas Frecuentes

### ¿Por qué necesito dos claves diferentes?

Porque tienen **propósitos completamente diferentes**:
- `SECRET_KEY`: Para operaciones **internas** de Flask (invisible para usuarios)
- `API_KEY`: Para **autenticación administrativa** (visible en headers)

### ¿Pueden tener el mismo valor?

**No se recomienda**. Por seguridad, deben ser diferentes:
- Si alguien compromete tu `API_KEY`, aún tendrá que descubrir `SECRET_KEY` para atacar las sesiones de Flask
- Separación de responsabilidades: cada clave tiene un propósito específico

### ¿Los jugadores necesitan alguna de estas claves?

**No**. Los jugadores usan su propio sistema de autenticación:
- `X-Player-ID`: Su identificador único
- `X-Player-Token`: Su token personal (generado al crear cuenta)

### ¿Qué pasa si cambio SECRET_KEY en producción?

**Consecuencias:**
- Todas las sesiones activas de Flask se invalidarán
- Los usuarios del dashboard web tendrán que volver a iniciar sesión
- Las cookies existentes dejarán de funcionar

**Recomendación:** Solo cámbiala si sospechas que fue comprometida.

### ¿Qué pasa si cambio API_KEY en producción?

**Consecuencias:**
- Tu dashboard web dejará de poder acceder a la API
- Scripts y herramientas con la API_KEY antigua dejarán de funcionar
- Deberás actualizar la API_KEY en todos los servicios que la usen

**Recomendación:** Actualiza todos los servicios inmediatamente después del cambio.

### ¿Dónde guardo API_KEY en mi dashboard web?

Depende de cómo esté construido tu dashboard:

1. **Si es una web separada en Railway:**
   ```javascript
   // Usa variables de entorno en tu frontend
   const API_KEY = process.env.REACT_APP_API_KEY;
   ```

2. **Si usas el dashboard Flask integrado:**
   ```python
   # Ya está disponible en settings
   from app.config.settings import settings
   headers = {"X-API-Key": settings.api_key}
   ```

---

## Seguridad: Mejores Prácticas

### ✅ Hacer

- Genera claves con `openssl rand -hex 32`
- Usa valores **diferentes** para cada clave
- Mantén las claves **secretas** (nunca las commitees al repositorio)
- Rota las claves periódicamente (cada 6-12 meses)
- Usa claves largas (mínimo 32 caracteres)

### ❌ Evitar

- Usar la misma clave para ambas variables
- Usar valores simples como "123456" o "password"
- Compartir las claves públicamente
- Hardcodear las claves en el código
- Commitear archivos `.env` al repositorio

---

## Referencia Rápida

### SECRET_KEY
```bash
# Generación
openssl rand -hex 32

# Configuración (Railway)
SECRET_KEY=a1b2c3d4e5f6g7h8i9j0...

# Uso
# Automático por Flask, no necesitas hacer nada
```

### API_KEY
```bash
# Generación
openssl rand -hex 32

# Configuración (Railway)
API_KEY=z9y8x7w6v5u4t3s2r1q0...

# Uso (ejemplos)
curl -H "X-API-Key: z9y8x7w6..." https://api.railway.app/v1/players
fetch('/v1/players', { headers: { 'X-API-Key': 'z9y8x7w6...' } })
```

---

## Recursos Adicionales

- [Guía de Despliegue en Railway](./RAILWAY_DEPLOYMENT.md)
- [Integración con Unity](./UNITY_INTEGRATION.md)
- [Middleware de Autenticación](../app/middleware/auth.py)
- [Configuración de Flask](../app/domain/web/app.py)

---

Documentación actualizada: 2025-01-10
