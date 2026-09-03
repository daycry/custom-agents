---
description: Orquesta el ciclo completo de una iniciativa (spec → evaluación → plan → implementación → pruebas → documentación) con la CADENA NATIVA del plugin como motor por defecto (autosuficiente: TDD, worktrees, subagentes frescos y debugging sistemático opt-in). Solo delega el backbone en superpowers si el usuario lo pide explícitamente. Invoca los agentes por nombre y con puertas de control.
argument-hint: <objetivo de la iniciativa> [rapido | completo] [--superpowers]
---

# /dev-cycle — orquestador del ciclo de desarrollo

Ejecuta el ciclo de una iniciativa de forma explícita y fiable. Objetivo: **$ARGUMENTS**.

Mantén `docs/roadmap/<fecha>-<slug>/tasks.md` como **ledger canónico** de progreso en todo el
ciclo (ver regla 8 de `docs/CONVENTIONS.md`), sea cual sea el motor de implementación.

## Fase 0 — Preparación y modo
1. Deriva un `<slug>` corto en kebab-case del objetivo y fija/crea la carpeta `docs/roadmap/<fecha>-<slug>/` (reutilízala si ya existe).
2. **La cadena nativa del plugin es SIEMPRE el motor por defecto** (Modo B), esté o no superpowers instalado — el plugin es autosuficiente (TDD, worktrees, subagentes frescos y debug-root-cause propios, opt-in vía `.claude/dev.json`). **Solo** se delega el backbone en superpowers (Modo A) si el usuario lo pide **explícitamente**: la frase "usa superpowers" (o equivalente inequívoco) o el argumento `--superpowers`. Si lo pide y superpowers NO está instalado, dilo y sigue en nativa. **No preguntes qué motor usar ni delegues por detectarlo instalado.**
3. Ofrece añadir al `CLAUDE.md` del proyecto (si no está) la **regla de ledger canónico**: "El progreso de un plan se registra en `docs/roadmap/<…>/tasks.md`; cualquier implementador —incluidos orquestadores externos como superpowers SDD— debe marcar ahí cada tarea; los ledgers propios son espejo, no fuente."

> La **capa de dominio** (evaluación/presupuesto, seguridad, documentación, Confluence, PDF) es de este plugin y se ejecuta **en ambos modos**. Lo único que cambia entre A y B es **quién hace el backbone** (spec/plan/implementación/pruebas/review).

## Fase 0-bis — PUERTA DE ENTRADA: flujo completo vs. vía rápida
Antes de arrancar, **pregunta al usuario** cómo quiere abordarlo (una sola pregunta, con recomendación según el tamaño aparente del cambio):

- **Flujo completo** (Fases 1→6): `evaluator` (spec + presupuesto) → `architect` (opcional: opciones de diseño) → `planner` → implementación → revisión → qa → documentación. Para trabajo no trivial, con incógnitas, multi-fichero, o cuando quieras el presupuesto en €/tokens y la traza PM completa.
- **Vía rápida** (salta el papeleo PM, conserva la red de calidad): **omite Fases 1 y 2** (sin spec, sin evaluación, sin plan detallado). El orquestador crea directamente un **`tasks.md` ligero** en `docs/roadmap/<fecha>-<slug>/` (solo ese fichero: banner de ledger canónico + frontmatter con `verificacion: obligatoria` + una fase + las tareas mínimas con criterios de aceptación verificables y su campo `- **Verificación**: \`<comando>\` → <resultado esperado>` — `ledger-lint.py` exige el campo cuando el frontmatter lo declara), va directo a **`implementer`**, y **mantiene las puertas de calidad**: la **revisión adversarial de dos lentes** (Fase 3) y **`qa`** con `qa-gate`. Cierra con `documenter` solo si el usuario lo pide. Para cambios pequeños/claros que se describen en una o dos frases. **Por qué la vía rápida NO salta la calidad.** El papeleo de PM (spec/evaluación/plan) es lo caro y prescindible en un cambio pequeño; la revisión de dos lentes y `qa-gate` son baratas y son la red que evita meter un bug "por ir rápido". Por eso la vía rápida ahorra ceremonia, no seguridad. El `tasks.md` ligero conserva el **ledger canónico**, así que el progreso, la imputación de horas y el volcado a Jira siguen funcionando igual. Si el usuario pide algo **trivial de verdad** (un typo, una línea), puede pedir explícitamente saltarse también la revisión/qa — pero no es el defecto.

