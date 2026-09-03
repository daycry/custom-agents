# Contratos oficiales de Claude Code que usa este plugin — verificados con fecha

Léelo desde `plugin-dev` **antes de hacer WebFetch**: si el contrato que necesitas está aquí y tiene
menos de 90 días, úsalo; si dudas o han pasado más de 90 días, re-verifica (sección final) y actualiza
la fecha de la fila. Fuente de todas las filas: `https://code.claude.com/docs/en/<página>.md`.
**Última verificación completa: 2026-09-03.**

| Contrato | Página | Verificado |
|---|---|---|
| Hooks (eventos, stdin, salida JSON, exit codes, placeholders) | `hooks.md` | 2026-09-03 |
| `SessionEnd` (stdin, `reason`, no bloquea, presupuesto 1,5 s) y hooks `prompt`/`agent` (solo decisión `ok/reason`) | `hooks.md` + `hooks-guide.md` | 2026-09-03 (memory-health) |
| Frontmatter de subagente (`model`, `effort`, `tools`, …) y prioridad del modelo | `sub-agents.md` | 2026-09-03 |
| Frontmatter de skill y relación commands ↔ skills | `skills.md` | 2026-09-03 |
| CLI headless (`-p`, `--bare`, `--output-format`, `--allowedTools`…) | `headless.md` | 2026-09-03 |
| `statusLine` en `settings.json` | `statusline.md` | 2026-09-03 |
| `plugin.json` / marketplace / `claude plugin` CLI / `${CLAUDE_PLUGIN_ROOT}` | `plugins-reference.md` | 2026-09-03 |

## 1. Hooks (`hooks.md`)

**Eventos** (lista oficial hoy): `SessionStart`, `Setup`, `UserPromptSubmit`, `UserPromptExpansion`, `PreToolUse`, `PermissionRequest`, `PermissionDenied`, `PostToolUse`, `PostToolUseFailure`, `PostToolBatch`, `Notification`, `MessageDisplay`, `SubagentStart`, `SubagentStop`, `TaskCreated`, `TaskCompleted`, `Stop`, `StopFailure`, `TeammateIdle`, `InstructionsLoaded`, `ConfigChange`, `CwdChanged`, `DirectoryAdded`, `FileChanged`, `WorktreeCreate`, `WorktreeRemove`, `PreCompact`, `PostCompact`, `PreModelSwitch`, `PostModelSwitch`, `Elicitation`, `ElicitationResult`, `SessionEnd`. **Usamos** `PostToolUse`, `SubagentStop`, `SessionStart`, `SessionEnd` (informativos, `hooks/hooks.json`) y `PreToolUse` (guardia, solo en el frontmatter de `implementer`/`architect`, ADR-007).

**Stdin común a todo evento:** `session_id`, `prompt_id`, `transcript_path`, `cwd`, `permission_mode`, `effort` (`{level: low|medium|high|xhigh|max}`), `hook_event_name`, `agent_id`/`agent_type` (subagentes). **Por evento:** `SessionStart` → `source` ∈ `startup|resume|clear|compact|fork` (son también los **matchers**; usamos `startup|resume|compact`); `PreToolUse` → `tool_name`, `tool_input`, `tool_use_id`; `PostToolUse` → + `tool_result`; `SubagentStop` → `agent_id`, `agent_type`, `last_assistant_message`.

**Salida JSON (stdout, exit 0):** `systemMessage` (la mayoría de eventos), `hookSpecificOutput.hookEventName`, `hookSpecificOutput.additionalContext` (`SessionStart`, `UserPromptSubmit`, eventos de tool), `hookSpecificOutput.permissionDecision` ∈ `allow|deny|ask` + `permissionDecisionReason` (`PreToolUse`, `PermissionRequest`, `PermissionDenied`), `updatedInput` (`PreToolUse`), `continue`/`stopReason` (`Stop`, `SubagentStop`), `suppressOutput`. **Exit codes:** `0` → parsea JSON si stdout empieza por `{`; texto plano en `SessionStart`/`UserPromptSubmit` se añade como contexto; `2` → **bloquea** (no lo anula un JSON `allow`); otro → error no bloqueante. **Nuestro principio:** informativos siempre exit 0; el deny va en JSON con razón.

