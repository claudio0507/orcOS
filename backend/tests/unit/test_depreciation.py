"""Unit tests for depreciation.py — linear depreciation calculation."""
from __future__ import annotations

from decimal import Decimal

import pytest

from app.pricing_engine.depreciation import DepreciationMethod, linear_daily
from app.pricing_engine.exceptions import PricingEngineError
from app.pricing_engine.rounding import RoundingMode


def test_linear_daily_basic():
    """Linear depreciation: (10000 - 1000) / 365 days."""
    result = linear_daily(
        acquisition=Decimal("10000.00"),
        residual=Decimal("1000.00"),
        useful_life_days=365,
    )
    assert result.method == DepreciationMethod.LINEAR
    assert result.acquisition == Decimal("10000.00")
    assert result.residual == Decimal("1000.00")
    assert result.useful_life_days == 365
    # (10000 - 1000) / 365 = 24.657534... ≈ 24.66
    assert result.daily == Decimal("24.66")


def test_linear_daily_zero_residual():
    """Depreciation with zero residual value."""
    result = linear_daily(
        acquisition=Decimal("5000.00"),
        residual=Decimal("0"),
        useful_life_days=500,
    )
    # 5000 / 500 = 10.00
    assert result.daily == Decimal("10.00")


def test_linear_daily_zero_acquisition():
    """Item with zero acquisition cost has zero daily depreciation."""
    result = linear_daily(
        acquisition=Decimal("0"),
        residual=Decimal("0"),
        useful_life_days=365,
    )
    assert result.daily == Decimal("0.00")


def test_linear_daily_small_values():
    """Handles very small acquisition values with rounding."""
    result = linear_daily(
        acquisition=Decimal("10.00"),
        residual=Decimal("1.00"),
        useful_life_days=30,
    )
    # (10 - 1) / 30 = 0.30
    assert result.daily == Decimal("0.30")


def test_useful_life_days_must_be_positive():
    """useful_life_days <= 0 raises PricingEngineError."""
    with pytest.raises(PricingEngineError) as exc:
        linear_daily(
            acquisition=Decimal("1000"),
            residual=Decimal("0"),
            useful_life_days=0,
        )
    assert "useful_life_days deve ser > 0" in str(exc.value)

    with pytest.raises(PricingEngineError):
        linear_daily(
            acquisition=Decimal("1000"),
            residual=Decimal("0"),
            useful_life_days=-5,
        )


def test_acquisition_must_be_non_negative():
    """Negative acquisition raises PricingEngineError."""
    with pytest.raises(PricingEngineError) as exc:
        linear_daily(
            acquisition=Decimal("-100"),
            residual=Decimal("0"),
            useful_life_days=365,
        )
    assert "acquisition deve ser >= 0" in str(exc.value)


def test_residual_must_be_non_negative():
    """Negative residual raises PricingEngineError."""
    with pytest.raises(PricingEngineError) as exc:
        linear_daily(
            acquisition=Decimal("1000"),
            residual=Decimal("-50"),
            useful_life_days=365,
        )
    assert "residual deve ser >= 0" in str(exc.value)


def test_residual_cannot_exceed_acquisition():
    """Residual > acquisition raises PricingEngineError."""
    with pytest.raises(PricingEngineError) as exc:
        linear_daily(
            acquisition=Decimal("1000"),
            residual=Decimal("1100"),
            useful_life_days=365,
        )
    assert "residual" in str(exc.value) and "não pode ser maior" in str(exc.value)


def test_residual_equals_acquisition_yields_zero():
    """When residual == acquisition, daily depreciation is zero."""
    result = linear_daily(
        acquisition=Decimal("1000.00"),
        residual=Decimal("1000.00"),
        useful_life_days=365,
    )
    assert result.daily == Decimal("0.00")


def test_rounding_mode_banker():
    """Default rounding mode is BANKER (round half to even)."""
    result = linear_daily(
        acquisition=Decimal("100.00"),
        residual=Decimal("0"),
        useful_life_days=6,  # 100/6 = 16.66666...
        rounding=RoundingMode.BANKER,
    )
    # 16.66666... → 16.67 (banker's rounding)
    assert result.daily == Decimal("16.67")


def test_rounding_mode_commercial():
    """Can specify COMMERCIAL (ROUND_HALF_UP) rounding mode."""
    result = linear_daily(
        acquisition=Decimal("100.00"),
        residual=Decimal("0"),
        useful_life_days=3,  # 100/3 = 33.33333...
        rounding=RoundingMode.COMMERCIAL,
    )
    # 33.33333... → 33.33
    assert result.daily == Decimal("33.33")


def test_depreciation_result_frozen():
    """DepreciationResult is immutable."""
    result = linear_daily(
        acquisition=Decimal("1000"),
        residual=Decimal("100"),
        useful_life_days=365,
    )
    with pytest.raises(AttributeError):
        result.daily = Decimal("999")  # type: ignore


def test_depreciation_result_slots():
    """DepreciationResult uses __slots__ for memory efficiency."""
    result = linear_daily(
        acquisition=Decimal("1000"),
        residual=Decimal("0"),
        useful_life_days=365,
    )
    # Should not have __dict__ due to slots
    assert not hasattr(result, "__dict__")
