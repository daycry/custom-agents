# agent-kits/qa — toolkit privado del agente `qa`

Ejecuta E2E con Playwright contra la app local y produce el informe. Uso interno del agente `qa`.

- `runner/` — proyecto Playwright base: `package.json`, `playwright.config.mjs` (**modo estricto**: `retries: 2` con detección de flaky, `forbidOnly`, timeout configurable `QA_TIMEOUT_MS`, reporter JSON + capturas + trazas, solo Chromium) y `tests/E2E-example.spec.mjs` (plantilla que el agente adapta por cada `E2E-xx`).
- `lib-guardrail.sh` — gate local-only para la URL objetivo (mismo patrón que `nemesis`).
- `qa-gate.py` — **veredicto determinista**: parsea `results.json` y decide verde/rojo por exit code (0 failed y 0 flaky sin justificar; justificaciones con `--justify fichero.json`). La ausencia de evidencia es rojo. Tests en `tests/test_qa_gate.py`.
- `coverage-check.py` — **puerta de cobertura** criterios↔tests: cruza el campo «Cubre (tests)» de `tasks.md` con los bloques del `test-plan.md`; referencias rotas = error, tareas sin cobertura y tests sin referenciar = avisos para triage.
- `templates/report.md` — plantilla del informe de QA (resultados + evidencias + checklist manual).

Playwright + Chromium se instalan **fuera del repo**, en `~/.claude/tool-cache/qa/`, con **permiso previo** (descarga pesada). La salida va a `docs/roadmap/<fecha>-<slug>/testing/`. El PDF se genera con la skill compartida `to-pdf`.

**Documentación completa:** [`docs/agents/qa.md`](../../docs/agents/qa.md)
**Convención del repo:** [`docs/CONVENTIONS.md`](../../docs/CONVENTIONS.md)
