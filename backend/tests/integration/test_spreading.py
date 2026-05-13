"""Testes de integração — endpoint POST /orcamentos/{id}/spreading."""
from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration.factories.ficha import FichaFactory
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


async def make_ficha(session: AsyncSession, tenant, orcamento, **kwargs):
    """Cria e persiste uma Ficha na sessão."""
    ficha = FichaFactory.build(
        tenant_id=tenant.id,
        orcamento_id=orcamento.id,
        **kwargs,
    )
    session.add(ficha)
    await session.flush()
    return ficha


class TestSpreadingEndpoint:
    """POST /api/v1/orcamentos/{id}/spreading"""

    async def test_spreading_basico_duas_fichas(
        self, client: AsyncClient, session: AsyncSession
    ):
        """Spreading com 2 fichas e custo fixo — happy path."""
        tenant = await make_tenant(session)
        headers = {"X-Tenant-ID": str(tenant.id)}
        orc = await make_orcamento(
            session, tenant, custo_fixo_total="1000.00"
        )

        # Ficha 1: 100 un × R$50.00 = R$5000.00
        await make_ficha(
            session, tenant, orc,
            descricao="Placa tipo A",
            quantidade="100.00",
            custo_unitario="50.00",
            preco_unitario_calculado="50.00",
        )
        # Ficha 2: 200 un × R$25.00 = R$5000.00
        await make_ficha(
            session, tenant, orc,
            descricao="Suporte tipo B",
            quantidade="200.00",
            custo_unitario="25.00",
            preco_unitario_calculado="25.00",
        )

        resp = await client.post(
            f"/api/v1/orcamentos/{orc.id}/spreading",
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()

        assert data["orcamento_id"] == str(orc.id)
        assert data["custo_fixo_total"] == "1000.00"
        assert len(data["linhas"]) == 2
        assert data["ca001_validado"] is True

        # Pesos iguais (5000 cada) → fixo dividido 50/50 = R$500 cada
        # final_unit_price ficha 1 = 50 + 500/100 = 55.00
        # final_unit_price ficha 2 = 25 + 500/200 = 27.50
        for linha in data["linhas"]:
            assert Decimal(linha["final_unit_price"]) > Decimal(linha["variable_unit_price"])

    async def test_ca001_invariante_conservacao(
        self, client: AsyncClient, session: AsyncSession
    ):
        """Valida que CA-001 é satisfeita: Σ(final×qty) == Σ(var×qty) + fixos ± R$0.01."""
        tenant = await make_tenant(session)
        headers = {"X-Tenant-ID": str(tenant.id)}
        orc = await make_orcamento(
            session, tenant, custo_fixo_total="3333.33"
        )

        # 3 fichas com quantidades e preços variados para forçar resíduos
        await make_ficha(
            session, tenant, orc,
            descricao="Item A",
            quantidade="7.00",
            custo_unitario="123.45",
            preco_unitario_calculado="123.45",
        )
        await make_ficha(
            session, tenant, orc,
            descricao="Item B",
            quantidade="13.00",
            custo_unitario="67.89",
            preco_unitario_calculado="67.89",
        )
        await make_ficha(
            session, tenant, orc,
            descricao="Item C",
            quantidade="3.00",
            custo_unitario="999.99",
            preco_unitario_calculado="999.99",
        )

        resp = await client.post(
            f"/api/v1/orcamentos/{orc.id}/spreading",
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["ca001_validado"] is True

        # Verificação manual da invariante
        total_var = sum(
            Decimal(l["variable_unit_price"]) * Decimal(l["quantity"])
            for l in data["linhas"]
        )
        total_final = sum(
            Decimal(l["final_line_total"])
            for l in data["linhas"]
        )
        expected = total_var + Decimal(data["custo_fixo_total"])
        assert abs(total_final - expected) <= Decimal("0.01")

    async def test_spreading_com_custo_fixo_override(
        self, client: AsyncClient, session: AsyncSession
    ):
        """Override de custo fixo no payload."""
        tenant = await make_tenant(session)
        headers = {"X-Tenant-ID": str(tenant.id)}
        orc = await make_orcamento(
            session, tenant, custo_fixo_total="1000.00"
        )
        await make_ficha(
            session, tenant, orc,
            descricao="Item X",
            quantidade="10.00",
            custo_unitario="100.00",
            preco_unitario_calculado="100.00",
        )

        resp = await client.post(
            f"/api/v1/orcamentos/{orc.id}/spreading",
            json={"custo_fixo_override": "500.00"},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["custo_fixo_total"] == "500.00"  # override, não 1000
        assert data["ca001_validado"] is True

    async def test_spreading_sem_fichas_retorna_422(
        self, client: AsyncClient, session: AsyncSession
    ):
        """Orçamento sem fichas deve retornar 422."""
        tenant = await make_tenant(session)
        headers = {"X-Tenant-ID": str(tenant.id)}
        orc = await make_orcamento(session, tenant, custo_fixo_total="1000.00")

        resp = await client.post(
            f"/api/v1/orcamentos/{orc.id}/spreading",
            headers=headers,
        )
        assert resp.status_code == 422
        assert "fichas" in resp.json()["detail"].lower()

    async def test_spreading_orcamento_inexistente_retorna_404(
        self, client: AsyncClient, session: AsyncSession
    ):
        """Orçamento inexistente deve retornar 404."""
        tenant = await make_tenant(session)
        headers = {"X-Tenant-ID": str(tenant.id)}
        fake_id = uuid.uuid4()

        resp = await client.post(
            f"/api/v1/orcamentos/{fake_id}/spreading",
            headers=headers,
        )
        assert resp.status_code == 404

    async def test_spreading_sem_tenant_header_retorna_400(
        self, client: AsyncClient, session: AsyncSession
    ):
        """Requisição sem X-Tenant-ID deve retornar 400."""
        resp = await client.post(
            f"/api/v1/orcamentos/{uuid.uuid4()}/spreading",
        )
        assert resp.status_code == 400

    async def test_spreading_tenant_errado_retorna_404(
        self, client: AsyncClient, session: AsyncSession
    ):
        """Tenant errado não deve ver orçamento de outro tenant."""
        tenant_a = await make_tenant(session)
        tenant_b = await make_tenant(session)
        orc = await make_orcamento(
            session, tenant_a, custo_fixo_total="500.00"
        )
        await make_ficha(
            session, tenant_a, orc,
            descricao="Item",
            quantidade="5.00",
            custo_unitario="100.00",
            preco_unitario_calculado="100.00",
        )

        resp = await client.post(
            f"/api/v1/orcamentos/{orc.id}/spreading",
            headers={"X-Tenant-ID": str(tenant_b.id)},
        )
        assert resp.status_code == 404

    async def test_spreading_custo_fixo_zero(
        self, client: AsyncClient, session: AsyncSession
    ):
        """Custo fixo zero não deve alterar preços (spreading neutro)."""
        tenant = await make_tenant(session)
        headers = {"X-Tenant-ID": str(tenant.id)}
        orc = await make_orcamento(
            session, tenant, custo_fixo_total="0"
        )
        await make_ficha(
            session, tenant, orc,
            descricao="Item",
            quantidade="10.00",
            custo_unitario="100.00",
            preco_unitario_calculado="100.00",
        )

        resp = await client.post(
            f"/api/v1/orcamentos/{orc.id}/spreading",
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["ca001_validado"] is True
        # Preço final deve ser igual ao variável quando fixo = 0
        for linha in data["linhas"]:
            assert Decimal(linha["final_unit_price"]) == Decimal(
                linha["variable_unit_price"]
            )

    async def test_spreading_persiste_preco_nas_fichas(
        self, client: AsyncClient, session: AsyncSession
    ):
        """Verifica que preco_unitario_calculado é atualizado após spreading."""
        tenant = await make_tenant(session)
        headers = {"X-Tenant-ID": str(tenant.id)}
        orc = await make_orcamento(
            session, tenant, custo_fixo_total="200.00"
        )
        ficha = await make_ficha(
            session, tenant, orc,
            descricao="Item",
            quantidade="10.00",
            custo_unitario="100.00",
            preco_unitario_calculado="100.00",
        )

        resp = await client.post(
            f"/api/v1/orcamentos/{orc.id}/spreading",
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()

        # Preço final = 100 + 200/10 = 120.00
        assert data["linhas"][0]["final_unit_price"] == "120.00"

        # Verificar persistência via GET ficha
        await session.refresh(ficha)
        assert ficha.preco_unitario_calculado == "120.00"

    async def test_spreading_rounding_commercial(
        self, client: AsyncClient, session: AsyncSession
    ):
        """Testa modo de arredondamento 'commercial'."""
        tenant = await make_tenant(session)
        headers = {"X-Tenant-ID": str(tenant.id)}
        orc = await make_orcamento(
            session, tenant, custo_fixo_total="1000.00"
        )
        await make_ficha(
            session, tenant, orc,
            descricao="Item",
            quantidade="3.00",
            custo_unitario="100.00",
            preco_unitario_calculado="100.00",
        )

        resp = await client.post(
            f"/api/v1/orcamentos/{orc.id}/spreading",
            json={"rounding": "commercial"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["ca001_validado"] is True