**Si el usuario ya indica el modo, NO preguntes.** Respeta lo que pidió y arranca directo en ese modo:
- **Vía rápida explícita:** el objetivo trae "vía rápida", "rápido", "directo", "sin papeleo", "solo impleméntalo", o el argumento `rapido`/`--rapido`/`--quick`.
- **Flujo completo explícito:** "flujo completo", "con evaluación/presupuesto", "hazlo formal", o `--completo`/`--full`.

**Recomendación por defecto (solo si el usuario NO indicó modo):** si el objetivo se describe en una frase y toca pocos ficheros, propón **vía rápida**; si hay incógnitas, varias fases o el usuario quiere presupuesto, propón **flujo completo**. El usuario decide; respeta su elección.

> **Medición del coste (vía rápida).** El `tasks.md` ligero también se mide: al crearlo, `usage-meter.py start --artefacto "docs/roadmap/<fecha>-<slug>/tasks.md"` y, al dejarlo escrito, `close` → vuelca el JSON a su bloque `generacion:` (script en `agent-kits/shared/`; si degrada a `fuente: estimado`, anótalo y sigue — nunca bloquea).
>
> **Regla de no-solape (todo el ciclo).** Cada agente/fase mide su propio artefacto o tarea; como orquestador, asegúrate de que cada marcador se **cierra antes de abrir el siguiente** (evaluator cierra la evaluación antes de que planner abra el plan; una tarea cierra antes de lanzar la revisión): ventanas solapadas cuentan los mismos tokens dos veces y reparten mal el coste.

Si es **vía rápida**, salta a la Fase 3 (implementación) usando el `tasks.md` ligero; si es **flujo completo**, sigue en la Fase 1.

> **Modelo del agente (tiering configurable, capa 2).** Antes de despachar CUALQUIER agente por nombre (`evaluator`, `architect`, `planner`, `implementer`, `qa`, `documenter`, `nemesis`), resuelve su tier efectivo y pasa `model` en el parámetro `model` del Agent tool (contrato oficial sub-agents.md, verificado 2026-09-03: el parámetro por invocación tiene prioridad sobre el frontmatter):
>
> ```bash
> SHAREDKIT="$(find "$PWD/.claude" "$HOME/.claude" -type d -path '*agent-kits/shared' 2>/dev/null | head -1)"
> python3 "$SHAREDKIT/model-tier.py" <agente> --json     # {"model": "...", "effort": "...", "fuente": {"model": "frontmatter|dev.json", ...}}
> ```
>
> Si `fuente.model` es `dev.json`, pasa ese `model`; si es `frontmatter`, no pases nada (el agente ya lo declara). El `effort` de `dev.json` es **informativo**: el Agent tool no documenta ese parámetro, así que el efectivo es el del frontmatter — anúncialo («effort configurado high; efectivo: el del frontmatter») sin fingir que lo aplicas. Sin el script (instalación parcial) → frontmatter y sigue. Las lentes de la revisión resuelven su propio tier dentro de la skill `adversarial-review` (agente `reviewer`).

## Fase 1 — Evaluar (siempre en flujo completo, agente `evaluator`)
Invoca **`evaluator`** con el objetivo: crea/lee `spec.md` y produce `evaluation.md` (coste, esfuerzo, veredicto). Esto es valor propio (presupuesto en €/tokens) y va en los dos modos.

