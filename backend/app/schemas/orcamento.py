"""Schemas Pydantic v2 — Orcamento (request / response DTOs)."""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class OrcamentoCreate(BaseModel):
    """Payload para criação de um novo orçamento."""

    titulo: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Título descritivo do orçamento (ex: nome da obra).",
        examples=["Sinalização Viária – BR-153 km 42-58"],
    )
    descricao: str | None = Field(
        None,
        description="Descrição longa opcional com detalhes do escopo.",
        examples=["Implantação de sinalização horizontal e vertical na rodovia BR-153."],
    )
    custo_fixo_total: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        description=(
            "Custo fixo total do orçamento em R$ (Estrutura Operacional, "
            "mobilização, considerações excepcionais). Usado no spreading."
        ),
        examples=["15000.00"],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "titulo": "Sinalização Viária – BR-153 km 42-58",
                    "descricao": "Implantação de sinalização horizontal e vertical.",
                    "custo_fixo_total": "15000.00",
                }
            ]
        }
    }


class OrcamentoUpdate(BaseModel):
    """Payload para atualização parcial de um orçamento (PATCH)."""

    titulo: str | None = Field(
        None,
        min_length=1,
        max_length=500,
        description="Novo título do orçamento.",
        examples=["Sinalização Viária – BR-153 (revisão 2)"],
    )
    descricao: str | None = Field(
        None,
        description="Nova descrição.",
    )
    status: str | None = Field(
        None,
        description="Novo status: rascunho, em_revisao, aprovado, cancelado.",
        examples=["aprovado"],
    )
    custo_fixo_total: Decimal | None = Field(
        None,
        ge=0,
        description="Novo custo fixo total em R$.",
        examples=["20000.00"],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"titulo": "Título Atualizado", "status": "em_revisao"},
                {"custo_fixo_total": "25000.00"},
            ]
        }
    }


class OrcamentoRead(BaseModel):
    """Representação de leitura de um orçamento."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., description="ID único do orçamento (UUID v4).")
    tenant_id: uuid.UUID = Field(..., description="ID do tenant proprietário.")
    criado_por_id: uuid.UUID | None = Field(None, description="ID do usuário que criou.")
    titulo: str = Field(..., description="Título do orçamento.")
    descricao: str | None = Field(None, description="Descrição detalhada.")
    status: str = Field(..., description="Status atual: rascunho, em_revisao, aprovado, cancelado.")
    custo_fixo_total: str = Field(
        ...,
        description="Custo fixo total em R$ (Decimal armazenado como string).",
    )
    created_at: datetime = Field(..., description="Data/hora de criação (UTC).")
    updated_at: datetime = Field(..., description="Data/hora da última atualização (UTC).")


class OrcamentoList(BaseModel):
    """Lista paginada de orçamentos."""

    model_config = ConfigDict(from_attributes=True)

    items: list[OrcamentoRead] = Field(..., description="Orçamentos da página atual.")
    total: int = Field(..., description="Total de orçamentos (sem paginação).")
