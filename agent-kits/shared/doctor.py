#!/usr/bin/env python3
"""
doctor.py — diagnóstico DETERMINISTA y SIN EFECTOS de la instalación del plugin en un proyecto
(agent-kits/shared: lo invocan el comando `/doctor` y el paso 0 de `/setup`).

Cinco bloques, un veredicto por línea (✅ ok · ⚠️ aviso · ❌ error · ℹ️ informativo) y, en TODA
línea ⚠️/❌, el **arreglo sugerido** en llano:

  a) herramientas  `python3` (≥ 3.9), `git`, `bash`, `jq` (opcional: la statusline lo usa con
                   fallback a `python3`), `node`/`npm` (opcional: skill `to-pdf`), Playwright
                   (opcional: agente `qa`; `~/.claude/tool-cache/qa/node_modules/@playwright`).
  b) plugin        raíz resuelta (`--plugin-root` → `CLAUDE_PLUGIN_ROOT` → padre de
                   `agent-kits/shared` → `find` sobre `$PWD/.claude` y `$HOME/.claude`); hooks de
                   `hooks/hooks.json` (JSON válido; cada script existe → ❌ si no, y es ejecutable
                   → ⚠️ si no; reutiliza `lint_hook_commands` de `scripts/lint_plugin.py` si está,
                   comprobación local equivalente si no); statusline configurada o no (informativo).
  c) configs       `.claude/rates.json` (JSON válido; `precioTokens` a 0 o sin `verificado…` →
                   ⚠️ «a verificar» con la skill `rates-verify`), `.claude/dev.json` (JSON válido;
                   clave desconocida → ⚠️; valor fuera de vocabulario → ❌ con el valor esperado;
                   `modelos` resueltos con `model-tier.py --all --json` y sus avisos),
                   `.claude/jira.json` y `.claude/confluence.json` (si `enabled: true`, campos
                   obligatorios presentes; fichero ausente → «no configurado» informativo).
  d) estado        marcadores huérfanos de `usage-state.json` (`usage-meter.py status`), iniciativas
                   `en-progreso` (`progress-report.py active`), última entrada del journal
                   (`docs/knowledge/journal/`) y último informe de `evals/reports/` con su fecha.
  e) versión       `version` de `plugin.json` frente a `.claude/.plugin-version-seen` si existe.
                   **SIN RED**: no consulta marketplace, GitHub ni npm, así que solo dice «versión X;
                   la última vez que se vio este proyecto era Y» (o «sin registro»). NUNCA afirma
                   que haya una actualización disponible — no tiene forma de saberlo.

**No escribe nada en el proyecto** (ni configs, ni estado, ni caché): es un diagnóstico de solo
lectura, así que se puede lanzar sin miedo tantas veces como haga falta.

Uso:
  doctor.py [--root DIR] [--plugin-root DIR] [--json]
Exit:
  0  sin ❌ (los ⚠️/ℹ️ no bloquean: el plugin degrada, no rompe)
  1  al menos un ❌
  2  error de USO: `--root`/`--plugin-root` que no existen como directorio
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

OK, AVISO, ERROR, INFO = "ok", "aviso", "error", "info"
ICONO = {OK: "✅", AVISO: "⚠️", ERROR: "❌", INFO: "ℹ️"}
ORDEN = (OK, AVISO, ERROR, INFO)

TIMEOUT = 20                     # los scripts hermanos son locales y deterministas
HOOK_PATH_RE = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/([^\s\"']+)")
BACKTICK_RE = re.compile(r"`([^`]+)`")

# --- vocabulario de .claude/dev.json (regla 9 de docs/CONVENTIONS.md) -------------------
DEV_BOOLES = ("tdd", "worktree", "subagentes", "constitucion", "statusline")
DEV_LENTES = ("auto", "siempre", "nunca")
DEV_GUARDRAIL_REGLAS = ("alcance", "ramaPrincipal", "git")
DEV_SESION_CLAVES = ("indice", "journal")
DEV_CLAVES = set(DEV_BOOLES) | {"guardrails", "revision", "sesion", "modelos", "tests"}

JIRA_OBLIGATORIOS = ("cloudId", "granularidad", "assignee", "alCubrirJornada")
CONFLUENCE_OBLIGATORIOS = ("cloudId", "spaceKey", "anchor", "home")

PLAYWRIGHT_REL = os.path.join(".claude", "tool-cache", "qa", "node_modules", "@playwright")


# ------------------------------------------------------------------ utilidades

def linea(estado, que, detalle="", arreglo=""):
    """Una fila del informe. `arreglo` es OBLIGATORIO en ⚠️/❌ (lo comprueban los tests)."""
    return {"estado": estado, "que": que, "detalle": detalle, "arreglo": arreglo}


def _leer_json(path):
    """(datos, error_legible). Fichero ausente → (None, None)."""
    if not os.path.isfile(path):
        return None, None
    try:
        with open(path, encoding="utf-8-sig") as fh:
            return json.load(fh), None
    except (ValueError, UnicodeDecodeError) as e:
        return None, f"no es JSON válido ({e.__class__.__name__}: {e})"
    except OSError as e:
        return None, f"no se puede leer ({e.__class__.__name__})"


def _correr(cmd, cwd=None):
    """(stdout, ok). Nunca lanza: un script hermano ausente o roto degrada a (\"\", False)."""
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=TIMEOUT)
        return r.stdout, r.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return "", False


