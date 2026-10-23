# Orquestadores `orch-*` por intención y revisión por Workflow — C053–C058

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Seis definiciones completas: **11.177 bytes/306 líneas**. [commands-c3-orch-reading-evidence.json](commands-c3-orch-reading-evidence.json).
Nada se ejecutó ni se integró. Propuestas para T-08/T-11.

## Decisión común

C053–C057 son envoltorios de una línea sobre las skills `orch-*` (motor
`orch-pipeline`), ya comparadas: S195–S196 en
[skills-orch-opensource-approval.md](skills-orch-opensource-approval.md) y S197–S200 en
[skills-orch-parallel-plan.md](skills-orch-parallel-plan.md). Sus destinos están
**integrados**: las filas «Cambiar un comportamiento que ya funciona» y «Refactor puro»
de `skills/tdd/SKILL.md:40-41`, y las rebanadas verticales en `agents/planner.md:88`
(D-095). Los agentes que despachan también tienen ficha: `code-reviewer` (A008,
[agents-review-cpp-csharp-db.md](agents-review-cpp-csharp-db.md)), `security-reviewer`
y `refactor-cleaner` (A059, A056, [agents-refactor-security-silent-tdd-types.md](agents-refactor-security-silent-tdd-types.md)),
`code-explorer` (A007, [agents-a11y-architect-explorer.md](agents-a11y-architect-explorer.md))
y el arnés GAN ([agents-gan-harness.md](agents-gan-harness.md)).

Lo propio de los comandos es la **entrada por intención**: cinco puertas (nueva,
cambio, defecto, refactor, MVP), cada una con su negativo («no para bugs, usa…») y su
primer movimiento. El plugin tiene una sola entrada, `/dev-cycle` (o `quick-implement`
en lenguaje natural), que elige modo por tamaño (`commands/dev-cycle.md:32-42`) pero no
por intención; la tabla de `tdd` solo actúa con `tdd: true` y a nivel de tarea. Esa
fila ya figura pendiente en [commands-workflow-comparison.md](commands-workflow-comparison.md)
(«Entrada por intención»); estos cinco cuerpos la concretan:

**Propuesta (una línea, `commands/dev-cycle.md:30`, Fase 0 paso 4):** «Clasifica cada
cambio como capacidad nueva, cambio de un comportamiento que funciona, defecto o
refactor, y escribe su primer oráculo en la `Verificación` de la tarea: test nuevo en
rojo, test existente modificado en rojo, reproducción mínima del fallo
(`debug-root-cause` fase 1) o la misma suite en verde antes y después. Si el usuario
describe un defecto como cambio (o al revés), pregúntalo antes de despachar.»

Lo demás no se adopta: el tipo de commit `feat:/fix:/refactor:` (aquí el commit es por
tarea, `T-XX:`) y la **puerta 2** de confirmación antes del commit local. En el plugin
el commit pasa por `commit-selection.py` con vista previa y validación
(`commands/dev-cycle.md:494`), y lo que sí exige confirmación es integrar (paso 4, `:496`).

## C053 — orch-add-feature

`1.173 bytes/36 líneas` · frontmatter: solo `description`. Investigación → plan
(puerta 1) → TDD → `code-reviewer` (+ `security-reviewer` si hay disparador) → commit
`feat:` (puerta 2). Sin argumento, pregunta qué añadir.

- **Artefactos y dueño propio:** `task_list` → `planner` (`tasks.md`); código → `implementer`; commit → `/dev-cycle` Fase 6.
- **Despacho:** skill `orch-add-feature` → `orch-pipeline`.
- **Escenario positivo:** «añade exportación CSV al panel» → `/dev-cycle` (flujo completo
  si hay incógnitas, vía rápida si cabe en una frase) o `quick-implement` sin barra.
- **Escenario negativo:** «el login devuelve 500 con un + en el email» → es un defecto:
  `debug-root-cause` y la fila «Arreglar un fallo» de `tdd`, no un plan desde cero.

