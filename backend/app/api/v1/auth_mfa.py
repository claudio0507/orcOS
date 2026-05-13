"""Router: Autenticação MFA (TOTP)."""
from datetime import datetime, timezone
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select

from app.api.deps import SessionDep
from app.api.v1.auth import _issue_tokens
from app.auth.dependencies import get_current_user
from app.auth.jwt import decode_token
from app.auth.mfa import generate_totp_secret, get_provisioning_uri, verify_totp
from app.models.usuario import Usuario
from app.schemas.auth import MfaLoginRequest, TokenResponse

router = APIRouter(prefix="/auth/mfa", tags=["Autenticação MFA"])


class SetupResponse(BaseModel):
    secret: str
    provisioning_uri: str


class VerifySetupRequest(BaseModel):
    secret: str
    totp_code: str


@router.post(
    "/setup",
    response_model=SetupResponse,
    summary="Inicia a configuração do MFA (Gera secret e URI)",
)
async def mfa_setup(
    current_user: Usuario = Depends(get_current_user),
) -> SetupResponse:
    """
    Gera um novo secret TOTP e a URI correspondente para gerar o QR code no frontend.
    Ainda não ativa o MFA na conta (precisa ser verificado).
    """
    if current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA já está configurado para este usuário.",
        )
        
    secret = generate_totp_secret()
    uri = get_provisioning_uri(secret, current_user.email)
    
    return SetupResponse(secret=secret, provisioning_uri=uri)


@router.post(
    "/verify",
    summary="Verifica o código TOTP e ativa o MFA permanentemente",
)
async def mfa_verify(
    payload: VerifySetupRequest,
    session: SessionDep,
    current_user: Usuario = Depends(get_current_user),
) -> dict[str, str]:
    """Valida o TOTP submetido e, se válido, salva o segredo e ativa o MFA."""
    if current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA já está configurado.",
        )
        
    if not verify_totp(payload.secret, payload.totp_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código TOTP inválido.",
        )
        
    current_user.mfa_secret = payload.secret
    current_user.mfa_enabled = True
    current_user.mfa_enforced_at = None # Já cumpriu
    
    await session.commit()
    
    return {"status": "success", "message": "MFA ativado com sucesso."}


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Completa o login utilizando o código TOTP",
)
async def mfa_login(
    payload: MfaLoginRequest,
    session: SessionDep,
) -> TokenResponse:
    """
    Recebe um token parcial retornado pelo `/auth/login` + código TOTP.
    Se válido, emite os tokens finais (access + refresh).
    """
    try:
        # Extraímos sem validar a data de expiração caso já tenha passado ligeiramente?
        # É melhor validar sim. 5 minutos devem bastar.
        token_data = decode_token(payload.partial_token)
        
        if not token_data.get("mfa_pending"):
            raise ValueError("Token não é um partial token.")
            
        user_id_str = token_data.get("sub")
        if not user_id_str:
            raise ValueError("Token inválido.")
            
        user_id = uuid.UUID(user_id_str)
        
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token parcial inválido ou expirado.",
        )
        
    user = await session.get(Usuario, user_id)
    if not user or not user.ativo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário inválido.",
        )
        
    if not user.mfa_enabled or not user.mfa_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA não está configurado para este usuário.",
        )
        
    if not verify_totp(user.mfa_secret, payload.totp_code):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Código TOTP inválido.",
        )
        
    return await _issue_tokens(session, user)
