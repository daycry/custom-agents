#!/usr/bin/env bash
# Hook SubagentStop: cuando termina un subagente (p. ej. una tarea despachada por
# /dev-cycle con `subagentes: true`), emite el estado de las iniciativas del roadmap
# que están `en-progreso` (`progress-report.py active`) como `systemMessage`, para que
# el usuario vea el avance entre tareas sin leer el ledger. Solo emite si hay alguna
# activa. INFORMA, no decide: siempre exit 0 (jamás retiene al subagente).
#
# Contrato oficial (code.claude.com/docs/en/hooks, verificado 2026-09-02):
#   stdin  → { hook_event_name: "SubagentStop", agent_id, agent_type,
#              last_assistant_message, stop_hook_active, … }   (no se usa: el estado
#              se lee del ledger, no del mensaje del subagente)
#   stdout → {"systemMessage": "<texto>"}   (campo universal; se muestra al usuario).
#            NO se emite `decision`/`continue`/`additionalContext`: no se quiere
#            retener ni instruir al subagente.
#
# Prueba manual:
#   echo '{"hook_event_name":"SubagentStop","agent_type":"implementer"}' | bash hooks/subagent-progress.sh
set -u

cat >/dev/null 2>&1 || true   # consumir stdin (no se usa)

command -v python3 >/dev/null 2>&1 || exit 0

REPORT="${CLAUDE_PLUGIN_ROOT:-}/agent-kits/shared/progress-report.py"
if [ ! -f "$REPORT" ]; then
  REPORT="$(find "${CLAUDE_PROJECT_DIR:-$PWD}/.claude" "${HOME:-}/.claude" -type f -path '*agent-kits/shared/progress-report.py' 2>/dev/null | head -1)"
fi
[ -n "$REPORT" ] && [ -f "$REPORT" ] || exit 0

ROOT="${CLAUDE_PROJECT_DIR:-$PWD}/docs/roadmap"
[ -d "$ROOT" ] || exit 0

out="$(python3 "$REPORT" active --root "$ROOT" 2>/dev/null || true)"
[ -n "$out" ] || exit 0
[ "$out" != "sin iniciativas en progreso" ] || exit 0

printf '%s' "$out" | python3 -c 'import json,sys; print(json.dumps({"systemMessage": sys.stdin.read()}, ensure_ascii=False))' 2>/dev/null || true

exit 0
