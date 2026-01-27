#!/usr/bin/env python3
"""
Script para generar 6 partidas de ejemplo usando la API REST.

Crea partidas con diferentes características:
- Tiempos de juego variados
- Diferentes muertes por nivel
- Niveles repetidos
- Diferentes decisiones morales
- Diferentes estados de completado

Uso:
    python scripts/generate_sample_games_api.py [--base-url URL]

Ejemplos:
    # Local
    python scripts/generate_sample_games_api.py --base-url http://localhost:8000

    # Producción
    python scripts/generate_sample_games_api.py --base-url https://triskel.up.railway.app
"""

import argparse
import sys
import time
from random import choice

import requests

# Configuración de niveles
LEVELS = ["senda_ebano", "fortaleza_gigantes", "aquelarre_sombras"]

CHOICES_OPTIONS = {
    "senda_ebano": ["forzar", "sanar"],
    "fortaleza_gigantes": ["destruir", "construir"],
    "aquelarre_sombras": ["ocultar", "revelar"],
}

RELICS = ["lirio", "hacha", "manto"]

DEATH_CAUSES = ["fall", "enemy", "trap", "boss"]


# Colores para output
class Colors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


def print_step(message: str, color: str = Colors.OKCYAN):
    """Imprime un paso del proceso con color"""
    print(f"{color}{Colors.BOLD}▸ {message}{Colors.ENDC}")


def print_success(message: str):
    """Imprime un mensaje de éxito"""
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")


def print_info(message: str):
    """Imprime información"""
    print(f"{Colors.OKBLUE}  {message}{Colors.ENDC}")


def print_error(message: str):
    """Imprime un mensaje de error"""
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")


def print_warning(message: str):
    """Imprime un mensaje de advertencia"""
    print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")


class TriskelAPIClient:
    """Cliente para interactuar con Triskel API"""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.player_id = None
        self.player_token = None

    def _request(self, method: str, endpoint: str, data: dict = None):
        """Realiza una petición HTTP a la API"""
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}

        if self.player_id and self.player_token:
            headers["X-Player-ID"] = self.player_id
            headers["X-Player-Token"] = self.player_token

        try:
            response = requests.request(
                method=method, url=url, headers=headers, json=data, timeout=60
            )

            if not response.ok:
                error_detail = response.json().get("detail", response.text)
                raise Exception(f"API Error {response.status_code}: {error_detail}")

            if not response.text:
                return {}

            return response.json()

        except requests.exceptions.RequestException as e:
            raise Exception(f"Error de conexión: {str(e)}")

    def create_player(self, username: str, password: str, email: str = None):
        """Crea un nuevo jugador"""
        data = {"username": username, "password": password}
        if email:
            data["email"] = email

        response = self._request("POST", "/v1/players", data)
        self.player_id = response["player_id"]
        self.player_token = response["player_token"]
        return response

    def login(self, username: str, password: str):
        """Login de jugador"""
        data = {"username": username, "password": password}
        response = self._request("POST", "/v1/players/login", data)
        self.player_id = response["player_id"]
        self.player_token = response["player_token"]
        return response

    def create_game(self):
        """Crea una nueva partida"""
        return self._request("POST", "/v1/games", {})

    def get_player_games(self, player_id: str):
        """Obtiene partidas de un jugador"""
        return self._request("GET", f"/v1/games/player/{player_id}")

    def get_game(self, game_id: str):
        """Obtiene una partida por ID"""
        return self._request("GET", f"/v1/games/{game_id}")

    def update_game(self, game_id: str, data: dict):
        """Actualiza una partida"""
        return self._request("PATCH", f"/v1/games/{game_id}", data)

    def start_level(self, game_id: str, level_name: str):
        """Inicia un nivel"""
        return self._request("POST", f"/v1/games/{game_id}/level/start", {"level": level_name})

    def complete_level(
        self, game_id: str, level_name: str, deaths: int, time_seconds: int, relic=None, choice=None
    ):
        """Completa un nivel"""
        data = {"level": level_name, "deaths": deaths, "time_seconds": time_seconds}
        if relic:
            data["relic"] = relic
        if choice:
            data["choice"] = choice
        return self._request("POST", f"/v1/games/{game_id}/level/complete", data)

    def complete_game(self, game_id: str):
        """Completa el juego"""
        return self._request("POST", f"/v1/games/{game_id}/complete", {})

    def create_events_batch(self, events: list):
        """Crea múltiples eventos en batch"""
        return self._request("POST", "/v1/events/batch", {"events": events})

    def create_event(self, game_id: str, event_type: str, level: str, data: dict = None):
        """Crea un evento individual"""
        event_data = {
            "game_id": game_id,
            "player_id": self.player_id,
            "event_type": event_type,
            "level": level,
        }
        if data:
            event_data["data"] = data
        return self._request("POST", "/v1/events", event_data)


