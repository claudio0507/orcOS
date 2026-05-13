"""Model: Orcamento (orçamento de obra/serviço)."""
from __future__ import annotations

import uuid
from enum import StrEnum

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TenantScopedMixin


class StatusOrcamento(StrEnum):
    RASCUNHO = "rascunho"
    EM_REVISAO = "em_revisao"
    APROVADO = "aprovado"
    CANCELADO = "cancelado"


class Orcamento(TenantScopedMixin, Base):
    """
    Entidade que representa um orçamento de obra ou serviço.

    Um orçamento é o nó pai que agrupa diversas fichas (itens de serviço).
    Contém metadados globais, como o custo fixo total que será rateado
    entre as fichas filhas.
    """
    __tablename__ = "orcamentos"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    criado_por_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    titulo: Mapped[str] = mapped_column(String(500), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        server_default=StatusOrcamento.RASCUNHO,
        index=True,
    )
    # Custo fixo total do orçamento (Estrutura Operacional + mobilização, etc.)
    custo_fixo_total: Mapped[str] = mapped_column(
        String(30),  # Decimal armazenado como string para evitar perda de precisão
        nullable=False,
        server_default="0",
    )

    tenant: Mapped[Tenant] = relationship(back_populates="orcamentos", lazy="raise")
    criado_por: Mapped[Usuario | None] = relationship(
        back_populates="orcamentos", lazy="raise"
    )
    fichas: Mapped[list[Ficha]] = relationship(
        back_populates="orcamento", lazy="raise", cascade="all, delete-orphan"
    )


from app.models.ficha import Ficha  # noqa: E402
from app.models.tenant import Tenant  # noqa: E402
from app.models.usuario import Usuario  # noqa: E402
