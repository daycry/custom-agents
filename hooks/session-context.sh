#!/usr/bin/env bash
# Hook SessionStart (matcher `startup|resume|compact`): inyecta como contexto de sesión
#   (1) el ÍNDICE DE PIEZAS del plugin (`skill-index.py`: comandos/skills/agentes, ≤ 45 líneas /
#       ≤ 3.500 caracteres, con caché por hash en `.claude/.skill-index.cache`) — es lo que hace
#       que la skill/comando correcto se dispare aunque el usuario no lo nombre; desactivable con
#       `.claude/dev.json` → {"sesion": {"indice": false}};
#   (2) el bloque corto de `progress-report.py session` — iniciativas en progreso, tareas en
#       curso, marcadores abiertos del usage-meter y la línea de retoma del ledger canónico
#       (solo si hay algo activo);
#   (3) SOLO en `startup|resume` (no en `compact`: el journal no cambia dentro de la sesión), la
#       ÚLTIMA entrada del journal de sesión (`journal.py latest --n 2 --max-lines 25`: memoria
#       episódica que dejó el hook SessionEnd `session-journal.sh` — qué pasó, qué quedó pendiente).
# (1) y (2) van también en `compact`: la guía oficial (code.claude.com/docs/en/hooks-guide, «Re-inject
# context after compaction», verificada 2026-09-03) dice que la compactación RESUME la conversación
# y puede perder detalles, y recomienda un SessionStart con matcher `compact` para reinyectar el
# contexto crítico — el índice del arranque no sobrevive íntegro. Coste fijo y medido.
# Si no hay nada que decir (sin piezas + nada activo), NO emite nada. Siempre exit 0.
#
# Contrato oficial (code.claude.com/docs/en/hooks, verificado 2026-09-02):
#   stdin  → { hook_event_name: "SessionStart", source: startup|resume|clear|compact|fork, cwd, … }
#   stdout → {"hookSpecificOutput": {"hookEventName": "SessionStart",
#                                    "additionalContext": "<texto>"}}
#            `additionalContext` DEBE ir anidado en hookSpecificOutput (en primer nivel
#            se ignora en silencio); `hookEventName` es obligatorio. Salida capada a 10.000
#            caracteres por Claude Code: aquí se recorta a TOPE_CHARS antes de emitir.
#
# Prueba manual:
#   echo '{"hook_event_name":"SessionStart","source":"startup"}' | bash hooks/session-context.sh
set -u

INPUT="$(cat 2>/dev/null || true)"

command -v python3 >/dev/null 2>&1 || exit 0

# Kit shared: CLAUDE_PLUGIN_ROOT (lo exporta Claude Code) → find (regla 5 de CONVENTIONS).
SHARED="${CLAUDE_PLUGIN_ROOT:-}/agent-kits/shared"
if [ ! -f "$SHARED/progress-report.py" ] && [ ! -f "$SHARED/skill-index.py" ]; then
  SHARED="$(find "${CLAUDE_PROJECT_DIR:-$PWD}/.claude" "${HOME:-}/.claude" -type d -path '*agent-kits/shared' 2>/dev/null | head -1)"
fi
[ -n "$SHARED" ] && [ -d "$SHARED" ] || exit 0

# Raíz del proyecto: CLAUDE_PROJECT_DIR (lo exporta Claude Code) > cwd del payload > $PWD.
# `source` del payload (startup|resume|clear|compact|fork) decide si entra el journal.
eval "$(printf '%s' "$INPUT" | PYTHONIOENCODING=utf-8:replace python3 -c 'import json,shlex,sys
try: d = json.load(sys.stdin)
except Exception: d = {}
if not isinstance(d, dict): d = {}
print("P_CWD=%s" % shlex.quote(str(d.get("cwd") or "")))
print("P_SOURCE=%s" % shlex.quote(str(d.get("source") or "")))' 2>/dev/null || printf 'P_CWD=""\nP_SOURCE=""\n')"
ROOT="${CLAUDE_PROJECT_DIR:-${P_CWD:-}}"
ROOT="${ROOT:-$PWD}"

partes=""

# (1) Índice de piezas (el script decide caché, dev.json y localización del plugin; exit 0 siempre).
if [ -f "$SHARED/skill-index.py" ]; then
  idx="$(CLAUDE_PROJECT_DIR="$ROOT" python3 "$SHARED/skill-index.py" 2>/dev/null || true)"
  [ -n "$idx" ] && partes="$idx"
fi

# (2) Estado del roadmap (solo si hay docs/roadmap y algo activo).
if [ -f "$SHARED/progress-report.py" ] && [ -d "$ROOT/docs/roadmap" ]; then
  out="$(python3 "$SHARED/progress-report.py" session --root "$ROOT" 2>/dev/null || true)"
  case "$out" in
    ""|"roadmap: sin iniciativas en progreso") ;;      # línea neutra → no gastar contexto
    *) partes="${partes:+$partes

}$out" ;;
  esac
fi

# (3) Journal de sesión — solo al arrancar/retomar (startup|resume; también sin `source`, p. ej. en
#     una prueba manual): la compactación no cambia el journal, así que en `compact` no se repite.
case "${P_SOURCE:-startup}" in
  startup|resume)
    if [ -f "$SHARED/journal.py" ] && [ -d "$ROOT/docs/knowledge/journal" ]; then
      jr="$(python3 "$SHARED/journal.py" latest --root "$ROOT" --n 2 --max-lines 25 2>/dev/null || true)"
      [ -n "$jr" ] && partes="${partes:+$partes

}$jr"
    fi ;;
esac

[ -n "$partes" ] || exit 0

printf '%s' "$partes" | PYTHONIOENCODING=utf-8:replace python3 -c '
import json, sys
TOPE_CHARS = 9500   # margen bajo el tope de 10.000 caracteres de la salida del hook
t = sys.stdin.read()
if len(t) > TOPE_CHARS:
    t = t[:TOPE_CHARS - 1].rstrip() + "…"
print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": t}}, ensure_ascii=False))
' 2>/dev/null || true

exit 0