def create_or_get_test_player(client: TriskelAPIClient):
    """Crea o obtiene un jugador de prueba"""
    username = "test_player_demo"
    password = "demo123"

    print_step("Buscando o creando jugador de prueba...")

    try:
        # Intentar login primero
        response = client.login(username, password)
        print_success(f"Jugador encontrado: {username} ({response['player_id']})")
        return response
    except Exception:
        # Si falla, crear nuevo
        print_info("Jugador no encontrado, creando nuevo...")
        response = client.create_player(username, password, f"{username}@test.com")
        print_success(f"Jugador creado: {username} ({response['player_id']})")
        return response


def cleanup_active_games(client: TriskelAPIClient):
    """Completa o elimina partidas activas del jugador"""
    print_step("Limpiando partidas activas existentes...")

    try:
        games = client.get_player_games(client.player_id)
        active_games = [g for g in games if g["status"] == "in_progress"]

        if not active_games:
            print_info("No hay partidas activas")
            return

        print_info(f"Encontradas {len(active_games)} partidas activas")

        for game in active_games:
            game_id = game["game_id"]
            try:
                # Intentar completar la partida
                client.complete_game(game_id)
                print_info(f"  ✓ Partida {game_id[:20]}... completada")
            except Exception:
                # Si no se puede completar, intentar eliminar (requiere admin)
                try:
                    # Actualizar a abandonada
                    client.update_game(game_id, {"status": "abandoned"})
                    print_info(f"  ✓ Partida {game_id[:20]}... marcada como abandonada")
                except Exception:
                    print_warning(f"  ✗ No se pudo modificar partida {game_id[:20]}...")

        print_success("Limpieza completada")

    except Exception as e:
        print_error(f"Error limpiando partidas: {e}")


def play_level_with_events(
    client: TriskelAPIClient, game_id: str, level_name: str, deaths: int, time_seconds: int, moral_choice=None, relic=None
):
    """Juega un nivel completo con eventos"""
    # Iniciar nivel
    client.start_level(game_id, level_name)

    # Crear eventos de muerte
    if deaths > 0:
        events = [
            {
                "game_id": game_id,
                "player_id": client.player_id,
                "event_type": "player_death",
                "level": level_name,
                "data": {"cause": choice(DEATH_CAUSES)},
            }
            for _ in range(deaths)
        ]
        client.create_events_batch(events)
        time.sleep(0.5)  # Delay para simular tiempo

    # Completar nivel
    client.complete_level(game_id, level_name, deaths, time_seconds, relic=relic, choice=moral_choice)
    time.sleep(0.3)  # Delay después de completar nivel


def scenario_1_speedrun(client: TriskelAPIClient):
    """
    Escenario 1: Speedrun exitoso
    - 3 niveles completados
    - Pocas muertes (3 total)
    - Tiempo: 15 minutos
    - Decisiones buenas
    """
    print_step("Creando escenario 1: Speedrun exitoso", Colors.HEADER)

    game = client.create_game()
    game_id = game["game_id"]

    # Nivel 1: senda_ebano (5 min, 1 muerte)
    play_level_with_events(client, game_id, "senda_ebano", 1, 300, moral_choice="sanar", relic="lirio")
    time.sleep(0.5)

    # Nivel 2: fortaleza_gigantes (6 min, 1 muerte)
    play_level_with_events(
        client, game_id, "fortaleza_gigantes", 1, 360, moral_choice="construir", relic="hacha"
    )
    time.sleep(0.5)

    # Nivel 3: aquelarre_sombras (4 min, 1 muerte)
    play_level_with_events(
        client, game_id, "aquelarre_sombras", 1, 240, moral_choice="revelar", relic="manto"
    )
    time.sleep(0.5)

    # Completar juego
    client.complete_game(game_id)

    print_success(f"Partida creada: {game_id} (15 min, 3 muertes)")
    return game_id


