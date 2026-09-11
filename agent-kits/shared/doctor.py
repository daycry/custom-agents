#!/usr/bin/env python3
"""
doctor.py — diagnóstico DETERMINISTA y SIN EFECTOS de la instalación del plugin en un proyecto
(agent-kits/shared: lo invocan el comando `/doctor` y el paso 0 de `/setup`).

Seis bloques, un veredicto por línea (✅ ok · ⚠️ aviso · ❌ error · ℹ️ informativo) y, en TODA
línea ⚠️/❌, el **arreglo sugerido** en llano:

  a) herramientas  `python3` (≥ 3.9), `git`, `bash`, `jq` (opcional: la statusline lo usa con
                   fallback a `python3`), `node`/`npm` (opcional: skill `to-pdf`), Playwright
                   (opcional: agente `qa`; `~/.claude/tool-cache/qa/node_modules/@playwright`).
  b) plugin        raíz resuelta (`--plugin-root` → `CLAUDE_PLUGIN_ROOT` → padre de
                   `agent-kits/shared` → `find` sobre `$PWD/.claude` y `$HOME/.claude`); **cómo está
                   instalado** (`modo_instalacion`: `plugin` si la raíz cuelga de
                   `<CLAUDE_CONFIG_DIR>/plugins/cache/` o está en el registro, `copia` si la raíz es
                   un `.claude/` sin registro, `desconocido` en un checkout de desarrollo) y
                   **registro del plugin** (`installed_plugins.json` / `enabledPlugins` del scope:
                   dónde está dado de alta, ❌ si `enabledPlugins` lo tiene en `false`); hooks de
                   `hooks/hooks.json` (JSON válido; cada script existe → ❌ si no, y es ejecutable
                   → ⚠️ si no; reutiliza `lint_hook_commands` de `scripts/lint_plugin.py` si está,
                   comprobación local equivalente si no) — **en modo copia esa fila es ⚠️ pase lo que
                   pase**: Claude Code no lee `hooks/hooks.json` fuera de un plugin instalado, así que
                   el ✅ de antes era un falso positivo; statusline configurada o no (informativo).
  c) configs       `.claude/rates.json` (JSON válido; `precioTokens` a 0 o sin `verificado…` →
                   ⚠️ «a verificar» con la skill `rates-verify`), `.claude/dev.json` (JSON válido;
                   clave desconocida → ⚠️; valor fuera de vocabulario → ❌ con el valor esperado;
                   `modelos` resueltos con `model-tier.py --all --json` y sus avisos),
                   `.claude/jira.json` y `.claude/confluence.json` (si `enabled: true`, campos
                   obligatorios presentes; fichero ausente → «no configurado» informativo).
  d) estado        marcadores huérfanos de `usage-state.json` (`usage-meter.py status`), iniciativas
                   `en-progreso` (`progress-report.py active`) y último informe de `evals/reports/`.
  e) memoria       salud de la memoria técnica (memory-retrieval T-10 — hasta entonces `/doctor` daba
                   «Instalación sana» con 0 entradas de journal, sin contar las curadas ni validar nada):
                   entradas CURADAS de `docs/knowledge/{adr,gotchas,lessons}` por familia y por `estado`
                   (✅; carpeta vacía → ℹ️; sin carpeta → ℹ️ «un proyecto recién instalado nace sin
                   memoria»); índice `README.md` (biyección ficheros ↔ filas, enlaces y «Área» con
                   `lint_knowledge_index`, copia LITERAL —bloque `--8<--`, identidad con test— del criterio
                   de `scripts/lint_plugin.py`: el MISMO que el linter y `tests/test_knowledge_index.py`,
                   también si `plugin_root` resuelve a una copia instalada anterior) → ❌ nombrando fichero/ID; índice FTS5 `.claude/knowledge-index.sqlite` (caché de
                   `knowledge-find.py`: ℹ️ ausente o desfasado —se (re)construye en la próxima consulta—,
                   ⚠️ corrupto o `sqlite3` sin FTS5) — se LEE en modo `ro`, nunca se construye aquí;
                   journal (`docs/knowledge/journal/`): ⚠️ a 0 entradas CON memoria curada presente
                   (la episódica no se está escribiendo), ℹ️ en cualquier otro caso; y
                   `docs/roadmap/CALIBRATION.md`: ⚠️ si lleva > CALIBRACION_DIAS_MAX días sin fila y hay
                   iniciativas cerradas (`estado: completado`) después, diciendo cuántas y cuáles.
                   Solo ❌ el índice inválido; el resto son ⚠️ con su arreglo: si todo es rojo, la
                   gente lo ignora.
  f) versión       `version` de `plugin.json` frente a `.claude/.plugin-version-seen` si existe.
                   **SIN RED**: no consulta marketplace, GitHub ni npm, así que solo dice «versión X;
                   la última vez que se vio este proyecto era Y» (o «sin registro»). NUNCA afirma
                   que haya una actualización disponible — no tiene forma de saberlo.

**No escribe nada en el proyecto** (ni configs, ni estado, ni caché): es un diagnóstico de solo
lectura, así que se puede lanzar sin miedo tantas veces como haga falta.

Uso:
  doctor.py [--root DIR] [--plugin-root DIR] [--json] [--hoy AAAA-MM-DD]
  (`--hoy` fija la fecha de referencia de la antigüedad de CALIBRATION.md; default: hoy. Para tests.)
Exit:
  0  sin ❌ (los ⚠️/ℹ️ no bloquean: el plugin degrada, no rompe)
  1  al menos un ❌
  2  error de USO: `--root`/`--plugin-root` que no existen como directorio
"""
import argparse
import datetime
import json
import os
import re
import shutil
import subprocess
import sys

# Consola Windows (cp1252) o tuberías: reconfigurar ANTES de leer o imprimir nada (GOT-005).
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure, ya leído o None (capsys, pythonw)

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
DEV_SESION_CLAVES = ("indice", "journal", "memoria", "captura", "resumen")   # memoria: bloque (4) de session-context.sh (T-06);
                                                                              # captura/resumen: log crudo del turno y resumen por IA opt-in (memory-retrieval T-11/T-13)
DEV_CLAVES = set(DEV_BOOLES) | {"guardrails", "revision", "sesion", "modelos", "tests"}

JIRA_OBLIGATORIOS = ("cloudId", "granularidad", "assignee", "alCubrirJornada")
CONFLUENCE_OBLIGATORIOS = ("cloudId", "spaceKey", "anchor", "home")

PLAYWRIGHT_REL = os.path.join(".claude", "tool-cache", "qa", "node_modules", "@playwright")

# --- registro real del plugin en Claude Code (installer-registro-real T-05) ---------------
# Claude Code solo carga hooks, statusline y el namespace `/custom-agents:` de un plugin
# INSTALADO (registrado en `plugins/installed_plugins.json` + `enabledPlugins`). Un bundle
# copiado a `.claude/` tiene los mismos ficheros y ninguna de esas tres cosas: mirar solo que
# `hooks/hooks.json` exista daba un ✅ que no se correspondía con nada.
PLUGIN_NOMBRE = "custom-agents"
PLUGIN_PREFIJO = PLUGIN_NOMBRE + "@"
MARKETPLACE = "daycry"           # el marketplace que publica ESTE plugin
ADAPTADOR_OPENCODE = "custom-agents-hooks.js"   # el que registra `plugin` de `opencode.json`
ARREGLO_INSTALAR = ("npx @daycry/custom-agents install -p claude-code  (o, dentro de Claude Code, "
                    "`/plugin marketplace add daycry/custom-agents` + `/plugin install custom-agents`)")

# Scopes de plugin que Claude Code documenta (`claude plugin install|enable|disable --scope`) y
# el orden en que MANDAN. `enabledPlugins` se puede escribir en cualquier fichero de ajustes
# (`settings-reference#enabledplugins`: «Scope: Any file») y la pila de precedencia es la de
# `settings#settings-precedence`: «Managed > command line > Project local > Shared project > User».
# La línea de comandos no deja rastro en disco, así que no se puede diagnosticar; los otros cuatro
# niveles sí, y son los que se leen aquí.
SCOPES = ("user", "project", "local")
ORDEN_SCOPES = ("managed", "local", "project", "user")   # de más a menos mandón

# --- memoria técnica (memory-retrieval T-10) ---------------------------------------------
KNOWLEDGE_CARPETAS = (("adr", "ADR"), ("gotchas", "gotcha"), ("lessons", "lección"))
CALIBRACION_DIAS_MAX = 14        # días sin fila en CALIBRATION.md que, con iniciativas cerradas después, son ⚠️
FECHA_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")


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
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=TIMEOUT)
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

def _herramientas_basicas():
    """python3/git/bash: obligatorias (o casi) para que el plugin funcione."""
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
    return ls


