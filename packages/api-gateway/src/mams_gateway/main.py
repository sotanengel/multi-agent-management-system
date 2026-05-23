from contextlib import asynccontextmanager
from fastapi import FastAPI
from mams_gateway.middleware.auth import JWTAuthMiddleware
from mams_gateway.middleware.idempotency import IdempotencyMiddleware
from mams_gateway.routers import agents, health, tasks


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="MAMS API Gateway", version="0.1.0", lifespan=lifespan)

app.add_middleware(IdempotencyMiddleware)
app.add_middleware(JWTAuthMiddleware)

app.include_router(health.router)
app.include_router(agents.router)
app.include_router(tasks.router)
