from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import AuditLog


async def test_audit_log_created_on_post(client: AsyncClient, session: AsyncSession, tenant_headers: dict):
    resp = await client.post(
        "/api/v1/orcamentos",
        json={"titulo": "Obra Auditada", "custo_fixo_total": "100.00"},
        headers=tenant_headers,
    )
    assert resp.status_code == 201
    orcamento_id = resp.json()["id"]

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


async def test_verify_chain_endpoint(client: AsyncClient, tenant_headers: dict):
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

    resp_verify = await client.get(
        "/api/v1/admin/audit/verify",
        headers=tenant_headers,
    )

    assert resp_verify.status_code == 200
    data = resp_verify.json()
    assert data["status"] == "OK"
    assert data["count"] >= 2


async def test_audit_chain_corrupted(client: AsyncClient, session: AsyncSession, tenant_headers: dict):
    resp1 = await client.post(
        "/api/v1/orcamentos",
        json={"titulo": "Obra Corrompida", "custo_fixo_total": "100.00"},
        headers=tenant_headers,
    )
    orc_id = resp1.json()["id"]

    result = await session.execute(
        select(AuditLog).where(AuditLog.resource_id == orc_id)
    )
    log = result.scalars().first()
    log.new_value = '{"titulo": "Adulterado!", "custo_fixo_total": "999.99"}'
    await session.commit()

    resp_verify = await client.get(
        "/api/v1/admin/audit/verify",
        headers=tenant_headers,
    )

    assert resp_verify.status_code == 200
    data = resp_verify.json()
    assert data["status"] == "CORRUPTED"
    assert data["broken_at_id"] == str(log.id)
    assert "adulterado" in data["message"].lower()


async def test_audit_job_executes_and_updates_status(client: AsyncClient, session: AsyncSession, tenant_headers: dict):
    """Job atualiza _last_result; /status reflete o resultado."""
    from app.audit.job import verify_audit_chain

    result = await verify_audit_chain(session=session)

    assert result["status"] in ("OK", "EMPTY", "CORRUPTED")
    assert result["last_run"] is not None

    resp_status = await client.get(
        "/api/v1/admin/audit/status",
        headers=tenant_headers,
    )
    assert resp_status.status_code == 200
    data = resp_status.json()
    assert data["status"] in ("OK", "EMPTY", "CORRUPTED")
    assert data["last_run"] is not None


async def test_verify_endpoint_returns_valid_structure(client: AsyncClient, tenant_headers: dict):
    """/verify sempre retorna estrutura válida com status e count."""
    resp_verify = await client.get(
        "/api/v1/admin/audit/verify",
        headers=tenant_headers,
    )
    assert resp_verify.status_code == 200
    data = resp_verify.json()
    assert data["status"] in ("OK", "EMPTY", "CORRUPTED")
    assert "count" in data
    assert "message" in data


async def test_audit_chain_broken_prev_hash(client: AsyncClient, session: AsyncSession, tenant_headers: dict):
    """Quebra de encadeamento (prev_hash errado) é detectada como CORRUPTED."""
    await client.post(
        "/api/v1/orcamentos",
        json={"titulo": "Obra A", "custo_fixo_total": "50.00"},
        headers=tenant_headers,
    )
    await client.post(
        "/api/v1/orcamentos",
        json={"titulo": "Obra B", "custo_fixo_total": "75.00"},
        headers=tenant_headers,
    )

    result = await session.execute(
        select(AuditLog).order_by(AuditLog.timestamp.asc())
    )
    logs = result.scalars().all()
    assert len(logs) >= 2

    second_log = logs[1]
    second_log.prev_hash = "hash_invalido_adulterado_" + "0" * 40
    await session.commit()

    resp_verify = await client.get(
        "/api/v1/admin/audit/verify",
        headers=tenant_headers,
    )
    assert resp_verify.status_code == 200
    data = resp_verify.json()
    assert data["status"] == "CORRUPTED"
