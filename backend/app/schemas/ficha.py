"""Schemas Pydantic v2 — Ficha + cálculo de precificação."""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.ficha import TipoPrecificacao


class MarkupParams(BaseModel):
    """Parâmetros para precificação por Markup (divisor).

    Fórmula: preço = custo / (1 − tributos − lucro − despesas_indiretas)
    """

    tributes: Decimal = Field(
        ...,
        ge=0,
        lt=1,
        description="Percentual de tributos (ex: 0.12 = 12%).",
        examples=["0.12"],
    )
    profit: Decimal = Field(
        ...,
        ge=0,
        lt=1,
        description="Percentual de lucro desejado (ex: 0.10 = 10%).",
        examples=["0.10"],
    )
    indirect: Decimal = Field(
        ...,
        ge=0,
        lt=1,
        description="Percentual de despesas indiretas (ex: 0.05 = 5%).",
        examples=["0.05"],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"tributes": "0.12", "profit": "0.10", "indirect": "0.05"}
            ]
        }
    }


class BdiManualComponente(BaseModel):
    """Componente individual de um BDI Manual."""

    name: str = Field(
        ...,
        description="Nome do componente (ex: ISS, PIS/COFINS).",
        examples=["ISS"],
    )
    percent: Decimal = Field(
        ...,
        ge=0,
        lt=1,
        description="Percentual do componente (ex: 0.05 = 5%).",
        examples=["0.05"],
    )
    base: str = Field(
        ...,
        description="Base de cálculo: 'revenue' (sobre receita) ou 'cost' (sobre custo).",
        examples=["revenue"],
    )
    legal_reference: str = Field(
        "",
        description="Referência legal (ex: Art. 65, Lei 8.666).",
        examples=["Art. 65, Lei 8.666"],
    )


class BdiManualParams(BaseModel):
    """Parâmetros para BDI Manual — lista de componentes arbitrários."""

    components: list[BdiManualComponente] = Field(
        ...,
        description="Lista de componentes do BDI Manual.",
    )


class BdiClassicoParams(BaseModel):
    """Parâmetros para BDI Clássico (fórmula DNIT).

    Fórmula: BDI = ((1+AC+AF+R)(1+L) / (1−T)) − 1
    """

    administration: Decimal = Field(
        ...,
        ge=0,
        lt=1,
        description="Administração Central (AC) — ex: 0.04 = 4%.",
        examples=["0.04"],
    )
    financial: Decimal = Field(
        ...,
        ge=0,
        lt=1,
        description="Despesa Financeira (AF) — ex: 0.012 = 1.2%.",
        examples=["0.012"],
    )
    risk: Decimal = Field(
        ...,
        ge=0,
        lt=1,
        description="Risco/Seguro/Garantia (R) — ex: 0.01 = 1%.",
        examples=["0.01"],
    )
    profit: Decimal = Field(
        ...,
        ge=0,
        lt=1,
        description="Lucro (L) — ex: 0.08 = 8%.",
        examples=["0.08"],
    )
    tributes: Decimal = Field(
        ...,
        ge=0,
        lt=1,
        description="Tributos (T) — ex: 0.1365 = 13.65%.",
        examples=["0.1365"],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "administration": "0.04",
                    "financial": "0.012",
                    "risk": "0.01",
                    "profit": "0.08",
                    "tributes": "0.1365",
                }
            ]
        }
    }


