#!/usr/bin/env python3
"""
scope-check.py — comprobación DETERMINISTA de alcance del diff de una iniciativa.

(Iniciativa deterministic-guardrails: sustituye el check manual «git status / git diff --stat
solo dentro del alcance» del DoD del implementer y se ejecuta en /dev-cycle Fase 3 ANTES de
lanzar las dos lentes de revisión — un fichero fuera de alcance vuelve al implementer como gap
Important sin gastar revisores.)

Qué hace:
  1. Ficheros cambiados = `git diff --name-only <base> HEAD` ∪ `git status --porcelain`
     (comiteado + staged + sin comitear + sin seguimiento).
     base: `--base <ref>`; si no, merge-base con `main`/`master` (el que exista); si la rama
     actual ES la principal, base = HEAD (solo cambios sin comitear); si nada de eso → exit 2
     con mensaje (hay que pasar `--base`).
  2. Alcance declarado = campos `- **Archivos**:` de TODAS las tareas del ledger `tasks.md`
     (tokens entre acentos graves; globs `*` (un nivel) y `**/` (cero o más directorios),
     llaves `{a,b}`, carpetas con `/` final o existentes, «(nuevo)» y otros apuntes entre
     paréntesis se ignoran, listas por coma).
     Siempre en alcance: el propio `tasks.md` de la iniciativa y `docs/knowledge/**`.
  3. Clasifica: en alcance · fuera de alcance · declarados sin tocar.

Uso:
  scope-check.py <docs/roadmap/<fecha>-<slug>> [--base <ref>] [--warn-only] [--json]
Exit: 0 nada fuera de alcance · 1 hay ficheros fuera (con --warn-only siempre 0) ·
      2 error de uso (carpeta/ledger inválidos, sin git, sin base determinable).
"""
import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MAIN_BRANCHES = ("main", "master")
SIEMPRE_EN_ALCANCE = ("docs/knowledge/",)


def _load_glob_to_regex():
    """Reutiliza el traductor glob→regex de confluence-scope.py (`**/` = cero o más directorios,
    `*` = un nivel), la fuente única de esa semántica en el repo; si la skill no está instalada,
    copia local equivalente (fnmatch trata `**` como `*` y exigía un nivel — gap de la revisión)."""
    cand = os.path.join(HERE, "..", "..", "skills", "confluence-publish", "scripts", "confluence-scope.py")
    if os.path.isfile(cand):
        try:
            spec = importlib.util.spec_from_file_location("confluence_scope", cand)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod.glob_to_regex
        except Exception:  # noqa: BLE001 — degradación al traductor local
            pass

    def local(pattern):
        pattern = pattern.replace("\\", "/")
        out, i, n = [], 0, len(pattern)
        while i < n:
            if pattern[i:i + 3] == "**/":
                out.append("(?:.*/)?"); i += 3
            elif pattern[i:i + 2] == "**":
                out.append(".*"); i += 2
            elif pattern[i] == "*":
                out.append("[^/]*"); i += 1
            elif pattern[i] == "?":
                out.append("[^/]"); i += 1
            else:
                out.append(re.escape(pattern[i])); i += 1
        return re.compile("^" + "".join(out) + "$")
    return local


GLOB_TO_REGEX = _load_glob_to_regex()


