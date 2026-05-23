from __future__ import annotations
import uuid
from typing import Any
import httpx
from mams_gateway.settings import settings


async def record_event(agent_id: uuid.UUID, event_type: str, payload: dict[str, Any]) -> None:
    async with httpx.AsyncClient(base_url=settings.audit_service_url) as client:
        try:
            await client.post("/v1/audit", json={
                "agent_id": str(agent_id),
                "event_type": event_type,
                "payload": payload,
            }, timeout=3.0)
        except Exception:
            pass  # Audit failures are non-fatal