def _herramientas_opcionales():
    """jq/node-npm/Playwright: opcionales, solo informan si faltan."""
    ls = []
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
    return ls


def bloque_herramientas():
    ls = _herramientas_basicas() + _herramientas_opcionales()
    return {"clave": "herramientas", "titulo": "Herramientas", "lineas": ls}


# ------------------------------------------------------------------ b) plugin

def _bloque_plugin_raiz(plugin_root, modo=None):
    """Línea OK con el recuento de agentes/skills/comandos de la raíz del plugin."""
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
    return [linea(OK, "raíz del plugin", f"{plugin_root} · {n['agentes']} agentes · "
                                         f"{n['skills']} skills · {n['comandos']} comandos"
                                         + (f" · instalación: {modo}" if modo else ""))]


def _bloque_plugin_hooks_recorrer(plugin_root, datos):
    """Recorre `hooks.hooks` y devuelve (eventos, errs, warns, fuente)."""
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
    return eventos, errs, warns, fuente


def _bloque_plugin_hooks_lineas(eventos, errs, warns, fuente, modo="plugin"):
    """Traduce el recuento de eventos/errores/avisos a líneas del informe.

    `modo` es el de `modo_instalacion()`: **en modo copia el ✅ no se puede dar**, por muy bien que
    esté `hooks/hooks.json`, porque Claude Code no lo lee fuera de un plugin instalado. Lo mismo
    en modo `inactivo`: registrado pero apagado (o caché sin alta) tampoco carga hooks.
    """
    ls = []
    if modo == "copia":
        ls.append(linea(AVISO, "hooks registrados",
                        f"{' · '.join(eventos) or 'ninguno'} declarados en `hooks/hooks.json`, pero el "
                        f"bundle está copiado a `.claude/`: Claude Code NO lee `hooks/hooks.json` fuera "
                        f"de un plugin — hooks, statusline y namespace no disponibles ({fuente})",
                        ARREGLO_INSTALAR))
    elif modo == "inactivo":
        ls.append(linea(AVISO, "hooks registrados",
                        f"{' · '.join(eventos) or 'ninguno'} declarados en `hooks/hooks.json`, pero el "
                        f"plugin NO está activo en el registro (ver «registro del plugin»): Claude Code "
                        f"no carga sus hooks ({fuente})",
                        "activa el plugin (`/plugin enable custom-agents@daycry` o `true` en "
                        "`enabledPlugins`); si no llegó a instalarse, " + ARREGLO_INSTALAR))
    elif not errs and not warns:
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
    return ls


def _bloque_plugin_hooks(plugin_root, modo="plugin"):
    """Líneas de `hooks/hooks.json`: registro global y sus scripts/permisos."""
    hpath = os.path.join(plugin_root, "hooks", "hooks.json")
    datos, err = _leer_json(hpath)
    if err:
        return [linea(ERROR, "hooks/hooks.json", err,
                      "restaura el fichero del plugin (`claude plugin update`) o corrige el JSON: "
                      "con él roto ningún hook informativo se registra")]
    if datos is None:
        return [linea(AVISO, "hooks/hooks.json", "no existe",
                      "instalación parcial: reinstala el plugin si esperabas los hooks de progreso "
                      "y de bitácora (el ciclo funciona sin ellos, sin avisos en vivo)")]
    if not isinstance(datos.get("hooks"), dict):
        return [linea(ERROR, "hooks/hooks.json", "falta la raíz `hooks` (objeto evento → grupos)",
                      "restaura el fichero del plugin: el registro de hooks es inválido tal cual está")]
    eventos, errs, warns, fuente = _bloque_plugin_hooks_recorrer(plugin_root, datos)
    return _bloque_plugin_hooks_lineas(eventos, errs, warns, fuente, modo)


def claude_config_dir():
    """Config de Claude Code: `CLAUDE_CONFIG_DIR` si está, `~/.claude` si no (igual que el
    instalador, `install/providers.mjs`)."""
    return os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")


def _entradas_plugin(datos, *claves):
    """Claves `custom-agents@<marketplace>` dentro de `datos[clave1][clave2]…`, con su valor."""
    cur = datos
    for k in claves:
        if not isinstance(cur, dict):
            return {}
        cur = cur.get(k)
    if not isinstance(cur, dict):
        return {}
    return {k: v for k, v in cur.items() if str(k).startswith(PLUGIN_PREFIJO)}


def clave_plugin(plugin_root=None, cfg=None):
    """Clave EXACTA del plugin diagnosticado (`custom-agents@<marketplace>`).

    Se deduce del caché cuando la raíz cuelga de `<cfg>/plugins/cache/<marketplace>/custom-agents/…`
    y, si no, es la del marketplace que publica este plugin. Importa porque un
    `custom-agents@<otro>` en el registro **no dice nada** de este: mirarlo era el falso positivo
    (y el falso negativo) de la primera versión.
    """
    cfg = cfg or claude_config_dir()
    if plugin_root:
        cache = os.path.abspath(os.path.join(cfg, "plugins", "cache"))
        raiz = os.path.abspath(plugin_root)
        if os.path.normcase(raiz).startswith(os.path.normcase(cache) + os.sep):
            partes = raiz[len(cache) + 1:].split(os.sep)
            if len(partes) >= 2 and partes[1] == PLUGIN_NOMBRE:
                return PLUGIN_NOMBRE + "@" + partes[0]
    return PLUGIN_PREFIJO + MARKETPLACE


def _ruta_real(p):
    """Ruta absoluta con los enlaces RESUELTOS (junction, `subst`, symlink), o la absoluta si no
    se puede resolver: la misma carpeta vista por dos nombres tiene que casar."""
    try:
        return os.path.realpath(os.path.abspath(p))
    except (OSError, ValueError):
        try:
            return os.path.abspath(p)
        except (OSError, ValueError):
            return ""


def _clave_ruta(p):
    """Identidad comparable de una ruta (para casar y para deduplicar)."""
    return os.path.normcase(_ruta_real(p)) if isinstance(p, str) and p else ""


def _misma_ruta(a, b):
    """¿Son la misma carpeta? Un valor que NO sea cadena (un `projectPath` con un número, una
    lista, `null`) no casa con nada y **no lanza**: un fichero del usuario mal formado no puede
    tumbar `/doctor` entero, que es justo cuando se usa. Igual que `mismaRuta` en `install.mjs`."""
    if not isinstance(a, str) or not isinstance(b, str) or not a or not b:
        return False
    return _clave_ruta(a) == _clave_ruta(b)


def _fuentes_instalados(path, clave, project):
    """Entradas de `installed_plugins.json` para `clave`, con el scope que ellas mismas declaran.

    Una entrada de scope `project` **o `local`** vale para SU proyecto (`projectPath`), no para
    cualquiera: un alta hecha desde otro repo no dice nada de esta raíz. Un `scope` que no sea
    ninguno de los tres documentados NO cuenta (antes caía a `user`, el lado permisivo: una
    entrada ajena valía para todos) y se avisa.
    """
    datos, _err = _leer_json(path)
    if not isinstance(datos, dict):
        return []
    nodo = datos.get("plugins")
    if not isinstance(nodo, dict) or clave not in nodo:
        return []
    entradas = nodo[clave]
    if isinstance(entradas, dict):
        entradas = [entradas]
    if not isinstance(entradas, list):
        return []
    fuentes = []
    for e in entradas:
        e = e if isinstance(e, dict) else {}
        bruto = e.get("scope")
        scope = bruto if bruto in SCOPES else None
        ruta_proj = e.get("projectPath")
        if scope is None:
            aplica, motivo = False, f"scope desconocido (`{bruto!r}`): no cuenta como alta"
        elif scope == "user":
            aplica, motivo = True, ""
        elif not isinstance(ruta_proj, str):
            # `projectPath` con un número, una lista o ausente: la entrada no se puede atribuir a
            # NINGUNA carpeta. Se descarta con aviso; antes `os.path.abspath()` lanzaba y el
            # informe entero se quedaba sin salir (exit 1 con stdout vacío).
            aplica = False
            motivo = (f"`projectPath` no es una cadena ({json.dumps(ruta_proj, default=str)}): "
                      f"la entrada no se puede atribuir a esta raíz")
        else:
            aplica = _misma_ruta(ruta_proj, project)
            motivo = "" if aplica else f"alta de otro proyecto ({ruta_proj})"
        fuentes.append({"fichero": path, "scope": scope or "desconocido", "scope_bruto": bruto,
                        "scope_desconocido": scope is None, "clave": clave,
                        "fuente": "installed_plugins.json", "habilitado": None, "valor": None,
                        "invalido": False, "aplica": aplica, "motivo": motivo})
    return fuentes


