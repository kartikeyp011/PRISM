"""Computer vision detection — YOLOv8 live mode with mock fallback."""

from __future__ import annotations

import base64
import io
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)

_model = None
_model_failed = False


@dataclass
class Detection:
    label: str
    confidence: float
    bbox: list[float]  # normalized x1, y1, x2, y2


MOCK_DETECTIONS: dict[str, list[Detection]] = {
    "compliant_worker": [
        Detection("person", 0.94, [0.28, 0.12, 0.72, 0.92]),
        Detection("hard_hat", 0.91, [0.38, 0.12, 0.58, 0.28]),
        Detection("safety_vest", 0.89, [0.32, 0.32, 0.68, 0.72]),
    ],
    "no_ppe_worker": [
        Detection("person", 0.93, [0.28, 0.12, 0.72, 0.92]),
        Detection("no_hard_hat", 0.88, [0.38, 0.12, 0.58, 0.28]),
        Detection("no_safety_vest", 0.86, [0.32, 0.32, 0.68, 0.72]),
    ],
    "hot_work_scene": [
        Detection("person", 0.90, [0.22, 0.15, 0.55, 0.88]),
        Detection("welding_torch", 0.87, [0.48, 0.45, 0.62, 0.65]),
        Detection("fire", 0.82, [0.52, 0.38, 0.68, 0.58]),
    ],
}


def cv_mode() -> str:
    if settings.cv_enabled and _get_model() is not None:
        return "live"
    return "mock"


def _get_model():
    global _model, _model_failed
    if not settings.cv_enabled:
        return None
    if _model_failed:
        return None
    if _model is not None:
        return _model
    try:
        from ultralytics import YOLO

        _model = YOLO(settings.CV_MODEL)
        logger.info("Loaded CV model: %s", settings.CV_MODEL)
        return _model
    except Exception:
        logger.exception("Failed to load YOLO model — falling back to mock CV")
        _model_failed = True
        return None


def _mock_detect(sample_id: str | None) -> list[Detection]:
    key = sample_id if sample_id in MOCK_DETECTIONS else "compliant_worker"
    return list(MOCK_DETECTIONS[key])


def _live_detect(image_path: Path) -> list[Detection]:
    model = _get_model()
    if model is None:
        return []

    results = model.predict(str(image_path), verbose=False)
    detections: list[Detection] = []
    for result in results:
        if result.boxes is None:
            continue
        names = result.names or {}
        h, w = result.orig_shape
        for box in result.boxes:
            cls_id = int(box.cls[0])
            label = names.get(cls_id, str(cls_id))
            conf = float(box.conf[0])
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            detections.append(
                Detection(
                    label=label,
                    confidence=round(conf, 3),
                    bbox=[
                        round(x1 / w, 3),
                        round(y1 / h, 3),
                        round(x2 / w, 3),
                        round(y2 / h, 3),
                    ],
                )
            )
    return detections


def _load_image_bytes(image_base64: str) -> Path | None:
    try:
        from PIL import Image

        raw = base64.b64decode(image_base64.split(",")[-1])
        img = Image.open(io.BytesIO(raw)).convert("RGB")
        temp = Path(settings.CV_TEMP_DIR)
        temp.mkdir(parents=True, exist_ok=True)
        out = temp / "upload_frame.png"
        img.save(out)
        return out
    except Exception:
        logger.exception("Failed to decode uploaded image")
        return None


def analyze_image(
    *,
    sample_id: str | None = None,
    image_path: Path | None = None,
    image_base64: str | None = None,
) -> tuple[list[Detection], str]:
    """Run detection and return (detections, cv_mode)."""
    path = image_path
    if image_base64:
        path = _load_image_bytes(image_base64)

    mode = cv_mode()
    if mode == "live" and path is not None:
        detections = _live_detect(path)
        if detections:
            return detections, "live"

    return _mock_detect(sample_id), "mock"


def detection_to_dict(d: Detection) -> dict[str, Any]:
    return {"label": d.label, "confidence": d.confidence, "bbox": d.bbox}
