# Tests de Triskel API

Suite completa de tests con **nivel de exigencia alta** (70%+ cobertura) para garantizar la calidad y mantenibilidad del código.

## Estructura de Tests

```
tests/
├── conftest.py              # Fixtures compartidas y mocks
├── test_auth.py             # Tests existentes de Auth (17 casos)
├── unit/                    # Tests unitarios (60% del esfuerzo)
│   ├── test_player_models.py
│   ├── test_player_schemas.py
│   ├── test_player_service.py
│   ├── test_game_service.py
│   ├── test_game_schemas.py
│   └── test_event_service.py
├── integration/             # Tests de integración (30% del esfuerzo)
│   ├── test_player_adapter.py
│   └── test_auth_middleware.py
└── e2e/                     # Tests end-to-end (10% del esfuerzo)
    ├── test_game_workflow.py
    └── (más flujos E2E pueden agregarse)
```

## Instalación de Dependencias

```bash
# Instalar dependencias de testing
pip install pytest pytest-asyncio pytest-cov

# O usar requirements.txt si ya incluye estas dependencias
pip install -r requirements.txt
```

## Ejecutar Tests

### Todos los tests con cobertura
```bash
pytest
```

### Solo tests unitarios
```bash
pytest -m unit
```

### Solo tests de integración
```bash
pytest -m integration
```

### Solo tests E2E
```bash
pytest -m e2e
```

### Tests de seguridad
```bash
pytest -m security
```

### Tests de casos límite
```bash
pytest -m edge_case
```

### Ver cobertura detallada
```bash
pytest --cov=app --cov-report=html
# Luego abrir htmlcov/index.html en el navegador
```

### Tests con salida verbose
```bash
pytest -v
```

### Tests de un archivo específico
```bash
pytest tests/unit/test_player_service.py
```

### Tests de una clase específica
```bash
pytest tests/unit/test_player_service.py::TestPlayerStatsUpdate
```

### Tests de un caso específico
```bash
pytest tests/unit/test_player_service.py::TestPlayerStatsUpdate::test_moral_alignment_all_good_choices
```

## Marcadores (Markers)

Los tests están organizados con marcadores para filtrar fácilmente:

- `@pytest.mark.unit` - Tests unitarios de lógica de negocio
- `@pytest.mark.integration` - Tests de integración con adapters
- `@pytest.mark.e2e` - Tests end-to-end de flujos completos
- `@pytest.mark.slow` - Tests que tardan más de 1 segundo
- `@pytest.mark.security` - Tests de seguridad y autorización
- `@pytest.mark.edge_case` - Tests de casos límite y extremos
- `@pytest.mark.requires_firebase` - Tests que requieren mock de Firebase
- `@pytest.mark.requires_db` - Tests que requieren base de datos SQL

## Objetivo de Cobertura

**Meta: 70%+ de cobertura de código**

El archivo `pytest.ini` está configurado con `--cov-fail-under=70`, lo que significa que el build fallará si la cobertura es menor al 70%.

### Áreas con Alta Cobertura

✅ **Players Domain**
- Modelos y validaciones (Pydantic)
- Schemas de entrada/salida
- Lógica de negocio (PlayerService)
- Cálculo de moral alignment
- Actualización de estadísticas

✅ **Games Domain**
- Ciclo de vida de partidas
- Validación de partida activa
- Progresión de niveles
- Finalización de partidas

✅ **Events Domain**
- Creación individual y batch
- Validación de jugadores
- Queries con filtros

✅ **Auth Domain** (ya existente)
- Validación de contraseñas
- Hashing y verificación
- Tokens JWT

### Áreas a Expandir (Opcionales)

⚠️ **API Endpoints** - Agregar más tests E2E para endpoints completos
⚠️ **Middleware** - Tests de autenticación con casos reales
⚠️ **Validators** - Tests de validadores personalizados

## Fixtures Disponibles

### Datos de Prueba
- `player_id`, `player_token` - IDs y tokens únicos
- `sample_player`, `new_player` - Jugadores de prueba
- `sample_player_stats` - Estadísticas de jugador
- `active_game`, `completed_game`, `new_game` - Partidas de prueba
- `sample_event`, `level_start_event` - Eventos de prueba

