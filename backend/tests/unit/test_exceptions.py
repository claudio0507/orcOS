"""Unit tests for exceptions.py — pricing engine error hierarchy."""
from __future__ import annotations

from decimal import Decimal

import pytest

from app.pricing_engine.exceptions import (
    BdiGuardError,
    CycleError,
    InvalidProductivityError,
    MarkupGuardError,
    PricingEngineError,
    SpreadingError,
)


def test_pricing_engine_error_base():
    """Base error can be raised and caught."""
    with pytest.raises(PricingEngineError):
        raise PricingEngineError("Test error")


def test_markup_guard_error_attributes():
    """MarkupGuardError stores total and guard."""
    error = MarkupGuardError(total=Decimal("0.96"), guard=Decimal("0.95"))
    assert error.total == Decimal("0.96")
    assert error.guard == Decimal("0.95")
    assert "0.96" in str(error)
    assert "0.95" in str(error)


def test_bdi_guard_error_attributes():
    """BdiGuardError stores message, total, and guard."""
    msg = "Tributos excedem limite"
    error = BdiGuardError(message=msg, total=Decimal("0.97"), guard=Decimal("0.95"))
    assert error.total == Decimal("0.97")
    assert error.guard == Decimal("0.95")
    assert msg in str(error)


def test_invalid_productivity_error_attributes():
    """InvalidProductivityError stores prod_dia."""
    error = InvalidProductivityError(prod_dia=Decimal("-5"))
    assert error.prod_dia == Decimal("-5")
    assert "-5" in str(error)


def test_spreading_error():
    """SpreadingError can be raised."""
    with pytest.raises(SpreadingError) as exc:
        raise SpreadingError("Invalid spread configuration")
    assert "Invalid" in str(exc.value)


def test_cycle_error_path():
    """CycleError stores and formats the cycle path."""
    path = ["A", "B", "C", "A"]
    error = CycleError(path=path)
    assert error.path == path
    assert "A" in str(error)
    assert "B" in str(error)
    assert "->" in str(error)


def test_cycle_error_single_node():
    """CycleError with self-loop."""
    error = CycleError(path=["X", "X"])
    assert error.path == ["X", "X"]


def test_error_inheritance():
    """All custom errors inherit from PricingEngineError."""
    assert issubclass(MarkupGuardError, PricingEngineError)
    assert issubclass(BdiGuardError, PricingEngineError)
    assert issubclass(InvalidProductivityError, PricingEngineError)
    assert issubclass(SpreadingError, PricingEngineError)
    assert issubclass(CycleError, PricingEngineError)
