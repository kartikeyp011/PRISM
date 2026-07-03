"""CV detector mock mode unit tests."""

from app.cv.detector import analyze_image, cv_mode


def test_cv_mode_defaults_to_mock():
    assert cv_mode() == "mock"


def test_mock_no_ppe_sample():
    detections, mode = analyze_image(sample_id="no_ppe_worker")
    assert mode == "mock"
    labels = {d.label for d in detections}
    assert "no_hard_hat" in labels
    assert "no_safety_vest" in labels


def test_mock_compliant_sample():
    detections, mode = analyze_image(sample_id="compliant_worker")
    assert mode == "mock"
    labels = {d.label for d in detections}
    assert "hard_hat" in labels
    assert "no_hard_hat" not in labels


def test_mock_hot_work_sample():
    detections, mode = analyze_image(sample_id="hot_work_scene")
    assert mode == "mock"
    labels = {d.label for d in detections}
    assert "welding_torch" in labels
