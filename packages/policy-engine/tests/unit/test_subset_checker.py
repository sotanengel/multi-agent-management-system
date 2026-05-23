import pytest
from mams_core.schemas.agent import (
    ComputationLimits,
    ComputationRole,
    DelegationPolicy,
    MCPToolEntry,
    MCPToolRole,
    OperationRole,
    RoleBundle,
)
from mams_policy.subset_checker import (
    check_computation_role,
    check_delegation_policy,
    check_mcp_tool_role,
    check_operation_role,
    check_role_bundle_subset,
)


# --- OperationRole ------------------------------------------------------------

def test_operation_read_exact_match():
    parent = OperationRole(filesystem_read=["/workspace/data/**"])
    child = OperationRole(filesystem_read=["/workspace/data/**"])
    assert check_operation_role(child, parent) == []


def test_operation_read_child_more_specific():
    parent = OperationRole(filesystem_read=["/workspace/**"])
    child = OperationRole(filesystem_read=["/workspace/data/**"])
    assert check_operation_role(child, parent) == []


def test_operation_read_child_outside_parent():
    parent = OperationRole(filesystem_read=["/workspace/data/**"])
    child = OperationRole(filesystem_read=["/etc/**"])
    violations = check_operation_role(child, parent)
    assert len(violations) == 1
    assert "/etc/**" in violations[0]


def test_operation_write_violation():
    parent = OperationRole(filesystem_write=["/workspace/output/**"])
    child = OperationRole(filesystem_write=["/workspace/output/**", "/tmp/**"])
    violations = check_operation_role(child, parent)
    assert any("/tmp/**" in v for v in violations)


def test_operation_network_exact():
    parent = OperationRole(network_egress=["api.example.com:443"])
    child = OperationRole(network_egress=["api.example.com:443"])
    assert check_operation_role(child, parent) == []


def test_operation_network_not_allowed():
    parent = OperationRole(network_egress=["api.example.com:443"])
    child = OperationRole(network_egress=["evil.com:80"])
    violations = check_operation_role(child, parent)
    assert len(violations) == 1


def test_operation_process_allowed():
    parent = OperationRole(process_exec=["/usr/bin/python3", "/usr/bin/jq"])
    child = OperationRole(process_exec=["/usr/bin/python3"])
    assert check_operation_role(child, parent) == []


def test_operation_process_not_allowed():
    parent = OperationRole(process_exec=["/usr/bin/python3"])
    child = OperationRole(process_exec=["/bin/bash"])
    violations = check_operation_role(child, parent)
    assert any("/bin/bash" in v for v in violations)


def test_operation_empty_child():
    parent = OperationRole(filesystem_read=["/workspace/**"])
    child = OperationRole()
    assert check_operation_role(child, parent) == []


# --- ComputationRole ----------------------------------------------------------

def make_comp(
    primary: str,
    fallbacks: list[str] = [],
    max_tokens: int = 4096,
    max_steps: int = 20,
    budget: float = 10.0,
) -> ComputationRole:
    return ComputationRole(
        primary_model=primary,
        fallback_models=fallbacks,
        limits=ComputationLimits(
            max_tokens_per_call=max_tokens,
            max_steps_per_task=max_steps,
            monthly_budget_usd=budget,
        ),
    )


def test_computation_same_model():
    parent = make_comp("anthropic/claude-opus-4-7")
    child = make_comp("anthropic/claude-opus-4-7")
    assert check_computation_role(child, parent) == []


def test_computation_model_not_in_parent():
    parent = make_comp("anthropic/claude-opus-4-7")
    child = make_comp("openai/gpt-4o")
    violations = check_computation_role(child, parent)
    assert any("openai/gpt-4o" in v for v in violations)


def test_computation_fallback_in_parent():
    parent = make_comp("anthropic/claude-opus-4-7", fallbacks=["ollama/llama-3"])
    child = make_comp("ollama/llama-3")
    assert check_computation_role(child, parent) == []


def test_computation_tokens_within_limit():
    parent = make_comp("anthropic/claude-opus-4-7", max_tokens=8000)
    child = make_comp("anthropic/claude-opus-4-7", max_tokens=4000)
    assert check_computation_role(child, parent) == []


def test_computation_tokens_exceeds_limit():
    parent = make_comp("anthropic/claude-opus-4-7", max_tokens=4096)
    child = make_comp("anthropic/claude-opus-4-7", max_tokens=8192)
    violations = check_computation_role(child, parent)
    assert any("max_tokens_per_call" in v for v in violations)


