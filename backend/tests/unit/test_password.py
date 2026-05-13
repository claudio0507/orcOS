
from app.auth.password import get_password_hash, verify_password


def test_get_password_hash():
    password = "secret_password123"
    hashed = get_password_hash(password)
    assert hashed != password
    assert len(hashed) > 10
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$")


def test_verify_password_correct():
    password = "my_secure_password"
    hashed = get_password_hash(password)
    assert verify_password(password, hashed) is True


def test_verify_password_incorrect():
    password = "my_secure_password"
    hashed = get_password_hash(password)
    assert verify_password("wrong_password", hashed) is False
