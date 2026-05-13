"""Model: RefreshToken (para rotation e revogação)."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class RefreshToken(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    Representa um token de atualização para sessões de usuário.

    Permite a renovação do access_token sem nova autenticação por senha.
    Armazena o hash do token para segurança e suporta revogação.
    """
    __tablename__ = "refresh_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Vamos armazenar o token opaco em hash para evitar roubo via DB dump
    token_hash: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    usuario: Mapped[Usuario] = relationship(lazy="raise")


from app.models.usuario import Usuario  # noqa: E402
