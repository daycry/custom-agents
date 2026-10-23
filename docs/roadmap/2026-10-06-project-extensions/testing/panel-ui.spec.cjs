const { test, expect } = require('@playwright/test');
const { execFileSync } = require('node:child_process');
const { pathToFileURL } = require('node:url');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const root = path.resolve(__dirname, '../../../..');
let temporary, pagePath, inventory, untouched, forbiddenSideEffect;
const write = (base, relative, content) => {
  const destination = path.join(base, relative);
  fs.mkdirSync(path.dirname(destination), { recursive: true });
  fs.writeFileSync(destination, content, 'utf8');
  return destination;
};

test.beforeAll(() => {
  temporary = fs.mkdtempSync(path.join(os.tmpdir(), 'custom-agents-panel-ext-'));
  const project = path.join(temporary, 'project'), home = path.join(temporary, 'user');
  fs.mkdirSync(project); fs.mkdirSync(home);
  untouched = [];
  for (const base of [project, home]) {
    const file = write(base, '.claude/agents/billing.md', '---\nname: billing\ndescription: Billing specialist\n---\nPRIVATE AGENT BODY\n');
    untouched.push([file, fs.readFileSync(file, 'utf8')]);
  }
  write(project, '.claude/agents/implementer.md', '---\nname: implementer\ndescription: Project specialist\n---\nPRIVATE BODY\n');
  write(project, '.claude/personas/billing.md', 'PRIVATE PERSONA BODY\n');
  write(project, '.agents/skills/tax/SKILL.md', '---\nname: tax\ndescription: Tax guidance\n---\nPRIVATE SKILL BODY\n');
  write(project, '.codex/agents/tax.toml', 'name="tax"\ndescription="Tax specialist"\ndeveloper_instructions="PRIVATE INSTRUCTIONS"\n');
  forbiddenSideEffect = path.join(temporary, 'must-not-exist');
  const program = 'require("node:fs").writeFileSync(' + JSON.stringify(forbiddenSideEffect) + ',"executed")';
  write(project, '.opencode/tools/invoice.ts', program);
  const config = write(project, '.mcp.json', JSON.stringify({ mcpServers: {
    ledger: { type: 'stdio', command: 'node', args: ['-e', program], env: { TOKEN: 'PRIVATE MCP TOKEN' } },
    remote: { type: 'http', url: 'https://example.test/PRIVATE_URL', headers: { Authorization: 'PRIVATE_AUTH' } },
  }}));
  untouched.push([config, fs.readFileSync(config, 'utf8')]);
  const preferences = write(home, '.claude.json', JSON.stringify({ projects: { [project]: { disabledMcpServers: ['ledger'] } } }));
  untouched.push([preferences, fs.readFileSync(preferences, 'utf8')]);
  pagePath = path.join(temporary, 'panel.html');
  const output = execFileSync(process.env.PYTHON || 'python', [
    path.join(root, 'skills/plugin-panel/scripts/build_panel.py'), '--root', root,
    '--project', project, '--home', home, '--html', pagePath, '--json',
  ], { encoding: 'utf8', timeout: 20000 });
  inventory = JSON.parse(output);
  expect(fs.existsSync(forbiddenSideEffect)).toBe(false);
});

test.afterAll(() => {
  if (!temporary) return;
  const resolved = path.resolve(temporary), relative = path.relative(os.tmpdir(), resolved);
  if (relative.startsWith('..') || path.isAbsolute(relative) || !path.basename(resolved).startsWith('custom-agents-panel-ext-')) {
    throw new Error('Refusing cleanup outside the owned temporary fixture');
  }
  fs.rmSync(resolved, { recursive: true, force: true });
});

test.beforeEach(async ({ page }) => { await page.goto(pathToFileURL(pagePath).href); });

