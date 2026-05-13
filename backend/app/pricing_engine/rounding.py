"""Modos de arredondamento configuráveis por tenant.

PRD v2.0 §3.5: ROUND_HALF_EVEN (banker's) é o padrão para reduzir viés
sistemático em totais; ROUND_HALF_UP (comercial) atende solicitações de
tenants que esperam comportamento "Excel-like".
"""

from __future__ import annotations

from decimal import ROUND_HALF_EVEN, ROUND_HALF_UP, Decimal
from enum import StrEnum

from app.pricing_engine.decimal_config import quantize_money, quantize_pct


class RoundingMode(StrEnum):
    BANKER = "banker"  # ROUND_HALF_EVEN — default
    COMMERCIAL = "commercial"  # ROUND_HALF_UP


_DECIMAL_RULE = {
    RoundingMode.BANKER: ROUND_HALF_EVEN,
    RoundingMode.COMMERCIAL: ROUND_HALF_UP,
}


def round_money(value: Decimal, mode: RoundingMode = RoundingMode.BANKER) -> Decimal:
    """Arredonda para 2 casas com o modo informado."""
    return quantize_money(value, rounding=_DECIMAL_RULE[mode])


def round_pct(value: Decimal, mode: RoundingMode = RoundingMode.BANKER) -> Decimal:
    """Arredonda percentual para 6 casas."""
    return quantize_pct(value, rounding=_DECIMAL_RULE[mode])
