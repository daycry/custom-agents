---
spec: plugin-refactor
descripcion: >
  Refactor medido del plugin en dos bloques separados. (a) Refactor de código con CERO cambio de
  comportamiento: funciones largas en los cinco hotspots (32 → ≤ 16), copias accidentales convertidas en
  declaradas o eliminadas, falsos positivos del detector de TODO (8 → 1) y exclusión de `interop/` en
  `code-health`; aceptación por `code-health.py --baseline` sobre el JSON de esta carpeta y la misma suite
  en verde antes y después, con los contratos congelados. (b) Revisión de encadenamiento E1–E10 del
  §8-bis del análisis, que SÍ cambia comportamiento y se presupuesta como características propias. La
  decisión del §5 (copias declaradas vs módulo vendorizado) NO se toma aquí: va a `architect`.
  Fuente única del alcance: `analysis.md` de esta carpeta.
estado: aprobada
creado: 2026-09-10
actualizado: 2026-09-10
evaluacion: evaluation.md
design: design.md          # `aprobado` 2026-09-10 — decisión del §5: O1 (registro de copias declaradas + un test de identidad); ADR-016 `propuesta`
plan: pendiente
analisis: analysis.md
relacionado: docs/roadmap/2026-09-09-brief-budget/spec.md (toca el mismo `main()` de `task-brief.py`; ordenada DESPUÉS de este refactor) · docs/roadmap/2026-09-09-project-specialization/tasks.md (F1 integrada en master 919cca4; F2/F3 pendientes) · docs/knowledge/gotchas/GOT-005-consola-windows-cp1252.md · docs/knowledge/gotchas/GOT-009-presupuesto-del-brief-se-rompe-con-design-md.md
generacion:
  inicio: 2026-09-09T22:35:28Z
  fin: 2026-09-09T22:43:15Z
  fuente: estimado         # `usage-meter.py close` degradó en esta máquina (Windows): «carpeta de transcripciones no disponible» (es E7/C-13 de esta misma spec). Tokens a juicio por lo leído (analysis 213 líneas, plantillas, CALIBRATION, README del roadmap, greps de recon sobre 6 scripts) y lo escrito (esta spec)
  tokens_reales: { entrada: 60000, salida: 14000, cache_creacion: 25000, cache_lectura: 300000 }
  eur: 0.79
  horas_ia: 0.21
  duracion: 8m
  ratio_usado: 479326
---

# Refactor del plugin — deuda medida en hotspots, copias declaradas y contratos entre piezas

> **Evaluación:** [`evaluation.md`](evaluation.md) — `en-revision`
> **Diseño:** [`design.md`](design.md) — `aprobado` (2026-09-10): el §5 se cierra con **O1**, registro de copias declaradas (`agent-kits/shared/copias.json`) + **un** test de identidad byte a byte, con el error del linter sobre bloques idénticos no registrados como parte inseparable de la opción ([`ADR-016`](../../knowledge/adr/ADR-016-copias-declaradas-con-test-de-identidad.md), `propuesta`). **C-03 se encoge**: no hay copias accidentales, el trabajo es unificar los cuatro mecanismos de guardarraíl en uno
> **Plan de implementación:** pendiente
> **Análisis de origen:** [`analysis.md`](analysis.md) — **única fuente del alcance** (§1 medición · §2 duplicación · §3 funciones largas · §4 TODO · §5 decisión · §6 método · §7 lo que NO es · §8 señales · §8-bis encadenamiento · §9). Esta spec no lo amplía ni lo reinterpreta.

> **Terminología:**
> - **Hotspot**: fichero grande Y que cambia mucho (90 días de `git log`), según `code-health.py`. Los cinco principales: `knowledge-find.py`, `build_dashboard.py`, `doctor.py`, `lint_plugin.py`, `task-brief.py`.
> - **Función larga**: > 30 líneas (`--min-lines 6` × 5, default de `code-health.py`).
> - **Copia deliberada / declarada / guardada**: deliberada = existe por diseño (los scripts viajan sueltos, sin `import` común); declarada = un comentario en el código lo dice; guardada = un test compara las copias byte a byte. Hoy solo `celdas_md` y compañía están guardadas (`tests/test_knowledge_index.py`).
> - **Copia accidental**: nació igual en dos sitios sin que nadie decidiera duplicarla (clase 3 del §2).
> - **Contrato congelado**: flags de CLI, exit codes, forma de los `--json`, nombres de secciones del brief y la regex `REVISION_HDR_PATTERN`. No cambian en el bloque (a).
> - **Línea base**: [`code-health-baseline.json`](code-health-baseline.json) (2026-09-09, `--exclude-tests`).

