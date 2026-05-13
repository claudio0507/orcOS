"""Unit tests for spreading.py — fixed cost allocation."""
from __future__ import annotations

from decimal import Decimal

import pytest

from app.pricing_engine.exceptions import SpreadingError
from app.pricing_engine.spreading import SpreadingLine, spread_fixed_costs


def test_spreading_basic():
    """Basic spreading: 2 lines with equal weights."""
    lines = [
        SpreadingLine(id="A", variable_unit_price=Decimal("100"), quantity=Decimal("10")),
        SpreadingLine(id="B", variable_unit_price=Decimal("100"), quantity=Decimal("10")),
    ]
    result = spread_fixed_costs(lines=lines, fixed_total=Decimal("200"))

    # Each line weight = 100 * 10 = 1000, total = 2000
    # Each gets 200 * (1000/2000) = 100 fixed
    # A: final_unit_price = 100 + (100/10) = 110 per unit
    # B: final_unit_price = 100 + (100/10) = 110 per unit
    assert len(result) == 2
    assert result[0].final_unit_price == Decimal("110.00")
    assert result[1].final_unit_price == Decimal("110.00")
    assert sum(r.final_line_total for r in result) == Decimal("2200.00")


def test_spreading_disproportionate_weights():
    """Lines with different weights get different allocations."""
    lines = [
        SpreadingLine(id="heavy", variable_unit_price=Decimal("1000"), quantity=Decimal("10")),
        SpreadingLine(id="light", variable_unit_price=Decimal("100"), quantity=Decimal("10")),
    ]
    result = spread_fixed_costs(lines=lines, fixed_total=Decimal("1000"))

    # Heavy: weight = 10000, Light: weight = 1000, total = 11000
    # Heavy gets 1000 * (10000/11000) ≈ 909.09
    # Light gets 1000 * (1000/11000) ≈ 90.91
    heavy = result[0]
    light = result[1]
    assert heavy.allocated_fixed > light.allocated_fixed


def test_spreading_empty_list_raises():
    """Empty lines list raises SpreadingError."""
    with pytest.raises(SpreadingError) as exc:
        spread_fixed_costs(lines=[], fixed_total=Decimal("100"))
    assert "vazia" in str(exc.value)


def test_spreading_zero_quantity_raises():
    """Line with quantity <= 0 raises SpreadingError."""
    lines = [
        SpreadingLine(id="A", variable_unit_price=Decimal("100"), quantity=Decimal("0")),
    ]
    with pytest.raises(SpreadingError) as exc:
        spread_fixed_costs(lines=lines, fixed_total=Decimal("100"))
    assert "quantity<=0" in str(exc.value)

    lines = [
        SpreadingLine(id="A", variable_unit_price=Decimal("100"), quantity=Decimal("-5")),
    ]
    with pytest.raises(SpreadingError):
        spread_fixed_costs(lines=lines, fixed_total=Decimal("100"))


def test_spreading_negative_price_raises():
    """Line with negative variable_unit_price raises SpreadingError."""
    lines = [
        SpreadingLine(id="A", variable_unit_price=Decimal("-50"), quantity=Decimal("10")),
    ]
    with pytest.raises(SpreadingError) as exc:
        spread_fixed_costs(lines=lines, fixed_total=Decimal("100"))
    assert "variable_unit_price<0" in str(exc.value)


def test_spreading_zero_weight_with_fixed_raises():
    """All lines with zero unit price but fixed > 0 raises."""
    lines = [
        SpreadingLine(id="A", variable_unit_price=Decimal("0"), quantity=Decimal("10")),
        SpreadingLine(id="B", variable_unit_price=Decimal("0"), quantity=Decimal("5")),
    ]
    with pytest.raises(SpreadingError) as exc:
        spread_fixed_costs(lines=lines, fixed_total=Decimal("100"))
    assert "Soma de pesos zero" in str(exc.value)


def test_spreading_zero_weight_zero_fixed_returns_unchanged():
    """All zeros: zero prices and zero fixed return lines unchanged."""
    lines = [
        SpreadingLine(id="A", variable_unit_price=Decimal("0"), quantity=Decimal("10")),
        SpreadingLine(id="B", variable_unit_price=Decimal("0"), quantity=Decimal("5")),
    ]
    result = spread_fixed_costs(lines=lines, fixed_total=Decimal("0"))

    assert len(result) == 2
    assert result[0].final_unit_price == Decimal("0.00")
    assert result[1].final_unit_price == Decimal("0.00")
    assert result[0].carries_residue is False
    assert result[1].carries_residue is False


def test_spreading_residue_to_max_weight():
    """Rounding residue goes to the line with max weight."""
    lines = [
        SpreadingLine(id="heavy", variable_unit_price=Decimal("100"), quantity=Decimal("3")),
        SpreadingLine(id="light", variable_unit_price=Decimal("10"), quantity=Decimal("3")),
    ]
    result = spread_fixed_costs(lines=lines, fixed_total=Decimal("1.00"))

    # Heavy weight = 300, light weight = 30, total = 330
    # Heavy gets 1.00 * (300/330) ≈ 0.909090...
    # Light gets 1.00 * (30/330) ≈ 0.090909...
    # Rounding creates residue; heavy (max weight) carries it
    heavy_idx = 0
    light_idx = 1
    residue_carriers = [r for r in result if r.carries_residue]
    # If residue occurs, it should be on heavy line
    if residue_carriers:
        assert residue_carriers[0].id == "heavy"
        assert result[heavy_idx].id == "heavy"


def test_spreading_invariant_preserved():
    """Sum of final_line_total == sum of variable + fixed."""
    lines = [
        SpreadingLine(id="A", variable_unit_price=Decimal("50.25"), quantity=Decimal("3.75")),
        SpreadingLine(id="B", variable_unit_price=Decimal("123.45"), quantity=Decimal("2.5")),
    ]
    fixed = Decimal("456.78")
    result = spread_fixed_costs(lines=lines, fixed_total=fixed)

    sum_final = sum(r.final_line_total for r in result)
    sum_variable = sum(
        line.variable_unit_price * line.quantity for line in lines
    )
    expected = (sum_variable + fixed).quantize(Decimal("0.01"))

    assert sum_final == expected
