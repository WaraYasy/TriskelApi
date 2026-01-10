# Guía de Despliegue en Railway

Esta guía te ayudará a desplegar Triskel-API en Railway correctamente.

## Variables de Entorno Requeridas

Railway necesita que configures las siguientes variables de entorno en tu proyecto.

### 1. Variables OBLIGATORIAS

Estas variables son **obligatorias** para que la aplicación funcione en producción:

#### `SECRET_KEY` (Obligatoria)
Clave secreta para operaciones de seguridad internas.

```bash
# Genera una clave segura con:
openssl rand -hex 32
```

**Ejemplo:**
```
SECRET_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6
```

#### `API_KEY` (Obligatoria)
Clave API para acceso administrativo (dashboard, scripts, herramientas).

```bash
# Genera una clave segura con:
openssl rand -hex 32
```

**Ejemplo:**
```
API_KEY=x9y8z7w6v5u4t3s2r1q0p9o8n7m6l5k4j3i2h1g0f9e8d7c6b5a4
```

#### `FIREBASE_CREDENTIALS_BASE64` (Obligatoria)
Credenciales de Firebase codificadas en base64.

**Cómo generarlas:**

```bash
# Desde el directorio raíz del proyecto
cat config/firebase-credentials.json | base64
```

En macOS, usa:
```bash
cat config/firebase-credentials.json | base64 -w 0
```

**Ejemplo:**
```
FIREBASE_CREDENTIALS_BASE64=eyJ0eXBlIjoic2VydmljZV9hY2NvdW50IiwicHJvamVjdF9pZCI6InRyaXNrZWwtYXBpIiwicHJpdmF0ZV9rZXlfaWQiOi...
```

**Importante:** Copia toda la cadena base64 generada (será muy larga, es normal).

---

### 2. Variables OPCIONALES

Estas variables son opcionales, pero recomendadas para producción:

#### `CORS_ORIGINS` (Recomendada para Unity WebGL y Web)
Orígenes permitidos para CORS, separados por comas.

**Para este proyecto (Triskel):**
- Si tu juego Unity está compilado como **WebGL** y desplegado en algún servidor, necesitas añadir ese origen
- Si tienes una **web (dashboard/landing)** en Railway, necesitas añadir ese origen
- Si tu juego Unity es una **aplicación nativa** (Desktop, Android, iOS), **NO necesitas CORS** (las apps nativas no tienen restricciones CORS)

**Ejemplo para Unity WebGL + Web en Railway:**
```
CORS_ORIGINS=https://triskel-game.railway.app,https://triskel-web.railway.app
```

**Ejemplo para Unity WebGL en itch.io:**
```
CORS_ORIGINS=https://tu-usuario.itch.io,https://v6p9d9t4.ssl.hwcdn.net
```

**Ejemplo para múltiples dominios:**
```
CORS_ORIGINS=https://triskel.com,https://www.triskel.com,https://game.triskel.com,https://dashboard.triskel.com
```

**Por defecto:** Si no se configura en producción, no se permitirá ningún origen (modo restrictivo).

**Nota importante:** Si tu juego Unity es **solo nativo** (no WebGL), puedes omitir esta variable completamente ya que las aplicaciones nativas no están sujetas a las restricciones CORS del navegador.

#### `LOG_LEVEL` (Opcional)
Nivel de logs para la aplicación.

**Valores posibles:** `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

**Por defecto:** `INFO` en producción

**Ejemplo:**
```
LOG_LEVEL=INFO
```

---

## Variables que NO debes configurar

Las siguientes variables se configuran automáticamente y **NO** deben ser añadidas manualmente:

- `PORT`: Railway lo proporciona automáticamente con `$PORT`
- `RAILWAY_ENVIRONMENT`: Railway lo establece automáticamente a `production`
- `APP_NAME`: Hardcodeado en el código como "Triskel-API"
- `DEBUG`: Detectado automáticamente (`False` en Railway)

---

## Pasos para Desplegar en Railway

### 1. Crear Proyecto en Railway

1. Ve a [Railway](https://railway.app)
2. Crea un nuevo proyecto
3. Conecta tu repositorio de GitHub

### 2. Configurar Variables de Entorno

En el dashboard de Railway:

1. Ve a tu proyecto
2. Selecciona la pestaña **Variables**
3. Añade las variables obligatorias:
   - `SECRET_KEY`
   - `API_KEY`
   - `FIREBASE_CREDENTIALS_BASE64`
4. (Opcional) Añade las variables opcionales:
   - `CORS_ORIGINS`
   - `LOG_LEVEL`

### 3. Generar las Claves

```bash
# SECRET_KEY
openssl rand -hex 32

