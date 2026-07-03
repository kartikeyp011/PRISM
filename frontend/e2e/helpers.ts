/** Shared Playwright helpers for PRISM E2E tests. */

import type { Page } from "@playwright/test";

/** Leaflet tile loads can block the window "load" event — use domcontentloaded. */
export async function gotoApp(page: Page, path = "/"): Promise<void> {
  await page.goto(path, { waitUntil: "domcontentloaded" });
}
