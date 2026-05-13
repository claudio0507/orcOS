"""
Markup divisor — PRD v2.0 §3.5.3.

Dado:
    T = tributos sobre faturamento
    L = margem de lucro desejada
    D = despesas indiretas sobre faturamento

    markup_divisor = 1 - (T + L + D)
    unit_price     = unit_cost / markup_divisor

Guards (PRD §3.5.3):
    - T + L + D < guard  (default 95%; alerta a 70%, bloqueio a 95%).
    - Denominador <= 0  → MarkupGuardError.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Final

from app.pricing_engine.exceptions import MarkupGuardError
from app.pricing_engine.rounding import RoundingMode, round_money

DEFAULT_GUARD: Final[Decimal] = Decimal("0.95")
DEFAULT_ALERT: Final[Decimal] = Decimal("0.70")


@dataclass(frozen=True, slots=True)
class MarkupResult:
    total_components: Decimal  # T + L + D (fractional)
    divisor: Decimal  # 1 - total_components
    unit_price: Decimal  # unit_cost / divisor (rounded)
    is_alert: bool  # total_components >= alert threshold


def compute_markup_divisor(
    *,
    tributes: Decimal,
    profit: Decimal,
    indirect: Decimal,
    guard: Decimal = DEFAULT_GUARD,
) -> Decimal:
    """
    Calcula o divisor de markup 1 - (T + L + D).

    Aplica limites de segurança (guards) para evitar margens negativas ou excessivas.

    Args:
        tributes: Tributos sobre o faturamento (T).
        profit: Margem de lucro desejada (L).
        indirect: Despesas indiretas sobre o faturamento (D).
        guard: Limite máximo para a soma dos componentes.

    Returns:
        O divisor calculado para ser usado no cálculo do preço.

    Raises:
        MarkupGuardError: Se a soma T + L + D ultrapassar o limite guard.
    """
    total = tributes + profit + indirect
    if total >= guard:
        raise MarkupGuardError(total=total, guard=guard)
    divisor = Decimal("1") - total
    if divisor <= 0:  # pragma: no cover - defensive; guard<=1 already prevents this.
        raise MarkupGuardError(total=total, guard=guard)
    return divisor


def compute_unit_price(
    *,
    unit_cost: Decimal,
    tributes: Decimal,
    profit: Decimal,
    indirect: Decimal,
    guard: Decimal = DEFAULT_GUARD,
    alert: Decimal = DEFAULT_ALERT,
    rounding: RoundingMode = RoundingMode.BANKER,
) -> MarkupResult:
    """
    Calcula o preço unitário aplicando o markup divisor sobre o custo.

    Args:
        unit_cost: Custo unitário direto.
        tributes: Tributos sobre o faturamento.
        profit: Margem de lucro desejada.
        indirect: Despesas indiretas sobre o faturamento.
        guard: Limite máximo para a soma dos componentes.
        alert: Limite para disparar flag de alerta.
        rounding: Modo de arredondamento a ser aplicado.

    Returns:
        MarkupResult contendo o divisor, o preço calculado e flag de alerta.
    """
    divisor = compute_markup_divisor(
        tributes=tributes, profit=profit, indirect=indirect, guard=guard
    )
    total = tributes + profit + indirect
    raw_price = unit_cost / divisor
    return MarkupResult(
        total_components=total,
        divisor=divisor,
        unit_price=round_money(raw_price, mode=rounding),
        is_alert=total >= alert,
    )
