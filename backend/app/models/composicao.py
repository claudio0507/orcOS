"""Model: Composicao (insumo/componente de uma Ficha — nó do BOM).

Representa a árvore de composição: uma Ficha pode ter N componentes
(materiais, mão-de-obra, equipamentos). Ciclos são detectados em runtime
via BomGraph (bom_dag.py) antes de qualquer gravação.
"""
from __future__ import annotations

import uuid
from enum import StrEnum

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TenantScopedMixin


class TipoComposicao(StrEnum):
    MATERIAL = "material"
    MAO_DE_OBRA = "mao_de_obra"
    EQUIPAMENTO = "equipamento"
    SUBSERVICO = "subservico"


class Composicao(TenantScopedMixin, Base):
    """
    Entidade que representa um insumo ou subcomponente de uma ficha.

    Permite a criação de árvores de composição (BOM - Bill of Materials).
    Pode referenciar materiais, mão-de-obra, equipamentos ou sub-serviços.
    """
    __tablename__ = "composicoes"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ficha_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("fichas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Referência ao componente pai (NULL = raiz da composição)
    pai_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("composicoes.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    descricao: Mapped[str] = mapped_column(String(500), nullable=False)
    codigo: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    tipo: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        server_default=TipoComposicao.MATERIAL,
        index=True,
    )
    unidade: Mapped[str] = mapped_column(String(50), nullable=False, server_default="un")
    quantidade: Mapped[str] = mapped_column(String(30), nullable=False)
    custo_unitario: Mapped[str] = mapped_column(String(30), nullable=False)
    ordem: Mapped[int] = mapped_column(nullable=False, server_default="0")

    tenant: Mapped[Tenant] = relationship(lazy="raise")
    ficha: Mapped[Ficha] = relationship(back_populates="composicoes", lazy="raise")
    pai: Mapped[Composicao | None] = relationship(
        back_populates="filhos", remote_side="Composicao.id", lazy="raise"
    )
    filhos: Mapped[list[Composicao]] = relationship(
        back_populates="pai", lazy="raise", cascade="all, delete-orphan"
    )


from app.models.ficha import Ficha  # noqa: E402
from app.models.tenant import Tenant  # noqa: E402
