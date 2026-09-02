#!/usr/bin/env python3
"""
progress-report.py — línea de progreso DETERMINISTA del ledger canónico `tasks.md`
(agent-kits/shared: lo invocan los hooks `progress-line.sh` (PostToolUse),
`subagent-progress.sh` (SubagentStop), `session-context.sh` (SessionStart) y el
statusline opt-in `statusline/roadmap-statusline.sh`).

Reutiliza el parser estructural de `ledger-lint.py` (`parse_ledger`), importado como
módulo sin efectos secundarios; no valida, solo resume.

Subcomandos:
  line <tasks.md> [--json]
      UNA línea:
      📋 <slug> · T-04/12 completadas (33%) · fase 2/4 «<nombre>» · en curso: T-05 <título> · IA real 1h12m
      Tramos opcionales: «fase» solo si hay ≥1 fase; «en curso» solo si hay una tarea
      en-progreso; «IA real» solo si alguna tarea tiene horas IA reales MEDIDAS (formato
      XhYm); si todas las reales están marcadas «(estimado)», el tramo se rotula «IA est.».
  active [--root docs/roadmap] [--json]
      Una línea por iniciativa con estado `en-progreso` (frontmatter `estado:` o, si falta,
      tabla `| **Estado** |`). Sin ninguna → `sin iniciativas en progreso`. Ficheros que no
      se pueden parsear se SALTAN con aviso en stderr.
  session [--root .]
      Bloque ≤ 15 líneas para inyectar como contexto de sesión: activas, tareas en curso,
      marcadores huérfanos de `usage-meter.py status` (si está junto a este script) y la
      línea de retoma. Sin nada activo → UNA línea neutra (`LINEA_NEUTRA`).

Exit codes:
  0  OK (active/session: SIEMPRE 0, incluso sin roadmap — la información nunca bloquea)
  1  uso incorrecto / fichero inexistente (solo `line`)
  2  ledger ilegible o sin tareas `### T-XX` (solo `line`; aviso en stderr)
"""
import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LINEA_NEUTRA = "roadmap: sin iniciativas en progreso"
SIN_ACTIVAS = "sin iniciativas en progreso"


