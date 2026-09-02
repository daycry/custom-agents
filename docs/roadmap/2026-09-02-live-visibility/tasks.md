---
tasks: live-visibility
descripcion: Información en vivo mientras corren las tareas — línea de progreso determinista del ledger (hook PostToolUse), estado de iniciativas al terminar subagentes (SubagentStop), contexto al arrancar/retomar/compactar (SessionStart) y statusline opt-in con coste de sesión.
estado: completado        # borrador | en-progreso | completado | cancelado
creado: 2026-09-02
actualizado: 2026-09-02
via: rapida               # vía rápida de /dev-cycle: sin spec/evaluación/plan; conserva revisión de dos lentes + suites
generacion:
  fuente: estimado        # usage-meter no disponible en este entorno (sandbox cloud)
---

# Checklist de Tareas — live-visibility (vía rápida)

| | |
|---|---|
| **Estado** | completado |
| **Fecha** | 2026-09-02 |
| **Plan** | n/a — **vía rápida** (sin spec/evaluación/plan; ledger ligero + revisión de dos lentes + verificación) |

> **⚠️ Ledger canónico de progreso.** Este fichero es la **fuente única de verdad** del avance del cambio. **Cualquier** implementador —el agente `implementer`, el chat principal, o un orquestador externo— **debe** marcar aquí cada tarea (checkbox + estado) al completarla y actualizar el resumen. Los ledgers propios de otras herramientas son **espejo**, no fuente.

> **Decisión del usuario (2026-09-02).** Hoy, mientras `implementer`/subagentes trabajan, el usuario solo ve avisos de error del ledger. Se quiere progreso visible, estado al retomar y supervivencia a la compactación de contexto — todo **determinista** (scripts con tests + exit codes), sin prosa extra en los agentes, y **sin bloquear jamás** (hooks siempre exit 0; sin `python3`/`jq` → silencio).

> **Contratos oficiales verificados (2026-09-02).** Fuente: `https://code.claude.com/docs/en/hooks.md` y `https://code.claude.com/docs/en/statusline.md` (la doc `hooks.md` supera el tope de lectura del `WebFetch` del sandbox; el tramo final se contrastó con el espejo íntegro `github.com/ericbuess/claude-code-docs/docs/hooks.md`, cuyo prefijo coincide línea a línea con la oficial salvo espacios de tabla). Hallazgos que fijan el diseño:
> - `systemMessage` es campo **universal de primer nivel** («Warning message shown to the user»); `PostToolUse` y `SubagentStop` lo muestran al usuario. `PostToolUse` no admite decisiones de bloqueo; `hookSpecificOutput` exige `hookEventName`.
> - `additionalContext` **debe ir anidado** en `hookSpecificOutput` (en primer nivel se ignora en silencio). En `SessionStart` la forma es `{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"…"}}`; el stdout en texto plano también entra como contexto en ese evento.
> - Matchers de `SessionStart`: `startup` · `resume` · `clear` · `compact` · `fork`, alternativas con `|` (regex) → `"startup|resume|compact"` es válido. `SubagentStop` matchea por **tipo de agente** (sin matcher = todos). `${CLAUDE_PLUGIN_ROOT}` y `${CLAUDE_PROJECT_DIR}` se exportan a los hooks. Salidas de hook capadas a 10.000 caracteres.
> - `PostToolUse` stdin: `tool_name`, `tool_input.file_path` (absoluta), `tool_response`. `SubagentStop` stdin: `agent_id`, `agent_type`, `last_assistant_message`, `stop_hook_active`. `SessionStart` stdin: `source`.
> - Statusline: `settings.json` → `"statusLine": {"type":"command","command":"<ruta>", "padding"?: n}`; stdin con `model.display_name`, `cost.total_cost_usd`, `context_window.used_percentage` (puede ser `null` al inicio). La doc **no** documenta `${CLAUDE_PLUGIN_ROOT}` en `statusLine.command` (solo `~`), y el `settings.json` de un plugin solo admite `agent`/`subagentStatusLine` → la ruta se escribe **absoluta** en el `settings.json` del proyecto (contradice la hipótesis del brief; ver T-03).

