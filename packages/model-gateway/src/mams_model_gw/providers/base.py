"""Abstract LLM provider interface."""
from __future__ import annotations

from abc import ABC, abstractmethod

from mams_core.schemas.model import LLMMessage, TokenUsage


class LLMProvider(ABC):
    """Abstract base class for all LLM providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable provider name."""

    @abstractmethod
    def supports_model(self, model_id: str) -> bool:
        """Return True if this provider can handle the given model_id."""

    @abstractmethod
    async def complete(
        self,
        model_id: str,
        messages: list[LLMMessage],
        max_tokens: int,
    ) -> tuple[str, TokenUsage]:
        """Call the LLM and return (content, usage).

        Raises ModelProviderError on failure.
        """
