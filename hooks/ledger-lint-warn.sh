#!/usr/bin/env bash
# Hook PostToolUse (Write/Edit/MultiEdit): valida el ledger canónico tasks.md
# con ledger-lint.py en MODO AVISO cada vez que se edita. Determinista: ocurre
# siempre, sin depender del prompt. NUNCA bloquea la edición (siempre exit 0).
#
# Entrada: JSON por stdin con { tool_input: { file_path, edits[].file_path } }.
# Solo actúa sobre ficheros */docs/roadmap/*/tasks.md.
set -u

INPUT="$(cat 2>/dev/null || true)"

# Sin python3 no hay lint: salir en silencio (el hook jamás rompe el flujo).
command -v python3 >/dev/null 2>&1 || exit 0

# Extraer ruta(s) del payload (jq si está; grep de respaldo — mismo patrón
# que mark-docs-pending.sh).
paths=""
if command -v jq >/dev/null 2>&1; then
  paths="$(printf '%s' "$INPUT" | jq -r '[.tool_input.file_path, (.tool_input.edits[]?.file_path)] | map(select(. != null)) | .[]' 2>/dev/null)"
else
  paths="$(printf '%s' "$INPUT" | grep -oE '"file_path"[[:space:]]*:[[:space:]]*"[^"]+"' | sed -E 's/.*:[[:space:]]*"([^"]+)"/\1/')"
fi
[ -n "$paths" ] || exit 0

# Localizar ledger-lint.py: primero junto al plugin, después por find (scope
# proyecto/usuario), como el resto de kits.
LINT="${CLAUDE_PLUGIN_ROOT:-}/agent-kits/shared/ledger-lint.py"
if [ ! -f "$LINT" ]; then
  LINT="$(find "${CLAUDE_PROJECT_DIR:-$PWD}/.claude" "$HOME/.claude" -type f -path '*agent-kits/shared/ledger-lint.py' 2>/dev/null | head -1)"
fi
[ -n "$LINT" ] && [ -f "$LINT" ] || exit 0

while IFS= read -r p; do
  [ -n "$p" ] || continue
  case "$p" in
    *docs/roadmap/*tasks.md)
      python3 "$LINT" "$p" --warn-only 2>/dev/null || true
      ;;
  esac
done <<EOF
$paths
EOF

exit 0
