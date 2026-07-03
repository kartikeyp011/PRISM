import { expect, test } from "@playwright/test";
import { gotoApp } from "./helpers";

test.describe("Safety Map", () => {
  test.beforeEach(async ({ page }) => {
    await gotoApp(page);
    await page.getByRole("button", { name: "Safety Map" }).click();
  });

  test("shows map panel and layer toggles", async ({ page }) => {
    await expect(page.getByRole("heading", { name: "Safety Map", level: 2 })).toBeVisible();
    await expect(page.locator(".layer-toggles label").filter({ hasText: "zones" })).toBeVisible();
    await expect(page.locator(".layer-toggles label").filter({ hasText: "cameras" })).toBeVisible();
    await expect(page.locator(".leaflet-map")).toBeVisible();
  });

  test("CCTV analysis panel is available", async ({ page }) => {
    await expect(page.getByRole("heading", { name: "CCTV Analysis" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Analyze frame" })).toBeVisible();
  });
});