### Mocks
- `mock_firestore_client` - Cliente mock de Firestore
- `mock_db_session` - Sesión mock de SQL
- `mock_player_repository` - Repositorio mock de players
- `mock_game_repository` - Repositorio mock de games
- `mock_event_repository` - Repositorio mock de events

### Autenticación
- `admin_jwt_token` - Token JWT de admin válido
- `expired_jwt_token` - Token JWT expirado
- `api_key` - API Key válida
- `api_client` - Cliente de prueba de FastAPI
- `authenticated_api_client` - Cliente con JWT
- `player_api_client` - Cliente con player token

### Utilidades
- `assert_valid_uuid` - Validar que un string es UUID
- `assert_recent_timestamp` - Validar timestamp reciente
- `fixed_datetime`, `past_datetime`, `future_datetime` - Timestamps fijos

## Mejores Prácticas

### 1. Usa fixtures en lugar de crear datos manualmente
```python
# ✅ Bien
def test_create_player(sample_player):
    assert sample_player.username == "test_player"

# ❌ Mal
def test_create_player():
    player = Player(username="test", ...)
```

### 2. Marca los tests apropiadamente
```python
@pytest.mark.unit
@pytest.mark.edge_case
def test_games_completed_cannot_exceed_games_played():
    ...
```

### 3. Usa mocks para aislar dependencias
```python
def test_create_player(mock_player_repository):
    mock_player_repository.get_by_username.return_value = None
    # Test aislado sin tocar Firebase
```

### 4. Nombra tests descriptivamente
```python
# ✅ Bien
def test_moral_alignment_all_good_choices():
    ...

# ❌ Mal
def test_alignment():
    ...
```

### 5. Agrupa tests relacionados en clases
```python
@pytest.mark.unit
class TestPlayerStatsUpdate:
    def test_update_stats_completed_game(self):
        ...

    def test_update_stats_abandoned_game(self):
        ...
```

## Integración Continua (CI/CD)

Agrega esto a tu pipeline de CI:

```yaml
# .github/workflows/tests.yml
- name: Run tests with coverage
  run: |
    pytest --cov=app --cov-report=xml

- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

## Debugging Tests

### Ver print statements
```bash
pytest -s
```

### Detener en el primer fallo
```bash
pytest -x
```

### Ver traceback completo
```bash
pytest --tb=long
```

### Modo debugging interactivo
```bash
pytest --pdb
```

## Contribuir Nuevos Tests

Al agregar nuevos tests:

1. **Determina el tipo** - ¿Es unitario, integración o E2E?
2. **Usa fixtures existentes** - Revisa `conftest.py`
3. **Marca apropiadamente** - Usa `@pytest.mark.*`
4. **Cubre edge cases** - No solo happy paths
5. **Documenta casos complejos** - Agrega docstrings
6. **Verifica cobertura** - Debe mantenerse >70%

## Reportes de Cobertura

Después de ejecutar `pytest --cov`, se generan:

- **Terminal**: Reporte resumido con líneas faltantes
- **htmlcov/index.html**: Reporte HTML interactivo con código resaltado
- Líneas en rojo = no cubiertas
- Líneas en verde = cubiertas

## Troubleshooting

### Error: "Module not found"
```bash
# Asegúrate de estar en el directorio raíz
cd /path/to/Triskel-API
pytest
```

### Error: "No module named 'pytest'"
```bash
pip install pytest pytest-asyncio pytest-cov
```

### Tests muy lentos
```bash
# Ver los 10 tests más lentos
pytest --durations=10
```

### Firebase credential errors
Los mocks deberían evitar esto, pero si ocurre:
```bash
# Ejecuta solo tests que no requieren Firebase
pytest -m "not requires_firebase"
```

## Estadísticas Actuales

- **Total de tests**: ~80+ casos
- **Cobertura objetivo**: 70%+
- **Tiempo de ejecución**: <10 segundos (con mocks)
- **Dominios cubiertos**: Players, Games, Events, Auth

---

**¡Happy Testing! 🧪**

Los tests no solo verifican que el código funciona, sino que ayudan a:
- Detectar regresiones temprano
- Documentar comportamiento esperado
- Facilitar refactoring seguro
- Mejorar el diseño del código
