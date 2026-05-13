import uuid
from datetime import timedelta

import pytest
from jose import jwt

from app.auth.jwt import create_access_token, decode_token
from app.core.config import settings


def test_create_access_token():
    subject = uuid.uuid4()
    tenant_id = uuid.uuid4()
    role = "admin"

    token = create_access_token(
        subject=subject,
        tenant_id=tenant_id,
        role=role,
    )

    assert isinstance(token, str)

    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert payload["sub"] == str(subject)
    assert payload["tenant_id"] == str(tenant_id)
    assert payload["role"] == "admin"
    assert "exp" in payload
    assert payload.get("mfa_pending") is None


def test_create_partial_token_for_mfa():
    subject = uuid.uuid4()
    tenant_id = uuid.uuid4()
    role = "orcamentista"

    token = create_access_token(
        subject=subject,
        tenant_id=tenant_id,
        role=role,
        is_partial=True,
    )

    payload = decode_token(token)
    assert payload["sub"] == str(subject)
    assert payload.get("mfa_pending") is True


def test_decode_token():
    subject = uuid.uuid4()
    token = create_access_token(subject=subject, tenant_id=uuid.uuid4(), role="admin")

    payload = decode_token(token)
    assert payload["sub"] == str(subject)


def test_decode_expired_token():
    # Testa token com expiração negativa
    token = create_access_token(
        subject=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        role="admin",
        expires_delta=timedelta(minutes=-1),
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_token(token)
