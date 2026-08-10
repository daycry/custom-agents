#!/usr/bin/env python3
"""
lint_plugin.py — linter del plugin custom-agents.

Valida, sin dependencias externas (solo stdlib):
  1. Frontmatter de cada agents/*.md: `name`, `model`, `tools`, `description` presentes.
  2. `model` ∈ {haiku, sonnet, opus, inherit}.
  3. `tools` sean herramientas conocidas.
  4. `name` del frontmatter == nombre de fichero (kebab-case).
  5. El grafo `dependencies` (skills / kits / agents) apunta a artefactos que EXISTEN.
  6. No hay ciclos en el grafo de dependencias entre agentes.
  7. Nombres de agente únicos.

Avisos (no rompen el build):
  - `description` sin frase-gatillo ("Úsalo/Úsala cuando…", "PROACTIVAMENTE", "Use when").
  - Commands/skills con nombre GENÉRICO (riesgo de colisión si el bundle se copia a un
    `.claude/` en vez de instalarse como plugin, donde el namespace `custom-agents:` lo evita).

Uso:
  python scripts/lint_plugin.py            # lint del repo (cwd = raíz del plugin)
  python scripts/lint_plugin.py --root DIR
Salida: informe por stdout; exit 0 si no hay ERRORES, 1 si los hay.
"""
import argparse
import os
import re
import sys

VALID_MODELS = {"haiku", "sonnet", "opus", "inherit"}
VALID_TOOLS = {
    "Read", "Write", "Edit", "Grep", "Glob", "Bash",
    "WebFetch", "WebSearch", "Agent", "Task", "NotebookEdit",
}
# Tokens de nombre genéricos: alto riesgo de choque en modo copia-directa a .claude/.
GENERIC_NAME_TOKENS = {
    "setup", "retro", "qa", "status", "build", "test", "review",
    "plan", "planner", "docs", "deploy", "release", "init", "start",
}
TRIGGER_RE = re.compile(r"(Úsal[oa] cuando|PROACTIVAMENTE|Use (this )?when|Úsal[oa] PROACTIVAMENTE)", re.I)


def parse_frontmatter(text):
    """Parser mínimo de frontmatter YAML (solo lo que este linter necesita).
    Devuelve dict con: name, model, tools(list), description, dependencies{skills,kits,agents}."""
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    fm = text[3:end]
    out = {"dependencies": {"skills": [], "kits": [], "agents": []}}
    cur_dep = None  # None | "skills" | "kits" | "agents"
    in_deps = False
    for raw in fm.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.strip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        stripped = line.strip()
        if indent == 0 and ":" in stripped:
            key = stripped.split(":", 1)[0].strip()
            val = stripped.split(":", 1)[1].strip()
            in_deps = (key == "dependencies")
            cur_dep = None
            if key == "name":
                out["name"] = val
            elif key == "model":
                out["model"] = val
            elif key == "description":
                out["description"] = val
            elif key == "tools":
                out["tools"] = [t.strip() for t in val.split(",") if t.strip()]
        elif in_deps and indent == 2 and stripped.endswith(":"):
            cur_dep = stripped[:-1].strip()
            if cur_dep not in out["dependencies"]:
                out["dependencies"][cur_dep] = []
        elif in_deps and indent == 2 and ":" in stripped:
            # forma inline: "skills: []" o "skills:   # comentario"
            k = stripped.split(":", 1)[0].strip()
            v = stripped.split(":", 1)[1]
            v = v.split("#", 1)[0].strip()  # descarta comentario en línea
            cur_dep = k
            out["dependencies"].setdefault(k, [])
            if v and v != "[]":
                out["dependencies"][k].append(v.strip("[] "))
        elif in_deps and cur_dep and stripped.startswith("- "):
            item = stripped[2:].split("#", 1)[0].strip()
            if item:
                out["dependencies"][cur_dep].append(item)
    return out


