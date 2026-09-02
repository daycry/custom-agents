---
tasks: deterministic-guardrails
descripcion: Los guardrails duros del implementer (alcance en docs/roadmap/, rama de trabajo, git destructivo) pasan de prosa a script determinista con tests, impuestos por un hook PreToolUse con alcance SOLO del agente implementer; comprobación de alcance del diff (scope-check) antes de la revisión de dos lentes; linter que valida los campos nativos `hooks`/`skills` del frontmatter.
estado: completado        # borrador | en-progreso | completado | cancelado
creado: 2026-09-02
actualizado: 2026-09-02
via: rapida               # vía rápida de /dev-cycle: sin spec/evaluación/plan; conserva revisión de dos lentes + suites
generacion:
  fuente: estimado        # usage-meter no disponible en este entorno (sandbox cloud)
---

# Checklist de Tareas — deterministic-guardrails (vía rápida)

| | |
|---|---|
| **Estado** | completado |
| **Fecha** | 2026-09-02 |
| **Plan** | n/a — **vía rápida** (sin spec/evaluación/plan; ledger ligero + revisión de dos lentes + verificación) |

> **⚠️ Ledger canónico de progreso.** Este fichero es la **fuente única de verdad** del avance del cambio. **Cualquier** implementador —el agente `implementer`, el chat principal, o un orquestador externo— **debe** marcar aquí cada tarea (checkbox + estado) al completarla y actualizar el resumen. Los ledgers propios de otras herramientas son **espejo**, no fuente.

> **Decisión del usuario (2026-09-02).** Las reglas «no toques `docs/roadmap/` salvo `tasks.md`», «trabaja en rama» y «sin push forzado» del `implementer` viven hoy solo en prosa: se cumplen si el modelo las recuerda. Se quieren **impuestas por script determinista con tests** (patrón `ledger-lint`/`qa-gate`), pero **sin romper a los demás agentes**: `planner`/`evaluator`/`analyst` escriben en `docs/roadmap/` legítimamente, así que el deny tiene alcance SOLO del `implementer` (frontmatter `hooks:` del agente), nunca en `hooks/hooks.json` global. Degradación: sin `python3` el hook no bloquea (exit 0) y avisa una vez por `systemMessage`; desactivable en `.claude/dev.json` (`guardrails`).

> **Contratos oficiales verificados (2026-09-02, WebFetch).** Fuente: `https://code.claude.com/docs/en/hooks.md` y `https://code.claude.com/docs/en/sub-agents.md`. Hallazgos que fijan el diseño:
> - **PreToolUse** — stdin: `tool_name`, `tool_input` (`file_path` en Write/Edit; `command` en Bash), `tool_use_id`; en hooks de subagente también `agent_id`/`agent_type`. Salida de decisión: `{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow|deny|ask","permissionDecisionReason":"…"}}` (los campos `decision`/`reason` de primer nivel están **deprecados**). Exit 2 = bloqueo con stderr al modelo; **exit 0 sin stdout = sin decisión** (sigue el flujo normal de permisos — el silencio no aprueba). `systemMessage` es campo universal. `${CLAUDE_PROJECT_DIR}` y `${CLAUDE_PLUGIN_ROOT}` se exportan al proceso del hook. Se elige **exit 0 + JSON `deny`** (no exit 2): la razón llega estructurada y un fallo interno del script nunca se confunde con un bloqueo.
> - **Frontmatter de agente** — campo `hooks:` («Lifecycle hooks scoped to this subagent», se registran solo mientras corre el subagente) con la MISMA forma que `settings.json`: `hooks: { PreToolUse: [ { matcher: "…", hooks: [ { type: command, command: "…" } ] } ] }`. Campo `skills:` = lista de nombres a **precargar** (se inyecta el contenido completo al arrancar; una skill ausente se salta con aviso). `isolation: worktree` = worktree temporal ramificado desde la rama por defecto (no desde HEAD) — **no se usa**: choca con el opt-in `worktree` de `dev.json` (worktree único por iniciativa ramificado desde la rama de trabajo, integrado por el ritual de la Fase 6).
> - **Contradicción con el brief:** la doc de sub-agents **no** menciona `${CLAUDE_PLUGIN_ROOT}` en los `command` del frontmatter (solo `./scripts/...` y `$TOOL_INPUT`); `hooks.md` sí lo declara disponible «en todos los hooks» como variable de entorno del proceso. Como la expansión ocurre en la shell, el `command` del frontmatter la usa **con fallback `find`** en la propia línea: si la variable no está, resuelve el wrapper por `find` sobre `.claude/`; si tampoco, `exit 0` (sin decisión, nunca rompe).

