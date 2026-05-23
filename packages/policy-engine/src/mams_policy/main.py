from fastapi import FastAPI
from mams_policy.routers.evaluate import router as evaluate_router

app = FastAPI(title="MAMS Policy Engine", version="0.1.0")
app.include_router(evaluate_router, prefix="/v1")


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok"}
