---
description: Orquesta el ciclo completo de una iniciativa (spec → evaluación → plan → implementación → pruebas → documentación). Detecta si superpowers está disponible: si lo está, delega en él el backbone de desarrollo y añade la capa de dominio; si no, usa la cadena nativa. Invoca los agentes por nombre y con puertas de control.
argument-hint: <objetivo de la iniciativa> [rapido | completo]
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

## Fase 0-bis — PUERTA DE ENTRADA: flujo completo vs. vía rápida
Antes de arrancar, **pregunta al usuario** cómo quiere abordarlo (una sola pregunta, con recomendación según el tamaño aparente del cambio):

- **Flujo completo** (Fases 1→6): `evaluator` (spec + presupuesto) → `planner` → implementación → revisión → qa → documentación. Para trabajo no trivial, con incógnitas, multi-fichero, o cuando quieras el presupuesto en €/tokens y la traza PM completa.
- **Vía rápida** (salta el papeleo PM, conserva la red de calidad): **omite Fases 1 y 2** (sin spec, sin evaluación, sin plan detallado). El orquestador crea directamente un **`tasks.md` ligero** en `docs/roadmap/<fecha>-<slug>/` (solo ese fichero: banner de ledger canónico + una fase + las tareas mínimas con criterios de aceptación verificables), va directo a **`implementer`**, y **mantiene las puertas de calidad**: la **revisión adversarial de dos lentes** (Fase 3) y **`qa`** con `qa-gate`. Cierra con `documenter` solo si el usuario lo pide. Para cambios pequeños/claros que se describen en una o dos frases.

**Si el usuario ya indica el modo, NO preguntes.** Respeta lo que pidió y arranca directo en ese modo:
- **Vía rápida explícita:** el objetivo trae "vía rápida", "rápido", "directo", "sin papeleo", "solo impleméntalo", o el argumento `rapido`/`--rapido`/`--quick`.
- **Flujo completo explícito:** "flujo completo", "con evaluación/presupuesto", "hazlo formal", o `--completo`/`--full`.

**Recomendación por defecto (solo si el usuario NO indicó modo):** si el objetivo se describe en una frase y toca pocos ficheros, propón **vía rápida**; si hay incógnitas, varias fases o el usuario quiere presupuesto, propón **flujo completo**. El usuario decide; respeta su elección.

> **Por qué la vía rápida NO salta la calidad.** El papeleo de PM (spec/evaluación/plan) es lo caro y prescindible en un cambio pequeño; la revisión de dos lentes y `qa-gate` son baratas y son la red que evita meter un bug "por ir rápido". Por eso la vía rápida ahorra ceremonia, no seguridad. El `tasks.md` ligero conserva el **ledger canónico**, así que el progreso, la imputación de horas y el volcado a Jira siguen funcionando igual. Si el usuario pide algo **trivial de verdad** (un typo, una línea), puede pedir explícitamente saltarse también la revisión/qa — pero no es el defecto.

Si es **vía rápida**, salta a la Fase 3 (implementación) usando el `tasks.md` ligero; si es **flujo completo**, sigue en la Fase 1.

## Fase 1 — Evaluar (siempre en flujo completo, agente `evaluator`)
Invoca **`evaluator`** con el objetivo: crea/lee `spec.md` y produce `evaluation.md` (coste, esfuerzo, veredicto). Esto es valor propio (presupuesto en €/tokens) y va en los dos modos.

**Puerta go/no-go:** muestra el veredicto y pregunta si continuar. Si no-go, para.

## Fase 2 — Planificar (solo en flujo completo, agente `planner`)
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

