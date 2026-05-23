import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from mams_audit.db import async_session_factory
from mams_audit.routers.audit import router as audit_router
from mams_audit.settings import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Only start NATS subscriber if URL is configured (skip in unit tests)
    nc = None
    try:
        from mams_audit.subscriber import start_subscriber
        nc = await start_subscriber(async_session_factory)
    except Exception:
        logger.warning("Could not connect to NATS - running without subscriber")
    yield
    if nc:
        await nc.drain()


app = FastAPI(title="MAMS Audit Service", version="0.1.0", lifespan=lifespan)
app.include_router(audit_router, prefix="/v1")


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok"}
