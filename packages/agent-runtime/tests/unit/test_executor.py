import pytest
from unittest.mock import AsyncMock, patch
from mams_agent.executor import TaskExecutor
from mams_core.schemas.model import LLMResponse, TokenUsage
from mams_core.idempotency import new_uuid7


@pytest.mark.asyncio
async def test_executor_single_step():
    mock_response = LLMResponse(
        completion_id=new_uuid7(),
        content="Analysis complete: found 3 anomalies",
        model_used="anthropic/claude-opus-4-7",
        usage=TokenUsage(input_tokens=10, output_tokens=8, cost_usd=0.001),
    )

    with patch("mams_agent.executor.complete", new=AsyncMock(return_value=mock_response)):
        executor = TaskExecutor(
            agent_id="test-agent-123",
            instruction="Analyze the data",
            context={"dataset": "sales_2024.csv"},
        )
        result = await executor.run()

    assert result == "Analysis complete: found 3 anomalies"
    assert executor.step_count == 1


@pytest.mark.asyncio
async def test_executor_handles_error():
    with patch("mams_agent.executor.complete", new=AsyncMock(side_effect=Exception("API error"))):
        executor = TaskExecutor(
            agent_id="test-agent-123",
            instruction="Do something",
            context={},
        )
        result = await executor.run()

    assert "Error" in result


def test_executor_build_user_message():
    executor = TaskExecutor(
        agent_id="test",
        instruction="summarize",
        context={"key": "value"},
    )
    msg = executor._build_user_message()
    assert "summarize" in msg
    assert "value" in msg


def test_executor_build_user_message_no_context():
    executor = TaskExecutor(agent_id="test", instruction="summarize", context={})
    msg = executor._build_user_message()
    assert "summarize" in msg
    assert "Context" not in msg
