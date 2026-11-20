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
Nunca exit ≠ 0 por error interno: se registra en stderr y se DENIEGA con un motivo explícito (fix12: este modo
solo lo lanzan los hooks del rol protegido —implementer/architect—; permitir ante una excepción abriría justo la
protección que existe para ellos). Un stdin que no es JSON sigue permitiéndose (no es un error interno).
"""
import argparse
import bisect
import functools
import json
import os
import posixpath
import re
import shlex
import stat
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


def _gitdir_de(project_dir):
    """Directorio git (el de `.git/HEAD`) del proyecto, subiendo por los ancestros como git; resuelve `.git` como fichero `gitdir:` (worktrees, submodulos).
    None si no es concluyente (sin `.git`, enlace simbolico, fichero ilegible)."""
    d = os.path.abspath(project_dir or os.getcwd())
    for _ in range(128):
        g = os.path.join(d, ".git")
        try:
            info = os.lstat(g)
        except FileNotFoundError:
            info = None
        if info is not None:
            if stat.S_ISDIR(info.st_mode):
                return g
            if stat.S_ISREG(info.st_mode):
                with open(g, "rb") as fh:
                    m = re.fullmatch(r"gitdir:[ \t]*([^\r\n]+?)[ \t]*\r?\n?", fh.read(4096).decode("utf-8"))
                if not m:
                    return None
                ruta = m.group(1)
                return os.path.normpath(ruta if os.path.isabs(ruta) else os.path.join(d, ruta))
            return None
        padre = os.path.dirname(d)
        if padre == d:
            return None
        d = padre
    return None


def _commondir(gitdir):
    """Directorio comun de un worktree (el `commondir` de `gitdir`, relativo a este): None si no hay fichero `commondir`, False si no se puede leer."""
    f = os.path.join(gitdir, "commondir")
    if not os.path.isfile(f):
        return None
    try:
        with open(f, "rb") as fh:
            texto = fh.read(4096).decode("utf-8").strip()
    except (OSError, ValueError):
        return False
    if not texto or "\n" in texto:
        return False
    return os.path.normpath(texto if os.path.isabs(texto) else os.path.join(gitdir, texto))


def _es_repositorio(gitdir):
    """Como `is_git_directory` de git: `HEAD` y `objects/` + `refs/` en el directorio propio o, en un worktree, en el que apunta `commondir` (fix18, gap 8: validado, no solo presente)."""
    if not os.path.isfile(os.path.join(gitdir, "HEAD")):
        return False
    comun = _commondir(gitdir)
    if comun is False:
        return False                       # fix18 (gap 8): un `commondir` que no apunta a un repositorio lo salta git (y sube al padre)
    destino = gitdir if comun is None else comun
    return os.path.isdir(os.path.join(destino, "objects")) and os.path.isdir(os.path.join(destino, "refs"))


def rama_barata(project_dir, timeout=5):
    """Rama actual leyendo `.git/HEAD` (0,8 ms en reposo, 47 ms con la maquina saturada; `git rev-parse` cuesta 150-500 ms y con carga pasa del tope):
    el nombre, `HEAD` si esta suelto. Recurre a `current_branch` (git) si no es concluyente: `GIT_DIR`/`GIT_WORK_TREE`/`GIT_COMMON_DIR` en el entorno,
    sin `.git`, HEAD ilegible o enlace simbolico, reftable (`refs/heads/.invalid`) o una referencia simbolica que no es una rama (fix16, punto 4)."""
    try:
        if any(os.environ.get(k) for k in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR")):
            return current_branch(project_dir, timeout=timeout)
        gitdir = _gitdir_de(project_dir) if not project_dir or os.path.isdir(project_dir) else None   # un directorio que no existe lo decide git (falla)
        # fix17 (gap 17): git solo considera repositorio un directorio con `HEAD` + `objects/` + `refs/` (o, en un worktree, `commondir`); un `.git` a medias lo salta y sube al
        # repositorio padre: `rama_barata` no lee su HEAD y recurre a git, que decide como siempre.
        if gitdir is not None and _es_repositorio(gitdir):
            cabeza = os.path.join(gitdir, "HEAD")
            if not os.path.islink(cabeza):
                with open(cabeza, "rb") as fh:
                    texto = fh.read(1024).decode("utf-8").strip()
                if texto.startswith("ref: refs/heads/"):
                    nombre = texto[len("ref: refs/heads/"):]
                    if nombre and nombre != ".invalid" and "\n" not in nombre:
                        return nombre
                elif re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", texto):
                    return "HEAD"
    except (OSError, ValueError):
        pass
    return current_branch(project_dir, timeout=timeout)


# Cierre por diseño (T-06 fix5): el tokenizador PROPIO del guardarraíl y el de bash discrepaban en cada
# construcción que oculta texto (heredoc, `$(( ))`, `<<<`, `"…$(…)…"`). Aquí se lee la orden con la
# gramática de bash que importa para esto y todo lo que quede abierto al final es un hecho (`incompleta`)
# con el que `check_git` deniega la orden entera si contiene `git` o un cambio de base.
#
# Modelo de amenaza (T-06 fix6, decisión del usuario): el guardarraíl frena los ERRORES de un agente honesto; las
# indirecciones deliberadas (variable como programa, código por stdin hacia un intérprete, `find -exec`, heredoc a
# `python3`) son un LÍMITE conocido (docs/agents/implementer.md). Por eso el cuerpo de un heredoc se analiza SIEMPRE
# como órdenes, sin lista de intérpretes ni reglas de salto: la única excepción son las dos formas exactas de
# `git commit` con mensaje (`_quitar_mensajes_de_commit`).
_MAX_ANIDADO = 20          # profundidad de `$( )`, backticks y cuerpos de heredoc que se analizan


_OPACA_C = "`\\c` seguido de un carácter no ASCII (bash lo lee por bytes y el control depende del locale)"
_OPACA_U = "`\\U` con un punto de código fuera de rango"
_OPACA_ANIDADO = f"anidado de más de {_MAX_ANIDADO} niveles"


def _opaca(st, motivo):
    """Marca la lectura como OPACA (fix14) y como incompleta; se conserva el motivo de la primera."""
    st.incompleta = True
    st.opaca = st.opaca or motivo


class _Lectura:
    """Resultado compartido de una lectura: segmentos, cuerpos de heredoc y si quedó algo abierto."""
    __slots__ = ("out", "cuerpos", "incompleta", "tablas", "inicios", "opaca")

    def __init__(self):
        self.out, self.cuerpos, self.incompleta, self.tablas = [], [], False, {}
        # fix14: motivo (texto) de la PRIMERA lectura OPACA, o "". Opaca = el guardarraíl pierde texto o no sabe lo que se
        # ejecuta (`\c` + no ASCII, `\U` fuera de rango, anidado de más de `_MAX_ANIDADO` niveles): se deniega siempre.
        self.opaca = ""
        # `(posición, cuerpos de heredoc ya leídos)` de cada palabra `g…` que EMPIEZA una sentencia de nivel superior
        # (fuera de comilla, comentario, heredoc y sustitución): de ahí salen las formas exactas de `git commit` (fix7)
        self.inicios = []


def _delimitador(command, j):
    """Delimitador del heredoc que empieza en `j` (tras `<<` y un `-` opcional): comillas y barras
    invertidas se QUITAN (`E"OF"`, `\\EOF` → `EOF`). Devuelve `(delimitador, citado)` o None."""
    n = len(command)
    while j < n and command[j] in " \t":
        j += 1
    out, citado, leido = [], False, False
    while j < n:
        c = command[j]
        if c in " \t\n;&|()<>":      # el CR NO termina la palabra: en bash es un carácter normal (fix6, gap 9)
            break
        leido = True
        if c == "\\" and j + 1 < n:
            citado = True
            out.append(command[j + 1])
            j += 2
        elif c in "'\"":
            citado = True
            j += 1
            while j < n and command[j] != c:
                if c == '"' and command[j] == "\\" and j + 1 < n:
                    j += 1
                out.append(command[j])
                j += 1
            j += 1
        else:
            out.append(c)
            j += 1
    return ("".join(out), citado) if leido else None


def _saltar_heredocs(command, pos, pendientes, st):
    """Lee el cuerpo de cada heredoc pendiente (desde `pos`, primera línea tras la orden) hasta la línea que
    solo contiene el delimitador (con `<<-`, sin tabuladores iniciales) y lo guarda en `st.cuerpos` como
    `(texto, citado, cerrado)`. Devuelve la posición siguiente; un heredoc sin cierre marca `incompleta`."""
    for delim, guion, citado in pendientes:
        lineas = []
        while True:
            if pos >= len(command):
                st.cuerpos.append(("\n".join(lineas), citado, False))
                st.incompleta = True
                return len(command)
            fin = command.find("\n", pos)
            linea = command[pos:] if fin < 0 else command[pos:fin]
            pos = len(command) if fin < 0 else fin + 1
            if (linea.lstrip("\t") if guion else linea) == delim:
                break
            lineas.append(linea)
        st.cuerpos.append(("\n".join(lineas), citado, True))
    return pos


# Una aritmética `$(( … ))`/`(( … ))` deja de serlo (bash la lee como subshell) si lleva `;`, salto de línea, comillas,
# backtick, `$(`, dos palabras seguidas o la palabra `git`. Todas las marcas se anotan en UNA pasada lineal
# (`_TablaAritmetica`) y cada consulta es una búsqueda binaria: `_aritmetica` era O(n²) (T-06 fix6, gap 1).
_BT_ESCAPE_RE = re.compile(r"\\([$`\\])")
_ARIT_SUELTA_RE = re.compile(r"[;\n`'\"]")
_ARIT_DOLAR_RE = re.compile(r"\$\(")
_ARIT_GIT_RE = re.compile(r"\bgit\b")
_ARIT_PARES_RE = re.compile(r"(?=([A-Za-z0-9_$]\s+[A-Za-z0-9_$]))")


class _TablaAritmetica:
    """Una pasada sobre la orden: casa cada `(` con su `)` (como el recorrido por profundidad, sin mirar comillas) y
    guarda, por clase de marca, las posiciones de inicio y fin ordenadas (las fines son monótonas dentro de cada clase)."""
    __slots__ = ("cierre", "marcas")

    def __init__(self, command):
        pila, cierre = [], {}
        for m in re.finditer(r"[()]", command):
            if m.group() == "(":
                pila.append(m.start())
            elif pila:
                cierre[pila.pop()] = m.start()
        self.cierre = cierre
        self.marcas = []
        for regex, grupo in ((_ARIT_SUELTA_RE, 0), (_ARIT_DOLAR_RE, 0), (_ARIT_GIT_RE, 0), (_ARIT_PARES_RE, 1)):
            inicios, fines = [], []
            for m in regex.finditer(command):
                inicios.append(m.start(grupo))
                fines.append(m.end(grupo))
            self.marcas.append((inicios, fines))

    def invalida(self, j, k):
        """¿Hay alguna marca que invalide la aritmética dentro de `command[j:k]`?"""
        for inicios, fines in self.marcas:
            idx = bisect.bisect_left(inicios, j)
            if idx < len(inicios) and fines[idx] <= k:
                return True
        return False


def _aritmetica(command, j, st):
    """Posición tras el `))` de una expansión/orden aritmética cuyo contenido empieza en `j` (el `(` que la abre está
    en `j - 1`), o None si NO es aritmética (dos palabras seguidas, `;`, comillas, `$(`, `git`…: bash la lee entonces
    como subshell). Dentro de la aritmética `<<` es un desplazamiento, no un heredoc. Lineal (tabla por orden)."""
    tabla = st.tablas.get(command)
    if tabla is None:
        tabla = st.tablas[command] = _TablaAritmetica(command)
    k = tabla.cierre.get(j - 1)
    if k is None or command[k + 1:k + 2] != ")":
        return None
    return None if tabla.invalida(j, k) else k + 2


# Patrón de `case` que el lector sigue: sin comillas, escapes, corchetes, agrupaciones ni expansiones (fix11, punto 1).
_HEX = "0123456789abcdefABCDEF"
_PATRON_CASE_RE = re.compile(r"[\w.*?/+=,:%@^~-]+")
_ANSI_SIMPLES = {"a": "\a", "b": "\b", "e": "\x1b", "E": "\x1b", "f": "\f", "n": "\n", "r": "\r", "t": "\t", "v": "\v",
                 "\\": "\\", "'": "'", '"': '"', "?": "?"}


def _ansi_fin(command, i):
    r"""Delimita `$'…'` como el lexer de bash (fix12, punto 1): `i` apunta al primer carácter DESPUÉS de `$'`. Cada par `\X`
    se salta entero (sea `X` lo que sea: `\c'`, `\x'`, `\\`) y el primer `'` sin escapar cierra la cadena. Devuelve la posición
    del `'` de cierre o `-1` si no hay. La decodificación va DESPUÉS, sobre el contenido ya delimitado."""
    n = len(command)
    while i < n:
        c = command[i]
        if c == "\\":
            i += 2
        elif c == "'":
            return i
        else:
            i += 1
    return -1


def _ansi_c(command, i, st):
    r"""Escape de `$'…'` con la semántica de bash sobre el CONTENIDO ya delimitado (fix11 punto 3, fix12 punto 1): `i` apunta al
    carácter que sigue a la barra y `command` acaba donde acaba la cadena. Devuelve `(texto, posición siguiente)`.
    `\a \b \e \E \f \n \r \t \v \\ \' \" \?`, octal de 1 a 3 cifras, `\xHH`, `\x{H…}` (cualquier número de cifras, módulo 256;
    sin cifras da NUL), `\uHHHH`, `\UHHHHHHHH` y `\cX` (`\c\\` consume las dos barras; `\c` al final queda tal cual); un
    escape desconocido conserva la barra y el carácter. Lineal (cada escape consume lo que lee)."""
    n, c = len(command), command[i]
    if c in _ANSI_SIMPLES:
        return _ANSI_SIMPLES[c], i + 1
    if c in "01234567":
        j = i
        while j < n and j < i + 3 and command[j] in "01234567":
            j += 1
        return chr(int(command[i:j], 8) & 0xFF), j
    if c == "x" and command.startswith("{", i + 1):
        j = i + 2
        while j < n and command[j] in _HEX:
            j += 1
        valor = int(command[i + 2:j], 16) & 0xFF if j > i + 2 else 0
        return chr(valor), (j + 1 if command.startswith("}", j) else j)
    if c in "xuU":
        j, tope = i + 1, i + 1 + {"x": 2, "u": 4, "U": 8}[c]
        while j < n and j < tope and command[j] in _HEX:
            j += 1
        if j == i + 1:
            return "\\" + c, i + 1             # sin cifras: bash deja la barra
        try:
            return chr(int(command[i + 1:j], 16)), j
        except (ValueError, OverflowError):
            _opaca(st, _OPACA_U)
            return "", j
    if c == "c" and i + 1 < n:
        k, j = command[i + 1], i + 2
        if not k.isascii():
            # fix13 (gap 1 del intento 13): bash aplica `& 0x1F` al PRIMER BYTE UTF-8 y conserva los de continuacion, y el
            # control resultante (NUL, tabulador, salto de linea…) depende del byte y del locale: no se emula. La lectura queda
            # incompleta, y desde fix14 OPACA (deny siempre: git puede llegar escapado o partido sin el texto `git`) y el resto
            # del contenido se decodifica sin este caracter.
            _opaca(st, _OPACA_C)
            return "", j
        if k == "\\" and command.startswith("\\", j):
            j += 1                              # POSIX: `$'\c\\'` es una sola barra de control
        return (chr(0x7F) if k == "?" else chr(ord(k.upper()) & 0x1F)), j
    return "\\" + c, i + 1


def _ansi_decodificar(contenido, st):
    r"""Decodifica el contenido (ya delimitado) de un `$'…'`: un `\0` corta el resto de la cadena, como en bash."""
    out, i, n = [], 0, len(contenido)
    while i < n:
        c = contenido[i]
        if c == "\\" and i + 1 < n:
            texto, i = _ansi_c(contenido, i + 1, st)
            if texto == "\x00":
                break
            out.append(texto)
        else:
            out.append(c)
            i += 1
    return "".join(out)


def _case_palabra(cases, palabra, plana, cur, par, fin, st):
    """Seguimiento del `case` DENTRO de una sustitución `$(…)`/`<(…)`/`>(…)` por LISTA BLANCA (fix11, punto 1; el lector
    de gramática completa del fix10 no convergía: cada lente hallaba otra forma que bash ejecuta). Solo se sigue la forma
    simple: `case` sin comillas ni escapes como primera palabra de una orden, a profundidad 0 de la sustitución y sin
    prefijos (`time`, `coproc`, `function`, `!`, `{`…); `in` como palabra propia seguida de blanco; patrones sin comillas ni
    escapes ni `esac`; y `esac` como primera palabra. CUALQUIER otra aparición de `case`/`esac` deja la lectura `incompleta`
    (se deniega si hay git o cambio de base). `cases` es la pila de estados: `w` (espera el sujeto), `i` (espera `in`), `p`
    (en patrones) y `b` (en el cuerpo de una cláusula); `plana` es True si la palabra no llevaba comillas, escapes ni
    sustituciones (su texto coincide con lo escrito); `fin` es el carácter que la termina. O(1) por palabra.
    Devuelve True cuando la palabra es el `in` que abre los patrones (el llamador descarta la cabecera)."""
    top = cases[-1] if cases else None
    primero = not cur and par == 0
    reservada = palabra in ("case", "esac")
    if top == "w":
        if reservada:
            st.incompleta = True
            cases.pop()
        else:
            cases[-1] = "i"
    elif top == "i":
        if palabra == "in" and plana and fin in " \t\n":
            cases[-1] = "p"
            return True                  # `case x in` no es una orden: el llamador descarta la cabecera
        st.incompleta = True
        cases.pop()
    elif top == "p":
        if palabra == "esac" and plana and primero and fin in " \t\n;)":
            cases.pop()                  # `esac|*)` es un patrón, no el cierre: cae a `incompleta`
        elif reservada or not (plana and _PATRON_CASE_RE.fullmatch(palabra)):
            st.incompleta = True
    elif palabra == "case":
        if plana and primero and top is None:
            cases.append("w")
        else:
            st.incompleta = True
    elif palabra == "esac":
        if plana and primero and top == "b":
            cases.pop()
        else:
            st.incompleta = True
    return False


def _leer(command, i, modo, st, prof):
    """Tokeniza `command` desde `i`: `modo` `top` (hasta el final) o `sub` (hasta el `)` que cierra un `$(`). Los
    segmentos van a `st.out`. Devuelve `(posición, heredocs pendientes sin cuerpo)`. Los paréntesis sin comillas
    separan órdenes, `$(…)` y los backticks se leen como órdenes también DENTRO de comillas dobles (bash las
    ejecuta; el contenido de un backtick se lee aparte, sin sus barras de escape) y el cuerpo de un heredoc no se
    tokeniza aquí: lo lee `_segmentos` como órdenes."""
    n = len(command)
    if prof > _MAX_ANIDADO:
        _opaca(st, _OPACA_ANIDADO)
        return n, []
    cur, word, started, quote, pend, par, cierre = [], [], False, None, [], 0, False
    cases = []              # pila del seguimiento de `case` (solo dentro de una sustitución, fix10)
    ult_redir = -2          # posición del último `<`/`>` SIN escapar ni entrecomillar (fix7, gap 6)
    wini = 0                # dónde empieza la palabra en curso en `command`: «plana» = su texto coincide con lo escrito (fix11)
    while i < n:
        c = command[i]
        if not started:
            wini = i
        if quote is None and c == "\n" and pend:
            if started:
                cur.append("".join(word))
                word, started = [], False
            if cur:
                st.out.append(cur)
                cur = []
            i, pend = _saltar_heredocs(command, i + 1, pend, st), []
            continue
        if c == "g" and not started and not cur and quote is None and prof == 0 and modo == "top":
            st.inicios.append((i, len(st.cuerpos)))
        if c == "\\" and quote is None and i + 1 == n:
            word.append(c)           # escape final: la orden está incompleta
            started, st.incompleta = True, True
            break
        if c == "\\" and quote != "'" and i + 1 < n:
            following = command[i + 1]
            if following == "\n":
                i += 2
                continue
            if quote is None or following in '\\"$`':
                word.append(following)
                started = True
                i += 2
                continue
        if quote == "'":
            if c == "'":
                quote = None
            else:
                word.append(c)
            i += 1
            continue
        if c == "$" and quote is None and command.startswith("$$", i):
            # `$$` es el PID: la segunda `$` NO abre `$'…'` ni `$"…"` (fix7, gap 5: `echo $$'\'; git reset --hard #'`)
            word.append("$$")
            started = True
            i += 2
            continue
        if c == "$" and quote is None and command.startswith("$'", i):
            # ANSI-C `$'…'` como bash (fix12): primero se delimita por pares `\X` y después se decodifica el contenido.
            fin = _ansi_fin(command, i + 2)
            word.append(_ansi_decodificar(command[i + 2:n if fin < 0 else fin], st))
            started = True
            if fin < 0:
                st.incompleta = True         # sin comilla de cierre
            i = n if fin < 0 else fin + 1
            continue
        if c == "$" and quote is None and command.startswith('$"', i):
            # `$"…"` (traducción): la `$` no es parte de la palabra
            quote, started = '"', True
            i += 2
            continue
        if c == "$" and command.startswith("$(", i):
            fin = _aritmetica(command, i + 3, st) if command.startswith("$((", i) else None
            if fin is not None:
                word.append(command[i:fin])
                i = fin
            else:
                i, extra = _leer(command, i + 2, "sub", st, prof + 1)
                pend.extend(extra)
                word.append("$()")
            started = True
            continue
        if c == "`":
            # Sustitución con backticks: bash quita las barras de `\`` `\$` `\\` del contenido y LO LEE como una
            # orden (así `\`` anida otra sustitución). Se hace igual: contenido sin escapes -> lectura recursiva.
            j = i + 1
            while j < n and command[j] != "`":
                j += 2 if command[j] == "\\" else 1
            if j >= n:
                st.incompleta = True
            _leer(_BT_ESCAPE_RE.sub(r"\1", command[i + 1:min(j, n)]), 0, "top", st, prof + 1)
            i = min(j + 1, n)
            word.append("`")
            started = True
            continue
        if quote == '"':
            if c == '"':
                quote = None
            else:
                word.append(c)
            i += 1
            continue
        if c in "\"'":
            quote, started = c, True
        elif c == "<" and command.startswith("<<", i):
            # `<<<` (here-string) y `<<` (heredoc) separan palabra: `bash<<EOF` es `bash`, `<<`, `EOF`
            if started:
                cur.append("".join(word))
                word, started = [], False
            triple = command.startswith("<<<", i)
            if not triple:
                guion = command.startswith("<<-", i)
                d = _delimitador(command, i + 2 + guion)
                if d:
                    pend.append((d[0], guion, d[1]))
            cur.append("<<<" if triple else "<<")
            i += 3 if triple else 2
            continue
        elif c in "<>" and command.startswith("(", i + 1) and quote is None:
            # Sustitución de proceso `<(…)` / `>(…)` (fix9, gap 1): es PARTE de la palabra que la lleva, como `$(…)`. El
            # interior se lee aparte, como segmentos propios, y la orden exterior sigue entera con sus argumentos
            # (`xargs -a <(git diff --name-only) git restore` es un solo `xargs`: antes el `(` la partía y el `xargs` se perdía).
            # La palabra queda como `<()`/`>()`: sigue empezando por `<`/`>` (`_FUENTE_VISIBLE`, `source <(…)`).
            i, extra = _leer(command, i + 2, "sub", st, prof + 1)
            pend.extend(extra)
            word.append(c + "()")
            started = True
            ult_redir = -2
            continue
        elif c == "(" and command.startswith("((", i) and not cur and not started \
                and _aritmetica(command, i + 2, st) is not None:
            i = _aritmetica(command, i + 2, st)    # `(( expr ))`: aritmética, no órdenes
            continue
        elif c == "#" and not started:
            newline = command.find("\n", i)
            i = n if newline < 0 else newline
            continue
        elif c == "(" and cases and cases[-1] == "p" and par == 0 and not started and not cur:
            i += 1                        # `(` opcional delante de un patrón de `case`: no abre un grupo
            cur.append("(")               # y el patrón que sigue ya no es la primera palabra (`(esac)` no cierra el `case`)
            continue
        elif c == ")" and modo == "sub" and par == 0 and cases and cases[-1] == "p" \
                and not (started and "".join(word) == "esac" and command[wini:i] == "esac" and not cur):
            if started:
                _case_palabra(cases, "".join(word), command[wini:i] == "".join(word), cur, par, c, st)   # valida el patrón
            else:
                st.incompleta = True      # patrón vacío
            word, started, cur = [], False, []   # `)` que cierra un patrón de `case`: no cierra la sustitución
            if cases:
                cases[-1] = "b"
        elif c == ";" and cases and cases[-1] == "b" and par == 0 and command.startswith((";;", ";&"), i):
            if started:
                texto = "".join(word)
                _case_palabra(cases, texto, command[wini:i] == texto, cur, par, c, st)
                cur.append(texto)
                word, started = [], False
            if cur:
                st.out.append(cur)
                cur = []
            if cases:
                cases[-1] = "p"           # `;;`, `;&` y `;;&` terminan la cláusula: sigue otro patrón
            i += 3 if command.startswith(";;&", i) else 2
            continue
        elif c == ")" and modo == "sub" and par == 0:
            if started:
                texto = "".join(word)
                _case_palabra(cases, texto, command[wini:i] == texto, cur, par, c, st)
            i += 1
            cierre = True
            break
        elif c == "&" and (ult_redir == i - 1 or command.startswith("&>", i)):
            word.append(c)                # `2>&1`, `>&2`, `&>fichero`: redirección, no separador de órdenes
            started = True
        elif c in " \t\n;&|()":           # el CR NO separa: en bash es un carácter normal (fix6, gap 9)
            if started:
                texto = "".join(word)
                if modo == "sub" and _case_palabra(cases, texto, command[wini:i] == texto, cur, par, c, st):
                    cur = []
                else:
                    cur.append(texto)
                word, started = [], False
            if modo == "sub" and cases and (c in ";&|()" if cases[-1] in "wi" else c in ";&(" if cases[-1] == "p" else False):
                st.incompleta = True      # fuera de la forma simple: `case x; in`, `x;)`, `@(x|y)`…
            if modo == "sub" and cases and cases[-1] == "p" and (c == "|" or (c == "\n" and cur == ["|"])):
                cur = ["|"]               # tras `|` sigue un patrón: un `esac` ahí NO cierra el `case`
            elif c in "\n;&|()" and cur:
                if not (cases and cases[-1] == "p"):          # lo que hay entre patrones no es una orden
                    st.out.append(cur)
                cur = []
            par += (c == "(") - (c == ")" and par > 0)
        else:
            if c in "<>":
                ult_redir = i
            word.append(c)
            started = True
        i += 1
    if quote or (modo != "top" and not cierre) or cases:
        st.incompleta = True
    if started:
        cur.append("".join(word))
    if cur:
        st.out.append(cur)
    if modo == "top" and pend:
        st.incompleta = True          # heredoc cuya línea no llegó a terminar
        return i, []
    return i, pend


def _segmentos(command, _prof=0):
    """Literal shell words and command boundaries, retaining quoted punctuation as data.

    No expansion, substitution or execution. Devuelve `(segmentos, incompleta)`: `incompleta` es True si al
    terminar queda algo abierto (comilla, `$(`, backtick, heredoc sin cierre, escape final); nada se
    descarta en silencio y `check_git` deniega entonces la orden entera si contiene `git` o cambia la base.

    El cuerpo de un heredoc se analiza SIEMPRE como órdenes (T-06 fix6): el guardarraíl y bash discrepaban en cada
    construcción que oculta texto (`$[1<<2]`, `\\⏎` en el delimitador, `$BASH <<'EOF'`…), así que ya no hay reglas de
    salto ni lista de intérpretes. La única excepción son las dos formas exactas de `git commit` con mensaje, que
    `_quitar_mensajes_de_commit` retira de la orden ANTES de llegar aquí."""
    st = _Lectura()
    _leer(command, 0, "top", st, _prof)
    segs, incompleta = st.out, st.opaca or st.incompleta
    for texto, _citado, _cerrado in st.cuerpos:
        if _prof >= _MAX_ANIDADO:
            incompleta = incompleta if isinstance(incompleta, str) else _OPACA_ANIDADO
            continue
        sub, inc = _segmentos(texto, _prof + 1)
        segs.extend(sub)
        if not isinstance(incompleta, str):
            incompleta = inc if isinstance(inc, str) else (incompleta or inc)
    return segs, incompleta


# --- las dos FORMAS EXACTAS de `git commit` cuyo cuerpo de heredoc es el mensaje (T-06 fix6, punto 2; fix7, gaps 1, 2 y 11) ---
# Una palabra de opción: sin comillas ni `$`, backtick, `;`, `&`, `|`, `(`, `)`, `<`, `>`, barra ni espacios, o una
# cadena entrecomillada sin expansión. El delimitador va entrecomillado y el cierre es la PRIMERA línea igual a él.
_PALABRA_RE = re.compile(r"""(?:[^\s'"`$;&|()<>\\]|"[^"$`\\\n]*"|'[^'\n]*')+""")
_ESPACIOS_RE = re.compile(r"[ \t]+")
_GIT_COMMIT_RE = re.compile(r"git[ \t]+commit(?=[ \t])")
_CABECERA_M_RE = re.compile(r"""[ \t]+"\$\(cat[ \t]+<<'([A-Za-z_][A-Za-z0-9_]*)'\n""")
_CABECERA_F_RE = re.compile(r"""[ \t]+<<'([A-Za-z_][A-Za-z0-9_]*)'\n""")
_OPCION_M_RE = re.compile(r"-[A-Za-z]*m|--message")
_DESPUES_RE = re.compile(r"[ \t]*(?:&&|\|\||;|\n|\Z)")
_MAX_FORMAS = 64           # cabeceras que se intentan por orden: lo que pase de ahí se analiza como órdenes normales


def _forma_en(command, pos):
    """Cabecera de una de las dos formas exactas en `pos` (donde empieza `git commit`), sin tocar el cuerpo:
    `(tipo, opciones, flag, delimitador, fin de la cabecera)` o None. Las opciones se leen palabra a palabra y solo
    dentro de SU línea (sin retroceso: `_PALABRA_RE.match` toma la palabra más larga y no hay nada detrás que falle)."""
    m = _GIT_COMMIT_RE.match(command, pos)
    if not m:
        return None
    palabras, j = [], m.end()
    while True:
        e = _ESPACIOS_RE.match(command, j)
        p = _PALABRA_RE.match(command, e.end()) if e else None
        if not p:
            break
        palabras.append((e.start(), p.start(), p.end()))
        j = p.end()
    if not palabras:
        return None
    inicio_u, pal_u, fin_u = palabras[-1]
    ultima = command[pal_u:fin_u]
    c = _CABECERA_M_RE.match(command, j)
    if c and _OPCION_M_RE.fullmatch(ultima):
        return "m", command[m.end():inicio_u], ultima, c.group(1), c.end()
    c = _CABECERA_F_RE.match(command, j)
    if c and ultima == "-" and len(palabras) >= 2 and command[palabras[-2][1]:palabras[-2][2]] == "-F":
        return "f", command[m.end():palabras[-2][0]], None, c.group(1), c.end()
    return None


def _fin_de_forma(command, pos, d, con_parentesis):
    """Posición tras el cierre de la forma (cuerpo desde `pos`, delimitador `d`) o -1 si NO vale. No vale si falta el
    cierre exacto o si alguna línea del cuerpo, sin sus tabuladores iniciales, EMPIEZA por el delimitador sin ser la
    línea de cierre (`D)`, `D;`, `D x`: bash 5.2 cierra el heredoc dentro de `$(…)` con `D)` y ejecuta lo que sigue)."""
    n = len(command)
    while pos < n:
        fin = command.find("\n", pos)
        linea = command[pos:] if fin < 0 else command[pos:fin]
        if linea == d:
            cierre = pos + len(d)
            if con_parentesis:
                return cierre + 3 if command.startswith('\n)"', cierre) else -1
            return cierre
        if linea.lstrip("\t").startswith(d) or fin < 0:
            return -1
        pos = fin + 1
    return -1


def _empieza_sentencia(command, pos):
    """¿Lo que precede a `pos` en su línea es vacío o termina en `&&`, `||`, `;` o salto de línea?"""
    k = pos
    while k > 0 and command[k - 1] in " \t":
        k -= 1
    return k == 0 or command[k - 1] in ";\n" or command[k - 2:k] in ("&&", "||")


def _quitar_mensajes_de_commit(command):
    """Sustituye las dos formas exactas de `git commit` con mensaje por una orden equivalente SIN cuerpo:

    * `git commit [opciones] -m "$(cat <<'D' ⏎ … ⏎ D ⏎ )"`  ->  `git commit [opciones] -m x`
    * `git commit [opciones] -F - <<'D' ⏎ … ⏎ D`            ->  `git commit [opciones] -F -`

    En esas formas el cuerpo es el MENSAJE y no se analiza; las opciones sí (`--no-verify`, `-n`…). La forma vale solo
    si (fix7) EMPIEZA una sentencia según el tokenizador real —una única pasada anota dónde empieza cada palabra `g…`
    de nivel superior, fuera de comentario, comilla, heredoc y sustitución—, lo que la precede en su línea termina en
    `&&`, `||`, `;` o salto de línea, no hay ningún otro heredoc antes (el estado de las comillas en el punto de la
    forma es el mismo para bash y para el guardarraíl), ninguna línea del cuerpo empieza por el delimitador y lo que la
    sigue empieza en un separador. Coste lineal: una pasada del tokenizador, las opciones se leen en su línea y solo se
    intentan `_MAX_FORMAS` cabeceras. Cualquier otro heredoc se analiza como órdenes (con su precio: falso deny si el
    cuerpo tiene comillas impares; la salida es escribir el fichero con la herramienta de edición)."""
    if "<<" not in command or "git" not in command:
        return command
    st = _Lectura()
    _leer(command, 0, "top", st, 0)
    partes, ultimo, validas, intentos = [], 0, 0, 0
    for pos, cuerpos_antes in st.inicios:
        if cuerpos_antes != validas or pos < ultimo or not _empieza_sentencia(command, pos):
            continue
        forma = _forma_en(command, pos)
        if forma is None:
            continue
        intentos += 1
        if intentos > _MAX_FORMAS:
            break
        tipo, opciones, flag, d, cuerpo = forma
        fin = _fin_de_forma(command, cuerpo, d, tipo == "m")
        if fin < 0 or not _DESPUES_RE.match(command, fin):
            continue
        partes.append(command[ultimo:pos])
        partes.append(f"git commit{opciones} {flag} x" if tipo == "m" else f"git commit{opciones} -F -")
        ultimo, validas = fin, validas + 1
    if not validas:
        return command
    partes.append(command[ultimo:])
    return "".join(partes)


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


@functools.lru_cache(maxsize=4096)
def _program_name(token):
    # fix14 (gap 11): memoizada. Una orden de 250 KB de `a;a;…` la llamaba 2,6 millones de veces con los mismos pocos tokens.
    name = token.replace("\\", "/").rsplit("/", 1)[-1].lower()
    return name[:-4] if name.endswith(".exe") else name


# Palabras de control de shell y envoltorios que PRECEDEN al programa real de un segmento: el programa solo cuenta en
# esa posición (`echo cd`, `git restore src/cd`, `git commit -m env` no cambian nada). FUENTE ÚNICA (fix7, gaps 3, 7 y 9):
# `_desenvuelve` es lo que llaman `_check_git` (qué git se invoca) y `_cambia_base_en` (qué cambia la base); ya no hay dos
# implementaciones que se desincronicen (`env -S` solo se desenvolvía en una de ellas).
# fix15 (gaps 3, 4, 6 y 7): `time` y `nohup` ya NO son palabras de control: son envoltorios de la tabla (`/usr/bin/time -f %e git …` y
# `nohup -- git …` tienen opciones y `--`, que una palabra de control no salta), igual que `chrt`, `taskset`, `doas`, `winpty` y `su`.
_CONTROL = frozenset(("if", "then", "else", "elif", "while", "until", "do", "{", "!", "coproc", "builtin"))
_ENVOLTORIOS = frozenset(("env", "command", "builtin", "exec", "sudo", "nohup", "nice", "xargs", "stdbuf",
                          "timeout", "setsid", "ionice", "flock", "time", "chrt", "taskset", "doas", "winpty", "su"))
# Opciones de cada envoltorio (salvo `env`/`command`/`exec`, que tienen su propia rama): `(cortas con valor, largas con
# valor, cortas sin valor, largas sin valor, cortas con valor OPCIONAL pegado)`. Una opción que no figura aquí es
# DESCONOCIDA: el guardarraíl no sabe si consume un valor y, en una orden con `git`, se deniega.
_OPCIONES_ENVOLTORIO = {
    "timeout": ("ks", ("--kill-after", "--signal"), "v", ("--foreground", "--preserve-status", "--verbose",
                                                         "--help", "--version"), ""),
    "nice": ("n", ("--adjustment",), "0123456789", ("--help", "--version"), ""),
    "stdbuf": ("ioe", ("--input", "--output", "--error"), "", ("--help", "--version"), ""),
    "sudo": ("ughpCDRrtTU", ("--user", "--group", "--host", "--prompt", "--close-from", "--chdir", "--chroot", "--role",
                             "--type", "--command-timeout", "--other-user"), "AbEeHiKklnPSsVv",
             ("--askpass", "--background", "--preserve-env", "--edit", "--set-home", "--login", "--non-interactive",
              "--preserve-groups", "--stdin", "--shell", "--reset-timestamp", "--remove-timestamp", "--list",
              "--validate", "--version", "--help", "--no-update"), ""),
    "xargs": ("aEIdLnPs", ("--arg-file", "--delimiter", "--max-args",
                           "--max-procs", "--max-chars", "--process-slot-var"), "0oprtxv",
              ("--null", "--open-tty", "--interactive", "--no-run-if-empty", "--verbose", "--exit", "--show-limits",
               "--help", "--version"), "eil"),
    "setsid": ("", (), "cfw", ("--ctty", "--fork", "--wait", "--help", "--version"), ""),
    "ionice": ("cnpPu", ("--class", "--classdata", "--pid", "--pgid", "--uid"), "t", ("--ignore", "--help",
                                                                                  "--version"), ""),
    "flock": ("wE", ("--timeout", "--wait", "--conflict-exit-code"), "sxuneoF",
              ("--shared", "--exclusive", "--unlock", "--nonblock", "--nb", "--no-fork", "--close", "--fcntl", "--verbose", "--help",
               "--version"), ""),
    "nohup": ("", (), "", ("--help", "--version"), ""),
    # fix15: la palabra reservada `time` solo admite `-p` y `--`; `/usr/bin/time` (GNU) admite ademas `-f`, `-o`, `-a`, `-v`… Se aceptan las de
    # los dos: leer de mas solo analiza mas (`time -f %e git …` no ejecuta nada en la palabra reservada y ejecuta git con el binario).
    "time": ("fo", ("--format", "--output"), "ahpqvV", ("--append", "--help", "--portability", "--quiet", "--verbose",
                                                         "--version"), ""),
    # `chrt [opciones] prioridad orden…` y `taskset [opciones] mascara orden…`: tras las opciones va UN argumento propio (la prioridad / la mascara o
    # la lista de CPU de `-c`), como la duracion de `timeout`.
    "chrt": ("TPD", ("--sched-runtime", "--sched-period", "--sched-deadline"), "abdefhimoprRvV",
             ("--all-tasks", "--batch", "--deadline", "--ext", "--fifo", "--help", "--idle", "--max", "--other", "--pid",
              "--reset-on-fork", "--rr", "--verbose", "--version"), ""),
    "taskset": ("", (), "achpV", ("--all-tasks", "--cpu-list", "--help", "--pid", "--version"), ""),
    "doas": ("Cu", (), "Lns", (), ""),
    "winpty": ("", (), "hV", ("--help", "--version", "--showkey", "--mouse"), ""),
    "su": ("cgGsw", ("--command", "--session-command", "--group", "--supp-group", "--shell", "--whitelist-environment"),
           "lmpfPhV", ("--login", "--fast", "--preserve-environment", "--pty", "--help", "--version"), ""),
}
# Argumentos propios (no son opciones) que van tras las opciones y antes del programa.
_POSICIONALES = {"timeout": 1, "flock": 1, "chrt": 1, "taskset": 1}
# Opciones que se aceptan por PREFIJO (`winpty -Xallow-non-tty`, `-Xplain`).
_PREFIJOS_OPCION = {"winpty": ("-X",)}
# Opcion que lleva la ORDEN en una cadena (`flock F -c 'git …'`, `su -c 'git …'`): la cadena se analiza como `sh -c`, heredando la marca.
_CADENA_CORTAS = {"flock": "sexnuo", "su": "lmpfP"}
_CADENA_LARGAS = {"flock": ("--command",), "su": ("--command", "--session-command")}
# Opciones largas con valor OPCIONAL (GNU): el valor solo va pegado con `=`; separado, la palabra siguiente es el programa
# (`xargs --replace git restore {}` ejecuta `git`). Mismo criterio que `cortas con valor OPCIONAL pegado` (fix8, gap 2).
_LARGAS_OPCIONALES = {"xargs": ("--eof", "--replace", "--max-lines")}
_ENV_LARGAS_SIN_VALOR = ("--null", "--debug", "--list-signal-handling", "--help", "--version")
_ENV_LARGAS_CON_VALOR = ("--argv0",)
# fix16 (gap 1): GNU env trata `--block-signal`, `--default-signal` e `--ignore-signal` con argumento OPCIONAL: solo lo lleva pegado con `=`. Separado, la palabra
# siguiente es el programa (`env --default-signal git push --force` ejecuta git). Antes el guard se comia `git` como su valor.
_ENV_LARGAS_OPCIONALES = ("--block-signal", "--default-signal", "--ignore-signal")
_ENV_LARGAS = ("--ignore-environment", "--unset", "--chdir", "--split-string") + _ENV_LARGAS_SIN_VALOR + _ENV_LARGAS_CON_VALOR + _ENV_LARGAS_OPCIONALES


def _env_larga(o):
    """La opcion larga CANONICA de `env` que `o` abrevia (cualquier prefijo unico, como getopt: `--split`, `--s`, `--split=…`) o None si no
    existe o es ambigua (`--i`: `--ignore-environment` o `--ignore-signal`)."""
    base = o.split("=", 1)[0]
    candidatas = [x for x in _ENV_LARGAS if x == base] or [x for x in _ENV_LARGAS if x.startswith(base)]
    return candidatas[0] if len(candidatas) == 1 and len(base) >= 3 else None
_REDIRECCION_RE = re.compile(r"(?:[0-9]*|&)(?:<<<|<<|>>|>&|<&|<>|>\||>|<)(.*)\Z", re.DOTALL)
_MAX_RESOLUCIONES = 64


def _salta_redireccion(toks, i):
    """Índice tras una redirección que ocupa `toks[i]` (`>f`, `2>&1`, `&>f`, o `>` seguido de su destino); `i` si
    `toks[i]` no es una redirección. En posición de programa `2>&1 git restore .` ejecuta `git restore .`."""
    m = _REDIRECCION_RE.fullmatch(toks[i])
    if not m:
        return i
    return i + (1 if m.group(1) else 2)


def _opcion_envoltorio(nombre, toks, i):
    """Consume la opción de `toks[i]` (empieza por `-`) de un envoltorio de la tabla: `(índice siguiente, ¿conocida?)`.
    Las opciones largas aceptan cualquier prefijo único (como getopt) y su valor va tras `=` o en el token siguiente;
    las cortas se leen en clúster y una letra con valor se lleva el resto del token o el token siguiente."""
    cortas_v, largas_v, cortas_s, largas_s, cortas_o = _OPCIONES_ENVOLTORIO[nombre]
    o = toks[i]
    if o.startswith("--"):
        base = o.split("=", 1)[0]
        todas = largas_v + largas_s + _LARGAS_OPCIONALES.get(nombre, ())
        candidatas = [x for x in todas if x == base] or [x for x in todas if x.startswith(base)]
        if len(candidatas) != 1:
            return i + 1, False
        return (i + 2 if candidatas[0] in largas_v and "=" not in o else i + 1), True
    for k in range(1, len(o)):
        letra = o[k]
        if letra in cortas_v:
            return (i + 1 if k < len(o) - 1 else i + 2), True      # valor pegado o en el token siguiente
        if letra in cortas_o:
            return i + 1, True                                      # valor opcional: solo pegado
        if letra not in cortas_s:
            return i + 1, False
    return i + 1, True


def _cadena_de_orden(nombre, toks, i):
    """La opcion de `toks[i]` lleva la orden en una cadena (`flock -c|--command`, `su -c|--command|--session-command`)? `(indice siguiente,
    cadena)` o None. Valida cualquier prefijo unico de la larga, la corta suelta (`-c cadena`), pegada (`-cCADENA`) y en cluster (`-xc cadena`)."""
    o = toks[i]
    if o.startswith("--"):
        base = o.split("=", 1)[0]
        largas = _CADENA_LARGAS[nombre]
        candidatas = [x for x in largas if x == base] or [x for x in largas if x.startswith(base)]
        if len(candidatas) != 1 or len(base) < 3:
            return None
        if "=" in o:
            return i + 1, o.split("=", 1)[1]
        return i + 2, (toks[i + 1] if i + 1 < len(toks) else "")
    if not o.startswith("-") or o == "-":
        return None
    for k in range(1, len(o)):
        if o[k] == "c":
            pegada = o[k + 1:]
            if pegada:
                return i + 1, pegada
            return i + 2, (toks[i + 1] if i + 1 < len(toks) else "")
        if o[k] not in _CADENA_CORTAS[nombre]:
            return None
    return None


def _saltar_envoltorio(toks, i):
    """`(índice tras el envoltorio de `toks[i]` y sus opciones, ¿cambia el directorio?, opción desconocida|None, cadena de orden|None)`:
    salta opciones (con el valor de las que lo toman) y los argumentos propios (`_POSICIONALES`: la duración de `timeout`, el fichero
    de `flock`, la prioridad de `chrt`, la máscara de `taskset`). `sudo -D`/`--chdir` cambia el directorio de trabajo. Una opción de
    orden en cadena (`flock -c`, `su -c`) devuelve la cadena: el llamante la analiza como `sh -c` (fix15, gap 3). Lineal en `toks`."""
    nombre = _program_name(toks[i])
    n, chdir = len(toks), False
    i += 1
    if nombre == "su":
        # `su [opciones] [-] [usuario [argumentos]]`: sin `-c` no hay programa que ejecutar (abre una shell); con `-c`, la cadena es la orden,
        # antes o despues del usuario.
        for k in range(i, n):
            cadena = _cadena_de_orden(nombre, toks, k)
            if cadena:
                return cadena[0], chdir, None, cadena[1]
        return n, chdir, None, None
    while i < n:
        o = toks[i]
        if o == "--":
            i += 1
            break
        if not o.startswith("-") or o == "-":
            break
        if nombre == "sudo" and (o.startswith("--chdir") or (not o.startswith("--") and "D" in o[1:])):
            chdir = True
        if nombre == "flock":
            cadena = _cadena_de_orden(nombre, toks, i)
            if cadena:
                return cadena[0], chdir, None, cadena[1]          # `flock -c 'git …' f` o `flock --command='git …' f`
        if any(o.startswith(p) for p in _PREFIJOS_OPCION.get(nombre, ())):
            i += 1
            continue
        j, conocida = _opcion_envoltorio(nombre, toks, i)
        if not conocida:
            if nombre == "flock":
                # fix16 (gap 12): una opcion fuera de la tabla no impide buscar `-c`/`--command` en el resto (`flock --opcion-nueva F -c 'git ...'`)
                for k in range(i + 1, n):
                    cadena = _cadena_de_orden(nombre, toks, k)
                    if cadena:
                        return cadena[0], chdir, None, cadena[1]
            return i, chdir, o, None
        i = j
    i = min(n, i + _POSICIONALES.get(nombre, 0))
    if nombre == "flock":
        # `flock F -c 'git …'`: la orden en cadena va DESPUÉS del fichero, la forma canónica de flock
        while i < n and toks[i].startswith("-") and toks[i] != "-":
            cadena = _cadena_de_orden(nombre, toks, i)
            if not cadena:
                break
            return cadena[0], chdir, None, cadena[1]
    return i, chdir, None, None


_MAX_TROCEOS_S = 4
_MAX_VALOR_S = 2048             # un valor más largo no se trocea: se deniega SIEMPRE (el troceo es carácter a carácter)
_ESCAPES_ENV = {"t": "\t", "n": "\n", "v": "\v", "f": "\f", "r": "\r", "\\": "\\", "'": "'", '"': '"', "#": "#",
                "$": "$"}
_BLANCOS_ENV = " \t"       # coreutils 8.x separa SOLO por espacio y tabulador; 9.x también por LF, VT, FF y CR: estos cuatro, sueltos, son ambiguos (fix10)


class _OpcionIlegible(str):
    """La opción `-S` cuyo valor el guardarraíl no puede trocear. `siempre`: se deniega con o sin `git` (valor fuera del
    tope o con una comilla abierta); si no, solo con `git` (un escape desconocido, que env rechaza)."""
    siempre = False
    motivo = ""             # fix14: texto de la lectura OPACA (LF/VT/FF/CR suelto); vacío = valor fuera del tope o comilla abierta


class _SinTroceo(Exception):
    def __init__(self, siempre, motivo=""):
        super().__init__(siempre)
        self.siempre = siempre
        self.motivo = motivo        # fix14: texto de la lectura OPACA (LF/VT/FF/CR suelto en `env -S`); vacío en el resto


_OPACA_ENV_S = ("`env -S` con un LF/VT/FF/CR suelto en su valor (coreutils 8.x no lo separa y 9.x sí, y tras él un `#` abre un "
                "comentario)")


def _trocea_s(valor, cortes):
    r"""Palabras de un valor de `env -S` TROCEADO COMO LO HACE GNU env (fix9, gap 4; antes `shlex`, que no conoce sus
    escapes): solo el espacio y el tabulador separan (un LF, VT, FF o CR suelto es ambiguo entre coreutils 8.x y 9.x: lectura OPACA, se deniega siempre, fix14); las comillas simples son literales salvo `\\` y `\'`; las dobles admiten escapes; fuera
    de comillas `\_` separa y `\c` corta; `\t \n \v \f \r \\ \' \" \# \$` son el carácter; un `#` al empezar palabra abre un
    comentario. Lanza `_SinTroceo(siempre=True)` si ya hubo `_MAX_TROCEOS_S` troceos en esta orden (cada uno reconstruye la
    lista: una cadena de `-S` anidados sería cuadrática, fix8, gap 4), si el valor pasa de `_MAX_VALOR_S` caracteres o si
    queda una comilla abierta, y `_SinTroceo(siempre=False)` ante un escape desconocido o una barra final (env falla: se
    deniega solo con `git`). Lineal en el valor."""
    cortes[0] += 1
    if cortes[0] > _MAX_TROCEOS_S or len(valor) > _MAX_VALOR_S:
        raise _SinTroceo(True)
    palabras, palabra, en_palabra, comilla, i, n = [], [], False, None, 0, len(valor)

    def cierra():
        nonlocal palabra, en_palabra
        if en_palabra:
            palabras.append("".join(palabra))
        palabra, en_palabra = [], False

    while i < n:
        c = valor[i]
        if comilla == "'":
            if c == "'":
                comilla = None
            elif c == "\\" and valor[i + 1:i + 2] in ("\\", "'"):
                i += 1
                palabra.append(valor[i])
            else:
                palabra.append(c)
        elif c == "\\":
            sig = valor[i + 1:i + 2]
            if not sig:
                raise _SinTroceo(False)                       # barra final
            i += 1
            if sig == "_":
                if comilla == '"':
                    palabra.append(" ")
                else:
                    cierra()                                  # fuera de comillas es un separador
            elif sig == "c":
                if comilla:
                    raise _SinTroceo(False)                   # env: «'\c' must not appear in double-quoted -S string»
                break
            elif sig in _ESCAPES_ENV:
                palabra.append(_ESCAPES_ENV[sig])
                en_palabra = True
            else:
                raise _SinTroceo(False)
        elif comilla == '"':
            if c == '"':
                comilla = None
            else:
                palabra.append(c)
        elif c in "'\"":
            comilla, en_palabra = c, True
        elif c in _BLANCOS_ENV:
            cierra()
        elif c in "\n\v\f\r":
            # Forma AMBIGUA (fix10), OPACA desde fix14: coreutils 8.x no separa por ellos y 9.x sí (y tras ellos un `#` abre un
            # comentario). Lo que ejecuta cada env es distinto y el guardarraíl no sabe cuál: se deniega SIEMPRE, con o sin git.
            raise _SinTroceo(True, _OPACA_ENV_S)
        elif c == "#" and not en_palabra:
            break
        else:
            palabra.append(c)
            en_palabra = True
        i += 1
    if comilla:
        raise _SinTroceo(True)
    cierra()
    return palabras


def _opcion_ilegible(opcion, siempre, motivo=""):
    ilegible = _OpcionIlegible(opcion)
    ilegible.siempre = siempre
    ilegible.motivo = motivo
    return ilegible


def _opciones_env(nombre, toks, i, bindings, cortes):
    """`env`/`command`/`exec` en `toks[i]`: `(índice del programa, toks, ¿cambia el directorio?, opción
    desconocida|None)`. Anota en `bindings` lo que `env` deja o quita del entorno; el valor de `env -S` (una línea de
    órdenes que env trocea y ejecuta) se ANALIZA entero: sus palabras sustituyen a la opción en `toks`."""
    chdir = False
    i += 1
    while i < len(toks) and toks[i].startswith("-") and toks[i] != "--":
        o = toks[i]
        if nombre == "command":
            if o == "-p":
                i += 1
                continue
            if o in ("-v", "-V"):
                return i, toks, chdir, None        # `command -v git` consulta, no ejecuta
            return i, toks, chdir, o
        if o.startswith("--"):
            canon = _env_larga(o) if nombre == "env" else None     # fix15 (gap 7): `--split`, `--s`, `--split=` equivalen a `--split-string`
            if canon == "--ignore-environment":
                bindings.clear()
                i += 1
            elif canon == "--unset" and ("=" in o or i + 1 < len(toks)):
                if "=" in o:
                    bindings.pop(o.split("=", 1)[1], None)
                    i += 1
                else:
                    bindings.pop(toks[i + 1], None)
                    i += 2
            elif canon == "--chdir" and ("=" in o or i + 1 < len(toks)):
                chdir = True
                i += 1 if "=" in o else 2
            elif canon == "--split-string":
                valor, usados = ((o.split("=", 1)[1], 1) if "=" in o else
                                 (toks[i + 1] if i + 1 < len(toks) else "", 2))
                try:
                    palabras = _trocea_s(valor, cortes)
                except _SinTroceo as ilegible:
                    return i, toks, chdir, _opcion_ilegible(o, ilegible.siempre, ilegible.motivo)
                toks = toks[:i] + palabras + toks[i + usados:]
            elif canon in _ENV_LARGAS_SIN_VALOR:
                i += 1
            elif canon in _ENV_LARGAS_CON_VALOR:
                i += 1 if "=" in o else 2
            elif canon in _ENV_LARGAS_OPCIONALES:
                i += 1                      # fix16: el valor, si lo hay, va pegado con `=`
            else:
                return i, toks, chdir, o
            continue
        if o == "-" and nombre == "env":
            bindings.clear()
            i += 1
            continue
        k, consumido = 1, False
        while k < len(o):
            letra = o[k]
            if nombre == "env" and letra == "i":
                bindings.clear()
            elif (nombre == "env" and letra in "0v") or (nombre == "exec" and letra == "l"):
                pass
            elif nombre == "exec" and letra == "c":
                bindings.clear()
            elif (nombre == "env" and letra in "uCSaP") or (nombre == "exec" and letra == "a"):
                valor, usados = o[k + 1:], 1
                if not valor:
                    if i + 1 >= len(toks):
                        return i, toks, chdir, o
                    valor, usados = toks[i + 1], 2
                if letra == "u":
                    bindings.pop(valor, None)
                elif letra == "C":
                    chdir = True
                elif letra == "S":
                    try:
                        palabras = _trocea_s(valor, cortes)
                    except _SinTroceo as ilegible:
                        return i, toks, chdir, _opcion_ilegible(o, ilegible.siempre, ilegible.motivo)
                    toks = toks[:i] + palabras + toks[i + usados:]
                    usados = 0
                i += usados
                consumido = True
                break
            else:
                return i, toks, chdir, o
            k += 1
        if not consumido:
            i += 1
    if i < len(toks) and toks[i] == "--":
        i += 1
    return i, toks, chdir, None


@functools.lru_cache(maxsize=4096)
def _es_programa_llano(t):
    """¿`t` es ya el programa? Ni asignación, ni palabra de control, ni `function`, ni redirección, ni envoltorio: el recorrido de
    `_desenvuelve` sobre él no haría nada y termina en el primer token (fix14, gap 11: 125.000 segmentos de una palabra)."""
    if t == "function" or t in _CONTROL or _ASSIGNMENT_RE.fullmatch(t) or _REDIRECCION_RE.fullmatch(t):
        return False
    nombre = _program_name(t)
    return nombre not in ("env", "command", "exec") and nombre not in _ENVOLTORIOS


def _desenvuelve(toks, inherited=None):
    """`(resto, bindings, ¿cambia el directorio un envoltorio?, opción desconocida|None, ¿pasó por xargs?)` de un
    segmento: salta asignaciones (que se anotan en `bindings`), palabras de control, redirecciones iniciales, `function
    nombre` y envoltorios con sus opciones, hasta el programa real (`resto[0]`). Nunca evalúa texto de shell. Recorrido
    lineal: nada de rebanar `toks` por token. Una opción desconocida detiene el desenvuelto: `resto` empieza en ella."""
    bindings = dict(inherited or {})
    toks = list(toks)
    i, chdir, desconocida, via_xargs = 0, False, None, False
    cortes = [0]                        # troceos de `env -S` de esta invocación (tope: `_MAX_TROCEOS_S`)
    tras_env = False                    # fix16 (gap 7): tras `env`, CUALQUIER argumento con `=` es una asignacion (`env 1=x git ...`, `env A-B=1 git ...`)
    while i < len(toks):
        t = toks[i]
        if tras_env and "=" in t and not t.startswith("-"):
            asignacion = _ASSIGNMENT_RE.fullmatch(t)
            if asignacion:
                bindings[asignacion[1]] = asignacion[2]      # `env GIT_DIR=x git …` sigue anotando la variable sensible
            i += 1
            continue
        if _es_programa_llano(t):
            break
        asignacion = _ASSIGNMENT_RE.fullmatch(t)
        if asignacion:
            bindings[asignacion[1]] = asignacion[2]
            i += 1
        elif t == "function" and i + 1 < len(toks):
            i += 2                      # `function f { git … }`: el nombre y la llave no son el programa
        elif t == "coproc" and i + 2 < len(toks) and toks[i + 2] == "{":
            i += 3                      # fix16 (gap 7): `coproc NAME { git ...; }`: el nombre y la llave no son el programa
        elif t == "builtin" and i + 1 < len(toks) and toks[i + 1] == "--":
            i += 2                      # fix16 (gap 4): `builtin -- exec git ...`
        elif t in _CONTROL:
            i += 1          # `{ git restore .; }`, `then git restore .`, `! git …`: el programa sigue después
        elif _salta_redireccion(toks, i) != i:
            i = _salta_redireccion(toks, i)
        else:
            nombre = _program_name(t)
            if nombre in ("env", "command", "exec"):
                tras_env = tras_env or nombre == "env"
                i, toks, cambia, desc = _opciones_env(nombre, toks, i, bindings, cortes)
            elif nombre in _ENVOLTORIOS:
                via_xargs = via_xargs or nombre == "xargs"
                i, cambia, desc, cadena = _saltar_envoltorio(toks, i)
                if cadena is not None:
                    # `flock F -c 'git …'`, `su -c 'git …'`: la cadena es una orden de shell, igual que `sh -c '…'` (fix15, gap 3)
                    toks, i, chdir = ["sh", "-c", cadena], 0, chdir or cambia
                    continue
            else:
                break
            chdir = chdir or cambia
            if desc:
                desconocida = desc
                break
    return toks[i:], bindings, chdir, desconocida, via_xargs


def _literal_invocation(toks, inherited=None):
    """`(resto, bindings)` de `_desenvuelve`: qué programa se invoca y con qué asignaciones."""
    resto, bindings, _chdir, _desconocida, _xargs = _desenvuelve(toks, inherited)
    return resto, bindings


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


# Subcomandos que descartan o reescriben ficheros del árbol: con `xargs` las rutas llegan por la entrada estándar y no
# se pueden validar (fix7, gap 4), igual que `--pathspec-from-file`.
_XARGS_DESTRUCTIVOS = frozenset(("restore", "checkout", "reset", "clean", "rm", "checkout-index", "read-tree"))
_CAMBIA_DIR = frozenset(("cd", "pushd", "popd", "chdir"))
_GIT_DESTRUCTIVOS = frozenset(("checkout", "switch", "restore", "reset", "clean", "stash", "branch",
                               "update-ref", "push"))


def _git_cambia_base(toks):
    """¿La invocación cambia el directorio/árbol que git usa? `git -C`, `--work-tree`, `--git-dir`
    (T-06 fix3, gap 3). Solo mira las opciones globales, antes del subcomando."""
    if not toks or _program_name(toks[0]) != "git":
        return False
    i = 1
    while i < len(toks) and toks[i].startswith("-"):
        o = toks[i]
        if o in ("-C", "--work-tree", "--git-dir") or o.startswith(("--work-tree=", "--git-dir=")) \
                or (o.startswith("-C") and not o.startswith("--")):
            return True
        i += 2 if o in _GIT_GLOBAL_VALUES else 1
    return False


def _destino_es_el_propio_directorio(destino, memo=None):
    """¿El destino de un `cd`, resuelto, es el directorio de trabajo del hook? (gap 4). Lo que no se
    puede resolver sin ejecutar (`$X`, `~`, backtick, `-`) cuenta como cambio de base. `memo` (por orden)
    resuelve el cwd una vez y cada destino distinto una vez, con tope: pasado el tope, cambia la base."""
    if not destino or any(c in destino for c in "$`~*?[") or destino == "-":
        return False
    if memo is not None:
        if destino in memo["dest"]:
            return memo["dest"][destino]
        if len(memo["dest"]) >= _MAX_RESOLUCIONES:
            return False
    d = destino.replace("\\", "/") if os.name == "nt" else destino
    m = re.match(r"/([A-Za-z])(/.*)?\Z", d) if os.name == "nt" else None
    if m:
        d = m.group(1).upper() + ":" + (m.group(2) or "/")
    try:
        cwd = os.getcwd()
        if memo is not None and memo["cwd"] is None:
            memo["cwd"] = os.path.normcase(os.path.realpath(cwd))
        real_cwd = memo["cwd"] if memo is not None else os.path.normcase(os.path.realpath(cwd))
        propio = os.path.normcase(os.path.realpath(os.path.join(cwd, d))) == real_cwd
    except (OSError, ValueError):                 # fix12: `UnicodeEncodeError` (surrogate suelto) y `ValueError` son indeterminados
        propio = False                            # = «cambia la base»: falla cerrado
    if memo is not None:
        memo["dest"][destino] = propio
    return propio


def _cd_cambia_base(toks, idx, memo=None):
    """`cd|pushd|popd|chdir` en `toks[idx]`: cambia la base salvo `cd <propio directorio>` (gap 4)."""
    if _program_name(toks[idx]) not in ("cd", "chdir"):
        return True                      # pushd/popd: la pila de directorios no se resuelve aquí
    k = idx + 1
    while k < len(toks) and toks[k] in ("-L", "-P", "-e", "-@", "--"):
        k += 1
    return not (k < len(toks) and _destino_es_el_propio_directorio(toks[k], memo))


# Un `source`/`.` cuyo argumento es un descriptor, la entrada estándar o una sustitución de proceso (`<(…)` → el token `<`)
# ejecuta texto que el guardarraíl SÍ ve (heredoc, `echo cd ..` dentro de `<(…)`); con un fichero no lo ve.
_FUENTE_VISIBLE = ("<", "/dev/", "/proc/")


def _cambia_base_en(segmentos, _prof=0):
    """¿Alguna parte de la orden cambia el directorio/árbol de git? Solo en POSICIÓN DE PROGRAMA de cada
    segmento (tras asignaciones, palabras de control y envoltorios): `command cd ..`, `{ cd ..; … }`,
    `if …; then cd ..; fi`, `time cd`, `! cd`, `A=1 env -C ..`, `git -C ..`. Un `cd`/`env`/`git` que es solo
    un ARGUMENTO (`echo cd`, `git restore src/cd`) no cuenta. Lineal en el tamaño de la orden (T-06 fix5).
    Fix6, gap 5: el cambio de base se busca TAMBIÉN en el contenido de `eval` (sus argumentos son órdenes que se
    ejecutan en esta shell) y en `source`/`.` cuyo contenido se ve (`/dev/stdin`, `/dev/fd/…`, `<(…)`, un heredoc);
    las funciones ya están aplanadas en los segmentos y `. <(…)` también (los paréntesis separan órdenes).
    Fix7: el desenvuelto es el de `_desenvuelve` (el MISMO que usa `_check_git`: `env -S '…'` se analiza entero) y un
    `source`/`.` de un FICHERO normal ya no cuenta (su contenido no se ve: es un límite conocido del modelo de amenaza,
    docs/agents/implementer.md); antes `source .venv/bin/activate && git restore src/a.py` era un falso deny."""
    memo = {"cwd": None, "dest": {}}
    for toks in segmentos:
        resto, _bindings, chdir, _desconocida, _xargs = _desenvuelve(toks)
        if chdir:
            return True
        if not resto:
            continue
        nombre = _program_name(resto[0])
        if (nombre in _CAMBIA_DIR and _cd_cambia_base(resto, 0, memo)) \
                or (nombre == "git" and _git_cambia_base(resto)):
            return True
        if nombre in (".", "source") and any(a.startswith(_FUENTE_VISIBLE) or a == "-" for a in resto[1:]):
            return True
        if nombre in ("eval", "trap"):
            for cadena in _subcomandos_shell(resto):
                if _prof >= 3 or _cambia_base_en(_segmentos(cadena)[0], _prof + 1):
                    return True
        if nombre != "git":
            # fix16 (gap 1): git en cualquier posicion de la orden simple (`chroot / git -C ..`, `strace git -C ..`)
            if any(_program_name(w) == "git" and _git_cambia_base(resto[k:]) for k, w in enumerate(resto) if k):
                return True
    return False


_PRINCIPAL_RE = re.compile(r"(?:refs/heads/|heads/|refs/remotes/[^/]+/|remotes/[^/]+/|(?:origin|upstream)/)?"
                           r"(?:main|master)(?:[\^~].*|@\{.*)?\Z", re.I)


_ANTERIOR_RE = re.compile(r"@\{-[0-9]+\}")
_REMOTA_RE = re.compile(r"(?:refs/remotes/|remotes/|(?:origin|upstream)/)")


def _es_rama_principal(destino):
    """¿`destino` nombra la rama principal con alguna de sus formas (`master`, `refs/heads/master`, `origin/main`,
    `master^0`, `MAIN`)? Una rama de trabajo llamada `feature/main` NO cuenta."""
    return bool(_PRINCIPAL_RE.fullmatch(destino))


def _es_git(toks, sub):
    """Index of a recognized Git subcommand, or -1."""
    if not toks or _program_name(toks[0]) != "git":
        return -1                                      # fix14 (gap 11): lo habitual, sin analizar opciones globales
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
_MAX_ORDEN = 262144       # bytes: por encima, la orden se deniega sin analizarla
# Recorte barato y lineal ANTES de tokenizar (T-06 fix6, punto 1): por encima de 16 KB o 4.000 palabras la orden se
# deniega si su texto contiene `git` (sin distinguir mayúsculas: `GIT_DIR`) o algo que cambia la base. Por debajo de la
# cota el análisis es lineal (una pasada del tokenizador, tablas con búsqueda binaria, lista blanca de commit acotada) y
# las pruebas de coste (`test_guardrail_fix7.py`, `test_guardrail_check.py`) lo comprueban; si aun así el plazo del
# lanzador se agotara, el lanzador deniega por el rol protegido (ADR-023).
_MAX_TOKENS = 4000        # palabras (separadas por espacio) de la orden completa
_MAX_VISIBLE = 16384      # caracteres de la orden completa
_RECORTE_RE = re.compile(r"git|\b(?:cd|pushd|popd|chdir|env|eval|source)\b|--work-tree|--git-dir|--chdir", re.I)
_GIT_TEXTO_RE = re.compile(r"\bgit\b", re.I)   # fix14: git en Windows y macOS también es `GIT`/`Git`
# Intérpretes que, tras una opción de envoltorio desconocida, hacen que el guardarraíl deniegue aunque no vea git (fix14, gap 3).
_INTERPRETES = frozenset(_SHELLS | {"eval", "env", "xargs", "source", "exec", "command"})
_NOTA_HEREDOC = (" El cuerpo de un heredoc se analiza como órdenes (salvo en `git commit -m \"$(cat <<'EOF' … EOF\\n)\"` "
                 "y `git commit -F - <<'EOF' … EOF`): si es un fichero o un texto, escríbelo con la herramienta de "
                 "edición y usa `git commit -F <fichero>`, o evita las comillas impares en el cuerpo.")

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
    palabras = [t for t in toks[1:] if not t.startswith("-")] if (prog in _PAQUETEROS or prog in _CONTENEDORES or prog == "kubectl") else ()
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
    (también en clusters `-lc`, `-ec`, y `-oc VALOR`/`-Oc VALOR`/`-co VALOR`, donde `-o`/`-O` consumen su valor), los argumentos de `eval`
    (que acepta `--`) y la cadena de `trap` (la accion se ejecuta al saltar la senal: fix16, gaps 4, 5 y 6)."""
    if not toks:
        return []
    prog = _program_name(toks[0])
    if prog == "eval":
        resto = toks[2:] if len(toks) > 1 and toks[1] == "--" else toks[1:]
        return [" ".join(resto)] if resto else []
    if prog == "trap":
        # `trap [-lp] [--] [accion] señal…`: la accion es el primer argumento que no es opcion (`-` y la cadena vacia la restauran o ignoran).
        resto = [t for t in toks[1:] if t not in ("-p", "-l", "-lp", "-pl")]
        if resto and resto[0] == "--":
            resto = resto[1:]
        return [resto[0]] if resto and resto[0] not in ("", "-") else []
    if prog in _SHELLS or prog.startswith("$"):        # `$SHELL -c '…'`, `p=bash; $p -c '…'` (fix6, lente A)
        for i, t in enumerate(toks[1:], 1):
            if re.fullmatch(r"-[a-zA-Z]*c[a-zA-Z]*", t):
                destino = i + 1 + sum(1 for letra in t[1:] if letra in "oO")      # fix16 (gap 6): cada `o`/`O` del cluster consume un valor antes de la orden
                if destino < len(toks):
                    # `bash -c -- 'git …'`: tras `-c`, un `--` termina las opciones y la orden es la palabra siguiente (fix7)
                    return [toks[destino + 1] if toks[destino] == "--" and destino + 1 < len(toks) else toks[destino]]
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


def _clave_abs(ruta):
    """Ruta absoluta en forma comparable: `/` como separador, `C:/x` y `/c/x` unificados, minúsculas."""
    r = ruta.replace("\\", "/")
    m = re.match(r"^([A-Za-z]):(/.*)?$", r)
    if m:
        r = "/" + m.group(1) + (m.group(2) or "")
    return posixpath.normpath(r).lower() if r.startswith("/") else r.lower()


def _pathspec_permitido(token):
    """LISTA DE PERMITIDOS para el pathspec de `checkout`/`restore` que tocan el árbol (T-06 fix2, gap 1).

    Solo pasa una ruta relativa LITERAL: sin magia (empieza por `:`), sin comodines (`*`, `?`, `[`), sin
    expansión de shell (`$`, backtick, `~` inicial) y que, normalizada contra el directorio actual, queda
    DENTRO del proyecto sin ser el directorio actual, uno de sus ancestros ni la raíz. `../otro.py` pasa
    si el resultado sigue dentro del proyecto (`CLAUDE_PROJECT_DIR` si contiene al directorio actual, o el
    propio directorio actual). Las rutas absolutas se deniegan (nombra la relativa). No resuelve enlaces
    simbólicos. Cualquier otra forma se deniega: no se enumeran casos, se enumera lo aceptable."""
    if not token or token.startswith(":") or token.startswith("~"):
        return False
    if re.search(r"[*?\[$`]", token):
        return False
    t = token.replace("\\", "/")
    if t.startswith("/") or re.match(r"^[A-Za-z]:", t):
        return False
    cwd = _clave_abs(os.getcwd())
    raiz = cwd
    pdir = os.environ.get("CLAUDE_PROJECT_DIR")
    if pdir:
        p = _clave_abs(pdir)
        if cwd == p or cwd.startswith(p.rstrip("/") + "/"):
            raiz = p
    destino = posixpath.normpath(posixpath.join(cwd, t.lower()))
    if destino == raiz or cwd == destino or cwd.startswith(destino.rstrip("/") + "/"):
        return False
    return destino.startswith(raiz.rstrip("/") + "/")


def _valor_separado_de_source(t):
    """`--source X` / `-s X` / `-Ws X`: la opción consume el token SIGUIENTE como valor (gap 8)."""
    if t.startswith("--"):
        return "=" not in t and len(t) >= 4 and "--source".startswith(t)
    if re.fullmatch(r"-[a-zA-Z]+", t):
        for idx, ch in enumerate(t[1:], 1):
            if ch == "s":
                return idx == len(t) - 1
            if ch == "U":
                return False
    return False


def _razon_restauracion(sub, args, base_cambiada=False):
    """`git checkout|switch|restore` que DESCARTA cambios sin comitear (T-06, plugin-audit-2).

    Deniega: `checkout -f|--force`, `switch -f|--force|--discard-changes`, `--pathspec-from-file` (su
    contenido no se ve), `restore --worktree|-W` y, en `checkout|restore` que tocan el árbol, todo
    pathspec que NO sea una ruta relativa literal acotada (`_pathspec_permitido`: lista de permitidos).
    En `restore` cuentan como pathspec todos los argumentos que no son opción, antes o después de `--`;
    en `checkout`, los de después de `--` y, sin `--` ni `-b/-B`, todos los sueltos (pueden ser ficheros).
    NO toca `checkout <rama>`, `checkout -b|-B|-`, `checkout <rama> -- <fichero>`, `restore <fichero>` ni
    `restore --staged <lo-que-sea>` (solo índice; la regla de P4 sobre ficheros con cambios previos sigue
    siendo prosa del implementer).
    """
    if "--" in args:
        k = args.index("--")
        antes, rutas = args[:k], args[k + 1:]
    else:
        antes, rutas = args, []
    opciones, sueltos, k = [], [], 0
    while k < len(antes):
        t = antes[k]
        if t.startswith("-"):
            opciones.append(t)
            if sub == "restore" and _valor_separado_de_source(t):
                k += 1                      # el valor de `-s`/`--source` NO es un pathspec (gap 8)
        else:
            sueltos.append(t)
        k += 1
    if sub == "restore":
        rutas = sueltos + rutas                 # en restore todo lo que no es opción es pathspec
    elif "--" not in args and not any(re.match(r"-[a-zA-Z]*[bB]", t) and not t.startswith("--")
                                      or _prefijo(t, "--orphan") for t in opciones):
        rutas = sueltos                          # `checkout X` sin `--` y sin -b/-B: X puede ser un fichero
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
            if any(_prefijo(t, "--pathspec-from-file") for t in opciones):
                return msg
            if base_cambiada and rutas:
                return (f"`git {sub}` que descarta cambios sin comitear bloqueado: la orden cambia la base "
                        "(`git -C`, `--work-tree`, `--git-dir`, `env -C`, `cd`/`pushd`, `eval`, `source <(…)`) y el guardarraíl "
                        "valida la ruta contra el directorio actual — ejecuta la orden desde ese directorio.")
            malo = next((t for t in rutas if not _pathspec_permitido(t)), None)
            if malo is not None:
                return (f"`git {sub}` que descarta cambios sin comitear bloqueado: el pathspec `{malo}` no es "
                        "una ruta relativa literal dentro del proyecto (sin `:`, comodines, `$`, "
                        "backtick ni `~`, sin ser el propio directorio, un ancestro ni la raíz) — nombra el fichero "
                        "exacto o revierte con `git diff <foto> -- <ficheros> | git apply -R`.")
    if sub == "restore" and any(_prefijo(t, "--worktree") or _cluster(t, "W") for t in opciones):
        return msg
    return None


_ESCAPE_NUMERICO_RE = re.compile(r"\\(?:x\{([0-9a-fA-F]+)\}?|x([0-9a-fA-F]{1,2})|u([0-9a-fA-F]{1,4})|U([0-9a-fA-F]{1,8})|([0-7]{1,3}))")


class _DecodificacionInestable(Exception):
    """Los escapes numéricos de la orden siguen cambiando tras `_RONDAS_ESCAPES` rondas: lectura OPACA (fix15, gap 2)."""


_RONDAS_ESCAPES = 8       # más que la profundidad 3 de `bash -c`/`eval` con holgura; si no se estabiliza, el guardarraíl no sabe qué se forma


def _numerico(m):
    for valor, base in zip(m.groups(), (16, 16, 16, 16, 8)):
        if valor:
            try:
                return chr(int(valor, base))
            except (ValueError, OverflowError):
                return ""
    return m.group(0)


def _aplanado(command):
    """El texto sin la sintaxis que esconde palabras: escapes numéricos de `$'…'` aplicados HASTA UN PUNTO FIJO y sin comillas, barras ni `$`.
    Vista TERCERA y generosa para una lectura incompleta (fix14): el guardarraíl no sabe dónde acaban las comillas y las
    sustituciones, así que `"$(… *) g''it status …)"` o `$'\\x67it'` quedan como texto que no se decodifica. Una orden de nivel N
    (`bash -c $'$\\'\\x5cx67it\\''`) lleva el git codificado N veces: cada ronda decodifica un nivel (fix15, gap 2). Lineal: como mucho
    `_RONDAS_ESCAPES` + 1 pasadas. Lanza `_DecodificacionInestable` si tras `_RONDAS_ESCAPES` rondas aún cambia."""
    texto = command
    if "\\" in texto:
        for _ in range(_RONDAS_ESCAPES):
            nuevo = _ESCAPE_NUMERICO_RE.sub(_numerico, texto)
            if nuevo == texto:
                break
            texto = nuevo
        else:
            if _ESCAPE_NUMERICO_RE.sub(_numerico, texto) != texto:
                raise _DecodificacionInestable()
    return texto.translate(_SIN_SINTAXIS)


_SIN_SINTAXIS = {ord(c): None for c in "'\"\\$"}


_OPACA_ESCAPES = (f"orden con lectura opaca bloqueada (los escapes numéricos `\\xHH`/`\\u`/`\\U`/octal se anidan a más de {_RONDAS_ESCAPES} "
                  "niveles): el guardarraíl no puede saber qué texto forman y, ante la duda, no la da por inocua — escríbela sin codificar "
                  "caracteres dentro de otros escapes.")


_ANSI_ESC_RE = re.compile(_ESCAPE_NUMERICO_RE.pattern + r"|\\(.)", re.S)


def _ansi_esc(m):
    return _ANSI_SIMPLES.get(m.group(6), m.group(6)) if m.group(6) is not None else _numerico(m)


_VISTA_RE = re.compile(r"\$'((?:[^'\\]|\\.)*)'|\\(.)|['\"]", re.S)


def _vista_de_shell(texto):
    """Una pasada GENEROSA de bash sobre `texto`, de izquierda a derecha y sin distinguir donde empiezan y acaban las comillas: `$'…'` se decodifica
    (escapes numericos y simples) y su resultado NO se vuelve a leer en la misma pasada, `\\X` pasa a `X` y las comillas se descartan. Un git que solo se
    forma al concatenar trozos entrecomillados (`\\$\\'$'\\x5c'x67it\\'` -> `$'\\x67it'`, que `eval`/`bash -c` vuelve a leer) aparece en la pasada
    siguiente (fix16, gap 3)."""
    def sustituye(m):
        if m.group(1) is not None:
            return _ANSI_ESC_RE.sub(_ansi_esc, m.group(1))
        return m.group(2) if m.group(2) is not None else ""
    return _VISTA_RE.sub(sustituye, texto)


def _git_en_vistas_de_shell(command):
    """¿Aparece git en alguna de las pasadas de `_vista_de_shell` (hasta `_RONDAS_ESCAPES`)? Lanza `_DecodificacionInestable` si aun cambia tras el tope."""
    if "\\" not in command and "$'" not in command:
        return False
    texto = command
    for _ in range(_RONDAS_ESCAPES):
        nuevo = _vista_de_shell(texto)
        if _GIT_TEXTO_RE.search(nuevo):
            return True
        if nuevo == texto:
            return False
        texto = nuevo
    if _vista_de_shell(texto) != texto:
        raise _DecodificacionInestable()
    return False


def _contiene_git(command, segmentos):
    """¿Aparece git (sin distinguir mayúsculas) en el texto crudo, en alguna palabra YA DECODIFICADA (sin comillas, sin `$'…'`,
    con los escapes aplicados) o en el texto aplanado (`_aplanado`)? Una lectura incompleta no puede fiarse del texto crudo:
    `\\x67it`, `g''it` o `GIT` no lo traen como `git` (fix14, gap 1). Solo se llama con una lectura incompleta o con un CR."""
    return (bool(_GIT_TEXTO_RE.search(command)) or any(_GIT_TEXTO_RE.search(t) or ("\\" in t and _GIT_TEXTO_RE.search(_aplanado(t)))
                                                      for s in segmentos for t in s)
            or bool(_GIT_TEXTO_RE.search(_aplanado(command))) or _git_en_vistas_de_shell(command))


# fix16 (punto 1) y fix17 (punto 1): criterio por CLASE. Una palabra de la orden simple (decodificada, sin distinguir mayusculas, nombre base, con `.exe`) que sea git, un
# envoltorio de la tabla, una shell o `eval`/`trap` abre un sufijo que `_analiza_segmento` analiza como una orden nueva y completa. Vale aunque el programa de delante no este en
# la tabla (`chroot / git …`, `strace bash -c …`, `uv run env -S …`) y aunque la tabla se equivoque con sus opciones. Coste declarado: un `echo git reset --hard` sin comillas se
# deniega (falso deny aceptado).
_MAX_SUFIJOS_GIT = 32
_ANCLAS = frozenset({"git", "eval", "trap"} | _ENVOLTORIOS | _SHELLS)


def _anclas(toks):
    """Sufijos de `toks` que empiezan en una palabra de `_ANCLAS` (a partir de la segunda palabra). `None` si hay mas de `_MAX_SUFIJOS_GIT`."""
    sufijos = []
    for k in range(1, len(toks)):
        if _program_name(toks[k]) in _ANCLAS:
            if len(sufijos) >= _MAX_SUFIJOS_GIT:
                return None
            sufijos.append(toks[k:])
    return sufijos


# fix17 (punto 1): lo que git pasa a una shell. `{subcomando: (cortas con valor que se ejecuta, largas con valor que se ejecuta)}`. `submodule foreach` y `bisect run` llevan el
# codigo como argumentos (git los une con espacios y los ejecuta con `sh -c`). Un alias `!…` llega por `-c alias.x=!…`/`git config alias.x`, que la lista blanca de configuracion ya deniega.
_CODIGO_EN_GIT = {
    "rebase": ("x", ("--exec",)), "fetch": ("", ("--upload-pack",)), "pull": ("", ("--upload-pack",)), "push": ("", ("--receive-pack", "--exec")),
    "clone": ("u", ("--upload-pack",)), "ls-remote": ("", ("--upload-pack", "--exec")),
    "filter-branch": ("", ("--tree-filter", "--index-filter", "--env-filter", "--msg-filter", "--commit-filter", "--parent-filter", "--tag-name-filter", "--setup")),
    # fix18 (gap 7): el resto de opciones de git cuyo valor ejecuta una shell (el valor se analiza como codigo, como el de `rebase -x`: `difftool -x 'diff -u'` sigue permitido)
    "difftool": ("x", ("--extcmd",)), "grep": ("O", ("--open-files-in-pager",)), "archive": ("", ("--exec",)),
    "fetch-pack": ("", ("--upload-pack", "--exec")), "send-pack": ("", ("--receive-pack", "--exec")), "instaweb": ("", ("--httpd",)),
}
_CORTAS_SOLO_PEGADAS = {"grep": "O"}      # `git grep -O[<pager>]`: el valor es OPCIONAL y solo va pegado (`git grep -O v1` no lo consume)


def _codigo_de_git(toks):
    """Cadenas que git ejecutaria como codigo de shell en la invocacion `toks` (`toks[0]` es git)."""
    i, _hooks = _git_invocation(toks)
    if i < 0:
        return []
    sub, args = toks[i], toks[i + 1:]
    codigos = []
    if sub in ("submodule", "submodule--helper"):
        k = next((j for j, t in enumerate(args) if not t.startswith("-")), None)
        if k is not None and args[k] == "foreach":
            resto = args[k + 1:]
            while resto and resto[0].startswith("-"):
                resto = resto[1:]
            if resto:
                codigos.append(" ".join(resto))
    elif sub == "bisect":
        if args and args[0] == "run" and len(args) > 1:
            codigos.append(" ".join(args[1:]))
    elif sub in _CODIGO_EN_GIT:
        cortas, largas = _CODIGO_EN_GIT[sub]
        k = 0
        while k < len(args):
            t = args[k]
            if t == "--":
                break
            if t.startswith("--"):
                if _prefijo(t, *largas):
                    if "=" in t:
                        codigos.append(t.split("=", 1)[1])
                    elif k + 1 < len(args):
                        codigos.append(args[k + 1])
                        k += 1
            elif t.startswith("-") and len(t) > 1 and cortas:
                for m, letra in enumerate(t[1:], 1):
                    if letra in cortas:
                        valor = t[m + 1:]
                        if not valor and k + 1 < len(args) and letra not in _CORTAS_SOLO_PEGADAS.get(sub, ""):
                            valor = args[k + 1]
                            k += 1
                        if valor:
                            codigos.append(valor)
                        break
            k += 1
    return codigos


_CHECKOUT_LARGAS_SIN_VALOR = ("--force", "--quiet", "--merge", "--no-track", "--guess", "--no-guess", "--overlay",
                              "--no-overlay", "--progress", "--no-progress", "--ignore-skip-worktree-bits", "--discard-changes", "--no-recurse-submodules",
                              "--recurse-submodules", "--ignore-other-worktrees", "--no-detach", "--dwim")


def _analiza_cambio_rama(rest):
    """`(posicionales, ¿crea una rama con nombre?, nombre que `-B`/`-C`/`--force-create` crea o reinicia | None, ¿suelta HEAD?, ¿opcion larga con valor separado posible?,
    ¿sigue una remota (`-t`/`--track`)?, ¿es de ficheros (`-p`/`--patch`/`--ours`/`--theirs`)?)` de los argumentos de `git checkout|switch`. Lee clusters (`-fBmain`), valores
    pegados (`-Bmain`, `--force-create=main`) y abreviaturas de las largas (fix16, gaps 2, 8 y 14; fix17: `-t` sin nombre y las opciones que solo valen con ficheros)."""
    pos, crea, reinicia, suelta, separado, sigue, ficheros = [], False, None, False, False, False, False
    i, n = 0, len(rest)
    while i < n:
        t = rest[i]
        if t == "--":
            i += 1
        elif t.startswith("--"):
            base, igual, valor = t.partition("=")
            if len(base) >= 9 and "--force-create".startswith(base):
                reinicia = valor if igual else (rest[i + 1] if i + 1 < n else "")
                i += 1 if igual else 2
            elif len(base) >= 4 and ("--create".startswith(base) or "--orphan".startswith(base)):
                crea = True
                i += 1 if igual else 2
            else:
                if _prefijo(t, "--detach"):
                    suelta = True
                elif _prefijo(t, "--track"):
                    sigue = True
                elif any(len(base) >= 3 and lg.startswith(base) for lg in ("--patch", "--ours", "--theirs")):
                    ficheros = True
                elif not igual and not any(base == lg or (len(base) >= 3 and lg.startswith(base)) for lg in _CHECKOUT_LARGAS_SIN_VALOR):
                    separado = True            # `--conflict merge main`: puede llevarse la palabra siguiente como valor, no se sabe cual es el destino
                i += 1
        elif t.startswith("-") and len(t) > 1:
            consumido = 1
            for k, letra in enumerate(t[1:], 1):
                if letra in "bcBC":
                    valor = t[k + 1:]
                    if not valor:
                        valor = rest[i + 1] if i + 1 < n else ""
                        consumido = 2
                    if letra in "BC":
                        reinicia = valor
                    else:
                        crea = True
                    break
                if letra == "d":
                    suelta = True
                elif letra == "t":
                    sigue = True
                elif letra == "p":
                    ficheros = True
            i += consumido
        else:
            pos.append(t)
            i += 1
    return pos, crea, reinicia, suelta, separado, sigue, ficheros


_CTX = {"cwd": None}        # fix18 (gap 1): el `cwd` del payload (lo fija `decide`); sin el, el del proceso


def _cwd():
    return _CTX["cwd"] or os.getcwd()


def _ruta_existente(token):
    """¿Existe la ruta `token`? Se resuelve contra el `cwd` del payload (fix18), no contra el del proceso del guard."""
    try:
        return os.path.lexists(os.path.join(_cwd(), token))
    except (OSError, ValueError):
        return False


_PSEUDO_REF_RE = re.compile(r"[A-Z][A-Z_]*")
_MAX_PACKED = 8 * 1024 * 1024


def _ref_existe(nombre):
    """¿`nombre` resuelve como ref (rama local, remota, tag, pseudo-ref como `FETCH_HEAD`, o una expresion `x~1`/`x^`/`@{u}`)? Lectura barata de `.git/refs` + `packed-refs`, sin lanzar git
    (fix18, gap 1). True/False; None si no es concluyente (sin repositorio legible o reftable)."""
    if not nombre or nombre.startswith("-"):
        return False
    if re.search(r"[~^]|@\{", nombre) or nombre == "@":
        return True
    gitdir = _gitdir_de(_cwd())
    if gitdir is None or not _es_repositorio(gitdir):
        return None
    comun = _commondir(gitdir)
    comun = gitdir if comun is None else comun
    if comun is False or os.path.isdir(os.path.join(comun, "reftable")):
        return None
    candidatos = ["refs/" + nombre, "refs/tags/" + nombre, "refs/heads/" + nombre, "refs/remotes/" + nombre, "refs/remotes/" + nombre + "/HEAD"]
    if nombre.startswith("refs/"):
        candidatos.append(nombre)
    try:
        if _PSEUDO_REF_RE.fullmatch(nombre) and os.path.isfile(os.path.join(gitdir, nombre)):
            return True
        for c in candidatos:
            if os.path.isfile(os.path.join(comun, *c.split("/"))):
                return True
        empaquetado = os.path.join(comun, "packed-refs")
        if os.path.isfile(empaquetado):
            if os.path.getsize(empaquetado) > _MAX_PACKED:
                return None
            with open(empaquetado, "rb") as fh:
                for linea in fh.read().decode("utf-8", "replace").splitlines():
                    if linea[:1] in ("#", "^"):
                        continue
                    _sha, _sep, ref = linea.partition(" ")
                    if ref in candidatos:
                        return True
    except (OSError, ValueError):
        return None
    return False


def _razon_cambio_rama(sub, rest, branch):
    """`git checkout|switch` que saca de la rama de trabajo o la reinicia. fix17 (punto 2): LISTA BLANCA. Con una posicional solo se permite la rama actual, `HEAD` (en `checkout`: es un
    no-op que conserva la rama) y, en `checkout`, una ruta que existe; cualquier otra ref (otra rama, un tag, `FETCH_HEAD`, `fork/main`, un SHA corto, `-`, `@{u}`) se deniega, porque
    no se puede saber sintacticamente si suelta HEAD. `-B`/`-C`/`--force-create` solo valen sobre la rama actual y sin punto de partida (en otro caso reinician otra rama o la actual a otro
    punto); `-t`/`--track` sin nombre crea una rama local con el nombre de la remota. `checkout <ref> <ruta>…` restaura ficheros y `-p`/`--ours`/`--theirs` solo valen con ficheros.
    Con la rama DESCONOCIDA se deniega lo que no sea inocuo."""
    if "--" in rest:
        k = rest.index("--")
        antes, despues = rest[:k], rest[k + 1:]
        if sub == "checkout" and despues:
            return None                       # `git checkout main -- fichero` restaura ficheros, no cambia de rama
        rest = antes + despues
    desconocida = branch is None
    en_trabajo = branch is not None and branch not in MAIN_BRANCHES and branch != "HEAD"
    if not (en_trabajo or desconocida):
        return None
    pos, crea, reinicia, suelta, separado, sigue, ficheros = _analiza_cambio_rama(rest)
    donde = f"estás en la rama de trabajo «{branch}»" if en_trabajo else "no se puede saber la rama actual (¿sin repositorio o con HEAD ilegible?) y el guardarraíl falla cerrado"
    cierre = "la integración la dirige /dev-cycle (Fase 6); para otra rama de trabajo, que la abra el usuario o crea una nueva con `git switch -c`."
    if reinicia is not None:
        if en_trabajo and reinicia == branch and not pos:
            return None                       # `-B <la actual>` sin punto de partida es un no-op
        return (f"`git {sub} -B|-C {reinicia}` bloqueado: {donde}, y `-B`/`-C`/`--force-create` solo valen sobre la rama actual y sin punto de partida (en otro caso reinicia otra "
                f"rama o esta a otro punto: equivale a `git branch -f`/`git reset --keep`) — {cierre}")
    if ficheros and sub == "checkout":
        return None                           # `-p`, `--ours` y `--theirs` de `checkout` operan sobre ficheros, no cambian de rama (`switch` no tiene `-p`)
    if suelta:
        return f"`git {sub} --detach` bloqueado: {donde} y el implementer no suelta HEAD — {cierre}"
    if crea:
        return None
    if sigue and pos and _es_rama_principal(pos[-1].rsplit("/", 1)[-1]):
        return (f"`git {sub} --track {pos[-1]}` bloqueado: {donde} y `--track` sin nombre crea la rama local `{pos[-1].rsplit('/', 1)[-1]}` y cambia a ella — {cierre}")
    if sub == "checkout" and len(pos) >= 2 and not separado:
        return None                           # `git checkout <ref> <ruta>…`: restaura ficheros desde <ref>, no cambia de rama (`_razon_restauracion` ya los valido)
    for p in pos:
        if p == branch or (sub == "checkout" and p == "HEAD"):
            continue
        # fix18 (gap 1): una ref gana a una ruta homonima (git `checkout main` con un directorio `main` CAMBIA de rama) y delante de `--` sigue siendo una ref.
        # fix24 (lista blanca): fuera de la rama actual y de HEAD, una ruta solo vale detras de `--` (se devolvio None mas arriba); sin `--` el nombre puede ser una rama, un tag, `-`, un SHA o una
        # remota que git crea (DWIM) aunque haya un fichero o directorio con ese nombre, y el guardarrail no lo resuelve.
        return (f"`git {sub} {p}` bloqueado: {donde} y `{p}` no es la rama actual; solo se permite cambiar a la rama actual, `HEAD` o restaurar rutas DETRAS de `--` (`git checkout -- {p}`): sin `--` el "
                f"nombre puede ser una rama, un tag, `-`, un SHA o una remota (git la crea) aunque exista una ruta con ese nombre — {cierre}")
    return None


def _razon_rebase_bisect(toks):
    """`git rebase <upstream> <rama>` cambia a la rama y la reescribe; `git bisect start|reset <ref>` suelta HEAD en un commit (fix17, gap 16)."""
    i = _es_git(toks, "rebase")
    if i >= 0:
        args, pos, k, raiz = toks[i + 1:], [], 0, False
        con_valor_corta = "sxXC"                      # fix18 (gap 6): `-S` (`--gpg-sign`) lleva el valor OPCIONAL y solo pegado: no se come la palabra siguiente
        largas_con_valor = ("--onto", "--strategy", "--strategy-option", "--exec", "--whitespace", "--empty", "--trailer")
        while k < len(args):
            t = args[k]
            if t == "--":
                pos += args[k + 1:]
                break
            if t.startswith("--"):
                base, igual, _v = t.partition("=")
                if _prefijo(t, "--root"):
                    raiz = True
                elif not igual and base in largas_con_valor:
                    k += 1
            elif t.startswith("-") and len(t) > 1:
                letras = t[1:]
                for m, letra in enumerate(letras):
                    if letra in con_valor_corta:
                        if m == len(letras) - 1:
                            k += 1
                        break
            else:
                pos.append(t)
            k += 1
        if len(pos) >= 2 or (raiz and pos):
            return (f"`git rebase {' '.join(pos)}` bloqueado: con una rama como último argumento `rebase` cambia a esa rama y la reescribe — rebasa la actual con "
                    "`git rebase <upstream>`; la integración la dirige /dev-cycle (Fase 6).")
    i = _es_git(toks, "bisect")
    if i >= 0 and i + 1 < len(toks) and toks[i + 1] not in ("log", "visualize", "view", "help"):
        # fix18 (gap 6): `start` a secas seguido de `good|bad <ref>` suelta HEAD (el mensaje de fix17 recomendaba justo ese camino): cualquier subcomando que no sea de lectura se deniega.
        return (f"`git bisect {toks[i + 1]}` bloqueado: la bisección suelta HEAD en un commit y la rama de trabajo deja de ser la actual — que la haga el usuario (`git bisect log|visualize` sí se permiten).")
    return None


def _razon_cabeza(toks):
    """`git symbolic-ref HEAD <ref>` y `git update-ref HEAD <sha>` mueven HEAD sin pasar por checkout/switch (fix16, gap 14); `git update-ref refs/heads/<rama> <ref>` mueve una rama
    (la actual o la principal) sin pasar por `branch` (fix17, gap 15)."""
    for sub in ("symbolic-ref", "update-ref"):
        i = _es_git(toks, sub)
        if i < 0:
            continue
        args, k, borra = [], i + 1, False
        while k < len(toks):
            t = toks[k]
            if t == "-m":
                k += 2
                continue
            if t == "--":
                k += 1
                continue
            if t in ("-d", "--delete"):
                borra = True
            elif not t.startswith("-"):
                args.append(t)
            k += 1
        if args and args[0].upper() == "HEAD" and (sub == "update-ref" or borra or len(args) >= 2):
            return (f"`git {sub} HEAD …` bloqueado: mueve HEAD (de rama o de commit) sin pasar por `checkout`/`switch`, y el implementer no sale de "
                    "su rama de trabajo — la integración la dirige /dev-cycle (Fase 6).")
        if sub == "update-ref" and args and args[0].startswith("refs/heads/"):
            return (f"`git update-ref {args[0]} …` bloqueado: mueve una rama (la actual o la principal) sin pasar por `branch` y le quita sus commits — "
                    "la integración la dirige /dev-cycle (Fase 6).")
    return None


_MOVEDORES_DE_HISTORIA = frozenset(("merge", "pull", "rebase", "cherry-pick", "revert", "am", "commit", "reset"))


_C_IRRESOLUBLE = "<-C irresoluble>"      # fix24 (gap 5): hay un `-C` cuyo destino no se puede conocer sin ejecutar la shell


_ORDEN_RAW = ""     # fix25: texto de la orden que se esta analizando (lo fija `_check_git` justo antes de `_razon_git`)


def _fijar_orden_raw(texto):
    global _ORDEN_RAW
    _ORDEN_RAW = texto


def _comilla_de(v):
    """fix25 (gap 4): la comilla (`'` o `"`) que rodea la palabra `v` en la orden analizada, o "" si va sin comillas. El tokenizado las quita; la shell, no: `'~/m'` y `'$PWD'` no se expanden."""
    m = re.search(r"(['\"])" + re.escape(v) + r"\1", _ORDEN_RAW)
    return m.group(1) if m else ""


def _expande_C(v):
    """fix24 (gap 5): el destino de un `-C` con las formas que el guard SI puede resolver: `$PWD`/`${PWD}` (el `cwd` del payload), `~`/`~/...` y `$HOME`/`${HOME}` (el HOME del entorno), la ruta
    de Git Bash `/c/...` (Windows) y las rutas cortas 8.3 (las expande `realpath`). None si queda algo que solo la shell sabe resolver (`$VAR`, `$(...)`, backticks, globs, `~usuario`).
    fix25 (gap 4): como la shell, no expande dentro de comillas simples y entre dobles solo `$PWD`/`$HOME` (nunca `~`)."""
    comilla = _comilla_de(v)
    inicio = os.path.expanduser("~")
    if not comilla and (v == "~" or v.startswith(("~/", "~\\"))):
        v = inicio + v[1:]
    if comilla != "'":
        v = re.sub(r"\$\{?PWD\}?(?![A-Za-z0-9_])", lambda m: _cwd().replace("\\", "/"), v)
        v = re.sub(r"\$\{?HOME\}?(?![A-Za-z0-9_])", lambda m: inicio.replace("\\", "/"), v)
    if re.search(r"[$`*?\[]", v) or v.startswith("~"):
        return None
    if os.name == "nt":
        m = re.match(r"^/(?:cygdrive/)?([A-Za-z])(?:/(.*))?$", v)
        if m:
            v = m.group(1).upper() + ":/" + (m.group(2) or "")
    return v


def _directorios_C(toks):
    """Directorio al que apuntan los `-C <ruta>` de la invocacion git `toks` (cada `-C` es relativo al anterior): None si no hay `-C`; `_C_IRRESOLUBLE` si alguno no se puede resolver."""
    ruta = None
    i = 1
    while i < len(toks) and toks[i].startswith("-"):
        o = toks[i]
        if o == "-C" and i + 1 < len(toks):
            v = _expande_C(toks[i + 1])
            if v is None:
                return _C_IRRESOLUBLE
            ruta = v if ruta is None else os.path.join(ruta, v)
        if o in _GIT_GLOBAL_VALUES:
            i += 2
        else:
            i += 1
    if ruta is None:
        return None
    ruta = os.path.normpath(ruta if os.path.isabs(ruta) else os.path.join(_cwd(), ruta))
    try:
        return os.path.realpath(ruta) if os.path.exists(ruta) else ruta
    except (OSError, ValueError):
        return ruta


def _refspec_mueve_rama(destino):
    """¿El destino de un refspec es una rama local (`main`, `refs/heads/x`, `refs/heads/*`)? Los `refs/tags/`, `refs/remotes/` y demas no cuentan."""
    d = destino.lstrip("+")
    if not d or d.startswith(("refs/remotes/", "refs/tags/", "refs/notes/", "refs/stash", "refs/pull/")):
        return False
    return d.startswith("refs/heads/") or not d.startswith("refs/")


def _razon_refs(toks, i):
    """fix18 (gap 6): `fetch`/`pull`/`push` cuyo refspec mueve una rama local a la fuerza o desde el propio repositorio (`.`), `push <remoto> <src>:<rama principal>`, `worktree add -B`,
    `filter-branch` y `filter-repo` (reescriben o mueven `refs/heads/*` sin pasar por `branch`/`update-ref`)."""
    sub, args = toks[i], toks[i + 1:]
    if sub in ("filter-branch", "filter-repo"):
        return (f"`git {sub}` bloqueado: reescribe la historia de las ramas (`refs/heads/*`) — la limpieza del historial la decide el usuario.")
    if sub == "worktree" and args and args[0] == "add" and any(_cluster(t, "B") or (t.startswith("-B") and not t.startswith("--")) for t in args[1:]):
        return ("`git worktree add -B` bloqueado: reinicia una rama existente (equivale a `git branch -f`) — usa `-b` para una rama nueva (la integración la dirige /dev-cycle, Fase 6).")
    if sub in ("fetch", "pull", "push"):
        opciones = [t for t in args if t.startswith("-") and t != "--"]
        posicionales = [t for t in args if not t.startswith("-")]
        refspecs = [t for t in posicionales if ":" in t and "://" not in t and not re.match(r"^[A-Za-z]:[\\/]", t) and "@" not in t.split(":", 1)[0]]
        local = "." in posicionales[:1] or (sub != "push" and "." in posicionales)
        fuerza = any(_cluster(t, "f") or _prefijo(t, "--force") for t in opciones) or any(r.startswith("+") for r in refspecs)
        for r in refspecs:
            destino = r.rsplit(":", 1)[1]
            if sub == "push":
                if _refspec_mueve_rama(destino) and (local or _es_rama_principal(destino.lstrip("+").removeprefix("refs/heads/"))):
                    return (f"`git push … {r}` bloqueado: {'mueve una rama de este mismo repositorio' if local else 'integra en la rama principal'} sin pasar por `branch` ni la integración "
                            "que dirige /dev-cycle (Fase 6) — empuja tu rama (`git push -u origin <rama>`).")
            elif _refspec_mueve_rama(destino) and (local or fuerza):
                return (f"`git {sub} … {r}` bloqueado: con `+`/`--force` o desde `.` mueve una rama local (la actual o la principal) como `git branch -f` — haz `git {sub}` normal "
                        "o deja la integración al ritual de cierre de /dev-cycle (Fase 6).")
    return None


def _razon_destruye(toks, i):
    """fix18 (gaps 2 y 9): subcomandos que destruyen trabajo o la recuperacion que el guard protege al denegar `branch -D` y `stash drop`."""
    sub, args = toks[i], toks[i + 1:]
    if sub == "clone":
        # fix18: `git clone -c|--config <clave>=<valor>` fija la configuracion del clon NUEVO (`core.hooksPath`, `core.sshCommand`…): misma lista blanca que `-c` global
        k = 0
        while k < len(args):
            t, valor = args[k], None
            if t in ("-c", "--config") and k + 1 < len(args):
                valor, k = args[k + 1], k + 1
            elif t.startswith("--config="):
                valor = t.split("=", 1)[1]
            elif t.startswith("-c") and not t.startswith("--") and len(t) > 2:
                valor = t[2:]
            if valor is not None and not _config_permitida(valor.split("=", 1)[0], valor.split("=", 1)[1] if "=" in valor else None):
                return (f"`git clone --config {valor.split('=', 1)[0]}` bloqueado: esa clave puede ejecutar una orden o saltar hooks en el clon (lista blanca de configuración: "
                        "`user.name`, `user.email`, `core.quotepath`, `commit.gpgsign`, `init.defaultBranch`, `color.*`, `advice.*`).")
            k += 1
    if sub in ("submodule", "submodule--helper"):
        k = next((j for j, t in enumerate(args) if not t.startswith("-")), None)
        if k is not None and args[k] in ("update", "deinit") and any(_cluster(t, "f") or _prefijo(t, "--force") for t in args):
            return (f"`git submodule {args[k]} --force` bloqueado: descarta los cambios sin comitear de los submódulos — usa `git submodule update` sin `--force` o revierte solo lo tuyo.")
    elif sub == "gc":
        for t in args:
            if t.startswith("--prune=") and t.split("=", 1)[1] in ("now", "all"):
                return ("`git gc --prune=now|all` bloqueado: borra al instante los objetos sin referencia y con ellos la recuperación de lo que `branch -D`/`stash drop` dejarían — "
                        "usa `git gc` a secas (conserva 2 semanas).")
    elif sub == "prune":
        if not any(_cluster(t, "n") or _prefijo(t, "--dry-run") for t in args):
            return ("`git prune` bloqueado: borra objetos sin referencia sin periodo de gracia — que lo haga el usuario.")
    elif sub == "reflog" and args and args[0] in ("expire", "delete"):
        if not any(_cluster(t, "n") or _prefijo(t, "--dry-run") for t in args[1:]):
            return (f"`git reflog {args[0]}` bloqueado: borra el reflog, la recuperación de las ramas y los commits — que lo haga el usuario (`--dry-run` sí se permite).")
    return None


def _razon_git(toks, branch, base_cambiada):
    """Reglas de git para UNA invocacion (`toks[0]` es git): commit, push, reset, clean, stash, branch, update-ref, checkout/switch/restore.
    fix16: antes vivian dentro de `_check_git` y solo corrian con git como programa de la orden simple; ahora tambien sobre cada sufijo que
    empieza en una palabra `git` (`_sufijos_git`)."""
    i, hooks_override = _git_invocation(toks)
    if i >= 0 and toks[i] == "commit":
        if hooks_override:
            return ("`git commit` con override de core.hooksPath bloqueado: conserva los hooks "
                    "de verificación del proyecto; un cambio de ruta requiere revisión explícita.")
        if _commit_skips_verification(toks[i + 1:]):
            return ("`git commit` sin verificación bloqueado: conserva pre-commit y commit-msg; "
                    "corrige el fallo de los hooks en vez de omitirlos con --no-verify/-n.")
    i, _hooks = _git_invocation(toks)
    if i >= 0:
        # fix18 (gap 6): `-C <dir>`: el HEAD que cuenta es el del directorio. Con HEAD en la rama principal, lo que mueve su historia es integrar; con otra rama de trabajo, el resto de reglas
        # se aplican con ESA rama (un worktree de otra tarea).
        destino_C = _directorios_C(toks)
        if destino_C == _C_IRRESOLUBLE and toks[i] not in _SUB_LECTURA:
            return (f"`git -C <ruta que depende de la shell> {toks[i]}` bloqueado: el destino de `-C` no se puede resolver aquí (`$VAR`, `$(…)`, globs, `~usuario`) y `{toks[i]}` escribe; "
                    "si fuera un worktree con HEAD en la rama principal sería integrar — usa una ruta literal, `$PWD/…` o `~/…` (con `-C` sin resolver solo valen los subcomandos de lectura: "
                    + ", ".join(sorted(_SUB_LECTURA)[:8]) + "…).")
        if destino_C not in (None, _C_IRRESOLUBLE) and os.path.isdir(destino_C):
            rama_C = rama_barata(destino_C)
            if rama_C in MAIN_BRANCHES and toks[i] not in _SUB_LECTURA:
                return (f"`git -C {toks[i - 1] if i else ''} {toks[i]}` bloqueado: ese directorio tiene HEAD en la rama principal «{rama_C}» y `{toks[i]}` escribe en él (mueve su historia, sus ramas o su remoto) — "
                        "con `-C` hacia la rama principal solo valen los subcomandos de lectura; la integración la dirige /dev-cycle (Fase 6).")
            if rama_C is not None:
                branch = rama_C
        razon = _razon_refs(toks, i) or _razon_destruye(toks, i)
        if razon:
            return razon
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
    if i >= 0 and any(_prefijo(t, "--hard", "--keep", "--merge") for t in toks[i + 1:]):
        return ("`git reset --hard|--keep|--merge` bloqueado: reescribe el árbol de trabajo y puede descartar "
                "cambios sin comitear que pueden no ser tuyos — revierte solo lo de tu intento "
                "(`git diff <foto> -- <ficheros> | git apply -R`).")
    # Subcomandos que también descartan trabajo sin comitear (T-06 fix6, gap 11): `checkout-index -f` y
    # `read-tree -u|--reset` reescriben el árbol, `rm -f` borra ficheros con cambios y `worktree remove -f` un árbol entero.
    i = _es_git(toks, "checkout-index")
    if i >= 0 and any(_cluster(t, "f") or _prefijo(t, "--force") for t in toks[i + 1:]):
        return ("`git checkout-index -f` bloqueado: sobrescribe ficheros del árbol con cambios sin comitear — "
                "revierte solo lo de tu intento (`git diff <foto> -- <ficheros> | git apply -R`).")
    i = _es_git(toks, "read-tree")
    if i >= 0 and any(_cluster(t, "u") or _prefijo(t, "--reset") for t in toks[i + 1:]):
        return ("`git read-tree -u|--reset` bloqueado: reescribe el árbol de trabajo y descarta cambios sin "
                "comitear — revierte solo lo de tu intento.")
    i = _es_git(toks, "rm")
    if i >= 0 and any(_cluster(t, "f") or _prefijo(t, "--force") for t in toks[i + 1:]):
        return ("`git rm -f` bloqueado: borra ficheros aunque tengan cambios sin comitear — usa `git rm` sin "
                "`-f` o borra por nombre solo lo de tu intento.")
    i = _es_git(toks, "worktree")
    if i >= 0 and i + 1 < len(toks) and toks[i + 1] == "remove" \
            and any(_cluster(t, "f") or _prefijo(t, "--force") for t in toks[i + 2:]):
        return ("`git worktree remove --force` bloqueado: elimina un árbol de trabajo con cambios sin comitear — "
                "la limpieza de worktrees la dirige el ritual de cierre de /dev-cycle (Fase 6).")
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
            razon = _razon_restauracion(sub, toks[i + 1:], base_cambiada)
            if razon:
                return razon
            if sub == "restore":
                continue
            razon = _razon_cambio_rama(sub, toks[i + 1:], branch)
            if razon:
                return razon
    razon = _razon_cabeza(toks)
    if razon:
        return razon
    razon = _razon_rebase_bisect(toks)
    if razon:
        return razon
    return _lista_blanca(toks, branch)


# ---- fix24: LISTA BLANCA de git del implementer (decision del usuario 2026-11-20; politica unica, ADR-023). Es la ULTIMA capa de `_razon_git`: lo que las reglas anteriores dejan pasar solo es
# valido si el subcomando (y sus opciones globales) esta aqui; todo lo demas se deniega con un mensaje que dice que se permite. Cierra por CLASE lo que las lentes del intento 19 encontraron forma a forma
# (DWIM de remota, `checkout -`/SHA, `@:main`, `gc --prune=<fecha>`, `branch -m`, `fast-import`, `send-email --*-cmd`, la reversa de una biseccion...). Los envoltorios encadenados siguen siendo limite conocido.
_SUB_LECTURA = frozenset((
    "status", "diff", "log", "show", "rev-parse", "ls-files", "blame", "grep", "merge-base", "describe", "cat-file", "shortlog", "ls-tree", "rev-list", "diff-tree", "diff-files",
    "diff-index", "show-ref", "for-each-ref", "name-rev", "whatchanged", "show-branch", "count-objects", "check-ignore", "check-attr", "var", "version", "help", "annotate", "cherry", "range-diff"))
_SUB_ESCRIBE = frozenset((
    "add", "commit", "mv", "rm", "revert", "cherry-pick", "merge", "rebase", "reset", "switch", "checkout", "restore", "stash", "branch", "push", "fetch", "pull", "worktree", "apply",
    "format-patch", "clean", "notes", "tag", "bisect", "remote", "config", "reflog", "submodule"))
_GLOBALES_OK = frozenset(("-C", "-c", "--no-pager", "-P", "-p", "--paginate", "--no-optional-locks", "--no-advice", "--literal-pathspecs", "--glob-pathspecs", "--noglob-pathspecs",
                          "--icase-pathspecs", "--no-replace-objects", "--no-lazy-fetch"))
_PUSH_OPCIONES = frozenset(("-u", "--set-upstream", "-q", "--quiet", "-v", "--verbose", "-n", "--dry-run", "--follow-tags", "--tags", "--progress", "--no-progress"))
_TAG_CON_VALOR = ("--contains", "--no-contains", "--points-at", "--merged", "--no-merged", "--sort", "--format", "--column")
_TAG_ESCRIBE = ("--delete", "--force", "--annotate", "--sign", "--local-user", "--message", "--file", "--edit")


# ---- fix25 (intento 20): LISTA BLANCA de OPCIONES por subcomando que escribe. La de fix24 filtraba subcomandos pero no sus opciones (`rebase --update-refs`, `fetch --refmap`, `fetch -u`,
# `merge|pull|rebase --no-verify`...). Cada subcomando acepta SOLO las opciones conocidas e inocuas de aqui (`--x=v` y `--x v`, cortas agrupadas como `-am`); cualquier otra se deniega
# diciendo cuales se aceptan, lo que cierra por clase tambien las opciones que git anada en el futuro. Los subcomandos de lectura, `tag`, `notes`, `remote`, `reflog`, `bisect`, `config`,
# `clean`, `submodule`, `format-patch` y `push` conservan sus reglas semanticas propias (ninguna de sus opciones mueve una rama).
def _spec(sin="", con="", pegado="", largas="", valor=""):
    """(cortas sin valor, cortas con valor en la palabra siguiente o pegado, cortas con valor solo pegado, largas sin valor, largas con valor)."""
    return (sin, con, pegado, frozenset(largas.split()), frozenset(valor.split()))


_FETCH_LARGAS = ("quiet verbose all append prune prune-tags tags no-tags dry-run unshallow progress no-progress multiple atomic no-show-forced-updates show-forced-updates write-fetch-head "
                 "no-write-fetch-head recurse-submodules no-recurse-submodules ipv4 ipv6 auto-gc no-auto-gc porcelain")
_FETCH_VALOR = "depth deepen jobs shallow-since shallow-exclude"
_MERGE_LARGAS = ("no-edit edit ff no-ff ff-only squash no-squash commit no-commit abort continue quit quiet verbose stat no-stat log no-log signoff no-signoff allow-unrelated-histories "
                 "verify-signatures no-verify-signatures no-gpg-sign gpg-sign autostash no-autostash progress no-progress rerere-autoupdate no-rerere-autoupdate overwrite-ignore "
                 "no-overwrite-ignore summary no-summary")
_OPCIONES = {
    "add": _spec("AuvnNiepf", "", "", "all update verbose dry-run intent-to-add ignore-errors refresh patch interactive edit renormalize sparse ignore-removal no-ignore-removal "
                 "no-warn-embedded-repo ignore-missing force pathspec-file-nul", "chmod pathspec-from-file"),
    "commit": _spec("asqveoi", "mFCct", "Su", "all amend no-edit edit signoff no-signoff quiet verbose allow-empty allow-empty-message only include dry-run short branch porcelain long null status "
                    "no-status reset-author no-gpg-sign gpg-sign no-post-rewrite interactive patch untracked-files pathspec-file-nul",
                    "message file author date cleanup fixup squash trailer reuse-message reedit-message template pathspec-from-file"),
    "merge": _spec("eqv", "mXF", "S", _MERGE_LARGAS, "message file strategy-option cleanup"),
    "rebase": _spec("imqvfr", "xX", "SC", "continue abort skip quit interactive autosquash no-autosquash autostash no-autostash quiet verbose stat no-stat gpg-sign no-gpg-sign keep-empty "
                    "no-keep-empty root merge rebase-merges fork-point no-fork-point reapply-cherry-picks no-reapply-cherry-picks force-rebase committer-date-is-author-date ignore-date "
                    "reset-author-date signoff edit-todo show-current-patch no-ff keep-base no-update-refs apply rerere-autoupdate no-rerere-autoupdate",
                    "onto strategy-option exec whitespace empty trailer"),
    "fetch": _spec("qvapntP", "j", "", _FETCH_LARGAS, _FETCH_VALOR),
    "pull": _spec("qvapntPer", "jX", "S", _FETCH_LARGAS + " rebase no-rebase " + _MERGE_LARGAS, _FETCH_VALOR + " strategy-option"),
    "branch": _spec("arvlqtid", "u", "", "all remotes verbose list quiet show-current delete track no-track color no-color column no-column ignore-case omit-empty unset-upstream",
                    "contains no-contains merged no-merged points-at sort format abbrev set-upstream-to"),
    "stash": _spec("ukaqpS", "m", "", "include-untracked all keep-index no-keep-index quiet patch staged index stat oneline name-only name-status no-color color patch-with-stat raw shortstat "
                   "numstat summary only-untracked", "message pathspec-from-file"),
    "reset": _spec("qpN", "", "", "soft mixed quiet patch refresh no-refresh intent-to-add pathspec-file-nul", "pathspec-from-file"),
    "cherry-pick": _spec("nexs", "mX", "S", "no-commit edit no-edit signoff continue abort skip quit ff allow-empty allow-empty-message keep-redundant-commits no-gpg-sign gpg-sign "
                         "rerere-autoupdate no-rerere-autoupdate", "mainline strategy-option empty"),
    "revert": _spec("nes", "mX", "S", "no-commit edit no-edit signoff continue abort skip quit no-gpg-sign gpg-sign rerere-autoupdate no-rerere-autoupdate", "mainline strategy-option"),
    "switch": _spec("qtm", "cC", "", "quiet track no-track guess no-guess progress no-progress merge recurse-submodules", "create force-create orphan"),
    "checkout": _spec("qtmp", "bB", "", "quiet track no-track guess no-guess progress no-progress merge ours theirs patch recurse-submodules no-recurse-submodules overlay no-overlay "
                      "pathspec-file-nul", "conflict pathspec-from-file force-create orphan"),
    "restore": _spec("SWqpm", "s", "", "staged worktree quiet patch ours theirs merge ignore-unmerged overlay no-overlay progress no-progress recurse-submodules no-recurse-submodules "
                     "pathspec-file-nul", "source conflict pathspec-from-file"),
    "rm": _spec("rnq", "", "", "cached dry-run quiet ignore-unmatch sparse pathspec-file-nul", "pathspec-from-file"),
    "mv": _spec("knv", "", "", "dry-run verbose sparse"),
    "apply": _spec("vqR3z", "", "pC", "check stat numstat summary verbose quiet index cached 3way reverse ignore-whitespace ignore-space-change reject unidiff-zero apply allow-empty no-add "
                   "recount binary inaccurate-eof intent-to-add", "whitespace exclude include"),
}
_OPCIONES_WORKTREE = {
    "add": _spec("q", "b", "", "quiet no-checkout track no-track guess-remote no-guess-remote"),
    "list": _spec("vz", "", "", "verbose porcelain"),
    "prune": _spec("nv", "", "", "dry-run verbose", "expire"),
    "remove": _spec(),
}
_SUB_NUMERICAS = frozenset(("stash",))


def _razon_opciones(sub, args, spec, nombre=None):
    """Razon de deny si `args` lleva una opcion fuera de `spec` (ver `_spec`); None si todas estan en la lista blanca. Se corta en `--`."""
    sin, con, pegado, largas, valor = spec
    nombre = nombre or sub
    k = 0
    while k < len(args):
        t = args[k]
        k += 1
        if t == "--":
            break
        if t.startswith("--"):
            base, igual, _v = t[2:].partition("=")
            if base in valor:
                k += 0 if igual else 1
                continue
            if base in largas or base == "help":
                continue
        elif t.startswith("-") and len(t) > 1:
            if sub in _SUB_NUMERICAS and re.fullmatch(r"-\d+", t):
                continue
            malo = False
            for m, c in enumerate(t[1:]):
                if c in sin:
                    continue
                if c in con:
                    k += 1 if m == len(t) - 2 else 0
                    break
                if c in pegado:
                    break
                malo = True
                break
            if not malo:
                continue
        else:
            continue
        aceptadas = ", ".join(sorted("--" + x for x in (largas | valor))[:60]) + (f" y las cortas -{''.join(sorted(sin + con + pegado))}" if sin + con + pegado else "")
        return (f"`git {nombre} {t}` bloqueado: opción fuera de la lista blanca de `{nombre}` — el implementer solo usa las conocidas e inocuas, y lo que mueve ramas ajenas, salta hooks o "
                f"cambia la estrategia (`--update-refs`, `--refmap`, `-u`, `--no-verify`, `-s`…) lo hace el usuario o el ritual de cierre de /dev-cycle (Fase 6). Se aceptan: {aceptadas}.")
    return None


def _valor_de(args, cortas, largas):
    """Valor de la primera opcion de `args` entre las cortas `cortas` (`-b x`, `-bx`) o las largas `largas` (`--create x`, `--create=x`); None si no aparece."""
    for k, t in enumerate(args):
        if t == "--":
            return None
        if t in ("-" + c for c in cortas) or t in largas:
            return args[k + 1] if k + 1 < len(args) else ""
        if t.startswith("--"):
            base, igual, v = t.partition("=")
            if igual and base in largas:
                return v
        elif len(t) > 2 and t[1] in cortas and t.startswith("-") and not t.startswith("--"):
            return t[2:]
    return None


def _rama_actual_por_sustitucion():
    """fix25 (gap 6): ¿la orden analizada lleva UNA sola sustitucion `$(...)` y es exactamente `git branch --show-current` o `git rev-parse --abbrev-ref HEAD`? (la rama actual por construccion)."""
    return _ORDEN_RAW.count("$(") == 1 and len(re.findall(r"\$\(\s*git\s+(?:branch\s+--show-current|rev-parse\s+--abbrev-ref\s+HEAD)\s*\)", _ORDEN_RAW)) == 1


def _principal_o_actual(nombre, branch):
    n = nombre.removeprefix("refs/heads/")
    return _es_rama_principal(n) or (bool(branch) and n == branch)


def _lista_blanca(toks, branch):
    """Razon de deny o None para la invocacion git `toks` segun la lista blanca de subcomandos y opciones globales (ver arriba)."""
    i, _hooks = _git_invocation(toks)
    if i < 0:
        return None
    permitido = ("permitido: lectura (" + ", ".join(sorted(_SUB_LECTURA)[:12]) + "…) y, sobre tu rama de trabajo: add, commit, mv, rm (sin -f), revert, cherry-pick, merge, rebase, reset (sin --hard), "
                 "switch/checkout a la rama actual o `-b`, `checkout|restore -- <ruta>`, restore --staged, stash push|list|show|pop|apply, branch (listar o crear), push de la rama actual, fetch, "
                 "pull, worktree list|add -b|remove|prune, tag (listar), apply, format-patch, clean -n, config (claves inocuas), submodule status|update")
    k = 1
    while k < i:
        o = toks[k]
        base = o if o in _GLOBALES_OK else ("-C" if o.startswith("-C") and not o.startswith("--") else ("-c" if o.startswith("-c") and not o.startswith("--") else o))
        if base not in _GLOBALES_OK:
            return (f"opción global `{o.split('=', 1)[0]}` de git bloqueada: solo se permiten -C, -c (claves inocuas), --no-pager, -p/-P, --no-optional-locks y las --*-pathspecs "
                    "(`--git-dir`, `--work-tree`, `--exec-path`, `--bare`, `--namespace`, `--config-env`… cambian qué repositorio o qué programas usa git).")
        k += 2 if o in _GIT_GLOBAL_VALUES else 1
    sub, args = toks[i], toks[i + 1:]
    if sub not in _SUB_LECTURA and sub not in _SUB_ESCRIBE:
        return f"`git {sub}` bloqueado por la lista blanca de git del implementer ({permitido}). Lo demás lo hace el usuario o el ritual de cierre de /dev-cycle (Fase 6)."
    opciones = [t for t in args if t.startswith("-") and t != "--"]
    posicionales = [t for t in args if not t.startswith("-")]
    if sub in ("merge", "cherry-pick", "pull", "rebase", "revert") and branch in MAIN_BRANCHES:
        return f"`git {sub}` bloqueado: con HEAD en la rama principal «{branch}» integraría en ella — trabaja y integra solo HACIA tu rama de trabajo (la integración la dirige /dev-cycle, Fase 6)."
    if sub in _OPCIONES:
        razon = _razon_opciones(sub, args, _OPCIONES[sub])
        if razon:
            return razon
    if sub in ("switch", "checkout"):
        creada = _valor_de(args, "bB" if sub == "checkout" else "cC", ("--create", "--force-create") if sub == "switch" else ("--force-create",))
        if creada is not None and _es_rama_principal(creada.removeprefix("refs/heads/")):
            return f"`git {sub}` bloqueado: crear una rama con el nombre de la principal («{creada}») la mueve (equivale a `branch -f`) — usa un nombre de rama de trabajo."
    if sub == "tag":
        escribe = any(_prefijo(t, *_TAG_ESCRIBE) or _cluster(t, "d") or _cluster(t, "f") or _cluster(t, "a") or _cluster(t, "s") or _cluster(t, "u") or _cluster(t, "m") or _cluster(t, "F") for t in opciones)
        lista = any(_prefijo(t, "--list", "--contains", "--no-contains", "--points-at", "--merged", "--no-merged") or _cluster(t, "l") for t in opciones)
        if escribe or (posicionales and not lista):
            return "`git tag` bloqueado: solo se permite listar (`git tag`, `-l`, `--contains`, `--points-at`…); crear, mover o borrar tags lo decide el usuario o el ritual de cierre."
    elif sub == "notes":
        if posicionales and posicionales[0] not in ("list", "show"):
            return "`git notes` bloqueado: solo se permite leer (`git notes`, `list`, `show`)."
    elif sub == "remote":
        if posicionales and posicionales[0] not in ("show", "get-url"):
            return "`git remote` bloqueado: solo se permite `git remote [-v]`, `show` y `get-url` (cambiar remotos redirige los push)."
    elif sub == "stash":
        if posicionales and posicionales[0] not in ("push", "list", "show", "pop", "apply", "save"):
            return "`git stash` bloqueado: se permiten push, list, show, pop, apply (no drop, clear, branch, create ni store)."
    elif sub == "worktree":
        if not posicionales or posicionales[0] not in ("list", "add", "remove", "prune"):
            return "`git worktree` bloqueado: se permiten list, add (con `-b <rama nueva>`), remove (sin --force) y prune."
        accion = posicionales[0]
        k = args.index(accion)
        razon = _razon_opciones("worktree", args[k + 1:], _OPCIONES_WORKTREE[accion], f"worktree {accion}")
        if razon:
            return razon
        if accion == "add":
            nueva = _valor_de(args[k + 1:], "b", ())
            if not nueva:
                return "`git worktree add` bloqueado: sin `-b <rama nueva>` saca una rama EXISTENTE (la principal incluida) en otro árbol — usa `git worktree add <dir> -b <rama>`."
            if _principal_o_actual(nueva, branch):
                return f"`git worktree add -b {nueva}` bloqueado: ya es la rama principal o la actual — usa un nombre nuevo."
        if posicionales[0] == "add" and any(_cluster(t, "f") or _prefijo(t, "--force") for t in opciones):
            return "`git worktree add --force` bloqueado: crea el árbol aunque la rama ya esté en uso en otro — usa `git worktree add <dir> -b <rama>`."
    elif sub == "submodule":
        sub2 = posicionales[0] if posicionales else "status"
        if sub2 not in ("status", "update", "init", "sync", "summary", "foreach"):
            return "`git submodule` bloqueado: se permiten status, update, init, sync, summary y foreach (el código de foreach se analiza)."
    elif sub == "branch":
        if any(_cluster(t, "m") or _cluster(t, "M") or _cluster(t, "c") or _cluster(t, "C") or _prefijo(t, "--move", "--copy") for t in opciones):
            return "`git branch -m|-M|-c|-C` bloqueado: renombrar o copiar ramas mueve `refs/heads/*` (también la principal) — para listar usa `git branch`, para crear `git branch <rama>` o `git switch -c <rama>`."
        borra = any(_cluster(t, "d") or _prefijo(t, "--delete") for t in opciones)
        if borra:
            for n in posicionales:
                if _principal_o_actual(n, branch):
                    return (f"`git branch -d {n}` bloqueado: borrar la rama principal o la de trabajo actual y recrearla con `git branch`/`switch -c` la mueve (= `branch -f`) y deja la tarea sin su rama — "
                            "la limpieza de ramas la dirige el ritual de cierre de /dev-cycle (Fase 6).")
        elif posicionales and not any(_cluster(t, "l") or _cluster(t, "a") or _cluster(t, "r") or _prefijo(t, "--list", "--all", "--remotes", "--contains", "--no-contains", "--merged",
                                                                                                      "--no-merged", "--points-at", "--show-current") for t in opciones)                 and _es_rama_principal(posicionales[0].removeprefix("refs/heads/")):
            return f"`git branch {posicionales[0]}` bloqueado: crear una rama con el nombre de la principal la mueve (equivale a `branch -f`) — usa un nombre de rama de trabajo."
    elif sub == "clean":
        if not any(_cluster(t, "n") or _prefijo(t, "--dry-run") for t in opciones):
            return "`git clean` bloqueado: solo `clean -n|--dry-run` (simulación); borrar ficheros sin seguimiento puede llevarse cambios que no son tuyos."
    elif sub == "reflog":
        if posicionales and posicionales[0] not in ("show", "list", "exists"):
            return "`git reflog` bloqueado: solo se permite leerlo (`git reflog`, `show`)."
    elif sub == "push":
        malas = [t for t in opciones if t.split("=", 1)[0] not in _PUSH_OPCIONES]
        if malas:
            return f"`git push {malas[0]}` bloqueado: con la lista blanca solo se permiten {', '.join(sorted(_PUSH_OPCIONES))} (sin --force, --delete, --mirror, --no-verify, --prune…)."
        if len(posicionales) > 2 or (posicionales and (":" in posicionales[0] or posicionales[0] == ".")):
            return "`git push` bloqueado: solo se empuja la rama actual a su remoto (`git push [-u] [<remoto> [<rama>|HEAD|HEAD:<rama>]]`); sin refspec a otra rama y sin `.` como remoto."
        if len(posicionales) == 2:
            ref = posicionales[1]
            origen, dos, destino = ref.partition(":")
            origen = origen.removeprefix("refs/heads/")
            destino = (destino if dos else origen).removeprefix("refs/heads/")
            validos = {"HEAD", "@"} | ({branch} if branch and branch != "HEAD" else set())
            if "$()" in (origen, destino) and _rama_actual_por_sustitucion():
                validos.add("$()")      # fix25 (gap 6): `$(git branch --show-current)` / `$(git rev-parse --abbrev-ref HEAD)` son la rama actual por construccion
            if (dos and origen not in validos) or (not dos and origen not in validos) or (destino not in validos - {"@"}):
                return (f"`git push … {ref}` bloqueado: solo se empuja la rama actual (`{branch}`) o `HEAD` a una rama del mismo nombre; un refspec a otra rama (`@:main`, `HEAD@{{0}}:main`, `x:main`…) "
                        "mueve ramas ajenas.")
    elif sub in ("fetch", "pull"):
        if len(posicionales) > 2 or any(":" in t or t == "." for t in posicionales):
            return f"`git {sub}` bloqueado: sin refspec (`:`) ni `.` como remoto — `git {sub} [<remoto> [<rama>]]`."
    return None


def check_git(command, branch, _depth=0, _env=None, _base=False, _xargs=False, _inc=False):
    """Razón de deny o None. `branch` = rama actual (None si no hay git).
    Recursivo SOLO sobre lo que una shell ejecutaría (`sh -c "git push --force"`, `bash -c '…'`,
    `eval "…"`); un mensaje de commit con «rm -rf .» dentro es texto y no se analiza.
    Si la orden lleva un heredoc, el deny añade cómo escribirlo (T-06 fix6): su cuerpo se analiza como órdenes."""
    razon = _check_git(command, branch, _depth, _env, _base, _xargs, _inc)
    if razon and _depth == 0 and "<<" in command:
        razon += _NOTA_HEREDOC
    return razon


def _check_git(command, branch, _depth=0, _env=None, _base=False, _xargs=False, _inc=False):
    if _depth > 3:
        return ("orden con `bash -c`/`eval` anidados a más de 3 niveles bloqueada: el guardarraíl no la analiza "
                "entera — escribe la orden sin anidar.")
    if len(command) > _MAX_ORDEN:
        return (f"orden demasiado larga bloqueada ({len(command)} bytes, tope {_MAX_ORDEN}): el guardarraíl no "
                "la analiza — divídela en órdenes más cortas o escribe el contenido con Write.")
    # Recorte barato y lineal ANTES de tokenizar (fix6, punto 1): acota el coste del análisis que sigue.
    if (len(command) > _MAX_VISIBLE or len(command.split()) > _MAX_TOKENS) and _RECORTE_RE.search(command):
        return ("orden demasiado larga con `git` o cambio de base bloqueada: el guardarraíl no analiza "
                f"más de {_MAX_TOKENS} palabras ni {_MAX_VISIBLE} caracteres — divide la orden o escribe el "
                "contenido con la herramienta de edición.")
    command = _quitar_mensajes_de_commit(command)
    exportados = set()      # variables sensibles exportadas en segmentos anteriores de la MISMA orden
    segmentos, incompleta = _segmentos(command)
    # Lectura OPACA (fix14): el guardarraíl pierde texto o no sabe qué se ejecuta (`\c` + no ASCII, `\U` fuera de rango, anidado de
    # más de `_MAX_ANIDADO` niveles). Git puede llegar escapado o partido sin el texto `git`: se deniega siempre, sin buscarlo.
    if isinstance(incompleta, str):
        return (f"orden con lectura opaca bloqueada ({incompleta}): el guardarraíl no puede leerla entera y, ante la duda, no "
                "la da por inocua — escríbela sin esa construcción (`\\c` solo con ASCII, sin anidar tanto).")
    # El CR es un carácter normal en bash: `git status\r` no es `git status` y `echo x\r# …` no abre un comentario
    # (fix6, gap 9). En una orden con `git` (en cualquier grafía, fix14) no se intenta adivinar: se deniega.
    try:
        con_cr_y_git = "\r" in command and _contiene_git(command, segmentos)
    except _DecodificacionInestable:
        return _OPACA_ESCAPES
    if con_cr_y_git:
        return ("orden con retorno de carro (CR) y `git` bloqueada: bash trata el CR como parte de la palabra y el "
                "guardarraíl no puede saber qué ejecuta — escríbela con saltos de línea LF.")
    # La base cambia si CUALQUIER punto de la orden la cambia (o la heredó el `bash -c`/`eval` que la
    # contiene): el guardarraíl valida rutas contra el directorio actual, no contra el efectivo. El cambio de base
    # de un `eval`/`source` interno sube a la orden que lo contiene (`_cambia_base_en` lo mira también dentro).
    base_local = _cambia_base_en(segmentos)
    base_cambiada = _base or base_local
    incompleta = incompleta or _inc        # fix14: la marca se HEREDA al reanalizar el contenido de `bash -c`/`eval`
    try:
        contiene_git = bool(incompleta) and _contiene_git(command, segmentos)     # solo se necesita con una lectura incompleta
    except _DecodificacionInestable:
        return _OPACA_ESCAPES
    # Invariante de cierre (T-06 fix5): lo que el guardarraíl no pudo leer entero no se da por inocuo. Con algo
    # abierto al terminar de tokenizar (comilla, `$(`, backtick, heredoc sin cierre, escape final) la orden
    # ENTERA se deniega si contiene `git` o cambia la base; ya no se mira solo el último segmento.
    if incompleta and (contiene_git or base_local):
        return ("orden incompleta con `git` o cambio de base bloqueada (escape final, comilla, `$(`, backtick o "
                "heredoc sin cerrar): el guardarraíl no puede saber qué ruta o rama nombra — escríbela entera. Si es "
                "un mensaje de commit, usa `git commit -m \"$(cat <<'EOF' … EOF\\n)\"` o `git commit -F - <<'EOF'`; "
                "para cualquier otro texto, escríbelo con la herramienta de edición y usa `git commit -F <fichero>`.")
    for toks in segmentos:
        _fijar_orden_raw(command)       # fix25: el texto de ESTA orden (con comillas y `$(...)`) para las reglas que el tokenizado pierde; un `bash -c` anidado lo pisa, asi que se repone
        razon = _analiza_segmento(toks, branch, _depth, _env, _xargs, base_cambiada, incompleta, exportados)
        if razon:
            return razon
    return None


def _analiza_segmento(crudo, branch, _depth, _env, _xargs, base_cambiada, incompleta, exportados, _reanclado=False):
    """Razon de deny o None para UNA orden simple (`crudo`: sus palabras). Antes era el cuerpo del bucle de `_check_git` (fix17: tambien se llama sobre cada sufijo
    que abre una palabra git, envoltorio, shell o `eval`; `_reanclado` evita re-anclar dentro de un sufijo)."""
    toks, bindings, _chdir, desconocida, via_xargs = _desenvuelve(crudo, _env)
    if getattr(desconocida, "siempre", False) and getattr(desconocida, "motivo", ""):
        return (f"orden con lectura opaca bloqueada ({desconocida.motivo}): el guardarraíl no puede saber qué orden "
                "ejecuta env — escríbela sin `-S`, con el programa y sus argumentos en palabras separadas.")
    if getattr(desconocida, "siempre", False):
        return (f"valor de `env -S` ilegible bloqueado (`{desconocida}`: comilla abierta, más de {_MAX_VALOR_S} "
                f"caracteres o más de {_MAX_TROCEOS_S} `-S` anidados): el guardarraíl no puede saber qué orden "
                "ejecuta env — escríbela sin `-S`, con el programa y sus argumentos en palabras separadas.")
    if desconocida and (any(_GIT_TEXTO_RE.search(t) for t in crudo) or any(_GIT_TEXTO_RE.search(t) for t in toks)
                        or any(_program_name(t) in _INTERPRETES or _program_name(t).startswith("$") for t in toks)):
        return (f"opción `{desconocida}` de un envoltorio (`timeout`, `nice`, `sudo`, `xargs`, `flock`, `env`…) no "
                "reconocida en una orden con `git` o con un intérprete (`bash`, `sh`, `eval`, `env`, `xargs`…) detrás: el "
                "guardarraíl no puede saber si consume un valor ni qué orden ejecuta — escríbela sin esa opción o sin el "
                "envoltorio.")
    # Las rutas por stdin se HEREDAN al recursar en `sh|bash -c`/`eval` lanzados por `xargs` (fix8, gap 1): dentro de
    # `xargs -I{} sh -c 'git restore {}'` el `{}` es una ruta que el guardarraíl no ve, con o sin `{}` en la orden.
    via_xargs = via_xargs or _xargs
    if via_xargs:
        k, _hooks = _git_invocation(toks)
        if k >= 0 and toks[k] in _XARGS_DESTRUCTIVOS:
            return (f"`xargs … git {toks[k]}` bloqueado: las rutas llegan por la entrada estándar y el guardarraíl "
                    "no las ve, así que no puede saber qué cambios sin comitear descarta (mismo caso que "
                    "`--pathspec-from-file`) — nombra los ficheros en la propia orden o revierte con "
                    "`git diff <foto> -- <ficheros> | git apply -R`.")
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
        razon = check_git(sub, branch, _depth + 1, bindings, base_cambiada, via_xargs, bool(incompleta))
        if razon:
            return razon
    razon = check_ordenes_externas(toks)
    if razon:
        return razon
    razon = _razon_config(toks, bindings, exportados)
    if razon:
        return razon
    # fix17 (puntos 1 y 2): git que lanza git. Los argumentos que git pasa a una shell (`submodule foreach`, `rebase -x/--exec`, `bisect run`, los filtros de `filter-branch`,
    # `--upload-pack`/`--receive-pack`) se analizan como CODIGO, igual que el argumento de `bash -c`.
    if toks and _program_name(toks[0]) == "git":
        razon = _razon_git(toks, branch, base_cambiada)
        if razon:
            return razon
        for codigo in _codigo_de_git(toks):
            razon = check_git(codigo, branch, _depth + 1, bindings, base_cambiada, via_xargs, bool(incompleta))
            if razon:
                return razon
    # fix17 (puntos 1 y 2): RE-ANCLAJE general. Cada palabra de la orden simple que sea git, un envoltorio de la tabla, una shell o `eval` abre un sufijo que se analiza como un
    # SEGMENTO NUEVO y completo (sus propias asignaciones, `env -S`/`-C`, `xargs`, `bash -c`, config y cambio de base): lo que hay delante puede ser un programa que la tabla no
    # conoce (`uv run`, `chroot`, `strace`, `xvfb-run`…) y no sabemos que opciones consume. Hereda el entorno ya visto (superconjunto: solo analiza mas) y no se re-ancla dentro
    # de si mismo (el nivel exterior ya recorre cada palabra). Coste declarado: `echo git reset --hard` sin comillas se deniega (fix16).
    if not _reanclado:
        sufijos = _anclas(toks)
        if sufijos is None:
            return (f"orden con mas de {_MAX_SUFIJOS_GIT} palabras que abren un analisis (`git`, envoltorios, shells, `eval`) como argumentos de un programa bloqueada: el guardarrail "
                    "analiza cada una como una posible orden y no puede acotar el coste — escribe la orden con menos apariciones.")
        for sufijo in sufijos:
            razon = _analiza_segmento(sufijo, branch, _depth, bindings, via_xargs, base_cambiada or _cambia_base_en([sufijo]), incompleta, exportados, True)
            if razon:
                return razon
    if toks and toks[0].endswith("rm") and os.path.basename(toks[0]) == "rm":
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
            # fix15 (gap 1): la rama se consulta SIEMPRE, en cualquier orden Bash no vacia. Ninguna decision de seguridad depende de
            # `\bgit\b` en minusculas del texto crudo: `GIT switch main`, `g''it switch main` o `$'\x67it' checkout main` ejecutan git.
            if branch is None and branch_fn is not None:
                branch = branch_fn(project_dir)
            # fix18 (gap 1): las rutas y las refs se resuelven contra el `cwd` del payload (donde se ejecutara la orden), no contra el del proceso del guard.
            cwd = payload.get("cwd") if isinstance(payload, dict) else None
            previo = _CTX["cwd"]
            _CTX["cwd"] = cwd if isinstance(cwd, str) and cwd and os.path.isdir(cwd) else None
            try:
                return check_git(cmd, branch)
            finally:
                _CTX["cwd"] = previo
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
        razon = decide(payload, project_dir, cfg, branch_fn=rama_barata, agent=agent)
        if razon:
            print(deny_json(razon))
        return 0
    except Exception as e:  # noqa: BLE001 — fix12: este modo solo lo lanzan los hooks del rol protegido: ante la duda, se DENIEGA
        print(f"guardrail-check: error interno ({e!r}) — se deniega", file=sys.stderr)
        print(deny_json(f"error interno del guardarraíl ({e!r}): no se puede comprobar la orden, así que se deniega "
                        "(falla cerrado). Reintenta; si persiste, avisa para corregir el guardarraíl."))
        return 0


if __name__ == "__main__":
    sys.exit(main())
