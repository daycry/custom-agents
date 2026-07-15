---
description: Orquesta el ciclo de PRODUCTO de una iniciativa (spec → evaluación) y CIERRA ahí. Separa el rol PM (definir y presupuestar) del rol de desarrollo. Invoca al evaluator por nombre, aplica la puerta go/no-go y, si es go, ofrece el handoff a /dev-cycle sobre la misma carpeta (sin ejecutarlo).
argument-hint: <objetivo o idea de la iniciativa>
---

# /pm-cycle — orquestador del ciclo de producto

Cubre **solo el rol de producto (PM)** de una iniciativa: convertir una idea en una
**especificación** y una **evaluación** (coste, esfuerzo, veredicto) para **decidir**, y
**cerrar ahí**. No planifica, no implementa, no prueba, no documenta: eso es `/dev-cycle`.
Objetivo: **$ARGUMENTS**.

Comparte la **misma carpeta por iniciativa** que `/dev-cycle` — `docs/roadmap/<fecha>-<slug>/` —
para que, cuando se decida ejecutar, `/dev-cycle` recoja el testigo sin repetir trabajo
(ver reglas 7 y 8 de `docs/CONVENTIONS.md`).

## Fase 0 — Preparación
1. Deriva un `<slug>` corto en kebab-case del objetivo y fija/crea la carpeta `docs/roadmap/<fecha>-<slug>/` (reutilízala si ya existe; usa el mismo slug en toda la cadena).
2. Si el usuario pasa una spec ya existente en esa carpeta, se evaluará; si pasa la idea/requisitos por el prompt, el `evaluator` **creará primero** la `spec.md` (estado `borrador`) y luego la evaluará.

## Fase 1 — Evaluar (agente `evaluator`)
Invoca **`evaluator`** con el objetivo. El agente:
- Crea/lee `spec.md` y produce `evaluation.md` (coste €, esfuerzo en horas, previsión de tokens, complejidad, riesgos, veredicto) con sus plantillas.
- Enlaza spec↔evaluación (bidireccional) y mantiene el índice `docs/roadmap/README.md`.
- Al terminar de evaluar, deja la evaluación en `en-revision`.

> El campo **Plan** de la evaluación y el `plan:` de la spec quedan **`pendiente`**: en pm-cycle
> el plan **no** se crea (eso es `/dev-cycle` → `planner`).

## Fase 2 — Puerta go/no-go y CIERRE
Muestra el veredicto y pregunta si se aprueba. Este es el **final del ciclo PM** en cualquier caso:

- **Go (aprobada):** aplica spec → `aprobada` y evaluación → `completado`. **Cierra** con un
  resumen (iniciativa, coste €, esfuerzo, tokens, nº de características, veredicto y ruta de los
  artefactos) y **ofrece el handoff** en una línea, sin ejecutarlo:

  > Evaluación aprobada. Para planificar e implementar, lanza `/dev-cycle` sobre esta iniciativa
  > (`docs/roadmap/<fecha>-<slug>/`): ya tiene la spec **aprobada** y la evaluación **completada**,
  > así que arrancará directo en la planificación (`planner`).

- **No-go (se descarta):** aplica evaluación → `cancelado` (spec → `obsoleta` si se descarta la
  idea). Cierra explicando por qué no conviene y qué haría falta para reconsiderarla.

- **A revisar:** si el usuario pide ajustar la spec, itera con `evaluator` (spec sigue `borrador`
  / evaluación `en-revision`) y vuelve a esta puerta.

## Fase 3 — Salidas opcionales del cierre (solo tras un *go*)
Ninguna es automática: **ofrécelas en una línea** y ejecútalas solo si el usuario acepta. No
bloquean el cierre del ciclo PM.

- **Brief de decisión (PDF).** Un one-pager para stakeholders con el veredicto y el presupuesto
  (título, resumen ejecutivo, cuadro de mando de la evaluación, riesgos clave y decisión). Genéralo
  a partir de `spec.md` + `evaluation.md` y conviértelo con el agente **`pdfy`** / skill `to-pdf`;
  guárdalo como `docs/roadmap/<fecha>-<slug>/decision-brief.pdf`. Preséntalo al usuario.

- **Épica en Jira (opcional).** El volcado de tareas a Jira vive en el ciclo de desarrollo (skill
  **`jira-sync`**, al crear el plan): ahí se crea un issue por tarea bajo el proyecto/épica elegidos,
  con selector visual o conversacional. En pm-cycle **no dupliques esa mecánica**; como mucho, si el
  usuario quiere adelantar un contenedor, ofrece crear **una épica** desde la spec aprobada (título +
  resumen ejecutivo + presupuesto de la evaluación) con `jira-sync`, y **anota su clave** en el
  frontmatter de la spec (`jira: PROJ-123`) para que `/dev-cycle` cuelgue después las tareas de ella.
  Confirma proyecto antes de crear nada; no asumas.

> Si el usuario no quiere ninguna, cierra sin más. Estas salidas convierten la decisión en algo
> accionable (documento para decidir / ticket para el equipo) sin salir del rol PM.

## Transiciones de estado (OBLIGATORIAS)
Los artefactos nacen en `borrador`; no dejes nada en `borrador` al cerrar. Vocabularios:
spec = `borrador · aprobada · implementada · obsoleta`; evaluación = `borrador · en-progreso ·
en-revision · completado · cancelado`. En pm-cycle solo se tocan **spec** y **evaluación**
(nunca plan/tasks, que son de `/dev-cycle`):

| Momento | spec | evaluación |
|---|---|---|
| Tras evaluar (Fase 1) | borrador | `en-revision` |
| Puerta **go** (Fase 2) | `aprobada` | `completado` |
| Puerta **no-go** | (`obsoleta` si se descarta) | `cancelado` |

Aplica la transición **en el mismo paso** en que se cruza la puerta y mantén coherente el índice
`docs/roadmap/README.md`. La transición final de la spec a `implementada` **no** ocurre aquí:
la aplica `/dev-cycle` al cerrar el desarrollo.

## Reglas del orquestador
- **Invoca al `evaluator` por nombre**; no dependas de la auto-delegación.
- **Cierra en la evaluación.** pm-cycle **no** invoca a `planner`, `implementer`, `qa` ni `documenter` (el trabajo de desarrollo es de `/dev-cycle`). Las únicas salidas extra son las de Fase 3 (brief PDF con `pdfy`, handoff a Jira), siempre opt-in y sin crear plan.
- **Handoff = puente, no ejecución.** En go, ofreces el comando siguiente en una línea; el usuario decide cuándo lanzarlo.
- **Misma carpeta y mismo slug** que usará `/dev-cycle`, para que la cadena `spec → evaluación → plan` sea trazable.
- **Confluence (opt-in):** la sincronización de `docs/` la hace el propio `evaluator` vía la skill `confluence-publish` al escribir; no la fuerces aquí.
