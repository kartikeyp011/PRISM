"""VisionAgent — CCTV frame analysis and hazard detection."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.cv.service import CvAnalyzeResult, analyze_frame, get_samples


class VisionAgent:
    async def list_samples(self) -> list[dict]:
        return await get_samples()

    async def analyze(
        self,
        session: AsyncSession,
        *,
        camera_id: str | None = None,
        sample_id: str | None = None,
        image_base64: str | None = None,
    ) -> CvAnalyzeResult:
        return await analyze_frame(
            session,
            camera_id=camera_id,
            sample_id=sample_id,
            image_base64=image_base64,
        )


vision_agent = VisionAgent()
