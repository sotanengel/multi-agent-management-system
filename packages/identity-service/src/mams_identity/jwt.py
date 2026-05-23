import uuid
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt

from mams_identity.settings import settings


def create_token(agent_id: uuid.UUID, role_bundle_name: str) -> str:
    jti = str(uuid.uuid4())
    expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {
        "sub": str(agent_id),
        "role": role_bundle_name,
        "jti": jti,
        "exp": expire,
        "iat": datetime.now(UTC),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as e:
        raise ValueError(f"Invalid token: {e}") from e