# API_KEY
openssl rand -hex 32

# FIREBASE_CREDENTIALS_BASE64
cat config/firebase-credentials.json | base64 -w 0
```

Copia cada resultado y pégalo en Railway.

### 4. Verificar Configuración

Railway debería detectar automáticamente:
- `railway.json` para la configuración de build/deploy
- `requirements.txt` para las dependencias de Python
- `runtime.txt` para la versión de Python (3.11)

### 5. Desplegar

1. Haz push a tu rama principal (`main`)
2. Railway detectará los cambios y desplegará automáticamente
3. Verifica los logs en el dashboard de Railway

### 6. Health Check

Una vez desplegado, verifica que la API esté funcionando:

```bash
# Reemplaza <tu-url> con la URL de Railway
curl https://<tu-url>.railway.app/health
```

Deberías recibir:
```json
{
  "status": "ok",
  "version": "2.0.0"
}
```

---

## Solución de Problemas

### Error: "SECRET_KEY es obligatoria en producción"

**Causa:** No has configurado la variable `SECRET_KEY`.

**Solución:** Añade la variable `SECRET_KEY` en Railway con una clave generada con `openssl rand -hex 32`.

### Error: "API_KEY es obligatoria en producción"

**Causa:** No has configurado la variable `API_KEY`.

**Solución:** Añade la variable `API_KEY` en Railway con una clave generada con `openssl rand -hex 32`.

### Error: "FIREBASE_CREDENTIALS_BASE64 o FIREBASE_CREDENTIALS_JSON son obligatorias en producción"

**Causa:** No has configurado las credenciales de Firebase.

**Solución:** Genera las credenciales base64 y añádelas:
```bash
cat config/firebase-credentials.json | base64 -w 0
```

### Error: "Application failed to start"

**Verifica:**
1. Que todas las variables obligatorias están configuradas
2. Los logs de Railway para ver el error específico
3. Que el archivo `firebase-credentials.json` es válido

### CORS Errors en el frontend

**Causa:** No has configurado `CORS_ORIGINS` o los orígenes no coinciden.

**Solución:** Añade la variable `CORS_ORIGINS` con los orígenes de tu frontend:
```
CORS_ORIGINS=https://tu-frontend.com,https://www.tu-frontend.com
```

---

## Configuración Específica para Unity

### Unity Nativo (Desktop, Android, iOS)

Si tu juego Unity es una **aplicación nativa**, la configuración es muy simple:

1. **NO necesitas configurar CORS_ORIGINS** - Las aplicaciones nativas no tienen restricciones CORS
2. Simplemente apunta tu cliente Unity a la URL de Railway:
   ```csharp
   string apiUrl = "https://tu-api.railway.app";
   ```

### Unity WebGL

Si tu juego Unity está compilado como **WebGL**, necesitas configurar CORS:

1. **Despliega tu build WebGL** en un servidor (Railway, itch.io, Netlify, etc.)
2. **Obtén la URL** donde está desplegado tu WebGL
3. **Configura CORS_ORIGINS** en Railway con esa URL:
   ```
   CORS_ORIGINS=https://tu-juego-webgl.railway.app
   ```

#### Ejemplo para Unity WebGL en itch.io:

Si publicas tu juego en itch.io, necesitarás añadir **dos URLs**:
```
CORS_ORIGINS=https://tu-usuario.itch.io,https://v6p9d9t4.ssl.hwcdn.net
```

La segunda URL (`v6p9d9t4.ssl.hwcdn.net`) es necesaria porque itch.io sirve los archivos WebGL desde su CDN.

#### Testing Local de Unity WebGL:

Para probar localmente tu WebGL, añade `http://localhost` a CORS_ORIGINS en desarrollo:
```
# En tu .env local
CORS_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
```

