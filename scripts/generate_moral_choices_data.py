#!/usr/bin/env python3
"""
Script para generar partidas con diferentes patrones de decisiones morales.

Crea partidas con:
- Jugador completamente bueno (todas decisiones buenas)
- Jugador completamente malo (todas decisiones malas)
- Jugador neutral (decisiones mixtas)
- Varios patrones intermedios

Uso:
    python scripts/generate_moral_choices_data.py [--base-url URL]
"""

import argparse
import sys
import time
from random import choice

import requests

# Decisiones por nivel
LEVEL_CHOICES = {
    "senda_ebano": {"good": "sanar", "bad": "forzar"},
    "fortaleza_gigantes": {"good": "construir", "bad": "destruir"},
    "aquelarre_sombras": {"good": "revelar", "bad": "ocultar"},
}

LEVELS = list(LEVEL_CHOICES.keys())
RELICS = ["lirio", "hacha", "manto"]
DEATH_CAUSES = ["fall", "enemy", "trap", "boss"]


# Colores
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
    print(f"{color}{Colors.BOLD}▸ {message}{Colors.ENDC}")


def print_success(message: str):
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")


def print_info(message: str):
    print(f"{Colors.OKBLUE}  {message}{Colors.ENDC}")


def print_error(message: str):
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")


class TriskelAPIClient:
    """Cliente simple para la API"""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.player_id = None
        self.player_token = None

    def _request(self, method: str, endpoint: str, data: dict = None):
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

            return response.json() if response.text else {}

        except requests.exceptions.RequestException as e:
            raise Exception(f"Error de conexión: {str(e)}")

    def create_player(self, username: str, password: str, email: str = None):
        data = {"username": username, "password": password}
        if email:
            data["email"] = email
        response = self._request("POST", "/v1/players", data)
        self.player_id = response["player_id"]
        self.player_token = response["player_token"]
        return response

    def login(self, username: str, password: str):
        data = {"username": username, "password": password}
        response = self._request("POST", "/v1/players/login", data)
        self.player_id = response["player_id"]
        self.player_token = response["player_token"]
        return response

    def create_game(self):
        return self._request("POST", "/v1/games", {})

    def start_level(self, game_id: str, level_name: str):
        return self._request("POST", f"/v1/games/{game_id}/level/start", {"level": level_name})

    def complete_level(
        self, game_id: str, level_name: str, deaths: int, time_seconds: int, relic=None, choice=None
    ):
        data = {"level": level_name, "deaths": deaths, "time_seconds": time_seconds}
        if relic:
            data["relic"] = relic
        if choice:
            data["choice"] = choice
        return self._request("POST", f"/v1/games/{game_id}/level/complete", data)

    def complete_game(self, game_id: str):
        return self._request("POST", f"/v1/games/{game_id}/complete", {})

    def create_events_batch(self, events: list):
        return self._request("POST", "/v1/events/batch", {"events": events})

    def get_player_games(self, player_id: str):
        return self._request("GET", f"/v1/games/player/{player_id}")


def create_player_with_username(client: TriskelAPIClient, username: str, password: str):
    """Crea o hace login de un jugador"""
    try:
        response = client.login(username, password)
        print_success(f"Jugador encontrado: {username}")
        return response
    except Exception:
        try:
            response = client.create_player(username, password, f"{username}@test.com")
            print_success(f"Jugador creado: {username}")
            return response
        except Exception as e:
            print_error(f"Error con jugador {username}: {e}")
            return None


def cleanup_active_games(client: TriskelAPIClient):
    """Completa partidas activas"""
    try:
        games = client.get_player_games(client.player_id)
        active_games = [g for g in games if g["status"] == "in_progress"]

        if active_games:
            print_info(f"Limpiando {len(active_games)} partidas activas...")
            for game in active_games:
                try:
                    client.complete_game(game["game_id"])
                except Exception:
                    pass
    except Exception:
        pass


def play_level_simple(
    client: TriskelAPIClient, game_id: str, level_name: str, deaths: int, time_seconds: int, moral_choice: str, relic=None
):
    """Juega un nivel con decisión moral"""
    client.start_level(game_id, level_name)

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
        time.sleep(0.3)

    client.complete_level(game_id, level_name, deaths, time_seconds, relic=relic, choice=moral_choice)
    time.sleep(0.3)


def create_game_with_pattern(client: TriskelAPIClient, pattern_name: str, decisions: dict):
    """
    Crea una partida con un patrón específico de decisiones.

    Args:
        pattern_name: Nombre del patrón (para logging)
        decisions: Dict con decisiones por nivel, ej: {"senda_ebano": "good", ...}
    """
    print_step(f"Creando partida: {pattern_name}", Colors.HEADER)

    game = client.create_game()
    game_id = game["game_id"]

    # Jugar los 3 niveles con las decisiones especificadas
    for i, level in enumerate(LEVELS):
        decision_type = decisions.get(level, "good")  # Por defecto buena
        moral_choice = LEVEL_CHOICES[level][decision_type]

        # Variar tiempo y muertes
        deaths = 1 if decision_type == "bad" else 0  # Malas decisiones = más muertes
        time_seconds = 300 + (i * 60)  # 5, 6, 7 minutos
        relic = RELICS[i] if i < len(RELICS) else None

        play_level_simple(client, game_id, level, deaths, time_seconds, moral_choice, relic)

    # Completar juego
    client.complete_game(game_id)

    print_success(f"Partida creada: {game_id} - {pattern_name}")
    return game_id