**Puerta go/no-go:** muestra el veredicto y pregunta si continuar. Si no-go, para.

## Fase 2 — Planificar (solo en flujo completo: `architect` opcional → `planner`)

**Fase 2-a — Diseño (agente `architect`, opt-in).** Invoca **`architect`** ANTES de `planner` si (a) la
carpeta ya tiene `design.md` (lo creó `/pm-cycle` 2-bis) — si está `aprobado`, salta a 2-b; si está en
`borrador` (`opcion_elegida: pendiente`), retoma en el paso 2 de abajo — o (b) el usuario lo pide («explora
el diseño», «compara opciones antes de planificar»). Si no se da ninguna, **ofrécelo en una línea** cuando
la evaluación marque complejidad Alta o riesgo arquitectónico; si no, ve directo a 2-b. **Dos pasadas** (el
subagente devuelve UN mensaje; la validación por trozos es tuya, como la puerta go/no-go):
1. Invoca `architect` SIN `elegida:` → `design.md` en `borrador` + resumen estructurado (una línea por
   opción, recomendada, pregunta).
2. **Presenta al usuario por trozos**: AskUserQuestion en Cowork (una opción por entrada, recomendada
   marcada) / lista numerada + pregunta en CLI. Recoge la elección (o una variante).
3. Re-invoca `architect` con `elegida: O<n>` (o `variante: …` → repite 1-2). Fija la opción, escribe el
   ADR `propuesta`, enlaza `design:` en spec/plan y pasa `design.md` a `aprobado`.
**Puerta:** `design.md` en `aprobado` (o el usuario decide seguir sin diseño).

**Fase 2-b — Plan (agente `planner`).** **En los dos modos**, tu `planner` genera **tus artefactos** en `docs/roadmap/<…>/`:
`improvement-plan.md` + `tasks.md` (+ `test-plan.md` si hay UI). Estos ficheros son tuyos y con
tus plantillas — **no se delega la planificación**, para que tu estructura y tu ledger existan
siempre. Si existe `design.md` aprobado, `planner` lo lee y **respeta la opción elegida** (enlaza
`design:` ↔ `plan:`). Puerta: OK del plan.

> Si en Modo A superpowers aporta un `brainstorming`/design doc, incorpóralo como contenido de la
> `spec.md`; el plan ejecutable y el progreso viven en TU `improvement-plan.md` + `tasks.md`.

> **Jira (opcional, opt-in).** Recién creado el plan, `planner` **ofrece** volcar las tareas a Jira
> con la skill `jira-sync` (un issue por tarea bajo el proyecto/épica elegidos; selector visual en
> Cowork o conversacional en CLI/VS Code). Luego, durante la implementación, al completar cada tarea
> `implementer` imputa horas (Tiempo IA + Supervisión, tope jornada) y marca el issue *Done*. Todo
> sujeto al opt-in de `.claude/jira.json`: aunque el conector esté conectado, si Jira no se activó
> para el proyecto, no se toca nada.

## Fase 3 — Implementar y probar (según el modo)

**Modo A (superpowers — SOLO si el usuario lo pidió explícitamente):** delega solo la **ejecución** en superpowers —
`subagent-driven-development`/`executing-plans`, `test-driven-development`, `requesting-code-review` —
pero trabajando **contra tu `tasks.md`**: debe marcar ahí cada tarea (ledger canónico). Aprovechas
su TDD, worktrees y review maduros; tus ficheros de `docs/roadmap/` siguen siendo la fuente.
**Las transiciones de estado las aplicas TÚ (el orquestador), no superpowers** (que no toca tus
artefactos): pon el plan y la fase activa en `en-progreso` antes de delegar, asegúrate de que las
tareas quedan marcadas en `tasks.md` durante la ejecución, y al cerrar aplica plan → `completado`
y spec → `implementada`. Si superpowers marca su propio ledger, vuélcalo a `tasks.md`.

