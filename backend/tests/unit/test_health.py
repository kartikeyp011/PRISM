"""Health endpoint tests."""

import pytest

from app.contract import PATH_HEALTH


@pytest.mark.asyncio
async def test_health_returns_200(client):
    response = await client.get(PATH_HEALTH)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "1.0.0"
    assert data["llm_mode"] in ("mock", "live")