def main():
    parser = argparse.ArgumentParser(description="Generar partidas con decisiones morales variadas")
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="URL base de la API",
    )
    args = parser.parse_args()

    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 60}")
    print("  TRISKEL - Generador de Decisiones Morales")
    print(f"{'=' * 60}{Colors.ENDC}\n")

    # Verificar API
    try:
        response = requests.get(f"{args.base_url}/health", timeout=10)
        if not response.ok:
            print_error("La API no está disponible")
            sys.exit(1)
        print_success("API disponible")
    except Exception as e:
        print_error(f"Error conectando a la API: {e}")
        sys.exit(1)

    # Crear diferentes jugadores con diferentes perfiles morales
    players_patterns = [
        {
            "username": "hero_player",
            "password": "hero123",
            "games": [
                {
                    "name": "Héroe Puro - Todas buenas",
                    "decisions": {"senda_ebano": "good", "fortaleza_gigantes": "good", "aquelarre_sombras": "good"},
                },
                {
                    "name": "Héroe Puro - Todas buenas (2)",
                    "decisions": {"senda_ebano": "good", "fortaleza_gigantes": "good", "aquelarre_sombras": "good"},
                },
            ],
        },
        {
            "username": "villain_player",
            "password": "villain123",
            "games": [
                {
                    "name": "Villano Puro - Todas malas",
                    "decisions": {"senda_ebano": "bad", "fortaleza_gigantes": "bad", "aquelarre_sombras": "bad"},
                },
                {
                    "name": "Villano Puro - Todas malas (2)",
                    "decisions": {"senda_ebano": "bad", "fortaleza_gigantes": "bad", "aquelarre_sombras": "bad"},
                },
            ],
        },
        {
            "username": "neutral_player",
            "password": "neutral123",
            "games": [
                {
                    "name": "Neutral - Buena, Mala, Buena",
                    "decisions": {"senda_ebano": "good", "fortaleza_gigantes": "bad", "aquelarre_sombras": "good"},
                },
                {
                    "name": "Neutral - Mala, Buena, Mala",
                    "decisions": {"senda_ebano": "bad", "fortaleza_gigantes": "good", "aquelarre_sombras": "bad"},
                },
            ],
        },
        {
            "username": "redeemed_player",
            "password": "redeemed123",
            "games": [
                {
                    "name": "Redención - Mala, Mala, Buena",
                    "decisions": {"senda_ebano": "bad", "fortaleza_gigantes": "bad", "aquelarre_sombras": "good"},
                },
            ],
        },
        {
            "username": "fallen_player",
            "password": "fallen123",
            "games": [
                {
                    "name": "Caída - Buena, Buena, Mala",
                    "decisions": {"senda_ebano": "good", "fortaleza_gigantes": "good", "aquelarre_sombras": "bad"},
                },
            ],
        },
        {
            "username": "chaotic_player",
            "password": "chaotic123",
            "games": [
                {
                    "name": "Caótico 1 - Buena, Mala, Buena",
                    "decisions": {"senda_ebano": "good", "fortaleza_gigantes": "bad", "aquelarre_sombras": "good"},
                },
                {
                    "name": "Caótico 2 - Mala, Buena, Buena",
                    "decisions": {"senda_ebano": "bad", "fortaleza_gigantes": "good", "aquelarre_sombras": "good"},
                },
                {
                    "name": "Caótico 3 - Buena, Buena, Mala",
                    "decisions": {"senda_ebano": "good", "fortaleza_gigantes": "good", "aquelarre_sombras": "bad"},
                },
            ],
        },
    ]

    total_games = 0

    print(f"\n{Colors.HEADER}Creando jugadores con diferentes perfiles morales...{Colors.ENDC}\n")

    for player_pattern in players_patterns:
        print(f"\n{Colors.BOLD}▸▸▸ Jugador: {player_pattern['username']}{Colors.ENDC}")

        # Crear cliente y jugador
        client = TriskelAPIClient(args.base_url)
        player = create_player_with_username(
            client, player_pattern["username"], player_pattern["password"]
        )

        if not player:
            continue

        # Limpiar partidas activas
        cleanup_active_games(client)

        # Crear partidas con diferentes patrones
        for i, game_pattern in enumerate(player_pattern["games"], 1):
            print(f"\n  [{i}/{len(player_pattern['games'])}]")
            try:
                create_game_with_pattern(client, game_pattern["name"], game_pattern["decisions"])
                total_games += 1
                time.sleep(1)
            except Exception as e:
                print_error(f"Error: {e}")
                cleanup_active_games(client)

    # Resumen
    print(f"\n{Colors.OKGREEN}{Colors.BOLD}{'=' * 60}")
    print("  ✓ COMPLETADO")
    print(f"{'=' * 60}{Colors.ENDC}")
    print(f"\n{Colors.OKGREEN}Se crearon:{Colors.ENDC}")
    print(f"  • {total_games} partidas")
    print(f"  • {len(players_patterns)} jugadores con diferentes perfiles morales")
    print(f"\n{Colors.OKCYAN}Perfiles creados:{Colors.ENDC}")
    print("  • Héroe Puro (2 partidas - todas buenas)")
    print("  • Villano Puro (2 partidas - todas malas)")
    print("  • Neutral (2 partidas - mixtas equilibradas)")
    print("  • Redención (1 partida - de malo a bueno)")
    print("  • Caída (1 partida - de bueno a malo)")
    print("  • Caótico (3 partidas - patrones variados)")
    print(f"\n{Colors.OKCYAN}Puedes ver los resultados en:{Colors.ENDC}")
    print(f"  • Dashboard Decisiones: {args.base_url}/web/dashboard/choices")
    print(f"  • Dashboard General: {args.base_url}/web/")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}✗ Proceso interrumpido{Colors.ENDC}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.FAIL}✗ Error: {e}{Colors.ENDC}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
