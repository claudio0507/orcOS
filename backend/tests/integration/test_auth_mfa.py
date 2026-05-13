import pyotp
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

async def test_mfa_setup_and_verify(unmocked_client: AsyncClient, session: AsyncSession):
    tenant = TenantFactory()
    session.add(tenant)
    await session.flush()
    password = "pwd"
    user = UsuarioFactory(tenant_id=tenant.id, email="mfasetup@ex.com", hashed_password=get_password_hash(password), mfa_enabled=False)
    session.add(user)
    await session.commit()

    # 1. Login para pegar token
    resp_login = await unmocked_client.post(
        "/api/v1/auth/login",
        json={"email": "mfasetup@ex.com", "password": password, "tenant_id": str(tenant.id)},
        headers={"X-Tenant-ID": str(tenant.id)}
    )
    access_token = resp_login.json()["access_token"]

    # 2. Setup MFA
    resp_setup = await unmocked_client.post(
        "/api/v1/auth/mfa/setup",
        headers={"Authorization": f"Bearer {access_token}", "X-Tenant-ID": str(tenant.id)}
    )
    assert resp_setup.status_code == 200
    secret = resp_setup.json()["secret"]

    # 3. Verify MFA
    totp = pyotp.TOTP(secret)
    code = totp.now()

    resp_verify = await unmocked_client.post(
        "/api/v1/auth/mfa/verify",
        headers={"Authorization": f"Bearer {access_token}", "X-Tenant-ID": str(tenant.id)},
        json={"secret": secret, "totp_code": code}
    )
    assert resp_verify.status_code == 200

    # Refresh user
    await session.refresh(user)
    assert user.mfa_enabled is True
    assert user.mfa_secret == secret


async def test_mfa_login_flow(unmocked_client: AsyncClient, session: AsyncSession):
    tenant = TenantFactory()
    session.add(tenant)
    await session.flush()

    secret = pyotp.random_base32()
    password = "pwd"
    user = UsuarioFactory(
        tenant_id=tenant.id,
        email="mfalogin@ex.com",
        hashed_password=get_password_hash(password),
        mfa_enabled=True,
        mfa_secret=secret
    )
    session.add(user)
    await session.commit()

    # 1. Login inicial retorna partial_token e mfa_required
    resp_login = await unmocked_client.post(
        "/api/v1/auth/login",
        json={"email": "mfalogin@ex.com", "password": password, "tenant_id": str(tenant.id)},
        headers={"X-Tenant-ID": str(tenant.id)}
    )
    assert resp_login.status_code == 200
    data = resp_login.json()
    assert data["mfa_required"] is True
    assert data["refresh_token"] is None
    partial_token = data["access_token"]

    # 2. Completar login com TOTP
    totp = pyotp.TOTP(secret)
    code = totp.now()

    resp_mfa = await unmocked_client.post(
        "/api/v1/auth/mfa/login",
        json={"partial_token": partial_token, "totp_code": code},
        headers={"X-Tenant-ID": str(tenant.id)}
    )
    assert resp_mfa.status_code == 200
    mfa_data = resp_mfa.json()
    assert mfa_data["mfa_required"] is False
    assert mfa_data["refresh_token"] is not None
