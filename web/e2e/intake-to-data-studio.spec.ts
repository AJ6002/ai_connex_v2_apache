import { expect, test } from '@playwright/test';

/**
 * Sprint 4 — first vertical slice E2E spec (reserved in Sprint 1, authored here).
 *
 * Proves the proven contract layer (Sprint 1) + design system (Sprint 2) +
 * product structure (Sprint 3) come together into a working user journey,
 * end to end, against the MSW mock layer:
 *
 *   Intake (submit an Intent)
 *     -> Job tracking (real Job status polling, Artifact Package state)
 *     -> Data Studio Brain (renders the plan-selected stage)
 *
 * This is the Sprint 4 acceptance gate from the migration plan (§5, Sprint 4
 * success criteria) — not a smoke test, an actual walk of the slice.
 */

test.describe('Intake -> Job -> Data Studio (first vertical slice)', () => {
  test('submitting an intent from Intake leads to a trackable Job', async ({ page }) => {
    await page.goto('/intake');

    // The faithful Intake screen renders (proves routing + AppShell + mocks are live).
    await expect(page.getByRole('heading', { name: 'Asset Registration' })).toBeVisible();
    await expect(page.getByText('DROP_ZONE_ALPHA')).toBeVisible();

    // Submitting drives narrowIntent -> submitParseJob against the mock layer,
    // then navigates to the resulting job.
    await page.getByRole('button', { name: 'Browse Local Files' }).click();
    await page.waitForURL(/\/jobs\/.+/);

    // The Job screen renders real status/stage data from the mock, not a blank page.
    await expect(page.getByText(/JOB ID:/)).toBeVisible();
    await expect(page.getByText('EXECUTION PIPELINE')).toBeVisible();
  });

  test('a running job renders its live pipeline and log console', async ({ page }) => {
    await page.goto('/jobs/job_running');

    await expect(page.getByText('JOB ID: JOB-8294')).toBeVisible();
    await expect(page.getByText('LIVE EXECUTION LOGS (FASTAPI)')).toBeVisible();
    // Every Artifact/Job status has a distinct treatment (plan §9.4) — RUNNING
    // shows the streaming indicator, not a generic success state.
    await expect(page.getByText('STREAMING')).toBeVisible();
  });

  test('a completed job shows its artifacts as ready', async ({ page }) => {
    await page.goto('/jobs/job_completed');

    await expect(page.getByText('ARTIFACTS READY')).toBeVisible();
  });

  test('a job awaiting clarification can be resolved', async ({ page }) => {
    await page.goto('/jobs/job_clarify');

    await expect(page.getByText('CLARIFICATION REQUIRED')).toBeVisible();
    await page.getByRole('button', { name: 'event_time' }).click();

    // Resolving routes back through the same job — status updates, banner clears.
    await expect(page.getByText('CLARIFICATION REQUIRED')).not.toBeVisible();
  });

  test('Data Studio Brain renders the plan-selected profiling stage', async ({ page }) => {
    await page.goto('/data-studio');

    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Machine Ready' })).toBeVisible();
    await expect(page.getByText('1. STRUCTURAL PROFILE')).toBeVisible();

    // The Discovery stage in the breadcrumb links into the segmentation review —
    // proves the slice extends coherently, not just three isolated pages.
    await page.getByRole('link', { name: /Discovery/ }).click();
    await expect(page.getByRole('heading', { name: 'Discovery & Segmentation' })).toBeVisible();
  });
});