**`SessionEnd` (memory-health, 2026-09-03 — `hooks.md` §SessionEnd + `hooks-guide.md` §Limitations):** stdin `session_id`, `transcript_path`, `cwd`, `hook_event_name`, **`reason`** ∈ `clear|resume|logout|prompt_input_exit|other` (también es el **matcher**; sin matcher dispara en todos). «SessionEnd fires when a session terminates. Claude Code removes the session's worktrees and working directories, then runs your hooks before cleaning up the database.» **No puede bloquear**: la tabla de exit codes dice «Can block? No — Output and exit code are ignored, except `terminalSequence`» (la sección del evento matiza que un exit 2 «stops cleanup but leaves the session in place to resume» — contradicción menor dentro de la propia doc; nuestro hook siempre exit 0 y no emite nada). **Presupuesto:** «SessionEnd hooks of any type share a 1.5-second budget. If your settings set a longer per-hook `timeout`, Claude Code raises the budget to match, up to 60 seconds» → `hooks.json` declara `timeout: 20` en `session-journal.sh`. **Nota:** el ejemplo de stdin de la doc no muestra `permission_mode`/`effort` para este evento. Usamos `SessionEnd` SOLO para escribir a disco (`journal.py write`); reinyectar contexto es cosa de `SessionStart`.

**Hooks `prompt` y `agent` (memory-health, 2026-09-03 — `hooks-guide.md` §Prompt-based/Agent-based hooks, leída completa):** `type: "prompt"` envía el prompt + el JSON del evento (`$ARGUMENTS`) a un modelo (Haiku por defecto, `model` opcional) y «the model's only job is to return its decision as JSON: `"ok": true|false` + `reason`» (+ `impossible` en `Stop`/`SubagentStop`; `continueOnBlock` en `PreToolUse`/`PostToolUse`); timeout 30 s. `type: "agent"` (**experimental**) lanza un subagente con herramientas de lectura (Read/Grep/Glob) para verificar y devuelve el mismo `ok/reason`; 60 s y hasta 50 turnos. La guía solo describe el efecto de `ok: false` en `Stop`, `SubagentStop`, `PreToolUse`, `PostToolUse`, `PostToolBatch`, `UserPromptSubmit` y `UserPromptExpansion`. **No hay contrato** para que un hook `prompt`/`agent` devuelva texto que se escriba a disco o se inyecte en otro evento, y en `SessionEnd` la salida de cualquier hook se ignora → **el «resumen por IA» del journal NO se implementa** (ADR-010); `journal.py write --enrich` queda para uso manual. Sección `#prompt-based-hooks` de la referencia `hooks.md`: la lectura de hoy con WebFetch llegó **truncada** (la página es larga) — la lista exacta de eventos que admiten `prompt` en la referencia queda **«a re-verificar»**; la decisión no depende de ella (la salida en `SessionEnd` se ignora en cualquier caso).

**Placeholders / entorno:** `${CLAUDE_PROJECT_DIR}`, `${CLAUDE_PLUGIN_ROOT}` (cambia al actualizar el plugin), `${CLAUDE_PLUGIN_DATA}` (persistente); exportados también como variables de entorno al proceso del hook (+ `CLAUDE_EFFORT`). En shell-form, entre comillas dobles. **Timeouts** por defecto: 600 s (`command`/`http`/`mcp_tool`; 30 s en `UserPromptSubmit`/`PreModelSwitch`/`PostModelSwitch`, 10 s en `MessageDisplay`), 30 s `prompt`, 60 s `agent`; `SessionEnd` comparte 1,5 s entre todos sus hooks (sube hasta el `timeout` declarado, máx. 60 s).

