# Scripts de Testing - Triskel API

Scripts para probar todos los endpoints de la API de forma automatizada.

## Scripts Disponibles

### `test_api_complete.py`

Script principal de testing que prueba todos los endpoints y funcionalidades:

1. ✅ **Autenticación**
   - Crear usuario (registro con username + password)
   - Login con validación de credenciales
   - Obtener perfil del jugador

2. ✅ **Partidas**
   - Crear partida
   - Iniciar niveles
   - Completar niveles con decisiones morales y reliquias
   - Guardar progreso
   - Completar juego

3. ✅ **Eventos**
   - Crear eventos individuales
   - Crear eventos en batch
   - Obtener eventos de partida
   - Filtrar eventos por tipo

4. ✅ **Estadísticas**
   - Verificar estadísticas del jugador
   - Calcular alineación moral
   - Verificar reliquias y speedruns

### `run_tests.sh`

Script auxiliar de bash para ejecutar tests fácilmente.

## Uso

### Opción 1: Script Python directo

```bash
# Producción (Railway)
python3 scripts/test_api_complete.py --base-url https://triskel.up.railway.app

# Local
python3 scripts/test_api_complete.py --base-url http://localhost:8000

# Sin limpiar datos de prueba
python3 scripts/test_api_complete.py --no-cleanup
```

### Opción 2: Script bash (más fácil)

```bash
# Producción (default)
./scripts/run_tests.sh

# O explícitamente:
./scripts/run_tests.sh prod

# Local
./scripts/run_tests.sh local

# Sin cleanup
./scripts/run_tests.sh --no-cleanup

# Ver ayuda
./scripts/run_tests.sh --help
```

## Requisitos

```bash
pip install requests
```

## Salida Esperada

El script ejecuta todos los tests en orden y muestra:

- ✅ Estado de cada test (PASS/FAIL)
- 📊 Información detallada de cada operación
- 📈 Resumen final de resultados
- 🔑 Credenciales de prueba generadas

### Ejemplo de salida:

```
======================================================================
                   TRISKEL API - TEST COMPLETO
======================================================================

[PASO 0] Verificando disponibilidad de la API...
✓ API disponible en https://triskel.up.railway.app

[PASO 1] Creando jugador: test_user_1737400123
✓ Jugador creado exitosamente
  player_id: 550e8400-e29b-41d4-a716-446655440000
  username: test_user_1737400123
  player_token: 7c9e6679-7425-40de...

[PASO 2] Haciendo login: test_user_1737400123
✓ Login exitoso
  player_id: 550e8400-e29b-41d4-a716-446655440000
  username: test_user_1737400123
  active_game_id: None

[PASO 3] Obteniendo perfil del jugador...
✓ Perfil obtenido
  username: test_user_1737400123
  email: test_user_1737400123@test.com
  games_played: 0
  games_completed: 0

[PASO 4] Creando nueva partida...
✓ Partida creada
  game_id: game-abc-123
  current_level: hub_central
  status: in_progress

...

======================================================================
                      RESUMEN DE RESULTADOS
======================================================================

  [✓ PASS] Crear jugador
  [✓ PASS] Login
  [✓ PASS] Obtener perfil
  [✓ PASS] Crear partida
  [✓ PASS] Nivel: hub_central
  [✓ PASS] Nivel: senda_ebano
  [✓ PASS] Nivel: fortaleza_gigantes
  [✓ PASS] Guardar progreso
  [✓ PASS] Nivel: aquelarre_sombras
  [✓ PASS] Nivel: claro_almas
  [✓ PASS] Obtener eventos
  [✓ PASS] Completar juego
  [✓ PASS] Estadísticas finales
  [✓ PASS] Eliminar partida

Resultado: 14/14 tests pasaron

======================================================================
                    CREDENCIALES DE PRUEBA
======================================================================

  Username: test_user_1737400123
  Password: test_password_123
  Player ID: 550e8400-e29b-41d4-a716-446655440000
  Player Token: 7c9e6679-7425-40de...
  ⚠ Puedes usar estas credenciales para probar manualmente
```

## Tests Incluidos

| # | Test                    | Endpoint                              | Descripción                          |
|---|-------------------------|---------------------------------------|--------------------------------------|
| 0 | Health Check            | GET /health                           | Verifica disponibilidad de la API    |
| 1 | Crear jugador           | POST /v1/players                      | Registro con username + password     |
| 2 | Login                   | POST /v1/players/login                | Login con validación                 |
| 3 | Obtener perfil          | GET /v1/players/me                    | Perfil del jugador autenticado       |
| 4 | Crear partida           | POST /v1/games                        | Nueva partida                        |
| 5 | Jugar nivel             | POST /v1/games/{id}/level/start       | Iniciar nivel                        |
|   |                         | POST /v1/games/{id}/level/complete    | Completar nivel                      |
| 6 | Guardar progreso        | PATCH /v1/games/{id}                  | Actualizar partida                   |
| 7 | Obtener eventos         | GET /v1/events/game/{id}              | Eventos de la partida                |
| 8 | Completar juego         | POST /v1/games/{id}/complete          | Finalizar juego                      |
| 9 | Estadísticas finales    | GET /v1/players/me                    | Verificar stats actualizadas         |
| 10| Eliminar partida        | DELETE /v1/games/{id}                 | Cleanup (opcional)                   |

## Niveles Jugados

El script juega los 5 niveles del juego en orden:

1. **hub_central** - Sin decisión moral ni reliquia
2. **senda_ebano** - Decisión: "sanar" (buena), Reliquia: "lirio"
3. **fortaleza_gigantes** - Decisión: "construir" (buena), Reliquia: "hacha"
4. **aquelarre_sombras** - Decisión: "revelar" (buena), Reliquia: "manto"
5. **claro_almas** - Sin decisión moral ni reliquia (final)

Al completar el juego con 3 decisiones buenas:
- Alineación moral: 1.0 (completamente bueno)
- Final alcanzado: 1 (redención)

## Eventos Generados

Durante cada nivel, el script genera automáticamente:

- **player_death** - Número aleatorio de muertes (0-5) por nivel
- **level_complete** - Al completar cada nivel
- Eventos en batch para mejor rendimiento

## Notas

- El script genera un username único basado en timestamp
- La contraseña de prueba es `test_password_123` (17 caracteres, dentro del límite de 72)
- Todas las credenciales se muestran al final para debugging manual
- Con `--no-cleanup`, los datos quedan en la BD para inspección
- El script valida respuestas HTTP y maneja errores correctamente
- Salida colorizada para mejor visualización

**IMPORTANTE**: Asegúrate de que la API en el servidor tenga los últimos cambios desplegados antes de ejecutar los tests. Si ves errores relacionados con contraseñas, verifica que el código en producción esté actualizado.

## Depuración

Si algún test falla:

1. Verifica que la API esté corriendo:
   ```bash
   curl https://triskel.up.railway.app/health
   ```

2. Ejecuta sin cleanup para inspeccionar datos:
   ```bash
   ./scripts/run_tests.sh --no-cleanup
   ```

3. Usa las credenciales mostradas para probar manualmente:
   ```bash
   curl -X POST https://triskel.up.railway.app/v1/players/login \
     -H "Content-Type: application/json" \
     -d '{"username":"test_user_1737400123","password":"test_password_123"}'
   ```

## Integración Continua

Para usar en CI/CD:

```bash
# Ejecutar tests y fallar si alguno falla
./scripts/run_tests.sh || exit 1
```

El script retorna código de salida 0 si todos los tests pasan, 1 si alguno falla.