**Comparación.** El disparador de seguridad por lista (entrada de usuario, consultas,
llamadas externas) es en el plugin la Lente C por `review-lens-select.py`, por rutas y
líneas. **Destino:** la línea común de arriba; lo demás, ya integrado.

## C054 — orch-build-mvp

`1.309 bytes/36 líneas` · frontmatter: solo `description`. Desde un documento de
diseño: rebanadas verticales (puerta 1), andamiaje, traducción del documento a
`gan-harness/spec.md` + `eval-rubric.md` y bucle `/gan-build --skip-planner` «hasta
que la nota pase o se estanque»; revisión y un commit por rebanada (puerta 2).

- **Artefactos y dueño propio:** `gan-harness/spec.md` → `analyst` (`spec.md` de la
  iniciativa); rúbrica → criterios de aceptación de la spec y `Verificación` de las
  tareas (`planner`); código → `implementer`.
- **Despacho:** skill `orch-build-mvp`, `/gan-build`, `code-reviewer`, `security-reviewer`.
- **Escenario positivo:** «construye el MVP a partir de este SDD» → `/pm-cycle`
  (`analyst` lee el documento, spec aprobada, `evaluator`) y `/dev-cycle` con
  `planner` en rebanadas verticales.
- **Escenario negativo:** «itera hasta que el evaluador dé 7/10» → ninguna pieza; los
  veredictos son deterministas (`qa-gate.py`, fusión de lentes).

**Comparación.** Traducir el SDD a una segunda spec en `gan-harness/` deja dos fuentes
de verdad; el plugin tiene una carpeta por iniciativa enlazada (regla 7). La nota de
modelo como puerta ya está rechazada («Puntuaciones del modelo como veredicto»,
[skills-destinations.md](skills-destinations.md)). **Destino:** ya integrado (D-095); lo demás, **sin destino**.

## C055 — orch-change-feature

`1.388 bytes/38 líneas` · frontmatter: solo `description`. Suelo `small`; plan ligero
solo si hace falta investigar (puerta 1); actualiza primero los tests existentes al
comportamiento nuevo y después la implementación; revisión y commit (puerta 2).

- **Artefactos y dueño propio:** test modificado y código → `implementer` (con `tdd`); commit → `/dev-cycle` Fase 6.
- **Despacho:** skill `orch-change-feature`, `code-reviewer`, `security-reviewer`.
- **Escenario positivo:** «que alerte con 2 avisos en vez de 3» → `/dev-cycle` vía
  rápida o `quick-implement`, con la fila `skills/tdd/SKILL.md:40`.
- **Escenario negativo:** «el poller se cuelga con respuesta vacía» → defecto (C056), no cambio.

**Destino:** ya integrado (`skills/tdd/SKILL.md:40`) + la línea común.

## C056 — orch-fix-defect

`1.272 bytes/38 líneas` · frontmatter: solo `description`. Suelo `small`; acota la
causa con `code-explorer` si no está clara; test de regresión nuevo en rojo, arreglo
a verde, revisión y commit `fix:` (puerta 2).

- **Artefactos y dueño propio:** test de regresión y arreglo → `implementer`; el método de causa raíz → `debug-root-cause`.
- **Despacho:** skill `orch-fix-defect`, `code-explorer`, `code-reviewer`, `security-reviewer`.
- **Escenario positivo:** «el login devuelve 500 cuando el email lleva un +» →
  `debug-root-cause` (reproducción mínima) y su test de regresión como rojo de `tdd` (`skills/tdd/SKILL.md:39`).
- **Escenario negativo:** «ordena por prioridad en vez de por fecha» → cambio (C055).

**Comparación.** En el plugin `debug-root-cause` entra solo al tercer rojo de `qa` o
a demanda (`commands/dev-cycle.md:413`); un defecto que llega por la puerta de entrada
no se encamina a la reproducción. Es el hueco que cierra la línea común.
**Destino:** la línea común.

