#!/usr/bin/env bash
# Hook PostToolUse (Write/Edit/MultiEdit): cuando se edita un ledger canónico
# `docs/roadmap/*/tasks.md`, emite UNA línea de progreso determinista
# (`progress-report.py line`) como `systemMessage` — el usuario ve el avance sin
# que el agente tenga que redactarlo. INFORMA, no decide: siempre exit 0.
#
# Contrato oficial (code.claude.com/docs/en/hooks, verificado 2026-09-02):
#   stdin  → { tool_name, tool_input: { file_path | edits[].file_path }, tool_response, … }
#   stdout → {"systemMessage": "<texto>"}   (campo universal de primer nivel; en
#            PostToolUse se muestra al usuario; el tool ya corrió, no hay bloqueo)
#
# Debounce: la última línea emitida se guarda en
# ${CLAUDE_PROJECT_DIR:-$PWD}/.claude/.progress-last (estado local, en .gitignore);
# si la nueva línea es idéntica, no se emite nada (ediciones consecutivas sin cambio
# de estado no hacen ruido). La comparación+escritura es ATÓMICA (debt-cleanup T-01):
# si hay `flock`, la sección crítica se serializa sobre `.progress-last.lock` (N
# invocaciones concurrentes con la misma línea → exactamente UNA systemMessage); sin
# `flock` (macOS sin coreutils) la escritura sigue siendo atómica (temporal en el mismo
# directorio + `mv -f`, rename POSIX: nunca un fichero a medias), pero dos lectores
# pueden ver el estado viejo a la vez → como mucho alguna línea duplicada, nunca perdida.
#
# Prueba manual:
#   echo '{"tool_input":{"file_path":"'"$PWD"'/docs/roadmap/<slug>/tasks.md"}}' | bash hooks/progress-line.sh
set -u

INPUT="$(cat 2>/dev/null || true)"

# Sin python3 no hay informe: salir en silencio (el hook jamás rompe el flujo).
command -v python3 >/dev/null 2>&1 || exit 0

# Extraer ruta(s) del payload (jq si está; grep de respaldo — mismo patrón que
# ledger-lint-warn.sh).
paths=""
if command -v jq >/dev/null 2>&1; then
  paths="$(printf '%s' "$INPUT" | jq -r '[.tool_input.file_path, (.tool_input.edits[]?.file_path)] | map(select(. != null)) | .[]' 2>/dev/null)"
else
  paths="$(printf '%s' "$INPUT" | grep -oE '"file_path"[[:space:]]*:[[:space:]]*"[^"]+"' | sed -E 's/.*:[[:space:]]*"([^"]+)"/\1/')"
fi
[ -n "$paths" ] || exit 0

# Localizar progress-report.py: primero junto al plugin, después por find (scope
# proyecto/usuario), como el resto de kits (regla 5 de CONVENTIONS).
REPORT="${CLAUDE_PLUGIN_ROOT:-}/agent-kits/shared/progress-report.py"
if [ ! -f "$REPORT" ]; then
  REPORT="$(find "${CLAUDE_PROJECT_DIR:-$PWD}/.claude" "${HOME:-}/.claude" -type f -path '*agent-kits/shared/progress-report.py' 2>/dev/null | head -1)"
fi
[ -n "$REPORT" ] && [ -f "$REPORT" ] || exit 0

STATE_DIR="${CLAUDE_PROJECT_DIR:-$PWD}/.claude"
LAST="$STATE_DIR/.progress-last"
mkdir -p "$STATE_DIR" 2>/dev/null || true

# Cerrojo del debounce: con `flock`, sobre .progress-last.lock (fd 9; se libera al salir, la
# sección crítica dura milisegundos); sin `flock`, solo la escritura atómica (degradación).
cerrojo_debounce() {
  command -v flock >/dev/null 2>&1 && [ -d "$STATE_DIR" ] || return 0
  { exec 9>"$STATE_DIR/.progress-last.lock"; } 2>/dev/null && flock -w 5 9 2>/dev/null || true
}

# ¿Es la misma línea que la última emitida? (1 = repetida → silencio). Si no, la guarda de
# forma ATÓMICA: temporal en el MISMO directorio + `mv -f` (rename), nunca un fichero a medias.
debounce_repetida() {
  local line="$1" tmp
  if [ -f "$LAST" ] && [ "$(cat "$LAST" 2>/dev/null)" = "$line" ]; then
    return 0
  fi
  tmp="$(mktemp "$STATE_DIR/.progress-last.XXXXXX" 2>/dev/null)" || return 1
  if printf '%s' "$line" > "$tmp" 2>/dev/null && mv -f "$tmp" "$LAST" 2>/dev/null; then
    return 1
  fi
  rm -f "$tmp" 2>/dev/null
  return 1
}

while IFS= read -r p; do
  [ -n "$p" ] || continue
  p="${p//\\//}"   # rutas Windows nativas (C:\proy\docs\roadmap\...) → separador '/'
  case "$p" in
    *docs/roadmap/*tasks.md)
      [ -f "$p" ] || continue
      line="$(python3 "$REPORT" line "$p" 2>/dev/null || true)"
      [ -n "$line" ] || continue
      # Debounce (bajo cerrojo): misma línea que la última vez → silencio.
      cerrojo_debounce
      debounce_repetida "$line" && continue
      # JSON seguro (escapa comillas, backslashes, unicode) vía python3.
      printf '%s' "$line" | python3 -c 'import json,sys; print(json.dumps({"systemMessage": sys.stdin.read()}, ensure_ascii=False))' 2>/dev/null || true
      break   # una sola línea por invocación (el JSON de stdout debe ser un único objeto)
      ;;
  esac
done <<EOF
$paths
EOF

exit 0
