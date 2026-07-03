"""CV hazard derivation unit tests."""

from app.cv.detector import Detection
from app.cv.hazards import camera_status, derive_hazards


def test_derive_ppe_violation():
    detections = [
        Detection("person", 0.9, [0, 0, 1, 1]),
        Detection("no_hard_hat", 0.85, [0.1, 0.1, 0.3, 0.3]),
    ]
    hazards = derive_hazards(detections)
    assert len(hazards) == 1
    assert hazards[0]["type"] == "PPE_VIOLATION"
    assert hazards[0]["severity"] == "HIGH"


def test_derive_hot_work_hazard():
    detections = [
        Detection("person", 0.9, [0, 0, 1, 1]),
        Detection("welding_torch", 0.87, [0.4, 0.4, 0.6, 0.6]),
        Detection("fire", 0.82, [0.5, 0.3, 0.7, 0.5]),
    ]
    hazards = derive_hazards(detections)
    types = {h["type"] for h in hazards}
    assert "HOT_WORK_DETECTED" in types


def test_camera_status_critical():
    hazards = [{"type": "FIRE_SMOKE", "severity": "CRITICAL", "message": "smoke"}]
    assert camera_status(hazards) == "critical"


def test_camera_status_normal():
    assert camera_status([]) == "normal"
