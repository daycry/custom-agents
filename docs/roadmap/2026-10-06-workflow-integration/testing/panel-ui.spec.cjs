const { test, expect } = require('@playwright/test');
const { pathToFileURL } = require('node:url');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '../../../..');
const registry = JSON.parse(fs.readFileSync(path.join(root, 'agent-kits/shared/capability-catalog.json'), 'utf8'));

test.beforeEach(async ({ page }) => {
  await page.goto(pathToFileURL(process.env.PANEL_HTML).href);
});

test('P-01 totals match source files, visible cards and no JS errors', async ({ page }) => {
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.reload();
  const counts = (await page.locator('.stat strong').allTextContents()).map(Number);
  const files = directory => fs.readdirSync(path.join(root, directory));
  expect(counts.slice(0, 3)).toEqual([
    files('agents').filter(name => name.endsWith('.md')).length,
    files('skills').filter(name => fs.existsSync(path.join(root, 'skills', name, 'SKILL.md'))).length,
    files('commands').filter(name => name.endsWith('.md')).length,
  ]);
  const total = counts.reduce((sum, n) => sum + n, 0);
  await expect(page.locator('.card:visible')).toHaveCount(total);
  await expect(page.locator('#results')).toHaveText(`${total} capacidades visibles`);
  expect(errors).toEqual([]);
  const hooks = JSON.parse(fs.readFileSync(path.join(root, 'hooks/hooks.json'), 'utf8')).hooks;
  const events = Object.keys(hooks).filter(event => hooks[event].some(group => group.hooks.length));
  expect(counts[4]).toBe(events.length);
  await expect(page.locator('.card[data-kind="hooks"]')).toHaveCount(events.length);
  const postToolUse = page.locator('.card[data-kind="hooks"]').filter({ has: page.locator('h2', { hasText: /^PostToolUse$/ }) });
  await expect(postToolUse).toHaveCount(1);
  await expect(postToolUse.locator('li')).toHaveCount(hooks.PostToolUse.reduce((sum, group) => sum + group.hooks.length, 0));
});

test('P-02 search, filter and clearing restore the source catalog', async ({ page }) => {
  const total = await page.locator('.card:visible').count();
  await page.locator('#search').fill('stack-practices');
  await page.locator('#kind').selectOption('skills');
  await expect(page.locator('.card:visible')).toHaveCount(1);
  await expect(page.locator('.card:visible h2')).toHaveText('stack-practices');
  await page.locator('#search').fill('');
  await expect(page.locator('.card:visible')).toHaveCount(fs.readdirSync(path.join(root, 'skills')).filter(name => fs.existsSync(path.join(root, 'skills', name, 'SKILL.md'))).length);
  await page.locator('#kind').selectOption('all');
  await expect(page.locator('.card:visible')).toHaveCount(total);
});

test('P-03 roles show native responsibilities, matching guides and optional memory sources', async ({ page }) => {
  const roles = fs.readdirSync(path.join(root, 'agents')).filter(name => name.endsWith('.md')).map(name => name.slice(0, -3));
  await expect(page.locator('.workflow-role')).toHaveCount(roles.length);
  for (const role of roles) {
    const row = page.locator(`.workflow-role[data-role="${role}"]`);
    await expect(row.locator('h3')).toHaveText(role);
    await row.locator('summary').click();
    expect((await row.locator('.responsibility').innerText()).length).toBeGreaterThan(30);
    await expect(row.locator('.responsibility')).not.toContainText('unavailable');
    const guides = registry.capabilities.filter(entry => entry.roles.includes(role)).map(entry => entry.id).sort();
    await expect(row.locator('.guide-chip')).toHaveText(guides);
  }
  await expect(page.locator('#workflow')).toContainText('no acredita ejecución');
  await page.locator('#source-notes summary').click();
  const sources = JSON.parse(await page.locator('#source-notes pre').innerText());
  expect(sources.memory.graphify_artifact).toBe(fs.existsSync(path.join(root, 'graphify-out/graph.json')) ? 'present' : 'absent');
  await expect(page.locator('footer')).toContainText('dashboard del roadmap');
});

test('P-04 mobile controls and role guides have no horizontal overflow', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.locator('#search')).toBeVisible();
  await expect(page.locator('#kind')).toBeVisible();
  await page.locator('#kind').selectOption('agents');
  await page.locator('#search').fill('architect');
  await expect(page.locator('.card:visible')).toHaveCount(1);
  await page.locator('.workflow-role[data-role="architect"]').scrollIntoViewIfNeeded();
  await page.locator('.workflow-role[data-role="architect"] summary').click();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: process.env.PANEL_SCREENSHOT, fullPage: true });
});

test('P-05 hook actions expose useful purposes and filters work from the keyboard', async ({ page }) => {
  await page.locator('#kind').selectOption('hooks');
  await page.locator('#search').focus();
  await page.keyboard.type('PostToolUse');
  const hook = page.locator('.card:visible');
  await expect(hook).toHaveCount(1);
  await expect(hook.locator('li strong')).toHaveText(['Documentación pendiente', 'Validación del ledger', 'Progreso de la iniciativa']);
  await expect(hook).toContainText('Confluence');
  await expect(hook).toContainText('Write · Edit · MultiEdit');
  await expect(hook).not.toContainText('not declared');
  await page.screenshot({ path: path.join(root, 'scratchpad/.venv/panel-preview/workflow-desktop.png'), fullPage: true });
});

test('P-06 navigation selection follows clicks, keyboard and browser history', async ({ page }) => {
  const catalog = page.locator('.sidebar nav a[href="#catalog"]');
  const workflow = page.locator('.sidebar nav a[href="#workflow"]');
  const sources = page.locator('.sidebar nav a[href="#source-notes"]');
  await expect(catalog).toHaveAttribute('aria-current', 'location');
  await workflow.click();
  await expect(workflow).toHaveAttribute('aria-current', 'location');
  await expect(catalog).not.toHaveAttribute('aria-current', 'location');
  await sources.focus();
  await page.keyboard.press('Enter');
  await expect(sources).toHaveAttribute('aria-current', 'location');
  await expect(workflow).not.toHaveAttribute('aria-current', 'location');
  await page.goBack();
  await expect(workflow).toHaveAttribute('aria-current', 'location');
  await expect(sources).not.toHaveAttribute('aria-current', 'location');
});

test('P-07 each workflow stage selects its content and opens the native role', async ({ page }) => {
  for (const [stage, role] of [['Descubrir', 'analyst'], ['Diseñar', 'architect'], ['Planificar', 'planner'], ['Construir', 'implementer'], ['Revisar', 'reviewer'], ['Validar', 'qa']]) {
    const button = page.getByRole('button', { name: stage, exact: true });
    await button.click();
    await expect(button).toHaveAttribute('aria-pressed', 'true');
    await expect(page.locator('.flow-steps button[aria-pressed="true"]')).toHaveCount(1);
    await expect(page.locator('.flow-detail:visible')).toHaveCount(1);
    await expect(page.locator(`.flow-detail:visible a[href="#role-${role}"]`)).toBeVisible();
  }
  await page.locator('.flow-detail:visible a[href="#role-qa"]').click();
  await expect(page.locator('#role-qa details')).toHaveAttribute('open', '');
  await expect(page.locator('.sidebar nav a[href="#workflow"]')).toHaveAttribute('aria-current', 'location');
});
