#!/usr/bin/env python3
"""Seed script para criar dados de demo no Render."""
import asyncio
import uuid
import os

# Configurar DATABASE_URL se não existir
if not os.getenv("DATABASE_URL"):
    print("DATABASE_URL não configurado!")
    exit(1)

from app.db.base import Base
from app.db.session import engine, get_session
from app.models.tenant import Tenant
from app.models.usuario import Usuario, RoleUsuario
from app.auth.password import get_password_hash
from app.auth.mfa import generate_totp_secret
from app.pricing_engine.rounding import RoundingMode

async def seed():
    print("Criando tabelas...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    from sqlalchemy.ext.asyncio import async_sessionmaker
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    
    async with SessionLocal() as session:
        # Verificar se já existe
        from sqlalchemy import select
        result = await session.execute(select(Tenant))
        if result.scalar_one_or_none():
            print("Dados já existem!")
            return
        
        print("Criando tenant de demo...")
        tenant_id = uuid.UUID("395b1485-e979-411b-941d-9c152b4de585")
        tenant = Tenant(
            id=tenant_id,
            nome="Demo Tenant",
            slug="demo",
            rounding_mode=RoundingMode.BANKER
        )
        session.add(tenant)
        
        print("Criando usuário de demo...")
        mfa_secret = generate_totp_secret()
        user = Usuario(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            email="admin@demo.com",
            nome="Admin Demo",
            hashed_password=get_password_hash("demo123"),
            role=RoleUsuario.ADMIN,
            ativo=True,
            mfa_enabled=False,
            mfa_secret=mfa_secret
        )
        session.add(user)
        await session.commit()
        
        print("✅ Seed completo!")
        print(f"Tenant ID: {tenant_id}")
        print(f"Email: admin@demo.com")
        print(f"Senha: demo123")

if __name__ == "__main__":
    asyncio.run(seed())
