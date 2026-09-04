#!/usr/bin/env python3
"""
lint_plugin.py — linter del plugin custom-agents.

Valida, sin dependencias externas (solo stdlib):
  1. Frontmatter de cada agents/*.md: `name`, `model`, `tools`, `description` presentes.
  2. `model` ∈ {haiku, sonnet, opus, inherit} y `effort` ∈ {low, medium, high, xhigh, max} (valores
     oficiales de sub-agents.md, verificados 2026-09-03; tiering en docs/CONVENTIONS.md — parity-core T-01).
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
    manual se ha quedado atrás: `cp <x>.yml.MANUAL-COPY .github/workflows/<x>.yml`) [T-04a]; mismo
    criterio para el árbol `github-templates.MANUAL-COPY/` → `.github/` (issue forms + PR template).
  - Pieza (skill/comando/agente) SIN al menos 1 caso positivo en `evals/cases/` — la description es
    una promesa de activación que no se prueba. Reutiliza la lectura de `evals/check.py`
    (`piezas()` + `cargar_casos()`, importado por ruta, sin efectos secundarios); si el plugin no
    tiene `evals/cases/` (consumidor) no avisa [activation-reliability T-04].
  - `description` de más de DESC_WARN_CHARS caracteres (token-diet: entra en el índice de piezas
    que `skill-index.py` inyecta en cada arranque y en el catálogo de skills del sistema).
  - `skills/<x>/SKILL.md` de más de SKILL_WARN_LINES líneas (token-diet: el SKILL.md se inyecta COMPLETO
    al invocar la skill; el detalle va a `skills/<x>/references/<tema>.md` con lectura bajo demanda —
    regla «skills cortas» de CONVENTIONS). El umbral DURO (250) lo impone `tests/test_skill_size.py`
    [plan-and-diet T-01].
  - Dos piezas (agente/skill/comando) DISTINTAS declaran el MISMO disparador literal entrecomillado
    en su `description` (normalizado en minúsculas/espacios) — heurístico barato de "un rol, un
    dueño" (`lint_duplicate_triggers`, ADR-011, `docs/agents/ROLES.md`): cazá copiar-pegar un
    disparador de una pieza a otra. Compara en minúsculas y SIN ACENTOS («revisión» ≡ «revision») y
    solo mira las frases de ≥3 palabras que van DESPUÉS de «Úsalo/Úsala cuando…» / «Use when…» — no
    cualquier cita de la description [T-fix1]. No detecta solapes semánticos con frases distintas —
    esos siguen siendo criterio humano [roles-and-jira-flow T-01].
  - `.py` del plugin que escribe símbolos (no ASCII en el fuente) **o** lee de `sys.stdin`, y NO
    reconfigura `sys.stdin`/`stdout`/`stderr` a UTF-8 al arrancar (`lint_console_encoding`): en una
    consola cp1252 —o con la salida a un pipe en Windows, que es como lo lanza `release.py`— el
    primer `print` de un símbolo revienta con `UnicodeEncodeError` y el primer `stdin.read()` de un
    payload con emoji con `UnicodeDecodeError`. Los dos motivos son independientes: el que LEE no
    depende de su fuente sino del payload, así que un `.py` ASCII puro entra igual [T-05].
    La comprobación es ESTRUCTURAL (`ast`): la marca dentro de `main()` o citada en un docstring no
    cuenta, porque medido no protege [windows-console T-01/T-04/T-05, GOT-005].
  - `.py` del plugin que captura un subproceso en modo TEXTO sin `encoding=`
    (`lint_subprocess_encoding`): el LADO PADRE del mismo bug — los hijos escriben UTF-8 siempre, así
    que decodificarlos con el codec del locale revienta en cp1252 [windows-console T-04].
    Ambas reglas comparten con `tests/test_console_encoding.py` el bloque `es_pieza` /
    `snippet_al_arrancar` / `lee_stdin` / `exige_snippet` / `subprocess_sin_encoding`, replicado
    LITERAL y comparado byte a byte por la suite.

Uso:
  python scripts/lint_plugin.py            # lint del repo (cwd = raíz del plugin)
  python scripts/lint_plugin.py --root DIR
Salida: informe por stdout; exit 0 si no hay ERRORES, 1 si los hay.
"""
import argparse
import ast
import json
import os
import re
import sys
import unicodedata

