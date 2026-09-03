#!/usr/bin/env python3
"""
export-skills.py — exporta las SKILLS del plugin como paquete PORTABLE, agnóstico de Claude Code
(patrón multi-entorno de superpowers): lo que viaja son los `skills/<n>/SKILL.md` con sus
`references/`, `scripts/` y `assets/`, más los fragmentos de `agent-kits/shared/` que esas skills
citan. NO viajan agentes, comandos, hooks ni statusline (dependen del runtime de Claude Code), ni
las skills que solo son punteros a piezas que no viajan (`quick-implement` → `commands/dev-cycle.md`,
`plugin-dev` → desarrollo de este repo). El README del paquete (ES+EN) lo explica con una tabla.

Formatos (`--format`):
  claude     skills/ + agent-kits/shared/ + README.md — se copia como `skills/` de un proyecto.
  agents-md  + AGENTS.md raíz (estándar abierto que leen Codex, Copilot, Cursor, Jules… —
             markdown plano sin frontmatter, agents.md) con el índice compacto de skills.
  cursor     + .cursor/rules/custom-agents-skills.mdc (frontmatter de Cursor: `description`,
             `alwaysApply: false` → modo Agent-Selected) con el mismo índice.
  all        los tres.

Reescritura (documentada en el README del paquete): en los `.md` copiados, la búsqueda de
runtime `find "$PWD/.claude" [otras rutas] "$HOME/.claude" …` pasa a `find "${PORTABLE_ROOT:-.}" …`.
El resto del comando (`-type … -path '*agent-kits/shared/…'`) no cambia porque el paquete conserva
la misma estructura de carpetas (`skills/`, `agent-kits/shared/`).

Determinista: misma entrada → mismo árbol (orden fijo, saltos `\n`, sin mtimes en el contenido) y
un hash sha256 del contenido escrito en el README. `--check <dir>` valida un paquete generado:
toda referencia `references/…`, `scripts/…`, `assets/…`, `skills/<n>/…` y `agent-kits/shared/…`
citada en un `.md` del paquete existe dentro del paquete; no queda ningún `find "$PWD/.claude"`;
el hash del README y del fichero-marcador `.custom-agents-portable` coinciden con el contenido;
`AGENTS.md`/`.mdc` (si están) listan todas las skills. La carpeta de salida solo se vacía si tiene
README con marca Y el fichero-marcador (nunca se borra una carpeta ajena).

Uso:
  python3 scripts/export-skills.py [--out dist/portable] [--format all] [--root DIR] [--quiet]
  python3 scripts/export-skills.py --check dist/portable
Exit 0 si todo va bien; 1 si el `--check` encuentra problemas o la exportación no puede escribir.
Solo stdlib. Reutiliza `agent-kits/shared/skill-index.py` (lectura de frontmatters + resumen).
"""
import argparse
import hashlib
import importlib.util
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT_DEFAULT = os.path.dirname(HERE)
FORMATOS = ("claude", "agents-md", "cursor", "all")
MARCADOR = "custom-agents · portable skills"      # 1.ª línea del README del paquete
MARCADOR_FICHERO = ".custom-agents-portable"       # fichero-marcador dedicado (hash) — exigido antes de rmtree (patrón _STAGING-LEEME.md)
CURSOR_RULE = os.path.join(".cursor", "rules", "custom-agents-skills.mdc")
INDEX_ANCHO = 150                                 # caracteres por línea del índice de skills

# skills que NO viajan: son punteros a piezas que dependen de Claude Code
EXCLUIR_SKILLS = {
    "quick-implement": "es un atajo a `commands/dev-cycle.md` (comando de Claude Code, no viaja)",
    "plugin-dev": "sirve para desarrollar ESTE plugin (agentes, comandos, hooks) — necesita el repo, no un proyecto",
}
# viaja, pero un paso depende de Claude Code (tabla del README del paquete)
DEGRADA = (
    ("`skills/cybersecurity/` — paso «Spawn ALL 8 agents using the Agent tool»",
     "the 8 parallel specialist agents need Claude Code's `Agent` tool; in other environments run the 8 dimensions "
     "IN SEQUENCE with `references/agent-prompts.md` and aggregate with `references/aggregation-and-report.md` · "
     "en otros entornos, ejecuta las 8 dimensiones en secuencia con las referencias"),
)
# lo que NUNCA viaja, y por qué (tabla del README del paquete)
NO_VIAJA = (
    ("`agents/`", "los subagentes (`Agent` tool, `model`, `tools`) son un contrato de Claude Code"),
    ("`commands/`", "los comandos `/x` solo existen en Claude Code; en otros entornos se describen en `AGENTS.md`"),
    ("`hooks/` · `statusline/`", "PreToolUse/PostToolUse/SessionStart y la statusline son eventos del runtime de Claude Code"),
    ("`agent-kits/<agente>/`", "toolkits privados de cada agente; solo viaja `agent-kits/shared/` en la parte que las skills citan"),
    ("`.claude-plugin/` · `evals/` · `tests/`", "manifiestos del plugin y su CI; no aportan nada al consumidor de las skills"),
)

