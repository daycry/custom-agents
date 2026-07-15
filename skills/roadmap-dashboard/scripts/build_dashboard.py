#!/usr/bin/env python3
"""
roadmap-dashboard - generador
Escanea docs/roadmap/<fecha>-<slug>/ y produce:
  - un dashboard HTML autocontenido (--html RUTA)   -> vista local
  - un dashboard en Markdown (--md RUTA)             -> para publicar en Confluence
  - un resumen JSON de todas las iniciativas (--json)
Sin dependencias externas (solo stdlib). No modifica los ficheros de roadmap.

Uso:
  python build_dashboard.py --root docs/roadmap --html docs/roadmap/dashboard.html
  python build_dashboard.py --root docs/roadmap --md   docs/roadmap/dashboard.md
  python build_dashboard.py --root docs/roadmap --json
"""
import argparse
import datetime
import glob
import html
import json
import os
import re
import sys

# ---- estados y colores ------------------------------------------------------
SPEC_STATES = ["borrador", "aprobada", "implementada", "obsoleta"]
EVAL_STATES = ["borrador", "en-progreso", "en-revision", "completado", "cancelado"]

COLORS = {
    # spec
    "borrador": "#94a3b8", "aprobada": "#22c55e", "implementada": "#0ea5e9",
    "obsoleta": "#64748b",
    # eval / plan
    "en-progreso": "#f59e0b", "en-revision": "#a855f7",
    "completado": "#22c55e", "cancelado": "#ef4444",
    # fallback
    "pendiente": "#64748b", "sin-dato": "#334155",
}
PRIO_COLORS = {"Baja": "#22c55e", "Media": "#eab308", "Alta": "#f97316", "Crítica": "#ef4444"}


