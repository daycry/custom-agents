---
generacion:
  inicio: 2026-08-11T12:45:00Z
  fin: 2026-08-11T13:40:00Z
  fuente: estimado          # retroactivo: el artefacto se generó ANTES de desplegar usage-meter
  tokens_reales: null       # estimación a juicio: ~90k facturables
  eur: null                 # precioTokens sin verificar (rates-verify)
  horas_ia: 0.3
  duracion: 18m
  ratio_usado: 300000       # default no calibrado
---

# 2026-08-11-coste-generacion

> Coste real de generación de artefactos y tareas: script determinista `usage-meter.py` (tokens reales desde la transcripción JSONL de Claude Code), bloque `generacion:` en el frontmatter de spec/eval/plan/tasks, overhead de proceso en `/roadmap-metrics`, calibración del ratio tokens→hora en `/retro`, horas-IA medidas para el worklog por tarea y formato humano de duraciones (`XhYm`).

| | |
|---|---|
| **Fecha** | 2026-08-11 |
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
| Tiempo humano | **20,1 h** (16,75 h base +20 %) | 0 h | Media |
| Tiempo IA (ejecución) | **6,4 h** (+ 1,6 h supervisión) | 0 h | Media |
| Coste total | **~1.044 €** | 0 € | Media |
| Tokens IA | **~1,77 M** (in 1,51 M / out 0,26 M) | 0 | Baja |
| Multiplicador productividad | **×2,4** | — | — |
| Tareas | **10** | 0 hechas | — |

> **Herencia y delta.** Las horas por característica se **heredan de la evaluación sin re-estimar**: C-01 4,5 h · C-02 1,0 h · C-03 2,0 h · C-04 2,0 h · C-05 1,5 h · C-06 3,0 h · C-07 1,0 h · C-08 1,0 h = **16,0 h base (19,2 h con margen, ~995 €, ~1,69 M tokens)**. Este plan añade una **tarea de cierre** no presupuestada en la evaluación: E2E de juguete + actualización de índices (T-10, 0,75 h) → **delta +0,75 h base (+0,9 h con margen, +~40 €, +80k tokens)**. Total del plan: **16,75 h base / 20,1 h con margen / ~1.044 € / ~1,77 M tokens**.

---

## Estimación por fase

| Fase | Estimado (h) | Tokens (in / out) | Coste € |
|------|-------------|-------------------|---------|
| Fase 1 — Núcleo de medición (C-01, C-08) | 5,5 | 470k / 85k | ~287 € |
| Fase 2 — Contrato del dato e integración del ciclo (C-02, C-03) | 3,0 | 280k / 45k | ~157 € |
| Fase 3 — Visibilidad y calibración (C-04, C-05) | 3,5 | 320k / 55k | ~184 € |
| Fase 4 — Extrapolación a tareas y cierre (C-06, C-07 + cierre) | 4,75 | 440k / 75k | ~248 € |
| **Total (base)** | **16,75 h** | **1,51 M / 0,26 M** | **~876 €** |

> Horas y costes de la tabla son **base** (sin colchón). El margen de contingencia (+20 % sobre las horas base) está en el presupuesto de abajo: total con margen **~1.044 €**.

---

## Presupuesto económico

**Coste = (horas × tarifa) + coste de tokens de IA.** Todos los importes en **EUR**.

### Supuestos (ajustables)

| Parámetro | Valor | Nota |
|-----------|-------|------|
| Tarifa de desarrollo | 50 €/h | Default compartido (no existe `.claude/rates.json`); heredado de la evaluación |
| Modelo IA asumido | claude-opus-4-8 | Modelo previsto para la ejecución |
| Precio input | 13,80 € / 1M tokens | ⚠️ verificar — supuesto de trabajo (15 USD/M × 0,92), heredado de la evaluación |
| Precio output | 69,00 € / 1M tokens | ⚠️ verificar — supuesto de trabajo (75 USD/M × 0,92) |
| Tipo de cambio | 1 USD = 0,92 € | Default |
| Ratio de supervisión | 25 % de las horas IA | Default |
| Margen de contingencia | 20 % | Sobre horas base |

### Desglose

| Concepto | Cálculo | Importe |
|----------|---------|---------|
| Desarrollo (humano, base) | 16,75 h × 50 €/h | 837,50 € |
| Margen de contingencia | +20 % sobre desarrollo base | 167,50 € |
| Tokens IA (input) | 1,51 M tok × 13,80 €/M ⚠️ | 20,84 € |
| Tokens IA (output) | 0,26 M tok × 69,00 €/M ⚠️ | 17,94 € |
| **Total estimado (con margen)** | | **~1.044 €** |

---

## Resumen ejecutivo

El plugin presupuesta lo que cuesta construir, pero no lo que cuesta **decidir qué construir**: producir la spec, la evaluación y el plan no deja rastro de coste. Este plan lo corrige midiendo con **tokens reales** (transcripción JSONL de Claude Code, misma fuente que `ccusage`) lo que consume cada artefacto del ciclo y cada tarea de implementación. Decisión de fondo confirmada con el usuario: **fechas = contexto, tokens = medida, horas = tokens × ratio calibrado** — nunca del reloj de pared (las esperas por límite de tokens romperían el reloj sin ser trabajo). Cuatro fases: (1) el script `usage-meter.py` con verificación empírica del formato al frente + el helper de formato humano `XhYm`; (2) el bloque `generacion:` en las plantillas y el arranque/cierre del meter desde analyst/evaluator/planner y la vía rápida; (3) el overhead de proceso en `/roadmap-metrics` y la calibración del ratio en `/retro`; (4) la extrapolación a tareas (horas-IA medidas al worklog) y el cierre documental con un E2E de juguete.

