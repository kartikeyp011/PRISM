"""Load and expose values from api_contract.yaml."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

CONTRACT_PATH = Path(__file__).resolve().parent.parent / "api_contract.yaml"


@lru_cache
def load_contract() -> dict[str, Any]:
    with CONTRACT_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_config_keys() -> dict[str, Any]:
    return load_contract()["config_keys"]


def get_constants() -> dict[str, Any]:
    return load_contract()["constants"]


def get_redis_topics() -> dict[str, str]:
    return load_contract()["redis_topics"]


def get_websocket_config() -> dict[str, Any]:
    return load_contract()["websocket"]


def get_endpoints() -> dict[str, Any]:
    return load_contract()["endpoints"]


def get_endpoint_path(name: str) -> str:
    return get_endpoints()[name]["path"]


# Convenience exports aligned with contract
RISK_LEVELS: list[str] = get_constants()["risk_levels"]
ALERT_STATUSES: list[str] = get_constants()["alert_statuses"]
EVENT_TYPES: list[str] = get_constants()["event_types"]
THRESHOLDS: dict[str, float | int] = get_constants()["thresholds"]
COMPOUND_RULES: list[dict[str, Any]] = get_constants()["compound_rules"]

REDIS_TOPIC_EVENTS_INGEST = get_redis_topics()["events_ingest"]
REDIS_TOPIC_ALERTS = get_redis_topics()["alerts"]
REDIS_TOPIC_RISK = get_redis_topics()["risk"]

WS_PATH = get_websocket_config()["path"]
WS_EVENTS: list[str] = get_websocket_config()["events"]

PATH_HEALTH = get_endpoint_path("health")
PATH_INGEST_EVENTS = get_endpoint_path("ingest_events")
PATH_SENSORS_LATEST = get_endpoint_path("sensors_latest")
PATH_RISK_ACTIVE = get_endpoint_path("risk_active")
PATH_ALERTS_ACTIVE = get_endpoint_path("alerts_active")
PATH_ALERTS_ACK = get_endpoint_path("alerts_ack")
PATH_MAP_LAYERS = get_endpoint_path("map_layers")
PATH_RAG_QUERY = get_endpoint_path("rag_query")
