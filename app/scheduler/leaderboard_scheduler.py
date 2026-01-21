"""
Scheduler para recalculo de Leaderboards

Usa APScheduler para ejecutar el recalculo cada 6 horas.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.logger import logger

# Instancia global del scheduler
scheduler = BackgroundScheduler()


def refresh_leaderboards_job():
    """
    Job que recalcula todos los leaderboards.

    Este job se ejecuta cada 6 horas por el scheduler.
    """
    logger.info("=== Scheduler: Iniciando recalculo de leaderboards ===")

    try:
        # Importar aqui para evitar imports circulares
        from app.domain.leaderboard.repository import LeaderboardRepository
        from app.domain.leaderboard.service import LeaderboardService

        # Crear instancias de servicio y repositorio
        repository = LeaderboardRepository()
        service = LeaderboardService(repository=repository)

        # Ejecutar recalculo
        updated = service.refresh_all_leaderboards()

        logger.info(
            f"=== Scheduler: Leaderboards actualizados exitosamente: {updated} ==="
        )

    except Exception as e:
        logger.error(f"=== Scheduler: Error recalculando leaderboards: {e} ===")


def start_scheduler():
    """
    Inicia el scheduler de leaderboards.

    Configura el job para ejecutarse cada 6 horas.
    Tambien ejecuta un recalculo inicial al arrancar.
    """
    if scheduler.running:
        logger.warning("Scheduler ya esta corriendo")
        return

    # Configurar job: cada 6 horas
    scheduler.add_job(
        refresh_leaderboards_job,
        trigger=IntervalTrigger(hours=6),
        id="leaderboard_refresh",
        name="Recalculo de Leaderboards",
        replace_existing=True,
    )

    # Iniciar scheduler
    scheduler.start()
    logger.info("Scheduler de leaderboards iniciado (intervalo: 6 horas)")

    # Ejecutar recalculo inicial (en background para no bloquear startup)
    scheduler.add_job(
        refresh_leaderboards_job,
        id="leaderboard_initial_refresh",
        name="Recalculo Inicial de Leaderboards",
        replace_existing=True,
    )
    logger.info("Recalculo inicial de leaderboards programado")


def shutdown_scheduler():
    """
    Detiene el scheduler de forma segura.

    Espera a que los jobs actuales terminen antes de cerrar.
    """
    if scheduler.running:
        scheduler.shutdown(wait=True)
        logger.info("Scheduler de leaderboards detenido")
