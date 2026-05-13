"""Engine assíncrono e sessionmaker.

Uso:
    async with async_session() as session:
        await session.execute(text("SET LOCAL app.tenant_id = :tid"), {"tid": str(tenant_id)})
        ...
"""
from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

async_session: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency FastAPI — fornece sessão com RLS configurado pelo caller."""
    async with async_session() as session:
        yield session