## C057 — orch-refine-code

`1.477 bytes/39 líneas` · frontmatter: solo `description`. Suelo `standard`; confirma
los tests en verde antes de tocar nada, añade tests de caracterización si falta
cobertura, reestructura en pasos con la suite verde y delega duplicados y código
muerto en `refactor-cleaner`; commit `refactor:` neutro (puerta 2).

- **Artefactos y dueño propio:** código → `implementer`; localizar duplicados → `code-health`.
- **Despacho:** skill `orch-refine-code`, `refactor-cleaner`, `code-reviewer`.
- **Escenario positivo:** «extrae el cliente HTTP de `poller.py` sin cambiar nada» →
  `/dev-cycle` vía rápida con `TDD n/a: refactor` (`skills/tdd/SKILL.md:41`) y `code-health` si hay que localizar duplicados.
- **Escenario negativo:** «limpia el módulo y de paso cambia el orden» → no es refactor; cambio (C055).

**Destino:** ya integrado (`skills/tdd/SKILL.md:41`; A056 en `agents/planner.md` P3) + la línea común.

## C058 — orch-review

`4.558 bytes/119 líneas` · frontmatter: `description` y `argument-hint`. Calcula el diff
(cambios locales sin comitear o un PR de GitHub por `gh`), se lo pasa al Workflow
`workflows/orch-review.workflow.js` (recurso transitivo, no leído) y presenta el
resultado: un revisor por dimensión, deduplicación por fragmento de evidencia,
verificador adversarial de cada hallazgo CRITICAL/HIGH y veredicto
`APPROVE`/`CHANGES_REQUESTED` con `incomplete` y `failedDimensions`.

- **Intención y disparador:** «revisa este diff» o «revisa el PR 42».
- **Artefactos y dueño propio:** ninguno escrito (informe en el chat). En el plugin, la
  sección `## Revisión de dos lentes — intento N` de `tasks.md` → `adversarial-review` (`docs/agents/ROLES.md:39`).
- **Despacho:** herramienta Workflow y `gh pr diff`/`gh pr view`.
- **Escenario positivo:** «revisión adversarial de la rama» → `adversarial-review` → `reviewer` por lente.
- **Escenario negativo:** «revisa el PR 42 y comenta en GitHub» → no cubierto: se
  revisa la rama del PR en local (modo sin plan, `skills/adversarial-review/SKILL.md:45`)
  y ninguna pieza propia publica en GitHub (en Jira sí).

**Comparación.** Coinciden la revisión en paralelo con contexto fresco y la
deduplicación (`skills/adversarial-review/SKILL.md:77-103`). Diferencias: la fuente
verifica los graves con un segundo modelo; el plugin, con el rebate del implementador
con evidencia (§4). La fuente no tiene Lente A (spec/plan). Su `description` remite a
otros dos comandos de revisión para la misma intención (`/code-review`, `/review-pr`);
el plugin tiene un dueño. Lo mejor de la pieza es el **contrato de fallo cerrado**
(l.104-108): una dimensión que no corrió deja el veredicto incompleto, nunca un
aprobado. El plugin degrada a subagente genérico si falta `reviewer` (§2.3), pero no
dice qué pasa si una lente no devuelve salida. También vale, si algún día hay modo PR,
derivar un número entero del argumento y no pasar el texto crudo al shell (l.41-45).

**Destino:** línea en `skills/adversarial-review/SKILL.md` §3 (concreta la fila
«Revisión reproducible» de [commands-workflow-comparison.md](commands-workflow-comparison.md)):
«Una lente que no devuelve su salida estructurada (error, rechazo también del
subagente de respaldo, salida vacía o truncada) no cuenta como "sin defectos": el
intento queda `incompleto`, la traza nombra la lente que faltó y el ciclo no pasa a
`qa` hasta relanzarla o hasta que el usuario lo acepte de forma explícita.»
