---
tasks: brief-budget
estado: en-progreso        # borrador | en-progreso | completado | cancelado
descripcion: >
  Cerrar la iniciativa de `brief-budget` para que el brief del subagente cumpla 10.000 caracteres sin
  tocar el tope global, sin recortar contrato ni tarea y sin tocar persona o memoria. Ejecutar en orden:
  C-05 en `xfail` de inicio, C-02, C-04, C-03, C-01 y cierre de C-05.
creado: 2026-09-09
actualizado: 2026-09-14
verificacion: obligatoria   # cada T-XX lleva `- **Verificación**:`; lo exige ledger-lint
generacion:            # se abre ahora la fase de planificación, ejecución real pendiente
  inicio: 2026-09-14T00:00:00Z
  fin: 2026-09-14T00:00:00Z
  fuente: estimado
  tokens_reales: { entrada: 0, salida: 0, cache_creacion: 0, cache_lectura: 0 }
  eur: 0.00
  horas_ia: 0.00
  duracion: 0m
  ratio_usado: 479326
---

# Checklist de Tareas — Presupuesto del brief por sección

| | |
|---|---|
| **Estado** | en-progreso |
| **Fecha** | 2026-09-09 |
| **Plan** | [`improvement-plan.md`](./improvement-plan.md) |
| **Spec** | [`spec.md`](./spec.md) |
| **Evaluación** | [`evaluation.md`](./evaluation.md) |
| **Análisis de origen** | [`analysis.md`](./analysis.md) |

> **⚠️ Ledger canónico de progreso.** Este fichero es la **fuente única de verdad** del avance del plan.
> Cada tarea debe quedar marcada con checkbox y estado al cerrarse, con la evidencia de verificación en el mismo bloque.

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. IA ejecutadas | H. IA objetivo | H. humanas objetivo |
|------|------------|-------|----------|------------------|-----------------|--------------------|
| Fase 0 — Guardia del CA-08 de todos los ledgers | 0 | 1 | 0% | 0,0 h | 2,0 h | 5,5 h |
| Fase 1 — Diseño bajo demanda | 0 | 1 | 0% | 0,0 h | 2,0 h | 6,0 h |
| Fase 2 — Verificación sin evidencia | 0 | 1 | 0% | 0,0 h | 2,0 h | 1,5 h |
| Fase 3 — Gaps sólo de la tarea | 0 | 1 | 0% | 0,0 h | 0,0 h* | 1,5 h |
| Fase 4 — Presupuesto por sección | 0 | 1 | 0% | 0,0 h | 2,0 h | 4,0 h |
| Cierre y revisión transversal | 0 | 1 | 0% | 0,0 h | 5,5 h | 1,4 h |
| **TOTAL** | **0** | **6** | **0%** | **0,0 h** | **16,5 h** | **26,4 h** |

_Nota:_ para C-03 la tabla separa la parte de estimación de lógica: base 1,5 h se ejecuta sobre tarea concreta;
la parte de revisión de proceso se traza en Cierre.

## Fase 0 — Guardarraíl de CA-08 para todos los ledgers (`xfail` inicial)

**Estado**: no iniciada · **Estimado**: 3,0 h · **Coste est.**: 151,79 € · **Prioridad**: Crítica

### T-01 — C-05: test CA-08 sobre todos los ledgers (`xfail` fechado en fase inicial)

- **Descripción**: `agent-kits/shared/test_task_brief.py` deja de validar sólo `memory-retrieval` y añade test
  parametrizable sobre `docs/roadmap/*/tasks.md` con `design.md` y sin él. Hasta que C-01 a C-04 hayan cerrado
  la brecha de tamaño, el test va en `xfail` con fecha y motivo explícito.
- **Estado**: no iniciada
- **Tiempo humano objetivo**: 3,0 h
- **Dependencias**: nada
- **Tipo**: QA
- **Criterios de aceptación**
- [ ] 8+ tareas o repos con diseño y sin diseño quedan cubiertas por el guardarraíl.
- [ ] No aparece aviso silencioso de suite verde con regresión en un ledger no cubierto.
- [ ] Existe evidencia `xfail(strict=True)` con fecha al menos en el primer intento.
- [ ] Final: `CA-05` verde y sin `xfail` de esta iniciativa.

## Fase 1 — Diseño bajo demanda (`C-02`)

**Estado**: no iniciada · **Estimado**: 6,0 h · **Coste est.**: 304,05 € · **Prioridad**: Alta

### T-02 — O2: diseño solo si la tarea lo necesita

- **Descripción**: `task-brief.py` inyecta `## Diseño` solo cuando la tarea referencia módulos del `design.md §5`.
  Si no, emite puntero en una sola línea y conserva contrato de sección.
