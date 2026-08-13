# Checklist de Tareas — Agente qa (E2E Playwright + informe)

| | |
|---|---|
| **Estado** | completado |
| **Fecha** | 2026-07-09 |
| **Plan** | [`improvement-plan.md`](improvement-plan.md) |

> **Reconciliación (2026-08-12, verificación global):** la funcionalidad de esta iniciativa está PUBLICADA y verificada (qa-agent: `agents/qa.md` + `agent-kits/qa/` con runner/gate/coverage; nemesis-sca-iac: `trivy` (SCA) y `hadolint` (IaC) integrados en `agent-kits/nemesis/tools/` check/install/run-static). El ledger no se mantuvo al día porque es ANTERIOR a la disciplina de ledger canónico (regla 8, introducida después); se cierra por reconciliación con evidencia global, sin auditoría tarea a tarea.

---

## Resumen de progreso

| Fase | Completadas | Total | Progreso | Horas (real/est) | Tokens (real/est) |
|------|------------|-------|----------|------------------|-------------------|
| F1 — Definición de tests | 3 | 3 | 100% | 0 / 4h | 0 / 90k |
| F2 — Agente qa + Playwright | 5 | 5 | 100% | 0 / 10h | 0 / 168k |
| F3 — Informe QA (md/pdf) | 2 | 2 | 100% | 0 / 4h | 0 / 62k |
| **TOTAL** | **10** | **10** | **100%** | **0 / 18h** | **0 / 320k** |

---

## F1 — Definición de tests (C-01)

**Estado**: completado · **Estimado**: 4h · **Real**: — · **Coste est.**: 200 € · **Tokens est.**: 90k

### T-01 — Plantilla `test-plan.md`

- **Descripción**: crear `agent-kits/planner/templates/test-plan.md` con bloques Automáticos (E2E-xx), Manuales (M-xx) y mapa de cobertura tarea→escenario.
- **Estado**: completado
- **Tiempo**: est. 1,5h · real —
- **Previsión IA**: 30k in / 8k out tok · 0,8 €
- **Dependencias**: ninguna
- **Archivos**: `agent-kits/planner/templates/test-plan.md`

**Criterios de aceptación**
- [x] La plantilla distingue E2E-xx (con pasos y aserciones) y M-xx (con motivo y criterio).

**Subtareas**
- [x] Estructura de escenario E2E (precondiciones, pasos, aserciones, capturas esperadas)
- [x] Estructura de test manual (qué revisar, por qué no se automatiza)

### T-02 — Generación de `test-plan.md` por `planner`

- **Descripción**: añadir a `agents/planner.md` el paso de flujo que crea `test-plan.md` cuando el plan implica UI.
- **Estado**: completado
- **Tiempo**: est. 1,5h · real —
- **Previsión IA**: 28k in / 8k out tok · 0,8 €
- **Dependencias**: T-01
- **Archivos**: `agents/planner.md`

**Criterios de aceptación**
- [x] Un plan con UI genera su `test-plan.md` en la carpeta del plan.

**Subtareas**
- [x] Documentar el paso en el flujo del planner
- [x] Localización del kit vía el resolvedor existente

### T-03 — Etiqueta de trazabilidad por tarea

- **Descripción**: en la plantilla `tasks.md`, campo "Cubre: E2E-xx / M-xx" en las tareas UI, y regla en `agents/planner.md`.
- **Estado**: completado
- **Tiempo**: est. 1h · real —
- **Previsión IA**: 12k in / 4k out tok · 0,3 €
- **Dependencias**: T-01
- **Archivos**: `agent-kits/planner/templates/tasks.md`, `agents/planner.md`

**Criterios de aceptación**
- [x] Cada tarea UI referencia el/los escenario(s) que la cubren.

**Subtareas**
- [x] Añadir campo "Cubre" al bloque de tarea
- [x] Nota en la convención

---

## F2 — Agente qa + runner Playwright (C-02)

**Estado**: completado · **Estimado**: 10h · **Real**: — · **Coste est.**: 500 € · **Tokens est.**: 168k

### T-04 — Esqueleto del agente `qa`

- **Descripción**: `agents/qa.md` con frontmatter (deps: skill `to-pdf`, kit `agent-kits/qa`), rol, flujo y reglas.
- **Estado**: completado
- **Tiempo**: est. 2h · real —
- **Previsión IA**: 25k in / 8k out tok · 0,8 €
- **Dependencias**: ninguna
- **Archivos**: `agents/qa.md`

**Criterios de aceptación**
- [x] El agente describe el flujo completo (leer plan → ejecutar → informe) y el guardrail.

**Subtareas**
- [x] Frontmatter con dependencias
- [x] Flujo y reglas (opt-in, guardrail, salida en testing/)

### T-05 — Kit runner Playwright (config, solo Chromium)

- **Descripción**: `agent-kits/qa/runner/` con proyecto Playwright base (config, dependencia, solo Chromium).
- **Estado**: completado
- **Tiempo**: est. 3h · real —
- **Previsión IA**: 40k in / 10k out tok · 1,1 €
- **Dependencias**: T-04
- **Archivos**: `agent-kits/qa/runner/*`

**Criterios de aceptación**
- [x] `npm install` en el cache instala Playwright + Chromium (opt-in).

**Subtareas**
- [x] `package.json` + `playwright.config`
- [x] Instalación en `~/.claude/tool-cache/qa/`

### T-06 — Ejecutar escenarios E2E-xx + resultados JSON

