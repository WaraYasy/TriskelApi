#!/usr/bin/env python3
"""
Script de testing completo para Triskel API

Prueba todos los endpoints y funcionalidades:
1. Crear usuario (registro con username + password)
2. Login (autenticación)
3. Obtener perfil
4. Crear partida
5. Iniciar/terminar sesiones (Windows y Android)
6. Jugar niveles completos
7. Crear eventos
8. Obtener sesiones del jugador y de la partida
9. Completar juego
10. Verificar estadísticas

Uso:
    python scripts/test_api_complete.py [--base-url URL] [--no-cleanup]

Ejemplos:
    # Producción
    python scripts/test_api_complete.py --base-url https://triskel.up.railway.app

    # Local
    python scripts/test_api_complete.py --base-url http://localhost:8000

    # Sin limpiar datos
    python scripts/test_api_complete.py --no-cleanup
"""

import argparse
import random
import sys
import time
from dataclasses import dataclass
from typing import Any, Optional

import requests

# URL por defecto (producción)
DEFAULT_BASE_URL = "https://triskel.up.railway.app"


# ============================================================================
# COLORES PARA TERMINAL
# ============================================================================


class Colors:
    """Códigos ANSI para colores en terminal"""

    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def print_header(text: str):
    """Imprime un header destacado"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(70)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}\n")


def print_step(step: int, text: str):
    """Imprime un paso del test"""
    print(f"{Colors.CYAN}{Colors.BOLD}[PASO {step}]{Colors.ENDC} {text}")


def print_success(text: str):
    """Imprime mensaje de éxito"""
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")


def print_error(text: str):
    """Imprime mensaje de error"""
    print(f"{Colors.RED}✗ {text}{Colors.ENDC}")


def print_warning(text: str):
    """Imprime mensaje de advertencia"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.ENDC}")


def print_info(text: str):
    """Imprime información"""
    print(f"{Colors.BLUE}  {text}{Colors.ENDC}")


# ============================================================================
# EXCEPCIONES
# ============================================================================


class APIError(Exception):
    """Error al llamar a la API"""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"API Error {status_code}: {detail}")


# ============================================================================
# CLIENTE API
# ============================================================================


@dataclass
class PlayerCredentials:
    """Credenciales del jugador autenticado"""

    player_id: str
    username: str
    player_token: str
    active_game_id: Optional[str] = None


