from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from mams_core.schemas.model import LLMRequest, LLMResponse
from mams_model_gw.budget_tracker import record_usage
from mams_model_gw.db import get_session
from mams_model_gw.router_logic import complete

router = APIRouter()


@router.post("/completions", response_model=LLMResponse)
async def create_completion(
    request: LLMRequest,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> LLMResponse:
    response = await complete(request)

    # Record usage (best-effort - don't fail if DB is down)
    try:
        await record_usage(
            db=db,
            agent_id=request.agent_id,
            completion_id=response.completion_id,
            model_used=response.model_used,
            usage=response.usage,
        )
    except Exception:
        pass

    return response
