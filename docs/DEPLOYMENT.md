# Guía de Deployment en Railway

Esta guía explica cómo deployar Triskel-API en Railway de forma segura y automatizada.

## Requisitos Previos

1. **Cuenta de Railway**: Crear una cuenta en [railway.app](https://railway.app)
2. **Railway CLI**: Instalar el CLI de Railway
   ```bash
   npm i -g @railway/cli
   ```
3. **Login en Railway**: Autenticarse
   ```bash
   railway login
   ```

## Configuración Inicial

### 1. Crear Proyecto en Railway

1. Ir a [railway.app](https://railway.app) y crear cuenta/login
2. Click en **"New Project"**
3. Seleccionar **"Deploy from GitHub repo"**
4. Autorizar acceso a GitHub y seleccionar el repositorio `Triskel-API`
5. Railway detectará automáticamente que es una aplicación Python

### 2. Configurar Variables de Entorno

**⚠️ IMPORTANTE: NUNCA guardes credenciales en archivos de texto**

#### Desde el Dashboard de Railway (Recomendado)

1. En tu proyecto de Railway, click en el servicio desplegado
2. Click en la pestaña **"Variables"**
3. Click en **"+ New Variable"** para cada variable
4. Añadir las variables listadas en la sección "Variables Requeridas" (ver abajo)

#### Alternativa: Railway CLI

Si prefieres usar la terminal:

```bash
# Instalar Railway CLI
npm i -g @railway/cli

# Login
railway login

# Enlazar proyecto
railway link

# Definir variables
railway variables --set APP_NAME="Triskel-API"
railway variables --set DEBUG="False"
railway variables --set ENVIRONMENT="production"
railway variables --set LOG_LEVEL="INFO"
railway variables --set CORS_ORIGINS="*"
railway variables --set FIREBASE_CREDENTIALS_JSON='{"type":"service_account",...}'
```

### 3. Variables Requeridas

Estas son las variables que DEBES configurar:

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `APP_NAME` | Nombre de la aplicación | `Triskel-API` |
| `DEBUG` | Modo debug | `False` (producción) |
| `ENVIRONMENT` | Entorno de ejecución | `production` |
| `PORT` | Puerto (Railway lo asigna automáticamente) | `8000` |
| `LOG_LEVEL` | Nivel de logs | `INFO` |
| `CORS_ORIGINS` | Orígenes permitidos para CORS | `https://tu-dominio.com` o `*` |
| `FIREBASE_CREDENTIALS_JSON` | Credenciales de Firebase (JSON completo) | `{"type":"service_account",...}` |

### 4. Obtener Credenciales de Firebase

1. Ir a [Firebase Console](https://console.firebase.google.com)
2. Seleccionar tu proyecto (`triskel-game`)
3. Ir a **Project Settings** > **Service Accounts**
4. Click en **Generate new private key**
5. Copiar todo el contenido del archivo JSON
6. Pegarlo cuando el script lo solicite

**⚠️ NOTA DE SEGURIDAD:** Si previamente expusiste credenciales en el repositorio:
- Rota las credenciales inmediatamente desde Firebase Console
- Genera una nueva clave privada
- Nunca reutilices credenciales expuestas

## Deployment

### Primera Vez

```bash
# Asegurarse de estar en el proyecto correcto
railway status

# Deployar
railway up
```

### Deployments Subsiguientes

Railway hace deployment automático cuando haces `git push` a la rama principal.

También puedes deployar manualmente:

```bash
railway up
```

## Verificación

### Ver Logs

```bash
railway logs
```

### Ver Variables Configuradas

```bash
railway variables
```

### Abrir la Aplicación

```bash
railway open
```

### Verificar Health Check

Railway usa el endpoint `/health` configurado en `railway.json`. Asegúrate de que este endpoint existe en tu aplicación.

## Configuración de CD/CI

### GitHub Actions (Ejemplo)

Crea `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Railway

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install Railway
        run: npm i -g @railway/cli

      - name: Deploy to Railway
        run: railway up --service triskel-api
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
```

Para obtener el token:
```bash
railway whoami --token
```

Añadir el token como secret en GitHub:
1. Ir a Settings > Secrets and variables > Actions
2. Crear nuevo secret: `RAILWAY_TOKEN`

## Troubleshooting

### Error: Variables no se cargan

1. Verificar que las variables estén configuradas:
   ```bash
   railway variables
   ```

2. Verificar que `settings.py` use `pydantic_settings` correctamente
   - La clase `Settings` debe heredar de `BaseSettings`
   - Debe tener `env_file = ".env"` en la clase Config
   - Las variables deben usar `case_sensitive = False`

### Error: Firebase no se conecta

1. Verificar que `FIREBASE_CREDENTIALS_JSON` sea JSON válido:
   ```bash
   railway variables | grep FIREBASE
   ```

2. Verificar que el JSON tenga todos los campos requeridos:
   - `type`
   - `project_id`
   - `private_key`
   - `client_email`

3. Verificar logs:
   ```bash
   railway logs
   ```

### Build falla

1. Verificar que `requirements.txt` esté actualizado
2. Verificar que `runtime.txt` especifica la versión correcta de Python
3. Ver logs de build:
   ```bash
   railway logs --build
   ```

## Mejores Prácticas

1. **Nunca commitear credenciales**
   - Usar `.gitignore` para archivos sensibles
   - Nunca guardar credenciales en archivos de texto

2. **Rotar credenciales regularmente**
   - Cambiar credenciales de Firebase cada 90 días
   - Usar diferentes credenciales para dev/staging/prod

3. **Monitoreo**
   - Revisar logs regularmente
   - Configurar alertas en Railway

4. **Variables de entorno**
   - Usar nombres descriptivos
   - Documentar todas las variables necesarias
   - Mantener `.env.example` actualizado

5. **Deployments**
   - Probar localmente antes de deployar
   - Usar branches para features
   - Deployar a producción solo desde `main`

## Recursos

- [Railway Docs](https://docs.railway.app)
- [Railway CLI](https://docs.railway.app/develop/cli)
- [Firebase Admin SDK](https://firebase.google.com/docs/admin/setup)