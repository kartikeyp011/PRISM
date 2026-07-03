import { useCallback, useEffect, useState } from "react";
import {
  fetchActiveAlerts,
  fetchMapLayers,
  fetchSensorsLatest,
  type AlertItem,
  type MapLayersResponse,
  WS_BASE,
  WS_PATH,
} from "../api/client";
import { RISK_COLORS, SENSOR_COLORS } from "../constants/riskColors";
import MapDetailDrawer, { type SelectedFeature } from "./MapDetailDrawer";
import SafetyMap from "./SafetyMap";
import CvAnalysisPanel from "./CvAnalysisPanel";

interface LayerVisibility {
  zones: boolean;
  sensors: boolean;
  workers: boolean;
  permits: boolean;
  cameras: boolean;
}

interface Props {
  compact?: boolean;
  pollIntervalMs?: number;
}

export default function SafetyMapPanel({
  compact = false,
  pollIntervalMs = 10000,
}: Props) {
  const [layers, setLayers] = useState<MapLayersResponse | null>(null);
  const [visibility, setVisibility] = useState<LayerVisibility>({
    zones: true,
    sensors: true,
    workers: true,
    permits: true,
    cameras: true,
  });
  const [selected, setSelected] = useState<SelectedFeature | null>(null);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [readings, setReadings] = useState<
    { sensor_type: string; value: number; unit: string; timestamp: string }[]
  >([]);
  const [error, setError] = useState<string | null>(null);

  const loadLayers = useCallback(() => {
    fetchMapLayers()
      .then(setLayers)
      .catch((err: Error) => setError(err.message));
  }, []);

  useEffect(() => {
    loadLayers();
    fetchActiveAlerts()
      .then((d) => setAlerts(d.alerts))
      .catch(() => undefined);
    const timer = setInterval(loadLayers, pollIntervalMs);
    return () => clearInterval(timer);
  }, [loadLayers, pollIntervalMs]);

  useEffect(() => {
    let ws: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout>;

    const connect = () => {
      ws = new WebSocket(`${WS_BASE}${WS_PATH}`);
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.event === "risk.changed" || data.event === "alert.created") {
          loadLayers();
        }
      };
      ws.onclose = () => {
        reconnectTimer = setTimeout(connect, 5000);
      };
      ws.onopen = () => ws?.send("ping");
    };
    connect();
    return () => {
      clearTimeout(reconnectTimer);
      ws?.close();
    };
  }, [loadLayers]);

  useEffect(() => {
    if (!selected?.properties.zone_id) {
      setReadings([]);
      return;
    }
    fetchSensorsLatest(String(selected.properties.zone_id))
      .then((d) => setReadings(d.readings))
      .catch(() => setReadings([]));
  }, [selected]);

  const toggle = (key: keyof LayerVisibility) => {
    setVisibility((v) => ({ ...v, [key]: !v[key] }));
  };

  const isEmpty =
    layers &&
    Object.values(layers.layers).every((fc) => fc.features.length === 0);

  return (
    <section className={`map-panel ${compact ? "map-panel-compact" : ""}`}>
      <header className="map-panel-header">
        <h2>Safety Map</h2>
        <div className="layer-toggles">
          {(Object.keys(visibility) as (keyof LayerVisibility)[]).map((key) => (
            <label key={key}>
              <input
                type="checkbox"
                checked={visibility[key]}
                onChange={() => toggle(key)}
              />
              {key}
            </label>
          ))}
        </div>
      </header>

      {error && (
        <div className="map-error">
          {error}
          <button type="button" onClick={loadLayers}>
            Retry
          </button>
        </div>
      )}

      {isEmpty && !error && (
        <p className="map-empty">
          No map data yet — run{" "}
          <code>docker compose --profile demo up simulator</code>
        </p>
      )}

      <div className="map-container-wrap">
        <SafetyMap
          layers={layers}
          visibility={visibility}
          riskColors={layers?.risk_colors ?? RISK_COLORS}
          sensorColors={SENSOR_COLORS}
          cvHazardColors={layers?.cv_hazard_colors ?? {}}
          onSelect={setSelected}
        />
        <MapDetailDrawer
          feature={selected}
          alerts={alerts}
          readings={readings}
          onClose={() => setSelected(null)}
        />
      </div>

      {!compact && (
        <CvAnalysisPanel
          demoCameraId="66666666-6666-6666-6666-666666666666"
          onAnalyzed={loadLayers}
        />
      )}
    </section>
  );
}