def _json_de(salida):
    try:
        return json.loads(salida)
    except (ValueError, TypeError):
        return None


def es_plugin(root):
    """Una raíz de plugin tiene, al menos, `agents/` o `skills/` (instalaciones parciales incluidas)."""
    return bool(root) and os.path.isdir(root) and (
        os.path.isdir(os.path.join(root, "agents")) or os.path.isdir(os.path.join(root, "skills")))


def localizar_plugin(explicito=None):
    """`--plugin-root` → `CLAUDE_PLUGIN_ROOT` → padre de agent-kits/shared → `find` en
    `$PWD/.claude` y `$HOME/.claude` (misma precedencia que model-tier.py, regla 5)."""
    if explicito:
        return explicito if es_plugin(explicito) else None
    for cand in (os.environ.get("CLAUDE_PLUGIN_ROOT"), os.path.dirname(os.path.dirname(HERE))):
        if es_plugin(cand):
            return cand
    for base in (os.path.join(os.getcwd(), ".claude"), os.path.join(os.path.expanduser("~"), ".claude")):
        if not os.path.isdir(base):
            continue
        salida, _ok = _correr(["find", base, "-type", "d", "-path", "*agent-kits/shared"])
        for ln in salida.splitlines():
            cand = os.path.dirname(os.path.dirname(ln.strip()))
            if es_plugin(cand):
                return cand
    return None