class TriskelAPIClient:
    """Cliente para interactuar con Triskel API"""

    def __init__(self, base_url: str):
        """
        Inicializa el cliente.

        Args:
            base_url: URL base de la API (ej: http://localhost:8000)
        """
        self.base_url = base_url.rstrip("/")
        self.credentials: Optional[PlayerCredentials] = None

    def _request(
        self, method: str, endpoint: str, data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Realiza una petición HTTP a la API.

        Args:
            method: Método HTTP (GET, POST, PATCH, DELETE)
            endpoint: Endpoint (ej: /v1/players)
            data: Datos a enviar en el body (opcional)

        Returns:
            Respuesta JSON de la API

        Raises:
            APIError: Si la petición falla
        """
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}

        # Agregar headers de autenticación si hay credenciales
        if self.credentials:
            headers["X-Player-ID"] = self.credentials.player_id
            headers["X-Player-Token"] = self.credentials.player_token

        try:
            response = requests.request(
                method=method, url=url, headers=headers, json=data, timeout=30
            )

            # Si la respuesta no es exitosa, lanzar error
            if not response.ok:
                error_detail = response.json().get("detail", response.text)
                raise APIError(response.status_code, error_detail)

            # Manejar respuestas vacías
            if not response.text:
                return {}

            return response.json()

        except requests.exceptions.RequestException as e:
            raise APIError(0, f"Error de conexión: {str(e)}")

    # ========== PLAYERS ==========

    def create_player(
        self, username: str, password: str, email: str | None = None
    ) -> PlayerCredentials:
        """
        Crea un nuevo jugador (registro).

        Args:
            username: Nombre de usuario
            password: Contraseña
            email: Email opcional

        Returns:
            PlayerCredentials con las credenciales del jugador
        """
        data = {"username": username, "password": password}
        if email:
            data["email"] = email

        response = self._request("POST", "/v1/players", data)

        self.credentials = PlayerCredentials(
            player_id=response["player_id"],
            username=response["username"],
            player_token=response["player_token"],
            active_game_id=None,
        )
        return self.credentials

    def login(self, username: str, password: str) -> PlayerCredentials:
        """
        Login de jugador.

        Args:
            username: Nombre de usuario
            password: Contraseña

        Returns:
            PlayerCredentials con las credenciales del jugador
        """
        data = {"username": username, "password": password}
        response = self._request("POST", "/v1/players/login", data)

        self.credentials = PlayerCredentials(
            player_id=response["player_id"],
            username=response["username"],
            player_token=response["player_token"],
            active_game_id=response.get("active_game_id"),
        )
        return self.credentials

    def get_my_profile(self) -> dict[str, Any]:
        """Obtiene el perfil del jugador autenticado"""
        return self._request("GET", "/v1/players/me")

    def update_player(self, player_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Actualiza un jugador"""
        return self._request("PATCH", f"/v1/players/{player_id}", data)

    def delete_player(self, player_id: str) -> dict[str, Any]:
        """Elimina un jugador"""
        return self._request("DELETE", f"/v1/players/{player_id}")

    # ========== GAMES ==========

    def create_game(self) -> dict[str, Any]:
        """Crea una nueva partida"""
        return self._request("POST", "/v1/games", {})

    def get_game(self, game_id: str) -> dict[str, Any]:
        """Obtiene una partida por ID"""
        return self._request("GET", f"/v1/games/{game_id}")

    def update_game(self, game_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Actualiza una partida"""
        return self._request("PATCH", f"/v1/games/{game_id}", data)

    def start_level(self, game_id: str, level_name: str) -> dict[str, Any]:
        """Inicia un nivel"""
        return self._request("POST", f"/v1/games/{game_id}/level/start", {"level": level_name})

    def complete_level(
        self,
        game_id: str,
        level_name: str,
        deaths: int,
        time_seconds: int = 120,
        relic: str | None = None,
        choice: str | None = None,
    ) -> dict[str, Any]:
        """Completa un nivel"""
        data = {"level": level_name, "deaths": deaths, "time_seconds": time_seconds}
        if relic:
            data["relic"] = relic
        if choice:
            data["choice"] = choice
        return self._request("POST", f"/v1/games/{game_id}/level/complete", data)

    def complete_game(self, game_id: str) -> dict[str, Any]:
        """Completa el juego"""
        return self._request("POST", f"/v1/games/{game_id}/complete", {})

    def delete_game(self, game_id: str) -> dict[str, Any]:
        """Elimina una partida"""
        return self._request("DELETE", f"/v1/games/{game_id}")

    # ========== EVENTS ==========

    def create_event(
        self,
        game_id: str,
        event_type: str,
        level: str | None = None,
        metadata: dict | None = None,
    ) -> dict[str, Any]:
        """Crea un evento"""
        data = {
            "game_id": game_id,
            "player_id": self.credentials.player_id,
            "event_type": event_type,
        }
        if level:
            data["level"] = level
        if metadata:
            data["metadata"] = metadata
        return self._request("POST", "/v1/events", data)

    def create_events_batch(self, events: list[dict[str, Any]]) -> dict[str, Any]:
        """Crea múltiples eventos en batch"""
        return self._request("POST", "/v1/events/batch", {"events": events})

    def get_game_events(self, game_id: str, limit: int = 100) -> list[dict[str, Any]]:
        """Obtiene eventos de una partida"""
        return self._request("GET", f"/v1/events/game/{game_id}?limit={limit}")

    def get_game_events_by_type(
        self, game_id: str, event_type: str, limit: int = 100
    ) -> list[dict[str, Any]]:
        """Obtiene eventos de una partida filtrados por tipo"""
        return self._request("GET", f"/v1/events/game/{game_id}/type/{event_type}?limit={limit}")

    # ========== SESSIONS ==========

    def start_session(self, game_id: str, platform: str = "windows") -> dict[str, Any]:
        """Inicia una sesión de juego"""
        data = {"game_id": game_id, "platform": platform}
        return self._request("POST", "/v1/sessions", data)

    def end_session(self, session_id: str) -> dict[str, Any]:
        """Termina una sesión de juego"""
        return self._request("PATCH", f"/v1/sessions/{session_id}/end", {})

    def get_player_sessions(self, player_id: str, limit: int = 100) -> list[dict[str, Any]]:
        """Obtiene sesiones de un jugador"""
        return self._request("GET", f"/v1/sessions/player/{player_id}?limit={limit}")

    def get_game_sessions(self, game_id: str, limit: int = 100) -> list[dict[str, Any]]:
        """Obtiene sesiones de una partida"""
        return self._request("GET", f"/v1/sessions/game/{game_id}?limit={limit}")


# ============================================================================
# FUNCIONES DE TEST
# ============================================================================


def test_health_check(client: TriskelAPIClient) -> bool:
    """Prueba que la API esté disponible"""
    print_step(0, "Verificando disponibilidad de la API...")

    try:
        response = requests.get(f"{client.base_url}/health", timeout=10)
        if response.ok:
            print_success(f"API disponible en {client.base_url}")
            return True
        else:
            print_error(f"API no responde correctamente: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"No se puede conectar a la API: {e}")
        return False


def test_create_player(client: TriskelAPIClient, username: str, password: str) -> bool:
    """Prueba creación de jugador"""
    print_step(1, f"Creando jugador: {username}")

    try:
        credentials = client.create_player(username, password, f"{username}@test.com")

        print_success("Jugador creado exitosamente")
        print_info(f"player_id: {credentials.player_id}")
        print_info(f"username: {credentials.username}")
        print_info(f"player_token: {credentials.player_token[:20]}...")

        return True

    except APIError as e:
        print_error(f"Error creando jugador: {e.detail}")
        return False


def test_login(client: TriskelAPIClient, username: str, password: str) -> bool:
    """Prueba login de jugador"""
    print_step(2, f"Haciendo login: {username}")

    try:
        credentials = client.login(username, password)

        print_success("Login exitoso")
        print_info(f"player_id: {credentials.player_id}")
        print_info(f"username: {credentials.username}")
        print_info(f"active_game_id: {credentials.active_game_id or 'None'}")

        return True

    except APIError as e:
        print_error(f"Error en login: {e.detail}")
        return False


def test_get_profile(client: TriskelAPIClient) -> bool:
    """Prueba obtener perfil"""
    print_step(3, "Obteniendo perfil del jugador...")

    try:
        profile = client.get_my_profile()

        print_success("Perfil obtenido")
        print_info(f"username: {profile['username']}")
        print_info(f"email: {profile.get('email', 'N/A')}")
        print_info(f"games_played: {profile['games_played']}")
        print_info(f"games_completed: {profile['games_completed']}")

        return True

    except APIError as e:
        print_error(f"Error obteniendo perfil: {e}")
        return False


def test_create_game(client: TriskelAPIClient) -> str | None:
    """Prueba crear partida"""
    print_step(4, "Creando nueva partida...")

    try:
        game = client.create_game()

        print_success("Partida creada")
        print_info(f"game_id: {game['game_id']}")
        print_info(f"current_level: {game['current_level']}")
        print_info(f"status: {game['status']}")

        return game["game_id"]

    except APIError as e:
        print_error(f"Error creando partida: {e}")
        return None


def test_play_level(
    client: TriskelAPIClient,
    game_id: str,
    level_name: str,
    choice: str | None = None,
    relic: str | None = None,
) -> bool:
    """Prueba jugar un nivel completo"""
    print_step("▶", f"Jugando nivel: {level_name}")

    try:
        # 1. Iniciar nivel
        client.start_level(game_id, level_name)
        print_info(f"Nivel '{level_name}' iniciado")

        # 2. Simular muertes (eventos)
        deaths = random.randint(0, 5)
        if deaths > 0:
            # Incluir player_id en cada evento
            player_id = client.credentials.player_id
            events = [
                {
                    "game_id": game_id,
                    "player_id": player_id,
                    "event_type": "player_death",
                    "level": level_name,
                }
                for _ in range(deaths)
            ]
            client.create_events_batch(events)
            print_info(f"Muertes: {deaths}")

        # 3. Crear evento de nivel completado (level_end, no level_complete)
        client.create_event(game_id, "level_end", level_name)

        # 4. Completar nivel
        client.complete_level(game_id, level_name, deaths, relic=relic, choice=choice)
        print_success(f"Nivel '{level_name}' completado")

        if choice:
            print_info(f"Decisión moral: {choice}")
        if relic:
            print_info(f"Reliquia obtenida: {relic}")

        return True

    except APIError as e:
        print_error(f"Error jugando nivel: {e}")
        return False


def test_save_progress(client: TriskelAPIClient, game_id: str) -> bool:
    """Prueba guardar progreso"""
    print_step(5, "Guardando progreso de la partida...")

    try:
        # Simular tiempo jugado
        game = client.get_game(game_id)
        current_time = game.get("total_time_seconds", 0)
        new_time = current_time + random.randint(300, 600)

        updated_game = client.update_game(
            game_id,
            {"total_time_seconds": new_time, "current_level": game["current_level"]},
        )

        print_success("Progreso guardado")
        print_info(f"Tiempo total: {updated_game['total_time_seconds']}s")
        print_info(f"Nivel actual: {updated_game['current_level']}")

        return True

    except APIError as e:
        print_error(f"Error guardando progreso: {e}")
        return False


def test_get_events(client: TriskelAPIClient, game_id: str) -> bool:
    """Prueba obtener eventos"""
    print_step(6, "Obteniendo eventos de la partida...")

    try:
        events = client.get_game_events(game_id)

        print_success(f"Eventos obtenidos: {len(events)}")

        # Contar eventos por tipo
        event_counts = {}
        for event in events:
            event_type = event["event_type"]
            event_counts[event_type] = event_counts.get(event_type, 0) + 1

        for event_type, count in event_counts.items():
            print_info(f"  {event_type}: {count}")

        return True

    except APIError as e:
        print_error(f"Error obteniendo eventos: {e}")
        return False


def test_start_session(
    client: TriskelAPIClient, game_id: str, platform: str = "windows"
) -> str | None:
    """Prueba iniciar una sesión de juego"""
    print_step("🎮", f"Iniciando sesión de juego (platform: {platform})...")

    try:
        session = client.start_session(game_id, platform)

        print_success("Sesión iniciada")
        print_info(f"session_id: {session['session_id']}")
        print_info(f"platform: {session['platform']}")
        print_info(f"is_active: {session['is_active']}")

        return session["session_id"]

    except APIError as e:
        print_error(f"Error iniciando sesión: {e}")
        return None


def test_end_session(client: TriskelAPIClient, session_id: str) -> bool:
    """Prueba terminar una sesión de juego"""
    print_step("⏹️", "Terminando sesión de juego...")

    try:
        # Esperar un poco para que haya duración
        time.sleep(2)

        session = client.end_session(session_id)

        print_success("Sesión terminada")
        print_info(f"session_id: {session['session_id']}")
        print_info(f"duration_seconds: {session['duration_seconds']}s")
        print_info(f"is_active: {session['is_active']}")

        return True

    except APIError as e:
        print_error(f"Error terminando sesión: {e}")
        return False


def test_get_player_sessions(client: TriskelAPIClient, player_id: str) -> bool:
    """Prueba obtener sesiones de un jugador"""
    print_step("📊", "Obteniendo sesiones del jugador...")

    try:
        sessions = client.get_player_sessions(player_id)

        print_success(f"Sesiones del jugador obtenidas: {len(sessions)}")

        if sessions:
            for i, session in enumerate(sessions[:3], 1):  # Mostrar max 3
                print_info(
                    f"  Sesión {i}: {session['session_id'][:20]}... ({session['duration_seconds']}s)"
                )

        return True

    except APIError as e:
        print_error(f"Error obteniendo sesiones del jugador: {e}")
        return False


def test_get_game_sessions(client: TriskelAPIClient, game_id: str) -> bool:
    """Prueba obtener sesiones de una partida"""
    print_step("🎯", "Obteniendo sesiones de la partida...")

    try:
        sessions = client.get_game_sessions(game_id)

        print_success(f"Sesiones de la partida obtenidas: {len(sessions)}")

        # Contar sesiones activas vs cerradas
        active = sum(1 for s in sessions if s["is_active"])
        closed = len(sessions) - active

        print_info(f"  Sesiones activas: {active}")
        print_info(f"  Sesiones cerradas: {closed}")

        return True

    except APIError as e:
        print_error(f"Error obteniendo sesiones de la partida: {e}")
        return False


def test_complete_game(client: TriskelAPIClient, game_id: str) -> bool:
    """Prueba completar el juego"""
    print_step(7, "Completando el juego...")

    try:
        result = client.complete_game(game_id)

        print_success("Juego completado")
        print_info(f"status: {result['status']}")

        return True

    except APIError as e:
        print_error(f"Error completando juego: {e}")
        return False


def test_final_stats(client: TriskelAPIClient) -> bool:
    """Prueba obtener estadísticas finales"""
    print_step(8, "Verificando estadísticas finales...")

    try:
        profile = client.get_my_profile()
        stats = profile["stats"]

        print_success("Estadísticas obtenidas")
        print_info(f"Partidas jugadas: {profile['games_played']}")
        print_info(f"Partidas completadas: {profile['games_completed']}")
        print_info(f"Tiempo total: {profile['total_playtime_seconds']}s")
        print_info(f"Decisiones buenas: {stats['total_good_choices']}")
        print_info(f"Decisiones malas: {stats['total_bad_choices']}")
        print_info(f"Muertes totales: {stats['total_deaths']}")
        print_info(f"Alineación moral: {stats['moral_alignment']:.2f}")

        if stats["favorite_relic"]:
            print_info(f"Reliquia favorita: {stats['favorite_relic']}")
        if stats["best_speedrun_seconds"]:
            print_info(f"Mejor speedrun: {stats['best_speedrun_seconds']}s")

        return True

    except APIError as e:
        print_error(f"Error obteniendo estadísticas: {e}")
        return False


def test_delete_game(client: TriskelAPIClient, game_id: str) -> bool:
    """Prueba eliminar partida"""
    print_step(9, "Eliminando partida de prueba...")

    try:
        client.delete_game(game_id)
        print_success("Partida eliminada")
        return True

    except APIError as e:
        print_error(f"Error eliminando partida: {e}")
        return False


# ============================================================================
# MAIN
# ============================================================================


def run_full_test(base_url: str, cleanup: bool = True):
    """
    Ejecuta la suite completa de tests.

    Args:
        base_url: URL base de la API
        cleanup: Si True, elimina la partida al final
    """
    print_header("TRISKEL API - TEST COMPLETO")

    client = TriskelAPIClient(base_url)
    results = []
    game_id = None

    # Generar username aleatorio
    username = f"test_user_{int(time.time())}"
    password = "test_password_123"

    # 0. Health check
    if not test_health_check(client):
        print_error("La API no está disponible. Abortando tests.")
        return False

    # 1. Crear jugador
    results.append(("Crear jugador", test_create_player(client, username, password)))

    # 2. Login (probamos que funcione el login)
    results.append(("Login", test_login(client, username, password)))

    # 3. Obtener perfil
    results.append(("Obtener perfil", test_get_profile(client)))

    # 4. Crear partida
    game_id = test_create_game(client)
    results.append(("Crear partida", game_id is not None))

    if game_id:
        # 5. Iniciar sesión (Windows)
        session_id_1 = test_start_session(client, game_id, "windows")
        results.append(("Iniciar sesión (Windows)", session_id_1 is not None))

        # 6. Jugar niveles con sesión activa
        results.append(("Nivel: hub_central", test_play_level(client, game_id, "hub_central")))

        results.append(
            (
                "Nivel: senda_ebano",
                test_play_level(client, game_id, "senda_ebano", choice="sanar", relic="lirio"),
            )
        )

        # 7. Terminar primera sesión
        if session_id_1:
            results.append(("Terminar sesión (Windows)", test_end_session(client, session_id_1)))

        # 8. Iniciar segunda sesión (Android)
        session_id_2 = test_start_session(client, game_id, "android")
        results.append(("Iniciar sesión (Android)", session_id_2 is not None))

        # 9. Continuar jugando niveles
        results.append(
            (
                "Nivel: fortaleza_gigantes",
                test_play_level(
                    client,
                    game_id,
                    "fortaleza_gigantes",
                    choice="construir",
                    relic="hacha",
                ),
            )
        )

        # 10. Guardar progreso
        results.append(("Guardar progreso", test_save_progress(client, game_id)))

        # 11. Más niveles
        results.append(
            (
                "Nivel: aquelarre_sombras",
                test_play_level(
                    client,
                    game_id,
                    "aquelarre_sombras",
                    choice="revelar",
                    relic="manto",
                ),
            )
        )

        results.append(("Nivel: claro_almas", test_play_level(client, game_id, "claro_almas")))

        # 12. Obtener sesiones del jugador
        if client.credentials:
            results.append(
                (
                    "Obtener sesiones del jugador",
                    test_get_player_sessions(client, client.credentials.player_id),
                )
            )

        # 13. Obtener sesiones de la partida
        results.append(("Obtener sesiones de la partida", test_get_game_sessions(client, game_id)))

        # 14. Terminar segunda sesión
        if session_id_2:
            results.append(("Terminar sesión (Android)", test_end_session(client, session_id_2)))

        # 15. Obtener eventos
        results.append(("Obtener eventos", test_get_events(client, game_id)))

        # 16. Completar juego (final 1 = bueno)
        results.append(("Completar juego", test_complete_game(client, game_id)))

        # 17. Estadísticas finales
        results.append(("Estadísticas finales", test_final_stats(client)))

        # 18. Cleanup (opcional)
        if cleanup:
            results.append(("Eliminar partida", test_delete_game(client, game_id)))

    # Resumen
    print_header("RESUMEN DE RESULTADOS")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = (
            f"{Colors.GREEN}✓ PASS{Colors.ENDC}" if result else f"{Colors.RED}✗ FAIL{Colors.ENDC}"
        )
        print(f"  [{status}] {name}")

    print()
    color = Colors.GREEN if passed == total else Colors.RED
    print(f"{color}{Colors.BOLD}Resultado: {passed}/{total} tests pasaron{Colors.ENDC}")

    if client.credentials:
        print()
        print_header("CREDENCIALES DE PRUEBA")
        print_info(f"Username: {username}")
        print_info(f"Password: {password}")
        print_info(f"Player ID: {client.credentials.player_id}")
        print_info(f"Player Token: {client.credentials.player_token[:20]}...")
        print_warning("Puedes usar estas credenciales para probar manualmente")

    return passed == total


def main():
    parser = argparse.ArgumentParser(description="Test completo de Triskel API")
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"URL base de la API (default: {DEFAULT_BASE_URL})",
    )
    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="No eliminar la partida de prueba al final",
    )

    args = parser.parse_args()

    success = run_full_test(args.base_url, cleanup=not args.no_cleanup)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
