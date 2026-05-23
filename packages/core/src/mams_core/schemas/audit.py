"""Audit log schemas."""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AuditEventType(str, Enum):
    AGENT_CREATED = "agent.created"
    AGENT_TERMINATED = "agent.terminated"
    TASK_SUBMITTED = "task.submitted"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    MODEL_CALLED = "model.called"
    CHILD_SPAWNED = "agent.child_spawned"
    POLICY_EVALUATED = "policy.evaluated"
    TOOL_CALLED = "tool.called"


class AuditEntry(BaseModel):
    """A single tamper-evident audit log entry."""
    entry_id: uuid.UUID
    agent_id: uuid.UUID
    sequence_num: int = Field(..., ge=0, description="Monotonically increasing per agent")
    event_type: AuditEventType
    payload: dict[str, Any] = Field(default_factory=dict)
    prev_hash: str = Field(description="SHA-256 hex of previous entry ('' for first entry)")
    entry_hash: str = Field(description="SHA-256 hex of this entry")
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditEntryCreate(BaseModel):
    """Request to create an audit entry (hash computed server-side)."""
    agent_id: uuid.UUID
    event_type: AuditEventType
    payload: dict[str, Any] = Field(default_factory=dict)
