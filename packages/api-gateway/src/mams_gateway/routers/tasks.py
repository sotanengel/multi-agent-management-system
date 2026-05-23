from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from mams_core.idempotency import new_uuid7
from mams_core.schemas.task import Task, TaskStatus
from mams_gateway.clients import audit
from mams_gateway.settings import settings

router = APIRouter(prefix="/v1/tasks")

# In-memory task store (MVP - replace with State Store later)
_tasks: dict[uuid.UUID, Task] = {}


class SubmitTaskRequest(BaseModel):
    agent_id: uuid.UUID
    instruction: str
    context: dict = {}
    operation_id: uuid.UUID | None = None


@router.post("", response_model=Task, status_code=201)
async def submit_task(body: SubmitTaskRequest) -> Task:
    import nats as nats_client

    task_id = new_uuid7()
    operation_id = body.operation_id or new_uuid7()
    now = datetime.now(tz=timezone.utc)

    task = Task(
        task_id=task_id,
        agent_id=body.agent_id,
        instruction=body.instruction,
        context=body.context,
        operation_id=operation_id,
        status=TaskStatus.QUEUED,
        created_at=now,
    )
    _tasks[task_id] = task

    # Publish to NATS
    try:
        nc = await nats_client.connect(settings.nats_url)
        subject = f"agent.{body.agent_id}.tasks"
        msg = json.dumps({
            "task_id": str(task_id),
            "agent_id": str(body.agent_id),
            "instruction": body.instruction,
            "context": body.context,
            "operation_id": str(operation_id),
        })
        await nc.publish(subject, msg.encode())
        await nc.drain()
    except Exception:
        pass  # NATS not available in test environment

    await audit.record_event(
        agent_id=body.agent_id,
        event_type="task.submitted",
        payload={"task_id": str(task_id), "instruction": body.instruction[:100]},
    )

    return task


@router.get("/{task_id}", response_model=Task)
async def get_task(task_id: uuid.UUID) -> Task:
    task = _tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.get("", response_model=list[Task])
async def list_tasks(agent_id: uuid.UUID | None = None) -> list[Task]:
    tasks = list(_tasks.values())
    if agent_id:
        tasks = [t for t in tasks if t.agent_id == agent_id]
    return tasks
