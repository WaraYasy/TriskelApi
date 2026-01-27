
#!/usr/bin/env py
# hon3
"""
Script para generar 6 partidas de ejemplo con datos variados.

Crea partidas con diferentes características:
- Tiempos de juego variados
- Diferentes muertes por nivel
- Niveles repetidos
- Diferentes decisiones morales
- Diferentes estados de completado
"""

import os
import sys
import time
from datetime import datetime, timedelta
from random import choice

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.domain.events.models import GameEvent
from app.domain.games.models import Game, GameChoices, GameMetrics
from app.domain.players.models import Player
from app.domain.players.service import hash_password
from app.infrastructure.database.firebase_client import get_firestore_client

# Configuración de niveles
LEVELS = [
    "senda_ebano",
    "fortaleza_gigantes",
    "aquelarre_sombras"
]

CHOICES_OPTIONS = {
    "senda_ebano": ["forzar", "sanar"],
    "fortaleza_gigantes": ["destruir", "construir"],
    "aquelarre_sombras": ["ocultar", "revelar"]
}

RELICS = ["lirio", "hacha", "manto"]

DEATH_CAUSES = ["fall", "enemy", "trap", "boss"]

# Colores para output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_step(message: str, color: str = Colors.OKCYAN):
    """Imprime un paso del proceso con color"""
    print(f"{color}{Colors.BOLD}▸ {message}{Colors.ENDC}")


def print_success(message: str):
    """Imprime un mensaje de éxito"""
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")


def print_info(message: str):
    """Imprime información"""
    print(f"{Colors.OKBLUE}  {message}{Colors.ENDC}")


def create_or_get_test_player(db) -> Player:
    """Crea o obtiene un jugador de prueba"""
    print_step("Buscando jugador de prueba...")

    # Buscar jugador existente
    players_ref = db.collection("players")
    query = players_ref.where("username", "==", "test_player_demo").limit(1)
    docs = list(query.stream())

    if docs:
        player_data = docs[0].to_dict()
        player = Player.from_dict(player_data)
        print_success(f"Jugador encontrado: {player.username} ({player.player_id})")
        return player

    # Crear nuevo jugador
    print_step("Creando jugador de prueba...")
    player = Player(
        username="test_player_demo",
        email="demo@triskel.com",
        password_hash=hash_password("demo123")  # Password de demo
    )

    players_ref.document(player.player_id).set(player.to_dict())
    print_success(f"Jugador creado: {player.username} ({player.player_id})")

    return player


