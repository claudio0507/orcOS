#!/usr/bin/env python3
"""Seed idempotente para o modo sandbox.

Cria o tenant demo (UUID 00000000-...) e o usuário de teste.
Pode ser executado múltiplas vezes sem duplicar dados.

Uso:
    cd backend
    python scripts/seed_sandbox.py
"""
from __future__ import annotations

import asyncio
import sys
import uuid

import bcrypt
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import settings

DEMO_TENANT_ID = "00000000-0000-0000-0000-000000000000"
DEMO_EMAIL = "demo@orcos.app"
DEMO_PASSWORD = "demo123"
DEMO_NOME = "Demo Admin"


def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


async def seed() -> None:
    engine = create_async_engine(settings.DATABASE_URL, echo=False)

    async with AsyncSession(engine) as session:
        # Ativa RLS para o tenant demo (necessário em tabelas com FORCE RLS)
        await session.execute(text(f"SET app.tenant_id = '{DEMO_TENANT_ID}'"))

        # Tenant ─────────────────────────────────────────────────────────────
        result = await session.execute(
            text("SELECT id FROM tenants WHERE id = :id"),
            {"id": DEMO_TENANT_ID},
        )
        if result.scalar_one_or_none() is None:
            await session.execute(
                text("""
                    INSERT INTO tenants (id, nome, slug, rounding_mode, ativo, created_at, updated_at)
                    VALUES (:id, 'Empresa Demo', 'demo', 'banker', true, NOW(), NOW())
                """),
                {"id": DEMO_TENANT_ID},
            )
            print(f"✓ Tenant criado: {DEMO_TENANT_ID}")
        else:
            print(f"→ Tenant já existe: {DEMO_TENANT_ID}")

        # Usuário ─────────────────────────────────────────────────────────────
        result = await session.execute(
            text("SELECT id FROM usuarios WHERE tenant_id = :tid AND email = :email"),
            {"tid": DEMO_TENANT_ID, "email": DEMO_EMAIL},
        )
        if result.scalar_one_or_none() is None:
            await session.execute(
                text("""
                    INSERT INTO usuarios
                        (id, tenant_id, email, nome, hashed_password, role, ativo, mfa_enabled, created_at, updated_at)
                    VALUES
                        (:id, :tid, :email, :nome, :pw, 'admin', true, false, NOW(), NOW())
                """),
                {
                    "id": str(uuid.uuid4()),
                    "tid": DEMO_TENANT_ID,
                    "email": DEMO_EMAIL,
                    "nome": DEMO_NOME,
                    "pw": _hash(DEMO_PASSWORD),
                },
            )
            print(f"✓ Usuário criado: {DEMO_EMAIL}")
        else:
            print(f"→ Usuário já existe: {DEMO_EMAIL}")

        await session.commit()

    await engine.dispose()

    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  orcOS Sandbox — credenciais de acesso")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  Email:     {DEMO_EMAIL}")
    print(f"  Senha:     {DEMO_PASSWORD}")
    print(f"  Tenant ID: {DEMO_TENANT_ID}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


if __name__ == "__main__":
    asyncio.run(seed())
    sys.exit(0)