### Configuración para Dashboard Web

Si además tienes un dashboard web en Railway:

1. Despliega tu dashboard web como un servicio separado en Railway
2. Añade su URL a CORS_ORIGINS:
   ```
   CORS_ORIGINS=https://triskel-game.railway.app,https://triskel-dashboard.railway.app
   ```

### Recomendación Final

Configura CORS_ORIGINS según tu caso:

```bash
# Caso 1: Solo Unity Nativo + Dashboard Web
CORS_ORIGINS=https://triskel-dashboard.railway.app

# Caso 2: Unity WebGL + Dashboard Web
CORS_ORIGINS=https://triskel-game.railway.app,https://triskel-dashboard.railway.app

# Caso 3: Unity Nativo (no necesitas CORS)
# No configures CORS_ORIGINS, la configuración por defecto funcionará
```

---

## Checklist de Despliegue

Antes de desplegar, verifica:

### Variables Obligatorias
- [ ] Has generado `SECRET_KEY` con `openssl rand -hex 32`
- [ ] Has generado `API_KEY` con `openssl rand -hex 32`
- [ ] Has generado `FIREBASE_CREDENTIALS_BASE64` desde el archivo JSON
- [ ] Has configurado las 3 variables obligatorias en Railway

### Configuración de CORS (según tu caso)
- [ ] Si usas **Unity WebGL**: Has configurado `CORS_ORIGINS` con la URL de tu juego WebGL
- [ ] Si usas **Dashboard Web**: Has configurado `CORS_ORIGINS` con la URL del dashboard
- [ ] Si usas **Unity Nativo solo**: Puedes omitir `CORS_ORIGINS` (no necesario)

### Repositorio
- [ ] Has verificado que `railway.json`, `Procfile`, y `requirements.txt` están en el repo
- [ ] Has hecho commit y push de todos los cambios al branch principal

### Despliegue
- [ ] Has configurado todas las variables necesarias en Railway
- [ ] El despliegue se completó sin errores
- [ ] Has verificado el health check endpoint: `https://tu-api.railway.app/health`
- [ ] Has probado la API docs: `https://tu-api.railway.app/docs`

### Testing desde Unity/Web
- [ ] Has actualizado la URL de la API en tu cliente Unity/Web
- [ ] Has probado crear un jugador desde Unity/Web
- [ ] Has verificado que no hay errores CORS en la consola del navegador (si usas WebGL/Web)

---

## Documentación Adicional

- [Documentación de Railway](https://docs.railway.app)
- [Variables de Entorno en Railway](https://docs.railway.app/develop/variables)
- [Despliegue de Python en Railway](https://docs.railway.app/guides/python)

---

## Resumen Rápido para Triskel (Unity + Web)

### Configuración Mínima Obligatoria

```bash
# 1. Genera las claves
openssl rand -hex 32  # Copia para SECRET_KEY
openssl rand -hex 32  # Copia para API_KEY
cat config/firebase-credentials.json | base64 -w 0  # Copia para FIREBASE_CREDENTIALS_BASE64

# 2. En Railway, configura:
SECRET_KEY=<clave-generada-1>
API_KEY=<clave-generada-2>
FIREBASE_CREDENTIALS_BASE64=<base64-generado>
```

### Configuración de CORS (después de desplegar)

Una vez que tengas las URLs de tus servicios desplegados:

```bash
# Si tu web está en: https://triskel-dashboard.railway.app
CORS_ORIGINS=https://triskel-dashboard.railway.app

# Si además usas Unity WebGL en: https://triskel-game.railway.app
CORS_ORIGINS=https://triskel-dashboard.railway.app,https://triskel-game.railway.app
```

**Importante:** Si tu Unity es **solo nativo** (Desktop/Android/iOS), no necesitas configurar CORS_ORIGINS.

---

## Contacto y Soporte

Si tienes problemas con el despliegue:

1. Verifica los logs en Railway
2. Revisa esta guía paso a paso
3. Consulta la documentación de Railway
4. Contacta al equipo de desarrollo
