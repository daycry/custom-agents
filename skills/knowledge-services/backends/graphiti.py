#!/usr/bin/env python3
"""
backends/graphiti.py — adaptador Graphiti (`type: "graphiti"`, ADR-018) del contrato de
`backends/__init__.py`. Cliente MCP streamable-HTTP minimo (stdlib, sin librerias) contra el
servidor de `dockers/knowledge-graphs`: `initialize` -> `notifications/initialized` ->
`tools/call`; sesion (`Mcp-Session-Id`) capturada y reenviada; el endpoint fijo del protocolo es
`/mcp` SIN barra final (CA-15) — un `307`/`308` hacia esa forma se sigue manualmente (nunca en
silencio), revalidando el guardarrail de red en CADA salto.

`health`/`verify` NUNCA lanzan (contrato de adaptador, design.md): degradan a
`off · sano · degradado · error`. `verify` NOMBRA el remedio sin ejecutarlo (CA-16). `rebuild` es
el UNICO camino que llama a `clear_graph` (acotado al `group_id` propio) y reproduce el mismo
manifiesto que la sincronizacion incremental. `revoke` escribe un episodio de invalidacion (+
triplete `SUPERSEDES` opcional) y NUNCA llama a `delete_episode` (design.md, enmienda 2026-09-18).

Decision de diseno documentada (plan ambiguo -T-04/T-05-, elegida por el implementer):
  - La extraccion de entidades la hace el SERVIDOR (su `config.yaml`); `graphiti_providers.py`
    solo orienta esa extraccion con `custom_extraction_instructions`, sin llamar a ningun modelo
    desde este proceso (ver docstring de ese modulo).
  - Idempotencia de `apply()` via un manifiesto LOCAL propio (`graphiti-manifest.json` bajo
    `.claude/knowledge-services/`, patron diario pendiente->publicado calcado de
    `markdown_export.py`) — el reintento acotado y el dead-letter de `outbox.py` los orquesta
    `knowledge-sync.py` UNA capa por encima (T-05 solo necesita ser idempotente ante reintentos
    ajenos, no reimplementar la cola).
  - `status` de cada episodio es la constante `"aprobado"`: toda entrada que llega aqui viene de
    `approved/`, donde `estado: aprobado` ya es invariante (`knowledge-index.py`).

Sin dependencias externas; solo stdlib (`hashlib`, `ipaddress`, `json`, `socket`, `threading`,
`urllib.request`, `uuid`).

Uso: cargado por `backends/__init__.py::cargar_adaptador("graphiti", ...)`, nunca ejecutado solo.
Exit: N/A (modulo de libreria, sin CLI propia)
"""
import hashlib
import http.client
import ipaddress
import json
import os
import re
import socket
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure, ya leído o None (capsys, pythonw)

try:
    from . import graphiti_providers as _gp  # paquete normal (tests que importan por ruta relativa)
except ImportError:  # cargado por importlib.util.spec_from_file_location (backends/__init__.py)
    import importlib.util as _ilu
    _RUTA_PROVIDERS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "graphiti_providers.py")
    _spec = _ilu.spec_from_file_location("ks_backend_graphiti_providers", _RUTA_PROVIDERS)
    _gp = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_gp)

try:
    from . import graphiti_model as _gm  # paquete normal (tests que importan por ruta relativa)
except ImportError:  # cargado por importlib.util.spec_from_file_location (backends/__init__.py)
    import importlib.util as _ilu2
    _RUTA_MODEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "graphiti_model.py")
    _spec2 = _ilu2.spec_from_file_location("ks_backend_graphiti_model", _RUTA_MODEL)
    _gm = _ilu2.module_from_spec(_spec2)
    _spec2.loader.exec_module(_gm)


# --8<-- hosts locales COMPARTIDO (graphiti-memory T-01-fix1) — REPLICADO LITERAL en skills/knowledge-services/backends/markdown_export.py, agent-kits/shared/knowledge-schema.py y skills/knowledge-services/backends/graphiti.py
_SUFIJOS_LOCALES = (".test", ".local", ".internal")
_HOSTS_LOCALES_LITERALES = {"localhost", "host.docker.internal"}
# --8<-- fin hosts locales COMPARTIDO
# Gap #34 (revisión Fase 2 intento 1): las dos constantes de arriba ya NO se usan como
# cortocircuito de `_host_permitido` (ver abajo) — un host con nombre se RESUELVE SIEMPRE, sin
# excepción para literales/sufijos "conocidos" (ese cortocircuito es exactamente el agujero (a)
# del gap: un `307 Location` hacia `exfil.internal` pasaba sin resolver DNS). Se mantienen
# declaradas solo para no romper el contrato byte-a-byte de `copias.json` (bloque `hosts_locales`,
# tercera copia añadida en T-04).

_DNS_TIMEOUT_S = 2.0
_DNS_CACHE_TTL_S = 300  # gap #44: una resolución positiva expira a los 5 min (mismo patrón TTL
                        # que `markdown_export.py`, sin ser copia literal: implementación propia)
_DNS_CACHE_TTL_S_LENTO = 5  # resolución vacía o colgada: TTL corto, para no perforar el tope de
                            # tiempo en cada llamada consecutiva pero tampoco cachear "no hay ruta"
                            # por mucho tiempo si la red se recupera
_dns_cache = {}  # {host: (lista_de_ips, expira_epoch_s)}
_MAX_REDIRECCIONES = 3  # gap #34: solo 307/308 se siguen (preservan método); como máximo 3 saltos
_PROTOCOLO_MCP = "2025-03-26"
_NAMESPACE_EPISODIOS = uuid.UUID("6f9c9b0a-6f1e-4a4a-9c1e-6f6f6f6f6f6f")  # constante propia, estable


class ConfigInvalida(Exception):
    """La config del backend no permite operar (p. ej. `group_id` vacio con `enabled: true`)."""


class HostNoPermitido(Exception):
    """El host de `endpoint`/`health.url` no es local/privado y `allow_remote` no lo autoriza."""


class ErrorMCP(Exception):
    """El servidor respondio con un error JSON-RPC, o la respuesta no tiene la forma esperada."""


def _resolver_host(host, timeout_s=_DNS_TIMEOUT_S):
    """Resuelve `host` con un tope de tiempo duro (hilo con `join(timeout_s)`): una resolucion
    DNS colgada nunca debe bloquear `health()`/`plan()` indefinidamente."""
    resultado = {}

    def _resolver():
        try:
            resultado["direcciones"] = socket.getaddrinfo(host, None)
        except Exception as exc:  # noqa: BLE001 — cualquier fallo de resolucion es "no resuelto"
            resultado["error"] = exc

    hilo = threading.Thread(target=_resolver, daemon=True)
    hilo.start()
    hilo.join(timeout_s)
    if "direcciones" not in resultado:
        return []
    return [info[4][0] for info in resultado["direcciones"]]


