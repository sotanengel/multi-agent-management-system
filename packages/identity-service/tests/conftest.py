import uuid

import pytest

from mams_core.schemas.agent import (
    ComputationRole,
    DelegationPolicy,
    OperationRole,
    RoleBundle,
)


@pytest.fixture
def sample_role_bundle() -> RoleBundle:
    return RoleBundle(
        name="test-bundle",
        computation=ComputationRole(primary_model="anthropic/claude-opus-4-7"),
        operation=OperationRole(),
        delegation=DelegationPolicy(),
    )


@pytest.fixture
def sample_agent_id() -> uuid.UUID:
    return uuid.uuid4()
