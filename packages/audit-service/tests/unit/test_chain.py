import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from mams_core.schemas.audit import AuditEntryCreate, AuditEventType


@pytest.mark.asyncio
async def test_append_entry_first_entry():
    """First entry should have sequence_num=0 and prev_hash=''"""
    from mams_audit.chain import append_entry

    agent_id = uuid.uuid4()

    # Mock DB session
    mock_db = AsyncMock()
    # get_last_entry returns None (no previous entries)
    mock_db.execute = AsyncMock(
        return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None))
    )
    mock_db.commit = AsyncMock()

    create = AuditEntryCreate(
        agent_id=agent_id,
        event_type=AuditEventType.AGENT_CREATED,
        payload={"name": "test"},
    )

    # We need refresh to populate the record
    # Since refresh is mocked, we need to track what was added
    added_record = None

    def capture_add(record):
        nonlocal added_record
        added_record = record

    mock_db.add = capture_add

    async def mock_refresh(record):
        record.entry_id = uuid.uuid4()
        record.created_at = datetime.now(timezone.utc)

    mock_db.refresh = mock_refresh

    result = await append_entry(mock_db, create)

    assert result.sequence_num == 0
    assert result.prev_hash == ""
    assert result.agent_id == agent_id
    assert len(result.entry_hash) == 64


@pytest.mark.asyncio
async def test_verify_agent_chain_empty():
    """An agent with no entries should return True."""
    from mams_audit.chain import verify_agent_chain

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(
        return_value=MagicMock(
            scalars=MagicMock(
                return_value=MagicMock(all=MagicMock(return_value=[]))
            )
        )
    )

    agent_id = uuid.uuid4()
    result = await verify_agent_chain(mock_db, agent_id)
    assert result is True


@pytest.mark.asyncio
async def test_append_entry_second_entry_links_prev_hash():
    """Second entry should have sequence_num=1 and prev_hash equal to first entry hash."""
    from mams_audit.chain import append_entry
    from mams_audit.models import AuditEntryRecord
    from mams_core.crypto import compute_entry_hash
    from mams_core.idempotency import new_uuid7

    agent_id = uuid.uuid4()

    # Simulate an existing first entry
    first_entry_id = new_uuid7()
    first_hash = compute_entry_hash(
        entry_id=first_entry_id,
        sequence_num=0,
        event_type=AuditEventType.AGENT_CREATED.value,
        payload={},
        prev_hash="",
    )
    existing_record = MagicMock(spec=AuditEntryRecord)
    existing_record.entry_hash = first_hash
    existing_record.sequence_num = 0

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(
        return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=existing_record))
    )
    mock_db.commit = AsyncMock()

    added_record = None

    def capture_add(record):
        nonlocal added_record
        added_record = record

    mock_db.add = capture_add

    async def mock_refresh(record):
        record.entry_id = uuid.uuid4()
        record.created_at = datetime.now(timezone.utc)

    mock_db.refresh = mock_refresh

    create = AuditEntryCreate(
        agent_id=agent_id,
        event_type=AuditEventType.TASK_SUBMITTED,
        payload={"task": "do something"},
    )

    result = await append_entry(mock_db, create)

    assert result.sequence_num == 1
    assert result.prev_hash == first_hash
    assert len(result.entry_hash) == 64
