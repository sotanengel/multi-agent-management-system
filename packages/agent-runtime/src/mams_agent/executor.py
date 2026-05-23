"""Task execution loop for the agent runtime."""
from __future__ import annotations

import json
import logging
from typing import Any

from mams_core.schemas.model import LLMMessage, MessageRole
from mams_agent.clients.model_gw import complete
from mams_agent.settings import settings

logger = logging.getLogger(__name__)


class TaskExecutor:
    """Executes a single task assigned to this agent."""

    def __init__(self, agent_id: str, instruction: str, context: dict[str, Any]) -> None:
        self.agent_id = agent_id
        self.instruction = instruction
        self.context = context
        self.step_count = 0

    async def run(self) -> str:
        """Execute the task and return the result."""
        messages: list[LLMMessage] = [
            LLMMessage(
                role=MessageRole.SYSTEM,
                content=(
                    f"You are agent {self.agent_id}. "
                    "Complete the assigned task and respond with your result. "
                    "Be concise and focused."
                ),
            ),
            LLMMessage(
                role=MessageRole.USER,
                content=self._build_user_message(),
            ),
        ]

        result = ""
        while self.step_count < settings.max_steps_per_task:
            self.step_count += 1
            try:
                response = await complete(messages)
                result = response.content
                logger.info("Step %d complete: %d chars", self.step_count, len(result))
                # For MVP: single-step execution (no tool use loop)
                break
            except Exception as e:
                logger.error("Step %d failed: %s", self.step_count, e)
                result = f"Error: {e}"
                break

        return result

    def _build_user_message(self) -> str:
        msg = f"Task: {self.instruction}"
        if self.context:
            msg += f"\n\nContext: {json.dumps(self.context, indent=2)}"
        return msg