---

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervisión (real/est) | Tokens (real/est) |
|------|------------|-------|----------|-----------------------|------------------------|------------------------|-------------------|
| Fase única — visibilidad en vivo | 4 | 4 | 100% | 3,8 / 4,0h | 0,20 / 0,20h | 0,05 / 0,05h | 78k / 90k |
| **TOTAL** | **4** | **4** | **100%** | **3,8 / 4,0h** | **0,20 / 0,20h** | **0,05 / 0,05h** | **78k / 90k** |

---

## Fase única — visibilidad en vivo

**Estado**: completado · **Estimado**: 4,0h · **Real**: 3,8h (estimado) · **Coste est.**: ≈210 € · **Tokens est.**: 90k

### T-01 — `progress-report.py` (script determinista + tests)

- **Descripción**: `agent-kits/shared/progress-report.py` con subcomandos `line <tasks.md>` (una línea `📋 <slug> · T-04/12 completadas (33%) · fase 2/4 «<nombre>» · en curso: T-05 <título> · IA real 1h12m`), `active [--root]` (iniciativas `en-progreso` de `docs/roadmap/*/tasks.md`, exit 0 siempre, errores por fichero → stderr), `session [--root]` (bloque ≤15 líneas: activas + tareas en curso + marcadores huérfanos de `usage-meter.py status` + línea de retoma; si nada activo → una línea neutra) y `--json` en `line`/`active`. Reutiliza el parser de `ledger-lint.py` (refactor mínimo: función `parse_ledger()` importable sin efectos secundarios, CLI intacta). Tests en `agent-kits/shared/test_progress_report.py`.
- **Estado**: completado
- **Tiempo humano**: est. 1,5h · real 1,4h (estimado)
- **Tiempo IA (ejec.)**: est. 0,08h · real 0,08h (estimado)
- **Supervisión**: est. 0,02h · real 0,02h (estimado)
- **Archivos**: `agent-kits/shared/progress-report.py` (nuevo), `agent-kits/shared/test_progress_report.py` (nuevo), `agent-kits/shared/ledger-lint.py` (parser expuesto)

**Criterios de aceptación**
- [x] `line` sobre un ledger de 2 fases produce la línea con el formato exacto; sin horas reales omite el tramo `IA real`. Salida real sobre este ledger: `📋 live-visibility · T-00/4 completadas (0%) · fase 1/1 «visibilidad en vivo» · en curso: T-01 \`progress-report.py\` (script determinista + tests)`.
- [x] Ledger corrupto no explota: `line` → exit 2 con aviso en stderr; `active` lo salta con aviso y exit 0 (`test_line_corrupto_no_explota`, `test_active_lista_solo_en_progreso_y_salta_corruptos`).
- [x] Roadmap sin activas: `active` imprime `sin iniciativas en progreso`; `session` imprime una única línea neutra (`roadmap: sin iniciativas en progreso`).
- [x] `tests/test_ledger_lint.py` sigue verde tras el refactor (`10/10 OK`; salida de `ledger-lint.py` idéntica en los 16 ledgers del repo antes/después); `pytest agent-kits/shared/test_progress_report.py` → `18 passed`.

### T-02 — Hooks de progreso y de sesión