FIND_RE = re.compile(r'find(?:\s+"\$(?:PWD|HOME)/[^"]*")+')
FIND_COLGANDO = 'find "$PWD/.claude"'
SHARED_REF_RE = re.compile(r"(?:agent-kits/shared|\$SHAREDKIT)/([A-Za-z0-9_.\-]+)")
PY_NAME_RE = re.compile(r'"([A-Za-z0-9_\-]+\.py)"')
# referencias a ficheros del paquete citadas en los .md (placeholders <…>/{…} se ignoran)
REF_RE = re.compile(r"(?<![A-Za-z0-9_/.\-])((?:skills/[a-z0-9\-]+/|agent-kits/shared/)?(?:references|scripts|assets)/[A-Za-z0-9_./\-]+|agent-kits/shared/[A-Za-z0-9_./\-]+)")


def _skill_index():
    p = os.path.join(ROOT_DEFAULT, "agent-kits", "shared", "skill-index.py")
    spec = importlib.util.spec_from_file_location("skill_index", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def read_bytes(p):
    with open(p, "rb") as f:
        return f.read()


def write_text(p, s):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(s)


def write_bytes(p, b):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "wb") as f:
        f.write(b)


# ------------------------------------------------------------------ selección

def skills_que_viajan(root):
    sk = os.path.join(root, "skills")
    if not os.path.isdir(sk):
        return []
    return sorted(d for d in os.listdir(sk)
                  if os.path.isfile(os.path.join(sk, d, "SKILL.md")) and d not in EXCLUIR_SKILLS)


def _excluido(rel):
    partes = rel.replace(os.sep, "/").split("/")
    nombre = partes[-1]
    return ("__pycache__" in partes or nombre.endswith(".pyc")
            or (nombre.startswith("test_") and nombre.endswith(".py")))


def ficheros_skill(root, skill):
    """Rutas relativas a la raíz del plugin, orden fijo, sin caché ni tests."""
    base = os.path.join(root, "skills", skill)
    out = []
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames.sort()
        for fn in sorted(filenames):
            rel = os.path.relpath(os.path.join(dirpath, fn), root).replace(os.sep, "/")
            if not _excluido(rel):
                out.append(rel)
    return out


def reescribir(texto):
    """`find "$PWD/.claude" … "$HOME/.claude"` → `find "${PORTABLE_ROOT:-.}"`. Devuelve (texto, n)."""
    return FIND_RE.subn('find "${PORTABLE_ROOT:-.}"', texto)


def fragmentos_shared(root, textos):
    """Fragmentos de agent-kits/shared/ citados por los textos (+ cierre sobre los .py copiados:
    `scope-check.py` carga `ledger-lint.py` por nombre). Devuelve rutas relativas ordenadas."""
    shared = os.path.join(root, "agent-kits", "shared")
    pendientes = set()
    for t in textos:
        pendientes.update(SHARED_REF_RE.findall(t))
    vistos, out = set(), []
    while pendientes:
        nombre = pendientes.pop()
        if nombre in vistos:
            continue
        vistos.add(nombre)
        p = os.path.join(shared, nombre)
        if os.path.isdir(p):
            for dirpath, dirnames, filenames in os.walk(p):
                dirnames.sort()
                for fn in sorted(filenames):
                    rel = os.path.relpath(os.path.join(dirpath, fn), root).replace(os.sep, "/")
                    if not _excluido(rel):
                        out.append(rel)
        elif os.path.isfile(p):
            out.append(f"agent-kits/shared/{nombre}")
            try:
                src = read_bytes(p).decode("utf-8")
            except UnicodeDecodeError:
                src = ""
            if nombre.endswith(".py"):          # scope-check.py carga ledger-lint.py por nombre
                for otro in PY_NAME_RE.findall(src):
                    if otro != nombre and os.path.isfile(os.path.join(shared, otro)):
                        pendientes.add(otro)
            else:                               # un fragmento .md puede citar otro (knowledge-write → templates/adr.md)
                pendientes.update(x for x in SHARED_REF_RE.findall(src) if x not in vistos)
        # nombre citado que no existe: no es error de exportación (se documenta en --check si se cita)
    return sorted(set(out))


