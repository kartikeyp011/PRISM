"""Pydantic schema unit tests."""

import pytest
from pydantic import ValidationError

from app.models.schemas import IngestEventItem, IngestEventsRequest, validate_event_type


def test_validate_event_type_accepts_contract_values():
    assert validate_event_type("sensor_reading") is True
    assert validate_event_type("permit_update") is True
    assert validate_event_type("worker_location") is True
    assert validate_event_type("invalid") is False


def test_ingest_event_item_requires_fields():
    item = IngestEventItem(
        event_id="evt-1",
        event_type="sensor_reading",
        timestamp="2026-07-02T10:00:00Z",
        zone_id="22222222-2222-2222-2222-222222222222",
        payload={"sensor_id": "33333333-3333-3333-3333-333333333333", "value": 10.0},
    )
    assert item.event_id == "evt-1"


def test_ingest_events_request_requires_events_list():
    with pytest.raises(ValidationError):
        IngestEventsRequest.model_validate({})