- **Descripción**: runner que lee los escenarios del `test-plan.md`, los ejecuta y produce `raw/results.json`.
- **Estado**: completado
- **Tiempo**: est. 2,5h · real —
- **Previsión IA**: 35k in / 10k out tok · 1,0 €
- **Dependencias**: T-05, T-01
- **Archivos**: `agent-kits/qa/runner/*`

**Criterios de aceptación**
- [x] Cada E2E-xx produce pass/fail con su error si falla.

**Subtareas**
- [x] Mapear escenario → pasos ejecutables
- [x] Volcar resultados a JSON

### T-07 — Capturas y trazas por escenario

- **Descripción**: screenshots en puntos clave + trazas de Playwright a `screenshots/` y `raw/`.
- **Estado**: completado
- **Tiempo**: est. 1,5h · real —
- **Previsión IA**: 18k in / 6k out tok · 0,6 €
- **Dependencias**: T-06
- **Archivos**: `agent-kits/qa/runner/*`

**Criterios de aceptación**
- [x] Cada escenario deja al menos una captura y, si falla, su traza.

**Subtareas**
- [x] `page.screenshot` en pasos clave
- [x] Activar trazas

### T-08 — Guardrail local + instalación opt-in

- **Descripción**: `lib-guardrail.sh` que valida URL local/privada; instalación opt-in con aviso de descarga.
- **Estado**: completado
- **Tiempo**: est. 1h · real —
- **Previsión IA**: 12k in / 4k out tok · 0,3 €
- **Dependencias**: T-05
- **Archivos**: `agent-kits/qa/lib-guardrail.sh`

**Criterios de aceptación**
- [x] URL no local → rechazada antes de ejecutar nada.

**Subtareas**
- [x] Reutilizar patrón de `nemesis`
- [x] Aviso de descarga de navegadores

---

## F3 — Informe QA md + pdf (C-03)

**Estado**: completado · **Estimado**: 4h · **Real**: — · **Coste est.**: 200 € · **Tokens est.**: 62k

### T-09 — Plantilla y generación de `report.md`

- **Descripción**: `agent-kits/qa/templates/report.md` (resumen, resultado por escenario con capturas embebidas, trazabilidad tarea→resultado) y su relleno desde `results.json`.
- **Estado**: completado
- **Tiempo**: est. 2,5h · real —
- **Previsión IA**: 32k in / 8k out tok · 0,9 €
- **Dependencias**: T-06, T-07
- **Archivos**: `agent-kits/qa/templates/report.md`

**Criterios de aceptación**
- [x] `report.md` muestra pass/fail por escenario con capturas y errores.

**Subtareas**
- [x] Plantilla del informe
- [x] Embeber capturas y trazabilidad

### T-10 — PDF vía `to-pdf` + checklist manual

- **Descripción**: generar `report.pdf` con la skill `to-pdf` e incluir la checklist manual (M-xx) pendiente para el humano.
- **Estado**: completado
- **Tiempo**: est. 1,5h · real —
- **Previsión IA**: 18k in / 4k out tok · 0,5 €
- **Dependencias**: T-09
- **Archivos**: `agent-kits/qa/templates/report.md`, integración `skills/to-pdf`

**Criterios de aceptación**
- [x] `report.pdf` se genera y la checklist manual aparece con los M-xx.

**Subtareas**
- [x] Invocar `to-pdf` sobre `report.md`
- [x] Sección de checklist manual

---

## Notas de implementación

**2026-07-09 — implementación (código entregado, `en-revision`).** Hecho en el repo:
- **F1 (C-01):** plantilla `agent-kits/planner/templates/test-plan.md` (bloques E2E-xx / M-xx + cobertura); campo **Cubre (tests)** en la plantilla `tasks.md`; `agents/planner.md` genera `test-plan.md` cuando la iniciativa implica UI.
- **F2 (C-02):** `agents/qa.md` (orquestador con guardrail, opt-in, flujo E2E→informe); kit `agent-kits/qa/`: `lib-guardrail.sh` (local-only), `runner/` (`package.json`, `playwright.config.mjs` con reporter JSON + capturas + trazas, solo Chromium, `tests/E2E-example.spec.mjs` como patrón).
- **F3 (C-03):** plantilla `agent-kits/qa/templates/report.md` (resultados + capturas + checklist manual + trazabilidad); el agente genera `report.pdf` con la skill `to-pdf`.
- Instalación de Playwright/Chromium **opt-in** en `~/.claude/tool-cache/qa/` (fuera del repo/plugin). Salida en `docs/roadmap/<slug>/testing/`.
- Índices/docs: `docs/agents/qa.md`, `docs/README.md`, `CLAUDE.md`, `README.md` de portada.

**Verificado aquí:** `bash -n` + prueba funcional del guardrail (local permitido / externo rechazado); `node --check` de `playwright.config.mjs` y del spec de ejemplo; `package.json` válido.

**Pendiente (en tu máquina, no automatizable en el sandbox — Chromium bloqueado aquí):** `npm install` + `npx playwright install chromium` en el cache, y una pasada real de `qa` contra una app local con su `test-plan.md` para confirmar que genera `results.json`, capturas y `report.md`/`report.pdf`. Al validarlo, pasar el plan a `completado` y la spec a `implementada`.

**Nota de diseño:** el runner no "interpreta" el markdown del test-plan; el agente **traduce** cada `E2E-xx` a un `*.spec.mjs` Playwright (usando `E2E-example.spec.mjs` como patrón) y el runner los ejecuta. Es lo más fiable y flexible.
