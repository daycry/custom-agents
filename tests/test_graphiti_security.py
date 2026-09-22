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


# El servidor MCP falso (fixtures reales capturadas del stack) y el constructor de entradas de la
# suite del adaptador se REUTILIZAN; los tests de abajo son propios.
_suite_adaptador = _cargar(os.path.join(KS_SCRIPTS, "test_backend_graphiti.py"),
                           "graphiti_suite_adaptador_para_seguridad")
ServidorMCP = _suite_adaptador._ServidorMCPContext

ks_sync = _cargar(os.path.join(KS_SCRIPTS, "knowledge-sync.py"), "ks_sync_seguridad")
gr = _cargar(os.path.join(KS_BACKENDS, "graphiti.py"), "ks_graphiti_seguridad")
kf = _cargar(os.path.join(SHARED, "knowledge-find.py"), "kf_seguridad")
ob = _cargar(os.path.join(SHARED, "outbox.py"), "outbox_seguridad")


# ====================================================================== 1. sin red desde hooks

_TERMINOS_RED = ("urllib", "urlopen", "http.client", "httpx", "requests.", "socket.socket",
                 "socket.create_connection", "curl ", "wget ", "invoke-webrequest")
_MODULOS_RED = {"urllib", "urllib.request", "urllib.parse", "http.client", "httplib", "socket",
                "requests", "httpx", "ssl"}
# Los dos scripts que los hooks SI invocan y que definen en su propio argparse los flags
# prohibidos: la prohibicion es para quien los LLAMA, no para la herramienta que los declara.
_HERRAMIENTAS = {"knowledge-find.py", "capabilities.py"}
_MAX_SALTOS = 5
_RUTA_RE = re.compile(r"[\w./\\-]+\.(?:py|sh)")


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
    return "\n".join(l for l in texto.splitlines() if not l.lstrip().startswith("#"))


def _modulos_importados(ruta):
    if not ruta.endswith(".py"):
        return set()
    modulos = set()
    for nodo in ast.walk(ast.parse(_texto(ruta))):
        if isinstance(nodo, ast.Import):
            modulos |= {a.name for a in nodo.names}
        elif isinstance(nodo, ast.ImportFrom) and nodo.module:
            modulos.add(nodo.module)
    return modulos


def _resolver(ruta_rel):
    """Ruta real de un script citado: relativa al repo, o por NOMBRE bajo `agent-kits/shared/` y
    `hooks/` (las dos carpetas de donde salen los scripts que los hooks invocan)."""
    ruta_rel = ruta_rel.replace("\\", "/").lstrip("$/")
    candidato = os.path.normpath(os.path.join(ROOT, ruta_rel))
    if os.path.isfile(candidato):
        return candidato
    for carpeta in (SHARED, os.path.join(ROOT, "hooks")):
        posible = os.path.join(carpeta, os.path.basename(ruta_rel))
        if os.path.isfile(posible):
            return posible
    return None


def _scripts_citados_por_hooks_json():
    with open(HOOKS_JSON, encoding="utf-8") as f:
        config = json.load(f)
    textos = []
    for eventos in (config.get("hooks") or {}).values():
        for bloque in eventos:
            for hook in bloque.get("hooks") or []:
                textos.append(str(hook.get("command", "")))
                textos += [str(a) for a in hook.get("args") or []]
    citados = set()
    for texto in textos:
        citados |= {m.group(0) for m in _RUTA_RE.finditer(texto)}
    return citados


def _alcanzables_desde_hooks_json():
    """Cierre TRANSITIVO (hasta `_MAX_SALTOS`) de los scripts que `hooks/hooks.json` alcanza:
    `{etiqueta relativa al repo: ruta absoluta}`."""
    pendientes, vistos = _scripts_citados_por_hooks_json(), {}
    for _salto in range(_MAX_SALTOS):
        siguientes = set()
        for rel in sorted(pendientes):
            resuelta = _resolver(rel)
            if not resuelta:
                continue
            etiqueta = os.path.relpath(resuelta, ROOT).replace(os.sep, "/")
            if etiqueta in vistos:
                continue
            vistos[etiqueta] = resuelta
            siguientes |= {m.group(0) for m in _RUTA_RE.finditer(_codigo(resuelta))}
        pendientes = siguientes
        if not pendientes:
            break
    return vistos


def test_el_recorrido_alcanza_de_verdad_los_scripts_de_los_hooks():
    """Andamiaje del resto de la seccion: si el recorrido dejara de encontrar los scripts reales,
    los tests de abajo pasarian EN VACIO (el fallo mas peligroso de un escaneo)."""
    alcanzables = _alcanzables_desde_hooks_json()
    for esperado in ("hooks/session-context.sh", "hooks/session-journal.sh",
                     "agent-kits/shared/journal.py", "agent-kits/shared/outbox.py",
                     "agent-kits/shared/knowledge-find.py", "agent-kits/shared/skill-index.py"):
        assert esperado in alcanzables, (esperado, sorted(alcanzables))
    assert len(alcanzables) >= 8, sorted(alcanzables)


