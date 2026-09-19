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


# --8<-- hosts locales COMPARTIDO (graphiti-memory T-01-fix1) — REPLICADO LITERAL en skills/knowledge-services/backends/markdown_export.py, agent-kits/shared/knowledge-schema.py y skills/knowledge-services/backends/graphiti.py
_SUFIJOS_LOCALES = (".test", ".local", ".internal")
_HOSTS_LOCALES_LITERALES = {"localhost", "host.docker.internal"}
# --8<-- fin hosts locales COMPARTIDO

_DNS_TIMEOUT_S = 2.0
_MAX_REDIRECCIONES = 5
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


def _host_permitido(url, allow_remote):
    """True si `url` apunta a un host local/privado (mismo criterio que el adaptador Kwipu) o si
    `allow_remote` lo autoriza explicitamente. Fail-closed: cualquier fallo de parseo/resolucion
    devuelve False."""
    if allow_remote:
        try:
            return urllib.parse.urlsplit(url).scheme in ("http", "https")
        except ValueError:
            return False
    try:
        partes = urllib.parse.urlsplit(url)
    except ValueError:
        return False
    if partes.scheme not in ("http", "https"):
        return False
    host = partes.hostname or ""
    if not host:
        return False
    if host in _HOSTS_LOCALES_LITERALES or host.endswith(_SUFIJOS_LOCALES):
        return True
    try:
        ip = ipaddress.ip_address(host)
        return bool(ip.is_loopback or ip.is_private)
    except ValueError:
        pass
    for direccion in _resolver_host(host):
        try:
            ip = ipaddress.ip_address(direccion)
        except ValueError:
            continue
        if ip.is_loopback or ip.is_private:
            return True
    return False


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
    """POST JSON con seguimiento MANUAL de redirecciones (307/308 preservan el metodo, a
    diferencia de lo que hace `urllib` con 301/302/303 por defecto): revalida `_host_permitido`
    en CADA salto y comparte un unico presupuesto de tiempo total (`deadline`, no por salto)."""
    opener = urllib.request.build_opener(_SinRedireccionAutomatica)
    cuerpo = json.dumps(payload).encode("utf-8")
    url_actual = url
    deadline = time.monotonic() + timeout_s
    for _ in range(_MAX_REDIRECCIONES + 1):
        if not _host_permitido(url_actual, allow_remote):
            raise HostNoPermitido(url_actual)
        restante = deadline - time.monotonic()
        if restante <= 0:
            raise TimeoutError(f"timeout MCP agotado contra {url_actual}")
        req = urllib.request.Request(url_actual, data=cuerpo, headers=cabeceras, method="POST")
        try:
            return opener.open(req, timeout=restante)
        except urllib.error.HTTPError as e:
            if e.code in (301, 302, 303, 307, 308) and e.headers and e.headers.get("Location"):
                url_actual = urllib.parse.urljoin(url_actual, e.headers.get("Location"))
                continue
            raise
    raise ErrorMCP(f"demasiadas redirecciones siguiendo {url}")


