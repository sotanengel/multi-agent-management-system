"""Agent runtime entry point. Runs as a NATS subscriber inside a Docker container."""
from __future__ import annotations

import asyncio
import json
import logging
import signal

import nats

from mams_agent.executor import TaskExecutor
from mams_agent.settings import settings

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)


async def handle_task(msg) -> None:
    """Handle an incoming task message from NATS."""
    try:
        data = json.loads(msg.data.decode())
        task_id = data.get("task_id", "unknown")
        agent_id = data.get("agent_id", settings.agent_id)
        instruction = data.get("instruction", "")
        context = data.get("context", {})

        logger.info("Received task %s: %s", task_id, instruction[:80])

        executor = TaskExecutor(
            agent_id=agent_id,
            instruction=instruction,
            context=context,
        )
        result = await executor.run()
        logger.info("Task %s completed: %s chars", task_id, len(result))
        await msg.ack()
    except Exception:
        logger.exception("Failed to process task")
        await msg.nak()


async def run() -> None:
    if not settings.agent_id:
        logger.error("AGENT_ID environment variable not set")
        return

    nc = await nats.connect(settings.nats_url)
    js = nc.jetstream()

    subject = f"agent.{settings.agent_id}.tasks"
    logger.info("Agent %s listening on %s", settings.agent_id, subject)

    # Subscribe to agent-specific task subject
    try:
        await js.subscribe(subject, durable=f"agent-{settings.agent_id}", cb=handle_task)
    except Exception:
        # Fall back to core NATS if JetStream not available
        await nc.subscribe(subject, cb=handle_task)

    # Wait for shutdown signal
    stop_event = asyncio.Event()

    def on_signal():
        stop_event.set()

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, on_signal)

    await stop_event.wait()
    await nc.drain()
    logger.info("Agent %s shut down gracefully", settings.agent_id)


if __name__ == "__main__":
    asyncio.run(run())
