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
    """Calcula o divisor `1 - (T + L + D)` aplicando guards.

    Raises:
        MarkupGuardError: se T + L + D >= guard (denominador resultante <= (1-guard)).
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
    """Aplica markup divisor sobre o custo unitário.

    Retorna estrutura com divisor, preço final arredondado e flag de alerta
    (70% ≤ T+L+D < 95% por padrão).
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