- **Estado**: no iniciada
- **Tiempo humano objetivo**: 6,0 h
- **Dependencias**: T-01 finalizada (para no cerrar brecha ciega)
- **Tipo**: backend
- **Archivo(s)**: `agent-kits/shared/task-brief.py`, `agent-kits/shared/test_task_brief.py`, `agent-kits/architect/templates/design.md`
- **Criterios de aceptación**
- [ ] `## Diseño` deja de ser constante en las 22 tareas.
- [ ] Al menos dos patrones:
  - tarea con referencia real al diseño incluye sección completa o recortada con tope
  - tarea sin referencia devuelve puntero en una sola línea
- [ ] El criterio `design.md` se define de forma determinista y testeado en `tmp_path`.

## Fase 2 — Verificación sin evidencia (`C-04`)

**Estado**: no iniciada · **Estimado**: 2,0 h · **Coste est.**: 101,46 € · **Prioridad**: Media

### T-03 — O4: `Verificación` sin salida pegada

- **Descripción**: Ajustar `task-brief.py` y pruebas para mantener solo comando y resultado esperado;
  eliminar cola de evidencia pegada de los ledgers reales (salvo nota breve necesaria).
- **Estado**: no iniciada
- **Tiempo humano objetivo**: 2,0 h
- **Dependencias**: T-02
- **Tipo**: backend
- **Archivo(s)**: `agent-kits/shared/task-brief.py`, `agent-kits/shared/test_task_brief.py`
- **Criterios de aceptación**
- [ ] T-02 de referencia no conserva bloques de salida como texto pegado.
- [ ] No aumentan cambios en `ledger-lint` sin cobertura determinista.
- [ ] CA-04 verde en corpus medido.

## Fase 3 — Gaps de la tarea (`C-03`)

**Estado**: no iniciada · **Estimado**: 1,5 h · **Coste est.**: 76,13 € · **Prioridad**: Media

### T-04 — O3: `## Gaps pendientes de revisión` acotado y por tarea

- **Descripción**: Mantener el filtro `Tarea == tid` del último intento y acotar por tope para filas largas.
  Incluir test de regresión de dos tareas en mismo ledger y validación explícita de la premisa de filtro.
- **Estado**: no iniciada
- **Tiempo humano objetivo**: 1,5 h
- **Dependencias**: T-03
- **Tipo**: QA
- **Archivo(s)**: `agent-kits/shared/task-brief.py`, `agent-kits/shared/test_task_brief.py`
- **Criterios de aceptación**
- [ ] Se valida con fixture `tmp_path` que no se cuelan filas de otras tareas.
- [ ] La medición `gaps` entra bajo tope sin perder evidencia útil del propio task.
- [ ] CA-06 de scope de tarea verde.

## Fase 4 — Topes por sección (`C-01`)

**Estado**: no iniciada · **Estimado**: 4,0 h · **Coste est.**: 202,78 € · **Prioridad**: Alta

### T-05 — C-01: constantes `*_TOPE_CHARS` por sección

- **Descripción**: Crear `DISENO_TOPE_CHARS`, `GAPS_TOPE_CHARS` y `VERIFICACION_TOPE_CHARS` con recorte alineado por
  sección y comentario de justificación de medición en el contrato de código.
- **Estado**: no iniciada
- **Tiempo humano objetivo**: 4,0 h
- **Dependencias**: T-04
- **Tipo**: backend
- **Archivo(s)**: `agent-kits/shared/task-brief.py`, `agent-kits/shared/test_task_brief.py`
- **Criterios de aceptación**
- [ ] `## Diseño` deja de depender de `design.md` global.
- [ ] `Gaps` y `Verificación` quedan por debajo del nuevo tope salvo evidencia explícita justificada.
- [ ] El aviso final de runtime conserva causa por sección y no rompe contract.

## Fase 5 — Cierre y revisión final

**Estado**: no iniciada · **Estimado**: 1,5 h + revisión de dos lentes 5,5 h

### T-06 — Revisión de dos lentes y cierre

- **Descripción**: Revisión de dos lentes con `scope-check` al final de cada fase,
  corrección y cierre de la iniciativa:
  C-05 sale de `xfail` y pasa a verde, puertas y `retro` habilitadas.
- **Estado**: no iniciada
- **Tiempo humano objetivo**: 1,5 h
- **Tipo**: proceso
- **Archivo(s)**: `agent-kits/shared/task-brief.py`, `agent-kits/shared/test_task_brief.py`
- **Criterios de aceptación**
- [ ] `CA-01`, `CA-02`, `CA-03`, `CA-04`, `CA-05` verdes en la suite de `test_task_brief.py`.
- [ ] `brief-budget` queda listo para cerrar `plugin-refactor` sin tareas pendientes de su `Estado`.
- [ ] La iniciativa sale con `spec`/`evaluation` consistentes y evidencia de puertas completadas.

