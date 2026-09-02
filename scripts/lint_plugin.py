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
  8. `hooks/hooks.json` (si existe): JSON válido con raíz `hooks`, y cada `command` de tipo
     `command` referencia un fichero del plugin que EXISTE (los hooks globales informan, no
     bloquean: un hook roto es una pieza muerta, no un guardrail). Fichero sin bit ejecutable
     → AVISO (se lanzan con `bash "…"`; checkouts con core.fileMode=false lo perderían).
  9. Campos NATIVOS `skills:` y `hooks:` del frontmatter de un agente: cada skill de `skills:`
     (precarga) existe en `skills/` Y está declarada en `dependencies.skills` (el grafo del repo
     es superconjunto de la precarga); cada `command` de `hooks:` (hooks de guardia con alcance
     del agente) que referencie `${CLAUDE_PLUGIN_ROOT}/<ruta>` apunta a un fichero que existe.
     AVISO si la precarga declarada en `skills:` supera PRELOAD_WARN_BYTES (token-diet: el
     contenido completo se inyecta en CADA arranque; las skills opt-in van bajo demanda).

Avisos (no rompen el build):
  - `description` sin frase-gatillo ("Úsalo/Úsala cuando…", "PROACTIVAMENTE", "Use when").
  - Commands/skills con nombre GENÉRICO (riesgo de colisión si el bundle se copia a un
    `.claude/` en vez de instalarse como plugin, donde el namespace `custom-agents:` lo evita).
    Commands: cualquier token genérico (`roadmap-status` avisa). Skills: solo si el nombre
    COMPLETO es un token genérico o tiene un solo token (`review` avisa; `adversarial-review`,
    compuesto, no — las skills se auto-invocan por descripción, el nombre compuesto ya
    desambigua) [debt-cleanup T-04b].
  - `hooks/*.json` con bit ejecutable (un JSON no se ejecuta; modo 100755 heredado) [T-01c].
  - `<x>.yml.MANUAL-COPY` en la raíz y `.github/workflows/<x>.yml` existen y DIFIEREN (la copia
    manual se ha quedado atrás: `cp <x>.yml.MANUAL-COPY .github/workflows/<x>.yml`) [T-04a].

Uso:
  python scripts/lint_plugin.py            # lint del repo (cwd = raíz del plugin)
  python scripts/lint_plugin.py --root DIR
