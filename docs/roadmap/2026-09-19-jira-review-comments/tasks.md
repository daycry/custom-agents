---
verificacion: obligatoria
estado: completado
changelog: Fixed
generacion:               # vía rápida — ventana única de este ledger (usage-meter degradado en las 4 tareas: sin carpeta de transcripciones)
  fuente: estimado
  horas_ia: 0.7
  duracion: ~40m
---

# Checklist de Tareas — jira-review-comments (vía rápida: los comentarios de revisión no llegaban a Jira)

| | |
|---|---|
| **Estado** | completado |
| **Fecha** | 2026-09-19 |
| **Plan** | n/a — **vía rápida** (ledger ligero + revisión de dos lentes), a petición del usuario: «los reviews no añaden comentarios en las tareas de Jira: hace todo el flujo pero no se puede saber el resultado de la verificación ni de las x verificaciones de esa tarea» |

> **⚠️ Ledger canónico de progreso.** Este fichero es la **fuente única de verdad** del avance del plan. **Cualquier** implementador —el agente `implementer`, el chat principal, o un orquestador SDD externo— **debe** marcar aquí cada tarea (checkbox + estado) al completarla y actualizar el resumen. Los ledgers propios de otras herramientas son **espejo**, no fuente.

> **Diagnóstico (causa raíz, con evidencia).** El mecanismo funciona: `jira-flow.py plan --event gaps --actor reviewer --task T-01 --intento 1` sobre el ledger real de `knowledge-services`, con un `.claude/jira.json` habilitado y un `jira-state.json` de prueba, devolvió las 3 `ops` (etiqueta `ca-reviewer` → transición `reabrir` → comentario con la tabla completa de los 7 gaps del intento 1 y el pie «intento 2 de 3»). Lo que fallaba era la **propiedad**: `commands/dev-cycle.md` (tabla de eventos) decía que `revision`/`gaps` los dispara `adversarial-review`; `skills/adversarial-review/SKILL.md` §6 decía «el orquestador dispara»; `skills/jira-sync/references/review-publish.md` decía «el agente revisor» (que es solo lectura y no tiene tools de Jira); `docs/agents/ROLES.md` decía «lo publica el orquestador/implementer». Cuatro textos, cuatro dueños distintos → nadie lo ejecutaba y el ciclo terminaba sin rastro del veredicto de cada intento en Jira (violación de «un rol, un dueño», `ADR-011`). Además `dev-cycle.md` remitía a un «comentario FINAL (Paso 9 de `jira-sync`)» que no existe (es el Paso 7 y es por intento).

---

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervisión (real/est) | Tokens (real/est) |
|------|------------|-------|----------|-----------------------|------------------------|------------------------|-------------------|
| Fase 1 — Dueño único del evento de revisión en Jira | 2 | 2 | 100% | 0 / 1,0h | 0,4 (estimado) / 0,3h | 0 / 0,1h | — / 80k |
| Fase 2 — Selección de la sección correcta del intento (varias fases) | 2 | 2 | 100% | 0 / 0,8h | 0,3 (estimado) / 0,4h | 0 / 0,08h | — / 60k |
| **TOTAL** | **4** | **4** | **100%** | **0 / 1,8h** | **0,7 (estimado) / 0,7h** | **0 / 0,18h** | **— / 140k** |

---

## Fase 1 — Dueño único del evento de revisión en Jira

**Estado**: completado · **Estimado**: 1,0h · **Real**: — · **Coste est.**: ~50 € · **Tokens est.**: 80k

### T-01 — La skill `adversarial-review` publica el evento `revision`/`gaps` de CADA intento

