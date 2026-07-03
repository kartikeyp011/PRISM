"""Alert creation, dedup, persistence, and routing."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.alerts.ws_manager import ws_manager
from app.contract import REDIS_TOPIC_ALERTS, THRESHOLDS
from app.db.models import Alert, RiskAssessmentRecord
from app.services.redis_client import publish

logger = logging.getLogger(__name__)

DEDUP_SECONDS = int(THRESHOLDS["alert_dedup_seconds"])


@dataclass
class RuleHit:
    rule_id: str
    severity: str
    risk_level: str
    message: str
    context: dict


def _alert_payload(alert: Alert) -> dict:
    return {
        "alert_id": str(alert.id),
        "zone_id": str(alert.zone_id),
        "rule_id": alert.rule_id,
        "severity": alert.severity,
        "status": alert.status,
        "message": alert.message,
        "created_at": alert.created_at.isoformat(),
    }


async def persist_assessment(
    session: AsyncSession,
    zone_id: uuid.UUID,
    rule_id: str,
    risk_level: str,
    context: dict,
    assessed_at: datetime | None = None,
) -> RiskAssessmentRecord:
    record = RiskAssessmentRecord(
        zone_id=zone_id,
        rule_id=rule_id,
        risk_level=risk_level,
        context=context,
        assessed_at=assessed_at or datetime.now(timezone.utc),
    )
    session.add(record)
    await session.flush()
    return record


async def _is_duplicate(
    session: AsyncSession,
    zone_id: uuid.UUID,
    rule_id: str,
) -> bool:
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=DEDUP_SECONDS)
    result = await session.execute(
        select(Alert.id).where(
            Alert.zone_id == zone_id,
            Alert.rule_id == rule_id,
            Alert.created_at >= cutoff,
            Alert.status == "ACTIVE",
        )
    )
    return result.scalar_one_or_none() is not None


async def create_alert_from_hit(
    session: AsyncSession,
    zone_id: uuid.UUID,
    hit: RuleHit,
) -> Alert | None:
    if await _is_duplicate(session, zone_id, hit.rule_id):
        logger.debug("Deduped alert for rule %s zone %s", hit.rule_id, zone_id)
        return None

    assessment = await persist_assessment(
        session, zone_id, hit.rule_id, hit.risk_level, hit.context
    )
    alert = Alert(
        zone_id=zone_id,
        risk_assessment_id=assessment.id,
        rule_id=hit.rule_id,
        severity=hit.severity,
        status="ACTIVE",
        message=hit.message,
        created_at=datetime.now(timezone.utc),
    )
    session.add(alert)
    await session.flush()

    payload = _alert_payload(alert)
    await publish(REDIS_TOPIC_ALERTS, {"event": "alert.created", **payload})
    await ws_manager.broadcast("alert.created", payload)
    return alert


async def acknowledge_alert(
    session: AsyncSession,
    alert_id: str,
    acknowledged_by: str | None = None,
) -> Alert:
    alert_uuid = uuid.UUID(alert_id)
    alert = await session.get(Alert, alert_uuid)
    if alert is None:
        raise LookupError(f"Alert not found: {alert_id}")
    if alert.status == "ACKNOWLEDGED":
        raise ValueError(f"Alert already acknowledged: {alert_id}")

    alert.status = "ACKNOWLEDGED"
    alert.acked_at = datetime.now(timezone.utc)
    alert.acknowledged_by = acknowledged_by
    await session.flush()

    payload = _alert_payload(alert)
    await publish(REDIS_TOPIC_ALERTS, {"event": "alert.updated", **payload})
    await ws_manager.broadcast("alert.updated", payload)
    return alert


async def get_active_alerts(
    session: AsyncSession,
    zone_id: str | None = None,
) -> list[Alert]:
    query = (
        select(Alert)
        .where(Alert.status == "ACTIVE")
        .order_by(Alert.created_at.desc())
    )
    if zone_id:
        query = query.where(Alert.zone_id == uuid.UUID(zone_id))
    result = await session.execute(query)
    return list(result.scalars().all())