def parse_frontmatter(text):
    """Lee un frontmatter YAML sencillo (key: value) al inicio del fichero."""
    m = re.match(r"^\s*---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).splitlines():
        line = line.split("#", 1)[0].rstrip()  # quita comentarios inline
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm


def table_value(text, key):
    """Extrae el valor de una fila markdown tipo | **key** | valor | ... |."""
    for line in text.splitlines():
        if "|" not in line:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2:
            continue
        label = re.sub(r"[*`]", "", cells[0]).strip().lower()
        if label == key.lower():
            val = re.sub(r"[*`]", "", cells[1]).strip()
            return val or None
    return None


def scan(root):
    inits = []
    for path in sorted(glob.glob(os.path.join(root, "*"))):
        if not os.path.isdir(path):
            continue
        name = os.path.basename(path)
        spec_p = os.path.join(path, "spec.md")
        eval_p = os.path.join(path, "evaluation.md")
        plan_p = os.path.join(path, "improvement-plan.md")
        tasks_p = os.path.join(path, "tasks.md")
        testing_p = os.path.join(path, "testing")
        if not (os.path.exists(spec_p) or os.path.exists(eval_p)):
            continue  # no es carpeta de iniciativa

        rec = {
            "slug": name, "path": path,
            "titulo": name, "descripcion": None,
            "spec_estado": None, "eval_estado": None,
            "prioridad": None, "coste": None, "esfuerzo": None,
            "tokens": None, "multiplicador": None, "caracteristicas": None,
            "creado": None, "actualizado": None,
            "has_spec": os.path.exists(spec_p),
            "has_eval": os.path.exists(eval_p),
            "has_plan": os.path.exists(plan_p),
            "has_tasks": os.path.exists(tasks_p),
            "has_testing": os.path.isdir(testing_p),
        }

        if rec["has_spec"]:
            t = open(spec_p, encoding="utf-8", errors="replace").read()
            fm = parse_frontmatter(t)
            rec["spec_estado"] = fm.get("estado")
            rec["descripcion"] = fm.get("descripcion")
            rec["creado"] = fm.get("creado")
            rec["actualizado"] = fm.get("actualizado")
            hm = re.search(r"^#\s+(.+)$", t, re.M)
            if hm:
                rec["titulo"] = hm.group(1).strip()

        if rec["has_eval"]:
            t = open(eval_p, encoding="utf-8", errors="replace").read()
            rec["eval_estado"] = table_value(t, "Estado")
            rec["prioridad"] = table_value(t, "Prioridad global")
            rec["caracteristicas"] = table_value(t, "Características") or \
                table_value(t, "Características evaluadas")
            rec["coste"] = table_value(t, "Coste")
            rec["esfuerzo"] = table_value(t, "Esfuerzo humano")
            rec["tokens"] = table_value(t, "Tokens IA")
            rec["multiplicador"] = table_value(t, "Multiplicador productividad")

        # fase derivada para ordenar/priorizar
        if rec["has_testing"]:
            rec["fase"] = "en pruebas"
        elif rec["has_plan"]:
            rec["fase"] = "planificada"
        elif rec["has_eval"]:
            rec["fase"] = "evaluada"
        else:
            rec["fase"] = "solo spec"
        inits.append(rec)
    return inits


def warnings_for(inits):
    """Avisos no fatales: campos que no se han podido leer (posible desajuste de
    etiquetas entre las plantillas y este parser) e incoherencias de estado."""
    warns = []
    for r in inits:
        s = r["slug"]
        if r["has_eval"]:
            missing = [k for k in ("eval_estado", "coste", "esfuerzo") if not r.get(k)]
            if missing:
                warns.append(f"{s}: evaluation.md presente pero no se leyeron "
                             f"{', '.join(missing)} (¿cambiaron las etiquetas de la tabla?)")
        if r["has_spec"] and not r["spec_estado"]:
            warns.append(f"{s}: spec.md sin 'estado' en el frontmatter")
        if r["spec_estado"] == "aprobada" and r["has_eval"] \
                and r["eval_estado"] not in (None, "completado"):
            warns.append(f"{s}: spec 'aprobada' pero evaluación '{r['eval_estado']}' "
                         f"(se esperaba 'completado')")
        if r["spec_estado"] == "implementada" and not r["has_plan"]:
            warns.append(f"{s}: spec 'implementada' pero sin improvement-plan.md")
    return warns


# ---- HTML (vista local) -----------------------------------------------------
def pill(text, color):
    text = html.escape(str(text))
    return f'<span class="pill" style="--c:{color}">{text}</span>'


def render_html(inits, root):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    by_spec = {}
    for r in inits:
        by_spec[r["spec_estado"] or "sin-dato"] = by_spec.get(r["spec_estado"] or "sin-dato", 0) + 1

    cards = []
    for r in inits:
        se = r["spec_estado"] or "sin-dato"
        ee = r["eval_estado"] or "sin-dato"
        prio = r["prioridad"]
        chips = [pill("spec: " + se, COLORS.get(se, COLORS["sin-dato"]))]
        if r["has_eval"]:
            chips.append(pill("eval: " + ee, COLORS.get(ee, COLORS["sin-dato"])))
        if prio:
            chips.append(pill(prio, PRIO_COLORS.get(prio, "#64748b")))
        chips.append(pill(r["fase"], "#475569"))

        metrics = []
        for label, key in [("Coste", "coste"), ("Esfuerzo", "esfuerzo"),
                            ("Tokens", "tokens"), ("Prod.", "multiplicador"),
                            ("Carac.", "caracteristicas")]:
            if r.get(key):
                metrics.append(
                    f'<div class="m"><span class="mk">{label}</span>'
                    f'<span class="mv">{html.escape(str(r[key]))}</span></div>')

        arts = []
        for label, flag in [("spec", "has_spec"), ("evaluación", "has_eval"),
                            ("plan", "has_plan"), ("tasks", "has_tasks"),
                            ("testing", "has_testing")]:
            cls = "on" if r[flag] else "off"
            arts.append(f'<span class="art {cls}">{label}</span>')

        desc = html.escape(r["descripcion"]) if r["descripcion"] else ""
        cards.append(f"""
      <article class="card">
        <div class="chips">{''.join(chips)}</div>
        <h3>{html.escape(r['titulo'])}</h3>
        <p class="slug">{html.escape(r['slug'])}</p>
        {f'<p class="desc">{desc}</p>' if desc else ''}
        <div class="metrics">{''.join(metrics) if metrics else '<span class="nodata">Sin evaluación aún</span>'}</div>
        <div class="arts">{''.join(arts)}</div>
      </article>""")

    counters = "".join(
        f'<div class="counter"><span class="cn">{n}</span>'
        f'<span class="cl">{pill(st, COLORS.get(st, COLORS["sin-dato"]))}</span></div>'
        for st, n in sorted(by_spec.items(), key=lambda x: -x[1]))

    body = "".join(cards) if cards else \
        '<p class="empty">No hay iniciativas en <code>docs/roadmap/</code> todavía. ' \
        'Crea una con <code>/pm-cycle &lt;objetivo&gt;</code>.</p>'

    return f"""<!doctype html>
<html lang="es"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Roadmap · dashboard</title>
<style>
:root{{color-scheme:dark}}
*{{box-sizing:border-box}}
body{{margin:0;font:15px/1.5 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;
  background:#0b1120;color:#e2e8f0;padding:28px}}
header{{display:flex;flex-wrap:wrap;gap:16px;align-items:baseline;justify-content:space-between;margin-bottom:8px}}
h1{{font-size:22px;margin:0}}
.meta{{color:#94a3b8;font-size:13px}}
.counters{{display:flex;flex-wrap:wrap;gap:14px;margin:18px 0 26px}}
.counter{{display:flex;align-items:center;gap:8px;background:#111c33;border:1px solid #1e293b;
  border-radius:10px;padding:8px 12px}}
.cn{{font-size:20px;font-weight:700}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px}}
.card{{background:#111c33;border:1px solid #1e293b;border-radius:14px;padding:16px 18px}}
.card h3{{margin:10px 0 2px;font-size:16px}}
.slug{{margin:0;color:#64748b;font-size:12px;font-family:ui-monospace,monospace}}
.desc{{color:#cbd5e1;font-size:13px;margin:10px 0}}
.chips{{display:flex;flex-wrap:wrap;gap:6px}}
.pill{{font-size:11px;font-weight:600;padding:2px 9px;border-radius:999px;
  color:#0b1120;background:var(--c);white-space:nowrap}}
.metrics{{display:flex;flex-wrap:wrap;gap:8px 16px;margin:14px 0 12px}}
.m{{display:flex;flex-direction:column}}
.mk{{font-size:10px;text-transform:uppercase;letter-spacing:.05em;color:#64748b}}
.mv{{font-size:14px;font-weight:600}}
.nodata{{color:#64748b;font-size:13px;font-style:italic}}
.arts{{display:flex;flex-wrap:wrap;gap:6px;border-top:1px solid #1e293b;padding-top:12px}}
.art{{font-size:11px;padding:2px 8px;border-radius:6px}}
.art.on{{background:#14342b;color:#4ade80}}
.art.off{{background:#1e293b;color:#475569;text-decoration:line-through}}
.empty{{color:#94a3b8}}
code{{background:#1e293b;padding:1px 6px;border-radius:5px;font-size:.9em}}
footer{{margin-top:28px;color:#475569;font-size:12px}}
</style></head><body>
<header>
  <h1>🗺️ Roadmap — estado de iniciativas</h1>
  <span class="meta">{len(inits)} iniciativa(s) · {html.escape(root)} · generado {now}</span>
</header>
<div class="counters">{counters}</div>
<div class="grid">{body}</div>
<footer>Generado por la skill <code>roadmap-dashboard</code>. Vuelve a ejecutar
<code>/roadmap-status</code> para refrescar. No editar a mano.</footer>
</body></html>"""


# ---- Markdown (para Confluence) --------------------------------------------
def md_cell(val):
    """Valor seguro para una celda de tabla markdown (sin romper con | ni saltos)."""
    if val is None:
        return "—"
    return str(val).replace("|", "/").replace("\n", " ").strip() or "—"


def render_markdown(inits, root):
    """Dashboard en Markdown, apto para publicarse como página de Confluence."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    by_spec = {}
    for r in inits:
        k = r["spec_estado"] or "sin-dato"
        by_spec[k] = by_spec.get(k, 0) + 1

    out = []
    out.append("# 🗺️ Roadmap — estado de iniciativas")
    out.append("")
    out.append(f"> Generado automáticamente el **{now}** · **{len(inits)}** iniciativa(s). "
               "Página de solo lectura; el estado real vive en `docs/roadmap/`. No editar a mano.")
    out.append("")
    if not inits:
        out.append("_No hay iniciativas en el roadmap todavía._")
        out.append("")
        return "\n".join(out)

    reparto = " · ".join(f"{n} {st}" for st, n in sorted(by_spec.items(), key=lambda x: -x[1]))
    out.append(f"**Reparto por estado (spec):** {reparto}")
    out.append("")
    out.append("## Iniciativas")
    out.append("")
    out.append("| Iniciativa | Spec | Evaluación | Prioridad | Fase | Coste | Esfuerzo | Tokens | Prod. |")
    out.append("|---|---|---|---|---|---|---|---|---|")
    for r in inits:
        out.append("| " + " | ".join(md_cell(x) for x in [
            f"{r['titulo']} (`{r['slug']}`)",
            r["spec_estado"], r["eval_estado"] if r["has_eval"] else "—",
            r["prioridad"], r["fase"], r["coste"], r["esfuerzo"],
            r["tokens"], r["multiplicador"],
        ]) + " |")
    out.append("")
    out.append("## Artefactos por iniciativa")
    out.append("")
    out.append("| Iniciativa | spec | evaluación | plan | tasks | testing |")
    out.append("|---|---|---|---|---|---|")
    mark = lambda b: "✅" if b else "—"
    for r in inits:
        out.append("| " + " | ".join([
            md_cell(r["slug"]), mark(r["has_spec"]), mark(r["has_eval"]),
            mark(r["has_plan"]), mark(r["has_tasks"]), mark(r["has_testing"]),
        ]) + " |")
    out.append("")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="docs/roadmap")
    ap.add_argument("--html", help="ruta de salida del HTML (vista local)")
    ap.add_argument("--md", help="ruta de salida del Markdown (para Confluence)")
    ap.add_argument("--json", action="store_true", help="volcar JSON a stdout")
    ap.add_argument("--strict", action="store_true",
                    help="salir con código 1 si hay avisos (para CI)")
    args = ap.parse_args()

    if not os.path.isdir(args.root):
        print(f"[roadmap-dashboard] no existe {args.root}", file=sys.stderr)
        sys.exit(2)

    inits = scan(args.root)
    warns = warnings_for(inits)
    for w in warns:
        print(f"[roadmap-dashboard][aviso] {w}", file=sys.stderr)

    if args.json:
        print(json.dumps(inits, ensure_ascii=False, indent=2))
    if args.html:
        os.makedirs(os.path.dirname(os.path.abspath(args.html)), exist_ok=True)
        with open(args.html, "w", encoding="utf-8") as f:
            f.write(render_html(inits, args.root))
        print(f"[roadmap-dashboard] HTML: {len(inits)} iniciativa(s) -> {args.html}")
    if args.md:
        os.makedirs(os.path.dirname(os.path.abspath(args.md)), exist_ok=True)
        with open(args.md, "w", encoding="utf-8") as f:
            f.write(render_markdown(inits, args.root))
        print(f"[roadmap-dashboard] MD: {len(inits)} iniciativa(s) -> {args.md}")
    if not any([args.html, args.md, args.json]):
        print(f"[roadmap-dashboard] {len(inits)} iniciativa(s) encontradas")

    if args.strict and warns:
        sys.exit(1)


if __name__ == "__main__":
    main()
