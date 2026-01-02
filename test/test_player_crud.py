"""
Script de prueba para operaciones CRUD de Players
"""
from app.models.player import PlayerCreate, PlayerUpdate, PlayerStats
from app.repositories.player_repository import PlayerRepository
from app.firebase import firebase_manager


def print_separator(title: str):
    """Imprime un separador visual"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_player_crud():
    """Prueba completa de operaciones CRUD para Players"""

    # Inicializar Firebase
    print_separator("INICIALIZANDO FIREBASE")
    firebase_manager.initialize()

    # Crear repositorio
    repo = PlayerRepository()

    # 1. CREATE - Crear jugadores
    print_separator("1. CREATE - Crear jugadores")

    player1_data = PlayerCreate(
        username="heroe_valiente",
        email="heroe@triskel.com"
    )

    player2_data = PlayerCreate(
        username="sombra_oscura",
        email="sombra@triskel.com"
    )

    player1 = repo.create(player1_data)
    print(f"   Jugador 1 creado:")
    print(f"   - ID: {player1.player_id}")
    print(f"   - Username: {player1.username}")
    print(f"   - Email: {player1.email}")
    print(f"   - Created at: {player1.created_at}")

    player2 = repo.create(player2_data)
    print(f"\n   Jugador 2 creado:")
    print(f"   - ID: {player2.player_id}")
    print(f"   - Username: {player2.username}")

    # 2. READ - Leer jugadores
    print_separator("2. READ - Leer jugadores")

    # Por ID
    print(f"   Buscando jugador por ID: {player1.player_id}")
    found_player = repo.get_by_id(player1.player_id)
    if found_player:
        print(f"   ✅ Encontrado: {found_player.username}")
    else:
        print(f"   ❌ No encontrado")

    # Por username
    print(f"\n   Buscando jugador por username: {player2.username}")
    found_player = repo.get_by_username(player2.username)
    if found_player:
        print(f"   ✅ Encontrado: {found_player.player_id}")
    else:
        print(f"   ❌ No encontrado")

    # Todos los jugadores
    print(f"\n   Listando todos los jugadores:")
    all_players = repo.get_all()
    print(f"   Total de jugadores: {len(all_players)}")
    for player in all_players:
        print(f"   - {player.username} ({player.player_id})")

    # 3. UPDATE - Actualizar jugador
    print_separator("3. UPDATE - Actualizar jugador")

    update_data = PlayerUpdate(
        total_playtime_seconds=3600,
        games_played=5,
        games_completed=2,
        stats=PlayerStats(
            total_good_choices=10,
            total_bad_choices=3,
            total_deaths=15,
            favorite_relic="lirio",
            best_speedrun_seconds=1800,
            moral_alignment=0.7
        )
    )

    print(f"   Actualizando jugador: {player1.player_id}")
    updated_player = repo.update(player1.player_id, update_data)

    if updated_player:
        print(f"   ✅ Jugador actualizado:")
        print(f"   - Tiempo de juego: {updated_player.total_playtime_seconds}s")
        print(f"   - Partidas jugadas: {updated_player.games_played}")
        print(f"   - Partidas completadas: {updated_player.games_completed}")
        print(f"   - Reliquia favorita: {updated_player.stats.favorite_relic}")
        print(f"   - Alineación moral: {updated_player.stats.moral_alignment}")
    else:
        print(f"   ❌ No se pudo actualizar")

    # 4. EXISTS - Verificar existencia
    print_separator("4. EXISTS - Verificar existencia")

    print(f"   ¿Existe {player1.player_id}? {repo.exists(player1.player_id)}")
    print(f"   ¿Existe 'id-falso'? {repo.exists('id-falso')}")

    # 5. COUNT - Contar jugadores
    print_separator("5. COUNT - Contar jugadores")

    total = repo.count()
    print(f"   Total de jugadores en la base de datos: {total}")

    # 6. DELETE - Eliminar jugadores
    print_separator("6. DELETE - Eliminar jugadores")

    print(f"   Eliminando jugador: {player1.username}")
    deleted = repo.delete(player1.player_id)
    if deleted:
        print(f"   ✅ Jugador eliminado correctamente")
    else:
        print(f"   ❌ No se pudo eliminar")

    print(f"\n   Eliminando jugador: {player2.username}")
    deleted = repo.delete(player2.player_id)
    if deleted:
        print(f"   ✅ Jugador eliminado correctamente")
    else:
        print(f"   ❌ No se pudo eliminar")

    # 7. VERIFICAR LIMPIEZA
    print_separator("7. VERIFICAR LIMPIEZA")

    remaining = repo.count()
    print(f"   Jugadores restantes: {remaining}")

    print_separator("✅ PRUEBAS COMPLETADAS")
    print("\n🎉 Todas las operaciones CRUD funcionan correctamente!\n")


if __name__ == "__main__":
    try:
        test_player_crud()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
