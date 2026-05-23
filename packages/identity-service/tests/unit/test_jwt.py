import uuid

import pytest

from mams_identity.jwt import create_token, decode_token


def test_create_token_returns_string() -> None:
    agent_id = uuid.uuid4()
    token = create_token(agent_id, "test-bundle")
    assert isinstance(token, str)
    assert len(token) > 0


def test_decode_token_roundtrip() -> None:
    agent_id = uuid.uuid4()
    token = create_token(agent_id, "test-bundle")
    payload = decode_token(token)
    assert payload["sub"] == str(agent_id)
    assert payload["role"] == "test-bundle"
    assert "jti" in payload
    assert "exp" in payload


def test_decode_invalid_token() -> None:
    with pytest.raises(ValueError, match="Invalid token"):
        decode_token("not.a.valid.jwt")


def test_decode_tampered_token() -> None:
    agent_id = uuid.uuid4()
    token = create_token(agent_id, "test-bundle")
    # Tamper with the token
    parts = token.split(".")
    parts[1] = "tampered"
    with pytest.raises(ValueError):
        decode_token(".".join(parts))


def test_token_payload_has_required_fields() -> None:
    agent_id = uuid.uuid4()
    token = create_token(agent_id, "admin-bundle")
    payload = decode_token(token)
    assert "sub" in payload
    assert "role" in payload
    assert "jti" in payload
    assert "exp" in payload
    assert payload["role"] == "admin-bundle"
