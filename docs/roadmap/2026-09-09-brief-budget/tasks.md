---
tasks: brief-budget
estado: completado        # borrador | en-progreso | completado | cancelado
descripcion: >
  Cerrar la iniciativa de `brief-budget` para que el brief del subagente cumpla 10.000 caracteres sin
  tocar el tope global, sin recortar contrato ni requisitos vigentes y sin tocar persona o memoria. Ejecutar en orden:
  C-05 en `xfail` de inicio, C-02, C-04, C-03, C-01 y cierre de C-05.
creado: 2026-09-09
actualizado: 2026-10-06
changelog: Fixed
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
| **Estado** | completado |
| **Fecha** | 2026-09-09 |
| **Plan** | [`improvement-plan.md`](./improvement-plan.md) |
| **Spec** | [`spec.md`](./spec.md) |
| **Evaluación** | [`evaluation.md`](./evaluation.md) |
| **Análisis de origen** | [`analysis.md`](./analysis.md) |

> **⚠️ Ledger canónico de progreso.** Este fichero es la **fuente única de verdad** del avance del plan.
> Cada tarea debe quedar marcada con checkbox y estado al cerrarse, con la evidencia de verificación en el mismo bloque.

## Ejecución — 2026-10-06

Implementación realizada; cierre validado con revisión y puertas finales. Historial accesible en el ledger, criterios intactos y excepción de mínimo protegido documentada en la spec. Las estimaciones históricas se conservan; los ceros del bloque de planificación no representan consumo de esta ejecución, que no dispone de medición compatible con Codex.

- RED: el fixture de presupuesto compartido falló con `11694 > 10000` antes de introducir el ajuste global auxiliar — 2026-10-06.
- Verificación provisional: `test_task_brief.py` → 73 passed, 0 xfailed. Las mediciones finales y los veredictos independientes se añaden en el informe de pruebas.
- El cierre de esta iniciativa no cierra por sí solo `plugin-refactor`, que mantiene su propio ledger.

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. IA ejecutadas | H. IA objetivo | H. humanas objetivo |
|------|------------|-------|----------|------------------|-----------------|--------------------|
| Fase 0 — Guardia del CA-08 de todos los ledgers | 1 | 1 | 100% | no medido | 2,0 h | 5,5 h |
| Fase 1 — Diseño bajo demanda | 1 | 1 | 100% | no medido | 2,0 h | 6,0 h |
| Fase 2 — Verificación sin evidencia | 1 | 1 | 100% | no medido | 2,0 h | 1,5 h |
| Fase 3 — Gaps sólo de la tarea | 1 | 1 | 100% | no medido | 0,0 h* | 1,5 h |
| Fase 4 — Presupuesto por sección | 1 | 1 | 100% | no medido | 2,0 h | 4,0 h |
| Cierre y revisión transversal | 1 | 1 | 100% | no medido | 5,5 h | 1,4 h |
| **TOTAL** | **6** | **6** | **100%** | **no medido** | **16,5 h** | **26,4 h** |

_Nota:_ para C-03 la tabla separa la parte de estimación de lógica: base 1,5 h se ejecuta sobre tarea concreta;
la parte de revisión de proceso se traza en Cierre.

## Fase 0 — Guardarraíl de CA-08 para todos los ledgers (`xfail` inicial)

**Estado**: completado · **Estimado**: 3,0 h · **Coste est.**: 151,79 € · **Prioridad**: Crítica

### T-01 — C-05: test CA-08 sobre todos los ledgers (`xfail` fechado en fase inicial)

- **Changelog**: La prueba del presupuesto recorre los ledgers reales con diseño, constitución y memoria; exige tamaño acotado o aviso exacto del mínimo irreducible.

- **Descripción**: `agent-kits/shared/test_task_brief.py` deja de validar sólo `memory-retrieval` y añade test
  parametrizable sobre `docs/roadmap/*/tasks.md` con `design.md` y sin él. Hasta que C-01 a C-04 hayan cerrado
  la brecha de tamaño, el test va en `xfail` con fecha y motivo explícito.
- **Estado**: completado
- **Tiempo humano objetivo**: 3,0 h
- **Dependencias**: ninguna
- **Archivos**: `docs/roadmap/CALIBRATION.md`, `agent-kits/shared/test_task_brief.py`
- **Tipo**: backend
- **Verificación**: `python -m pytest agent-kits/shared/test_task_brief.py -q` → suite verde, sin xfail.

**Criterios de aceptación**:
- [x] 8+ tareas o repos con diseño y sin diseño quedan cubiertas por el guardarraíl.
- [x] No aparece aviso silencioso de suite verde con regresión en un ledger no cubierto.
- [x] Se conserva la evidencia del `xfail(strict=True)` inicial fechado 2026-09-14; la prueba final no tiene xfail.
- [x] Final: `CA-05` verde y sin `xfail` de esta iniciativa.

