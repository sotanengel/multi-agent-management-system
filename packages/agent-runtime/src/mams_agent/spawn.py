"""Child agent spawning logic."""
from __future__ import annotations

import logging
import uuid
from typing import Any

from mams_core.idempotency import new_uuid7
from mams_core.schemas.agent import RoleBundle
from mams_agent.clients.lifecycle import create_child_container

logger = logging.getLogger(__name__)


async def spawn_child_agent(
    parent_id: uuid.UUID,
    child_name: str,
    child_role_bundle: RoleBundle,
    max_recursion_depth: int,
    current_depth: int,
) -> uuid.UUID | None:
    """Spawn a child agent container.

    Returns the new agent's UUID, or None if spawning is not permitted.
    """
    if current_depth >= max_recursion_depth:
        logger.warning(
            "Cannot spawn child: depth %d would exceed max %d",
            current_depth + 1,
            max_recursion_depth,
        )
        return None

    if not child_role_bundle.delegation.can_spawn_children and current_depth == 0:
        pass  # parent decides, not child bundle

    child_id = new_uuid7()
    try:
        await create_child_container(
            agent_id=child_id,
            role_bundle=child_role_bundle.model_dump(mode="json"),
        )
        logger.info("Spawned child agent %s (depth=%d)", child_id, current_depth + 1)
        return child_id
    except Exception as e:
        logger.error("Failed to spawn child agent: %s", e)
        return None
