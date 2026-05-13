"""Fixtures para testes E2E.
Testam o fluxo completo sem mocks de usuário, exigindo login real.
"""
from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.session import get_session
from app.main import app

# Em E2E, poderíamos usar um banco Postgres real se o docker-compose estivesse up.
# Para manter portabilidade no pytest, usamos SQLite por padrão, 
# mas permitimos override via env var.
import os
TEST_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./test_e2e.db")

@pytest_asyncio.fixture(scope="session")
async def e2e_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest_asyncio.fixture
async def e2e_session(e2e_engine):
    factory = async_sessionmaker(e2e_engine, expire_on_commit=False, autoflush=False)
    async with factory() as session:
        yield session
        await session.rollback()

@pytest_asyncio.fixture
async def e2e_client(e2e_session: AsyncSession):
    """Client que usa a sessão de teste mas NÃO mocka o usuário."""
    
    async def _override_session():
        yield e2e_session

    app.dependency_overrides[get_session] = _override_session
    # Garantimos que não há mocks de auth ativos
    from app.auth.dependencies import get_current_user, require_mfa
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(require_mfa, None)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
    app.dependency_overrides.clear()
