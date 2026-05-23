"""UUIDv7 generation and idempotency utilities."""
from __future__ import annotations

import uuid

import uuid_utils


def new_uuid7() -> uuid.UUID:
    """Generate a new time-ordered UUIDv7."""
    return uuid.UUID(str(uuid_utils.uuid7()))


def operation_key(operation_id: uuid.UUID) -> str:
    """Redis key for storing an idempotency response."""
    return f"op:{operation_id}"
