#!/usr/bin/env python3
"""
journal.py — memoria EPISÓDICA de sesión, determinista y sin MCP (agent-kits/shared).

Una entrada por sesión en `docs/knowledge/journal/AAAA-MM-DD-<slug>.md` (bitácora cronológica,
NO curada — a diferencia de `adr/`, `gotchas/` y `lessons/`, que son memoria curada con umbral;
ver `knowledge-write.md`). La escribe el hook `hooks/session-journal.sh` (SessionEnd) y la
reinyecta `hooks/session-context.sh` (SessionStart `startup|resume`, no `compact`).

Subcomandos (exit 0 SIEMPRE salvo error de uso → 2; la bitácora nunca bloquea):
  draft  [--root DIR] [--session-id ID] [--transcript FICHERO] [--reason R] [--enrich JSON]
      Borrador de la entrada SIN modelo, en JSON:
        fecha · session_id · reason · iniciativa (primera `en-progreso` del roadmap, vía
        progress-report.py active) · resumen (primer prompt del usuario de la transcripción si
        es legible — formato JSONL NO oficial, best-effort — o «Sesión sobre <iniciativa>») ·
        decisiones/pendientes (vacías salvo --enrich) · ficheros_tocados (top 10 de
        `git status --porcelain` + `git diff --name-only HEAD`) · tareas_cambiadas (tareas
        cuyo `- **Estado**:` difiere entre el tasks.md de trabajo y `git show HEAD:…`) ·
        marcadores_cerrados (usage-state.json con `ultimoCierre` de hoy) · avisos.
      Sin git → listas vacías + aviso. Sin roadmap → iniciativa "n/a".
  write  [--root DIR] --session-id ID [--reason R] [--fuente hook|manual] [--enrich JSON] [--draft JSON]
      Escribe la entrada SOLO si el proyecto tiene rastro del plugin (existe `docs/roadmap/`,
      `docs/knowledge/` o `.claude/dev.json`); en cualquier otro repo sale en silencio (exit 0, sin
      stdout) para no sembrar carpetas donde nadie usa el plugin (T-fix1). IDEMPOTENTE por
      session_id: si ya hay una entrada con ese id la ACTUALIZA en sitio (mismo fichero); si no,
      crea `AAAA-MM-DD-<slug>.md` — slug = iniciativa activa, o `sesion` si no hay ninguna — (sufijo
      -2, -3 si el nombre ya existe con otra sesión). Regenera el índice `journal/README.md`.
      Imprime la ruta. Las entradas SE VERSIONAN (memoria del proyecto, como ADR/lecciones); quien
      no quiera, añade `docs/knowledge/journal/*.md` (no el README) a su `.gitignore`.
  latest [--root DIR] [--n 2] [--max-lines 25]
      Bloque compacto para el contexto de sesión: la ÚLTIMA entrada o las N últimas si son de
      días distintos; recortado a --max-lines. Sin carpeta/entradas → sin salida.
  index  [--root DIR]
      Regenera `docs/knowledge/journal/README.md` (tabla fecha · iniciativa · resumen · fuente).

`--enrich JSON` (fichero o `-` para stdin): {"resumen": "...", "decisiones": [...], "pendientes": [...]}
— hoy solo manual: la doc oficial (hooks.md, 2026-09-03) no permite que un hook `prompt`/`agent`
en SessionEnd devuelva texto (solo decisión `ok/reason`, y en SessionEnd la salida se ignora).
"""
import argparse
import datetime as _dt
import importlib.util
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
JOURNAL_REL = os.path.join("docs", "knowledge", "journal")
TOP_FICHEROS = 10
GIT_TIMEOUT = 5
LISTAS = ("decisiones", "pendientes", "ficheros_tocados", "tareas_cambiadas", "marcadores_cerrados")
_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _load_module(name, filename):
    path = os.path.join(HERE, filename)
    if not os.path.isfile(path):
        return None
    try:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    except Exception:  # noqa: BLE001 — degradación: sin el módulo, sin esa medida
        return None


def hoy():
    return _dt.date.today().isoformat()


def slugify(s):
    """Slug del nombre de fichero: la iniciativa activa; sin iniciativa (`n/a`, vacío) → `sesion`."""
    if not s or s.strip().lower() in ("n/a", "na", "n-a"):
        return "sesion"
    s = _SLUG_RE.sub("-", s.lower()).strip("-")
    return s or "sesion"


def proyecto_con_plugin(root):
    """¿Hay rastro del plugin en el proyecto? Solo entonces se escribe la bitácora (T-fix1)."""
    return any(os.path.exists(os.path.join(root, *p)) for p in
               (("docs", "roadmap"), ("docs", "knowledge"), (".claude", "dev.json")))


