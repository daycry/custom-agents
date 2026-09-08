#!/usr/bin/env python3
"""
retro-gate.py — PUERTA determinista del cierre de una iniciativa: sin retro no hay cierre (memory-retrieval T-17; spec CA-23).

`/retro` era «un comando que alguien recuerda», y `docs/roadmap/CALIBRATION.md` llevaba semanas sin fila con
iniciativas cerradas detrás (medido en `analysis.md`: 15 días y 13 cerradas). Esta puerta la usa `/dev-cycle`
Fase 6 (paso 8 del ritual de cierre) con el mismo patrón que `qa-gate.py` y `ledger-lint.py`: una puerta con exit
code, no un aviso ignorable («un aviso que se puede ignorar se ignorará», `LES-012`). Comprueba dos hechos
mecánicos: (1) existe `docs/roadmap/<fecha>-<slug>/retro.md` con frontmatter (`---` … `---`) y cuerpo; (2)
`docs/roadmap/CALIBRATION.md` tiene una fila cuya columna «Iniciativa» es el slug (con o sin fecha, con o sin
acentos graves). NO escribe la retro ni la fila —eso es `/retro`, con las causas que solo conoce quien las
vivió—: automatiza EXIGIRLA. Informa (ℹ️) si el ledger no está `completado`, sin cambiar el veredicto.

Uso:
  retro-gate.py <docs/roadmap/<fecha>-<slug> | <fecha>-<slug> | slug> [--root DIR] [--json]
Exit: 0 puerta abierta · 1 cerrada (imprime qué falta y el comando exacto `/retro docs/roadmap/<carpeta>`) ·
2 error de uso (carpeta no encontrada o ambigua).
"""
import argparse
import json
import os
import re
import sys

# Consola Windows (cp1252) o tuberías: reconfigurar ANTES de imprimir nada (GOT-005).
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure, ya leído o None (capsys, pythonw)

OK, KO, INFO = "✅", "❌", "ℹ️"
_FILA_RE = re.compile(r"^\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*([^|]+?)\s*\|")
_FECHA_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-")


def slug_de(nombre_carpeta):
    return _FECHA_RE.sub("", nombre_carpeta)


def resolver_carpeta(root, arg):
    """`docs/roadmap/<fecha>-<slug>` (relativa a root o absoluta), `<fecha>-<slug>` o `slug` → carpeta absoluta.
    None si no existe; "ambigua" si un slug sin fecha casa con varias carpetas."""
    roadmap = os.path.join(root, "docs", "roadmap")
    candidatos = [arg, os.path.join(root, arg), os.path.join(roadmap, arg)]
    for c in candidatos:
        if os.path.isdir(c) and (os.path.isfile(os.path.join(c, "tasks.md"))
                                 or os.path.basename(os.path.dirname(os.path.abspath(c))) == "roadmap"):
            return os.path.abspath(c)
    if os.path.isdir(roadmap):
        iguales = [d for d in sorted(os.listdir(roadmap))
                   if os.path.isdir(os.path.join(roadmap, d)) and slug_de(d) == arg]
        if len(iguales) == 1:
            return os.path.join(roadmap, iguales[0])
        if len(iguales) > 1:
            return "ambigua"
    return None


def raiz_de(carpeta):
    """Raíz del proyecto a partir de `<raíz>/docs/roadmap/<carpeta>` (None si la carpeta no cuelga de ahí): la puerta
    juzga el CALIBRATION.md del proyecto de la iniciativa, no el del cwd."""
    c = os.path.abspath(carpeta)
    roadmap, docs = os.path.dirname(c), os.path.dirname(os.path.dirname(c))
    if os.path.basename(roadmap) == "roadmap" and os.path.basename(docs) == "docs":
        return os.path.dirname(docs)
    return None


def retro_ok(carpeta):
    """(bool, motivo) — retro.md existe, empieza por frontmatter cerrado y tiene cuerpo."""
    p = os.path.join(carpeta, "retro.md")
    if not os.path.isfile(p):
        return False, "retro.md no existe"
    try:
        text = open(p, encoding="utf-8-sig", errors="replace").read()
    except OSError as e:
        return False, f"retro.md ilegible ({e.__class__.__name__})"
    if not text.strip():
        return False, "retro.md está vacío"
    if not text.startswith("---") or text.find("\n---", 3) == -1:
        return False, "retro.md sin frontmatter (`---` … `---`)"
    cuerpo = text[text.find("\n---", 3) + 4:].strip()
    if not cuerpo:
        return False, "retro.md sin cuerpo tras el frontmatter"
    return True, "retro.md con frontmatter y cuerpo"


