# Documentación del agente `qa`

Agente que **audita un plan** ejecutando sus tests E2E con **Playwright** contra la app local, captura evidencias y entrega un informe **md + pdf** con checklist manual. Es el equivalente funcional de `nemesis` pero para **QA/UI**.

---

## 1. Entrada y salida

- **Entrada:** una iniciativa en `docs/roadmap/<fecha>-<slug>/` con su `test-plan.md` (bloques `E2E-xx` automáticos y `M-xx` manuales, que genera `planner`), más la **URL local** de la app en ejecución.
- **Salida:** `docs/roadmap/<fecha>-<slug>/testing/` con `report.md` + `report.pdf`, `screenshots/` y `raw/` (results.json + trazas).

---

## 2. Cómo funciona

`planner` define los tests en `test-plan.md`; `qa` los ejecuta. Traduce cada escenario `E2E-xx` a un test Playwright, los corre (solo Chromium en esta iteración) contra la URL local, captura screenshots en los puntos clave y recoge resultados en JSON. Luego rellena el informe: estado global, resultado por escenario con capturas y errores, **checklist manual** con los `M-xx` para la persona, y trazabilidad tarea→resultado. El PDF se genera con la skill compartida **`to-pdf`**.

---

## 3. Requisitos y guardrail

- **Node** en la máquina. Playwright + Chromium se instalan **fuera del repo** en `~/.claude/tool-cache/qa/`, con **permiso previo** (descarga pesada) — mismo patrón opt-in que `nemesis`/`pdfy`.
- **Guardrail:** los E2E solo contra hosts **locales/privados** (`localhost`, `127.0.0.1`, `*.test`, redes privadas). Una URL externa se rechaza.

---

## 4. Relación con `planner`

`planner` genera el `test-plan.md` (y las etiquetas **Cubre (tests)** en las tareas de UI); `qa` lo consume. Si un plan no tiene `test-plan.md`, hay que (re)generarlo con `planner` antes de auditar.

---

## 5. Cómo se invoca

Dentro del proyecto, en Claude Code:

- `usa el agente qa contra https://miapp.test`
- `qa, audita el plan docs/roadmap/2026-07-09-mi-feature con la app en http://localhost:8080`
- `prueba la UI con Playwright y genera el informe`

La primera vez pide permiso para instalar Playwright/Chromium y confirma la URL local.

---

## 6. Kit (`agent-kits/qa/`)

- `runner/` — proyecto Playwright (config con reporter JSON + capturas + trazas; `tests/E2E-example.spec.mjs` como patrón).
- `lib-guardrail.sh` — gate local-only de la URL.
- `templates/report.md` — plantilla del informe.
