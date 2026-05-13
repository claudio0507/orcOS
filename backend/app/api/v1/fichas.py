"""Router: Fichas + cálculo com pricing_engine."""
from __future__ import annotations

import json
import uuid
from decimal import Decimal

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import SessionDep, TenantIDDep
from app.models.ficha import Ficha, TipoPrecificacao
from app.models.orcamento import Orcamento
from app.pricing_engine.bdi import (
    BdiComponent,
    ClassicBdiInputs,
    ComponentBase,
    compute_price_classic,
    compute_price_manual,
)
from app.pricing_engine.markup import compute_unit_price
from app.pricing_engine.rounding import RoundingMode
from app.schemas.ficha import (
    BdiClassicoParams,
    BdiManualParams,
    FichaCalcResult,
    FichaCreate,
    FichaRead,
    FichaUpdate,
    MarkupParams,
)

router = APIRouter(prefix="/orcamentos/{orcamento_id}/fichas", tags=["Fichas"])


@router.get("", response_model=list[FichaRead])
async def listar_fichas(
    orcamento_id: uuid.UUID,
    session: SessionDep,
    tenant_id: TenantIDDep,
) -> list[Ficha]:
    await _assert_orcamento_exists(session, tenant_id, orcamento_id)
    result = await session.execute(
        select(Ficha)
        .where(Ficha.orcamento_id == orcamento_id, Ficha.tenant_id == tenant_id)
        .order_by(Ficha.ordem)
    )
    return list(result.scalars().all())


@router.post("", response_model=FichaRead, status_code=status.HTTP_201_CREATED)
async def criar_ficha(
    orcamento_id: uuid.UUID,
    payload: FichaCreate,
    session: SessionDep,
    tenant_id: TenantIDDep,
) -> Ficha:
    await _assert_orcamento_exists(session, tenant_id, orcamento_id)
    ficha = Ficha(
        tenant_id=tenant_id,
        orcamento_id=orcamento_id,
        descricao=payload.descricao,
        unidade=payload.unidade,
        quantidade=str(payload.quantidade),
        custo_unitario=str(payload.custo_unitario),
        tipo_precificacao=payload.tipo_precificacao,
        parametros_precificacao=(
            payload.parametros_precificacao.model_dump_json()
            if payload.parametros_precificacao
            else None
        ),
        ordem=payload.ordem,
    )
    session.add(ficha)
    await session.commit()
    await session.refresh(ficha)
    return ficha


@router.get("/{ficha_id}", response_model=FichaRead)
async def obter_ficha(
    orcamento_id: uuid.UUID,
    ficha_id: uuid.UUID,
    session: SessionDep,
    tenant_id: TenantIDDep,
) -> Ficha:
    return await _get_ficha_or_404(session, tenant_id, orcamento_id, ficha_id)


@router.patch("/{ficha_id}", response_model=FichaRead)
async def atualizar_ficha(
    orcamento_id: uuid.UUID,
    ficha_id: uuid.UUID,
    payload: FichaUpdate,
    session: SessionDep,
    tenant_id: TenantIDDep,
) -> Ficha:
    ficha = await _get_ficha_or_404(session, tenant_id, orcamento_id, ficha_id)
    data = payload.model_dump(exclude_unset=True)
    for field in ("quantidade", "custo_unitario"):
        if field in data and data[field] is not None:
            data[field] = str(data[field])
    if "parametros_precificacao" in data and data["parametros_precificacao"] is not None:
        data["parametros_precificacao"] = data["parametros_precificacao"].model_dump_json()
    for field, value in data.items():
        setattr(ficha, field, value)
    await session.commit()
    await session.refresh(ficha)
    return ficha


@router.delete("/{ficha_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_ficha(
    orcamento_id: uuid.UUID,
    ficha_id: uuid.UUID,
    session: SessionDep,
    tenant_id: TenantIDDep,
) -> None:
    ficha = await _get_ficha_or_404(session, tenant_id, orcamento_id, ficha_id)
    await session.delete(ficha)
    await session.commit()


@router.post("/{ficha_id}/calcular", response_model=FichaCalcResult)
async def calcular_preco(
    orcamento_id: uuid.UUID,
    ficha_id: uuid.UUID,
    session: SessionDep,
    tenant_id: TenantIDDep,
) -> FichaCalcResult:
    """Executa o pricing_engine para a ficha e persiste o resultado."""
    ficha = await _get_ficha_or_404(session, tenant_id, orcamento_id, ficha_id)
    custo = Decimal(ficha.custo_unitario)
    params = json.loads(ficha.parametros_precificacao) if ficha.parametros_precificacao else {}

    try:
        if ficha.tipo_precificacao == TipoPrecificacao.MARKUP:
            p = MarkupParams(**params)
            res = compute_unit_price(
                unit_cost=custo,
                tributes=p.tributes,
                profit=p.profit,
                indirect=p.indirect,
            )
            resultado = FichaCalcResult(
                ficha_id=ficha.id,
                preco_unitario=str(res.unit_price),
                divisor=str(res.divisor),
                is_alert=res.is_alert,
                detalhes={"total_components": str(res.total_components)},
            )

        elif ficha.tipo_precificacao == TipoPrecificacao.BDI_MANUAL:
            p = BdiManualParams(**params)
            components = [
                BdiComponent(
                    name=c.name,
                    percent=c.percent,
                    base=ComponentBase(c.base),
                    legal_reference=c.legal_reference,
                )
                for c in p.components
            ]
            res = compute_price_manual(unit_cost=custo, components=components)
            resultado = FichaCalcResult(
                ficha_id=ficha.id,
                preco_unitario=str(res.unit_price),
                is_alert=res.is_alert,
                detalhes={"t_revenue": str(res.t_revenue), "t_cost": str(res.t_cost)},
            )

        else:  # BDI_CLASSICO
            p = BdiClassicoParams(**params)
            inputs = ClassicBdiInputs(
                administration=p.administration,
                financial=p.financial,
                risk=p.risk,
                profit=p.profit,
                tributes=p.tributes,
            )
            res = compute_price_classic(unit_cost=custo, inputs=inputs)
            resultado = FichaCalcResult(
                ficha_id=ficha.id,
                preco_unitario=str(res.unit_price),
                is_alert=res.is_alert,
                detalhes={"bdi": str(res.bdi)},
            )

    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    ficha.preco_unitario_calculado = resultado.preco_unitario
    await session.commit()
    return resultado


async def _assert_orcamento_exists(session, tenant_id: uuid.UUID, orcamento_id: uuid.UUID) -> None:
    result = await session.execute(
        select(Orcamento).where(
            Orcamento.id == orcamento_id, Orcamento.tenant_id == tenant_id
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Orçamento não encontrado.")


async def _get_ficha_or_404(
    session, tenant_id: uuid.UUID, orcamento_id: uuid.UUID, ficha_id: uuid.UUID
) -> Ficha:
    result = await session.execute(
        select(Ficha).where(
            Ficha.id == ficha_id,
            Ficha.orcamento_id == orcamento_id,
            Ficha.tenant_id == tenant_id,
        )
    )
    ficha = result.scalar_one_or_none()
    if not ficha:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ficha não encontrada.")
    return ficha
