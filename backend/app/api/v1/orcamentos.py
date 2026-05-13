"""Router: CRUD de Orçamentos."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select

from app.api.deps import SessionDep, TenantIDDep
from app.audit.middleware import log_audit_action
from app.auth.dependencies import get_current_user, require_mfa
from app.models.orcamento import Orcamento, StatusOrcamento
from app.models.usuario import Usuario
from app.schemas.errors import RESPONSES_CRUD_READ, RESPONSES_CRUD_WRITE
from app.schemas.orcamento import OrcamentoCreate, OrcamentoList, OrcamentoRead, OrcamentoUpdate

router = APIRouter(
    prefix="/orcamentos",
    tags=["Orçamentos"],
    dependencies=[Depends(get_current_user)],
)


@router.get(
    "",
    response_model=OrcamentoList,
    summary="Listar orçamentos do tenant",
    description=(
        "Retorna uma lista paginada de orçamentos pertencentes ao tenant informado "
        "no header `X-Tenant-ID`. Suporta filtro por status e paginação via `limit`/`offset`."
    ),
    response_description="Lista paginada com `items` e `total`.",
    responses={**RESPONSES_CRUD_READ},
)
async def listar_orcamentos(
    session: SessionDep,
    tenant_id: TenantIDDep,
    status_filter: str | None = Query(
        None,
        alias="status",
        description="Filtrar por status: rascunho, em_revisao, aprovado, cancelado.",
        examples=["rascunho", "aprovado"],
    ),
    limit: int = Query(50, ge=1, le=200, description="Máximo de itens por página."),
    offset: int = Query(0, ge=0, description="Deslocamento para paginação."),
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


@router.post(
    "",
    response_model=OrcamentoRead,
    status_code=status.HTTP_201_CREATED,
    summary="Criar novo orçamento",
    description=(
        "Cria um novo orçamento para o tenant. O status inicial é sempre `rascunho`. "
        "O campo `custo_fixo_total` define os custos fixos que serão distribuídos "
        "no spreading (rateio)."
    ),
    response_description="Orçamento criado com ID gerado e status `rascunho`.",
    responses={**RESPONSES_CRUD_WRITE},
)
async def criar_orcamento(
    payload: OrcamentoCreate,
    session: SessionDep,
    tenant_id: TenantIDDep,
    current_user: Usuario = Depends(get_current_user),
) -> Orcamento:
    """Cria novo orçamento para o tenant."""
    orcamento = Orcamento(
        tenant_id=tenant_id,
        titulo=payload.titulo,
        descricao=payload.descricao,
        custo_fixo_total=str(payload.custo_fixo_total),
        status=StatusOrcamento.RASCUNHO,
        criado_por_id=current_user.id,
    )
    session.add(orcamento)
    await session.flush()
    
    await log_audit_action(
        session=session,
        user_id=current_user.id,
        tenant_id=tenant_id,
        action="POST",
        resource_type="Orcamento",
        resource_id=str(orcamento.id),
        old_value=None,
        new_value=payload.model_dump(mode="json"),
    )
    
    await session.commit()
    await session.refresh(orcamento)
    return orcamento


@router.get(
    "/{orcamento_id}",
    response_model=OrcamentoRead,
    summary="Obter orçamento por ID",
    description=(
        "Retorna os detalhes de um orçamento específico. "
        "Retorna 404 se o orçamento não existir ou pertencer a outro tenant."
    ),
    response_description="Detalhes completos do orçamento.",
    responses={**RESPONSES_CRUD_READ},
)
async def obter_orcamento(
    orcamento_id: uuid.UUID,
    session: SessionDep,
    tenant_id: TenantIDDep,
) -> Orcamento:
    """Retorna um orçamento pelo ID, filtrado por tenant."""
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


@router.patch(
    "/{orcamento_id}",
    response_model=OrcamentoRead,
    summary="Atualizar orçamento (parcial)",
    description=(
        "Atualização parcial (PATCH) de um orçamento. Apenas os campos enviados "
        "no payload serão atualizados. Permite alterar título, descrição, status e custo fixo."
    ),
    response_description="Orçamento atualizado.",
    responses={**RESPONSES_CRUD_WRITE},
)
async def atualizar_orcamento(
    orcamento_id: uuid.UUID,
    payload: OrcamentoUpdate,
    session: SessionDep,
    tenant_id: TenantIDDep,
    current_user: Usuario = Depends(get_current_user),
) -> Orcamento:
    """Atualiza campos parciais de um orçamento."""
    orcamento = await _get_or_404(session, tenant_id, orcamento_id)
    old_data = {"titulo": orcamento.titulo, "status": orcamento.status, "custo_fixo_total": str(orcamento.custo_fixo_total)}
    data = payload.model_dump(exclude_unset=True)
    if "custo_fixo_total" in data:
        data["custo_fixo_total"] = str(data["custo_fixo_total"])
    for field, value in data.items():
        setattr(orcamento, field, value)
        
    await session.flush()
    await log_audit_action(
        session=session,
        user_id=current_user.id,
        tenant_id=tenant_id,
        action="PATCH",
        resource_type="Orcamento",
        resource_id=str(orcamento.id),
        old_value=old_data,
        new_value=data,
    )
    await session.commit()
    await session.refresh(orcamento)
    return orcamento


@router.delete(
    "/{orcamento_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deletar orçamento",
    description=(
        "Remove um orçamento e todas as suas fichas (cascade). "
        "Retorna 404 se não encontrado ou pertencer a outro tenant. "
        "Requer MFA ativado."
    ),
    responses={**RESPONSES_CRUD_READ},
    dependencies=[Depends(require_mfa)],
)
async def deletar_orcamento(
    orcamento_id: uuid.UUID,
    session: SessionDep,
    tenant_id: TenantIDDep,
    current_user: Usuario = Depends(get_current_user),
) -> None:
    """Deleta um orçamento (cascade deleta fichas associadas)."""
    orcamento = await _get_or_404(session, tenant_id, orcamento_id)
    old_data = {"titulo": orcamento.titulo, "id": str(orcamento.id)}
    await session.delete(orcamento)
    await session.flush()
    await log_audit_action(
        session=session,
        user_id=current_user.id,
        tenant_id=tenant_id,
        action="DELETE",
        resource_type="Orcamento",
        resource_id=str(orcamento.id),
        old_value=old_data,
        new_value=None,
    )
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
