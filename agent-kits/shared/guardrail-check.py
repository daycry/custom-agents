#!/usr/bin/env python3
"""
guardrail-check.py — guardrails DETERMINISTAS del `implementer` (hook PreToolUse).

Las reglas se comparten entre wrappers locales de agentes y el dispatcher
native-guardrail.py. El dispatcher selecciona solo IDs propios desde metadata
nativa; planner/evaluator/analyst y la sesión principal mantienen sus permisos.
Los hooks del frontmatter no se ejecutan en agentes Claude de plugin ni en TOML
Codex. Registro y límites: docs/knowledge/adr/ADR-023-guardias-por-identidad-nativa.md.

Uso:
  guardrail-check.py pre-tool [--project-dir DIR] [--agent implementer|architect]   # JSON del hook por stdin
  (sin --agent: $CLAUDE_AGENT_NAME si existe, si no `implementer`)

Modo `architect` (parity-core T-fix1, wrapper hooks/architect-guardrail.sh; enmienda a ADR-007):
  alcance        permitido SOLO `docs/roadmap/<inic>/design.md`; memoria mediante servicio,
                 sin Write/Edit directo. `spec.md`/`improvement-plan.md` de la iniciativa SOLO con
                 la herramienta Edit y si `old_string`/`new_string` contienen `design:` o `design.md`
                 (el enlace de la regla 7) — un Write completo o un Edit sin esa marca → deny. Riesgo
                 asumido y documentado: un Edit que incluya `design:` junto a otros cambios pasa (el
                 hook no puede diffear el fichero); lo caza la Lente A. Todo lo demás (código,
                 tasks.md, evaluation.md, gotchas/lessons, security-scan) → deny.
  git            igual que el implementer. ramaPrincipal NO aplica (escribe solo documentos, como planner).

Reglas (cada una desactivable en `.claude/dev.json` → `"guardrails": {…}`):
  alcance        Write/Edit/MultiEdit/NotebookEdit sobre docs/roadmap/** que no sea `tasks.md`
                 (incl. testing/**, que es de qa) → deny. docs/security-scan/** → deny.
                 docs/knowledge/** → deny en herramientas directas; conocimiento nuevo mediante
                 knowledge-curation.py. Rutas CASE-INSENSITIVE
                 (`Docs/Roadmap/x/Spec.md` también deny: Windows/macOS no distinguen mayúsculas).
                 Excepción en la raíz de docs/roadmap/: `README.md` (índice de iniciativas, que el
                 cierre de cada iniciativa actualiza) → permitido. `CALIBRATION.md`, `DRIFT.md` y
                 `BACKLOG.md` siguen deny POR DISEÑO: los escriben /retro, /spec-drift y /pm-backlog,
                 que son comandos (no pasan por este hook), no el implementer.
  git            Bash: `git commit --no-verify|-n` y overrides explícitos de core.hooksPath en commit → deny;
                 `git push --force|-f|--force-with-lease` → deny; `git branch -D` → deny;
                 `git reset --hard`, `git clean -f*` (simulación solo con `-n` exacto o `--dry-run`, sin
                 `--no-dry-run`), `git push --delete|-d|--mirror|--prune` o refspec `:rama`,
                 `git stash drop|clear`, `git branch -D|-M|-C|-f|--force`, `git update-ref -d|--stdin`
                 → deny (auditoría 2026-11-09, H-12). Toda opción larga destructiva se reconoce por
                 CUALQUIER prefijo (`--h`, `--m`, `--force-w`). `git clean` se analiza de verdad (`--`
                 separa rutas, `-e`/`--exclude` consumen valor, gana el último de `-n`/`--dry-run`).
                 Configuración por LISTA BLANCA (`_CONFIG_PERMITIDA`): `-c`/`--config-env` y las
                 escrituras de `git config` solo con user.name, user.email, core.quotepath,
                 commit.gpgsign, init.defaultBranch, color.*, advice.*; `--file`/`--blob`, secciones y
                 `--edit` → deny. Variables `GIT_*`, `HOME`, `XDG_CONFIG_HOME` (sin distinguir
                 mayúsculas; prefijo, `env`, `export`, `set`) solo cuando la orden ejecuta git → deny.
                 Opciones globales desconocidas → deny. Evita accidentes y formas conocidas; NO es un
                 sandbox (envoltorios nice/sudo/xargs, scripts propios y configs editadas a mano
                 quedan fuera: ADR-023, ADR-007);
                 `git checkout|switch main|master` → deny solo si la rama actual es una feature;
                 `git checkout -f`, `checkout|restore .`, `restore --worktree|-W`, `switch --discard-changes` → deny
                 (descartan cambios sin comitear; `checkout main -- <fichero>` y `checkout -b` siguen);
                 `rm -rf` sobre `/`, `~`, `.git`, `.` → deny; refspec `+rama` en push = force;
                 se analizan también las cadenas de `sh -c "…"`/`bash -c '…'`.
                 Misma regla, órdenes con efecto fuera del repo: `npm|pnpm|yarn publish`,
                 `docker|podman system|volume prune`, `kubectl delete` (las dos con `--dry-run` se
                 permiten) y `DROP TABLE|DATABASE|SCHEMA` como argumento de psql/mysql/mariadb/sqlite3
                 → deny. Análisis literal: SQL desde fichero o tubería no se ve. Todo lo demás permitido.
  ramaPrincipal  HEAD en main/master + Write/Edit fuera de docs/roadmap/**/tasks.md → deny.
                 Sin git → no aplica.
  `"guardrails": false` apaga todo (aviso una vez por proyecto vía systemMessage).
  Fichero ausente/corrupto → defaults (todo activo).

Salida: contrato oficial de PreToolUse (https://code.claude.com/docs/en/hooks.md, 2026-09-02):
  deny  → stdout {"hookSpecificOutput": {"hookEventName": "PreToolUse",
                  "permissionDecision": "deny", "permissionDecisionReason": "…"}} · exit 0
  allow → sin stdout · exit 0 (sin decisión: sigue el flujo normal de permisos)
Nunca exit ≠ 0 por error interno: se registra en stderr y se permite (un guardrail roto no
debe convertirse en un bloqueo fantasma).
"""
import argparse
import json
import os
import posixpath
import re
import shlex
import subprocess
import sys
import time

# Consola Windows (cp1252) o tuberías: reconfigurar ANTES de leer o imprimir nada (GOT-005).
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure, ya leído o None (capsys, pythonw)

WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
MAIN_BRANCHES = {"main", "master"}
DEFAULTS = {"alcance": True, "git": True, "ramaPrincipal": True}


