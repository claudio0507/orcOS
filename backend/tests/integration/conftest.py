"""Fixtures de integração — banco SQLite in-memory + AsyncClient.

Para rodar contra PostgreSQL real, exporte DATABASE_TEST_URL:
    export DATABASE_TEST_URL=postgresql+asyncpg://orcos:orcos@localhost:5432/orcos_test
"""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.session import get_session
from app.main import app

# SQLite async para testes — sem necessidade de Postgres em CI
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_orcos.db"


@pytest_asyncio.fixture(scope="session")
async def engine():
    """Engine de teste — cria todas as tabelas, destrói ao final."""
    _engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield _engine
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await _engine.dispose()


@pytest_asyncio.fixture
async def session(engine):
    """Sessão isolada por teste — rollback ao final."""
    factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    async with factory() as sess:
        yield sess
        await sess.rollback()


@pytest_asyncio.fixture
async def client(session: AsyncSession):
    """AsyncClient com override da sessão de banco e bypass de auth."""
    from app.auth.dependencies import get_current_user, require_mfa
    from app.models.usuario import RoleUsuario, Usuario

    async def _override_session():
        yield session

    async def _mock_current_user():
        return Usuario(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            email="test@example.com",
            nome="Test User",
            hashed_password="hash",
            role=RoleUsuario.ADMIN,
            ativo=True,
            mfa_enabled=True,
        )

    app.dependency_overrides[get_session] = _override_session
    app.dependency_overrides[get_current_user] = _mock_current_user
    app.dependency_overrides[require_mfa] = _mock_current_user

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def tenant_headers(session) -> dict[str, str]:
    """Helper que retorna headers com X-Tenant-ID e Authorization Bearer de um tenant/usuário criado."""
    import asyncio

    from app.auth.jwt import create_access_token
    from tests.integration.factories.tenant import TenantFactory
    from tests.integration.factories.usuario import UsuarioFactory

    async def _create():
        tenant = TenantFactory()
        session.add(tenant)
        await session.flush()

        user = UsuarioFactory(tenant_id=tenant.id)
        session.add(user)
        await session.flush()

        return tenant, user

    tenant, user = asyncio.get_event_loop().run_until_complete(_create())
    token = create_access_token(
        subject=user.id,
        tenant_id=tenant.id,
        role=user.role,
    )
    return {
        "X-Tenant-ID": str(tenant.id),
        "Authorization": f"Bearer {token}",
    }
