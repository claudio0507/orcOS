"""Model: Ficha (linha de serviço ou insumo dentro de um Orçamento)."""
from __future__ import annotations

import uuid
from enum import StrEnum

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TenantScopedMixin


class TipoPrecificacao(StrEnum):
    MARKUP = "markup"
    BDI_MANUAL = "bdi_manual"
    BDI_CLASSICO = "bdi_classico"


class Ficha(TenantScopedMixin, Base):
    """
    Entidade que representa um item de linha em um orçamento.

    Uma ficha pode ser um serviço complexo ou um insumo simples.
    Contém as regras de precificação individuais e o resultado do
    cálculo de preço unitário final.
    """
    __tablename__ = "fichas"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    orcamento_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orcamentos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    descricao: Mapped[str] = mapped_column(String(500), nullable=False)
    unidade: Mapped[str] = mapped_column(String(50), nullable=False, server_default="un")
    # Valores como string Decimal para preservar precisão exata
    quantidade: Mapped[str] = mapped_column(String(30), nullable=False)
    custo_unitario: Mapped[str] = mapped_column(String(30), nullable=False)
    tipo_precificacao: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        server_default=TipoPrecificacao.MARKUP,
        index=True,
    )
    # JSON com parâmetros do modo (ex: {"tributes": "0.12", "profit": "0.10", ...})
    parametros_precificacao: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Preço unitário calculado (snapshot — atualizado ao recalcular)
    preco_unitario_calculado: Mapped[str | None] = mapped_column(String(30), nullable=True)
    ordem: Mapped[int] = mapped_column(nullable=False, server_default="0", index=True)

    tenant: Mapped[Tenant] = relationship(lazy="raise")
    orcamento: Mapped[Orcamento] = relationship(back_populates="fichas", lazy="raise")
    composicoes: Mapped[list[Composicao]] = relationship(
        back_populates="ficha", lazy="raise", cascade="all, delete-orphan"
    )


from app.models.composicao import Composicao  # noqa: E402
from app.models.orcamento import Orcamento  # noqa: E402
from app.models.tenant import Tenant  # noqa: E402
