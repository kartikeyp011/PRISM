"""Validate backend code alignment with api_contract.yaml."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

BACKEND_ROOT = Path(__file__).resolve().parent.parent
CONTRACT_PATH = BACKEND_ROOT / "api_contract.yaml"

sys.path.insert(0, str(BACKEND_ROOT))


def load_contract() -> dict:
    with CONTRACT_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate_config_keys(contract: dict) -> list[str]:
    from app.config import Settings

    errors: list[str] = []
    fields = set(Settings.model_fields.keys())
    for key in contract["config_keys"]:
        if contract["config_keys"][key].get("kaggle_only"):
            continue
        if key not in fields:
            errors.append(f"Config key missing from Settings: {key}")
    return errors


def validate_endpoint_paths(contract: dict) -> list[str]:
    from app import contract as contract_module

    mapping = {
        "health": contract_module.PATH_HEALTH,
        "ingest_events": contract_module.PATH_INGEST_EVENTS,
        "sensors_latest": contract_module.PATH_SENSORS_LATEST,
        "risk_active": contract_module.PATH_RISK_ACTIVE,
        "alerts_active": contract_module.PATH_ALERTS_ACTIVE,
        "alerts_ack": contract_module.PATH_ALERTS_ACK,
        "map_layers": contract_module.PATH_MAP_LAYERS,
        "rag_query": contract_module.PATH_RAG_QUERY,
    }
    errors: list[str] = []
    for name, spec in contract["endpoints"].items():
        expected = spec["path"]
        actual = mapping.get(name)
        if actual != expected:
            errors.append(f"Endpoint path mismatch: {name} expected {expected}, got {actual}")
    return errors


def validate_redis_topics(contract: dict) -> list[str]:
    from app import contract as contract_module

    mapping = {
        "events_ingest": contract_module.REDIS_TOPIC_EVENTS_INGEST,
        "alerts": contract_module.REDIS_TOPIC_ALERTS,
        "risk": contract_module.REDIS_TOPIC_RISK,
    }
    errors: list[str] = []
    for key, expected in contract["redis_topics"].items():
        actual = mapping.get(key)
        if actual != expected:
            errors.append(f"Redis topic mismatch: {key} expected {expected}, got {actual}")
    return errors


def validate_websocket(contract: dict) -> list[str]:
    from app import contract as contract_module

    errors: list[str] = []
    if contract_module.WS_PATH != contract["websocket"]["path"]:
        errors.append(
            f"WebSocket path mismatch: expected {contract['websocket']['path']}, "
            f"got {contract_module.WS_PATH}"
        )
    for event in contract["websocket"]["events"]:
        if event not in contract_module.WS_EVENTS:
            errors.append(f"WebSocket event missing: {event}")
    return errors


def validate_constants(contract: dict) -> list[str]:
    from app import contract as contract_module

    errors: list[str] = []
    if contract_module.RISK_LEVELS != contract["constants"]["risk_levels"]:
        errors.append("RISK_LEVELS constant drift from contract")
    if contract_module.ALERT_STATUSES != contract["constants"]["alert_statuses"]:
        errors.append("ALERT_STATUSES constant drift from contract")
    if contract_module.EVENT_TYPES != contract["constants"]["event_types"]:
        errors.append("EVENT_TYPES constant drift from contract")
    if contract_module.RISK_COLORS != contract["constants"]["risk_colors"]:
        errors.append("RISK_COLORS constant drift from contract")
    return errors


def validate_routes_registered() -> list[str]:
    from app.main import app

    registered = {route.path for route in app.routes if hasattr(route, "methods")}
    errors: list[str] = []
    from app import contract as contract_module

    for path in [
        contract_module.PATH_HEALTH,
        contract_module.PATH_INGEST_EVENTS,
        contract_module.PATH_SENSORS_LATEST,
        contract_module.PATH_RISK_ACTIVE,
        contract_module.PATH_ALERTS_ACTIVE,
        contract_module.PATH_ALERTS_ACK,
        contract_module.PATH_MAP_LAYERS,
        contract_module.PATH_RAG_QUERY,
    ]:
        if path not in registered:
            errors.append(f"Route not registered in FastAPI app: {path}")
    return errors


def main() -> int:
    if not CONTRACT_PATH.exists():
        print(f"ERROR: Contract file not found: {CONTRACT_PATH}")
        return 1

    contract = load_contract()
    errors: list[str] = []
    errors.extend(validate_config_keys(contract))
    errors.extend(validate_endpoint_paths(contract))
    errors.extend(validate_redis_topics(contract))
    errors.extend(validate_websocket(contract))
    errors.extend(validate_constants(contract))
    errors.extend(validate_routes_registered())

    if errors:
        print("Contract validation FAILED:")
        for err in errors:
            print(f"  - {err}")
        return 1

    print("Contract validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