**Modo B — cadena NATIVA (el defecto, siempre):**

> **Disciplina de desarrollo (`.claude/dev.json`, opt-in, defaults off — la crea `/setup`).** Antes de implementar, lee la config: `tdd: true` → el implementer sigue la skill **`tdd`** (fuente única de RED-GREEN-REFACTOR) por tarea con evidencia del rojo en el ledger; `worktree: true` → la iniciativa se trabaja en un worktree de git aislado (degradación a rama normal con aviso si no hay soporte); `subagentes: true` → el despacho por subagentes de contexto fresco (ver más abajo). Sin fichero o corrupto: defaults `false` + aviso — comportamiento clásico. Las tres opciones son combinables.

1. **`implementer`** → implementa fase a fase sobre rama (o worktree, si `worktree: true`), marcando `tasks.md` por tarea (con RED-GREEN-REFACTOR si `tdd: true`).

   **Despacho por subagentes de contexto fresco (si `subagentes: true` en `.claude/dev.json`).** En vez de implementar todas las tareas en un mismo contexto, cada `T-XX` la ejecuta un **subagente fresco** (Task tool) que no arrastra el ruido de las tareas anteriores. El ciclo por tarea, que coordinas TÚ (el orquestador):
   1. **Brief determinista** — genera el brief con el script del kit shared (nunca lo redactes a mano):

      ```bash
      SHAREDKIT="$(find "$PWD/.claude" "$HOME/.claude" -type d -path '*agent-kits/shared' 2>/dev/null | head -1)"
      python3 "$SHAREDKIT/task-brief.py" "docs/roadmap/<fecha>-<slug>" T-XX
      ```

      El script valida el ledger (`ledger-lint`), y extrae SOLO la tarea + criterios + fase + **persona de dominio** (si la tarea lleva `- **Tipo**: frontend|backend|db|devops|test|docs`, el brief antepone el perfil corto de `agent-kits/shared/personas/<tipo>.md`: prioridades, trampas típicas y evidencia exigible del dominio; sin etiqueta → subagente genérico; etiqueta sin persona en el catálogo → aviso y genérico, nunca bloquea) + la **opción elegida de `design.md`** (si existe y está `aprobado`; solo esa sección) + arquitectura + constitución (si existe) + el contrato de retorno. Exit ≠ 0 → arregla la causa antes de despachar.
   2. **Despacho brief-only** — lanza el subagente con el brief como único contexto (con `tdd: true`, `task-brief.py` ya incluye la sección «TDD» que manda seguir la skill `tdd` y devolver la evidencia del rojo). El subagente NO explora el repo entero: el brief y los ficheros que referencia.
   3. **Estados de retorno** — el subagente termina en uno de: `DONE` (valida tú contra los criterios ANTES de marcar `completado` en el ledger) · `DONE_WITH_CONCERNS: <duda>` (valida y pasa la duda a la revisión de dos lentes) · `NEEDS_CONTEXT: <qué>` (re-despacha UNA vez añadiendo al brief exactamente lo pedido — el subagente tiene PROHIBIDO inventar) · `BLOCKED: <qué>` (resuélvelo tú o pregunta al usuario; no re-despaches a ciegas).
   4. **Re-despacho acotado** — máximo **1** re-despacho por tarea (por gap de validación o por `NEEDS_CONTEXT`); si el segundo intento tampoco cierra, la tarea pasa al **flujo normal** (`implementer` en contexto principal) con aviso en el ledger.
   5. **Las puertas no cambian**: la medición por tarea (usage-meter), la revisión de dos lentes y `qa-gate` se ejecutan exactamente igual — el despacho solo cambia QUIÉN implementa, no qué se valida.
   6. **Despacho PARALELO de tareas independientes (opcional dentro de `subagentes: true`).** Las tareas de una MISMA fase **sin dependencias entre sí** (campo `Dependencias` del ledger) pueden despacharse en un lote paralelo de **máximo 3** subagentes. Condición de aislamiento: con `worktree: true`, cada tarea del lote trabaja en su propio worktree **temporal de tarea** (`git worktree add ../<repo>-<slug>-TXX -b tmp/<slug>-TXX`, ramificado desde `feature/<slug>` — es la excepción al worktree único por iniciativa de P2 del implementer); sin worktrees, solo paraleliza tareas cuyos campos `Archivos` no se solapen (si tocan lo mismo, secuencial). Los retornos los validas **secuencialmente** (uno a uno contra sus criterios) y, al validar cada `DONE`, **reintegras su rama temporal en `feature/<slug>`** (merge; si hay conflicto, esa tarea vuelve al flujo secuencial) y retiras su worktree — así, cuando lances la **revisión de dos lentes**, TODO el trabajo del lote está en `feature/<slug>` y el diff que ven los revisores es completo. Solo tú tocas el ledger. **Medición honesta del lote:** en paralelo las ventanas de usage-meter se solapan (contarían los mismos tokens varias veces), así que el lote se mide con UNA clave (`usage-meter.py start --artefacto "<slug>/lote-<n>"`) y las horas medidas se **reparten proporcionalmente a la estimación** de cada tarea, marcadas `(medido, lote)` en el ledger — jamás lo presentes como medición individual exacta. Con despacho secuencial (el default), nada de esto aplica.

   **TDD en modo subagentes:** con `tdd: true`, el subagente devuelve la evidencia del rojo junto a su estado; como el subagente tiene PROHIBIDO tocar el ledger, **eres tú (orquestador)** quien registra la línea `RED: <test> falló con <error> · <fecha>` en la tarea del ledger al validar el `DONE` — sin esa línea, el TDD de la tarea no cuenta.

   **Medición por tarea (usage-meter).** Al ARRANCAR cada `T-XX`: `usage-meter.py start --artefacto "<slug>/T-XX"`; al COMPLETARLA: `close` con la misma clave (en el flujo clásico lo ejecuta el `implementer` — su P3 lo trae; con `subagentes: true` lo coordinas tú por despacho). Las **horas-IA medidas** del JSON (`horas_ia`, con `fuente: medido`) se escriben como tiempo IA **real** de la tarea en `tasks.md` — anota `(medido)` junto al valor — y son las que usa la imputación a Jira (`worklog.py plan` ya prefiere real sobre estimado; su aritmética de jornada/banco NO cambia). Reglas: (a) si el meter degrada, deja la estimación a juicio marcada `(estimado)` y sigue; (b) re-medir la MISMA ventana (re-close inmediato) sustituye; pero una **corrección posterior** (gaps de revisión) se mide con clave nueva `"<slug>/T-XX-fix<N>"` y sus horas se **SUMAN** al real de la tarea en el ledger — la implementación original no se pierde; (c) los tokens del bucle de revisión (los revisores) NO van a la tarea — la revisión tiene su propia imputación `[revisión]` por intento (ver más abajo); cierra el marcador de la tarea ANTES de lanzar la revisión. Duraciones presentadas en formato `XhYm` (`usage-meter.py fmt`).