## Arquitectura de la solución

- **Nuevo** `agent-kits/shared/usage-meter.py` (+ `test_usage_meter.py`): `start|close|status|fmt` por artefacto/tarea; marcadores en `.claude/usage-state.json`; suma de `usage` por ventana con sidechains; conversión € (`rates.json`) y horas (ratio de `CALIBRATION.md` > default); degradación a `fuente: estimado` sin bloquear; `--transcript-dir` inyectable para tests.
- **Plantillas** (evaluator/planner) y `tasks.md` ligero: bloque `generacion:` en frontmatter (inicio, fin, tokens_reales desglosado, eur, horas_ia, duración legible `XhYm`, ratio_usado, fuente).
- **Prosa de integración**: `agents/analyst.md`, `agents/evaluator.md`, `agents/planner.md`, `commands/dev-cycle.md` (vía rápida + marcador por `T-XX` en Modo B), `commands/retro.md` (ratio real → `CALIBRATION.md`), `skills/roadmap-dashboard/` (sección coste de proceso), `agent-kits/shared/estimation-defaults.md` (ratio default + precedencia).
- **Reutiliza**: `rates.json` + regla de fiabilidad (`rates-verify`), flujo real→est de `worklog.py plan` (las horas medidas entran como "real", sin tocar el script), traza `--attempt`/`[revisión]` de jira-granularity (los tokens del revisor van al bloque de revisión, no a la tarea).

## Fases y tareas

Detalle operativo, criterios y estado en [`tasks.md`](tasks.md) (ledger canónico).

| Fase | Tareas | Entrega |
|------|--------|---------|
| **Fase 1 — Núcleo de medición** | T-01 verificación empírica del JSONL · T-02 `usage-meter.py` + tests · T-03 helper `fmt` (formato `XhYm`) + tests | El script medidor completo y testeado, con el formato humano de duraciones |
| **Fase 2 — Contrato del dato e integración** | T-04 bloque `generacion:` en plantillas · T-05 arranque/cierre del meter en analyst/evaluator/planner + vía rápida | Todo artefacto nuevo del ciclo nace medido |
| **Fase 3 — Visibilidad y calibración** | T-06 coste de proceso en `/roadmap-metrics` · T-07 ratio real tokens→hora en `/retro` → `CALIBRATION.md` | El overhead se ve por iniciativa y el ratio se calibra con datos |
| **Fase 4 — Extrapolación y cierre** | T-08 medición por `T-XX` → horas-IA medidas al worklog · T-09 ratio default + documentación (CONVENTIONS, FLOWS, README shared) · T-10 E2E de juguete + índices | El worklog imputa medido, docs al día, verificación end-to-end |

## Riesgos del plan

| Riesgo | Mitigación en el plan |
|--------|----------------------|
| Formato JSONL distinto al asumido | T-01 lo verifica ANTES de escribir el parser (condición del go); parser tolerante + degradación testeada (criterio de T-02) |
| Doble contabilidad al reabrir artefacto/tarea | Criterio explícito de idempotencia en T-02 y T-08 (re-cierre sustituye) |
| Ratio default poco creíble al inicio | `ratio_usado` + `fuente` visibles (T-04); T-07 lo calibra con las primeras retros; T-09 lo declara "no calibrado" |
| Solape de marcadores | Regla "cerrar antes de abrir" en la prosa (T-05); limitación documentada |
| Formato de duraciones aplicado a medias | T-03 entrega el helper único; T-04/T-06/T-08 lo consumen (criterio en cada una); no se reimplementa a mano |

## Criterios de éxito del plan

- Una iniciativa de juguete completa el ciclo y sus 4 artefactos llevan bloque `generacion:` con `tokens_reales > 0` y `fuente: medido` (T-10).
- `pytest` de `usage-meter.py` en verde, incluida la degradación (transcripción ausente → `estimado`, sin bloquear) y el helper `fmt` (`0,53→32m`, `1,53→1h 32m`, `18→18h`).
- `/roadmap-metrics` muestra la sección de coste de proceso separada de implementación, con "sin datos" para iniciativas legacy (nunca 0 inventado).
- En Modo B, una tarea completada imputa al worklog horas-IA **medidas** (visible `fuente: medido` en el ledger); la aritmética de jornada/banco no cambia (tests de `worklog.py` siguen verdes).
- Todas las duraciones presentadas (frontmatter, tasks, informes, comentarios Jira) van en formato `XhYm`.

## Referencias

- [`spec.md`](spec.md) · [`evaluation.md`](evaluation.md) · [`tasks.md`](tasks.md)
- `agent-kits/shared/` (patrón de scripts deterministas + fragmentos compartidos) · `skills/jira-sync/scripts/worklog.py` (flujo real→est) · `commands/retro.md` (CALIBRATION.md)
