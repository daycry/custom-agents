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
  // Modo estricto (iniciativa qa-strict): timeouts explícitos, sin test.only
  // accidental, y 2 reintentos para que el reporter marque los flaky — el
  // veredicto lo decide qa-gate.py sobre results.json, no el LLM.
  timeout: (() => {                       // QA_TIMEOUT_MS no numérico o ≤0 → default seguro
    const t = Number(process.env.QA_TIMEOUT_MS);
    return Number.isFinite(t) && t > 0 ? t : 30_000;
  })(),
  expect: { timeout: 5_000 },
  retries: 2,                 // flaky = falla y pasa al reintento → lo evalúa qa-gate
  forbidOnly: true,           // un test.only olvidado rompe la ejecución, no la esconde
  fullyParallel: false,
  reporter: [
    ['list'],
    ['json', { outputFile: `${OUT}/raw/results.json` }],  // evidencia para qa-gate.py
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