def _resolver_host_cacheado(host, timeout_s=_DNS_TIMEOUT_S):
    """Cachea por proceso el resultado de `_resolver_host` con TTL (gap #44: sin caché, cada POST
    y cada salto de redirección resolvía DNS de nuevo). Un resultado vacío (sin resolver o
    colgado) se cachea con un TTL corto para no perforar el tope de tiempo en llamadas
    consecutivas, pero tampoco bloquear una recuperación de red por mucho tiempo."""
    ahora = time.time()
    entrada = _dns_cache.get(host)
    if entrada and entrada[1] > ahora:
        return entrada[0]
    direcciones = _resolver_host(host, timeout_s)
    ttl = _DNS_CACHE_TTL_S if direcciones else _DNS_CACHE_TTL_S_LENTO
    _dns_cache[host] = (direcciones, ahora + ttl)
    return direcciones


def _direcciones_de_host(host, timeout_s=_DNS_TIMEOUT_S):
    """Direcciones IP de `host`: si ya es un literal IP se devuelve tal cual (sin red); si es un
    nombre, se RESUELVE SIEMPRE (gap #34: antes, `localhost`/sufijos "conocidos" devolvían `True`
    sin resolver, así que un `307 Location` hacia un host con nombre nunca se comprobaba de
    verdad — se validaba la CADENA, no la IP real a la que apunta ese nombre en ese momento)."""
    try:
        return [str(ipaddress.ip_address(host))]
    except ValueError:
        pass
    return _resolver_host_cacheado(host, timeout_s)


def _direccion_prohibida_siempre(ip):
    """Link-local (`169.254.0.0/16`, `fe80::/10`, típico endpoint de metadatos de nube) y
    no-especificada (`0.0.0.0`, `::`) se rechazan SIEMPRE, incluso con `allow_remote: true` (gap
    #34c): `allow_remote` autoriza salir a redes remotas, no a la red de metadatos del propio
    host ni a direcciones sin sentido como destino de conexión."""
    return bool(ip.is_link_local or ip.is_unspecified)


def _direccion_permitida(ip, allow_remote):
    if _direccion_prohibida_siempre(ip):
        return False
    if allow_remote:
        return True
    return bool(ip.is_loopback or ip.is_private)


def _validar_host(url, allow_remote):
    """Direcciones IP validadas de `url`, o `None` si el host no está permitido (fail-closed ante
    cualquier fallo de parseo/resolución). TODAS las direcciones resueltas de un host con nombre
    deben ser loopback/privadas (o autorizadas por `allow_remote`, salvo las SIEMPRE prohibidas de
    `_direccion_prohibida_siempre`) — un host que resuelve a varias IPs y solo alguna es privada
    ya no basta (gap #34b, DNS rebinding parcial)."""
    try:
        partes = urllib.parse.urlsplit(url)
    except ValueError:
        return None
    if partes.scheme not in ("http", "https"):
        return None
    if partes.username or partes.password:
        return None  # gap #43: userinfo en la URL nunca se acepta
    host = partes.hostname or ""
    if not host:
        return None
    direcciones = _direcciones_de_host(host)
    if not direcciones:
        return None  # no resuelto a tiempo, o sin direcciones: fail-closed
    ips = []
    for direccion in direcciones:
        try:
            ips.append(ipaddress.ip_address(direccion))
        except ValueError:
            return None
    if not all(_direccion_permitida(ip, allow_remote) for ip in ips):
        return None
    return [str(ip) for ip in ips]


def _host_permitido(url, allow_remote):
    """True si `url` apunta a un host local/privado (o `allow_remote` lo autoriza, salvo las
    direcciones SIEMPRE prohibidas). Ver `_validar_host` para el detalle; esta función es el
    booleano que consumen `health()`/`_get_health_endpoint()`."""
    return _validar_host(url, allow_remote) is not None


def _conectar_por_ip_si_http(url, direcciones_validas):
    """Mitigación del TOCTOU entre `_validar_host` y la conexión real (gap #34, riesgo residual
    documentado): si el esquema es `http` y el host es un NOMBRE (no ya un literal IP), la
    conexión TCP se hace contra una de las IPs YA VALIDADAS, preservando la cabecera `Host`
    original para que el servidor siga viendo el mismo virtual host. Para `https` esto rompe la
    validación del certificado (SNI se negocia contra la IP, no el nombre) y NO se aplica: el
    riesgo de que la IP cambie entre la validación y el `connect()` queda como residual para
    `https`, aceptable porque el invariante local/privado del repo ya exige que el endpoint sea
    loopback/privado (superficie de ataque acotada a la propia red del proyecto)."""
    partes = urllib.parse.urlsplit(url)
    if partes.scheme != "http" or not partes.hostname or not direcciones_validas:
        return url, None
    try:
        ipaddress.ip_address(partes.hostname)
        return url, None  # ya es un literal IP: nada que sustituir
    except ValueError:
        pass
    ip = direcciones_validas[0]
    netloc = f"[{ip}]" if ":" in ip else ip
    if partes.port:
        netloc += f":{partes.port}"
    host_cabecera = partes.hostname + (f":{partes.port}" if partes.port else "")
    return partes._replace(netloc=netloc).geturl(), host_cabecera


def _sanear_url_para_mensaje(url):
    """Nunca imprime userinfo (gap #43) ni bytes no confiables (gap #41) en un mensaje de error:
    reconstruye la URL sin credenciales y aplica `_sanear_detalle` (control/ANSI fuera, tope de
    200 caracteres) sobre el resultado."""
    try:
        partes = urllib.parse.urlsplit(url)
    except ValueError:
        return _sanear_detalle(url)
    if partes.username or partes.password:
        netloc = (partes.hostname or "") + (f":{partes.port}" if partes.port else "")
        partes = partes._replace(netloc=netloc)
    return _sanear_detalle(partes.geturl())


# --8<-- sanear_detalle (funcion) — REPLICADO LITERAL en skills/knowledge-services/backends/markdown_export.py y skills/knowledge-services/backends/graphiti.py
_CONTROL_O_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]|[\x00-\x1f\x7f]")
_SANEADO_TOPE_CHARS = 200


