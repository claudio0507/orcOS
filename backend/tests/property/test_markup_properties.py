"""Property-based tests for markup divisor (PRD §3.5.3)."""

from __future__ import annotations

from decimal import Decimal

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from app.pricing_engine.exceptions import MarkupGuardError
from app.pricing_engine.markup import (
    DEFAULT_GUARD,
    compute_markup_divisor,
    compute_unit_price,
)


def pct_strategy(max_value: str = "1.5") -> st.SearchStrategy[Decimal]:
    return st.decimals(
        min_value=Decimal("0"),
        max_value=Decimal(max_value),
        places=4,
        allow_nan=False,
        allow_infinity=False,
    )


@settings(deadline=None, max_examples=200, suppress_health_check=[HealthCheck.too_slow])
@given(t=pct_strategy(), l=pct_strategy(), d=pct_strategy())
def test_guard_blocks_sum_at_or_above_guard(t: Decimal, l: Decimal, d: Decimal) -> None:  # noqa: E741
    """Para qualquer (T, L, D), o motor ou aceita (sum < guard) ou rejeita com MarkupGuardError."""
    total = t + l + d
    if total >= DEFAULT_GUARD:
        with pytest.raises(MarkupGuardError):
            compute_markup_divisor(tributes=t, profit=l, indirect=d)
    else:
        divisor = compute_markup_divisor(tributes=t, profit=l, indirect=d)
        assert divisor == Decimal("1") - total
        assert divisor > 0


@settings(deadline=None, max_examples=200)
@given(
    cost=st.decimals(
        min_value=Decimal("0.01"),
        max_value=Decimal("1000000"),
        places=2,
        allow_nan=False,
        allow_infinity=False,
    ),
    t=pct_strategy("0.30"),
    l=pct_strategy("0.30"),
    d=pct_strategy("0.20"),
)
def test_price_grows_with_components(cost: Decimal, t: Decimal, l: Decimal, d: Decimal) -> None:  # noqa: E741
    """Aumentar T, L ou D (mantendo sum < guard) sempre aumenta (ou mantém) o preço."""
    total = t + l + d
    assume(total < Decimal("0.80"))  # margem de segurança vs guard

    base = compute_unit_price(unit_cost=cost, tributes=t, profit=l, indirect=d)
    bumped = compute_unit_price(
        unit_cost=cost,
        tributes=t + Decimal("0.05"),
        profit=l,
        indirect=d,
    )
    assert bumped.unit_price >= base.unit_price


@settings(deadline=None, max_examples=100)
@given(
    cost=st.decimals(
        min_value=Decimal("1"),
        max_value=Decimal("10000"),
        places=2,
        allow_nan=False,
        allow_infinity=False,
    ),
)
def test_zero_components_yields_cost_itself(cost: Decimal) -> None:
    """T=L=D=0 → preço unitário == custo (a menos de arredondamento monetário)."""
    result = compute_unit_price(
        unit_cost=cost, tributes=Decimal("0"), profit=Decimal("0"), indirect=Decimal("0")
    )
    assert result.unit_price == cost.quantize(Decimal("0.01"))
    assert result.divisor == Decimal("1")