def _cargar_linter(plugin_root):
    """`scripts/lint_plugin.py` del plugin como módulo (sin efectos) o None: reutilizamos su
    `lint_hook_commands` para no tener dos criterios de «hook roto» en el repo."""
    if not plugin_root:
        return None
    path = os.path.join(plugin_root, "scripts", "lint_plugin.py")
    if not os.path.isfile(path):
        return None
    previo = sys.dont_write_bytecode
    sys.dont_write_bytecode = True          # importar no debe dejar `__pycache__` (solo lectura)
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("lint_plugin_doctor", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod if hasattr(mod, "lint_hook_commands") else None
    except Exception:            # noqa: BLE001 — el doctor degrada a su comprobación local
        return None
    finally:
        sys.dont_write_bytecode = previo


def _hooks_local(plugin_root, cmds, origen):
    """Comprobación equivalente a `lint_hook_commands` cuando el linter no está disponible."""
    errs, warns = [], []
    for cmd in cmds:
        for rel in HOOK_PATH_RE.findall(cmd):
            fp = os.path.join(plugin_root, rel)
            if not os.path.isfile(fp):
                errs.append(f"{origen}: el command referencia `{rel}`, que no existe")
            elif not os.access(fp, os.X_OK):
                warns.append(f"{origen}: `{rel}` no es ejecutable (chmod +x recomendado; se lanza con `bash`)")
    return errs, warns


def _rel_de(msg):
    m = BACKTICK_RE.search(msg)
    return m.group(1) if m else ""


# ------------------------------------------------------------------ a) herramientas

def bloque_herramientas():
    ls = []
    v = sys.version_info
    ver = f"{v.major}.{v.minor}.{v.micro}"
    if v >= (3, 9):
        ls.append(linea(OK, "python3", f"{ver} (≥ 3.9)"))
    else:
        ls.append(linea(ERROR, "python3", f"{ver} — el plugin necesita 3.9+",
                        "instala Python 3.9 o superior; sin él los scripts deterministas no corren"))

    if shutil.which("git"):
        ls.append(linea(OK, "git", "en PATH"))
    else:
        ls.append(linea(AVISO, "git", "no está en PATH",
                        "instala git: sin él no hay ramas, `scope-check.py`, hotspots de "
                        "`code-health` ni ficheros tocados en el journal (el resto sigue funcionando)"))

    if shutil.which("bash"):
        ls.append(linea(OK, "bash", "en PATH"))
    else:
        ls.append(linea(AVISO, "bash", "no está en PATH",
                        "instala bash: los hooks de `hooks/` se lanzan con `bash` y sin él no informan"))

    if shutil.which("jq"):
        ls.append(linea(OK, "jq", "en PATH (opcional)"))
    else:
        ls.append(linea(INFO, "jq", "no está (opcional)",
                        "no hace falta: la statusline usa `python3` como alternativa"))

    node, npm = shutil.which("node"), shutil.which("npm")
    if node and npm:
        ls.append(linea(OK, "node/npm", "en PATH (opcional)"))
    else:
        falta = " y ".join(x for x, p in (("node", node), ("npm", npm)) if not p)
        ls.append(linea(INFO, "node/npm", f"falta {falta} (opcional)",
                        "solo lo necesita la skill `to-pdf` (Chromium headless); instálalo si vas a "
                        "exportar PDF"))

    pw = os.path.join(os.path.expanduser("~"), PLAYWRIGHT_REL)
    if os.path.isdir(pw):
        ls.append(linea(OK, "Playwright", "caché de herramientas presente (opcional)"))
    else:
        ls.append(linea(INFO, "Playwright", "no instalado (opcional)",
                        "solo lo necesita el agente `qa` para E2E en local; lo instala él la primera vez"))
    return {"clave": "herramientas", "titulo": "Herramientas", "lineas": ls}


# ------------------------------------------------------------------ b) plugin

def bloque_plugin(plugin_root, project, explicito=None):
    ls = []
    if not plugin_root:
        que = "raíz del plugin"
        det = (f"`--plugin-root {explicito}` no contiene el plugin (falta `agents/` y `skills/`)"
               if explicito else "no localizada")
        ls.append(linea(ERROR, que, det,
                        "instálalo como plugin (`/plugin marketplace add …` + `/plugin install custom-agents`) "
                        "o pásame la ruta con `--plugin-root <dir>`"))
        return {"clave": "plugin", "titulo": "Plugin", "lineas": ls}

    n = {}
    for k, sub, pred in (("agentes", "agents", lambda p: p.endswith(".md")),
                         ("comandos", "commands", lambda p: p.endswith(".md")),
                         ("skills", "skills", None)):
        d = os.path.join(plugin_root, sub)
        try:
            entradas = os.listdir(d)
        except OSError:
            n[k] = 0
            continue
        n[k] = len([e for e in entradas if pred(e)]) if pred else \
            len([e for e in entradas if os.path.isdir(os.path.join(d, e))])
    ls.append(linea(OK, "raíz del plugin", f"{plugin_root} · {n['agentes']} agentes · "
                                           f"{n['skills']} skills · {n['comandos']} comandos"))

    # --- hooks globales ---
    hpath = os.path.join(plugin_root, "hooks", "hooks.json")
    datos, err = _leer_json(hpath)
    if err:
        ls.append(linea(ERROR, "hooks/hooks.json", err,
                        "restaura el fichero del plugin (`claude plugin update`) o corrige el JSON: "
                        "con él roto ningún hook informativo se registra"))
    elif datos is None:
        ls.append(linea(AVISO, "hooks/hooks.json", "no existe",
                        "instalación parcial: reinstala el plugin si esperabas los hooks de progreso "
                        "y de bitácora (el ciclo funciona sin ellos, sin avisos en vivo)"))
    elif not isinstance(datos.get("hooks"), dict):
        ls.append(linea(ERROR, "hooks/hooks.json", "falta la raíz `hooks` (objeto evento → grupos)",
                        "restaura el fichero del plugin: el registro de hooks es inválido tal cual está"))
    else:
        linter = _cargar_linter(plugin_root)
        eventos, errs, warns = [], [], []
        for evento, grupos in datos["hooks"].items():
            if not isinstance(grupos, list):
                errs.append(f"hooks/hooks.json [{evento}]: `{evento}` debe ser una lista de grupos")
                continue
            cmds = [str(h.get("command", "")) for g in grupos if isinstance(g, dict)
                    for h in g.get("hooks", []) if isinstance(h, dict) and h.get("type") == "command"]
            eventos.append(f"{evento} ({len(cmds)})")
            fn = linter.lint_hook_commands if linter else _hooks_local
            e, w = fn(plugin_root, cmds, f"hooks/hooks.json [{evento}]")
            errs.extend(e)
            warns.extend(w)
        fuente = "criterio de `lint_plugin.py`" if linter else "comprobación local (linter no disponible)"
        if not errs and not warns:
            ls.append(linea(OK, "hooks registrados", f"{' · '.join(eventos) or 'ninguno'} — todos "
                                                     f"existen y son ejecutables ({fuente})"))
        else:
            ls.append(linea(INFO, "hooks registrados", f"{' · '.join(eventos) or 'ninguno'} ({fuente})"))
        for msg in errs:
            rel = _rel_de(msg)
            ls.append(linea(ERROR, "hook sin script", msg,
                            f"falta `{rel}`: reinstala o actualiza el plugin (`claude plugin update "
                            f"custom-agents`); un hook roto es una pieza muerta"))
        for msg in warns:
            rel = _rel_de(msg)
            ls.append(linea(AVISO, "hook no ejecutable", msg,
                            f"`chmod +x {rel}` (y `git update-index --chmod=+x {rel}` si lo versionas)"))

    # --- statusline (informativo) ---
    spath = os.path.join(project, ".claude", "settings.json")
    datos, err = _leer_json(spath)
    if err:
        ls.append(linea(AVISO, "statusline", f".claude/settings.json {err}",
                        "corrige el JSON de `.claude/settings.json` (es tu fichero, no del plugin) o "
                        "relanza `/setup` paso 5-bis"))
    elif datos is None:
        ls.append(linea(INFO, "statusline", "sin `.claude/settings.json` — no configurada",
                        "opcional: `/setup` paso 5-bis la activa (progreso del roadmap + coste de sesión)"))
    else:
        sl = datos.get("statusLine") if isinstance(datos, dict) else None
        cmd = sl.get("command", "") if isinstance(sl, dict) else ""
        if not cmd:
            ls.append(linea(INFO, "statusline", "no configurada en `.claude/settings.json`",
                            "opcional: `/setup` paso 5-bis la activa"))
        elif "roadmap-statusline.sh" in cmd and not os.path.isfile(cmd.strip('"\' ')):
            ls.append(linea(AVISO, "statusline", f"apunta a `{cmd}`, que no existe",
                            "relanza `/setup` paso 5-bis: la ruta se escribe ABSOLUTA en el momento "
                            "del setup y se rompe al mover o reinstalar el plugin"))
        else:
            ls.append(linea(OK, "statusline", f"configurada (`{cmd}`)"))
    return {"clave": "plugin", "titulo": "Plugin", "lineas": ls}


# ------------------------------------------------------------------ c) configs del proyecto

def _rates(project):
    path = os.path.join(project, ".claude", "rates.json")
    datos, err = _leer_json(path)
    if err:
        return [linea(ERROR, "rates.json", err,
                      "recréalo desde `agent-kits/evaluator/templates/rates.example.json` o con "
                      "`/setup` paso 1 (sin él, evaluator y planner no pueden presupuestar)")]
    if datos is None:
        return [linea(INFO, "rates.json", "no configurado",
                      "`/setup` paso 1 lo crea (tarifa, jornada, ratio de supervisión, precio de tokens)")]
    if not isinstance(datos, dict):
        return [linea(ERROR, "rates.json", "la raíz no es un objeto JSON",
                      "recréalo con `/setup` paso 1")]
    pt = datos.get("precioTokens")
    if not isinstance(pt, dict):
        return [linea(AVISO, "rates.json", "válido, pero sin bloque `precioTokens`",
                      "ejecuta la skill `rates-verify`: sin precio, el coste en € de las evaluaciones "
                      "es incompleto")]
    verificado = any(k.startswith("verificado") and pt.get(k) for k in pt)
    a_cero = not pt.get("input") or not pt.get("output")
    if a_cero or not verificado:
        motivo = "precio a 0" if a_cero else "sin fecha de verificación"
        return [linea(AVISO, "rates.json", f"`precioTokens` a verificar ({motivo})",
                      "ejecuta la skill `rates-verify`: lee la doc oficial de precios y lo escribe con fecha")]
    fecha = next((pt[k] for k in pt if k.startswith("verificado") and pt.get(k)), "")
    return [linea(OK, "rates.json", f"válido · precio de tokens verificado el {fecha}")]


def _dev_valida(datos):
    """Líneas de vocabulario de dev.json: clave desconocida → ⚠️, valor inválido → ❌."""
    ls = []
    for k in sorted(datos):
        if k.startswith("_"):
            continue
        if k not in DEV_CLAVES:
            ls.append(linea(AVISO, f"dev.json `{k}`", "clave desconocida (se ignora)",
                            f"quítala o revísala: las claves válidas son {', '.join(sorted(DEV_CLAVES))} "
                            f"(regla 9 de `docs/CONVENTIONS.md`)"))
    for k in DEV_BOOLES:
        if k in datos and not isinstance(datos[k], bool):
            ls.append(linea(ERROR, f"dev.json `{k}`", f"{datos[k]!r} no es booleano",
                            f"pon `\"{k}\": true` o `\"{k}\": false` (o relanza `/setup` paso 5)"))
    g = datos.get("guardrails")
    if g is not None and not isinstance(g, bool):
        if not isinstance(g, dict):
            ls.append(linea(ERROR, "dev.json `guardrails`", f"{g!r} no es booleano ni objeto de reglas",
                            "pon `true`/`false` o `{\"alcance\": true, \"ramaPrincipal\": true, "
                            "\"git\": true}` (relanza `/setup` paso 5)"))
        else:
            for sk, sv in sorted(g.items()):
                if sk not in DEV_GUARDRAIL_REGLAS:
                    ls.append(linea(AVISO, f"dev.json `guardrails.{sk}`", "regla desconocida (se ignora)",
                                    f"reglas válidas: {', '.join(DEV_GUARDRAIL_REGLAS)}"))
                elif not isinstance(sv, bool):
                    ls.append(linea(ERROR, f"dev.json `guardrails.{sk}`", f"{sv!r} no es booleano",
                                    f"pon `\"{sk}\": true` o `false`"))
    rev = datos.get("revision")
    if rev is not None:
        if not isinstance(rev, dict):
            ls.append(linea(ERROR, "dev.json `revision`", f"{rev!r} no es un objeto",
                            "usa `{\"lenteSeguridad\": \"auto\", \"lenteRendimiento\": \"auto\"}` "
                            "(relanza `/setup` paso 5-ter)"))
        else:
            for sk in sorted(rev):
                sv = rev[sk]
                if sk in ("lenteSeguridad", "lenteRendimiento"):
                    if sv not in DEV_LENTES:
                        ls.append(linea(ERROR, f"dev.json `revision.{sk}`", f"{sv!r} fuera de vocabulario",
                                        f"valores esperados: {' · '.join(DEV_LENTES)} "
                                        f"(relanza `/setup` paso 5-ter)"))
                elif sk == "excluir":
                    if not isinstance(sv, list) or not all(isinstance(x, str) and x for x in sv):
                        ls.append(linea(ERROR, "dev.json `revision.excluir`", f"{sv!r} no es una lista de globs",
                                        "usa `[\"hooks/**\"]`: globs que se sacan de la heurística de RUTA "
                                        "de la lente (no del escaneo de contenido)"))
                else:
                    ls.append(linea(AVISO, f"dev.json `revision.{sk}`", "clave desconocida (se ignora)",
                                    "claves válidas: lenteSeguridad, lenteRendimiento, excluir"))
    ses = datos.get("sesion")
    if ses is not None:
        if not isinstance(ses, dict):
            ls.append(linea(ERROR, "dev.json `sesion`", f"{ses!r} no es un objeto",
                            "usa `{\"indice\": true, \"journal\": true}`"))
        else:
            for sk in sorted(ses):
                if sk not in DEV_SESION_CLAVES:
                    ls.append(linea(AVISO, f"dev.json `sesion.{sk}`", "clave desconocida (se ignora)",
                                    f"claves válidas: {', '.join(DEV_SESION_CLAVES)}"))
                elif not isinstance(ses[sk], bool):
                    ls.append(linea(ERROR, f"dev.json `sesion.{sk}`", f"{ses[sk]!r} no es booleano",
                                    f"pon `\"{sk}\": true` o `false`"))
    tests = datos.get("tests")
    if tests is not None:
        if not isinstance(tests, dict):
            ls.append(linea(ERROR, "dev.json `tests`", f"{tests!r} no es un objeto",
                            "usa `{\"coberturaMinima\": 80}` (o quita la clave: sin ella no hay gate)"))
        else:
            for sk in sorted(tests):
                sv = tests[sk]
                if sk != "coberturaMinima":
                    ls.append(linea(AVISO, f"dev.json `tests.{sk}`", "clave desconocida (se ignora)",
                                    "clave válida: coberturaMinima"))
                elif not isinstance(sv, int) or isinstance(sv, bool) or not 0 <= sv <= 100:
                    ls.append(linea(ERROR, "dev.json `tests.coberturaMinima`", f"{sv!r} no es un entero 0-100",
                                    "pon un entero entre 0 y 100 (p. ej. `80`) o quita la clave para no "
                                    "aplicar gate de cobertura"))
    return ls


def _modelos(datos, plugin_root, project):
    """`modelos` resuelto con el script determinista: sus avisos son los del doctor."""
    mods = datos.get("modelos")
    if mods is None:
        return []
    if not isinstance(mods, dict):
        return [linea(ERROR, "dev.json `modelos`", f"{mods!r} no es un objeto {{agente: {{model, effort}}}}",
                      "usa `{\"implementer\": {\"model\": \"opus\"}}` o quita la clave (ausente = "
                      "tiering del frontmatter)")]
    script = os.path.join(plugin_root or HERE, "agent-kits", "shared", "model-tier.py")
    if not os.path.isfile(script):
        script = os.path.join(HERE, "model-tier.py")
    if not os.path.isfile(script):
        return [linea(INFO, "dev.json `modelos`", f"{len(mods)} override(s) declarado(s); "
                                                  f"`model-tier.py` no está para resolverlos",
                      "instalación parcial: reinstala el plugin si quieres la tabla efectiva")]
    salida, _ok = _correr([sys.executable, script, "--all", "--json",
                           "--project", project] + (["--root", plugin_root] if plugin_root else []))
    d = _json_de(salida)
    if d is None:
        return [linea(AVISO, "dev.json `modelos`", "`model-tier.py --all --json` no devolvió JSON",
                      "ejecútalo a mano para ver el error: "
                      "`python3 agent-kits/shared/model-tier.py --all`")]
    ls = []
    for a in d.get("avisos", []):
        ls.append(linea(AVISO, "dev.json `modelos`", a,
                        "corrige el valor en `.claude/dev.json` (model ∈ haiku|sonnet|opus|inherit|"
                        "claude-… · effort ∈ low|medium|high|xhigh|max) o relanza `/setup` paso 5-quater"))
    aplicados = [f["agente"] for f in d.get("agentes", []) if f.get("fuente", {}).get("model") == "dev.json"]
    if not ls:
        ls.append(linea(OK, "dev.json `modelos`",
                        f"{len(mods)} override(s) · aplicados: {', '.join(aplicados) or 'ninguno'}"))
    return ls


def _dev(plugin_root, project):
    path = os.path.join(project, ".claude", "dev.json")
    datos, err = _leer_json(path)
    if err:
        return [linea(ERROR, "dev.json", err,
                      "recréalo con `/setup` (paso 5): mientras esté corrupto, la disciplina de "
                      "`/dev-cycle` (tdd, worktree, subagentes, lentes, modelos) se ignora entera")]
    if datos is None:
        return [linea(INFO, "dev.json", "no configurado",
                      "`/setup` paso 5 lo crea; sin él valen los defaults: sin TDD/worktree/subagentes, "
                      "guardrails activos, lente de seguridad `auto`, índice y journal de sesión activos")]
    if not isinstance(datos, dict):
        return [linea(ERROR, "dev.json", "la raíz no es un objeto JSON",
                      "recréalo con `/setup` (paso 5)")]
    ls = _dev_valida(datos)
    ls.extend(_modelos(datos, plugin_root, project))
    if not any(x["estado"] in (AVISO, ERROR) for x in ls):
        claves = [k for k in sorted(datos) if not k.startswith("_")]
        ls.insert(0, linea(OK, "dev.json", f"válido · {len(claves)} clave(s): {', '.join(claves) or '—'}"))
    return ls


def _optin(project, fichero, etiqueta, obligatorios, arreglo_alta):
    path = os.path.join(project, ".claude", fichero)
    datos, err = _leer_json(path)
    if err:
        return [linea(ERROR, fichero, err, f"recréalo o bórralo: {arreglo_alta}")]
    if datos is None:
        return [linea(INFO, fichero, f"no configurado — {etiqueta} desactivado",
                      f"opcional: {arreglo_alta}")]
    if not isinstance(datos, dict):
        return [linea(ERROR, fichero, "la raíz no es un objeto JSON", f"recréalo: {arreglo_alta}")]
    if datos.get("enabled") is not True:
        return [linea(INFO, fichero, f"`enabled: {datos.get('enabled')!r}` — {etiqueta} desactivado "
                                     f"a propósito", f"opcional: {arreglo_alta}")]
    faltan = [c for c in obligatorios if not datos.get(c)]
    if faltan:
        return [linea(AVISO, fichero, f"`enabled: true` pero faltan campos: {', '.join(faltan)}",
                      f"{arreglo_alta} (los rellena y persiste; hasta entonces la skill preguntará "
                      f"en cada uso)")]
    return [linea(OK, fichero, f"`enabled: true` · campos obligatorios presentes")]


def bloque_configs(plugin_root, project):
    ls = _rates(project) + _dev(plugin_root, project)
    ls += _optin(project, "jira.json", "volcado a Jira", JIRA_OBLIGATORIOS,
                 "`/setup` paso 3 o la skill `jira-sync`")
    ls += _optin(project, "confluence.json", "espejo en Confluence", CONFLUENCE_OBLIGATORIOS,
                 "`/setup` paso 2 o el alta guiada de la skill `confluence-publish`")
    return {"clave": "configs", "titulo": "Configs del proyecto (`.claude/`)", "lineas": ls}


# ------------------------------------------------------------------ d) estado

def _marcadores(plugin_root, project):
    state = os.path.join(project, ".claude", "usage-state.json")
    script = os.path.join(plugin_root or HERE, "agent-kits", "shared", "usage-meter.py")
    if not os.path.isfile(script):
        script = os.path.join(HERE, "usage-meter.py")
    d = None
    if os.path.isfile(script):
        d = _json_de(_correr([sys.executable, script, "status", "--state", state])[0])
    if d is None:                       # degradación: leer el estado directamente
        crudo, err = _leer_json(state)
        if err:
            return [linea(AVISO, "marcadores de medición", f"`usage-state.json` {err}",
                          "bórralo: es ESTADO, no config — los siguientes `usage-meter.py start` lo recrean")]
        d = {"marcadores": [{"artefacto": k, "cerrado": "ultimoCierre" in (v or {}), "horas_desde_inicio": None}
                            for k, v in (crudo or {}).items()]}
    abiertos = [m for m in d.get("marcadores", []) if not m.get("cerrado")]
    if not d.get("marcadores"):
        return [linea(INFO, "marcadores de medición", "sin marcadores abiertos ni cerrados")]
    if not abiertos:
        return [linea(OK, "marcadores de medición", f"{len(d['marcadores'])} marcador(es), todos cerrados")]
    out = []
    for m in abiertos:
        edad = m.get("horas_desde_inicio")
        det = f"`{m.get('artefacto')}` abierto" + (f" desde hace {edad} h" if edad is not None else "")
        out.append(linea(AVISO, "marcador huérfano", det,
                         f"ciérralo: `python3 agent-kits/shared/usage-meter.py close --artefacto "
                         f"{m.get('artefacto')}` (una ventana abierta reparte mal el coste del artefacto)"))
    return out


def _iniciativas(plugin_root, project):
    roadmap = os.path.join(project, "docs", "roadmap")
    if not os.path.isdir(roadmap):
        return [linea(INFO, "iniciativas", "sin `docs/roadmap/` en este proyecto",
                      "normal en un proyecto nuevo: `/pm-cycle <idea>` o `/dev-cycle <objetivo>` crea la primera")]
    script = os.path.join(plugin_root or HERE, "agent-kits", "shared", "progress-report.py")
    if not os.path.isfile(script):
        script = os.path.join(HERE, "progress-report.py")
    if not os.path.isfile(script):
        return [linea(INFO, "iniciativas", "`progress-report.py` no está para resumirlas",
                      "instalación parcial: reinstala el plugin")]
    d = _json_de(_correr([sys.executable, script, "active", "--root", roadmap, "--json"])[0])
    if d is None:
        return [linea(AVISO, "iniciativas", "`progress-report.py active` no devolvió JSON",
                      "ejecútalo a mano para ver el error: "
                      "`python3 agent-kits/shared/progress-report.py active --root docs/roadmap`")]
    activas = d.get("activas", [])
    if not activas:
        return [linea(INFO, "iniciativas", "ninguna `en-progreso`")]
    return [linea(INFO, "iniciativa en progreso", a.get("linea") or a.get("slug", "")) for a in activas]


def _journal(project):
    d = os.path.join(project, "docs", "knowledge", "journal")
    if not os.path.isdir(d):
        return [linea(INFO, "journal de sesión", "sin `docs/knowledge/journal/`",
                      "lo crea el hook `SessionEnd` al cerrar la primera sesión (opt-out: "
                      "`dev.json` `sesion.journal: false`)")]
    entradas = sorted(f for f in os.listdir(d) if f.endswith(".md") and f != "README.md")
    if not entradas:
        return [linea(INFO, "journal de sesión", "carpeta sin entradas todavía",
                      "la escribe el hook `SessionEnd` al cerrar la sesión")]
    return [linea(INFO, "journal de sesión", f"{len(entradas)} entrada(s) · última `{entradas[-1]}`")]


def _informes(project):
    d = os.path.join(project, "evals", "reports")
    if not os.path.isdir(d):
        return [linea(INFO, "informes de evals", "sin `evals/reports/`",
                      "opcional: `python3 evals/run.py` los escribe (cuesta tokens reales)")]
    informes = sorted(f for f in os.listdir(d) if f.endswith(".json"))
    if not informes:
        return [linea(INFO, "informes de evals", "sin informes",
                      "opcional: `python3 evals/run.py --target <pieza>` escribe `evals/reports/<fecha>.json`")]
    ultimo = informes[-1]
    m = re.match(r"(\d{4}-\d{2}-\d{2})", ultimo)
    fecha = m.group(1) if m else "fecha no legible en el nombre"
    return [linea(INFO, "informes de evals", f"{len(informes)} informe(s) · último `{ultimo}` ({fecha})")]


def bloque_estado(plugin_root, project):
    ls = _marcadores(plugin_root, project) + _iniciativas(plugin_root, project) \
        + _journal(project) + _informes(project)
    return {"clave": "estado", "titulo": "Estado del trabajo", "lineas": ls}


# ------------------------------------------------------------------ e) versión

AVISO_SIN_RED = ("sin red por diseño: `/doctor` NO consulta el marketplace, así que no puede "
                 "decirte si hay una versión más nueva")


def bloque_version(plugin_root, project):
    ls = []
    version = None
    datos, err = (_leer_json(os.path.join(plugin_root, ".claude-plugin", "plugin.json"))
                  if plugin_root else (None, "plugin no localizado"))
    if not plugin_root:
        ls.append(linea(INFO, "versión del plugin", "no legible: el plugin no está localizado",
                        "ver la línea ❌ del bloque Plugin; "
                        + AVISO_SIN_RED))
    elif err:
        ls.append(linea(ERROR, "plugin.json", err,
                        "restaura el fichero del plugin (`claude plugin update`): sin él Claude Code "
                        "no puede cargarlo"))
    else:
        version = (datos or {}).get("version") if isinstance(datos, dict) else None
        if not version:
            ls.append(linea(AVISO, "versión del plugin", "sin campo `version` en `.claude-plugin/plugin.json`",
                            "restaura el fichero del plugin o añade `\"version\": \"X.Y.Z\"`"))
        else:
            ls.append(linea(INFO, "versión del plugin", f"{version} — {AVISO_SIN_RED}"))

    seen_path = os.path.join(project, ".claude", ".plugin-version-seen")
    seen = ""
    if os.path.isfile(seen_path):
        try:
            seen = open(seen_path, encoding="utf-8-sig").read().strip()
        except OSError:
            seen = ""
    if not seen:
        ls.append(linea(INFO, "versión vista en este proyecto", "sin registro previo",
                        "opcional: `echo <version> > .claude/.plugin-version-seen` deja constancia de "
                        "con qué versión trabajaste (nadie lo escribe automáticamente hoy)"))
    elif version and seen != version:
        ls.append(linea(INFO, "versión vista en este proyecto",
                        f"la última vez que se vio este proyecto era {seen}; ahora hay {version}",
                        "solo es un registro local: revisa el CHANGELOG del plugin si te interesa qué "
                        "cambió entre esas dos versiones"))
    else:
        ls.append(linea(INFO, "versión vista en este proyecto", f"{seen} — igual que la actual"))
    return {"clave": "version", "titulo": "Versión", "lineas": ls}


# ------------------------------------------------------------------ informe

def diagnostico(project, plugin_root_explicito=None):
    plugin_root = localizar_plugin(plugin_root_explicito)
    bloques = [bloque_herramientas(),
               bloque_plugin(plugin_root, project, plugin_root_explicito),
               bloque_configs(plugin_root, project),
               bloque_estado(plugin_root, project),
               bloque_version(plugin_root, project)]
    resumen = {e: 0 for e in ORDEN}
    for b in bloques:
        for l in b["lineas"]:
            resumen[l["estado"]] = resumen.get(l["estado"], 0) + 1
    return {"proyecto": os.path.abspath(project),
            "plugin_root": plugin_root,
            "bloques": bloques,
            "resumen": resumen,
            "exit": 1 if resumen[ERROR] else 0}


def _celda(texto):
    return (texto or "—").replace("|", "\\|").replace("\n", " ").strip() or "—"


def render_md(inf):
    plug = f"`{inf['plugin_root']}`" if inf["plugin_root"] else "no localizado"
    out = ["# `/doctor` — diagnóstico de la instalación", "",
           f"**Proyecto**: `{inf['proyecto']}` · **Plugin**: {plug}", ""]
    for b in inf["bloques"]:
        out += [f"## {b['titulo']}", "", "| | Comprobación | Detalle | Arreglo sugerido |", "|---|---|---|---|"]
        for l in b["lineas"]:
            out.append(f"| {ICONO[l['estado']]} | {_celda(l['que'])} | {_celda(l['detalle'])} "
                       f"| {_celda(l['arreglo'])} |")
        out.append("")
    r = inf["resumen"]
    out += ["## Resumen", "",
            f"**{r[OK]} ✅ · {r[AVISO]} ⚠️ · {r[ERROR]} ❌ · {r[INFO]} ℹ️**", ""]
    if r[ERROR]:
        out.append(f"Hay {r[ERROR]} problema(s) que **rompen** algo del plugin: aplica el arreglo de "
                   f"cada línea ❌ y vuelve a pasar `/doctor` (exit 1).")
    elif r[AVISO]:
        out.append(f"Nada roto: {r[AVISO]} aviso(s) de cosas a medias que **degradan sin bloquear** "
                   f"(exit 0).")
    else:
        out.append("Instalación sana: nada roto ni a medias (exit 0).")
    out.append("")
    out.append("Las líneas ℹ️ son informativas (opcional no instalado, opt-in apagado, estado del "
               "trabajo): no hay nada que arreglar en ellas.")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description="diagnóstico determinista de la instalación del plugin")
    ap.add_argument("--root", default=".", help="proyecto a diagnosticar (default: cwd)")
    ap.add_argument("--plugin-root", default=None, help="raíz del plugin (default: autodetección)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    if not os.path.isdir(args.root):
        print(f"❌ uso: --root `{args.root}` no es un directorio", file=sys.stderr)
        return 2
    if args.plugin_root is not None and not os.path.isdir(args.plugin_root):
        print(f"❌ uso: --plugin-root `{args.plugin_root}` no es un directorio", file=sys.stderr)
        return 2

    inf = diagnostico(args.root, args.plugin_root)
    print(json.dumps(inf, ensure_ascii=False, indent=2) if args.json else render_md(inf))
    return inf["exit"]


if __name__ == "__main__":
    sys.exit(main())