- **Descripción**: `skills/adversarial-review/SKILL.md` §6 «Salida y traza» pasa de «el orquestador dispara» a un paso EJECUTABLE propio: nada más escribir la sección `## Revisión de dos lentes — intento N` corre `jira-flow.py plan --ledger <tasks.md> --event revision|gaps --actor reviewer --task T-XX --intento N --json` y aplica las `ops` con el conector; sin `jira.json`/issue degrada con aviso. `commands/dev-cycle.md`: la invocación de la skill (punto 2 de la Fase 3) deja de hablar de «comentario FINAL (Paso 9)» y dice «comentario firmado de CADA intento (Paso 7), lo ejecuta la propia skill»; la tabla de eventos fija el dueño («su paso 6, por intento; no el orquestador ni `reviewer`»); el bullet del worklog aclara que el comentario no es del orquestador. `skills/jira-sync/references/review-publish.md`: la cabecera del bloque `revision`/`gaps` nombra a la skill como ejecutor único (no al agente `reviewer`). `docs/agents/ROLES.md`: filas `reviewer` y `adversarial-review` coherentes con lo anterior. Interop regenerado.
- **Estado**: completado
- **Tipo**: docs (prosa de piezas: skill, comando, referencia, matriz de roles)
- **Tiempo humano**: est. 0,6h · real —
- **Tiempo IA (ejec.)**: est. 0,2h · real 0,3h (estimado; ventana compartida con T-02)
- **Supervisión**: est. 0,06h · real —
- **Archivos**: `skills/adversarial-review/SKILL.md`, `commands/dev-cycle.md`, `skills/jira-sync/references/review-publish.md`, `docs/agents/ROLES.md`, `interop/codex/prompts/dev-cycle.md`, `interop/opencode/commands/dev-cycle.md`
- **Verificación**: `grep -n "lo publica ESTA skill" skills/adversarial-review/SKILL.md && grep -c "Paso 9" commands/dev-cycle.md` → una coincidencia en la skill y `0` en el comando · `python scripts/export-interop.py --check` → «al día» · `python scripts/lint_plugin.py` → 0 errores
- **Changelog**: The adversarial review now posts its verdict to Jira after every attempt (the `revision`/`gaps` comment with the graded gap table), so each task's issue shows the result of each verification; before, four pieces each assumed another one would post it and nothing reached Jira.

**Criterios de aceptación**
- [x] Un solo dueño declarado en las cuatro piezas (skill §6, tabla de `dev-cycle`, `review-publish.md`, `ROLES.md`) y es el mismo: la skill `adversarial-review`
- [x] El paso de la skill es ejecutable tal cual (comando completo con `--actor reviewer --intento N`) y degrada con aviso sin Jira
- [x] Ninguna pieza remite ya a un «Paso 9» inexistente ni a un comentario «final» en lugar de «por intento»
- [x] `SKILL.md` ≤ 200 líneas; interop regenerado y `--check` limpio

### T-02 — Guardarraíl: test de propiedad única sobre los ficheros reales

- **Descripción**: `tests/test_review_jira_owner.py` lee los ficheros REALES (no fixtures) y falla si vuelve a abrirse el hueco: la skill contiene el comando `jira-flow.py … --event revision|gaps … --actor reviewer … --intento N`; la skill no dice que «el orquestador dispara» esos eventos; la tabla de `dev-cycle.md` nombra a `adversarial-review` en las filas `revision`/`gaps` y no cita «Paso 9» ni «comentario FINAL»; `review-publish.md` nombra a la skill como ejecutor; `ROLES.md` no atribuye la publicación al orquestador/implementer/reviewer. Además ejecuta `jira-flow.py` sobre un ledger de prueba con Jira habilitado y comprueba que el evento `gaps` del intento 1 produce el comentario con la tabla de gaps y el pie «intento 2 de 3» (así el test documenta también que el mecanismo funciona y que lo que faltaba era el dueño).
- **Estado**: completado
- **Tipo**: test
- **Tiempo humano**: est. 0,4h · real —
- **Tiempo IA (ejec.)**: est. 0,1h · real 0,1h (estimado)
- **Supervisión**: est. 0,04h · real —
- **Archivos**: `tests/test_review_jira_owner.py`
- **Verificación**: `python -m pytest -q tests/test_review_jira_owner.py` → todos en verde; revertir a mano la frase «el orquestador dispara» en la skill → el test falla nombrando la pieza
- **Changelog**: A regression test now guards that exactly one piece owns posting the review verdict to Jira.

**Criterios de aceptación**
- [x] El test corre contra los ficheros reales del repo y contra un ledger de prueba con Jira habilitado (mecanismo + propiedad)
- [x] Falla con mensaje que nombra la pieza y la frase ofensiva si se reintroduce un segundo dueño o el «Paso 9»

---

## Fase 2 — Selección de la sección correcta del intento (ledgers con varias fases)

**Estado**: completado · **Estimado**: 0,8h · **Real**: — · **Coste est.**: ~40 € · **Tokens est.**: 60k