2. **Revisión adversarial — skill `adversarial-review` (fuente única del método; aquí solo se invoca).** Invócala por nombre pasándole: la carpeta de la iniciativa (`docs/roadmap/<fecha>-<slug>/`), el **nº de intento N** y, si N > 1, la **tabla de veredictos del intento anterior** (incluidos los `descartado (rebatido)` con su evidencia). La skill hace el resto: puerta previa `scope-check.py` (exit 1 → gap Important al `implementer` sin gastar revisores), `review-lens-select.py` para decidir si añade la **Lente C** (seguridad, condicional), lentes A/B(/C) en paralelo con contexto fresco, fusión, graduación `Critical / Important / Minor`, arbitraje de los rebates con evidencia, sección «Revisión de dos lentes — intento N» en `tasks.md`, promoción de las entradas `docs/knowledge/` `propuesta` → `aceptada` al cerrar sin gaps pendientes, y comentario FINAL en Jira (Paso 9 de `jira-sync`) si hay opt-in y plan volcado. Espera de vuelta: veredicto por criterio ✓/✗, gaps graduados con su veredicto, qué lentes corrieron y el ledger actualizado (`ledger-lint` exit 0).
   - **Tuyo (orquestador) — bucle reviewer→implementer ACOTADO (regla dura).** Si quedan gaps Critical/Important: las tareas afectadas vuelven a `en-progreso`, `implementer` corrige (ese tiempo es **implementación**, clave `"<slug>/T-XX-fix<N>"`) y **relanzas la skill** sobre el nuevo diff con contador explícito ("revisión, intento 2 de 3"). **Máximo 3 intentos**; al 3.º con gaps, PARA y pregunta (seguir / re-planificar con `planner` / aceptar como deuda). Rebatir con evidencia **no consume intento**; lo Minor se anota sin bloquear. Solo Modo B (en Modo A superpowers trae su `requesting-code-review`).
   - **Tuyo (orquestador) — worklog `[revisión]` POR INTENTO (si `jira.json` `enabled` y se volcó el plan):** al cerrar cada pasada, `worklog.py plan --kind revision --attempt N` — cada intento queda como su propia entrada en Jira con duración y fecha, y `reviewAttempts` guarda la traza para `/retro`. Los tokens de los revisores NO van a la tarea: cierra el marcador de la tarea ANTES de invocar la skill.
