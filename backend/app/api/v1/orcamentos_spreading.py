"""Router: Spreading — rateio de custos fixos do orçamento."""
from __future__ import annotations

import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.api.deps import SessionDep, TenantIDDep
from app.auth.dependencies import get_current_user, require_mfa
from app.models.ficha import Ficha
from app.models.orcamento import Orcamento
from app.pricing_engine.rounding import RoundingMode, round_money
from app.pricing_engine.spreading import SpreadingLine, spread_fixed_costs
from app.schemas.errors import RESPONSES_ACTION
from app.schemas.spreading import (
    SpreadingRequest,
    SpreadingResponse,
    SpreadingResultLineRead,
)

router = APIRouter(
    prefix="/orcamentos",
    tags=["Spreading"],
    dependencies=[Depends(get_current_user), Depends(require_mfa)],
)


@router.post(
    "/{orcamento_id}/spreading",
    response_model=SpreadingResponse,
    status_code=status.HTTP_200_OK,
    summary="Executar spreading (rateio de custos fixos)",
    description=(
        "Distribui os custos fixos do orçamento proporcionalmente ao **peso** "
        "(preço variável × quantidade) de cada ficha.\n\n"
        "### Algoritmo\n\n"
        "```\n"
        "peso_i         = preço_variável_i × qty_i\n"
        "total_pesos    = Σ peso_i\n"
        "fixo_alocado_i = fixos_totais × (peso_i / total_pesos)\n"
        "preço_final_i  = preço_variável_i + (fixo_alocado_i / qty_i)\n"
        "```\n\n"
        "### Invariante CA-001 (Conservação de Totais)\n\n"
        "O endpoint garante a seguinte invariante:\n\n"
        "> **CA-001:** Σ(preço_final × qty) = Σ(preço_variável × qty) + custos_fixos ± R$0,01\n\n"
        "A tolerância de R$0,01 decorre exclusivamente do arredondamento monetário "
        "para 2 casas decimais. O resíduo é absorvido pela linha de maior peso "
        "(marcada com `carries_residue: true`).\n\n"
        "### Persistência\n\n"
        "O `preço_unitario_calculado` de cada ficha é **atualizado** com o preço "
        "final após spreading. Para reverter, recalcule as fichas individualmente.\n\n"
        "### Override de Custo Fixo\n\n"
        "O payload aceita `custo_fixo_override` para simular cenários sem alterar "
        "o valor persistido no orçamento."
    ),
    response_description=(
        "Resultado do spreading com totais, validação CA-001, e detalhamento por ficha."
    ),
    responses={
        **RESPONSES_ACTION,
        200: {
            "description": (
                "Spreading executado com sucesso. `ca001_validado` indica se a "
                "invariante de conservação de totais foi satisfeita."
            ),
        },
    },
)
async def executar_spreading(
    orcamento_id: uuid.UUID,
    session: SessionDep,
    tenant_id: TenantIDDep,
    payload: SpreadingRequest | None = None,
) -> SpreadingResponse:
    """Aplica o rateio de custos fixos (spreading) sobre todas as fichas.

    O algoritmo distribui os custos fixos proporcionalmente ao peso
    (preço_variável × qty) de cada ficha, preservando a invariante CA-001:

        Σ(final_unit_price × qty) == Σ(variable_unit_price × qty) + fixed_total ± R$0.01

    Persiste `preco_unitario_calculado` em cada ficha com o preço final.
    """
    # 1. Buscar orçamento com RLS
    orcamento = await _get_orcamento_or_404(session, tenant_id, orcamento_id)

    # 2. Buscar fichas do orçamento
    result = await session.execute(
        select(Ficha)
        .where(Ficha.orcamento_id == orcamento_id, Ficha.tenant_id == tenant_id)
        .order_by(Ficha.ordem)
    )
    fichas = list(result.scalars().all())

    if not fichas:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Orçamento não possui fichas para spreading.",
        )

    # 3. Determinar parâmetros
    body = payload or SpreadingRequest()
    fixed_total = (
        body.custo_fixo_override
        if body.custo_fixo_override is not None
        else Decimal(orcamento.custo_fixo_total)
    )
    rounding_mode = RoundingMode(body.rounding)

    # 4. Construir SpreadingLines a partir das fichas
    #    variable_unit_price = preco_unitario_calculado (se existir) ou custo_unitario
    spreading_lines: list[SpreadingLine] = []
    for ficha in fichas:
        variable_price = Decimal(
            ficha.preco_unitario_calculado
            if ficha.preco_unitario_calculado
            else ficha.custo_unitario
        )
        qty = Decimal(ficha.quantidade)
        spreading_lines.append(
            SpreadingLine(
                id=str(ficha.id),
                variable_unit_price=variable_price,
                quantity=qty,
            )
        )

    # 5. Executar spreading
    try:
        result_lines = spread_fixed_costs(
            lines=spreading_lines,
            fixed_total=fixed_total,
            rounding=rounding_mode,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        )

    # 6. Persistir preço final em cada ficha
    ficha_map = {str(f.id): f for f in fichas}
    for rl in result_lines:
        ficha = ficha_map[rl.id]
        ficha.preco_unitario_calculado = str(rl.final_unit_price)
    await session.commit()

    # 7. Validar CA-001
    total_variavel = sum(
        (Decimal(f.preco_unitario_calculado or f.custo_unitario) * Decimal(f.quantidade))
        for f in fichas
    )
    # Recalcular com os valores originais (antes do spreading) para CA-001
    total_variavel_original = sum(
        sl.variable_unit_price * sl.quantity for sl in spreading_lines
    )
    total_final = sum(rl.final_line_total for rl in result_lines)
    expected = round_money(total_variavel_original + fixed_total, mode=rounding_mode)
    tolerance = Decimal("0.01")
    ca001_ok = abs(total_final - expected) <= tolerance
    residuo_aplicado = any(rl.carries_residue for rl in result_lines)

    # 8. Montar resposta
    linhas_response = [
        SpreadingResultLineRead(
            ficha_id=uuid.UUID(rl.id),
            descricao=ficha_map[rl.id].descricao,
            variable_unit_price=str(rl.variable_unit_price),
            quantity=str(rl.quantity),
            allocated_fixed=str(rl.allocated_fixed),
            final_unit_price=str(rl.final_unit_price),
            final_line_total=str(rl.final_line_total),
            carries_residue=rl.carries_residue,
        )
        for rl in result_lines
    ]

    return SpreadingResponse(
        orcamento_id=orcamento_id,
        custo_fixo_total=str(fixed_total),
        total_variavel=str(round_money(total_variavel_original, mode=rounding_mode)),
        total_final=str(total_final),
        residuo_aplicado=residuo_aplicado,
        linhas=linhas_response,
        ca001_validado=ca001_ok,
    )


async def _get_orcamento_or_404(
    session, tenant_id: uuid.UUID, orcamento_id: uuid.UUID
) -> Orcamento:
    result = await session.execute(
        select(Orcamento).where(
            Orcamento.id == orcamento_id,
            Orcamento.tenant_id == tenant_id,
        )
    )
    orcamento = result.scalar_one_or_none()
    if not orcamento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Orçamento não encontrado.",
        )
    return orcamento
