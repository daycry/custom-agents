---
spec: subagent-personas
descripcion: Perfiles de dominio para el subagente de contexto fresco de /dev-cycle (C-08 de sdd-hardening) — el despacho elige una persona especializada (frontend, backend, base de datos, devops, tester…) según el tipo de la tarea, al estilo de los catálogos de wshobson/agents y LiorCohen/sdd, sin mantener 80 agentes: un catálogo corto de prompts de persona en el kit shared
estado: implementada      # borrador | aprobada | implementada | obsoleta
creado: 2026-08-12
actualizado: 2026-08-12
evaluacion: n/a — vía rápida (ledger ligero: tasks.md)
plan: n/a — vía rápida (ledger ligero: tasks.md)
generacion:
  inicio: 2026-08-12T08:20:00Z
  fin: 2026-08-12T08:22:00Z
  fuente: estimado          # spec borrador de backlog, redactada en la conversación de sdd-hardening
  tokens_reales: null
  eur: null
  horas_ia: 0.05
  duracion: 3m
  ratio_usado: 300000
---

# Perfiles de dominio para los subagentes de contexto fresco

> **Origen:** decisión del usuario durante la iniciativa [`2026-08-12-sdd-hardening`](../2026-08-12-sdd-hardening/spec.md) (C-08): las 4 mecánicas del ciclo de subagentes se incorporan allí; los perfiles de dominio se anotaron aquí como spec borrador.
>
> **Implementada** el 2026-08-12 como **vía rápida** (sdd-hardening ya cerrada): ledger en [`tasks.md`](tasks.md). Catálogo de 6 personas en `agent-kits/shared/personas/`, campo opcional `Tipo` en la plantilla de tareas del planner, e inyección en el brief por `task-brief.py` (+6 tests TDD).

## Idea

Cuando `/dev-cycle` despacha una `T-XX` a un subagente fresco (`subagentes: true`), hoy el subagente es genérico. Esta spec propone que el despacho elija una **persona de dominio** según el tipo de la tarea — frontend, backend, base de datos, devops, tester — inyectando al brief un bloque corto de especialización (convenciones, trampas típicas, criterios de calidad del dominio), al estilo de los catálogos de [wshobson/agents](https://github.com/wshobson/agents) (~80 especialistas) y [LiorCohen/sdd](https://github.com/LiorCohen/sdd) (7 agentes de dominio), pero **sin mantener un catálogo enorme**: 5-7 personas cortas en `agent-kits/shared/personas/`, elegidas por una etiqueta de tipo en la tarea del plan (`tipo: frontend|backend|db|devops|test|docs`) que el planner asigna al crear el ledger.

## Alcance tentativo

- Catálogo corto de personas (5-7) como fragmentos de prompt en el kit shared.
- Etiqueta `tipo:` por tarea en la plantilla de `tasks.md` (opcional; sin etiqueta → subagente genérico, como en sdd-hardening).
- `task-brief.py` añade la persona al brief cuando hay etiqueta.
- Fuera: catálogo grande estilo wshobson (mantenimiento), personas por proyecto (posible v2 vía constitución).

## Dependencias

- `2026-08-12-sdd-hardening` **cerrada** (C-08: despacho por subagentes + `task-brief.py`).

## Estimación gruesa (a validar por evaluator)

~2-2,5 h base. Valor: mayor calidad de primera pasada del subagente en tareas de dominio marcado; coste de mantenimiento contenido por diseño (catálogo corto).