3. **`qa`** → pruebas E2E (solo local), informe y evidencias. El veredicto verde/rojo lo da `qa-gate.py` (exit code), no una impresión.

**Bucle de corrección de qa ACOTADO (regla dura).** Si qa sale rojo: la(s) tarea(s) afectadas vuelven a `implementer`, se corrigen y qa **re-ejecuta**. Contador explícito ("intento 2 de 3"). **Máximo 3 intentos**; si el 3.º sigue rojo, ANTES de parar ejecuta **UNA pasada de la skill `debug-root-cause`** (4 fases con evidencia: reproducción mínima → aislamiento → hipótesis probada → fix propuesto; solo cadena nativa — con superpowers explícito manda su systematic-debugging). Luego PARA y pregunta al usuario qué hacer — seguir con el fix propuesto, re-planificar con `planner`, o cancelar — presentando el **diagnóstico** (causa probada, o lo descartado + hipótesis vivas si no concluyó) junto a la salida de qa-gate de cada intento. El tiempo del diagnóstico se imputa como implementación de la tarea afectada. No cierres estados en rojo y no degrades el umbral para "pasar".

### Ciclo Jira de la Fase 3 (opt-in, `.claude/jira.json` `enabled: true`) — la secuencia, UNA sola vez

El estado del issue, los comentarios y las horas los produce **`jira-flow.py`** (skill `jira-sync`,
Paso 7): tú no redactas comentarios ni compones llamadas — el script devuelve `ops` (etiqueta →
transición → comentario → worklog) **ya firmadas por el agente** y en orden; ejecútalas seguidas con
las tools del conector. Una llamada por evento y tarea (con granularidad `fase`, `--batch` agrupa las
tareas de la fase en un comentario). El **ledger sigue siendo la fuente**; Jira es espejo.

