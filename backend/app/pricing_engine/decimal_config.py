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
    """
    Cria um objeto Decimal a partir de um valor de entrada sem quantização.

    Args:
        value: Valor numérico ou string.

    Returns:
        Objeto Decimal correspondente.
    """
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def pct(value: str | int | float | Decimal) -> Decimal:
    """
    Cria um objeto Decimal representando um percentual em forma fracionária.

    Args:
        value: Valor numérico ou string (ex: "0.15" para 15%).

    Returns:
        Objeto Decimal correspondente.
    """
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def quantize_money(value: Decimal, rounding: str) -> Decimal:
    """
    Arredonda um valor Decimal para precisão monetária (2 casas decimais).

    Args:
        value: O valor a ser arredondado.
        rounding: A regra de arredondamento da biblioteca decimal (ex: ROUND_HALF_EVEN).

    Returns:
        Valor quantizado para 2 casas decimais.
    """
    return value.quantize(MONEY_QUANT, rounding=rounding)


def quantize_pct(value: Decimal, rounding: str) -> Decimal:
    """
    Arredonda um valor Decimal para precisão de percentual (6 casas decimais).

    Args:
        value: O valor a ser arredondado.
        rounding: A regra de arredondamento da biblioteca decimal.

    Returns:
        Valor quantizado para 6 casas decimais.
    """
    return value.quantize(PCT_QUANT, rounding=rounding)