def _fuentes_enabled(path, scope, clave):
    """`enabledPlugins[clave]` de un `settings.json`.

    Solo `true` es alta; `false` es apagado explícito; **cualquier otro valor** (`0`, `null`,
    `"false"`) es un valor inválido: se avisa y no cuenta como alta.
    """
    datos, _err = _leer_json(path)
    if not isinstance(datos, dict):
        return []
    nodo = datos.get("enabledPlugins")
    if not isinstance(nodo, dict) or clave not in nodo:
        return []
    v = nodo[clave]
    valor = v if isinstance(v, bool) else None
    return [{"fichero": path, "scope": scope, "clave": clave, "fuente": "enabledPlugins",
             "habilitado": valor, "valor": valor, "invalido": not isinstance(v, bool),
             "bruto": v, "aplica": True, "motivo": ""}]


def managed_settings_path():
    """`managed-settings.json` de la plataforma (ajustes impuestos por la organización), o `""`.

    Rutas de `settings#settings-files`: `/Library/Application Support/ClaudeCode/` en macOS,
    `/etc/claude-code/` en Linux y WSL, `C:\\ProgramData\\ClaudeCode\\` en Windows. Está POR ENCIMA
    de todo lo demás en la pila de precedencia, así que si existe se lee; si el sistema no es
    ninguno de los tres (o la ruta no se puede resolver) se devuelve `""` y el diagnóstico sigue
    con los tres niveles de usuario, que es lo que hay.
    """
    if sys.platform == "darwin":
        cand = "/Library/Application Support/ClaudeCode/managed-settings.json"
    elif os.name == "nt":
        base = os.environ.get("PROGRAMDATA") or "C:\\ProgramData"
        cand = os.path.join(base, "ClaudeCode", "managed-settings.json")
    else:
        cand = "/etc/claude-code/managed-settings.json"
    try:
        return cand if os.path.isfile(cand) else ""
    except OSError:
        return ""


def _niveles_settings(project, cfg):
    """Los ficheros de ajustes que se leen, **de menos a más mandón**, ya deduplicados.

    `user` (`<cfg>/settings.json`) · `project` (`<proyecto>/.claude/settings.json`) · `local`
    (`<proyecto>/.claude/settings.local.json`, donde escribe `claude plugin disable --scope local`)
    · `managed` (el de la plataforma, si existe).

    Con `CLAUDE_CONFIG_DIR` apuntando al `.claude/` del proyecto, `user` y `project` son el MISMO
    fichero: se cuenta una vez, con el scope más específico (el informe listaba el mismo fichero
    dos veces, con dos scopes, como si fueran dos altas).
    """
    candidatos = [("user", os.path.join(cfg, "settings.json")),
                  ("project", os.path.join(project, ".claude", "settings.json")),
                  ("local", os.path.join(project, ".claude", "settings.local.json"))]
    gestionado = managed_settings_path()
    if gestionado:
        candidatos.append(("managed", gestionado))
    vistos = {}
    for scope, path in candidatos:
        clave = _clave_ruta(path) or path
        # El último gana el nombre: los candidatos van de menos a más específico, así que un
        # fichero compartido entre dos niveles se queda con el que más manda.
        vistos[clave] = (scope, path)
    return list(vistos.values())


def estado_plugin(plugin_root, project, cfg=None):
    """**Estado EFECTIVO** del plugin para ESTA raíz: la única definición de «está activo».

    Recorre TODAS las fuentes que Claude Code lee (no se para en la primera que acierta), se queda
    con las que aplican a esta raíz y resuelve con estas reglas:

    · solo cuenta la clave exacta del plugin diagnosticado (`clave_plugin`);
    · una entrada de `installed_plugins.json` cuenta si su scope es `user`, o si es `project` /
      `local` y su `projectPath` es esta raíz (un scope desconocido no cuenta);
    · `enabledPlugins` se lee en los CUATRO ficheros de la pila documentada
      (`settings-reference#enabledplugins`: «Scope: Any file») y manda el nivel más alto que se
      pronuncia, según `settings#settings-precedence` («Managed > command line > Project local >
      Shared project > User»): `managed` > `local` > `project` > `user`. Dentro de ese nivel, un
      `false` explícito gana a cualquier alta;
    · sin pronunciamiento explícito, un alta (entrada instalada) basta para estar activo.

    `settings.local.json` importa especialmente: es donde escribe `claude plugin disable --scope
    local` y no leerlo daba `modo: plugin` + hooks ✅ con el plugin apagado.

    Devuelve `{clave, habilitado, fuentes, aplican, mandan, apagadas, invalidas, ignoradas}`.
    `install.mjs status` resuelve lo mismo con las mismas reglas (`leerRegistro`): las dos
    herramientas tienen que dar el MISMO veredicto sobre el mismo estado.
    """
    cfg = cfg or claude_config_dir()
    clave = clave_plugin(plugin_root, cfg)
    fuentes = []
    fuentes += _fuentes_instalados(os.path.join(cfg, "plugins", "installed_plugins.json"), clave, project)
    for scope, path in _niveles_settings(project, cfg):
        fuentes += _fuentes_enabled(path, scope, clave)

    aplican = [f for f in fuentes if f["aplica"]]
    explicitas = [f for f in aplican if isinstance(f["valor"], bool)]
    mandan = []
    for nivel in ORDEN_SCOPES:
        mandan = [f for f in explicitas if f["scope"] == nivel]
        if mandan:
            break
    altas = [f for f in aplican if not f["invalido"] and f["valor"] is not False]
    habilitado = all(f["valor"] is True for f in mandan) if mandan else bool(altas)
    return {"clave": clave, "habilitado": habilitado, "fuentes": fuentes, "aplican": aplican,
            "mandan": mandan, "apagadas": [f for f in mandan if f["valor"] is False],
            "invalidas": [f for f in aplican if f["invalido"]],
            "ignoradas": [f for f in fuentes if not f["aplica"]],
            "desconocidas": [f for f in fuentes if f.get("scope_desconocido")]}


def registro_plugin(project, cfg=None, plugin_root=None):
    """Dónde está REGISTRADO el plugin, leyendo los ficheros que Claude Code lee de verdad.

    Devuelve la lista de fuentes que APLICAN a esta raíz — `{fichero, scope, clave, fuente,
    habilitado}` (`habilitado` es `None` cuando el fichero no expresa habilitación, como
    `installed_plugins.json`) — con el scope que declara cada entrada, no uno supuesto. Lista
    vacía = no está registrado para esta raíz, que es justo el caso que el ✅ de antes tapaba.
    """
    est = estado_plugin(plugin_root, project, cfg)
    return [{k: f[k] for k in ("fichero", "scope", "clave", "fuente", "habilitado")}
            for f in est["aplican"]]


def modo_instalacion(plugin_root, project, cfg=None):
    """`plugin` · `copia` · `inactivo` · `desconocido`, con la razón en llano.

    · `plugin`      — el **estado efectivo** está activo (`estado_plugin`): el runtime lo carga.
    · `copia`       — la raíz ES un `.claude/` (del proyecto o del usuario) y NO está activo:
                      el bundle está copiado y Claude Code no se entera (hooks, statusline y
                      namespace `/custom-agents:` no existen).
    · `inactivo`    — está instalado como plugin (la raíz cuelga de `plugins/cache/…`) o hay un
                      apagado explícito, pero el estado efectivo NO está activo: los hooks **no**
                      se cargan, así que la fila de hooks no puede salir en ✅.
    · `desconocido` — ni una cosa ni la otra (checkout de desarrollo, `--plugin-root` a mano).
    """
    cfg = cfg or claude_config_dir()
    est = estado_plugin(plugin_root, project, cfg)
    hits = [{k: f[k] for k in ("fichero", "scope", "clave", "fuente", "habilitado")}
            for f in est["aplican"]]
    raiz = os.path.normcase(os.path.abspath(plugin_root)) if plugin_root else ""
    cache = os.path.normcase(os.path.abspath(os.path.join(cfg, "plugins", "cache")))
    en_cache = bool(raiz) and (raiz == cache or raiz.startswith(cache + os.sep))
    base = {"registro": hits, "estado": est}
    if est["habilitado"]:
        razon = ("la raíz cuelga de `plugins/cache/` y el registro lo da por activo" if en_cache
                 else "el plugin está activo en el registro de Claude Code")
        return dict(base, modo="plugin", razon=razon)
    copias = {os.path.normcase(os.path.abspath(os.path.join(project, ".claude"))),
              os.path.normcase(os.path.abspath(cfg))}
    if raiz in copias or os.path.basename(raiz) == ".claude":
        return dict(base, modo="copia", razon="la raíz es un `.claude/` sin registro activo")
    if en_cache or est["apagadas"]:
        return dict(base, modo="inactivo",
                    razon=("el plugin está en el registro pero APAGADO" if est["apagadas"]
                           else "la raíz cuelga de `plugins/cache/` sin entrada que lo active"))
    return dict(base, modo="desconocido",
                razon="la raíz no es ni una copia en `.claude/` ni el caché de plugins")


