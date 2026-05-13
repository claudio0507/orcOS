"""Funções utilitárias para TOTP (Time-Based One-Time Password) usando pyotp."""
import pyotp

from app.core.config import settings


def generate_totp_secret() -> str:
    """Gera um segredo base32 aleatório (ex: JBSWY3DPEHPK3PXP)."""
    return pyotp.random_base32()


def get_provisioning_uri(secret: str, user_email: str) -> str:
    """Gera a URI (otpauth://) para transformar em QR Code no frontend."""
    return pyotp.totp.TOTP(secret).provisioning_uri(
        name=user_email,
        issuer_name=getattr(settings, "MFA_ISSUER_NAME", "orcOS"),
    )


def verify_totp(secret: str, code: str) -> bool:
    """Verifica se o código de 6 dígitos é válido para o segredo."""
    totp = pyotp.TOTP(secret)
    return totp.verify(code)
