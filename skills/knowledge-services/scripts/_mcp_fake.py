#!/usr/bin/env python3
"""Servidor MCP FALSO y constructor de entradas: modulo de APOYO compartido por las suites que
prueban la memoria Graphiti (`test_backend_graphiti.py` y `tests/test_graphiti_security.py`).

Gap #166 (Minor, fix1 Fase 4): la suite de seguridad importaba `test_backend_graphiti.py` POR RUTA
con un nombre de modulo propio, asi que bajo la invocacion unica de pytest de CI el mismo fichero
de tests se cargaba DOS veces con nombres distintos (dos juegos de fixtures, dos clases de handler,
estado compartido entre suites). Ahora el servidor falso vive aqui y las dos suites lo cargan con
el mismo nombre de modulo (`NOMBRE_MODULO`), comprobando antes `sys.modules`: una sola carga
por proceso.

No contiene tests (el nombre empieza por `_`, asi que pytest no lo recolecta). Sin red real: sirve
las fixtures capturadas del stack en `127.0.0.1:0`.
"""
import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 - sin reconfigure, ya leido o None (capsys, pythonw)

HERE = os.path.dirname(os.path.abspath(__file__))
# Nombre CANONICO del modulo: las dos suites lo cargan con este nombre y comprueban antes si ya
# esta en `sys.modules`, asi que el fichero se ejecuta UNA sola vez por proceso (gap #166).
NOMBRE_MODULO = "ks_graphiti_mcp_fake"


FIXTURES = os.path.join(HERE, "fixtures", "graphiti")


def _leer_fixture(nombre):
    with open(os.path.join(FIXTURES, nombre), "r", encoding="utf-8") as f:
        return json.load(f)


_FIXTURE_INITIALIZE = _leer_fixture("graphiti-mcp-initialize-2026-09-18.json")
_FIXTURE_TOOLS_LIST = _leer_fixture("graphiti-mcp-tools-list-2026-09-18.json")
_FIXTURE_GET_STATUS = _leer_fixture("graphiti-mcp-get-status-2026-09-18.json")

# Gap #69 (Critical, fix4): el CONTRATO REAL del servidor -el `required` de cada tool, capturado
# en el fixture `tools/list`- lo hace cumplir el servidor falso de esta suite. Sin esto, una
# llamada que omite un campo obligatorio (p. ej. `add_triplet` sin `source_node_name`) pasaba
# verde aqui y fallaba contra el servidor REAL con `isError`.
_REQUIRED_POR_TOOL = {
    t["name"]: tuple((t.get("inputSchema") or {}).get("required") or ())
    for t in _FIXTURE_TOOLS_LIST["result"]["tools"]
}


def _campos_obligatorios_que_faltan(nombre, argumentos):
    """Campos `required` del fixture real ausentes (o vacios) en `argumentos`."""
    faltan = []
    for campo in _REQUIRED_POR_TOOL.get(nombre, ()):
        valor = (argumentos or {}).get(campo)
        if valor is None or valor == "":
            faltan.append(campo)
    return faltan