def _bloque_plugin_registro(info, cfg):
    """Fila «registro del plugin»: dónde está dado de alta PARA ESTA RAÍZ, o por qué no carga."""
    est = info["estado"]
    ls = []
    if est["apagadas"]:
        h = est["apagadas"][0]
        ls.append(linea(ERROR, "registro del plugin",
                        f"manda `{h['fichero']}` (scope {h['scope']}, el de mayor precedencia que se "
                        f"pronuncia): ahí `{h['clave']}` está en `enabledPlugins` como `false`, así que "
                        f"Claude Code lo ignora entero",
                        f"ponlo a `true` en {h['fichero']} o `claude plugin enable {h['clave']} "
                        f"--scope {h['scope']}`"))
    elif est["habilitado"]:
        donde = " · ".join(f"{h['clave']} en {h['fichero']} ({h['fuente']}, scope {h['scope']})"
                           for h in est["aplican"] if h["valor"] is not False)
        # Cuál de todos MANDA, no solo el veredicto: con cuatro niveles de ajustes
        # (`managed` > `local` > `project` > `user`), saber dónde tocar es media respuesta.
        if est["mandan"]:
            m = est["mandan"][0]
            donde += f" — manda `{m['fichero']}` (scope {m['scope']})"
        ls.append(linea(OK, "registro del plugin", donde))
    elif info["modo"] == "inactivo":
        ls.append(linea(AVISO, "registro del plugin",
                        f"sin entrada de `{est['clave']}` que lo active en `installed_plugins.json` ni en "
                        f"`enabledPlugins` de {cfg}, con la raíz colgando de "
                        f"`{os.path.join(cfg, 'plugins', 'cache')}`: caché de una instalación a medias",
                        ARREGLO_INSTALAR))
    elif info["modo"] == "copia":
        ls.append(linea(AVISO, "registro del plugin",
                        f"sin entrada de `{est['clave']}` en {cfg} — el bundle está copiado, no instalado",
                        ARREGLO_INSTALAR))
    else:
        ls.append(linea(INFO, "registro del plugin",
                        f"sin entrada de `{est['clave']}` en {cfg}; {info['razon']} (checkout de desarrollo "
                        f"o `--plugin-root`): aquí el registro no dice nada"))
    for h in est["invalidas"]:
        ls.append(linea(AVISO, "registro con valor inválido",
                        f"`{h['clave']}` vale `{json.dumps(h.get('bruto'))}` en `enabledPlugins` de "
                        f"{h['fichero']} (scope {h['scope']}): solo `true` habilita, así que no cuenta "
                        f"como alta",
                        f"pon `true` (o quita la clave) en `enabledPlugins` de {h['fichero']}"))
    # Entradas de `installed_plugins.json` que NO se pueden atribuir: se dicen en vez de caer al
    # lado permisivo (un `scope` raro contando como `user` valía para todos los proyectos).
    raras = [h for h in est.get("desconocidas", [])]
    if raras:
        ls.append(linea(AVISO, "registro con scope desconocido",
                        " · ".join(f"`{est['clave']}` en {h['fichero']} declara "
                                   f"`scope: {json.dumps(h.get('scope_bruto'), default=str)}`, que no es "
                                   f"`user`, `project` ni `local`: no cuenta como alta"
                                   for h in raras),
                        f"reinstala con `npx @daycry/custom-agents install -p claude-code` o corrige el "
                        f"`scope` de esa entrada en `installed_plugins.json`"))
    sin_ruta = [h for h in est["ignoradas"] if "no es una cadena" in h["motivo"]]
    if sin_ruta:
        ls.append(linea(AVISO, "registro sin proyecto atribuible",
                        " · ".join(f"{h['fichero']}: {h['motivo']}" for h in sin_ruta),
                        "reinstala con `npx @daycry/custom-agents install -p claude-code` (reescribe la "
                        "entrada con el `projectPath` de esta carpeta)"))
    return ls

def _codex_home():
    """`CODEX_HOME` si está, `~/.codex` si no (lo mismo que lee el instalador)."""
    return os.environ.get("CODEX_HOME") or os.path.join(os.path.expanduser("~"), ".codex")


def _opencode_home():
    """Config global de OpenCode: `~/.config/opencode` (no `~/.opencode`), igual que el instalador."""
    return os.path.join(os.path.expanduser("~"), ".config", "opencode")


def _toml_habilitado(path, clave):
    """¿`plugins."<clave>".enabled` es `true` en ese `config.toml`?

    Devuelve `(valor, error)`: `valor` es `True`/`False`/`None` (sin entrada) y `error` explica por
    qué no se pudo mirar. Se parsea con `tomllib` (3.11+), que acepta las cinco formas de escribir
    la tabla; sin él se dice y no se adivina.
    """
    if not os.path.isfile(path):
        return None, ""
    try:
        import tomllib
    except ImportError:
        return None, "sin `tomllib` (Python < 3.11): no puedo leer `config.toml`"
    try:
        with open(path, "rb") as fh:
            datos = tomllib.load(fh)
    except (OSError, ValueError) as e:
        return None, f"`config.toml` ilegible ({type(e).__name__})"
    nodo = datos.get("plugins")
    if not isinstance(nodo, dict) or not isinstance(nodo.get(clave), dict):
        return None, ""
    v = nodo[clave].get("enabled")
    return (v if isinstance(v, bool) else None), ("" if isinstance(v, bool) or v is None
                                                  else f"`enabled` vale `{v!r}`, que no es un booleano")


def _bloque_registro_codex(project, clave_cc):
    """Fila «registro en Codex»: `enabled = true` en el `config.toml` del scope, que es lo único
    que hace que Codex cargue el plugin (copiar sus ficheros no basta). Mismo criterio que
    `install.mjs status`.

    Se miran DOS claves: la que escribe siempre el instalador (`PLUGIN_ID` de
    `install/providers.mjs`, `custom-agents@daycry`) y la que se dedujo de la raíz de Claude Code,
    que con un fork es otra. Mirar solo la segunda hacía buscar en el `config.toml` una clave que
    el instalador nunca escribe; la fila dice cuál encontró.
    """
    claves = list(dict.fromkeys([PLUGIN_PREFIJO + MARKETPLACE, clave_cc]))
    fuentes = [(os.path.join(_codex_home(), "config.toml"), "user", _codex_home()),
               (os.path.join(project, ".codex", "config.toml"), "project", os.path.join(project, ".codex"))]
    detectados = [base for _p, _s, base in fuentes if os.path.isdir(base)]
    activos, apagados, errores = [], [], []
    copiado = [base for _p, _s, base in fuentes
               if os.path.isdir(os.path.join(base, "plugins", PLUGIN_NOMBRE))]
    for path, scope, _base in fuentes:
        for clave in claves:
            valor, err = _toml_habilitado(path, clave)
            if err:
                errores.append(f"{path}: {err}")
            if valor is True:
                activos.append((path, scope, clave))
            elif valor is False:
                apagados.append((path, scope, clave))
    if activos:
        return [linea(OK, "registro en Codex",
                      " · ".join(f"`{c}` con `enabled = true` en {p} (scope {s})"
                                 for p, s, c in activos))]
    if apagados:
        p, s, c = apagados[0]
        return [linea(AVISO, "registro en Codex",
                      f"`{c}` está en {p} (scope {s}) con `enabled = false`: Codex no lo carga",
                      f"pon `enabled = true` en `[plugins.\"{c}\"]` de {p} o reinstala con "
                      f"`npx @daycry/custom-agents install -p codex`")]
    if errores:
        return [linea(AVISO, "registro en Codex", " · ".join(dict.fromkeys(errores)),
                      "usa Python 3.11+ para este diagnóstico, o mira a mano `[plugins."
                      f"\"{claves[0]}\"] enabled` en tu `config.toml`")]
    if copiado:
        return [linea(AVISO, "registro en Codex",
                      f"los ficheros del plugin están en {os.path.join(copiado[0], 'plugins', PLUGIN_NOMBRE)} "
                      f"pero `{claves[0]}` no está habilitado en ningún `config.toml`: Codex no lo carga",
                      "npx @daycry/custom-agents install -p codex  (escribe `enabled = true` en tu `config.toml`)")]
    if detectados:
        # Lo DETECTADO, no `CODEX_HOME` a secas: lo que hay puede ser solo el `.codex` del proyecto
        # (y el `~/.codex` que se nombraba antes, no existir).
        return [linea(INFO, "registro en Codex",
                      f"Codex está en esta máquina ({' · '.join(detectados)}) y el plugin no está "
                      f"instalado ahí — opcional: `npx @daycry/custom-agents install -p codex`")]
    return [linea(INFO, "registro en Codex", "Codex no está en esta máquina: nada que comprobar")]


