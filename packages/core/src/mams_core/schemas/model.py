"""LLM request/response schemas."""
from __future__ import annotations

import uuid
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class LLMMessage(BaseModel):
    role: MessageRole
    content: str
    tool_call_id: str | None = None
    name: str | None = None


class LLMRequest(BaseModel):
    agent_id: uuid.UUID
    model: str = Field(..., description="Model ID e.g. 'anthropic/claude-opus-4-7'")
    messages: list[LLMMessage]
    max_tokens: int = Field(default=4096, ge=1)
    operation_id: uuid.UUID = Field(description="Idempotency key")
    extra: dict[str, Any] = Field(default_factory=dict, description="Provider-specific params")


class TokenUsage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0


class LLMResponse(BaseModel):
    completion_id: uuid.UUID
    content: str
    model_used: str = Field(..., description="Actual model used (may differ if fallback triggered)")
    usage: TokenUsage = Field(default_factory=TokenUsage)
    finish_reason: str = "stop"
