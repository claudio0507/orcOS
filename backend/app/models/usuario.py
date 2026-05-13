"""Model: Usuario (membro de um Tenant)."""
from __future__ import annotations

import uuid
from enum import StrEnum

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TenantScopedMixin


class RoleUsuario(StrEnum):
    ADMIN = "admin"
    ORCAMENTISTA = "orcamentista"
    VISUALIZADOR = "visualizador"


class Usuario(TenantScopedMixin, Base):
    __tablename__ = "usuarios"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        server_default=RoleUsuario.ORCAMENTISTA,
    )
    ativo: Mapped[bool] = mapped_column(nullable=False, server_default="true")

    tenant: Mapped[Tenant] = relationship(back_populates="usuarios", lazy="raise")
    orcamentos: Mapped[list[Orcamento]] = relationship(
        back_populates="criado_por", lazy="raise"
    )

    __table_args__ = (
        # Email único dentro do mesmo tenant
        UniqueConstraint("tenant_id", "email", name="uq_usuarios_tenant_email"),
    )


from app.models.tenant import Tenant  # noqa: E402
from app.models.orcamento import Orcamento  # noqa: E402