# ---------------------------------------------------------------- config ----
def load_config(project_dir, max_bytes=None):
    """Devuelve (config dict con las 3 claves, activo bool). Nunca lanza."""
    path = os.path.join(project_dir, ".claude", "dev.json")
    try:
        if max_bytes is None:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
        else:
            with open(path, "rb") as fh:
                raw = fh.read(max_bytes + 1)
            if len(raw) > max_bytes:
                raise ValueError("config limit")
            data = json.loads(raw.decode("utf-8"))
    except (OSError, ValueError, UnicodeDecodeError):
        return dict(DEFAULTS), True
    g = data.get("guardrails", True) if isinstance(data, dict) else True
    if g is False:
        return {k: False for k in DEFAULTS}, False
    cfg = dict(DEFAULTS)
    if isinstance(g, dict):
        for k in DEFAULTS:
            if k in g:
                cfg[k] = bool(g[k])
    return cfg, True


# ----------------------------------------------------------------- rutas ----
def normalize_path(p, project_dir):
    """`\\`→`/`, absolutas bajo el proyecto → relativas, sin `./` inicial."""
    if not isinstance(p, str) or not p:
        return ""
    p = p.replace("\\", "/")
    root = (project_dir or "").replace("\\", "/").rstrip("/")
    if root and (p == root or p.startswith(root + "/")):
        p = p[len(root):].lstrip("/")
    # Windows: C:/proy/docs/… no bajo el proyecto → se deja tal cual (los patrones buscan
    # `docs/roadmap/` en cualquier posición, así que sigue casando).
    # normpath resuelve `./` y `..` (docs/roadmap/x/../../src/a.py es src/a.py, no roadmap —
    # falso positivo cazado por la revisión); las cadenas vacías/`.` no son rutas.
    p = posixpath.normpath(p) if p else ""
    return "" if p == "." else p


def extract_paths(tool_input):
    paths = []
    if not isinstance(tool_input, dict):
        return paths
    for k in ("file_path", "notebook_path", "path"):
        v = tool_input.get(k)
        if isinstance(v, str):
            paths.append(v)
    for e in tool_input.get("edits", []) if isinstance(tool_input.get("edits"), list) else []:
        if isinstance(e, dict) and isinstance(e.get("file_path"), str):
            paths.append(e["file_path"])
    return paths


# re.I: `Docs/Roadmap/x/Spec.md` casa igual (deuda de deterministic-guardrails: los patrones eran
# case-sensitive «como git en Linux», pero el implementer también corre en Windows/macOS).
_ROADMAP_RE = re.compile(r"(?:^|/)docs/roadmap/(.*)$", re.I)
_SECSCAN_RE = re.compile(r"(?:^|/)docs/security-scan(?:/|$)", re.I)
# Único fichero de la RAÍZ de docs/roadmap/ que el implementer puede tocar: el índice de iniciativas
# (lo actualiza el cierre de cada iniciativa). CALIBRATION/DRIFT/BACKLOG los escriben comandos.
_RAIZ_PERMITIDOS = {"readme.md"}


def es_ledger(rel):
    """docs/roadmap/<algo>/…/tasks.md fuera de testing/ (lo único del roadmap que toca el implementer),
    o docs/roadmap/README.md (índice). Comparación en minúsculas."""
    m = _ROADMAP_RE.search(rel)
    if not m:
        return False
    partes = [x.lower() for x in m.group(1).split("/")]
    if len(partes) == 1:
        return partes[0] in _RAIZ_PERMITIDOS
    return partes[-1] == "tasks.md" and "testing" not in partes[:-1]


_DESIGN_MARK_RE = re.compile(r"design:|design\.md", re.I)


def _inic_fichero(rel):
    """(carpeta-iniciativa, nombre) para docs/roadmap/<inic>/<fichero> (2 niveles), o (None, None)."""
    m = _ROADMAP_RE.search(rel)
    if not m:
        return None, None
    partes = m.group(1).split("/")
    if len(partes) != 2:
        return None, None
    return partes[0], partes[1].lower()


def _memory_write_reason(rel):
    """Memory persistence belongs to its services, including legacy trees."""
    if re.search(r"(?:^|/)docs/knowledge(?:/|$)", rel, re.I):
        return (f"«{rel}»: la memoria no se modifica con Write/Edit directo. "
                "Propón conocimiento nuevo con knowledge-curation.py y knowledge-write.md; "
                "el journal y los índices los persisten sus servicios. Conserva el legado.")
    return None


def check_alcance_architect(rel, tool, tool_input):
    """Razón de deny o None — alcance del `architect` (diseño/enlaces; memoria mediante servicio)."""
    if _SECSCAN_RE.search(rel):
        return f"«{rel}» está bajo docs/security-scan/ (propiedad de nemesis): el architect no escribe ahí."
    memory_reason = _memory_write_reason(rel)
    if memory_reason:
        return memory_reason
    inic, fn = _inic_fichero(rel)
    if inic and fn == "design.md":
        return None
    if inic and fn in ("spec.md", "improvement-plan.md"):
        if tool != "Edit":
            return (f"«{rel}»: el architect solo añade el enlace `design:` (frontmatter + callout) a spec/plan, "
                    f"y solo con Edit — no reescribas el fichero (Write); el contenido es de analyst/planner.")
        blob = " ".join(str(tool_input.get(k, "")) for k in ("old_string", "new_string"))
        if _DESIGN_MARK_RE.search(blob):
            return None
        return (f"«{rel}»: el architect solo toca el enlace `design:`/`design.md` de spec/plan (regla 7 de "
                f"CONVENTIONS); ese Edit no lo contiene — deja la observación en «Preguntas abiertas» de design.md.")
    return (f"«{rel}» está fuera del alcance del architect: escribe SOLO docs/roadmap/<inic>/design.md, el enlace "
            f"`design:` en spec/plan (Edit). Ni código, ni tasks.md, ni "
            f"evaluation.md — anótalo en «Preguntas abiertas» de design.md y sigue.")


def check_alcance(rel):
    """Razón de deny o None."""
    if _SECSCAN_RE.search(rel):
        return (f"«{rel}» está bajo docs/security-scan/ (propiedad de nemesis): el implementer "
                f"no escribe ahí — deja el hallazgo en tasks.md y sigue.")
    memory_reason = _memory_write_reason(rel)
    if memory_reason:
        return memory_reason
    m = _ROADMAP_RE.search(rel)
    if m and not es_ledger(rel):
        if "/testing/" in ("/" + m.group(1)).lower():
            return (f"«{rel}» está bajo docs/roadmap/**/testing/ (propiedad de qa): el implementer "
                    f"solo toca tasks.md en docs/roadmap/ — no escribas informes de prueba.")
        if "/" not in m.group(1):
            return (f"«{rel}» está en la raíz de docs/roadmap/: el implementer solo toca README.md (índice) "
                    f"ahí; CALIBRATION.md, DRIFT.md y BACKLOG.md los escriben /retro, /spec-drift y "
                    f"/pm-backlog — anota la duda en tasks.md y sigue.")
        if m.group(1).lower().endswith("/design.md"):
            return (f"«{rel}» está en docs/roadmap/: el implementer solo toca tasks.md (ledger); "
                    f"el diseño lo cambia architect — anota la duda en tasks.md y sigue.")
        return (f"«{rel}» está en docs/roadmap/: el implementer solo toca tasks.md (ledger); "
                f"el plan/spec/evaluación los cambia planner — anota la duda en tasks.md y sigue.")
    return None


