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

# Consola Windows (cp1252) o tuberías: reconfigurar ANTES de leer o imprimir nada (GOT-005).
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure, ya leído o None (capsys, pythonw)

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
    """Formato puro de horas; resumir un ledger no carga el meter ni su estado."""
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


def resumir(path, *, text=None):
    """Resume un ledger; con texto suministrado no accede al sistema de archivos."""
    if text is None:
        try:
            with open(path, encoding="utf-8-sig", errors="replace") as source:
                text = source.read()   # tolera BOM para los consumidores históricos
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
                             capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10, check=False)
        data = json.loads(res.stdout or "{}")
        return [m.get("artefacto", "?") for m in data.get("marcadores", []) if not m.get("cerrado")]
    except Exception:  # noqa: BLE001 — cualquier fallo del meter = no disponible
        return None


# ------------------------------------------------------------------ retoma dirigida, solo lectura

_RESUME_SCAN = 128
_RESUME_BYTES = 1024 * 1024
_HISTORY_FIELDS = ("entry", "fecha", "session_id", "runtime", "iniciativa", "resumen",
                   "fuente", "cierre", "resumen_por", "decisiones", "pendientes",
                   "ficheros_tocados", "tareas_cambiadas", "marcadores_cerrados",
                   "materializado_en", "derivados_en", "output_truncated", "identity_resolvable")


def _initiative_name(value):
    return (isinstance(value, str) and bool(value) and value not in (".", "..")
            and not any(c in value for c in "/\\:\x00"))


def _resume_result(status, *, ledger=None, history=None, candidates=None, issues=None):
    return {"status": status, "ledger": ledger, "history": history or [],
            "candidates": candidates or [], "issues": issues or [], "output_truncated": False}


def _public_resume(result, journal):
    """Proyección pública con vocabulario fijo y presupuesto independiente de la entrada."""
    truncated = False
    def clean(value, limit=160):
        nonlocal truncated
        if isinstance(value, str):
            projected = journal.public_text(value, limit=limit)
            truncated |= projected != value
            return projected
        if isinstance(value, list):
            if len(value) > 4:
                truncated = True
            return [clean(item, limit) for item in value[:4]]
        if isinstance(value, dict):
            return {key: clean(item, limit) for key, item in value.items()}
        return value
    ledger = result.get("ledger")
    if ledger:
        ledger = dict(ledger)
        truncated |= len(ledger["en_progreso"]) > 4
        ledger["en_progreso"] = ledger["en_progreso"][:4]
        result["ledger"] = clean(ledger)
    entries = result["history"]
    truncated |= len(entries) > 2 or any(entry.get("output_truncated") for entry in entries)
    result["history"] = []
    for entry in entries[:2]:
        visible = {k: entry[k] for k in _HISTORY_FIELDS if k in entry}
        projected = clean(visible, 120)
        projected['output_truncated'] = bool(entry.get('output_truncated') or projected != visible)
        projected['identity_resolvable'] = bool(entry.get('identity_resolvable') and
            all(projected.get(k) == entry.get(k) for k in ('entry', 'session_id', 'iniciativa')))
        truncated |= projected['output_truncated']
        result['history'].append(projected)
    for field in ("candidates", "issues"):
        values = result[field]
        truncated |= len(values) > 16
        result[field] = [clean(value, 100) for value in values[:16]]
    result["output_truncated"] = truncated
    # Escaped strings and multibyte text consume more JSON bytes than characters.
    # If the projection still exceeds its budget, retain the current ledger and
    # report that historical detail and candidate labels were omitted.
    if len(json.dumps(result, ensure_ascii=False).encode("utf-8")) > 12000:
        result["history"] = []
        result["candidates"] = result["candidates"][:4]
        result["issues"] = [{"status": "output_budget"}]
        result["output_truncated"] = True
    return result


