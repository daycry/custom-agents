#!/usr/bin/env bash
# Hook UserPromptSubmit (sin matcher: el evento no lo admite): acumula el TURNO DEL USUARIO en un log crudo
# NO versionado, `.claude/session-prompts-<session_id>.log` (una línea JSON por turno; `*.log` está en el
# .gitignore), para que el hook SessionEnd (`session-journal.sh` → `journal.py write`) extraiga de ahí las
# `decisiones` y `pendientes` de la entrada del journal al cerrar la sesión (memory-retrieval T-11/T-12).
# El FORMATO del log y sus topes viven en `agent-kits/shared/journal.py capture` (fuente única: quien lo
# escribe y quien lo lee son el mismo módulo): tope por turno CAPTURA_MAX_CHARS, tope por fichero
# LOG_MAX_BYTES (se conservan los últimos turnos) y purga de logs con más de LOG_RETENCION_DIAS días.
# Opt-out por turno: la etiqueta `<private>` en cualquier parte del turno → el log NO se toca (ni se crea,
# ni mtime, ni tamaño) y ese turno tampoco sale de la transcripción al cerrar. Opt-out por proyecto:
# `.claude/dev.json` → {"sesion": {"journal": false}} (sin journal no hay para qué capturar) o
# {"sesion": {"captura": false}}. Privacidad (revisión F4, Lente C): los secretos evidentes se REDACTAN antes
# de escribir (`journal.py redactar`), el log nace 0600 (POSIX) y `capture` siembra `.claude/.gitignore` con
# `session-prompts-*.log` para que el log no entre en git en un proyecto consumidor. Solo escribe en proyectos
# con RASTRO del plugin (mismo criterio que el journal, T-fix1): en un repo ajeno no siembra ni `.claude/`.
# NO se registra ningún PostToolUse: solo el turno del usuario (decisión del usuario: lo demás es ruido y coste).
# INFORMA (escribe a disco), no decide: siempre exit 0 y SIN stdout — en UserPromptSubmit el stdout en texto
# plano se INYECTA como contexto de Claude y un exit 2 BLOQUEA Y BORRA el prompt del usuario.
#
# Contrato oficial (code.claude.com/docs/en/hooks-guide.md + hooks.md, verificado 2026-09-08):
#   stdin  → { hook_event_name: "UserPromptSubmit", session_id, cwd, transcript_path, prompt: "<texto del turno>" }
#            «Every event includes common fields like `session_id` […] `UserPromptSubmit` hooks get the `prompt` text»
#   stdout → texto plano, o JSON `hookSpecificOutput.additionalContext`, se AÑADE al contexto → aquí NADA.
#   exit   → 2 = «Blocks prompt processing and erases the prompt» → aquí SIEMPRE 0.
#   tiempo → default 30 s en este evento (bajado desde los 600 s generales); hooks.json declara `timeout: 5`.
#   matcher → «no matcher support · always fires on every occurrence».
#
# Prueba manual:
#   echo '{"hook_event_name":"UserPromptSubmit","session_id":"s1","prompt":"decidimos usar FTS5"}' | bash hooks/user-prompt-capture.sh
set -u

INPUT="$(cat 2>/dev/null || true)"
[ -n "$INPUT" ] || exit 0

command -v python3 >/dev/null 2>&1 || exit 0

# journal.py: CLAUDE_PLUGIN_ROOT (lo exporta Claude Code) → el propio repo del plugin (sin la variable, dentro
# de este repo, el `find` caería a una copia INSTALADA anterior a la rama en curso) → find (regla 5 de CONVENTIONS).
JOURNAL="${CLAUDE_PLUGIN_ROOT:-}/agent-kits/shared/journal.py"
[ -f "$JOURNAL" ] || JOURNAL="${CLAUDE_PROJECT_DIR:-$PWD}/agent-kits/shared/journal.py"
if [ ! -f "$JOURNAL" ]; then
  JOURNAL="$(find "${CLAUDE_PROJECT_DIR:-$PWD}/.claude" "${CLAUDE_PROJECT_DIR:-$PWD}/.codex" "${CLAUDE_PROJECT_DIR:-$PWD}/.opencode" "${HOME:-}/.claude" "${HOME:-}/.codex" "${HOME:-}/.config/opencode" -type f -path '*agent-kits/shared/journal.py' 2>/dev/null | head -1)"
fi
[ -n "$JOURNAL" ] && [ -f "$JOURNAL" ] || exit 0

# La raíz la resuelve `capture` (CLAUDE_PROJECT_DIR > `cwd` del payload > .); aquí solo se pasa si la tenemos.
args=(capture)
[ -n "${CLAUDE_PROJECT_DIR:-}" ] && args+=(--root "$CLAUDE_PROJECT_DIR")

printf '%s' "$INPUT" | PYTHONIOENCODING=utf-8:replace python3 "$JOURNAL" "${args[@]}" >/dev/null 2>&1 || true

exit 0