# ------------------------------------------------------------------- git ----
def current_branch(project_dir, timeout=5):
    """Nombre de la rama o None si no hay git / no se puede saber."""
    started = time.monotonic()
    try:
        r = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=project_dir or None,
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
        if r.returncode != 0:
            remaining = timeout - (time.monotonic() - started)
            if remaining <= 0:
                return None
            # HEAD is a valid symbolic branch even before its first commit.
            r = subprocess.run(["git", "symbolic-ref", "--quiet", "--short", "HEAD"], cwd=project_dir or None,
                               capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=remaining)
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode != 0:
        return None
    b = r.stdout.strip()
    return b or None


def _segmentos(command):
    """Literal shell words and command boundaries, retaining quoted punctuation as data.

    No expansion, substitution or execution. Newlines outside quotes separate commands;
    escaped newlines continue the same command. Invalid quoting cannot execute as given.
    """
    out, cur, word = [], [], []
    quote, started, i = None, False, 0
    while i < len(command):
        char = command[i]
        if char == "\\" and quote is None and i + 1 == len(command):
            return out  # Keep already complete commands; this final word is incomplete.
        if char == "\\" and quote != "'" and i + 1 < len(command):
            following = command[i + 1]
            if following == "\n":
                i += 2
                continue
            if quote is None or following in '\\"$`':
                word.append(following)
                started = True
                i += 2
                continue
        if quote:
            if char == quote:
                quote = None
            else:
                word.append(char)
        elif char in "\"'":
            quote, started = char, True
        elif char == "#" and not started:
            newline = command.find("\n", i)
            i = len(command) if newline < 0 else newline
            continue
        elif char in " \t\r\n;&|":
            if started:
                cur.append("".join(word))
                word, started = [], False
            if char in "\n;&|" and cur:
                out.append(cur)
                cur = []
        else:
            word.append(char)
            started = True
        i += 1
    if quote:
        return out
    if started:
        cur.append("".join(word))
    if cur:
        out.append(cur)
    return out


_ASSIGNMENT_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)=(.*)\Z", re.DOTALL)
# Opciones globales de git 2.4x que toman su valor en el TOKEN SIGUIENTE (revisión intento 2).
_GIT_GLOBAL_VALUES = frozenset(("-C", "-c", "--git-dir", "--work-tree", "--namespace", "--config-env",
                                "--super-prefix", "--attr-source", "--list-cmds"))
# Opciones globales sin valor separado (o con `=` en el mismo token). Cualquier otra opción
# global se trata de forma conservadora: el guardarraíl no adivina si consume un valor.
_GIT_GLOBAL_FLAGS = frozenset(("-v", "--version", "-h", "--help", "-p", "--paginate", "-P", "--no-pager",
                               "--no-replace-objects", "--no-lazy-fetch", "--no-optional-locks",
                               "--no-advice", "--bare", "--literal-pathspecs", "--glob-pathspecs",
                               "--noglob-pathspecs", "--icase-pathspecs", "--exec-path", "--html-path",
                               "--man-path", "--info-path"))
_GIT_GLOBAL_EQ = ("--git-dir=", "--work-tree=", "--namespace=", "--super-prefix=", "--config-env=",
                  "--attr-source=", "--list-cmds=", "--exec-path=")
# Unique value-option prefixes in Git's commit parser; --fi and --t are ambiguous.
_COMMIT_LONG_VALUES = {
    "--m": "--message", "--fil": "--file", "--reu": "--reuse-message",
    "--ree": "--reedit-message", "--fix": "--fixup", "--sq": "--squash",
    "--au": "--author", "--da": "--date", "--te": "--template",
    "--tr": "--trailer", "--c": "--cleanup", "--pathspec-fr": "--pathspec-from-file",
}


def _program_name(token):
    name = token.replace("\\", "/").rsplit("/", 1)[-1].lower()
    return name[:-4] if name.endswith(".exe") else name


def _literal_invocation(toks, inherited=None):
    """Unwrap only literal assignment/env/command/exec prefixes; never evaluate shell text."""
    bindings = dict(inherited or {})
    i = 0
    while i < len(toks):
        assignment = _ASSIGNMENT_RE.fullmatch(toks[i])
        if assignment:
            bindings[assignment[1]] = assignment[2]
            i += 1
        elif _program_name(toks[i]) in ("env", "command", "exec"):
            wrapper = _program_name(toks[i])
            i += 1
            while i < len(toks) and toks[i].startswith("-") and toks[i] != "--":
                option = toks[i]
                if wrapper == "env" and option in ("-", "-i", "--ignore-environment"):
                    bindings.clear()
                elif wrapper == "env" and option in ("-u", "--unset") and i + 1 < len(toks):
                    i += 1
                    bindings.pop(toks[i], None)
                elif wrapper == "env" and option.startswith("--unset="):
                    bindings.pop(option.split("=", 1)[1], None)
                elif wrapper == "env" and option in ("-C", "--chdir") and i + 1 < len(toks):
                    i += 1  # Directory changes do not change verification flags.
                elif wrapper == "env" and option.startswith("--chdir="):
                    pass
                elif wrapper == "command" and option == "-p":
                    pass
                elif wrapper in ("env", "exec") and not option.startswith("--"):
                    offset = 1
                    valid = True
                    while offset < len(option):
                        flag = option[offset]
                        if (wrapper == "env" and flag == "i") or (wrapper == "exec" and flag == "c"):
                            bindings.clear()
                        elif wrapper == "exec" and flag == "l":
                            pass
                        elif (wrapper == "env" and flag in "uC") or (wrapper == "exec" and flag == "a"):
                            value = option[offset + 1:]
                            if not value:
                                if i + 1 >= len(toks):
                                    valid = False
                                    break
                                i += 1
                                value = toks[i]
                            if wrapper == "env" and flag == "u":
                                bindings.pop(value, None)
                            break
                        else:
                            valid = False
                            break
                        offset += 1
                    if not valid:
                        break
                else:
                    break  # Unknown syntax is outside this literal grammar.
                i += 1
            if i < len(toks) and toks[i] == "--":
                i += 1
        else:
            break
    return toks[i:], bindings


