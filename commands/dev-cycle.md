---
description: Orquesta el ciclo completo de una iniciativa (spec → evaluación → plan → implementación → pruebas → documentación). Detecta si superpowers está disponible: si lo está, delega en él el backbone de desarrollo y añade la capa de dominio; si no, usa la cadena nativa. Invoca los agentes por nombre y con puertas de control.
argument-hint: <objetivo de la iniciativa>
---

# /dev-cycle — orquestador del ciclo de desarrollo

Ejecuta el ciclo de una iniciativa de forma explícita y fiable. Objetivo: **$ARGUMENTS**.

Mantén `docs/roadmap/<fecha>-<slug>/tasks.md` como **ledger canónico** de progreso en todo el
ciclo (ver regla 8 de `docs/CONVENTIONS.md`), sea cual sea el motor de implementación.

## Fase 0 — Preparación y detección
1. Deriva un `<slug>` corto en kebab-case del objetivo y fija/crea la carpeta `docs/roadmap/<fecha>-<slug>/` (reutilízala si ya existe).
2. **Detecta si superpowers está disponible** (sus skills instaladas, p. ej. `using-superpowers` / `subagent-driven-development` / `writing-plans`). Anota el modo:
   - **Modo A — con superpowers:** delegas en él el backbone de desarrollo.
   - **Modo B — nativo (sin superpowers):** usas la cadena de agentes de este plugin.
3. Ofrece añadir al `CLAUDE.md` del proyecto (si no está) la **regla de ledger canónico**: "El progreso de un plan se registra en `docs/roadmap/<…>/tasks.md`; cualquier implementador —incluidos orquestadores externos como superpowers SDD— debe marcar ahí cada tarea; los ledgers propios son espejo, no fuente."

> La **capa de dominio** (evaluación/presupuesto, seguridad, documentación, Confluence, PDF) es de este plugin y se ejecuta **en ambos modos**. Lo único que cambia entre A y B es **quién hace el backbone** (spec/plan/implementación/pruebas/review).

## Fase 1 — Evaluar (siempre, agente `evaluator`)
Invoca **`evaluator`** con el objetivo: crea/lee `spec.md` y produce `evaluation.md` (coste, esfuerzo, veredicto). Esto es valor propio (presupuesto en €/tokens) y va en los dos modos.

**Puerta go/no-go:** muestra el veredicto y pregunta si continuar. Si no-go, para.

## Fase 2 — Planificar (siempre, agente `planner`)
**En los dos modos**, tu `planner` genera **tus artefactos** en `docs/roadmap/<…>/`:
`improvement-plan.md` + `tasks.md` (+ `test-plan.md` si hay UI). Estos ficheros son tuyos y con
tus plantillas — **no se delega la planificación**, para que tu estructura y tu ledger existan
siempre. Puerta: OK del plan.

> Si en Modo A superpowers aporta un `brainstorming`/design doc, incorpóralo como contenido de la
> `spec.md`; el plan ejecutable y el progreso viven en TU `improvement-plan.md` + `tasks.md`.

> **Jira (opcional, opt-in).** Recién creado el plan, `planner` **ofrece** volcar las tareas a Jira
> con la skill `jira-sync` (un issue por tarea bajo el proyecto/épica elegidos; selector visual en
> Cowork o conversacional en CLI/VS Code). Luego, durante la implementación, al completar cada tarea
> `implementer` imputa horas (Tiempo IA + Supervisión, tope jornada) y marca el issue *Done*. Todo
> sujeto al opt-in de `.claude/jira.json`: aunque el conector esté conectado, si Jira no se activó
> para el proyecto, no se toca nada.

## Fase 3 — Implementar y probar (según el modo)

