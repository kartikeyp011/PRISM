"""AlertAgent — dedupe, prioritize, route alerts."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.alerts.service import acknowledge_alert, get_active_alerts
from app.db.models import Alert


class AlertAgent:
    async def list_active(
        self, session: AsyncSession, zone_id: str | None = None
    ) -> list[Alert]:
        return await get_active_alerts(session, zone_id)

    async def acknowledge(
        self,
        session: AsyncSession,
        alert_id: str,
        acknowledged_by: str | None = None,
    ) -> Alert:
        return await acknowledge_alert(session, alert_id, acknowledged_by)


alert_agent = AlertAgent()
