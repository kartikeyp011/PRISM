"""Pytest configuration and fixtures."""

from __future__ import annotations

import os

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

INTEGRATION = os.environ.get("INTEGRATION_TESTS") == "1"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def integration_client(client):
    if not INTEGRATION:
        pytest.skip("Set INTEGRATION_TESTS=1 with postgres and redis running")
    from app.db.init_db import init_db

    try:
        await init_db()
    except Exception as exc:
        pytest.skip(f"Database not available: {exc}")
    yield client
