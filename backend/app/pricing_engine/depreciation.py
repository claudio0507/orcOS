"""
Depreciação de Ferramental, EPI e Frota — PRD v2.0 §3.5.2.

Esta iteração entrega o método **Linear** (padrão). Métodos alternativos (soma
dos dígitos, acelerada) serão adicionados quando o domínio confirmar a regra
contábil interna da Alta Noroeste — a interface `DepreciationMethod` já
contempla extensão.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from app.pricing_engine.exceptions import PricingEngineError
from app.pricing_engine.rounding import RoundingMode, round_money


class DepreciationMethod(StrEnum):
    LINEAR = "linear"


@dataclass(frozen=True, slots=True)
class DepreciationResult:
    daily: Decimal
    method: DepreciationMethod
    acquisition: Decimal
    residual: Decimal
    useful_life_days: int


def linear_daily(
    *,
    acquisition: Decimal,
    residual: Decimal,
    useful_life_days: int,
    rounding: RoundingMode = RoundingMode.BANKER,
) -> DepreciationResult:
    """
    Calcula a depreciação linear diária de um ativo.

    Fórmula: depreciação = (aquisição - residual) / vida_útil_dias.

    Args:
        acquisition: Valor de aquisição do ativo.
        residual: Valor residual ao final da vida útil.
        useful_life_days: Vida útil estimada em dias.
        rounding: Modo de arredondamento a ser aplicado.

    Returns:
        DepreciationResult contendo o valor diário e metadados.

    Raises:
        PricingEngineError: Se parâmetros forem negativos ou vida útil for zero.
    """
    if useful_life_days <= 0:
        raise PricingEngineError(
            f"useful_life_days deve ser > 0 (recebido: {useful_life_days})."
        )
    if acquisition < 0:
        raise PricingEngineError(f"acquisition deve ser >= 0 (recebido: {acquisition}).")
    if residual < 0:
        raise PricingEngineError(f"residual deve ser >= 0 (recebido: {residual}).")
    if residual > acquisition:
        raise PricingEngineError(
            f"residual ({residual}) não pode ser maior que acquisition ({acquisition})."
        )

    raw_daily = (acquisition - residual) / Decimal(useful_life_days)
    return DepreciationResult(
        daily=round_money(raw_daily, mode=rounding),
        method=DepreciationMethod.LINEAR,
        acquisition=acquisition,
        residual=residual,
        useful_life_days=useful_life_days,
    )
