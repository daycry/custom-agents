---
evaluation: session-end-durable-capture
estado: completado
spec: spec.md
plan: improvement-plan.md
creado: 2026-09-17
generacion: {fuente: estimado, tokens_reales: {entrada: 0, salida: 0, cache_creacion: 0, cache_lectura: 0}, eur: null, horas_ia: 0.0, duracion: 0m, ratio_usado: 0}
---

# Evaluación - session-end-durable-capture

| Métrica | Estimado | Confianza |
|---|---:|---|
| Tiempo humano | 14h (12h base +20%) | Media-alta |
| Tiempo IA / supervisión | 4.2h / 1.1h | Media |
| Coste humano (50 EUR/h) | 700 EUR | Media |
| Tokens | 165k in / 65k out | Baja |

## Evaluación por característica

| ID | Alcance | Base | Riesgo |
|---|---|---:|---|
| C-01 | Capturador atómico + exec form | 2h | Payload de `SessionEnd` con `reason` o campos nuevos; se valida solo lo mínimo. |
| C-02 | Materializador con claim/done/dead-letter | 3h | Regresión del camino actual de escritura; se cubre con la suite de `test_journal.py` existente. |
| C-03 | Reconciliación en `SessionStart` con presupuesto | 2h | Bloquear el arranque; presupuesto y `max` fijos + test con 100 pendientes. |
| C-04 | `status`/`/doctor`/triage | 1.5h | Sección de doctor duplicando lógica; usa `journal.py status --json`. |
| C-05 | `outbox.py` + `redact.py` compartidos | 2h | Copias no declaradas (ADR-016); registrar en `copias.json` si viajan. |
| C-06 | Tests de shell, bench, doc, GOT | 1.5h | Bench no determinista en CI lenta; umbral p99 laxo y 30 iteraciones. |

## Comparación con el paquete externo (CA-HOOK-001)

El paquete estimaba 26-40 h y 15 tareas. La diferencia se explica por lo que **ya existe** en el repo y el paquete
daba por hacer: checkpoint por turno (`user-prompt-capture.sh`), idempotencia por `session_id`, escritura atómica
(`_escribir_atomico`), cerrojos (`_cerrojo`), redacción de secretos (`redactar`), suite de shell de hooks
(`tests/test_hooks_shell.py`) y sección de journal en `/doctor`. Lo que se conserva del paquete es el
**diseño** (capturar ≠ materializar, outbox/dead-letter, exec form, matriz de garantías, triage del
`Hook cancelled`).

**Veredicto: Go.** P0: el fallo es reproducible hoy y bloquea la fiabilidad de toda la cadena de memoria
(el journal es la entrada episódica que `/retro` promociona a candidatas). Ordenar **antes** de la Fase 3 de
`knowledge-services`, que consume `outbox.py`.
