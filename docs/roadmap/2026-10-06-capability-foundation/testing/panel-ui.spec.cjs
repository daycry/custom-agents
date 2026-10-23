const { test, expect } = require('@playwright/test');
const { pathToFileURL } = require('node:url');

test.beforeEach(async ({ page }) => {
  await page.goto(pathToFileURL(process.env.PANEL_HTML).href);
});

test('P-01 catalog totals match visible cards and no JS errors', async ({ page }) => {
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  await page.reload();
  const counts = await page.locator('.stat strong').allTextContents();
  const expected = counts.reduce((sum, n) => sum + Number(n), 0);
  await expect(page.locator('.card:visible')).toHaveCount(expected);
  await expect(page.locator('#results')).toHaveText(`${expected} capabilities shown`);
  expect(errors).toEqual([]);
});

test('P-02 search selects matching capability cards', async ({ page }) => {
  await page.locator('#search').fill('plugin-panel');
  const cards = page.locator('.card:visible');
  expect(await cards.count()).toBeGreaterThan(0);
  for (const text of await cards.allTextContents()) expect(text.toLowerCase()).toContain('plugin-panel');
  await expect(page.locator('#results')).toHaveText(`${await cards.count()} capabilities shown`);
});

test('P-03 type filter and reset restore the catalog', async ({ page }) => {
  const total = await page.locator('.card:visible').count();
  await page.locator('#kind').selectOption('skills');
  const kinds = await page.locator('.card:visible').evaluateAll(cards => cards.map(c => c.dataset.kind));
  expect(kinds.length).toBeGreaterThan(0);
  expect(kinds.every(kind => kind === 'skills')).toBe(true);
  await page.locator('#kind').selectOption('all');
  await expect(page.locator('.card:visible')).toHaveCount(total);
});

test('P-04 mobile controls remain usable without horizontal overflow', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.locator('#search')).toBeVisible();
  await expect(page.locator('#kind')).toBeVisible();
  await page.locator('#kind').selectOption('agents');
  await page.locator('#search').fill('architect');
  await expect(page.locator('.card:visible')).toHaveCount(1);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({ path: process.env.PANEL_SCREENSHOT, fullPage: true });
});