**Modo A (con superpowers):** delega solo la **ejecución** en superpowers —
`subagent-driven-development`/`executing-plans`, `test-driven-development`, `requesting-code-review` —
pero trabajando **contra tu `tasks.md`**: debe marcar ahí cada tarea (ledger canónico). Aprovechas
su TDD, worktrees y review maduros; tus ficheros de `docs/roadmap/` siguen siendo la fuente.
**Las transiciones de estado las aplicas TÚ (el orquestador), no superpowers** (que no toca tus
artefactos): pon el plan y la fase activa en `en-progreso` antes de delegar, asegúrate de que las
tareas quedan marcadas en `tasks.md` durante la ejecución, y al cerrar aplica plan → `completado`
y spec → `implementada`. Si superpowers marca su propio ledger, vuélcalo a `tasks.md`.

**Modo B (nativo, sin superpowers):**
1. **`implementer`** → implementa fase a fase sobre rama, marcando `tasks.md` por tarea.
2. **`qa`** → pruebas E2E (solo local), informe y evidencias.

En ambos modos, al salir debes tener: código implementado, pruebas en verde y `tasks.md` al día.
La puerta de pruebas aplica igual: si rojo, corrige; si verde, sigue.

## Fase 4 — Documentar (siempre, agente `documenter`)
Con las pruebas en verde, invoca **`documenter`** para generar/actualizar la documentación del proyecto (una vez al final, no por tarea).

## Fase 5 — Seguridad (opcional, agente `nemesis`)
Si el usuario lo pide o la iniciativa lo amerita, invoca **`nemesis`** para auditar la seguridad de lo construido (solo entornos locales/privados).

## Fase 6 — Sincronizar y cerrar
La documentación/artefactos se sincronizan con Confluence vía `confluence-publish` (opt-in; la invocan los agentes al escribir en `docs/`). Cierra con un resumen: modo usado (A/B), iniciativa, tareas completadas, estado de pruebas, ruta de la doc y enlaces.

## Transiciones de estado (OBLIGATORIAS en cada fase)
Los artefactos nacen en `borrador`. En **cada fase/puerta** que se supera, actualiza su estado
(frontmatter + cabecera) al que toque; **no dejes nada en `borrador`** al avanzar. Vocabularios:
spec = `borrador · aprobada · implementada · obsoleta`; evaluación/plan/tareas = `borrador ·
en-progreso · en-revision · completado · cancelado`.

| Momento | spec | evaluación | plan / tasks |
|---|---|---|---|
| Tras evaluar (Fase 1) | borrador | `en-revision` | — |
| Puerta **go** | `aprobada` | `completado` | — |
| Puerta **no-go** | (obsoleta si se descarta) | `cancelado` | — |
| Plan creado (Fase 2) | aprobada | completado | `borrador` |
| Puerta OK del plan → arranca impl. | aprobada | completado | `en-progreso` (plan y fase activa) |
| Durante impl. (Fase 3) | aprobada | completado | tareas `en-progreso`→`completado`; fase `completado` al cerrar |
| qa en rojo | aprobada | completado | tarea/plan → `en-progreso` (reabrir) |
| Cierre (qa verde + documentado) | `implementada` | completado | plan `completado` |
| Cancelación en cualquier punto | (obsoleta) | `cancelado` | `cancelado` |

Aplica la transición **en el mismo paso** en que se cruza la puerta, y mantén coherente la tabla
de resumen de `tasks.md`.

**Estas transiciones son responsabilidad del orquestador y se aplican en LOS DOS MODOS.** En
**Modo A** superpowers no actualiza tus estados ni tu `tasks.md` por su cuenta: eres tú quien
aplica las transiciones sobre tus artefactos y quien garantiza que `tasks.md` refleje el progreso
(volcando el ledger de superpowers si hace falta). En **Modo B** las aplican `implementer`/`qa`,
que ya lo tienen en sus instrucciones.

## Reglas del orquestador
- **Invoca a los agentes por nombre**; no dependas de la auto-delegación.
- **No dependas de superpowers:** si no está, el Modo B hace el ciclo completo con los agentes del plugin.
- **`tasks.md` es la fuente única de progreso** en los dos modos.
- **Respeta las puertas** (go/no-go, OK de plan, verde de pruebas).
- Si el usuario pide solo una parte (p. ej. "solo planifica"), ejecuta hasta esa fase y detente.