## Fase 1 — Diseño bajo demanda (`C-02`)

**Estado**: completado · **Estimado**: 6,0 h · **Coste est.**: 304,05 € · **Prioridad**: Alta

### T-02 — O2: diseño solo si la tarea lo necesita

- **Changelog**: El brief selecciona módulos de diseño por rutas concretas y omite los ajenos; el diseño sin tabla conserva un respaldo acotado.

- **Descripción**: `task-brief.py` inyecta `## Diseño` solo cuando la tarea referencia módulos del `design.md §5`.
  Si no, emite puntero en una sola línea y conserva contrato de sección.
- **Estado**: completado
- **Tiempo humano objetivo**: 6,0 h
- **Dependencias**: T-01 finalizada (para no cerrar brecha ciega)
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/task-brief.py`, `agent-kits/shared/test_task_brief.py`, `agent-kits/architect/templates/design.md`
- **Verificación**: `python -m pytest agent-kits/shared/test_task_brief.py -q` → suite verde, sin xfail.

**Criterios de aceptación**:
- [x] `## Diseño` deja de ser constante en las 22 tareas.
- [x] Al menos dos patrones:
  - tarea con referencia real al diseño incluye sección completa o recortada con tope
  - tarea sin referencia devuelve puntero en una sola línea
- [x] El criterio `design.md` se define de forma determinista y testeado en `tmp_path`.

## Fase 2 — Verificación sin evidencia (`C-04`)

**Estado**: completado · **Estimado**: 2,0 h · **Coste est.**: 101,46 € · **Prioridad**: Media

### T-03 — O4: `Verificación` sin salida pegada

- **Changelog**: El brief enlaza la evidencia ejecutada al ledger y conserva comandos, resultados esperados, criterios y decisiones vigentes.

- **Descripción**: Ajustar `task-brief.py` y pruebas para mantener solo comando y resultado esperado;
  eliminar cola de evidencia pegada de los ledgers reales (salvo nota breve necesaria).