def _load_parse_ledger():
    spec = importlib.util.spec_from_file_location("ledger_lint", os.path.join(HERE, "ledger-lint.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.parse_ledger


# ------------------------------------------------------------------- git ----
def git(root, *args, check=True):
    r = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout


def repo_root(path):
    try:
        return git(path, "rev-parse", "--show-toplevel").strip()
    except (RuntimeError, OSError):
        return None


def resolver_base(root, base):
    """Devuelve (ref, descripción) o lanza RuntimeError con mensaje claro."""
    if base:
        git(root, "rev-parse", "--verify", "--quiet", base + "^{commit}")
        return base, f"--base {base}"
    actual = git(root, "rev-parse", "--abbrev-ref", "HEAD").strip()
    if actual in MAIN_BRANCHES:
        return "HEAD", f"HEAD (rama principal «{actual}»: solo cambios sin comitear)"
    for b in MAIN_BRANCHES:
        if subprocess.run(["git", "rev-parse", "--verify", "--quiet", b], cwd=root,
                          capture_output=True).returncode == 0:
            mb = git(root, "merge-base", b, "HEAD").strip()
            return mb, f"merge-base {b}…HEAD ({mb[:8]})"
    raise RuntimeError(
        f"no hay base clara: la rama «{actual}» no es main/master y no existe ninguna de las dos "
        f"en el repo — pasa `--base <ref>` (p. ej. el commit desde el que partió la rama).")


def ficheros_cambiados(root, base):
    out = set()
    if base != "HEAD":
        out.update(l.strip() for l in git(root, "diff", "--name-only", base, "HEAD").splitlines() if l.strip())
    for ln in git(root, "status", "--porcelain", "--untracked-files=all").splitlines():
        if len(ln) < 4:
            continue
        p = ln[3:]
        if " -> " in p:
            p = p.split(" -> ", 1)[1]
        p = p.strip().strip('"')
        if p:
            out.add(p.rstrip("/"))
    return sorted(out)


# --------------------------------------------------------------- ledger ----
_TOKEN_RE = re.compile(r"`([^`\n]+)`")
_PATH_OK = re.compile(r"^[\w./*?\[\]{},~@+\-]+$")


def _expandir_llaves(tok):
    m = re.search(r"\{([^{}]*)\}", tok)
    if not m:
        return [tok]
    out = []
    for alt in m.group(1).split(","):
        out.extend(_expandir_llaves(tok[:m.start()] + alt.strip() + tok[m.end():]))
    return out


def patrones_del_ledger(text, parse_ledger):
    """[(patrón, T-XX)] a partir de los campos Archivos de cada tarea (tokens en acentos graves)."""
    parsed = parse_ledger(text)
    ids = [t["id"] for t in parsed["tareas"]]
    patrones = []
    # trocear por cabeceras de tarea para atribuir cada campo a su T-XX
    chunks = re.split(r"^(?=###\s+T-\d+\b)", text, flags=re.M)
    for ch in chunks:
        m = re.match(r"###\s+(T-\d+)\b", ch)
        tid = m.group(1) if m and m.group(1) in ids else None
        if not tid:
            continue
        for ln in ch.splitlines():
            if not re.match(r"^\s*-\s*\*\*Archivos\*\*\s*:", ln):
                continue
            campo = ln.split(":", 1)[1]
            for tok in _TOKEN_RE.findall(campo):
                tok = tok.strip().replace("\\", "/")
                tok = re.sub(r"^\./", "", tok)
                if not tok or " " in tok or not _PATH_OK.match(tok):
                    continue          # «sus tests», «CI», frases… no son rutas
                if tok.startswith("/"):
                    continue          # rutas absolutas fuera del repo (/tmp/…) no cuentan
                for p in _expandir_llaves(tok):
                    patrones.append((p, tid))
    return patrones


def casa(path, patron, root):
    pat = patron.rstrip("/")
    if patron.endswith("/") or os.path.isdir(os.path.join(root, pat)):
        return path == pat or path.startswith(pat + "/")
    if any(c in pat for c in "*?"):
        return GLOB_TO_REGEX(pat).match(path) is not None   # `*` un nivel · `**/` cero o más directorios
    return path == pat


def clasificar(cambiados, patrones, tasks_rel, root):
    en, fuera, usados = [], [], set()
    for f in cambiados:
        hit = [i for i, (p, _) in enumerate(patrones) if casa(f, p, root)]
        usados.update(hit)          # también si el fichero ya está en alcance «de oficio»
        if hit or f == tasks_rel or any(f.startswith(p) for p in SIEMPRE_EN_ALCANCE):
            en.append(f)
        else:
            fuera.append(f)
    sin_tocar = sorted({f"{p} ({t})" for i, (p, t) in enumerate(patrones) if i not in usados})
    return en, fuera, sin_tocar


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("iniciativa", help="carpeta docs/roadmap/<fecha>-<slug>")
    ap.add_argument("--base", default=None, help="ref base del diff (default: merge-base con main/master)")
    ap.add_argument("--warn-only", action="store_true", help="siempre exit 0 (solo informa)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    carpeta = os.path.abspath(args.iniciativa)
    tasks = os.path.join(carpeta, "tasks.md")
    if not os.path.isfile(tasks):
        print(f"scope-check: no existe {tasks}", file=sys.stderr)
        return 2
    root = repo_root(carpeta)
    if not root:
        print("scope-check: la iniciativa no está dentro de un repositorio git", file=sys.stderr)
        return 2
    root = os.path.realpath(root)
    tasks_rel = os.path.relpath(os.path.realpath(tasks), root).replace("\\", "/")
    slug = os.path.basename(carpeta)
    try:
        base, base_desc = resolver_base(root, args.base)
        cambiados = ficheros_cambiados(root, base)
    except RuntimeError as e:
        print(f"scope-check: {e}", file=sys.stderr)
        return 2

    parse_ledger = _load_parse_ledger()
    text = open(tasks, encoding="utf-8", errors="replace").read()
    patrones = patrones_del_ledger(text, parse_ledger)
    en, fuera, sin_tocar = clasificar(cambiados, patrones, tasks_rel, root)

    if args.json:
        print(json.dumps({"slug": slug, "base": base, "base_desc": base_desc, "cambiados": len(cambiados),
                          "en_alcance": en, "fuera_de_alcance": fuera, "declarados_sin_tocar": sin_tocar,
                          "patrones": [p for p, _ in patrones]}, ensure_ascii=False, indent=2))
    else:
        print(f"scope-check: {slug} · base {base_desc} · {len(cambiados)} fichero(s) cambiado(s) · "
              f"{len(patrones)} patrón(es) declarados en Archivos")
        print(f"✅ en alcance ({len(en)}):" + ("".join(f"\n   {f}" for f in en) or " —"))
        print(f"❌ fuera de alcance ({len(fuera)}):" + ("".join(f"\n   {f}" for f in fuera) or " —"))
        if sin_tocar:
            print(f"ℹ️  declarados sin tocar ({len(sin_tocar)}):" + "".join(f"\n   {f}" for f in sin_tocar))
        if fuera:
            print("→ o el fichero es necesario (añádelo al campo Archivos de su tarea y anótalo) "
                  "o revierte el cambio; hasta entonces la revisión no arranca.")
    if fuera and not args.warn_only:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
