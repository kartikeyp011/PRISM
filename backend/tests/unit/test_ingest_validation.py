"""Ingest endpoint validation tests."""

import pytest

from app.contract import PATH_INGEST_EVENTS


@pytest.mark.asyncio
async def test_rejects_invalid_event_type(client):
    response = await client.post(
        PATH_INGEST_EVENTS,
        json={
            "events": [
                {
                    "event_id": "bad-001",
                    "event_type": "unknown_type",
                    "timestamp": "2026-07-02T10:00:00Z",
                    "zone_id": "22222222-2222-2222-2222-222222222222",
                    "payload": {},
                }
            ]
        },
    )
    assert response.status_code == 400
    assert "Invalid event_type" in response.json()["detail"]
