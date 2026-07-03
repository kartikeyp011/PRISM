"""Build GeoJSON map layers from PostGIS data."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.contract import CV_HAZARD_COLORS, RISK_COLORS, THRESHOLDS
from app.cv.hazards import camera_status
from app.cv.service import latest_analysis_by_camera

LEL_HIGH = float(THRESHOLDS["lel_high"])
O2_LOW = float(THRESHOLDS["o2_low"])


def empty_feature_collection() -> dict[str, Any]:
    return {"type": "FeatureCollection", "features": []}


def _parse_geojson(value: Any) -> dict | None:
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        return json.loads(value)
    return None


def _sensor_status(sensor_type: str, value: float | None) -> str:
    if value is None:
        return "unknown"
    if sensor_type == "LEL":
        return "critical" if value > LEL_HIGH else "normal"
    if sensor_type == "O2":
        return "critical" if value < O2_LOW else "normal"
    return "normal"


async def _fetch_zone_features(session: AsyncSession) -> list[dict]:
    result = await session.execute(
        text(
            """
            SELECT
                z.id::text,
                z.name,
                z.zone_type,
                ST_AsGeoJSON(z.polygon)::json AS geometry,
                COALESCE(
                    (
                        SELECT ra.risk_level
                        FROM risk_assessments ra
                        WHERE ra.zone_id = z.id
                        ORDER BY ra.assessed_at DESC
                        LIMIT 1
                    ),
                    'LOW'
                ) AS risk_level
            FROM zones z
            WHERE z.polygon IS NOT NULL
            """
        )
    )
    features = []
    for row in result.mappings():
        geometry = _parse_geojson(row["geometry"])
        if not geometry:
            continue
        risk_level = row["risk_level"]
        features.append(
            {
                "type": "Feature",
                "id": row["id"],
                "geometry": geometry,
                "properties": {
                    "zone_id": row["id"],
                    "name": row["name"],
                    "zone_type": row["zone_type"],
                    "risk_level": risk_level,
                    "fill_color": RISK_COLORS.get(risk_level, RISK_COLORS["LOW"]),
                },
            }
        )
    return features


async def _fetch_sensor_features(session: AsyncSession) -> list[dict]:
    result = await session.execute(
        text(
            """
            SELECT
                s.id::text,
                s.zone_id::text,
                s.sensor_type,
                s.unit,
                ST_AsGeoJSON(s.location)::json AS geometry,
                (
                    SELECT sr.value
                    FROM sensor_readings sr
                    WHERE sr.sensor_id = s.id
                    ORDER BY sr.time DESC
                    LIMIT 1
                ) AS latest_value,
                (
                    SELECT sr.time
                    FROM sensor_readings sr
                    WHERE sr.sensor_id = s.id
                    ORDER BY sr.time DESC
                    LIMIT 1
                ) AS latest_time
            FROM sensors s
            WHERE s.location IS NOT NULL
            """
        )
    )
    features = []
    for row in result.mappings():
        geometry = _parse_geojson(row["geometry"])
        if not geometry:
            continue
        value = row["latest_value"]
        sensor_type = row["sensor_type"]
        features.append(
            {
                "type": "Feature",
                "id": row["id"],
                "geometry": geometry,
                "properties": {
                    "sensor_id": row["id"],
                    "zone_id": row["zone_id"],
                    "sensor_type": sensor_type,
                    "unit": row["unit"],
                    "value": float(value) if value is not None else None,
                    "timestamp": row["latest_time"].isoformat() if row["latest_time"] else None,
                    "status": _sensor_status(sensor_type, float(value) if value is not None else None),
                },
            }
        )
    return features


async def _fetch_worker_features(session: AsyncSession) -> list[dict]:
    result = await session.execute(
        text(
            """
            SELECT DISTINCT ON (wl.worker_id)
                wl.id::text,
                wl.worker_id,
                wl.zone_id::text,
                wl.recorded_at,
                ST_AsGeoJSON(wl.location)::json AS geometry
            FROM worker_locations wl
            WHERE wl.location IS NOT NULL
            ORDER BY wl.worker_id, wl.recorded_at DESC
            """
        )
    )
    features = []
    for row in result.mappings():
        geometry = _parse_geojson(row["geometry"])
        if not geometry:
            continue
        features.append(
            {
                "type": "Feature",
                "id": row["id"],
                "geometry": geometry,
                "properties": {
                    "worker_id": row["worker_id"],
                    "zone_id": row["zone_id"],
                    "recorded_at": row["recorded_at"].isoformat(),
                },
            }
        )
    return features


async def _fetch_permit_features(session: AsyncSession) -> list[dict]:
    result = await session.execute(
        text(
            """
            SELECT
                p.id::text,
                p.external_id,
                p.zone_id::text,
                p.permit_type,
                p.status,
                p.start_time,
                p.end_time,
                ST_AsGeoJSON(ST_Centroid(z.polygon))::json AS geometry
            FROM permits p
            JOIN zones z ON z.id = p.zone_id
            WHERE p.status = 'active' AND z.polygon IS NOT NULL
            """
        )
    )
    features = []
    for row in result.mappings():
        geometry = _parse_geojson(row["geometry"])
        if not geometry:
            continue
        features.append(
            {
                "type": "Feature",
                "id": row["id"],
                "geometry": geometry,
                "properties": {
                    "permit_id": row["external_id"],
                    "zone_id": row["zone_id"],
                    "permit_type": row["permit_type"],
                    "status": row["status"],
                    "start_time": row["start_time"].isoformat(),
                    "end_time": row["end_time"].isoformat() if row["end_time"] else None,
                },
            }
        )
    return features


async def _fetch_camera_features(session: AsyncSession) -> list[dict]:
    latest = await latest_analysis_by_camera(session)
    result = await session.execute(
        text(
            """
            SELECT
                c.id::text,
                c.zone_id::text,
                c.name,
                c.status,
                ST_AsGeoJSON(c.location)::json AS geometry
            FROM cameras c
            WHERE c.location IS NOT NULL
            """
        )
    )
    features = []
    for row in result.mappings():
        geometry = _parse_geojson(row["geometry"])
        if not geometry:
            continue
        analysis = latest.get(row["id"])
        hazards = analysis.hazards if analysis else []
        hazard_status = camera_status(hazards)
        features.append(
            {
                "type": "Feature",
                "id": row["id"],
                "geometry": geometry,
                "properties": {
                    "camera_id": row["id"],
                    "zone_id": row["zone_id"],
                    "name": row["name"],
                    "status": row["status"],
                    "hazard_status": hazard_status,
                    "fill_color": CV_HAZARD_COLORS.get(hazard_status, CV_HAZARD_COLORS["normal"]),
                    "hazard_count": len(hazards),
                    "last_analyzed_at": analysis.analyzed_at.isoformat() if analysis else None,
                    "last_cv_mode": analysis.cv_mode if analysis else None,
                    "last_hazards": hazards[:3],
                },
            }
        )
    return features


async def build_map_layers(session: AsyncSession) -> dict[str, Any]:
    zones = await _fetch_zone_features(session)
    sensors = await _fetch_sensor_features(session)
    workers = await _fetch_worker_features(session)
    permits = await _fetch_permit_features(session)
    cameras = await _fetch_camera_features(session)

    return {
        "type": "FeatureCollection",
        "risk_colors": RISK_COLORS,
        "cv_hazard_colors": CV_HAZARD_COLORS,
        "layers": {
            "zones": {"type": "FeatureCollection", "features": zones},
            "sensors": {"type": "FeatureCollection", "features": sensors},
            "workers": {"type": "FeatureCollection", "features": workers},
            "permits": {"type": "FeatureCollection", "features": permits},
            "cameras": {"type": "FeatureCollection", "features": cameras},
        },
    }
