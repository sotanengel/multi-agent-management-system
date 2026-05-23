"""Token and cost usage tracking."""
from __future__ import annotations

import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from mams_core.idempotency import new_uuid7
from mams_core.schemas.model import TokenUsage
from mams_model_gw.models import ModelUsageRecord


async def record_usage(
    db: AsyncSession,
    agent_id: uuid.UUID,
    completion_id: uuid.UUID,
    model_used: str,
    usage: TokenUsage,
) -> None:
    """Persist model usage for budget tracking."""
    record = ModelUsageRecord(
        id=new_uuid7(),
        agent_id=agent_id,
        completion_id=completion_id,
        model_used=model_used,
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        cost_usd=usage.cost_usd,
    )
    db.add(record)
    await db.commit()
