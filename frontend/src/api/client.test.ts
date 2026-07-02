import { describe, expect, it } from "vitest";
import { API_PATHS, SCENARIOS } from "./client";

describe("API client contract paths", () => {
  it("defines ingest and sensors endpoints", () => {
    expect(API_PATHS.ingestEvents).toBe("/api/v1/ingest/events");
    expect(API_PATHS.sensorsLatest).toBe("/api/v1/sensors/latest");
  });

  it("lists available demo scenarios", () => {
    expect(SCENARIOS.some((s) => s.id === "compound_risk_demo")).toBe(true);
  });
});