- **Descripción**: `hooks/progress-line.sh` (PostToolUse Write|Edit|MultiEdit sobre `*docs/roadmap/*tasks.md` → `{"systemMessage": "<línea>"}`, debounce por `.claude/.progress-last`), `hooks/subagent-progress.sh` (SubagentStop → `systemMessage` con las activas, solo si hay), `hooks/session-context.sh` (SessionStart `startup|resume|compact` → `hookSpecificOutput.additionalContext`; línea neutra → nada). Registro en `hooks/hooks.json`; `.claude/.progress-last` en `.gitignore`. Misma resolución de rutas que `ledger-lint-warn.sh`. Nunca exit ≠ 0.
- **Estado**: completado
- **Tiempo humano**: est. 1,0h · real 0,9h (estimado)
- **Tiempo IA (ejec.)**: est. 0,05h · real 0,05h (estimado)
- **Supervisión**: est. 0,01h · real 0,01h (estimado)
- **Dependencias**: T-01
- **Archivos**: `hooks/progress-line.sh` (nuevo), `hooks/subagent-progress.sh` (nuevo), `hooks/session-context.sh` (nuevo), `hooks/hooks.json`, `.gitignore`

**Criterios de aceptación**
- [x] Simulación de stdin de los 3 hooks con salida real (desde la raíz del repo, con `export CLAUDE_PLUGIN_ROOT=$PWD CLAUDE_PROJECT_DIR=$PWD` — Claude Code exporta ambas; sin ellas el hook resuelve por `find` sobre `.claude/`, como `ledger-lint-warn.sh`):
  - `echo '{"tool_input":{"file_path":"'"$PWD"'/docs/roadmap/2026-09-02-live-visibility/tasks.md"}}' | bash hooks/progress-line.sh` → `{"systemMessage": "📋 live-visibility · T-01/4 completadas (25%) · fase 1/1 «visibilidad en vivo» · en curso: T-02 Hooks de progreso y de sesión · IA real 5m"}` · exit 0.
  - `echo '{"hook_event_name":"SubagentStop","agent_type":"implementer"}' | bash hooks/subagent-progress.sh` → `{"systemMessage": "📋 knowledge-split · T-05/5 completadas (100%) · …\n📋 live-visibility · T-01/4 completadas (25%) · …"}` · exit 0.
  - `echo '{"hook_event_name":"SessionStart","source":"resume"}' | bash hooks/session-context.sh` → `{"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "Roadmap en progreso (ledger canónico = tasks.md):\n- 📋 knowledge-split · …\n- 📋 live-visibility · … en curso: T-02 …\n  · en-progreso: T-02 Hooks de progreso y de sesión\nLedger canónico: docs/roadmap/<…>/tasks.md — retoma desde la tarea en-progreso"}}` · exit 0. Con `CLAUDE_PROJECT_DIR=/tmp` (sin `docs/roadmap/`) → sin salida, exit 0. Con `PATH=/nonexistent` (sin python3) → sin salida, exit 0.
- [x] Segunda edición idéntica del mismo ledger → `progress-line.sh` no emite nada (debounce vía `.claude/.progress-last`, verificado: 2.ª invocación sin stdout, exit 0). Fichero fuera de `docs/roadmap/` (incl. forma `edits[]` de MultiEdit) → sin salida.
- [x] `bash -n` de los 3 hooks OK; `hooks/hooks.json` JSON válido (`json.load` OK) con `PostToolUse` (matcher `Write|Edit|MultiEdit`), `SubagentStop` (sin matcher = todos los tipos de agente) y `SessionStart` (matcher `startup|resume|compact`; se excluye `clear` a propósito: tras `/clear` el usuario empieza de cero y `fork` hereda el contexto). Ambos JSON de salida validados con `json.load`.

### T-03 — Statusline opt-in

- **Descripción**: `statusline/roadmap-statusline.sh` lee el JSON de stdin (`model.display_name`, `cost.total_cost_usd`, `context_window.used_percentage`) y añade `progress-report.py active --json` (una iniciativa: `slug T-04/12 33%`; varias: `N iniciativas activas`). Una línea ≤ ~100 caracteres. Degrada: sin `jq` → `python3`; sin ninguno → solo el modelo. Paso 5-bis en `commands/setup.md` (opt-in, default No; mergea `statusLine` en `.claude/settings.json` con ruta ABSOLUTA; no pisa una `statusLine` previa sin confirmación; persiste `"statusline"` en `dev.json`; reversión documentada). Mención en `docs/observability.md` + EN.
- **Estado**: completado
- **Tiempo humano**: est. 0,8h · real 0,8h (estimado)
- **Tiempo IA (ejec.)**: est. 0,04h · real 0,04h (estimado)
- **Supervisión**: est. 0,01h · real 0,01h (estimado)
- **Dependencias**: T-01
- **Archivos**: `statusline/roadmap-statusline.sh` (nuevo), `commands/setup.md`, `docs/observability.md`, `docs/en/observability.md`

