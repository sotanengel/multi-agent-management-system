"""Tests for core Pydantic schemas."""
import uuid
from datetime import datetime, timezone

from mams_core.schemas.agent import (
    Agent,
    AgentStatus,
    ComputationRole,
    DelegationPolicy,
    OperationRole,
    RoleBundle,
)
from mams_core.schemas.audit import AuditEntry, AuditEventType
from mams_core.schemas.model import LLMMessage, LLMRequest, LLMResponse, MessageRole, TokenUsage
from mams_core.schemas.policy import PolicyAction, PolicyDecision, PolicyRequest, PolicyResource
from mams_core.schemas.task import Task, TaskStatus


def test_role_bundle_defaults():
    rb = RoleBundle(
        name="minimal",
        computation=ComputationRole(primary_model="anthropic/claude-opus-4-7"),
    )
    assert rb.name == "minimal"
    assert rb.operation.filesystem_read == []
    assert rb.delegation.can_spawn_children is False


def test_agent_creation(base_agent: Agent):
    assert base_agent.status == AgentStatus.RUNNING
    assert base_agent.depth == 0
    assert base_agent.parent_agent_id is None


def test_task_schema():
    now = datetime.now(tz=timezone.utc)
    task = Task(
        task_id=uuid.uuid4(),
        agent_id=uuid.uuid4(),
        instruction="analyze data",
        operation_id=uuid.uuid4(),
        status=TaskStatus.QUEUED,
        created_at=now,
    )
    assert task.status == TaskStatus.QUEUED
    assert task.result is None


def test_policy_decision_allowed():
    decision = PolicyDecision(allowed=True, reason="all checks passed")
    assert decision.violations == []


def test_policy_decision_denied():
    decision = PolicyDecision(
        allowed=False,
        reason="role violation",
        violations=["filesystem_write path not in parent"],
    )
    assert len(decision.violations) == 1


def test_llm_request_response():
    req = LLMRequest(
        agent_id=uuid.uuid4(),
        model="anthropic/claude-opus-4-7",
        messages=[LLMMessage(role=MessageRole.USER, content="hello")],
        operation_id=uuid.uuid4(),
    )
    assert len(req.messages) == 1

    resp = LLMResponse(
        completion_id=uuid.uuid4(),
        content="world",
        model_used="anthropic/claude-opus-4-7",
        usage=TokenUsage(input_tokens=5, output_tokens=3, cost_usd=0.001),
    )
    assert resp.usage.input_tokens == 5


def test_audit_entry_schema():
    now = datetime.now(tz=timezone.utc)
    entry = AuditEntry(
        entry_id=uuid.uuid4(),
        agent_id=uuid.uuid4(),
        sequence_num=0,
        event_type=AuditEventType.AGENT_CREATED,
        payload={"name": "test"},
        prev_hash="",
        entry_hash="abc123",
        created_at=now,
    )
    assert entry.sequence_num == 0
    assert entry.prev_hash == ""
