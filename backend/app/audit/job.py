"""CA-006: Job de auditoria agendado (APScheduler)."""
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

async def verify_audit_chain() -> None:
    """
    Executa a verificação de integridade de todos os logs de auditoria.
    """
    logger.info("Job de auditoria: Verificação iniciada (placeholder).")
    # Lógica será implementada na próxima etapa
    pass

def start_scheduler() -> None:
    """
    Inicia o agendador de tarefas (APScheduler).
    """
    if not scheduler.running:
        scheduler.add_job(
            verify_audit_chain,
            trigger=CronTrigger(hour=3, minute=0),
            id="daily_audit_verification",
            name="Verify Audit Chain Integrity",
            replace_existing=True,
        )
        scheduler.start()
        logger.info("Scheduler de auditoria iniciado.")

def stop_scheduler() -> None:
    """
    Para o agendador de tarefas.
    """
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler de auditoria parado.")
