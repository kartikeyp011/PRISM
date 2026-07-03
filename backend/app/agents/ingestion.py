"""IngestionAgent — normalize sensor/permit/worker events into canonical schema."""

from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.risk import risk_agent
from app.ingestion.service import IngestResult, get_latest_sensor_data, ingest_events
from app.models.schemas import IngestEventItem

logger = logging.getLogger(__name__)


class IngestionAgent:
    async def process_batch(
        self, session: AsyncSession, events: list[IngestEventItem]
    ) -> IngestResult:
        result = await ingest_events(session, events)
        if result.accepted > 0 and result.zone_ids:
            try:
                await risk_agent.evaluate_zones(session, result.zone_ids)
            except Exception:
                logger.exception("Risk evaluation failed after ingest")
        return result

    async def latest_sensors(
        self, session: AsyncSession, zone_id: str | None = None, limit: int = 50
    ) -> tuple[list[dict], int, str | None, int]:
        return await get_latest_sensor_data(session, zone_id=zone_id, limit=limit)


ingestion_agent = IngestionAgent()