> **Causa 2 (con evidencia).** Corregida la propiedad (Fase 1), el comentario seguía pudiendo ser el equivocado: `jira-flow.py::seccion_revision(texto, intento)` elegía la PRIMERA cabecera `## Revisión de dos lentes — intento N` que casara con ese número. Un ledger con varias fases (cada una arranca su propio bucle desde «intento 1») tiene VARIAS cabeceras con el mismo número — el real de `docs/roadmap/2026-09-15-knowledge-services/tasks.md` tiene 4 secciones «intento 1», una por fase — así que `--task T-04 --intento 1` caía en la sección de la Fase 1 (gaps de T-01/T-02/T-03), no encontraba filas de T-04 y devolvía `{"error": ["el intento 1 no tiene gaps para T-04 — usa --event revision"]}`: un «sin gaps» FALSO justo cuando SÍ los había, en la fase correcta. Además, las cabeceras reales de ese ledger para las fases 2-4 llevan un paréntesis tras el número («intento 1 (Fase 2: T-04, T-05, T-06): …») que ni siquiera casa con `REVISION_HDR_PATTERN` (exige `:` u fin de línea justo tras el número), así que esas secciones son invisibles para `jira-flow.py` y `task-brief.py` sin que nada avisara.

### T-03 — `jira-flow.py` elige la sección del intento por las tareas pedidas

- **Descripción**: `seccion_revision(texto, intento, tareas=None)` (nuevo parámetro opcional, retrocompatible) — entre TODAS las cabeceras con ese `intento`, elige la que MENCIONE alguna de las `tareas` pedidas, restringido a la cabecera/resumen o a la columna `Tarea` de sus filas (patrón `T-NN`; nunca `Corrección`/`Evidencia`, que citan tests y otras tareas de contexto y darían falsos positivos en un ledger real con fases que se referencian entre sí — comprobado con el ledger real: una fila de la Fase 1 cita "T-04" en su celda `Corrección`). Si ninguna cabecera menciona las tareas, usa la ÚLTIMA (más reciente) y añade un aviso explicando el porqué. Con una sola cabecera para ese `intento`, o sin `tareas`, el comportamiento no cambia. Los dos llamadores (`evidencia_aprobado` y el bloque `revision`/`gaps` de `construir_plan`) pasan ahora `tareas`; el aviso de fallback se añade a `avisos` del plan.
- **Estado**: completado
- **Tipo**: código (script determinista, sin modelo)
- **Tiempo humano**: est. 0,5h · real —
- **Tiempo IA (ejec.)**: est. 0,25h · real 0,2h (estimado; usage-meter degradado: sin carpeta de transcripciones)
- **Supervisión**: est. 0,05h · real —
- **Archivos**: `skills/jira-sync/scripts/jira-flow.py`, `skills/jira-sync/scripts/test_jira_flow.py`
- **Verificación**: `python -m pytest -q skills/jira-sync/scripts/test_jira_flow.py` → 47 passed (los 42 previos + 5 nuevos: selección por tarea en ambas fases, revisión limpia de una fase con gaps pendientes en otra, fallback con aviso, y el caso de una sola sección sin cambios). Además, contra el ledger REAL `docs/roadmap/2026-09-15-knowledge-services/tasks.md` (copiado a un tmp con `.claude/jira.json` `{"enabled": true}` y `.claude/jira-state.json` `{"tasks": {"T-04": {"issueKey": "KS-4"}}}`, y sus 10 cabeceras con paréntesis normalizadas a la forma sin paréntesis tras el número — ver nota de decisión más abajo): `plan --event gaps --actor reviewer --task T-04 --intento 1 --root <tmp> --json` → el comentario cita **"Revisión de dos lentes — intento 1: 16 gap(s)" (T-04)** con la fila `#40 Critical: curator-gate.py no tiene entrada en MODOS…` de la Fase 2, y NO ninguna fila de la Fase 1 (T-01/T-02/T-03); `--task T-01 --intento 1` sobre el mismo tmp sigue devolviendo la sección de la Fase 1 (`#5 Important: id_prefix por defecto…`).
- **Changelog**: The review comment posted to Jira for a task now comes from that task's own review round, not from a different phase that happened to share the same attempt number.

**Criterios de aceptación**
- [x] Ledger con Fase 1 «intento 1» (gaps de T-01) y Fase 2 «intento 1» (gaps de T-04): `--event gaps --task T-04 --intento 1` trae la tabla de la Fase 2 y NO la de la Fase 1
- [x] `--event gaps --task T-01 --intento 1` sobre el mismo ledger trae la de la Fase 1
- [x] `--event revision --task T-05 --intento 1` cuando la Fase 2 dice «sin gaps» para T-05 pero la Fase 1 tenía gaps (de T-01) con el mismo número: exit 0, comentario de revisión aprobada, sin transición de reapertura
- [x] Tarea sin mención en ninguna cabecera de ese intento: cae en la última con aviso en `avisos`
- [x] El comportamiento con una sola sección para ese `intento` no cambia (la suite previa de 42 tests sigue en verde)