def _resolver_spec_opencode(spec, cfg_path):
    """Ruta a la que apunta un spec de `plugin`. **Un spec con forma de ruta se resuelve contra la
    carpeta del fichero de config que lo declara** (`config/plugin.ts`, `resolvePluginSpec`), que
    es justo lo que escribe el instalador (`rutaPluginOpencode`)."""
    if not isinstance(spec, str) or not spec:
        return ""
    ruta = spec.replace("\\", "/")
    if os.path.isabs(ruta):
        return ruta
    return os.path.join(os.path.dirname(cfg_path), ruta)


def _bloque_registro_opencode(project):
    """Fila «registro en OpenCode»: el adaptador de hooks dado de alta en `plugin` de
    `opencode.json` (OpenCode también autodescubre `plugins/*.js`; el alta es lo comprobable).

    Se compara la RUTA RESUELTA contra la que escribe el instalador, no el nombre del fichero:
    casar por basename daba ✅ a cualquier `custom-agents-hooks.js` de cualquier sitio, y `status`
    —que compara la ruta exacta— decía lo contrario sobre el MISMO `opencode.json`.
    """
    fuentes = [(os.path.join(_opencode_home(), "opencode.json"), "user", _opencode_home()),
               (os.path.join(project, "opencode.json"), "project", os.path.join(project, ".opencode"))]
    detectados = [base for _p, _s, base in fuentes if os.path.isdir(base)]
    altas, ajenas, copiado, errores = [], [], [], []
    for path, scope, base in fuentes:
        esperado = os.path.join(base, "plugins", ADAPTADOR_OPENCODE)
        if os.path.isfile(esperado):
            copiado.append(base)
        datos, err = _leer_json(path)
        if err:
            # Ilegible no es ausente: «reinstala» no arregla un JSON roto del usuario (el gemelo
            # de Codex ya lo distinguía).
            errores.append(f"{path} {err}")
            continue
        if not isinstance(datos, dict):
            continue
        nodo = datos.get("plugin")
        if nodo is not None and not isinstance(nodo, list):
            # `status` solo cuenta una lista (descriptor `json-array`): un escalar no es el alta.
            errores.append(f"{path}: `plugin` no es una lista, así que el alta no se puede comprobar")
            continue
        for e in (nodo or []):
            if _misma_ruta(_resolver_spec_opencode(e, path), esperado):
                altas.append((path, scope, e))
            elif isinstance(e, str) and os.path.basename(e.replace("\\", "/")) == ADAPTADOR_OPENCODE:
                ajenas.append((path, scope, e, esperado))
    if altas:
        return [linea(OK, "registro en OpenCode",
                      " · ".join(f"`{e}` en `plugin` de {p} (scope {s})" for p, s, e in altas))]
    if errores:
        return [linea(AVISO, "registro en OpenCode", " · ".join(errores),
                      "corrige tu `opencode.json` (es tuyo, no del plugin): tiene que ser JSON válido "
                      "y `plugin`, una lista de specs")]
    if ajenas:
        p, s, e, esperado = ajenas[0]
        return [linea(AVISO, "registro en OpenCode",
                      f"`plugin` de {p} (scope {s}) declara `{e}`, que resuelve a "
                      f"{_resolver_spec_opencode(e, p)} y NO es el adaptador instalado ({esperado}): "
                      f"OpenCode carga otro fichero, o ninguno",
                      "npx @daycry/custom-agents install -p opencode  (deja en `plugin` la ruta del "
                      "adaptador que instala)")]
    if copiado:
        return [linea(AVISO, "registro en OpenCode",
                      f"el adaptador está en {os.path.join(copiado[0], 'plugins', ADAPTADOR_OPENCODE)} pero "
                      f"no aparece en `plugin` de ningún `opencode.json`: el alta comprobable no está",
                      "npx @daycry/custom-agents install -p opencode  (añade el adaptador a `plugin` "
                      "de tu `opencode.json`)")]
    if detectados:
        return [linea(INFO, "registro en OpenCode",
                      f"OpenCode está en esta máquina ({' · '.join(detectados)}) y el plugin no está "
                      f"instalado ahí — opcional: `npx @daycry/custom-agents install -p opencode`")]
    return [linea(INFO, "registro en OpenCode", "OpenCode no está en esta máquina: nada que comprobar")]


def _bloque_plugin_statusline(project):
    """Líneas informativas de la statusline configurada en `.claude/settings.json`."""
    spath = os.path.join(project, ".claude", "settings.json")
    datos, err = _leer_json(spath)
    if err:
        return [linea(AVISO, "statusline", f".claude/settings.json {err}",
                      "corrige el JSON de `.claude/settings.json` (es tu fichero, no del plugin) o "
                      "relanza `/setup` paso 5-bis")]
    if datos is None:
        return [linea(INFO, "statusline", "sin `.claude/settings.json` — no configurada",
                      "opcional: `/setup` paso 5-bis la activa (progreso del roadmap + coste de sesión)")]
    sl = datos.get("statusLine") if isinstance(datos, dict) else None
    cmd = sl.get("command", "") if isinstance(sl, dict) else ""
    if not cmd:
        return [linea(INFO, "statusline", "no configurada en `.claude/settings.json`",
                      "opcional: `/setup` paso 5-bis la activa")]
    if "roadmap-statusline.sh" in cmd and not os.path.isfile(cmd.strip('"\' ')):
        return [linea(AVISO, "statusline", f"apunta a `{cmd}`, que no existe",
                      "relanza `/setup` paso 5-bis: la ruta se escribe ABSOLUTA en el momento "
                      "del setup y se rompe al mover o reinstalar el plugin")]
    return [linea(OK, "statusline", f"configurada (`{cmd}`)")]


def bloque_plugin(plugin_root, project, explicito=None):
    ls = []
    if not plugin_root:
        que = "raíz del plugin"
        det = (f"`--plugin-root {explicito}` no contiene el plugin (falta `agents/` y `skills/`)"
               if explicito else "no localizada")
        ls.append(linea(ERROR, que, det,
                        "instálalo como plugin (`/plugin marketplace add …` + `/plugin install custom-agents`) "
                        "o pásame la ruta con `--plugin-root <dir>`"))
        # La forma del bloque es la MISMA con y sin raíz: quien lea `--json` no tiene que adivinar
        # si las claves están (gap B-6). Sin raíz no hay nada que resolver: `desconocido` y sin fuentes.
        return {"clave": "plugin", "titulo": "Plugin", "lineas": ls,
                "modo": "desconocido", "registro": []}

    cfg = claude_config_dir()
    info = modo_instalacion(plugin_root, project, cfg)
    ls.extend(_bloque_plugin_raiz(plugin_root, info["modo"]))
    ls.extend(_bloque_plugin_registro(info, cfg))
    ls.extend(_bloque_registro_codex(project, info["estado"]["clave"]))
    ls.extend(_bloque_registro_opencode(project))
    ls.extend(_bloque_plugin_hooks(plugin_root, info["modo"]))
    ls.extend(_bloque_plugin_statusline(project))
    return {"clave": "plugin", "titulo": "Plugin", "lineas": ls, "modo": info["modo"],
            "registro": info["registro"]}


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


def _dev_valida_guardrails(g):
    """Líneas de `guardrails` (booleano global u objeto de reglas)."""
    ls = []
    if g is None or isinstance(g, bool):
        return ls
    if not isinstance(g, dict):
        ls.append(linea(ERROR, "dev.json `guardrails`", f"{g!r} no es booleano ni objeto de reglas",
                        "pon `true`/`false` o `{\"alcance\": true, \"ramaPrincipal\": true, "
                        "\"git\": true}` (relanza `/setup` paso 5)"))
        return ls
    for sk, sv in sorted(g.items()):
        if sk not in DEV_GUARDRAIL_REGLAS:
            ls.append(linea(AVISO, f"dev.json `guardrails.{sk}`", "regla desconocida (se ignora)",
                            f"reglas válidas: {', '.join(DEV_GUARDRAIL_REGLAS)}"))
        elif not isinstance(sv, bool):
            ls.append(linea(ERROR, f"dev.json `guardrails.{sk}`", f"{sv!r} no es booleano",
                            f"pon `\"{sk}\": true` o `false`"))
    return ls


def _dev_valida_revision(rev):
    """Líneas de `revision` (lentes de la revisión adversarial y exclusiones)."""
    ls = []
    if rev is None:
        return ls
    if not isinstance(rev, dict):
        ls.append(linea(ERROR, "dev.json `revision`", f"{rev!r} no es un objeto",
                        "usa `{\"lenteSeguridad\": \"auto\", \"lenteRendimiento\": \"auto\"}` "
                        "(relanza `/setup` paso 5-ter)"))
        return ls
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
    return ls


