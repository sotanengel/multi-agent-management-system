import pytest
from httpx import AsyncClient, ASGITransport
from jose import jwt
from datetime import UTC, datetime, timedelta
import uuid

from mams_gateway.main import app
from mams_gateway.settings import settings


def make_token(agent_id: uuid.UUID | None = None) -> str:
    if agent_id is None:
        agent_id = uuid.uuid4()
    payload = {
        "sub": str(agent_id),
        "role": "test-bundle",
        "jti": str(uuid.uuid4()),
        "exp": datetime.now(UTC) + timedelta(hours=1),
        "iat": datetime.now(UTC),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


@pytest.mark.asyncio
async def test_missing_token_returns_401():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/v1/agents")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_invalid_token_returns_401():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/v1/agents", headers={"Authorization": "Bearer invalid.jwt"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_healthz_no_auth_required():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/healthz")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_valid_token_passes():
    token = make_token()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/v1/agents", headers={"Authorization": f"Bearer {token}"})
    # Should get 200 (empty list), not 401
    assert response.status_code == 200
