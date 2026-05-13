from datetime import datetime, timezone
import pytest

from app.audit.hash_chain import compute_entry_hash


def test_compute_entry_hash_genesis():
    timestamp = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    
    hash_val = compute_entry_hash(
        timestamp=timestamp,
        user_id=None,
        action="POST",
        resource_type="Tenant",
        resource_id="123",
        old_value=None,
        new_value='{"name": "Test"}',
        prev_hash=None,
    )
    
    assert isinstance(hash_val, str)
    assert len(hash_val) == 64  # sha256 hex


def test_compute_entry_hash_deterministic():
    timestamp = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    kwargs = dict(
        timestamp=timestamp,
        user_id="user-1",
        action="PATCH",
        resource_type="Orcamento",
        resource_id="orc-1",
        old_value='{"status": "rascunho"}',
        new_value='{"status": "aprovado"}',
        prev_hash="abc123hash",
    )
    
    hash1 = compute_entry_hash(**kwargs)
    hash2 = compute_entry_hash(**kwargs)
    
    assert hash1 == hash2


def test_compute_entry_hash_changes_with_data():
    timestamp = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    kwargs = dict(
        timestamp=timestamp,
        user_id="user-1",
        action="PATCH",
        resource_type="Orcamento",
        resource_id="orc-1",
        old_value='{"status": "rascunho"}',
        new_value='{"status": "aprovado"}',
        prev_hash="abc123hash",
    )
    
    hash_base = compute_entry_hash(**kwargs)
    
    kwargs_changed = kwargs.copy()
    kwargs_changed["new_value"] = '{"status": "cancelado"}'
    
    hash_changed = compute_entry_hash(**kwargs_changed)
    
    assert hash_base != hash_changed
