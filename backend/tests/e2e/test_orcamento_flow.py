import pytest
import uuid
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.auth.password import get_password_hash
from app.models.tenant import Tenant
from app.models.usuario import Usuario, RoleUsuario
from app.pricing_engine.rounding import RoundingMode

import pyotp
from app.auth.mfa import generate_totp_secret

@pytest.mark.asyncio
async def test_complete_orcamento_workflow(e2e_client: AsyncClient, e2e_session: AsyncSession):
    """
    Testa o fluxo completo de um orçamento:
    1. Setup de dados (Tenant + Usuário com MFA)
    2. Login Passo 1 (Senha) -> Recebe partial_token
    3. Login Passo 2 (TOTP) -> Recebe JWT final
    4. Criar Orçamento
    5. Adicionar Fichas (Itens)
    6. Calcular preço unitário (Pricing Engine)
    7. Executar Spreading (Rateio de Custos Fixos)
    8. Validar Invariante CA-001
    """
    
    # --- 1. SETUP DE DADOS ---
    tenant_id = uuid.uuid4()
    tenant = Tenant(
        id=tenant_id,
        nome="E2E Construction Ltd",
        slug="e2e-construction",
        rounding_mode=RoundingMode.BANKER
    )
    e2e_session.add(tenant)
    
    password = "E2E_Secure_Password_2026"
    mfa_secret = generate_totp_secret()
    user_id = uuid.uuid4()
    user = Usuario(
        id=user_id,
        tenant_id=tenant_id,
        email="admin@e2e.com",
        nome="E2E Admin",
        hashed_password=get_password_hash(password),
        role=RoleUsuario.ADMIN,
        ativo=True,
        mfa_enabled=True, # MFA ativado exige login em 2 passos
        mfa_secret=mfa_secret
    )
    e2e_session.add(user)
    await e2e_session.commit()

    # --- 2. LOGIN PASSO 1 (Senha) ---
    login_resp = await e2e_client.post(
        "/api/v1/auth/login",
        json={
            "email": "admin@e2e.com",
            "password": password,
            "tenant_id": str(tenant_id)
        },
        headers={"X-Tenant-ID": str(tenant_id)}
    )
    assert login_resp.status_code == 200
    assert login_resp.json()["mfa_required"] is True
    partial_token = login_resp.json()["access_token"]

    # --- 3. LOGIN PASSO 2 (TOTP) ---
    totp = pyotp.TOTP(mfa_secret)
    totp_code = totp.now()
    
    mfa_resp = await e2e_client.post(
        "/api/v1/auth/mfa/login",
        json={
            "partial_token": partial_token,
            "totp_code": totp_code
        },
        headers={"X-Tenant-ID": str(tenant_id)}
    )
    assert mfa_resp.status_code == 200
    token = mfa_resp.json()["access_token"]
    auth_headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": str(tenant_id)
    }

    # --- 3. CRIAR ORÇAMENTO ---
    orc_resp = await e2e_client.post(
        "/api/v1/orcamentos",
        json={
            "titulo": "Reforma Galpão E2E",
            "descricao": "Projeto de teste E2E",
            "custo_fixo_total": "5000.00"
        },
        headers=auth_headers
    )
    assert orc_resp.status_code == 201
    orc_id = orc_resp.json()["id"]

    # --- 4. ADICIONAR FICHAS ---
    # Ficha 1: Pintura (Markup)
    f1_resp = await e2e_client.post(
        f"/api/v1/orcamentos/{orc_id}/fichas",
        json={
            "descricao": "Pintura Externa",
            "unidade": "m2",
            "quantidade": "100.00",
            "custo_unitario": "50.00",
            "tipo_precificacao": "markup",
            "parametros_precificacao": {
                "tributes": "0.12",
                "profit": "0.10",
                "indirect": "0.08"
            }
        },
        headers=auth_headers
    )
    assert f1_resp.status_code == 201
    f1_id = f1_resp.json()["id"]

    # Ficha 2: Piso (BDI Clássico)
    f2_resp = await e2e_client.post(
        f"/api/v1/orcamentos/{orc_id}/fichas",
        json={
            "descricao": "Piso Industrial",
            "unidade": "m2",
            "quantidade": "200.00",
            "custo_unitario": "80.00",
            "tipo_precificacao": "bdi_classico",
            "parametros_precificacao": {
                "administration": "0.05",
                "financial": "0.01",
                "risk": "0.02",
                "profit": "0.10",
                "tributes": "0.15"
            }
        },
        headers=auth_headers
    )
    assert f2_resp.status_code == 201
    f2_id = f2_resp.json()["id"]

    # --- 5. CALCULAR PREÇOS UNITÁRIOS ---
    # Calcular Ficha 1
    calc1_resp = await e2e_client.post(f"/api/v1/orcamentos/{orc_id}/fichas/{f1_id}/calcular", headers=auth_headers)
    assert calc1_resp.status_code == 200
    price1 = Decimal(calc1_resp.json()["preco_unitario"])
    assert price1 > Decimal("50.00")

    # Calcular Ficha 2
    calc2_resp = await e2e_client.post(f"/api/v1/orcamentos/{orc_id}/fichas/{f2_id}/calcular", headers=auth_headers)
    assert calc2_resp.status_code == 200
    price2 = Decimal(calc2_resp.json()["preco_unitario"])
    assert price2 > Decimal("80.00")

    # --- 6. EXECUTAR SPREADING (RATEIO) ---
    # Distribui os R$ 5000,00 de custo fixo proporcionalmente
    spread_resp = await e2e_client.post(
        f"/api/v1/orcamentos/{orc_id}/spreading",
        json={"rounding": "banker"},
        headers=auth_headers
    )
    assert spread_resp.status_code == 200
    data = spread_resp.json()
    
    # --- 7. VALIDAR INVARIANTE CA-001 ---
    assert data["ca001_validado"] is True
    
    # Soma dos totais finais deve ser igual à soma dos variáveis + fixo (± 0.01)
    total_final = Decimal(data["total_final"])
    total_var = Decimal(data["total_variavel"])
    fixo = Decimal(data["custo_fixo_total"])
    
    assert abs(total_final - (total_var + fixo)) <= Decimal("0.01")
    assert data["residuo_aplicado"] in [True, False] # Depende se houve sobra
    assert len(data["linhas"]) == 2
