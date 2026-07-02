"""Replay JSON scenario batches against the PRISM ingest API."""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import httpx

API_URL = os.environ.get("PRISM_API_URL", "http://localhost:8000").rstrip("/")
SCENARIO = os.environ.get("SCENARIO", "compound_risk_demo")
SCENARIOS_DIR = Path(os.environ.get("SCENARIOS_DIR", "scenarios"))


def load_scenario(name: str) -> dict:
    path = SCENARIOS_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Scenario not found: {path}")
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def post_batch(client: httpx.Client, events: list[dict]) -> dict:
    response = client.post(
        f"{API_URL}/api/v1/ingest/events",
        json={"events": events},
        timeout=30.0,
    )
    response.raise_for_status()
    return response.json()


def main() -> int:
    print(f"PRISM Simulator — API: {API_URL}")
    print(f"Scenario: {SCENARIO}")

    try:
        scenario = load_scenario(SCENARIO)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"Description: {scenario.get('description', '')}")

    with httpx.Client() as client:
        try:
            health = client.get(f"{API_URL}/api/v1/health", timeout=10.0)
            health.raise_for_status()
            print(f"Backend healthy: {health.json()}")
        except httpx.HTTPError as exc:
            print(f"Backend not reachable: {exc}", file=sys.stderr)
            return 1

        total_accepted = 0
        batches = scenario.get("batches", [])
        for index, batch in enumerate(batches, start=1):
            delay = batch.get("delay_seconds", 0)
            if delay > 0:
                print(f"Waiting {delay}s before batch {index}…")
                time.sleep(delay)

            events = batch.get("events", [])
            if not events:
                continue

            result = post_batch(client, events)
            total_accepted += result.get("accepted", 0)
            print(
                f"Batch {index}/{len(batches)}: "
                f"accepted={result.get('accepted', 0)} "
                f"skipped={result.get('skipped', 0)} "
                f"status={result.get('status')}"
            )

        latest = client.get(f"{API_URL}/api/v1/sensors/latest", timeout=10.0)
        latest.raise_for_status()
        summary = latest.json()
        print(
            f"Done — total accepted: {total_accepted}, "
            f"events_ingested={summary.get('events_ingested')}, "
            f"readings={summary.get('count')}, "
            f"last_event_at={summary.get('last_event_at')}"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
