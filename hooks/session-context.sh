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
#       episódica que dejó el hook SessionEnd `session-journal.sh` — qué pasó, qué quedó pendiente);
#   (4) la MEMORIA TÉCNICA del ÁREA de la iniciativa activa (memory-retrieval T-06): NO el corpus
#       (27.100 tokens no caben en TOPE_CHARS) sino los mejores aciertos compactos de
#       `knowledge-find.py --contexto <título del ledger> --iniciativa <slug>` (enrutado por ÁREA, la
#       misma orden que usa `task-brief.py`), con tope PROPIO `MEMORIA_TOPE_CHARS = 1200` (≤ 300 tokens,
#       spec CA-10) aplicado ANTES del recorte global — la memoria no se come el índice ni el roadmap.
#       Sin iniciativa activa, sin `docs/knowledge/`, sin aciertos o con `dev.json` →
#       {"sesion": {"memoria": false}} el bloque no se emite y el resto sale idéntico. También en
#       `compact`, por la misma razón que (1): lo que la compactación resume, se reinyecta.
# (1), (2) y (4) van también en `compact`: la guía oficial (code.claude.com/docs/en/hooks-guide, «Re-inject
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

# (4) Memoria técnica del área de la iniciativa activa (memory-retrieval T-06). Un solo python compone el
#     bloque: lee dev.json (opt-out `sesion.memoria`), pide las activas a progress-report.py y los aciertos
#     a knowledge-find.py (la MISMA orden enrutada que task-brief.py), y lo topa a MEMORIA_TOPE_CHARS antes
#     de sumarlo. Cualquier fallo → sin bloque; el hook sigue exit 0.
if [ -f "$SHARED/knowledge-find.py" ] && [ -f "$SHARED/progress-report.py" ] && [ -d "$ROOT/docs/knowledge" ] && [ -d "$ROOT/docs/roadmap" ]; then
  mem="$(PYTHONIOENCODING=utf-8:replace python3 - "$SHARED" "$ROOT" <<'PY' 2>/dev/null || true
import json, os, re, subprocess, sys
MEMORIA_TOPE_CHARS = 1200      # ≤ 300 tokens (spec CA-10); tope PROPIO, antes del recorte global a TOPE_CHARS
MEMORIA_LIMIT = 8              # aciertos que se piden por iniciativa; el tope de caracteres es el que manda
shared, root = sys.argv[1], sys.argv[2]
try:
    with open(os.path.join(root, ".claude", "dev.json"), encoding="utf-8-sig") as f:
        cfg = json.load(f)
    ses = cfg.get("sesion") if isinstance(cfg, dict) else None
    if isinstance(ses, dict) and ses.get("memoria") is False:
        sys.exit(0)
except Exception:
    pass                                                  # sin dev.json o corrupto → activado (como indice/journal)

def run(*args):
    r = subprocess.run([sys.executable, *args], capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=20)
    return json.loads(r.stdout) if r.returncode == 0 else {}

activas = run(os.path.join(shared, "progress-report.py"), "active", "--root", os.path.join(root, "docs", "roadmap"), "--json").get("activas", [])
lineas, vistos, total, ordenes = [], set(), 0, []
for a in activas[:2]:
    slug, path = a.get("slug", ""), a.get("path", "")
    titulo = ""
    try:
        with open(os.path.join(root, path) if not os.path.isabs(path) else path, encoding="utf-8", errors="replace") as f:
            for ln in f:
                if ln.startswith("# "):
                    titulo = re.sub(r"^#\s*(?:Checklist de Tareas\s*[—:-]\s*)?", "", ln).strip()
                    break
    except OSError:
        pass
    d = run(os.path.join(shared, "knowledge-find.py"), "--json", "--root", root, "--limit", str(MEMORIA_LIMIT),
            "--contexto", titulo, "--iniciativa", slug)
    total += int(d.get("total", 0) or 0)
    ordenes.append(f"--contexto \"{titulo}\" --iniciativa {slug}")
    for ac in d.get("aciertos", []):
        if ac.get("id") not in vistos and ac.get("linea"):
            vistos.add(ac["id"]); lineas.append(ac["linea"])
if not lineas:
    sys.exit(0)
kf = os.path.join(shared, "knowledge-find.py")
cab = (f"Memoria técnica del área activa (docs/knowledge · {total} acierto(s) de knowledge-find.py; el estado va "
       "delante: aceptada = doctrina, propuesta = indicio, obsoleta = no aplicar):")
pie = f"Detalle solo por ID: python3 \"{kf}\" --show <ID>  (o --related <ID>: su grafo curado)"
n = len(lineas)
while n > 0:
    fuera = total - n
    extra = [f"… y {fuera} más: python3 \"{kf}\" {' · '.join(ordenes)}"] if fuera > 0 else []
    bloque = "\n".join([cab] + [f"- {l}" for l in lineas[:n]] + extra + [pie])
    if len(bloque) <= MEMORIA_TOPE_CHARS:
        print(bloque); break
    n -= 1
PY
)"
  [ -n "$mem" ] && partes="${partes:+$partes

}$mem"
fi

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