# Consola Windows (cp1252) o tuberías: reconfigurar ANTES de leer o imprimir nada (GOT-005).
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure, ya leído o None (capsys, pythonw)

VALID_MODELS = {"haiku", "sonnet", "opus", "inherit"}
VALID_EFFORTS = {"low", "medium", "high", "xhigh", "max"}   # sub-agents.md (2026-09-03); el override por
                                                            # proyecto lo resuelve agent-kits/shared/model-tier.py
PRELOAD_WARN_BYTES = 16 * 1024   # `skills:` precarga >16 KB (≈4k tokens) → aviso token-diet
DESC_WARN_CHARS = 1200           # description > 1.200 caracteres → aviso token-diet (índice de piezas)
SKILL_WARN_LINES = 200           # SKILL.md > 200 líneas → aviso token-diet (detalle a references/)
SKILL_HARD_LINES = 250           # umbral DURO: lo impone tests/test_skill_size.py (aquí solo se cita en el aviso)
VALID_TOOLS = {
    "Read", "Write", "Edit", "Grep", "Glob", "Bash",
    "WebFetch", "WebSearch", "Agent", "Task", "NotebookEdit",
}
# --8<-- criterio de consola COMPARTIDO (windows-console T-04/T-05) — REPLICADO LITERAL en
# scripts/lint_plugin.py y en tests/test_console_encoding.py. No lo edites en uno solo:
# `test_linter_y_suite_replican_el_mismo_bloque` compara los dos textos byte a byte, y
# `test_linter_y_suite_dan_el_mismo_veredicto` compara sus veredictos sobre árboles reales.
# Se replica (en vez de importarse) por el mismo contrato que el snippet: los scripts del plugin
# son standalone y el paquete portable los copia sueltos, sin PYTHONPATH ni módulo común.
CONSOLE_MARK = 'reconfigure(encoding="utf-8", errors="replace")'


def es_pieza(rel):
    """¿`rel` es una pieza del plugin a la que aplican las reglas de consola (CONVENTIONS 8)?

    Fuera del criterio, y solo esto:
      - las suites: basename que empieza por `test_` (no imprimen a la consola de nadie);
      - cualquier ruta con un segmento de directorio `fixtures`: es código del proyecto CONSUMIDOR
        simulado (lo que ejecutan los evals), no una pieza nuestra, y su salida no es nuestra.
    """
    partes = rel.replace("\\", "/").split("/")
    return not partes[-1].startswith("test_") and "fixtures" not in partes[:-1]


def _es_reconfigure(nodo):
    """¿`nodo` es la llamada `<stream>.reconfigure(encoding="utf-8", errors="replace")` del snippet?

    Se mira el NODO, no el texto: así una mención en un docstring o en un comentario no cuenta.
    """
    if not (isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Attribute)
            and nodo.func.attr == "reconfigure"):
        return False
    kws = {k.arg: k.value for k in nodo.keywords}
    return all(isinstance(kws.get(a), ast.Constant) and kws[a].value == v
               for a, v in (("encoding", "utf-8"), ("errors", "replace")))


def _previo_admitido(nodo):
    """Sentencias de módulo que pueden ir ANTES del snippet: no leen ni escriben en los streams."""
    if isinstance(nodo, (ast.Import, ast.ImportFrom)):     # incluye `from __future__ import …`
        return True
    return (isinstance(nodo, ast.Expr) and isinstance(nodo.value, ast.Constant)
            and isinstance(nodo.value.value, str))        # docstring del módulo


