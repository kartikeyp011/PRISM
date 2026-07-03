import type { AlertItem } from "../api/client";

export interface SelectedFeature {
  layer: "zones" | "sensors" | "workers" | "permits" | "cameras";
  properties: Record<string, unknown>;
}

interface Props {
  feature: SelectedFeature | null;
  alerts: AlertItem[];
  readings: { sensor_type: string; value: number; unit: string; timestamp: string }[];
  onClose: () => void;
}

export default function MapDetailDrawer({
  feature,
  alerts,
  readings,
  onClose,
}: Props) {
  if (!feature) return null;

  const { layer, properties } = feature;
  const zoneAlerts = alerts.filter(
    (a) => a.zone_id === properties.zone_id
  );

  return (
    <aside className="map-drawer">
      <header>
        <h3>{layer.slice(0, -1)} detail</h3>
        <button type="button" onClick={onClose} aria-label="Close drawer">
          ×
        </button>
      </header>

      {layer === "zones" && (
        <dl>
          <dt>Name</dt>
          <dd>{String(properties.name)}</dd>
          <dt>Type</dt>
          <dd>{String(properties.zone_type)}</dd>
          <dt>Risk level</dt>
          <dd>{String(properties.risk_level)}</dd>
        </dl>
      )}

      {layer === "sensors" && (
        <dl>
          <dt>Sensor</dt>
          <dd>{String(properties.sensor_type)}</dd>
          <dt>Reading</dt>
          <dd>
            {properties.value != null
              ? `${properties.value} ${properties.unit}`
              : "No data"}
          </dd>
          <dt>Status</dt>
          <dd>{String(properties.status)}</dd>
        </dl>
      )}

      {layer === "workers" && (
        <dl>
          <dt>Worker ID</dt>
          <dd>{String(properties.worker_id)}</dd>
          <dt>Recorded</dt>
          <dd>{new Date(String(properties.recorded_at)).toLocaleString()}</dd>
        </dl>
      )}

      {layer === "permits" && (
        <dl>
          <dt>Permit</dt>
          <dd>{String(properties.permit_id)}</dd>
          <dt>Type</dt>
          <dd>{String(properties.permit_type)}</dd>
          <dt>Status</dt>
          <dd>{String(properties.status)}</dd>
        </dl>
      )}

      {layer === "cameras" && (
        <>
          <dl>
            <dt>Camera</dt>
            <dd>{String(properties.name)}</dd>
            <dt>Status</dt>
            <dd>{String(properties.status)}</dd>
            <dt>Hazard status</dt>
            <dd>{String(properties.hazard_status ?? "normal")}</dd>
            {properties.last_analyzed_at != null && (
              <>
                <dt>Last analyzed</dt>
                <dd>
                  {new Date(String(properties.last_analyzed_at)).toLocaleString()}
                </dd>
              </>
            )}
          </dl>
          {Array.isArray(properties.last_hazards) &&
            (properties.last_hazards as { type: string; severity: string; message: string }[])
              .length > 0 && (
              <section>
                <h4>CV hazards</h4>
                <ul>
                  {(properties.last_hazards as { type: string; severity: string; message: string }[]).map(
                    (h) => (
                      <li key={h.type}>
                        {h.type} — {h.severity}
                      </li>
                    )
                  )}
                </ul>
              </section>
            )}
        </>
      )}

      {readings.length > 0 && (
        <section>
          <h4>Zone readings</h4>
          <ul>
            {readings.map((r) => (
              <li key={r.sensor_type}>
                {r.sensor_type}: {r.value}
                {r.unit}
              </li>
            ))}
          </ul>
        </section>
      )}

      {zoneAlerts.length > 0 && (
        <section>
          <h4>Linked alerts</h4>
          <ul>
            {zoneAlerts.map((a) => (
              <li key={a.alert_id}>
                {a.rule_id} — {a.severity}
              </li>
            ))}
          </ul>
        </section>
      )}
    </aside>
  );
}
