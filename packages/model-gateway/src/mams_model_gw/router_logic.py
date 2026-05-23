"""Provider selection and fallback logic."""
from __future__ import annotations

import logging

from mams_core.errors import ModelProviderError
from mams_core.idempotency import new_uuid7
from mams_core.schemas.model import LLMRequest, LLMResponse
from mams_model_gw.providers.anthropic import AnthropicProvider
from mams_model_gw.providers.base import LLMProvider
from mams_model_gw.providers.ollama import OllamaProvider

logger = logging.getLogger(__name__)

_providers: list[LLMProvider] = [AnthropicProvider(), OllamaProvider()]


def _get_provider(model_id: str) -> LLMProvider | None:
    for provider in _providers:
        if provider.supports_model(model_id):
            return provider
    return None


async def complete(request: LLMRequest) -> LLMResponse:
    """Route an LLM request to the appropriate provider with fallback support."""
    models_to_try = [request.model]
    # Note: fallback models would be extracted from the agent's role bundle
    # For now, only try the requested model

    last_error: Exception | None = None
    for model_id in models_to_try:
        provider = _get_provider(model_id)
        if provider is None:
            logger.warning("No provider found for model: %s", model_id)
            continue

        try:
            content, usage = await provider.complete(
                model_id=model_id,
                messages=request.messages,
                max_tokens=request.max_tokens,
            )
            return LLMResponse(
                completion_id=new_uuid7(),
                content=content,
                model_used=model_id,
                usage=usage,
            )
        except ModelProviderError as e:
            logger.warning("Provider %s failed for model %s: %s", provider.provider_name, model_id, e)
            last_error = e

    raise ModelProviderError(
        "router",
        f"All models failed. Last error: {last_error}",
    )