def snippet_al_arrancar(src):
    """¿El snippet de CONVENTIONS 8 protege de verdad a este fichero? (True/False/None)

    ESTRUCTURAL con `ast`, no `grep` de subcadena: medido (T-04) que la marca dentro de `main()` con
    un `print` de símbolos a nivel de módulo antes, o citada solo en un docstring, daba 0 avisos y el
    script reventaba igual bajo cp1252. Exige las dos cosas:
      (a) la llamada a `reconfigure` está en una sentencia de NIVEL DE MÓDULO (no dentro de un `def`
          ni de una `class`: ahí no protege el arranque), y
      (b) esa sentencia va antes de cualquier otra sentencia de módulo que no sea el docstring o un
          `import`/`from … import` — es decir, antes del primer `print` o del primer `stdin.read()`.
    `None` = el fichero no es Python parseable: ni se afirma ni se niega (no se opina a ciegas).
    """
    try:
        arbol = ast.parse(src)
    except (SyntaxError, ValueError):
        return None
    for i, nodo in enumerate(arbol.body):
        if isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if any(_es_reconfigure(n) for n in ast.walk(nodo)):
            return all(_previo_admitido(p) for p in arbol.body[:i])
    return False


def _sys_alias(arbol):
    """Nombres con los que este módulo nombra a `sys` y a `sys.stdin` (`import sys as s`,
    `from sys import stdin as entrada`)."""
    alias, directos = {"sys"}, set()
    for n in ast.walk(arbol):
        if isinstance(n, ast.Import):
            for a in n.names:
                if a.name == "sys":
                    alias.add(a.asname or "sys")
        elif isinstance(n, ast.ImportFrom) and n.module == "sys":
            for a in n.names:
                if a.name == "stdin":
                    directos.add(a.asname or "stdin")
    return alias, directos


def lee_stdin(src):
    """¿Este fichero USA `sys.stdin`? El lado que LEE no depende de su fuente, sino del PAYLOAD.

    Un `.py` 100 % ASCII revienta igual: `json.load(sys.stdin)` decodifica con el codec del locale, y
    el JSON de una release de GitHub trae emojis en `body` (🐛 = `F0 9F 90 9B`, con el byte `0x90`, y
    👍 con `0x8D`; ninguno existe en cp1252). Medido en `agent-kits/nemesis/tools/pick_asset.py`, que
    era la 28.ª pieza versionada y quedaba invisible para el criterio del lado que ESCRIBE.
    Con `ast`, no con `grep`: una mención en un comentario o dentro de una cadena no cuenta. El propio
    snippet nombra `sys.stdin`, así que queda fuera SOLO el `iter` de su `for` — si no, todo fichero
    con snippet «leería» stdin y el criterio se volvería circular. Excluir la sentencia entera sería
    peor que circular: apagaría la detección en todo el cuerpo de la función que alojase el snippet.
    """
    try:
        arbol = ast.parse(src)
    except (SyntaxError, ValueError):
        return False
    alias, directos = _sys_alias(arbol)
    del_snippet = set()
    for n in ast.walk(arbol):
        # SOLO el `sys.stdin` que el propio snippet nombra en su `iter`: excluir la sentencia entera
        # (o peor, cualquier ancestro que la contenga) apagaba la detección en todo el cuerpo de la
        # función donde estuviera el snippet — justo el anti-patrón «snippet dentro de `main()`» que
        # el linter existe para cazar. Medido en la revisión, intento 3.
        if isinstance(n, ast.For) and any(_es_reconfigure(c) for c in ast.walk(n)):
            del_snippet.update(id(x) for x in ast.walk(n.iter))
    for n in ast.walk(arbol):
        if id(n) in del_snippet:
            continue
        if (isinstance(n, ast.Attribute) and n.attr == "stdin"
                and isinstance(n.value, ast.Name) and n.value.id in alias):
            return True
        if isinstance(n, ast.Name) and n.id in directos:
            return True
        # `input()` y `fileinput.input()` leen del mismo stdin y con el mismo codec del locale.
        if isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Name) and f.id == "input":
                return True
            if (isinstance(f, ast.Attribute) and f.attr in ("input", "FileInput")
                    and isinstance(f.value, ast.Name) and f.value.id == "fileinput"):
                return True
    return False


