"""Task schemas."""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Task(BaseModel):
    """Represents a task assigned to an agent."""
    task_id: uuid.UUID
    agent_id: uuid.UUID
    instruction: str
    context: dict[str, Any] = Field(default_factory=dict)
    operation_id: uuid.UUID = Field(description="Idempotency key (UUIDv7)")
    status: TaskStatus = TaskStatus.QUEUED
    result: str | None = None
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
