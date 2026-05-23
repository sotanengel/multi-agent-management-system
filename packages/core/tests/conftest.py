"""Shared test fixtures for mams-core."""
import uuid
from datetime import datetime, timezone

import pytest

from mams_core.schemas.agent import (
    Agent,
    AgentStatus,
    ComputationLimits,
    ComputationRole,
    DelegationPolicy,
    MCPToolEntry,
    MCPToolRole,
    OperationRole,
    RoleBundle,
)


@pytest.fixture
def base_role_bundle() -> RoleBundle:
    return RoleBundle(
        name="test-agent",
        operation=OperationRole(
            filesystem_read=["/workspace/data/**"],
            filesystem_write=["/workspace/output/**"],
            network_egress=["api.internal.example.com:443"],
            process_exec=["/usr/bin/python3"],
        ),
        computation=ComputationRole(
            primary_model="anthropic/claude-opus-4-7",
            fallback_models=["ollama/llama-3.1-70b"],
            limits=ComputationLimits(
                max_tokens_per_call=8000,
                monthly_budget_usd=100.0,
            ),
        ),
        mcp_tools=MCPToolRole(
            allowed=[MCPToolEntry(name="filesystem", modes=["read-only"])]
        ),
        delegation=DelegationPolicy(
            can_spawn_children=True,
            max_children=3,
            max_recursion_depth=2,
        ),
    )


@pytest.fixture
def base_agent(base_role_bundle: RoleBundle) -> Agent:
    now = datetime.now(tz=timezone.utc)
    return Agent(
        agent_id=uuid.uuid4(),
        name="test-agent",
        role_bundle=base_role_bundle,
        status=AgentStatus.RUNNING,
        depth=0,
        created_at=now,
        updated_at=now,
    )