**Tope de caracteres (10.000):** este repo lo cita desde 2026-09-02 (`CONVENTIONS` regla 8, `skill-index.py` ≤ 3.500 para caber). **En la lectura de hoy de `hooks.md` NO se localizó el número** → marcado **«a re-verificar»**: hasta confirmarlo, mantén el límite propio (≤ 3.500 + contexto de retoma ≤ 15 líneas) como presupuesto conservador.

## 2. Subagentes (`sub-agents.md`)

| Campo | Valores oficiales | ¿Lo usamos? | Por qué |
|---|---|---|---|
| `name`, `description` | obligatorios; description con disparadores | **Sí** | Base de la activación (evals) |
| `model` | `sonnet` · `opus` · `haiku` · `fable` · `inherit` · id completo `claude-…` | **Sí** (`haiku|sonnet|opus|inherit`; el linter no admite `fable` ni ids en el frontmatter — `dev.json` `modelos` sí admite ids) | Tiering de CONVENTIONS |
| `effort` | `low` · `medium` · `high` · `xhigh` · `max` («overrides the session effort level»; disponibilidad según modelo) | **Sí** (obligatorio por el linter desde parity-core) | Tiering en dos capas |
| `tools` | nombres, `Agent`, `Agent(tipo)`, `mcp__<server>` | **Sí**, mínimos | `reviewer` sin Write/Edit por construcción |
| `disallowedTools` | nombres, `mcp__*` | No | Preferimos lista blanca `tools` |
| `skills` | lista (precarga el contenido COMPLETO) | Solo si la skill hace falta en TODAS las ejecuciones (token-diet) | ≈15k tokens por precarga opt-in |
| `hooks` | `PreToolUse`/`PostToolUse`/`Stop` con alcance del agente | **Sí**, solo guardia del `implementer` | ADR-007 |
| `isolation` | `worktree` | **No** | Choca con el opt-in `worktree` de `dev.json` |
| `memory` | `user` · `project` · `local` | **No** | La memoria del proyecto es `docs/knowledge/` (versionada, revisable) |
| `permissionMode`, `maxTurns`, `background`, `color`, `mcpServers`, `initialPrompt` | ver doc | No | Sin necesidad hoy |

**Prioridad del modelo (v2.1.251+):** (1) parámetro `model` por invocación del Agent tool → (2) frontmatter (`inherit` = sesión) → (3) `CLAUDE_CODE_SUBAGENT_MODEL` → (4) sesión. Antes de v2.1.251 la variable de entorno mandaba sobre todo. `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` (v2.1.257+) fuerza la variable para todos. Valores fuera del `availableModels` de la organización se sustituyen. **El Agent tool NO documenta parámetro `effort`** → `model-tier.py` lo declara informativo. El thinking del subagente hereda el de la sesión (v2.1.198+), sin ajuste por agente.

## 3. Skills (`skills.md`)

- **Commands = skills:** «Custom commands have been merged into skills» — `.claude/commands/x.md` y `.claude/skills/x/SKILL.md` crean el mismo `/x`; los ficheros de `commands/` aceptan el mismo frontmatter salvo `name` y `paths`. Por eso el índice de piezas dice «los comandos se invocan por `/` o por descripción».
- **Frontmatter:** `name`, `description` (recomendada; **el listado trunca description + `when_to_use` a 1.536 caracteres** → nuestro aviso a 1.200), `argument-hint`, `disable-model-invocation` (solo el usuario la invoca; su description sale del contexto), `user-invocable: false` (solo Claude), `allowed-tools`/`disallowed-tools` (por turno), `model` y `effort` (mismos valores que subagentes; con `context: fork` fijan el modelo del subagente), `context: fork` + `agent`, `paths` (globs de activación), `metadata`, `compatibility`. No usamos `disable-model-invocation` (queremos auto-activación) ni `paths`.
- **Sustituciones en el cuerpo:** `$ARGUMENTS`, `$ARGUMENTS[N]`/`$N`, `${CLAUDE_SKILL_DIR}`, `${CLAUDE_PROJECT_DIR}`, `${CLAUDE_EFFORT}` y, en skills de plugin, `${CLAUDE_PLUGIN_ROOT}`/`${CLAUDE_PLUGIN_DATA}`. El `SKILL.md` invocado entra **completo** y persiste en el contexto → regla «skills cortas» (ADR-008).