def _git_invocation(toks):
    """Locate the Git subcommand and explicit hooksPath overrides, consuming global values."""
    if not toks or _program_name(toks[0]) != "git":
        return -1, False
    i = 1
    hooks_override = False
    while i < len(toks) and toks[i].startswith("-"):
        option = toks[i]
        config = None
        if option in _GIT_GLOBAL_VALUES:
            if i + 1 >= len(toks):
                return -1, False
            if option in ("-c", "--config-env"):
                config = toks[i + 1]
            i += 2
        else:
            if option.startswith("-c") and not option.startswith("--"):
                config = option[2:]
            elif option.startswith("--config-env="):
                config = option.split("=", 1)[1]
            i += 1
        if config is not None and config.split("=", 1)[0].lower() == "core.hookspath":
            hooks_override = True
    return (i if i < len(toks) else -1), hooks_override


def _es_git(toks, sub):
    """Index of a recognized Git subcommand, or -1."""
    i, _override = _git_invocation(toks)
    return i if i >= 0 and toks[i] == sub else -1


def _commit_skips_verification(args):
    skips = False
    i = 0
    while i < len(args):
        token = args[i]
        if token == "--":
            break
        if len(token) > 2 and "--no-verify".startswith(token):
            skips = True
        elif (len(token) >= len("--veri") and "--verify".startswith(token)) or (
                len(token) >= len("--no-no-veri") and "--no-no-verify".startswith(token)):
            skips = False
        elif any(
                token.startswith(prefix) and option.startswith(token)
                for prefix, option in _COMMIT_LONG_VALUES.items()):
            i += 1
        elif token.startswith("-") and not token.startswith("--"):
            for offset, flag in enumerate(token[1:], 1):
                if flag == "n":
                    skips = True
                elif flag in "mFCct":
                    if offset == len(token) - 1:
                        i += 1
                    break
                elif flag in "Su":
                    break  # Optional short values attach to this same token.
        i += 1
    return skips


_SHELLS = {"sh", "bash", "zsh", "dash", "ksh"}

# Órdenes cuyo efecto cae FUERA del repositorio y no se deshace desde él (registro público,
# estado del host, clúster, base de datos). Análisis literal de la invocación, como el resto
# de reglas Bash: un SQL leído de fichero (`psql -f x.sql`) o por tubería no se ve; lo cubre
# la revisión del diff. `--dry-run` no produce el efecto y se permite.
_PAQUETEROS = {"npm", "pnpm", "yarn"}
_PAQUETE_COMO_ARG = {"install", "i", "add", "uninstall", "remove", "rm", "un", "view", "info",
                     "show", "search", "help", "docs", "why", "ls", "list", "outdated"}
_CONTENEDORES = {"docker", "podman"}
_CLIENTES_SQL = {"psql", "mysql", "mariadb", "sqlite3"}
_SQL_DESTRUCTIVO_RE = re.compile(r"\bDROP\s+(?:TABLE|DATABASE|SCHEMA)\b", re.I)


def _es_simulacion(toks):
    return any(t == "--dry-run" or (t.startswith("--dry-run=") and t != "--dry-run=none") for t in toks)


def check_ordenes_externas(toks):
    """Razón de deny o None para publicar paquetes, purgar el host de contenedores, borrar
    recursos de un clúster o ejecutar `DROP TABLE|DATABASE|SCHEMA` con un cliente SQL."""
    if not toks:
        return None
    prog = _program_name(toks[0])
    palabras = [t for t in toks[1:] if not t.startswith("-")]
    if prog in _PAQUETEROS and "publish" in palabras and not _es_simulacion(toks) \
            and palabras[0] not in _PAQUETE_COMO_ARG:
        return (f"`{prog} publish` bloqueado: publica en un registro público y no se puede retirar "
                f"limpiamente — la publicación es del usuario o de la release; usa `--dry-run` para verificar.")
    if prog in _CONTENEDORES and len(palabras) >= 2 and palabras[0] in ("system", "volume") \
            and palabras[1] == "prune":
        return (f"`{prog} {palabras[0]} prune` bloqueado: purga contenedores, imágenes o volúmenes de TODO "
                f"el host, no solo de este proyecto — limpia los del proyecto (`compose down`) o que lo "
                f"ejecute el usuario.")
    if prog == "kubectl" and "delete" in palabras and not _es_simulacion(toks):
        return ("`kubectl delete` bloqueado: borra recursos del clúster del contexto activo, que puede no "
                "ser local — usa `--dry-run=client` para verificar y deja el borrado al usuario.")
    for i, t in enumerate(toks):
        if _program_name(t) in _CLIENTES_SQL:
            if any(_SQL_DESTRUCTIVO_RE.search(a) for a in toks[i + 1:]):
                return ("`DROP TABLE|DATABASE|SCHEMA` con un cliente SQL bloqueado: destruye datos que el "
                        "repositorio no restaura — escríbelo como migración revisable o que lo ejecute el usuario.")
            break
    return None


def _subcomandos_shell(toks):
    """Cadenas que una shell ejecutaría como comando: el argumento de `-c` de sh/bash/zsh/dash
    (también en clusters `-lc`, `-ec`) y los argumentos de `eval`."""
    if not toks:
        return []
    prog = _program_name(toks[0])
    if prog == "eval":
        return [" ".join(toks[1:])] if len(toks) > 1 else []
    if prog in _SHELLS:
        for i, t in enumerate(toks[1:], 1):
            if re.fullmatch(r"-[a-zA-Z]*c[a-zA-Z]*", t) and i + 1 < len(toks):
                return [toks[i + 1]]
    return []


def _prefijo(token, *opciones):
    """¿`token` es `--<p>` (≥ 1 carácter tras `--`) prefijo de alguna opción? Git acepta cualquier
    prefijo único de una opción larga; si es ambiguo la rechaza, así que denegar de más es seguro."""
    if not token.startswith("--") or len(token) < 3:
        return False
    base = token.split("=", 1)[0]
    return any(op.startswith(base) for op in opciones)


def _cluster(token, letra):
    """`-abc` (clúster de opciones cortas) que contiene `letra`."""
    return bool(re.fullmatch(r"-[a-zA-Z0-9]+", token)) and letra in token[1:]


# LISTA BLANCA de configuración en línea y de `git config` (revisión intento 3). Todo lo demás
# se deniega: cualquier otra clave puede ejecutar una orden (core.editor, core.pager,
# core.sshCommand, diff.external, alias.*), saltar hooks (core.hooksPath), relajar la confianza
# (safe.directory), cargar otra config (include*) o cambiar qué borra un push (remote.*).
#   user.name / user.email   identidad del commit; no ejecutan nada
#   core.quotepath           solo cómo se escriben las rutas en la salida
#   commit.gpgsign           SOLO con valor verdadero (fix3b): activar la firma; desactivarla se deniega
#   init.defaultbranch       nombre de la rama inicial de `git init`
#   color.* / advice.*       presentación y mensajes de ayuda
_CONFIG_PERMITIDA = frozenset(("user.name", "user.email", "core.quotepath", "commit.gpgsign",
                               "init.defaultbranch"))
