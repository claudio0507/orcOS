"""
Configuração global de Decimal para o motor de pricing.

PRD v2.0 §3.5: todos os campos monetários e percentuais são `DECIMAL(18, 6)` no
banco; cálculos intermediários usam contexto com precisão 28 (cabe DECIMAL(28,*)
sem perda). Arredondamento final em ROUND_HALF_EVEN (banker's), configurável
para ROUND_HALF_UP (comercial) por tenant via `rounding.RoundingMode`.
"""

from __future__ import annotations

from decimal import Decimal, getcontext
from typing import Final

CALCULATION_PRECISION: Final[int] = 28
getcontext().prec = CALCULATION_PRECISION

MONEY_QUANT: Final[Decimal] = Decimal("0.01")
PCT_QUANT: Final[Decimal] = Decimal("0.000001")


def money(value: str | int | float | Decimal) -> Decimal:
    """Build a Decimal from a value without quantizing.

    Uses str() to avoid binary-float artifacts (Decimal(0.1) != Decimal('0.1')).
    """
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def pct(value: str | int | float | Decimal) -> Decimal:
    """Build a percentage Decimal in fractional form (0.15 == 15%)."""
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def quantize_money(value: Decimal, rounding: str) -> Decimal:
    """Quantize a Decimal to monetary precision (2 places) with given rounding mode."""
    return value.quantize(MONEY_QUANT, rounding=rounding)


def quantize_pct(value: Decimal, rounding: str) -> Decimal:
    """Quantize a Decimal to percentage precision (6 places)."""
    return value.quantize(PCT_QUANT, rounding=rounding)