| Evento | Cuándo | Quién lo dispara | Transición | Comentario (firma) | Worklog |
|---|---|---|---|---|---|
| `arrancar` | al abrir `T-XX` | `implementer` | → *En curso* | — | — |
| `implementado` | criterios cumplidos | `implementer` | *(sigue En curso)* | `ca-implementer`: qué hizo, evidencia, ficheros | implementación (horas medidas) |
| `revision` | cierre de intento sin gaps | `adversarial-review` | — | `ca-reviewer`: veredicto por criterio | `[revisión] --attempt N` |
| `gaps` | cierre de intento con gaps | `adversarial-review` | → *En curso* (reabre) | `ca-reviewer`: gaps graduados | `[revisión] --attempt N` |
| `qa-verde` / `qa-rojo` | veredicto de `qa-gate.py` | `qa` | — | `ca-qa`: X/Y del gate + evidencias | — |
| `aprobado` | revisión sin gaps **y** qa verde | **el orquestador (tú)**, `--actor orquestador --qa-verde` | → *Done* | `ca-orquestador`: cierre con la evidencia | — |

**`aprobado` es TUYO y con evidencia (no a ciegas).** `jira-flow.py` lo rechaza (exit 2, `ops: []`,
con la razón) si el ledger no tiene una última sección `## Revisión de dos lentes — intento N` sin
gaps pendientes para esas tareas, o si no le pasas `--qa-verde` — flag que pasas **solo tras leer el
exit 0 de `agent-kits/qa/qa-gate.py`**, nunca por el resumen de `qa`. Es el único evento que ve los
dos veredictos, y por eso el único que puede cerrar el issue.

**Cómo se entera el `implementer` de los gaps:** por su **brief** (`task-brief.py` inyecta los gaps
del último intento desde el ledger), no por Jira — el comentario `gaps` es el espejo para el equipo.
Sin Jira activado, el ciclo es idéntico salvo que no se publica nada: el script lee
`.claude/jira.json` y con `enabled` ≠ `true` devuelve `ops: []` y `jira: "desactivado"` (exit 0, sin
ruido). Reejecutar una fase tampoco duplica: cada plan con `ops` queda anotado en `jira-state.json`
(`flow[...]`) y repetir el mismo evento da `ops: []` + `yaRealizado: true` (`--force` para repetirlo
a propósito). En `revision`/`gaps`, `--intento N` es obligatorio.

En ambos modos, al salir debes tener: código implementado, revisión pasada, `qa-gate` en verde y `tasks.md` al día (validado con `ledger-lint.py`).

## Fase 4 — Documentar (siempre, agente `documenter`)
Con las pruebas en verde, invoca **`documenter`** para generar/actualizar la documentación del proyecto (una vez al final, no por tarea).

## Fase 5 — Seguridad (opcional, agente `nemesis`)
Si el usuario lo pide o la iniciativa lo amerita, invoca **`nemesis`** para auditar la seguridad de lo construido (solo entornos locales/privados).

## Fase 6 — Sincronizar y cerrar

**Ritual de cierre de rama (obligatorio, en orden):**

1. **Verificación final sobre la rama**: suites y lint del proyecto en verde (las mismas comprobaciones de P5 del implementer, una última vez sobre el estado final).
2. **Commits ordenados**: un commit lógico por tarea (`T-XX: …`), sin restos de instrumentación temporal (logs/asserts de diagnóstico fuera del diff — regla de `debug-root-cause`).
3. **Resumen de merge/PR derivado del LEDGER** (no de memoria): título, qué se hizo tarea a tarea, criterios de aceptación cumplidos, veredicto de qa-gate y ruta de las evidencias. Es la descripción del PR o el mensaje del merge.
4. **Integración según el flujo del repo**: merge directo o PR — si no está claro cuál usa el equipo, **pregunta**; no mergees por defecto.
5. **Limpieza**: rama integrada eliminada; worktrees retirados (`git worktree remove` + `prune`); marcadores de usage-meter sin huérfanos (`usage-meter.py status` limpio).
6. **Notas de cambios**: con el ledger ya en `completado`, invoca la skill **`changelog-sync`** (determinista, idempotente) para generar las entradas `[Unreleased]`/`[Sin publicar]` de esta iniciativa en ambos CHANGELOG, y afina la redacción sin ampliar alcance. No crea la sección de versión: eso es del release.
7. **Estados finales**: plan/tasks → `completado`, spec → `implementada` (tabla de abajo), fila del índice al día.

