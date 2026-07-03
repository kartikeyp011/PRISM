"""Unit tests for compound risk rules."""

import uuid
from types import SimpleNamespace

from app.risk.engine import (
    ZoneContext,
    evaluate_confined_space_occupancy,
    evaluate_hot_work_gas_spike,
    evaluate_permit_zone_mismatch,
)

ZONE_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")


def _permit(permit_type: str) -> SimpleNamespace:
    return SimpleNamespace(permit_type=permit_type, status="active")


def test_hot_work_gas_spike_fires_when_lel_high():
    ctx = ZoneContext(
        zone_id=ZONE_ID,
        zone_type="confined_space",
        active_permits=[_permit("hot_work")],
        latest_readings={"LEL": 42.0},
        worker_count=0,
        workers_outside_zone=0,
    )
    hit = evaluate_hot_work_gas_spike(ctx)
    assert hit is not None
    assert hit.rule_id == "HotWorkGasSpike"
    assert hit.risk_level == "HIGH"


def test_hot_work_gas_spike_silent_when_lel_safe():
    ctx = ZoneContext(
        zone_id=ZONE_ID,
        zone_type="confined_space",
        active_permits=[_permit("hot_work")],
        latest_readings={"LEL": 5.0},
        worker_count=0,
        workers_outside_zone=0,
    )
    assert evaluate_hot_work_gas_spike(ctx) is None


def test_hot_work_gas_spike_silent_without_permit():
    ctx = ZoneContext(
        zone_id=ZONE_ID,
        zone_type="confined_space",
        active_permits=[],
        latest_readings={"LEL": 42.0},
        worker_count=0,
        workers_outside_zone=0,
    )
    assert evaluate_hot_work_gas_spike(ctx) is None


def test_confined_space_occupancy_fires():
    ctx = ZoneContext(
        zone_id=ZONE_ID,
        zone_type="confined_space",
        active_permits=[_permit("confined_space")],
        latest_readings={"O2": 18.5},
        worker_count=1,
        workers_outside_zone=0,
    )
    hit = evaluate_confined_space_occupancy(ctx)
    assert hit is not None
    assert hit.rule_id == "ConfinedSpaceOccupancy"
    assert hit.risk_level == "CRITICAL"


def test_confined_space_occupancy_silent_when_o2_ok():
    ctx = ZoneContext(
        zone_id=ZONE_ID,
        zone_type="confined_space",
        active_permits=[_permit("confined_space")],
        latest_readings={"O2": 20.5},
        worker_count=1,
        workers_outside_zone=0,
    )
    assert evaluate_confined_space_occupancy(ctx) is None


def test_permit_zone_mismatch_fires():
    ctx = ZoneContext(
        zone_id=ZONE_ID,
        zone_type="confined_space",
        active_permits=[_permit("hot_work")],
        latest_readings={},
        worker_count=1,
        workers_outside_zone=2,
    )
    hit = evaluate_permit_zone_mismatch(ctx)
    assert hit is not None
    assert hit.rule_id == "PermitZoneMismatch"


def test_permit_zone_mismatch_silent_when_workers_inside():
    ctx = ZoneContext(
        zone_id=ZONE_ID,
        zone_type="confined_space",
        active_permits=[_permit("hot_work")],
        latest_readings={},
        worker_count=1,
        workers_outside_zone=0,
    )
    assert evaluate_permit_zone_mismatch(ctx) is None
