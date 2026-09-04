#!/usr/bin/env bash
# Hook SessionEnd (sin matcher: también `clear`, porque un /clear cierra una unidad de trabajo):
# deja la entrada de BITÁCORA de la sesión en `docs/knowledge/journal/AAAA-MM-DD-<slug>.md` con
# `agent-kits/shared/journal.py write` — borrador DETERMINISTA (fecha, iniciativa activa, ficheros
# tocados por git, tareas del ledger que cambiaron de estado, marcadores del usage-meter cerrados,
# primer prompt de la transcripción como resumen best-effort). Idempotente por `session_id`: la
# segunda ejecución de la misma sesión ACTUALIZA la entrada, no la duplica. La última entrada la
# reinyecta `session-context.sh` al arrancar/retomar. Desactivable con `.claude/dev.json` →
# {"sesion": {"journal": false}}. Solo escribe en proyectos con RASTRO del plugin (`docs/roadmap/`,
# `docs/knowledge/` o `.claude/dev.json`; lo decide `journal.py write`): en cualquier otro repo el
# plugin instalado no siembra carpetas (T-fix1). INFORMA (escribe una nota), no decide: siempre exit 0.
#
# Contrato oficial (code.claude.com/docs/en/hooks.md + hooks-guide.md, verificado 2026-09-03):
#   stdin  → { hook_event_name: "SessionEnd", session_id, transcript_path, cwd,
#              reason: clear|resume|logout|prompt_input_exit|other }
#   stdout → se IGNORA («Output and exit code are ignored, except terminalSequence»): SessionEnd
#            no puede bloquear ni inyectar contexto; por eso el hook solo escribe a disco.
#   tiempo → todos los hooks de SessionEnd comparten un presupuesto de 1,5 s que sube hasta el
#            `timeout` por hook (máx. 60 s) → hooks.json declara `timeout: 20`. El script solo hace
#            git status/diff/show locales (≤ 5 s cada uno) y lee ficheros pequeños.
#   Hooks `prompt`/`agent`: devuelven solo la decisión {"ok","reason"} y su salida en SessionEnd se
#   ignora → NO hay resumen por IA; `journal.py write --enrich` queda para uso MANUAL.
#
# Prueba manual:
#   echo '{"hook_event_name":"SessionEnd","session_id":"s1","reason":"other","cwd":"'"$PWD"'"}' | bash hooks/session-journal.sh
set -u

INPUT="$(cat 2>/dev/null || true)"

command -v python3 >/dev/null 2>&1 || exit 0

JOURNAL="${CLAUDE_PLUGIN_ROOT:-}/agent-kits/shared/journal.py"
if [ ! -f "$JOURNAL" ]; then
  JOURNAL="$(find "${CLAUDE_PROJECT_DIR:-$PWD}/.claude" "${HOME:-}/.claude" -type f -path '*agent-kits/shared/journal.py' 2>/dev/null | head -1)"
fi
[ -n "$JOURNAL" ] && [ -f "$JOURNAL" ] || exit 0

# session_id · reason · transcript_path · cwd del payload (en una sola pasada de python).
eval "$(printf '%s' "$INPUT" | PYTHONIOENCODING=utf-8:replace python3 -c '
import json, shlex, sys
try: d = json.load(sys.stdin)
except Exception: d = {}
if not isinstance(d, dict): d = {}
for k in ("session_id", "reason", "transcript_path", "cwd"):
    print("J_%s=%s" % (k.upper(), shlex.quote(str(d.get(k) or ""))))
' 2>/dev/null || printf 'J_SESSION_ID=""\nJ_REASON=""\nJ_TRANSCRIPT_PATH=""\nJ_CWD=""\n')"

ROOT="${CLAUDE_PROJECT_DIR:-${J_CWD:-$PWD}}"
[ -d "$ROOT" ] || exit 0
[ -n "${J_SESSION_ID:-}" ] || exit 0          # sin session_id no hay clave de idempotencia → nada

# Opt-out del consumidor: .claude/dev.json → {"sesion": {"journal": false}}
if [ -f "$ROOT/.claude/dev.json" ]; then
  activo="$(PYTHONIOENCODING=utf-8:replace python3 -c '
import json, sys
try: d = json.load(open(sys.argv[1], encoding="utf-8"))
except Exception: d = {}
s = d.get("sesion") if isinstance(d, dict) else None
print("0" if isinstance(s, dict) and s.get("journal") is False else "1")
' "$ROOT/.claude/dev.json" 2>/dev/null || echo 1)"
  [ "$activo" = "1" ] || exit 0
fi

args=(write --root "$ROOT" --session-id "$J_SESSION_ID" --fuente hook)
[ -n "${J_REASON:-}" ] && args+=(--reason "$J_REASON")
[ -n "${J_TRANSCRIPT_PATH:-}" ] && args+=(--transcript "$J_TRANSCRIPT_PATH")

python3 "$JOURNAL" "${args[@]}" >/dev/null 2>&1 || true

exit 0
