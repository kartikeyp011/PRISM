"""Derive safety hazards from CV detections."""

from __future__ import annotations

from typing import Any

from app.cv.detector import Detection


def derive_hazards(detections: list[Detection], sample_id: str | None = None) -> list[dict[str, Any]]:
    labels = {d.label for d in detections}
    hazards: list[dict[str, Any]] = []

    if "no_hard_hat" in labels or "no_safety_vest" in labels:
        hazards.append(
            {
                "type": "PPE_VIOLATION",
                "severity": "HIGH",
                "message": "Worker detected without required PPE (hard hat and/or safety vest).",
            }
        )

    if "welding_torch" in labels or "fire" in labels:
        hazards.append(
            {
                "type": "HOT_WORK_DETECTED",
                "severity": "HIGH",
                "message": "Hot work activity detected — verify active permit and gas monitoring.",
            }
        )

    if "smoke" in labels:
        hazards.append(
            {
                "type": "FIRE_SMOKE",
                "severity": "CRITICAL",
                "message": "Smoke detected in monitored area — initiate emergency response.",
            }
        )

    if "person" in labels and sample_id == "hot_work_scene" and not any(
        h["type"] == "HOT_WORK_DETECTED" for h in hazards
    ):
        hazards.append(
            {
                "type": "UNAUTHORIZED_PERSON",
                "severity": "MEDIUM",
                "message": "Person detected in restricted hot-work zone.",
            }
        )

    return hazards


def camera_status(hazards: list[dict[str, Any]]) -> str:
    severities = {h.get("severity") for h in hazards}
    if "CRITICAL" in severities:
        return "critical"
    if severities & {"HIGH", "MEDIUM"}:
        return "warning"
    return "normal"
