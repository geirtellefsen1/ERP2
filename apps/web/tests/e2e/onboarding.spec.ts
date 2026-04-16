import { test, expect } from "@playwright/test";

test.describe("Onboarding wizard", () => {
  test.beforeEach(async ({ page }) => {
    // Mock the onboarding state API so tests don't depend on a running backend
    await page.route("**/api/v1/onboarding/state", async (route) => {
      const method = route.request().method();
      if (method === "GET") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            current_step: 1,
            step_data: null,
            completed_at: null,
            step_names: [
              "Agency Setup",
              "Invite Users",
              "Connect Bank",
              "Import Chart of Accounts",
              "First Client",
            ],
          }),
        });
      } else if (method === "PUT") {
        const body = route.request().postDataJSON();
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            current_step: body.current_step,
            step_data: body.step_data,
            completed_at: null,
            step_names: [
              "Agency Setup",
              "Invite Users",
              "Connect Bank",
              "Import Chart of Accounts",
              "First Client",
            ],
          }),
        });
      }
    });

    await page.goto("/onboarding");
  });

  test("loads and shows step 1 (Agency Setup)", async ({ page }) => {
    await expect(page.getByRole("heading", { name: "Agency Setup" })).toBeVisible();
    await expect(page.getByText("Step 1 of 5")).toBeVisible();
    await expect(page.getByLabel("Agency Name")).toBeVisible();
    await expect(page.getByLabel("Slug")).toBeVisible();
    await expect(page.getByText("Creates your agency workspace.")).toBeVisible();
  });

  test("clicking Continue advances to step 2 (Invite Users)", async ({ page }) => {
    await expect(page.getByRole("heading", { name: "Agency Setup" })).toBeVisible();

    await page.getByRole("button", { name: "Continue" }).click();

    await expect(page.getByRole("heading", { name: "Invite Users" })).toBeVisible();
    await expect(page.getByText("Step 2 of 5")).toBeVisible();
    await expect(page.getByRole("button", { name: "Add" })).toBeVisible();
  });
});
