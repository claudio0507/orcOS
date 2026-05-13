"""Base declarativa SQLAlchemy 2 + mixin de colunas padrão."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base para todos os modelos ORM."""

    type_annotation_map: dict[Any, Any] = {}


class UUIDPrimaryKeyMixin:
    """UUID gerado em Python (compatível com SQLite e PostgreSQL)."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )


class TimestampMixin:
    """created_at / updated_at com timezone, preenchidos pelo banco."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class TenantScopedMixin(UUIDPrimaryKeyMixin, TimestampMixin):
    """Mixin para tabelas multi-tenant: PK + timestamps + tenant_id.

    tenant_id é declarado nas subclasses com ForeignKey para evitar
    dependência circular no import order.
    """
