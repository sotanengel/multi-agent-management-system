"""Ollama local LLM provider."""
from __future__ import annotations

import httpx

from mams_core.errors import ModelProviderError
from mams_core.schemas.model import LLMMessage, TokenUsage
from mams_model_gw.providers.base import LLMProvider
from mams_model_gw.settings import settings


class OllamaProvider(LLMProvider):
    @property
    def provider_name(self) -> str:
        return "ollama"

    def supports_model(self, model_id: str) -> bool:
        return model_id.startswith("ollama/")

    async def complete(
        self,
        model_id: str,
        messages: list[LLMMessage],
        max_tokens: int,
    ) -> tuple[str, TokenUsage]:
        model_name = model_id.removeprefix("ollama/")
        api_messages = [
            {"role": msg.role.value, "content": msg.content}
            for msg in messages
        ]

        try:
            async with httpx.AsyncClient(
                base_url=settings.ollama_base_url,
                timeout=settings.request_timeout_seconds,
            ) as client:
                resp = await client.post("/api/chat", json={
                    "model": model_name,
                    "messages": api_messages,
                    "stream": False,
                    "options": {"num_predict": max_tokens},
                })
                resp.raise_for_status()
                data = resp.json()

            content = data.get("message", {}).get("content", "")
            eval_count = data.get("eval_count", 0)
            prompt_eval_count = data.get("prompt_eval_count", 0)

            usage = TokenUsage(
                input_tokens=prompt_eval_count,
                output_tokens=eval_count,
                cost_usd=0.0,  # Local model - no cost
            )
            return content, usage
        except httpx.HTTPError as e:
            raise ModelProviderError("ollama", str(e)) from e