test('P-01 three runtimes, origins and counts are distinct from the bundle', async ({ page }) => {
  const errors = []; page.on('pageerror', error => errors.push(error.message)); await page.reload();
  const counts = inventory.counts;
  expect((await page.locator('.stat strong').allTextContents()).map(Number)).toEqual([
    counts.agents, counts.skills, counts.commands, counts.tools, new Set(inventory.hooks.map(h => `${h.runtime}:${h.event}`)).size,
  ]);
  await expect(page.locator('#extensions .card')).toHaveCount(inventory.extensions.pieces.length);
  for (const runtime of ['claude-code', 'codex', 'opencode']) {
    expect(await page.locator(`#extensions [data-runtime="${runtime}"]`).count()).toBeGreaterThan(0);
  }
  await expect(page.locator('#extensions [data-scope="user"]')).toHaveCount(1);
  const card = page.locator('#extensions [data-kind="agent"]').filter({ has: page.getByRole('heading', { name: 'billing', exact: true }) }).first();
  await card.locator('summary').click();
  await expect(card.locator('details code').first()).toContainText('.claude/agents/billing.md');
  expect(errors).toEqual([]);
  await page.locator('#extensions').screenshot({ path: test.info().outputPath('desktop-extensions.png') });
});

test('P-02 origin and runtime filters preserve duplicates and bundle controls', async ({ page }) => {
  const initialBundle = await page.locator('#catalog .card:visible').count();
  await page.locator('#extension-kind').selectOption('agent');
  await page.locator('#extension-runtime').selectOption('claude-code');
  await page.locator('#extension-search').fill('billing');
  await expect(page.locator('#extensions .card:visible')).toHaveCount(2);
  await expect(page.locator('#extensions .card:visible').first()).toContainText('Nombre repetido');
  await page.locator('#extension-scope').selectOption('user');
  await expect(page.locator('#extensions .card:visible')).toHaveCount(1);
  await expect(page.locator('#extensions .card:visible')).toHaveAttribute('data-scope', 'user');
  await expect(page.locator('#catalog .card:visible')).toHaveCount(initialBundle);
  await page.locator('#search').fill('stack-practices'); await page.locator('#kind').selectOption('skills');
  await expect(page.locator('#catalog .card:visible')).toHaveCount(1);
  await expect(page.locator('#extensions .card:visible')).toHaveCount(1);
  await page.locator('#extension-search').fill('');
  for (const id of ['extension-kind', 'extension-runtime', 'extension-scope']) await page.locator('#' + id).selectOption('all');
  await expect(page.locator('#extensions .card:visible')).toHaveCount(inventory.extensions.pieces.length);
});

test('P-03 declared MCP status omits credentials and never runs consumer code', async ({ page }) => {
  const network = []; page.on('request', request => { if (/^https?:/.test(request.url())) network.push(request.url()); });
  await page.reload();
  await page.locator('#extension-kind').selectOption('mcp');
  const ledger = page.locator('#extensions .card').filter({ has: page.getByRole('heading', { name: 'ledger', exact: true }) });
  await expect(ledger).toContainText('Disponibilidad sin verificar');
  await expect(ledger).toContainText('Deshabilitado en la configuración');
  const html = await page.content();
  for (const value of ['PRIVATE AGENT BODY', 'PRIVATE PERSONA BODY', 'PRIVATE SKILL BODY', 'PRIVATE INSTRUCTIONS', 'PRIVATE MCP TOKEN', 'PRIVATE_URL', 'PRIVATE_AUTH', 'must-not-exist']) expect(html).not.toContain(value);
  expect(network).toEqual([]); expect(fs.existsSync(forbiddenSideEffect)).toBe(false);
  for (const [file, original] of untouched) expect(fs.readFileSync(file, 'utf8')).toBe(original);
});

test('P-04 keyboard navigation and mobile filters remain usable without overflow', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  const nav = page.locator('.sidebar nav a[href="#extensions"]');
  await nav.focus(); await page.keyboard.press('Enter'); await expect(nav).toHaveAttribute('aria-current', 'location');
  await page.locator('#extension-kind').selectOption('agent');
  await page.locator('#extension-runtime').selectOption('claude-code');
  await page.locator('#extension-scope').focus(); await page.keyboard.press('ArrowDown'); await page.keyboard.press('Enter');
  await expect(page.locator('#extension-scope')).toHaveValue('project');
  await page.locator('#extension-search').focus(); await page.keyboard.type('billing');
  await expect(page.locator('#extensions .card:visible')).toHaveCount(1);
  const details = page.locator('#extensions .card:visible details');
  await details.locator('summary').focus(); await page.keyboard.press('Enter'); await expect(details).toHaveAttribute('open', '');
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
  expect(overflow).toBe(false);
  await page.locator('#extensions').screenshot({ path: test.info().outputPath('mobile-extensions.png') });
});
