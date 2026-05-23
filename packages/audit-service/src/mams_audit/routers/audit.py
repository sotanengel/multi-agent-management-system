from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from mams_core.schemas.audit import AuditEntry, AuditEntryCreate
from mams_audit.chain import append_entry, get_entries, verify_agent_chain
from mams_audit.db import get_session

router = APIRouter()


@router.post("/audit", response_model=AuditEntry)
async def create_audit_entry(
    body: AuditEntryCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> AuditEntry:
    return await append_entry(db, body)


@router.get("/audit/{agent_id}", response_model=dict)
async def get_audit_entries(
    agent_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    from_seq: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> dict:
    entries = await get_entries(db, agent_id, from_seq=from_seq, limit=limit)
    chain_valid = await verify_agent_chain(db, agent_id)
    return {
        "agent_id": str(agent_id),
        "entries": [e.model_dump(mode="json") for e in entries],
        "chain_valid": chain_valid,
        "total": len(entries),
    }
