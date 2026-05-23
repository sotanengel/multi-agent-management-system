import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch

from mams_gateway.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"
