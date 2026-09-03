#!/usr/bin/env python3
"""
guardrail-check.py — guardrails DETERMINISTAS del `implementer` (hook PreToolUse).

(Iniciativa deterministic-guardrails: las reglas «no toques docs/roadmap/ salvo tasks.md»,
«trabaja en rama» y «sin git destructivo» pasan de prosa a script con tests. Lo invoca el
wrapper `hooks/implementer-guardrail.sh`, registrado SOLO en el frontmatter `hooks:` de
`agents/implementer.md` — nunca en `hooks/hooks.json` global: planner/evaluator/analyst
escriben en docs/roadmap/ legítimamente. Ver docs/knowledge/adr/ADR-007.)

Uso:
  guardrail-check.py pre-tool [--project-dir DIR] [--agent implementer|architect]   # JSON del hook por stdin
  (sin --agent: $CLAUDE_AGENT_NAME si existe, si no `implementer`)

Modo `architect` (parity-core T-fix1, wrapper hooks/architect-guardrail.sh; enmienda a ADR-007):
  alcance        permitido SOLO `docs/roadmap/<inic>/design.md`, `docs/knowledge/adr/**` y
                 `docs/knowledge/README.md`; `spec.md`/`improvement-plan.md` de la iniciativa SOLO con
                 la herramienta Edit y si `old_string`/`new_string` contienen `design:` o `design.md`
                 (el enlace de la regla 7) — un Write completo o un Edit sin esa marca → deny. Riesgo
                 asumido y documentado: un Edit que incluya `design:` junto a otros cambios pasa (el
                 hook no puede diffear el fichero); lo caza la Lente A. Todo lo demás (código,
                 tasks.md, evaluation.md, gotchas/lessons, security-scan) → deny.
  git            igual que el implementer. ramaPrincipal NO aplica (escribe solo documentos, como planner).

Reglas (cada una desactivable en `.claude/dev.json` → `"guardrails": {…}`):
  alcance        Write/Edit/MultiEdit/NotebookEdit sobre docs/roadmap/** que no sea `tasks.md`
                 (incl. testing/**, que es de qa) → deny. docs/security-scan/** → deny.
                 docs/knowledge/** → permitido (ADR del implementer). Rutas CASE-INSENSITIVE
                 (`Docs/Roadmap/x/Spec.md` también deny: Windows/macOS no distinguen mayúsculas).
                 Excepción en la raíz de docs/roadmap/: `README.md` (índice de iniciativas, que el
                 cierre de cada iniciativa actualiza) → permitido. `CALIBRATION.md`, `DRIFT.md` y
                 `BACKLOG.md` siguen deny POR DISEÑO: los escriben /retro, /spec-drift y /pm-backlog,
                 que son comandos (no pasan por este hook), no el implementer.
  git            Bash: `git push --force|-f|--force-with-lease` → deny; `git branch -D` → deny;
                 `git checkout|switch main|master` → deny solo si la rama actual es una feature;
                 `rm -rf` sobre `/`, `~`, `.git`, `.` → deny; refspec `+rama` en push = force;
                 se analizan también las cadenas de `sh -c "…"`/`bash -c '…'`. Todo lo demás permitido.
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

WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
MAIN_BRANCHES = {"main", "master"}
DEFAULTS = {"alcance": True, "git": True, "ramaPrincipal": True}


# ---------------------------------------------------------------- config ----
def load_config(project_dir):
    """Devuelve (config dict con las 3 claves, activo bool). Nunca lanza."""
    path = os.path.join(project_dir, ".claude", "dev.json")
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
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


def check_alcance_architect(rel, tool, tool_input):
    """Razón de deny o None — alcance del `architect` (solo diseño, ADR e índice de knowledge)."""
    low = rel.lower()
    if _SECSCAN_RE.search(rel):
        return f"«{rel}» está bajo docs/security-scan/ (propiedad de nemesis): el architect no escribe ahí."
    if re.search(r"(?:^|/)docs/knowledge/(adr/[^/]+|readme\.md)$", low):
        return None
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
            f"`design:` en spec/plan (Edit) y docs/knowledge/adr/ + README.md. Ni código, ni tasks.md, ni "
            f"evaluation.md — anótalo en «Preguntas abiertas» de design.md y sigue.")


def check_alcance(rel):
    """Razón de deny o None."""
    if _SECSCAN_RE.search(rel):
        return (f"«{rel}» está bajo docs/security-scan/ (propiedad de nemesis): el implementer "
                f"no escribe ahí — deja el hallazgo en tasks.md y sigue.")
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
def current_branch(project_dir):
    """Nombre de la rama o None si no hay git / no se puede saber."""
    try:
        r = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=project_dir or None,
                           capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode != 0:
        return None
    b = r.stdout.strip()
    return b or None


def _segmentos(command):
    """Trocea por `;`, `&&`, `||`, `|` RESPETANDO comillas (shlex con punctuation_chars): así
    `sh -c 'cd x && rm -rf .'` es UN segmento cuyo argumento se analiza aparte (intento 2)."""
    try:
        lex = shlex.shlex(command, posix=True, punctuation_chars=";&|")
        lex.whitespace_split = True
        toks = list(lex)
    except ValueError:
        toks = command.split()
    out, cur = [], []
    for t in toks:
        if t and set(t) <= set(";&|"):
            if cur:
                out.append(cur)
            cur = []
        else:
            cur.append(t)
    if cur:
        out.append(cur)
    return out


def _es_git(toks, sub):
    """toks = ['git', <opciones globales…>, sub, …] → índice del subcomando o -1."""
    if not toks or os.path.basename(toks[0]) != "git":
        return -1
    i = 1
    while i < len(toks) and toks[i].startswith("-"):
        # opciones globales con valor: -C <dir>, -c <k=v>
        if toks[i] in ("-C", "-c") and i + 1 < len(toks):
            i += 2
        else:
            i += 1
    return i if i < len(toks) and toks[i] == sub else -1


_SHELLS = {"sh", "bash", "zsh", "dash", "ksh"}


def _subcomandos_shell(toks):
    """Cadenas que una shell ejecutaría como comando: el argumento de `-c` de sh/bash/zsh/dash
    (también en clusters `-lc`, `-ec`) y los argumentos de `eval`."""
    if not toks:
        return []
    prog = os.path.basename(toks[0])
    if prog == "eval":
        return [" ".join(toks[1:])] if len(toks) > 1 else []
    if prog in _SHELLS:
        for i, t in enumerate(toks[1:], 1):
            if re.fullmatch(r"-[a-zA-Z]*c[a-zA-Z]*", t) and i + 1 < len(toks):
                return [toks[i + 1]]
    return []


def check_git(command, branch, _depth=0):
    """Razón de deny o None. `branch` = rama actual (None si no hay git).
    Recursivo SOLO sobre lo que una shell ejecutaría (`sh -c "git push --force"`, `bash -c '…'`,
    `eval "…"`); un mensaje de commit con «rm -rf .» dentro es texto y no se analiza."""
    if _depth > 3:
        return None
    for toks in _segmentos(command):
        # Solo se recurre en el argumento de `sh|bash|zsh|dash -c` y en el de `eval` — NO en tokens
        # arbitrarios (`git commit -m "rm -rf . en el mensaje"` es texto, no un comando; regresión
        # cazada en la revisión, intento 2).
        for sub in _subcomandos_shell(toks):
            razon = check_git(sub, branch, _depth + 1)
            if razon:
                return razon
        i = _es_git(toks, "push")
        if i >= 0:
            for t in toks[i + 1:]:
                if t == "--force" or t.startswith("--force-with-lease") or t.startswith("--force=") \
                        or (re.fullmatch(r"-[a-zA-Z]+", t) and "f" in t) \
                        or (t.startswith("+") and len(t) > 1):          # refspec `+main` = force
                    return ("`git push` forzado bloqueado: reescribe historia compartida — "
                            "haz push normal; si de verdad hace falta, que lo pida el usuario.")
        i = _es_git(toks, "branch")
        if i >= 0:
            rest = toks[i + 1:]
            if any(t == "-D" or (re.fullmatch(r"-[a-zA-Z]+", t) and "D" in t) for t in rest) \
                    or ("--delete" in rest and "--force" in rest):
                return ("`git branch -D` bloqueado: borra una rama sin comprobar que esté integrada — "
                        "usa `-d`, o que lo haga el ritual de cierre de /dev-cycle (Fase 6).")
        for sub in ("checkout", "switch"):
            i = _es_git(toks, sub)
            if i >= 0:
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