# ------------------------------------------------------------------ índice de skills

def indice_skills(pkg_root, si):
    """[(nombre, resumen, description completa)] leyendo los frontmatters del paquete (solo hay skills)."""
    out = []
    for kind, nombre, desc, _hint, _raw in si.piezas(pkg_root):
        if kind == "skill":
            out.append((nombre, si.resumen(desc, INDEX_ANCHO), si.limpiar(desc)))
    return out


def tabla_indice(idx):
    lineas = ["| Skill | When to use it · Cuándo usarla | Read · Lee |", "|---|---|---|"]
    for nombre, res, _d in idx:
        lineas.append(f"| `{nombre}` | {res} | `skills/{nombre}/SKILL.md` |")
    return "\n".join(lineas)


def texto_agents_md(idx, version):
    return f"""# AGENTS.md — custom-agents portable skills (v{version})

This repository ships a set of **skills** exported from the Claude Code plugin
[`custom-agents`](https://github.com/daycry/custom-agents). A skill is a folder
`skills/<name>/` with a `SKILL.md` (the map: purpose, triggers, steps, guardrails) and, on demand,
`references/<topic>.md`, `scripts/` and `assets/`. They are plain Markdown + Python: no Claude Code
runtime is needed.

## How to use them

1. Before starting a task, check the index below. If the user's request matches a skill, **read
   `skills/<name>/SKILL.md` first** and follow it. Read a `references/<topic>.md` only when the
   SKILL.md tells you to at that step.
2. Skills resolve shared fragments with `find "${{PORTABLE_ROOT:-.}}" …`: run them from the folder
   that contains `skills/` and `agent-kits/shared/`, or export `PORTABLE_ROOT` pointing to it.
3. Scripts are deterministic and have exit codes; trust the exit code, not the prose.

Not included (they depend on Claude Code): agents, `/commands`, hooks, statusline. See `README.md`.

## Skill index

{tabla_indice(idx)}

---

*Español:* antes de cualquier tarea, comprueba si aplica una skill del índice; si es así, lee
`skills/<nombre>/SKILL.md` y síguela (las `references/` solo al llegar al paso que las cita).
"""


def texto_cursor_mdc(idx, version):
    nombres = ", ".join(n for n, _r, _d in idx)
    return f"""---
description: "custom-agents portable skills v{version} — read skills/<name>/SKILL.md when a request matches one of: {nombres}"
alwaysApply: false
---

# custom-agents portable skills

Skills exported from the Claude Code plugin `custom-agents` (Markdown + Python, no runtime needed).
When the user's request matches a skill, **read `skills/<name>/SKILL.md` first** and follow it;
open `references/<topic>.md` only at the step that cites it. Shared fragments are found with
`find "${{PORTABLE_ROOT:-.}}" …` (run from the folder holding `skills/` and `agent-kits/shared/`).
Agents, `/commands`, hooks and statusline are NOT included (Claude Code only) — see `README.md`.

{tabla_indice(idx)}
"""


# ------------------------------------------------------------------ README del paquete

