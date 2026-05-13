import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_mfa
from app.auth.password import get_password_hash
from app.db.session import get_session
from app.main import app
from tests.integration.factories.tenant import TenantFactory
from tests.integration.factories.usuario import UsuarioFactory


@pytest_asyncio.fixture
async def unmocked_client(session: AsyncSession):
    old_overrides = app.dependency_overrides.copy()
    async def _override_session():
        yield session
    app.dependency_overrides[get_session] = _override_session
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(require_mfa, None)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides = old_overrides

async def test_login_success(unmocked_client: AsyncClient, session: AsyncSession):
    tenant = TenantFactory()
    session.add(tenant)
    await session.flush()
    password = "MySecurePassword123"
    hashed = get_password_hash(password)
    user = UsuarioFactory(tenant_id=tenant.id, email="testlogin@example.com", hashed_password=hashed)
    session.add(user)
    await session.commit()

    resp = await unmocked_client.post(
        "/api/v1/auth/login",
        json={
            "email": "testlogin@example.com",
            "password": password,
            "tenant_id": str(tenant.id)
        },
        headers={"X-Tenant-ID": str(tenant.id)}
    )

    if resp.status_code != 200:
        print("ERROR PAYLOAD:", resp.json())
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["mfa_required"] is False
    assert data["token_type"] == "bearer"


async def test_login_invalid_password(unmocked_client: AsyncClient, session: AsyncSession):
    tenant = TenantFactory()
    session.add(tenant)
    await session.flush()

    hashed = get_password_hash("CorrectPassword")
    user = UsuarioFactory(tenant_id=tenant.id, email="wrongpwd@example.com", hashed_password=hashed)
    session.add(user)
    await session.commit()

    resp = await unmocked_client.post(
        "/api/v1/auth/login",
        json={
            "email": "wrongpwd@example.com",
            "password": "WrongPassword",
            "tenant_id": str(tenant.id)
        },
        headers={"X-Tenant-ID": str(tenant.id)}
    )

    assert resp.status_code == 401


async def test_refresh_token(unmocked_client: AsyncClient, session: AsyncSession):
    # Primeiro fazemos login
    tenant = TenantFactory()
    session.add(tenant)
    await session.flush()

    password = "MySecurePassword123"
    hashed = get_password_hash(password)
    user = UsuarioFactory(tenant_id=tenant.id, email="testrefresh@example.com", hashed_password=hashed)
    session.add(user)
    await session.commit()

    resp = await unmocked_client.post(
        "/api/v1/auth/login",
        json={
            "email": "testrefresh@example.com",
            "password": password,
            "tenant_id": str(tenant.id)
        },
        headers={"X-Tenant-ID": str(tenant.id)}
    )
    refresh_token = resp.json()["refresh_token"]

    # Agora rotacionamos
    resp_refresh = await unmocked_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
        headers={"X-Tenant-ID": str(tenant.id)}
    )

    assert resp_refresh.status_code == 200
    assert "access_token" in resp_refresh.json()
    assert resp_refresh.json()["refresh_token"] != refresh_token


async def test_logout(unmocked_client: AsyncClient, session: AsyncSession):
    tenant = TenantFactory()
    session.add(tenant)
    await session.flush()

    password = "pwd"
    user = UsuarioFactory(tenant_id=tenant.id, email="logout@example.com", hashed_password=get_password_hash(password))
    session.add(user)
    await session.commit()

    # Login
    resp = await unmocked_client.post(
        "/api/v1/auth/login",
        json={"email": "logout@example.com", "password": password, "tenant_id": str(tenant.id)},
        headers={"X-Tenant-ID": str(tenant.id)}
    )
    access_token = resp.json()["access_token"]

    # Logout
    resp_logout = await unmocked_client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {access_token}", "X-Tenant-ID": str(tenant.id)}
    )

    assert resp_logout.status_code == 204
