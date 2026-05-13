"""Pydantic schemas para autenticação (JWT e MFA)."""
from __future__ import annotations

import uuid
from pydantic import BaseModel, EmailStr, Field


class TokenResponse(BaseModel):
    """Resposta de token após login ou refresh bem-sucedido."""

    access_token: str = Field(..., description="JWT access token.")
    refresh_token: str | None = Field(None, description="Opaque refresh token (se aplicável).")
    token_type: str = Field("bearer", description="Tipo do token (bearer).")
    mfa_required: bool = Field(False, description="True se o MFA TOTP for obrigatório para completar o login.")


class LoginRequest(BaseModel):
    """Payload para login padrão (email/senha)."""

    email: EmailStr = Field(..., description="Email do usuário.")
    password: str = Field(..., description="Senha em texto plano.")
    tenant_id: uuid.UUID = Field(..., description="ID do tenant a qual o usuário pertence.")


class MfaLoginRequest(BaseModel):
    """Payload para completar o login via MFA TOTP."""

    partial_token: str = Field(..., description="Access token parcial retornado pelo /login.")
    totp_code: str = Field(..., description="Código TOTP de 6 dígitos gerado pelo app auth.", min_length=6, max_length=6)


class RefreshRequest(BaseModel):
    """Payload para rotacionar o refresh token."""

    refresh_token: str = Field(..., description="Refresh token atual.")
