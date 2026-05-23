"""Policy evaluation logic."""
from __future__ import annotations

from mams_core.schemas.policy import PolicyAction, PolicyDecision, PolicyRequest
from mams_policy.subset_checker import check_role_bundle_subset


def evaluate(request: PolicyRequest) -> PolicyDecision:
    """Evaluate a policy request and return a decision."""
    match request.action:
        case PolicyAction.SPAWN_CHILD:
            return _evaluate_spawn_child(request)
        case PolicyAction.CALL_MODEL:
            return _evaluate_call_model(request)
        case PolicyAction.CALL_TOOL:
            return _evaluate_call_tool(request)
        case PolicyAction.READ_FILE:
            return _evaluate_read_file(request)
        case PolicyAction.WRITE_FILE:
            return _evaluate_write_file(request)
        case PolicyAction.EXEC_PROCESS:
            return _evaluate_exec_process(request)
        case _:
            return PolicyDecision(allowed=True, reason="action not restricted")


def _evaluate_spawn_child(request: PolicyRequest) -> PolicyDecision:
    parent_bundle = request.principal.role_bundle
    if not parent_bundle.delegation.can_spawn_children:
        return PolicyDecision(
            allowed=False,
            reason="agent not permitted to spawn children",
            violations=["can_spawn_children is False"],
        )
    child_bundle = request.resource.child_role_bundle
    if child_bundle is None:
        return PolicyDecision(allowed=False, reason="child_role_bundle required for spawn_child")
    violations = check_role_bundle_subset(child_bundle, parent_bundle)
    if violations:
        return PolicyDecision(allowed=False, reason="child role exceeds parent role", violations=violations)
    return PolicyDecision(allowed=True, reason="child role is valid subset of parent")


def _evaluate_call_model(request: PolicyRequest) -> PolicyDecision:
    model_id = request.resource.model_id
    if model_id is None:
        return PolicyDecision(allowed=False, reason="model_id required for call_model")
    comp = request.principal.role_bundle.computation
    allowed_models = {comp.primary_model} | set(comp.fallback_models)
    if model_id not in allowed_models:
        return PolicyDecision(
            allowed=False,
            reason=f"model '{model_id}' not in agent's allowed models",
            violations=[f"model '{model_id}' not permitted"],
        )
    return PolicyDecision(allowed=True, reason="model permitted")


def _evaluate_call_tool(request: PolicyRequest) -> PolicyDecision:
    tool_name = request.resource.tool_name
    if tool_name is None:
        return PolicyDecision(allowed=False, reason="tool_name required for call_tool")
    allowed = {t.name for t in request.principal.role_bundle.mcp_tools.allowed}
    if tool_name not in allowed:
        return PolicyDecision(
            allowed=False,
            reason=f"tool '{tool_name}' not in agent's allowed tools",
            violations=[f"tool '{tool_name}' not permitted"],
        )
    return PolicyDecision(allowed=True, reason="tool permitted")


def _evaluate_read_file(request: PolicyRequest) -> PolicyDecision:
    import fnmatch
    file_path = request.resource.file_path
    if file_path is None:
        return PolicyDecision(allowed=False, reason="file_path required for read_file")
    allowed_paths = request.principal.role_bundle.operation.filesystem_read
    for pattern in allowed_paths:
        if fnmatch.fnmatch(file_path, pattern):
            return PolicyDecision(allowed=True, reason="file read permitted")
    return PolicyDecision(
        allowed=False,
        reason=f"file path '{file_path}' not in allowed read paths",
        violations=[f"read path '{file_path}' not permitted"],
    )


def _evaluate_write_file(request: PolicyRequest) -> PolicyDecision:
    import fnmatch
    file_path = request.resource.file_path
    if file_path is None:
        return PolicyDecision(allowed=False, reason="file_path required for write_file")
    allowed_paths = request.principal.role_bundle.operation.filesystem_write
    for pattern in allowed_paths:
        if fnmatch.fnmatch(file_path, pattern):
            return PolicyDecision(allowed=True, reason="file write permitted")
    return PolicyDecision(
        allowed=False,
        reason=f"file path '{file_path}' not in allowed write paths",
        violations=[f"write path '{file_path}' not permitted"],
    )


def _evaluate_exec_process(request: PolicyRequest) -> PolicyDecision:
    process_path = request.resource.process_path
    if process_path is None:
        return PolicyDecision(allowed=False, reason="process_path required for exec_process")
    allowed = request.principal.role_bundle.operation.process_exec
    if process_path not in allowed:
        return PolicyDecision(
            allowed=False,
            reason=f"process '{process_path}' not permitted",
            violations=[f"process '{process_path}' not permitted"],
        )
    return PolicyDecision(allowed=True, reason="process execution permitted")
