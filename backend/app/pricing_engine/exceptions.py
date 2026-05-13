"""Hierarquia de erros do motor de pricing.

Todos os erros derivam de `PricingEngineError` para permitir try/except amplo
no boundary HTTP (mapeia tipicamente para HTTP 422 com payload estruturado).
"""

from __future__ import annotations

from decimal import Decimal


class PricingEngineError(Exception):
    """Erro de domínio do motor de pricing."""


class MarkupGuardError(PricingEngineError):
    """Soma de tributos+lucro+despesas excede o limite seguro do markup divisor."""

    def __init__(self, total: Decimal, guard: Decimal) -> None:
        super().__init__(
            f"Soma de tributos/lucro/despesas ({total}) excede o limite seguro ({guard})."
        )
        self.total = total
        self.guard = guard


class BdiGuardError(PricingEngineError):
    """Composição do BDI viola o guard (denominador <= 0 ou soma >= 95%)."""

    def __init__(self, message: str, total: Decimal, guard: Decimal) -> None:
        super().__init__(message)
        self.total = total
        self.guard = guard


class InvalidProductivityError(PricingEngineError):
    """PROD/DIA <= 0 — divisão impossível."""

    def __init__(self, prod_dia: Decimal) -> None:
        super().__init__(f"PROD/DIA deve ser > 0 (recebido: {prod_dia}).")
        self.prod_dia = prod_dia


class SpreadingError(PricingEngineError):
    """Configuração inválida para spreading (linhas vazias, qty<=0, soma zero, etc)."""


class CycleError(PricingEngineError):
    """Ciclo detectado no BOM. `path` lista os IDs no ciclo (início→fim==início)."""

    def __init__(self, path: list[str]) -> None:
        super().__init__(f"Ciclo no BOM: {' -> '.join(path)}")
        self.path = path