def _leer_respuesta_mcp(resp):
    """Las respuestas MCP llegan como `application/json` o como `text/event-stream` (SSE, lineas
    `data: <json>`); se devuelve `(cuerpo_parseado_o_None, session_id_o_None)`."""
    tipo = (resp.headers.get_content_type() if hasattr(resp.headers, "get_content_type")
            else resp.headers.get("Content-Type", ""))
    crudo = resp.read().decode("utf-8", errors="replace")
    session_id = resp.headers.get("Mcp-Session-Id")
    if "text/event-stream" in (tipo or ""):
        datos = None
        for linea in crudo.splitlines():
            linea = linea.strip()
            if linea.startswith("data:"):
                fragmento = linea[len("data:"):].strip()
                if fragmento:
                    datos = fragmento
        if datos is None:
            return None, session_id
        return json.loads(datos), session_id
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

    def _llamar(self, payload):
        resp = _post_json(self._url, payload, self._cabeceras(), self._timeout_s, self._allow_remote)
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
        return self._peticion("tools/call", {"name": nombre, "arguments": argumentos or {}})

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
    proyecto lo declara); sigue como maximo un salto de redireccion manualmente."""
    if not _host_permitido(url, allow_remote):
        return {"estado": "error", "detalle": f"host no local/privado, rechazado: {url}"}
    opener = urllib.request.build_opener(_SinRedireccionAutomatica)
    try:
        with opener.open(urllib.request.Request(url, method="GET"), timeout=timeout_s) as resp:
            cuerpo = resp.read()
    except urllib.error.HTTPError as e:
        if e.code in (301, 302, 303, 307, 308) and e.headers and e.headers.get("Location") and _saltos < _MAX_REDIRECCIONES:
            destino = urllib.parse.urljoin(url, e.headers.get("Location"))
            return _get_health_endpoint(destino, timeout_s, allow_remote, _saltos + 1)
        return {"estado": "degradado" if 500 <= e.code < 600 else "error", "detalle": f"HTTP {e.code} de {url}"}
    except (urllib.error.URLError, TimeoutError, socket.timeout, http.client.HTTPException, OSError) as e:
        return {"estado": "off", "detalle": f"sin conexion a {url}: {type(e).__name__}: {e}"}
    try:
        datos = json.loads(cuerpo.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as e:
        return {"estado": "error", "detalle": f"respuesta no JSON de {url}: {e}"}
    sano = isinstance(datos, dict) and datos.get("status") == "ok"
    return {"estado": "sano" if sano else "degradado",
            "detalle": json.dumps(datos, ensure_ascii=False) if isinstance(datos, (dict, list)) else str(datos)}


def health(cfg):
    """Nunca lanza (contrato de adaptador, design.md): `health.url` (si esta declarada, GET
    simple) + `get_status` via MCP (`initialize` -> `tools/call get_status`)."""
    cfg = cfg or {}
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
        return {"estado": "error", "detalle": f"host no local/privado, rechazado: {e}"}
    except urllib.error.HTTPError as e:
        return {"estado": "degradado" if 500 <= e.code < 600 else "error",
                "detalle": f"HTTP {e.code} de {endpoint}"}
    except (urllib.error.URLError, TimeoutError, socket.timeout, http.client.HTTPException, OSError) as e:
        return {"estado": "off", "detalle": f"sin conexion a {endpoint}: {type(e).__name__}: {e}"}
    except (ErrorMCP, ValueError) as e:
        return {"estado": "error", "detalle": f"{type(e).__name__}: {e}"}

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


def _episodio_upsert(group_id, op):
    cuerpo_texto = op.get("resumen") if op.get("modo") == "resumen" and op.get("resumen") else op["cuerpo"]
    proveniencia = (
        f"knowledge_id: {op['id']}\nversion: {op['version']}\nstatus: aprobado\n"
        f"evidence_level: {op.get('evidencia')}\nsource_path: {op.get('ruta')}\nhash: {op['hash']}\n\n"
    )
    return {
        "name": f"{op['id']}@{op['version']}",
        "episode_body": proveniencia + cuerpo_texto,
        "group_id": group_id,
        "source": "text",
        "source_description": "custom-agents:graphiti-memory",
        "uuid": _uuid_episodio(group_id, op["id"], op["version"]),
    }


def _aplicar_upsert(cliente, proveedor, provider_cfg, group_id, op):
    episodio = proveedor(provider_cfg, _episodio_upsert(group_id, op))
    cliente.tools_call("add_memory", episodio)
    return episodio["uuid"]


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
            "source_node_name": tombstone_uuid,
            "edge_name": "SUPERSEDES",
            "fact": f"{id_} invalidado",
            "target_node_name": entrada_previa["uuid"],
            "group_id": group_id,
        })
    return tombstone_uuid


def apply(ops, cfg):
    """Diario pendiente->publicado (idempotencia PROPIA ante reintentos): escribe el manifiesto
    `.pending` con el OBJETIVO completo ANTES de tocar el servidor, aplica cada op, y solo si
    TODAS tuvieron exito renombra `.pending` -> publicado. Un fallo parcial deja el `.pending`
    reflejando solo lo que SI se aplico -nunca pierde ni corrompe lo publicado antes-, y levanta
    para que `knowledge-sync.py` decida el reintento/dead-letter (via `outbox.py`, una capa por
    encima)."""
    cfg = cfg or {}
    group_id = cfg.get("group_id")
    if not group_id:
        raise ConfigInvalida("`group_id` vacio: no se puede aplicar sin un grupo estable")
    manifest, _pendiente = _leer_manifest(cfg)
    publicado = dict(manifest.get("entradas") or {})
    objetivo = dict(publicado)
    for op in ops:
        if op["tipo"] == "revoke":
            objetivo.pop(op["id"], None)
        else:
            objetivo[op["id"]] = {
                "version": op["version"], "hash": op["hash"], "category": op.get("category"),
                "uuid": _uuid_episodio(group_id, op["id"], op["version"]),
            }
    _escribir_manifest(cfg, {"group_id": group_id, "entradas": objetivo}, sufijo=".pending")

    if not ops:
        _escribir_manifest(cfg, {"group_id": group_id, "entradas": objetivo})
        _borrar_pending(cfg)
        return {"aplicados": 0, "revocados": 0}

    allow_remote = bool(cfg.get("allow_remote", False))
    timeout_s = _timeout_s(cfg)
    proveedor = _gp.resolver_proveedor(((cfg.get("provider") or {}).get("llm")) or "none")
    provider_cfg = cfg.get("provider") or {}
    cliente = ClienteMCP(cfg.get("endpoint"), timeout_s=timeout_s, allow_remote=allow_remote)
    cliente.initialize()

    aplicados, revocados, fallidos = 0, 0, []
    for op in ops:
        try:
            if op["tipo"] == "upsert":
                _aplicar_upsert(cliente, proveedor, provider_cfg, group_id, op)
                aplicados += 1
            else:
                _aplicar_revoke(cliente, group_id, publicado.get(op["id"]), op["id"])
                revocados += 1
        except Exception as e:  # noqa: BLE001 - un fallo de una op no debe perder las demas
            fallidos.append({"id": op["id"], "tipo": op["tipo"], "error": f"{type(e).__name__}: {e}"})

    if fallidos:
        ids_fallidos = {f["id"] for f in fallidos}
        objetivo_parcial = dict(publicado)
        for op in ops:
            if op["id"] in ids_fallidos:
                continue
            if op["tipo"] == "upsert":
                objetivo_parcial[op["id"]] = objetivo[op["id"]]
            else:
                objetivo_parcial.pop(op["id"], None)
        _escribir_manifest(cfg, {"group_id": group_id, "entradas": objetivo_parcial}, sufijo=".pending")
        raise ErrorMCP(
            f"{len(fallidos)} operacion(es) fallaron; publicacion parcial retenida en "
            f"`graphiti-manifest.pending.json`: {fallidos}")

    _escribir_manifest(cfg, {"group_id": group_id, "entradas": objetivo})
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
    manifest, _pendiente = _leer_manifest(cfg)
    if knowledge_id not in (manifest.get("entradas") or {}):
        return {"revocado": False, "razon": "no publicado", "id": knowledge_id}
    resultado = apply([{"tipo": "revoke", "id": knowledge_id}], cfg)
    return {"revocado": True, "id": knowledge_id, "resultado": resultado}


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
    try:
        cliente = ClienteMCP(cfg.get("endpoint"), timeout_s=_timeout_s(cfg), allow_remote=allow_remote)
        cliente.initialize()
        resultado = cliente.tools_call(
            "get_episodes", {"group_ids": [group_id], "max_episodes": max(len(entradas) * 2, 50)})
    except Exception as e:  # noqa: BLE001 - verify() nunca lanza (mismo contrato que health())
        return {"ok": False, "razon": f"no se pudo consultar get_episodes: {type(e).__name__}: {e}",
                "desfase": []}
    contenido = _contenido_tool_call(resultado)
    if isinstance(contenido, list):
        episodios_remotos = contenido
    elif isinstance(contenido, dict):
        episodios_remotos = contenido.get("episodes") or []
    else:
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
    desfase = [
        {"knowledge_id": id_, "motivo": "episodio no encontrado en el grafo", "remedio": _REMEDIO_DESFASE}
        for id_, meta in sorted(entradas.items())
        if f"{id_}@{meta.get('version')}" not in nombres_remotos
    ]
    salida = {"ok": not desfase, "desfase": desfase}
    if otros_grupos:
        salida["aviso"] = f"el servidor devolvio episodios de otro(s) group_id: {sorted(otros_grupos)}"
    return salida
