"""Router: Fichas + cálculo com pricing_engine."""
from __future__ import annotations

import json
import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.api.deps import SessionDep, TenantIDDep
from app.audit.middleware import log_audit_action
from app.auth.dependencies import get_current_user, require_mfa
from app.models.ficha import Ficha, TipoPrecificacao
from app.models.orcamento import Orcamento
from app.models.usuario import Usuario
from app.pricing_engine.bdi import (
    BdiComponent,
    ClassicBdiInputs,
    ComponentBase,
    compute_price_classic,
    compute_price_manual,
)
from app.pricing_engine.markup import compute_unit_price
from app.schemas.errors import RESPONSES_ACTION, RESPONSES_CRUD_READ, RESPONSES_CRUD_WRITE
from app.schemas.ficha import (
    BdiClassicoParams,
    BdiManualParams,
    FichaCalcResult,
    FichaCreate,
    FichaRead,
    FichaUpdate,
    MarkupParams,
)

router = APIRouter(
    prefix="/orcamentos/{orcamento_id}/fichas",
    tags=["Fichas"],
    dependencies=[Depends(get_current_user)],
)


@router.get(
    "",
    response_model=list[FichaRead],
    summary="Listar fichas de um orçamento",
    description=(
        "Retorna todas as fichas (linhas de serviço/insumo) de um orçamento, "
        "ordenadas por `ordem`. O orçamento deve pertencer ao tenant."
    ),
    response_description="Lista de fichas ordenadas por posição.",
    responses={**RESPONSES_CRUD_READ},
)
async def listar_fichas(
    orcamento_id: uuid.UUID,
    session: SessionDep,
    tenant_id: TenantIDDep,
) -> list[Ficha]:
    """
    Lista todas as fichas associadas a um orçamento.

    Args:
        orcamento_id: ID do orçamento pai.
        session: Sessão do banco de dados.
        tenant_id: ID do tenant para isolamento.

    Returns:
        Lista de objetos Ficha ordenados pelo campo ordem.
    """
    await _assert_orcamento_exists(session, tenant_id, orcamento_id)
    result = await session.execute(
        select(Ficha)
        .where(Ficha.orcamento_id == orcamento_id, Ficha.tenant_id == tenant_id)
        .order_by(Ficha.ordem)
    )
    return list(result.scalars().all())


@router.post(
    "",
    response_model=FichaRead,
    status_code=status.HTTP_201_CREATED,
    summary="Criar nova ficha",
    description=(
        "Adiciona uma nova ficha ao orçamento. A ficha representa uma linha de "
        "serviço ou insumo com custo unitário e parâmetros de precificação.\n\n"
        "**Modos de precificação suportados:**\n"
        "- `markup` — Divisor = 1 − (tributos + lucro + despesas indiretas)\n"
        "- `bdi_manual` — Componentes arbitrários sobre receita ou custo\n"
        "- `bdi_classico` — Fórmula DNIT: (1+AC+AF+R)(1+L) / (1−T)"
    ),
    response_description="Ficha criada com ID gerado.",
    responses={**RESPONSES_CRUD_WRITE},
)
async def criar_ficha(
    orcamento_id: uuid.UUID,
    payload: FichaCreate,
    session: SessionDep,
    tenant_id: TenantIDDep,
    current_user: Usuario = Depends(get_current_user),
) -> Ficha:
    """
    Cria uma nova ficha de serviço ou insumo em um orçamento.

    Args:
        orcamento_id: ID do orçamento ao qual a ficha pertence.
        payload: Dados da ficha (descrição, custo, modo de precificação, etc).
        session: Sessão do banco de dados.
        tenant_id: ID do tenant.
        current_user: Usuário que está criando a ficha.

    Returns:
        A ficha criada com o ID gerado.
    """
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
    await session.flush()

    await log_audit_action(
        session=session,
        user_id=current_user.id,
        tenant_id=tenant_id,
        action="POST",
        resource_type="Ficha",
        resource_id=str(ficha.id),
        old_value=None,
        new_value=payload.model_dump(mode="json"),
    )

    await session.commit()
    await session.refresh(ficha)
    return ficha


