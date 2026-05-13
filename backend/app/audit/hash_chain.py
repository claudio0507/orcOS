"""CA-006: Cálculo do Hash SHA-256 para o Audit Trail."""
import hashlib
from datetime import datetime


def compute_entry_hash(
    timestamp: datetime,
    user_id: str | None,
    action: str,
    resource_type: str,
    resource_id: str,
    old_value: str | None,
    new_value: str | None,
    prev_hash: str | None,
) -> str:
    """Calcula o SHA-256 da entrada concatenando seus campos."""

    # Formatar timestamp sem microsegundos para garantir consistência após resgatar do SQLite
    ts_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")

    components = [
        prev_hash or "GENESIS",
        ts_str,
        str(user_id) if user_id else "SYSTEM",
        action,
        resource_type,
        resource_id,
        old_value or "NULL",
        new_value or "NULL",
    ]

    raw_data = "|".join(components)
    return hashlib.sha256(raw_data.encode("utf-8")).hexdigest()