def texto_readme(idx, viajan, shared_rel, formatos, version, n_reescritos, hash_hex):
    filas_skills = "\n".join(f"| `skills/{n}/` | ✅ | {r} |" for n, r, _d in idx)
    filas_excl = "\n".join(f"| `skills/{n}/` | ❌ | {why} |" for n, why in sorted(EXCLUIR_SKILLS.items()))
    filas_no = "\n".join(f"| {q} | ❌ | {why} |" for q, why in NO_VIAJA)
    filas_deg = "\n".join(f"| {q} | ⚠️ degrades · degrada | {why} |" for q, why in DEGRADA)
    shared_txt = "\n".join(f"- `{s}`" for s in shared_rel) or "- (ninguno)"
    fmts = ", ".join(f"`{f}`" for f in formatos)
    return f"""<!-- {MARCADOR} · hash: {hash_hex} -->
# custom-agents — portable skills (v{version})

**English** · Español más abajo.

Skills exported from the Claude Code plugin [`custom-agents`](https://github.com/daycry/custom-agents),
packaged to be used **outside Claude Code** (Codex, GitHub Copilot, Cursor, Jules… anything that reads
`AGENTS.md` or Cursor rules) or dropped as-is into a project's `skills/` folder. Generated by
`scripts/export-skills.py` (formats: {fmts}). Deterministic: same input → same tree.

**Content hash (sha256 of every file except this README):** `{hash_hex}` — verify with
`python3 scripts/export-skills.py --check <this folder>`.

## What travels / what does not / why · Qué viaja / qué no / por qué

| Piece · Pieza | Travels · Viaja | Why · Por qué |
|---|---|---|
{filas_skills}
| `agent-kits/shared/` (only the fragments cited by the skills above — see list below) | ✅ | shared prompt fragments and deterministic scripts the skills call (`ledger-lint.py`, `scope-check.py`, personas…) |
{filas_excl}
{filas_no}
{filas_deg}

Shared fragments included · Fragmentos compartidos incluidos ({len(shared_rel)}):
{shared_txt}

## Use it · Úsalo

| Environment · Entorno | How · Cómo |
|---|---|
| **Codex / Copilot / Jules / any `AGENTS.md` reader** | Copy `AGENTS.md`, `skills/` and `agent-kits/` to your repo root (or merge the "Skill index" section into your existing `AGENTS.md`). The agent reads `skills/<name>/SKILL.md` when a request matches. |
| **Cursor** | Copy `.cursor/rules/custom-agents-skills.mdc` plus `skills/` and `agent-kits/` to your repo. The rule is *Agent-Selected* (`alwaysApply: false` + `description`): Cursor attaches it when relevant. |
| **Claude Code (without the plugin)** | Copy `skills/*` into `.claude/skills/` and `agent-kits/shared/` into `.claude/agent-kits/shared/`. You lose agents, commands and hooks — install the plugin (`/plugin marketplace add daycry/custom-agents`) to get the full lifecycle. |

### Paths · Rutas (`PORTABLE_ROOT`)

In the plugin, skills locate shared files at runtime with a `find` over `$PWD/.claude` and
`$HOME/.claude` (`-type … -path '*agent-kits/shared/…'`). In this package that
prefix is **rewritten** ({n_reescritos} occurrence(s)) to `find "${{PORTABLE_ROOT:-.}}"`: run the
agent from the folder that contains `skills/` and `agent-kits/shared/`, or export
`PORTABLE_ROOT=/path/to/that/folder`. Nothing else in the commands changes — the package keeps the
plugin's folder layout, so the `-path '*agent-kits/shared/…'` patterns still match.

Degradation · Degradación: a skill that cites a piece that did not travel simply does not find it and
continues without it — the skills are written to degrade with a warning, never to block. The row
marked ⚠️ above lists the known case (`cybersecurity` runs its 8 dimensions in sequence instead of
spawning 8 agents).

---

## Español (resumen)

Skills del plugin de Claude Code `custom-agents`, empaquetadas para usarlas **fuera de Claude Code**
(Codex, Copilot, Cursor, Jules… todo lo que lee `AGENTS.md` o reglas de Cursor) o para copiarlas tal
cual como carpeta `skills/` de un proyecto. Viajan los `SKILL.md` con sus `references/`, `scripts/`
y `assets/` y los fragmentos de `agent-kits/shared/` que citan; **no** viajan agentes, comandos,
hooks ni statusline (dependen de Claude Code), ni `quick-implement`/`plugin-dev` (punteros a piezas
que no viajan). Degrada con aviso: `cybersecurity` (sin `Agent` tool, ejecuta las 8 dimensiones en
secuencia con `references/agent-prompts.md`). Rutas: el `find` sobre `$PWD/.claude` y `$HOME/.claude` se reescribe a `find "${{PORTABLE_ROOT:-.}}" …`;
ejecuta desde la carpeta que contiene `skills/` y `agent-kits/shared/` o exporta `PORTABLE_ROOT`.
Verifica la integridad con `python3 scripts/export-skills.py --check <carpeta>`.
"""


# ------------------------------------------------------------------ hash + export

def hash_paquete(pkg_root):
    """sha256 sobre (ruta relativa, contenido) de todos los ficheros salvo README.md y el marcador, en orden fijo."""
    h = hashlib.sha256()
    for rel in listar(pkg_root):
        if rel in ("README.md", MARCADOR_FICHERO):
            continue
        h.update(rel.encode("utf-8") + b"\0")
        h.update(read_bytes(os.path.join(pkg_root, rel)) + b"\0")
    return h.hexdigest()


