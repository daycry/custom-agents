# agent-kits/qa — toolkit privado del agente `qa`

Ejecuta E2E con Playwright contra la app local y produce el informe. Uso interno del agente `qa`.

- `runner/` — proyecto Playwright base: `package.json`, `playwright.config.mjs` (reporter JSON + capturas + trazas, solo Chromium) y `tests/E2E-example.spec.mjs` (plantilla que el agente adapta por cada `E2E-xx`).
- `lib-guardrail.sh` — gate local-only para la URL objetivo (mismo patrón que `nemesis`).
- `templates/report.md` — plantilla del informe de QA (resultados + evidencias + checklist manual).

Playwright + Chromium se instalan **fuera del repo**, en `~/.claude/tool-cache/qa/`, con **permiso previo** (descarga pesada). La salida va a `docs/roadmap/<fecha>-<slug>/testing/`. El PDF se genera con la skill compartida `to-pdf`.

**Documentación completa:** [`docs/agents/qa.md`](../../docs/agents/qa.md)
**Convención del repo:** [`docs/CONVENTIONS.md`](../../docs/CONVENTIONS.md)
