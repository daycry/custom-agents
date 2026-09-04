#!/usr/bin/env python3
"""
model-tier.py — tier EFECTIVO (model + effort) de un agente, resuelto en DOS capas (parity-core T-01):

  capa 1  frontmatter de `agents/<agente>.md` (`model:` obligatorio · `effort:` según la tabla de
          tiering de docs/CONVENTIONS.md; sin `effort:` → `inherit`, el agente hereda el de la sesión).
  capa 2  `.claude/dev.json` del proyecto consumidor → `"modelos": {"<agente>": {"model": "…", "effort": "…"}}`
          (parcial: cada clave presente y VÁLIDA sustituye a la del frontmatter; inválida → aviso y se
          ignora; fichero ausente o corrupto → aviso y capa 1). Config ≠ estado: la escribe /setup
          (paso 5-quater) o el usuario a mano.

Lo llaman los ORQUESTADORES (`/dev-cycle`, `/pm-cycle`, `adversarial-review`, `quick-implement`) antes de
despachar un agente por nombre, para pasar `model` en el parámetro por invocación del Agent tool
(contrato oficial sub-agents.md, verificado 2026-09-03: «per-invocation `model` parameter» es la
prioridad 1 desde v2.1.251; luego el frontmatter; luego CLAUDE_CODE_SUBAGENT_MODEL; luego la sesión).
HONESTIDAD: el Agent tool NO documenta un parámetro `effort` → el `effort` de dev.json es INFORMATIVO
(el orquestador lo anuncia; el único efectivo es el del frontmatter). Invocación manual `@agente` →
Claude Code lee solo el frontmatter (la capa 2 no aplica): esto también lo imprime la salida.

Valores válidos (sub-agents.md, 2026-09-03): model ∈ {haiku, sonnet, opus, inherit} ∪ {fable} ∪ ids
completos `claude-*`; effort ∈ {low, medium, high, xhigh, max}.

Uso:
  model-tier.py <agente> [--json] [--root DIR] [--project DIR]
  model-tier.py --all    [--json] [--root DIR] [--project DIR]      # tabla efectiva de todos los agentes
Localización del plugin: --root → CLAUDE_PLUGIN_ROOT → padre de agent-kits/shared → find en $PWD/.claude
y $HOME/.claude. Proyecto: --project → CLAUDE_PROJECT_DIR → $PWD.
Exit: 0 ok · 1 agente inexistente · 2 plugin no localizado. Nunca lanza por un dev.json roto.
"""
import argparse
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
MODELOS_ALIAS = {"haiku", "sonnet", "opus", "inherit", "fable"}
MODEL_ID_RE = re.compile(r"^claude-[a-z0-9][a-z0-9.-]*$")
EFFORTS = ("low", "medium", "high", "xhigh", "max")


def model_valido(v):
    return isinstance(v, str) and (v in MODELOS_ALIAS or bool(MODEL_ID_RE.match(v)))


def effort_valido(v):
    return isinstance(v, str) and v in EFFORTS


# ------------------------------------------------------------------ localización

def es_plugin(root):
    return bool(root) and os.path.isdir(os.path.join(root, "agents"))


def localizar_root(explicito=None):
    if explicito:                      # pedido explícito: se respeta; inválido → None sin buscar por ahí
        return explicito if es_plugin(explicito) else None
    for c in (os.environ.get("CLAUDE_PLUGIN_ROOT"), os.path.dirname(os.path.dirname(HERE))):
        if c and es_plugin(c):
            return c
    for base in (os.path.join(os.getcwd(), ".claude"), os.path.join(os.path.expanduser("~"), ".claude")):
        if not os.path.isdir(base):
            continue
        try:
            r = subprocess.run(["find", base, "-type", "d", "-path", "*agent-kits/shared"],
                               capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10)
            for line in r.stdout.splitlines():
                cand = os.path.dirname(os.path.dirname(line.strip()))
                if es_plugin(cand):
                    return cand
        except (OSError, subprocess.SubprocessError):
            continue
    return None


def proyecto_dir(explicito=None):
    return explicito or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


# ------------------------------------------------------------------ capa 1: frontmatter

def frontmatter(path):
    try:
        text = open(path, encoding="utf-8-sig").read()
    except (OSError, UnicodeDecodeError):
        return {}
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    out = {}
    for raw in text[3:end].splitlines():
        if not raw.strip() or raw.lstrip().startswith("#") or raw[0] in " \t" or ":" not in raw:
            continue
        k, v = raw.split(":", 1)
        out[k.strip()] = v.split("#", 1)[0].strip() if not v.strip().startswith(("'", '"')) else v.strip()
    return out


def agentes(root):
    d = os.path.join(root, "agents")
    try:
        return sorted(f[:-3] for f in os.listdir(d) if f.endswith(".md"))
    except OSError:
        return []


# ------------------------------------------------------------------ capa 2: dev.json

