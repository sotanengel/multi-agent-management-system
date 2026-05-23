from __future__ import annotations

import json
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
import redis.asyncio as aioredis
from mams_gateway.settings import settings

logger = logging.getLogger(__name__)

_redis: aioredis.Redis | None = None


def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis


class IdempotencyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        op_id = request.headers.get("X-Operation-Id")
        if not op_id or request.method not in ("POST", "PATCH", "DELETE"):
            return await call_next(request)

        key = f"op:{op_id}"
        try:
            cached = await get_redis().get(key)
            if cached:
                data = json.loads(cached)
                return JSONResponse(data["body"], status_code=data["status_code"])
        except Exception:
            logger.warning("Redis idempotency check failed", exc_info=True)

        response = await call_next(request)

        if 200 <= response.status_code < 300:
            try:
                body_bytes = b""
                async for chunk in response.body_iterator:
                    body_bytes += chunk
                body = json.loads(body_bytes)
                await get_redis().setex(
                    key,
                    settings.idempotency_ttl_seconds,
                    json.dumps({"status_code": response.status_code, "body": body}),
                )
                return JSONResponse(body, status_code=response.status_code,
                                    headers=dict(response.headers))
            except Exception:
                logger.warning("Failed to cache idempotency response", exc_info=True)

        return response
