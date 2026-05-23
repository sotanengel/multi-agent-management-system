import uuid
import pytest
from unittest.mock import AsyncMock, patch
from mams_agent.spawn import spawn_child_agent


@pytest.mark.asyncio
async def test_spawn_blocked_at_max_depth(sample_role_bundle):
    parent_id = uuid.uuid4()
    result = await spawn_child_agent(
        parent_id=parent_id,
        child_name="child",
        child_role_bundle=sample_role_bundle,
        max_recursion_depth=2,
        current_depth=2,  # AT max depth, should be blocked
    )
    assert result is None


@pytest.mark.asyncio
async def test_spawn_success(sample_role_bundle):
    parent_id = uuid.uuid4()

    with patch("mams_agent.spawn.create_child_container", new=AsyncMock(return_value={"container_id": "abc"})):
        result = await spawn_child_agent(
            parent_id=parent_id,
            child_name="child",
            child_role_bundle=sample_role_bundle,
            max_recursion_depth=3,
            current_depth=1,
        )

    assert result is not None
    assert isinstance(result, uuid.UUID)


@pytest.mark.asyncio
async def test_spawn_lifecycle_failure(sample_role_bundle):
    parent_id = uuid.uuid4()

    with patch("mams_agent.spawn.create_child_container", new=AsyncMock(side_effect=Exception("Docker error"))):
        result = await spawn_child_agent(
            parent_id=parent_id,
            child_name="child",
            child_role_bundle=sample_role_bundle,
            max_recursion_depth=3,
            current_depth=1,
        )

    assert result is None
