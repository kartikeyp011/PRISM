"""Database initialization, extensions, hypertable, and demo seed data."""

from __future__ import annotations

import uuid

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Base, Facility, Sensor, Zone
from app.db.session import engine

# Demo facility/zone/sensor IDs used by compound_risk_demo scenario
DEMO_FACILITY_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
DEMO_ZONE_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
DEMO_SENSOR_LEL_ID = uuid.UUID("33333333-3333-3333-3333-333333333333")
DEMO_SENSOR_O2_ID = uuid.UUID("44444444-4444-4444-4444-444444444444")


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE"))
        await conn.run_sync(Base.metadata.create_all)
        await _ensure_hypertable(conn)
        await _ensure_spatial_indexes(conn)
        await conn.execute(text("SELECT 1"))

    async with AsyncSession(engine) as session:
        await _seed_demo_data(session)
        await session.commit()


async def _ensure_spatial_indexes(conn) -> None:
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_zones_polygon ON zones USING GIST (polygon)",
        "CREATE INDEX IF NOT EXISTS idx_sensors_location ON sensors USING GIST (location)",
        "CREATE INDEX IF NOT EXISTS idx_worker_locations_location ON worker_locations USING GIST (location)",
    ]
    for stmt in indexes:
        await conn.execute(text(stmt))


async def _ensure_hypertable(conn) -> None:
    result = await conn.execute(
        text(
            """
            SELECT 1 FROM timescaledb_information.hypertables
            WHERE hypertable_name = 'sensor_readings'
            """
        )
    )
    if result.scalar() is None:
        await conn.execute(
            text(
                "SELECT create_hypertable('sensor_readings', 'time', if_not_exists => TRUE)"
            )
        )


async def _seed_demo_data(session: AsyncSession) -> None:
    existing = await session.get(Facility, DEMO_FACILITY_ID)
    if existing:
        return

    facility = Facility(
        id=DEMO_FACILITY_ID,
        name="Demo Refinery",
        footprint="SRID=4326;POLYGON((-122.42 37.77,-122.41 37.77,-122.41 37.78,-122.42 37.78,-122.42 37.77))",
    )
    zone = Zone(
        id=DEMO_ZONE_ID,
        facility_id=DEMO_FACILITY_ID,
        name="Confined Space A",
        zone_type="confined_space",
        polygon="SRID=4326;POLYGON((-122.418 37.774,-122.417 37.774,-122.417 37.775,-122.418 37.775,-122.418 37.774))",
    )
    lel_sensor = Sensor(
        id=DEMO_SENSOR_LEL_ID,
        zone_id=DEMO_ZONE_ID,
        sensor_type="LEL",
        unit="%",
        location="SRID=4326;POINT(-122.4175 37.7745)",
    )
    o2_sensor = Sensor(
        id=DEMO_SENSOR_O2_ID,
        zone_id=DEMO_ZONE_ID,
        sensor_type="O2",
        unit="%",
        location="SRID=4326;POINT(-122.4176 37.7746)",
    )
    session.add_all([facility, zone, lel_sensor, o2_sensor])
