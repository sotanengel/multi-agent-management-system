from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from mams_core.idempotency import new_uuid7
from mams_core.schemas.agent import Agent, AgentStatus, RoleBundle
from mams_core.schemas.policy import PolicyAction, PolicyPrincipal, PolicyResource
from mams_gateway import clients
from mams_gateway.clients import audit, identity, lifecycle, policy
from mams_gateway.dependencies import get_current_agent_id

router = APIRouter(prefix="/v1/agents")


class CreateAgentRequest(BaseModel):
    name: str
    role_bundle: RoleBundle
    parent_agent_id: uuid.UUID | None = None


@router.post("", response_model=Agent, status_code=201)
async def create_agent(
    body: CreateAgentRequest,
    request: Request,
) -> Agent:
    agent_id = new_uuid7()
    now = datetime.now(tz=timezone.utc)
    depth = 0

    # If child agent, validate role subset via policy engine
    if body.parent_agent_id:
        # Get parent role bundle from identity service
        try:
            parent_data = await identity.get_agent(body.parent_agent_id)
            parent_role_bundle = RoleBundle(**parent_data["role_bundle"])
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Parent agent not found: {e}") from e

        principal = PolicyPrincipal(
            agent_id=body.parent_agent_id,
            role_bundle=parent_role_bundle,
        )
        policy_req = {
            "principal": principal.model_dump(mode="json"),
            "action": PolicyAction.SPAWN_CHILD.value,
            "resource": {
                "child_role_bundle": body.role_bundle.model_dump(mode="json"),
            },
        }
        decision = await policy.evaluate(policy_req)
        if not decision["allowed"]:
            raise HTTPException(
                status_code=403,
                detail=f"Policy denied: {decision['reason']}",
            )
        depth = parent_data.get("depth", 0) + 1

    # Register in identity service
    await identity.register_agent(
        agent_id=agent_id,
        name=body.name,
        role_bundle=body.role_bundle.model_dump(mode="json"),
        parent_agent_id=body.parent_agent_id,
        depth=depth,
    )

    # Create container
    container_info = await lifecycle.create_container(
        agent_id=agent_id,
        role_bundle=body.role_bundle.model_dump(mode="json"),
    )

    # Record audit event (best-effort)
    await audit.record_event(
        agent_id=agent_id,
        event_type="agent.created",
        payload={"name": body.name, "depth": depth},
    )

    return Agent(
        agent_id=agent_id,
        name=body.name,
        parent_agent_id=body.parent_agent_id,
        role_bundle=body.role_bundle,
        status=AgentStatus.PENDING,
        container_id=container_info.get("container_id"),
        depth=depth,
        created_at=now,
        updated_at=now,
    )


@router.get("", response_model=list[Agent])
async def list_agents() -> list[Agent]:
    return []


@router.get("/{agent_id}", response_model=Agent)
async def get_agent(agent_id: uuid.UUID) -> Agent:
    try:
        data = await identity.get_agent(agent_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail="Agent not found") from e
    now = datetime.now(tz=timezone.utc)
    return Agent(
        agent_id=uuid.UUID(data["agent_id"]),
        name=data["name"],
        parent_agent_id=uuid.UUID(data["parent_agent_id"]) if data.get("parent_agent_id") else None,
        role_bundle=RoleBundle(**data["role_bundle"]),
        status=AgentStatus(data.get("status", "pending")),
        depth=data.get("depth", 0),
        created_at=data.get("created_at", now),
        updated_at=data.get("updated_at", now),
    )


@router.delete("/{agent_id}", status_code=204)
async def delete_agent(agent_id: uuid.UUID) -> None:
    await lifecycle.delete_container(agent_id)
    await audit.record_event(
        agent_id=agent_id,
        event_type="agent.terminated",
        payload={"agent_id": str(agent_id)},
    )
