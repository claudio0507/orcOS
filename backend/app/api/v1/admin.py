"""Router: Administração Geral."""
from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user

router = APIRouter(
    prefix="/admin",
    tags=["Administração"],
    dependencies=[Depends(get_current_user)],
)

# Outros endpoints de administração (usuários, etc) podem ser adicionados aqui.
