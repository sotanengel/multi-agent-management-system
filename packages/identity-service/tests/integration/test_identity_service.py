import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from mams_core.schemas.agent import (
    AgentStatus,
    ComputationRole,
    DelegationPolicy,
    OperationRole,
    RoleBundle,
)
from mams_identity.main import app
from mams_identity.models import AgentRecord


@pytest.fixture
def sample_role_bundle() -> RoleBundle:
    return RoleBundle(
        name="test-bundle",
        computation=ComputationRole(primary_model="anthropic/claude-opus-4-7"),
        operation=OperationRole(),
        delegation=DelegationPolicy(),
    )


@pytest.fixture
def sample_agent_id() -> uuid.UUID:
    return uuid.UUID("12345678-1234-5678-1234-567812345678")


@pytest.fixture
def sample_agent_record(
    sample_agent_id: uuid.UUID, sample_role_bundle: RoleBundle
) -> AgentRecord:
    record = AgentRecord(
        agent_id=sample_agent_id,
        name="test-agent",
        parent_agent_id=None,
        role_bundle_json=sample_role_bundle.model_dump(),
        status=AgentStatus.PENDING.value,
        depth=0,
    )
    record.created_at = datetime.now(timezone.utc)
    record.updated_at = datetime.now(timezone.utc)
    return record


@pytest.mark.asyncio
async def test_healthz() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_register_agent(
    sample_agent_id: uuid.UUID,
    sample_role_bundle: RoleBundle,
    sample_agent_record: AgentRecord,
) -> None:
    mock_session = AsyncMock()
    mock_session.get = AsyncMock(return_value=None)
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock(side_effect=lambda r: r)

    # Pre-set timestamps on the record to simulate DB assignment
    sample_agent_record.created_at = datetime.now(timezone.utc)
    sample_agent_record.updated_at = datetime.now(timezone.utc)

    async def mock_get_session():  # type: ignore[return]
        yield mock_session

    with patch("mams_identity.routers.agents.get_db", mock_get_session):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/v1/agents",
                json={
                    "agent_id": str(sample_agent_id),
                    "name": "test-agent",
                    "parent_agent_id": None,
                    "role_bundle": sample_role_bundle.model_dump(),
                    "depth": 0,
                },
            )

    assert response.status_code == 201
    data = response.json()
    assert data["agent_id"] == str(sample_agent_id)
    assert data["name"] == "test-agent"
    assert data["status"] == AgentStatus.PENDING.value


@pytest.mark.asyncio
async def test_get_agent_not_found(sample_agent_id: uuid.UUID) -> None:
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    async def mock_get_session():  # type: ignore[return]
        yield mock_session

    with patch("mams_identity.routers.agents.get_db", mock_get_session):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/v1/agents/{sample_agent_id}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_agent(
    sample_agent_id: uuid.UUID, sample_agent_record: AgentRecord
) -> None:
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_agent_record
    mock_session.execute = AsyncMock(return_value=mock_result)

    async def mock_get_session():  # type: ignore[return]
        yield mock_session

    with patch("mams_identity.routers.agents.get_db", mock_get_session):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/v1/agents/{sample_agent_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["agent_id"] == str(sample_agent_id)
    assert data["name"] == "test-agent"


@pytest.mark.asyncio
async def test_issue_token(
    sample_agent_id: uuid.UUID, sample_agent_record: AgentRecord
) -> None:
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_agent_record
    mock_session.execute = AsyncMock(return_value=mock_result)

    async def mock_get_session():  # type: ignore[return]
        yield mock_session

    with patch("mams_identity.routers.tokens.get_db", mock_get_session):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/v1/tokens",
                json={"agent_id": str(sample_agent_id)},
            )

    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0


@pytest.mark.asyncio
async def test_verify_token(sample_agent_id: uuid.UUID) -> None:
    from mams_identity.jwt import create_token

    token = create_token(sample_agent_id, "test-bundle")

    mock_session = AsyncMock()
    mock_session.get = AsyncMock(return_value=None)

    async def mock_get_session():  # type: ignore[return]
        yield mock_session

    with patch("mams_identity.routers.tokens.get_db", mock_get_session):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/v1/tokens/verify", json={"token": token})

    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["agent_id"] == str(sample_agent_id)
    assert data["role"] == "test-bundle"


@pytest.mark.asyncio
async def test_verify_invalid_token() -> None:
    mock_session = AsyncMock()

    async def mock_get_session():  # type: ignore[return]
        yield mock_session

    with patch("mams_identity.routers.tokens.get_db", mock_get_session):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/v1/tokens/verify", json={"token": "not.a.valid.jwt"}
            )

    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert data["agent_id"] is None
    assert data["role"] is None


@pytest.mark.asyncio
async def test_revoke_token(sample_agent_id: uuid.UUID) -> None:
    from mams_identity.jwt import create_token

    token = create_token(sample_agent_id, "test-bundle")

    mock_session = AsyncMock()
    mock_session.get = AsyncMock(return_value=None)
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()

    async def mock_get_session():  # type: ignore[return]
        yield mock_session

    with patch("mams_identity.routers.tokens.get_db", mock_get_session):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/v1/tokens/revoke", json={"token": token})

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_agent(
    sample_agent_id: uuid.UUID, sample_agent_record: AgentRecord
) -> None:
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_agent_record
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock(side_effect=lambda r: r)

    async def mock_get_session():  # type: ignore[return]
        yield mock_session

    with patch("mams_identity.routers.agents.get_db", mock_get_session):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.delete(f"/v1/agents/{sample_agent_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == AgentStatus.TERMINATED.value
