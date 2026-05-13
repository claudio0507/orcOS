"""Schemas Pydantic v2 — Spreading (rateio de custos fixos)."""
from __future__ import annotations

import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class SpreadingRequest(BaseModel):
    """Payload opcional para override do custo fixo no momento do spreading.

    Se omitido, usa orcamento.custo_fixo_total.
    """

    custo_fixo_override: Decimal | None = Field(
        None,
        ge=0,
        description="Override do custo fixo total. Se None, usa o valor do orçamento.",
    )
    rounding: str = Field(
        default="banker",
        pattern="^(banker|commercial)$",
        description="Modo de arredondamento: 'banker' (default) ou 'commercial'.",
    )


class SpreadingResultLineRead(BaseModel):
    """Resultado do spreading por linha (ficha)."""

    model_config = ConfigDict(from_attributes=True)

    ficha_id: uuid.UUID
    descricao: str
    variable_unit_price: str
    quantity: str
    allocated_fixed: str
    final_unit_price: str
    final_line_total: str
    carries_residue: bool


class SpreadingResponse(BaseModel):
    """Resposta do endpoint de spreading."""

    orcamento_id: uuid.UUID
    custo_fixo_total: str
    total_variavel: str
    total_final: str
    residuo_aplicado: bool
    linhas: list[SpreadingResultLineRead]
    ca001_validado: bool = Field(
        ...,
        description=(
            "True se Σ(final_unit_price × qty) == "
            "Σ(variable_unit_price × qty) + fixed_total ± R$0.01"
        ),
    )
