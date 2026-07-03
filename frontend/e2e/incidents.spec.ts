import { expect, test } from "@playwright/test";
import { gotoApp } from "./helpers";

test.describe("Incidents / RAG", () => {
  test.beforeEach(async ({ page }) => {
    await gotoApp(page);
    await page.getByRole("button", { name: "Incidents" }).click();
  });

  test("shows incident intelligence chat UI", async ({ page }) => {
    await expect(page.getByRole("heading", { name: "Incident Intelligence" })).toBeVisible();
    await expect(
      page.getByPlaceholder("Ask about SOPs, OSHA rules, or past incidents…")
    ).toBeVisible();
    await expect(page.getByRole("button", { name: "Ask" })).toBeVisible();
    await expect(
      page.getByText("Ask a compliance or incident question to get started.")
    ).toBeVisible();
  });

  test("example question triggers assistant response when backend is up", async ({
    page,
    request,
  }) => {
    const health = await request
      .get("http://localhost:8000/api/v1/health")
      .catch(() => null);
    test.skip(!health?.ok(), "Backend not running on :8000");

    const example = page.getByRole("button", {
      name: /hot work permit requirements/i,
    });
    await example.click();

    await expect(page.getByText("Searching knowledge base…")).toBeVisible();
    await expect(page.getByText("You")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText("PRISM")).toBeVisible({ timeout: 15_000 });
  });
});
