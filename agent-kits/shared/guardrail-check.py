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
import bisect
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


class _Lectura:
    """Resultado compartido de una lectura: segmentos, cuerpos de heredoc y si quedó algo abierto."""
    __slots__ = ("out", "cuerpos", "incompleta", "tablas", "inicios")

    def __init__(self):
        self.out, self.cuerpos, self.incompleta, self.tablas = [], [], False, {}
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


def _leer(command, i, modo, st, prof):
    """Tokeniza `command` desde `i`: `modo` `top` (hasta el final) o `sub` (hasta el `)` que cierra un `$(`). Los
    segmentos van a `st.out`. Devuelve `(posición, heredocs pendientes sin cuerpo)`. Los paréntesis sin comillas
    separan órdenes, `$(…)` y los backticks se leen como órdenes también DENTRO de comillas dobles (bash las
    ejecuta; el contenido de un backtick se lee aparte, sin sus barras de escape) y el cuerpo de un heredoc no se
    tokeniza aquí: lo lee `_segmentos` como órdenes."""
    n = len(command)
    if prof > _MAX_ANIDADO:
        st.incompleta = True
        return n, []
    cur, word, started, quote, pend, par, cierre = [], [], False, None, [], 0, False
    ult_redir = -2          # posición del último `<`/`>` SIN escapar ni entrecomillar (fix7, gap 6)
    while i < n:
        c = command[i]
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
        if quote == "$'":
            # ANSI-C `$'…'`: la barra escapa el carácter siguiente (también la comilla simple) (fix6, lente C)
            if c == "\\" and i + 1 < n:
                word.append(command[i + 1])
                i += 2
                continue
            if c == "'":
                quote = None
            else:
                word.append(c)
            i += 1
            continue
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
        if c == "$" and quote is None and command.startswith(("$'", '$"'), i):
            # `$'…'` (ANSI-C) y `$"…"` (traducción): la `$` no es parte de la palabra
            quote, started = ("$'" if command[i + 1] == "'" else '"'), True
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
        elif c == "(" and command.startswith("((", i) and not cur and not started \
                and _aritmetica(command, i + 2, st) is not None:
            i = _aritmetica(command, i + 2, st)    # `(( expr ))`: aritmética, no órdenes
            continue
        elif c == "#" and not started:
            newline = command.find("\n", i)
            i = n if newline < 0 else newline
            continue
        elif c == ")" and modo == "sub" and par == 0:
            i += 1
            cierre = True
            break
        elif c == "&" and (ult_redir == i - 1 or command.startswith("&>", i)):
            word.append(c)                # `2>&1`, `>&2`, `&>fichero`: redirección, no separador de órdenes
            started = True
        elif c in " \t\n;&|()":           # el CR NO separa: en bash es un carácter normal (fix6, gap 9)
            if started:
                cur.append("".join(word))
                word, started = [], False
            if c in "\n;&|()" and cur:
                st.out.append(cur)
                cur = []
            par += (c == "(") - (c == ")" and par > 0)
        else:
            if c in "<>":
                ult_redir = i
            word.append(c)
            started = True
        i += 1
    if quote or (modo != "top" and not cierre):
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
    segs, incompleta = st.out, st.incompleta
    for texto, _citado, _cerrado in st.cuerpos:
        if _prof >= _MAX_ANIDADO:
            incompleta = True
            continue
        sub, inc = _segmentos(texto, _prof + 1)
        segs.extend(sub)
        incompleta = incompleta or inc
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


def _program_name(token):
    name = token.replace("\\", "/").rsplit("/", 1)[-1].lower()
    return name[:-4] if name.endswith(".exe") else name


# Palabras de control de shell y envoltorios que PRECEDEN al programa real de un segmento: el programa solo cuenta en
# esa posición (`echo cd`, `git restore src/cd`, `git commit -m env` no cambian nada). FUENTE ÚNICA (fix7, gaps 3, 7 y 9):
# `_desenvuelve` es lo que llaman `_check_git` (qué git se invoca) y `_cambia_base_en` (qué cambia la base); ya no hay dos
# implementaciones que se desincronicen (`env -S` solo se desenvolvía en una de ellas).
_CONTROL = frozenset(("if", "then", "else", "elif", "while", "until", "do", "{", "!", "time", "coproc", "nohup",
                      "builtin"))
