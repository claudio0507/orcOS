"""Testes de integração — endpoints CRUD de Orçamentos."""
from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.orcamento import StatusOrcamento
from tests.integration.factories.orcamento import OrcamentoFactory
from tests.integration.factories.tenant import TenantFactory

pytestmark = pytest.mark.asyncio


async def make_tenant(session: AsyncSession, **kwargs):
    """Cria e persiste um Tenant na sessão."""
    tenant = TenantFactory.build(**kwargs)
    session.add(tenant)
    await session.flush()
    return tenant


async def make_orcamento(session: AsyncSession, tenant, **kwargs):
    """Cria e persiste um Orcamento na sessão."""
    orc = OrcamentoFactory.build(tenant_id=tenant.id, **kwargs)
    session.add(orc)
    await session.flush()
    return orc


class TestCriarOrcamento:
    async def test_cria_com_dados_validos(self, client: AsyncClient, session: AsyncSession):
        tenant = await make_tenant(session)
        headers = {"X-Tenant-ID": str(tenant.id)}

        resp = await client.post(
            "/api/v1/orcamentos",
            json={"titulo": "Obra Nova", "custo_fixo_total": "5000.00"},
            headers=headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["titulo"] == "Obra Nova"
        assert data["status"] == StatusOrcamento.RASCUNHO
        assert data["tenant_id"] == str(tenant.id)

    async def test_rejeita_sem_tenant_header(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/orcamentos",
            json={"titulo": "Sem header"},
        )
        assert resp.status_code == 400

    async def test_rejeita_tenant_id_invalido(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/orcamentos",
            json={"titulo": "UUID ruim"},
            headers={"X-Tenant-ID": "nao-eh-uuid"},
        )
        assert resp.status_code == 400

    async def test_rejeita_titulo_vazio(self, client: AsyncClient, session: AsyncSession):
        tenant = await make_tenant(session)
        resp = await client.post(
            "/api/v1/orcamentos",
            json={"titulo": ""},
            headers={"X-Tenant-ID": str(tenant.id)},
        )
        assert resp.status_code == 422


class TestListarOrcamentos:
    async def test_lista_apenas_do_proprio_tenant(
        self, client: AsyncClient, session: AsyncSession
    ):
        tenant_a = await make_tenant(session)
        tenant_b = await make_tenant(session)

        await make_orcamento(session, tenant_a)
        await make_orcamento(session, tenant_a)
        await make_orcamento(session, tenant_b)

        resp = await client.get(
            "/api/v1/orcamentos",
            headers={"X-Tenant-ID": str(tenant_a.id)},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert all(item["tenant_id"] == str(tenant_a.id) for item in data["items"])

    async def test_filtra_por_status(self, client: AsyncClient, session: AsyncSession):
        tenant = await make_tenant(session)
        await make_orcamento(session, tenant, status=StatusOrcamento.APROVADO)
        await make_orcamento(session, tenant, status=StatusOrcamento.RASCUNHO)

        resp = await client.get(
            "/api/v1/orcamentos?status=aprovado",
            headers={"X-Tenant-ID": str(tenant.id)},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["status"] == "aprovado"


class TestObterOrcamento:
    async def test_retorna_orcamento_existente(self, client: AsyncClient, session: AsyncSession):
        tenant = await make_tenant(session)
        orc = await make_orcamento(session, tenant, titulo="Minha Obra")

        resp = await client.get(
            f"/api/v1/orcamentos/{orc.id}",
            headers={"X-Tenant-ID": str(tenant.id)},
        )
        assert resp.status_code == 200
        assert resp.json()["titulo"] == "Minha Obra"

    async def test_retorna_404_tenant_errado(self, client: AsyncClient, session: AsyncSession):
        tenant_a = await make_tenant(session)
        tenant_b = await make_tenant(session)
        orc = await make_orcamento(session, tenant_a)

        resp = await client.get(
            f"/api/v1/orcamentos/{orc.id}",
            headers={"X-Tenant-ID": str(tenant_b.id)},
        )
        assert resp.status_code == 404

    async def test_retorna_404_id_inexistente(self, client: AsyncClient, session: AsyncSession):
        tenant = await make_tenant(session)
        resp = await client.get(
            f"/api/v1/orcamentos/{uuid.uuid4()}",
            headers={"X-Tenant-ID": str(tenant.id)},
        )
        assert resp.status_code == 404


class TestAtualizarOrcamento:
    async def test_atualiza_titulo(self, client: AsyncClient, session: AsyncSession):
        tenant = await make_tenant(session)
        orc = await make_orcamento(session, tenant)

        resp = await client.patch(
            f"/api/v1/orcamentos/{orc.id}",
            json={"titulo": "Título Atualizado"},
            headers={"X-Tenant-ID": str(tenant.id)},
        )
        assert resp.status_code == 200
        assert resp.json()["titulo"] == "Título Atualizado"

    async def test_atualiza_status(self, client: AsyncClient, session: AsyncSession):
        tenant = await make_tenant(session)
        orc = await make_orcamento(session, tenant)

        resp = await client.patch(
            f"/api/v1/orcamentos/{orc.id}",
            json={"status": "aprovado"},
            headers={"X-Tenant-ID": str(tenant.id)},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "aprovado"


class TestDeletarOrcamento:
    async def test_deleta_e_retorna_204(self, client: AsyncClient, session: AsyncSession):
        tenant = await make_tenant(session)
        orc = await make_orcamento(session, tenant)

        resp = await client.delete(
            f"/api/v1/orcamentos/{orc.id}",
            headers={"X-Tenant-ID": str(tenant.id)},
        )
        assert resp.status_code == 204

    async def test_nao_deleta_de_outro_tenant(self, client: AsyncClient, session: AsyncSession):
        tenant_a = await make_tenant(session)
        tenant_b = await make_tenant(session)
        orc = await make_orcamento(session, tenant_a)

        resp = await client.delete(
            f"/api/v1/orcamentos/{orc.id}",
            headers={"X-Tenant-ID": str(tenant_b.id)},
        )
        assert resp.status_code == 404
