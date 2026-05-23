import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from mams_core.schemas.model import LLMMessage, MessageRole
from mams_model_gw.providers.anthropic import AnthropicProvider
from mams_model_gw.providers.ollama import OllamaProvider


def test_anthropic_supports_model():
    p = AnthropicProvider()
    assert p.supports_model("anthropic/claude-opus-4-7")
    assert p.supports_model("claude-sonnet-4-6")
    assert not p.supports_model("ollama/llama-3")
    assert not p.supports_model("openai/gpt-4")


def test_ollama_supports_model():
    p = OllamaProvider()
    assert p.supports_model("ollama/llama-3.1-70b")
    assert not p.supports_model("anthropic/claude-opus-4-7")


@pytest.mark.asyncio
async def test_anthropic_missing_api_key():
    from mams_core.errors import ModelProviderError
    from mams_model_gw import settings as settings_module

    p = AnthropicProvider()
    messages = [LLMMessage(role=MessageRole.USER, content="Hi")]

    # Temporarily clear the API key
    original = settings_module.settings.anthropic_api_key
    settings_module.settings.anthropic_api_key = ""

    try:
        with pytest.raises(ModelProviderError, match="ANTHROPIC_API_KEY"):
            await p.complete("anthropic/claude-opus-4-7", messages, 100)
    finally:
        settings_module.settings.anthropic_api_key = original


@pytest.mark.asyncio
async def test_ollama_http_error():
    import httpx
    from mams_core.errors import ModelProviderError

    p = OllamaProvider()
    messages = [LLMMessage(role=MessageRole.USER, content="Hi")]

    with patch("httpx.AsyncClient.post", side_effect=httpx.ConnectError("Connection refused")):
        with pytest.raises(ModelProviderError):
            await p.complete("ollama/llama-3", messages, 100)
