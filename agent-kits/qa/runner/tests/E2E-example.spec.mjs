// EJEMPLO/plantilla de test E2E. El agente `qa` crea un fichero como este por
// cada escenario E2E-xx del test-plan.md (traduciendo pasos y aserciones).
// Guarda capturas en QA_OUT/screenshots para embeberlas en el informe.
import { test, expect } from '@playwright/test';
import { mkdirSync } from 'node:fs';
import { join } from 'node:path';

const SHOTS = join(process.env.QA_OUT || 'testing', 'screenshots');
mkdirSync(SHOTS, { recursive: true });

test('E2E-01 — la home responde y muestra el título', async ({ page }) => {
  await page.goto('/');                                   // usa baseURL (QA_BASE_URL)
  await page.screenshot({ path: join(SHOTS, 'E2E-01-home.png'), fullPage: true });
  await expect(page).toHaveTitle(/.+/);                   // aserción de ejemplo
});
