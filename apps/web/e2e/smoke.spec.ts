import { expect, test } from '@playwright/test';

/**
 * Smoke e2e for every page shell. The FastAPI backend is not running during
 * these tests, so data fetches land in error/empty states — the assertions
 * target the static shell (heading, nav, form controls) which must render
 * regardless of backend health.
 */

const NAV_TABS = ['Search', 'Trends', 'Journals', 'Institutions', 'Settings'];

test.beforeEach(async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveURL(/\/search$/);
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Elsevier Academic Explorer');
});

test('root redirects to the search page', async ({ page }) => {
  await expect(page).toHaveURL(/\/search$/);
});

test('nav exposes all five sections', async ({ page }) => {
  for (const label of NAV_TABS) {
    await expect(page.getByRole('tab', { name: label })).toBeVisible();
  }
});

test('search page renders the query form', async ({ page }) => {
  await expect(page.getByPlaceholder('machine learning for drug discovery')).toBeVisible();
});

test('trends page renders the research field form', async ({ page }) => {
  await page.getByRole('tab', { name: 'Trends' }).click();
  await expect(page).toHaveURL(/\/trends$/);
  await expect(page.getByText('Research field', { exact: true })).toBeVisible();
});

test('journals page renders the metrics lookup', async ({ page }) => {
  await page.getByRole('tab', { name: 'Journals' }).click();
  await expect(page).toHaveURL(/\/journals$/);
  await expect(page.locator('form, input').first()).toBeVisible();
});

test('institutions page renders the analysis form', async ({ page }) => {
  await page.getByRole('tab', { name: 'Institutions' }).click();
  await expect(page).toHaveURL(/\/institutions$/);
  await expect(page.getByText('Institution name', { exact: true })).toBeVisible();
});

test('settings page renders the credential form', async ({ page }) => {
  await page.getByRole('tab', { name: 'Settings' }).click();
  await expect(page).toHaveURL(/\/settings$/);
  await expect(page.getByText('API key', { exact: true })).toBeVisible();
});