# ------------------------------------------------------------------ git

def _git(root, *args):
    """stdout de git o None si git no está / no es repo / falla (nunca lanza)."""
    try:
        r = subprocess.run(["git", "-C", root, *args], capture_output=True, text=True,
                           timeout=GIT_TIMEOUT, check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode != 0:
        return None
    return r.stdout


def _es_journal(path):
    return path.replace("\\", "/").lstrip("./").startswith(JOURNAL_REL.replace(os.sep, "/") + "/")


def ficheros_tocados(root, avisos):
    """Top N de ficheros con cambios (sin comitear: status; + diff vs HEAD), con su marca."""
    status = _git(root, "status", "--porcelain", "--untracked-files=all")
    if status is None:
        avisos.append("git no disponible o no es un repositorio: sin ficheros tocados")
        return []
    vistos, out = set(), []
    for line in status.splitlines():
        if len(line) < 4:
            continue
        marca, path = line[:2].strip() or "M", line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if _es_journal(path):            # la propia bitácora no cuenta como trabajo de la sesión
            continue
        if path and path not in vistos:
            vistos.add(path)
            out.append({"path": path, "cambio": marca})
    diff = _git(root, "diff", "--name-only", "HEAD") or ""
    for path in diff.splitlines():
        path = path.strip()
        if path and path not in vistos and not _es_journal(path):
            vistos.add(path)
            out.append({"path": path, "cambio": "M"})
    return out[:TOP_FICHEROS]


def tareas_cambiadas(root, avisos):
    """Tareas cuyo estado difiere entre el tasks.md de trabajo y HEAD, para cada ledger
    modificado del roadmap (`T-01: borrador → en-progreso`). Reutiliza parse_ledger."""
    ll = _load_module("ledger_lint", "ledger-lint.py")
    if ll is None:
        avisos.append("ledger-lint.py no está junto a journal.py: sin tareas cambiadas")
        return []
    status = _git(root, "status", "--porcelain")
    if status is None:
        return []
    out = []
    for line in status.splitlines():
        path = line[3:].strip()
        if not re.search(r"docs/roadmap/[^/]+/tasks\.md$", path.replace("\\", "/")):
            continue
        marca = line[:2].strip()
        antes = _git(root, "show", f"HEAD:{path}") if "?" not in marca else ""
        try:
            ahora = open(os.path.join(root, path), encoding="utf-8-sig", errors="replace").read()
        except OSError:
            continue
        try:
            t_antes = {t["id"]: t["estado"] for t in ll.parse_ledger(antes or "")["tareas"]}
            t_ahora = ll.parse_ledger(ahora)["tareas"]
        except Exception:  # noqa: BLE001 — ledger ilegible: no es motivo para fallar
            continue
        slug = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", path.replace("\\", "/").split("/")[-2])
        for t in t_ahora:
            prev = t_antes.get(t["id"])
            if t["estado"] and prev != t["estado"]:
                out.append({"iniciativa": slug, "id": t["id"], "titulo": t["titulo"],
                            "antes": prev or "—", "ahora": t["estado"]})
    return out


# ------------------------------------------------------------------ roadmap / meter / transcripción

def iniciativa_activa(root):
    pr = _load_module("progress_report", "progress-report.py")
    roadmap = os.path.join(root, "docs", "roadmap")
    if pr is None or not os.path.isdir(roadmap):
        return None
    try:
        import contextlib
        import io
        with contextlib.redirect_stderr(io.StringIO()):
            rs = pr.activas(roadmap)
    except Exception:  # noqa: BLE001
        return None
    return rs[0]["slug"] if rs else None


def marcadores_cerrados(root, fecha):
    state = os.path.join(root, ".claude", "usage-state.json")
    try:
        data = json.load(open(state, encoding="utf-8"))
    except (OSError, ValueError):
        return []
    if not isinstance(data, dict):
        return []
    return sorted(k for k, m in data.items()
                  if isinstance(m, dict) and str(m.get("ultimoCierre", "")).startswith(fecha))


def primer_prompt(transcript, max_chars=160):
    """Primer mensaje de usuario de la transcripción JSONL (formato no oficial: best-effort).
    Ignora mensajes de sistema/meta y los que empiezan por '<' (recordatorios, comandos)."""
    if not transcript or not os.path.isfile(transcript):
        return None
    try:
        with open(transcript, encoding="utf-8", errors="replace") as fh:
            for raw in fh:
                try:
                    rec = json.loads(raw)
                except ValueError:
                    continue
                if not isinstance(rec, dict) or rec.get("type") != "user" or rec.get("isMeta"):
                    continue
                msg = rec.get("message") or {}
                content = msg.get("content") if isinstance(msg, dict) else None
                if isinstance(content, list):
                    content = " ".join(b.get("text", "") for b in content
                                       if isinstance(b, dict) and b.get("type") == "text")
                if not isinstance(content, str):
                    continue
                texto = " ".join(content.split())
                if not texto or texto.startswith("<"):
                    continue
                return texto if len(texto) <= max_chars else texto[:max_chars - 1].rstrip() + "…"
    except OSError:
        return None
    return None


def cargar_enrich(spec, avisos):
    if not spec:
        return {}
    try:
        data = json.load(sys.stdin) if spec == "-" else json.load(open(spec, encoding="utf-8"))
    except (OSError, ValueError) as e:
        avisos.append(f"--enrich ilegible ({e}); se ignora")
        return {}
    return data if isinstance(data, dict) else {}


def _lista(v):
    if isinstance(v, str):
        return [v] if v.strip() else []
    return [str(x) for x in v] if isinstance(v, list) else []


def draft(root, session_id=None, transcript=None, reason=None, enrich=None):
    avisos = []
    fecha = hoy()
    iniciativa = iniciativa_activa(root) or "n/a"
    enr = cargar_enrich(enrich, avisos)
    resumen = enr.get("resumen") or primer_prompt(transcript) or f"Sesión sobre {iniciativa}"
    return {
        "fecha": fecha,
        "session_id": session_id or "manual",
        "reason": reason or "manual",
        "iniciativa": iniciativa,
        "resumen": str(resumen),
        "decisiones": _lista(enr.get("decisiones")),
        "pendientes": _lista(enr.get("pendientes")),
        "ficheros_tocados": ficheros_tocados(root, avisos),
        "tareas_cambiadas": tareas_cambiadas(root, avisos),
        "marcadores_cerrados": marcadores_cerrados(root, fecha),
        "avisos": avisos,
    }


# ------------------------------------------------------------------ fichero de entrada

def _yaml_str(s):
    return json.dumps(str(s), ensure_ascii=False)


def render(e, fuente):
    fm = [f"fecha: {e['fecha']}", f"session_id: {_yaml_str(e['session_id'])}",
          f"reason: {e.get('reason') or 'manual'}", f"iniciativa: {e['iniciativa']}",
          f"resumen: {_yaml_str(e['resumen'])}", f"fuente: {fuente}"]
    for k in ("decisiones", "pendientes"):
        fm.append(f"{k}:" + ("" if e[k] else " []"))
        fm += [f"  - {_yaml_str(x)}" for x in e[k]]
    fm.append("ficheros_tocados:" + ("" if e["ficheros_tocados"] else " []"))
    fm += [f"  - {_yaml_str(f['path'] + ' (' + f['cambio'] + ')')}" for f in e["ficheros_tocados"]]
    fm.append("tareas_cambiadas:" + ("" if e["tareas_cambiadas"] else " []"))
    fm += [f"  - {_yaml_str(t['iniciativa'] + ' ' + t['id'] + ': ' + t['antes'] + ' → ' + t['ahora'])}"
           for t in e["tareas_cambiadas"]]
    fm.append("marcadores_cerrados:" + ("" if e["marcadores_cerrados"] else " []"))
    fm += [f"  - {_yaml_str(m)}" for m in e["marcadores_cerrados"]]

    body = [f"# Journal — {e['fecha']} — {e['iniciativa']}", "",
            "> Entrada de **bitácora de sesión** (memoria episódica, cronológica, no curada; "
            "`agent-kits/shared/journal.py`). Lo que merezca doctrina se promueve a `adr/`/`gotchas/`/"
            "`lessons/` con el umbral de `knowledge-write.md`; esto NO se publica en Confluence.", "",
            "## Resumen", "", e["resumen"], ""]

    def seccion(titulo, items, vacio):
        body.extend([f"## {titulo}", ""])
        body.extend([f"- {x}" for x in items] if items else [f"_{vacio}_"])
        body.append("")

    seccion("Decisiones", e["decisiones"], "sin decisiones registradas (borrador determinista)")
    seccion("Pendientes", e["pendientes"], "sin pendientes registrados")
    seccion(f"Ficheros tocados (top {TOP_FICHEROS})",
            [f"`{f['path']}` ({f['cambio']})" for f in e["ficheros_tocados"]], "sin cambios detectados")
    seccion("Tareas que cambiaron de estado",
            [f"`{t['iniciativa']}` {t['id']} {t['titulo']}: {t['antes']} → {t['ahora']}".replace("  ", " ")
             for t in e["tareas_cambiadas"]], "ninguna")
    seccion("Marcadores de coste cerrados (usage-meter)",
            [f"`{m}`" for m in e["marcadores_cerrados"]], "ninguno")
    if e.get("avisos"):
        seccion("Avisos", e["avisos"], "")
    return "---\n" + "\n".join(fm) + "\n---\n\n" + "\n".join(body).rstrip() + "\n"


def parse_entry(path):
    """Frontmatter mínimo de una entrada → dict (escalares + listas). None si no es entrada."""
    try:
        text = open(path, encoding="utf-8-sig", errors="replace").read()
    except OSError:
        return None
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    out, cur = {"_path": path}, None
    for raw in text[3:end].splitlines():
        if not raw.strip():
            continue
        if raw.startswith("  - ") and cur:
            out.setdefault(cur, []).append(_unquote(raw[4:].strip()))
            continue
        if ":" not in raw or raw.startswith(" "):
            continue
        k, v = raw.split(":", 1)
        k, v = k.strip(), v.strip()
        if v == "" or v == "[]":
            out[k], cur = [], k
        else:
            out[k], cur = _unquote(v), None
    if "fecha" not in out or "session_id" not in out:
        return None
    return out


def _unquote(v):
    if len(v) >= 2 and v[0] == '"' and v[-1] == '"':
        try:
            return json.loads(v)
        except ValueError:
            return v[1:-1]
    return v


def journal_dir(root):
    return os.path.join(root, JOURNAL_REL)


def entradas(root):
    """Entradas ordenadas por (fecha, mtime): la última es la más reciente."""
    d = journal_dir(root)
    if not os.path.isdir(d):
        return []
    out = []
    for fn in os.listdir(d):
        if not fn.endswith(".md") or fn == "README.md":
            continue
        p = os.path.join(d, fn)
        e = parse_entry(p)
        if e:
            try:
                e["_mtime"] = os.stat(p).st_mtime
            except OSError:
                e["_mtime"] = 0
            out.append(e)
    out.sort(key=lambda e: (str(e.get("fecha")), e["_mtime"], e["_path"]))
    return out


def write(root, e, fuente="hook"):
    """Escribe/actualiza la entrada; None (sin tocar disco) si el proyecto no tiene rastro del plugin."""
    if not proyecto_con_plugin(root):
        return None
    d = journal_dir(root)
    os.makedirs(d, exist_ok=True)
    destino = None
    for prev in entradas(root):
        if prev.get("session_id") == e["session_id"]:
            destino = prev["_path"]
            break
    if destino is None:
        base = f"{e['fecha']}-{slugify(e['iniciativa'])}"
        destino = os.path.join(d, base + ".md")
        n = 2
        while os.path.exists(destino):
            destino = os.path.join(d, f"{base}-{n}.md")
            n += 1
    with open(destino, "w", encoding="utf-8") as fh:
        fh.write(render(e, fuente))
    index(root)
    return destino


# ------------------------------------------------------------------ índice y latest

def index(root):
    d = journal_dir(root)
    if not os.path.isdir(d):
        return None
    es = entradas(root)
    lines = ["# `docs/knowledge/journal/` — bitácora de sesión (memoria episódica)", "",
             "Una entrada por sesión, **generada** por `agent-kits/shared/journal.py` (hook `SessionEnd`; la",
             "última se reinyecta al arrancar/retomar). Cronológica y **no curada**: lo que merezca doctrina",
             "se promueve a `adr/`, `gotchas/` o `lessons/` con el umbral de `knowledge-write.md`. **Excluida de",
             "Confluence** (`docs/knowledge/journal/**`). Nombre: `AAAA-MM-DD-<iniciativa activa | sesion>.md` (sufijo `-2`",
             "si otra sesión del día ya lo usó). **Las entradas se versionan** (memoria del proyecto, como ADR y lecciones);",
             "quien no quiera versionarlas añade `docs/knowledge/journal/*.md` (no este README) a su `.gitignore`.",
             "Este índice lo regenera `journal.py index`; no lo edites.", "",
             "| Fecha | Iniciativa | Resumen | Fuente |", "|---|---|---|---|"]
    for e in reversed(es):
        fn = os.path.basename(e["_path"])
        resumen = str(e.get("resumen", "")).replace("|", "\\|")
        if len(resumen) > 100:
            resumen = resumen[:99].rstrip() + "…"
        lines.append(f"| [{e['fecha']}]({fn}) | {e.get('iniciativa', 'n/a')} | {resumen} | {e.get('fuente', '?')} |")
    if not es:
        lines.append("| — | — | _sin entradas todavía_ | — |")
    p = os.path.join(d, "README.md")
    with open(p, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return p


def _corta(items, n=3):
    items = [str(x) for x in items]
    if len(items) <= n:
        return "; ".join(items)
    return "; ".join(items[:n]) + f" (+{len(items) - n})"


def latest(root, n=2, max_lines=25):
    es = entradas(root)
    if not es:
        return ""
    sel = [es[-1]]
    for prev in reversed(es[:-1]):
        if len(sel) >= n:
            break
        if prev.get("fecha") != sel[-1].get("fecha"):
            sel.append(prev)
    out = [f"Journal de sesión (docs/knowledge/journal/ — memoria episódica; {len(sel)} última(s) entrada(s)):"]
    for e in sel:
        out.append(f"- {e['fecha']} · {e.get('iniciativa', 'n/a')} · {e.get('resumen', '')} · fuente: {e.get('fuente', '?')}")
        if e.get("decisiones"):
            out.append(f"  decisiones: {_corta(e['decisiones'])}")
        if e.get("pendientes"):
            out.append(f"  pendientes: {_corta(e['pendientes'])}")
        if e.get("tareas_cambiadas"):
            out.append(f"  tareas: {_corta(e['tareas_cambiadas'], 4)}")
        if e.get("ficheros_tocados"):
            out.append(f"  tocados: {_corta([f.split(' (')[0] for f in e['ficheros_tocados']], 5)}")
    if len(out) > max_lines:
        out = out[:max_lines - 1] + ["  …"]
    return "\n".join(out)


# ------------------------------------------------------------------ CLI

def cmd_draft(a):
    print(json.dumps(draft(a.root, a.session_id, a.transcript, a.reason, a.enrich), ensure_ascii=False, indent=2))
    return 0


def cmd_write(a):
    if a.draft:
        try:
            e = json.load(sys.stdin) if a.draft == "-" else json.load(open(a.draft, encoding="utf-8"))
        except (OSError, ValueError) as err:
            print(f"journal: --draft ilegible: {err}", file=sys.stderr)
            return 2
        for k in LISTAS:
            e.setdefault(k, [])
        e.setdefault("avisos", [])
        e["session_id"] = a.session_id or e.get("session_id") or "manual"
    else:
        e = draft(a.root, a.session_id, a.transcript, a.reason, a.enrich)
    if a.reason:
        e["reason"] = a.reason
    p = write(a.root, e, a.fuente)
    if p is None:                       # sin rastro del plugin: silencio (exit 0, sin stdout)
        return 0
    print(os.path.relpath(p, a.root))
    return 0


def cmd_latest(a):
    t = latest(a.root, a.n, a.max_lines)
    if t:
        print(t)
    return 0


def cmd_index(a):
    p = index(a.root)
    if p:
        print(os.path.relpath(p, a.root))
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[1].strip())
    sub = p.add_subparsers(dest="cmd", required=True)

    def comunes(sp):
        sp.add_argument("--root", default=os.environ.get("CLAUDE_PROJECT_DIR") or ".")

    sp = sub.add_parser("draft", help="borrador determinista (JSON)")
    comunes(sp)
    sp.add_argument("--session-id")
    sp.add_argument("--transcript")
    sp.add_argument("--reason")
    sp.add_argument("--enrich", help="JSON con resumen/decisiones/pendientes (fichero o -)")
    sp.set_defaults(fn=cmd_draft)

    sp = sub.add_parser("write", help="escribe/actualiza la entrada de la sesión")
    comunes(sp)
    sp.add_argument("--session-id", required=True)
    sp.add_argument("--transcript")
    sp.add_argument("--reason")
    sp.add_argument("--fuente", choices=("hook", "manual"), default="hook")
    sp.add_argument("--enrich")
    sp.add_argument("--draft", help="usar este JSON (de `draft`) en vez de recalcular")
    sp.set_defaults(fn=cmd_write)

    sp = sub.add_parser("latest", help="bloque compacto de la(s) última(s) entrada(s)")
    comunes(sp)
    sp.add_argument("--n", type=int, default=2)
    sp.add_argument("--max-lines", type=int, default=25)
    sp.set_defaults(fn=cmd_latest)

    sp = sub.add_parser("index", help="regenera journal/README.md")
    comunes(sp)
    sp.set_defaults(fn=cmd_index)

    a = p.parse_args(argv)
    try:
        return a.fn(a)
    except Exception as e:  # noqa: BLE001 — la bitácora nunca bloquea una sesión
        print(f"journal: {e}", file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main())
