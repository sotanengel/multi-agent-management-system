from __future__ import annotations
import uuid
import httpx
from mams_gateway.settings import settings


async def verify_token(token: str) -> dict:
    """Returns {"valid": bool, "agent_id": str|None, "role": str|None}"""
    async with httpx.AsyncClient(base_url=settings.identity_service_url) as client:
        resp = await client.post("/v1/tokens/verify", json={"token": token}, timeout=5.0)
        resp.raise_for_status()
        return resp.json()


async def register_agent(agent_id: uuid.UUID, name: str, role_bundle: dict,
                          parent_agent_id: uuid.UUID | None = None, depth: int = 0) -> dict:
    async with httpx.AsyncClient(base_url=settings.identity_service_url) as client:
        resp = await client.post("/v1/agents", json={
            "agent_id": str(agent_id),
            "name": name,
            "parent_agent_id": str(parent_agent_id) if parent_agent_id else None,
            "role_bundle": role_bundle,
            "depth": depth,
        }, timeout=5.0)
        resp.raise_for_status()
        return resp.json()


async def issue_token(agent_id: uuid.UUID) -> str:
    async with httpx.AsyncClient(base_url=settings.identity_service_url) as client:
        resp = await client.post("/v1/tokens", json={"agent_id": str(agent_id)}, timeout=5.0)
        resp.raise_for_status()
        return resp.json()["access_token"]


async def get_agent(agent_id: uuid.UUID) -> dict:
    async with httpx.AsyncClient(base_url=settings.identity_service_url) as client:
        resp = await client.get(f"/v1/agents/{agent_id}", timeout=5.0)
        resp.raise_for_status()
        return resp.json()
