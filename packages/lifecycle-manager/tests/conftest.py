import uuid
import pytest
from mams_core.schemas.agent import (
    ComputationRole, ComputationLimits, DelegationPolicy, OperationRole, RoleBundle
)


@pytest.fixture
def sample_role_bundle() -> RoleBundle:
    return RoleBundle(
        name="test-agent",
        computation=ComputationRole(
            primary_model="anthropic/claude-opus-4-7",
            limits=ComputationLimits(
                max_tokens_per_call=4096,
                cpu_limit="0.5",
                memory_limit="256m",
            ),
        ),
        operation=OperationRole(),
        delegation=DelegationPolicy(),
    )


@pytest.fixture
def sample_agent_id() -> uuid.UUID:
    return uuid.uuid4()
