---
generacion:               # MEDIDO por usage-meter.py (una ventana cubre plan + tasks)
  inicio: 2026-08-12T07:51:04Z
  fin: 2026-08-12T07:53:41Z
  fuente: medido
  tokens_reales: { entrada: 8, salida: 12820, cache_creacion: 13335, cache_lectura: 1581487 }
  eur: 1.10                  # verificado con rates-verify (Opus 4.8; incluye caché) el 2026-08-18
  horas_ia: 0.05
  duracion: 3m                 
  ratio_usado: 479326       # calibrado (mediana de CALIBRATION.md; re-derivado en la retro del 2026-08-18)
---

# 2026-08-12-sdd-hardening

> SDD hardening: constitución del proyecto consumidor con enforcement por la lente A, `/spec-drift` (deriva spec↔código), criterios Given/When/Then opcionales traducibles a E2E, TDD RED-GREEN-REFACTOR y worktrees opt-in en Modo B, skill `debug-root-cause` para el 3.er rojo de qa, y documentación de compatibilidad con monitores de sesión externos.

| | |
|---|---|
| **Fecha** | 2026-08-12 |
| **Estado** | completado |
| **Tipo** | Nueva Funcionalidad |
| **Prioridad** | Media |
| **Solicitante** | jmano@mediapro.tv |
| **Responsable** | implementer (ejecución) · jmano@mediapro.tv (aprobación) |
| **Spec** | [`spec.md`](spec.md) |
| **Evaluación** | [`evaluation.md`](evaluation.md) |

---

## Cuadro de mando

| Métrica | Estimado | Real | Confianza |
|--------|---------|------|-----------|
| Tiempo humano | **23,1 h** (19,25 h base +20 %) | 0 h | Media |
| Tiempo IA (ejecución) | **7,4 h** (+ 1,9 h supervisión) | 0 h | Media |
| Coste total | **~1.195 €** | 0 € | Media |
| Tokens IA | **~1,84 M** (in 1,56 M / out 0,28 M) | 0 | Baja |
| Multiplicador productividad | **×2,5** | — | — |
| Tareas | **13** | 0 hechas | — |

> **Herencia y delta.** Horas heredadas de la evaluación (re-evaluada 2026-08-12 ×2, 8 características con C-08 ampliada a las 4 mecánicas) sin re-estimar: C-01 2,5 h · C-02 3,0 h · C-03 2,0 h · C-04 3,5 h · C-05 2,5 h · C-06 1,0 h · C-07 1,0 h · C-08 3,0 h = **18,5 h base (~1.150 € con margen)**. Delta del plan: T-11 cierre con E2E de juguete + índices + lint, **+0,75 h base** → total **19,25 h base / 23,1 h con margen / ~1.195 € / ~1,84 M tokens**.

---

## Estimación por fase

| Fase | Estimado (h) | Tokens (in / out) | Coste € |
|------|-------------|-------------------|---------|
| Fase 1 — Gobernanza: constitución (C-01) | 2,5 | 200k / 35k | ~131 € |
| Fase 2 — Specs verificables: G/W/T + drift (C-03, C-02) | 5,0 | 410k / 75k | ~271 € |
| Fase 3 — Disciplina nativa: debugging + TDD/worktrees (C-05, C-04) | 6,0 | 470k / 90k | ~317 € |
| Fase 3-bis — Autosuficiencia: nativa por defecto + subagentes con 4 mecánicas (C-07, C-08) | 4,0 | 315k / 60k | ~209 € |
| Fase 4 — Ecosistema y cierre (C-06 + E2E) | 1,75 | 155k / 25k | ~93 € |
| **Total (base)** | **19,25 h** | **1,56 M / 0,28 M** | **~1.003 €** |

> Horas y costes de la tabla son **base**. Con el margen (+20 % sobre horas base): **~1.195 €**.

---

## Presupuesto económico

Supuestos heredados de la evaluación (tarifa 50 €/h, precios de tokens ⚠️ verificar, margen 20 %).

| Concepto | Cálculo | Importe |
|----------|---------|---------|
| Desarrollo (humano, base) | 19,25 h × 50 €/h | 962,50 € |
| Margen de contingencia | +20 % | 192,50 € |
| Tokens IA (input) | 1,56 M × 13,80 €/M ⚠️ | 21,53 € |
| Tokens IA (output) | 0,28 M × 69,00 €/M ⚠️ | 19,32 € |
| **Total estimado (con margen)** | | **~1.195 €** |

---

## Resumen ejecutivo