def fila_calibracion(root, carpeta):
    """(bool, motivo) — CALIBRATION.md tiene una fila cuya Iniciativa es el slug o la carpeta completa."""
    cal = os.path.join(root, "docs", "roadmap", "CALIBRATION.md")
    if not os.path.isfile(cal):
        return False, "docs/roadmap/CALIBRATION.md no existe"
    nombre = os.path.basename(os.path.normpath(carpeta))
    objetivo = {nombre, slug_de(nombre)}
    try:
        for ln in open(cal, encoding="utf-8-sig", errors="replace"):
            m = _FILA_RE.match(ln)
            if m and m.group(2).strip().strip("`").strip() in objetivo:
                return True, f"fila del {m.group(1)} para `{slug_de(nombre)}` en CALIBRATION.md"
    except OSError as e:
        return False, f"CALIBRATION.md ilegible ({e.__class__.__name__})"
    return False, f"sin fila para `{slug_de(nombre)}` en docs/roadmap/CALIBRATION.md"


def estado_ledger(carpeta):
    p = os.path.join(carpeta, "tasks.md")
    try:
        text = open(p, encoding="utf-8-sig", errors="replace").read()
    except OSError:
        return None
    m = re.search(r"^estado:\s*([a-z\-]+)", text, re.M)
    return m.group(1) if m else None


def veredicto(root, carpeta):
    nombre = os.path.basename(os.path.normpath(carpeta))
    slug = slug_de(nombre)
    r_ok, r_motivo = retro_ok(carpeta)
    f_ok, f_motivo = fila_calibracion(root, carpeta)
    faltan = ([] if r_ok else ["retro.md"]) + ([] if f_ok else ["fila en CALIBRATION.md"])
    estado = estado_ledger(carpeta)
    lineas = [(OK if r_ok else KO, r_motivo), (OK if f_ok else KO, f_motivo)]
    if estado and estado != "completado":
        lineas.append((INFO, f"el ledger está `{estado}`, no `completado`: la retro es de iniciativas cerradas (no cambia el veredicto)"))
    return {"abierta": not faltan, "carpeta": f"docs/roadmap/{nombre}", "slug": slug, "retro": r_ok, "fila": f_ok,
            "faltan": faltan, "ledger_estado": estado, "comando": f"/retro docs/roadmap/{nombre}", "lineas": lineas}


def render(v):
    out = [f"retro-gate: {v['carpeta']} (slug `{v['slug']}`)"]
    out += [f"{icono} {texto}" for icono, texto in v["lineas"]]
    if v["abierta"]:
        out.append(f"{OK} Puerta ABIERTA: la iniciativa puede declararse cerrada.")
    else:
        out.append(f"{KO} Puerta CERRADA — falta: {', '.join(v['faltan'])}. Ejecuta `{v['comando']}` (escribe retro.md y la "
                   "fila de CALIBRATION.md con las causas reales) y vuelve a pasar la puerta. La iniciativa NO se declara "
                   "cerrada hasta entonces.")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1].strip())
    ap.add_argument("carpeta", nargs="?", help="docs/roadmap/<fecha>-<slug>, <fecha>-<slug> o slug")
    ap.add_argument("--root", default=None, help="raíz del proyecto (default: la de la carpeta, o CLAUDE_PROJECT_DIR, o cwd)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if not a.carpeta:
        ap.print_usage(sys.stderr)
        print("retro-gate: falta la carpeta de la iniciativa", file=sys.stderr)
        return 2
    root = os.path.abspath(a.root or os.environ.get("CLAUDE_PROJECT_DIR") or ".")
    carpeta = resolver_carpeta(root, a.carpeta)
    if carpeta not in (None, "ambigua"):
        root = raiz_de(carpeta) or root                 # la raíz manda desde la carpeta resuelta
    if carpeta is None:
        print(f"retro-gate: no encuentro la iniciativa `{a.carpeta}` bajo {os.path.join(root, 'docs', 'roadmap')}", file=sys.stderr)
        return 2
    if carpeta == "ambigua":
        print(f"retro-gate: `{a.carpeta}` casa con varias carpetas de docs/roadmap/: pasa la carpeta con su fecha", file=sys.stderr)
        return 2
    v = veredicto(root, carpeta)
    if a.json:
        print(json.dumps({k: val for k, val in v.items() if k != "lineas"}, ensure_ascii=False, indent=2))
    else:
        print(render(v))
    return 0 if v["abierta"] else 1


if __name__ == "__main__":
    sys.exit(main())
