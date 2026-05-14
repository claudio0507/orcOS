"""CA-006: Job de auditoria agendado (APScheduler)."""
import logging
from datetime import UTC, datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.verification import verify_chain_integrity

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

_last_result: dict = {
    "status": "PENDING",
    "last_run": None,
    "count": 0,
    "message": "Nenhuma verificação executada ainda.",
    "broken_at_id": None,
}


def get_last_result() -> dict:
    """Retorna o resultado da última execução do job de auditoria."""
    return _last_result


async def verify_audit_chain(session: AsyncSession | None = None) -> dict:
    """
    Verifica integridade da cadeia de audit logs.

    Aceita sessão opcional para facilitar testes. Em produção (APScheduler),
    cria sua própria sessão via async_session.
    """
    global _last_result
    logger.info("Job de auditoria: iniciando verificação da hash chain.")

    if session is not None:
        result = await verify_chain_integrity(session)
    else:
        from app.db.session import async_session as session_factory
        async with session_factory() as db:
            result = await verify_chain_integrity(db)

    result["last_run"] = datetime.now(UTC).isoformat()
    _last_result = result

    if result["status"] == "CORRUPTED":
        logger.critical(
            "ALERTA DE ADULTERAÇÃO: hash chain corrompida! "
            "Log ID: %s — %s",
            result.get("broken_at_id"),
            result.get("message"),
        )
    else:
        logger.info(
            "Job de auditoria: %s (%d registros verificados).",
            result["status"],
            result.get("count", 0),
        )

    return result


def _scheduled_job() -> None:
    """Wrapper síncrono que o APScheduler invoca — delega para coroutine."""
    import asyncio
    asyncio.get_event_loop().run_until_complete(verify_audit_chain())


def start_scheduler() -> None:
    """Inicia o agendador de tarefas (APScheduler)."""
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
    """Para o agendador de tarefas."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler de auditoria parado.")
