"""Model: AuditLog para CA-006 (Trilha de auditoria imutável)."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPrimaryKeyMixin


class AuditLog(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "audit_logs"

    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Contexto
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)

    # Ação
    action: Mapped[str] = mapped_column(String(50), nullable=False) # POST, PUT, DELETE
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False) # Orcamento, Ficha
    resource_id: Mapped[str] = mapped_column(String(100), nullable=False)

    # Diff (JSON)
    # Usando Text no SQLite para retrocompatibilidade, mas em Postgres deve ser JSONB.
    # O SQLAlchemy gerencia dicionários via TypeDecorator se necessário, mas aqui salvaremos str.
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Hash Chain (CA-006)
    prev_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    entry_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)

    usuario = relationship("Usuario", lazy="raise")
    tenant = relationship("Tenant", lazy="raise")
