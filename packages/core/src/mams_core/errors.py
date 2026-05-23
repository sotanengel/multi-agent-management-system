"""Typed exception hierarchy for MAMS."""
from __future__ import annotations


class MAMSError(Exception):
    """Base exception for all MAMS errors."""


class PolicyViolationError(MAMSError):
    """Raised when a policy check fails."""

    def __init__(self, violations: list[str]) -> None:
        self.violations = violations
        super().__init__(f"Policy violations: {', '.join(violations)}")


class AgentNotFoundError(MAMSError):
    """Raised when an agent cannot be found."""


class TaskNotFoundError(MAMSError):
    """Raised when a task cannot be found."""


class IdempotencyConflictError(MAMSError):
    """Raised when an operation ID is reused with different parameters."""


class RoleBundleValidationError(MAMSError):
    """Raised when a RoleBundle is invalid."""


class ContainerError(MAMSError):
    """Raised when a container operation fails."""


class ModelProviderError(MAMSError):
    """Raised when an LLM provider call fails."""

    def __init__(self, provider: str, message: str) -> None:
        self.provider = provider
        super().__init__(f"[{provider}] {message}")