class _ServidorMCPFalso(BaseHTTPRequestHandler):
    """Dispatcher JSON-RPC minimo sobre POST `/mcp`. `respuestas_tools` mapea
    `nombre_de_tool -> resultado_MCP` (o una funcion `(argumentos) -> resultado_MCP`); las
    llamadas a `tools/call` quedan en `llamadas` (lista de `(nombre, argumentos)`) para que los
    tests comprueben que, p. ej., `clear_graph` solo llego con el `group_id` propio."""

    respuestas_tools = {}
    llamadas = []
    session_id = "sesion-fake-1"
    forma_redirect = None  # None | "redirect_una_vez" (simula 307 de "/mcp/" -> "/mcp")
    forzar_sse = False
    sse_partido = False  # gap #76: parte el JSON del `result` en DOS lineas `data:` (spec SSE)
    validar_required = True  # gap #69: exige el `required` del fixture real en cada `tools/call`

    def do_POST(self):  # noqa: N802 - nombre impuesto por BaseHTTPRequestHandler
        largo = int(self.headers.get("Content-Length", 0))
        # Siempre se drena el cuerpo ANTES de responder (incluso en la rama de redirección): un
        # cuerpo sin leer deja datos pendientes en el socket que Windows corta con
        # ConnectionAbortedError en la siguiente petición de la misma suite.
        crudo = self.rfile.read(largo) if largo else b"{}"
        if self.forma_redirect == "redirect_una_vez" and self.path == "/mcp/":
            self.send_response(307)
            self.send_header("Location", "/mcp")
            self.end_headers()
            return
        peticion = json.loads(crudo.decode("utf-8"))
        metodo = peticion.get("method")
        id_ = peticion.get("id")
        if metodo == "notifications/initialized":
            self.send_response(202)
            self.end_headers()
            return
        if metodo == "initialize":
            cuerpo = dict(_FIXTURE_INITIALIZE)
            cuerpo["id"] = id_
            self._responder_json(cuerpo)
            return
        if metodo == "tools/list":
            cuerpo = dict(_FIXTURE_TOOLS_LIST)
            cuerpo["id"] = id_
            self._responder_json(cuerpo)
            return
        if metodo == "tools/call":
            params = peticion.get("params") or {}
            nombre = params.get("name")
            argumentos = params.get("arguments") or {}
            type(self).llamadas.append((nombre, argumentos))
            if self.validar_required:
                faltan = _campos_obligatorios_que_faltan(nombre, argumentos)
                if faltan:
                    # Igual que el servidor real: error de la TOOL (`isError`), no de JSON-RPC.
                    self._responder_json({"jsonrpc": "2.0", "id": id_, "result": {
                        "isError": True,
                        "content": [{"type": "text", "text":
                                     f"missing required argument(s) for `{nombre}`: {faltan}"}],
                    }})
                    return
            if nombre == "get_status":
                cuerpo = dict(_FIXTURE_GET_STATUS)
                cuerpo["id"] = id_
                self._responder_json(cuerpo)
                return
            manejador = self.respuestas_tools.get(nombre)
            resultado = manejador(argumentos) if callable(manejador) else (
                manejador if manejador is not None else {"content": [], "structuredContent": {"ok": True}})
            self._responder_json({"jsonrpc": "2.0", "id": id_, "result": resultado})
            return
        self.send_response(404)
        self.end_headers()

    def _responder_json(self, cuerpo):
        self.send_response(200)
        if self.session_id:
            self.send_header("Mcp-Session-Id", self.session_id)
        if self.forzar_sse or self.sse_partido:
            self.send_header("Content-Type", "text/event-stream")
            crudo_json = json.dumps(cuerpo)
            if self.sse_partido:
                # Gap #76: un evento SSE puede traer el JSON repartido en VARIAS lineas `data:`
                # (spec SSE: el cuerpo del evento es la concatenacion de sus lineas `data:` con
                # un salto de linea), y el servidor Graphiti lo hace con resultados largos. Se
                # reparte por LINEAS del JSON indentado: cada linea es un `data:` propio y solo
                # la concatenacion de TODAS vuelve a ser JSON valido.
                lineas = json.dumps(cuerpo, indent=2).splitlines()
                datos = ("".join(f"data: {linea}\n" for linea in lineas)
                          + "\n").encode("utf-8")
            else:
                datos = f"data: {crudo_json}\n\n".encode("utf-8")
        else:
            self.send_header("Content-Type", "application/json")
            datos = json.dumps(cuerpo).encode("utf-8")
        self.end_headers()
        self.wfile.write(datos)

    def log_message(self, *args, **kwargs):
        pass


class _ServidorMCPContext:
    def __init__(self, **atributos):
        self._atributos = atributos

    def __enter__(self):
        atributos = dict(self._atributos)
        atributos["llamadas"] = []
        handler = type("Handler", (_ServidorMCPFalso,), atributos)
        self.httpd = HTTPServer(("127.0.0.1", 0), handler)
        self.handler_cls = handler
        self.puerto = self.httpd.server_address[1]
        self.hilo = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.hilo.start()
        return self

    def __exit__(self, *exc):
        self.httpd.shutdown()
        self.httpd.server_close()

    @property
    def endpoint(self):
        return f"http://127.0.0.1:{self.puerto}"

    @property
    def llamadas(self):
        return self.handler_cls.llamadas


def _entrada(id_="mem.gotchas.graphiti-timeout", version=1, category="GOTCHA",
             evidencia="multiple_validated_cases", cuerpo="Cuerpo de la entrada.\n", modo="completo",
             resumen=None, ruta="docs/knowledge/approved/gotchas/GOT-001.md"):
    return {
        "id": id_, "version": version, "category": category, "evidencia": evidencia,
        "fuentes": ["docs/x.md"], "tags": ["graphiti"], "modo": modo, "cuerpo": cuerpo,
        "resumen": resumen, "ruta": ruta, "folder": "gotchas", "enlaces": [],
    }