def _sanear_detalle(texto):
    """Recorta a 200 caracteres y sustituye caracteres de control (incluidas las secuencias ANSI
    `ESC[...`) por un espacio; ver comentario arriba para el porqué de cada regla."""
    saneado = _CONTROL_O_ANSI_RE.sub(" ", str(texto))
    return saneado[:_SANEADO_TOPE_CHARS]
# --8<-- fin sanear_detalle (funcion)


class _SinRedireccionAutomatica(urllib.request.HTTPRedirectHandler):
    """`urllib` nunca sigue una redireccion por su cuenta: cada salto se revalida contra
    `_host_permitido` antes de seguirse (un `Location` no confiable no debe escapar del
    guardarrail de red, CA-09)."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: N802 - API de urllib
        return None


def _url_mcp(endpoint):
    """El endpoint del protocolo MCP es SIEMPRE `/mcp` (sin barra); si `endpoint` ya la trae tal
    cual (con o sin barra final) se usa LITERAL -CA-15, "la URL configurada se usa tal cual"- y
    es responsabilidad de `_post_json` seguir el `307`/`308` que el servidor pueda devolver desde
    `/mcp/` hacia `/mcp`. Solo se completa la ruta cuando el `endpoint` no la trae en absoluto."""
    sin_barra = endpoint.rstrip("/")
    if sin_barra.endswith("/mcp"):
        return endpoint
    return sin_barra + "/mcp"


def _post_json(url, payload, cabeceras, timeout_s, allow_remote):
    """POST JSON con seguimiento MANUAL de redirecciones: SOLO 307/308 se siguen (preservan el
    método; 301/302/303 se tratan como error citando la URL — gap #34d, antes se seguían los
    cinco códigos re-POSTeando el cuerpo completo a un destino no confiable), como máximo
    `_MAX_REDIRECCIONES` saltos, revalidando `_validar_host` en CADA salto y sin reenviar
    `Mcp-Session-Id` si el salto cambia de host (gap #34e/M3/M4). Comparte un único presupuesto de
    tiempo total (`deadline`, no por salto)."""
    opener = urllib.request.build_opener(_SinRedireccionAutomatica)
    cuerpo = json.dumps(payload).encode("utf-8")
    url_actual = url
    cabeceras_actuales = dict(cabeceras)
    try:
        host_original = urllib.parse.urlsplit(url).hostname
    except ValueError:
        host_original = None
    deadline = time.monotonic() + timeout_s
    for _ in range(_MAX_REDIRECCIONES + 1):
        direcciones = _validar_host(url_actual, allow_remote)
        if direcciones is None:
            raise HostNoPermitido(_sanear_url_para_mensaje(url_actual))
        restante = deadline - time.monotonic()
        if restante <= 0:
            raise TimeoutError(f"timeout MCP agotado contra {_sanear_url_para_mensaje(url_actual)}")
        url_conexion, host_cabecera = _conectar_por_ip_si_http(url_actual, direcciones)
        req = urllib.request.Request(url_conexion, data=cuerpo, headers=cabeceras_actuales, method="POST")
        if host_cabecera:
            req.add_unredirected_header("Host", host_cabecera)
        try:
            return opener.open(req, timeout=restante)
        except urllib.error.HTTPError as e:
            location = e.headers.get("Location") if e.headers else None
            if not location:
                raise
            if e.code not in (307, 308):
                raise ErrorMCP(
                    f"redireccion HTTP {e.code} no soportada (solo se siguen 307/308): "
                    f"{_sanear_url_para_mensaje(url_actual)} -> {_sanear_url_para_mensaje(location)}")
            nueva_url = urllib.parse.urljoin(url_actual, location)
            try:
                host_nuevo = urllib.parse.urlsplit(nueva_url).hostname
            except ValueError:
                host_nuevo = None
            if host_nuevo != host_original:
                cabeceras_actuales.pop("Mcp-Session-Id", None)
            url_actual = nueva_url
            continue
    raise ErrorMCP(f"demasiadas redirecciones ({_MAX_REDIRECCIONES}) siguiendo {_sanear_url_para_mensaje(url)}")


def _leer_respuesta_mcp(resp):
    """Las respuestas MCP llegan como `application/json` o como `text/event-stream` (SSE, lineas
    `data: <json>`); se devuelve `(cuerpo_parseado_o_None, session_id_o_None)`."""
    tipo = (resp.headers.get_content_type() if hasattr(resp.headers, "get_content_type")
            else resp.headers.get("Content-Type", ""))
    crudo = resp.read().decode("utf-8", errors="replace")
    session_id = resp.headers.get("Mcp-Session-Id")
    if "text/event-stream" in (tipo or ""):
        # gap #38: un evento SSE puede traer el JSON partido en VARIAS lineas `data:` (se
        # concatenan con "\n", spec SSE); antes solo se guardaba la ULTIMA linea `data:` de todo
        # el cuerpo, perdiendo el resto si el JSON estaba partido en mas de una linea o si habia
        # mas de un evento en el cuerpo. Se acumula por evento (separado por linea en blanco) y
        # se devuelve el ULTIMO evento no vacio (el resultado final de la peticion).
        eventos = []
        actual = []
        for linea in crudo.splitlines():
            if linea.strip() == "":
                if actual:
                    eventos.append("\n".join(actual))
                    actual = []
                continue
            if linea.startswith("data:"):
                actual.append(linea[len("data:"):].lstrip(" "))
        if actual:
            eventos.append("\n".join(actual))
        eventos = [e for e in eventos if e.strip()]
        if not eventos:
            return None, session_id
        return json.loads(eventos[-1]), session_id
    if not crudo.strip():
        return None, session_id
    return json.loads(crudo), session_id


class ClienteMCP:
    """Cliente MCP streamable-HTTP minimo: `initialize` -> `notifications/initialized` ->
    `tools/call`, con `Mcp-Session-Id` capturado del handshake y reenviado en toda llamada
    posterior."""

    def __init__(self, endpoint, timeout_s=3.0, allow_remote=False):
        self._url = _url_mcp(endpoint)
        self._timeout_s = timeout_s
        self._allow_remote = allow_remote
        self._session_id = None
        self._siguiente_id = 1

    def _cabeceras(self):
        cabeceras = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self._session_id:
            cabeceras["Mcp-Session-Id"] = self._session_id
        return cabeceras

    def _llamar(self, payload, _reintentar_sesion=True):
        """Gap #49: si el servidor ya olvido la sesion (`Mcp-Session-Id` caducado/desconocido)
        responde 404/400 en vez de re-emitir una sesion nueva; sin este reintento, esa condicion
        se colaba hasta el llamador como un `HTTPError` crudo aunque re-`initialize()`-arse
        resuelve el problema. Se reintenta UNA sola vez (`_reintentar_sesion=False` en el
        reintento) para no entrar en bucle si el servidor esta realmente caido."""
        try:
            resp = _post_json(self._url, payload, self._cabeceras(), self._timeout_s, self._allow_remote)
        except urllib.error.HTTPError as e:
            if _reintentar_sesion and self._session_id and e.code in (400, 404):
                self._session_id = None
                self.initialize()
                return self._llamar(payload, _reintentar_sesion=False)
            raise
        try:
            cuerpo, session_id = _leer_respuesta_mcp(resp)
        finally:
            resp.close()
        if session_id:
            self._session_id = session_id
        return cuerpo

    def _peticion(self, metodo, params=None):
        payload = {"jsonrpc": "2.0", "id": self._siguiente_id, "method": metodo}
        self._siguiente_id += 1
        if params is not None:
            payload["params"] = params
        cuerpo = self._llamar(payload)
        if cuerpo is None:
            raise ErrorMCP(f"respuesta vacia de `{metodo}`")
        if "error" in cuerpo:
            raise ErrorMCP(f"MCP `{metodo}` -> {cuerpo['error']}")
        return cuerpo.get("result")

    def _notificacion(self, metodo, params=None):
        payload = {"jsonrpc": "2.0", "method": metodo}
        if params is not None:
            payload["params"] = params
        self._llamar(payload)  # sin `id`: no se exige `result`, solo confirma el transporte

    def initialize(self, client_name="custom-agents", client_version="1.0"):
        resultado = self._peticion("initialize", {
            "protocolVersion": _PROTOCOLO_MCP,
            "capabilities": {},
            "clientInfo": {"name": client_name, "version": client_version},
        })
        self._notificacion("notifications/initialized")
        return resultado

    def tools_list(self):
        return self._peticion("tools/list")

    def tools_call(self, nombre, argumentos=None):
        """Gap #33 (Critical): `tools/call` puede devolver un `result` valido a nivel JSON-RPC
        pero con `isError: true` a nivel de HERRAMIENTA (el servidor Graphiti asi informa fallos
        de la propia tool, p. ej. `add_memory` con datos invalidos) — sin este chequeo, esas
        llamadas se contaban como aplicadas con exito en `apply()` en vez de caer a
        `fallidos`/dead-letter."""
        resultado = self._peticion("tools/call", {"name": nombre, "arguments": argumentos or {}})
        if isinstance(resultado, dict) and resultado.get("isError"):
            contenido = _contenido_tool_call(resultado)
            detalle = contenido if contenido is not None else resultado.get("content")
            raise ErrorMCP(f"tool `{nombre}` devolvio isError=true: {_sanear_detalle(detalle)}")
        return resultado

    def get_status(self):
        return self.tools_call("get_status", {})


def _contenido_tool_call(resultado):
    """Un resultado de `tools/call` trae `structuredContent` (dict/list ya parseado) o
    `content[].text` (JSON como cadena, hay que parsearlo); se prueban ambas formas."""
    if not isinstance(resultado, dict):
        return None
    estructurado = resultado.get("structuredContent")
    if estructurado is not None:
        return estructurado
    contenido = resultado.get("content")
    if isinstance(contenido, list):
        for bloque in contenido:
            if isinstance(bloque, dict) and bloque.get("type") == "text":
                try:
                    return json.loads(bloque.get("text", ""))
                except (ValueError, TypeError):
                    continue
    return None


def _timeout_s(cfg, clave="timeout_ms", default_ms=3000):
    valor = (cfg or {}).get(clave, default_ms)
    if isinstance(valor, bool) or not isinstance(valor, (int, float)) or valor <= 0:
        valor = default_ms
    return max(valor / 1000.0, 0.01)


def _get_health_endpoint(url, timeout_s, allow_remote, _saltos=0):
    """GET simple contra `health.url` (endpoint de liveness separado del protocolo MCP, si el
    proyecto lo declara); sigue como maximo `_MAX_REDIRECCIONES` saltos, SOLO 307/308 (gap #34d,
    mismo criterio que `_post_json`: 301/302/303 no se siguen, se informan como error), revalidando
    `_validar_host` en cada salto y conectando por IP validada si el esquema es `http`."""
    direcciones = _validar_host(url, allow_remote)
    if direcciones is None:
        return {"estado": "error", "detalle": f"host no local/privado, rechazado: {_sanear_url_para_mensaje(url)}"}
    opener = urllib.request.build_opener(_SinRedireccionAutomatica)
    url_conexion, host_cabecera = _conectar_por_ip_si_http(url, direcciones)
    req = urllib.request.Request(url_conexion, method="GET")
    if host_cabecera:
        req.add_unredirected_header("Host", host_cabecera)
    try:
        with opener.open(req, timeout=timeout_s) as resp:
            cuerpo = resp.read()
    except urllib.error.HTTPError as e:
        location = e.headers.get("Location") if e.headers else None
        if location and e.code in (307, 308) and _saltos < _MAX_REDIRECCIONES:
            destino = urllib.parse.urljoin(url, location)
            return _get_health_endpoint(destino, timeout_s, allow_remote, _saltos + 1)
        if location and e.code not in (307, 308):
            return {"estado": "error",
                    "detalle": f"redireccion HTTP {e.code} no soportada (solo 307/308) de "
                               f"{_sanear_url_para_mensaje(url)}"}
        return {"estado": "degradado" if 500 <= e.code < 600 else "error",
                "detalle": f"HTTP {e.code} de {_sanear_url_para_mensaje(url)}"}
    except (urllib.error.URLError, TimeoutError, socket.timeout, http.client.HTTPException, OSError) as e:
        # gap #41: `e` puede llevar bytes CRUDOS de lo que respondió el servidor (p. ej.
        # `BadStatusLine` incluye la primera línea recibida tal cual) — se sanea antes de exponerlo.
        return {"estado": "off",
                "detalle": f"sin conexion a {_sanear_url_para_mensaje(url)}: {type(e).__name__}: {_sanear_detalle(e)}"}
    try:
        datos = json.loads(cuerpo.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as e:
        return {"estado": "error", "detalle": f"respuesta no JSON de {_sanear_url_para_mensaje(url)}: {_sanear_detalle(e)}"}
    sano = isinstance(datos, dict) and datos.get("status") == "ok"
    return {"estado": "sano" if sano else "degradado",
            "detalle": json.dumps(datos, ensure_ascii=False) if isinstance(datos, (dict, list)) else str(datos)}


def _modo(cfg):
    """`mode` normalizado (`off`/`shadow`/`read`), default `shadow` (mismo default que el
    esquema). Gap #35: antes se validaba pero nadie lo LEIA -`off` seguia sincronizando y
    `rebuild` seguia ejecutando `clear_graph`-."""
    modo = (cfg or {}).get("mode")
    return modo if modo in ("off", "shadow", "read") else "shadow"


def _aplicar_telemetria(cfg):
    """Gap #45: `telemetria` (bool, `design.md:47`) se traduce a la variable de entorno
    `GRAPHITI_TELEMETRY_ENABLED` que lee el SDK/servidor Graphiti ANTES de abrir cualquier
    conexion MCP -no hay otro punto de extension en este cliente minimo para comunicarlo-."""
    os.environ["GRAPHITI_TELEMETRY_ENABLED"] = "true" if bool((cfg or {}).get("telemetria")) else "false"


def health(cfg):
    """Nunca lanza (contrato de adaptador, design.md): `health.url` (si esta declarada, GET
    simple) + `get_status` via MCP (`initialize` -> `tools/call get_status`)."""
    cfg = cfg or {}
    if _modo(cfg) == "off":
        return {"estado": "off", "detalle": "off por configuracion (mode=off)"}
    _aplicar_telemetria(cfg)
    endpoint = cfg.get("endpoint")
    if not endpoint:
        return {"estado": "off", "detalle": "sin `endpoint` configurado"}
    allow_remote = bool(cfg.get("allow_remote", False))
    health_cfg = cfg.get("health") or {}
    detalle_get = None
    if health_cfg.get("url"):
        veredicto_get = _get_health_endpoint(
            health_cfg["url"], _timeout_s(health_cfg, "timeout_ms", 800), allow_remote)
        if veredicto_get["estado"] in ("off", "error"):
            return veredicto_get
        detalle_get = veredicto_get["detalle"]

    try:
        cliente = ClienteMCP(endpoint, timeout_s=_timeout_s(cfg), allow_remote=allow_remote)
        cliente.initialize()
        resultado = cliente.get_status()
    except HostNoPermitido as e:
        return {"estado": "error", "detalle": f"host no local/privado, rechazado: {_sanear_detalle(e)}"}
    except urllib.error.HTTPError as e:
        return {"estado": "degradado" if 500 <= e.code < 600 else "error",
                "detalle": f"HTTP {e.code} de {_sanear_url_para_mensaje(endpoint)}"}
    except (urllib.error.URLError, TimeoutError, socket.timeout, http.client.HTTPException, OSError) as e:
        return {"estado": "off",
                "detalle": f"sin conexion a {_sanear_url_para_mensaje(endpoint)}: {type(e).__name__}: {_sanear_detalle(e)}"}
    except (ErrorMCP, ValueError) as e:
        return {"estado": "error", "detalle": f"{type(e).__name__}: {_sanear_detalle(e)}"}

    contenido = _contenido_tool_call(resultado) or {}
    status = contenido.get("status") if isinstance(contenido, dict) else None
    detalle = f"get_status={status}" + (f"; health.url={detalle_get}" if detalle_get else "")
    if status == "ok":
        return {"estado": "sano", "detalle": detalle}
    if status in (None, "degraded"):
        return {"estado": "degradado", "detalle": detalle}
    return {"estado": "error", "detalle": detalle}


# ---------------------------------------------------------------------------
# Manifiesto local (`.claude/knowledge-services/graphiti-manifest.json`): patron diario
# pendiente -> publicado calcado de `markdown_export.py` (T-05). Da idempotencia PROPIA a
# `apply()` (mismas `entries` -> nada que reenviar) ante reintentos externos de `knowledge-sync.py`
# (el reintento/dead-letter de `outbox.py` vive una capa por encima, ver docstring del modulo).
# ---------------------------------------------------------------------------

def _manifest_dir(cfg):
    return os.path.join(cfg.get("_root") or ".", ".claude", "knowledge-services")


def _manifest_path(cfg, sufijo=""):
    return os.path.join(_manifest_dir(cfg), f"graphiti-manifest{sufijo}.json")


def _leer_manifest(cfg):
    """Si hay una publicacion interrumpida (`.pending`), ES el objetivo de comparacion -asi una
    corrida que retoma completa exactamente lo que faltaba, no repite ni pierde nada-; si no,
    el manifiesto publicado. Devuelve `(datos, era_pendiente)`."""
    ruta_pending = _manifest_path(cfg, ".pending")
    ruta_pub = _manifest_path(cfg)
    ruta = ruta_pending if os.path.isfile(ruta_pending) else ruta_pub
    if not os.path.isfile(ruta):
        return {"group_id": None, "entradas": {}}, (ruta == ruta_pending)
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            datos = json.load(f)
    except (ValueError, OSError):
        return {"group_id": None, "entradas": {}}, (ruta == ruta_pending)
    if not isinstance(datos, dict) or not isinstance(datos.get("entradas"), dict):
        return {"group_id": None, "entradas": {}}, (ruta == ruta_pending)
    return datos, (ruta == ruta_pending)


def _escribir_manifest(cfg, datos, sufijo=""):
    directorio = _manifest_dir(cfg)
    os.makedirs(directorio, exist_ok=True)
    ruta = _manifest_path(cfg, sufijo)
    tmp = ruta + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2, sort_keys=True)
    os.replace(tmp, ruta)
    return ruta


def _uuid_episodio(group_id, knowledge_id, version):
    return str(uuid.uuid5(_NAMESPACE_EPISODIOS, f"{group_id}:{knowledge_id}:{version}"))


def _uuid_tombstone(group_id, knowledge_id):
    return str(uuid.uuid5(_NAMESPACE_EPISODIOS, f"{group_id}:{knowledge_id}:tombstone"))


def plan(entries, cfg, force=False):
    """Puro/idempotente: mismas `entries` -> mismos `ops`. Compara contra el manifiesto OBJETIVO
    (pendiente si hay una publicacion interrumpida, publicado si no) para decidir que entradas
    cambiaron (hash+version) y que ids quedaron fuera de `approved/` (-> `revoke`). `force=True`
    (usado por `rebuild`) trata TODO como `upsert` y omite los `revoke` (el grafo se vacia antes)."""
    cfg = cfg or {}
    group_id = cfg.get("group_id")
    if not group_id:
        raise ConfigInvalida("`group_id` vacio: no se puede planificar sin un grupo estable")
    manifest, _pendiente = _leer_manifest(cfg)
    objetivo = manifest.get("entradas") or {}
    ops = []
    vistos = set()
    for entrada in sorted(entries, key=lambda e: e["id"]):
        id_ = entrada["id"]
        vistos.add(id_)
        version = entrada.get("version")
        cuerpo = entrada.get("cuerpo") or ""
        hash_ = hashlib.sha256(cuerpo.encode("utf-8")).hexdigest()
        previo = objetivo.get(id_)
        if not force and previo and previo.get("version") == version and previo.get("hash") == hash_:
            continue
        ops.append({
            "tipo": "upsert", "id": id_, "version": version, "hash": hash_,
            "category": entrada.get("category"), "evidencia": entrada.get("evidencia"),
            "fuentes": entrada.get("fuentes") or [], "ruta": entrada.get("ruta"),
            "resumen": entrada.get("resumen"), "modo": entrada.get("modo"), "cuerpo": cuerpo,
        })
    if not force:
        for id_ in sorted(set(objetivo) - vistos):
            ops.append({"tipo": "revoke", "id": id_})
    return ops


_DELIM_PROVENIENCIA = "--- procedencia ---"
_DELIM_CONTENIDO = "--- contenido ---"


def _escapar_delimitador(texto, delimitador):
    """Gap #42: si el cuerpo del episodio empieza por (o contiene) el propio delimitador, un
    cuerpo hostil podia falsificar procedencia insertando un segundo bloque `knowledge_id: …
    status: aprobado …` que el extractor server-side leeria como si fuera la cabecera real. Se
    escapa anteponiendo un backslash a cualquier aparicion literal del delimitador dentro del
    cuerpo NO CONFIABLE."""
    return texto.replace(delimitador, "\\" + delimitador)


def _episodio_upsert(group_id, op, cfg=None):
    """CA-13 (gap #36): el episodio lleva `category` y `entity_type` (resuelto contra
    `backends.graphiti.config.entity_map` via `graphiti_model.tipo_entidad`) ademas del `hash`
    del aprobado, y `hash_enviado` -el hash de lo que REALMENTE viaja al servidor, que con
    `modo: resumen` es distinto del `hash` del cuerpo completo (T-05 lo necesita para detectar
    cambios que solo afectan al resumen)."""
    cfg = cfg or {}
    cuerpo_texto = op.get("resumen") if op.get("modo") == "resumen" and op.get("resumen") else op["cuerpo"]
    hash_enviado = hashlib.sha256(cuerpo_texto.encode("utf-8")).hexdigest()
    categoria = op.get("category")
    entity_type = _gm.tipo_entidad(categoria, cfg)
    # Gap #42: bloque de procedencia DELIMITADO (nunca texto plano concatenado sin marca), con el
    # cuerpo NO CONFIABLE escapado si contiene alguno de los delimitadores.
    proveniencia = (
        f"{_DELIM_PROVENIENCIA}\n"
        f"knowledge_id: {op['id']}\nversion: {op['version']}\nstatus: aprobado\n"
        f"category: {categoria}\nentity_type: {entity_type}\n"
        f"evidence_level: {op.get('evidencia')}\nsource_path: {op.get('ruta')}\nhash: {op['hash']}\n"
        f"{_DELIM_CONTENIDO}\n"
    )
    cuerpo_escapado = _escapar_delimitador(_escapar_delimitador(cuerpo_texto, _DELIM_PROVENIENCIA), _DELIM_CONTENIDO)
    return {
        "name": f"{op['id']}@{op['version']}",
        "episode_body": proveniencia + cuerpo_escapado,
        "group_id": group_id,
        "source": "text",
        "source_description": "custom-agents:graphiti-memory",
        "uuid": _uuid_episodio(group_id, op["id"], op["version"]),
        "category": categoria,
        "entity_type": entity_type,
        "hash_enviado": hash_enviado,
    }


def _aplicar_upsert(cliente, proveedor, provider_cfg, group_id, op, cfg=None, entrada_previa=None):
    """Gap #40: si `entrada_previa` (la versión publicada anterior de este `id`) existe y su
    `version` cambió, se emite ADEMÁS un tombstone de esa versión anterior + `SUPERSEDES` hacia
    ella (sucesión observable, CA-11) — el nuevo episodio nunca sustituye a la anterior en
    silencio."""
    episodio = proveedor(provider_cfg, _episodio_upsert(group_id, op, cfg))
    # Gap #46 (CA-14): un proveedor que devuelve una estructura invalida (falta `name`,
    # `episode_body` o `group_id`, p. ej. un bug de un proveedor futuro) NUNCA debe llegar a
    # `add_memory` -se rechaza aqui y la op cae a `fallidos`/dead-letter como cualquier otro
    # `ErrorMCP`, sin gastar una llamada de red con datos incompletos.
    if not isinstance(episodio, dict) or not episodio.get("name") or not episodio.get("episode_body") \
            or not episodio.get("group_id"):
        raise ErrorMCP(
            f"proveedor devolvio una estructura invalida para `add_memory` (faltan "
            f"name/episode_body/group_id): {_sanear_detalle(episodio)}")
    cliente.tools_call("add_memory", episodio)
    if entrada_previa and entrada_previa.get("version") != op.get("version") and entrada_previa.get("uuid"):
        _tombstone_supersedes(cliente, group_id, op["id"], entrada_previa["uuid"], episodio["uuid"],
                              f"{op['id']} superado por version {op.get('version')}")
    return episodio["uuid"]


def _tombstone_supersedes(cliente, group_id, id_, uuid_anterior, uuid_nuevo, fact):
    """Episodio tombstone de `uuid_anterior` + triplete `SUPERSEDES` (`uuid_nuevo` -> `uuid_anterior`,
    campos `*_uuid`: gap #40, la tool espera `source_node_uuid`/`target_node_uuid`, no
    `*_node_name`). NUNCA llama a `delete_episode` (design.md, enmienda 2026-09-18)."""
    tombstone_uuid = _uuid_tombstone(group_id, f"{id_}:{uuid_anterior}")
    cliente.tools_call("add_memory", {
        "name": f"{id_}@tombstone",
        "episode_body": f"knowledge_id: {id_}\nstatus: invalidado\n\nEntrada retirada o superada.",
        "group_id": group_id,
        "source": "text",
        "source_description": "custom-agents:graphiti-memory",
        "uuid": tombstone_uuid,
    })
    cliente.tools_call("add_triplet", {
        "source_node_uuid": uuid_nuevo,
        "edge_name": "SUPERSEDES",
        "fact": fact,
        "target_node_uuid": uuid_anterior,
        "group_id": group_id,
    })
    return tombstone_uuid


def _aplicar_revoke(cliente, group_id, entrada_previa, id_):
    """Tombstone: un episodio de invalidacion + (si habia un uuid previo publicado) un triplete
    `SUPERSEDES` hacia el. NUNCA llama a `delete_episode` (design.md, enmienda 2026-09-18)."""
    if not entrada_previa:
        return None
    tombstone_uuid = _uuid_tombstone(group_id, id_)
    cliente.tools_call("add_memory", {
        "name": f"{id_}@tombstone",
        "episode_body": f"knowledge_id: {id_}\nstatus: invalidado\n\nEntrada retirada de `approved/`.",
        "group_id": group_id,
        "source": "text",
        "source_description": "custom-agents:graphiti-memory",
        "uuid": tombstone_uuid,
    })
    if entrada_previa.get("uuid"):
        cliente.tools_call("add_triplet", {
            "source_node_uuid": tombstone_uuid,
            "edge_name": "SUPERSEDES",
            "fact": f"{id_} invalidado",
            "target_node_name": entrada_previa["uuid"],
            "group_id": group_id,
        })
    return tombstone_uuid


def apply(ops, cfg):
    """Diario pendiente->publicado (idempotencia PROPIA ante reintentos). Gap #32 (Critical): el
    `.pending` se escribe INCREMENTALMENTE -una vez por op, justo DESPUES de que esa op tuvo
    exito contra el servidor-, nunca el objetivo completo ANTES de tocar el servidor: si el
    proceso muere a mitad (no una excepcion Python capturable, sino un corte/kill real), el
    `.pending` en disco refleja EXACTAMENTE lo que de verdad se aplico hasta ese instante, ni una
    op de mas. Un fallo parcial (excepcion capturada) deja el `.pending` ya coherente -no hace
    falta recalcularlo al final- y levanta para que `knowledge-sync.py` decida el
    reintento/dead-letter (via `outbox.py`, una capa por encima).

    Gap #44 (Minor D): `config.concurrency` (validado por el esquema, entero >= 1) queda
    RESERVADO -no se usa un `ThreadPoolExecutor`- porque el servidor Graphiti de referencia
    (`design.md:77-78`) impone `SEMAPHORE_LIMIT: 1`: paralelizar aqui no ganaria nada y anadiria
    una fuente de fallos parciales intercalados dificil de razonar sobre `.pending`. La cache de
    resolucion DNS (`_resolver_host_cacheado`, TTL corto) es la mitigacion real del coste de
    "una conexion + una resolucion DNS por operacion" que motivo este gap."""
    cfg = cfg or {}
    if _modo(cfg) == "off":
        raise ConfigInvalida("`mode: off`: el adaptador no aplica cambios (gap #35)")
    _aplicar_telemetria(cfg)
    group_id = cfg.get("group_id")
    if not group_id:
        raise ConfigInvalida("`group_id` vacio: no se puede aplicar sin un grupo estable")
    manifest, _pendiente = _leer_manifest(cfg)
    publicado = dict(manifest.get("entradas") or {})

    if not ops:
        _escribir_manifest(cfg, {"group_id": group_id, "entradas": publicado})
        _borrar_pending(cfg)
        return {"aplicados": 0, "revocados": 0}

    allow_remote = bool(cfg.get("allow_remote", False))
    timeout_s = _timeout_s(cfg)
    proveedor = _gp.resolver_proveedor(((cfg.get("provider") or {}).get("llm")) or "none")
    provider_cfg = cfg.get("provider") or {}
    cliente = ClienteMCP(cfg.get("endpoint"), timeout_s=timeout_s, allow_remote=allow_remote)
    cliente.initialize()

    progreso = dict(publicado)  # se muta y se persiste tras CADA op con éxito, no al final
    _escribir_manifest(cfg, {"group_id": group_id, "entradas": progreso}, sufijo=".pending")
    aplicados, revocados, fallidos = 0, 0, []
    for op in ops:
        try:
            if op["tipo"] == "upsert":
                _aplicar_upsert(cliente, proveedor, provider_cfg, group_id, op, cfg=cfg,
                                entrada_previa=publicado.get(op["id"]))
                progreso[op["id"]] = {
                    "version": op["version"], "hash": op["hash"], "category": op.get("category"),
                    "uuid": _uuid_episodio(group_id, op["id"], op["version"]),
                }
                aplicados += 1
            else:
                _aplicar_revoke(cliente, group_id, publicado.get(op["id"]), op["id"])
                progreso.pop(op["id"], None)
                revocados += 1
        except Exception as e:  # noqa: BLE001 - un fallo de una op no debe perder las demas
            fallidos.append({"id": op["id"], "tipo": op["tipo"], "error": f"{type(e).__name__}: {e}"})
            continue
        _escribir_manifest(cfg, {"group_id": group_id, "entradas": progreso}, sufijo=".pending")

    if fallidos:
        raise ErrorMCP(
            f"{len(fallidos)} operacion(es) fallaron; publicacion parcial retenida en "
            f"`graphiti-manifest.pending.json`: {fallidos}")

    _escribir_manifest(cfg, {"group_id": group_id, "entradas": progreso})
    _borrar_pending(cfg)
    return {"aplicados": aplicados, "revocados": revocados}


def _borrar_pending(cfg):
    ruta_pending = _manifest_path(cfg, ".pending")
    if os.path.isfile(ruta_pending):
        os.remove(ruta_pending)


def rebuild(entries, cfg):
    """UNICO camino que llama a `clear_graph`, acotado al `group_id` propio (design.md); vacia el
    manifiesto local a juego y republica todo via `plan(force=True)` + `apply()` — reproduce el
    MISMO hash de manifiesto que la sincronizacion incremental (mismos uuid5 deterministas)."""
    cfg = cfg or {}
    if _modo(cfg) == "off":
        raise ConfigInvalida("`mode: off`: el adaptador no reconstruye el grafo (gap #35)")
    _aplicar_telemetria(cfg)
    group_id = cfg.get("group_id")
    if not group_id:
        raise ConfigInvalida("`group_id` vacio: no se puede reconstruir sin un grupo estable")
    allow_remote = bool(cfg.get("allow_remote", False))
    cliente = ClienteMCP(cfg.get("endpoint"), timeout_s=_timeout_s(cfg), allow_remote=allow_remote)
    cliente.initialize()
    cliente.tools_call("clear_graph", {"group_ids": [group_id]})
    _escribir_manifest(cfg, {"group_id": group_id, "entradas": {}})
    _borrar_pending(cfg)
    ops = plan(entries, cfg, force=True)
    return apply(ops, cfg)


def revoke(knowledge_id, cfg):
    """No-op DECLARADO si `knowledge_id` no esta publicado (contrato de adaptador); si lo esta,
    reusa el diario de `apply()` con una sola operacion `revoke` (misma seguridad ante fallos)."""
    cfg = cfg or {}
    if _modo(cfg) == "off":
        raise ConfigInvalida("`mode: off`: el adaptador no revoca (gap #35)")
    manifest, _pendiente = _leer_manifest(cfg)
    if knowledge_id not in (manifest.get("entradas") or {}):
        return {"revocado": False, "razon": "no publicado", "id": knowledge_id}
    resultado = apply([{"tipo": "revoke", "id": knowledge_id}], cfg)
    return {"revocado": True, "id": knowledge_id, "resultado": resultado}


def puede_leer(cfg):
    """Gap #35: `read` exige `health` sano Y `verify` sin desfase antes de servir lecturas (el
    router de T-07 llamara a esta funcion antes de leer); `shadow`/`off` nunca autorizan lectura
    -`shadow` solo escribe-. Nunca lanza (mismo contrato que `health`/`verify`)."""
    cfg = cfg or {}
    if _modo(cfg) != "read":
        return {"puede": False, "razon": f"mode={_modo(cfg)!r} no autoriza lectura (solo `read`)"}
    veredicto_health = health(cfg)
    if veredicto_health.get("estado") != "sano":
        return {"puede": False, "razon": f"health no sano: {veredicto_health}"}
    veredicto_verify = verify(cfg)
    if veredicto_verify.get("ok") is not True:
        return {"puede": False, "razon": f"verify con desfase o ilegible: {veredicto_verify}"}
    return {"puede": True}


_REMEDIO_DESFASE = ("reindexar: ejecutar `knowledge-sync.py --backend <id>` (o `--rebuild` si el "
                    "desfase persiste); este `verify()` nunca lo ejecuta por su cuenta (CA-16)")
_REMEDIO_PUBLICACION_INCOMPLETA = ("reintentar `knowledge-sync.py --backend <id>`: la publicacion "
                                   "anterior no completo (`graphiti-manifest.pending.json` presente)")


def verify(cfg):
    """Nunca lanza (contrato de adaptador): compara el manifiesto local con `get_episodes` del
    `group_id` propio; NOMBRA el remedio sin ejecutarlo (CA-16)."""
    cfg = cfg or {}
    if os.path.isfile(_manifest_path(cfg, ".pending")):
        return {"ok": False, "razon": "publicacion_incompleta", "desfase": [],
                "remedio": _REMEDIO_PUBLICACION_INCOMPLETA}
    manifest, _pendiente = _leer_manifest(cfg)
    entradas = manifest.get("entradas") or {}
    if not entradas:
        return {"ok": True, "desfase": []}
    group_id = cfg.get("group_id") or manifest.get("group_id")
    if not group_id:
        return {"ok": False, "razon": "sin group_id", "desfase": []}
    allow_remote = bool(cfg.get("allow_remote", False))
    esperados = {f"{id_}@{meta.get('version')}" for id_, meta in entradas.items()}
    nombres_remotos = set()
    otros_grupos = set()
    respuesta_ilegible = False
    try:
        cliente = ClienteMCP(cfg.get("endpoint"), timeout_s=_timeout_s(cfg), allow_remote=allow_remote)
        cliente.initialize()
        # Gap #39: `get_episodes` es una ventana de los MAS RECIENTES, no un filtro por nombre —
        # una entrada antigua real puede quedar fuera de una ventana fija. Se pide una ventana
        # generosa y, si TODAVIA faltan nombres esperados y la respuesta llego "llena" (indicio de
        # que hay mas detras), se AMPLIA la ventana hasta `_MAX_EPISODIOS_VERIFY` o hasta que dos
        # peticiones consecutivas devuelvan el mismo tamano (el servidor ya no tiene mas).
        max_episodes = max(len(entradas) * 2, 50)
        tamano_previo = -1
        for _ in range(4):
            resultado = cliente.tools_call(
                "get_episodes", {"group_ids": [group_id], "max_episodes": max_episodes})
            contenido = _contenido_tool_call(resultado)
            if contenido is None:
                respuesta_ilegible = True
                episodios_remotos = []
            elif isinstance(contenido, list):
                episodios_remotos = contenido
            elif isinstance(contenido, dict):
                episodios_remotos = contenido.get("episodes")
                if episodios_remotos is None:
                    respuesta_ilegible = True
                    episodios_remotos = []
            else:
                respuesta_ilegible = True
                episodios_remotos = []
            nombres_remotos = set()
            otros_grupos = set()
            for ep in episodios_remotos:
                if not isinstance(ep, dict):
                    continue
                grupo_ep = ep.get("group_id")
                if grupo_ep and grupo_ep != group_id:
                    otros_grupos.add(grupo_ep)
                    continue
                if ep.get("name"):
                    nombres_remotos.add(ep["name"])
            faltan = esperados - nombres_remotos
            if not faltan or respuesta_ilegible or len(episodios_remotos) == tamano_previo:
                break
            if len(episodios_remotos) < max_episodes:
                break  # el servidor ya devolvio TODO lo que tiene (menos de lo pedido)
            tamano_previo = len(episodios_remotos)
            max_episodes = min(max_episodes * 4, _MAX_EPISODIOS_VERIFY)
    except Exception as e:  # noqa: BLE001 - verify() nunca lanza (mismo contrato que health())
        return {"ok": False, "razon": f"no se pudo consultar get_episodes: {type(e).__name__}: {_sanear_detalle(e)}",
                "desfase": []}
    if respuesta_ilegible:
        return {"ok": None, "razon": "respuesta de get_episodes ilegible (no es lista ni {\"episodes\": [...]})",
                "desfase": []}
    desfase = [
        {"knowledge_id": id_, "motivo": "episodio no encontrado en el grafo", "remedio": _REMEDIO_DESFASE}
        for id_, meta in sorted(entradas.items())
        if f"{id_}@{meta.get('version')}" not in nombres_remotos
    ]
    salida = {"ok": not desfase, "desfase": desfase}
    if otros_grupos:
        salida["aviso"] = f"el servidor devolvio episodios de otro(s) group_id: {sorted(otros_grupos)}"
    return salida


_MAX_EPISODIOS_VERIFY = 5000  # tope duro de la ampliacion de ventana de get_episodes (gap #39)