def exige_snippet(data, src):
    """¿Esta pieza TIENE que llevar el snippet? Dos motivos independientes, no uno:

      (a) su FUENTE trae caracteres no ASCII — los imprime, y en cp1252 el primer `print` revienta
          con `UnicodeEncodeError`;
      (b) LEE de `sys.stdin` — el payload puede traerlos aunque el fuente sea ASCII puro, y entonces
          revienta con `UnicodeDecodeError`.
    `data` son los bytes del fichero y `src` su texto. El `or` corta a la izquierda: solo se parsea
    (b) cuando (a) no ha decidido ya.
    """
    return any(b > 127 for b in data) or lee_stdin(src)


def _kw(nodo, nombre):
    for k in nodo.keywords:
        if k.arg == nombre:
            return k
    return None


def _kw_verdadero(k):
    return k is not None and not (isinstance(k.value, ast.Constant) and k.value.value in (False, None))


SUBPROCESS_FUNCS = {"run", "Popen", "check_output", "check_call", "call", "getoutput", "getstatusoutput"}


def subprocess_sin_encoding(src):
    """Líneas con una llamada a `subprocess` en modo TEXTO y SIN `encoding=` (el lado PADRE, T-04).

    Desde T-01 los hijos escriben UTF-8 SIEMPRE; un padre que los decodifique con el codec del
    locale (`text=True` a secas) revienta con `UnicodeDecodeError` en una consola cp1252 — justo
    donde antes daba su veredicto. `capture_output=True` a solas NO entra: devuelve bytes y no
    decodifica nada. Lo que enciende el modo texto es `text=` / `universal_newlines=` / `errors=`.
    Se reconoce la llamada por el nombre (`subprocess.run`, alias de import, `from subprocess import
    run`) y también por llevar `capture_output=`, que solo existe en `subprocess.run` — así entra el
    invocador indirecto (`runner(cmd, capture_output=True, text=True, …)` de `evals/run.py`).
    `[]` si el fichero no es Python parseable.
    """
    try:
        arbol = ast.parse(src)
    except (SyntaxError, ValueError):
        return []
    alias = {"subprocess"}
    directos = set()
    for n in ast.walk(arbol):
        if isinstance(n, ast.Import):
            for a in n.names:
                if a.name == "subprocess":
                    alias.add(a.asname or "subprocess")
        elif isinstance(n, ast.ImportFrom) and n.module == "subprocess":
            for a in n.names:
                directos.add(a.asname or a.name)
    fuera = []
    for n in ast.walk(arbol):
        if not isinstance(n, ast.Call):
            continue
        f = n.func
        es = ((isinstance(f, ast.Attribute) and f.attr in SUBPROCESS_FUNCS
               and isinstance(f.value, ast.Name) and f.value.id in alias)
              or (isinstance(f, ast.Name) and f.id in directos)
              or _kw(n, "capture_output") is not None)
        if not es:
            continue
        texto = (_kw_verdadero(_kw(n, "text")) or _kw_verdadero(_kw(n, "universal_newlines"))
                 or _kw(n, "errors") is not None
                 or (isinstance(f, ast.Attribute) and f.attr in ("getoutput", "getstatusoutput")))
        if texto and _kw(n, "encoding") is None:
            fuera.append(n.lineno)
    return sorted(set(fuera))
# --8<-- fin del criterio de consola COMPARTIDO
# Directorios que no son código fuente NUESTRO: se podan del `os.walk` por coste y ruido. No son
# parte del criterio (`es_pieza` lo es): `git ls-files` —lo que usa la suite— tampoco los lista.
CONSOLE_SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", "node_modules", "vendor", "dist", "build",
                     ".venv", "venv", "target", ".next", "coverage", "bin", "obj"}
