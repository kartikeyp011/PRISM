import { useCallback, useEffect, useState } from "react";
import {
  analyzeCvSample,
  fetchCvSamples,
  type CvAnalyzeResponse,
  type CvSampleItem,
} from "../api/client";

interface Props {
  demoCameraId?: string;
  onAnalyzed?: () => void;
}

export default function CvAnalysisPanel({ demoCameraId, onAnalyzed }: Props) {
  const [samples, setSamples] = useState<CvSampleItem[]>([]);
  const [selected, setSelected] = useState("no_ppe_worker");
  const [result, setResult] = useState<CvAnalyzeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchCvSamples()
      .then((d) => {
        setSamples(d.samples);
        if (d.samples.length > 0) {
          setSelected(d.samples[0].sample_id);
        }
      })
      .catch((err: Error) => setError(err.message));
  }, []);

  const runAnalysis = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await analyzeCvSample(selected, demoCameraId);
      setResult(response);
      onAnalyzed?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  }, [selected, demoCameraId, onAnalyzed]);

  return (
    <section className="cv-panel">
      <header>
        <h3>CCTV Analysis</h3>
        <span className="cv-mode-badge">
          {result?.cv_mode ?? "mock"} mode
        </span>
      </header>
      <p className="cv-panel-desc">
        Run demo frame analysis — results overlay on camera markers on the map.
      </p>

      {samples.length > 0 && (
        <label className="cv-sample-select">
          Demo sample
          <select
            value={selected}
            onChange={(e) => setSelected(e.target.value)}
            disabled={loading}
          >
            {samples.map((s) => (
              <option key={s.sample_id} value={s.sample_id}>
                {s.title}
              </option>
            ))}
          </select>
        </label>
      )}

      <button type="button" onClick={runAnalysis} disabled={loading || !selected}>
        {loading ? "Analyzing…" : "Analyze frame"}
      </button>

      {error && <p className="cv-error">{error}</p>}

      {result && (
        <div className="cv-results">
          <h4>
            Detections ({result.detections.length})
            {result.hazards.length > 0 && (
              <span className="cv-hazard-count">
                · {result.hazards.length} hazard
                {result.hazards.length !== 1 ? "s" : ""}
              </span>
            )}
          </h4>
          <ul>
            {result.detections.map((d) => (
              <li key={`${d.label}-${d.confidence}`}>
                {d.label}{" "}
                <span className="cv-confidence">
                  {(d.confidence * 100).toFixed(0)}%
                </span>
              </li>
            ))}
          </ul>
          {result.hazards.length > 0 && (
            <>
              <h4>Hazards</h4>
              <ul className="cv-hazards">
                {result.hazards.map((h) => (
                  <li key={h.type} className={`cv-hazard-${h.severity.toLowerCase()}`}>
                    <strong>{h.type}</strong> — {h.message}
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      )}
    </section>
  );
}
