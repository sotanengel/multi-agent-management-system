"""HTTP client for Model Gateway."""
from __future__ import annotations

import uuid
import httpx
from mams_core.idempotency import new_uuid7
from mams_core.schemas.model import LLMMessage, LLMRequest, LLMResponse, MessageRole
from mams_agent.settings import settings


async def complete(
    messages: list[LLMMessage],
    model: str | None = None,
    max_tokens: int | None = None,
) -> LLMResponse:
    """Send completion request to Model Gateway."""
    request = LLMRequest(
        agent_id=uuid.UUID(settings.agent_id) if settings.agent_id else uuid.uuid4(),
        model=model or settings.primary_model,
        messages=messages,
        max_tokens=max_tokens or settings.max_tokens_per_call,
        operation_id=new_uuid7(),
    )
    async with httpx.AsyncClient(base_url=settings.model_gateway_url, timeout=120.0) as client:
        resp = await client.post("/v1/completions", json=request.model_dump(mode="json"))
        resp.raise_for_status()
        return LLMResponse(**resp.json())
