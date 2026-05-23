"""Agent and RoleBundle schemas."""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"
    FAILED = "failed"


class NetworkEgress(BaseModel):
    """Allowed outbound network destinations."""
    destinations: list[str] = Field(default_factory=list, description="CIDRs or FQDNs")


class OperationRole(BaseModel):
    """Defines allowed OS-level operations."""
    filesystem_read: list[str] = Field(default_factory=list, description="Allowed read paths (glob)")
    filesystem_write: list[str] = Field(default_factory=list, description="Allowed write paths (glob)")
    network_egress: list[str] = Field(default_factory=list, description="Allowed CIDRs/FQDNs")
    process_exec: list[str] = Field(default_factory=list, description="Allowed executables")


class ComputationLimits(BaseModel):
    """Resource limits for computation."""
    max_tokens_per_call: int = Field(default=4096, ge=1)
    max_steps_per_task: int = Field(default=20, ge=1)
    monthly_budget_usd: float = Field(default=10.0, ge=0)
    cpu_limit: str = Field(default="1.0", description="Docker CPU limit e.g. '1.0'")
    memory_limit: str = Field(default="512m", description="Docker memory limit e.g. '512m'")


class ComputationRole(BaseModel):
    """Defines allowed models and compute resources."""
    primary_model: str = Field(..., description="Model ID e.g. 'anthropic/claude-opus-4-7'")
    fallback_models: list[str] = Field(default_factory=list)
    limits: ComputationLimits = Field(default_factory=ComputationLimits)


class MCPToolEntry(BaseModel):
    """A single allowed MCP tool."""
    name: str
    modes: list[str] = Field(default_factory=lambda: ["read-only"])
    rate_limit: str | None = Field(default=None, description="e.g. '60/min'")


class MCPToolRole(BaseModel):
    """Defines allowed MCP tools."""
    allowed: list[MCPToolEntry] = Field(default_factory=list)


class DelegationPolicy(BaseModel):
    """Controls child agent spawning."""
    can_spawn_children: bool = False
    max_children: int = Field(default=0, ge=0)
    max_recursion_depth: int = Field(default=0, ge=0)
    child_must_be_subset_of_parent: bool = True


class RoleBundle(BaseModel):
    """Complete role definition for an agent."""
    name: str
    version: str = "1.0.0"
    operation: OperationRole = Field(default_factory=OperationRole)
    computation: ComputationRole
    mcp_tools: MCPToolRole = Field(default_factory=MCPToolRole)
    delegation: DelegationPolicy = Field(default_factory=DelegationPolicy)


class Agent(BaseModel):
    """Represents an agent instance."""
    agent_id: uuid.UUID
    name: str
    parent_agent_id: uuid.UUID | None = None
    role_bundle: RoleBundle
    status: AgentStatus = AgentStatus.PENDING
    container_id: str | None = None
    depth: int = Field(default=0, ge=0, description="Recursion depth from root")
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