_CONFIG_PERMITIDA_PREFIJOS = ("color.", "advice.")


# Claves de la lista blanca que solo valen con valor VERDADERO (revisión fix3b): desactivar la firma
# de commits es saltarse una puerta, como `--no-verify`.
_CONFIG_SOLO_VERDADERO = frozenset(("commit.gpgsign",))
_VERDADERO = ("true", "yes", "on", "1")


def _config_permitida(clave, valor="true"):
    """¿Clave de la lista blanca y, si exige verdadero, con un valor verdadero conocido?"""
    clave = clave.lower()
    if not (clave in _CONFIG_PERMITIDA or clave.startswith(_CONFIG_PERMITIDA_PREFIJOS)):
        return False
    if clave in _CONFIG_SOLO_VERDADERO:
        return valor is not None and valor.strip().lower() in _VERDADERO
    return True


def _env_sensible(nombre):
    """Variables que cambian qué config, qué repo o qué programas usa git (sin distinguir mayúsculas)."""
    n = str(nombre).upper()
    return n.startswith("GIT_") or n in ("HOME", "XDG_CONFIG_HOME")


_EXPORTADORES = ("export", "set", "setenv", "typeset", "declare", "local", "readonly")


def _globales(toks):
    """(pares (clave, valor|None) de `-c`/`--config-env`, opción desconocida|None)."""
    pares, desconocida = [], None
    i = 1
    while i < len(toks) and toks[i].startswith("-"):
        option, config, por_env = toks[i], None, False
        if option in _GIT_GLOBAL_VALUES:
            if i + 1 >= len(toks):
                break
            if option == "-c":
                config = toks[i + 1]
            elif option == "--config-env":
                config, por_env = toks[i + 1], True
            i += 2
        elif option.startswith("-c") and not option.startswith("--"):
            config = option[2:]
            i += 1
        elif option.startswith("--config-env="):
            config, por_env = option.split("=", 1)[1], True
            i += 1
        elif option in _GIT_GLOBAL_FLAGS or option.startswith(_GIT_GLOBAL_EQ):
            i += 1
        else:
            desconocida = option
            break
        if config is not None:
            clave, igual, valor = config.partition("=")
            # `--config-env=k=VAR`: el valor está en el entorno → desconocido (None).
            # Sin `=` git lo toma como verdadero, pero aquí «sin valor» es desconocido (None), igual
            # que `--config-env` (el valor está en el entorno): ninguno cuenta como verdadero.
            pares.append((clave.lower(), valor if igual and not por_env else None))
    return pares, desconocida


_CONFIG_LARGAS = ("--global", "--system", "--local", "--worktree", "--file", "--blob", "--get", "--get-all",
                  "--get-regexp", "--get-urlmatch", "--replace-all", "--add", "--unset", "--unset-all",
                  "--rename-section", "--remove-section", "--list", "--fixed-value", "--type", "--no-type",
                  "--bool", "--int", "--bool-or-int", "--bool-or-str", "--path", "--expiry-date", "--null",
                  "--name-only", "--includes", "--no-includes", "--show-origin", "--show-scope",
                  "--get-color", "--get-colorbool", "--edit", "--default", "--comment", "--value", "--all",
                  "--regexp", "--url")
_CONFIG_CON_VALOR = ("--file", "--blob", "--type", "--default", "--comment", "--value", "--url")
_CONFIG_LECTURA = ("--get", "--get-all", "--get-regexp", "--get-urlmatch", "--list", "--get-color",
                   "--get-colorbool")
_CONFIG_ESCRITURA = ("--replace-all", "--add", "--unset", "--unset-all", "--rename-section",
                     "--remove-section", "--edit")


def _resuelve(token, opciones):
    """Opción larga a la que corresponde `token` (exacta o prefijo único), o None si es ambigua/desconocida."""
    base = token.split("=", 1)[0]
    if base in opciones:
        return base
    hits = [o for o in opciones if o.startswith(base)]
    return hits[0] if len(hits) == 1 else None


def _razon_git_config(args):
    """`git config`: lecturas permitidas; escrituras solo de claves de la lista blanca, sin --file/--blob."""
    sub = args[0] if args and args[0] in ("get", "list", "set", "unset", "rename-section",
                                           "remove-section", "edit") else None
    if sub in ("get", "list"):
        return None
    if sub in ("rename-section", "remove-section", "edit"):
        return f"`git config {sub}` bloqueado: reescribe secciones o abre un editor sobre la configuración."
    resto = args[1:] if sub else args
    acciones, fichero, posicionales = set(), False, []
    i = 0
    while i < len(resto):
        t = resto[i]
        if t == "--":
            posicionales += resto[i + 1:]
            break
        if t.startswith("--"):
            op = _resuelve(t, _CONFIG_LARGAS)
            if op is None:
                return f"`git config {t}` bloqueado: opción desconocida o ambigua; escribe la opción completa."
            if op in _CONFIG_CON_VALOR and "=" not in t:
                i += 1
            if op in ("--file", "--blob"):
                fichero = True
            if op in _CONFIG_LECTURA or op in _CONFIG_ESCRITURA:
                acciones.add(op)
        elif t.startswith("-") and len(t) > 1:
            for j, ch in enumerate(t[1:], 1):
                if ch == "f":
                    fichero = True
                    if j == len(t) - 1:
                        i += 1
                    break
                if ch == "l":
                    acciones.add("--list")
                elif ch == "e":
                    acciones.add("--edit")
        else:
            posicionales.append(t)
        i += 1
    escritura = bool(sub) or bool(acciones & set(_CONFIG_ESCRITURA)) or (
        not acciones and len(posicionales) >= 2)
    if not escritura:
        return None
    if acciones & {"--rename-section", "--remove-section", "--edit"}:
        return "`git config` que renombra, borra secciones o abre el editor bloqueado."
    if fichero:
        return "`git config --file/--blob` de escritura bloqueado: escribe una configuración que el guardarraíl no controla."
    clave = posicionales[0] if posicionales else ""
    valor = posicionales[1] if len(posicionales) > 1 and not acciones & {"--unset", "--unset-all"} \
        and sub != "unset" else None
    if not _config_permitida(clave, valor if clave.lower() in _CONFIG_SOLO_VERDADERO else "true"):
        return (f"`git config` que escribe `{clave or '?'}` bloqueado: solo se escriben claves de la lista "
                "blanca (user.name, user.email, core.quotepath, commit.gpgsign solo a verdadero, init.defaultBranch, color.*, "
                "advice.*) — si hace falta otra, que la ponga el usuario.")
    return None


