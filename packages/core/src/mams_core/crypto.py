"""Hash-chain primitives for tamper-evident audit logs."""
from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any


def compute_entry_hash(
    entry_id: uuid.UUID,
    sequence_num: int,
    event_type: str,
    payload: dict[str, Any],
    prev_hash: str,
) -> str:
    """Compute SHA-256 hash for an audit log entry."""
    content = json.dumps(
        {
            "entry_id": str(entry_id),
            "sequence_num": sequence_num,
            "event_type": event_type,
            "payload": payload,
            "prev_hash": prev_hash,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(content.encode()).hexdigest()


def verify_chain(entries: list[dict[str, Any]]) -> bool:
    """Verify the integrity of an audit log hash chain.

    Entries must be sorted by sequence_num ascending.
    Returns True only if every hash is valid and prev_hash links are intact.
    """
    if not entries:
        return True
    for i, entry in enumerate(entries):
        expected = compute_entry_hash(
            entry_id=uuid.UUID(entry["entry_id"]),
            sequence_num=entry["sequence_num"],
            event_type=entry["event_type"],
            payload=entry["payload"],
            prev_hash=entry["prev_hash"],
        )
        if expected != entry["entry_hash"]:
            return False
        if i > 0 and entries[i - 1]["entry_hash"] != entry["prev_hash"]:
            return False
    return True
