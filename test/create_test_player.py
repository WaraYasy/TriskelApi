"""
Script para crear un jugador de prueba permanente
"""
from app.models.player import PlayerCreate, PlayerStats, PlayerUpdate
from app.repositories.player_repository import PlayerRepository
from app.firebase import firebase_manager


def create_test_player():
    """Crea un jugador de prueba para visualizar en Firebase Console"""

    print("=" * 60)
    print("  CREANDO JUGADOR DE PRUEBA")
    print("=" * 60)

    # Inicializar Firebase
    firebase_manager.initialize()

    # Crear repositorio
    repo = PlayerRepository()

    # Crear jugador con datos completos
    player_data = PlayerCreate(
        username="jugador_demo",
        email="demo@triskel.com"
    )

    player = repo.create(player_data)

    print(f"\n✅ Jugador creado exitosamente!")
    print(f"   ID: {player.player_id}")
    print(f"   Username: {player.username}")
    print(f"   Email: {player.email}")

    # Actualizar con estadísticas de ejemplo
    update_data = PlayerUpdate(
        total_playtime_seconds=7200,  # 2 horas
        games_played=3,
        games_completed=1,
        stats=PlayerStats(
            total_good_choices=8,
            total_bad_choices=2,
            total_deaths=25,
            favorite_relic="lirio",
            best_speedrun_seconds=2400,
            moral_alignment=0.6
        )
    )

    updated_player = repo.update(player.player_id, update_data)

    print(f"\n📊 Estadísticas agregadas:")
    print(f"   - Tiempo de juego: {updated_player.total_playtime_seconds // 60} minutos")
    print(f"   - Partidas jugadas: {updated_player.games_played}")
    print(f"   - Partidas completadas: {updated_player.games_completed}")
    print(f"   - Elecciones buenas: {updated_player.stats.total_good_choices}")
    print(f"   - Elecciones malas: {updated_player.stats.total_bad_choices}")
    print(f"   - Muertes totales: {updated_player.stats.total_deaths}")
    print(f"   - Reliquia favorita: {updated_player.stats.favorite_relic}")
    print(f"   - Alineación moral: {updated_player.stats.moral_alignment}")

    print("\n" + "=" * 60)
    print("🎉 Ahora ve a Firebase Console y verás la colección 'players'!")
    print("=" * 60)
    print(f"\n📍 https://console.firebase.google.com/")
    print(f"   → Proyecto: triskel-game")
    print(f"   → Firestore Database")
    print(f"   → Colección: players")
    print(f"   → Documento: {player.player_id}\n")


if __name__ == "__main__":
    try:
        create_test_player()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