_ENVOLTORIOS = frozenset(("env", "command", "builtin", "exec", "sudo", "nohup", "nice", "xargs", "stdbuf",
                          "timeout", "setsid", "ionice", "flock"))
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
    "xargs": ("aEIdLnPs", ("--arg-file", "--eof", "--replace", "--delimiter", "--max-lines", "--max-args",
                           "--max-procs", "--max-chars", "--process-slot-var"), "0oprtxv",
              ("--null", "--open-tty", "--interactive", "--no-run-if-empty", "--verbose", "--exit", "--show-limits",
               "--help", "--version"), "eil"),
    "setsid": ("", (), "cfw", ("--ctty", "--fork", "--wait", "--help", "--version"), ""),
    "ionice": ("cnpPu", ("--class", "--classdata", "--pid", "--pgid", "--uid"), "t", ("--ignore", "--help",
                                                                                  "--version"), ""),
    "flock": ("wE", ("--timeout", "--wait", "--conflict-exit-code"), "sxuneoF",
              ("--shared", "--exclusive", "--unlock", "--nonblock", "--nb", "--no-fork", "--close", "--help",
               "--version"), ""),
    "nohup": ("", (), "", ("--help", "--version"), ""),
}
_ENV_LARGAS_SIN_VALOR = ("--null", "--debug", "--list-signal-handling", "--help", "--version")
_ENV_LARGAS_CON_VALOR = ("--argv0", "--block-signal", "--default-signal", "--ignore-signal")
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
        todas = largas_v + largas_s
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


def _saltar_envoltorio(toks, i):
    """`(índice tras el envoltorio de `toks[i]` y sus opciones, ¿cambia el directorio?, opción desconocida|None)`:
    salta opciones (con el valor de las que lo toman) y los argumentos propios de `timeout` (la duración) y `flock` (el
    fichero). `sudo -D`/`--chdir` cambia el directorio de trabajo."""
    nombre = _program_name(toks[i])
    n, chdir = len(toks), False
    i += 1
    while i < n:
        o = toks[i]
        if o == "--":
            i += 1
            break
        if not o.startswith("-") or o == "-":
            break
        if nombre == "sudo" and (o.startswith("--chdir") or (not o.startswith("--") and "D" in o[1:])):
            chdir = True
        j, conocida = _opcion_envoltorio(nombre, toks, i)
        if not conocida:
            return i, chdir, o
        i = j
    if nombre == "flock" and i < n and toks[i] in ("-c", "--command"):
        return i, chdir, toks[i]                    # `flock f -c 'git …'`: la orden va en una cadena que no se ve
    if nombre in ("timeout", "flock") and i < n:
        i += 1                                      # la duración / el fichero de bloqueo
    return i, chdir, None


def _opciones_env(nombre, toks, i, bindings):
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
            base = o.split("=", 1)[0]
            if nombre == "env" and o in ("--ignore-environment",):
                bindings.clear()
                i += 1
            elif nombre == "env" and o == "--unset" and i + 1 < len(toks):
                bindings.pop(toks[i + 1], None)
                i += 2
            elif nombre == "env" and o.startswith("--unset="):
                bindings.pop(o.split("=", 1)[1], None)
                i += 1
            elif nombre == "env" and (o == "--chdir" and i + 1 < len(toks)):
                chdir = True
                i += 2
            elif nombre == "env" and o.startswith("--chdir="):
                chdir = True
                i += 1
            elif nombre == "env" and (o == "--split-string" or o.startswith("--split-string=")):
                valor, usados = ((o.split("=", 1)[1], 1) if "=" in o else
                                 (toks[i + 1] if i + 1 < len(toks) else "", 2))
                toks = toks[:i] + valor.split() + toks[i + usados:]
            elif nombre == "env" and base in _ENV_LARGAS_SIN_VALOR:
                i += 1
            elif nombre == "env" and base in _ENV_LARGAS_CON_VALOR:
                i += 1 if "=" in o else 2
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
                    toks = toks[:i] + valor.split() + toks[i + usados:]
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


