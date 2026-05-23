from contextlib import asynccontextmanager
from fastapi import FastAPI
from mams_model_gw.routers.completions import router as completions_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="MAMS Model Gateway", version="0.1.0", lifespan=lifespan)
app.include_router(completions_router, prefix="/v1")


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok"}
