from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mams_core.errors import ContainerError
from mams_core.schemas.agent import RoleBundle
from mams_lifecycle.db import get_session
from mams_lifecycle.docker_client import create_agent_container, stop_agent_container
from mams_lifecycle.models import ContainerRecord
from mams_lifecycle.settings import settings

router = APIRouter()


class CreateContainerRequest(BaseModel):
    agent_id: uuid.UUID
    role_bundle: RoleBundle


class ContainerResponse(BaseModel):
    agent_id: uuid.UUID
    container_id: str | None
    status: str


@router.post("/containers", response_model=ContainerResponse, status_code=201)
async def create_container(
    body: CreateContainerRequest,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ContainerResponse:
    container_id: str | None = None
    status = "running"

    try:
        container_id = create_agent_container(body.agent_id, body.role_bundle)
    except ContainerError:
        # If Docker not available (e.g., no agent runtime image yet), record as pending
        status = "pending"
        container_id = f"stub-{body.agent_id}"

    record = ContainerRecord(
        agent_id=body.agent_id,
        container_id=container_id,
        image=settings.agent_runtime_image,
        status=status,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db.add(record)
    await db.commit()

    return ContainerResponse(
        agent_id=body.agent_id,
        container_id=container_id,
        status=status,
    )


@router.delete("/containers/{agent_id}", status_code=204)
async def delete_container(
    agent_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    result = await db.execute(
        select(ContainerRecord).where(ContainerRecord.agent_id == agent_id)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Container not found")

    if record.container_id and not record.container_id.startswith("stub-"):
        try:
            stop_agent_container(record.container_id)
        except ContainerError:
            pass  # Log but don't fail - container may already be gone

    record.status = "terminated"
    record.updated_at = datetime.now(UTC)
    await db.commit()


@router.get("/containers/{agent_id}", response_model=ContainerResponse)
async def get_container(
    agent_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ContainerResponse:
    result = await db.execute(
        select(ContainerRecord).where(ContainerRecord.agent_id == agent_id)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Container not found")
    return ContainerResponse(
        agent_id=record.agent_id,
        container_id=record.container_id,
        status=record.status,
    )