def _razon_config(toks, bindings, exportados=()):
    """Configuración y entorno de git, por LISTA BLANCA (revisión intento 3)."""
    if not toks or _program_name(toks[0]) != "git":
        return None
    nombres = sorted({k for k in (bindings or {}) if _env_sensible(k)} | set(exportados))
    if nombres:
        return (f"entorno de git bloqueado ({', '.join(nombres)}): cambia la config, el repo o los programas "
                "que ejecuta git (editor, ssh, hooks) sin que el guardarraíl lo vea.")
    pares, desconocida = _globales(toks)
    if desconocida:
        return (f"opción global de git no reconocida (`{desconocida}`) bloqueada: el guardarraíl no puede "
                "saber si consume un valor y desplazaría el subcomando — escribe la orden sin ella.")
    for clave, valor in pares:
        if not _config_permitida(clave, valor):
            return (f"configuración de git en línea bloqueada (`{clave}`): fuera de la lista blanca puede ejecutar "
                    "órdenes, saltar hooks o cambiar qué se borra.")
    i = _es_git(toks, "config")
    if i >= 0:
        return _razon_git_config(toks[i + 1:])
    return None


def _razon_clean(args):
    """`git clean`: análisis real de argumentos (revisión intento 3)."""
    forzado = simulado = False
    i = 0
    while i < len(args):
        t = args[i]
        if t == "--":
            break                                   # lo que sigue son rutas
        if t.startswith("--"):
            op = _resuelve(t, ("--force", "--no-force", "--dry-run", "--no-dry-run", "--quiet", "--no-quiet",
                               "--interactive", "--exclude"))
            if op is None:
                return f"`git clean {t}` bloqueado: opción desconocida o ambigua."
            if op == "--exclude" and "=" not in t:
                i += 1
            elif op == "--force":
                forzado = True
            elif op == "--no-force":
                forzado = False
            elif op == "--dry-run":
                simulado = True
            elif op == "--no-dry-run":
                simulado = False
        elif t.startswith("-") and len(t) > 1:
            for j, ch in enumerate(t[1:], 1):
                if ch == "e":                          # consume el resto del clúster o el token siguiente
                    if j == len(t) - 1:
                        i += 1
                    break
                if ch == "f":
                    forzado = True
                elif ch == "n":
                    simulado = True
        i += 1
    if forzado and not simulado:
        return ("`git clean -f` bloqueado: borra ficheros sin seguimiento sin recuperación — "
                "borra por nombre solo los ficheros nuevos de tu intento.")
    return None


def _cluster_con_fuerza(token, con_valor):
    """`-abc` con la opción corta `f` DE VERDAD: se recorre de izquierda a derecha y una letra que
    consume valor (`b`/`B` en checkout, `c`/`C` en switch) se lleva el RESTO del clúster, así que el
    `f` de `-bfeature` es parte de un nombre de rama, no la opción de fuerza (T-06 fix1, gap 16)."""
    if not re.fullmatch(r"-[a-zA-Z0-9]+", token):
        # `-bfeature/y`: el clúster real acaba donde empieza el valor; mira solo la parte letra-dígito inicial
        m = re.match(r"-([a-zA-Z0-9]+)", token)
        if not m or token.startswith("--"):
            return False
        token = "-" + m.group(1)
    for ch in token[1:]:
        if ch in con_valor:
            return False
        if ch == "f":
            return True
    return False


def _sin_barra_final(texto):
    return texto.rstrip("/") or "/"


def _rutas_de_referencia():
    """Raíces contra las que se compara una ruta absoluta: el directorio actual y el del proyecto."""
    raices = [os.getcwd()]
    pdir = os.environ.get("CLAUDE_PROJECT_DIR")
    if pdir:
        raices.append(pdir)
    return raices


def _clave_abs(ruta):
    """Ruta absoluta en forma comparable: `/` como separador, `C:/x` y `/c/x` unificados, minúsculas."""
    r = ruta.replace("\\", "/")
    m = re.match(r"^([A-Za-z]):(/.*)?$", r)
    if m:
        r = "/" + m.group(1) + (m.group(2) or "")
    return posixpath.normpath(r).lower() if r.startswith("/") else r.lower()


def _solo_comodines(texto):
    comps = [c for c in texto.split("/") if c not in ("", ".")]
    return all(re.fullmatch(r"\*+", c) for c in comps)


def _parte_pathspec(token):
    """`(patrón, top, excluye)` de un pathspec con su magia (`:/`, `:(top,glob)`, `:!`, `:^`)."""
    if token.startswith(":("):
        m = re.match(r":\(([^)]*)\)(.*)$", token, re.S)
        if m:
            magias = {x.strip().lower() for x in m.group(1).split(",")}
            return m.group(2), "top" in magias, "exclude" in magias
        return token, False, False
    if token.startswith(":") and len(token) > 1:
        i, top, excluye = 1, False, False
        while i < len(token) and token[i] in "/!^":
            top, excluye = top or token[i] == "/", excluye or token[i] in "!^"
            i += 1
        if i < len(token) and token[i] == ":":
            i += 1
        return token[i:], top, excluye
    return token, False, False


_VAR_PWD = re.compile(r"^(?:\$\{PWD\}|\$PWD|\$\(\s*pwd\s*\)|`\s*pwd\s*`)(.*)$", re.S)


def _abarca_el_arbol(token):
    """¿Este pathspec abarca TODO el árbol (o más)? Normalizado, no literal (T-06 fix1, gap 4):
    `.`, `./`, `src/..`, `..` (sale del directorio actual), `*`/`**`/`**/*`, `:/`, `:/*`, `:(top)`,
    `:(glob)**`, `$PWD`/`${PWD}`/`$(pwd)`, o una ruta absoluta igual o ANTERIOR al directorio actual
    o al del proyecto. Un pathspec solo de exclusión (`:!x`) también lo abarca: es «todo menos x»."""
    patron, top, _ = _parte_pathspec(token)
    patron = patron.replace("\\", "/")
    m = _VAR_PWD.match(patron)
    if m:
        patron = _clave_abs(os.getcwd()) + m.group(1)
        absoluta = True
    else:
        absoluta = patron.startswith("/") or bool(re.match(r"^[A-Za-z]:(/|$)", patron))
    if absoluta:
        comps = [c for c in patron.replace("\\", "/").split("/")]
        while comps and (comps[-1] == "" or re.fullmatch(r"\*+", comps[-1])):
            comps.pop()
        base = _clave_abs("/".join(comps) or "/")
        return any(r == base or r.startswith(_sin_barra_final(base) + "/") or base == "/"
                   for r in map(_clave_abs, _rutas_de_referencia()))
    if _solo_comodines(patron):
        return True
    norm = posixpath.normpath(patron)
    if norm == ".":
        return True
    comps = [c for c in norm.split("/") if c != "."]
    if comps and comps[0] == "..":
        # `..` sale del directorio actual (quizá de la raíz): abarca el árbol si lo que queda es nada o comodines
        resto = [c for c in comps if c != ".."]
        return not resto or all(re.fullmatch(r"\*+", c) for c in resto)
    return False


