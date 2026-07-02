"""Ingestion service — normalize and persist event batches."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.contract import REDIS_TOPIC_EVENTS_INGEST
from app.db.models import Permit, RawEvent, SensorReading, WorkerLocation
from app.models.schemas import IngestEventItem
from app.services.redis_client import publish

logger = logging.getLogger(__name__)


@dataclass
class IngestResult:
    accepted: int
    skipped: int
    event_ids: list[str]
    status: str


def _parse_timestamp(value: str) -> datetime:
    ts = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts


async def ingest_events(session: AsyncSession, events: list[IngestEventItem]) -> IngestResult:
    if not events:
        return IngestResult(accepted=0, skipped=0, event_ids=[], status="accepted")

    event_ids = [e.event_id for e in events]
    existing_result = await session.execute(
        select(RawEvent.event_id).where(RawEvent.event_id.in_(event_ids))
    )
    existing_ids = set(existing_result.scalars().all())

    new_events = [e for e in events if e.event_id not in existing_ids]
    skipped = len(events) - len(new_events)

    if not new_events:
        return IngestResult(
            accepted=0,
            skipped=skipped,
            event_ids=[],
            status="duplicate",
        )

    accepted_ids: list[str] = []
    zone_ids: set[str] = set()

    for event in new_events:
        zone_uuid = uuid.UUID(event.zone_id)
        zone_ids.add(event.zone_id)
        received_at = _parse_timestamp(event.timestamp)

        session.add(
            RawEvent(
                event_id=event.event_id,
                event_type=event.event_type,
                zone_id=zone_uuid,
                payload=event.payload,
                received_at=received_at,
            )
        )

        if event.event_type == "sensor_reading":
            _persist_sensor_reading(session, event, zone_uuid, received_at)
        elif event.event_type == "permit_update":
            await _persist_permit(session, event, zone_uuid, received_at)
        elif event.event_type == "worker_location":
            _persist_worker_location(session, event, zone_uuid, received_at)

        accepted_ids.append(event.event_id)

    await session.flush()

    await publish(
        REDIS_TOPIC_EVENTS_INGEST,
        {
            "event_ids": accepted_ids,
            "zone_ids": list(zone_ids),
            "count": len(accepted_ids),
        },
    )

    return IngestResult(
        accepted=len(accepted_ids),
        skipped=skipped,
        event_ids=accepted_ids,
        status="accepted",
    )


def _persist_sensor_reading(
    session: AsyncSession,
    event: IngestEventItem,
    zone_uuid: uuid.UUID,
    recorded_at: datetime,
) -> None:
    payload = event.payload
    sensor_id = uuid.UUID(str(payload["sensor_id"]))
    session.add(
        SensorReading(
            time=recorded_at,
            sensor_id=sensor_id,
            value=float(payload["value"]),
            quality=str(payload.get("quality", "good")),
        )
    )


async def _persist_permit(
    session: AsyncSession,
    event: IngestEventItem,
    zone_uuid: uuid.UUID,
    recorded_at: datetime,
) -> None:
    payload = event.payload
    external_id = str(payload["permit_id"])
    existing = await session.execute(
        select(Permit).where(Permit.external_id == external_id)
    )
    permit = existing.scalar_one_or_none()
    start_time = _parse_timestamp(str(payload.get("start_time", event.timestamp)))
    end_time_raw = payload.get("end_time")
    end_time = _parse_timestamp(str(end_time_raw)) if end_time_raw else None

    if permit:
        permit.status = str(payload["status"])
        permit.permit_type = str(payload["permit_type"])
        permit.start_time = start_time
        permit.end_time = end_time
    else:
        session.add(
            Permit(
                zone_id=zone_uuid,
                permit_type=str(payload["permit_type"]),
                status=str(payload["status"]),
                start_time=start_time,
                end_time=end_time,
                external_id=external_id,
            )
        )


def _persist_worker_location(
    session: AsyncSession,
    event: IngestEventItem,
    zone_uuid: uuid.UUID,
    recorded_at: datetime,
) -> None:
    payload = event.payload
    lat = payload.get("latitude")
    lon = payload.get("longitude")
    location = None
    if lat is not None and lon is not None:
        location = f"SRID=4326;POINT({lon} {lat})"

    session.add(
        WorkerLocation(
            zone_id=zone_uuid,
            worker_id=str(payload["worker_id"]),
            location=location,
            recorded_at=recorded_at,
        )
    )


async def get_latest_sensor_data(
    session: AsyncSession,
    zone_id: str | None = None,
    limit: int = 50,
) -> tuple[list[dict], int, str | None, int]:
    """Return readings, count, last_event_at, total events ingested."""
    from app.db.models import Sensor

    events_count_result = await session.execute(select(func.count()).select_from(RawEvent))
    events_ingested = events_count_result.scalar() or 0

    last_event_result = await session.execute(select(func.max(RawEvent.received_at)))
    last_event_at = last_event_result.scalar()

    query = (
        select(
            SensorReading,
            Sensor.sensor_type,
            Sensor.unit,
            Sensor.zone_id,
        )
        .join(Sensor, SensorReading.sensor_id == Sensor.id)
        .order_by(SensorReading.time.desc())
        .limit(limit)
    )
    if zone_id:
        query = query.where(Sensor.zone_id == uuid.UUID(zone_id))

    result = await session.execute(query)
    rows = result.all()

    readings = [
        {
            "sensor_id": str(reading.sensor_id),
            "zone_id": str(zone_id_val),
            "sensor_type": sensor_type,
            "value": reading.value,
            "unit": unit,
            "timestamp": reading.time.isoformat(),
        }
        for reading, sensor_type, unit, zone_id_val in rows
    ]

    last_event_str = last_event_at.isoformat() if last_event_at else None
    return readings, len(readings), last_event_str, events_ingested
