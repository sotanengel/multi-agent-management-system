import uuid
import pytest
from mams_core.schemas.agent import (
    ComputationRole,
    DelegationPolicy,
    MCPToolEntry,
    MCPToolRole,
    OperationRole,
    RoleBundle,
)
from mams_core.schemas.policy import PolicyAction, PolicyPrincipal, PolicyRequest, PolicyResource
from mams_policy.evaluator import evaluate


def make_principal(
    can_spawn: bool = True,
    read_paths: list[str] | None = None,
    write_paths: list[str] | None = None,
    models: list[str] | None = None,
    tools: list[str] | None = None,
    max_recursion: int = 3,
    max_children: int = 5,
) -> PolicyPrincipal:
    if read_paths is None:
        read_paths = ["/workspace/**"]
    if write_paths is None:
        write_paths = ["/workspace/output/**"]
    if models is None:
        models = ["anthropic/claude-opus-4-7"]
    tool_entries = [MCPToolEntry(name=t, modes=["read-write"]) for t in (tools or [])]
    return PolicyPrincipal(
        agent_id=uuid.uuid4(),
        role_bundle=RoleBundle(
            name="test",
            computation=ComputationRole(primary_model=models[0], fallback_models=models[1:]),
            operation=OperationRole(
                filesystem_read=read_paths,
                filesystem_write=write_paths,
                process_exec=["/usr/bin/python3"],
            ),
            mcp_tools=MCPToolRole(allowed=tool_entries),
            delegation=DelegationPolicy(
                can_spawn_children=can_spawn,
                max_children=max_children,
                max_recursion_depth=max_recursion,
            ),
        ),
    )


def test_call_model_allowed():
    principal = make_principal(models=["anthropic/claude-opus-4-7"])
    req = PolicyRequest(
        principal=principal,
        action=PolicyAction.CALL_MODEL,
        resource=PolicyResource(model_id="anthropic/claude-opus-4-7"),
    )
    decision = evaluate(req)
    assert decision.allowed is True


def test_call_model_not_allowed():
    principal = make_principal(models=["anthropic/claude-opus-4-7"])
    req = PolicyRequest(
        principal=principal,
        action=PolicyAction.CALL_MODEL,
        resource=PolicyResource(model_id="openai/gpt-4o"),
    )
    decision = evaluate(req)
    assert decision.allowed is False


def test_call_model_missing_id():
    principal = make_principal()
    req = PolicyRequest(
        principal=principal,
        action=PolicyAction.CALL_MODEL,
        resource=PolicyResource(),
    )
    decision = evaluate(req)
    assert decision.allowed is False


def test_read_file_allowed():
    principal = make_principal(read_paths=["/workspace/**"])
    req = PolicyRequest(
        principal=principal,
        action=PolicyAction.READ_FILE,
        resource=PolicyResource(file_path="/workspace/data/file.csv"),
    )
    decision = evaluate(req)
    assert decision.allowed is True


def test_read_file_denied():
    principal = make_principal(read_paths=["/workspace/**"])
    req = PolicyRequest(
        principal=principal,
        action=PolicyAction.READ_FILE,
        resource=PolicyResource(file_path="/etc/passwd"),
    )
    decision = evaluate(req)
    assert decision.allowed is False


def test_write_file_allowed():
    principal = make_principal(write_paths=["/workspace/output/**"])
    req = PolicyRequest(
        principal=principal,
        action=PolicyAction.WRITE_FILE,
        resource=PolicyResource(file_path="/workspace/output/result.json"),
    )
    decision = evaluate(req)
    assert decision.allowed is True


def test_write_file_denied():
    principal = make_principal(write_paths=["/workspace/output/**"])
    req = PolicyRequest(
        principal=principal,
        action=PolicyAction.WRITE_FILE,
        resource=PolicyResource(file_path="/workspace/data/file.csv"),
    )
    decision = evaluate(req)
    assert decision.allowed is False


def test_exec_process_allowed():
    principal = make_principal()
    req = PolicyRequest(
        principal=principal,
        action=PolicyAction.EXEC_PROCESS,
        resource=PolicyResource(process_path="/usr/bin/python3"),
    )
    decision = evaluate(req)
    assert decision.allowed is True


def test_exec_process_denied():
    principal = make_principal()
    req = PolicyRequest(
        principal=principal,
        action=PolicyAction.EXEC_PROCESS,
        resource=PolicyResource(process_path="/bin/bash"),
    )
    decision = evaluate(req)
    assert decision.allowed is False


def test_call_tool_allowed():
    principal = make_principal(tools=["filesystem"])
    req = PolicyRequest(
        principal=principal,
        action=PolicyAction.CALL_TOOL,
        resource=PolicyResource(tool_name="filesystem"),
    )
    decision = evaluate(req)
    assert decision.allowed is True


def test_call_tool_denied():
    principal = make_principal(tools=["filesystem"])
    req = PolicyRequest(
        principal=principal,
        action=PolicyAction.CALL_TOOL,
        resource=PolicyResource(tool_name="shell"),
    )
    decision = evaluate(req)
    assert decision.allowed is False


def test_spawn_child_no_permission():
    principal = make_principal(can_spawn=False, max_recursion=0, max_children=0)
    child_bundle = RoleBundle(
        name="child",
        computation=ComputationRole(primary_model="anthropic/claude-opus-4-7"),
        delegation=DelegationPolicy(can_spawn_children=False, max_children=0, max_recursion_depth=0),
    )
    req = PolicyRequest(
        principal=principal,
        action=PolicyAction.SPAWN_CHILD,
        resource=PolicyResource(child_role_bundle=child_bundle),
    )
    decision = evaluate(req)
    assert decision.allowed is False


def test_spawn_child_valid():
    principal = make_principal(can_spawn=True, max_recursion=3, max_children=5)
    child_bundle = RoleBundle(
        name="child",
        computation=ComputationRole(primary_model="anthropic/claude-opus-4-7"),
        operation=OperationRole(filesystem_read=["/workspace/**"]),
        delegation=DelegationPolicy(can_spawn_children=True, max_children=3, max_recursion_depth=2),
    )
    req = PolicyRequest(
        principal=principal,
        action=PolicyAction.SPAWN_CHILD,
        resource=PolicyResource(child_role_bundle=child_bundle),
    )
    decision = evaluate(req)
    assert decision.allowed is True
