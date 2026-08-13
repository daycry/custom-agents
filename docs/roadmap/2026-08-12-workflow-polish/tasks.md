---
generacion:               # vía rápida MEDIDA (usage-meter; primera vía rápida real del plugin)
  inicio: 2026-08-12T20:13:11Z
  fin: 2026-08-12T20:15:14Z
  fuente: medido
  tokens_reales: { entrada: 14, salida: 7134, cache_creacion: 9229, cache_lectura: 5188431 }
  eur: null                 # precioTokens sin verificar (rates-verify)
  horas_ia: 0.05
  duracion: 3m
  ratio_usado: 300000       # default no calibrado
---

# Checklist de Tareas — workflow-polish (vía rápida: las 3 skills de superpowers que faltaban)

| | |
|---|---|
| **Estado** | completado |
| **Fecha** | 2026-08-12 |
| **Plan** | n/a — **vía rápida** (sin spec/evaluación/plan; ledger ligero + revisión de dos lentes + verificación) |

> **⚠️ Ledger canónico de progreso.** Este fichero es la **fuente única de verdad** del avance del plan. **Cualquier** implementador —el agente `implementer`, el chat principal, o un orquestador externo (p. ej. *superpowers SDD*)— **debe** marcar aquí cada tarea (checkbox + estado) al completarla y actualizar el resumen. Los ledgers propios de otras herramientas son **espejo**, no fuente.

> **Origen:** análisis comparativo contra el catálogo v6.2.0 de superpowers (14 skills): 11 ya cubiertas nativas; esta vía rápida cierra las 3 restantes. Estimación gruesa: ~3,5 h base.

---

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervisión (real/est) | Tokens (real/est) |
|------|------------|-------|----------|-----------------------|------------------------|------------------------|-------------------|
| Fase 1 — Workflow polish | 3 | 3 | 100% | 0 / 3,5h | 0,05 (medido) / 1,1h | 0 / 0,3h | 16k (medido) / 330k |
| **TOTAL** | **3** | **3** | **100%** | **0 / 3,5h** | **0,05 (medido) / 1,1h** | **0 / 0,3h** | **16k (medido) / 330k** |

---

## Fase 1 — Workflow polish

**Estado**: completado · **Estimado**: 3,5h · **Real**: — · **Coste est.**: ~184 € · **Tokens est.**: 330k

### T-01 — Disciplina de RECIBIR la revisión (receiving-code-review)

- **Descripción**: El implementador (implementer o subagente) NO aplica los gaps del revisor a ciegas: **verifica cada señalamiento** contra el código/spec antes de corregir y, si un gap es incorrecto, lo **rebate con evidencia** (`fichero:línea` + por qué) en vez de "corregir" algo que estaba bien. El orquestador arbitra: gap rebatido con evidencia → se marca `descartado (rebatido)` en la traza de revisión y no cuenta para el bucle; sin evidencia → se corrige. Prosa en `commands/dev-cycle.md` (bucle de corrección) y `agents/implementer.md`.
- **Estado**: completado
- **Tiempo humano**: est. 1,0h · real —
- **Tiempo IA (ejec.)**: est. 0,3h · real — (medido)
- **Supervisión**: est. 0,1h · real —
- **Archivos**: `commands/dev-cycle.md`, `agents/implementer.md`

**Criterios de aceptación**
- [x] El bucle de corrección exige verificar cada gap antes de aplicarlo (nada de obediencia ciega)
- [x] Rebatir requiere evidencia concreta; el orquestador arbitra y deja traza (`descartado (rebatido)`)
- [x] Compatible con las severidades Critical/Important/Minor y con el tope de 3 intentos (rebatir no consume intento)

### T-02 — Despacho PARALELO de tareas independientes (dispatching-parallel-agents)

- **Descripción**: Con `subagentes: true`, las tareas de una misma fase **sin dependencias entre sí** (campo Dependencias del ledger) pueden despacharse en paralelo (lotes de máx. 3), cada subagente con su brief de `task-brief.py`; con `worktree: true`, cada tarea del lote en su propio worktree para no pisarse. El orquestador valida los retornos secuencialmente y marca el ledger. **Medición honesta en paralelo**: las ventanas de usage-meter se solapan, así que el lote se mide con UNA clave (`<slug>/lote-<n>`) y las horas se reparten proporcionalmente a la estimación de cada tarea, marcadas `(medido, lote)` — nunca se presenta como medición individual exacta. Prosa en `commands/dev-cycle.md`.
- **Estado**: completado
- **Tiempo humano**: est. 1,5h · real —
- **Tiempo IA (ejec.)**: est. 0,5h · real — (medido)
- **Supervisión**: est. 0,15h · real —
- **Archivos**: `commands/dev-cycle.md`

**Criterios de aceptación**
- [x] Solo tareas de la misma fase y sin dependencias mutuas; lotes de máx. 3; validación secuencial del orquestador
- [x] Con `worktree: true`, un worktree por tarea del lote (aislamiento real); sin él, el paralelo se limita a tareas que no toquen los mismos ficheros (según campo Archivos)
- [x] La medición del lote es honesta: clave única + reparto proporcional marcado `(medido, lote)`; jamás se presenta como medida individual
- [x] Con despacho secuencial (default), nada cambia

### T-03 — Ritual de CIERRE de rama (finishing-a-development-branch)

- **Descripción**: Paso explícito de cierre en `/dev-cycle` (tras qa verde y docs) y en `implementer` P6: (1) verificación final — suites y lint del proyecto en verde sobre la rama; (2) commits ordenados por tarea (`T-XX: …`), sin restos de instrumentación temporal; (3) **resumen de merge/PR** generado desde el ledger (título, qué se hizo por tarea, criterios cumplidos, evidencias de qa); (4) integración según el flujo del repo (merge directo o PR — preguntar si no está claro); (5) limpieza: rama/worktree eliminados tras integrar, marcadores de usage-meter cerrados (`status` sin huérfanos); (6) estados finales aplicados (plan `completado`, spec `implementada`).
- **Estado**: completado
- **Tiempo humano**: est. 1,0h · real —
- **Tiempo IA (ejec.)**: est. 0,3h · real — (medido)
- **Supervisión**: est. 0,05h · real —
- **Archivos**: `commands/dev-cycle.md`, `agents/implementer.md`

**Criterios de aceptación**
- [x] Los 6 pasos del ritual documentados en orden, con el resumen de PR derivado del ledger (no redactado de memoria)
- [x] La limpieza incluye worktrees y marcadores huérfanos del meter
- [x] Si el flujo de integración del repo no está claro, se pregunta (no se mergea por defecto)