**Nota de decisión (sin respaldo literal del encargo).** El ledger real de `knowledge-services` tiene sus cabeceras de las fases 2-4 con un paréntesis tras el número («intento 1 (Fase 2: …): …») que NO casa con `REVISION_HDR_PATTERN` — ni siquiera llegan a ser "candidatas" para T-03, son invisibles del todo (ese es exactamente el hallazgo de T-04). Normalizar el fichero real del repo está fuera del alcance de esta tarea (no está en `Archivos`, y es un ledger histórico cerrado de otra iniciativa), así que la verificación de arriba se hizo sobre una COPIA en un directorio temporal con esas 10 cabeceras reescritas a la forma sin paréntesis (`… — intento N: Fase X (T-…) — …`), no sobre el fichero del repo. Sin esa normalización, `--task T-04 --intento 1` sobre el fichero real tal cual sigue devolviendo el mismo error `{"error": ["el intento 1 no tiene gaps para T-04…"]}` que reportó el usuario, porque el problema en ESE ledger concreto es la Causa 2-bis (T-04: cabeceras que no casan), no la selección entre candidatas de T-03. T-03 por sí sola solo resuelve la ambigüedad entre secciones que SÍ casan con el patrón; T-04 (aviso de `ledger-lint`) es la única pieza que puede alertar de las que no casan — arreglarlas de verdad exige editar a mano cada ledger afectado, tarea que no corresponde a esta iniciativa.

### T-04 — `ledger-lint.py` avisa de cabeceras de revisión que NO casan con el patrón

- **Descripción**: en `lint()`, toda línea que empiece por `## Revisi` y contenga `dos lentes` pero no case con `REVISION_HDR_RE` produce un AVISO (no error: el ledger sigue siendo válido, solo esa sección queda invisible para `jira-flow.py`/`task-brief.py`): «línea N: cabecera de revisión no casa con REVISION_HDR_PATTERN: jira-flow/task-brief no la verán — usa `## Revisión de dos lentes — intento N: <resumen>` (sin paréntesis tras N)». No se tocó `skills/adversarial-review/SKILL.md` (ya documenta el formato correcto en su paso 6 y está a 200 líneas justas, sin hueco para una línea más) ni `commands/`/`agents/`/`hooks/` (T-04 no los toca, así que no aplica regenerar interop; `export-interop.py --check` sigue «al día» porque T-01/T-02 ya lo habían regenerado).
- **Estado**: completado
- **Tipo**: código (script determinista)
- **Tiempo humano**: est. 0,3h · real —
- **Tiempo IA (ejec.)**: est. 0,15h · real 0,1h (estimado; usage-meter degradado: sin carpeta de transcripciones)
- **Supervisión**: est. 0,03h · real —
- **Archivos**: `agent-kits/shared/ledger-lint.py`, `tests/test_ledger_lint.py`
- **Verificación**: `python tests/test_ledger_lint.py` → `test_ledger_lint: 25/25 OK` (los 23 previos + 2 nuevos: cabecera con paréntesis tras el número → aviso con el texto exacto del mensaje; cabecera con el resumen de fase dentro del `: <resumen>` en vez de un paréntesis tras el número → sin aviso)
- **Changelog**: `ledger-lint` now flags review headers with the wrong shape so a task's Jira comment never silently comes from the wrong review round.

**Criterios de aceptación**
- [x] Fixture con «intento 1 (Fase 2: T-04): …» → aviso con el texto de arriba
- [x] Fixture con «intento 1: Fase 2 (T-04) — …» → sin aviso
- [x] Es AVISO, no error (exit 0 con `--warn-only` y sin él, mismo criterio que el resto de avisos legacy del script)

**Nota (ruta declarada distinta a la del encargo).** El encargo cita `agent-kits/shared/test_ledger_lint.py`; el test real del repo vive en `tests/test_ledger_lint.py` (no hay copia en `agent-kits/shared/`) y es un script con `assert`/`main()`, no pytest — se ejecuta con `python tests/test_ledger_lint.py`, como el resto de la suite (`tests/test_suites_no_pytest.py`). Se usó la ruta real.
