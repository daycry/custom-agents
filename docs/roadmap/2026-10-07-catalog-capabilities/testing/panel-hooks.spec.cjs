const { test, expect } = require('@playwright/test');
const { pathToFileURL } = require('node:url');
const fs = require('node:fs');

const inventory = JSON.parse(fs.readFileSync(process.env.PANEL_JSON, 'utf8'));
const groups = runtime => new Set(inventory.hooks.filter(hook => runtime === 'all' || hook.runtime === runtime).map(hook => `${hook.runtime}:${hook.event}`)).size;

test.beforeEach(async ({ page }) => {
  await page.goto(pathToFileURL(process.env.PANEL_HTML).href);
});

test('H-01 hook groups and handler counts match runtime declarations', async ({ page }) => {
  const errors = [];
  const network = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('request', request => { if (/^https?:/.test(request.url())) network.push(request.url()); });
  await page.reload();
  expect(Number(await page.locator('.stat strong').nth(4).innerText())).toBe(groups('all'));
  await expect(page.locator('[data-kind="hooks"]')).toHaveCount(groups('all'));
  await expect(page.locator('.hook-handlers > li')).toHaveCount(inventory.counts.hooks);
  await page.locator('#source-notes summary').click();
  const sources = JSON.parse(await page.locator('#source-notes pre').innerText());
  expect(sources.hook_handlers).toBe(inventory.counts.hooks);
  expect(sources.hook_groups).toBe(groups('all'));
  expect(sources.hook_sources).toEqual(inventory.hook_sources);
  expect(errors).toEqual([]);
  expect(network).toEqual([]);
});

test('H-02 runtime filters separate PostToolUse without losing actions', async ({ page }) => {
  await page.locator('#kind').selectOption('hooks');
  for (const runtime of ['claude-code', 'codex', 'opencode']) {
    await page.locator('#hook-runtime').selectOption(runtime);
    await expect(page.locator('#catalog .card:visible')).toHaveCount(groups(runtime));
    for (const item of await page.locator('#catalog .card:visible').all()) await expect(item).toHaveAttribute('data-runtime', runtime);
    await page.locator('#search').fill('PostToolUse');
    await expect(page.locator('#catalog .card:visible')).toHaveCount(1);
    await expect(page.locator('.card:visible .hook-handlers > li')).toHaveCount(3);
    await expect(page.locator('.card:visible li strong')).toHaveText(['Documentación pendiente', 'Validación del ledger', 'Progreso de la iniciativa']);
    await page.locator('#search').fill('');
  }
  await page.locator('#hook-runtime').selectOption('all');
  await expect(page.locator('#catalog .card:visible')).toHaveCount(groups('all'));
});

test('H-03 budgets show provenance, identities and limits', async ({ page }) => {
  await page.locator('#kind').selectOption('hooks');
  await page.locator('#search').fill('SessionEnd');
  const codex = page.locator('#catalog .card:visible[data-runtime="codex"]');
  const claude = page.locator('#catalog .card:visible[data-runtime="claude-code"]');
  const opencode = page.locator('#catalog .card:visible[data-runtime="opencode"]');
  await expect(codex).toContainText('Timeout: 3 s');
  await expect(claude).toContainText('Timeout: 5 s');
  await expect(opencode).toContainText('Supervisión del adapter: 20000 ms');
  await opencode.locator('summary').click();
  await expect(opencode).toContainText('no equivale a un timeout de registro');
  await expect(opencode).toContainText('session.execution.succeeded');
  await expect(opencode).toContainText('not a teardown hook');
  await page.locator('#search').fill('PreToolUse');
  for (const runtime of ['claude-code', 'codex', 'opencode']) {
    const card = page.locator(`#catalog .card:visible[data-runtime="${runtime}"]`);
    await expect(card.locator('li strong')).toHaveText(['Guardia de roles']);
    await card.locator('summary').click();
    const ids = inventory.hooks.find(hook => hook.runtime === runtime && hook.behavior === 'guard').role_ids;
    for (const id of ids) await expect(card).toContainText(id);
    await expect(card).toContainText('Carga sin verificar');
  }
});

