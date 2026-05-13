"""Unit tests for decimal_config.py — Decimal configuration."""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

import pytest

from app.pricing_engine.decimal_config import (
    CALCULATION_PRECISION,
    MONEY_QUANT,
    PCT_QUANT,
    money,
    pct,
    quantize_money,
    quantize_pct,
)


def test_constants_are_defined():
    """Module constants are properly defined."""
    assert CALCULATION_PRECISION == 28
    assert MONEY_QUANT == Decimal("0.01")
    assert PCT_QUANT == Decimal("0.000001")


def test_money_from_string():
    """money() converts string to Decimal."""
    result = money("123.45")
    assert result == Decimal("123.45")
    assert isinstance(result, Decimal)


def test_money_from_int():
    """money() converts int to Decimal."""
    result = money(100)
    assert result == Decimal("100")


def test_money_from_float():
    """money() converts float to Decimal via string to avoid binary artifacts."""
    result = money(0.1)
    assert result == Decimal("0.1")
    assert result != Decimal(0.1)  # Decimal(float) has rounding errors


def test_money_from_decimal_passthrough():
    """money() with Decimal input returns it unchanged."""
    input_val = Decimal("500.50")
    result = money(input_val)
    assert result is input_val


def test_pct_from_string():
    """pct() converts string to Decimal."""
    result = pct("0.15")
    assert result == Decimal("0.15")


def test_pct_from_int():
    """pct() converts int to Decimal."""
    result = pct(50)
    assert result == Decimal("50")


def test_pct_from_float():
    """pct() converts float to Decimal via string."""
    result = pct(0.25)
    assert result == Decimal("0.25")


def test_pct_from_decimal_passthrough():
    """pct() with Decimal input returns it unchanged."""
    input_val = Decimal("0.075")
    result = pct(input_val)
    assert result is input_val


def test_quantize_money_to_2_places():
    """quantize_money() rounds to 2 decimal places."""
    value = Decimal("123.4567")
    result = quantize_money(value, rounding=ROUND_HALF_UP)
    assert result == Decimal("123.46")


def test_quantize_money_preserves_2_place():
    """quantize_money() preserves exact 2-place values."""
    value = Decimal("99.99")
    result = quantize_money(value, rounding=ROUND_HALF_UP)
    assert result == Decimal("99.99")


def test_quantize_pct_to_6_places():
    """quantize_pct() rounds to 6 decimal places."""
    value = Decimal("0.123456789")
    result = quantize_pct(value, rounding=ROUND_HALF_UP)
    assert result == Decimal("0.123457")


def test_quantize_pct_with_rounding_mode():
    """quantize_pct() respects rounding mode parameter."""
    value = Decimal("0.0000005")
    result = quantize_pct(value, rounding=ROUND_HALF_UP)
    assert result == Decimal("0.000001")