def listar(pkg_root):
    out = []
    for dirpath, dirnames, filenames in os.walk(pkg_root):
        dirnames.sort()
        for fn in sorted(filenames):
            out.append(os.path.relpath(os.path.join(dirpath, fn), pkg_root).replace(os.sep, "/"))
    return sorted(out)


def version_plugin(root):
    try:
        import json
        with open(os.path.join(root, ".claude-plugin", "plugin.json"), encoding="utf-8") as f:
            return json.load(f).get("version", "0.0.0")
    except (OSError, ValueError):
        return "0.0.0"


def es_paquete_nuestro(out):
    """Un paquete generado aquí tiene el README con MARCADOR en la 1.ª línea Y el fichero-marcador
    dedicado `.custom-agents-portable` (con el hash). Ambos son obligatorios antes de borrar nada:
    un README falsificado o copiado no basta (patrón `_STAGING-LEEME.md` de confluence-scope --stage)."""
    readme = os.path.join(out, "README.md")
    marca = os.path.join(out, MARCADOR_FICHERO)
    if not (os.path.isfile(readme) and os.path.isfile(marca)):
        return False
    cab = read_bytes(readme).decode("utf-8", "replace")[:200]
    m = read_bytes(marca).decode("utf-8", "replace")
    return MARCADOR in cab and m.startswith(f"{MARCADOR}\n") and re.search(r"hash: [0-9a-f]{64}", m) is not None


def preparar_salida(out):
    """Vacía `out` solo si está vacío o es un paquete nuestro (README con MARCADOR + fichero-marcador
    `.custom-agents-portable`); si no, aborta sin tocar nada."""
    if os.path.isdir(out):
        if os.listdir(out) and not es_paquete_nuestro(out):
            sys.exit(f"ERROR: {out} existe y no es un paquete generado por export-skills.py "
                     f"(falta README con marca o {MARCADOR_FICHERO}); elige otra carpeta o vacíala")
        shutil.rmtree(out)
    os.makedirs(out)


def exportar(root, out, formato, quiet=False):
    si = _skill_index()
    formatos = ("claude", "agents-md", "cursor") if formato == "all" else (formato,)
    preparar_salida(out)
    viajan = skills_que_viajan(root)
    textos_md, n_reescritos = [], 0
    for skill in viajan:
        for rel in ficheros_skill(root, skill):
            src = os.path.join(root, rel)
            dst = os.path.join(out, rel)
            if rel.endswith(".md"):
                t, n = reescribir(read_bytes(src).decode("utf-8"))
                n_reescritos += n
                textos_md.append(t)
                write_text(dst, t)
            else:
                write_bytes(dst, read_bytes(src))
    shared_rel = fragmentos_shared(root, textos_md)
    for rel in shared_rel:
        src, dst = os.path.join(root, rel), os.path.join(out, rel)
        if rel.endswith(".md"):
            t, n = reescribir(read_bytes(src).decode("utf-8"))
            n_reescritos += n
            write_text(dst, t)
        else:
            write_bytes(dst, read_bytes(src))
    version = version_plugin(root)
    idx = indice_skills(out, si)
    if "agents-md" in formatos:
        write_text(os.path.join(out, "AGENTS.md"), texto_agents_md(idx, version))
    if "cursor" in formatos:
        write_text(os.path.join(out, CURSOR_RULE), texto_cursor_mdc(idx, version))
    h = hash_paquete(out)
    write_text(os.path.join(out, "README.md"),
               texto_readme(idx, viajan, shared_rel, formatos, version, n_reescritos, h))
    write_text(os.path.join(out, MARCADOR_FICHERO),
               f"{MARCADOR}\nversion: {version}\nformato: {formato}\nhash: {h}\n"
               f"(fichero-marcador: export-skills.py solo regenera carpetas que lo tienen; no lo borres)\n")
    if not quiet:
        print(f"export-skills: {len(viajan)} skills · {len(shared_rel)} fragmentos shared · "
              f"{n_reescritos} find reescritos · formato {formato} → {out}")
        for rel in listar(out):
            print(f"  {rel}")
        print(f"hash: {h}")
    return {"skills": viajan, "shared": shared_rel, "hash": h, "reescritos": n_reescritos}


# ------------------------------------------------------------------ check

def _limpiar_ref(ref):
    return ref.rstrip(".,;:)").rstrip("/")


