"""RiskAgent — evaluate compound rules for ingested zones."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Alert, RiskAssessmentRecord
from app.risk.engine import evaluate_zones


class RiskAgent:
    async def evaluate_zones(self, session: AsyncSession, zone_ids: list[str]) -> list[Alert]:
        return await evaluate_zones(session, zone_ids)

    async def get_active_assessments(
        self,
        session: AsyncSession,
        zone_id: str | None = None,
    ) -> list[RiskAssessmentRecord]:
        query = (
            select(RiskAssessmentRecord)
            .where(RiskAssessmentRecord.risk_level.in_(["MEDIUM", "HIGH", "CRITICAL"]))
            .order_by(RiskAssessmentRecord.assessed_at.desc())
            .limit(50)
        )
        if zone_id:
            import uuid

            query = query.where(RiskAssessmentRecord.zone_id == uuid.UUID(zone_id))
        result = await session.execute(query)
        return list(result.scalars().all())


risk_agent = RiskAgent()
