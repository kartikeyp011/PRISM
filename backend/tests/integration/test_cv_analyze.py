"""Integration tests for CV analyze endpoint."""

import pytest

from app.contract import PATH_CV_ANALYZE, PATH_CV_SAMPLES, PATH_MAP_LAYERS

DEMO_CAMERA_ID = "66666666-6666-6666-6666-666666666666"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cv_samples_lists_demo_entries(integration_client):
    response = await integration_client.get(PATH_CV_SAMPLES)
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 3
    ids = {s["sample_id"] for s in data["samples"]}
    assert "no_ppe_worker" in ids


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cv_analyze_no_ppe_detects_hazard(integration_client):
    response = await integration_client.post(
        PATH_CV_ANALYZE,
        json={
            "sample_id": "no_ppe_worker",
            "camera_id": DEMO_CAMERA_ID,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["cv_mode"] in ("mock", "live")
    assert len(data["detections"]) >= 1
    hazard_types = {h["type"] for h in data["hazards"]}
    assert "PPE_VIOLATION" in hazard_types


@pytest.mark.integration
@pytest.mark.asyncio
async def test_map_layers_includes_cameras(integration_client):
    await integration_client.post(
        PATH_CV_ANALYZE,
        json={"sample_id": "no_ppe_worker", "camera_id": DEMO_CAMERA_ID},
    )

    response = await integration_client.get(PATH_MAP_LAYERS)
    assert response.status_code == 200
    data = response.json()

    assert "cv_hazard_colors" in data
    cameras = data["layers"]["cameras"]
    assert cameras["type"] == "FeatureCollection"
    assert len(cameras["features"]) >= 1

    cam = cameras["features"][0]
    assert cam["geometry"]["type"] == "Point"
    assert "hazard_status" in cam["properties"]