## Contexto y objetivo

Tras tres rondas de corrección sobre `task-brief.py` en un día, el usuario pidió «una revisión de código y refactorizar… de todo el plugin». El análisis midió primero (`code-health.py . --exclude-tests --json`, 2026-09-09): **36 ficheros · 14.259 líneas · 7,6 % duplicado (273 bloques) · anidamiento máximo 6 · 8 TODO (6 falsos positivos)**, y **104 funciones > 30 líneas** (105 en la línea base; T-01 de `project-specialization` eliminó código muerto), de las que **32 (30 %) están en los cinco hotspots** (`lint_plugin.py` 9 · `build_dashboard.py` 8 · `doctor.py` 8 · `task-brief.py` 4 · `knowledge-find.py` 3; medido 2026-09-10 con `--top 1000`).

El hallazgo que ordena el alcance (§2): **la mayor parte del 7,6 % no es deuda, es diseño** — los scripts viajan sueltos (paquete portable, Codex/OpenCode) y la duplicación es el mecanismo de portabilidad. Perseguir el porcentaje sin decidir antes cómo comparten código las piezas (§5) sería una regresión disfrazada. Por eso esta spec:

1. **Bloque (a) — refactor de código con cero cambio de comportamiento** sobre lo que SÍ es deuda: funciones largas en hotspots, copias accidentales, detector de TODO, exclusión de `interop/`.
2. **Bloque (b) — revisión de encadenamiento** (§8-bis): diez huecos de contrato entre piezas, verificados en un ciclo real. Cambian comportamiento y van como características propias.
3. **No decide el §5**: O1 (copias declaradas) vs O2 (módulo vendorizado) va a `architect`; O3 (import común) queda descartado por el requisito multi-runtime (`docs/INTEROP.md`).

Objetivo medible (§8): funciones largas en los 5 hotspots **32 → ≤ 16** sin ninguna nueva > 60; **0 bloques accidentales sin declarar**; TODO **8 → 1**; suites, linter, evals, `export-interop.py --check` y `release.py --dry-run` **idénticos en verde**; `code-health --baseline` **«mejora» en cada tarea, nunca «empeora»**.

## Decisiones de diseño

| Decisión | Elección | Motivo |
|---|---|---|
| Dos bloques separados | **(a) cero cambio de comportamiento · (b) cambios de contrato** | §7 y §8-bis del análisis: un refactor no cuela features; los huecos de encadenamiento son defectos de contrato y se presupuestan aparte |
| Aceptación del bloque (a) | **`code-health.py . --exclude-tests --json --baseline docs/roadmap/2026-09-09-plugin-refactor/code-health-baseline.json` + misma suite en verde** | §6.1 y §6.2: sin cifra no hay tarea cerrada; sin tests nuevos que legitimen comportamiento nuevo |
| Contratos congelados en (a) | **flags, exit codes, formas `--json`, secciones del brief, `REVISION_HDR_PATTERN`** | §6.2; los `--json` de `knowledge-find.py` (consumido por `task-brief.py` y `session-context.sh`) y `scope-check.py` (consumido por la revisión) son API interna |
| Decisión §5 | **NO se toma aquí → `architect` (Fase 2-bis)** | Condiciona C-03 y E9; O3 descartada (rompe el standalone) |
| Orden respecto a `brief-budget` | **Este refactor primero (partir `main()` de `task-brief.py`), `brief-budget` después** | §7: al revés se refactoriza dos veces; `brief-budget` ya tiene go del usuario ordenado después |
| Copias deliberadas | **No se tocan hasta la decisión del §5** | §6.4; hoy son el guardarraíl de portabilidad |
| Revisión de dos lentes | **Por tramo, no por tarea** | §6.6: en un refactor la Lente B (regresiones) es la que trabaja |
| Un hotspot por tarea | **Empezando por `task-brief.py` (acaba de sufrir) y `knowledge-find.py` (el que más cambia)** | §6.3 |
| Prosa fuera | **`agents/*.md`, `commands/*.md`, `skills/*/SKILL.md` no se tocan en (a)** | §7: es dominio de `plugin-dev`. En (b) sí se tocan las piezas de prosa que un hueco exija (E1, E2/E3, E5) |
| Registros fechados | **`docs/roadmap/*` cerrado, ADR, LES y CHANGELOG intactos** | Precedente `sin-motor-externo`: los 104 ficheros que citan `/dev-cycle` son en su mayoría históricos; E5 se resuelve en la doc viva y en `/doctor`, no reescribiendo el pasado |