def _desenvuelve(toks, inherited=None):
    """`(resto, bindings, ¿cambia el directorio un envoltorio?, opción desconocida|None, ¿pasó por xargs?)` de un
    segmento: salta asignaciones (que se anotan en `bindings`), palabras de control, redirecciones iniciales, `function
    nombre` y envoltorios con sus opciones, hasta el programa real (`resto[0]`). Nunca evalúa texto de shell. Recorrido
    lineal: nada de rebanar `toks` por token. Una opción desconocida detiene el desenvuelto: `resto` empieza en ella."""
    bindings = dict(inherited or {})
    toks = list(toks)
    i, chdir, desconocida, via_xargs = 0, False, None, False
    while i < len(toks):
        t = toks[i]
        asignacion = _ASSIGNMENT_RE.fullmatch(t)
        if asignacion:
            bindings[asignacion[1]] = asignacion[2]
            i += 1
        elif t == "function" and i + 1 < len(toks):
            i += 2                      # `function f { git … }`: el nombre y la llave no son el programa
        elif t in _CONTROL:
            i += 1          # `{ git restore .; }`, `then git restore .`, `time git …`: el programa sigue después
            if t == "time":
                while i < len(toks) and toks[i] in ("-p", "--"):
                    i += 1
        elif _salta_redireccion(toks, i) != i:
            i = _salta_redireccion(toks, i)
        else:
            nombre = _program_name(t)
            if nombre in ("env", "command", "exec"):
                i, toks, cambia, desc = _opciones_env(nombre, toks, i, bindings)
            elif nombre in _ENVOLTORIOS:
                via_xargs = via_xargs or nombre == "xargs"
                i, cambia, desc = _saltar_envoltorio(toks, i)
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
    except OSError:
        propio = False
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
        if nombre == "eval" and len(resto) > 1:
            if _prof >= 3 or _cambia_base_en(_segmentos(" ".join(resto[1:]))[0], _prof + 1):
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
_GIT_TEXTO_RE = re.compile(r"\bgit\b")
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
    if prog in _SHELLS or prog.startswith("$"):        # `$SHELL -c '…'`, `p=bash; $p -c '…'` (fix6, lente A)
        for i, t in enumerate(toks[1:], 1):
            if re.fullmatch(r"-[a-zA-Z]*c[a-zA-Z]*", t) and i + 1 < len(toks):
                # `bash -c -- 'git …'`: tras `-c`, un `--` termina las opciones y la orden es la palabra siguiente (fix7)
                return [toks[i + 2] if toks[i + 1] == "--" and i + 2 < len(toks) else toks[i + 1]]
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


def check_git(command, branch, _depth=0, _env=None, _base=False):
    """Razón de deny o None. `branch` = rama actual (None si no hay git).
    Recursivo SOLO sobre lo que una shell ejecutaría (`sh -c "git push --force"`, `bash -c '…'`,
    `eval "…"`); un mensaje de commit con «rm -rf .» dentro es texto y no se analiza.
    Si la orden lleva un heredoc, el deny añade cómo escribirlo (T-06 fix6): su cuerpo se analiza como órdenes."""
    razon = _check_git(command, branch, _depth, _env, _base)
    if razon and _depth == 0 and "<<" in command:
        razon += _NOTA_HEREDOC
    return razon