def create_game_scenario_1(player_id: str, db) -> tuple[Game, list[GameEvent]]:
    """
    Escenario 1: Partida completada rápida
    - 3 niveles completados
    - Pocas muertes
    - Tiempo total: ~15 minutos
    - Decisiones morales buenas
    """
    print_step("Creando escenario 1: Speedrun exitoso", Colors.HEADER)

    base_time = datetime.utcnow() - timedelta(hours=2)
    game = Game(
        player_id=player_id,
        status="completed",
        started_at=base_time,
        ended_at=base_time + timedelta(minutes=15),
        total_time_seconds=900,  # 15 minutos
        completion_percentage=100.0,
        levels_completed=LEVELS,
        boss_defeated=True,
        choices=GameChoices(
            senda_ebano="sanar",
            fortaleza_gigantes="construir",
            aquelarre_sombras="revelar"
        ),
        relics=RELICS,
        metrics=GameMetrics(
            total_deaths=3,
            time_per_level={
                "senda_ebano": 300,  # 5 min
                "fortaleza_gigantes": 360,  # 6 min
                "aquelarre_sombras": 240  # 4 min
            },
            deaths_per_level={
                "senda_ebano": 1,
                "fortaleza_gigantes": 1,
                "aquelarre_sombras": 1
            }
        )
    )

    events = []
    current_time = base_time

    for level in LEVELS:
        # Level start
        events.append(GameEvent(
            game_id=game.game_id,
            player_id=player_id,
            timestamp=current_time,
            event_type="level_start",
            level=level,
            data={"attempt": 1}
        ))

        # Una muerte por nivel
        current_time += timedelta(seconds=game.metrics.time_per_level[level] // 2)
        events.append(GameEvent(
            game_id=game.game_id,
            player_id=player_id,
            timestamp=current_time,
            event_type="player_death",
            level=level,
            data={"cause": choice(DEATH_CAUSES)}
        ))

        # Level complete
        current_time += timedelta(seconds=game.metrics.time_per_level[level] // 2)
        events.append(GameEvent(
            game_id=game.game_id,
            player_id=player_id,
            timestamp=current_time,
            event_type="level_end",
            level=level,
            data={
                "time_seconds": game.metrics.time_per_level[level],
                "deaths": 1,
                "choice": getattr(game.choices, level)
            }
        ))

        time.sleep(0.5)  # Delay visual

    print_success(f"Partida creada: {game.game_id} (15 min, 3 muertes)")
    return game, events


def create_game_scenario_2(player_id: str, db) -> tuple[Game, list[GameEvent]]:
    """
    Escenario 2: Partida completada con muchas muertes
    - 3 niveles completados
    - Muchas muertes (20+)
    - Tiempo total: ~45 minutos
    - Decisiones morales mixtas
    """
    print_step("Creando escenario 2: Partida difícil completada", Colors.HEADER)

    base_time = datetime.utcnow() - timedelta(hours=5)
    game = Game(
        player_id=player_id,
        status="completed",
        started_at=base_time,
        ended_at=base_time + timedelta(minutes=45),
        total_time_seconds=2700,  # 45 minutos
        completion_percentage=100.0,
        levels_completed=LEVELS,
        boss_defeated=True,
        choices=GameChoices(
            senda_ebano="forzar",
            fortaleza_gigantes="construir",
            aquelarre_sombras="ocultar"
        ),
        relics=["lirio", "hacha"],
        metrics=GameMetrics(
            total_deaths=24,
            time_per_level={
                "senda_ebano": 900,  # 15 min
                "fortaleza_gigantes": 1200,  # 20 min
                "aquelarre_sombras": 600  # 10 min
            },
            deaths_per_level={
                "senda_ebano": 8,
                "fortaleza_gigantes": 12,
                "aquelarre_sombras": 4
            }
        )
    )

    events = []
    current_time = base_time

    for level in LEVELS:
        deaths_in_level = game.metrics.deaths_per_level[level]
        level_time = game.metrics.time_per_level[level]

        # Level start
        events.append(GameEvent(
            game_id=game.game_id,
            player_id=player_id,
            timestamp=current_time,
            event_type="level_start",
            level=level,
            data={"attempt": 1}
        ))

        # Múltiples muertes
        time_per_death = level_time // (deaths_in_level + 1)
        for i in range(deaths_in_level):
            current_time += timedelta(seconds=time_per_death)
            events.append(GameEvent(
                game_id=game.game_id,
                player_id=player_id,
                timestamp=current_time,
                event_type="player_death",
                level=level,
                data={"cause": choice(DEATH_CAUSES)}
            ))
            time.sleep(0.1)  # Delay corto entre muertes

        # Level complete
        current_time += timedelta(seconds=time_per_death)
        events.append(GameEvent(
            game_id=game.game_id,
            player_id=player_id,
            timestamp=current_time,
            event_type="level_end",
            level=level,
            data={
                "time_seconds": level_time,
                "deaths": deaths_in_level,
                "choice": getattr(game.choices, level)
            }
        ))

        time.sleep(0.5)

    print_success(f"Partida creada: {game.game_id} (45 min, 24 muertes)")
    return game, events


def create_game_scenario_3(player_id: str, db) -> tuple[Game, list[GameEvent]]:
    """
    Escenario 3: Partida en progreso (segundo nivel)
    - 1 nivel completado, jugando el segundo
    - Muertes moderadas
    - Tiempo parcial
    """
    print_step("Creando escenario 3: Partida en progreso", Colors.HEADER)

    base_time = datetime.utcnow() - timedelta(minutes=30)
    game = Game(
        player_id=player_id,
        status="in_progress",
        started_at=base_time,
        total_time_seconds=1200,  # 20 minutos
        completion_percentage=50.0,
        levels_completed=["senda_ebano"],
        current_level="fortaleza_gigantes",
        choices=GameChoices(senda_ebano="sanar"),
        relics=["lirio"],
        metrics=GameMetrics(
            total_deaths=7,
            time_per_level={
                "senda_ebano": 720,  # 12 min
                "fortaleza_gigantes": 480  # 8 min (en progreso)
            },
            deaths_per_level={
                "senda_ebano": 3,
                "fortaleza_gigantes": 4
            }
        )
    )

    events = []
    current_time = base_time

    # Nivel 1 completado
    events.append(GameEvent(
        game_id=game.game_id,
        player_id=player_id,
        timestamp=current_time,
        event_type="level_start",
        level="senda_ebano",
        data={"attempt": 1}
    ))

    for i in range(3):
        current_time += timedelta(seconds=240)
        events.append(GameEvent(
            game_id=game.game_id,
            player_id=player_id,
            timestamp=current_time,
            event_type="player_death",
            level="senda_ebano",
            data={"cause": choice(DEATH_CAUSES)}
        ))
        time.sleep(0.2)

    events.append(GameEvent(
        game_id=game.game_id,
        player_id=player_id,
        timestamp=current_time,
        event_type="level_end",
        level="senda_ebano",
        data={"time_seconds": 720, "deaths": 3, "choice": "sanar"}
    ))

    # Nivel 2 en progreso
    current_time += timedelta(seconds=60)
    events.append(GameEvent(
        game_id=game.game_id,
        player_id=player_id,
        timestamp=current_time,
        event_type="level_start",
        level="fortaleza_gigantes",
        data={"attempt": 1}
    ))

    for i in range(4):
        current_time += timedelta(seconds=120)
        events.append(GameEvent(
            game_id=game.game_id,
            player_id=player_id,
            timestamp=current_time,
            event_type="player_death",
            level="fortaleza_gigantes",
            data={"cause": choice(DEATH_CAUSES)}
        ))
        time.sleep(0.2)

    print_success(f"Partida creada: {game.game_id} (en progreso, nivel 2)")
    return game, events


def create_game_scenario_4(player_id: str, db) -> tuple[Game, list[GameEvent]]:
    """
    Escenario 4: Partida abandonada en primer nivel
    - Solo primer nivel
    - Muchas muertes, frustración
    - Nunca completado
    """
    print_step("Creando escenario 4: Partida abandonada", Colors.HEADER)

    base_time = datetime.utcnow() - timedelta(days=1)
    game = Game(
        player_id=player_id,
        status="abandoned",
        started_at=base_time,
        total_time_seconds=1800,  # 30 minutos
        completion_percentage=15.0,
        levels_completed=[],
        current_level="senda_ebano",
        metrics=GameMetrics(
            total_deaths=15,
            time_per_level={"senda_ebano": 1800},
            deaths_per_level={"senda_ebano": 15}
        )
    )

    events = []
    current_time = base_time

    events.append(GameEvent(
        game_id=game.game_id,
        player_id=player_id,
        timestamp=current_time,
        event_type="level_start",
        level="senda_ebano",
        data={"attempt": 1}
    ))

    # Muchas muertes seguidas
    for i in range(15):
        current_time += timedelta(seconds=120)
        events.append(GameEvent(
            game_id=game.game_id,
            player_id=player_id,
            timestamp=current_time,
            event_type="player_death",
            level="senda_ebano",
            data={"cause": choice(DEATH_CAUSES)}
        ))
        time.sleep(0.15)

    print_success(f"Partida creada: {game.game_id} (abandonada, 15 muertes)")
    return game, events


def create_game_scenario_5(player_id: str, db) -> tuple[Game, list[GameEvent]]:
    """
    Escenario 5: Partida con nivel repetido
    - Completó nivel 1, volvió a jugarlo
    - Decisiones diferentes en segunda pasada
    """
    print_step("Creando escenario 5: Nivel repetido", Colors.HEADER)

    base_time = datetime.utcnow() - timedelta(hours=8)
    game = Game(
        player_id=player_id,
        status="in_progress",
        started_at=base_time,
        total_time_seconds=2400,  # 40 minutos
        completion_percentage=66.0,
        levels_completed=["senda_ebano", "fortaleza_gigantes"],
        current_level="aquelarre_sombras",
        choices=GameChoices(
            senda_ebano="sanar",
            fortaleza_gigantes="destruir"
        ),
        relics=["lirio"],
        metrics=GameMetrics(
            total_deaths=11,
            time_per_level={
                "senda_ebano": 1200,  # Jugado 2 veces
                "fortaleza_gigantes": 900,
                "aquelarre_sombras": 300
            },
            deaths_per_level={
                "senda_ebano": 5,
                "fortaleza_gigantes": 4,
                "aquelarre_sombras": 2
            }
        )
    )

    events = []
    current_time = base_time

    # Primera pasada del nivel 1
    events.append(GameEvent(
        game_id=game.game_id,
        player_id=player_id,
        timestamp=current_time,
        event_type="level_start",
        level="senda_ebano",
        data={"attempt": 1}
    ))

    for i in range(3):
        current_time += timedelta(seconds=120)
        events.append(GameEvent(
            game_id=game.game_id,
            player_id=player_id,
            timestamp=current_time,
            event_type="player_death",
            level="senda_ebano",
            data={"cause": choice(DEATH_CAUSES)}
        ))
        time.sleep(0.15)

    current_time += timedelta(seconds=120)
    events.append(GameEvent(
        game_id=game.game_id,
        player_id=player_id,
        timestamp=current_time,
        event_type="level_end",
        level="senda_ebano",
        data={"time_seconds": 600, "deaths": 3, "choice": "sanar"}
    ))

    # Segunda pasada del nivel 1 (repetido)
    current_time += timedelta(seconds=180)
    events.append(GameEvent(
        game_id=game.game_id,
        player_id=player_id,
        timestamp=current_time,
        event_type="level_start",
        level="senda_ebano",
        data={"attempt": 2, "reason": "replay"}
    ))

    for i in range(2):
        current_time += timedelta(seconds=150)
        events.append(GameEvent(
            game_id=game.game_id,
            player_id=player_id,
            timestamp=current_time,
            event_type="player_death",
            level="senda_ebano",
            data={"cause": choice(DEATH_CAUSES)}
        ))
        time.sleep(0.15)

    current_time += timedelta(seconds=150)
    events.append(GameEvent(
        game_id=game.game_id,
        player_id=player_id,
        timestamp=current_time,
        event_type="level_end",
        level="senda_ebano",
        data={"time_seconds": 600, "deaths": 2, "choice": "sanar"}
    ))

    # Nivel 2
    current_time += timedelta(seconds=120)
    events.append(GameEvent(
        game_id=game.game_id,
        player_id=player_id,
        timestamp=current_time,
        event_type="level_start",
        level="fortaleza_gigantes",
        data={"attempt": 1}
    ))

    for i in range(4):
        current_time += timedelta(seconds=180)
        events.append(GameEvent(
            game_id=game.game_id,
            player_id=player_id,
            timestamp=current_time,
            event_type="player_death",
            level="fortaleza_gigantes",
            data={"cause": choice(DEATH_CAUSES)}
        ))
        time.sleep(0.15)

    current_time += timedelta(seconds=180)
    events.append(GameEvent(
        game_id=game.game_id,
        player_id=player_id,
        timestamp=current_time,
        event_type="level_end",
        level="fortaleza_gigantes",
        data={"time_seconds": 900, "deaths": 4, "choice": "destruir"}
    ))

    # Nivel 3 en progreso
    current_time += timedelta(seconds=60)
    events.append(GameEvent(
        game_id=game.game_id,
        player_id=player_id,
        timestamp=current_time,
        event_type="level_start",
        level="aquelarre_sombras",
        data={"attempt": 1}
    ))

    for i in range(2):
        current_time += timedelta(seconds=150)
        events.append(GameEvent(
            game_id=game.game_id,
            player_id=player_id,
            timestamp=current_time,
            event_type="player_death",
            level="aquelarre_sombras",
            data={"cause": choice(DEATH_CAUSES)}
        ))
        time.sleep(0.15)

    print_success(f"Partida creada: {game.game_id} (nivel repetido)")
    return game, events


def create_game_scenario_6(player_id: str, db) -> tuple[Game, list[GameEvent]]:
    """
    Escenario 6: Partida perfecta sin muertes
    - 3 niveles completados
    - 0 muertes
    - Tiempo óptimo: ~12 minutos
    - Todas las decisiones buenas
    """
    print_step("Creando escenario 6: Partida perfecta (0 muertes)", Colors.HEADER)

    base_time = datetime.utcnow() - timedelta(hours=12)
    game = Game(
        player_id=player_id,
        status="completed",
        started_at=base_time,
        ended_at=base_time + timedelta(minutes=12),
        total_time_seconds=720,  # 12 minutos
        completion_percentage=100.0,
        levels_completed=LEVELS,
        boss_defeated=True,
        choices=GameChoices(
            senda_ebano="sanar",
            fortaleza_gigantes="construir",
            aquelarre_sombras="revelar"
        ),
        relics=RELICS,
        metrics=GameMetrics(
            total_deaths=0,
            time_per_level={
                "senda_ebano": 240,  # 4 min
                "fortaleza_gigantes": 300,  # 5 min
                "aquelarre_sombras": 180  # 3 min
            },
            deaths_per_level={
                "senda_ebano": 0,
                "fortaleza_gigantes": 0,
                "aquelarre_sombras": 0
            }
        )
    )

    events = []
    current_time = base_time

    for level in LEVELS:
        # Level start
        events.append(GameEvent(
            game_id=game.game_id,
            player_id=player_id,
            timestamp=current_time,
            event_type="level_start",
            level=level,
            data={"attempt": 1}
        ))

        # No deaths, directo a complete
        current_time += timedelta(seconds=game.metrics.time_per_level[level])
        events.append(GameEvent(
            game_id=game.game_id,
            player_id=player_id,
            timestamp=current_time,
            event_type="level_end",
            level=level,
            data={
                "time_seconds": game.metrics.time_per_level[level],
                "deaths": 0,
                "choice": getattr(game.choices, level),
                "perfect": True
            }
        ))

        time.sleep(0.5)

    print_success(f"Partida creada: {game.game_id} (12 min, 0 muertes - PERFECTO)")
    return game, events


def save_game_and_events(game: Game, events: list[GameEvent], db):
    """Guarda la partida y sus eventos en Firestore"""
    print_info(f"  Guardando partida {game.game_id}...")

    # Guardar partida
    games_ref = db.collection("games")
    games_ref.document(game.game_id).set(game.to_dict())

    # Guardar eventos en batch
    events_ref = db.collection("events")
    batch = db.batch()

    for i, event in enumerate(events):
        event_ref = events_ref.document(event.event_id)
        batch.set(event_ref, event.to_dict())

        # Firestore batch máximo 500 operaciones
        if (i + 1) % 500 == 0:
            batch.commit()
            batch = db.batch()

    # Commit final
    if events:
        batch.commit()

    print_info(f"  ✓ Guardados {len(events)} eventos")


def main():
    """Función principal"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}")
    print("  TRISKEL - Generador de Partidas de Ejemplo")
    print(f"{'='*60}{Colors.ENDC}\n")

    # Conectar a Firebase
    print_step("Conectando a Firebase...")
    db = get_firestore_client()
    print_success("Conexión establecida")

    # Crear o obtener jugador
    player = create_or_get_test_player(db)

    print(f"\n{Colors.HEADER}Generando 6 partidas con diferentes características...{Colors.ENDC}\n")

    # Crear las 6 partidas
    scenarios = [
        create_game_scenario_1,
        create_game_scenario_2,
        create_game_scenario_3,
        create_game_scenario_4,
        create_game_scenario_5,
        create_game_scenario_6,
    ]

    total_events = 0

    for i, scenario_func in enumerate(scenarios, 1):
        print(f"\n{Colors.BOLD}[{i}/6]{Colors.ENDC}")
        game, events = scenario_func(player.player_id, db)
        save_game_and_events(game, events, db)
        total_events += len(events)
        time.sleep(1)  # Pausa entre partidas

    # Resumen final
    print(f"\n{Colors.OKGREEN}{Colors.BOLD}{'='*60}")
    print("  ✓ COMPLETADO")
    print(f"{'='*60}{Colors.ENDC}")
    print(f"\n{Colors.OKGREEN}Se crearon:{Colors.ENDC}")
    print("  • 6 partidas variadas")
    print(f"  • {total_events} eventos de telemetría")
    print(f"  • Jugador: {player.username} ({player.player_id})")
    print(f"\n{Colors.OKCYAN}Puedes ver los resultados en:{Colors.ENDC}")
    print("  • Dashboard: http://localhost:8000/web/")
    print("  • API: http://localhost:8000/docs")
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