def leer_modelos(project, avisos):
    """Bloque `modelos` de .claude/dev.json (dict) o {} con aviso si falta/está roto."""
    p = os.path.join(project, ".claude", "dev.json")
    if not os.path.isfile(p):
        return {}
    try:
        with open(p, encoding="utf-8-sig") as fh:
            data = json.load(fh)
    except (OSError, ValueError) as e:
        avisos.append(f"dev.json ilegible ({e.__class__.__name__}): se usa solo el frontmatter")
        return {}
    if not isinstance(data, dict):
        avisos.append("dev.json: la raíz no es un objeto JSON — se usa solo el frontmatter")
        return {}
    modelos = data.get("modelos")
    if modelos is None:
        return {}
    if not isinstance(modelos, dict):
        avisos.append("dev.json `modelos` no es un objeto {agente: {model, effort}}: se ignora")
        return {}
    return modelos


# ------------------------------------------------------------------ resolución

def resolver(agente, root=None, project=None, _modelos=None, _avisos=None):
    """Dict {agente, model, effort, fuente:{model,effort}, avisos:[…]} o None si el agente no existe."""
    root = localizar_root(root)
    if not root:
        return None
    path = os.path.join(root, "agents", f"{agente}.md")
    if not os.path.isfile(path):
        return None
    fm = frontmatter(path)
    avisos = [] if _avisos is None else _avisos
    model = fm.get("model") or "inherit"
    fuente_m = "frontmatter" if fm.get("model") else "ausente→inherit"
    effort = fm.get("effort") or "inherit"
    fuente_e = "frontmatter" if fm.get("effort") else "heredado"
    if fm.get("effort") and not effort_valido(fm["effort"]):
        avisos.append(f"frontmatter `effort: {fm['effort']}` inválido (usa {', '.join(EFFORTS)})")
    modelos = leer_modelos(proyecto_dir(project), avisos) if _modelos is None else _modelos
    override = modelos.get(agente) if isinstance(modelos, dict) else None
    if override is not None and not isinstance(override, dict):
        avisos.append(f"dev.json modelos.{agente} no es un objeto: se ignora")
        override = None
    if override:
        if "model" in override:
            if model_valido(override["model"]):
                model, fuente_m = override["model"], "dev.json"
            else:
                avisos.append(f"dev.json modelos.{agente}.model={override['model']!r} inválido: se ignora")
        if "effort" in override:
            if effort_valido(override["effort"]):
                effort, fuente_e = override["effort"], "dev.json"
            else:
                avisos.append(f"dev.json modelos.{agente}.effort={override['effort']!r} inválido: se ignora")
    return {"agente": agente, "model": model, "effort": effort,
            "fuente": {"model": fuente_m, "effort": fuente_e}, "avisos": avisos}


NOTA = ("Nota: `model` se pasa en el parámetro por invocación del Agent tool; `effort` de dev.json es "
        "INFORMATIVO (el Agent tool no documenta ese parámetro — solo el del frontmatter es efectivo). "
        "Invocación manual `@agente` → frontmatter.")


def linea(r):
    return (f"{r['agente']}: model={r['model']} effort={r['effort']} "
            f"(model: {r['fuente']['model']} · effort: {r['fuente']['effort']})")


def main(argv=None):
    ap = argparse.ArgumentParser(description="tier efectivo (model + effort) de un agente: frontmatter + dev.json")
    ap.add_argument("agente", nargs="?", help="nombre del agente (agents/<agente>.md)")
    ap.add_argument("--all", action="store_true", help="tabla de todos los agentes")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--root", default=None, help="raíz del plugin (default: autodetección)")
    ap.add_argument("--project", default=None, help="proyecto consumidor con .claude/dev.json (default: $CLAUDE_PROJECT_DIR o cwd)")
    args = ap.parse_args(argv)
    if not args.all and not args.agente:
        ap.error("indica <agente> o --all")

    root = localizar_root(args.root)
    if not root:
        print("❌ plugin no localizado (agents/ no encontrado): usa --root o CLAUDE_PLUGIN_ROOT", file=sys.stderr)
        return 2
    avisos_globales = []
    modelos = leer_modelos(proyecto_dir(args.project), avisos_globales)

    if args.all:
        filas = [resolver(a, root=root, project=args.project, _modelos=modelos, _avisos=list(avisos_globales))
                 for a in agentes(root)]
        filas = [f for f in filas if f]
        if args.json:
            print(json.dumps({"agentes": filas, "avisos": avisos_globales}, ensure_ascii=False))
        else:
            print("| Agente | model | effort | fuente |")
            print("|---|---|---|---|")
            for f in filas:
                print(f"| {f['agente']} | {f['model']} | {f['effort']} | {f['fuente']['model']} · {f['fuente']['effort']} |")
            for a in avisos_globales:
                print(f"⚠️  {a}", file=sys.stderr)
            print(NOTA)
        return 0

    r = resolver(args.agente, root=root, project=args.project, _modelos=modelos, _avisos=list(avisos_globales))
    if r is None:
        print(f"❌ agente `{args.agente}` no existe en {os.path.join(root, 'agents')}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(r, ensure_ascii=False))
    else:
        for a in r["avisos"]:
            print(f"⚠️  {a}", file=sys.stderr)
        print(linea(r))
        print(NOTA)
    return 0


if __name__ == "__main__":
    sys.exit(main())
