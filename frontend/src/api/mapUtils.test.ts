import { describe, expect, it } from "vitest";
import { isValidFeatureCollection } from "./mapUtils";

describe("mapUtils", () => {
  it("validates FeatureCollection for layer render", () => {
    expect(
      isValidFeatureCollection({
        type: "FeatureCollection",
        features: [
          {
            type: "Feature",
            geometry: { type: "Point", coordinates: [-122.4, 37.77] },
            properties: { sensor_type: "LEL" },
          },
        ],
      })
    ).toBe(true);
  });
});