def check(pkg_root):
    problemas = []
    readme = os.path.join(pkg_root, "README.md")
    if not os.path.isfile(readme):
        return [f"falta README.md en {pkg_root}"]
    cab = read_bytes(readme).decode("utf-8", "replace")[:300]
    m = re.search(r"hash: ([0-9a-f]{64})", cab)
    real = hash_paquete(pkg_root)
    if not m:
        problemas.append("README.md sin hash de contenido")
    elif m.group(1) != real:
        problemas.append(f"hash del README ({m.group(1)[:12]}…) ≠ hash del contenido "
                         f"({real[:12]}…): el paquete fue modificado")
    marca = os.path.join(pkg_root, MARCADOR_FICHERO)
    if not os.path.isfile(marca):
        problemas.append(f"falta el fichero-marcador {MARCADOR_FICHERO}")
    else:
        mm = re.search(r"hash: ([0-9a-f]{64})", read_bytes(marca).decode("utf-8", "replace"))
        if not mm or mm.group(1) != real:
            problemas.append(f"{MARCADOR_FICHERO}: hash ausente o distinto del contenido")
    skills_dir = os.path.join(pkg_root, "skills")
    skills = sorted(d for d in os.listdir(skills_dir)) if os.path.isdir(skills_dir) else []
    if not skills:
        problemas.append("el paquete no contiene skills/")
    for rel in listar(pkg_root):
        if not rel.endswith((".md", ".mdc")):
            continue
        texto = read_bytes(os.path.join(pkg_root, rel)).decode("utf-8", "replace")
        if FIND_COLGANDO in texto:
            problemas.append(f"{rel}: queda un `{FIND_COLGANDO}` sin reescribir")
        if not rel.startswith(("skills/", "agent-kits/")):
            continue
        skill_dir = os.path.join(pkg_root, *rel.split("/")[:2]) if rel.startswith("skills/") else None
        for ref in REF_RE.findall(texto):
            ref = _limpiar_ref(ref)
            if any(c in ref for c in "<>{}") or not ref:
                continue
            if ref.startswith(("skills/", "agent-kits/")):
                p = os.path.join(pkg_root, ref)
            elif skill_dir:
                p = os.path.join(skill_dir, ref)
            else:
                continue
            if not os.path.exists(p) and skill_dir and not ref.startswith(("skills/", "agent-kits/")):
                # una skill puede citar el fichero de otra por su ruta corta (confluence-pull → assets/ de confluence-publish)
                if any(os.path.exists(os.path.join(skills_dir, s, ref)) for s in skills):
                    continue
            if not os.path.exists(p):
                problemas.append(f"{rel}: cita `{ref}` y no existe en el paquete")
    for extra in ("AGENTS.md", CURSOR_RULE):
        p = os.path.join(pkg_root, extra)
        if os.path.isfile(p):
            texto = read_bytes(p).decode("utf-8", "replace")
            for s in skills:
                if f"`skills/{s}/SKILL.md`" not in texto:
                    problemas.append(f"{extra}: no lista la skill `{s}`")
    if os.path.isfile(os.path.join(pkg_root, CURSOR_RULE)):
        texto = read_bytes(os.path.join(pkg_root, CURSOR_RULE)).decode("utf-8", "replace")
        if not texto.startswith("---\ndescription:") or "\nalwaysApply: false\n" not in texto:
            problemas.append(f"{CURSOR_RULE}: frontmatter de Cursor incompleto (description / alwaysApply)")
    return sorted(set(problemas))


def main(argv=None):
    ap = argparse.ArgumentParser(description="exporta las skills del plugin como paquete portable")
    ap.add_argument("--out", default=os.path.join("dist", "portable"), help="carpeta de salida (default dist/portable)")
    ap.add_argument("--format", choices=FORMATOS, default="all")
    ap.add_argument("--root", default=ROOT_DEFAULT, help="raíz del plugin (default: padre de scripts/)")
    ap.add_argument("--check", metavar="DIR", help="valida un paquete generado en DIR y sale")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    if args.check:
        problemas = check(os.path.abspath(args.check))
        for p in problemas:
            print(f"❌ {p}")
        n = len(listar(os.path.abspath(args.check))) if os.path.isdir(args.check) else 0
        print(f"export-skills --check: {n} ficheros · {len(problemas)} problema(s)")
        return 1 if problemas else 0

    root = os.path.abspath(args.root)
    if not os.path.isdir(os.path.join(root, "skills")):
        sys.exit(f"ERROR: {root} no tiene skills/")
    exportar(root, os.path.abspath(args.out), args.format, quiet=args.quiet)
    return 0


if __name__ == "__main__":
    sys.exit(main())