**Criterios de aceptación**
- [x] Simulación con el JSON de ejemplo de la doc oficial: `echo '{"model":{"display_name":"Opus"},"cost":{"total_cost_usd":0.01234},"context_window":{"used_percentage":8}}' | bash statusline/roadmap-statusline.sh` → en este repo (2 activas) `[Opus] $0.01 ctx 8% · 📋 2 iniciativas activas`; con una sola activa (`CLAUDE_PROJECT_DIR` a una copia con solo esta iniciativa) `[Opus] $0.01 ctx 8% · 📋 live-visibility T-02/4 50%` (55 caracteres); sin `docs/roadmap/` → `[Opus] $0.01 ctx 8%`; `used_percentage: null` → se omite el tramo `ctx`. Exit 0 en todos.
- [x] Sin `jq` en PATH → misma línea vía `python3` (verificado con un PATH sin jq); sin `jq` ni `python3` → `[Opus]` y exit 0; stdin vacío → sin salida, exit 0. `bash -n` OK. **Defecto cazado en la prueba:** el primer borrador usaba `f"{r[\"slug\"]}"` dentro de una cadena bash de comillas simples (los `\"` son literales → SyntaxError silenciado → tramo roadmap vacío); corregido con `%`-format.
- [x] `commands/setup.md` paso 5-bis documenta activación (opt-in, default No; ruta resuelta con `find` en tiempo de setup y escrita ABSOLUTA), no-pisar (`statusLine` previa se conserva salvo confirmación explícita), persistencia `"statusline"` en `dev.json` y reversión. Mención en `docs/observability.md` + `docs/en/observability.md` (sección «Visibilidad en vivo» / «Live visibility»). **Decisión frente al brief:** la doc oficial NO admite `${CLAUDE_PLUGIN_ROOT}` en `statusLine.command` (solo `~`) y el `settings.json` de un plugin solo admite `agent`/`subagentStatusLine` → ruta absoluta en el `settings.json` del proyecto, como preveía el brief en su caso por defecto.

### T-04 — Documentación, convenciones y linter

- **Descripción**: `docs/CONVENTIONS.md` + EN (regla 8: eventos usados y principio «los hooks informan, no deciden; siempre exit 0»), `skills/plugin-dev/SKILL.md` (fila hook del Paso 0), `docs/FLOWS.md` + EN (flujo «visibilidad en vivo»), `README.md` + `README.es.md` («qué obtienes»), `docs/README.md` + EN si indexan hooks/scripts, `agent-kits/shared/README.md` (inventario), `CLAUDE.md` (árbol `statusline/` + fila hooks), `docs/roadmap/README.md` (fila). `scripts/lint_plugin.py`: comprobación mínima de `hooks/hooks.json` (JSON válido; cada `command` referencia un fichero existente y ejecutable) + test en `tests/test_lint_plugin.py`. NO se toca `CHANGELOG*.md` (lo hace el orquestador).
- **Estado**: completado
- **Tiempo humano**: est. 0,7h · real 0,7h (estimado)
- **Tiempo IA (ejec.)**: est. 0,03h · real 0,03h (estimado)
- **Supervisión**: est. 0,01h · real 0,01h (estimado)
- **Dependencias**: T-01, T-02, T-03
- **Archivos**: `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md`, `skills/plugin-dev/SKILL.md`, `docs/FLOWS.md`, `docs/en/FLOWS.md`, `README.md`, `README.es.md`, `docs/README.md`, `docs/en/README.md`, `agent-kits/shared/README.md`, `CLAUDE.md`, `docs/roadmap/README.md`, `scripts/lint_plugin.py`, `tests/test_lint_plugin.py`, `docs/roadmap/2026-08-20-knowledge-split/tasks.md` (estado a `completado`, orquestador `7dae657`)

