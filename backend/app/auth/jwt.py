"""Configurações e utilitários para JWT (Access e Refresh tokens)."""
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt

from app.core.config import settings


def create_access_token(
    subject: str | Any,
    tenant_id: str,
    role: str,
    expires_delta: timedelta | None = None,
    is_partial: bool = False,
) -> str:
    """
    Gera um JWT Access Token.
    
    Args:
        subject: Geralmente o ID do usuário (sub).
        tenant_id: ID do tenant (para validação cruzada se necessário).
        role: Papel do usuário (admin, orcamentista, etc).
        expires_delta: Tempo de expiração customizado.
        is_partial: Se True, o token serve apenas para transição MFA.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # Partial tokens para MFA duram apenas 5 minutos
        minutes = 5 if is_partial else settings.ACCESS_TOKEN_EXPIRE_MINUTES
        expire = datetime.now(timezone.utc) + timedelta(minutes=minutes)

    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "tenant_id": str(tenant_id),
        "role": str(role),
    }
    
    if is_partial:
        to_encode["mfa_pending"] = True

    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> dict[str, Any]:
    """Decodifica e valida o JWT, retornando as claims."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
