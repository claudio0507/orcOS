import pyotp
import pytest

from app.auth.mfa import generate_totp_secret, get_provisioning_uri, verify_totp


def test_generate_totp_secret():
    secret = generate_totp_secret()
    assert isinstance(secret, str)
    assert len(secret) >= 16  # Segredos base32 normalmente têm pelo menos 16 chars


def test_get_provisioning_uri():
    secret = generate_totp_secret()
    email = "teste@exemplo.com"
    uri = get_provisioning_uri(secret, email)
    
    import urllib.parse
    encoded_email = urllib.parse.quote(email)
    
    assert uri.startswith("otpauth://totp/")
    assert encoded_email in uri
    assert secret in uri


def test_verify_totp_correct():
    secret = generate_totp_secret()
    totp = pyotp.TOTP(secret)
    code = totp.now()
    
    assert verify_totp(secret, code) is True


def test_verify_totp_incorrect():
    secret = generate_totp_secret()
    
    assert verify_totp(secret, "000000") is False
    assert verify_totp(secret, "abcdef") is False
