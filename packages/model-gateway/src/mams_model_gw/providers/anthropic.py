"""Anthropic Claude provider."""
from __future__ import annotations

import anthropic

from mams_core.errors import ModelProviderError
from mams_core.schemas.model import LLMMessage, MessageRole, TokenUsage
from mams_model_gw.providers.base import LLMProvider
from mams_model_gw.settings import settings

# Pricing per 1M tokens (USD) - approximate, update as needed
PRICING: dict[str, tuple[float, float]] = {
    "claude-opus-4-7": (15.0, 75.0),
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-haiku-4-5-20251001": (0.25, 1.25),
}


def _cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    base = model.split("/")[-1]  # strip "anthropic/" prefix
    in_price, out_price = PRICING.get(base, (3.0, 15.0))
    return (input_tokens * in_price + output_tokens * out_price) / 1_000_000


class AnthropicProvider(LLMProvider):
    @property
    def provider_name(self) -> str:
        return "anthropic"

    def supports_model(self, model_id: str) -> bool:
        return model_id.startswith("anthropic/") or model_id.startswith("claude-")

    async def complete(
        self,
        model_id: str,
        messages: list[LLMMessage],
        max_tokens: int,
    ) -> tuple[str, TokenUsage]:
        if not settings.anthropic_api_key:
            raise ModelProviderError("anthropic", "ANTHROPIC_API_KEY not configured")

        api_key = settings.anthropic_api_key
        client = anthropic.AsyncAnthropic(api_key=api_key)

        # Extract system message if present
        system = ""
        api_messages = []
        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                system = msg.content
            else:
                api_messages.append({"role": msg.role.value, "content": msg.content})

        # Strip provider prefix from model name
        model_name = model_id.removeprefix("anthropic/")

        try:
            kwargs: dict = {
                "model": model_name,
                "messages": api_messages,
                "max_tokens": max_tokens,
            }
            if system:
                kwargs["system"] = system

            response = await client.messages.create(**kwargs)
            content = response.content[0].text if response.content else ""
            usage = TokenUsage(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                cost_usd=_cost_usd(model_id, response.usage.input_tokens, response.usage.output_tokens),
            )
            return content, usage
        except anthropic.APIError as e:
            raise ModelProviderError("anthropic", str(e)) from e
