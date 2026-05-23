from __future__ import annotations

import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from jose import JWTError, jwt
from mams_gateway.settings import settings

logger = logging.getLogger(__name__)

EXEMPT_PATHS = {"/healthz", "/readyz"}


class JWTAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)

        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return JSONResponse({"detail": "Missing Bearer token"}, status_code=401)

        token = auth.removeprefix("Bearer ")
        try:
            payload = jwt.decode(
                token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
            )
            request.state.agent_id = payload.get("sub")
            request.state.role = payload.get("role")
        except JWTError as e:
            logger.warning("Invalid JWT: %s", e)
            return JSONResponse({"detail": "Invalid or expired token"}, status_code=401)

        return await call_next(request)
