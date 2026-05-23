import pytest
import uuid
from mams_core.schemas.agent import (
    ComputationRole, DelegationPolicy, OperationRole, RoleBundle
)


@pytest.fixture
def sample_agent_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def sample_role_bundle() -> RoleBundle:
    return RoleBundle(
        name="test-agent",
        computation=ComputationRole(primary_model="anthropic/claude-opus-4-7"),
        operation=OperationRole(),
        delegation=DelegationPolicy(
            can_spawn_children=True,
            max_children=3,
            max_recursion_depth=2,
        ),
    )