def _check_git(command, branch, _depth=0, _env=None, _base=False):
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
    # El CR es un carácter normal en bash: `git status\r` no es `git status` y `echo x\r# …` no abre un comentario
    # (fix6, gap 9). En una orden con `git` no se intenta adivinar: se deniega.
    if "\r" in command and _GIT_TEXTO_RE.search(command):
        return ("orden con retorno de carro (CR) y `git` bloqueada: bash trata el CR como parte de la palabra y el "
                "guardarraíl no puede saber qué ejecuta — escríbela con saltos de línea LF.")
    exportados = set()      # variables sensibles exportadas en segmentos anteriores de la MISMA orden
    segmentos, incompleta = _segmentos(command)
    # La base cambia si CUALQUIER punto de la orden la cambia (o la heredó el `bash -c`/`eval` que la
    # contiene): el guardarraíl valida rutas contra el directorio actual, no contra el efectivo. El cambio de base
    # de un `eval`/`source` interno sube a la orden que lo contiene (`_cambia_base_en` lo mira también dentro).
    base_local = _cambia_base_en(segmentos)
    base_cambiada = _base or base_local
    contiene_git = bool(_GIT_TEXTO_RE.search(command))
    # Invariante de cierre (T-06 fix5): lo que el guardarraíl no pudo leer entero no se da por inocuo. Con algo
    # abierto al terminar de tokenizar (comilla, `$(`, backtick, heredoc sin cierre, escape final) la orden
    # ENTERA se deniega si contiene `git` o cambia la base; ya no se mira solo el último segmento.
    if incompleta and (contiene_git or base_local):
        return ("orden incompleta con `git` o cambio de base bloqueada (escape final, comilla, `$(`, backtick o "
                "heredoc sin cerrar): el guardarraíl no puede saber qué ruta o rama nombra — escríbela entera. Si es "
                "un mensaje de commit, usa `git commit -m \"$(cat <<'EOF' … EOF\\n)\"` o `git commit -F - <<'EOF'`; "
                "para cualquier otro texto, escríbelo con la herramienta de edición y usa `git commit -F <fichero>`.")
    for n, toks in enumerate(segmentos):
        crudo = toks
        toks, bindings, _chdir, desconocida, via_xargs = _desenvuelve(toks, _env)
        if desconocida and any(_GIT_TEXTO_RE.search(t) for t in crudo):
            return (f"opción `{desconocida}` de un envoltorio (`timeout`, `nice`, `sudo`, `xargs`, `flock`, `env`…) no "
                    "reconocida en una orden con `git`: el guardarraíl no puede saber si consume un valor ni qué "
                    "orden ejecuta — escríbela sin esa opción o sin el envoltorio.")
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
            razon = check_git(sub, branch, _depth + 1, bindings, base_cambiada)
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
                razon = _razon_restauracion(sub, toks[i + 1:],
                                            base_cambiada)
                if razon:
                    return razon
                if sub == "restore":
                    continue
                if "--" in toks[i + 1:]:
                    continue          # `git checkout main -- fichero` restaura ficheros, no cambia de rama
                args = [t for t in toks[i + 1:] if not t.startswith("-")]
                flags = [t for t in toks[i + 1:] if t.startswith("-")]
                # El destino puede ser la rama principal con otro nombre (`refs/heads/master`, `origin/main`,
                # `master^0`, `MAIN`) o «la anterior» (`-`, `@{-1}`): fix6, gap 11.
                destino = args[0] if args else ("-" if "-" in flags else None)
                crea = any(f in ("-b", "-B", "-c", "-C", "-t", "--track") for f in flags)
                # Fix7, gap 8: también «la anterior» con cualquier N (`@{-2}`), una ref remota (`origin/HEAD`, deja HEAD
                # suelto sobre ella) y `--detach`/`-d` (suelta HEAD de la rama de trabajo, con o sin destino).
                sale = destino is not None and (destino == "-" or _ANTERIOR_RE.fullmatch(destino)
                                                or _es_rama_principal(destino) or _REMOTA_RE.match(destino))
                suelta = any(_prefijo(f, "--detach") or _cluster(f, "d") for f in flags)
                if (sale or suelta) and not crea and branch and branch not in MAIN_BRANCHES and branch != "HEAD":
                    return (f"`git {sub} {destino or '--detach'}` bloqueado: estás en la rama de trabajo «{branch}» "
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