> **Punto de entrada de la vía rápida.** Si se eligió vía rápida, aquí se entra directamente con el `tasks.md` ligero (sin spec/evaluación/plan). El resto de la fase —implementación, revisión de dos lentes y qa— es idéntico; solo se ha saltado el papeleo PM.

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
2. **Revisión adversarial de DOS LENTES (contexto fresco, en paralelo).** Antes de `qa`, lanza **dos subagentes genéricos en paralelo** (Task tool) con contexto limpio — que NO hayan visto implementar — cada uno con una lente distinta:
   - **Lente A — conformidad con la spec/plan:** "Revisa el diff de la iniciativa `docs/roadmap/<fecha>-<slug>/` contra `improvement-plan.md` y `tasks.md`. Comprueba: (1) cada `T-XX` marcada como hecha está realmente implementada y cumple sus criterios; (2) nada fuera del alcance del plan (`git diff --stat`); (3) los criterios con test tienen su test. **Devuelve salida ESTRUCTURADA por criterio: `T-XX` → cada criterio de aceptación → ✓/✗**, más los gaps (fichero:línea). Solo gaps de requisitos, no estilo."
   - **Lente B — calidad y robustez del código:** "Revisa el diff de la iniciativa buscando SOLO defectos de corrección: casos límite sin manejar, errores silenciados, condiciones de carrera, inputs que rompen, regresiones probables. NO reportes preferencias de estilo ni sugerencias de refactor. Lista de defectos (fichero:línea, escenario concreto de fallo) o 'sin defectos'."

   **Fusiona** los dos resultados (deduplica gaps que señalen lo mismo). La lente A da el **veredicto por criterio** (✓/✗); la lente B aporta defectos de robustez a los gaps.

   **Bucle reviewer→implementer ACOTADO (regla dura).** Si hay gaps de corrección/requisitos: las tareas afectadas vuelven a `en-progreso`, `implementer` corrige (ese tiempo es **implementación**), y **relanzas la revisión** sobre el nuevo diff. Contador explícito ("revisión, intento 2 de 3"). **Máximo 3 intentos**; al 3.º con gaps, PARA y pregunta (seguir / re-planificar con `planner` / aceptar como deuda). Lo estilo/sobre-ingeniería se descarta (un revisor siempre encuentra algo). Solo Modo B (en Modo A superpowers trae su `requesting-code-review`).

   **Publicar el resultado en Jira (si `jira.json` `enabled` y se volcó el plan).** El **worklog de revisión se imputa POR INTENTO**: al cerrar cada pasada del bucle, imputa esa pasada (`worklog.py plan --kind revision --attempt N`) — así cada intento queda como su propia entrada en Jira con su duración y fecha, y `reviewAttempts` guarda la traza para `/retro`. El **comentario** es único y FINAL (tras el bucle): invoca el **Paso 9 de `jira-sync`**, renderiza contra `agent-kits/shared/review-report.template.md` y publícalo con la granularidad del volcado (modo fase: uno por fase al cerrarla; modo tarea: uno por tarea), incluyendo "revisión superada en N intento(s)". Idempotente (`reviewComentado`).
3. **`qa`** → pruebas E2E (solo local), informe y evidencias. El veredicto verde/rojo lo da `qa-gate.py` (exit code), no una impresión.

**Bucle de corrección de qa ACOTADO (regla dura).** Si qa sale rojo: la(s) tarea(s) afectadas vuelven a `implementer`, se corrigen y qa **re-ejecuta**. Contador explícito ("intento 2 de 3"). **Máximo 3 intentos**; si el 3.º sigue rojo, PARA: resume los fallos persistentes (con la salida de qa-gate de cada intento) y pregunta al usuario qué hacer — seguir intentando, re-planificar la tarea con `planner`, o cancelarla. No cierres estados en rojo y no degrades el umbral para "pasar".

En ambos modos, al salir debes tener: código implementado, revisión pasada, `qa-gate` en verde y `tasks.md` al día (validado con `ledger-lint.py`).

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

> **Vía rápida:** no hay spec/evaluación/plan que transicionar — solo el `tasks.md` ligero, que sigue el vocabulario de tareas (`borrador → en-progreso → completado`). Todo lo demás de esta tabla se salta.

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
