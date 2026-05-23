"""Tests for hash-chain crypto primitives."""
import uuid

from mams_core.crypto import compute_entry_hash, verify_chain


def _make_entry(entry_id: uuid.UUID, seq: int, prev_hash: str, payload: dict) -> dict:
    h = compute_entry_hash(entry_id, seq, "agent.created", payload, prev_hash)
    return {
        "entry_id": str(entry_id),
        "sequence_num": seq,
        "event_type": "agent.created",
        "payload": payload,
        "prev_hash": prev_hash,
        "entry_hash": h,
    }


def test_compute_entry_hash_deterministic():
    eid = uuid.UUID("01905e9a-0000-7000-8000-000000000001")
    h1 = compute_entry_hash(eid, 0, "agent.created", {"name": "test"}, "")
    h2 = compute_entry_hash(eid, 0, "agent.created", {"name": "test"}, "")
    assert h1 == h2
    assert len(h1) == 64  # SHA-256 hex


def test_compute_entry_hash_different_inputs_differ():
    eid = uuid.UUID("01905e9a-0000-7000-8000-000000000001")
    h1 = compute_entry_hash(eid, 0, "agent.created", {"name": "a"}, "")
    h2 = compute_entry_hash(eid, 0, "agent.created", {"name": "b"}, "")
    assert h1 != h2


def test_verify_chain_empty():
    assert verify_chain([]) is True


def test_verify_chain_single_entry():
    eid = uuid.uuid4()
    entry = _make_entry(eid, 0, "", {"x": 1})
    assert verify_chain([entry]) is True


def test_verify_chain_multiple_entries():
    entries = []
    prev = ""
    for i in range(5):
        eid = uuid.uuid4()
        entry = _make_entry(eid, i, prev, {"step": i})
        entries.append(entry)
        prev = entry["entry_hash"]
    assert verify_chain(entries) is True


def test_verify_chain_detects_tampering():
    entries = []
    prev = ""
    for i in range(3):
        eid = uuid.uuid4()
        entry = _make_entry(eid, i, prev, {"step": i})
        entries.append(entry)
        prev = entry["entry_hash"]

    # Tamper with middle entry
    entries[1]["payload"] = {"step": 999}
    assert verify_chain(entries) is False


def test_verify_chain_detects_broken_link():
    entries = []
    prev = ""
    for i in range(3):
        eid = uuid.uuid4()
        entry = _make_entry(eid, i, prev, {"step": i})
        entries.append(entry)
        prev = entry["entry_hash"]

    # Corrupt the prev_hash link
    entries[2]["prev_hash"] = "deadbeef" * 8
    assert verify_chain(entries) is False
