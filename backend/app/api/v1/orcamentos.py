"""Router: CRUD de Orçamentos."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from app.api.deps import SessionDep, TenantIDDep
from app.models.orcamento import Orcamento, StatusOrcamento
from app.schemas.orcamento import OrcamentoCreate, OrcamentoList, OrcamentoRead, OrcamentoUpdate

router = APIRouter(prefix="/orcamentos", tags=["Orçamentos"])


@router.get("", response_model=OrcamentoList)
async def listar_orcamentos(
    session: SessionDep,
    tenant_id: TenantIDDep,
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> OrcamentoList:
    """Lista orçamentos do tenant com paginação opcional."""
    base_q = select(Orcamento).where(Orcamento.tenant_id == tenant_id)
    if status_filter:
        base_q = base_q.where(Orcamento.status == status_filter)

    q = base_q.order_by(Orcamento.created_at.desc()).limit(limit).offset(offset)
    total_q = select(func.count()).select_from(base_q.subquery())

    items = (await session.execute(q)).scalars().all()
    total = (await session.execute(total_q)).scalar_one()
    return OrcamentoList(items=list(items), total=total)


@router.post("", response_model=OrcamentoRead, status_code=status.HTTP_201_CREATED)
async def criar_orcamento(
    payload: OrcamentoCreate,
    session: SessionDep,
    tenant_id: TenantIDDep,
) -> Orcamento:
    """Cria novo orçamento para o tenant."""
    orcamento = Orcamento(
        tenant_id=tenant_id,
        titulo=payload.titulo,
        descricao=payload.descricao,
        custo_fixo_total=str(payload.custo_fixo_total),
        status=StatusOrcamento.RASCUNHO,
    )
    session.add(orcamento)
    await session.commit()
    await session.refresh(orcamento)
    return orcamento


@router.get("/{orcamento_id}", response_model=OrcamentoRead)
async def obter_orcamento(
    orcamento_id: uuid.UUID,
    session: SessionDep,
    tenant_id: TenantIDDep,
) -> Orcamento:
    result = await session.execute(
        select(Orcamento).where(
            Orcamento.id == orcamento_id,
            Orcamento.tenant_id == tenant_id,
        )
    )
    orcamento = result.scalar_one_or_none()
    if not orcamento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Orçamento não encontrado.")
    return orcamento


@router.patch("/{orcamento_id}", response_model=OrcamentoRead)
async def atualizar_orcamento(
    orcamento_id: uuid.UUID,
    payload: OrcamentoUpdate,
    session: SessionDep,
    tenant_id: TenantIDDep,
) -> Orcamento:
    orcamento = await _get_or_404(session, tenant_id, orcamento_id)
    data = payload.model_dump(exclude_unset=True)
    if "custo_fixo_total" in data:
        data["custo_fixo_total"] = str(data["custo_fixo_total"])
    for field, value in data.items():
        setattr(orcamento, field, value)
    await session.commit()
    await session.refresh(orcamento)
    return orcamento


@router.delete("/{orcamento_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_orcamento(
    orcamento_id: uuid.UUID,
    session: SessionDep,
    tenant_id: TenantIDDep,
) -> None:
    orcamento = await _get_or_404(session, tenant_id, orcamento_id)
    await session.delete(orcamento)
    await session.commit()


async def _get_or_404(session, tenant_id: uuid.UUID, orcamento_id: uuid.UUID) -> Orcamento:
    result = await session.execute(
        select(Orcamento).where(
            Orcamento.id == orcamento_id,
            Orcamento.tenant_id == tenant_id,
        )
    )
    orcamento = result.scalar_one_or_none()
    if not orcamento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Orçamento não encontrado.")
    return orcamento