def _dev_valida_sesion(ses):
    """Líneas de `sesion` (índice, journal, memoria, captura, resumen)."""
    ls = []
    if ses is None:
        return ls
    if not isinstance(ses, dict):
        ls.append(linea(ERROR, "dev.json `sesion`", f"{ses!r} no es un objeto",
                        "usa `{\"indice\": true, \"journal\": true, \"memoria\": true, \"captura\": true, \"resumen\": false}`"))
        return ls
    for sk in sorted(ses):
        if sk not in DEV_SESION_CLAVES:
            ls.append(linea(AVISO, f"dev.json `sesion.{sk}`", "clave desconocida (se ignora)",
                            f"claves válidas: {', '.join(DEV_SESION_CLAVES)}"))
        elif not isinstance(ses[sk], bool):
            ls.append(linea(ERROR, f"dev.json `sesion.{sk}`", f"{ses[sk]!r} no es booleano",
                            f"pon `\"{sk}\": true` o `false`"))
    return ls


def _dev_valida_tests(tests):
    """Líneas de `tests` (gate de cobertura)."""
    ls = []
    if tests is None:
        return ls
    if not isinstance(tests, dict):
        ls.append(linea(ERROR, "dev.json `tests`", f"{tests!r} no es un objeto",
                        "usa `{\"coberturaMinima\": 80}` (o quita la clave: sin ella no hay gate)"))
        return ls
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
    ls.extend(_dev_valida_guardrails(datos.get("guardrails")))
    ls.extend(_dev_valida_revision(datos.get("revision")))
    ls.extend(_dev_valida_sesion(datos.get("sesion")))
    ls.extend(_dev_valida_tests(datos.get("tests")))
    return ls


def _modelos_localizar_script(plugin_root):
    """Ruta a `model-tier.py` (junto al plugin o junto a este propio doctor.py), o None."""
    script = os.path.join(plugin_root or HERE, "agent-kits", "shared", "model-tier.py")
    if not os.path.isfile(script):
        script = os.path.join(HERE, "model-tier.py")
    return script if os.path.isfile(script) else None


def _modelos_lineas_de_json(d, mods):
    """Líneas a partir del JSON de `model-tier.py --all --json` ya parseado."""
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


def _modelos(datos, plugin_root, project):
    """`modelos` resuelto con el script determinista: sus avisos son los del doctor."""
    mods = datos.get("modelos")
    if mods is None:
        return []
    if not isinstance(mods, dict):
        return [linea(ERROR, "dev.json `modelos`", f"{mods!r} no es un objeto {{agente: {{model, effort}}}}",
                      "usa `{\"implementer\": {\"model\": \"opus\"}}` o quita la clave (ausente = "
                      "tiering del frontmatter)")]
    script = _modelos_localizar_script(plugin_root)
    if script is None:
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
    return _modelos_lineas_de_json(d, mods)


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
                      "guardrails activos, lente de seguridad `auto`, índice, journal y memoria de sesión activos")]
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


def _journal(project, n_curadas=0):
    """Journal (memoria EPISÓDICA). A 0 entradas CON memoria curada presente es ⚠️: la bitácora que
    prometía `memory-health` no se está escribiendo (medido en el análisis de `memory-retrieval`: 0
    entradas desde que se construyó). Sin memoria curada, ℹ️: un proyecto nuevo no está roto."""
    d = os.path.join(project, "docs", "knowledge", "journal")
    entradas = sorted(f for f in os.listdir(d) if f.endswith(".md") and f != "README.md") if os.path.isdir(d) else []
    if entradas:
        return [linea(INFO, "journal de sesión", f"{len(entradas)} entrada(s) · última `{entradas[-1]}`")]
    if n_curadas:
        return [linea(AVISO, "journal de sesión",
                      f"0 entradas con {n_curadas} entrada(s) curada(s): la memoria episódica no se está escribiendo"
                      + ("" if os.path.isdir(d) else " (ni existe `docs/knowledge/journal/`)"),
                      "comprueba que el hook `SessionEnd` está registrado (bloque Plugin de este informe) y que "
                      "`dev.json` no trae `sesion.journal: false`; la primera sesión cerrada con el plugin cargado "
                      "escribe la entrada (`hooks/session-journal.sh` → `journal.py write`)")]
    if not os.path.isdir(d):
        return [linea(INFO, "journal de sesión", "sin `docs/knowledge/journal/`",
                      "lo crea el hook `SessionEnd` al cerrar la primera sesión (opt-out: "
                      "`dev.json` `sesion.journal: false`)")]
    return [linea(INFO, "journal de sesión", "carpeta sin entradas todavía",
                  "la escribe el hook `SessionEnd` al cerrar la sesión")]


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
    ls = _marcadores(plugin_root, project) + _iniciativas(plugin_root, project) + _informes(project)
    return {"clave": "estado", "titulo": "Estado del trabajo", "lineas": ls}


# ------------------------------------------------------------------ e) memoria técnica (memory-retrieval T-10)

# --8<-- celdas de tabla Markdown COMPARTIDAS — REPLICADO LITERAL en scripts/lint_plugin.py,
# agent-kits/shared/knowledge-find.py y agent-kits/shared/doctor.py (los scripts son standalone: el paquete
# portable los copia sueltos, sin import común); tests/test_knowledge_index.py compara las copias byte a byte.
def celdas_md(fila):
    """Celdas de una fila `| a | b |` respetando `|` dentro de acentos graves."""
    out, actual, en_codigo = [], [], False
    for ch in fila.strip():
        if ch == "`":
            en_codigo = not en_codigo
        if ch == "|" and not en_codigo:
            out.append("".join(actual).strip())
            actual = []
        else:
            actual.append(ch)
    out.append("".join(actual).strip())
    if out and out[0] == "":
        out = out[1:]
    if out and out[-1] == "":
        out = out[:-1]
    return out
# --8<-- fin de celdas de tabla Markdown COMPARTIDAS


# --8<-- criterio del índice de knowledge COMPARTIDO (memory-retrieval T-04) — REPLICADO LITERAL en
# agent-kits/shared/doctor.py (la comprobación de /doctor es ESTE criterio, no una aproximación: antes tenía
# una local «equivalente» que dejaba pasar una fila hacia un fichero inexistente — revisión intento 1, gap 6);
# tests/test_knowledge_index.py compara las dos copias byte a byte. Necesita `celdas_md` (bloque de arriba).
KNOWLEDGE_INDICE_CARPETAS = ("adr", "gotchas", "lessons")


def filas_knowledge_index(texto):
    """(filas DENTRO de la tabla del índice, líneas con forma de fila que quedaron FUERA).

    La tabla es el bloque CONTIGUO de líneas `|` desde la cabecera `| Entrada |`; una línea en blanco la
    cierra (mismo criterio que `tabla_y_cola` en tests/test_roadmap_index.py). Cada fila →
    {linea (1-based), ruta (relativa a docs/knowledge, del enlace), id, area, celdas}.
    """
    lineas = texto.split("\n")
    ini = next((i for i, l in enumerate(lineas) if l.startswith("| Entrada |")), None)
    if ini is None:
        return [], []
    fin = ini
    while fin < len(lineas) and lineas[fin].startswith("|"):
        fin += 1

    def fila(n):
        c = celdas_md(lineas[n])
        entrada = re.sub(r"<!--.*?-->", "", c[0] if c else "")
        m = re.search(r"\]\(([^)\s]+)\)", entrada)
        return {"linea": n + 1, "ruta": m.group(1) if m else "", "id": c[1] if len(c) > 1 else "",
                "area": c[3] if len(c) > 3 else "", "celdas": c}

    dentro = [fila(n) for n in range(ini + 2, fin)]
    fuera = [fila(n) for n in range(fin, len(lineas)) if lineas[n].startswith("|") and len(celdas_md(lineas[n])) >= 3]
    return dentro, fuera


