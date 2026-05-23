import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mams_core.schemas.agent import Agent, AgentStatus, RoleBundle
from mams_identity.dependencies import get_db
from mams_identity.models import AgentRecord

router = APIRouter(tags=["agents"])


class AgentRegisterRequest(BaseModel):
    agent_id: uuid.UUID
    name: str
    parent_agent_id: uuid.UUID | None = None
    role_bundle: RoleBundle
    depth: int = 0


def _record_to_agent(record: AgentRecord) -> Agent:
    role_bundle = RoleBundle.model_validate(record.role_bundle_json)
    return Agent(
        agent_id=record.agent_id,
        name=record.name,
        parent_agent_id=record.parent_agent_id,
        role_bundle=role_bundle,
        status=AgentStatus(record.status),
        container_id=None,
        depth=record.depth,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


@router.post("/agents", response_model=Agent, status_code=status.HTTP_201_CREATED)
async def register_agent(
    request: AgentRegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> Agent:
    """Register a new agent and store its role bundle."""
    existing = await db.get(AgentRecord, request.agent_id)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Agent {request.agent_id} already exists",
        )

    record = AgentRecord(
        agent_id=request.agent_id,
        name=request.name,
        parent_agent_id=request.parent_agent_id,
        role_bundle_json=request.role_bundle.model_dump(),
        status=AgentStatus.PENDING.value,
        depth=request.depth,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return _record_to_agent(record)


@router.get("/agents/{agent_id}", response_model=Agent)
async def get_agent(
    agent_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Agent:
    """Retrieve an agent record by ID."""
    result = await db.execute(select(AgentRecord).where(AgentRecord.agent_id == agent_id))
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found",
        )
    return _record_to_agent(record)


@router.delete("/agents/{agent_id}", response_model=Agent)
async def delete_agent(
    agent_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Agent:
    """Soft-delete an agent by setting status to 'terminated'."""
    result = await db.execute(select(AgentRecord).where(AgentRecord.agent_id == agent_id))
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found",
        )
    record.status = AgentStatus.TERMINATED.value
    record.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(record)
    return _record_to_agent(record)
