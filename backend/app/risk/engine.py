"""Compound risk rule evaluator."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.alerts.service import RuleHit, create_alert_from_hit, persist_assessment
from app.alerts.ws_manager import ws_manager
from app.contract import REDIS_TOPIC_RISK, THRESHOLDS
from app.db.models import Alert, Permit, Sensor, SensorReading, WorkerLocation, Zone
from app.services.redis_client import publish

logger = logging.getLogger(__name__)

LEL_HIGH = float(THRESHOLDS["lel_high"])
O2_LOW = float(THRESHOLDS["o2_low"])


@dataclass
class ZoneContext:
    zone_id: uuid.UUID
    zone_type: str
    active_permits: list[Permit]
    latest_readings: dict[str, float]
    worker_count: int
    workers_outside_zone: int


async def _load_zone_context(session: AsyncSession, zone_id: uuid.UUID) -> ZoneContext | None:
    zone = await session.get(Zone, zone_id)
    if zone is None:
        return None

    permits_result = await session.execute(
        select(Permit).where(Permit.zone_id == zone_id, Permit.status == "active")
    )
    active_permits = list(permits_result.scalars().all())

    readings: dict[str, float] = {}
    sensors_result = await session.execute(select(Sensor).where(Sensor.zone_id == zone_id))
    for sensor in sensors_result.scalars().all():
        latest = await session.execute(
            select(SensorReading.value)
            .where(SensorReading.sensor_id == sensor.id)
            .order_by(SensorReading.time.desc())
            .limit(1)
        )
        value = latest.scalar_one_or_none()
        if value is not None:
            readings[sensor.sensor_type] = value

    worker_count_result = await session.execute(
        select(func.count())
        .select_from(WorkerLocation)
        .where(WorkerLocation.zone_id == zone_id)
    )
    worker_count = worker_count_result.scalar() or 0

    outside_result = await session.execute(
        text(
            """
            SELECT COUNT(*)
            FROM worker_locations wl
            JOIN zones z ON z.id = wl.zone_id
            WHERE wl.zone_id = :zone_id
              AND wl.location IS NOT NULL
              AND z.polygon IS NOT NULL
              AND NOT ST_Contains(z.polygon, wl.location)
            """
        ),
        {"zone_id": str(zone_id)},
    )
    workers_outside = outside_result.scalar() or 0

    return ZoneContext(
        zone_id=zone_id,
        zone_type=zone.zone_type,
        active_permits=active_permits,
        latest_readings=readings,
        worker_count=worker_count,
        workers_outside_zone=workers_outside,
    )


def evaluate_hot_work_gas_spike(ctx: ZoneContext) -> RuleHit | None:
    has_hot_work = any(p.permit_type == "hot_work" for p in ctx.active_permits)
    lel = ctx.latest_readings.get("LEL")
    if has_hot_work and lel is not None and lel > LEL_HIGH:
        return RuleHit(
            rule_id="HotWorkGasSpike",
            severity="HIGH",
            risk_level="HIGH",
            message=f"LEL at {lel}% exceeds threshold during active hot-work permit",
            context={"lel": lel, "threshold": LEL_HIGH},
        )
    return None


def evaluate_confined_space_occupancy(ctx: ZoneContext) -> RuleHit | None:
    has_confined = any(p.permit_type == "confined_space" for p in ctx.active_permits)
    o2 = ctx.latest_readings.get("O2")
    if has_confined and ctx.worker_count > 0 and o2 is not None and o2 < O2_LOW:
        return RuleHit(
            rule_id="ConfinedSpaceOccupancy",
            severity="CRITICAL",
            risk_level="CRITICAL",
            message=f"O2 at {o2}% below minimum with workers in confined space",
            context={"o2": o2, "threshold": O2_LOW, "worker_count": ctx.worker_count},
        )
    return None


def evaluate_permit_zone_mismatch(ctx: ZoneContext) -> RuleHit | None:
    if not ctx.active_permits:
        return None
    if ctx.workers_outside_zone > 0:
        return RuleHit(
            rule_id="PermitZoneMismatch",
            severity="MEDIUM",
            risk_level="MEDIUM",
            message=f"{ctx.workers_outside_zone} worker(s) outside permitted zone boundary",
            context={"workers_outside": ctx.workers_outside_zone},
        )
    return None


RULE_EVALUATORS = [
    evaluate_hot_work_gas_spike,
    evaluate_confined_space_occupancy,
    evaluate_permit_zone_mismatch,
]


async def evaluate_zone(session: AsyncSession, zone_id: uuid.UUID) -> list[RuleHit]:
    ctx = await _load_zone_context(session, zone_id)
    if ctx is None:
        return []

    hits: list[RuleHit] = []
    for evaluator in RULE_EVALUATORS:
        hit = evaluator(ctx)
        if hit:
            hits.append(hit)

    if not hits:
        await persist_assessment(
            session,
            zone_id,
            rule_id="none",
            risk_level="LOW",
            context={"readings": ctx.latest_readings},
        )
        await publish(
            REDIS_TOPIC_RISK,
            {
                "event": "risk.changed",
                "zone_id": str(zone_id),
                "risk_level": "LOW",
            },
        )
        await ws_manager.broadcast(
            "risk.changed",
            {"zone_id": str(zone_id), "risk_level": "LOW"},
        )
    else:
        top = max(hits, key=lambda h: ["LOW", "MEDIUM", "HIGH", "CRITICAL"].index(h.risk_level))
        await publish(
            REDIS_TOPIC_RISK,
            {
                "event": "risk.changed",
                "zone_id": str(zone_id),
                "risk_level": top.risk_level,
                "rule_id": top.rule_id,
            },
        )
        await ws_manager.broadcast(
            "risk.changed",
            {
                "zone_id": str(zone_id),
                "risk_level": top.risk_level,
                "rule_id": top.rule_id,
            },
        )

    return hits


async def evaluate_zones(session: AsyncSession, zone_ids: list[str]) -> list[Alert]:
    created: list[Alert] = []
    seen: set[uuid.UUID] = set()
    for zone_id_str in zone_ids:
        zone_uuid = uuid.UUID(zone_id_str)
        if zone_uuid in seen:
            continue
        seen.add(zone_uuid)
        try:
            hits = await evaluate_zone(session, zone_uuid)
            for hit in hits:
                alert = await create_alert_from_hit(session, zone_uuid, hit)
                if alert:
                    created.append(alert)
        except Exception:
            logger.exception("Risk evaluation failed for zone %s", zone_id_str)
    return created
