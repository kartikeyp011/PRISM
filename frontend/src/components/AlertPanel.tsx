import { useCallback, useEffect, useState } from "react";
import {
  acknowledgeAlert,
  fetchActiveAlerts,
  fetchRiskActive,
  type AlertItem,
  type RiskAssessment,
  WS_PATH,
  WS_BASE,
} from "../api/client";

const SEVERITY_CLASS: Record<string, string> = {
  LOW: "severity-low",
  MEDIUM: "severity-medium",
  HIGH: "severity-high",
  CRITICAL: "severity-critical",
};

interface Props {
  compact?: boolean;
}

export default function AlertPanel({ compact = false }: Props) {
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [riskSummary, setRiskSummary] = useState<RiskAssessment[]>([]);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(() => {
    Promise.all([fetchActiveAlerts(), fetchRiskActive()])
      .then(([alertData, riskData]) => {
        setAlerts(alertData.alerts);
        setRiskSummary(
          riskData.assessments.filter((a) =>
            ["HIGH", "CRITICAL"].includes(a.risk_level)
          )
        );
        setError(null);
      })
      .catch((err: Error) => setError(err.message));
  }, []);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 8000);
    return () => clearInterval(interval);
  }, [refresh]);

  useEffect(() => {
    let ws: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout>;

    const connect = () => {
      ws = new WebSocket(`${WS_BASE}${WS_PATH}`);
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.event === "alert.created") {
          setAlerts((prev) => {
            const exists = prev.some((a) => a.alert_id === data.alert_id);
            if (exists) return prev;
            return [
              {
                alert_id: data.alert_id,
                zone_id: data.zone_id,
                rule_id: data.rule_id,
                severity: data.severity,
                status: data.status,
                message: data.message,
                created_at: data.created_at,
              },
              ...prev,
            ];
          });
        }
        if (data.event === "alert.updated") {
          setAlerts((prev) =>
            prev.filter((a) => a.alert_id !== data.alert_id)
          );
        }
        if (data.event === "risk.changed") {
          refresh();
        }
      };
      ws.onclose = () => {
        reconnectTimer = setTimeout(connect, 3000);
      };
      ws.onopen = () => {
        ws?.send("ping");
      };
    };

    connect();
    return () => {
      clearTimeout(reconnectTimer);
      ws?.close();
    };
  }, [refresh]);

  const handleAck = async (alertId: string) => {
    try {
      await acknowledgeAlert(alertId);
      setAlerts((prev) => prev.filter((a) => a.alert_id !== alertId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ack failed");
    }
  };

  return (
    <section className={`alert-panel ${compact ? "alert-strip" : "status-card"}`}>
      {!compact && <h2>Alerts</h2>}
      {compact && alerts.length > 0 && (
        <span className="alert-strip-label">Active alerts:</span>
      )}
      {error && <p className="error">{error}</p>}

      {!compact && (
        <div className="risk-summary">
          <h3>Active Risk</h3>
          {riskSummary.length === 0 ? (
            <p className="muted">No elevated zones</p>
          ) : (
            <ul>
              {riskSummary.map((r) => (
                <li key={r.assessment_id} className={SEVERITY_CLASS[r.risk_level]}>
                  {r.rule_id} — {r.risk_level} (zone {r.zone_id.slice(0, 8)}…)
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      <div className={compact ? "alert-strip-list" : "alert-list"}>
        {!compact && <h3>Active Alerts ({alerts.length})</h3>}
        {alerts.length === 0 ? (
          !compact && <p className="muted">No active alerts</p>
        ) : (
          alerts.map((alert) => (
            <article
              key={alert.alert_id}
              className={`alert-toast ${SEVERITY_CLASS[alert.severity] ?? ""}`}
            >
              <header>
                <strong>{alert.rule_id}</strong>
                <span>{alert.severity}</span>
              </header>
              {!compact && <p>{alert.message}</p>}
              <footer>
                {!compact && (
                  <time>{new Date(alert.created_at).toLocaleString()}</time>
                )}
                <button type="button" onClick={() => handleAck(alert.alert_id)}>
                  Ack
                </button>
              </footer>
            </article>
          ))
        )}
      </div>
    </section>
  );
}