---

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervisión (real/est) | Tokens (real/est) |
|------|------------|-------|----------|-----------------------|------------------------|------------------------|-------------------|
| Fase única — guardrails deterministas | 5 | 5 | 100% | 4,2 / 5,0h | 0,23 / 0,25h | 0,06 / 0,06h | 88k / 110k |
| **TOTAL** | **5** | **5** | **100%** | **4,2 / 5,0h** | **0,23 / 0,25h** | **0,06 / 0,06h** | **88k / 110k** |

---

## Fase única — guardrails deterministas

**Estado**: completado · **Estimado**: 5,0h · **Real**: 4,2h (estimado) · **Coste est.**: ≈260 € · **Tokens est.**: 110k

### T-01 — `guardrail-check.py` (script determinista + tests)

- **Descripción**: `agent-kits/shared/guardrail-check.py pre-tool` lee el JSON del PreToolUse por stdin y decide. Reglas: (alcance) Write/Edit/MultiEdit/NotebookEdit sobre `docs/roadmap/**` que no sea `tasks.md` → deny (incl. `testing/**`, que es de qa); `docs/security-scan/**` → deny; `docs/knowledge/**` → permitido. (git) `git push --force|-f|--force-with-lease` → deny; `git checkout|switch main|master` → deny solo si la rama actual es una feature; `git branch -D` → deny; `rm -rf` sobre `/`, `~`, `.git` → deny. (rama) HEAD en `main`/`master` + Write/Edit fuera de `docs/roadmap/**/tasks.md` → deny; sin git → no aplica. Configurable en `.claude/dev.json` `guardrails: {ramaPrincipal, alcance, git}` (defaults `true`; `guardrails: false` apaga todo con aviso; fichero ausente/corrupto → defaults). Salida: JSON oficial `permissionDecision: deny` + razón en una frase (regla + cómo proceder); allow → sin stdout, exit 0. Normaliza `\`→`/` y absolutas → relativas a `CLAUDE_PROJECT_DIR`. Nunca exit ≠ 0 por error interno (stderr + allow).
- **Estado**: completado
- **Tiempo humano**: est. 1,5h · real 1,2h (estimado)
- **Tiempo IA (ejec.)**: est. 0,08h · real 0,07h (estimado)
- **Supervisión**: est. 0,02h · real 0,02h (estimado)
- **Archivos**: `agent-kits/shared/guardrail-check.py` (nuevo), `agent-kits/shared/test_guardrail_check.py` (nuevo)

**Criterios de aceptación**
- [x] `pytest agent-kits/shared/test_guardrail_check.py` → `20 passed` (cada regla allow/deny, ruta Windows `C:\proy\docs\roadmap\…`, ruta absoluta relativizada a `CLAUDE_PROJECT_DIR`, `dev.json` `guardrails: false` (aviso una vez, marca `.claude/.guardrail-off`) y por regla, sin git → rama no aplica, JSON inválido/vacío → allow con aviso en stderr, repo git real en `main`→deny / `feature/x`→allow). Ajuste tras la prueba: `git checkout main -- fichero` NO se bloquea (restaura ficheros, no cambia de rama).
- [x] Simulación (`CLAUDE_PROJECT_DIR=$PWD`, rama `feature/deterministic-guardrails`): Write `…/spec.md` → `{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": "«docs/roadmap/2026-09-02-deterministic-guardrails/spec.md» está en docs/roadmap/: el implementer solo toca tasks.md (ledger); el plan/spec/evaluación los cambia planner — anota la duda en tasks.md y sigue."}}` exit 0 · Bash `git push --force origin feature/x` → deny «`git push` forzado bloqueado: reescribe historia compartida — haz push normal…» exit 0 · Edit `…/tasks.md` → sin stdout, exit 0 · Write `scripts/lint_plugin.py` → sin stdout, exit 0.
- [x] El JSON de deny valida contra el contrato oficial (`hookSpecificOutput.hookEventName = PreToolUse`, `permissionDecision = deny`, `permissionDecisionReason` no vacío).

### T-02 — Cableado en `agents/implementer.md` + wrapper `hooks/implementer-guardrail.sh`

- **Descripción**: frontmatter `hooks:` (PreToolUse, matcher `Write|Edit|MultiEdit|NotebookEdit|Bash`) → wrapper `hooks/implementer-guardrail.sh` con la misma resolución de rutas que los otros hooks (`CLAUDE_PLUGIN_ROOT` → `find`); sin `python3` → exit 0 + `systemMessage` una vez por sesión (marca `${CLAUDE_PROJECT_DIR:-$PWD}/.claude/.guardrail-nopython`). Frontmatter **sin** `skills:` (precarga nativa confirmada por la doc, pero `jira-sync` + `confluence-publish` son opt-in y pesan ≈57 KB ≈ 15k tokens por arranque — token-diet; revisión intento 1, gap 1); `dependencies:` se mantiene (grafo del linter). Cuerpo §0 y §3: las reglas de alcance/rama/git están impuestas por hook; cómo desactivarlas; un DENY no es un error. Token-diet: sustituye prosa, no la duplica. `isolation: worktree` NO se usa (ver nota de contratos).
- **Estado**: completado
- **Tiempo humano**: est. 0,7h · real 0,6h (estimado)
- **Tiempo IA (ejec.)**: est. 0,04h · real 0,03h (estimado)
- **Supervisión**: est. 0,01h · real 0,01h (estimado)
- **Dependencias**: T-01
- **Archivos**: `agents/implementer.md`, `hooks/implementer-guardrail.sh` (nuevo), `.gitignore`

**Criterios de aceptación**
- [x] `bash -n hooks/implementer-guardrail.sh` OK. Con un PATH sin `python3` (solo bash/cat/mkdir/find): 1.ª invocación → `{"systemMessage": "⚠️ guardrails del implementer sin efecto: no hay python3 en PATH (alcance docs/roadmap/, rama y git NO se comprueban en esta sesión)."}` exit 0; 2.ª → sin stdout, exit 0 (marca `.claude/.guardrail-nopython`, en `.gitignore` junto a `.guardrail-off`).
- [x] Los 4 casos del T-01 a través del wrapper dan la misma salida (deny alcance · deny push · allow ledger · allow código), exit 0; también con `CLAUDE_PLUGIN_ROOT` y `HOME` sin definir (resuelve por `dirname $BASH_SOURCE`). La línea `command` del frontmatter, ejecutada con `sh -c` tal cual: con `CLAUDE_PLUGIN_ROOT` → deny; sin ella y con una copia en `$HOME/.claude/` → deny vía `find`; sin ninguna instalación → sin stdout, exit 0.
- [x] `agents/implementer.md`: cuerpo 78 → 77 líneas (la prosa de rama/alcance de §0 y §3 se sustituye por la referencia al hook); frontmatter YAML válido (`yaml.safe_load`: `name, description, model, tools, hooks, dependencies` — `skills:` retirado en `T-fix1`); `lint_plugin.py` → 0 errores · 3 avisos (los previos). `isolation: worktree` nativo NO se usa: ramifica desde la rama por defecto (no desde `feature/<slug>`) y lo limpia Claude Code, lo que choca con el opt-in `worktree` de `dev.json` (worktree único por iniciativa que integra el ritual de la Fase 6).

### T-03 — `scope-check.py` (pre-revisión) + tests + cableado

- **Descripción**: `agent-kits/shared/scope-check.py <carpeta-iniciativa> [--base <ref>] [--warn-only] [--json]`: ficheros cambiados (`git diff --name-only <base>...HEAD` + `git status --porcelain`); base = merge-base con `main`/`master` si existe, si no `--base` obligatorio con mensaje claro; lee los campos `Archivos` de TODAS las tareas (vía `parse_ledger` + regex de campo; globs, carpetas con `/`, «(nuevo)», listas por coma); clasifica en alcance / fuera / declarados sin tocar. El propio `tasks.md` y `docs/knowledge/**` siempre en alcance. Exit 0 sin fuera de alcance, 1 si hay (con `--warn-only` siempre 0). Cableado: `commands/dev-cycle.md` Fase 3 paso 2 (antes de las lentes; exit 1 → gap Important al implementer sin gastar revisores); DoD de `agents/implementer.md`; `skills/quick-implement/SKILL.md` si describe la revisión.
- **Estado**: completado
- **Tiempo humano**: est. 1,3h · real 1,1h (estimado)
- **Tiempo IA (ejec.)**: est. 0,07h · real 0,06h (estimado)
- **Supervisión**: est. 0,02h · real 0,02h (estimado)
- **Archivos**: `agent-kits/shared/scope-check.py` (nuevo), `agent-kits/shared/test_scope_check.py` (nuevo), `commands/dev-cycle.md`, `agents/implementer.md`, `skills/quick-implement/SKILL.md`

**Criterios de aceptación**
- [x] `pytest agent-kits/shared/test_scope_check.py` → `9 passed` (repo git temporal: fuera de alcance → exit 1 y `--warn-only` → 0; glob `tests/test_*.py`, carpeta `src/util/`, llaves `docs/{a,b}.md`, «(nuevo)»; frases y rutas absolutas `/tmp/…` del campo se ignoran; sin comitear + sin seguimiento cuentan; `tasks.md` propio y `docs/knowledge/**` en alcance pero `spec.md` de la misma carpeta fuera; sin `main`/`master` → exit 2 con mensaje `--base` y con `--base trunk` → 0; en rama principal base = HEAD; `master` como principal; ledger inexistente y fuera de git → exit 2).
- [x] Sobre ESTA iniciativa (tras T-01..T-03): `scope-check: 2026-09-02-deterministic-guardrails · base merge-base master…HEAD (4e94debb) · 8 fichero(s) cambiado(s) · 28 patrón(es) declarados en Archivos` · `✅ en alcance (8)` (`.gitignore`, los 4 scripts/tests shared, `agents/implementer.md`, el ledger, `hooks/implementer-guardrail.sh`) · `❌ fuera de alcance (0): —` · `ℹ️ declarados sin tocar (20)` (los de T-04/T-05 aún no empezadas) · exit 0.
- [x] `commands/dev-cycle.md` Fase 3 paso 2: puerta previa `scope-check.py` (exit 1 → gap Important al implementer sin lanzar lentes; exit 2 → `--base`; sin git → aviso) y la comprobación (2) de la lente A remite al check; DoD de `agents/implementer.md`: el check manual `git status / git diff --stat` se sustituye por `scope-check.py` exit 0; `skills/quick-implement/SKILL.md` punto 4 lo lista como puerta.

### T-04 — Linter + documentación + ADR

- **Descripción**: `scripts/lint_plugin.py` acepta `hooks`/`skills` en agentes; cada skill de `skills:` existe en `skills/` y está en `dependencies.skills`; los `command` de `hooks:` del frontmatter referencian ficheros existentes (reutiliza `lint_hooks`). Tests. Docs: `docs/CONVENTIONS.md` + EN (dos clases de hooks: informativos globales vs de guardia por agente; deny global prohibido; `skills:` nativo ⊆ `dependencies.skills`), `skills/plugin-dev/SKILL.md` (Paso 0 + Paso 2), `docs/FLOWS.md` + EN (scope-check antes de la revisión), `docs/agents/implementer.md` (guardrails), `commands/setup.md` paso 5 (`guardrails`, default activado), `agent-kits/shared/README.md` (+2 scripts), `CLAUDE.md`, `README.md`/`README.es.md`. ADR «deny solo con alcance de agente, nunca global» (`estado: propuesta`) + fila en `docs/knowledge/README.md`. NO se toca `CHANGELOG*.md`.
- **Estado**: completado
- **Tiempo humano**: est. 1,0h · real 1,0h (estimado)
- **Tiempo IA (ejec.)**: est. 0,04h · real 0,05h (estimado)
- **Supervisión**: est. 0,01h · real 0,01h (estimado)
- **Dependencias**: T-01, T-02, T-03
- **Archivos**: `scripts/lint_plugin.py`, `tests/test_lint_plugin.py`, `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md`, `skills/plugin-dev/SKILL.md`, `docs/FLOWS.md`, `docs/en/FLOWS.md`, `docs/agents/implementer.md`, `commands/setup.md`, `agent-kits/shared/README.md`, `CLAUDE.md`, `README.md`, `README.es.md`, `docs/knowledge/adr/ADR-007-deny-solo-con-alcance-de-agente.md` (nuevo), `docs/knowledge/README.md`, `docs/roadmap/README.md`

**Criterios de aceptación**
- [x] `test_lint_plugin: 14/14 OK` (casos 12 agente con `skills:` + `hooks:` válidos → 0 errores; 13 skill precargada inexistente → error y skill existente no declarada en `dependencies.skills` → error; 14 `command` de `hooks:` a `hooks/no-existe.sh` → error `[hooks]`). TDD: RED con el linter anterior (`git stash` de `scripts/lint_plugin.py`): `AssertionError` en el caso 13 (daba `0 errores`); GREEN tras implementar (`parse_frontmatter` recoge `skills` y `hook_commands`; `lint_hook_commands()` compartido con `lint_hooks()`).
- [x] `python3 scripts/lint_plugin.py` → `8 agentes · 0 errores · 3 avisos` (los previos de nombres genéricos); `test_mermaid_blocks: 30 diagrama(s) OK` (28 + los dos §6c nuevos, ES y EN).
- [x] Espejos EN en el mismo cambio: `CONVENTIONS` (regla 4 nota «campos nativos `skills:`/`hooks:`», regla 8 «dos clases de hooks; deny global prohibido», regla 9 fila `dev.json` + `guardrails`), `FLOWS` (§1 y §3 con el nodo `scope-check.py`; §6c nuevo «Guardrails deterministas del implementer»), `README`/`README.es` (fila «Guardrails deterministas»). Solo ES por convención: `CLAUDE.md` (filas Determinismo e implementer), `skills/plugin-dev/SKILL.md` (Paso 0 fila «hook de guardia» + Paso 2 opcionales nativos), `docs/agents/implementer.md` (sección «Guardrails deterministas» + nota de skills bajo demanda), `commands/setup.md` (paso 5 `guardrails`, default activado — solo ofrece desactivar), `agent-kits/shared/README.md` (+2 filas), `docs/roadmap/README.md` (fila). `docs/knowledge/adr/ADR-007-deny-solo-con-alcance-de-agente.md` con la plantilla (`estado: propuesta`; alternativas descartadas: deny global filtrando `agent_type`, `isolation: worktree`, exit 2) + fila en `docs/knowledge/README.md`. `CHANGELOG*.md` sin tocar. Ajuste tras la prueba con `scope-check.py` sobre esta iniciativa: los ficheros en alcance «de oficio» (`docs/knowledge/**`) ya no figuran como «declarados sin tocar».

### T-05 — Housekeeping: «Fase única» en la tabla de resumen de `ledger-lint.py`

- **Descripción**: la tabla de resumen solo reconocía filas `Fase\s+\d+`; «Fase única — …» disparaba el aviso falso «sin tabla Resumen de progreso (legacy)». Admite `Fase\s+(\d+|única)` (y `norm_fase` la casa con la sección `## Fase única — …`); test; comprobación sobre los 16 ledgers de que la única diferencia frente a `git show 4e94deb:agent-kits/shared/ledger-lint.py` es la desaparición de ese aviso.
- **Estado**: completado
- **Tiempo humano**: est. 0,5h · real 0,3h (estimado)
- **Tiempo IA (ejec.)**: est. 0,02h · real 0,02h (estimado)
- **Supervisión**: est. 0,00h · real 0,00h (estimado)
- **Archivos**: `agent-kits/shared/ledger-lint.py`, `tests/test_ledger_lint.py`

**Criterios de aceptación**
- [x] `tests/test_ledger_lint.py` caso 11: ledger con «Fase única — Todo» → exit 0 sin el aviso «Resumen de progreso»; misma fila descuadrada (2/3 vs 3 tareas) → exit 1 `descuadrado`. `test_ledger_lint: 11/11 OK`. Cambio: regex de filas `Fase\s+(?:\d+|única|unica)\b` (case-insensitive) y `norm_fase` → clave `fase-unica`.
- [x] Salida completa de `ledger-lint.py` sobre los 17 ledgers de `docs/roadmap/*/tasks.md` (16 previos + este) frente a `git show 4e94deb:agent-kits/shared/ledger-lint.py`: `diff` muestra ÚNICAMENTE la desaparición de la línea `⚠️ sin tabla «Resumen de progreso» reconocible (legacy)` (y el contador `1 avisos` → `0 avisos`) en los 3 ledgers con «Fase única»: `2026-08-20-knowledge-split`, `2026-09-02-live-visibility` y `2026-09-02-deterministic-guardrails`. Los otros 14 son idénticos; exit codes idénticos en los 17.

---

## Verificación final (DoD del implementer, rama `feature/deterministic-guardrails`)

- `python3 -m pytest -q tests agent-kits/shared` → **133 passed** (104 previos + 20 `test_guardrail_check` + 9 `test_scope_check`); tras `T-fix1`: **136 passed**. 9 suites-script de CI verdes (`confluence_scope 25/25 · coverage-check OK · dashboard OK · ledger_lint 11/11 · lint_plugin 15/15 · mermaid 30 · qa_gate 13/13 · readme_badges 6 · worklog 13`).
- `python3 scripts/lint_plugin.py` → `8 agentes · 0 errores · 3 avisos`. `bash -n hooks/implementer-guardrail.sh` OK. `ledger-lint.py` de este fichero → `0 incoherencias · 0 avisos`, exit 0.
- `scope-check.py docs/roadmap/2026-09-02-deterministic-guardrails` → `28 fichero(s) cambiado(s) · 28 patrón(es)` · `✅ en alcance (28)` · `❌ fuera de alcance (0)` · exit 0.
- Commits lógicos por tarea: `T-01` (`ab5d88d`), `T-02` (`efa5162`), `T-03` (`05bb438`), `T-05` (`491f0b8`), `T-04` (`72da43d`), `T-fix1` (`063d3da`, revisión intento 1), `T-fix2` (intento 2). Sin push.

## Revisión de dos lentes — intento 1: 4 gaps corregidos (2 Important, 2 Minor), 0 Critical, 2 aceptados como deuda (commit `T-fix1`)

Cada gap se reprodujo antes de corregir (todos reales; ninguno rebatido):

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | `skills:` precargaba `jira-sync` + `confluence-publish` (≈57 KB ≈ 15k tokens) en CADA arranque del implementer para funciones opt-in — rompe el token-diet | T-02, T-04 | `skills:` retirado del frontmatter (comentario explica por qué); soporte del campo intacto en linter/CONVENTIONS/plugin-dev con la regla «solo skills necesarias en TODAS las ejecuciones; las opt-in bajo demanda»; el linter AVISA si la precarga declarada supera 16 KB (`PRELOAD_WARN_BYTES`); nota en `docs/agents/implementer.md` | `test_lint_plugin` caso 15 (`precarga 17 KB` → aviso, no error) → `15/15 OK`; `lint_plugin` sigue en 0 errores · 3 avisos |
| 2 | Important | Evasiones de `check_git`: (a) `git push origin +main` (refspec `+` = force) allow; (b) `sh -c "git push --force"` / `bash -c '…'` allow; (c) `rm -rf .` / `rm -rf ./` allow (desde la raíz destruye `.git`) | T-01 | (a) token `+<ref>` tras `push` → deny; (b) `check_git` recursivo (≤3 niveles) sobre tokens con espacios que contengan `git`/`rm`; (c) `posixpath.normpath` del objetivo y `.`/`*` en la lista negra (`./dist`, `.cache` siguen permitidos) | `test_fix1_evasiones_git_refspec_mas_shell_c_y_rm_punto`; vía wrapper: los tres → JSON `deny`, exit 0 |
| 3 | Minor | `normalize_path`: `docs/roadmap/x/../../src/a.py` daba deny (falso positivo) | T-01 | `posixpath.normpath` tras `\`→`/` y relativización (`""`/`.` → sin ruta) | `test_fix1_normpath_resuelve_dotdot_sin_falsos_positivos` (`→ docs/src/a.py`, allow; `src/../docs/roadmap/x/spec.md` sigue deny); CLI: sin stdout / deny |
| 4 | Minor | `scope-check.py` `casa()`: `docs/**/*.md` no casaba `docs/knowledge_x.md` (fnmatch trata `**` como `*`) | T-03 | Reutiliza `glob_to_regex` de `skills/confluence-publish/scripts/confluence-scope.py` (`**/` = cero o más directorios, `*` = un nivel) vía importlib; copia local equivalente si la skill no está instalada | `test_fix1_doble_asterisco_cero_o_mas_directorios_y_asterisco_un_nivel` (`notes/x.md` y `notes/a/b.md` casan `notes/**/*.md`; `agents/sub/y.md` NO casa `agents/*.md`); repo temporal real: `✅ en alcance (2)`, exit 0 |

**Intento 2: 1 regresión corregida (commit `T-fix2`), 0 gaps nuevos.** La recursión de 2b entraba en CUALQUIER token con espacios que contuviera `git`/`rm` → `git commit -m "rm -rf . in message"` daba deny (el propio mensaje de `T-fix1` lo habría disparado). Acotada a lo que una shell ejecuta: argumento de `-c` de `sh|bash|zsh|dash|ksh` (incl. clusters `-lc`) y argumentos de `eval`; además `_segmentos` ahora trocea por `;`/`&&`/`||`/`|` **respetando comillas** (`shlex` con `punctuation_chars`), porque el troceo previo partía `sh -c 'cd x && rm -rf .'` por dentro de la cadena y la dejaba pasar. Tests (mismo `test_fix1_evasiones…`): `git commit -m "rm -rf . x"` allow · `echo "git push --force"` allow · `bash -c "git push -f"` deny · `sh -c 'cd x && rm -rf .'` deny · `bash -lc`/`zsh -c` deny. Vía wrapper: los 4 casos con la salida esperada, más `npm test && git push --force` y `git status; git push -f` → deny. `pytest` → **136 passed**; 9 suites verdes; `lint_plugin` 0 errores; `bash -n` OK.

**Verificado OK por la revisión (sin cambios):** `..` hacia dentro, `./`, MultiEdit `edits[]`, absolutas bajo el proyecto, `src/docs/roadmap-view.tsx` y `mydocs/roadmap/` permitidos, `push -f`/`--force-with-lease`/encadenado, `rm -rf .git|$HOME`, `rm -rf node_modules` permitido, `branch -d`, `checkout -b`, `checkout main` desde feature, detached HEAD, rama `master`, `dev.json` parcial/corrupto, stdin vacío/no-JSON, sin git en PATH, ~40 ms por invocación; `scope-check` exit 1/0/2 y mensaje sin main/master; `lint_plugin` con `skills: nope`, `hooks: "string"` y command inexistente (sin traceback).

**Aceptados como deuda:** mayúsculas en rutas (`Docs/Roadmap`) no casan (los patrones son case-sensitive, como git en Linux) — **saldada en 2026-09-02-debt-cleanup (T-02a)**; `docs/roadmap/README.md`/`CALIBRATION.md`/`DRIFT.md` bloqueados para el implementer por diseño (los toca el orquestador/comandos) — **saldada en 2026-09-02-debt-cleanup (T-02b: `README.md` permitido; `CALIBRATION`/`DRIFT`/`BACKLOG` siguen deny, documentados como diseño)**.

Tras la corrección: `pytest -q tests agent-kits/shared` → **136 passed** (133 + 3 nuevos); 9 suites-script verdes; `lint_plugin` → 0 errores · 3 avisos; `bash -n` OK; `scope-check.py` de esta iniciativa → 28 en alcance, 0 fuera, exit 0.

## Dudas y decisiones para el orquestador

- **Doc oficial vs brief:** (1) `${CLAUDE_PLUGIN_ROOT}` no está documentado en los `command` del frontmatter de sub-agents (solo en `hooks.md` como variable del proceso) → la línea del hook lleva fallback `find` + `exit 0`; probado con y sin la variable. (2) La doc confirma `skills:` (precarga de contenido completo); el linter y las convenciones lo soportan, pero el implementer NO lo usa (revisión intento 1: ≈15k tokens por arranque para skills opt-in) — regla documentada: solo skills necesarias en TODAS las ejecuciones; el linter avisa con >16 KB de precarga. (3) `isolation: worktree` descartado (ADR-007 alternativas). (4) Se elige JSON `deny` + exit 0 en vez de exit 2 (razón estructurada; error interno ≠ bloqueo).
- **Efecto sobre este mismo trabajo:** el hook no estaba activo en esta sesión (el implementer corrió como agente sin el frontmatter nuevo cargado), pero las reglas se cumplieron a mano: rama `feature/deterministic-guardrails` creada antes de tocar código; en `docs/roadmap/` solo `tasks.md` propio y `README.md` (índice — lo toca el cierre, T-04, como en live-visibility; con el hook activo esa edición del índice la tendría que hacer el orquestador, no el implementer).
- **Alcance del deny en `docs/roadmap/README.md`, `CALIBRATION.md`, `DRIFT.md`:** quedan bloqueados para el implementer (los escriben comandos/orquestador). Si se prefiere permitir el índice, es una línea en `es_ledger()` + test. — **saldada en 2026-09-02-debt-cleanup (T-02b)**
- **Tests de shell:** no hay suite de shell en el repo; la evidencia del wrapper es la simulación de stdin anotada en T-02 (reproducible) + `bash -n` + linter. — **saldada en 2026-09-02-debt-cleanup (T-06)** **CHANGELOG** no tocado (orquestador). Tabla de revisión de dos lentes: pendiente de añadir al final cuando llegue.