def lint(root):
    errors, warnings = [], []
    agents_dir = os.path.join(root, "agents")
    skills_dir = os.path.join(root, "skills")
    kits_dir = os.path.join(root, "agent-kits")
    commands_dir = os.path.join(root, "commands")

    # --- Agentes ---
    agent_names = set()
    dep_graph = {}
    if not os.path.isdir(agents_dir):
        errors.append(f"No existe el directorio de agentes: {agents_dir}")
        return errors, warnings

    for fn in sorted(os.listdir(agents_dir)):
        if not fn.endswith(".md"):
            continue
        stem = fn[:-3]
        path = os.path.join(agents_dir, fn)
        fm = parse_frontmatter(open(path, encoding="utf-8").read())
        if fm is None:
            errors.append(f"{fn}: frontmatter ausente o mal formado")
            continue
        # requeridos
        for field in ("name", "model", "tools", "description"):
            if field not in fm or not fm.get(field):
                errors.append(f"{fn}: falta el campo requerido `{field}`")
        name = fm.get("name", "")
        if name:
            if name != stem:
                errors.append(f"{fn}: `name: {name}` no coincide con el nombre de fichero `{stem}`")
            if name in agent_names:
                errors.append(f"{fn}: nombre de agente duplicado `{name}`")
            agent_names.add(name)
        # model
        model = fm.get("model")
        if model and model not in VALID_MODELS:
            errors.append(f"{fn}: `model: {model}` no es válido (usa {sorted(VALID_MODELS)})")
        # tools
        for t in fm.get("tools", []):
            if t not in VALID_TOOLS:
                errors.append(f"{fn}: herramienta desconocida en `tools`: `{t}`")
        # description triggers (warning)
        desc = fm.get("description", "")
        if desc and not TRIGGER_RE.search(desc):
            warnings.append(f"{fn}: la `description` no tiene frase-gatillo (\"Úsalo cuando…\"/\"PROACTIVAMENTE\") → peor auto-delegación")
        dep_graph[name] = fm.get("dependencies", {}).get("agents", [])

    # --- Referencias del grafo ---
    for fn in sorted(os.listdir(agents_dir)):
        if not fn.endswith(".md"):
            continue
        fm = parse_frontmatter(open(os.path.join(agents_dir, fn), encoding="utf-8").read())
        if not fm:
            continue
        deps = fm.get("dependencies", {})
        for sk in deps.get("skills", []):
            if not os.path.isfile(os.path.join(skills_dir, sk, "SKILL.md")):
                errors.append(f"{fn}: skill declarada inexistente: `{sk}` (falta skills/{sk}/SKILL.md)")
        for kit in deps.get("kits", []):
            kp = kit[len("agent-kits/"):] if kit.startswith("agent-kits/") else kit
            if not os.path.isdir(os.path.join(kits_dir, kp)):
                errors.append(f"{fn}: kit declarado inexistente: `{kit}` (falta agent-kits/{kp}/)")
        for ag in deps.get("agents", []):
            if ag not in agent_names:
                errors.append(f"{fn}: agente en handoff inexistente: `{ag}`")

    # --- Ciclos en el grafo de agentes ---
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {n: WHITE for n in dep_graph}

    def dfs(n, stack):
        color[n] = GRAY
        for m in dep_graph.get(n, []):
            if m not in color:
                continue
            if color[m] == GRAY:
                errors.append(f"Ciclo en dependencias de agentes: {' → '.join(stack + [m])}")
            elif color[m] == WHITE:
                dfs(m, stack + [m])
        color[n] = BLACK

    for n in list(dep_graph):
        if color[n] == WHITE:
            dfs(n, [n])

    # --- Namespacing: nombres genéricos en commands/skills (warning) ---
    for d, kind, get_names in (
        (commands_dir, "command", lambda dd: [f[:-3] for f in os.listdir(dd) if f.endswith(".md")]),
        (skills_dir, "skill", lambda dd: [x for x in os.listdir(dd) if os.path.isdir(os.path.join(dd, x))]),
    ):
        if not os.path.isdir(d):
            continue
        for nm in sorted(get_names(d)):
            toks = set(re.split(r"[-_]", nm.lower()))
            if toks & GENERIC_NAME_TOKENS:
                warnings.append(
                    f"{kind} `{nm}`: nombre genérico — sin instalar como plugin (namespace `custom-agents:`) "
                    f"puede chocar con otro `.claude/`. Ok si se usa como plugin.")
    return errors, warnings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    args = ap.parse_args()
    root = os.path.abspath(args.root)
    errors, warnings = lint(root)

    for w in warnings:
        print(f"⚠️  {w}")
    for e in errors:
        print(f"❌ {e}")
    n_agents = len([f for f in os.listdir(os.path.join(root, "agents")) if f.endswith(".md")]) \
        if os.path.isdir(os.path.join(root, "agents")) else 0
    print(f"\nlint_plugin: {n_agents} agentes · {len(errors)} errores · {len(warnings)} avisos")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
