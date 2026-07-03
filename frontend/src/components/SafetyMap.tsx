import L from "leaflet";
import { GeoJSON, MapContainer, TileLayer } from "react-leaflet";
import type { Layer, PathOptions } from "leaflet";
import type {
  GeoJsonFeatureCollection,
  MapLayersResponse,
} from "../api/client";
import type { SelectedFeature } from "./MapDetailDrawer";

interface LayerVisibility {
  zones: boolean;
  sensors: boolean;
  workers: boolean;
  permits: boolean;
  cameras: boolean;
}

interface Props {
  layers: MapLayersResponse | null;
  visibility: LayerVisibility;
  riskColors: Record<string, string>;
  sensorColors: Record<string, string>;
  cvHazardColors: Record<string, string>;
  onSelect: (feature: SelectedFeature) => void;
}

const DEFAULT_CENTER: [number, number] = [37.7745, -122.4175];
const DEFAULT_ZOOM = 16;

function bindClick(
  layerType: SelectedFeature["layer"],
  onSelect: (f: SelectedFeature) => void
) {
  return (feature: GeoJSON.Feature, layer: Layer) => {
    layer.on("click", () => {
      onSelect({
        layer: layerType,
        properties: feature.properties as Record<string, unknown>,
      });
    });
  };
}

export default function SafetyMap({
  layers,
  visibility,
  riskColors,
  sensorColors,
  cvHazardColors,
  onSelect,
}: Props) {
  const zoneStyle = (feature?: GeoJSON.Feature): PathOptions => {
    const level = String(feature?.properties?.risk_level ?? "LOW");
    const color = riskColors[level] ?? riskColors.LOW;
    return {
      fillColor: color,
      fillOpacity: 0.35,
      color,
      weight: 2,
    };
  };

  const pointToLayer = (
    _feature: GeoJSON.Feature,
    latlng: L.LatLng,
    color: string
  ) => {
    return L.circleMarker(latlng, {
      radius: 8,
      fillColor: color,
      color: "#fff",
      weight: 1,
      fillOpacity: 0.9,
    });
  };

  const renderPoints = (
    data: GeoJsonFeatureCollection | undefined,
    layerType: SelectedFeature["layer"],
    colorFn: (props: Record<string, unknown>) => string
  ) => {
    if (!data || data.features.length === 0) return null;
    return (
      <GeoJSON
        key={`${layerType}-${data.features.length}`}
        data={data as GeoJSON.GeoJSON}
        pointToLayer={(feature, latlng) =>
          pointToLayer(
            feature,
            latlng,
            colorFn(feature.properties as Record<string, unknown>)
          )
        }
        onEachFeature={bindClick(layerType, onSelect)}
      />
    );
  };

  return (
    <MapContainer
      center={DEFAULT_CENTER}
      zoom={DEFAULT_ZOOM}
      className="leaflet-map"
      scrollWheelZoom
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {visibility.zones && layers?.layers.zones && (
        <GeoJSON
          key={`zones-${layers.layers.zones.features.length}`}
          data={layers.layers.zones as GeoJSON.GeoJSON}
          style={zoneStyle}
          onEachFeature={bindClick("zones", onSelect)}
        />
      )}
      {visibility.sensors &&
        renderPoints(layers?.layers.sensors, "sensors", (p) =>
          sensorColors[String(p.status)] ?? sensorColors.unknown
        )}
      {visibility.workers &&
        renderPoints(layers?.layers.workers, "workers", () => "#a855f7")}
      {visibility.permits &&
        renderPoints(layers?.layers.permits, "permits", () => "#06b6d4")}
      {visibility.cameras &&
        renderPoints(layers?.layers.cameras, "cameras", (p) =>
          String(p.fill_color ?? cvHazardColors[String(p.hazard_status ?? "normal")] ?? "#22c55e")
        )}
    </MapContainer>
  );
}
