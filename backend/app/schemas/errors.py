"""Schemas padronizados de erro — usados em `responses` dos routers.

Garante que /docs e /redoc exibam exemplos consistentes para 400, 404 e 422.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Detalhe de um erro de validação individual (422)."""

    loc: list[str | int] = Field(
        ...,
        description="Caminho do campo que causou o erro.",
        examples=[["body", "titulo"]],
    )
    msg: str = Field(
        ...,
        description="Mensagem de erro legível.",
        examples=["String should have at least 1 character"],
    )
    type: str = Field(
        ...,
        description="Tipo do erro (códigos Pydantic / FastAPI).",
        examples=["string_too_short"],
    )


class ErrorResponse400(BaseModel):
    """Requisição malformada — ex: header X-Tenant-ID ausente ou UUID inválido."""

    detail: str = Field(
        ...,
        description="Descrição do problema na requisição.",
        examples=["Header X-Tenant-ID obrigatório."],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"detail": "Header X-Tenant-ID obrigatório."},
                {"detail": "X-Tenant-ID inválido — esperado UUID v4."},
            ]
        }
    }


class ErrorResponse404(BaseModel):
    """Recurso não encontrado ou inacessível para o tenant atual."""

    detail: str = Field(
        ...,
        description="Descrição do recurso não encontrado.",
        examples=["Orçamento não encontrado."],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"detail": "Orçamento não encontrado."},
                {"detail": "Ficha não encontrada."},
                {"detail": "Tenant não encontrado ou inativo."},
            ]
        }
    }


class ErrorResponse422(BaseModel):
    """Erro de validação — payload inválido ou regra de negócio violada."""

    detail: str | list[ErrorDetail] = Field(
        ...,
        description=(
            "String com mensagem de erro de negócio, "
            "ou lista de erros de validação Pydantic."
        ),
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"detail": "Orçamento não possui fichas para spreading."},
                {
                    "detail": [
                        {
                            "loc": ["body", "titulo"],
                            "msg": "String should have at least 1 character",
                            "type": "string_too_short",
                        }
                    ]
                },
                {
                    "detail": (
                        "Soma de tributos/lucro/despesas (0.98) "
                        "excede o limite seguro (0.95)."
                    )
                },
            ]
        }
    }


# ── Helpers para uso nos routers ────────────────────────────────────────
# Dict pronto para passar em `responses={...}` de cada endpoint.

RESPONSES_400: dict = {
    400: {
        "model": ErrorResponse400,
        "description": "Requisição inválida — header `X-Tenant-ID` ausente ou malformado.",
    },
}

RESPONSES_404: dict = {
    404: {
        "model": ErrorResponse404,
        "description": "Recurso não encontrado ou fora do escopo do tenant.",
    },
}

RESPONSES_422: dict = {
    422: {
        "model": ErrorResponse422,
        "description": "Erro de validação de payload ou regra de negócio.",
    },
}

RESPONSES_CRUD_READ: dict = {**RESPONSES_400, **RESPONSES_404}
RESPONSES_CRUD_WRITE: dict = {**RESPONSES_400, **RESPONSES_404, **RESPONSES_422}
RESPONSES_ACTION: dict = {**RESPONSES_400, **RESPONSES_404, **RESPONSES_422}