# Tokens de nombre genéricos: alto riesgo de choque en modo copia-directa a .claude/.
GENERIC_NAME_TOKENS = {
    "setup", "retro", "qa", "status", "build", "test", "review",
    "plan", "planner", "docs", "deploy", "release", "init", "start",
}
TRIGGER_RE = re.compile(r"(Úsal[oa] cuando|PROACTIVAMENTE|Use (this )?when|Úsal[oa] PROACTIVAMENTE)", re.I)
QUOTED_RE = re.compile(r'["“«]([^"”»]{3,})["”»]')   # frase entrecomillada de un disparador literal
# Un disparador es una frase que el USUARIO diría: al menos 3 palabras. Con menos, la cita es
# vocabulario compartido (`"fase"`, `"tasks.md"`, `"go"`) y avisar de ella era ruido puro.
MIN_PALABRAS_DISPARADOR = 3


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
            elif key == "effort":
                out["effort"] = val.split("#", 1)[0].strip()
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
        for field in ("name", "model", "effort", "tools", "description"):
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
        effort = fm.get("effort")
        if effort and effort not in VALID_EFFORTS:
            errors.append(f"{fn}: `effort: {effort}` no es válido (usa {sorted(VALID_EFFORTS)})")
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

    # --- Activación: cobertura en evals/cases/ + longitud de las descriptions (avisos) ---
    warnings.extend(lint_activacion(root))

    # --- Skills cortas: SKILL.md > SKILL_WARN_LINES líneas (aviso token-diet) ---
    warnings.extend(lint_skill_sizes(root))

    # --- Un rol, un dueño (ADR-011): disparador literal entrecomillado duplicado entre piezas ---
    warnings.extend(lint_duplicate_triggers(root))

    # --- Consola no-UTF8 (windows-console T-01/T-04, GOT-005): las dos mitades del mismo bug ---
    warnings.extend(lint_console_encoding(root))      # lado propio: imprime/lee sin reconfigurar
    warnings.extend(lint_subprocess_encoding(root))   # lado padre: decodifica al hijo sin encoding=
    return errors, warnings


def _py_del_plugin(root):
    """[(ruta absoluta, ruta relativa)] de los `.py` del plugin en DISCO, según `es_pieza`.

    El linter mira el disco (tiene que funcionar sobre un plugin desempaquetado, sin git); la suite
    `tests/test_console_encoding.py` mira `git ls-files`. Esa diferencia es deliberada y es la ÚNICA:
    el criterio de qué cuenta como pieza (`es_pieza`) es el mismo texto en los dos sitios.
    """
    out = []
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in CONSOLE_SKIP_DIRS]
        for f in sorted(fn):
            if not f.endswith(".py"):
                continue
            p = os.path.join(dp, f)
            rel = os.path.relpath(p, root).replace(os.sep, "/")
            if es_pieza(rel):
                out.append((p, rel))
    return sorted(out, key=lambda t: t[1])


def _leer(p):
    """El fichero como bytes y como texto, o (None, None) si no se puede leer."""
    try:
        with open(p, "rb") as fh:
            data = fh.read()
    except OSError:
        return None, None
    return data, data.decode("utf-8", "replace")


