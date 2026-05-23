import pytest
import uuid
from mams_core.schemas.model import LLMMessage, LLMRequest, MessageRole
from mams_core.idempotency import new_uuid7


@pytest.fixture
def sample_request() -> LLMRequest:
    return LLMRequest(
        agent_id=uuid.uuid4(),
        model="anthropic/claude-sonnet-4-6",
        messages=[LLMMessage(role=MessageRole.USER, content="Hello!")],
        max_tokens=100,
        operation_id=new_uuid7(),
    )
