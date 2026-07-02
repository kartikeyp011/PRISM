"""IngestionAgent — normalize sensor/permit/worker events into canonical schema."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.service import IngestResult, get_latest_sensor_data, ingest_events
from app.models.schemas import IngestEventItem


class IngestionAgent:
    async def process_batch(
        self, session: AsyncSession, events: list[IngestEventItem]
    ) -> IngestResult:
        return await ingest_events(session, events)

    async def latest_sensors(
        self, session: AsyncSession, zone_id: str | None = None, limit: int = 50
    ) -> tuple[list[dict], int, str | None, int]:
        return await get_latest_sensor_data(session, zone_id=zone_id, limit=limit)


ingestion_agent = IngestionAgent()