@router.get(
    "/{ficha_id}",
    response_model=FichaRead,
    summary="Obter ficha por ID",
    description=(
        "Retorna os detalhes de uma ficha específica. "
        "Retorna 404 se a ficha, o orçamento ou o tenant não conferem."
    ),
    response_description="Detalhes completos da ficha.",
    responses={**RESPONSES_CRUD_READ},
)
async def obter_ficha(
    orcamento_id: uuid.UUID,
    ficha_id: uuid.UUID,
    session: SessionDep,
    tenant_id: TenantIDDep,
) -> Ficha:
    """
    Recupera os detalhes de uma ficha específica.

    Args:
        orcamento_id: ID do orçamento.
        ficha_id: ID da ficha solicitada.
        session: Sessão do banco de dados.
        tenant_id: ID do tenant.

    Returns:
        O objeto Ficha correspondente.

    Raises:
        HTTPException: Se a ficha não for encontrada ou não pertencer ao orçamento/tenant.
    """
    return await _get_ficha_or_404(session, tenant_id, orcamento_id, ficha_id)


@router.patch(
    "/{ficha_id}",
    response_model=FichaRead,
    summary="Atualizar ficha (parcial)",
    description=(
        "Atualização parcial (PATCH) de uma ficha. Apenas os campos enviados "
        "serão atualizados. Permite alterar descrição, quantidade, custo, modo de "
        "precificação e parâmetros."
    ),
    response_description="Ficha atualizada.",
    responses={**RESPONSES_CRUD_WRITE},
)
async def atualizar_ficha(
    orcamento_id: uuid.UUID,
    ficha_id: uuid.UUID,
    payload: FichaUpdate,
    session: SessionDep,
    tenant_id: TenantIDDep,
    current_user: Usuario = Depends(get_current_user),
) -> Ficha:
    """
    Atualiza campos específicos de uma ficha existente.

    Args:
        orcamento_id: ID do orçamento.
        ficha_id: ID da ficha a ser atualizada.
        payload: Dados para atualização parcial.
        session: Sessão do banco de dados.
        tenant_id: ID do tenant.
        current_user: Usuário realizando a atualização.

    Returns:
        A ficha atualizada.
    """
    ficha = await _get_ficha_or_404(session, tenant_id, orcamento_id, ficha_id)
    old_data = {
        "descricao": ficha.descricao,
        "quantidade": str(ficha.quantidade),
        "custo_unitario": str(ficha.custo_unitario),
        "tipo_precificacao": ficha.tipo_precificacao,
    }
    data = payload.model_dump(exclude_unset=True)
    for field in ("quantidade", "custo_unitario"):
        if field in data and data[field] is not None:
            data[field] = str(data[field])
    if "parametros_precificacao" in data and data["parametros_precificacao"] is not None:
        data["parametros_precificacao"] = data["parametros_precificacao"].model_dump_json()
    for field, value in data.items():
        setattr(ficha, field, value)

    await session.flush()
    await log_audit_action(
        session=session,
        user_id=current_user.id,
        tenant_id=tenant_id,
        action="PATCH",
        resource_type="Ficha",
        resource_id=str(ficha.id),
        old_value=old_data,
        new_value=data,
    )
    await session.commit()
    await session.refresh(ficha)
    return ficha


@router.delete(
    "/{ficha_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deletar ficha",
    description="Remove uma ficha do orçamento. Retorna 404 se não encontrada. Requer MFA ativado.",
    responses={**RESPONSES_CRUD_READ},
    dependencies=[Depends(require_mfa)],
)
async def deletar_ficha(
    orcamento_id: uuid.UUID,
    ficha_id: uuid.UUID,
    session: SessionDep,
    tenant_id: TenantIDDep,
    current_user: Usuario = Depends(get_current_user),
) -> None:
    """
    Remove uma ficha do sistema.

    Args:
        orcamento_id: ID do orçamento.
        ficha_id: ID da ficha a ser removida.
        session: Sessão do banco de dados.
        tenant_id: ID do tenant.
        current_user: Usuário realizando a exclusão.
    """
    ficha = await _get_ficha_or_404(session, tenant_id, orcamento_id, ficha_id)
    old_data = {"descricao": ficha.descricao, "id": str(ficha.id)}

    await session.delete(ficha)
    await session.flush()
    await log_audit_action(
        session=session,
        user_id=current_user.id,
        tenant_id=tenant_id,
        action="DELETE",
        resource_type="Ficha",
        resource_id=str(ficha.id),
        old_value=old_data,
        new_value=None,
    )
    await session.commit()


