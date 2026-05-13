import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import AuditLog


async def test_audit_log_created_on_post(client: AsyncClient, session: AsyncSession, tenant_headers: dict):
    # Criamos um orçamento via POST
    resp = await client.post(
        "/api/v1/orcamentos",
        json={"titulo": "Obra Auditada", "custo_fixo_total": "100.00"},
        headers=tenant_headers,
    )
    assert resp.status_code == 201
    orcamento_id = resp.json()["id"]

    # Verificamos no banco se o audit_log foi gerado
    result = await session.execute(
        select(AuditLog).where(AuditLog.resource_id == orcamento_id)
    )
    logs = result.scalars().all()
    assert len(logs) == 1
    log = logs[0]

    assert log.action == "POST"
    assert log.resource_type == "Orcamento"
    assert log.entry_hash is not None
    assert "Obra Auditada" in log.new_value


@pytest.mark.skip(reason="Endpoint /verify agora é placeholder na estrutura base")
async def test_verify_chain_endpoint(client: AsyncClient, session: AsyncSession, tenant_headers: dict):
    # Fazemos algumas operações para gerar logs
    resp1 = await client.post(
        "/api/v1/orcamentos",
        json={"titulo": "Obra 1", "custo_fixo_total": "100.00"},
        headers=tenant_headers,
    )
    orc_id = resp1.json()["id"]

    await client.patch(
        f"/api/v1/orcamentos/{orc_id}",
        json={"status": "cancelado"},
        headers=tenant_headers,
    )

    # Agora verificamos a chain como ADMIN (o token injetado no conftest é RoleUsuario.ADMIN)
    resp_verify = await client.get(
        "/api/v1/admin/audit/verify",
        headers=tenant_headers
    )

    assert resp_verify.status_code == 200
    data = resp_verify.json()
    assert data["status"] == "OK"
    assert data["count"] >= 2


@pytest.mark.skip(reason="Endpoint /verify agora é placeholder na estrutura base")
async def test_audit_chain_corrupted(client: AsyncClient, session: AsyncSession, tenant_headers: dict):
    # Geramos um log válido
    resp1 = await client.post(
        "/api/v1/orcamentos",
        json={"titulo": "Obra Corrompida", "custo_fixo_total": "100.00"},
        headers=tenant_headers,
    )
    orc_id = resp1.json()["id"]

    # Pegamos o log e adulteramos diretamente
    result = await session.execute(
        select(AuditLog).where(AuditLog.resource_id == orc_id)
    )
    log = result.scalars().first()
    log.new_value = '{"titulo": "Adulterado!", "custo_fixo_total": "999.99"}'
    await session.commit()

    # Agora a verificação deve falhar
    resp_verify = await client.get(
        "/api/v1/admin/audit/verify",
        headers=tenant_headers
    )

    assert resp_verify.status_code == 200
    data = resp_verify.json()
    assert data["status"] == "CORRUPTED"
    assert data["broken_at_id"] == str(log.id)
    assert "adulterado" in data["message"].lower()

@pytest.mark.skip(reason="Job em implementação - estrutura base criada")
async def test_audit_job_status_and_execution(client: AsyncClient, session: AsyncSession, tenant_headers: dict):
    from app.audit.job import verify_audit_chain

    # Executamos o job (placeholder)
    await verify_audit_chain()

    # O endpoint status deve retornar o placeholder
    resp_status = await client.get(
        "/api/v1/admin/audit/status",
        headers=tenant_headers
    )
    assert resp_status.status_code == 200
    data = resp_status.json()
    assert data["status"] == "not_implemented"