def test_ningun_script_alcanzable_desde_hooks_toca_la_red():
    """«Llamadas de red en hooks» esta FUERA DE ALCANCE (spec.md). Se mira el CODIGO (sin
    comentarios ni docstrings) de todo el cierre transitivo."""
    ofensores = []
    for etiqueta, ruta in sorted(_alcanzables_desde_hooks_json().items()):
        codigo = _codigo(ruta).lower()
        for termino in _TERMINOS_RED:
            if termino in codigo:
                ofensores.append((etiqueta, termino))
        for modulo in sorted(_modulos_importados(ruta) & _MODULOS_RED):
            ofensores.append((etiqueta, "import " + modulo))
    assert ofensores == [], ofensores


def test_ningun_script_alcanzable_desde_hooks_invoca_el_sincronizador_ni_capabilities():
    """`knowledge-sync.py` y `capabilities.py` son caminos que cargan un adaptador de backend
    (codigo CON capacidad de red): ningun hook puede llegar a ellos."""
    ofensores = []
    for etiqueta, ruta in sorted(_alcanzables_desde_hooks_json().items()):
        codigo = _codigo(ruta)
        for prohibido in ("knowledge-sync.py", "capabilities.py"):
            if prohibido in codigo and os.path.basename(ruta) != prohibido:
                ofensores.append((etiqueta, prohibido))
    assert ofensores == [], ofensores


def test_ningun_hook_pasa_intent_ni_backends_dir_a_knowledge_find():
    """`--intent`/`--backends-dir` son los UNICOS flags de `knowledge-find.py` que cargan un
    adaptador (CA-12): ningun llamador alcanzable desde los hooks los usa."""
    ofensores = []
    for etiqueta, ruta in sorted(_alcanzables_desde_hooks_json().items()):
        if os.path.basename(ruta) in _HERRAMIENTAS:
            continue
        codigo = _codigo(ruta)
        for flag in ("--intent", "--backends-dir"):
            if flag in codigo:
                ofensores.append((etiqueta, flag))
    assert ofensores == [], ofensores


_LLAMADA_KF_RE = re.compile(
    r"""run\(\s*os\.path\.join\(shared,\s*["']knowledge-find\.py["']\)\s*,(?P<args>[^)]*)\)""")


def _flags_reales_de_session_context():
    """Flags REALES con los que `hooks/session-context.sh` invoca `knowledge-find.py`, leidos del
    propio hook: si manana cambian, este test los ve."""
    texto = _texto(os.path.join(ROOT, "hooks", "session-context.sh"))
    m = _LLAMADA_KF_RE.search(texto)
    assert m, "no se encontro la invocacion de knowledge-find.py en hooks/session-context.sh"
    return re.findall(r"""["'](--[\w-]+)["']""", m.group("args"))


def test_el_argv_real_del_hook_no_carga_ningun_adaptador(tmp_path, monkeypatch, capsys):
    """Espia VIVO sobre `cargar_adaptador` (el unico camino del nucleo hacia un modulo con red):
    con el argv EXACTO del hook, `knowledge-find.py` no puede llegar a el."""
    flags = _flags_reales_de_session_context()
    assert flags, "el hook ya no pasa ningun flag a knowledge-find.py"
    assert "--intent" not in flags and "--backends-dir" not in flags, flags

    root = str(tmp_path)
    os.makedirs(os.path.join(root, "docs", "knowledge"), exist_ok=True)
    with open(os.path.join(root, "docs", "knowledge", "README.md"), "w", encoding="utf-8") as f:
        f.write("# Memoria tecnica\n")

    binit = _cargar(os.path.join(KS_BACKENDS, "__init__.py"), "binit_espia_seguridad")

    def _prohibido(*a, **k):
        raise AssertionError("el argv del hook no puede cargar un adaptador de backend")

    monkeypatch.setattr(binit, "cargar_adaptador", _prohibido)
    monkeypatch.setattr(kf, "_cargar_modulo", lambda *a, **k: binit)

    valores = {"--root": root, "--limit": "0",
               "--contexto": "Checklist de Tareas - Memoria Graphiti",
               "--iniciativa": "graphiti-memory"}
    argv = []
    for flag in flags:
        argv.append(flag)
        if flag in valores:
            argv.append(valores[flag])
    assert kf.main(argv) == 0
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


def _taxonomia_graphiti(root, endpoint, provider=None, extra_config=None):
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
        "backends": {"graphiti": {"type": "graphiti", "enabled": True, "config": cfg_backend}},
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


