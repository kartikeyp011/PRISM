"""CV analysis orchestration and persistence."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cv.detector import analyze_image, detection_to_dict
from app.cv.hazards import camera_status, derive_hazards
from app.cv.samples import list_samples, sample_path
from app.db.models import Camera, CvAnalysis


class CvAnalyzeResult:
    def __init__(
        self,
        analysis_id: str,
        camera_id: str | None,
        sample_id: str | None,
        cv_mode: str,
        detections: list[dict],
        hazards: list[dict],
        analyzed_at: str,
    ):
        self.analysis_id = analysis_id
        self.camera_id = camera_id
        self.sample_id = sample_id
        self.cv_mode = cv_mode
        self.detections = detections
        self.hazards = hazards
        self.analyzed_at = analyzed_at


async def get_samples() -> list[dict]:
    return list_samples()


async def analyze_frame(
    session: AsyncSession,
    *,
    camera_id: str | None = None,
    sample_id: str | None = None,
    image_base64: str | None = None,
) -> CvAnalyzeResult:
    camera: Camera | None = None
    if camera_id:
        camera = await session.get(Camera, uuid.UUID(camera_id))
        if camera is None:
            raise LookupError(f"Camera not found: {camera_id}")

    path = sample_path(sample_id) if sample_id else None
    if sample_id and path is None:
        raise ValueError(f"Unknown sample_id: {sample_id}")

    detections, mode = analyze_image(
        sample_id=sample_id,
        image_path=path,
        image_base64=image_base64,
    )
    hazards = derive_hazards(detections, sample_id=sample_id)
    det_dicts = [detection_to_dict(d) for d in detections]
    now = datetime.now(timezone.utc)

    record = CvAnalysis(
        id=uuid.uuid4(),
        camera_id=camera.id if camera else None,
        sample_id=sample_id,
        cv_mode=mode,
        detections=det_dicts,
        hazards=hazards,
        analyzed_at=now,
    )
    session.add(record)
    await session.commit()

    return CvAnalyzeResult(
        analysis_id=str(record.id),
        camera_id=str(camera.id) if camera else None,
        sample_id=sample_id,
        cv_mode=mode,
        detections=det_dicts,
        hazards=hazards,
        analyzed_at=now.isoformat(),
    )


async def latest_analysis_by_camera(
    session: AsyncSession,
) -> dict[str, CvAnalysis]:
    result = await session.execute(
        select(CvAnalysis).order_by(CvAnalysis.analyzed_at.desc())
    )
    latest: dict[str, CvAnalysis] = {}
    for row in result.scalars():
        if row.camera_id is None:
            continue
        key = str(row.camera_id)
        if key not in latest:
            latest[key] = row
    return latest
