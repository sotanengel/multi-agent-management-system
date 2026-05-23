"""Role bundle subset validation.

Security invariant: a child agent's permissions must never exceed its parent's.
All checks are pure functions with no side effects.
"""
from __future__ import annotations

import fnmatch

from mams_core.schemas.agent import (
    ComputationRole,
    DelegationPolicy,
    MCPToolRole,
    OperationRole,
    RoleBundle,
)


def _is_path_subset(child_paths: list[str], parent_paths: list[str]) -> list[str]:
    """Return list of child paths NOT covered by any parent path glob.

    A child path is "covered" if at least one parent glob matches it OR
    if the child glob is a more-specific version of a parent glob.
    We use both directions: child path matches a parent glob, or a parent
    path matches/contains the child path pattern.
    """
    violations = []
    for child_path in child_paths:
        covered = False
        for parent_path in parent_paths:
            # Exact match
            if child_path == parent_path:
                covered = True
                break
            # Child is more specific: parent glob covers child literal
            if fnmatch.fnmatch(child_path, parent_path):
                covered = True
                break
            # Parent glob covers child glob (parent is same or broader)
            # e.g. parent="/workspace/**" covers child="/workspace/data/**"
            if fnmatch.fnmatch(child_path, parent_path):
                covered = True
                break
            # Check if child glob is a prefix subset of parent glob
            # Normalize: strip trailing ** and compare prefix
            parent_base = parent_path.rstrip("*").rstrip("/")
            child_base = child_path.rstrip("*").rstrip("/")
            if child_base.startswith(parent_base):
                covered = True
                break
        if not covered:
            violations.append(f"path '{child_path}' not permitted by parent")
    return violations


def _is_list_subset(child_items: list[str], parent_items: list[str], label: str) -> list[str]:
    """Return violations where child items are not in parent items (exact match)."""
    parent_set = set(parent_items)
    return [
        f"{label} '{item}' not permitted by parent"
        for item in child_items
        if item not in parent_set
    ]


def check_operation_role(child: OperationRole, parent: OperationRole) -> list[str]:
    """Validate child OperationRole is a subset of parent OperationRole."""
    violations: list[str] = []
    violations.extend(_is_path_subset(child.filesystem_read, parent.filesystem_read))
    violations.extend(_is_path_subset(child.filesystem_write, parent.filesystem_write))
    violations.extend(_is_list_subset(child.network_egress, parent.network_egress, "network_egress"))
    violations.extend(_is_list_subset(child.process_exec, parent.process_exec, "process_exec"))
    return violations


def check_computation_role(child: ComputationRole, parent: ComputationRole) -> list[str]:
    """Validate child ComputationRole is within parent limits."""
    violations: list[str] = []

    # Model must be in parent's allowed set (primary + fallbacks)
    parent_models = {parent.primary_model} | set(parent.fallback_models)
    child_models = {child.primary_model} | set(child.fallback_models)
    for model in child_models:
        if model not in parent_models:
            violations.append(f"model '{model}' not permitted by parent")

    # Numeric limits: child must be <= parent
    cl = child.limits
    pl = parent.limits
    if cl.max_tokens_per_call > pl.max_tokens_per_call:
        violations.append(
            f"max_tokens_per_call {cl.max_tokens_per_call} exceeds parent limit {pl.max_tokens_per_call}"
        )
    if cl.max_steps_per_task > pl.max_steps_per_task:
        violations.append(
            f"max_steps_per_task {cl.max_steps_per_task} exceeds parent limit {pl.max_steps_per_task}"
        )
    if cl.monthly_budget_usd > pl.monthly_budget_usd:
        violations.append(
            f"monthly_budget_usd {cl.monthly_budget_usd} exceeds parent limit {pl.monthly_budget_usd}"
        )
    return violations


def check_mcp_tool_role(child: MCPToolRole, parent: MCPToolRole) -> list[str]:
    """Validate child MCPToolRole is a subset of parent MCPToolRole."""
    violations: list[str] = []
    parent_tools: dict[str, set[str]] = {
        t.name: set(t.modes) for t in parent.allowed
    }
    for child_tool in child.allowed:
        if child_tool.name not in parent_tools:
            violations.append(f"MCP tool '{child_tool.name}' not permitted by parent")
            continue
        # Check modes subset
        parent_modes = parent_tools[child_tool.name]
        for mode in child_tool.modes:
            if mode not in parent_modes:
                violations.append(
                    f"MCP tool '{child_tool.name}' mode '{mode}' not permitted by parent"
                )
    return violations


def check_delegation_policy(child: DelegationPolicy, parent: DelegationPolicy) -> list[str]:
    """Validate child delegation policy doesn't escalate depth."""
    violations: list[str] = []

    if child.can_spawn_children and not parent.can_spawn_children:
        violations.append("child cannot have can_spawn_children=True when parent has False")

    if child.max_children > parent.max_children:
        violations.append(
            f"max_children {child.max_children} exceeds parent limit {parent.max_children}"
        )

    # Depth amplification prevention: child depth must be strictly less than parent
    if child.max_recursion_depth >= parent.max_recursion_depth:
        violations.append(
            f"max_recursion_depth {child.max_recursion_depth} must be less than "
            f"parent's {parent.max_recursion_depth} (depth-amplification prevention)"
        )
    return violations


def check_role_bundle_subset(child: RoleBundle, parent: RoleBundle) -> list[str]:
    """Check that child RoleBundle is a subset of parent RoleBundle.

    Returns a list of violation messages. Empty list means the child is valid.
    """
    violations: list[str] = []
    violations.extend(check_operation_role(child.operation, parent.operation))
    violations.extend(check_computation_role(child.computation, parent.computation))
    violations.extend(check_mcp_tool_role(child.mcp_tools, parent.mcp_tools))
    violations.extend(check_delegation_policy(child.delegation, parent.delegation))
    return violations
