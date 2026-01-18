# Configuración de CI/CD para Triskel API

Este documento explica cómo está configurado el CI/CD de Triskel API usando GitHub Actions.

## Workflows Configurados

### 1. CI - Tests y Cobertura (`ci.yml`)

Este workflow se ejecuta automáticamente en:
- Push a las ramas: `main`, `develop`, `feature/**`
- Pull requests hacia: `main`, `develop`

#### Jobs incluidos:

##### Test Job
- **Matriz de Python**: Ejecuta tests en Python 3.11, 3.12 y 3.13
- **Steps**:
  1. Instala dependencias desde `requirements.txt`
  2. Configura Firebase credentials (opcional, desde secrets)
  3. Ejecuta linter ruff (opcional, no falla el build)
  4. Ejecuta tests unitarios
  5. Ejecuta todos los tests con reporte de cobertura
  6. Sube cobertura a Codecov (opcional)
  7. Archiva reporte HTML de cobertura
  8. Verifica que la cobertura sea >= 37%

##### Lint Job
- Ejecuta herramientas de calidad de código:
  - `ruff`: Linter rápido para Python
  - `black`: Verificación de formato
  - `isort`: Verificación de orden de imports

##### Security Job
- Análisis de seguridad:
  - `bandit`: Detecta problemas de seguridad en el código
  - `safety`: Verifica vulnerabilidades en dependencias

## Configuración de Secrets

Para que el CI funcione completamente, necesitas configurar estos secrets en GitHub:

### Secrets Requeridos

1. **FIREBASE_CREDENTIALS** (Opcional)
   - Contenido del archivo `config/firebase-credentials.json`
   - Necesario si tienes tests que requieren Firebase
   - Path: Settings → Secrets and variables → Actions → New repository secret

2. **CODECOV_TOKEN** (Opcional)
   - Token de Codecov para subir reportes de cobertura
   - Obtenerlo en: https://codecov.io/
   - Path: Settings → Secrets and variables → Actions → New repository secret

### Cómo configurar FIREBASE_CREDENTIALS

```bash
# 1. Lee el contenido del archivo
cat config/firebase-credentials.json

# 2. Copia TODO el contenido JSON

# 3. Ve a GitHub:
#    Settings → Secrets and variables → Actions → New repository secret
#    Name: FIREBASE_CREDENTIALS
#    Secret: [pega el JSON aquí]
```

### Cómo configurar CODECOV_TOKEN

```bash
# 1. Ve a https://codecov.io/ y vincula tu repositorio

# 2. Copia el token que te proporciona Codecov

# 3. Ve a GitHub:
#    Settings → Secrets and variables → Actions → New repository secret
#    Name: CODECOV_TOKEN
#    Secret: [pega el token aquí]
```

## Badges para el README

Puedes agregar estos badges a tu README.md:

```markdown
![CI Tests](https://github.com/USERNAME/REPO/workflows/CI%20-%20Tests%20y%20Cobertura/badge.svg)
[![codecov](https://codecov.io/gh/USERNAME/REPO/branch/main/graph/badge.svg)](https://codecov.io/gh/USERNAME/REPO)
```

Reemplaza `USERNAME` y `REPO` con tu información.

## Dependabot

Se ha configurado Dependabot para actualizar automáticamente:
- Dependencias de Python (semanalmente los lunes)
- GitHub Actions (semanalmente los lunes)

Las PRs de Dependabot se crearán automáticamente con el prefijo:
- `DEPS:` para dependencias de Python
- `CI:` para actualizaciones de GitHub Actions

## Ejecución Local

Para ejecutar los mismos checks que el CI localmente:

### Tests
```bash
# Todos los tests
pytest

# Solo unitarios
pytest -m unit

# Con cobertura HTML
pytest --cov=app/domain --cov-report=html
```

### Linting
```bash
# Instalar herramientas
pip install ruff black isort

# Ejecutar checks
ruff check app/ tests/
black --check app/ tests/
isort --check-only app/ tests/

# Auto-fix
ruff check app/ tests/ --fix
black app/ tests/
isort app/ tests/
```

### Seguridad
```bash
# Instalar herramientas
pip install bandit safety

# Ejecutar análisis
bandit -r app/
safety check
```

## Ver Resultados del CI

1. **En Pull Requests**: Los checks aparecen automáticamente en la PR
2. **En Actions Tab**: Ve a la pestaña "Actions" del repositorio
3. **Artifacts**: Los reportes HTML se guardan como artifacts por 30 días

## Troubleshooting

### Error: "Firebase credentials not found"
- Configura el secret `FIREBASE_CREDENTIALS` o marca los tests como opcionales

### Error: "Coverage below 37%"
- Revisa qué tests fallaron
- Agrega más tests o ajusta el umbral en `pytest.ini`

### Tests fallan localmente pero pasan en CI (o viceversa)
- Verifica que estés usando la misma versión de Python
- Asegúrate de tener las mismas dependencias: `pip install -r requirements.txt`

### Linter falla
- Ejecuta auto-fix localmente:
  ```bash
  black app/ tests/
  isort app/ tests/
  ruff check app/ tests/ --fix
  ```

## Personalización

### Cambiar versiones de Python testeadas
Edita `.github/workflows/ci.yml`:
```yaml
strategy:
  matrix:
    python-version: ['3.11', '3.12', '3.13']  # Modifica esta lista
```

### Cambiar umbral de cobertura
Edita `pytest.ini`:
```ini
--cov-fail-under=37  # Cambia este número
```

### Agregar más checks
Agrega nuevos steps en `.github/workflows/ci.yml`

## Mejoras Futuras

Considera agregar:
- [ ] Deploy automático a staging/production
- [ ] Tests de performance
- [ ] Análisis de complejidad de código
- [ ] Notificaciones a Slack/Discord
- [ ] Pre-commit hooks
- [ ] Docker image building y push a registry
