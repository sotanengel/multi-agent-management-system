"""Policy evaluation schemas."""
from __future__ import annotations

import uuid
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from mams_core.schemas.agent import RoleBundle


class PolicyAction(str, Enum):
    SPAWN_CHILD = "spawn_child"
    CALL_MODEL = "call_model"
    CALL_TOOL = "call_tool"
    SUBMIT_TASK = "submit_task"
    READ_FILE = "read_file"
    WRITE_FILE = "write_file"
    EXEC_PROCESS = "exec_process"


class PolicyPrincipal(BaseModel):
    agent_id: uuid.UUID
    role_bundle: RoleBundle


class PolicyResource(BaseModel):
    """The resource being accessed. Fields are action-dependent."""
    child_role_bundle: RoleBundle | None = None
    model_id: str | None = None
    tool_name: str | None = None
    file_path: str | None = None
    process_path: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class PolicyRequest(BaseModel):
    principal: PolicyPrincipal
    action: PolicyAction
    resource: PolicyResource = Field(default_factory=PolicyResource)


class PolicyDecision(BaseModel):
    allowed: bool
    reason: str
    violations: list[str] = Field(default_factory=list)