def _load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, filename))
    if spec is None or spec.loader is None:
        raise ImportError(filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_ll = _load_module("ledger_lint", "ledger-lint.py")
parse_ledger = _ll.parse_ledger
norm_estado = _ll.norm_estado


def fmt_horas(horas):
    """Horas decimales → 'XhYm' (mismo formato que usage-meter.py fmt). Copia local mínima
    para no depender del meter en runtime; si el meter está, se prefiere su implementación."""
    try:
        um = _load_module("usage_meter", "usage-meter.py")
        return um.fmt_horas(horas)
    except Exception:  # noqa: BLE001 — degradación: formato local
        total_min = round(float(horas) * 60)
        h, m = divmod(total_min, 60)
        if h and m:
            return f"{h}h {m}m"
        if h:
            return f"{h}h"
        return f"{m}m"


# ------------------------------------------------------------------ núcleo

def slug_de(path, frontmatter):
    d = os.path.basename(os.path.dirname(os.path.abspath(path)))
    slug = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", d)
    if not slug or slug in (".", "") or d in (".", ""):
        slug = frontmatter.get("tasks") or "ledger"
    return slug


def nombre_fase(nombre):
    """'Fase 2 — Núcleo' → 'Núcleo'; 'Fase única — visibilidad' → 'visibilidad'; sin separador → tal cual."""
    m = re.match(r"^\s*Fase\b[^—–:-]*[—–:-]\s*(.+)$", nombre)
    return (m.group(1) if m else nombre).strip()


def resumir(path):
    """Lee y resume un ledger. Lanza ValueError si es ilegible o no tiene tareas."""
    try:
        text = open(path, encoding="utf-8-sig", errors="replace").read()   # tolera BOM
    except OSError as e:
        raise ValueError(f"no se puede leer: {e}") from e
    parsed = parse_ledger(text)
    tareas = parsed["tareas"]
    if not tareas:
        raise ValueError("sin tareas `### T-XX` reconocibles")

    total = len(tareas)
    completadas = sum(1 for t in tareas if t["estado"] == "completado")
    pct = round(100 * completadas / total) if total else 0

    en_curso = next((t for t in tareas if t["estado"] == "en-progreso"), None)

    fases = parsed["fases"]
    fase = None
    if fases:
        idx = None
        if en_curso is not None:
            idx = next((i for i, f in enumerate(fases) if en_curso in f["tareas"]), None)
        if idx is None:
            idx = next((i for i, f in enumerate(fases)
                        if any(t["estado"] != "completado" for t in f["tareas"])), len(fases) - 1)
        fase = {"indice": idx + 1, "total": len(fases), "nombre": nombre_fase(fases[idx]["nombre"])}

    # Horas IA: solo cuentan como «real» las NO marcadas «(estimado)»; si todas las que hay
    # son estimadas, se suman igual pero se rotulan «IA est.» (no se vende estimado como medido).
    medidas = [t["ia_real_h"] for t in tareas if t["ia_real_h"] is not None
               and t["ia_real_fuente"] != "estimado"]
    estimadas = [t["ia_real_h"] for t in tareas if t["ia_real_h"] is not None
                 and t["ia_real_fuente"] == "estimado"]
    if medidas:
        ia_real_h, ia_fuente = round(sum(medidas), 4), "medido"
    elif estimadas:
        ia_real_h, ia_fuente = round(sum(estimadas), 4), "estimado"
    else:
        ia_real_h, ia_fuente = None, None

    estado = norm_estado(parsed["frontmatter"]["estado"]) if parsed["frontmatter"].get("estado") \
        else parsed["estado_tabla"]

    return {
        "slug": slug_de(path, parsed["frontmatter"]),
        "path": path,
        "estado": estado,
        "completadas": completadas,
        "total": total,
        "pct": pct,
        "fase": fase,
        "en_curso": {"id": en_curso["id"], "titulo": en_curso["titulo"]} if en_curso else None,
        "en_progreso": [{"id": t["id"], "titulo": t["titulo"]}
                        for t in tareas if t["estado"] == "en-progreso"],
        "ia_real_h": ia_real_h,
        "ia_fuente": ia_fuente,
        "ia_real_fmt": fmt_horas(ia_real_h) if ia_real_h is not None else None,
    }


def linea(r):
    partes = [f"📋 {r['slug']}",
              f"T-{r['completadas']:02d}/{r['total']} completadas ({r['pct']}%)"]
    if r["fase"]:
        partes.append(f"fase {r['fase']['indice']}/{r['fase']['total']} «{r['fase']['nombre']}»")
    if r["en_curso"]:
        t = r["en_curso"]
        partes.append(f"en curso: {t['id']} {t['titulo']}".rstrip())
    if r["ia_real_fmt"]:
        rotulo = "IA real" if r.get("ia_fuente") == "medido" else "IA est."
        partes.append(f"{rotulo} {r['ia_real_fmt']}")
    return " · ".join(partes)


def activas(root):
    """[(resumen)] de las iniciativas en-progreso bajo root/*/tasks.md; avisa por stderr y sigue."""
    out = []
    if not os.path.isdir(root):
        return out
    for d in sorted(os.listdir(root)):
        p = os.path.join(root, d, "tasks.md")
        if not os.path.isfile(p):
            continue
        try:
            r = resumir(p)
        except ValueError as e:
            print(f"⚠️  progress-report: {p}: {e} (saltado)", file=sys.stderr)
            continue
        if r["estado"] == "en-progreso":
            out.append(r)
    return out


def marcadores_huerfanos(root="."):
    """Marcadores abiertos (sin cierre) de usage-meter.py status sobre el estado del PROYECTO
    (`<root>/.claude/usage-state.json`, no el cwd); None si el meter no está o falla."""
    meter = os.path.join(HERE, "usage-meter.py")
    if not os.path.isfile(meter):
        return None
    try:
        state = os.path.join(root, ".claude", "usage-state.json")
        res = subprocess.run([sys.executable, meter, "status", "--state", state],
                             capture_output=True, text=True, timeout=10, check=False)
        data = json.loads(res.stdout or "{}")
        return [m.get("artefacto", "?") for m in data.get("marcadores", []) if not m.get("cerrado")]
    except Exception:  # noqa: BLE001 — cualquier fallo del meter = no disponible
        return None


# ------------------------------------------------------------------ CLI

def cmd_line(args):
    if not os.path.isfile(args.tasks):
        print(f"progress-report: no existe {args.tasks}", file=sys.stderr)
        return 1
    try:
        r = resumir(args.tasks)
    except ValueError as e:
        print(f"⚠️  progress-report: {args.tasks}: {e}", file=sys.stderr)
        return 2
    if args.json:
        r["linea"] = linea(r)
        print(json.dumps(r, ensure_ascii=False))
    else:
        print(linea(r))
    return 0


def cmd_active(args):
    rs = activas(args.root)
    if args.json:
        for r in rs:
            r["linea"] = linea(r)
        print(json.dumps({"activas": rs}, ensure_ascii=False))
        return 0
    if not rs:
        print(SIN_ACTIVAS)
        return 0
    for r in rs:
        print(linea(r))
    return 0


def cmd_session(args):
    root = os.path.join(args.root, "docs", "roadmap")
    rs = activas(root)
    if not rs:
        print(LINEA_NEUTRA)
        return 0
    out = ["Roadmap en progreso (ledger canónico = tasks.md):"]
    for r in rs:
        out.append("- " + linea(r))
        for t in r["en_progreso"]:
            out.append(f"  · en-progreso: {t['id']} {t['titulo']}".rstrip())
    huerf = marcadores_huerfanos(args.root)
    if huerf is None:
        out.append("usage-meter: no disponible")
    elif huerf:
        out.append("usage-meter: marcadores abiertos → " + ", ".join(huerf[:5])
                   + (" …" if len(huerf) > 5 else ""))
    rel = os.path.relpath(rs[0]["path"], args.root) if len(rs) == 1 \
        else os.path.join("docs", "roadmap", "<…>", "tasks.md")
    out.append(f"Ledger canónico: {rel} — retoma desde la tarea en-progreso")
    print("\n".join(out[:15]))
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[1].strip())
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("line", help="una línea de progreso de un tasks.md")
    sp.add_argument("tasks")
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(fn=cmd_line)

    sp = sub.add_parser("active", help="iniciativas en-progreso bajo --root")
    sp.add_argument("--root", default=os.path.join("docs", "roadmap"))
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(fn=cmd_active)

    sp = sub.add_parser("session", help="bloque de contexto de sesión (≤15 líneas)")
    sp.add_argument("--root", default=".")
    sp.set_defaults(fn=cmd_session)

    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
