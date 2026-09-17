#!/usr/bin/env bash
# Hook SessionEnd (sin matcher: también `clear`, porque un /clear cierra una unidad de trabajo):
# CAPTURA ULTRALIGERA y ATÓMICA (session-end-durable-capture T-03, spec CA-01): deja un *envelope*
# en la outbox local (`.claude/journal/outbox/`, vía `agent-kits/shared/journal.py capture-end`) y
# NADA MÁS — no abre el transcript, no ejecuta git, no llama a IA, no usa red. La MATERIALIZACIÓN
# (borrador determinista, git, log de prompts, resumen IA opt-in) corre después, de forma
# recuperable: `agent-kits/shared/journal.py replay`, invocado por `session-context.sh` en
# SessionStart con presupuesto (T-05, iniciativa aparte) o a demanda. Desactivable con
# `.claude/dev.json` → {"sesion": {"journal": false}} (lo decide `journal.py capture-end`). Solo
# escribe en proyectos con RASTRO del plugin (`docs/roadmap/`, `docs/knowledge/` o
# `.claude/dev.json`). INFORMA (escribe a disco), no decide: siempre exit 0.
#
# Contrato oficial (code.claude.com/docs/en/hooks.md + hooks-guide.md, verificado 2026-09-03):
#   stdin  → { hook_event_name: "SessionEnd", session_id, transcript_path, cwd,
#              reason: clear|resume|logout|prompt_input_exit|other }
#   stdout → se IGNORA («Output and exit code are ignored, except terminalSequence»): SessionEnd
#            no puede bloquear ni inyectar contexto; por eso el hook solo escribe a disco.
#   tiempo → todos los hooks de SessionEnd comparten un presupuesto de 1,5 s que sube hasta el
#            `timeout` por hook (máx. 60 s) → hooks.json declara `timeout: 5` (era 45: el trabajo
#            pesado —git, IA, log de prompts— ya no corre aquí, corre en `replay`) y pasa a EXEC
#            FORM (`command: bash`, `args: [...]`, CA-09) para que el runtime no tenga que
#            tokenizar una línea de shell en el camino más corto posible.
#
# Prueba manual:
#   echo '{"hook_event_name":"SessionEnd","session_id":"s1","reason":"other","cwd":"'"$PWD"'"}' | bash hooks/session-journal.sh
set -u

INPUT="$(cat 2>/dev/null || true)"

command -v python3 >/dev/null 2>&1 || exit 0

# journal.py: CLAUDE_PLUGIN_ROOT → el propio repo del plugin (sin la variable, dentro de este repo, el `find`
# caería a una copia INSTALADA anterior a la rama en curso — revisión intento 1, gap 9) → find (regla 5).
JOURNAL="${CLAUDE_PLUGIN_ROOT:-}/agent-kits/shared/journal.py"
[ -f "$JOURNAL" ] || JOURNAL="${CLAUDE_PROJECT_DIR:-$PWD}/agent-kits/shared/journal.py"
if [ ! -f "$JOURNAL" ]; then
  JOURNAL="$(find "${CLAUDE_PROJECT_DIR:-$PWD}/.claude" "${CLAUDE_PROJECT_DIR:-$PWD}/.codex" "${CLAUDE_PROJECT_DIR:-$PWD}/.opencode" "${HOME:-}/.claude" "${HOME:-}/.codex" "${HOME:-}/.config/opencode" -type f -path '*agent-kits/shared/journal.py' 2>/dev/null | head -1)"
fi
[ -n "$JOURNAL" ] && [ -f "$JOURNAL" ] || exit 0

ROOT="${CLAUDE_PROJECT_DIR:-$PWD}"
[ -d "$ROOT" ] || exit 0

# El payload entero viaja tal cual a `capture-end` (lee stdin: session_id/reason/cwd/transcript_path);
# nada de lo que decida (session_id ausente, opt-out, sin rastro del plugin) se resuelve aquí.
printf '%s' "$INPUT" | python3 "$JOURNAL" capture-end --root "$ROOT" >/dev/null 2>&1 || true

exit 0
