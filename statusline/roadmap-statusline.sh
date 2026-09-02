#!/usr/bin/env bash
# roadmap-statusline.sh — barra de estado OPT-IN de Claude Code: modelo · coste de la
# sesión · contexto usado · progreso del roadmap (ledger canónico).
#
# Se activa en /setup (paso 5-bis) escribiendo en `.claude/settings.json` del proyecto:
#   {"statusLine": {"type": "command", "command": "/ruta/ABSOLUTA/statusline/roadmap-statusline.sh"}}
# (la doc oficial solo documenta `~` en `statusLine.command`, no `${CLAUDE_PLUGIN_ROOT}`;
# por eso /setup resuelve la ruta con `find` y la escribe absoluta). Reversión: borrar
# la clave `statusLine` de settings.json (o `/statusline remove`).
#
# Contrato oficial (code.claude.com/docs/en/statusline, verificado 2026-09-02):
#   stdin (JSON) → model.display_name · cost.total_cost_usd ·
#                  context_window.used_percentage (puede ser null al inicio de sesión)
#   stdout       → lo que se imprime se muestra tal cual (una línea aquí, ≤ ~100 chars).
#
# Degradación (nunca falla, siempre exit 0):
#   - con jq → parsea con jq; sin jq → python3; sin ninguno → imprime solo el modelo
#     (si se puede extraer con grep) o nada.
#   - sin progress-report.py o sin docs/roadmap/ → omite el tramo del roadmap.
#
# Prueba manual (JSON de ejemplo de la doc):
#   echo '{"model":{"display_name":"Opus"},"cost":{"total_cost_usd":0.01234},"context_window":{"used_percentage":8}}' \
#     | bash statusline/roadmap-statusline.sh
set -u

INPUT="$(cat 2>/dev/null || true)"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)"

model="" cost="" ctx=""
if command -v jq >/dev/null 2>&1; then
  model="$(printf '%s' "$INPUT" | jq -r '.model.display_name // empty' 2>/dev/null)"
  cost="$(printf '%s' "$INPUT" | jq -r '.cost.total_cost_usd // empty' 2>/dev/null)"
  ctx="$(printf '%s' "$INPUT" | jq -r '.context_window.used_percentage // empty' 2>/dev/null)"
elif command -v python3 >/dev/null 2>&1; then
  eval "$(printf '%s' "$INPUT" | python3 -c '
import json, sys, shlex
try:
    d = json.load(sys.stdin)
except Exception:
    d = {}
g = lambda *ks: (lambda v: "" if v is None else v)(
    __import__("functools").reduce(lambda a, k: a.get(k) if isinstance(a, dict) else None, ks, d))
print("model=" + shlex.quote(str(g("model", "display_name"))))
print("cost=" + shlex.quote(str(g("cost", "total_cost_usd"))))
print("ctx=" + shlex.quote(str(g("context_window", "used_percentage"))))
' 2>/dev/null)"
else
  # Sin parser JSON: solo el modelo, por grep (mejor esfuerzo).
  model="$(printf '%s' "$INPUT" | grep -oE '"display_name"[[:space:]]*:[[:space:]]*"[^"]*"' 2>/dev/null | head -1 | sed -E 's/.*:[[:space:]]*"([^"]*)"/\1/' 2>/dev/null)"
  [ -n "$model" ] && printf '[%s]\n' "$model" 2>/dev/null
  exit 0
fi

out=""
[ -n "$model" ] && out="[$model]"
# Coste y contexto solo si son numéricos (un valor raro se omite, no se imprime a medias).
if printf '%s' "$cost" | grep -qE '^[0-9]+([.][0-9]+)?$'; then
  cost_fmt="$(printf '%.2f' "$cost" 2>/dev/null)"
  [ -n "$cost_fmt" ] && out="${out:+$out }\$${cost_fmt}"
fi
if printf '%s' "$ctx" | grep -qE '^[0-9]+([.][0-9]+)?$'; then
  ctx_int="$(printf '%.0f' "$ctx" 2>/dev/null)"
  [ -n "$ctx_int" ] && out="${out:+$out }ctx ${ctx_int}%"
fi

# ---- roadmap (progress-report.py active --json) ----
if command -v python3 >/dev/null 2>&1; then
  REPORT="$HERE/../agent-kits/shared/progress-report.py"
  if [ ! -f "$REPORT" ]; then
    REPORT="$(find "$PWD/.claude" "${HOME:-}/.claude" -type f -path '*agent-kits/shared/progress-report.py' 2>/dev/null | head -1)"
  fi
  ROOT="${CLAUDE_PROJECT_DIR:-$PWD}/docs/roadmap"
  if [ -n "$REPORT" ] && [ -f "$REPORT" ] && [ -d "$ROOT" ]; then
    rm_seg="$(python3 "$REPORT" active --root "$ROOT" --json 2>/dev/null | python3 -c '
import json, sys
try:
    a = json.load(sys.stdin).get("activas", [])
except Exception:
    a = []
if len(a) == 1:
    r = a[0]
    print("📋 %s T-%02d/%d %d%%" % (r["slug"], r["completadas"], r["total"], r["pct"]))
elif len(a) > 1:
    print("📋 %d iniciativas activas" % len(a))
' 2>/dev/null)"
    [ -n "$rm_seg" ] && out="${out:+$out · }$rm_seg"
  fi
fi

[ -n "$out" ] && printf '%s\n' "$out"
exit 0