def test_ca14_salida_estructurada_invalida_del_proveedor_no_llega_a_add_memory(tmp_path,
                                                                               monkeypatch):
    """CA-14, primera forma: con `provider.llm: ollama` y una salida estructurada invalida, la op
    falla ANTES de gastar la llamada de red — el grafo no ve nada y el manifiesto PUBLICADO no se
    toca (no hay datos corruptos)."""
    root = str(tmp_path)
    with ServidorMCP() as srv:
        monkeypatch.setitem(gr._gp.PROVEEDORES, "ollama", _proveedor_ollama_roto)
        cfg = {"_root": root, "group_id": "proy-seguridad", "endpoint": srv.endpoint,
               "allow_remote": False, "timeout_ms": 2000,
               "provider": {"llm": "ollama", "model": "qwen2.5:7b"}}
        ops = gr.plan([_suite_adaptador._entrada()], cfg)
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


# ================================ 4. CA-05: ninguna pieza escribe en el grafo por su cuenta

PIEZAS_SKILL_DUENA = ("skills/knowledge-services/SKILL.md",)
_PRIMITIVAS_ESCRITURA = ("add_memory", "add_triplet", "clear_graph", "delete_episode",
                         "delete_entity_edge", "delete_group")
_FLAGS_SOLO_LECTURA = ("--check", "--dry-run", "--outbox-status", "--propose-config")


def _piezas():
    """`agents/*.md` + `commands/*.md` + `skills/*/SKILL.md` (etiqueta relativa -> ruta)."""
    piezas = {}
    for carpeta, patron in (("agents", ".md"), ("commands", ".md")):
        base = os.path.join(ROOT, carpeta)
        for nombre in sorted(os.listdir(base)):
            if nombre.endswith(patron):
                piezas[carpeta + "/" + nombre] = os.path.join(base, nombre)
    base_skills = os.path.join(ROOT, "skills")
    for nombre in sorted(os.listdir(base_skills)):
        ruta = os.path.join(base_skills, nombre, "SKILL.md")
        if os.path.isfile(ruta):
            piezas["skills/" + nombre + "/SKILL.md"] = ruta
    return piezas


def test_el_recorrido_de_piezas_no_esta_vacio():
    """Andamiaje: sin piezas, los dos tests de abajo pasarian en vacio."""
    piezas = _piezas()
    assert "agents/knowledge-curator.md" in piezas and "commands/dev-cycle.md" in piezas
    assert len(piezas) >= 20, sorted(piezas)


def test_ca05_ninguna_pieza_invoca_primitivas_de_escritura_en_el_grafo():
    """CA-05: solo el sincronizador escribe. Ninguna pieza (agente, comando o skill), incluida la
    skill duena, manda `add_memory`/`add_triplet`/`clear_graph`/`delete_*` por su cuenta."""
    ofensores = []
    for etiqueta, ruta in sorted(_piezas().items()):
        texto = _texto(ruta)
        for primitiva in _PRIMITIVAS_ESCRITURA:
            if primitiva in texto:
                ofensores.append((etiqueta, primitiva))
    assert ofensores == [], ofensores


def test_ca05_ninguna_pieza_ajena_invoca_el_sincronizador_en_modo_escritura():
    """Fuera de la skill `knowledge-services`, una pieza puede NOMBRAR `knowledge-sync.py`, pero
    solo en un modo de SOLO LECTURA (`--check`/`--dry-run`/`--outbox-status`/`--propose-config`):
    una publicacion real (`--backend <id>` a secas, o `--rebuild`) es escritura en el grafo."""
    ofensores = []
    for etiqueta, ruta in sorted(_piezas().items()):
        if etiqueta in PIEZAS_SKILL_DUENA:
            continue
        for linea in _texto(ruta).splitlines():
            if "knowledge-sync.py --backend" not in linea and "knowledge-sync.py` --backend" not in linea:
                continue
            if not any(flag in linea for flag in _FLAGS_SOLO_LECTURA) or "--rebuild" in linea:
                ofensores.append((etiqueta, linea.strip()[:120]))
    assert ofensores == [], ofensores


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
    """Gap #78 (CWE-200): `127.0.0.1:A` y `127.0.0.1:B` son servicios DISTINTOS — un 307 hacia
    otro puerto no puede llevarse el `Mcp-Session-Id` de la sesion anterior."""
    espia = _EspiaConexiones(monkeypatch)
    with _ServidorEfimero(_responder_initialize) as destino:
        with _ServidorEfimero(_redirector(307, destino.endpoint + "/mcp")) as origen:
            cliente = gr.ClienteMCP(origen.endpoint, timeout_s=2.0, allow_remote=False)
            cliente._session_id = "sesion-del-origen"
            cliente.initialize()
        cabeceras_origen = origen.peticiones[0][1]
        cabeceras_destino = destino.peticiones[0][1]
    assert cabeceras_origen.get("Mcp-Session-Id") == "sesion-del-origen"
    assert not any(k.lower() == "mcp-session-id" for k in cabeceras_destino), cabeceras_destino
    assert espia.fuera_de_loopback == []
