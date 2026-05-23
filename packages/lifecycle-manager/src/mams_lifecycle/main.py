from contextlib import asynccontextmanager
from fastapi import FastAPI
from mams_lifecycle.routers.containers import router as containers_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="MAMS Lifecycle Manager", version="0.1.0", lifespan=lifespan)
app.include_router(containers_router, prefix="/v1")


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok"}
