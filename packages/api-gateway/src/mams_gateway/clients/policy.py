from __future__ import annotations
import httpx
from mams_gateway.settings import settings


async def evaluate(request_body: dict) -> dict:
    """Returns {"allowed": bool, "reason": str, "violations": list}"""
    async with httpx.AsyncClient(base_url=settings.policy_engine_url) as client:
        resp = await client.post("/v1/evaluate", json=request_body, timeout=5.0)
        resp.raise_for_status()
        return resp.json()