Salida: informe por stdout; exit 0 si no hay ERRORES, 1 si los hay.
"""
import argparse
import json
import os
import re
import sys

VALID_MODELS = {"haiku", "sonnet", "opus", "inherit"}
PRELOAD_WARN_BYTES = 16 * 1024   # `skills:` precarga >16 KB (≈4k tokens) → aviso token-diet
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
    out = {"dependencies": {"skills": [], "kits": [], "agents": []}, "skills": [], "hook_commands": []}
    cur_dep = None  # None | "skills" | "kits" | "agents"
    in_deps = False
    cur_top = None  # clave de nivel 0 activa (para `skills:` y `hooks:` nativos)
    for raw in fm.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.strip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        stripped = line.strip()
        if indent > 0 and cur_top == "hooks":
            m = re.match(r"-?\s*command\s*:\s*(.+)$", stripped)
            if m:
                cmd = m.group(1).strip()
                if len(cmd) >= 2 and cmd[0] == cmd[-1] and cmd[0] in "'\"":
                    cmd = cmd[1:-1]
                out["hook_commands"].append(cmd)
            continue
        if indent > 0 and cur_top == "skills" and stripped.startswith("- "):
            item = stripped[2:].split("#", 1)[0].strip()
            if item:
                out["skills"].append(item)
            continue
        if indent == 0 and ":" in stripped:
            key = stripped.split(":", 1)[0].strip()
            val = stripped.split(":", 1)[1].strip()
            in_deps = (key == "dependencies")
            cur_dep = None
            cur_top = key
            if key == "skills":
                v = val.split("#", 1)[0].strip()
                if v and v != "[]":
                    out["skills"].extend(x.strip() for x in v.strip("[] ").split(",") if x.strip())
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
        # --- campos nativos `skills:` (precarga) y `hooks:` (guardia con alcance del agente) ---
        preload_bytes = 0
        for sk in fm.get("skills", []):
            sk_md = os.path.join(skills_dir, sk, "SKILL.md")
            if not os.path.isfile(sk_md):
                errors.append(f"{fn}: skill precargada en `skills:` inexistente: `{sk}` (falta skills/{sk}/SKILL.md)")
            else:
                preload_bytes += os.path.getsize(sk_md)
            if sk not in deps.get("skills", []):
                errors.append(f"{fn}: `skills: {sk}` no está en `dependencies.skills` — el grafo del repo debe ser "
                              f"superconjunto de la precarga nativa (regla 4 de CONVENTIONS)")
        if preload_bytes > PRELOAD_WARN_BYTES:
            warnings.append(f"{fn}: `skills:` precarga {preload_bytes // 1024} KB en CADA arranque del agente "
                            f"(token-diet: solo skills necesarias en TODAS sus ejecuciones; las opt-in van bajo demanda)")
        h_err, h_warn = lint_hook_commands(root, fm.get("hook_commands", []), f"{fn} [hooks]")
        errors.extend(h_err)
        warnings.extend(h_warn)

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

    # --- hooks/hooks.json: JSON válido + commands que existen (ejecutable = aviso) ---
    h_err, h_warn = lint_hooks(root)
    errors.extend(h_err)
    warnings.extend(h_warn)

    # --- Namespacing: nombres genéricos en commands/skills (warning) ---
    for d, kind, get_names in (
        (commands_dir, "command", lambda dd: [f[:-3] for f in os.listdir(dd) if f.endswith(".md")]),
        (skills_dir, "skill", lambda dd: [x for x in os.listdir(dd) if os.path.isdir(os.path.join(dd, x))]),
    ):
        if not os.path.isdir(d):
            continue
        for nm in sorted(get_names(d)):
            if nombre_generico(nm, kind):
                warnings.append(
                    f"{kind} `{nm}`: nombre genérico — sin instalar como plugin (namespace `custom-agents:`) "
                    f"puede chocar con otro `.claude/`. Ok si se usa como plugin.")

    # --- Copias manuales de workflows: <x>.yml.MANUAL-COPY vs .github/workflows/<x>.yml ---
    warnings.extend(lint_manual_copies(root))
    return errors, warnings


def nombre_generico(nm, kind):
    """Commands: aviso si CUALQUIER token del nombre es genérico (`roadmap-status`). Skills: solo si
    el nombre completo es un token genérico o tiene un solo token (`review` sí; `adversarial-review`
    no: compuesto, se auto-invoca por descripción). Debt-cleanup T-04b."""
    toks = [t for t in re.split(r"[-_]", nm.lower()) if t]
    if kind == "skill":
        return len(toks) <= 1 and bool(set(toks) & GENERIC_NAME_TOKENS)
    return bool(set(toks) & GENERIC_NAME_TOKENS)


def lint_manual_copies(root):
    """Avisos: cada `<x>.yml.MANUAL-COPY` de la raíz cuya copia `.github/workflows/<x>.yml` exista y
    NO sea byte-idéntica (la ruta es protegida para las herramientas remotas: la copia es manual y
    puede quedarse atrás; `tests/test_ci_manual_copy.py` lo comprueba con el mismo criterio)."""
    warns = []
    try:
        nombres = sorted(os.listdir(root))
    except OSError:
        return warns
    for fn in nombres:
        if not fn.endswith(".yml.MANUAL-COPY"):
            continue
        destino = os.path.join(root, ".github", "workflows", fn[:-len(".MANUAL-COPY")])
        if not os.path.isfile(destino):
            continue
        try:
            a = open(os.path.join(root, fn), "rb").read()
            b = open(destino, "rb").read()
        except OSError:
            continue
        if a != b:
            warns.append(f"{fn} y .github/workflows/{fn[:-len('.MANUAL-COPY')]} difieren — copia manual "
                         f"pendiente: `cp {fn} .github/workflows/{fn[:-len('.MANUAL-COPY')]}`")
    return warns


HOOK_PATH_RE = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/([^\s\"']+)")


def _es_ejecutable(fp):
    """Bit ejecutable según el índice de git (100755) si el fichero está versionado; si no, os.access."""
    try:
        import subprocess
        r = subprocess.run(["git", "ls-files", "-s", "--", os.path.basename(fp)],
                           cwd=os.path.dirname(fp), capture_output=True, text=True, timeout=5)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.split()[0] == "100755"
    except (OSError, subprocess.SubprocessError):
        pass
    return os.access(fp, os.X_OK)


def lint_hooks(root):
    """(errores, avisos) de hooks/hooks.json (vacíos si no existe el fichero)."""
    path = os.path.join(root, "hooks", "hooks.json")
    if not os.path.isfile(path):
        return [], []
    errs, warns = [], []
    try:
        data = json.load(open(path, encoding="utf-8"))
    except (ValueError, UnicodeDecodeError) as e:
        return [f"hooks/hooks.json: no es JSON válido ({e})"], []
    hooks = data.get("hooks") if isinstance(data, dict) else None
    if not isinstance(hooks, dict):
        return ["hooks/hooks.json: falta la raíz `hooks` (objeto evento → lista de grupos)"], []
    # Un .json de hooks/ con bit ejecutable no rompe nada, pero es un modo heredado sin sentido
    # (el JSON se lee, no se ejecuta) → aviso (debt-cleanup T-01c).
    # El modo de verdad es el del ÍNDICE de git (en montajes OneDrive/Windows/WSL el sistema de
    # ficheros muestra TODO como ejecutable y os.access daría un falso positivo); sin git → modo fs.
    hooks_dir = os.path.dirname(path)
    for fn in sorted(os.listdir(hooks_dir)):
        fp = os.path.join(hooks_dir, fn)
        if fn.endswith(".json") and os.path.isfile(fp) and _es_ejecutable(fp):
            warns.append(f"hooks/{fn}: un .json no debería ser ejecutable (chmod -x; `git update-index --chmod=-x`)")
    for evento, grupos in hooks.items():
        if not isinstance(grupos, list):
            errs.append(f"hooks/hooks.json: `{evento}` debe ser una lista de grupos")
            continue
        cmds = []
        for g in grupos:
            for h in (g.get("hooks", []) if isinstance(g, dict) else []):
                if isinstance(h, dict) and h.get("type") == "command":
                    cmds.append(str(h.get("command", "")))
        e, w = lint_hook_commands(root, cmds, f"hooks/hooks.json [{evento}]")
        errs.extend(e)
        warns.extend(w)
    return errs, warns


def lint_hook_commands(root, cmds, origen):
    """(errores, avisos) de una lista de `command`: cada `${CLAUDE_PLUGIN_ROOT}/<ruta>` debe
    existir (error) y ser ejecutable (aviso). Lo comparten hooks.json y el `hooks:` de agentes."""
    errs, warns = [], []
    for cmd in cmds:
        for rel in HOOK_PATH_RE.findall(cmd):
            fp = os.path.join(root, rel)
            if not os.path.isfile(fp):
                errs.append(f"{origen}: el command referencia `{rel}`, que no existe")
            elif not os.access(fp, os.X_OK):
                warns.append(f"{origen}: `{rel}` no es ejecutable (chmod +x recomendado; se lanza con `bash`)")
    return errs, warns


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