**Criterios de aceptación**
- [x] Cada doc ES tocada tiene su espejo EN actualizado en el mismo cambio: `CONVENTIONS` (regla 8, nota «Visibilidad en vivo (hooks)»), `FLOWS` (flujo 6b + nodo `statusline`/`settings.json` en el 7), `observability` (sección nueva + coexistencia de hooks), `README`/`README.es` (fila «Progreso en vivo»), `docs/README` + `docs/en/README` (frase de observabilidad; no indexan hooks/scripts). Solo ES por convención: `CLAUDE.md` (árbol `statusline/`, filas Linter/Determinismo/Hooks), `skills/plugin-dev/SKILL.md` (fila hook del Paso 0), `agent-kits/shared/README.md` (inventario), `docs/roadmap/README.md` (fila). `test_mermaid_blocks: 28 diagrama(s) OK`.
- [x] `python3 scripts/lint_plugin.py` → `8 agentes · 0 errores · 3 avisos` (avisos previos de nombres genéricos). Comprobación nueva `lint_hooks()`: JSON válido con raíz `hooks`, cada `command` con `${CLAUDE_PLUGIN_ROOT}/<ruta>` debe existir y ser ejecutable. TDD: RED `test_lint_plugin` falló en el caso 10 (`AssertionError` — el linter daba 0 errores con `hooks/fantasma.sh`), GREEN tras implementar → `test_lint_plugin: 11/11 OK` (casos 9 válido, 10 inexistente, 11 no-ejecutable + JSON inválido). Bits de ejecución verificados en git (`100755` en los 5 hooks y la statusline → seguro en clon limpio, GOT-002).
- [x] `python3 -m pytest -q tests agent-kits/shared` → `95 passed` (77 previos + 18 de `test_progress_report.py`); las 9 suites-script de CI en verde (`confluence_scope 25/25 · coverage-check OK · dashboard OK · ledger_lint 10/10 · lint_plugin 11/11 · mermaid 28 · qa_gate 13/13 · readme_badges 6 · worklog 13`); `bash -n` OK en los 5 hooks + statusline; `ledger-lint.py` de este fichero → `0 incoherencias · 1 avisos` (aviso legacy «Fase única», idéntico al de `knowledge-split`), exit 0.

---

## Revisión de dos lentes — intento 1: 8 gaps corregidos, 3 aceptados como deuda (commit `T-fix1`)

Cada gap se verificó reproduciéndolo antes de corregir (todos eran reales; ninguno rebatido):

| # | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|
| 1 | Nota del ledger decía que `knowledge-split` no se tocó, pero el orquestador lo cerró (`7dae657`) | T-04 | Nota corregida + fichero en `Archivos` | — |
| 2 | `parse_ledger` ignoraba el frontmatter con BOM UTF-8 → iniciativa invisible en `active`/statusline | T-01 | `text.lstrip("\ufeff")` en `parse_ledger` + `utf-8-sig` en `resumir` | `test_bom_utf8_no_oculta_la_iniciativa` (antes: `frontmatter == {}`) |
| 3 | `set -u` + `HOME` sin definir abortaba el `find` de los hooks (y de la statusline) | T-02, T-03 | `"${HOME:-}/.claude"` en los 3 hooks nuevos, `ledger-lint-warn.sh` y la statusline | `unset HOME` sin `CLAUDE_PLUGIN_ROOT` → exit 0 |
| 4 | `marcadores_huerfanos` leía `.claude/usage-state.json` del cwd, no de `--root` | T-01 | `usage-meter.py status --state <root>/.claude/usage-state.json` | `test_session_lee_usage_state_del_root_no_del_cwd` |
| 5 | «IA real» sumaba valores marcados `(estimado)`; `1h30m` → 1.0; `real: 2h` → None | T-01 | `ia_real_fuente` medido/estimado en el parser; solo lo medido rotula «IA real», si todo es estimado → «IA est.»; `_parse_horas` admite `XhYm` y `:` | `test_horas_estimadas_se_rotulan_ia_est`, `test_horas_medidas_ignoran_las_estimadas`, `test_parse_horas` (5 casos); salida de `ledger-lint.py` **idéntica en 16/16 ledgers** frente a `git show 721c67e:agent-kits/shared/ledger-lint.py` (salida completa, no solo la última línea) |
| 6 | Statusline: coste no numérico → `$0.00abc`; ruido stderr sin jq/python3 | T-03 | Coste/ctx solo si numéricos (si no, se omite el tramo); `2>/dev/null` en el camino sin parser | `{"cost":{"total_cost_usd":"abc"}}` → `[Opus] ctx 8%` |
| 7 | Linter: bit ejecutable como ERROR daría 5 falsos positivos con `core.fileMode=false` | T-04 | `lint_hooks()` devuelve `(errores, avisos)`; fichero inexistente = error, no ejecutable = aviso | `test_lint_plugin` caso 11 ajustado → `11/11 OK` |
| 8 | Rutas Windows nativas (`C:\…\docs\roadmap\…\tasks.md`) no casaban con el `case` | T-02 | `p="${p//\\//}"` antes del `case` en `progress-line.sh`, `ledger-lint-warn.sh` y `mark-docs-pending.sh` | payload con `\\` → misma `systemMessage` |

**Aceptados como deuda (no corregidos):** debounce de `.progress-last` no atómico bajo concurrencia (solo ruido, nunca pérdida) — **saldada en 2026-09-02-debt-cleanup (T-01a)**; título de tarea con negrita interna en `### T-XX` se muestra con los `**` — **saldada en 2026-09-02-debt-cleanup (T-01b)**; `hooks/hooks.json` con modo `100755` heredado del repo — **saldada en 2026-09-02-debt-cleanup (T-01c)**.

Tras la corrección: `pytest -q tests agent-kits/shared` → **104 passed** (95 + 9 nuevos); 9 suites-script verdes; `lint_plugin` → 0 errores · 3 avisos; `bash -n` OK en 5 hooks + statusline. Nota: la línea de progreso de ESTA iniciativa ahora rotula `IA est. 12m` (sus horas están marcadas `(estimado)`, como manda el gap 5).

## Dudas y decisiones para el orquestador

- **Doc oficial vs brief:** (1) `${CLAUDE_PLUGIN_ROOT}` NO está documentado para `statusLine.command` → ruta absoluta resuelta en `/setup` (caso por defecto del brief). (2) `SubagentStop` sí admite `hookSpecificOutput.additionalContext`, pero va al **subagente**, no al usuario → el hook usa `systemMessage` (al usuario), como pedía el brief. (3) El matcher de `SessionStart` omite `clear`/`fork` a propósito (el brief pedía `startup|resume|compact`).
- **Dato heredado (corregido por el orquestador, commit `7dae657`):** `docs/roadmap/2026-08-20-knowledge-split/tasks.md` estaba `en-progreso` pese a estar al 100 % → aparecía como «activa» en `active`/`session`/statusline. Puesto a `completado` (frontmatter + tabla); hoy `active` solo lista `live-visibility`.
- **CHANGELOG** no tocado (lo hace el orquestador). Tests de hooks: no hay suite de shell en el repo; la evidencia es la simulación manual de stdin anotada arriba (reproducible) + `bash -n` + linter de `hooks.json` — **saldada en 2026-09-02-debt-cleanup (T-06: `tests/test_hooks_shell.py`; verificación en sesión real → lista manual en `docs/observability.md`, T-05)**.