class FichaCreate(BaseModel):
    """Payload para criação de uma ficha (linha de serviço/insumo)."""

    descricao: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Descrição do serviço ou insumo.",
        examples=["Placa de sinalização R-1 (PARE) — 0,50×0,50m"],
    )
    unidade: str = Field(
        default="un",
        max_length=50,
        description="Unidade de medida (un, m², m³, kg, etc.).",
        examples=["un", "m²", "m³"],
    )
    quantidade: Decimal = Field(
        ...,
        gt=0,
        description="Quantidade (deve ser > 0).",
        examples=["25.00"],
    )
    custo_unitario: Decimal = Field(
        ...,
        ge=0,
        description="Custo unitário em R$ (≥ 0).",
        examples=["450.00"],
    )
    tipo_precificacao: TipoPrecificacao = Field(
        TipoPrecificacao.MARKUP,
        description="Modo de precificação: markup, bdi_manual, bdi_classico.",
        examples=["markup"],
    )
    parametros_precificacao: MarkupParams | BdiManualParams | BdiClassicoParams | None = Field(
        None,
        description="Parâmetros específicos do modo de precificação escolhido.",
    )
    ordem: int = Field(
        0,
        description="Posição da ficha na listagem (0-indexed).",
        examples=[0, 1, 2],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "descricao": "Placa de sinalização R-1 (PARE) — 0,50×0,50m",
                    "unidade": "un",
                    "quantidade": "25.00",
                    "custo_unitario": "450.00",
                    "tipo_precificacao": "markup",
                    "parametros_precificacao": {
                        "tributes": "0.12",
                        "profit": "0.10",
                        "indirect": "0.05",
                    },
                    "ordem": 0,
                }
            ]
        }
    }


class FichaUpdate(BaseModel):
    """Payload para atualização parcial de uma ficha (PATCH)."""

    descricao: str | None = Field(None, min_length=1, max_length=500, description="Nova descrição.")
    unidade: str | None = Field(None, description="Nova unidade de medida.")
    quantidade: Decimal | None = Field(None, gt=0, description="Nova quantidade.")
    custo_unitario: Decimal | None = Field(None, ge=0, description="Novo custo unitário em R$.")
    tipo_precificacao: TipoPrecificacao | None = Field(None, description="Novo modo de precificação.")
    parametros_precificacao: MarkupParams | BdiManualParams | BdiClassicoParams | None = Field(
        None, description="Novos parâmetros de precificação."
    )
    ordem: int | None = Field(None, description="Nova posição na listagem.")


class FichaRead(BaseModel):
    """Representação de leitura de uma ficha."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., description="ID único da ficha (UUID v4).")
    tenant_id: uuid.UUID = Field(..., description="ID do tenant proprietário.")
    orcamento_id: uuid.UUID = Field(..., description="ID do orçamento pai.")
    descricao: str = Field(..., description="Descrição do serviço/insumo.")
    unidade: str = Field(..., description="Unidade de medida.")
    quantidade: str = Field(..., description="Quantidade (Decimal como string).")
    custo_unitario: str = Field(..., description="Custo unitário em R$ (Decimal como string).")
    tipo_precificacao: str = Field(..., description="Modo de precificação utilizado.")
    preco_unitario_calculado: str | None = Field(
        None,
        description="Preço unitário calculado pelo pricing engine (snapshot). Atualizado ao recalcular ou após spreading.",
    )
    ordem: int = Field(..., description="Posição na listagem.")
    created_at: datetime = Field(..., description="Data/hora de criação (UTC).")
    updated_at: datetime = Field(..., description="Data/hora da última atualização (UTC).")


class FichaCalcResult(BaseModel):
    """Resultado do cálculo de preço unitário via pricing engine."""

    ficha_id: uuid.UUID = Field(..., description="ID da ficha calculada.")
    preco_unitario: str = Field(
        ...,
        description="Preço unitário calculado em R$ (Decimal como string).",
        examples=["616.44"],
    )
    divisor: str | None = Field(
        None,
        description="Divisor do Markup (só para tipo_precificacao=markup).",
        examples=["0.73"],
    )
    is_alert: bool = Field(
        ...,
        description="True se o cálculo gerou alerta (ex: divisor < 0.05).",
    )
    detalhes: dict = Field(
        default={},
        description="Detalhes específicos do modo (ex: total_components, bdi, t_revenue).",
        examples=[{"total_components": "0.27"}, {"bdi": "0.3142"}],
    )
