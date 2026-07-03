"""Integration tests for map layers API."""

import pytest

from app.contract import PATH_MAP_LAYERS


@pytest.mark.integration
@pytest.mark.asyncio
async def test_map_layers_returns_valid_geojson(integration_client):
    response = await integration_client.get(PATH_MAP_LAYERS)
    assert response.status_code == 200
    data = response.json()

    assert data["type"] == "FeatureCollection"
    assert "risk_colors" in data
    assert "LOW" in data["risk_colors"]

    for layer_name in ("zones", "sensors", "workers", "permits"):
        layer = data["layers"][layer_name]
        assert layer["type"] == "FeatureCollection"
        assert isinstance(layer["features"], list)

    zones = data["layers"]["zones"]["features"]
    assert len(zones) >= 1
    assert zones[0]["geometry"]["type"] == "Polygon"
    assert "risk_level" in zones[0]["properties"]