## 4. CLI headless (`headless.md`)

`claude -p "<prompt>"` (= `--print`); `--output-format text|json|stream-json` (`stream-json` exige `--verbose`; `json` trae `total_cost_usd`); `--bare` salta hooks, skills, commands, subagentes, plugins, MCP, memoria y CLAUDE.md del host, **exige `ANTHROPIC_API_KEY`** (no usa el login OAuth) y **sí carga `--plugin-dir <ruta>`** (tabla «To load → Use»); `--allowedTools "Bash(python3:*),…"` (sintaxis de reglas de permisos; en `-p` nadie aprueba y `acceptEdits` no cubre Bash); `--max-turns N`; `--permission-mode auto|dontAsk|acceptEdits|…`; `--agents <json>`; `--continue`/`--resume`. `system/init` lista `plugins` y `plugin_errors` (gate de CI). Las `/skill` del usuario funcionan dentro del prompt de `-p`. Lo usa `evals/run.py` y `headless.yml`.

## 5. Status line (`statusline.md`)

`settings.json` → `"statusLine": {"type": "command", "command": "<script o comando inline>", "padding": 0}`; `~` documentado en `command`; **`${CLAUDE_PLUGIN_ROOT}` no aparece** para `statusLine`, y el `settings` de `plugin.json` **solo admite `agent` y `subagentStatusLine`** (plugins-reference) → por eso `/setup` 5-bis escribe la ruta absoluta del script. Stdin: `model.display_name`, `cost.total_cost_usd`, `context_window.used_percentage` (puede ser `null` al inicio), `workspace`, `rate_limits` (opcional).

## 6. Plugin y marketplace (`plugins-reference.md`)

`plugin.json`: `name` (obligatorio), `displayName`, `version`, `description`, `author {name,email,url}`, `homepage`, `repository`, `license`, `keywords`, `metadata`, `defaultEnabled`, rutas `skills|commands|agents|hooks|mcpServers|outputStyles|lspServers`, `userConfig`, `dependencies`, `settings` (solo `agent`, `subagentStatusLine`). Marketplace: `name`, `source`, `description`, `version`, `strict`, `tags`, `category`. CLI: `claude plugin init|install|uninstall|prune|enable|disable|update|list|details|validate` (**no existe `plugin eval`**: `evals/` es formato propio).

**`${CLAUDE_PLUGIN_ROOT}` — contradicción registrada (2026-09-03):** la tabla oficial dice que se sustituye en «Skill and agent content — *anywhere the placeholder appears*» (además de hooks, MCP y LSP). La regla 5 de `docs/CONVENTIONS.md` asume que **no** se expande en markdown y por eso usa `find` sobre `$PWD/.claude` y `$HOME/.claude`. **Decisión:** se mantiene `find` porque cubre también la instalación como `.claude/` copiado (sin plugin, sin `CLAUDE_PLUGIN_ROOT`) y el paquete portable; `${CLAUDE_PLUGIN_ROOT}` queda como **candidato a simplificación** (primer candidato con fallback `find`, como ya hace el hook del `implementer`). Re-verificar en la próxima pasada y abrir iniciativa si se confirma.

## Cómo re-verificar (≤ 15 min)

1. Para cada fila de la tabla inicial: `WebFetch https://code.claude.com/docs/en/<página>.md` con la pregunta concreta («valores de `effort`», «¿existe parámetro effort en el Agent tool?», «tope de caracteres de `additionalContext`»). El índice de páginas está en `https://code.claude.com/docs/llms.txt`.
2. Compara con la fila; si cambia, actualiza la fila **y** la pieza del repo que la usa (linter `VALID_*`, `model-tier.py`, `evals/run.py`, `/setup`), en el mismo cambio.
3. Pon la fecha nueva en la fila y en «Última verificación completa».
4. Si un contrato marcado «a re-verificar» se confirma, quita la marca; si se refuta, abre iniciativa (vía rápida) con la corrección.
