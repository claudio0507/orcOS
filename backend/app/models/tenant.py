"""Model: Tenant (empresa/organização cliente do SaaS)."""
from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.pricing_engine.rounding import RoundingMode


class Tenant(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    Entidade raiz que representa uma empresa ou organização cliente (SaaS).

    Implementa multi-tenancy isolando dados entre diferentes organizações.
    Define configurações globais da empresa, como o modo de arredondamento.
    """
    __tablename__ = "tenants"

    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    # String para compatibilidade SQLite/Postgres (Enum real na migration Alembic)
    rounding_mode: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=RoundingMode.BANKER,
        server_default=RoundingMode.BANKER,
    )
    ativo: Mapped[bool] = mapped_column(nullable=False, default=True, server_default="true")

    # lazy="raise" força uso explícito de selectinload/joinedload
    usuarios: Mapped[list[Usuario]] = relationship(back_populates="tenant", lazy="raise")
    orcamentos: Mapped[list[Orcamento]] = relationship(back_populates="tenant", lazy="raise")


from app.models.orcamento import Orcamento  # noqa: E402
from app.models.usuario import Usuario  # noqa: E402