@router.post(
    "/{ficha_id}/calcular",
    response_model=FichaCalcResult,
    summary="Calcular preço unitário da ficha",
    description=(
        "Executa o **pricing engine** para calcular o preço unitário da ficha "
        "com base no `custo_unitario` e nos `parametros_precificacao` configurados.\n\n"
        "O resultado é persistido em `preco_unitario_calculado` (snapshot) e retornado "
        "com detalhes do cálculo.\n\n"
        "**Modos suportados:**\n\n"
        "| Modo | Fórmula |\n"
        "|------|--------|\n"
        "| `markup` | `preço = custo / (1 − tributos − lucro − indiretas)` |\n"
        "| `bdi_manual` | Componentes sobre receita/custo |\n"
        "| `bdi_classico` | `preço = custo × (1 + BDI)` — fórmula DNIT |"
    ),
    response_description="Resultado do cálculo com preço unitário, divisor e detalhes.",
    responses={**RESPONSES_ACTION},
)
async def calcular_preco(
    orcamento_id: uuid.UUID,
    ficha_id: uuid.UUID,
    session: SessionDep,
    tenant_id: TenantIDDep,
) -> FichaCalcResult:
    """
    Executa o cálculo de preço unitário da ficha usando o pricing engine.

    Aplica as regras de Markup ou BDI conforme configurado na ficha.

    Args:
        orcamento_id: ID do orçamento.
        ficha_id: ID da ficha a ser calculada.
        session: Sessão do banco de dados.
        tenant_id: ID do tenant.

    Returns:
        FichaCalcResult com o preço final e detalhes do cálculo.

    Raises:
        HTTPException: Se houver erro de validação nos parâmetros ou custo.
    """
    ficha = await _get_ficha_or_404(session, tenant_id, orcamento_id, ficha_id)
    custo = Decimal(ficha.custo_unitario)
    params = json.loads(ficha.parametros_precificacao) if ficha.parametros_precificacao else {}

    try:
        if ficha.tipo_precificacao == TipoPrecificacao.MARKUP:
            p_markup = MarkupParams(**params)
            res_markup = compute_unit_price(
                unit_cost=custo,
                tributes=p_markup.tributes,
                profit=p_markup.profit,
                indirect=p_markup.indirect,
            )
            resultado = FichaCalcResult(
                ficha_id=ficha.id,
                preco_unitario=str(res_markup.unit_price),
                divisor=str(res_markup.divisor),
                is_alert=res_markup.is_alert,
                detalhes={"total_components": str(res_markup.total_components)},
            )

        elif ficha.tipo_precificacao == TipoPrecificacao.BDI_MANUAL:
            p_manual = BdiManualParams(**params)
            components = [
                BdiComponent(
                    name=c.name,
                    percent=c.percent,
                    base=ComponentBase(c.base),
                    legal_reference=c.legal_reference,
                )
                for c in p_manual.components
            ]
            res_manual = compute_price_manual(unit_cost=custo, components=components)
            resultado = FichaCalcResult(
                ficha_id=ficha.id,
                preco_unitario=str(res_manual.unit_price),
                is_alert=res_manual.is_alert,
                detalhes={"t_revenue": str(res_manual.t_revenue), "t_cost": str(res_manual.t_cost)},
            )

        else:  # BDI_CLASSICO
            p_classic = BdiClassicoParams(**params)
            inputs = ClassicBdiInputs(
                administration=p_classic.administration,
                financial=p_classic.financial,
                risk=p_classic.risk,
                profit=p_classic.profit,
                tributes=p_classic.tributes,
            )
            res_classic = compute_price_classic(unit_cost=custo, inputs=inputs)
            resultado = FichaCalcResult(
                ficha_id=ficha.id,
                preco_unitario=str(res_classic.unit_price),
                is_alert=res_classic.is_alert,
                detalhes={"bdi": str(res_classic.bdi)},
            )

    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc))

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