## Configuración / parámetros

| Parámetro | Clave / mecanismo | Default | Valor objetivo |
|---|---|---|---|
| Umbral de función larga | `code-health.py --min-lines` | 6 (× 5 = 30 líneas) | **sin cambio** |
| Funciones > 30 líneas en los 5 hotspots | señal §8 | 32 | **≤ 16**, ninguna nueva > 60 |
| Bloques accidentales sin declarar | señal §8 | ≥ 4 pares (ver supuesto S-2) | **0** |
| Marcadores TODO detectados | `code-health.py` §4 | 8 (6 falsos positivos) | **1** (`usage-meter.py:380`) |
| Exclusión de rutas generadas en `code-health` | **no existe** (`add_argument` solo tiene `--exclude-tests`, verificado) | — | `interop/` excluible (flag aditivo; ver CA-07 y S-4) |
| Línea base | `code-health-baseline.json` | 2026-09-09 | comparación con los **mismos flags** con que se tomó |

## Arquitectura y componentes

**Bloque (a) — reutiliza, no crea.** Toca solo código Python de los cinco hotspots y de `code-health.py`; las suites existentes son el contrato (`tests/` 25 ficheros, `agent-kits/shared/test_*.py`, `skills/*/scripts/test_*.py`; ~780 funciones de test). Puertas de cada tarea (§6.5): `code-health --baseline`, `python scripts/lint_plugin.py`, `python evals/check.py`, `export-interop.py --check`, `tests/test_knowledge_index.py` (copias guardadas), y `release.py --dry-run` al cerrar.

| Pieza | Qué se toca | Contrato que NO cambia |
|---|---|---|
| `agent-kits/shared/task-brief.py` (685 líneas, `main()` 160) | partir `main()` en las siete secciones que ya monta; fundir las cuatro reglas de la persona (`PERSONA_TOPE_CHARS`, `PERSONA_SUELO_CHARS`, `PERSONA_TOPE_MINIMO_UTIL`, margen dinámico) en una función con nombre | nombres de secciones del brief, `BRIEF_TOPE_CHARS`, `_REVISION_HDR_FALLBACK`, `--json`, exit codes; `agent-kits/shared/test_task_brief.py` en verde sin tocar |
| `agent-kits/shared/knowledge-find.py` (852 líneas, `main()` 87) | partir `main()` y las otras dos largas | forma del `--json` (lo consumen `task-brief.py` y `session-context.sh`), `--doctrina`, `--show`, `--related` |
| `agent-kits/shared/doctor.py` (942 líneas, `bloque_plugin()` 87) | 8 funciones largas | veredictos ✅/⚠️/❌ por línea, `--json`, exit 1 si hay ❌; `celdas_md` y compañía **no se tocan** (copia guardada) |
| `scripts/lint_plugin.py` (969 líneas, `lint()` 114) | 9 funciones largas | avisos y errores actuales, exit codes; `celdas_md` **no se toca** |
| `skills/roadmap-dashboard/scripts/build_dashboard.py` (613 líneas, `render_html()` 93, `scan()` 85) | 8 funciones largas | HTML/MD/JSON de salida byte-idénticos para el mismo roadmap |
| `skills/code-health/scripts/code-health.py` | `TODO_RE` y exclusión del propio detector; exclusión de rutas | flags existentes, exit codes, forma del `--json` y de `--baseline`; 14 tests en verde + los nuevos SOLO para el detector y la exclusión (excepción declarada, ver CA-06/CA-07) |
| Copias accidentales (clase 3 del §2) | `evals/check.py:110` ↔ `lint_plugin.py:906` (15) · `task-brief.py:581` ↔ `jira-flow.py:249` (13) · `export-skills.py:36` ↔ `jira-flow.py:83` (13) · `code-health.py:27` ↔ `deps-inventory.py:29` (13) | mecanismo según §5: O1 registro + un test byte a byte; O2 módulo vendorizado por el empaquetador. **Bloqueado por la decisión** |

