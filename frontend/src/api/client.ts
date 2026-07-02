/**
 * API client paths aligned with backend/api_contract.yaml
 */
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export const API_PATHS = {
  health: "/api/v1/health",
  ingestEvents: "/api/v1/ingest/events",
  sensorsLatest: "/api/v1/sensors/latest",
  riskActive: "/api/v1/risk/active",
  alertsAck: "/api/v1/alerts/ack",
  mapLayers: "/api/v1/map/layers",
  ragQuery: "/api/v1/rag/query",
} as const;

export const WS_PATH = "/ws/alerts";

export interface HealthResponse {
  status: string;
  version: string;
  llm_mode: string;
}

export interface SensorReading {
  sensor_id: string;
  zone_id: string;
  sensor_type: string;
  value: number;
  unit: string;
  timestamp: string;
}

export interface SensorsLatestResponse {
  readings: SensorReading[];
  count: number;
  events_ingested: number;
  last_event_at: string | null;
}

export const SCENARIOS = [
  { id: "compound_risk_demo", label: "Compound Risk Demo" },
] as const;

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE}${API_PATHS.health}`);
  if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
  return res.json();
}

export async function fetchSensorsLatest(
  zoneId?: string
): Promise<SensorsLatestResponse> {
  const params = zoneId ? `?zone_id=${encodeURIComponent(zoneId)}` : "";
  const res = await fetch(`${API_BASE}${API_PATHS.sensorsLatest}${params}`);
  if (!res.ok) throw new Error(`Sensors latest failed: ${res.status}`);
  return res.json();
}
