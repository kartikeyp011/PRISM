"""Unit tests for map GeoJSON helpers."""

from app.map.service import _sensor_status, empty_feature_collection


def test_empty_feature_collection_structure():
    fc = empty_feature_collection()
    assert fc["type"] == "FeatureCollection"
    assert fc["features"] == []


def test_sensor_status_lel_critical():
    assert _sensor_status("LEL", 42.0) == "critical"
    assert _sensor_status("LEL", 5.0) == "normal"


def test_sensor_status_o2_critical():
    assert _sensor_status("O2", 18.0) == "critical"
    assert _sensor_status("O2", 20.5) == "normal"


def test_sensor_status_unknown_value():
    assert _sensor_status("LEL", None) == "unknown"
