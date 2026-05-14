"""Router: Administração de Auditoria (CA-006)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.job import get_last_result
from app.audit.verification import verify_chain_integrity
from app.auth.dependencies import get_current_user
from app.db.session import get_session
from app.models.usuario import RoleUsuario, Usuario

router = APIRouter(
    prefix="/admin/audit",
    tags=["Administração - Auditoria"],
    dependencies=[Depends(get_current_user)],
)


def require_admin(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    """Garante que o usuário é administrador L1."""
    if current_user.role != RoleUsuario.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores.",
        )
    return current_user


@router.get("/status", dependencies=[Depends(require_admin)])
async def get_audit_status() -> dict:
    """
    Recupera o resultado da última verificação automática de integridade.

    Returns:
        Último status conhecido: PENDING, OK, CORRUPTED ou EMPTY.
    """
    return get_last_result()


@router.get("/verify", dependencies=[Depends(require_admin)])
async def manual_verify(session: AsyncSession = Depends(get_session)) -> dict:
    """
    Executa verificação de integridade da cadeia de auditoria sob demanda.

    Returns:
        Resultado imediato da verificação de todos os hashes (OK, CORRUPTED ou EMPTY).
    """
    return await verify_chain_integrity(session)
