"""Router: Autenticação base (Login, Refresh, Logout)."""
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.api.deps import SessionDep
from app.auth.dependencies import get_current_user
from app.auth.jwt import create_access_token
from app.auth.password import verify_password
from app.core.config import settings
from app.models.refresh_token import RefreshToken
from app.models.usuario import Usuario
from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Realiza login com email, senha e tenant_id",
)
async def login(
    payload: LoginRequest,
    session: SessionDep,
) -> TokenResponse:
    import logging
    logger = logging.getLogger(__name__)
    """
    Realiza a autenticação de um usuário.

    Verifica as credenciais (email/senha/tenant) e, se bem-sucedido, emite tokens
    ou exige verificação de MFA.

    Args:
        payload: Dados de login (email, senha, tenant_id).
        session: Sessão do banco de dados.

    Returns:
        TokenResponse com tokens de acesso ou flag de mfa_required.

    Raises:
        HTTPException: Se as credenciais forem inválidas ou o usuário estiver inativo.
    """
    logger.info(f"Login attempt: {payload.email} / {payload.tenant_id}")
    result = await session.execute(
        select(Usuario).where(
            Usuario.tenant_id == payload.tenant_id,
            Usuario.email == payload.email,
        )
    )
    user = result.scalar_one_or_none()
    logger.info(f"User found: {user is not None}")

    if not user or not user.ativo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
        )

    if not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
        )

    # Se MFA está ativado, emite token parcial
    if user.mfa_enabled:
        partial_token = create_access_token(
            subject=user.id,
            tenant_id=user.tenant_id,
            role=user.role,
            is_partial=True,
        )
        return TokenResponse(
            access_token=partial_token,
            refresh_token=None,
            mfa_required=True,
        )

    # Fluxo normal (sem MFA)
    return await _issue_tokens(session, user)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Rotaciona o refresh token para obter novo access token",
)
async def refresh_token(
    payload: RefreshRequest,
    session: SessionDep,
) -> TokenResponse:
    """
    Gera um novo access_token a partir de um refresh_token válido.

    Implementa rotação de refresh tokens (o token antigo é revogado).

    Args:
        payload: Objeto contendo o refresh_token opaco.
        session: Sessão do banco de dados.

    Returns:
        TokenResponse com novos tokens emitidos.

    Raises:
        HTTPException: Se o token for inválido, expirado ou o usuário for inativo.
    """
    # Como não decodificamos JWT aqui para o refresh_token opaco, validamos
    # comparando direto com o token_hash armazenado
    # Importante: num cenário real, faríamos um hash (SHA-256) da string antes de buscar
    # mas para simplificar, buscaremos exato se estiver armazenando sem salt extra.
    # Vamos importar hashlib
    import hashlib

    token_hash = hashlib.sha256(payload.refresh_token.encode()).hexdigest()

    result = await session.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked == False,  # noqa: E712
            RefreshToken.expires_at > datetime.now(UTC),
        )
    )
    db_token = result.scalar_one_or_none()

    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido ou expirado",
        )

    user = await session.get(Usuario, db_token.user_id)
    if not user or not user.ativo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário inválido ou inativo",
        )

    # Revogar o token antigo (Rotation)
    db_token.revoked = True

    return await _issue_tokens(session, user)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Encerra a sessão revogando os refresh tokens",
)
async def logout(
    session: SessionDep,
    current_user: Usuario = Depends(get_current_user),
) -> None:
    """
    Encerra a sessão do usuário.

    Revoga todos os refresh tokens ativos vinculados ao usuário logado.

    Args:
        session: Sessão do banco de dados.
        current_user: O usuário autenticado solicitando o logout.
    """
    result = await session.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == current_user.id,
            RefreshToken.revoked == False, # noqa: E712
        )
    )
    tokens = result.scalars().all()
    for t in tokens:
        t.revoked = True

    await session.commit()


async def _issue_tokens(session: SessionDep, user: Usuario) -> TokenResponse:
    """Helper para emitir par Access+Refresh, armazenando o Refresh."""
    import hashlib
    import secrets

    access_token = create_access_token(
        subject=user.id,
        tenant_id=user.tenant_id,
        role=user.role,
        is_partial=False,
    )

    raw_refresh = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_refresh.encode()).hexdigest()

    expires_at = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    db_refresh = RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
        revoked=False,
    )
    session.add(db_refresh)
    await session.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=raw_refresh,
        mfa_required=False,
    )
