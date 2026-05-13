"""Middleware / Serviço para registro automático na Trilha de Auditoria."""
import json
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.hash_chain import compute_entry_hash
from app.audit.models import AuditLog


async def log_audit_action(
    session: AsyncSession,
    user_id: uuid.UUID | None,
    tenant_id: uuid.UUID | None,
    action: str,
    resource_type: str,
    resource_id: str,
    old_value: dict | None = None,
    new_value: dict | None = None,
) -> None:
    """
    Grava uma entrada no AuditLog calculando o hash com base no último registro.
    Esta função deve ser chamada dentro da mesma transação da ação principal.
    """
    now = datetime.now(UTC)

    # Busca o último hash global do banco (para manter a chain)
    # Como o sistema pode ter concorrência, o ideal seria um LOCK na tabela,
    # mas para simplificar o MVP usaremos a última entrada por data.
    result = await session.execute(
        select(AuditLog.entry_hash)
        .order_by(AuditLog.timestamp.desc(), AuditLog.id.desc())
        .limit(1)
    )
    last_hash = result.scalar_one_or_none()

    old_val_str = json.dumps(old_value, default=str) if old_value else None
    new_val_str = json.dumps(new_value, default=str) if new_value else None

    entry_hash = compute_entry_hash(
        timestamp=now,
        user_id=str(user_id) if user_id else None,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        old_value=old_val_str,
        new_value=new_val_str,
        prev_hash=last_hash,
    )

    audit_log = AuditLog(
        timestamp=now,
        user_id=user_id,
        tenant_id=tenant_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        old_value=old_val_str,
        new_value=new_val_str,
        prev_hash=last_hash,
        entry_hash=entry_hash,
    )

    session.add(audit_log)