- **Estado**: completado
- **Tiempo humano objetivo**: 2,0 h
- **Dependencias**: T-02
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/task-brief.py`, `agent-kits/shared/test_task_brief.py`, `docs/roadmap/2026-09-09-brief-budget/**`
- **Verificación**: `python -m pytest agent-kits/shared/test_task_brief.py -q` → suite verde, sin xfail.

**Criterios de aceptación**:
- [x] T-02 de referencia no conserva bloques de salida como texto pegado.
- [x] No aumentan cambios en `ledger-lint` sin cobertura determinista.
- [x] CA-04 verde en corpus medido.

## Fase 3 — Gaps de la tarea (`C-03`)

**Estado**: completado · **Estimado**: 1,5 h · **Coste est.**: 76,13 € · **Prioridad**: Media

### T-04 — O3: `## Gaps pendientes de revisión` acotado y por tarea

- **Changelog**: Los gaps relevantes se limitan a la tarea y al último intento; su sección tiene presupuesto propio.

- **Descripción**: Mantener el filtro `Tarea == tid` del último intento y acotar por tope para filas largas.
  Incluir test de regresión de dos tareas en mismo ledger y validación explícita de la premisa de filtro.
- **Estado**: completado
- **Tiempo humano objetivo**: 1,5 h
- **Dependencias**: T-03
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/task-brief.py`, `agent-kits/shared/test_task_brief.py`, `docs/roadmap/2026-09-09-brief-budget/**`
- **Verificación**: `python -m pytest agent-kits/shared/test_task_brief.py -q` → suite verde, sin xfail.

**Criterios de aceptación**:
- [x] Se valida con fixture `tmp_path` que no se cuelan filas de otras tareas.
- [x] La medición `gaps` entra bajo tope sin perder evidencia útil del propio task.
- [x] CA-06 de scope de tarea verde.

## Fase 4 — Topes por sección (`C-01`)

**Estado**: completado · **Estimado**: 4,0 h · **Coste est.**: 202,78 € · **Prioridad**: Alta

### T-05 — C-01: constantes `*_TOPE_CHARS` por sección

- **Changelog**: Diseño, gaps y verificación tienen topes propios; el ajuste global preserva memoria y suelo de persona e informa contratos que requieren dividirse.

- **Descripción**: Crear `DISENO_TOPE_CHARS`, `GAPS_TOPE_CHARS` y `VERIFICACION_TOPE_CHARS` con recorte alineado por
  sección y comentario de justificación de medición en el contrato de código.
- **Estado**: completado
- **Tiempo humano objetivo**: 4,0 h
- **Dependencias**: T-04
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/task-brief.py`, `agent-kits/shared/test_task_brief.py`, `docs/roadmap/2026-09-09-brief-budget/**`
- **Verificación**: `python -m pytest agent-kits/shared/test_task_brief.py -q` → suite verde, sin xfail.

**Criterios de aceptación**:
- [x] `## Diseño` deja de depender de `design.md` global.
- [x] `Gaps` y `Verificación` quedan por debajo del nuevo tope salvo evidencia explícita justificada.
- [x] El aviso final de runtime conserva causa por sección y no rompe contract.

## Fase 5 — Cierre y revisión final

**Estado**: completado · **Estimado**: 1,5 h + revisión de dos lentes 5,5 h

### T-06 — Revisión de dos lentes y cierre

- **Changelog**: Revisión y regresiones cierran el presupuesto del brief con informe real, retrospectiva y exportación sin deriva.

- **Descripción**: Revisión de dos lentes con `scope-check` al final de cada fase,
  corrección y cierre de la iniciativa:
  C-05 sale de `xfail` y pasa a verde, puertas y `retro` habilitadas.
- **Estado**: completado
- **Tiempo humano objetivo**: 1,5 h
- **Tipo**: docs
- **Archivos**: `agent-kits/shared/task-brief.py`, `agent-kits/shared/test_task_brief.py`, `docs/roadmap/2026-09-09-brief-budget/**`
- **Verificación**: `python -m pytest agent-kits/shared/test_task_brief.py -q` → suite verde, sin xfail.

**Criterios de aceptación**:
- [x] `CA-01`, `CA-02`, `CA-03`, `CA-04`, `CA-05` verdes en la suite de `test_task_brief.py`.
- [x] Se entrega la dependencia de brief-budget a plugin-refactor sin alterar el estado de sus tareas ajenas.
- [x] La iniciativa sale con `spec`/`evaluation` consistentes y evidencia de puertas completadas.



## Revisión de dos lentes — intento 1: Fase 5 (T-01, T-02, T-03, T-04, T-05, T-06) — tres Important

Lentes A+B mediante fallback genérico; reviewer no está disponible como tipo de herramienta.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | Notas fix previas podían contener decisiones vigentes | T-05 | corregido: conservar todas las notas | RED: faltaba rename/link; fixture notas_previas verde |
| 2 | Important | Encabezado dentro de fence partía diseño | T-02 | corregido: encabezados fuera de fences | RED: 1 fence; fixture no_separa_encabezados verde |
| 3 | Important | Verificación con solo salida volvía a La tarea | T-03 | corregido: campo declarado se retira aunque quede vacío | RED: OUTPUT_HISTORY presente; fixture solo_evidencia verde |

## Revisión de dos lentes — intento 2: Fase 5 (T-01, T-02, T-05, T-06) — cuatro Important

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 4 | Important | Nota sin viñeta tras RED se perdía | T-05 | corregido: cualquier campo bold cierra historial | RED: faltaba current decision; campos_sin_vineta verde |
| 5 | Important | Diseño podía dejar comentario HTML abierto | T-02 | corregido: cortes con estado estructural cerrado | RED: 1 apertura, 0 cierres; comentarios_html verde |
| 6 | Important | Persona larga declaraba mínimo falso | T-05 | corregido: medir nota y salto final dentro de margen flexible | RED: 10140 > 10000; minimo_falso verde |
| 7 | Important | CA-01/02 prometían cero excesos con constitución real | T-06 | corregido: excepción explícita y dos contextos medidos | invocación normal 10/22 excesos irreducibles; informe final |

La expectativa antigua de conservar RED con verificación vacía se actualizó al contrato de historial enlazado: fixture anterior y tres regresiones verdes.

## Revisión de dos lentes — intento 3: Fase 5 (T-01, T-02, T-03, T-04, T-05, T-06) — sin gaps

Lente A+B y lente B independientes: 0 Critical, 0 Important, 0 Minor pendientes. Correcciones verificadas por lectura y 11 tests brief_budget / 3 regresiones enfocadas verdes. C+D no detectaron riesgos introducidos en el diff coordinado de hooks/brief. QA y cierre documental a cargo del orquestador.

Puerta de alcance coordinada: unión exacta de los campos Archivos de hooks-runtime y brief-budget, `scope-check --base HEAD` exit 0, sin avisos ni producción excluida. `.claude/settings.json` era ajeno y queda sin modificar. catálogo de referencia solo conserva su análisis autorizado.

## Cierre — 2026-10-06

6/6 tareas completadas. Evidencia final: [testing/report.md](testing/report.md); retrospectiva: [retro.md](retro.md). Cobertura Python changed-only 94,45%, gate90 verde. Contratos irreducibles requieren dividir la tarea. Sin publicación de versión ni cierre de iniciativas vecinas.
