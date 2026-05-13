"""
orcOS pricing engine.

Motor de cálculo financeiro do sistema Alta Noroeste. Decimal-only, sem efeitos
colaterais (I/O ou banco). Pode ser embutido em workers, na API ou usado
standalone para back-office.

Conceitos formalizados conforme PRD v2.0 §3.5:

- Custo m² = Custo Dia / PROD_DIA (com guard PROD_DIA > 0)
- Markup divisor com guard de soma de tributos+lucro+despesas
- BDI em dois modos coexistentes (Manual da Empresa e Clássico TCU)
- Spreading de fixos com invariante de conservação
- Depreciação linear (extensível)
- Detecção de ciclo em BOM
"""

from app.pricing_engine.decimal_config import (
    MONEY_QUANT,
    PCT_QUANT,
    money,
    pct,
    quantize_money,
    quantize_pct,
)
from app.pricing_engine.exceptions import (
    BdiGuardError,
    CycleError,
    InvalidProductivityError,
    MarkupGuardError,
    PricingEngineError,
    SpreadingError,
)

__all__ = [
    "MONEY_QUANT",
    "PCT_QUANT",
    "BdiGuardError",
    "CycleError",
    "InvalidProductivityError",
    "MarkupGuardError",
    "PricingEngineError",
    "SpreadingError",
    "money",
    "pct",
    "quantize_money",
    "quantize_pct",
]
