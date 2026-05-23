"""HTTP client for Lifecycle Manager - used for child agent spawning."""
from __future__ import annotations

import uuid
import httpx
from mams_agent.settings import settings


async def create_child_container(agent_id: uuid.UUID, role_bundle: dict) -> dict:
    async with httpx.AsyncClient(base_url=settings.lifecycle_manager_url, timeout=10.0) as client:
        resp = await client.post("/v1/containers", json={
            "agent_id": str(agent_id),
            "role_bundle": role_bundle,
        })
        resp.raise_for_status()
        return resp.json()
