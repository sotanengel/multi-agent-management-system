from __future__ import annotations
import uuid
import httpx
from mams_gateway.settings import settings


async def create_container(agent_id: uuid.UUID, role_bundle: dict) -> dict:
    """Create a Docker container for an agent. Returns container info."""
    async with httpx.AsyncClient(base_url=settings.lifecycle_manager_url) as client:
        try:
            resp = await client.post("/v1/containers", json={
                "agent_id": str(agent_id),
                "role_bundle": role_bundle,
            }, timeout=10.0)
            resp.raise_for_status()
            return resp.json()
        except httpx.ConnectError:
            # Lifecycle manager not yet available - return stub
            return {"container_id": f"stub-{agent_id}", "status": "pending"}


async def delete_container(agent_id: uuid.UUID) -> None:
    async with httpx.AsyncClient(base_url=settings.lifecycle_manager_url) as client:
        try:
            resp = await client.delete(f"/v1/containers/{agent_id}", timeout=5.0)
            resp.raise_for_status()
        except httpx.ConnectError:
            pass  # Lifecycle manager not available