def _pathspecs_arbol_entero(rutas):
    """¿Alguna de `rutas` abarca el árbol entero? Si TODAS son exclusiones también (todo menos x)."""
    reales = []
    excl = 0
    for t in rutas:
        _, _, excluye = _parte_pathspec(t)
        if excluye:
            excl += 1
        else:
            reales.append(t)
    if excl and not reales:
        return True
    return any(_abarca_el_arbol(t) for t in reales)


def _razon_restauracion(sub, args):
    """`git checkout|switch|restore` que DESCARTA cambios sin comitear (T-06, plugin-audit-2).

    Deniega: `checkout -f|--force`, `switch -f|--force|--discard-changes`, `checkout|restore` con un
    pathspec que abarque el árbol entero (normalizado: `.`, `./`, `..`, `*`, `:/`, `:(top)`, `:(glob)**`,
    `$PWD`, ruta absoluta de la raíz, solo exclusiones), `--pathspec-from-file` (su contenido no se ve)
    y `restore --worktree|-W`. NO toca `git checkout main -- <fichero>`, `checkout -b`, `restore --staged`
    ni `restore <fichero>`: restauran un fichero o no descartan nada del árbol (la regla de P4 sobre
    ficheros con cambios previos sigue siendo prosa del implementer).
    """
    if "--" in args:
        k = args.index("--")
        antes, rutas = args[:k], args[k + 1:]
    else:
        antes, rutas = args, [t for t in args if not t.startswith("-")]
    opciones = [t for t in antes if t.startswith("-")]
    msg = (f"`git {sub}` que descarta cambios sin comitear bloqueado: pueden no ser tuyos — "
           "revierte solo lo de tu intento (`git diff <foto> -- <ficheros> | git apply -R`).")
    if sub == "checkout" and any(_cluster_con_fuerza(t, "bB") or _prefijo(t, "--force") for t in opciones):
        return msg
    if sub == "switch" and any(_cluster_con_fuerza(t, "cC") or _prefijo(t, "--force", "--discard-changes")
                               for t in opciones):
        return msg
    if sub in ("checkout", "restore"):
        solo_indice = sub == "restore" and any(_prefijo(t, "--staged") or _cluster(t, "S") for t in opciones) \
            and not any(_prefijo(t, "--worktree") or _cluster(t, "W") for t in opciones)
        if not solo_indice:
            if any(_prefijo(t, "--pathspec-from-file") for t in opciones) or _pathspecs_arbol_entero(rutas):
                return msg
    if sub == "restore" and any(_prefijo(t, "--worktree") or _cluster(t, "W") for t in opciones):
        return msg
    return None


def check_git(command, branch, _depth=0, _env=None):
    """Razón de deny o None. `branch` = rama actual (None si no hay git).
    Recursivo SOLO sobre lo que una shell ejecutaría (`sh -c "git push --force"`, `bash -c '…'`,
    `eval "…"`); un mensaje de commit con «rm -rf .» dentro es texto y no se analiza."""
    if _depth > 3:
        return None
    exportados = set()      # variables sensibles exportadas en segmentos anteriores de la MISMA orden
    for toks in _segmentos(command):
        toks, bindings = _literal_invocation(toks, _env)
        if toks and toks[0] in _EXPORTADORES:
            exportados |= {t.split("=", 1)[0] for t in toks[1:] if _env_sensible(t.split("=", 1)[0])}
        elif not toks:
            exportados |= {k for k in bindings if _env_sensible(k)}   # `GIT_DIR=x; git …`
        if exportados:
            bindings = {**bindings, **{k: "" for k in exportados if k not in bindings}}
        # Solo se recurre en el argumento de `sh|bash|zsh|dash -c` y en el de `eval` — NO en tokens
        # arbitrarios (`git commit -m "rm -rf . en el mensaje"` es texto, no un comando; regresión
        # cazada en la revisión, intento 2).
        for sub in _subcomandos_shell(toks):
            razon = check_git(sub, branch, _depth + 1, bindings)
            if razon:
                return razon
        razon = check_ordenes_externas(toks)
        if razon:
            return razon
        razon = _razon_config(toks, bindings, exportados)
        if razon:
            return razon
        i, hooks_override = _git_invocation(toks)
        if i >= 0 and toks[i] == "commit":
            if hooks_override:
                return ("`git commit` con override de core.hooksPath bloqueado: conserva los hooks "
                        "de verificación del proyecto; un cambio de ruta requiere revisión explícita.")
            if _commit_skips_verification(toks[i + 1:]):
                return ("`git commit` sin verificación bloqueado: conserva pre-commit y commit-msg; "
                        "corrige el fallo de los hooks en vez de omitirlos con --no-verify/-n.")
        i = _es_git(toks, "push")
        if i >= 0:
            for t in toks[i + 1:]:
                if _prefijo(t, "--force", "--force-with-lease", "--force-if-includes") or _cluster(t, "f") \
                        or (t.startswith("+") and len(t) > 1):          # refspec `+main` = force
                    return ("`git push` forzado bloqueado: reescribe historia compartida — "
                            "haz push normal; si de verdad hace falta, que lo pida el usuario.")
                if _prefijo(t, "--delete", "--mirror", "--prune") or _cluster(t, "d") \
                        or re.fullmatch(r"\+?:[^:]+", t):              # refspec `:rama` = borrar
                    return ("`git push` que borra ramas remotas bloqueado (`--delete`/`-d`/`:rama`/`--mirror`/"
                            "`--prune`) — la limpieza de ramas la dirige el ritual de cierre de /dev-cycle (Fase 6).")
        i = _es_git(toks, "reset")
        if i >= 0 and any(_prefijo(t, "--hard") for t in toks[i + 1:]):
            return ("`git reset --hard` bloqueado: descarta cambios sin comitear que pueden no ser "
                    "tuyos — revierte solo lo de tu intento (`git diff <foto> -- <ficheros> | git apply -R`).")
        i = _es_git(toks, "clean")
        if i >= 0:
            razon = _razon_clean(toks[i + 1:])
            if razon:
                return razon
        i = _es_git(toks, "stash")
        if i >= 0 and i + 1 < len(toks) and toks[i + 1] in ("drop", "clear"):
            return (f"`git stash {toks[i + 1]}` bloqueado: elimina stashes sin recuperación sencilla — "
                    "si sobra, que lo descarte el usuario.")
        i = _es_git(toks, "branch")
        if i >= 0:
            rest = toks[i + 1:]
            fuerza = any(_cluster(t, "f") or _prefijo(t, "--force") for t in rest)
            if any(_cluster(t, "D") or _cluster(t, "M") or _cluster(t, "C") for t in rest) or fuerza:
                return ("`git branch -D|-M|-C|-f` bloqueado: borra, mueve, copia o reapunta una rama a la fuerza — "
                        "usa `-d`/`-m`, o que lo haga el ritual de cierre de /dev-cycle (Fase 6).")
        i = _es_git(toks, "update-ref")
        if i >= 0 and any(_cluster(t, "d") or _prefijo(t, "--stdin") for t in toks[i + 1:]):
            return ("`git update-ref -d|--stdin` bloqueado: borra o reescribe referencias sin las comprobaciones "
                    "de `git branch` — que lo haga el usuario.")
        for sub in ("checkout", "switch", "restore"):
            i = _es_git(toks, sub)
            if i >= 0:
                razon = _razon_restauracion(sub, toks[i + 1:])
                if razon:
                    return razon
                if sub == "restore":
                    continue
                if "--" in toks[i + 1:]:
                    continue          # `git checkout main -- fichero` restaura ficheros, no cambia de rama
                args = [t for t in toks[i + 1:] if not t.startswith("-")]
                flags = [t for t in toks[i + 1:] if t.startswith("-")]
                if args and args[0] in MAIN_BRANCHES and not any(f in ("-b", "-B", "-c", "-C") for f in flags) \
                        and branch and branch not in MAIN_BRANCHES and branch != "HEAD":
                    return (f"`git {sub} {args[0]}` bloqueado: estás en la rama de trabajo «{branch}» "
                            f"y el implementer no sale de ella — la integración la dirige /dev-cycle (Fase 6).")
        if toks and os.path.basename(toks[0]) == "rm":
            flags = [t for t in toks[1:] if t.startswith("-")]
            targets = [t for t in toks[1:] if not t.startswith("-")]
            rec = any(f in ("--recursive",) or (re.fullmatch(r"-[a-zA-Z]+", f) and ("r" in f or "R" in f)) for f in flags)
            frc = any(f == "--force" or (re.fullmatch(r"-[a-zA-Z]+", f) and "f" in f) for f in flags)
            if rec and frc:
                home = os.path.expanduser("~").replace("\\", "/").rstrip("/")
                for t in targets:
                    n = t.replace("\\", "/")
                    n = posixpath.normpath(n) if n else n          # `./` → `.`, `.git/` → `.git`
                    if n in ("/", "/*", "~", "~/*", "$HOME", "${HOME}", ".git", ".", "*") \
                            or (home and n == home) or n.endswith("/.git"):
                        return (f"`rm -rf {t}` bloqueado: destruiría el sistema, el home o el repositorio "
                                f"(.git — `rm -rf .` desde la raíz también) — si es intencional, que lo "
                                f"ejecute el usuario a mano.")
    return None


