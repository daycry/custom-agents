#!/usr/bin/env bash
# Hook PostToolUse (Write/Edit/MultiEdit): marca que hay documentación pendiente de
# sincronizar con Confluence. NO publica nada y NO depende de git.
#
# Deja una marca vacía en .claude/.confluence-pending cuando se edita un fichero bajo docs/
# (excepto docs/security-scan/). La sincronización real la hace la skill confluence-publish,
# que compara docs/ contra el manifiesto .claude/confluence-state.json y, al terminar, borra
# esta marca. Así el hook es solo un disparador determinista.
#
# Entrada: JSON por stdin con { tool_input: { file_path, edits[].file_path, ... } }.
set -u

INPUT="$(cat 2>/dev/null || true)"

# Extrae la(s) ruta(s) de fichero del payload. Usa jq si está; si no, grep de respaldo.
paths=""
if command -v jq >/dev/null 2>&1; then
  paths="$(printf '%s' "$INPUT" | jq -r '[.tool_input.file_path, (.tool_input.edits[]?.file_path)] | map(select(. != null)) | .[]' 2>/dev/null)"
else
  paths="$(printf '%s' "$INPUT" | grep -oE '"file_path"[[:space:]]*:[[:space:]]*"[^"]+"' | sed -E 's/.*:[[:space:]]*"([^"]+)"/\1/')"
fi

[ -n "$paths" ] || exit 0

hit=0
while IFS= read -r p; do
  [ -n "$p" ] || continue
  case "$p" in
    *docs/security-scan/*) continue ;;   # nunca sincronizar datos sensibles de nemesis
    *docs/*) hit=1 ;;                     # cambio bajo docs/ -> pendiente
  esac
done <<EOF
$paths
EOF

[ "$hit" = "1" ] || exit 0

DIR="${CLAUDE_PROJECT_DIR:-$PWD}/.claude"
mkdir -p "$DIR" 2>/dev/null || exit 0
: > "$DIR/.confluence-pending" 2>/dev/null || true
exit 0
