"""Hash-chain management for audit entries."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mams_core.crypto import compute_entry_hash, verify_chain
from mams_core.idempotency import new_uuid7
from mams_core.schemas.audit import AuditEntry, AuditEntryCreate, AuditEventType
from mams_audit.models import AuditEntryRecord


async def get_last_entry(db: AsyncSession, agent_id: uuid.UUID) -> AuditEntryRecord | None:
    """Get the most recent audit entry for an agent."""
    result = await db.execute(
        select(AuditEntryRecord)
        .where(AuditEntryRecord.agent_id == agent_id)
        .order_by(AuditEntryRecord.sequence_num.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def append_entry(
    db: AsyncSession, create: AuditEntryCreate
) -> AuditEntry:
    """Append a new entry to the audit chain for an agent."""
    last = await get_last_entry(db, create.agent_id)
    prev_hash = last.entry_hash if last else ""
    sequence_num = (last.sequence_num + 1) if last else 0

    entry_id = new_uuid7()
    entry_hash = compute_entry_hash(
        entry_id=entry_id,
        sequence_num=sequence_num,
        event_type=create.event_type.value,
        payload=create.payload,
        prev_hash=prev_hash,
    )

    record = AuditEntryRecord(
        entry_id=entry_id,
        agent_id=create.agent_id,
        sequence_num=sequence_num,
        event_type=create.event_type.value,
        payload=create.payload,
        prev_hash=prev_hash,
        entry_hash=entry_hash,
        created_at=datetime.now(UTC),
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    return AuditEntry(
        entry_id=record.entry_id,
        agent_id=record.agent_id,
        sequence_num=record.sequence_num,
        event_type=AuditEventType(record.event_type),
        payload=record.payload,
        prev_hash=record.prev_hash,
        entry_hash=record.entry_hash,
        created_at=record.created_at,
    )


async def get_entries(
    db: AsyncSession,
    agent_id: uuid.UUID,
    from_seq: int = 0,
    limit: int = 100,
) -> list[AuditEntry]:
    """Retrieve audit entries for an agent starting from a sequence number."""
    result = await db.execute(
        select(AuditEntryRecord)
        .where(
            AuditEntryRecord.agent_id == agent_id,
            AuditEntryRecord.sequence_num >= from_seq,
        )
        .order_by(AuditEntryRecord.sequence_num)
        .limit(limit)
    )
    records = result.scalars().all()
    return [
        AuditEntry(
            entry_id=r.entry_id,
            agent_id=r.agent_id,
            sequence_num=r.sequence_num,
            event_type=AuditEventType(r.event_type),
            payload=r.payload,
            prev_hash=r.prev_hash,
            entry_hash=r.entry_hash,
            created_at=r.created_at,
        )
        for r in records
    ]


async def verify_agent_chain(db: AsyncSession, agent_id: uuid.UUID) -> bool:
    """Verify the complete hash chain for an agent."""
    entries = await get_entries(db, agent_id, limit=10000)
    entries_dicts = [e.model_dump(mode="json") for e in entries]
    # Convert UUID objects to strings for verify_chain
    for d in entries_dicts:
        d["entry_id"] = str(d["entry_id"])
        d["agent_id"] = str(d["agent_id"])
        d["event_type"] = d["event_type"] if isinstance(d["event_type"], str) else d["event_type"].value
    return verify_chain(entries_dicts)
