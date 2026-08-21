# 2026-07-09-qa-agent

> Evaluación/presupuesto del nuevo agente qa (E2E con Playwright + informe md/pdf).

| | |
|---|---|
| **Fecha** | 2026-07-09 |
| **Estado** | completado |
| **Prioridad global** | Media |
| **Solicitante** | daycry |
| **Spec** | [`spec.md`](spec.md) |
| **Plan** | [`improvement-plan.md`](improvement-plan.md) |
| **Características evaluadas** | 3 |

---

## Cuadro de mando

| Métrica | Total estimado | Confianza |
|--------|----------------|-----------|
| Esfuerzo humano | **21,6 h** (18 h base +20 %) | Media |
| Tiempo IA (ejecución) | **1,4 h** (+ 0,35 h supervisión) | Media |
| Coste | **~1.087 €** | Media |
| Tokens IA | **320k** (in 250k / out 70k) | Media |
| Multiplicador productividad | **×12,3** | — |
| Características | **3** | — |

---

## Resumen ejecutivo

La spec propone un agente **`qa`** que audita un plan ejecutando sus tests E2E con **Playwright**, captura evidencias y entrega un informe **md + pdf** (reutilizando `to-pdf`) con checklist manual. Incluye extender `planner` para generar un **`test-plan.md`** por plan. Complejidad media-alta concentrada en la integración de Playwright; el resto reutiliza piezas del bundle. Se presupuesta para decidir su inclusión.

---

## Requerimientos recibidos

| ID | Característica | Requisito origen (ref.) | ¿Claro? |
|----|---------------|-------------------------|---------|
| C-01 | Definición de tests: `test-plan.md` + `planner` lo genera + etiquetas por tarea | spec §Arquitectura / §Flujo | Sí |
| C-02 | Agente `qa` + runner Playwright (kit, guardrail local, capturas) | spec §Arquitectura / §Flujo | Sí |
| C-03 | Informe QA md + pdf (vía `to-pdf`) con evidencias + checklist manual | spec §Flujo (4) | Sí |

**Ambigüedades / información que falta:** ninguna bloqueante. Playwright descarga navegadores en el primer uso (red + disco), bajo permiso.

---

## Datos necesarios para una evaluación completa

- [x] Requerimientos completos (spec redactada)
- [x] Alcance acotado (spec §Alcance)
- [x] Reutilización identificada (skill `to-pdf`, patrón guardrail de `nemesis`)
- [x] Ubicación de salida definida (`docs/roadmap/<slug>/testing/`)
- [ ] Confirmar entorno con Node + espacio para navegadores de Playwright
- [x] Tarifa/hora y supuestos de coste confirmados

---

## Supuestos económicos (ajustables)

**Coste = (horas × tarifa) + coste de tokens de IA.** Importes en EUR.

| Parámetro | Valor | Nota |
|-----------|-------|------|
| Tarifa de desarrollo | 50 €/h | — |
| Modelo IA asumido | claude-opus-4-8 | Base de la previsión de tokens |
| Precio input | 12 € / 1M tokens | ilustrativo, verificar tarifa vigente |
| Precio output | 60 € / 1M tokens | ilustrativo, verificar tarifa vigente |
| Ratio de supervisión | ~25 % de las horas IA | — |
| Margen de contingencia | 20 % | Sobre horas base (humanas e IA) |

---

## Evaluación por característica

### C-01 — Definición de tests (`test-plan.md` + planner + tags)

- **Requisito origen**: spec §Arquitectura / §Flujo
- **Descripción**: plantilla `agent-kits/planner/templates/test-plan.md` (bloques Automáticos E2E-xx / Manuales M-xx + cobertura), paso en el flujo de `planner` para generarla, y etiqueta de trazabilidad por tarea en `tasks.md`.
- **Complejidad**: Media
- **Esfuerzo**: 4 h base · confianza Alta
- **Previsión IA**: 70k in / 20k out tok · ~1,6 €
- **Coste**: (4 h × 50 €/h) + tokens = **~202 €** (base)
- **Impacto / áreas afectadas**: `agent-kits/planner/templates/`, `agents/planner.md`, plantilla `tasks.md`
- **Dependencias y prerequisitos**: ninguna
- **Riesgos**: bajo; es documentación estructurada
- **Incógnitas / preguntas abiertas**: formato exacto de la etiqueta de trazabilidad (campo en la tarea)

### C-02 — Agente `qa` + runner Playwright

