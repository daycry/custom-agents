#!/usr/bin/env bash
# Hook SessionStart (matcher `startup|resume|compact`): inyecta como contexto de sesión
# el bloque corto de `progress-report.py session` — iniciativas en progreso, tareas
# en curso, marcadores abiertos del usage-meter y la línea de retoma del ledger
# canónico. Sobrevive a la compactación (matcher `compact`) y al retomar (`resume`).
# Si no hay nada activo, NO emite nada (cero coste de contexto). Siempre exit 0.
#
# Contrato oficial (code.claude.com/docs/en/hooks, verificado 2026-09-02):
#   stdin  → { hook_event_name: "SessionStart", source: startup|resume|clear|compact|fork, cwd, … }
#   stdout → {"hookSpecificOutput": {"hookEventName": "SessionStart",
#                                    "additionalContext": "<texto>"}}
#            `additionalContext` DEBE ir anidado en hookSpecificOutput (en primer nivel
#            se ignora en silencio); `hookEventName` es obligatorio.
#
# Prueba manual:
#   echo '{"hook_event_name":"SessionStart","source":"resume"}' | bash hooks/session-context.sh
set -u

INPUT="$(cat 2>/dev/null || true)"

command -v python3 >/dev/null 2>&1 || exit 0

REPORT="${CLAUDE_PLUGIN_ROOT:-}/agent-kits/shared/progress-report.py"
if [ ! -f "$REPORT" ]; then
  REPORT="$(find "${CLAUDE_PROJECT_DIR:-$PWD}/.claude" "${HOME:-}/.claude" -type f -path '*agent-kits/shared/progress-report.py' 2>/dev/null | head -1)"
fi
[ -n "$REPORT" ] && [ -f "$REPORT" ] || exit 0

# Raíz del proyecto: CLAUDE_PROJECT_DIR (lo exporta Claude Code) > cwd del payload > $PWD.
ROOT="${CLAUDE_PROJECT_DIR:-}"
if [ -z "$ROOT" ] && command -v jq >/dev/null 2>&1; then
  ROOT="$(printf '%s' "$INPUT" | jq -r '.cwd // empty' 2>/dev/null)"
fi
ROOT="${ROOT:-$PWD}"
[ -d "$ROOT/docs/roadmap" ] || exit 0

out="$(python3 "$REPORT" session --root "$ROOT" 2>/dev/null || true)"
[ -n "$out" ] || exit 0
# Línea neutra (nada activo) → no gastar contexto.
case "$out" in
  "roadmap: sin iniciativas en progreso") exit 0 ;;
esac

printf '%s' "$out" | python3 -c 'import json,sys; print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": sys.stdin.read()}}, ensure_ascii=False))' 2>/dev/null || true

exit 0