**Bloque (b) — sí crea.** Un fichero nuevo de prosa (`docs/agents/CONTRACTS.md` o nombre que fije `planner`, junto a `ROLES.md`: quién invoca a quién, con qué flags, exit codes, ficheros y marcadores), comprobaciones nuevas en `lint_plugin.py`, prosa en `planner.md` / `dev-cycle.md` / `qa.md` / `implementer.md` / `lens-prompts.md`, heurística en `review-lens-select.py`, exclusiones en `scope-check.py`, una línea en `/doctor`, y la corrección de `usage-meter.py` en Windows. Todo lo de prosa regenera `interop/` (`export-interop.py`) y pasa `evals/check.py`.

## Flujo (paso a paso)

1. `architect` (Fase 2-bis, recomendado): `design.md` con O1 vs O2 del §5; ADR `propuesta`. Sin esto, C-03 y E9 no se abren; el resto del bloque (a) sí.
2. Bloque (a), un hotspot por tarea: `task-brief.py` → `knowledge-find.py` → `doctor.py` → `lint_plugin.py` → `build_dashboard.py`. Cada tarea cierra con `code-health --baseline` = «mejora» + suite en verde.
3. Detector de TODO y exclusión de `interop/` (C-04, C-05). Tras C-05, **se toma una segunda línea base** con el flag nuevo para que las comparaciones posteriores no atribuyan al refactor las 118 líneas del adaptador generado (S-4).
4. Copias accidentales según la opción elegida (C-03).
5. Bloque (b): matriz de contratos (C-06) primero — es la que alimenta C-07 (linter), C-09 (dependientes) y la Lente A —; después E1 (C-08), E2/E3 (C-09), linter (C-07, sobre el `lint_plugin.py` ya refactorizado), E6/E5/E7/E4 (C-12, C-11, C-13, C-10).
6. Revisión de dos lentes **por tramo** (§6.6) y corrección post-revisión; cierre con `export-interop.py --check`, `changelog-sync`, `release.py --dry-run`, `/retro`.
7. `brief-budget` arranca después, sobre el `task-brief.py` partido.

## Alcance

