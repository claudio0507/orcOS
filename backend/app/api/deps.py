"""Dependências FastAPI — sessão, tenant, autenticação."""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_session
from app.models.tenant import Tenant

# UUID padrão do tenant demo — deve existir no banco quando SANDBOX_MODE=True
_SANDBOX_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000000")


async def get_tenant_id(
    x_tenant_id: Annotated[str | None, Header(alias="X-Tenant-ID")] = None,
) -> uuid.UUID:
    """Extrai e valida o tenant_id do header X-Tenant-ID.

    Em SANDBOX_MODE, usa tenant demo quando o header estiver ausente.
    """
    if not x_tenant_id:
        if settings.SANDBOX_MODE:
            return _SANDBOX_TENANT_ID
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Header X-Tenant-ID obrigatório.",
        )
    try:
        return uuid.UUID(x_tenant_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Tenant-ID inválido — esperado UUID v4.",
        )


async def get_db_session(
    session: Annotated[AsyncSession, Depends(get_session)],
    tenant_id: Annotated[uuid.UUID, Depends(get_tenant_id)],
) -> AsyncSession:  # type: ignore[return]
    """Sessão com RLS configurado para o tenant da requisição.

    Define app.tenant_id na sessão Postgres para ativar as policies RLS.
    No-op em SQLite (usado em testes — sem RLS).
    """
    dialect = session.bind.dialect.name if session.bind else "postgresql"  # type: ignore[union-attr]
    if dialect == "postgresql":
        await session.execute(
            text("SET LOCAL app.tenant_id = :tid"),
            {"tid": str(tenant_id)},
        )
    yield session  # type: ignore[misc]


async def get_verified_tenant(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_id: Annotated[uuid.UUID, Depends(get_tenant_id)],
) -> Tenant:
    """Garante que o tenant existe e está ativo."""
    result = await session.execute(
        select(Tenant).where(Tenant.id == tenant_id, Tenant.ativo.is_(True))
    )
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant não encontrado ou inativo.",
        )
    return tenant


# Type aliases para uso nos routers
SessionDep = Annotated[AsyncSession, Depends(get_db_session)]
TenantIDDep = Annotated[uuid.UUID, Depends(get_tenant_id)]
TenantDep = Annotated[Tenant, Depends(get_verified_tenant)]