def lint_knowledge_index(root):
    """ERRORES del índice `docs/knowledge/README.md` (regla 10). [] si el proyecto no tiene `docs/knowledge/`."""
    base = os.path.join(root, "docs", "knowledge")
    if not os.path.isdir(base):
        return []
    ficheros = []
    for c in KNOWLEDGE_INDICE_CARPETAS:
        d = os.path.join(base, c)
        if os.path.isdir(d):
            ficheros += [f"{c}/{f}" for f in sorted(os.listdir(d)) if f.endswith(".md") and f.lower() != "readme.md"]
    indice = os.path.join(base, "README.md")
    if not os.path.isfile(indice):
        return [f"docs/knowledge/README.md: no existe y hay {len(ficheros)} entrada(s) en adr/, gotchas/, lessons/ — "
                f"sin índice ninguna es alcanzable (es el único camino de lectura)"] if ficheros else []
    try:
        texto = open(indice, encoding="utf-8-sig").read()
    except (OSError, UnicodeDecodeError) as e:
        return [f"docs/knowledge/README.md: no se puede leer ({e})"]
    dentro, fuera = filas_knowledge_index(texto)
    errs = []
    if not dentro and not fuera:
        return [f"docs/knowledge/README.md: no encuentro la tabla del índice (cabecera `| Entrada | ID | Tipo | Área | …`) "
                f"y hay {len(ficheros)} entrada(s)"] if ficheros else []
    for f in fuera:
        errs.append(f"docs/knowledge/README.md:{f['linea']}: fila «{f['id'] or f['ruta']}» fuera de la tabla (una línea en "
                    f"blanco la cierra en Markdown: se renderiza como texto con las barras) — muévela dentro")
    vistos_id, vistas_ruta = {}, {}
    for f in dentro:
        etiqueta = f"docs/knowledge/README.md:{f['linea']} ({f['id'] or 'sin ID'})"
        if not f["id"]:
            errs.append(f"{etiqueta}: fila sin ID")
        elif f["id"] in vistos_id:
            errs.append(f"{etiqueta}: ID repetido `{f['id']}` (ya en la línea {vistos_id[f['id']]})")
        else:
            vistos_id[f["id"]] = f["linea"]
        if not f["ruta"]:
            errs.append(f"{etiqueta}: la columna Entrada no enlaza a ningún fichero (`[`ruta`](ruta)`)")
        elif not os.path.isfile(os.path.join(base, f["ruta"])):
            errs.append(f"{etiqueta}: enlaza a `{f['ruta']}`, que no existe — biyección rota (fila sin fichero)")
        elif f["ruta"] in vistas_ruta:
            errs.append(f"{etiqueta}: ruta repetida `{f['ruta']}` (ya en la línea {vistas_ruta[f['ruta']]})")
        else:
            vistas_ruta[f["ruta"]] = f["linea"]
        if not f["area"]:
            errs.append(f"{etiqueta}: fila sin «Área» — para los ADR el área SOLO vive aquí; sin ella la entrada no se "
                        f"enruta (knowledge-find.py --area) ni se puede reconstruir")
    con_fila = {f["ruta"] for f in dentro}
    for rel in ficheros:
        if rel not in con_fila:
            errs.append(f"docs/knowledge/{rel}: entrada sin fila en docs/knowledge/README.md — invisible para el único "
                        f"camino de lectura; añade su fila (con «Área») en la tabla del índice")
    return errs
# --8<-- fin del criterio del índice de knowledge COMPARTIDO


def _cargar_knowledge_find(plugin_root):
    """`knowledge-find.py` como módulo (sin efectos): su parser del corpus y su lector del índice en
    modo `ro`. None si no está (instalación parcial) → recuento local mínimo."""
    for base in ((os.path.join(plugin_root, "agent-kits", "shared") if plugin_root else None), HERE):
        path = os.path.join(base, "knowledge-find.py") if base else None
        if path and os.path.isfile(path):
            previo = sys.dont_write_bytecode
            sys.dont_write_bytecode = True
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location("knowledge_find_doctor", path)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                return mod
            except Exception:        # noqa: BLE001 — degradación: recuento local
                return None
            finally:
                sys.dont_write_bytecode = previo
    return None


def _frontmatter_estado(path):
    try:
        with open(path, encoding="utf-8-sig", errors="replace") as fh:
            texto = fh.read(4000)
    except OSError:
        return ""
    m = re.search(r"^estado:\s*([a-záéíóú-]+)", texto, re.M | re.I)
    return m.group(1).lower() if m else ""


def _curadas(project, kf):
    """[(tipo, estado)] de las entradas curadas, con el parser del script si está, o local si no."""
    base = os.path.join(project, "docs", "knowledge")
    if kf is not None:
        try:
            return [(e["tipo"], e["estado"]) for e in kf.cargar_corpus(project)]
        except Exception:            # noqa: BLE001
            pass
    out = []
    for carpeta, _etq in KNOWLEDGE_CARPETAS:
        d = os.path.join(base, carpeta)
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if fn.endswith(".md") and fn.lower() != "readme.md":
                tipo = {"adr": "adr", "gotchas": "gotcha", "lessons": "leccion"}[carpeta]
                out.append((tipo, _frontmatter_estado(os.path.join(d, fn)) or "?"))
    return out


def _indice_readme(project, n_curadas):
    """Biyección ficheros ↔ filas + «Área»: `lint_knowledge_index`, la copia LITERAL del criterio de
    `scripts/lint_plugin.py` (bloque `--8<--` de arriba, identidad afirmada por tests/test_knowledge_index.py).
    Así /doctor juzga con el mismo criterio que el linter y la suite aunque `plugin_root` resuelva a una copia
    instalada anterior: antes delegaba en ella y, si no traía `lint_knowledge_index`, caía a una comprobación
    local que solo veía «fichero sin fila» y «fila sin Área» — una fila hacia un fichero inexistente pasaba ✅."""
    try:
        errs = list(lint_knowledge_index(project))
    except Exception as e:           # noqa: BLE001 — nunca bloquea: se dice y se sigue
        errs = [f"docs/knowledge/README.md: no se pudo comprobar ({e.__class__.__name__}: {e})"]
    if not errs:
        return [linea(OK, "índice de memoria (README)",
                      f"biyección ficheros ↔ filas, enlaces y «Área» en las {n_curadas} entrada(s) (criterio de `lint_plugin.py`, copia literal con test de identidad)")]
    resto = f" · … y {len(errs) - 3} más" if len(errs) > 3 else ""
    return [linea(ERROR, "índice de memoria (README)", " · ".join(errs[:3]) + resto,
                  "añade la fila (con «Área») o corrige el enlace en `docs/knowledge/README.md`: una entrada sin "
                  "fila es INVISIBLE para el único camino de lectura y para los ADR el área solo vive ahí; "
                  "`python3 scripts/lint_plugin.py` y `tests/test_knowledge_index.py` lo comprueban")]


def _indice_fts5_desfasado_o_corrupto(path):
    """El hash no cuadra: ¿desfasado (fichero abre bien) o corrupto (no abre / sin esquema)?"""
    try:
        import sqlite3
        con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        try:
            con.execute("SELECT valor FROM meta WHERE clave = 'hash'").fetchone()
        finally:
            con.close()
        return linea(INFO, "índice de búsqueda (FTS5)", "desfasado respecto al corpus",
                     "normal tras editar `docs/knowledge/`: se reconstruye solo en la próxima consulta")
    except Exception:            # noqa: BLE001 — bytes basura, esquema viejo…
        return linea(AVISO, "índice de búsqueda (FTS5)", "corrupto (no abre o no tiene el esquema)",
                     "se reconstruye solo en la próxima consulta; si no, bórralo: `rm .claude/knowledge-index.sqlite` "
                     "(es caché, no el almacén)")


def _indice_fts5_leer(path, project, kf):
    """Lectura efectiva de la caché ya confirmada FTS5-capaz."""
    if not os.path.isfile(path):
        return [linea(INFO, "índice de búsqueda (FTS5)", "sin `.claude/knowledge-index.sqlite`",
                      "se construye en la primera consulta de `knowledge-find.py` (caché reconstruible, en .gitignore)")]
    h = kf.hash_corpus(kf.ficheros_corpus(project))
    entradas, estado = kf.leer_indice(path, h)
    if entradas is not None:
        return [linea(OK, "índice de búsqueda (FTS5)", f"válido · al día con el corpus ({len(entradas)} entrada(s))")]
    return [_indice_fts5_desfasado_o_corrupto(path)]


def _indice_fts5(project, kf):
    """Caché de búsqueda: se LEE en `mode=ro`, nunca se construye aquí (solo lectura)."""
    path = os.path.join(project, ".claude", "knowledge-index.sqlite")
    if kf is None:
        return [linea(INFO, "índice de búsqueda (FTS5)", "`knowledge-find.py` no está para comprobarlo",
                      "instalación parcial: reinstala el plugin si quieres la búsqueda de memoria")]
    try:
        if not kf.fts5_disponible():
            return [linea(AVISO, "índice de búsqueda (FTS5)", "`sqlite3` de este Python no trae FTS5",
                          "las consultas de `knowledge-find.py` van en recorrido plano (mismos aciertos, más lentas); "
                          "un Python con SQLite ≥ 3.9 compilado con FTS5 lo arregla")]
        return _indice_fts5_leer(path, project, kf)
    except Exception as e:           # noqa: BLE001
        return [linea(INFO, "índice de búsqueda (FTS5)", f"no comprobable ({e.__class__.__name__})",
                      "ejecuta `python3 agent-kits/shared/knowledge-find.py --limit 1 --json` y mira `indice`")]