def scenario_2_difficult(client: TriskelAPIClient):
    """
    Escenario 2: Partida difícil completada
    - 3 niveles completados
    - Muchas muertes (24 total)
    - Tiempo: 45 minutos
    """
    print_step("Creando escenario 2: Partida difícil completada", Colors.HEADER)

    game = client.create_game()
    game_id = game["game_id"]

    # Nivel 1: senda_ebano (15 min, 8 muertes)
    play_level_with_events(client, game_id, "senda_ebano", 8, 900, moral_choice="forzar", relic="lirio")
    time.sleep(0.5)

    # Nivel 2: fortaleza_gigantes (20 min, 12 muertes)
    play_level_with_events(
        client, game_id, "fortaleza_gigantes", 12, 1200, moral_choice="construir", relic="hacha"
    )
    time.sleep(0.5)

    # Nivel 3: aquelarre_sombras (10 min, 4 muertes)
    play_level_with_events(client, game_id, "aquelarre_sombras", 4, 600, moral_choice="ocultar")
    time.sleep(0.5)

    # Completar juego
    client.complete_game(game_id)

    print_success(f"Partida creada: {game_id} (45 min, 24 muertes)")
    return game_id


def scenario_3_in_progress(client: TriskelAPIClient):
    """
    Escenario 3: Partida en progreso (nivel 2)
    - 1 nivel completado
    - Jugando el segundo nivel
    - 7 muertes totales
    """
    print_step("Creando escenario 3: Partida en progreso", Colors.HEADER)

    game = client.create_game()
    game_id = game["game_id"]

    # Nivel 1 completado (12 min, 3 muertes)
    play_level_with_events(client, game_id, "senda_ebano", 3, 720, moral_choice="sanar", relic="lirio")
    time.sleep(0.5)

    # Nivel 2 iniciado pero no completado (solo eventos de muerte)
    client.start_level(game_id, "fortaleza_gigantes")

    # Crear 4 eventos de muerte sin completar el nivel
    events = [
        {
            "game_id": game_id,
            "player_id": client.player_id,
            "event_type": "player_death",
            "level": "fortaleza_gigantes",
            "data": {"cause": choice(DEATH_CAUSES)},
        }
        for _ in range(4)
    ]
    client.create_events_batch(events)

    # Actualizar métricas manualmente ya que el nivel no está completado
    client.update_game(
        game_id,
        {
            "current_level": "fortaleza_gigantes",
            "total_time_seconds": 1200,  # 20 min total
        },
    )

    # Completar la partida para no bloquear las siguientes
    client.complete_game(game_id)

    print_success(f"Partida creada: {game_id} (en progreso, nivel 2)")
    return game_id


def scenario_4_abandoned(client: TriskelAPIClient):
    """
    Escenario 4: Partida abandonada
    - Solo primer nivel iniciado
    - Muchas muertes (15)
    - Nunca completado
    """
    print_step("Creando escenario 4: Partida abandonada", Colors.HEADER)

    game = client.create_game()
    game_id = game["game_id"]

    # Iniciar nivel pero no completarlo
    client.start_level(game_id, "senda_ebano")

    # Muchas muertes
    events = [
        {
            "game_id": game_id,
            "player_id": client.player_id,
            "event_type": "player_death",
            "level": "senda_ebano",
            "data": {"cause": choice(DEATH_CAUSES)},
        }
        for _ in range(15)
    ]
    client.create_events_batch(events)

    # Actualizar estado a abandonada
    client.update_game(
        game_id,
        {
            "status": "abandoned",
            "current_level": "senda_ebano",
            "total_time_seconds": 1800,  # 30 min
        },
    )

    print_success(f"Partida creada: {game_id} (abandonada, 15 muertes)")
    return game_id


def scenario_5_level_replay(client: TriskelAPIClient):
    """
    Escenario 5: Nivel repetido
    - Completó nivel 1 dos veces
    - En progreso en nivel 3
    """
    print_step("Creando escenario 5: Nivel repetido", Colors.HEADER)

    game = client.create_game()
    game_id = game["game_id"]

    # Primera pasada del nivel 1 (10 min, 3 muertes)
    play_level_with_events(client, game_id, "senda_ebano", 3, 600, moral_choice="sanar", relic="lirio")
    time.sleep(0.5)

    # Segunda pasada del nivel 1 (10 min, 2 muertes) - jugador volvió a jugarlo
    play_level_with_events(client, game_id, "senda_ebano", 2, 600, moral_choice="sanar")
    time.sleep(0.5)

    # Nivel 2 (15 min, 4 muertes)
    play_level_with_events(
        client, game_id, "fortaleza_gigantes", 4, 900, moral_choice="destruir", relic="hacha"
    )
    time.sleep(0.5)

    # Nivel 3 iniciado (2 muertes)
    client.start_level(game_id, "aquelarre_sombras")
    events = [
        {
            "game_id": game_id,
            "player_id": client.player_id,
            "event_type": "player_death",
            "level": "aquelarre_sombras",
            "data": {"cause": choice(DEATH_CAUSES)},
        }
        for _ in range(2)
    ]
    client.create_events_batch(events)

    client.update_game(
        game_id,
        {
            "current_level": "aquelarre_sombras",
            "total_time_seconds": 2400,  # 40 min
        },
    )

    # Completar la partida para no bloquear las siguientes
    client.complete_game(game_id)

    print_success(f"Partida creada: {game_id} (nivel repetido)")
    return game_id


