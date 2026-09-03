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
3. **Descubrimiento (opcional).** Si el objetivo llega **poco definido** (idea vaga, sin alcance/criterios claros), **ofrece** un paso previo con el agente **`analyst`**: afina la idea con preguntas dirigidas y deja una `spec.md` sólida antes de presupuestar (no se estima sobre ambigüedades) — es la puerta de entrada única al descubrimiento (`ADR-011`; antes existía una skill `discovery` separada, retirada por redundante). Si ya hay una spec madura, sáltalo y ve directo a evaluar.

> **Modelo del agente (tiering configurable, capa 2).** Antes de despachar un agente por nombre, resuelve su tier efectivo y pasa `model` en el parámetro `model` del Agent tool (contrato oficial: el parámetro por invocación gana al frontmatter; el `effort` de `dev.json` es informativo porque el Agent tool no lo admite por invocación — el efectivo es el del frontmatter):
>
> ```bash
> SHAREDKIT="$(find "$PWD/.claude" "$HOME/.claude" -type d -path '*agent-kits/shared' 2>/dev/null | head -1)"
> python3 "$SHAREDKIT/model-tier.py" evaluator --json     # {"model": "...", "effort": "...", "fuente": {...}}
> ```
>
> Sin `dev.json` `modelos.<agente>` (o sin el script — instalación parcial) → no pases `model`: el frontmatter del agente manda. Aplica a `evaluator` y, en Fase 2-bis, a `architect`.

## Fase 1 — Evaluar (agente `evaluator`)
Invoca **`evaluator`** con el objetivo. El agente:
- Crea/lee `spec.md` y produce `evaluation.md` (coste €, esfuerzo en horas, previsión de tokens, complejidad, riesgos, veredicto) con sus plantillas.
- Enlaza spec↔evaluación (bidireccional) y mantiene el índice `docs/roadmap/README.md`.
- Al terminar de evaluar, deja la evaluación en `en-revision`.

> **Medición del coste de generación (usage-meter) — regla de no-solape.** Cada agente de la
> cadena mide su propio artefacto (`usage-meter.py start`/`close`, bloque `generacion:` del
> frontmatter). Como orquestador, asegúrate de que cada agente **cierra su marcador antes de
> invocar al siguiente** (analyst cierra la spec antes de que evaluator abra la evaluación):
> dos ventanas solapadas cuentan los mismos tokens en ambos artefactos y reparten mal el coste.

> El campo **Plan** de la evaluación y el `plan:` de la spec quedan **`pendiente`**: en pm-cycle
> el plan **no** se crea (eso es `/dev-cycle` → `planner`).

## Fase 2 — Puerta go/no-go y CIERRE
Muestra el veredicto y pregunta si se aprueba. Este es el **final del ciclo PM** en cualquier caso:

- **Go (aprobada):** aplica spec → `aprobada` y evaluación → `completado`. **Cierra** con un
  resumen (iniciativa, coste €, esfuerzo, tokens, nº de características, veredicto y ruta de los
  artefactos) y **ofrece el handoff** en una línea, sin ejecutarlo:

  > Evaluación aprobada. Para planificar e implementar, lanza `/dev-cycle` sobre esta iniciativa
  > (`docs/roadmap/<fecha>-<slug>/`): ya tiene la spec **aprobada** y la evaluación **completada**
  > (y el `design.md` **aprobado**, si hiciste el paso de diseño), así que arrancará directo en la
  > planificación (`planner`).

- **No-go (se descarta):** aplica evaluación → `cancelado` (spec → `obsoleta` si se descarta la
  idea). Cierra explicando por qué no conviene y qué haría falta para reconsiderarla.

- **A revisar:** si el usuario pide ajustar la spec, itera con `evaluator` (spec sigue `borrador`
  / evaluación `en-revision`) y vuelve a esta puerta.

## Fase 2-bis — Diseño (opcional, agente `architect`, solo tras un *go*)
Tras el go y antes del handoff, **ofrece en una línea**: «¿Quieres explorar el diseño antes de planificar
(`architect`: 2-3 opciones con trade-offs, validadas contigo)?» — **recomiéndalo** si la evaluación marca
complejidad **Alta** en alguna característica o señala riesgo arquitectónico (integraciones, cambios de
modelo de datos, decisiones difíciles de revertir); para cambios acotados, di que puede saltarse. Si
acepta, el paso es **en dos pasadas** (un subagente devuelve un solo mensaje: la validación por trozos la
haces TÚ, igual que la puerta go/no-go):

1. **Pasada 1.** Invoca **`architect`** por nombre (tier: `model-tier.py architect`) con la carpeta de la
   iniciativa y SIN `elegida:`. Devuelve `design.md` en `borrador` (`opcion_elegida: pendiente`) y un
   resumen estructurado: una línea por opción + la recomendada + la pregunta.
2. **Presenta al usuario por trozos** (paridad de clientes): en Cowork/escritorio, una **AskUserQuestion**
   con una opción por entrada (título · complejidad · riesgo · coste · reversibilidad) y la recomendada
   marcada; en CLI/VS Code, la misma información como **lista numerada** en texto y una pregunta
   («¿1, 2, 3 o una variante?»). Una opción por bloque; nada de volcar `design.md` entero.
3. **Pasada 2.** Re-invoca **`architect`** con `elegida: O<n>` (o `variante: <texto>` → vuelve a la pasada 1
   con la opción nueva). Fija `opcion_elegida`, escribe el ADR `propuesta`, enlaza `design:` en la spec y
   pasa `design.md` a `aprobado`. `/dev-cycle` lo recogerá en su Fase 2 y `planner` respetará la opción.

Sigue siendo rol PM: no se crea plan aquí.

## Fase 3 — Salidas opcionales del cierre (solo tras un *go*)
Ninguna es automática: **ofrécelas en una línea** y ejecútalas solo si el usuario acepta. No
bloquean el cierre del ciclo PM.

- **Brief de decisión (PDF).** Un one-pager para stakeholders con el veredicto y el presupuesto
  (título, resumen ejecutivo, cuadro de mando de la evaluación, riesgos clave y decisión). Genéralo
  a partir de `spec.md` + `evaluation.md` y conviértelo con la skill **`to-pdf`**;
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
- **Cierra en la evaluación.** pm-cycle **no** invoca a `planner`, `implementer`, `qa` ni `documenter` (el trabajo de desarrollo es de `/dev-cycle`). Las únicas salidas extra son el diseño opt-in de Fase 2-bis (`architect`, que tampoco planifica) y las de Fase 3 (brief PDF con la skill `to-pdf`, handoff a Jira), siempre opt-in y sin crear plan.
- **Handoff = puente, no ejecución.** En go, ofreces el comando siguiente en una línea; el usuario decide cuándo lanzarlo.
- **Misma carpeta y mismo slug** que usará `/dev-cycle`, para que la cadena `spec → evaluación → plan` sea trazable.
- **Confluence (opt-in):** la sincronización de `docs/` la hace el propio `evaluator` vía la skill `confluence-publish` al escribir; no la fuerces aquí.
