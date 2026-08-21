# 2026-07-09-qa-agent

> Nuevo agente qa: E2E con Playwright + informe md/pdf del plan auditado. Plan de implementación.

| | |
|---|---|
| **Fecha** | 2026-07-09 |
| **Estado** | borrador |
| **Tipo** | Nueva Funcionalidad |
| **Prioridad** | Media |
| **Solicitante** | daycry |
| **Responsable** | — |
| **Spec** | [`spec.md`](spec.md) |
| **Evaluación** | [`evaluation.md`](evaluation.md) |

---

## Cuadro de mando

| Métrica | Estimado | Real | Confianza |
|--------|---------|------|-----------|
| Tiempo humano | **21,6 h** (18 h base +20 %) | 0 h | Media |
| Tiempo IA (ejecución) | **1,4 h** (+ 0,35 h supervisión) | 0 h | Media |
| Coste total | **~1.087 €** | 0 € | Media |
| Tokens IA | **320k** (in 250k / out 70k) | 0 | Media |
| Multiplicador productividad | **×12,3** | — | — |
| Tareas | **10** | 0 hechas | — |

---

## Estimación por fase

| Fase | Estimado (h) | Tokens (in / out) | Coste € |
|------|-------------|-------------------|---------|
| F1 — Definición de tests (test-plan + planner) | 4 | 70k / 20k | 200 |
| F2 — Agente qa + runner Playwright | 10 | 130k / 38k | 500 |
| F3 — Informe QA (md + pdf) | 4 | 50k / 12k | 200 |
| **Total (base)** | **18 h** | **250k / 70k** | **900 €** |

---

## Presupuesto económico

**Coste = (horas × tarifa) + coste de tokens de IA.** Importes en EUR.

### Supuestos (ajustables)

| Parámetro | Valor | Nota |
|-----------|-------|------|
| Tarifa de desarrollo | 50 €/h | — |
| Modelo IA asumido | claude-opus-4-8 | Base de la previsión de tokens |
| Precio input | 12 € / 1M tokens | ilustrativo, verificar tarifa vigente |
| Precio output | 60 € / 1M tokens | ilustrativo, verificar tarifa vigente |
| Ratio de supervisión | ~25 % de las horas IA | — |
| Horas por empleado-mes (FTE) | 160 h | — |
| Margen de contingencia | 20 % | Sobre horas base (humanas e IA) |

### Desglose

| Concepto | Cálculo | Importe |
|----------|---------|---------|
| Desarrollo (humano, base) | 18 h × 50 €/h | 900 € |
| Margen de contingencia | +20 % sobre desarrollo base | 180 € |
| Tokens IA (input) | 250k × 12 €/1M | 3,0 € |
| Tokens IA (output) | 70k × 60 €/1M | 4,2 € |
| **Total estimado (con margen)** | | **~1.087 €** |

---

## Previsión de tokens (por fase)

| Fase | Input (tok) | Output (tok) | Total (tok) | Coste € |
|------|------------|-------------|-------------|---------|
| F1 | 70k | 20k | 90k | 1,6 |
| F2 | 130k | 38k | 168k | 3,8 |
| F3 | 50k | 12k | 62k | 1,3 |
| **Total** | **250k** | **70k** | **320k** | **~7 €** |

**Método de estimación:** nº de ficheros a crear (agente, kit, runner Playwright, plantillas) × tamaño medio + generación de código del runner y de las plantillas.

---

## Productividad IA (humano vs. IA)

| KPI | Valor |
|-----|-------|
| Horas humanas estimadas | 21,6 h (18 h base +20 %) |
| Horas IA (ejecución) | 1,4 h (1,2 h base +20 %) |
| Supervisión humana | 0,35 h |
| **Horas totales (IA + supervisión)** | **1,75 h** |
| Horas ahorradas | 19,85 h |
| **Ahorro** | **91,9 %** |
| **Multiplicador de productividad** | **×12,3** |
| FTE equivalentes *(opcional)* | 0,12 |

> Horas con margen de contingencia (+20 %) ya aplicado. Base: 18 h humanas / 1,2 h IA. Horas IA estimadas como supuesto (≈ horas humanas ÷ 15); supervisión al 25 % de las horas IA.

---

## Resumen ejecutivo

Crear el agente `qa` que audita un plan ejecutando sus tests E2E con Playwright contra la app local, captura evidencias y entrega un informe md + pdf con checklist manual. Incluye extender `planner` para generar un `test-plan.md` por plan. Reutiliza la skill `to-pdf` y el patrón de guardrail local + instalación opt-in de `nemesis`.

### Objetivos

