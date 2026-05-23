"""Tests for UUIDv7 generation."""
import uuid

from mams_core.idempotency import new_uuid7, operation_key


def test_new_uuid7_returns_uuid():
    result = new_uuid7()
    assert isinstance(result, uuid.UUID)


def test_new_uuid7_unique():
    ids = [new_uuid7() for _ in range(100)]
    assert len(set(ids)) == 100


def test_operation_key_format():
    uid = uuid.UUID("01905e9a-0000-7000-8000-000000000001")
    key = operation_key(uid)
    assert key.startswith("op:")
    assert str(uid) in key
