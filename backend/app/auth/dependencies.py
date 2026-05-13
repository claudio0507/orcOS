"""Dependências FastAPI para autenticação (JWT e MFA)."""
import uuid
from datetime import UTC, datetime

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import text

from app.api.deps import SessionDep
from app.auth.jwt import decode_token
from app.models.usuario import RoleUsuario, Usuario

# Usamos HTTPBearer para capturar o token "Bearer <token>"
security = HTTPBearer(auto_error=False)


async def get_current_user(
    session: SessionDep,
    token: HTTPAuthorizationCredentials | None = Depends(security),
) -> Usuario:
    """
    Decodifica o JWT, busca o usuário e valida o status e CA-008 (MFA enforcement).
    Também define implicitamente o RLS para o tenant_id contido no token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas ou expiradas",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        # Se for teste e injetarmos header mockado, poderíamos bypassar aqui,
        # mas faremos isso em conftest.py para manter este código limpo.
        raise credentials_exception

    try:
        payload = decode_token(token.credentials)
        user_id_str: str | None = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception

        # Partial tokens (MFA) não dão acesso a endpoints regulares
        if payload.get("mfa_pending"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="MFA pendente. Conclua o login primeiro.",
            )

        user_id = uuid.UUID(user_id_str)
        # Em vez de buscar só o usuário, precisamos do tenant para setar o RLS
        tenant_id = payload.get("tenant_id")
        if not tenant_id:
            raise credentials_exception

        # Seta o RLS do banco de dados (que seria feito no get_tenant_id original)
        dialect = session.bind.dialect.name if session.bind else "postgresql"
        if dialect == "postgresql":
            await session.execute(
                text("SET LOCAL app.tenant_id = :tid"), {"tid": str(tenant_id)}
            )

    except (JWTError, ValueError):
        raise credentials_exception

    user = await session.get(Usuario, user_id)
    if user is None or not user.ativo:
        raise credentials_exception

    # CA-008: MFA Enforcement para L1 (ADMIN) e L2 (ORCAMENTISTA)
    if user.role in (RoleUsuario.ADMIN, RoleUsuario.ORCAMENTISTA) and not user.mfa_enabled:
        if user.mfa_enforced_at:
            now = datetime.now(UTC)
            # Como mfa_enforced_at pode ser naive em SQLite local, tratamos as timezones
            if user.mfa_enforced_at.tzinfo is None:
                enforced_at = user.mfa_enforced_at.replace(tzinfo=UTC)
            else:
                enforced_at = user.mfa_enforced_at

            if (now - enforced_at).days > 7:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Bloqueio CA-008: Configure o MFA (Autenticação 2 Fatores) para continuar acessando o sistema."
                )

    return user


async def require_mfa(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    """Dependência adicional para endpoints sensíveis (ex: spreading, deletar orçamentos)."""
    if not current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operação requer MFA ativado."
        )
    return current_user
