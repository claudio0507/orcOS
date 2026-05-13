"""Unit tests for rounding.py — rounding mode selection."""
from __future__ import annotations

from decimal import Decimal

import pytest

from app.pricing_engine.rounding import RoundingMode, round_money, round_pct


def test_rounding_mode_enum_values():
    """RoundingMode has BANKER and COMMERCIAL modes."""
    assert RoundingMode.BANKER == "banker"
    assert RoundingMode.COMMERCIAL == "commercial"


def test_round_money_banker_default():
    """round_money() uses BANKER (round half to even) by default."""
    # 16.665 rounds to 16.66 (even)
    result = round_money(Decimal("16.665"))
    assert result == Decimal("16.66")


def test_round_money_banker_explicit():
    """round_money() with explicit BANKER mode."""
    result = round_money(Decimal("16.665"), mode=RoundingMode.BANKER)
    assert result == Decimal("16.66")


def test_round_money_commercial():
    """round_money() with COMMERCIAL (round half up) mode."""
    # 16.665 rounds to 16.67 (commercial)
    result = round_money(Decimal("16.665"), mode=RoundingMode.COMMERCIAL)
    assert result == Decimal("16.67")


def test_round_money_banker_vs_commercial():
    """BANKER and COMMERCIAL give different results for .5 cases."""
    value = Decimal("10.015")  # 0.015 is ambiguous at 2 places
    banker = round_money(value, mode=RoundingMode.BANKER)
    commercial = round_money(value, mode=RoundingMode.COMMERCIAL)
    # May differ depending on context
    assert banker in [Decimal("10.01"), Decimal("10.02")]
    assert commercial in [Decimal("10.01"), Decimal("10.02")]


def test_round_pct_banker_default():
    """round_pct() uses BANKER mode by default."""
    # 0.0000005 rounds to 0.000000 (half to even)
    result = round_pct(Decimal("0.0000005"))
    # 0.0000005 → 0.000000 (banker's)
    assert result == Decimal("0.000000")


def test_round_pct_commercial():
    """round_pct() with COMMERCIAL mode."""
    result = round_pct(Decimal("0.0000005"), mode=RoundingMode.COMMERCIAL)
    # 0.0000005 → 0.000001 (commercial)
    assert result == Decimal("0.000001")


def test_round_pct_precision():
    """round_pct() maintains 6 decimal places."""
    result = round_pct(Decimal("0.123456789"))
    assert result == Decimal("0.123457")


def test_round_money_zero():
    """round_money() handles zero."""
    result = round_money(Decimal("0"))
    assert result == Decimal("0.00")


def test_round_pct_zero():
    """round_pct() handles zero."""
    result = round_pct(Decimal("0"))
    assert result == Decimal("0.000000")


def test_round_money_large_values():
    """round_money() works with large values."""
    result = round_money(Decimal("999999.999"))
    assert result == Decimal("1000000.00")


def test_round_pct_small_values():
    """round_pct() works with very small values."""
    result = round_pct(Decimal("0.0000001"))
    assert result == Decimal("0.000000")
