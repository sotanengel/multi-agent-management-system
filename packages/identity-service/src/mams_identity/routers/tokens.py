import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mams_identity.dependencies import get_db
from mams_identity.jwt import create_token, decode_token
from mams_identity.models import AgentRecord, TokenBlocklist
from mams_identity.settings import settings

router = APIRouter(tags=["tokens"])


class TokenRequest(BaseModel):
    agent_id: uuid.UUID


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


class RevokeRequest(BaseModel):
    token: str


class VerifyRequest(BaseModel):
    token: str


class VerifyResponse(BaseModel):
    valid: bool
    agent_id: str | None = None
    role: str | None = None


@router.post("/tokens", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def issue_token(
    request: TokenRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Issue a JWT for an agent."""
    result = await db.execute(
        select(AgentRecord).where(AgentRecord.agent_id == request.agent_id)
    )
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {request.agent_id} not found",
        )

    role_bundle_name: str = record.role_bundle_json.get("name", "unknown")
    access_token = create_token(record.agent_id, role_bundle_name)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.jwt_expire_minutes * 60,
    )


@router.post("/tokens/revoke", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_token(
    request: RevokeRequest,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Add a token's JTI to the blocklist."""
    try:
        payload = decode_token(request.token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    jti: str = payload.get("jti", "")
    if not jti:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token does not contain a JTI claim",
        )

    exp_timestamp = payload.get("exp")
    if exp_timestamp is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token does not contain an exp claim",
        )
    expires_at = datetime.fromtimestamp(exp_timestamp, tz=UTC)

    existing = await db.get(TokenBlocklist, jti)
    if existing is None:
        blocklist_entry = TokenBlocklist(jti=jti, expires_at=expires_at)
        db.add(blocklist_entry)
        await db.commit()


@router.post("/tokens/verify", response_model=VerifyResponse)
async def verify_token(
    request: VerifyRequest,
    db: AsyncSession = Depends(get_db),
) -> VerifyResponse:
    """Verify a token is valid and not revoked."""
    try:
        payload = decode_token(request.token)
    except ValueError:
        return VerifyResponse(valid=False, agent_id=None, role=None)

    jti: str = payload.get("jti", "")
    if jti:
        blocklist_entry = await db.get(TokenBlocklist, jti)
        if blocklist_entry is not None:
            return VerifyResponse(valid=False, agent_id=None, role=None)

    agent_id: str | None = payload.get("sub")
    role: str | None = payload.get("role")

    return VerifyResponse(valid=True, agent_id=agent_id, role=role)