- **Requisito origen**: spec §Arquitectura / §Flujo
- **Descripción**: `agents/qa.md` + `agent-kits/qa/` con runner Playwright (config, ejecuta escenarios E2E-xx, capturas + trazas, resultados JSON), guardrail local-only e instalación opt-in en `~/.claude/tool-cache/qa/`.
- **Complejidad**: Alta
- **Esfuerzo**: 10 h base · confianza Media
- **Previsión IA**: 130k in / 38k out tok · ~3,8 €
- **Coste**: (10 h × 50 €/h) + tokens = **~504 €** (base)
- **Impacto / áreas afectadas**: `agents/qa.md`, `agent-kits/qa/*`
- **Dependencias y prerequisitos**: Node + navegadores de Playwright (opt-in); C-01 (para tener escenarios)
- **Riesgos**: integración/instalación de Playwright (pesada); flaky tests; mitigable con esperas robustas y trazas
- **Incógnitas / preguntas abiertas**: alcance de navegadores (solo Chromium vs. varios) — se sugiere solo Chromium en la 1ª iteración

### C-03 — Informe QA (md + pdf) con evidencias y checklist manual

- **Requisito origen**: spec §Flujo (4)
- **Descripción**: plantilla `agent-kits/qa/templates/report.md` + generación con resultados (pass/fail por escenario, capturas embebidas, errores), checklist manual (M-xx) y trazabilidad tarea→resultado; `report.pdf` vía skill `to-pdf`.
- **Complejidad**: Media
- **Esfuerzo**: 4 h base · confianza Alta
- **Previsión IA**: 50k in / 12k out tok · ~1,3 €
- **Coste**: (4 h × 50 €/h) + tokens = **~201 €** (base)
- **Impacto / áreas afectadas**: `agent-kits/qa/templates/`, integración con `skills/to-pdf`
- **Dependencias y prerequisitos**: C-02 (resultados a partir de los que se genera); skill `to-pdf`
- **Riesgos**: bajo; el patrón md→pdf ya existe
- **Incógnitas / preguntas abiertas**: ninguna relevante

---

## Comparativa

| # | Característica | Complejidad | Horas (base) | Coste € (base) | Tokens | Prioridad | Confianza |
|---|---------------|-------------|--------------|----------------|--------|-----------|-----------|
| C-01 | test-plan + planner + tags | Media | 4 h | ~202 € | 90k | Media | Alta |
| C-02 | agente qa + Playwright | Alta | 10 h | ~504 € | 168k | Media | Media |
| C-03 | informe md/pdf | Media | 4 h | ~201 € | 62k | Media | Alta |
| | **Total (base)** | | **18 h** | **~907 €** | **320k** | | |

---

## Presupuesto total

| Concepto | Cálculo | Importe |
|----------|---------|---------|
| Desarrollo (humano, base) | 18 h × 50 €/h | 900 € |
| Margen de contingencia | +20 % sobre desarrollo base | 180 € |
| Tokens IA (input) | 250k × 12 €/1M | 3,0 € |
| Tokens IA (output) | 70k × 60 €/1M | 4,2 € |
| **Total estimado (con margen)** | | **~1.087 €** |

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

## Recomendación

- **Veredicto**: go. Aporta la pata de QA/UI que falta y reutiliza piezas del bundle (`to-pdf`, patrón de guardrail). El riesgo se concentra en C-02 (Playwright).
- **Quick win**: C-01 (test-plan + planner) — pequeño, sin dependencias, y deja el terreno listo.
- **Orden sugerido**: C-01 → C-02 → C-03 (definir escenarios → ejecutarlos → reportarlos).
- **Bloqueante menor**: confirmar Node + espacio/red para los navegadores de Playwright.

---

## Riesgos transversales

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Tests E2E frágiles (flaky) | Media | Medio | Selectores robustos, auto-waits de Playwright, reintentos y trazas |
| Instalación pesada de navegadores | Media | Bajo | Opt-in + solo Chromium en la 1ª iteración |
| App no levantada al auditar | Media | Medio | Comprobación previa de la URL local y mensaje claro |

---

## Siguiente paso

Para **ejecutar** lo aprobado, genera el plan detallado con el agente **`planner`** (creará `docs/roadmap/2026-07-09-qa-agent/` con `improvement-plan.md` + `tasks.md`, y de paso su `test-plan.md`). Características aprobadas para planificar: **C-01, C-02 y C-03**.

---

## Changelog

- 2026-07-09: Evaluación creada a partir de [`spec.md`](spec.md).
- 2026-07-09: Plan generado ([`improvement-plan.md`](improvement-plan.md)); cadena cerrada.
