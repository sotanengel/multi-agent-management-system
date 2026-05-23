import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from mams_core.schemas.agent import ComputationRole, DelegationPolicy, OperationRole, RoleBundle
from mams_core.schemas.policy import PolicyAction, PolicyPrincipal, PolicyRequest, PolicyResource
from mams_policy.main import app


@pytest.mark.asyncio
async def test_healthz():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_evaluate_call_model_allowed():
    principal = PolicyPrincipal(
        agent_id=uuid.uuid4(),
        role_bundle=RoleBundle(
            name="test",
            computation=ComputationRole(primary_model="anthropic/claude-opus-4-7"),
            delegation=DelegationPolicy(),
        ),
    )
    request = PolicyRequest(
        principal=principal,
        action=PolicyAction.CALL_MODEL,
        resource=PolicyResource(model_id="anthropic/claude-opus-4-7"),
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/v1/evaluate", json=request.model_dump(mode="json"))
    assert response.status_code == 200
    data = response.json()
    assert data["allowed"] is True


@pytest.mark.asyncio
async def test_evaluate_call_model_denied():
    principal = PolicyPrincipal(
        agent_id=uuid.uuid4(),
        role_bundle=RoleBundle(
            name="test",
            computation=ComputationRole(primary_model="anthropic/claude-opus-4-7"),
            delegation=DelegationPolicy(),
        ),
    )
    request = PolicyRequest(
        principal=principal,
        action=PolicyAction.CALL_MODEL,
        resource=PolicyResource(model_id="openai/gpt-4"),
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/v1/evaluate", json=request.model_dump(mode="json"))
    assert response.status_code == 200
    data = response.json()
    assert data["allowed"] is False
