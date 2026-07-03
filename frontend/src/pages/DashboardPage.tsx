import { useEffect, useState } from "react";
import { fetchHealth, type HealthResponse } from "../api/client";
import IngestionStatusPanel from "../components/IngestionStatusPanel";
import SafetyMapPanel from "../components/SafetyMapPanel";

export default function DashboardPage() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchHealth()
      .then(setHealth)
      .catch((err: Error) => setError(err.message));
  }, []);

  return (
    <div className="dashboard-layout">
      <div className="dashboard-side">
        <section className="status-card">
          <h2>System Status</h2>
          {error && <p className="error">API unreachable: {error}</p>}
          {health && (
            <ul>
              <li>Status: {health.status}</li>
              <li>Version: {health.version}</li>
              <li>LLM mode: {health.llm_mode}</li>
            </ul>
          )}
          {!health && !error && <p>Connecting to backend…</p>}
        </section>
        <IngestionStatusPanel />
      </div>
      <SafetyMapPanel compact />
    </div>
  );
}