def lint_console_encoding(root):
    """Avisos: `.py` del plugin que TIENE que reconfigurar los streams al arrancar y no lo hace.

    Quién tiene que llevarlo lo decide `exige_snippet`, y son DOS motivos independientes:
      - **escribe símbolos** (no ASCII en el fuente): el primer `print` revienta con
        `UnicodeEncodeError` en cuanto la salida no es UTF-8 —consola Windows legacy y, sobre todo,
        la salida a un PIPE, donde Python cae al ANSI codepage del locale (`cp1252` en un Windows
        español), que es exactamente cómo `release.py` lanza los checks—;
      - **lee de `sys.stdin`**: ahí no manda el fuente sino el PAYLOAD, así que un script ASCII puro
        revienta igual con `UnicodeDecodeError` en cuanto el JSON de entrada trae un emoji (así se
        apagaba el guardrail del implementer en T-04, y así `pick_asset.py` presentaba un fallo de
        codificación como «no hay binario para tu plataforma» — T-05).
    Aviso, no error: es una regla de robustez, y un plugin consumidor puede tener `.py` que ni
    imprimen ni leen de stdin — esos quedan FUERA del criterio y no se les avisa de nada.

    La comprobación es ESTRUCTURAL (`snippet_al_arrancar`): la marca dentro de `main()` o citada en
    un docstring NO cuenta, porque medido no protege de nada.
    """
    warns = []
    for p, rel in _py_del_plugin(root):
        data, texto = _leer(p)
        if data is None or not exige_snippet(data, texto):
            continue
        if snippet_al_arrancar(texto) is not False:
            continue
        motivos = []
        if any(b > 127 for b in data):
            motivos.append("imprime caracteres no ASCII")
        if lee_stdin(texto):
            motivos.append("lee de `sys.stdin`")
        warns.append(
            f"`{rel}`: {' y '.join(motivos)}, y no reconfigura los streams AL ARRANCAR — "
            f"en una consola cp1252 (o con la salida a un pipe en Windows) el primer print revienta "
            f"con UnicodeEncodeError, y el primer stdin.read() con UnicodeDecodeError. Copia el "
            f"snippet de 4 líneas tras los imports, a nivel de módulo — dentro de `main()` o citado "
            f"en un docstring no vale (CONVENTIONS regla 8, GOT-005); "
            f"`tests/test_console_encoding.py` lo prueba bajo cp1252")
    return warns


def lint_subprocess_encoding(root):
    """Avisos: `.py` del plugin que captura un subproceso en modo TEXTO sin `encoding=` (lado PADRE).

    La otra mitad de GOT-005, la que causó los dos fallos críticos de T-04: desde T-01 los hijos
    escriben UTF-8 SIEMPRE, así que el padre que los decodifique con el codec del locale revienta en
    consola cp1252 justo donde antes daba su veredicto (`task-brief.py` → `ledger-lint.py`).
    """
    warns = []
    for p, rel in _py_del_plugin(root):
        _data, texto = _leer(p)
        if texto is None:
            continue
        lineas = subprocess_sin_encoding(texto)
        if not lineas:
            continue
        donde = ", ".join(f"línea {n}" for n in lineas)
        warns.append(
            f"`{rel}`: captura un subproceso en modo texto SIN `encoding=` ({donde}) — los scripts "
            f"del plugin escriben UTF-8 siempre (CONVENTIONS regla 8), así que en una consola "
            f"cp1252 el PADRE revienta con UnicodeDecodeError al leerlos. Añade "
            f'`encoding="utf-8", errors="replace"` a la llamada (GOT-005, lado padre)')
    return warns


def lint_skill_sizes(root):
    """Avisos: `skills/<x>/SKILL.md` con más de SKILL_WARN_LINES líneas (el fichero entra completo en el
    contexto al invocar la skill; el detalle debe vivir en `references/` y leerse bajo demanda)."""
    warns = []
    sk = os.path.join(root, "skills")
    if not os.path.isdir(sk):
        return warns
    for d in sorted(os.listdir(sk)):
        p = os.path.join(sk, d, "SKILL.md")
        if not os.path.isfile(p):
            continue
        try:
            with open(p, encoding="utf-8", errors="replace") as f:
                n = sum(1 for _ in f)
        except OSError:
            continue
        if n > SKILL_WARN_LINES:
            warns.append(f"skill `{d}`: SKILL.md de {n} líneas (> {SKILL_WARN_LINES}) — token-diet: mueve el detalle a "
                         f"skills/{d}/references/<tema>.md y déjalo enlazado «léelo solo al llegar al paso X» "
                         f"(umbral duro {SKILL_HARD_LINES} en tests/test_skill_size.py)")
    return warns


