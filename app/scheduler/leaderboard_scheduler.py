"""Scheduler para recálculo de Leaderboards.

Usa APScheduler para ejecutar el recalculo cada 6 horas.

Autor: Mandrágora
"""

import time

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.logger import logger

# Instancia global del scheduler
scheduler = BackgroundScheduler()

# Configuración de retry
MAX_RETRIES = 3
RETRY_DELAYS = [60, 300, 900]  # 1 min, 5 min, 15 min (exponential backoff)


def refresh_leaderboards_job():
    """Job que recalcula todos los leaderboards con retry logic.

    Este job se ejecuta cada 6 horas por el scheduler.
    Si falla, reintenta hasta 3 veces con exponential backoff.
    """
    logger.info("=== Scheduler: Iniciando recalculo de leaderboards ===")

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # Importar aqui para evitar imports circulares
            from app.domain.leaderboard.repository import LeaderboardRepository
            from app.domain.leaderboard.service import LeaderboardService

            # Crear instancias de servicio y repositorio
            repository = LeaderboardRepository()
            service = LeaderboardService(repository=repository)

            # Ejecutar recalculo
            updated = service.refresh_all_leaderboards()

            logger.info(f"=== Scheduler: Leaderboards actualizados exitosamente: {updated} ===")
            return  # Éxito - salir del loop

        except Exception as e:
            if attempt < MAX_RETRIES:
                # Falló pero quedan intentos - esperar y reintentar
                delay = RETRY_DELAYS[attempt - 1]
                logger.warning(
                    f"=== Scheduler: Intento {attempt}/{MAX_RETRIES} falló: {e}. "
                    f"Reintentando en {delay}s... ==="
                )
                time.sleep(delay)
            else:
                # Último intento falló - loguear error final
                logger.error(
                    f"=== Scheduler: Error FINAL recalculando leaderboards después de {MAX_RETRIES} intentos: {e} ==="
                )


def start_scheduler():
    """Inicia el scheduler de leaderboards.

    Configura el job para ejecutarse cada 6 horas.
    También ejecuta un recálculo inicial al arrancar.
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
        misfire_grace_time=3600,  # 1 hora de gracia si el job se perdió
        max_instances=1,  # Solo una instancia del job a la vez
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
    """Detiene el scheduler de forma segura.

    Espera a que los jobs actuales terminen antes de cerrar.
    """
    if scheduler.running:
        scheduler.shutdown(wait=True)
        logger.info("Scheduler de leaderboards detenido")