- **Dentro — bloque (a), refactor de código (cero cambio de comportamiento):**
  - **C-01** `task-brief.py`: `main()` de 160 líneas en las siete secciones; las cuatro reglas de la persona en una función con nombre; 4 funciones largas → ≤ 2.
  - **C-02** Los otros cuatro hotspots (`knowledge-find.py` 3 · `doctor.py` 8 · `lint_plugin.py` 9 · `build_dashboard.py` 8): 28 funciones largas → ≤ 14; ninguna nueva > 60.
  - **C-03** Copias accidentales (clase 3 del §2) → **declaradas** (registro + un test byte a byte, si O1) o **eliminadas** (si una de las piezas no la necesita), incluyendo el patrón E9 (`REVISION_HDR_PATTERN` y sus dos `_REVISION_HDR_FALLBACK` en `task-brief.py:576` y `jira-flow.py:231`) en el mismo registro. **Bloqueada por la decisión del §5.**
  - **C-04** Detector de TODO de `code-health.py`: 8 → 1 (excluir comentarios que enumeran marcadores y el propio detector; la regla «palabra seguida de `(`» deja de aceptar la prosa castellana «TODO (»).
  - **C-05** `code-health.py` puede excluir `interop/` (generado por `export-interop.py`) del informe. Hoy no tiene `--exclude` por ruta.
- **Dentro — bloque (b), revisión de encadenamiento (§8-bis; cambia comportamiento):**
  - **C-06** Matriz de contratos pieza → pieza en `docs/agents/` junto a `ROLES.md` (`ROLES.md` dice quién decide; esta dice **cómo se hablan**): flags, exit codes, ficheros, marcadores (`test-plan: n/a`, `interop/**`, `fuente: estimado`). Alimenta C-07, C-09 y la Lente A.
  - **C-07** Comprobaciones nuevas en `lint_plugin.py`: (a) toda ruta de script citada entre acentos graves en `agents/`, `commands/`, `skills/` existe (65 rutas únicas hoy); (b) todo `/comando` citado en la doc existe como `commands/<x>.md` (18 distintos hoy, con placeholders `/algo`, `/nombre` a tolerar); (c) cada regla «al tocar X regenera/actualiza Y» de `CLAUDE.md` tiene puerta ejecutable (`--check`), no solo prosa.
  - **C-08** E1 — caso sin UI resuelto en las tres piezas a la vez: marcador `test-plan: n/a (sin UI)` que emite `planner`, lo lee `dev-cycle` y `qa` sale limpio sin pedir regenerar (`agents/qa.md:94` hoy: «hay que (re)generarlo con `planner`»).
  - **C-09** E2 + E3 — piezas dependientes enumeradas: `planner` mete `interop/**` (y las piezas que describen a la pieza tocada) en `Archivos` de las tareas que tocan `commands/`/`agents/`/`hooks/`; `implementer` regenera; la Lente A ejecuta `export-interop.py --check`.
  - **C-10** E4 — `review-lens-select.py` reconoce **flujo de texto controlado por el consumidor hacia un prompt/brief** como disparador de la Lente C (hoy solo patrones de código peligroso y stems de ruta: dio `lente_c: false` tres veces con la suplantación del contrato de retorno).
  - **C-11** E5 — el nombre real del comando instalado como plugin (`/custom-agents:dev-cycle`, no `/dev-cycle`): `/doctor` lo comprueba y la **doc viva** (README ES/EN, INSTALL ES/EN, `docs/README.md` ES/EN, `CLAUDE.md`) cita la forma que funciona. Los registros fechados no se reescriben.
  - **C-12** E6 — `scope-check.py` con lista de exclusión para lo que no es de ninguna tarea (`CONTINUE-HERE*.md`, `.claude/**`), con default en el script y override en `dev.json`.
  - **C-13** E7 — `usage-meter.py` en Windows: (i) localizar la carpeta de transcripciones cuando el `cwd` lleva espacios (`_project_transcript_dir` sustituye `/ \ . :` por `-` pero **no el espacio**; en este repo la carpeta real es `C--Users-…-OneDrive---Imagina-Media-…`), y (ii) que el agregado de `fuente: estimado` sea visible (`/doctor` o `/roadmap-metrics` cuentan cuántos bloques `generacion:` son estimados).
- **Fuera (con motivo):**
  - **Prosa de `agents/*.md`, `commands/*.md`, `skills/*/SKILL.md` en el bloque (a)** — §7: es `plugin-dev` (≤ 200 líneas, `--diet-check`). En (b) solo la que un hueco exija.
  - **Cualquier feature, flag o exit code nuevo en (a)** — §7. Lo que parezca defecto se anota y va por su cauce (`quick-implement` o iniciativa). Excepciones **declaradas** aquí: CA-06 (el detector cuenta menos TODO) y CA-07 (flag aditivo de exclusión); ninguna otra.
  - **`brief-budget`** (composición del brief) — §7: iniciativa propia, ordenada después.
  - **Perseguir el 7,6 % de duplicado** — §7 y conclusión del §2: no baja sin la decisión del §5; el objetivo son las funciones largas y las copias accidentales.
  - **La decisión del §5** — la toma `architect`, no esta spec ni su evaluación.
  - **Las copias deliberadas y guardadas** (`celdas_md` y compañía) — §6.4: no se tocan hasta el §5; si se elige O1, entran en el registro sin cambiar de texto.
  - **E8** (guardarraíl del tope del brief recorre un solo ledger sin `design.md`) — **ya presupuestado como C-05 de `brief-budget`**; aquí se cita, no se paga dos veces.
  - **O3 (import común)** — descartada por el análisis: rompe el standalone (`docs/INTEROP.md`).
  - **Funciones largas fuera de los cinco hotspots** (`journal.py` 6, `code-health.py` 5, adaptadores JS 5+5, `jira-flow.py`, `deps-inventory.py`, `release.py`, `ledger-lint.py`, `evals/check.py`, `coverage-check.py`) — §8 fija la señal en los cinco hotspots; el resto es deuda registrada, no alcance.
  - **Reescribir los ~104 ficheros que citan `/dev-cycle`** — la mayoría son registros fechados del roadmap; precedente `sin-motor-externo`.

## Manejo de errores

| Caso | Comportamiento |
|---|---|
| `code-health --baseline` dice «empeora» en una tarea del bloque (a) | La tarea no se cierra; se revierte o se corrige hasta «mejora» (§6.1) |
| Un test existente falla tras un refactor | Se corrige el refactor, **no el test**; un test que hubiera que cambiar para pasar es un cambio de comportamiento → fuera de (a) |
| Durante el refactor aparece un defecto real | Se anota (ledger / gotcha) y va por su cauce; no se corrige en la misma tarea (§7) |
| `architect` no ha decidido el §5 al llegar a C-03 | C-03 y el registro E9 quedan bloqueados; el resto de (a) y todo (b) siguen |
| Se elige O2 y el módulo vendorizado no se resuelve en el árbol de trabajo | El script degrada al comportamiento actual (copia local) con aviso; `export-*.py --check` lo detecta |
| Comprobación nueva del linter (C-07) da falso positivo (placeholders `<x>.py`, `/algo`) | Lista de tolerancias explícita en el linter; nunca un error que bloquee la CI por un ejemplo de plantilla |
| `test-plan: n/a` ausente en un plan sin UI (C-08) | `qa` avisa una vez con el comando que lo fija y termina limpio (exit 0); no entra en bucle |
| Lente C se dispara de más tras C-10 | Se mide la tasa sobre los últimos ledgers; si sube el coste por revisión, la heurística se acota (`dev.json` `revision.excluir`) |
| `usage-meter` sigue sin transcripciones tras C-13 (i) | Degrada a `fuente: estimado` como hoy, pero el agregado (ii) lo hace visible |

## Criterios de aceptación

**Bloque (a) — cero cambio de comportamiento**

- [ ] [GWT] CA-01 — Dado el árbol tras cerrar C-01 y C-02, Cuando se ejecuta `python skills/code-health/scripts/code-health.py . --exclude-tests --json --top 1000`, Entonces las funciones > 30 líneas en `task-brief.py` + `knowledge-find.py` + `doctor.py` + `lint_plugin.py` + `build_dashboard.py` son **≤ 16** y ninguna función **nueva** supera 60 líneas.
- [ ] [GWT] CA-02 — Dado cualquier tarea del bloque (a) cerrada, Cuando se ejecuta `code-health.py . --exclude-tests --json --baseline docs/roadmap/2026-09-09-plugin-refactor/code-health-baseline.json` con los **mismos flags** de la línea base, Entonces el veredicto es «mejora» y nunca «empeora».
- [ ] [GWT] CA-03 — Dado el árbol antes y después de cada tarea de (a), Cuando se ejecutan `pytest -q tests/ agent-kits/shared/ skills/`, `python scripts/lint_plugin.py`, `python evals/check.py`, `python scripts/export-interop.py --check` y `python scripts/release.py --dry-run`, Entonces el resultado (tests que pasan, avisos, exit codes) es **idéntico** y en verde.
- [ ] CA-04 — Ningún test existente se modifica ni se borra en el bloque (a); los únicos tests nuevos son los de CA-06 y CA-07 (excepciones declaradas) y el de copias declaradas de CA-05.
- [ ] [GWT] CA-05 — Dada la decisión del §5 tomada, Cuando se cierra C-03, Entonces los cuatro pares accidentales del §2 (y el patrón E9) están **o** en un registro comparado byte a byte por UN test (O1) **o** eliminados **o** vendorizados por el empaquetador (O2), y `grep -rn "sin_vallas\|_REVISION_HDR_FALLBACK"` devuelve solo copias registradas.
- [ ] [GWT] CA-06 — Dado el árbol actual, Cuando se ejecuta `code-health.py . --exclude-tests --json`, Entonces `todos` es **1** (`agent-kits/shared/usage-meter.py:380`) y el test nuevo del detector cubre: comentario que enumera marcadores, la prosa «TODO (» en castellano y el propio fichero del detector.
- [ ] [GWT] CA-07 — Dado `interop/` presente, Cuando se ejecuta `code-health.py` con la exclusión de rutas generadas, Entonces el par `hooks/opencode-plugin.js` ↔ `interop/opencode/plugins/custom-agents-hooks.js` (118 líneas) **no** aparece en duplicados, y sin el flag la salida es byte-idéntica a la actual (default sin cambio).
- [ ] CA-08 — Los contratos congelados no cambian: `grep -n "add_argument" <script>` y los exit codes de cada hotspot son idénticos antes/después; la forma del `--json` de `knowledge-find.py` y `scope-check.py` se compara con una salida capturada antes del refactor.
- [ ] CA-09 — `agents/*.md`, `commands/*.md` y `skills/*/SKILL.md` no aparecen en el diff del bloque (a) (`git diff --stat <base>..HEAD -- agents commands 'skills/*/SKILL.md'` vacío).

**Bloque (b) — encadenamiento**

- [ ] CA-10 — Existe la matriz de contratos en `docs/agents/` junto a `ROLES.md`, con una fila por arista pieza → pieza (invocador, invocado, flags, exit codes, ficheros, marcadores) y cubre al menos las diez aristas E1–E10.
- [ ] [GWT] CA-11 — Dado un `agents/x.md` que cita `` `agent-kits/shared/no-existe.py` ``, Cuando se ejecuta `python scripts/lint_plugin.py`, Entonces avisa con fichero y ruta; y con el árbol actual **no** produce ningún aviso nuevo (65 rutas citadas existen o están toleradas como placeholder).
- [ ] [GWT] CA-12 — Dado un doc que cita `` `/no-existe` ``, Cuando se ejecuta el linter, Entonces avisa; `/algo`, `/nombre` y los comandos nativos (`/clear`, `/agents`, `/reload-plugins`) están tolerados.
- [ ] CA-13 — Cada regla «al tocar X regenera/actualiza Y» de `CLAUDE.md` está en la matriz con su puerta ejecutable (`--check`, test o lint) nombrada; el linter falla si una fila de la matriz no tiene puerta.
- [ ] [GWT] CA-14 — Dado un plan sin UI con `test-plan: n/a (sin UI)`, Cuando `/dev-cycle` llega a la Fase 3 e invoca `qa`, Entonces `qa` termina limpio sin pedir regenerar el `test-plan.md` y lo deja escrito en el informe; sin el marcador, avisa una vez y termina (no bucle).
- [ ] CA-15 — La plantilla de tareas del `planner` y su prompt incluyen `interop/**` en `Archivos` cuando la tarea toca `commands/`, `agents/` o `hooks/`; `implementer` regenera; el prompt de la Lente A ejecuta `export-interop.py --check` y lo cita ✓/✗.
- [ ] [GWT] CA-16 — Dado un diff que introduce texto controlado por el consumidor (`.claude/**`, `dev.json`, `personas/*.md`) en una cadena que acaba en un brief o prompt, Cuando se ejecuta `review-lens-select.py`, Entonces `lente_c: true` con el motivo; el caso real de `project-specialization` F1 (tres `lente_c: false`) pasa a `true` en el test.
- [ ] [GWT] CA-17 — Dado el plugin instalado desde el marketplace, Cuando se ejecuta `/doctor`, Entonces informa del nombre real de los comandos (`/custom-agents:<cmd>`) y ⚠️ si la doc viva cita la forma corta; README/INSTALL/docs/README ES y EN y `CLAUDE.md` citan la forma que funciona.
- [ ] [GWT] CA-18 — Dado un diff con `CONTINUE-HERE.md` y `.claude/usage-state.json` tocados, Cuando se ejecuta `scope-check.py`, Entonces no los reporta «fuera de alcance»; con `dev.json` `alcance.excluir` se amplía la lista; test con mutante.
- [ ] [GWT] CA-19 — Dado un `cwd` con espacios cuya carpeta `~/.claude/projects/<encoded>` existe, Cuando `usage-meter.py start` se ejecuta, Entonces `transcriptDir` no es `null`; test unitario de `_project_transcript_dir` con `cwd` con espacios, y `/doctor` (o `/roadmap-metrics`) muestra «N de M bloques `generacion:` con `fuente: estimado`».
- [ ] CA-20 — Todo cambio de prosa de (b) regenera `interop/` (`export-interop.py --check` verde), pasa `evals/check.py` y actualiza el espejo EN cuando el fichero lo tiene.

## Pruebas

- **Bloque (a)**: la prueba ES la suite existente sin tocar (CA-03, CA-04) más `code-health --baseline` (CA-02). Capturas previas de los `--json` de `knowledge-find.py` y `scope-check.py` y del HTML/MD/JSON de `build_dashboard.py` sobre el roadmap actual, comparadas byte a byte tras cada tarea (CA-08). Tests nuevos solo en `skills/code-health/scripts/test_code_health.py` (CA-06, CA-07) y el test de copias declaradas (CA-05).
- **Bloque (b)**: tests unitarios con mutante para `lint_plugin.py` (CA-11/12/13), `review-lens-select.py` (CA-16), `scope-check.py` (CA-18), `usage-meter.py` y `doctor.py` (CA-17, CA-19); casos en `evals/cases/` para la prosa tocada (CA-14, CA-15); revisión de dos lentes por tramo con la Lente A contra esta spec y la matriz (CA-10).
- **Sin `test-plan.md`**: no hay UI. Esta iniciativa es la primera candidata a usar el marcador `test-plan: n/a (sin UI)` que introduce C-08.

## Referencias

- [`analysis.md`](analysis.md) §1–§9 y §8-bis (E1–E10) — fuente única del alcance; [`code-health-baseline.json`](code-health-baseline.json) y [`code-health-baseline.md`](code-health-baseline.md) — línea base 2026-09-09.
- `skills/code-health/scripts/code-health.py:452-460` — `add_argument`: no hay `--exclude` por ruta (verificado 2026-09-10); `:47-49` — `TODO_RE` acepta «palabra seguida de `(`».
- `agent-kits/shared/task-brief.py:574-587` y `skills/jira-sync/scripts/jira-flow.py:227-239` — `_REVISION_HDR_FALLBACK` (E9); `agent-kits/shared/ledger-lint.py:179` — `REVISION_HDR_PATTERN` canónica.
- `agent-kits/shared/usage-meter.py:84-94` — `_project_transcript_dir`: `re.sub(r"[/\\.:]", "-", cwd)` no sustituye espacios (E7-i).
- `agents/qa.md:94`, `agents/planner.md:40`, `commands/dev-cycle.md` Fase 3 — la contradicción E1.
- `tests/test_knowledge_index.py` — única comparación byte a byte de copias (`celdas_md` y compañía); `tests/test_console_encoding.py` + `lint_plugin.py` (`CONSOLE_MARK`, `snippet_al_arrancar`) — guardarraíl estructural del snippet UTF-8 (GOT-005).
- `docs/agents/ROLES.md` — matriz de roles junto a la que vive la matriz de contratos (C-06). `docs/INTEROP.md` — requisito multi-runtime que descarta O3.
- `docs/roadmap/2026-09-09-brief-budget/spec.md` C-05 — cubre E8. `docs/roadmap/CALIBRATION.md` fila `memory-retrieval` — la revisión y su corrección son la partida grande.

## Decisiones confirmadas (revisión del usuario · pendiente)

1. Dos bloques separados, (a) con cero cambio de comportamiento y (b) como características propias. **Pendiente de confirmar en la puerta go/no-go.**
2. La decisión del §5 va a `architect` (Fase 2-bis); O3 descartada. **Pendiente.**
3. Orden: este refactor antes que `brief-budget`. **Ya ordenado por el usuario (go de `brief-budget` «DESPUÉS de este refactor»).**

## Supuestos

- **S-1** Las cifras de la línea base (36 · 14.259 · 7,6 % · 273 · anidamiento 6 · 8 TODO) y las 32 funciones largas en hotspots son las verificadas por el orquestador el 2026-09-09/10; no se re-miden aquí. El total 105 → 104 por T-01 de `project-specialization` ya está integrado en `master` (919cca4).
- **S-2** El bloque UTF-8 (`doctor.py:56` ↔ `guardrail-check.py:49` ↔ `build_dashboard.py:14` ↔ `evals/run.py:55`), listado en el §2 como accidental, **ya es deliberado, declarado y guardado**: `windows-console` T-01 lo replicó LITERAL a propósito (GOT-005) y `tests/test_console_encoding.py` + `lint_plugin.py` lo vigilan por `ast` (`CONSOLE_MARK`). Se asume que C-03 lo registra sin tocarlo y que los pares accidentales son **cuatro** (54 líneas), no ocho. Lo verificaría: `grep -n "CONSOLE_MARK\|snippet_al_arrancar" tests/test_console_encoding.py scripts/lint_plugin.py`.
- **S-3** El bloque (a) se presupuesta sobre O1 para C-03 (el mecanismo ya existe); si `architect` elige O2, C-03 crece (generador + `--check`) — la evaluación lo cuantifica como delta.
- **S-4** La comparación con `--baseline` se hace **con los mismos flags** con que se tomó la línea base; tras C-05 se toma una segunda línea base con la exclusión activa. Comparar una salida excluyendo `interop/` contra la línea base sin excluirlo daría «mejora» ficticia (−118 líneas duplicadas).
- **S-5** C-11 no reescribe los registros fechados que citan `/dev-cycle` (≈ 104 ficheros); solo la doc viva. Si el usuario quiere el barrido completo, es una característica aparte.
- **S-6** C-07 (c) necesita que las reglas «al tocar X regenera Y» estén enumeradas en un sitio parseable (la matriz de C-06); sin eso, (c) no es lintable. Por eso C-06 precede a C-07.
- **S-7** El `test-plan: n/a (sin UI)` de C-08 se emite en el frontmatter de `improvement-plan.md` (o donde fije `planner`); `qa-gate.py` no cambia de contrato.
- **S-8** Windows es el único entorno donde E7 está observado; el test de CA-19 se hace con `cwd` sintético (con espacios) para que corra igual en CI Linux.