def scenario_6_perfect(client: TriskelAPIClient):
    """
    Escenario 6: Partida perfecta (0 muertes)
    - 3 niveles completados
    - 0 muertes
    - Tiempo: 12 minutos
    """
    print_step("Creando escenario 6: Partida perfecta (0 muertes)", Colors.HEADER)

    game = client.create_game()
    game_id = game["game_id"]

    # Nivel 1 (4 min, 0 muertes)
    play_level_with_events(client, game_id, "senda_ebano", 0, 240, moral_choice="sanar", relic="lirio")
    time.sleep(0.5)

    # Nivel 2 (5 min, 0 muertes)
    play_level_with_events(
        client, game_id, "fortaleza_gigantes", 0, 300, moral_choice="construir", relic="hacha"
    )
    time.sleep(0.5)

    # Nivel 3 (3 min, 0 muertes)
    play_level_with_events(
        client, game_id, "aquelarre_sombras", 0, 180, moral_choice="revelar", relic="manto"
    )
    time.sleep(0.5)

    # Completar juego
    client.complete_game(game_id)

    print_success(f"Partida creada: {game_id} (12 min, 0 muertes - PERFECTO)")
    return game_id


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="Generar partidas de ejemplo via API")
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="URL base de la API (default: http://localhost:8000)",
    )

    args = parser.parse_args()

    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 60}")
    print("  TRISKEL - Generador de Partidas (API)")
    print(f"{'=' * 60}{Colors.ENDC}\n")

    print_step(f"Conectando a API: {args.base_url}")

    # Crear cliente
    client = TriskelAPIClient(args.base_url)

    # Verificar que la API esté disponible
    try:
        response = requests.get(f"{args.base_url}/health", timeout=10)
        if not response.ok:
            print_error("La API no está disponible")
            sys.exit(1)
        print_success("API disponible")
    except Exception as e:
        print_error(f"Error conectando a la API: {e}")
        sys.exit(1)

    # Crear o obtener jugador
    create_or_get_test_player(client)

    # Limpiar partidas activas
    cleanup_active_games(client)

    print(f"\n{Colors.HEADER}Generando 6 partidas con diferentes características...{Colors.ENDC}\n")

    # Crear las 6 partidas
    scenarios = [
        scenario_1_speedrun,
        scenario_2_difficult,
        scenario_3_in_progress,
        scenario_4_abandoned,
        scenario_5_level_replay,
        scenario_6_perfect,
    ]

    game_ids = []

    for i, scenario_func in enumerate(scenarios, 1):
        print(f"\n{Colors.BOLD}[{i}/6]{Colors.ENDC}")
        try:
            game_id = scenario_func(client)
            game_ids.append(game_id)
            time.sleep(1)  # Pausa entre partidas
        except Exception as e:
            print_error(f"Error creando escenario {i}: {e}")
            # Intentar limpiar partidas activas si hubo error
            try:
                cleanup_active_games(client)
            except Exception:
                pass
            continue

    # Resumen final
    print(f"\n{Colors.OKGREEN}{Colors.BOLD}{'=' * 60}")
    print("  ✓ COMPLETADO")
    print(f"{'=' * 60}{Colors.ENDC}")
    print(f"\n{Colors.OKGREEN}Se crearon:{Colors.ENDC}")
    print(f"  • {len(game_ids)} partidas variadas")
    print("  • Jugador: test_player_demo")
    print(f"\n{Colors.OKCYAN}Puedes ver los resultados en:{Colors.ENDC}")
    print(f"  • Dashboard: {args.base_url}/web/")
    print(f"  • API Docs: {args.base_url}/docs")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}✗ Proceso interrumpido por el usuario{Colors.ENDC}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.FAIL}✗ Error: {e}{Colors.ENDC}\n")
        import traceback

        traceback.print_exc()
        sys.exit(1)
