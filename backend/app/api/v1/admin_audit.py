"""Router: Administração de Auditoria (CA-006)."""
from fastapi import APIRouter, Depends
from app.auth.dependencies import get_current_user
from app.models.usuario import RoleUsuario, Usuario
from fastapi import HTTPException, status

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
async def get_audit_status():
    """Retorna o status da última verificação agendada."""
    return {"status": "not_implemented", "message": "Estrutura base criada. Lógica em implementação."}

@router.get("/verify", dependencies=[Depends(require_admin)])
async def manual_verify():
    """Dispara uma verificação manual da cadeia de auditoria."""
    return {"status": "not_implemented", "message": "Estrutura base criada. Lógica em implementação."}