def _cargar_evals_check(root):
    """Importa `evals/check.py` del plugin por ruta (módulo sin efectos secundarios) o None."""
    path = os.path.join(root, "evals", "check.py")
    if not os.path.isfile(path):
        return None
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("evals_check", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if all(hasattr(mod, f) for f in ("piezas", "cargar_casos", "nombre_fichero")):
            return mod
    except Exception:  # noqa: BLE001 — el linter degrada a su lector local
        pass
    return None


def _frontmatter_plegado(path):
    """Lector local mínimo (clave: valor de nivel 0, bloques `>`/`|` plegados) para las descriptions
    de skills/commands cuando `evals/check.py` no está disponible."""
    try:
        text = open(path, encoding="utf-8-sig").read()
    except (OSError, UnicodeDecodeError):
        return {}
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    out, key = {}, None
    for raw in text[3:end].splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw[0] not in " \t" and ":" in raw:
            key, val = raw.split(":", 1)
            key, val = key.strip(), val.strip()
            out[key] = "" if val in (">", "|", ">-", "|-") else val
        elif key and raw[0] in " \t":
            out[key] = (out.get(key, "") + " " + raw.strip()).strip()
    return out


def _piezas_local(root):
    out = {}
    sk = os.path.join(root, "skills")
    if os.path.isdir(sk):
        for d in sorted(os.listdir(sk)):
            p = os.path.join(sk, d, "SKILL.md")
            if os.path.isfile(p):
                out[f"skill:{d}"] = _frontmatter_plegado(p).get("description", "")
    for kind, sub in (("command", "commands"), ("agent", "agents")):
        dd = os.path.join(root, sub)
        if os.path.isdir(dd):
            for fn in sorted(os.listdir(dd)):
                if fn.endswith(".md"):
                    out[f"{kind}:{fn[:-3]}"] = _frontmatter_plegado(os.path.join(dd, fn)).get("description", "")
    return out


def lint_activacion(root):
    """Avisos de fiabilidad de activación: (a) pieza sin ≥ 1 caso positivo en evals/cases/ (solo si
    la carpeta existe); (b) description > DESC_WARN_CHARS caracteres."""
    warns = []
    check = _cargar_evals_check(root)
    repo = check.piezas(root) if check else _piezas_local(root)
    cases_dir = os.path.join(root, "evals", "cases")
    if check and os.path.isdir(cases_dir):
        positivos = {}
        for fn, data, err in check.cargar_casos(cases_dir):
            if err or not isinstance(data, dict):
                continue
            target = data.get("target")
            casos = data.get("cases") if isinstance(data.get("cases"), list) else []
            n = sum(1 for c in casos if isinstance(c, dict) and isinstance(c.get("expect"), dict)
                    and c["expect"].get("activates") is True)
            positivos[target] = positivos.get(target, 0) + n
        for target in sorted(repo):
            if positivos.get(target, 0) < 1:
                warns.append(f"{target}: sin caso positivo en evals/cases/{check.nombre_fichero(target)} — "
                             f"su description es una promesa de activación sin probar (ver evals/README.md)")
    for target in sorted(repo):
        n = len(repo.get(target) or "")
        if n > DESC_WARN_CHARS:
            warns.append(f"{target}: description de {n} caracteres (> {DESC_WARN_CHARS}) — token-diet: "
                         f"entra en el índice de piezas de cada arranque; recórtala a lo que dispara la activación")
    return warns


def _plega_acentos(s):
    """«revisión» → «revision» (NFD + fuera los diacríticos). La `ñ` también se plega: para comparar
    disparadores es lo que queremos («año» ≡ «ano» es un falso positivo aceptable; el coste de
    perder «revisión» ≢ «revision» era mucho mayor)."""
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


def _normaliza_disparador(frase):
    """minúsculas + espacios colapsados + ACENTOS PLEGADOS. El copiar-pegar entre piezas rara vez es
    byte a byte: una escribe «revisión de código» y la otra «revision de codigo» y el aviso no
    saltaba (T-fix1). Sigue siendo un match literal-tras-normalizar, no semántico: los solapes con
    frases distintas los caza la revisión humana (ADR-011)."""
    return _plega_acentos(" ".join(frase.strip().lower().split()))


def _cola_de_disparadores(desc):
    """Trozo de la `description` que va DESDE el marcador de disparadores («Úsalo/Úsala cuando…»,
    «Use when…») hasta el final: es el único sitio donde viven las frases que el usuario diría.
    Antes se miraba TODA la description, así que cualquier cita de ≥4 caracteres compartida (un
    nombre de fichero, un estado, un término del dominio) se anunciaba como disparador duplicado."""
    m = TRIGGER_RE.search(desc or "")
    return (desc or "")[m.start():] if m else ""


def lint_duplicate_triggers(root):
    """Aviso heurístico (ADR-011, `docs/agents/ROLES.md`): dos piezas (agente/skill/comando)
    DISTINTAS declaran en su `description` el MISMO disparador literal entrecomillado.

    Dos acotaciones que evitan ruido y falsos negativos (T-fix1): se compara normalizado en
    minúsculas, espacios **y acentos** («revisión de código» ≡ «Revision de codigo»), y solo cuentan
    las frases de ≥ `MIN_PALABRAS_DISPARADOR` palabras que aparecen DESPUÉS del marcador de
    disparadores («Úsalo/Úsala cuando…», «Use when…») — no cualquier cita de la description, que
    hacía saltar el aviso por un nombre de fichero o un término del dominio compartido.

    Es la colisión más barata de cazar (copiar un disparador de una pieza a otra sin darse cuenta) —
    NO detecta solapes semánticos con frases distintas (los cuatro que resolvió ADR-011 lo eran;
    esos los sigue cazando la revisión humana en la puerta de "pieza nueva" de
    skills/plugin-dev/SKILL.md)."""
    check = _cargar_evals_check(root)
    repo = check.piezas(root) if check else _piezas_local(root)
    por_frase = {}
    for target in sorted(repo):
        for m in QUOTED_RE.finditer(_cola_de_disparadores(repo.get(target) or "")):
            frase = _normaliza_disparador(m.group(1))
            if len(frase.split()) < MIN_PALABRAS_DISPARADOR:
                continue   # ruido: vocabulario compartido, no un disparador
            por_frase.setdefault(frase, []).append(target)
    warns = []
    for frase, targets in sorted(por_frase.items()):
        vistos = sorted(set(targets))
        if len(vistos) > 1:
            warns.append(f"disparador duplicado \"{frase}\" en {', '.join(vistos)} — "
                         f"¿copiado de una pieza a otra? (comparado en minúsculas y sin acentos; "
                         f"docs/agents/ROLES.md, ADR-011)")
    return warns


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
    # árbol github-templates.MANUAL-COPY/ → .github/ (issue forms + PR template; distribution T-03)
    arbol = os.path.join(root, "github-templates.MANUAL-COPY")
    if os.path.isdir(arbol):
        for dirpath, _dirs, files in os.walk(arbol):
            for f in sorted(files):
                src = os.path.join(dirpath, f)
                rel = os.path.relpath(src, arbol).replace(os.sep, "/")
                dst = os.path.join(root, ".github", rel)
                if not os.path.isfile(dst):
                    continue
                try:
                    if open(src, "rb").read() != open(dst, "rb").read():
                        warns.append(f"github-templates.MANUAL-COPY/{rel} y .github/{rel} difieren — copia manual "
                                     f"pendiente: `cp github-templates.MANUAL-COPY/{rel} .github/{rel}`")
                except OSError:
                    continue
    return warns


HOOK_PATH_RE = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/([^\s\"']+)")


def _es_ejecutable(fp):
    """Bit ejecutable según el índice de git (100755) si el fichero está versionado; si no, os.access."""
    try:
        import subprocess
        r = subprocess.run(["git", "ls-files", "-s", "--", os.path.basename(fp)],
                           cwd=os.path.dirname(fp), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=5)
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
