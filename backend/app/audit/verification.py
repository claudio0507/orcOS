"""CA-006: Verificação da integridade da Hash Chain (Audit Trail)."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.hash_chain import compute_entry_hash
from app.audit.models import AuditLog


async def verify_chain_integrity(session: AsyncSession) -> dict:
    """
    Percorre todo o AuditLog do mais antigo ao mais recente
    e recalcula os hashes para verificar se houve adulteração.
    Retorna o status da chain e o total de registros válidos.
    """
    result = await session.execute(
        select(AuditLog).order_by(AuditLog.timestamp.asc(), AuditLog.id.asc())
    )
    logs = result.scalars().all()

    if not logs:
        return {"status": "EMPTY", "count": 0, "message": "Nenhum registro de auditoria.", "broken_at_id": None}

    prev_hash = None

    for log in logs:
        if prev_hash is not None and log.prev_hash != prev_hash:
            return {
                "status": "CORRUPTED",
                "count": len(logs),
                "broken_at_id": str(log.id),
                "message": f"Quebra de chain encontrada no log ID {log.id}. prev_hash não corresponde.",
            }

        expected_hash = compute_entry_hash(
            timestamp=log.timestamp,
            user_id=str(log.user_id) if log.user_id else None,
            action=log.action,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            old_value=log.old_value,
            new_value=log.new_value,
            prev_hash=log.prev_hash,
        )

        if log.entry_hash != expected_hash:
            return {
                "status": "CORRUPTED",
                "count": len(logs),
                "broken_at_id": str(log.id),
                "message": f"Hash adulterado no log ID {log.id}. Conteúdo não corresponde ao hash.",
            }

        prev_hash = log.entry_hash

    return {"status": "OK", "count": len(logs), "message": "A cadeia de auditoria está íntegra.", "broken_at_id": None}
