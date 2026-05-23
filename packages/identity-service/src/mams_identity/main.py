from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI

from mams_identity.routers import agents, tokens


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    yield


app = FastAPI(title="MAMS Identity Service", version="0.1.0", lifespan=lifespan)
app.include_router(agents.router, prefix="/v1")
app.include_router(tokens.router, prefix="/v1")


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok"}
