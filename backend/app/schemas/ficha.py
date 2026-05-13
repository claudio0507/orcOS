"""Schemas Pydantic v2 — Ficha + cálculo de precificação."""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.ficha import TipoPrecificacao


class MarkupParams(BaseModel):
    tributes: Decimal = Field(..., ge=0, lt=1)
    profit: Decimal = Field(..., ge=0, lt=1)
    indirect: Decimal = Field(..., ge=0, lt=1)


class BdiManualComponente(BaseModel):
    name: str
    percent: Decimal = Field(..., ge=0, lt=1)
    base: str  # "revenue" | "cost"
    legal_reference: str = ""


class BdiManualParams(BaseModel):
    components: list[BdiManualComponente]


class BdiClassicoParams(BaseModel):
    administration: Decimal = Field(..., ge=0, lt=1)
    financial: Decimal = Field(..., ge=0, lt=1)
    risk: Decimal = Field(..., ge=0, lt=1)
    profit: Decimal = Field(..., ge=0, lt=1)
    tributes: Decimal = Field(..., ge=0, lt=1)


class FichaCreate(BaseModel):
    descricao: str = Field(..., min_length=1, max_length=500)
    unidade: str = Field(default="un", max_length=50)
    quantidade: Decimal = Field(..., gt=0)
    custo_unitario: Decimal = Field(..., ge=0)
    tipo_precificacao: TipoPrecificacao = TipoPrecificacao.MARKUP
    parametros_precificacao: MarkupParams | BdiManualParams | BdiClassicoParams | None = None
    ordem: int = 0


class FichaUpdate(BaseModel):
    descricao: str | None = Field(None, min_length=1, max_length=500)
    unidade: str | None = None
    quantidade: Decimal | None = Field(None, gt=0)
    custo_unitario: Decimal | None = Field(None, ge=0)
    tipo_precificacao: TipoPrecificacao | None = None
    parametros_precificacao: MarkupParams | BdiManualParams | BdiClassicoParams | None = None
    ordem: int | None = None


class FichaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    orcamento_id: uuid.UUID
    descricao: str
    unidade: str
    quantidade: str
    custo_unitario: str
    tipo_precificacao: str
    preco_unitario_calculado: str | None
    ordem: int
    created_at: datetime
    updated_at: datetime


class FichaCalcResult(BaseModel):
    ficha_id: uuid.UUID
    preco_unitario: str
    divisor: str | None = None
    is_alert: bool
    detalhes: dict = {}