def _resume_ledger(root, initiative, reader):
    """Resuelve carpeta exacta o slug único sin elegir dentro de un scan incompleto."""
    def read(folder, *, max_bytes=256 * 1024):
        relative = "docs/roadmap/" + folder + "/tasks.md"
        result = reader.read_text(root, relative, max_bytes=max_bytes)
        if result["status"] != "ok":
            return result["status"], None, result.get("bytes", 0)
        try:
            summary = resumir(relative, text=result["text"])
        except (ValueError, TypeError, KeyError, OverflowError):
            return "malformed", None, result["bytes"]
        return "ok", summary, result["bytes"]

    # An exact dated folder is independent of unrelated ledger failures.
    if initiative is not None and re.match(r"^\d{4}-\d{2}-\d{2}-.+", initiative):
        status, summary, _ = read(initiative)
        return status, summary, [], [] if status == "ok" else [{"entry": initiative, "status": status}]
    listing = reader.list_names(root, "docs/roadmap", max_entries=_RESUME_SCAN)
    if listing["status"] != "ok" or not listing["complete"]:
        status = "incomplete" if listing["status"] == "incomplete" else listing["status"]
        return status, None, [], [{"status": status, "scope": "roadmap"}]
    matches, issues = [], []
    remaining = _RESUME_BYTES
    for folder in listing["names"]:
        if not _initiative_name(folder):
            issues.append({"entry": folder, "status": "invalid_path"})
            continue
        if remaining <= 0:
            issues.append({"status": "scan_budget"})
            break
        status, summary, size = read(folder, max_bytes=min(256 * 1024, remaining))
        remaining -= size
        if status in ("not_found", "not_regular"):
            continue  # This roadmap entry has no ledger.
        if status != "ok":
            issues.append({"entry": folder, "status": status})
            continue
        matches_selection = (summary["slug"] == initiative if initiative is not None
                             else summary["estado"] == "en-progreso")
        if matches_selection:
            matches.append((folder, summary))
    candidates = [folder for folder, _ in matches]
    if issues:
        return "incomplete", None, candidates, issues
    if len(matches) > 1:
        return "ambiguous", None, candidates, []
    if not matches:
        return "not_found", None, [], [{"scope": "roadmap", "status": "no_matching_ledger"}]
    return "ok", matches[0][1], [], []


def resume(root, *, initiative=None, session_id=None, runtime=None, entry=None):
    """Compose current ledger and quoted history without usage state or subprocesses.

    Explicit selections never fall back to a different initiative or journal entry.
    Historical claims remain evidence from their recorded session, not current QA.
    """
    try:
        journal = _load_module("resume_journal", "journal.py")
        reader = _load_module("resume_local_read", "local-read.py")
    except (ImportError, OSError, SyntaxError):
        return _resume_result('reader_unavailable', issues=[{'status': 'incomplete_bundle'}])
    def finish(status, **kwargs):
        return _public_resume(_resume_result(status, **kwargs), journal)
    if initiative is not None and (not _initiative_name(initiative)
                                  or journal.public_text(initiative, limit=4096) != initiative):
        return finish("invalid_selection", issues=[{"status": "invalid_initiative"}])
    selected_history = None
    if initiative is None and (session_id is not None or entry is not None):
        selected_history = journal.select_entries(root, initiative=initiative, session_id=session_id,
                                                  runtime=runtime, entry=entry)
        if selected_history["status"] != "ok" or not selected_history["complete"]:
            return finish(selected_history["status"], candidates=selected_history["candidates"],
                          issues=selected_history["issues"])
        if initiative is None:
            if any(e.get("identity_resolvable") is False
                   or ("identity_resolvable" not in e and e.get("output_truncated"))
                   for e in selected_history["entries"]):
                return finish("initiative_unknown", history=selected_history["entries"],
                              issues=[{"status": "historical_identity_truncated"}])
            names = {e.get("iniciativa") for e in selected_history["entries"] if e.get("iniciativa")}
            if len(names) != 1:
                return finish("initiative_unknown" if not names else "ambiguous",
                              history=selected_history["entries"], candidates=sorted(names),
                              issues=[{"status": "history_does_not_identify_one_initiative"}])
            initiative = next(iter(names))
            if not _initiative_name(initiative):
                return finish("invalid_selection", issues=[{"status": "invalid_historical_initiative"}])
    status, summary, candidates, issues = _resume_ledger(root, initiative, reader)
    if summary is None:
        return finish(status, candidates=candidates, issues=issues,
                      history=selected_history["entries"] if selected_history else None)
    selected_history = selected_history or journal.select_entries(root, initiative=summary["slug"],
                                                                  session_id=session_id, runtime=runtime, entry=entry)
    history_status = selected_history["status"]
    issues.extend(selected_history["issues"])
    history_absent = history_status in ("empty", "not_found")
    if history_absent:
        issues.append({"scope": "history", "status": history_status})
        if session_id is None and entry is None:
            # A ledger remains useful without history. An explicitly requested
            # session or file that is missing retains its failure status.
            history_status = "ok"
    if not selected_history["complete"] and history_status == "ok" and not history_absent:
        history_status = "incomplete"
    return finish(history_status, ledger=summary, history=selected_history["entries"],
                  candidates=selected_history["candidates"], issues=issues)


