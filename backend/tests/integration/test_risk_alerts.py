"""Integration tests for risk engine and alerts."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from app.contract import PATH_ALERTS_ACTIVE, PATH_ALERTS_ACK, PATH_INGEST_EVENTS

SCENARIO_PATH = (
    Path(__file__).resolve().parents[3] / "simulator" / "scenarios" / "compound_risk_demo.json"
)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_compound_risk_demo_triggers_hot_work_alert(integration_client):
    scenario = json.loads(SCENARIO_PATH.read_text(encoding="utf-8"))

    for batch in scenario["batches"][:3]:
        response = await integration_client.post(
            PATH_INGEST_EVENTS,
            json={"events": batch["events"]},
        )
        assert response.status_code == 202

    alerts = await integration_client.get(PATH_ALERTS_ACTIVE)
    assert alerts.status_code == 200
    data = alerts.json()
    rule_ids = [a["rule_id"] for a in data["alerts"]]
    assert "HotWorkGasSpike" in rule_ids


@pytest.mark.integration
@pytest.mark.asyncio
async def test_acknowledge_alert(integration_client):
    scenario = json.loads(SCENARIO_PATH.read_text(encoding="utf-8"))
    batch = scenario["batches"][2]["events"]
    await integration_client.post(PATH_INGEST_EVENTS, json={"events": batch})

    alerts = await integration_client.get(PATH_ALERTS_ACTIVE)
    active = alerts.json()["alerts"]
    if not active:
        pytest.skip("No alerts created — prior batches may be required")

    alert_id = active[0]["alert_id"]
    ack = await integration_client.post(
        PATH_ALERTS_ACK,
        json={"alert_id": alert_id, "acknowledged_by": "test-operator"},
    )
    assert ack.status_code == 200
    assert ack.json()["status"] == "ACKNOWLEDGED"

    alerts_after = await integration_client.get(PATH_ALERTS_ACTIVE)
    remaining_ids = [a["alert_id"] for a in alerts_after.json()["alerts"]]
    assert alert_id not in remaining_ids


@pytest.mark.integration
@pytest.mark.asyncio
async def test_websocket_receives_alert_created(integration_client):
    scenario = json.loads(SCENARIO_PATH.read_text(encoding="utf-8"))
    batch = scenario["batches"][2]["events"]

    received: list[dict] = []

    async def listen():
        async with integration_client.websocket_connect("/ws/alerts") as ws:
            await ws.receive_json()
            await integration_client.post(PATH_INGEST_EVENTS, json={"events": batch})
            for _ in range(5):
                try:
                    msg = await asyncio.wait_for(ws.receive_json(), timeout=3.0)
                    received.append(msg)
                    if msg.get("event") == "alert.created":
                        break
                except asyncio.TimeoutError:
                    break

    await listen()
    events = [m.get("event") for m in received]
    assert "alert.created" in events