La documentación/artefactos se sincronizan con Confluence vía `confluence-publish` (opt-in; la invocan los agentes al escribir en `docs/`). Cierra con un resumen: modo usado (nativa/superpowers), iniciativa, tareas completadas, estado de pruebas, coste medido (usage-meter), ruta de la doc y enlaces. Ofrece `/retro` como siguiente paso natural.

## Transiciones de estado (OBLIGATORIAS en cada fase)
Los artefactos nacen en `borrador`. En **cada fase/puerta** que se supera, actualiza su estado
(frontmatter + cabecera) al que toque; **no dejes nada en `borrador`** al avanzar. Vocabularios:
spec = `borrador · aprobada · implementada · obsoleta`; evaluación/plan/tareas = `borrador ·
en-progreso · en-revision · completado · cancelado`; design = `borrador · aprobado · obsoleto`.

> **Vía rápida:** no hay spec/evaluación/plan que transicionar — solo el `tasks.md` ligero, que sigue el vocabulario de tareas (`borrador → en-progreso → completado`). Todo lo demás de esta tabla se salta.
>
> **`design.md` (opcional, agente `architect`):** vocabulario propio `borrador · aprobado · obsoleto`. Solo existe si se hizo el paso de diseño; la columna queda `—` si no.

| Momento | spec | evaluación | design (opcional) | plan / tasks |
|---|---|---|---|---|
| Tras evaluar (Fase 1) | borrador | `en-revision` | — | — |
| Puerta **go** | `aprobada` | `completado` | — | — |
| Puerta **no-go** | (obsoleta si se descarta) | `cancelado` | — | — |
| Diseño presentado (Fase 2-a) | aprobada | completado | `borrador` (opciones abiertas) | — |
| Opción validada por el usuario | aprobada | completado | `aprobado` | — |
| Plan creado (Fase 2-b) | aprobada | completado | aprobado (`plan:` relleno) | `borrador` |
| Puerta OK del plan → arranca impl. | aprobada | completado | aprobado | `en-progreso` (plan y fase activa) |
| Durante impl. (Fase 3) | aprobada | completado | aprobado | tareas `en-progreso`→`completado`; fase `completado` al cerrar |
| qa en rojo | aprobada | completado | aprobado | tarea/plan → `en-progreso` (reabrir) |
| Re-diseño (se descarta la opción) | aprobada | completado | `obsoleto` → nuevo `design.md` `borrador` | plan `en-revision` |
| Cierre (qa verde + documentado) | `implementada` | completado | aprobado | plan `completado` |
| Cancelación en cualquier punto | (obsoleta) | `cancelado` | `obsoleto` | `cancelado` |

Aplica la transición **en el mismo paso** en que se cruza la puerta, y mantén coherente la tabla
de resumen de `tasks.md`.

**Estas transiciones son responsabilidad del orquestador y se aplican en LOS DOS MODOS.** En
**Modo A** superpowers no actualiza tus estados ni tu `tasks.md` por su cuenta: eres tú quien
aplica las transiciones sobre tus artefactos y quien garantiza que `tasks.md` refleje el progreso
(volcando el ledger de superpowers si hace falta). En **Modo B** las aplican `implementer`/`qa`,
que ya lo tienen en sus instrucciones.

## Reglas del orquestador
- **Invoca a los agentes por nombre**; no dependas de la auto-delegación.
- **Cero dependencia de superpowers:** la cadena nativa (Modo B) es el defecto SIEMPRE y hace el ciclo completo con los agentes del plugin; superpowers (Modo A) solo entra bajo petición explícita del usuario.
- **`tasks.md` es la fuente única de progreso** en los dos modos.
- **Respeta las puertas** (go/no-go, OK de plan, verde de pruebas).
- Si el usuario pide solo una parte (p. ej. "solo planifica"), ejecuta hasta esa fase y detente.
