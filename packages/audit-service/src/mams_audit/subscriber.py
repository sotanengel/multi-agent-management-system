"""NATS JetStream subscriber for audit events."""
from __future__ import annotations

import json
import logging

import nats
from nats.js.api import StreamConfig

from mams_audit.settings import settings

logger = logging.getLogger(__name__)


async def create_stream_if_not_exists(js: nats.js.JetStreamContext) -> None:
    """Create NATS JetStream stream for audit events if it doesn't exist."""
    try:
        await js.find_stream(settings.nats_subject)
    except Exception:
        await js.add_stream(
            StreamConfig(
                name=settings.nats_stream_name,
                subjects=[settings.nats_subject],
                max_msgs=1_000_000,
            )
        )


async def start_subscriber(db_session_factory) -> nats.NATS:
    """Connect to NATS and start consuming audit events.

    Returns the NATS connection so the caller can close it on shutdown.
    """
    nc = await nats.connect(settings.nats_url)
    js = nc.jetstream()

    await create_stream_if_not_exists(js)

    async def message_handler(msg):
        try:
            from mams_core.schemas.audit import AuditEntryCreate
            from mams_audit.chain import append_entry

            data = json.loads(msg.data.decode())
            create = AuditEntryCreate(**data)
            async with db_session_factory() as session:
                await append_entry(session, create)
            await msg.ack()
        except Exception:
            logger.exception("Failed to process audit event")
            await msg.nak()

    await js.subscribe(
        settings.nats_subject,
        durable="audit-service",
        cb=message_handler,
    )
    logger.info("Audit subscriber started on %s", settings.nats_subject)
    return nc
