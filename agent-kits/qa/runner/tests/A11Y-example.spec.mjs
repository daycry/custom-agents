// Plantilla A11Y-xx (accesibilidad con axe-core) — OPT-IN.
// El agente `qa` la adapta por cada bloque A11Y-xx del test-plan SOLO si el
// usuario aceptó instalar la dependencia (mismo flujo de permiso que Chromium):
//   ( cd "$CACHE" && npm install --no-audit --no-fund @axe-core/playwright )
// Si el usuario declina, los A11Y-xx pasan a la checklist manual del informe.
//
// Umbral por defecto: 0 violaciones `serious`/`critical` (ajustable en el test-plan).
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

const OUT = process.env.QA_OUT || 'testing';

test('A11Y-01 — {{página o flujo}}', async ({ page }, testInfo) => {
  await page.goto('{{/ruta-relativa}}');

  const results = await new AxeBuilder({ page }).analyze();
  const graves = results.violations.filter(v =>
    ['serious', 'critical'].includes(v.impact));

  // evidencia: volcado completo para el informe
  await testInfo.attach('axe-results.json', {
    body: JSON.stringify(results.violations, null, 2),
    contentType: 'application/json',
  });
  await page.screenshot({ path: `${OUT}/screenshots/A11Y-01.png`, fullPage: true });

  expect(graves, graves.map(v => `${v.id}: ${v.help}`).join('\n')).toEqual([]);
});
