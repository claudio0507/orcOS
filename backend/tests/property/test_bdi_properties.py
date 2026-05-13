"""Property-based tests for BDI (PRD §3.5.5) — ambos os modos."""

from __future__ import annotations

from decimal import Decimal

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from app.pricing_engine.bdi import (
    BdiComponent,
    ClassicBdiInputs,
    ComponentBase,
    compute_price_classic,
    compute_price_manual,
)
from app.pricing_engine.exceptions import BdiGuardError


def pct(max_value: str = "1.5") -> st.SearchStrategy[Decimal]:
    return st.decimals(
        min_value=Decimal("0"),
        max_value=Decimal(max_value),
        places=4,
        allow_nan=False,
        allow_infinity=False,
    )


def cost() -> st.SearchStrategy[Decimal]:
    return st.decimals(
        min_value=Decimal("0.01"),
        max_value=Decimal("1000000"),
        places=2,
        allow_nan=False,
        allow_infinity=False,
    )


@settings(deadline=None, max_examples=200, suppress_health_check=[HealthCheck.too_slow])
@given(unit_cost=cost(), t_rev=pct("1.5"), t_cost=pct("0.50"))
def test_manual_guard_consistency(unit_cost: Decimal, t_rev: Decimal, t_cost: Decimal) -> None:
    """Manual mode: aceita iff T_rev < 0.95; preço >= custo quando T_cost >= 0."""
    components = [
        BdiComponent("rev", t_rev, ComponentBase.REVENUE),
        BdiComponent("cost", t_cost, ComponentBase.COST),
    ]
    if t_rev >= Decimal("0.95"):
        with pytest.raises(BdiGuardError):
            compute_price_manual(unit_cost=unit_cost, components=components)
    else:
        result = compute_price_manual(unit_cost=unit_cost, components=components)
        # custo_ajustado = unit_cost * (1 + t_cost) >= unit_cost
        assert result.adjusted_cost >= unit_cost
        # preço >= custo (porque divisor <= 1 e custo_ajustado >= unit_cost)
        # com tolerância de arredondamento monetário (1 centavo)
        assert result.unit_price + Decimal("0.01") >= unit_cost.quantize(Decimal("0.01"))


@settings(deadline=None, max_examples=200)
@given(
    unit_cost=cost(),
    ac=pct("0.30"),
    df=pct("0.10"),
    r=pct("0.20"),
    l=pct("0.30"),
    t=pct("1.0"),
)
def test_classic_guard_consistency(
    unit_cost: Decimal,
    ac: Decimal,
    df: Decimal,
    r: Decimal,
    l: Decimal,  # noqa: E741
    t: Decimal,
) -> None:
    """Classic mode: aceita iff T < 0.95; com inputs >= 0 o preço resultante >= custo."""
    inputs = ClassicBdiInputs(
        administration=ac, financial=df, risk=r, profit=l, tributes=t
    )
    if t >= Decimal("0.95"):
        with pytest.raises(BdiGuardError):
            compute_price_classic(unit_cost=unit_cost, inputs=inputs)
    else:
        result = compute_price_classic(unit_cost=unit_cost, inputs=inputs)
        # BDI deve ser >= 0 quando todos os inputs são >= 0 (não há "preço negativo").
        assert result.bdi >= 0
        # preço >= custo (a menos de arredondamento)
        assert result.unit_price + Decimal("0.01") >= unit_cost.quantize(Decimal("0.01"))


@settings(deadline=None, max_examples=100)
@given(unit_cost=cost())
def test_classic_zero_inputs_equals_cost(unit_cost: Decimal) -> None:
    inputs = ClassicBdiInputs(
        administration=Decimal("0"),
        financial=Decimal("0"),
        risk=Decimal("0"),
        profit=Decimal("0"),
        tributes=Decimal("0"),
    )
    result = compute_price_classic(unit_cost=unit_cost, inputs=inputs)
    assert result.bdi == Decimal("0")
    assert result.unit_price == unit_cost.quantize(Decimal("0.01"))
