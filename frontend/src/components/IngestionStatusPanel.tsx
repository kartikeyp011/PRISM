import { useEffect, useState } from "react";
import {
  fetchSensorsLatest,
  SCENARIOS,
  type SensorsLatestResponse,
} from "../api/client";

interface Props {
  pollIntervalMs?: number;
}

export default function IngestionStatusPanel({ pollIntervalMs = 5000 }: Props) {
  const [scenario, setScenario] = useState(SCENARIOS[0].id);
  const [data, setData] = useState<SensorsLatestResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    const load = () => {
      fetchSensorsLatest()
        .then((result) => {
          if (active) {
            setData(result);
            setError(null);
          }
        })
        .catch((err: Error) => {
          if (active) setError(err.message);
        });
    };

    load();
    const timer = setInterval(load, pollIntervalMs);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [pollIntervalMs]);

  return (
    <section className="status-card ingestion-panel">
      <h2>Ingestion Status</h2>
      <label className="scenario-select">
        Scenario
        <select
          value={scenario}
          onChange={(e) => setScenario(e.target.value)}
          aria-label="Scenario selector"
        >
          {SCENARIOS.map((s) => (
            <option key={s.id} value={s.id}>
              {s.label}
            </option>
          ))}
        </select>
      </label>
      {error && <p className="error">{error}</p>}
      {data && (
        <ul>
          <li>Events ingested: {data.events_ingested}</li>
          <li>Latest readings: {data.count}</li>
          <li>
            Last event:{" "}
            {data.last_event_at
              ? new Date(data.last_event_at).toLocaleString()
              : "—"}
          </li>
          <li>Active scenario: {scenario}</li>
        </ul>
      )}
      {!data && !error && <p>Loading ingestion status…</p>}
      <p className="hint">
        Run demo:{" "}
        <code>docker compose --profile demo up simulator</code>
      </p>
    </section>
  );
}