def resume_text(result):
    """Compact rendering; journal text is explicitly quoted as historical evidence."""
    out = ["Retoma dirigida · estado: " + result["status"]]
    summary = result.get("ledger")
    if summary:
        out.extend(["Ledger vigente: " + summary["path"], linea(summary)])
        for task in summary["en_progreso"]:
            out.append("En progreso: " + task["id"] + " " + task["titulo"])
    if result["candidates"]:
        references = [value.get("entry", "?") if isinstance(value, dict) else str(value)
                      for value in result["candidates"]]
        out.append("Selecciona una referencia exacta: " + ", ".join(references))
    for entry in result["history"]:
        out.append("Historial citado (no acredita QA vigente): " + entry.get("entry", "?")
                   + " · " + entry.get("fecha", "?") + " · sesión " + entry.get("session_id", "?"))
        for field in ("runtime", "fuente", "resumen", "cierre", "decisiones", "pendientes"):
            if entry.get(field):
                value = entry[field]
                out.append("> " + field + ": " + ("; ".join(value) if isinstance(value, list) else str(value)))
    for issue in result["issues"]:
        out.append("Aviso: " + (issue.get("status", "unknown") if isinstance(issue, dict) else str(issue)))
    if result["output_truncated"]:
        out.append("Salida resumida: detalles omitidos por el presupuesto de presentación.")
    text = "\n".join(out[:31])
    if len(out) > 31 or len(text) > 5950:
        text = text[:5950] + "\nSalida truncada por el presupuesto de presentación."
    return text


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
    rel = rel.replace("\\", "/")
    out.append(f"Ledger canónico: {rel} — retoma desde la tarea en-progreso")
    print("\n".join(out[:15]))
    return 0


def cmd_resume(args):
    result = resume(args.root, initiative=args.initiative, session_id=args.session_id,
                    runtime=args.runtime, entry=args.entry)
    if args.history_only:
        if result["status"] == "ok" and not result["history"]:
            return 0
        journal = _load_module("resume_render_journal", "journal.py")
        print(journal.selected_text({"status": result["status"], "entries": result["history"]}))
    else:
        print(json.dumps(result, ensure_ascii=False) if args.json else resume_text(result))
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

    sp = sub.add_parser("resume", help="retoma dirigida, de solo lectura, desde ledger e historial")
    sp.add_argument("--root", default=".")
    sp.add_argument("--initiative")
    sp.add_argument("--session-id")
    sp.add_argument("--runtime")
    sp.add_argument("--entry")
    output = sp.add_mutually_exclusive_group()
    output.add_argument("--json", action="store_true")
    output.add_argument("--history-only", action="store_true", help="solo contexto histórico acotado")
    sp.set_defaults(fn=cmd_resume)

    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