def _ledgers_cerrados(roadmap):
    """[(slug sin fecha, fecha de cierre)] de los `tasks.md` con `estado: completado`; la fecha es
    `actualizado:` del frontmatter (o la del nombre de la carpeta si falta)."""
    out = []
    for d in sorted(os.listdir(roadmap)) if os.path.isdir(roadmap) else []:
        t = os.path.join(roadmap, d, "tasks.md")
        if not os.path.isfile(t):
            continue
        try:
            cab = open(t, encoding="utf-8-sig", errors="replace").read(3000)
        except OSError:
            continue
        if not re.search(r"^estado:\s*completado\b", cab, re.M):
            continue
        m = re.search(r"^actualizado:\s*(\d{4}-\d{2}-\d{2})", cab, re.M) or FECHA_RE.match(d)
        try:
            fecha = datetime.date.fromisoformat(m.group(1)) if m else None
        except ValueError:
            fecha = None
        out.append((re.sub(r"^\d{4}-\d{2}-\d{2}-", "", d), fecha))
    return out


def _calibracion_leer(cal):
    """Última fecha y conjunto de slugs con fila en CALIBRATION.md. `None, None` si no se puede leer."""
    ultima, con_fila = None, set()
    if not os.path.isfile(cal):
        return ultima, con_fila
    try:
        for ln in open(cal, encoding="utf-8-sig", errors="replace"):
            m = re.match(r"^\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*([^|]+?)\s*\|", ln)
            if m:
                try:
                    f = datetime.date.fromisoformat(m.group(1))
                except ValueError:
                    continue
                ultima = max(ultima, f) if ultima else f
                con_fila.add(m.group(2).strip().strip("`"))
    except OSError:
        return "error", con_fila
    return ultima, con_fila


def _calibracion(project, hoy=None):
    roadmap = os.path.join(project, "docs", "roadmap")
    if not os.path.isdir(roadmap):
        return []
    hoy = hoy or datetime.date.today()
    cal = os.path.join(roadmap, "CALIBRATION.md")
    ultima, con_fila = _calibracion_leer(cal)
    if ultima == "error":
        return [linea(AVISO, "calibración (CALIBRATION.md)", "no se puede leer", "revisa permisos del fichero")]
    cerrados = _ledgers_cerrados(roadmap)
    pendientes = [s for s, f in cerrados if s not in con_fila and (ultima is None or (f is not None and f > ultima))]
    que = "calibración (CALIBRATION.md)"
    arreglo = ("`/retro docs/roadmap/<fecha>-<slug>` de cada una: escribe su fila en CALIBRATION.md y recalibra el "
               "ratio tokens→hora que usan `evaluator` y `usage-meter.py` (la memoria episódica solo se vuelve "
               "lección pasando por ahí); el cierre de `/dev-cycle` (Fase 6, paso 8: `retro-gate.py`) no se declara "
               "completo sin ella")
    if ultima is None:
        if pendientes:
            return [linea(AVISO, que, f"sin fila (o sin fichero) y {len(pendientes)} iniciativa(s) cerrada(s) sin retro: "
                                      f"{', '.join(pendientes[:6])}{' …' if len(pendientes) > 6 else ''}", arreglo)]
        return [linea(INFO, que, "sin filas todavía", "`/retro` la crea al cerrar la primera iniciativa")]
    dias = (hoy - ultima).days
    if dias > CALIBRACION_DIAS_MAX and pendientes:
        return [linea(AVISO, que, f"última fila {ultima.isoformat()}: {dias} días sin fila y {len(pendientes)} "
                                  f"iniciativa(s) cerrada(s) después sin retro: {', '.join(pendientes[:6])}"
                                  f"{' …' if len(pendientes) > 6 else ''}", arreglo)]
    if pendientes:
        return [linea(INFO, que, f"última fila {ultima.isoformat()} ({dias} días) · {len(pendientes)} cerrada(s) después "
                                 f"sin retro todavía: {', '.join(pendientes[:6])}", arreglo)]
    return [linea(OK, que, f"última fila {ultima.isoformat()} ({dias} días) · ninguna iniciativa cerrada sin retro")]


def bloque_memoria(plugin_root, project, hoy=None):
    base = os.path.join(project, "docs", "knowledge")
    if not os.path.isdir(base):
        ls = [linea(INFO, "memoria técnica", "sin `docs/knowledge/` — un proyecto recién instalado nace sin memoria, y es correcto",
                    "la crea el primer registro: un ADR/gotcha/lección de una puerta de decisión, o `/retro` al cerrar una iniciativa")]
        ls += _journal(project, 0) + _calibracion(project, hoy)
        return {"clave": "memoria", "titulo": "Memoria técnica (`docs/knowledge/`)", "lineas": ls}
    kf = _cargar_knowledge_find(plugin_root)
    curadas = _curadas(project, kf)
    n = len(curadas)
    if not n:
        ls = [linea(INFO, "memoria curada", "`docs/knowledge/` sin entradas todavía (adr/, gotchas/, lessons/)",
                    "se pobla con las puertas de decisión y con `/retro`; nada que arreglar")]
    else:
        por_tipo = {t: sum(1 for x, _ in curadas if x == t) for t in ("adr", "gotcha", "leccion")}
        estados = {}
        for _t, e in curadas:
            estados[e or "?"] = estados.get(e or "?", 0) + 1
        det_estados = " · ".join(f"{v} {k}" for k, v in sorted(estados.items(), key=lambda kv: (-kv[1], kv[0])))
        ls = [linea(OK, "memoria curada", f"{n} entrada(s): {por_tipo['adr']} ADR · {por_tipo['gotcha']} gotcha(s) · "
                                          f"{por_tipo['leccion']} lección(es) · estados: {det_estados}")]
    ls += _indice_readme(project, n)
    ls += _indice_fts5(project, kf) if n else []
    ls += _journal(project, n) + _calibracion(project, hoy)
    return {"clave": "memoria", "titulo": "Memoria técnica (`docs/knowledge/`)", "lineas": ls}


# ------------------------------------------------------------------ f) versión

AVISO_SIN_RED = ("sin red por diseño: `/doctor` NO consulta el marketplace, así que no puede "
                 "decirte si hay una versión más nueva")


def _bloque_version_plugin(plugin_root):
    """Líneas + versión detectada de `.claude-plugin/plugin.json` (o None si no se pudo leer)."""
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
    return ls, version


def _bloque_version_vista(project, version):
    """Línea informativa comparando la versión vista la última vez con la actual."""
    seen_path = os.path.join(project, ".claude", ".plugin-version-seen")
    seen = ""
    if os.path.isfile(seen_path):
        try:
            seen = open(seen_path, encoding="utf-8-sig").read().strip()
        except OSError:
            seen = ""
    if not seen:
        return linea(INFO, "versión vista en este proyecto", "sin registro previo",
                     "opcional: `echo <version> > .claude/.plugin-version-seen` deja constancia de "
                     "con qué versión trabajaste (nadie lo escribe automáticamente hoy)")
    if version and seen != version:
        return linea(INFO, "versión vista en este proyecto",
                     f"la última vez que se vio este proyecto era {seen}; ahora hay {version}",
                     "solo es un registro local: revisa el CHANGELOG del plugin si te interesa qué "
                     "cambió entre esas dos versiones")
    return linea(INFO, "versión vista en este proyecto", f"{seen} — igual que la actual")


def bloque_version(plugin_root, project):
    ls, version = _bloque_version_plugin(plugin_root)
    ls.append(_bloque_version_vista(project, version))
    return {"clave": "version", "titulo": "Versión", "lineas": ls}


# ------------------------------------------------------------------ informe

def diagnostico(project, plugin_root_explicito=None, hoy=None):
    plugin_root = localizar_plugin(plugin_root_explicito)
    bloques = [bloque_herramientas(),
               bloque_plugin(plugin_root, project, plugin_root_explicito),
               bloque_configs(plugin_root, project),
               bloque_estado(plugin_root, project),
               bloque_memoria(plugin_root, project, hoy),
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
    ap.add_argument("--hoy", default=None, help="fecha de referencia AAAA-MM-DD para la antigüedad de CALIBRATION.md (tests)")
    args = ap.parse_args(argv)

    hoy = None
    if args.hoy:
        try:
            hoy = datetime.date.fromisoformat(args.hoy)
        except ValueError:
            print(f"❌ uso: --hoy `{args.hoy}` no es una fecha AAAA-MM-DD", file=sys.stderr)
            return 2
    if not os.path.isdir(args.root):
        print(f"❌ uso: --root `{args.root}` no es un directorio", file=sys.stderr)
        return 2
    if args.plugin_root is not None and not os.path.isdir(args.plugin_root):
        print(f"❌ uso: --plugin-root `{args.plugin_root}` no es un directorio", file=sys.stderr)
        return 2

    inf = diagnostico(args.root, args.plugin_root, hoy)
    print(json.dumps(inf, ensure_ascii=False, indent=2) if args.json else render_md(inf))
    return inf["exit"]


if __name__ == "__main__":
    sys.exit(main())
