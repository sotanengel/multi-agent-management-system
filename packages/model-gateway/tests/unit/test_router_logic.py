import uuid
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from mams_core.schemas.model import LLMMessage, LLMRequest, MessageRole, TokenUsage
from mams_core.idempotency import new_uuid7


def make_request(model: str = "anthropic/claude-opus-4-7") -> LLMRequest:
    return LLMRequest(
        agent_id=uuid.uuid4(),
        model=model,
        messages=[LLMMessage(role=MessageRole.USER, content="test")],
        max_tokens=100,
        operation_id=new_uuid7(),
    )


@pytest.mark.asyncio
async def test_complete_unknown_model():
    from mams_core.errors import ModelProviderError
    from mams_model_gw.router_logic import complete

    request = make_request(model="unknown/model-xyz")
    with pytest.raises(ModelProviderError):
        await complete(request)


@pytest.mark.asyncio
async def test_complete_provider_failure():
    from mams_core.errors import ModelProviderError
    from mams_model_gw.router_logic import complete

    request = make_request(model="anthropic/claude-opus-4-7")

    with patch("mams_model_gw.router_logic.AnthropicProvider") as MockProvider:
        mock_instance = MagicMock()
        mock_instance.supports_model.return_value = True
        mock_instance.complete = AsyncMock(side_effect=ModelProviderError("anthropic", "API error"))
        MockProvider.return_value = mock_instance

        # Since providers are module-level list, patch the list
        with patch("mams_model_gw.router_logic._providers", [mock_instance]):
            with pytest.raises(ModelProviderError):
                await complete(request)