# --------------------------------------------------------------- decisión ----
def decide(payload, project_dir, cfg=None, branch=None, branch_fn=None, agent="implementer"):
    """Devuelve la razón de deny (str) o None. Pura salvo `branch_fn` (inyectable en tests).
    `agent`: `implementer` (default) o `architect` (alcance propio; sin regla ramaPrincipal)."""
    cfg = cfg or DEFAULTS
    tool = payload.get("tool_name") if isinstance(payload, dict) else None
    tool_input = payload.get("tool_input", {}) if isinstance(payload, dict) else {}
    if tool in WRITE_TOOLS:
        rels = [normalize_path(p, project_dir) for p in extract_paths(tool_input)]
        rels = [r for r in rels if r]
        if cfg.get("alcance", True):
            for rel in rels:
                razon = (check_alcance_architect(rel, tool, tool_input if isinstance(tool_input, dict) else {})
                         if agent == "architect" else check_alcance(rel))
                if razon:
                    return razon
        if agent == "architect":
            return None
        if cfg.get("ramaPrincipal", True) and rels:
            if branch is None and branch_fn is not None:
                branch = branch_fn(project_dir)
            if branch in MAIN_BRANCHES:
                fuera = [r for r in rels if not es_ledger(r)]
                if fuera:
                    return (f"estás en «{branch}» y vas a escribir «{fuera[0]}»: trabaja en una rama "
                            f"(feature/<slug>) — P2 del implementer. Crea la rama (`git checkout -b feature/<slug>`) "
                            f"y repite la edición; el ledger tasks.md sí puede tocarse aquí.")
        return None
    if tool == "Bash" and cfg.get("git", True):
        cmd = tool_input.get("command") if isinstance(tool_input, dict) else None
        if isinstance(cmd, str) and cmd.strip():
            if branch is None and branch_fn is not None and re.search(r"\bgit\b", cmd):
                branch = branch_fn(project_dir)
            return check_git(cmd, branch)
    return None


def deny_json(reason):
    return json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                              "permissionDecision": "deny",
                                              "permissionDecisionReason": reason}},
                      ensure_ascii=False)


def _aviso_off_una_vez(project_dir):
    """`guardrails: false` → systemMessage la primera vez (marca inocua en .claude/)."""
    marca = os.path.join(project_dir, ".claude", ".guardrail-off")
    if os.path.exists(marca):
        return None
    try:
        os.makedirs(os.path.dirname(marca), exist_ok=True)
        open(marca, "w").close()
    except OSError:
        pass
    return json.dumps({"systemMessage": "⚠️ guardrails del implementer/architect DESACTIVADOS "
                                        "(.claude/dev.json → guardrails: false): alcance, rama y git "
                                        "no se comprueban."}, ensure_ascii=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("modo", choices=["pre-tool"])
    ap.add_argument("--project-dir", default=None,
                    help="raíz del proyecto (default: $CLAUDE_PROJECT_DIR o cwd)")
    ap.add_argument("--agent", default=None, choices=["implementer", "architect"],
                    help="agente cuyas reglas aplican (default: $CLAUDE_AGENT_NAME si es uno de ellos, si no implementer)")
    args = ap.parse_args()
    agent = args.agent or (os.environ.get("CLAUDE_AGENT_NAME") if os.environ.get("CLAUDE_AGENT_NAME") in ("implementer", "architect") else None) or "implementer"
    project_dir = args.project_dir or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    try:
        raw = sys.stdin.read()
        try:
            payload = json.loads(raw) if raw.strip() else {}
        except ValueError:
            print("guardrail-check: stdin no es JSON — se permite", file=sys.stderr)
            return 0
        cfg, activo = load_config(project_dir)
        if not activo:
            msg = _aviso_off_una_vez(project_dir)
            if msg:
                print(msg)
            return 0
        razon = decide(payload, project_dir, cfg, branch_fn=current_branch, agent=agent)
        if razon:
            print(deny_json(razon))
        return 0
    except Exception as e:  # noqa: BLE001 — un guardrail roto nunca bloquea
        print(f"guardrail-check: error interno ({e!r}) — se permite", file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main())
