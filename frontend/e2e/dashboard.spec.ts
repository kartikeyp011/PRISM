import { expect, test } from "@playwright/test";
import { gotoApp } from "./helpers";

test.describe("Dashboard", () => {
  test("loads PRISM shell and dashboard content", async ({ page }) => {
    await gotoApp(page);
    await expect(page.getByRole("heading", { name: "PRISM", level: 1 })).toBeVisible();
    await expect(page.getByRole("button", { name: "Dashboard" })).toHaveClass(/nav-active/);
    await expect(page.getByRole("heading", { name: "System Status" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Ingestion Status" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Safety Map" })).toBeVisible();
  });

  test("navigation switches pages", async ({ page }) => {
    await gotoApp(page);
    await page.getByRole("button", { name: "Safety Map" }).click();
    await expect(page.getByRole("button", { name: "Safety Map" })).toHaveClass(/nav-active/);
    await expect(page.getByRole("heading", { name: "CCTV Analysis" })).toBeVisible();

    await page.getByRole("button", { name: "Incidents" }).click();
    await expect(page.getByRole("heading", { name: "Incident Intelligence" })).toBeVisible();

    await page.getByRole("button", { name: "Dashboard" }).click();
    await expect(page.getByRole("heading", { name: "System Status" })).toBeVisible();
  });
});
