// Config Playwright del agente qa.
// Variables de entorno (las fija el agente al ejecutar):
//   QA_BASE_URL  URL local de la app (ya validada por el guardrail)
//   QA_TESTS     carpeta con los *.spec.mjs que el agente genera desde los E2E-xx
//   QA_OUT       carpeta de salida (docs/roadmap/<slug>/testing)
import { defineConfig } from '@playwright/test';

const OUT = process.env.QA_OUT || 'testing';

export default defineConfig({
  testDir: process.env.QA_TESTS || './tests',
  outputDir: `${OUT}/raw/artifacts`,
  timeout: 30_000,
  expect: { timeout: 5_000 },
  retries: 1,
  fullyParallel: false,
  reporter: [
    ['list'],
    ['json', { outputFile: `${OUT}/raw/results.json` }],
  ],
  use: {
    baseURL: process.env.QA_BASE_URL,
    headless: true,
    screenshot: 'on',            // captura al final de cada test
    trace: 'retain-on-failure',  // traza cuando falla
    video: 'off',
    viewport: { width: 1280, height: 800 },
    ignoreHTTPSErrors: true,     // entornos locales con TLS autofirmado
  },
  // Solo Chromium en esta iteración (ver spec/plan qa-agent).
  projects: [{ name: 'chromium', use: { browserName: 'chromium' } }],
});