def test_computation_budget_exceeds():
    parent = make_comp("anthropic/claude-opus-4-7", budget=10.0)
    child = make_comp("anthropic/claude-opus-4-7", budget=100.0)
    violations = check_computation_role(child, parent)
    assert any("monthly_budget_usd" in v for v in violations)


def test_computation_steps_exceeds():
    parent = make_comp("anthropic/claude-opus-4-7", max_steps=10)
    child = make_comp("anthropic/claude-opus-4-7", max_steps=20)
    violations = check_computation_role(child, parent)
    assert any("max_steps_per_task" in v for v in violations)


# --- MCPToolRole --------------------------------------------------------------

def test_mcp_tool_allowed():
    parent = MCPToolRole(allowed=[MCPToolEntry(name="filesystem", modes=["read-only"])])
    child = MCPToolRole(allowed=[MCPToolEntry(name="filesystem", modes=["read-only"])])
    assert check_mcp_tool_role(child, parent) == []


def test_mcp_tool_not_in_parent():
    parent = MCPToolRole(allowed=[MCPToolEntry(name="filesystem", modes=["read-only"])])
    child = MCPToolRole(allowed=[MCPToolEntry(name="shell", modes=["read-write"])])
    violations = check_mcp_tool_role(child, parent)
    assert any("shell" in v for v in violations)


def test_mcp_tool_mode_escalation():
    parent = MCPToolRole(allowed=[MCPToolEntry(name="filesystem", modes=["read-only"])])
    child = MCPToolRole(allowed=[MCPToolEntry(name="filesystem", modes=["read-write"])])
    violations = check_mcp_tool_role(child, parent)
    assert any("read-write" in v for v in violations)


def test_mcp_tool_empty_child():
    parent = MCPToolRole(allowed=[MCPToolEntry(name="filesystem", modes=["read-only"])])
    child = MCPToolRole()
    assert check_mcp_tool_role(child, parent) == []


# --- DelegationPolicy ---------------------------------------------------------

def test_delegation_valid():
    parent = DelegationPolicy(can_spawn_children=True, max_children=5, max_recursion_depth=3)
    child = DelegationPolicy(can_spawn_children=True, max_children=3, max_recursion_depth=2)
    assert check_delegation_policy(child, parent) == []


def test_delegation_spawn_escalation():
    parent = DelegationPolicy(can_spawn_children=False, max_children=0, max_recursion_depth=0)
    child = DelegationPolicy(can_spawn_children=True, max_children=1, max_recursion_depth=0)
    violations = check_delegation_policy(child, parent)
    assert any("can_spawn_children" in v for v in violations)


def test_delegation_depth_amplification():
    parent = DelegationPolicy(can_spawn_children=True, max_children=5, max_recursion_depth=2)
    child = DelegationPolicy(can_spawn_children=True, max_children=3, max_recursion_depth=2)
    violations = check_delegation_policy(child, parent)
    assert any("depth-amplification" in v for v in violations)


def test_delegation_max_children_exceeds():
    parent = DelegationPolicy(can_spawn_children=True, max_children=3, max_recursion_depth=3)
    child = DelegationPolicy(can_spawn_children=True, max_children=10, max_recursion_depth=2)
    violations = check_delegation_policy(child, parent)
    assert any("max_children" in v for v in violations)


# --- Full RoleBundle ----------------------------------------------------------

def make_bundle(name: str = "test") -> RoleBundle:
    return RoleBundle(
        name=name,
        computation=ComputationRole(primary_model="anthropic/claude-opus-4-7"),
        operation=OperationRole(filesystem_read=["/workspace/**"]),
        delegation=DelegationPolicy(can_spawn_children=True, max_children=3, max_recursion_depth=3),
    )


def test_full_bundle_valid_subset():
    parent = make_bundle("parent")
    child = RoleBundle(
        name="child",
        computation=ComputationRole(primary_model="anthropic/claude-opus-4-7"),
        operation=OperationRole(filesystem_read=["/workspace/data/**"]),
        delegation=DelegationPolicy(can_spawn_children=True, max_children=2, max_recursion_depth=2),
    )
    assert check_role_bundle_subset(child, parent) == []


def test_full_bundle_multiple_violations():
    parent = make_bundle("parent")
    child = RoleBundle(
        name="bad-child",
        computation=ComputationRole(primary_model="openai/gpt-4o"),  # not allowed
        operation=OperationRole(filesystem_read=["/etc/**"]),  # not allowed
        delegation=DelegationPolicy(
            can_spawn_children=False, max_children=0, max_recursion_depth=3
        ),  # depth amplification
    )
    violations = check_role_bundle_subset(child, parent)
    assert len(violations) >= 2
