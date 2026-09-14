---
design: n/a
estado: en-progreso        # borrador | en-progreso | completado | cancelado
creado: 2026-09-09
actualizado: 2026-09-14
prioridad: alta
solicitante: usuario (decisión de lanzar la iniciativa aparte; opción B del hallazgo)
solicitud: opción del usuario del 2026-09-09 de cerrar el bloque de F1 y abrir iniciativa aparte
generacion:            # ventana compartida con este plan, spec.md y evaluation.md (se evita duplicación contable)
  inicio: 2026-09-09T17:56:55Z
  fin: 2026-09-14T00:00:00Z
  fuente: estimado
  tokens_reales: { entrada: 0, salida: 0, cache_creacion: 0, cache_lectura: 0 }
  eur: 0.00
  horas_ia: 0.00
  duracion: 0m
  ratio_usado: 479326
---

# Plan de implementación — 2026-09-09-brief-budget

## Resumen

- Estado: en-progreso
- Objetivo: que el brief de subagente vuelva a cumplir `BRIEF_TOPE_CHARS = 10000` sin subir el tope y sin recortar contrato ni persona.
- Alcance: los cinco cambios de `analysis.md` O1–O5 + revisión de dos lentes + cierre.
- Dependencia externa explícita: coordinación con `plugin-refactor` para mantener intacto `task-brief.py`.

## Criterio operativo de esta iniciativa

No se cierra la iniciativa hasta que:
- CA-01 (0 de 22 encima de 10.000 en `project-specialization`) salga verde.
- CA-02 (diseño deja de ser constante) salga verde.
- CA-05 (guardarraíl sobre todos los ledgers) salga verde y sin `xfail` restante.
- El bloque `plugin-refactor` no queda bloqueado por cambios sobre `task-brief.py` que fuerce refactor doble.

## Orden de ejecución recomendado

La orden queda fija por decisión del usuario:

1. C-05 en `xfail` fechado (fase de rojo controlado sobre guardarraíl).
2. C-02.
3. C-04.
4. C-03.
5. C-01.
6. C-05 en verde y cierre.

## Fases y presupuesto por bloque

| Fase | Estado | Esfuerzo base | Coste base | Tokens base (in / out) |
|---|---|---|---|---|
| Fase 0 — Guardarraíl de todos los ledgers | pendiente | 3,0 h | 151,79 € | 230 k |
| Fase 1 — Diseño bajo demanda | pendiente | 6,0 h | 304,05 € | 380 k / 60 k |
| Fase 2 — Verificación sin evidencia | pendiente | 2,0 h | 101,46 € | 140 k / 20 k |
| Fase 3 — Gaps de la tarea + tope | pendiente | 1,5 h | 76,13 € | 110 k / 15 k |
| Fase 4 — Presupuestos por sección | pendiente | 4,0 h | 202,78 € | 360 k / 40 k |
| Revisión de dos lentes (transversal) | pendiente | 5,5 h | 280,39 € | 1,19 M |
| Cierre y puertas | pendiente | 1,5 h | 75,00 € | 55 k |

## Estrategia de medición y validación

### Criterios de calidad

- `python3 -m pytest agent-kits/shared/test_task_brief.py -q -k ca08` para todas las ramas de verificación indicadas.
- `ledger-lint.py` en cada cierre parcial y final.
- `lint_plugin.py`, `scripts/export-interop.py --check` (si hay cambios en contratos/plantillas).
- Revisión de dos lentes por tramo con reproducción de cada gap.

### Riesgo de secuencia con `plugin-refactor`

Si `plugin-refactor` avanza primero y parte `main()` de `task-brief.py` en funciones, `brief-budget` debe integrar funciones con nombres por sección desde el inicio para evitar refactor doble.

## Checklist de fases

### Fase 0 — Guardarraíl visible desde el inicio (C-05)

- Objetivo: `ca08` extendido a `docs/roadmap/*/tasks.md` en `xfail` con fecha.
- Resultado esperado: suite controlada desde el primer commit, no silenciamiento de regresión.

### Fase 1 — Diseño bajo demanda (C-02)

- Objetivo: `## Diseño` aparece solo cuando la tarea toca el diseño definido en `design.md`.
- Resultado esperado: no constante de 3.510 para el 100% de tareas.

### Fase 2 — Verificación sin evidencia (C-04)

- Objetivo: `Verificación` no incluye cola de salida pegada.
- Resultado esperado: comando + resultado esperado, sin evidencia extensa.

### Fase 3 — Gaps por tarea (C-03)

- Objetivo: `## Gaps pendientes` queda limitada por columna de tarea y tope estable.
- Resultado esperado: se descartan entradas de otras tareas e historiales ajenos al contexto del brief actual.

### Fase 4 — Presupuesto por sección (C-01)

- Objetivo: constantes por sección para `Diseño`, `Gaps` y `Verificación`.
- Resultado esperado: corte claro por sección y aviso final agregado sin cambiar contrato.

### Fase 5 — C-05 verde + cierre

- Objetivo: guardarraíl pasa de `xfail` a verde con pruebas reales sobre toda la carpeta.
- Resultado esperado: iniciativa completa y listo para pasar el check de cierre.

## Dependencias técnicas

- `agent-kits/shared/task-brief.py`.
- `agent-kits/shared/test_task_brief.py`.
- `agent-kits/architect/templates/design.md` para reglas de sección O2.
- `docs/roadmap/2026-09-09-project-specialization/tasks.md` como corpus de validación y medición principal.

## Riesgos y mitigaciones principales

- La ruta de Windows (`GOT-008`) altera margenes de caracteres; se valida sobre la máquina objetivo.
- O2 puede quedar ambiguo si no se define criterio determinista: se bloquea a criterio de mapeo `Archivos`/`Dependencias` contra `design.md §5`.
- O3 puede encontrarse ya implementada en parte (`_gaps_pendientes_de_tarea`): se verifica antes de estimar cambios grandes.
- O1 mal definida puede recortar señal útil; por eso C-01 se deja al final, como red de salida.

## Criterio de éxito para la iniciativa

- `plan` ejecutado según orden.
- `tasks.md` completo con cada tarea marcada, incluyendo verificación y notas de cierre.
- `plugin-refactor` permite cerrar su tramo R4 sin tareas abiertas fuera de su backlog.