- Definir los tests por plan (`test-plan.md`: automáticos E2E-xx + manuales M-xx) con trazabilidad por tarea.
- Ejecutar los automáticos con Playwright (solo Chromium en esta iteración) contra la app local, con capturas.
- Entregar `report.md` + `report.pdf` en `docs/roadmap/<slug>/testing/` con evidencias y checklist manual.

---

## Datos necesarios para un informe completo

- [x] Requisitos confirmados (spec redactada y aprobada)
- [x] Alcance cerrado (spec §Alcance; solo Chromium en la 1ª iteración)
- [x] Reutilización identificada (skill `to-pdf`, patrón guardrail de `nemesis`)
- [ ] Entorno con **Node** y espacio/red para navegadores de Playwright
- [x] Tarifa/hora y supuestos de coste confirmados

---

## Análisis de impacto

- **`agents/qa.md`** — nuevo agente orquestador.
- **`agent-kits/qa/`** — nuevo kit: runner Playwright, guardrail, plantilla de informe.
- **`agent-kits/planner/templates/test-plan.md`** — nueva plantilla + generación por `planner`.
- **`agents/planner.md`** — paso de flujo para generar `test-plan.md` y etiqueta de trazabilidad por tarea.
- **`skills/to-pdf/`** — se consume (sin cambios) para el PDF.
- **`docs/README.md`, `CLAUDE.md`, `docs/agents/qa.md`** — alta e índice del nuevo agente.

---

## Cambios arquitectónicos

- El agente `qa` audita **contra un plan** (lee `improvement-plan.md`, `tasks.md`, `test-plan.md`); salida en `docs/roadmap/<slug>/testing/`.
- Guardrail local-only para la URL objetivo (mismo patrón que `nemesis`).
- Playwright se instala opt-in en `~/.claude/tool-cache/qa/` (fuera del repo/plugin).

---

## Archivos a crear/modificar

| Archivo | Acción | Propósito |
|---------|--------|-----------|
| `agents/qa.md` | Crear | Agente orquestador de QA |
| `agent-kits/qa/runner/*` | Crear | Proyecto/config Playwright + runner de escenarios |
| `agent-kits/qa/lib-guardrail.sh` | Crear | Gate local-only de la URL objetivo |
| `agent-kits/qa/templates/report.md` | Crear | Plantilla del informe de QA |
| `agent-kits/qa/README.md` | Crear | Doc breve del kit |
| `agent-kits/planner/templates/test-plan.md` | Crear | Plantilla de test-plan por plan |
| `agents/planner.md` | Modificar | Generar `test-plan.md` + etiqueta de trazabilidad |
| `agent-kits/planner/templates/tasks.md` | Modificar | Campo "Cubre: E2E-xx / M-xx" por tarea |
| `docs/agents/qa.md`, `docs/README.md`, `CLAUDE.md` | Crear/Modificar | Documentación e índice |

---

## Dependencias y prerequisitos

- **F1 antes que F2** (los escenarios deben existir para ejecutarlos).
- Node + navegadores de Playwright (opt-in) para F2.
- Skill `to-pdf` disponible (ya en el bundle) para F3.

---

## Criterios de aceptación (global)

- [ ] `planner` genera un `test-plan.md` con bloques E2E-xx y M-xx y las tareas UI llevan su etiqueta de cobertura.
- [ ] `qa` ejecuta los E2E-xx contra una URL local, captura screenshots y produce `testing/report.md` + `report.pdf`.
- [ ] Una URL no local es rechazada por el guardrail.
- [ ] Sin Playwright instalado y declinando la instalación, el informe declara los automáticos no ejecutados y mantiene la checklist manual.
- [ ] El informe embebe capturas y lista los tests manuales (M-xx) pendientes.

---

## Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Tests E2E frágiles (flaky) | Media | Medio | Auto-waits de Playwright, selectores robustos, reintentos y trazas |
| Instalación pesada de navegadores | Media | Bajo | Opt-in + solo Chromium en la 1ª iteración |
| App no levantada al auditar | Media | Medio | Comprobación previa de la URL local y mensaje claro |

---

## Métricas de éxito

- Un plan de ejemplo con app local trivial se audita de punta a punta y el informe refleja pass/fail con capturas.
- El humano puede seguir la checklist manual sin ambigüedad.

---

## Agregación de tiempo

- 2026-07-09: Creación del plan (`Tiempo consumido`: 0h).

---

## Changelog

- 2026-07-09: Plan creado a partir de [`evaluation.md`](evaluation.md) (aprobadas C-01, C-02, C-03) y [`spec.md`](spec.md).
