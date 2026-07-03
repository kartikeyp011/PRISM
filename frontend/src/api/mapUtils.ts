import { describe, expect, it } from "vitest";
import type { GeoJsonFeatureCollection } from "./client";

export function isValidFeatureCollection(fc: GeoJsonFeatureCollection): boolean {
  return fc.type === "FeatureCollection" && Array.isArray(fc.features);
}

describe("GeoJSON validation", () => {
  it("accepts valid FeatureCollection", () => {
    expect(
      isValidFeatureCollection({ type: "FeatureCollection", features: [] })
    ).toBe(true);
  });

  it("rejects invalid structure", () => {
    expect(
      isValidFeatureCollection({ type: "Feature", features: [] } as never)
    ).toBe(false);
  });
});