El plugin ya es SDD (cadena de artefactos + puerta económica + calibración); esta iniciativa lo completa con lo mejor de los tres ecosistemas comparados. De Spec Kit: la **constitución** (principios permanentes del consumidor, con enforcement real vía lente A, no póster) y el **análisis de deriva** (`/spec-drift`, informar → `/pm-cycle`, nunca parchear). De la práctica SDD: criterios **G/W/T opcionales** que qa traduce 1:1 a E2E. De superpowers, como **fallback del Modo B y siempre opt-in con default off**: TDD RED-GREEN-REFACTOR con evidencia del rojo, worktrees aislados, y el método de **debugging sistemático** en 4 fases que se dispara justo donde hoy el bucle de qa se rinde (3.er rojo). Del ecosistema de observabilidad: documentar la **coexistencia** con monitores de sesión (Agent-Monitor) en vez de clonarlos. Regla transversal: en Modo A superpowers manda; nada de esto lo duplica.

## Arquitectura de la solución

- **Nuevo**: `agent-kits/shared/templates/CONSTITUTION.template.md` · `agent-kits/shared/constitution-check.md` (fragmento) · `commands/spec-drift.md` · `skills/debug-root-cause/SKILL.md` · `docs/observability.md` · config `.claude/dev.json`.
- **Se toca**: `commands/setup.md` (constitución + dev.json), 6 `agents/*.md` (fragmento constitución; implementer además TDD/worktrees), `commands/dev-cycle.md` (lente A con constitución; gancho debug-root-cause al 3.er rojo; TDD/worktrees Modo B), plantilla de spec (variante G/W/T), skill discovery y `agents/qa.md` (G/W/T→E2E), `agent-kits/qa/coverage-check.py` + tests (criterios `[GWT]`), `docs/CONVENTIONS.md` (regla 9: dev.json) y `docs/FLOWS.md`/`docs/README.md`/`docs/INSTALL.md`.
- **Reutiliza**: patrón de fragmentos shared, subagentes de lente A, bucles acotados, opt-ins de `/setup`, `lint_plugin.py`, medición usage-meter (esta iniciativa nace medida).

## Fases y tareas

Detalle y estado en [`tasks.md`](tasks.md) (ledger canónico).

| Fase | Tareas | Entrega |
|------|--------|---------|
| **Fase 1 — Gobernanza** | T-01 plantilla + fragmento constitución · T-02 integración (6 agentes, lente A, /setup) | La constitución existe, se lee y se hace cumplir |
| **Fase 2 — Specs verificables** | T-03 variante G/W/T (plantilla, analyst, discovery, qa) · T-04 coverage-check `[GWT]` + tests · T-05 `/spec-drift` + DRIFT.md | Criterios traducibles a tests y deriva detectable |
| **Fase 3 — Disciplina nativa** | T-06 skill `debug-root-cause` + gancho 3.er rojo · T-07 `.claude/dev.json` + /setup · T-08 TDD opt-in (implementer + dev-cycle) · T-09 worktrees opt-in | La cadena nativa con la disciplina de superpowers, sin depender de él |
| **Fase 3-bis — Autosuficiencia** | T-12 cadena nativa SIEMPRE por defecto (superpowers solo explícito) · T-13 subagentes de contexto fresco opt-in con las 4 mecánicas (task-brief.py, brief-only, estados ricos, revisor persistente) | El plugin se basta solo; el motor externo pasa a opcional real |
| **Fase 4 — Ecosistema y cierre** | T-10 `docs/observability.md` + enlaces · T-11 E2E de juguete (drift + puerta constitucional) + índices + lint | Documentado, verificado y enlazado |

## Riesgos del plan

| Riesgo | Mitigación |
|--------|------------|
| Falsos gaps constitucionales de la lente A | Prosa de la lente: solo principios EXPLÍCITOS, citando la línea del fichero (T-02, criterio) |
| /spec-drift caro o alegre | Lotes máx. 3, filtro por slug, `no verificable` obligatorio sin evidencia (T-05, criterios) |
| TDD-teatro | Evidencia del ROJO en el ledger antes del código (T-08, criterio); lente B caza tests vacíos |
| Chocar con superpowers en Modo A | Regla explícita en cada pieza: solo Modo B (T-06/T-08/T-09, criterios) |

## Criterios de éxito del plan

- Con `docs/CONSTITUTION.md` de juguete que veta algo, la lente A marca gap citando la línea (E2E de T-11).
- `/spec-drift` sobre una spec de juguete produce DRIFT.md con ✓/✗/no-verificable correctos (E2E de T-11).
- Un criterio `[GWT]` con su ID en test-plan cuenta como cubierto en `coverage-check.py` (test de T-04).
- Con `tdd: true`, el ledger muestra evidencia del rojo antes del verde; con `dev.json` ausente, todo funciona como hoy.
- `lint_plugin.py` y todas las suites en verde; los 4 artefactos de esta iniciativa con `generacion:` `fuente: medido`.

## Referencias

[`spec.md`](spec.md) · [`evaluation.md`](evaluation.md) · [`tasks.md`](tasks.md) · análisis comparativo 2026-08-12 (superpowers / Spec Kit / LiorCohen-sdd / Agent-Monitor)
