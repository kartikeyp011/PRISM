"""Simulator scenario file tests."""

import json
from pathlib import Path

SCENARIO_PATH = Path(__file__).resolve().parents[3] / "simulator" / "scenarios" / "compound_risk_demo.json"


def test_compound_risk_demo_has_required_batches():
    scenario = json.loads(SCENARIO_PATH.read_text(encoding="utf-8"))
    assert scenario["name"] == "compound_risk_demo"
    assert len(scenario["batches"]) >= 3

    event_types = set()
    for batch in scenario["batches"]:
        for event in batch["events"]:
            event_types.add(event["event_type"])

    assert "sensor_reading" in event_types
    assert "permit_update" in event_types
    assert "worker_location" in event_types
