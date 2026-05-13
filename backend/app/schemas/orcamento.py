"""Schemas Pydantic v2 — Orcamento (request / response DTOs)."""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class OrcamentoCreate(BaseModel):
    titulo: str = Field(..., min_length=1, max_length=500)
    descricao: str | None = None
    custo_fixo_total: Decimal = Field(default=Decimal("0"), ge=0)


class OrcamentoUpdate(BaseModel):
    titulo: str | None = Field(None, min_length=1, max_length=500)
    descricao: str | None = None
    status: str | None = None
    custo_fixo_total: Decimal | None = Field(None, ge=0)


class OrcamentoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    criado_por_id: uuid.UUID | None
    titulo: str
    descricao: str | None
    status: str
    custo_fixo_total: str
    created_at: datetime
    updated_at: datetime


class OrcamentoList(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[OrcamentoRead]
    total: int
