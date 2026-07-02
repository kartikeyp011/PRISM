"""Integration tests for ingestion — require postgres + redis."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.contract import PATH_INGEST_EVENTS, PATH_SENSORS_LATEST

SCENARIO_PATH = (
    Path(__file__).resolve().parents[3] / "simulator" / "scenarios" / "compound_risk_demo.json"
)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ingest_scenario_batch_persists(integration_client):
    scenario = json.loads(SCENARIO_PATH.read_text(encoding="utf-8"))
    first_batch = scenario["batches"][0]["events"]

    response = await integration_client.post(
        PATH_INGEST_EVENTS,
        json={"events": first_batch},
    )
    assert response.status_code == 202
    data = response.json()
    assert data["accepted"] == len(first_batch)
    assert data["status"] == "accepted"

    latest = await integration_client.get(PATH_SENSORS_LATEST)
    assert latest.status_code == 200
    summary = latest.json()
    assert summary["events_ingested"] >= len(first_batch)
    assert summary["count"] >= 1
    assert summary["last_event_at"] is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_duplicate_event_is_idempotent(integration_client):
    event = {
        "event_id": "idempotent-test-001",
        "event_type": "sensor_reading",
        "timestamp": "2026-07-02T11:00:00Z",
        "zone_id": "22222222-2222-2222-2222-222222222222",
        "payload": {
            "sensor_id": "33333333-3333-3333-3333-333333333333",
            "sensor_type": "LEL",
            "value": 7.5,
            "unit": "%",
        },
    }

    first = await integration_client.post(PATH_INGEST_EVENTS, json={"events": [event]})
    assert first.status_code == 202

    second = await integration_client.post(PATH_INGEST_EVENTS, json={"events": [event]})
    assert second.status_code == 200
    data = second.json()
    assert data["accepted"] == 0
    assert data["skipped"] == 1
    assert data["status"] == "duplicate"
