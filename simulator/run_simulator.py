"""Demo scenario simulator — full implementation in Feature 1."""

from __future__ import annotations

import os
import sys
import time

import httpx

API_URL = os.environ.get("PRISM_API_URL", "http://localhost:8000")
SCENARIO_PATH = os.environ.get("SCENARIO_PATH", "scenarios/compound_risk_demo.json")


def main() -> int:
    print(f"PRISM Simulator (stub) — target API: {API_URL}")
    print(f"Scenario: {SCENARIO_PATH}")
    print("Simulator will replay events in Feature 1. Checking API health…")

    try:
        response = httpx.get(f"{API_URL}/api/v1/health", timeout=10.0)
        response.raise_for_status()
        print(f"Backend healthy: {response.json()}")
    except httpx.HTTPError as exc:
        print(f"Backend not reachable: {exc}", file=sys.stderr)
        return 1

    print("Waiting for Feature 1 ingestion implementation…")
    time.sleep(2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