test('H-04 action links restore filters, focus and browser history', async ({ page }) => {
  const own = inventory.hooks.find(hook => hook.runtime === 'codex' && hook.event === 'SessionEnd');
  await page.goto(pathToFileURL(process.env.PANEL_HTML).href + '#' + own.id);
  await expect(page.locator('#kind')).toHaveValue('hooks');
  await expect(page.locator('#hook-runtime')).toHaveValue('codex');
  await expect(page.locator('#' + own.id)).toBeFocused();
  await expect(page.locator('#' + own.id + ' details')).toHaveAttribute('open', '');
  const workflow = page.locator('.sidebar nav a[href="#workflow"]');
  await workflow.click();
  await expect(workflow).toHaveAttribute('aria-current', 'location');
  const source = page.locator('.sidebar nav a[href="#source-notes"]');
  await source.focus();
  await page.keyboard.press('Enter');
  await expect(source).toHaveAttribute('aria-current', 'location');
  await expect(page.locator('#source-notes')).toBeFocused();
  await page.goBack();
  await expect(workflow).toHaveAttribute('aria-current', 'location');
  await page.goBack();
  await expect(page.locator('#' + own.id)).toBeFocused();
});

test('H-05 unknown fragment reports a limit without a JavaScript error', async ({ page }) => {
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto(pathToFileURL(process.env.PANEL_HTML).href + '#missing-hook');
  await expect(page.locator('#navigation-status')).not.toBeEmpty();
  await expect(page.locator('.sidebar nav a[aria-current="location"]')).toHaveCount(1);
  expect(errors).toEqual([]);
});

test('H-06 all six workflow stages select their own content', async ({ page }) => {
  for (const [label, role] of [['Descubrir', 'analyst'], ['Diseñar', 'architect'], ['Planificar', 'planner'], ['Construir', 'implementer'], ['Revisar', 'reviewer'], ['Validar', 'qa']]) {
    const button = page.getByRole('button', { name: label, exact: true });
    await button.focus();
    await page.keyboard.press('Enter');
    await expect(button).toHaveAttribute('aria-pressed', 'true');
    await expect(page.locator('.flow-detail:visible')).toHaveCount(1);
    await expect(page.locator(`.flow-detail:visible a[href="#role-${role}"]`)).toBeVisible();
  }
});

test('H-07 mobile Sources and runtime controls stay reachable without overflow', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  const sources = page.locator('.sidebar nav a[href="#source-notes"]');
  await expect(sources).toBeVisible();
  await sources.click();
  await expect(page.locator('#source-notes')).toBeFocused();
  await page.locator('.sidebar nav a[href="#catalog"]').click();
  await page.locator('#kind').selectOption('hooks');
  await page.locator('#hook-runtime').selectOption('codex');
  await expect(page.locator('#catalog .card:visible')).toHaveCount(groups('codex'));
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: process.env.PANEL_SCREENSHOT, fullPage: true });
});

test('H-08 reduced motion and skip link remain operable', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
  expect(await page.evaluate(() => getComputedStyle(document.documentElement).scrollBehavior)).toBe('auto');
  await page.locator('.skip-link').focus();
  await page.keyboard.press('Enter');
  await expect(page.locator('#main')).toBeFocused();
});

test('H-09 extension runtime filtering stays independent of hook filtering', async ({ page }) => {
  const cards = page.locator('#extensions .card:visible');
  const total = inventory.extensions.pieces.length;
  expect(total).toBeGreaterThan(2);
  const bundleBefore = await page.locator('#catalog .card:visible').count();
  for (const runtime of ['claude-code', 'codex', 'opencode']) {
    await page.locator('#extension-runtime').selectOption(runtime);
    const expected = inventory.extensions.pieces.filter(piece => piece.runtime === runtime).length;
    expect(expected).toBeGreaterThan(0);
    await expect(cards).toHaveCount(expected);
    for (const card of await cards.all()) await expect(card).toHaveAttribute('data-runtime', runtime);
    await expect(page.locator('#catalog .card:visible')).toHaveCount(bundleBefore);
  }
  await page.locator('#extension-runtime').selectOption('all');
  await expect(cards).toHaveCount(total);
  await page.locator('#kind').selectOption('hooks');
  await page.locator('#hook-runtime').selectOption('codex');
  await expect(cards).toHaveCount(total);
  await expect(page.locator('#catalog .card:visible')).toHaveCount(groups('codex'));
  expect(await page.content()).not.toContain('PRIVATE BODY');
});
