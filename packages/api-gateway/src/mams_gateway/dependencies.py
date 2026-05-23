from __future__ import annotations
import uuid
from fastapi import HTTPException, Request


def get_current_agent_id(request: Request) -> uuid.UUID:
    agent_id = getattr(request.state, "agent_id", None)
    if not agent_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return uuid.UUID(agent_id)
