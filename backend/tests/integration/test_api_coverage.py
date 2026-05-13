import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests.integration.factories.tenant import TenantFactory
from tests.integration.factories.orcamento import OrcamentoFactory

pytestmark = pytest.mark.asyncio

async def make_tenant(session: AsyncSession, **kwargs):
    tenant = TenantFactory.build(**kwargs)
    session.add(tenant)
    await session.flush()
    return tenant

class TestApiValidationErrors:
    async def test_422_invalid_email_login(self, client: AsyncClient):
        tenant_id = str(uuid.uuid4())
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "not-an-email", "password": "any", "tenant_id": tenant_id},
            headers={"X-Tenant-ID": tenant_id} # Adiciona header obrigatório
        )
        assert resp.status_code == 422

    async def test_422_invalid_uuid_orcamento(self, client: AsyncClient):
        tenant_id = str(uuid.uuid4())
        resp = await client.get(
            "/api/v1/orcamentos/not-a-uuid",
            headers={"X-Tenant-ID": tenant_id}
        )
        assert resp.status_code == 422

    async def test_422_negative_cost_orcamento(self, client: AsyncClient, session: AsyncSession):
        tenant = await make_tenant(session)
        resp = await client.post(
            "/api/v1/orcamentos",
            json={"titulo": "Teste", "custo_fixo_total": "-10.00"},
            headers={"X-Tenant-ID": str(tenant.id)}
        )
        assert resp.status_code == 422

class TestApiRLS:
    async def test_get_orcamento_wrong_tenant(self, client: AsyncClient, session: AsyncSession):
        tenant_a = await make_tenant(session)
        tenant_b = await make_tenant(session)
        
        orc_a = OrcamentoFactory.build(tenant_id=tenant_a.id)
        session.add(orc_a)
        await session.flush()
        
        # Acessa orc_a com header do tenant_b
        resp = await client.get(
            f"/api/v1/orcamentos/{orc_a.id}",
            headers={"X-Tenant-ID": str(tenant_b.id)}
        )
        assert resp.status_code == 404

    async def test_update_orcamento_wrong_tenant(self, client: AsyncClient, session: AsyncSession):
        tenant_a = await make_tenant(session)
        tenant_b = await make_tenant(session)
        
        orc_a = OrcamentoFactory.build(tenant_id=tenant_a.id)
        session.add(orc_a)
        await session.flush()
        
        resp = await client.patch(
            f"/api/v1/orcamentos/{orc_a.id}",
            json={"titulo": "Hacker"},
            headers={"X-Tenant-ID": str(tenant_b.id)}
        )
        assert resp.status_code == 404
