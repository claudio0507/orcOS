"""Schemas Pydantic v2 — Spreading (rateio de custos fixos).

Invariante CA-001 (PRD v2.0 §3.5.4):

    Σ(preço_final × qty) == Σ(preço_variável × qty) + custos_fixos ± R$0,01

O arredondamento monetário pode gerar resíduos de até R$0,01 que são
absorvidos pela linha de maior peso (`carries_residue=True`).
"""
from __future__ import annotations

import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class SpreadingRequest(BaseModel):
    """Payload opcional para o endpoint de spreading.

    Permite override do custo fixo e escolha do modo de arredondamento.
    Se o body for omitido, utiliza `orcamento.custo_fixo_total` e arredondamento banker.
    """

    custo_fixo_override: Decimal | None = Field(
        None,
        ge=0,
        description=(
            "Override do custo fixo total em R$. "
            "Se `null` ou omitido, utiliza o valor de `orcamento.custo_fixo_total`. "
            "Útil para simular cenários sem alterar o orçamento."
        ),
        examples=["5000.00"],
    )
    rounding: str = Field(
        default="banker",
        pattern="^(banker|commercial)$",
        description=(
            "Modo de arredondamento monetário:\n"
            "- **`banker`** (padrão): ROUND_HALF_EVEN — reduz viés sistemático.\n"
            "- **`commercial`**: ROUND_HALF_UP — comportamento \"Excel-like\"."
        ),
        examples=["banker", "commercial"],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"custo_fixo_override": "5000.00", "rounding": "banker"},
                {"rounding": "commercial"},
            ]
        }
    }


class SpreadingResultLineRead(BaseModel):
    """Resultado do spreading para uma linha (ficha) individual.

    Cada linha mostra o preço variável original, o fixo alocado,
    e o preço final que será persistido na ficha.
    """

    model_config = ConfigDict(from_attributes=True)

    ficha_id: uuid.UUID = Field(..., description="ID da ficha.")
    descricao: str = Field(..., description="Descrição da ficha (para referência rápida).")
    variable_unit_price: str = Field(
        ...,
        description="Preço unitário variável original (antes do spreading), em R$.",
        examples=["50.00"],
    )
    quantity: str = Field(
        ...,
        description="Quantidade da ficha.",
        examples=["100.00"],
    )
    allocated_fixed: str = Field(
        ...,
        description="Valor de custo fixo alocado ao total da linha em R$ (já arredondado).",
        examples=["500.00"],
    )
    final_unit_price: str = Field(
        ...,
        description=(
            "Preço unitário final = variable_unit_price + (allocated_fixed / quantity). "
            "Este valor é persistido em `ficha.preco_unitario_calculado`."
        ),
        examples=["55.00"],
    )
    final_line_total: str = Field(
        ...,
        description="Total da linha = final_unit_price × quantity.",
        examples=["5500.00"],
    )
    carries_residue: bool = Field(
        ...,
        description=(
            "Se `true`, esta linha absorveu o resíduo de arredondamento "
            "para preservar a invariante CA-001. Tipicamente a linha de maior peso."
        ),
    )


class SpreadingResponse(BaseModel):
    """Resposta completa do endpoint de spreading.

    Inclui todas as linhas rateadas e a validação da invariante **CA-001**.

    ### Invariante CA-001 (Conservação de Totais)

    ```
    Σ(final_unit_price × quantity) == Σ(variable_unit_price × quantity) + fixed_total ± R$0,01
    ```

    Quando `ca001_validado` é `true`, a soma dos totais finais das linhas difere
    no máximo R$0,01 da soma esperada (variáveis + fixos). A diferença é causada
    exclusivamente por arredondamento monetário e é absorvida pela linha de maior peso.
    """

    orcamento_id: uuid.UUID = Field(..., description="ID do orçamento processado.")
    custo_fixo_total: str = Field(
        ...,
        description="Custo fixo total utilizado (pode ser override ou o valor do orçamento).",
        examples=["5000.00"],
    )
    total_variavel: str = Field(
        ...,
        description="Σ(variable_unit_price × quantity) — total variável antes do spreading.",
        examples=["10000.00"],
    )
    total_final: str = Field(
        ...,
        description="Σ(final_unit_price × quantity) — total final após spreading.",
        examples=["15000.00"],
    )
    residuo_aplicado: bool = Field(
        ...,
        description="Se `true`, houve ajuste de resíduo de arredondamento em pelo menos uma linha.",
    )
    linhas: list[SpreadingResultLineRead] = Field(
        ...,
        description="Resultado detalhado por ficha.",
    )
    ca001_validado: bool = Field(
        ...,
        description=(
            "**Invariante CA-001 (Conservação de Totais)**. "
            "`true` se Σ(final_unit_price × qty) == Σ(variable_unit_price × qty) + fixed_total ± R$0,01. "
            "Sempre deve ser `true` — uma falha indica bug no motor de spreading."
        ),
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "orcamento_id": "550e8400-e29b-41d4-a716-446655440000",
                    "custo_fixo_total": "1000.00",
                    "total_variavel": "10000.00",
                    "total_final": "11000.00",
                    "residuo_aplicado": False,
                    "ca001_validado": True,
                    "linhas": [
                        {
                            "ficha_id": "660e8400-e29b-41d4-a716-446655440001",
                            "descricao": "Placa R-1 (PARE)",
                            "variable_unit_price": "50.00",
                            "quantity": "100.00",
                            "allocated_fixed": "500.00",
                            "final_unit_price": "55.00",
                            "final_line_total": "5500.00",
                            "carries_residue": False,
                        },
                        {
                            "ficha_id": "770e8400-e29b-41d4-a716-446655440002",
                            "descricao": "Suporte tipo flangeado",
                            "variable_unit_price": "25.00",
                            "quantity": "200.00",
                            "allocated_fixed": "500.00",
                            "final_unit_price": "27.50",
                            "final_line_total": "5500.00",
                            "carries_residue": False,
                        },
                    ],
                }
            ]
        }
    }
