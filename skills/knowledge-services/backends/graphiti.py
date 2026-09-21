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
import tempfile
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


def _direcciones_de_host(host, timeout_s=_DNS_TIMEOUT_S, cachear=True):
    """Direcciones IP de `host`: si ya es un literal IP se devuelve tal cual (sin red); si es un
    nombre, se RESUELVE SIEMPRE (gap #34: antes, `localhost`/sufijos "conocidos" devolvían `True`
    sin resolver, así que un `307 Location` hacia un host con nombre nunca se comprobaba de
    verdad — se validaba la CADENA, no la IP real a la que apunta ese nombre en ese momento).

    Gap #62 (Minor): la caché de 300s (`_resolver_host_cacheado`) mitigaba el coste de resolver
    DNS en cada salto para `http` -donde `_conectar_por_ip_si_http` conecta por la IP YA
    VALIDADA, así que un rebinding entre la validación y el `connect()` no cuela-, pero para
    `https` esa mitigación NO existe (SNI obliga a conectar por nombre, ver comentario de
    `_conectar_por_ip_si_http`): reutilizar ahí la misma caché de 5 minutos ampliaba la ventana
    de rebinding de "milisegundos entre validar y conectar" a "hasta 300s", sin que la
    validación aportase ninguna garantía real sobre la IP a la que el `connect()` de `https`
    fuera a resolver por su cuenta. `cachear=False` (pasado por `_validar_host` cuando el
    esquema es `https`) fuerza una resolución fresca en cada llamada."""
    try:
        return [str(ipaddress.ip_address(host))]
    except ValueError:
        pass
    if not cachear:
        return _resolver_host(host, timeout_s)
    return _resolver_host_cacheado(host, timeout_s)


# --8<-- direccion prohibida siempre COMPARTIDO (graphiti-memory T-04-fix4, gaps #71/#75) - REPLICADO LITERAL en skills/knowledge-services/backends/graphiti.py y agent-kits/shared/knowledge-schema.py
def _normalizar_ip(ip):
    """Desenvuelve las formas de TRANSICION IPv6 -> IPv4 antes de clasificar una direccion:
    IPv4-mapeada (`::ffff:169.254.169.254`, gap #53), 6to4 (`2002::/16`, gap #71) y Teredo
    (`2001:0::/32`, gap #71; se toma la direccion del CLIENTE, que es la que de verdad se
    contacta). CPython clasifica esas tres formas mirando SOLO el prefijo IPv6 nativo, asi que
    sin desenvolverlas un `2002:a9fe:a9fe::1` (= el endpoint de metadatos `169.254.169.254`) es
    `is_private=True` y se cuela por el guardarrail de red (CWE-918)."""
    mapeada = getattr(ip, "ipv4_mapped", None)
    if mapeada is not None:
        return mapeada
    seis_a_cuatro = getattr(ip, "sixtofour", None)
    if seis_a_cuatro is not None:
        return seis_a_cuatro
    teredo = getattr(ip, "teredo", None)
    if teredo is not None:
        return teredo[1]
    return ip


def _es_transicion_ipv6(ip):
    """True si `ip` es 6to4 o Teredo. Ninguna de las dos es nunca un endpoint local legitimo de
    este proyecto (el invariante es `localhost`/red privada), y las dos las clasifica CPython
    como privadas por su prefijo: se rechazan como clase, no solo cuando lo que envuelven es una
    direccion prohibida."""
    return getattr(ip, "sixtofour", None) is not None or getattr(ip, "teredo", None) is not None


def _direccion_prohibida_siempre(ip):
    """Link-local (`169.254.0.0/16`, `fe80::/10`, tipico endpoint de metadatos de nube), no
    especificada (`0.0.0.0`, `::`) y prefijos de transicion IPv6 (6to4/Teredo) se rechazan
    SIEMPRE, incluso con `allow_remote: true` (gaps #34c y #71): `allow_remote` autoriza salir a
    redes remotas, no a la red de metadatos del propio host ni a direcciones sin sentido como
    destino de conexion."""
    if _es_transicion_ipv6(ip):
        return True
    ip = _normalizar_ip(ip)
    return bool(ip.is_link_local or ip.is_unspecified)
# --8<-- fin direccion prohibida siempre COMPARTIDO


def _direccion_permitida(ip, allow_remote):
    if _direccion_prohibida_siempre(ip):
        return False
    ip = _normalizar_ip(ip)
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
    direcciones = _direcciones_de_host(host, cachear=(partes.scheme != "https"))
    if not direcciones:
        return None  # no resuelto a tiempo, o sin direcciones: fail-closed
    ips = []
    for direccion in direcciones:
        try:
            ip = ipaddress.ip_address(direccion)
        except ValueError:
            return None
        # Gap #71: la AUTORIZACION se decide sobre la direccion TAL CUAL (para que
        # `_direccion_prohibida_siempre` pueda ver que es 6to4/Teredo); lo que se devuelve para
        # conectar es la forma ya normalizada (IPv4 equivalente cuando la hay, gap #53).
        if not _direccion_permitida(ip, allow_remote):
            return None
        ips.append(_normalizar_ip(ip))
    return [str(ip) for ip in ips]


def _host_permitido(url, allow_remote):
    """True si `url` apunta a un host local/privado (o `allow_remote` lo autoriza, salvo las
    direcciones SIEMPRE prohibidas). Ver `_validar_host` para el detalle; esta función es el
    booleano que consumen `health()`/`_get_health_endpoint()`."""
    return _validar_host(url, allow_remote) is not None


def _direcciones_ipv4_primero(direcciones_validas):
    """Ordena las direcciones IPv4 antes que las IPv6 (gap #52, Critical, regresión de #34/#41):
    `_conectar_por_ip_si_http` solo probaba `direcciones_validas[0]`; en Windows/dual-stack,
    `localhost` puede resolver `['::1', '127.0.0.1']` con la IPv6 primero aunque el servidor
    real solo escuche en IPv4, así que la conexión fallaba con la pila real disponible en la
    IP siguiente de la misma lista ya validada."""
    def _familia(ip):
        # Gap #84 (Minor D): la clave es SOLO la familia -`sorted` es estable, asi que dentro de
        # cada familia se conserva el orden que dio `getaddrinfo` (preferencia RFC 6724). Con
        # `(familia, cadena)` se reordenaba por texto y esa preferencia se tiraba a la basura.
        try:
            return 0 if ipaddress.ip_address(ip).version == 4 else 1
        except ValueError:
            return 2
    return sorted(direcciones_validas, key=_familia)


def _conectar_por_ip_si_http(url, direcciones_validas):
    """Mitigación del TOCTOU entre `_validar_host` y la conexión real (gap #34, riesgo residual
    documentado): si el esquema es `http` y el host es un NOMBRE (no ya un literal IP), la
    conexión TCP se hace contra una de las IPs YA VALIDADAS, preservando la cabecera `Host`
    original para que el servidor siga viendo el mismo virtual host. Para `https` esto rompe la
    validación del certificado (SNI se negocia contra la IP, no el nombre) y NO se aplica: el
    riesgo de que la IP cambie entre la validación y el `connect()` queda como residual para
    `https`, aceptable porque el invariante local/privado del repo ya exige que el endpoint sea
    loopback/privado (superficie de ataque acotada a la propia red del proyecto).

    Devuelve una LISTA de candidatos `(url_conexion, host_cabecera)` -gap #52-: antes se devolvía
    un único candidato con `direcciones_validas[0]`, así que si esa IP concreta no aceptaba la
    conexión (pila equivocada, firewall) la petición entera fallaba aunque otra IP YA VALIDADA de
    la misma lista sí funcionara. El llamador (`_post_json`/`_get_health_endpoint`) recorre la
    lista completa, IPv4 primero, y solo propaga el error de la ÚLTIMA IP probada."""
    partes = urllib.parse.urlsplit(url)
    if partes.scheme != "http" or not partes.hostname or not direcciones_validas:
        return [(url, None)]
    try:
        ipaddress.ip_address(partes.hostname)
        return [(url, None)]  # ya es un literal IP: nada que sustituir
    except ValueError:
        pass
    host_cabecera = partes.hostname + (f":{partes.port}" if partes.port else "")
    candidatos = []
    for ip in _direcciones_ipv4_primero(direcciones_validas):
        netloc = f"[{ip}]" if ":" in ip else ip
        if partes.port:
            netloc += f":{partes.port}"
        candidatos.append((partes._replace(netloc=netloc).geturl(), host_cabecera))
    return candidatos


def _sanear_url_para_mensaje(url):
    """Nunca imprime userinfo (gap #43) ni bytes no confiables (gap #41) en un mensaje de error:
    reconstruye la URL sin credenciales y aplica `_sanear_detalle` (control/ANSI fuera, tope de
    200 caracteres) sobre el resultado.

    Gap #63 (Minor, doble fail-open): una URL con userinfo mal formado (p. ej. un `[` suelto
    dentro del usuario/contraseña) hace que `urlsplit` lance `ValueError` -antes, este camino
    devolvía la URL CRUDA (con las credenciales embebidas) saneada solo por longitud/caracteres
    de control, sin quitar el userinfo. Si no se puede ni PARSEAR la URL para quitarle las
    credenciales, no hay forma segura de mostrarla: se devuelve un marcador fijo, nunca la URL
    original."""
    try:
        partes = urllib.parse.urlsplit(url)
    except ValueError:
        return "<url no parseable>"
    if partes.username or partes.password:
        netloc = (partes.hostname or "") + (f":{partes.port}" if partes.port else "")
        partes = partes._replace(netloc=netloc)
    return _sanear_detalle(partes.geturl())


# --8<-- sanear_detalle (funcion) — REPLICADO LITERAL en las CINCO copias declaradas del bloque `sanear_detalle` de agent-kits/shared/copias.json
# Gap #93 (Minor, fix5): la clase [\x00-\x1f\x7f] dejaba pasar tres familias que TAMBIEN
# falsifican una linea de log o invierten visualmente el texto de un mensaje/`causa`: los
# controles C1 (\x80-\x9f, entre ellos CSI \x9b), los separadores Unicode de linea/parrafo
# ( / , que muchos visores rompen como salto de linea) y los controles bidi
# (‪-‮ RLO/LRO..., ⁦-⁩ isolates), con los que un texto hostil del servidor
# puede reordenar lo que el humano lee sin cambiar un solo byte del resto.
_CONTROL_O_ANSI_RE = re.compile(
    r"\x1b\[[0-9;]*[A-Za-z]|[\x00-\x1f\x7f-\x9f  ‪-‮⁦-⁩]")
_SANEADO_TOPE_CHARS = 200


def _sanear_detalle(texto):
    """Recorta a 200 caracteres y sustituye caracteres de control (incluidas las secuencias ANSI
    `ESC[...`, los C1, los separadores Unicode y los controles bidi) por un espacio; ver
    comentario arriba para el porque de cada regla."""
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
    def _origen(u):
        """Gap #78 (Minor, CWE-200): la identidad de un salto es `(esquema, host, puerto)`, no
        solo el hostname — `127.0.0.1:A` y `127.0.0.1:B` son servicios DISTINTOS y la sesion MCP
        no debe cruzar de uno a otro (ni de `https` a `http`)."""
        try:
            partes_u = urllib.parse.urlsplit(u)
        except ValueError:
            return None
        return (partes_u.scheme, partes_u.hostname, partes_u.port)

    origen_actual = _origen(url)
    deadline = time.monotonic() + timeout_s
    for _ in range(_MAX_REDIRECCIONES + 1):
        direcciones = _validar_host(url_actual, allow_remote)
        if direcciones is None:
            raise HostNoPermitido(_sanear_url_para_mensaje(url_actual))
        candidatos = _conectar_por_ip_si_http(url_actual, direcciones)
        redireccion_pendiente = None
        error_conexion = None
        for indice, (url_conexion, host_cabecera) in enumerate(candidatos):
            # Gap #83 (Minor D): el presupuesto es COMPARTIDO -lo que QUEDA se recalcula antes
            # de CADA candidata y de cada salto, y se REPARTE entre las candidatas que faltan-.
            # Antes se calculaba una sola vez por salto y cada IP recibia el tope entero otra
            # vez, asi que `timeout_ms: 3000` con `localhost` dual-stack costaba hasta 6 s. El
            # reparto conserva el fallback del gap #52: una primera IP que se cuelga no puede
            # quedarse con TODO el presupuesto y dejar sin intento a las ya validadas que faltan.
            restante = deadline - time.monotonic()
            if restante <= 0:
                raise TimeoutError(
                    f"timeout MCP agotado contra {_sanear_url_para_mensaje(url_actual)}")
            restante = restante / (len(candidatos) - indice)
            req = urllib.request.Request(
                url_conexion, data=cuerpo, headers=cabeceras_actuales, method="POST")
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
                redireccion_pendiente = location
                break
            except (urllib.error.URLError, OSError, TimeoutError) as e:
                # Gap #52: error de CONEXIÓN (no de protocolo HTTP) con esta IP concreta -se
                # prueba la siguiente IP ya validada de la lista antes de rendirse; solo se
                # propaga si era la ÚLTIMA candidata.
                error_conexion = e
                if indice == len(candidatos) - 1:
                    raise
                continue
        if redireccion_pendiente is not None:
            nueva_url = urllib.parse.urljoin(url_actual, redireccion_pendiente)
            origen_nuevo = _origen(nueva_url)
            # Gap #78: se compara contra el salto ANTERIOR (no contra el primero) y por la terna
            # completa: cualquier cambio de esquema, host o puerto tira la cabecera de sesion.
            if origen_nuevo is None or origen_nuevo != origen_actual:
                cabeceras_actuales.pop("Mcp-Session-Id", None)
            origen_actual = origen_nuevo
            url_actual = nueva_url
            continue
        if error_conexion is not None:
            raise error_conexion
    raise ErrorMCP(f"demasiadas redirecciones ({_MAX_REDIRECCIONES}) siguiendo {_sanear_url_para_mensaje(url)}")


_MAX_RESPUESTA_KB_DEFAULT = 8192  # gap #70: tope duro de lectura de UNA respuesta MCP (8 MiB)
_TROZO_LECTURA_BYTES = 64 * 1024


def _max_respuesta_bytes(cfg):
    """`max_respuesta_kb` (entero > 0, KiB); valor invalido o ausente -> el default (gap #70).
    Mismo criterio de tipo ESTRICTO que el esquema (gap #88): un `float` no es un entero."""
    valor = (cfg or {}).get("max_respuesta_kb", _MAX_RESPUESTA_KB_DEFAULT)
    if isinstance(valor, bool) or not isinstance(valor, int) or valor <= 0:
        valor = _MAX_RESPUESTA_KB_DEFAULT
    return valor * 1024


def _leer_cuerpo_acotado(resp, max_bytes):
    """Gap #70 (Important): la lectura de una respuesta MCP va POR TROZOS y con tope duro — antes
    era un `resp.read()` sin limite en TODAS las llamadas (a diferencia de `health.url`, capado
    en #58): 120 MB anunciados = 240 MB de pico, y un stream infinito daba `MemoryError`, que no
    estaba en los `except` de `health()` (que por contrato NUNCA lanza). Exceder el tope es un
    `ErrorMCP` explicito, nunca un `MemoryError`."""
    trozos = []
    total = 0
    while True:
        trozo = resp.read(_TROZO_LECTURA_BYTES)
        if not trozo:
            break
        total += len(trozo)
        if total > max_bytes:
            raise ErrorMCP(
                f"respuesta MCP mayor que el tope de lectura ({max_bytes} bytes, "
                f"`max_respuesta_kb`): se corta la lectura")
        trozos.append(trozo)
    return b"".join(trozos)


def _leer_respuesta_mcp(resp, id_esperado=None, max_bytes=None):
    """Las respuestas MCP llegan como `application/json` o como `text/event-stream` (SSE, lineas
    `data: <json>`); se devuelve `(cuerpo_parseado_o_None, session_id_o_None)`.

    Gap #51 (Critical, reabre #33/#38): un stream SSE puede traer VARIOS eventos en la misma
    respuesta -el resultado final de la petición Y una `notifications/progress` que el servidor
    Graphiti emite mientras procesa `add_memory`, SIN `id` propio-. Quedarse con el ÚLTIMO evento
    (como hacía la corrección de #38) es tan frágil como quedarse con el primero: si la
    notificación llega DESPUÉS del resultado, sustituye al resultado real y `_peticion` ve un
    dict sin `error` -> `result=None`, así que `tools_call` nunca ve `isError` y la operación se
    cuenta como éxito falso. Con `id_esperado` (siempre que la petición original llevaba `id`,
    es decir, no es una notificación saliente), se selecciona el ÚNICO evento cuyo campo `id`
    coincide con el de la petición y se DESCARTAN el resto (notificaciones del servidor, que no
    llevan `id` o llevan uno distinto). Sin ningún evento con ese `id`, se devuelve `None` (el
    llamador -`_peticion`- ya lo trata como `ErrorMCP`: "respuesta vacia")."""
    tipo = (resp.headers.get_content_type() if hasattr(resp.headers, "get_content_type")
            else resp.headers.get("Content-Type", ""))
    crudo = _leer_cuerpo_acotado(
        resp, max_bytes if max_bytes is not None else _MAX_RESPUESTA_KB_DEFAULT * 1024
    ).decode("utf-8", errors="replace")
    session_id = resp.headers.get("Mcp-Session-Id")
    if "text/event-stream" in (tipo or ""):
        # Un evento SSE puede traer el JSON partido en VARIAS lineas `data:` (se concatenan con
        # "\n", spec SSE): se acumula por evento (separado por linea en blanco).
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
        candidatos = []
        for evento in eventos:
            try:
                candidatos.append(json.loads(evento))
            except ValueError:
                continue
        if id_esperado is not None:
            # Solo el evento cuyo `id` case con el de la petición; se descarta cualquier
            # notificación sin `id` (o con uno distinto) que el servidor haya intercalado.
            for cuerpo in candidatos:
                if isinstance(cuerpo, dict) and cuerpo.get("id") == id_esperado:
                    return cuerpo, session_id
            return None, session_id
        if not candidatos:
            return None, session_id
        return candidatos[-1], session_id
    if not crudo.strip():
        return None, session_id
    cuerpo = json.loads(crudo)
    if id_esperado is not None and isinstance(cuerpo, dict) and "id" in cuerpo \
            and cuerpo.get("id") != id_esperado:
        # JSON simple (no-SSE) con un `id` que no es el nuestro: no debería ocurrir en HTTP
        # (una respuesta por petición), pero fail-closed igual que en el camino SSE.
        return None, session_id
    return cuerpo, session_id


class ClienteMCP:
    """Cliente MCP streamable-HTTP minimo: `initialize` -> `notifications/initialized` ->
    `tools/call`, con `Mcp-Session-Id` capturado del handshake y reenviado en toda llamada
    posterior."""

    def __init__(self, endpoint, timeout_s=3.0, allow_remote=False, max_respuesta_bytes=None):
        self._url = _url_mcp(endpoint)
        self._timeout_s = timeout_s
        self._allow_remote = allow_remote
        self._session_id = None
        self._siguiente_id = 1
        # gap #70: tope duro de lectura por respuesta (`config.max_respuesta_kb`)
        self._max_respuesta_bytes = (max_respuesta_bytes if max_respuesta_bytes
                                      else _MAX_RESPUESTA_KB_DEFAULT * 1024)

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
            # Gap #51: se pasa el `id` de la propia peticion (None para notificaciones) para que
            # el lector SSE descarte cualquier `notifications/progress` intercalada y solo tome
            # el evento que responde a ESTA llamada.
            cuerpo, session_id = _leer_respuesta_mcp(
                resp, id_esperado=payload.get("id"), max_bytes=self._max_respuesta_bytes)
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
        # Gap #51/#66: valida la FORMA del `result` antes de devolverlo -sin esto, un cuerpo
        # bien formado en JSON-RPC pero sin `result` NI `error` (p. ej. una notificacion mal
        # enrutada que coincidio por casualidad con el `id`) se devolvia como `None` silencioso
        # en vez de fallar de forma explicita.
        if not isinstance(cuerpo, dict):
            raise ErrorMCP(f"respuesta de `{metodo}` no es un objeto JSON-RPC valido")
        if "error" in cuerpo:
            # Gap #72 (Important, CWE-117): el `error` viene del SERVIDOR (texto no confiable:
            # secuencias ANSI que borran la pantalla, CRLF que falsifican una linea de log, miles
            # de caracteres) y acababa interpolado CRUDO en stderr y en la `causa` de la
            # dead-letter. Se sanea igual que el resto de texto de red.
            raise ErrorMCP(f"MCP `{metodo}` -> {_sanear_detalle(cuerpo['error'])}")
        if "result" not in cuerpo:
            raise ErrorMCP(f"respuesta de `{metodo}` sin `result` ni `error`")
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


def _desenvolver_result(contenido):
    """T-07 (sonda de solo lectura contra el servidor REAL, 2026-09-21): el servidor envuelve el
    `structuredContent` de las tools cuyo esquema de salida NO es un objeto declarado bajo una
    UNICA clave `result` (`{"result": {"message": ..., "episodes": [...]}}`) — asi responden
    `get_episodes`, `search_nodes` y `search_memory_facts`; `get_status`, en cambio, lo devuelve
    plano (fixture `graphiti-mcp-get-status-2026-09-18.json`). Sin abrir ese envoltorio,
    `verify()`/`_reconciliar_publicado()`/`consultar()` veian "respuesta ilegible" contra el
    servidor real aunque las fixtures del servidor falso (structuredContent plano) pasaran.

    Se abre SOLO el caso inequivoco: un dict con esa unica clave y un dict/lista dentro. Un
    `result` conviviendo con otras claves, o escalar, se devuelve tal cual (podria ser el
    contenido legitimo de otra tool)."""
    if isinstance(contenido, dict) and list(contenido) == ["result"] \
            and isinstance(contenido["result"], (dict, list)):
        return contenido["result"]
    return contenido


def _contenido_tool_call(resultado):
    """Un resultado de `tools/call` trae `structuredContent` (dict/list ya parseado) o
    `content[].text` (JSON como cadena, hay que parsearlo); se prueban ambas formas. El envoltorio
    `{"result": ...}` del servidor real se abre en las dos (ver `_desenvolver_result`)."""
    if not isinstance(resultado, dict):
        return None
    estructurado = resultado.get("structuredContent")
    if estructurado is not None:
        return _desenvolver_result(estructurado)
    contenido = resultado.get("content")
    if isinstance(contenido, list):
        for bloque in contenido:
            if isinstance(bloque, dict) and bloque.get("type") == "text":
                try:
                    return _desenvolver_result(json.loads(bloque.get("text", "")))
                except (ValueError, TypeError):
                    continue
    return None


def _timeout_s(cfg, clave="timeout_ms", default_ms=3000):
    valor = (cfg or {}).get(clave, default_ms)
    if isinstance(valor, bool) or not isinstance(valor, (int, float)) or valor <= 0:
        valor = default_ms
    return max(valor / 1000.0, 0.01)


_MAX_LECTURA_HEALTH_BYTES = 64 * 1024  # gap #58: tope duro de lectura, ver mas abajo


def _get_health_endpoint(url, timeout_s, allow_remote, _saltos=0, _deadline=None):
    """GET simple contra `health.url` (endpoint de liveness separado del protocolo MCP, si el
    proyecto lo declara); sigue como maximo `_MAX_REDIRECCIONES` saltos, SOLO 307/308 (gap #34d,
    mismo criterio que `_post_json`: 301/302/303 no se siguen, se informan como error), revalidando
    `_validar_host` en cada salto y conectando por IP validada si el esquema es `http` (gap #52:
    prueba TODAS las IPs ya validadas, IPv4 primero, no solo la primera de la lista)."""
    # Gap #83 (Minor D): presupuesto de tiempo COMPARTIDO entre candidatas IP y entre saltos de
    # redireccion (antes, cada candidata y cada salto recibian `timeout_s` entero: `/doctor`
    # podia gastar 6,4 s con `timeout_ms: 3000`).
    deadline = _deadline if _deadline is not None else time.monotonic() + timeout_s
    direcciones = _validar_host(url, allow_remote)
    if direcciones is None:
        return {"estado": "error", "detalle": f"host no local/privado, rechazado: {_sanear_url_para_mensaje(url)}"}
    opener = urllib.request.build_opener(_SinRedireccionAutomatica)
    candidatos = _conectar_por_ip_si_http(url, direcciones)
    cuerpo = None
    error_final = None
    for indice, (url_conexion, host_cabecera) in enumerate(candidatos):
        restante = deadline - time.monotonic()
        if restante <= 0:
            return {"estado": "off",
                    "detalle": f"timeout agotado contra {_sanear_url_para_mensaje(url)}"}
        restante = restante / (len(candidatos) - indice)  # gap #83: reparto, ver `_post_json`
        req = urllib.request.Request(url_conexion, method="GET")
        if host_cabecera:
            req.add_unredirected_header("Host", host_cabecera)
        try:
            with opener.open(req, timeout=restante) as resp:
                # Gap #58 (Important): el camino de EXITO leia `resp.read()` sin tope, a
                # diferencia de los caminos de error de esta misma funcion -un endpoint de
                # salud que devuelva un cuerpo enorme (o infinito) podia agotar memoria; se
                # capa a `_MAX_LECTURA_HEALTH_BYTES` igual que hace `verify()` con las paginas.
                cuerpo = resp.read(_MAX_LECTURA_HEALTH_BYTES + 1)  # noqa: S conservado (#58)
            break
        except urllib.error.HTTPError as e:
            location = e.headers.get("Location") if e.headers else None
            if location and e.code in (307, 308) and _saltos < _MAX_REDIRECCIONES:
                destino = urllib.parse.urljoin(url, location)
                return _get_health_endpoint(destino, timeout_s, allow_remote, _saltos + 1,
                                            _deadline=deadline)
            if location and e.code not in (307, 308):
                return {"estado": "error",
                        "detalle": f"redireccion HTTP {e.code} no soportada (solo 307/308) de "
                                   f"{_sanear_url_para_mensaje(url)}"}
            return {"estado": "degradado" if 500 <= e.code < 600 else "error",
                    "detalle": f"HTTP {e.code} de {_sanear_url_para_mensaje(url)}"}
        except (urllib.error.URLError, TimeoutError, socket.timeout, http.client.HTTPException, OSError) as e:
            error_final = e
            if indice == len(candidatos) - 1:
                # gap #41: `e` puede llevar bytes CRUDOS de lo que respondió el servidor (p. ej.
                # `BadStatusLine` incluye la primera línea recibida tal cual) — se sanea antes de
                # exponerlo.
                return {"estado": "off",
                        "detalle": f"sin conexion a {_sanear_url_para_mensaje(url)}: "
                                   f"{type(error_final).__name__}: {_sanear_detalle(error_final)}"}
            continue
    if cuerpo is None:
        return {"estado": "off", "detalle": f"sin conexion a {_sanear_url_para_mensaje(url)}"}
    truncado = len(cuerpo) > _MAX_LECTURA_HEALTH_BYTES
    cuerpo = cuerpo[:_MAX_LECTURA_HEALTH_BYTES]
    try:
        datos = json.loads(cuerpo.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as e:
        return {"estado": "error", "detalle": f"respuesta no JSON de {_sanear_url_para_mensaje(url)}: {_sanear_detalle(e)}"}
    sano = isinstance(datos, dict) and datos.get("status") == "ok" and not truncado
    detalle_bruto = json.dumps(datos, ensure_ascii=False) if isinstance(datos, (dict, list)) else str(datos)
    return {"estado": "sano" if sano else "degradado",
            # Gap #58: el camino de EXITO tambien pasa por `_sanear_detalle` -antes solo lo
            # aplicaban los caminos de error de esta misma funcion, así que un `status`/campo
            # arbitrario del cuerpo de salud (no controlado por el propio proyecto) podía colar
            # secuencias ANSI/control sin filtrar en logs y mensajes.
            "detalle": _sanear_detalle(detalle_bruto)}


# --8<-- modo del backend (funcion publica del contrato, T-08-fix1) — REPLICADO LITERAL en las copias declaradas del bloque `modo_backend` de agent-kits/shared/copias.json
# Gap #109 (Minor, fix1 Fase 3): `capabilities.py` duplicaba el enum y el default de `mode` sin
# declararlo como copia (ADR-016) y ademas llamaba al simbolo PRIVADO `_modo` del adaptador,
# fuera del contrato E16. El adaptador expone `modo(cfg)` -funcion OPCIONAL del contrato,
# documentada en `backends/README.md`- y el respaldo de `capabilities.py` (para cuando el
# adaptador no esta instalado) es ESTE MISMO bloque, declarado en `copias.json`.
_MODOS = ("off", "shadow", "read")
_MODO_DEFAULT = "shadow"


def modo(cfg):
    """`mode` normalizado (`off`/`shadow`/`read`), default `shadow` (el mismo del esquema).
    Gap #35: antes se validaba pero nadie lo LEIA -`off` seguia sincronizando-."""
    valor = (cfg or {}).get("mode")
    return valor if valor in _MODOS else _MODO_DEFAULT
# --8<-- fin modo del backend


_modo = modo   # alias interno historico (este modulo lo usa en health/apply/verify/puede_leer)


def _aplicar_telemetria(cfg):
    """Gap #45: `telemetria` (bool, `design.md:47`) se traduce a la variable de entorno
    `GRAPHITI_TELEMETRY_ENABLED` que lee el SDK/servidor Graphiti ANTES de abrir cualquier
    conexion MCP -no hay otro punto de extension en este cliente minimo para comunicarlo-."""
    os.environ["GRAPHITI_TELEMETRY_ENABLED"] = "true" if bool((cfg or {}).get("telemetria")) else "false"


def proponer_config(taxonomy, cfg):
    """Funcion OPCIONAL del contrato de adaptador (gap #77, Important): el NUCLEO
    (`knowledge-sync.py --propose-config`) no conoce ningun backend concreto -invariante del plan
    (`improvement-plan.md:17`) y de ADR-018/CA-12-, asi que pregunta al adaptador si sabe proponer
    configuracion y, si la funcion existe, delega en ella. Aqui se delega a su vez en
    `graphiti_model.proponer_config` (tipos de entidad por categoria) y se añade `texto`, el
    render legible que el nucleo imprime tal cual cuando no se pide `--json`."""
    propuesta = _gm.proponer_config(taxonomy, cfg or {})
    texto = (
        propuesta["entity_types_yaml"]
        + "\n# entity_map propuesto para backends.<id>.config.entity_map:\n"
        + json.dumps(propuesta["entity_map"], ensure_ascii=False, indent=2)
        + "\n\n" + propuesta["nota"]
    )
    return {**propuesta, "texto": texto}


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
        # Gap #90 (Minor, fix5): `health()` era el UNICO de los cinco constructores de
        # `ClienteMCP` que no propagaba el tope de respuesta -ignoraba `config.max_respuesta_kb`,
        # justo en la funcion que llama `/doctor` (el arbitraje de #70 pedia el tope tambien
        # aqui).
        cliente = ClienteMCP(endpoint, timeout_s=_timeout_s(cfg), allow_remote=allow_remote,
                             max_respuesta_bytes=_max_respuesta_bytes(cfg))
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
    except (ErrorMCP, ValueError, MemoryError) as e:
        # Gap #70: `MemoryError` tambien se captura -una respuesta gigante no puede tumbar
        # `health()`, que por contrato NUNCA lanza (y es lo que llama `/doctor`).
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


def _leer_manifest_de(ruta):
    """Lee y valida un manifiesto en `ruta`; `None` si no existe, esta corrupto o tiene forma
    invalida (fail-closed, nunca lanza)."""
    if not os.path.isfile(ruta):
        return None
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            datos = json.load(f)
    except (ValueError, OSError):
        return None
    if not isinstance(datos, dict) or not isinstance(datos.get("entradas"), dict):
        return None
    return datos


def _leer_manifest(cfg):
    """Si hay una publicacion interrumpida (`.pending`), ES el objetivo de comparacion -asi una
    corrida que retoma completa exactamente lo que faltaba, no repite ni pierde nada-; si no,
    el manifiesto publicado. Devuelve `(datos, era_pendiente)`.

    Gap #65 (Minor): un `.pending` presente pero CORRUPTO/ilegible (proceso cortado a mitad de
    la escritura atomica, disco lleno a medio `os.replace`, etc.) degradaba a un manifiesto
    VACIO como objetivo -`plan()` entonces solo veia "todo nuevo" y NUNCA generaba los `revoke`
    de entradas que de verdad seguian publicadas pero ya no estaban en `entries`, y `apply()`
    con `ops` vacio (nada cambio a ojos de `plan()` salvo esos revokes silenciosamente
    perdidos) sobrescribía el manifiesto PUBLICADO bueno con ese vacío-derivado, perdiendo el
    historial. Ahora, si `.pending` existe pero no es legible, se usa el ULTIMO manifiesto
    PUBLICADO bueno como base -nunca un target vacío- y se sigue marcando "pendiente" (`True`)
    para que `apply()` fuerce la reconciliacion de #54 antes de promoverlo."""
    ruta_pending = _manifest_path(cfg, ".pending")
    ruta_pub = _manifest_path(cfg)
    if os.path.isfile(ruta_pending):
        datos = _leer_manifest_de(ruta_pending)
        if datos is not None:
            return datos, True
        datos_pub = _leer_manifest_de(ruta_pub)
        return (datos_pub if datos_pub is not None else {"group_id": None, "entradas": {}}), True
    datos_pub = _leer_manifest_de(ruta_pub)
    return (datos_pub if datos_pub is not None else {"group_id": None, "entradas": {}}), False


def _escribir_manifest(cfg, datos, sufijo=""):
    """Escritura atomica (`os.replace`) con temporal UNICO en el mismo directorio (gap #81: con
    un `<ruta>.tmp` FIJO, dos `knowledge-sync` concurrentes competian por el mismo fichero —en
    POSIX mezclando JSON, en Windows con un `PermissionError` fuera de todo `try`—; mismo patron
    que `markdown_export.py`, que ya usaba `mkstemp`)."""
    directorio = _manifest_dir(cfg)
    os.makedirs(directorio, exist_ok=True)
    ruta = _manifest_path(cfg, sufijo)
    descriptor, tmp = tempfile.mkstemp(prefix=os.path.basename(ruta) + ".", suffix=".tmp",
                                       dir=directorio)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2, sort_keys=True)
        os.replace(tmp, ruta)
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise
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
    objetivo = _entradas_del_grupo(manifest, group_id)
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
            # Gap #117 (Important, fix2 Fase 3): el `folder` declarado en `taxonomy.json` y los
            # `tags` de la entrada viajan hasta el episodio para que la procedencia lleve el
            # vocabulario del corpus LOCAL (`tipo`/`area`), no solo la clave de taxonomia.
            "folder": entrada.get("folder"), "tags": entrada.get("tags") or [],
        })
    if not force:
        for id_ in sorted(set(objetivo) - vistos):
            ops.append({"tipo": "revoke", "id": id_})
    return ops


def _grupo_del_manifiesto(manifest):
    grupo = (manifest or {}).get("group_id")
    return grupo if isinstance(grupo, str) and grupo else None


def _entradas_del_grupo(manifest, group_id):
    """Gap #73 (Important): el manifiesto pertenece a UN `group_id`. Si el proyecto cambia
    `group_id` en `taxonomy.json`, sus entradas NO describen el grupo nuevo (que esta vacio):
    compararlas dejaba la sincronizacion en un no-op silencioso -grupo nuevo vacio para siempre-
    y ademas conservaba los `uuid` del grupo viejo (un `SUPERSEDES` posterior habria apuntado a
    otro grupo). Con grupo distinto, la base de comparacion es VACIA: todo `upsert`."""
    grupo_previo = _grupo_del_manifiesto(manifest)
    if grupo_previo is not None and group_id and grupo_previo != group_id:
        return {}
    return (manifest or {}).get("entradas") or {}


_DELIM_PROVENIENCIA = "--- procedencia ---"
_DELIM_CONTENIDO = "--- contenido ---"


def _escapar_delimitador(texto, delimitador):
    """Gap #42: si el cuerpo del episodio empieza por (o contiene) el propio delimitador, un
    cuerpo hostil podia falsificar procedencia insertando un segundo bloque `knowledge_id: …
    status: aprobado …` que el extractor server-side leeria como si fuera la cabecera real. Se
    escapa anteponiendo un backslash a cualquier aparicion literal del delimitador dentro del
    cuerpo NO CONFIABLE."""
    return texto.replace(delimitador, "\\" + delimitador)


_EPISODE_BODY_MAX_KB_DEFAULT = 512  # gap #64: tope por defecto si `episode_body_max_kb` no esta declarado


def _tope_episode_body_bytes(cfg):
    """`episode_body_max_kb` (entero > 0, KiB); valor invalido o ausente -> el default."""
    # Gap #88 (Minor): entero ESTRICTO, igual que el esquema (`integer`) -aceptar `float` aqui
    # dejaba que una config RECHAZADA por el validador cambiara el comportamiento del adaptador.
    valor = (cfg or {}).get("episode_body_max_kb", _EPISODE_BODY_MAX_KB_DEFAULT)
    if isinstance(valor, bool) or not isinstance(valor, int) or valor <= 0:
        valor = _EPISODE_BODY_MAX_KB_DEFAULT
    return valor * 1024


_PREFIJO_TAG_AREA = "area:"


def _folder_declarado(op):
    """`categories[].folder` de la entrada (lo que `knowledge-sync.py` trae del indice), o el
    segmento de carpeta de su `ruta` bajo `docs/knowledge/approved/` si la op no lo trae (ops
    construidas a mano en tests o por un llamador antiguo). Nunca inventa un valor: sin ninguna
    de las dos fuentes devuelve `None` y el campo se omite del bloque de procedencia."""
    folder = op.get("folder")
    if isinstance(folder, str) and folder.strip():
        return folder.strip().strip("/").split("/")[0]
    ruta = op.get("ruta")
    if isinstance(ruta, str):
        partes = [p for p in ruta.replace("\\", "/").split("/") if p]
        if len(partes) >= 5 and partes[:3] == ["docs", "knowledge", "approved"]:
            return partes[3]
    return None


def _area_de_entrada(op):
    """`area` de la entrada a partir de sus `tags` `area:<valor>` (la convencion que ya usan las
    entradas de `docs/knowledge/approved/`), o `None`. Varios tags `area:` se unen por espacio:
    el post-filtro del nucleo casa por TOKEN, no por igualdad."""
    tags = op.get("tags")
    if not isinstance(tags, (list, tuple)):
        return None
    valores = [t[len(_PREFIJO_TAG_AREA):].strip() for t in tags
               if isinstance(t, str) and t.lower().startswith(_PREFIJO_TAG_AREA)]
    valores = [v for v in valores if v]
    return " ".join(valores) or None


def _episodio_upsert(group_id, op, cfg=None):
    """CA-13 (gap #36): el episodio lleva `category` y `entity_type` (resuelto contra
    `backends.graphiti.config.entity_map` via `graphiti_model.tipo_entidad`) ademas del `hash`
    del aprobado, y `hash_enviado` -el hash de lo que REALMENTE viaja al servidor, que con
    `modo: resumen` es distinto del `hash` del cuerpo completo (T-05 lo necesita para detectar
    cambios que solo afectan al resumen). Devuelve `(episodio, aviso_tope_o_None)`.

    Gap #64 (Minor): sin tope, un `episode_body` de hasta ~2 MB viajaba INTEGRO al servidor en
    una unica llamada `add_memory` (el arbitraje de #42 ya pedia un tope configurable con aviso).
    `episode_body_max_kb` (config, KiB) acota el tamaño; si se excede, se trunca preservando el
    bloque de procedencia (siempre cabe: es mucho más pequeño que el tope) y se devuelve un aviso
    de texto para que el llamador lo recoja -nunca se lanza una excepcion por esto, es un aviso,
    no un fallo de la operacion."""
    cfg = cfg or {}
    cuerpo_texto = op.get("resumen") if op.get("modo") == "resumen" and op.get("resumen") else op["cuerpo"]
    categoria = op.get("category")
    entity_type = _gm.tipo_entidad(categoria, cfg)
    # Gap #42: bloque de procedencia DELIMITADO (nunca texto plano concatenado sin marca), con el
    # cuerpo NO CONFIABLE escapado si contiene alguno de los delimitadores.
    # Gap #116 (Minor, fix1 Fase 3): un campo nulo se OMITE; antes se interpolaba con f-string y
    # el episodio viajaba con la cadena literal `"None"` como `evidence_level`/`source_path`, que
    # el fail-closed del nucleo aceptaba como si fuera una evidencia y una ruta canonica reales
    # («no se rellena con un valor inventado» decia el docstring de `consultar`, y se rellenaba).
    _campos = [("knowledge_id", op["id"]), ("version", op["version"]), ("status", "aprobado"),
               ("category", categoria), ("entity_type", entity_type),
               # Gap #117 (Important, fix2 Fase 3): la `category` es la clave de taxonomia
               # (`DECISION`/`GOTCHA`/...), un vocabulario que el corpus LOCAL no conoce -el
               # post-filtro `--tipo`/`--area` del nucleo la descartaba SIEMPRE-. `local_folder`
               # es el `categories[].folder` DECLARADO en `taxonomy.json` (`adr`/`gotchas`/
               # `lessons`), que es justo el vocabulario que `knowledge-find.tipo_normalizado`
               # sabe traducir al tipo local; `area` sale de los `tags` `area:<...>` de la propia
               # entrada. Ninguna equivalencia se cablea aqui ni en el nucleo: las dos salen de la
               # taxonomia y del frontmatter del proyecto.
               ("local_folder", _folder_declarado(op)), ("area", _area_de_entrada(op)),
               ("evidence_level", op.get("evidencia")), ("source_path", op.get("ruta")),
               ("hash", op["hash"])]
    proveniencia = _DELIM_PROVENIENCIA + "\n" + "".join(
        f"{clave}: {valor}\n" for clave, valor in _campos
        if valor is not None and str(valor).strip() != "") + _DELIM_CONTENIDO + "\n"
    cuerpo_escapado = _escapar_delimitador(_escapar_delimitador(cuerpo_texto, _DELIM_PROVENIENCIA), _DELIM_CONTENIDO)
    aviso = None
    tope = _tope_episode_body_bytes(cfg)
    # Gap #80 (Minor): se trunca SOLO el contenido -la cabecera de procedencia queda INTACTA-.
    # Antes se truncaba el `episode_body` entero desde el principio, asi que con un tope pequeño
    # y un `id`/`source_path` largos el episodio se quedaba sin `hash:` y sin el delimitador
    # `--- contenido ---` (el docstring decia "siempre cabe", y no era verdad). Si la cabecera
    # SOLA no cabe, es un error declarado, no un episodio mutilado.
    marcador = "\n[... episode_body truncado por episode_body_max_kb ...]"
    proveniencia_bytes = len(proveniencia.encode("utf-8"))
    marcador_bytes = len(marcador.encode("utf-8"))
    if proveniencia_bytes + marcador_bytes > tope:
        raise ErrorMCP(
            f"el bloque de procedencia de `{op['id']}@{op['version']}` ({proveniencia_bytes} bytes) "
            f"no cabe en `episode_body_max_kb` ({tope} bytes): sube el tope o acorta `id`/`ruta`")
    contenido_bytes = cuerpo_escapado.encode("utf-8")
    if proveniencia_bytes + len(contenido_bytes) > tope:
        recorte = tope - proveniencia_bytes - marcador_bytes
        cuerpo_escapado = contenido_bytes[:max(recorte, 0)].decode("utf-8", errors="ignore") + marcador
        aviso = (f"episode_body de `{op['id']}@{op['version']}` truncado de "
                 f"{proveniencia_bytes + len(contenido_bytes)} a {tope} bytes "
                 f"(episode_body_max_kb); el bloque de procedencia se preserva entero")
    episode_body = proveniencia + cuerpo_escapado
    # Gap #80 (b): `hash_enviado` es "el hash de lo que REALMENTE viaja al servidor", asi que se
    # calcula DESPUES de truncar (antes se calculaba sobre el cuerpo completo, contra su propio
    # docstring: dos truncados distintos del mismo cuerpo daban el mismo `hash_enviado`).
    hash_enviado = hashlib.sha256(cuerpo_escapado.encode("utf-8")).hexdigest()
    return {
        "name": f"{op['id']}@{op['version']}",
        "episode_body": episode_body,
        "group_id": group_id,
        "source": "text",
        "source_description": "custom-agents:graphiti-memory",
        "uuid": _uuid_episodio(group_id, op["id"], op["version"]),
        "category": categoria,
        "entity_type": entity_type,
        "hash_enviado": hash_enviado,
    }, aviso


def _nombre_episodio(id_, version):
    """Nombre del episodio tal y como viaja en `add_memory` (`<id>@<version>`): es el
    `source_node_name`/`target_node_name` que `add_triplet` exige por contrato (gap #69)."""
    return f"{id_}@{version}"


def _aplicar_upsert(cliente, proveedor, provider_cfg, group_id, op, cfg=None, entrada_previa=None):
    """Gap #40: si `entrada_previa` (la versión publicada anterior de este `id`) existe y su
    `version` cambió, se emite ADEMÁS un tombstone de esa versión anterior + `SUPERSEDES` hacia
    ella (sucesión observable, CA-11) — el nuevo episodio nunca sustituye a la anterior en
    silencio. Devuelve `(uuid, aviso_tope_o_None)` (gap #64)."""
    # Gap #94 (Minor, fix5): si la entrada previa publicada no trae `version`, el nombre del nodo
    # anterior (`<id>@<version>`) saldria como `<id>@None` — un nodo que no existe en el grafo:
    # `add_triplet` pasaria el `required` del servidor y colgaria el `SUPERSEDES` de un fantasma.
    # No se fabrica: la op cae a `fallidos` con causa explicita ANTES de tocar el servidor.
    if entrada_previa and entrada_previa.get("uuid") and entrada_previa.get("version") is None:
        raise ErrorMCP(
            f"entrada previa de `{op['id']}` sin `version` en el manifiesto: no se puede nombrar "
            f"el episodio anterior para el `SUPERSEDES` (no se inventa un nombre de nodo)")
    episodio_base, aviso_tope = _episodio_upsert(group_id, op, cfg)
    episodio = proveedor(provider_cfg, episodio_base)
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
                              f"{op['id']} superado por version {op.get('version')}",
                              nombre_anterior=_nombre_episodio(op["id"], entrada_previa["version"]),
                              nombre_nuevo=episodio["name"])
    return episodio["uuid"], aviso_tope


_SUFIJO_TOMBSTONE = "@tombstone"      # revoke: invalida la ENTRADA entera (todas sus versiones)
_SUFIJO_SUPERSEDED = "@superseded"    # sucesion: invalida SOLO el episodio de la version superada


def _tombstone_supersedes(cliente, group_id, id_, uuid_anterior, uuid_nuevo, fact,
                          nombre_anterior=None, nombre_nuevo=None):
    """Episodio tombstone de `uuid_anterior` + triplete `SUPERSEDES` (`uuid_nuevo` ->
    `uuid_anterior`).

    Gap #69 (Critical, fix4): el CONTRATO REAL de la tool (fixture capturado
    `fixtures/graphiti/graphiti-mcp-tools-list-2026-09-18.json`) declara
    `required: [source_node_name, edge_name, fact, target_node_name]` y deja los `*_uuid` como
    OPCIONALES — el arbitraje de #40 ("usa `*_uuid`") era incompleto: hay que enviar nombre Y
    uuid. Sin los nombres, el servidor real responde `isError` y TODO camino de
    sucesion/invalidacion (CA-11) caia a `fallidos`/dead-letter. NUNCA llama a `delete_episode`
    (design.md, enmienda 2026-09-18).

    Gap #94 (Minor, fix5): los fallbacks `_nombre_episodio(id_, "anterior"/"actual")` fabricaban
    nombres de nodos INEXISTENTES cuando el llamante no sabia el nombre real; pasaban el
    `required` del servidor y colgaban la arista de un fantasma. Ahora es un error explicito."""
    if not nombre_anterior or not nombre_nuevo:
        raise ErrorMCP(
            f"`SUPERSEDES` de `{id_}` sin los nombres REALES de los nodos (anterior/nuevo): no se "
            f"fabrican nombres (`add_triplet` los exige y uno inventado crea un nodo fantasma)")
    # Gap #96 (Critical, fix1 Fase 3): el tombstone de SUCESION DE VERSION no puede llamarse
    # igual que el de REVOKE (`<id>@tombstone`): `_indice_procedencia` invalidaba por `id`, asi
    # que subir de version dejaba invalidada tambien la version nueva (toda entrada que alguna
    # vez subio de version se servia como `invalidado`). Aqui se nombra la VERSION superada
    # (`<id>@<version>@superseded`), y solo esa; el `@tombstone` queda para el revoke, que si
    # invalida la entrada entera.
    tombstone_uuid = _uuid_tombstone(group_id, f"{id_}:{uuid_anterior}")
    cliente.tools_call("add_memory", {
        "name": f"{nombre_anterior}{_SUFIJO_SUPERSEDED}",
        "episode_body": (f"knowledge_id: {id_}\nepisodio: {nombre_anterior}\n"
                         f"status: invalidado\n\nVersion superada por `{nombre_nuevo}`."),
        "group_id": group_id,
        "source": "text",
        "source_description": "custom-agents:graphiti-memory",
        "uuid": tombstone_uuid,
    })
    cliente.tools_call("add_triplet", {
        "source_node_name": nombre_nuevo,
        "source_node_uuid": uuid_nuevo,
        "edge_name": "SUPERSEDES",
        "fact": fact,
        "target_node_name": nombre_anterior,
        "target_node_uuid": uuid_anterior,
        "group_id": group_id,
    })
    return tombstone_uuid


def _aplicar_revoke(cliente, group_id, entrada_previa, id_):
    """Tombstone: un episodio de invalidacion + (si habia un uuid previo publicado) un triplete
    `SUPERSEDES` hacia el. NUNCA llama a `delete_episode` (design.md, enmienda 2026-09-18).

    Gap #94 (Minor, fix5): con `uuid` previo pero sin `version` en el manifiesto, el
    `target_node_name` salia como `<id>@None` (nodo inexistente): se rechaza antes de emitir
    nada y la op cae a `fallidos` con causa explicita."""
    if not entrada_previa:
        return None
    if entrada_previa.get("uuid") and entrada_previa.get("version") is None:
        raise ErrorMCP(
            f"entrada publicada de `{id_}` sin `version` en el manifiesto: no se puede nombrar el "
            f"episodio a invalidar para el `SUPERSEDES` (no se inventa un nombre de nodo)")
    tombstone_uuid = _uuid_tombstone(group_id, id_)
    cliente.tools_call("add_memory", {
        "name": f"{id_}{_SUFIJO_TOMBSTONE}",
        "episode_body": f"knowledge_id: {id_}\nstatus: invalidado\n\nEntrada retirada de `approved/`.",
        "group_id": group_id,
        "source": "text",
        "source_description": "custom-agents:graphiti-memory",
        "uuid": tombstone_uuid,
    })
    if entrada_previa.get("uuid"):
        cliente.tools_call("add_triplet", {
            # Gap #56 (Important, mutante N6) + gap #69 (Critical, fix4): este camino -el de
            # REVOKE- es DISTINTO del de version-superada y tambien enviaba solo los `*_uuid`.
            # El contrato REAL de `add_triplet` exige los NOMBRES (`required` del fixture
            # `tools/list`) y acepta los uuid como refuerzo: se envian los cuatro campos.
            "source_node_name": f"{id_}{_SUFIJO_TOMBSTONE}",
            "source_node_uuid": tombstone_uuid,
            "edge_name": "SUPERSEDES",
            "fact": f"{id_} invalidado",
            "target_node_name": _nombre_episodio(id_, entrada_previa["version"]),
            "target_node_uuid": entrada_previa["uuid"],
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
    avisos = []
    # Gap #89 (Important, fix5): copia del manifiesto OBJETIVO ANTES de cualquier poda. La
    # reconciliacion de #68 puede quitar de `publicado` una entrada que el servidor no confirma
    # (episodio fuera de la ventana de `get_episodes`, o `uuid` distinto por #79); si esa entrada
    # tiene un `revoke` en `ops`, sus datos (version + uuid) siguen aqui y el tombstone se emite
    # igual. Sin esto, `_aplicar_revoke` recibia `None`, salia sin llamar al servidor y la op se
    # contaba como `revocados`: episodio VIVO e irrevocable en el grafo.
    heredado = dict(manifest.get("entradas") or {})

    # Gap #73 (Important): el manifiesto pertenece a UN `group_id`. Si cambio, su contenido no
    # describe el grupo nuevo: se archiva para poder revocarlo a mano y la base queda vacia.
    grupo_previo = _grupo_del_manifiesto(manifest)
    if grupo_previo is not None and grupo_previo != group_id:
        ruta_archivada = _archivar_manifest_de_otro_grupo(cfg, manifest, grupo_previo)
        avisos.append(
            f"`group_id` cambio de `{grupo_previo}` a `{group_id}`: la base de comparacion queda "
            f"vacia (todo `upsert`) y el manifiesto anterior se conserva en "
            f"`{os.path.basename(ruta_archivada)}` para revocacion manual")
        _borrar_pending(cfg)
        _pendiente = False
        publicado = {}
        # Los `uuid` del manifiesto viejo pertenecen a OTRO `group_id`: no sirven para revocar
        # nada en el grupo actual (gap #73), asi que tampoco se heredan (gap #89).
        heredado = {}
    else:
        publicado = dict(manifest.get("entradas") or {})

    # Gap #68 (Critical): la reconciliacion de #54 se hace SIEMPRE que haya `.pending` heredado
    # -tambien con ops nuevas por delante-, nunca solo en la rama `if not ops`: con >= 1 op, la
    # entrada fantasma se promovia a PUBLICADO con cero confirmaciones y, con hash/version
    # coincidentes, `plan()` no la volvia a proponer jamas.
    if _pendiente and publicado:
        confirmadas, confirmacion_posible = _reconciliar_publicado(cfg, group_id, publicado)
        if not confirmacion_posible:
            # Gap #67 (Critical): si la reconciliacion NO puede confirmar (servidor caido,
            # timeout, respuesta ilegible), no se toca nada -ni el `.pending` ni el publicado-.
            # Antes se escribia el `{}` derivado del fallo como manifiesto PUBLICADO: "no se
            # promueve nada" implementado como "se despublica todo" (episodios irrevocables en
            # el grafo y sin rastro local).
            avisos.append(
                "no se pudo CONFIRMAR contra el servidor el `.pending` heredado: no se toca ni el "
                "pendiente ni el manifiesto publicado; reintenta cuando el servidor responda")
            return {"aplicados": 0, "revocados": 0, "pendiente_sin_confirmar": True,
                    "avisos": avisos}
        no_confirmadas = sorted(set(publicado) - set(confirmadas))
        if no_confirmadas:
            # Gap #89 (fix5): el aviso unico ("`plan()` las volvera a proponer como `upsert`") era
            # FALSO para los ids que ya no estan en `approved/`: esos traen un `revoke`, no un
            # `upsert`. Se desglosa por lo que de verdad les pasa en ESTA corrida.
            ids_upsert = {o.get("id") for o in ops if o.get("tipo") == "upsert"}
            ids_revoke = {o.get("id") for o in ops if o.get("tipo") == "revoke"}
            avisos.append(
                "entradas del `.pending` heredado NO confirmadas por el servidor (se quitan del "
                "manifiesto): " + ", ".join(no_confirmadas))
            re_propuestas = [i for i in no_confirmadas if i in ids_upsert]
            a_revocar = [i for i in no_confirmadas if i in ids_revoke]
            sin_operacion = [i for i in no_confirmadas
                             if i not in ids_upsert and i not in ids_revoke]
            if re_propuestas:
                avisos.append("de ellas, se republican como `upsert` en esta corrida: "
                              + ", ".join(re_propuestas))
            if a_revocar:
                avisos.append(
                    "de ellas, se revocan IGUALMENTE contra el servidor (tombstone + `SUPERSEDES` "
                    "con los datos del manifiesto heredado): " + ", ".join(a_revocar))
            if sin_operacion:
                avisos.append(
                    "de ellas, sin operacion en esta corrida; `plan()` las volvera a proponer como "
                    "`upsert` solo si siguen en `approved/`: " + ", ".join(sin_operacion))
        publicado = confirmadas

    if not ops:
        _escribir_manifest(cfg, {"group_id": group_id, "entradas": publicado})
        _borrar_pending(cfg)
        _invalidar_cache_verify(cfg)  # gap #95: el manifiesto cambio, el `verify` cacheado sobra
        resultado = {"aplicados": 0, "revocados": 0}
        if avisos:
            resultado["avisos"] = avisos
        return resultado

    allow_remote = bool(cfg.get("allow_remote", False))
    timeout_s = _timeout_s(cfg)
    proveedor = _gp.resolver_proveedor(((cfg.get("provider") or {}).get("llm")) or "none")
    provider_cfg = cfg.get("provider") or {}
    cliente = ClienteMCP(cfg.get("endpoint"), timeout_s=timeout_s, allow_remote=allow_remote,
                         max_respuesta_bytes=_max_respuesta_bytes(cfg))
    cliente.initialize()

    progreso = dict(publicado)  # se muta y se persiste tras CADA op con éxito, no al final
    _escribir_manifest(cfg, {"group_id": group_id, "entradas": progreso}, sufijo=".pending")
    aplicados, revocados, fallidos = 0, 0, []
    for op in ops:
        try:
            if op["tipo"] == "upsert":
                _uuid_devuelto, aviso_tope = _aplicar_upsert(
                    cliente, proveedor, provider_cfg, group_id, op, cfg=cfg,
                    entrada_previa=publicado.get(op["id"]))
                if aviso_tope:
                    avisos.append(aviso_tope)
                progreso[op["id"]] = {
                    "version": op["version"], "hash": op["hash"], "category": op.get("category"),
                    "uuid": _uuid_episodio(group_id, op["id"], op["version"]),
                }
                aplicados += 1
            else:
                # Gap #89: `revocados` SOLO se incrementa despues de que el tombstone (y su
                # `SUPERSEDES`) hayan salido de verdad hacia el servidor; si no hay datos para
                # reconstruir el nombre/uuid, `_entrada_para_revoke` levanta y la op cae a
                # `fallidos` con causa explicita, nunca a `revocados`.
                _aplicar_revoke(cliente, group_id,
                                _entrada_para_revoke(group_id, op["id"], publicado, heredado),
                                op["id"])
                progreso.pop(op["id"], None)
                revocados += 1
        except Exception as e:  # noqa: BLE001 - un fallo de una op no debe perder las demas
            fallidos.append({"id": op["id"], "tipo": op["tipo"], "error": f"{type(e).__name__}: {e}"})
            continue
        _escribir_manifest(cfg, {"group_id": group_id, "entradas": progreso}, sufijo=".pending")

    if fallidos:
        # Gap #92 (Minor, fix5): los `avisos` acumulados (archivado de #73, poda de #68/#89,
        # truncado de #64) se PERDIAN cuando alguna op fallaba: la `ErrorMCP` solo llevaba el
        # resumen de fallidos y `knowledge-sync.py` no imprime otra cosa. Viajan tambien en el
        # mensaje (saneados y con tope, como los fallidos) y como atributo `avisos`.
        _invalidar_cache_verify(cfg)
        error = ErrorMCP(
            f"{len(fallidos)} operacion(es) fallaron; publicacion parcial retenida en "
            f"`graphiti-manifest.pending.json`: {_resumen_fallidos(fallidos)}"
            + (f"; avisos: {_resumen_avisos(avisos)}" if avisos else ""))
        error.avisos = list(avisos)
        raise error

    _escribir_manifest(cfg, {"group_id": group_id, "entradas": progreso})
    _borrar_pending(cfg)
    _invalidar_cache_verify(cfg)  # gap #95: acaba de cambiar el grafo y el manifiesto
    resultado = {"aplicados": aplicados, "revocados": revocados}
    if avisos:  # gap #64: solo se añade la clave si hay algo que avisar (compatibilidad con
        resultado["avisos"] = avisos  # las comparaciones exactas de tests existentes)
    return resultado


def _entrada_para_revoke(group_id, id_, publicado, heredado):
    """Gap #89 (Important, fix5): datos con los que emitir el tombstone de un `revoke`. Se prefiere
    el manifiesto ya reconciliado (`publicado`) y, si la poda de #68/#89 quito la entrada de ahi,
    se cae al manifiesto HEREDADO (`.pending`/publicado previo): el nombre del episodio
    (`<id>@<version>`) y el `uuid` (uuid5 determinista, reconstruible desde
    `group_id:id:version`) bastan para invalidarlo en el grafo. Sin `version` no hay forma de
    nombrar el nodo: se levanta y la op cae a `fallidos` con causa explicita (nunca se cuenta como
    revocada)."""
    entrada = publicado.get(id_) or heredado.get(id_)
    if not entrada:
        raise ErrorMCP(
            f"`revoke` de `{id_}`: sin rastro en el manifiesto (ni publicado ni heredado), no hay "
            f"datos para emitir el tombstone; no se cuenta como revocado")
    version = entrada.get("version")
    if version is None:
        raise ErrorMCP(
            f"`revoke` de `{id_}`: la entrada del manifiesto no trae `version`, no se puede "
            f"reconstruir el nombre del episodio (`<id>@<version>`); no se cuenta como revocado")
    return {**entrada, "version": version,
            "uuid": entrada.get("uuid") or _uuid_episodio(group_id, id_, version)}


_MAX_FALLIDOS_EN_MENSAJE = 5
_TOPE_RESUMEN_FALLIDOS_CHARS = 800
_MAX_AVISOS_EN_MENSAJE = 5
_TOPE_RESUMEN_AVISOS_CHARS = 800


def _resumen_avisos(avisos):
    """Gap #92: mismo tratamiento que `_resumen_fallidos` (acotar, sanear, capar) para los avisos
    que se adjuntan al mensaje de la `ErrorMCP` de una publicacion parcial."""
    piezas = [_sanear_detalle(a) for a in avisos[:_MAX_AVISOS_EN_MENSAJE]]
    resumen = "; ".join(piezas)
    if len(avisos) > _MAX_AVISOS_EN_MENSAJE:
        resumen += f"; ... y {len(avisos) - _MAX_AVISOS_EN_MENSAJE} mas"
    return resumen[:_TOPE_RESUMEN_AVISOS_CHARS]


def _resumen_fallidos(fallidos):
    """Gap #72 (Important, CWE-117): el resumen de `fallidos` se concatenaba ENTERO y con el
    texto del servidor tal cual dentro del mensaje de `ErrorMCP` -que `knowledge-sync.py` imprime
    y persiste como `causa` en la dead-letter-. Se acota el numero de fallos citados, se sanea
    cada causa y se capa el total."""
    piezas = [f"{f.get('tipo')} `{f.get('id')}`: {_sanear_detalle(f.get('error'))}"
              for f in fallidos[:_MAX_FALLIDOS_EN_MENSAJE]]
    resumen = "; ".join(piezas)
    if len(fallidos) > _MAX_FALLIDOS_EN_MENSAJE:
        resumen += f"; ... y {len(fallidos) - _MAX_FALLIDOS_EN_MENSAJE} mas"
    return resumen[:_TOPE_RESUMEN_FALLIDOS_CHARS]


def _sufijo_archivado(grupo_previo):
    """Gap #91 (Minor, fix5): el sufijo derivado SOLO del `group_id` saneado podia chocar con
    otros ficheros del mismo directorio. (a) Un `group_id` que sanea a `pending` producia
    `graphiti-manifest.pending.json` — el MARCADOR de publicacion interrumpida, que
    `_borrar_pending()` borra tres lineas despues: el aviso prometia un fichero que ya no existe.
    (b) Dos `group_id` distintos que sanean igual (`proy/a` y `proy_a`) se sobrescribian entre si.
    El sufijo lleva prefijo propio (`archivado-`, que ningun otro fichero del directorio usa) y
    una huella corta del `group_id` CRUDO, que distingue los que sanean igual."""
    saneado = re.sub(r"[^A-Za-z0-9._-]", "_", grupo_previo)
    huella = hashlib.sha1(grupo_previo.encode("utf-8")).hexdigest()[:8]
    return f".archivado-{saneado}-{huella}"


def _archivar_manifest_de_otro_grupo(cfg, manifest, grupo_previo):
    """Gap #73: conserva el manifiesto del `group_id` ANTERIOR como
    `graphiti-manifest.archivado-<group_id-saneado>-<huella>.json` (gap #91) — sin esto, sus
    `uuid` se perdian y sus episodios quedaban en el grafo sin forma de revocarlos. Si ese fichero
    ya existe (un ida y vuelta entre dos grupos), NO se sobrescribe: se numera (`-2`, `-3`...)."""
    sufijo = _sufijo_archivado(grupo_previo)
    candidato, n = sufijo, 1
    while os.path.isfile(_manifest_path(cfg, candidato)):
        n += 1
        candidato = f"{sufijo}-{n}"
    return _escribir_manifest(cfg, manifest, sufijo=candidato)


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
    cliente = ClienteMCP(cfg.get("endpoint"), timeout_s=_timeout_s(cfg), allow_remote=allow_remote,
                         max_respuesta_bytes=_max_respuesta_bytes(cfg))
    cliente.initialize()
    # Gap #82 (Minor): el `.pending` VACIO se escribe ANTES de `clear_graph` -es la marca de que
    # hay una reconstruccion en curso-. Si `clear_graph` borra y luego falla la lectura de la
    # respuesta (timeout), el grafo queda vacio: con la marca, `verify()` dice
    # "publicacion_incompleta" en vez de afirmar que todo sigue publicado (incremental no-op).
    _escribir_manifest(cfg, {"group_id": group_id, "entradas": {}}, sufijo=".pending")
    cliente.tools_call("clear_graph", {"group_ids": [group_id]})
    _escribir_manifest(cfg, {"group_id": group_id, "entradas": {}})
    _borrar_pending(cfg)
    _invalidar_cache_verify(cfg)  # gap #95: el grafo acaba de vaciarse; el verify cacheado miente
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
    _invalidar_cache_verify(cfg)  # gap #95 (`apply` ya invalida; explicito por si cambia)
    return {"revocado": True, "id": knowledge_id, "resultado": resultado}


_CACHE_VERIFY_TTL_S = 5  # gap #70 (lente D): ventana corta, solo para no repetir el barrido
_cache_verify = {}       # {(endpoint, group_id, root): (veredicto, expira_monotonic)}


def _invalidar_cache_verify(cfg):
    """Gap #95 (Minor, fix5): la cache de `verify()` (TTL 5 s) no se invalidaba nunca, asi que
    justo despues de un `apply()`/`rebuild()`/`revoke()` exitoso `puede_leer()` podia autorizar
    una lectura con un veredicto OBSOLETO (hasta 5 s de desfase invisible). Cada escritura que
    cambia el manifiesto o el grafo tira la entrada de SU clave (endpoint, group_id, root)."""
    cfg = cfg or {}
    _cache_verify.pop((cfg.get("endpoint"), cfg.get("group_id"), cfg.get("_root")), None)


def _verify_cacheado(cfg):
    """Gap #70 (Important, lente D): `puede_leer()` encadena `health()` + `verify()` y el router
    de T-07 la llamara POR CONSULTA — sin cache, cada consulta barria el grafo entero con
    `get_episodes`. El resultado se cachea en PROCESO con un TTL corto (5 s): suficiente para una
    rafaga de consultas, demasiado corto para enmascarar un desfase real."""
    cfg = cfg or {}
    clave = (cfg.get("endpoint"), cfg.get("group_id"), cfg.get("_root"))
    ahora = time.monotonic()
    entrada = _cache_verify.get(clave)
    if entrada and entrada[1] > ahora:
        return entrada[0]
    veredicto = verify(cfg)
    _cache_verify[clave] = (veredicto, ahora + _CACHE_VERIFY_TTL_S)
    return veredicto


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
    veredicto_verify = _verify_cacheado(cfg)
    if veredicto_verify.get("ok") is not True:
        return {"puede": False, "razon": f"verify con desfase o ilegible: {veredicto_verify}"}
    return {"puede": True}


_REMEDIO_DESFASE = ("reindexar: ejecutar `knowledge-sync.py --backend <id>` (o `--rebuild` si el "
                    "desfase persiste); este `verify()` nunca lo ejecuta por su cuenta (CA-16)")
_REMEDIO_PUBLICACION_INCOMPLETA = ("reintentar `knowledge-sync.py --backend <id>`: la publicacion "
                                   "anterior no completo (`graphiti-manifest.pending.json` presente)")


class _RespuestaIlegible(Exception):
    """Señal interna de `_nombres_remotos_confirmados`/`_indice_procedencia`: la respuesta de
    `get_episodes` no tenia la forma esperada (ni lista ni `{"episodes": [...]}`), o el servidor
    devolvio la variante `ErrorResponse` del `outputSchema` real (gap #102, fix1 Fase 3). El
    texto de la excepcion es el MOTIVO que se propaga al llamador: un backend que no pudo servir
    no puede parecer un backend que sirvio 0 aciertos."""


def _max_episodios_verify(cfg):
    """`max_episodes` (entero > 0): tope de la ventana de `get_episodes` que barre `verify()`
    (gap #70). Ausente o invalido -> `_MAX_EPISODIOS_VERIFY`, el tope duro historico."""
    valor = (cfg or {}).get("max_episodes", _MAX_EPISODIOS_VERIFY)
    if isinstance(valor, bool) or not isinstance(valor, int) or valor <= 0:
        valor = _MAX_EPISODIOS_VERIFY
    return min(valor, _MAX_EPISODIOS_VERIFY)


def _nombres_remotos_confirmados(cliente, group_id, entradas, tope_episodios=None):
    """`get_episodes` es una ventana de los MAS RECIENTES, no un filtro por nombre — una entrada
    antigua real puede quedar fuera de una ventana fija (gap #39). Se pide una ventana generosa
    y, si TODAVIA faltan nombres esperados y la respuesta llego "llena" (indicio de que hay mas
    detras), se AMPLIA la ventana hasta `_MAX_EPISODIOS_VERIFY` o hasta que dos peticiones
    consecutivas devuelvan el mismo tamano (el servidor ya no tiene mas). Devuelve
    `(nombres_remotos, otros_grupos, uuids_remotos)` -`uuids_remotos` mapea nombre -> `uuid` SOLO
    para los episodios en los que el servidor lo devuelve (gap #79)-; lanza `_RespuestaIlegible`
    si el servidor responde algo sin forma reconocible. Extraido de `verify()` para que `apply()`
    (gap #54) pueda reutilizarlo al reconciliar un `.pending` heredado antes de promoverlo.

    Gap #70 (Important, lente D): la ventana se amplia como maximo hasta `tope_episodios`
    (`config.max_episodes`, default `_MAX_EPISODIOS_VERIFY`) — sin tope configurable, `verify()`
    podia barrer hasta 15 000 episodios (~31 MB) para devolver un booleano.

    Gap #120 (Important, fix2 Fase 3): los dos topes de #70 se CONTRADECIAN con sus defaults en
    el escenario de referencia documentado (`backends/README.md`: 500 entradas / 15 000
    episodios). La ampliacion llegaba a 4 000 episodios (~12,5 MiB), por encima de
    `max_respuesta_kb` (8 MiB) — `ErrorMCP`, `verify` en falso, `puede_leer` en false y TODA
    consulta enrutada degradada a local. `get_episodes` no tiene cursor de paginacion (el
    contrato real solo acepta `group_ids` y `max_episodes`), asi que la "pagina" es la propia
    ventana: cuando una ampliacion NO cabe en el tope de lectura se conserva el resultado de la
    ultima ventana que SI cupo y se declara la ventana INCOMPLETA. Devuelve por eso
    `(nombres_remotos, otros_grupos, uuids_remotos, ventana_completa, tombstones_de_entradas_vivas)`:
    lo que no se pudo mirar no es lo mismo que lo que no esta (misma distincion del gap #67), y
    `tombstones_de_entradas_vivas` alimenta el aviso de migracion del gap #126."""
    tope = tope_episodios or _MAX_EPISODIOS_VERIFY
    esperados = {f"{id_}@{meta.get('version')}" for id_, meta in entradas.items()}
    nombres_remotos = set()
    otros_grupos = set()
    uuids_remotos = {}
    tombstones = set()
    ventana_completa = True
    max_episodes = min(max(len(entradas) * 2, 50), tope)
    tamano_previo = -1
    hubo_ventana_buena = False
    for _ in range(6):
        try:
            resultado = cliente.tools_call(
                "get_episodes", {"group_ids": [group_id], "max_episodes": max_episodes})
        except ErrorMCP:
            # Gap #120: la ventana ampliada no cabe en `max_respuesta_kb`. Si ya hubo una que SI
            # cupo, se conserva y se declara incompleta; si ni la PRIMERA cabe, es un error real
            # de configuracion y sube al llamador como hasta ahora.
            if not hubo_ventana_buena:
                raise
            ventana_completa = False
            break
        contenido = _contenido_tool_call(resultado)
        if contenido is None:
            raise _RespuestaIlegible()
        elif isinstance(contenido, list):
            episodios_remotos = contenido
        elif isinstance(contenido, dict):
            episodios_remotos = contenido.get("episodes")
            if episodios_remotos is None:
                raise _RespuestaIlegible()
        else:
            raise _RespuestaIlegible()
        hubo_ventana_buena = True
        nombres_remotos = set()
        otros_grupos = set()
        uuids_remotos = {}
        tombstones = set()
        for ep in episodios_remotos:
            if not isinstance(ep, dict):
                continue
            grupo_ep = ep.get("group_id")
            if grupo_ep and grupo_ep != group_id:
                otros_grupos.add(grupo_ep)
                continue
            if ep.get("name"):
                nombres_remotos.add(ep["name"])
                if ep.get("uuid"):
                    uuids_remotos[ep["name"]] = ep["uuid"]
                if ep["name"].endswith(_SUFIJO_TOMBSTONE):
                    tombstones.add(ep["name"][: -len(_SUFIJO_TOMBSTONE)])
        faltan = esperados - nombres_remotos
        if not faltan or len(episodios_remotos) == tamano_previo:
            break
        if len(episodios_remotos) < max_episodes:
            break  # el servidor ya devolvio TODO lo que tiene (menos de lo pedido)
        if max_episodes >= tope:
            # Gap #70: ventana al tope configurado, no se amplia mas. Gap #120: si TODAVIA faltan
            # nombres, la ventana no ha podido confirmarlo todo -se declara incompleta.
            ventana_completa = not faltan
            break
        tamano_previo = len(episodios_remotos)
        max_episodes = min(max_episodes * 4, tope)
    # Gap #126 (Minor, fix2 Fase 3): tombstone `<id>@tombstone` de una entrada que el manifiesto
    # da por VIVA = grafo publicado antes de fix1, cuando la sucesion de version usaba el mismo
    # sufijo que el revoke; el lector de hoy invalidaria la entrada entera.
    tombstones_vivos = sorted(tombstones & set(entradas))
    return nombres_remotos, otros_grupos, uuids_remotos, ventana_completa, tombstones_vivos


def _reconciliar_publicado(cfg, group_id, entradas):
    """Gap #54 (Important, mutante N1): un `.pending` heredado de una corrida CORTADA (proceso
    matado a mitad, sin excepcion Python capturable) se promovia a manifiesto PUBLICADO CON CERO
    llamadas de confirmacion al servidor cuando la siguiente corrida no generaba `ops` nuevas
    (`plan()` ya no ve diferencias porque compara contra ESE MISMO `.pending`, gap #32) — asi el
    manifiesto local podia dar por publicadas entradas que en realidad nunca llegaron a
    `add_memory`. Antes de promover, se confirma cada entrada contra `get_episodes` del propio
    `group_id`; lo no confirmado se descarta del manifiesto (una proxima `plan()` la volvera a
    proponer como `upsert`, que es el comportamiento seguro: reintentar de mas nunca pierde datos,
    promover de mas si).

    Devuelve `(confirmadas, confirmacion_posible)` (gap #67, Critical): distinguir "el servidor
    dice que no tiene esto" de "no he podido preguntarle" es la diferencia entre no promover y
    DESPUBLICAR. Antes devolvia `{}` en los dos casos y `apply()` escribia ese `{}` como
    manifiesto publicado, dejando episodios irrevocables en el grafo y sin rastro local.

    Gap #79 (Minor, CWE-345): un nombre que el servidor AFIRMA tener no basta si ademas devuelve
    un `uuid` que no es el nuestro (un servidor rogue podria "suprimir" entradas de forma
    permanente). Cuando `get_episodes` devuelve `uuid`, tiene que coincidir; cuando no lo
    devuelve, se confirma por nombre (limite documentado en `backends/README.md`)."""
    if not entradas:
        return entradas, True
    allow_remote = bool(cfg.get("allow_remote", False))
    try:
        cliente = ClienteMCP(cfg.get("endpoint"), timeout_s=_timeout_s(cfg),
                             allow_remote=allow_remote,
                             max_respuesta_bytes=_max_respuesta_bytes(cfg))
        cliente.initialize()
        (nombres_remotos, _otros_grupos, uuids_remotos, ventana_completa,
         _tombstones) = _nombres_remotos_confirmados(
            cliente, group_id, entradas, _max_episodios_verify(cfg))
    except Exception:  # noqa: BLE001 - sin servidor/respuesta ilegible: NO se puede confirmar
        return {}, False
    if not ventana_completa:
        # Gap #120: con la ventana incompleta NO se puede afirmar que lo no visto no esta -y aqui
        # "no confirmado" significa DESPUBLICAR del manifiesto. Se trata como "no he podido
        # preguntar" (gap #67): no se promueve nada, no se pierde nada.
        return {}, False
    confirmadas = {}
    for id_, meta in entradas.items():
        nombre = f"{id_}@{meta.get('version')}"
        if nombre not in nombres_remotos:
            continue
        uuid_remoto = uuids_remotos.get(nombre)
        if uuid_remoto and meta.get("uuid") and uuid_remoto != meta.get("uuid"):
            continue
        confirmadas[id_] = meta
    return confirmadas, True


def verify(cfg):
    """Nunca lanza (contrato de adaptador): compara el manifiesto local con `get_episodes` del
    `group_id` propio; NOMBRA el remedio sin ejecutarlo (CA-16)."""
    cfg = cfg or {}
    # Gap #55 (Important): `verify` era la UNICA funcion publica sin cortocircuito de
    # `mode: off` — `knowledge-sync --check` con `mode: off` seguia haciendo POSTs reales
    # contra el servidor via `tools_call("get_episodes", ...)`, distinto del resto del
    # adaptador (`health`/`apply`/`rebuild` si respetan `mode: off`).
    if _modo(cfg) == "off":
        return {"ok": None, "razon": "mode: off"}
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
        cliente = ClienteMCP(cfg.get("endpoint"), timeout_s=_timeout_s(cfg),
                             allow_remote=allow_remote,
                             max_respuesta_bytes=_max_respuesta_bytes(cfg))
        cliente.initialize()
        (nombres_remotos, otros_grupos, _uuids_remotos, ventana_completa,
         tombstones_vivos) = _nombres_remotos_confirmados(
            cliente, group_id, entradas, _max_episodios_verify(cfg))
    except _RespuestaIlegible:
        return {"ok": None, "razon": "respuesta de get_episodes ilegible (no es lista ni {\"episodes\": [...]})",
                "desfase": []}
    except Exception as e:  # noqa: BLE001 - verify() nunca lanza (mismo contrato que health())
        return {"ok": False, "razon": f"no se pudo consultar get_episodes: {type(e).__name__}: {_sanear_detalle(e)}",
                "desfase": []}
    no_confirmadas = [id_ for id_, meta in sorted(entradas.items())
                      if f"{id_}@{meta.get('version')}" not in nombres_remotos]
    # Gap #120 (fix2 Fase 3): con la ventana INCOMPLETA (el tope de lectura corto la ampliacion),
    # lo no confirmado NO es desfase -es "no he podido mirarlo"-. Declararlo desfase dejaba
    # `verify` en falso, `puede_leer` en false y toda consulta enrutada degradada a local en el
    # escenario de referencia con los defaults. Se publica como `no_verificado` + aviso.
    desfase = [] if (no_confirmadas and not ventana_completa) else [
        {"knowledge_id": id_, "motivo": "episodio no encontrado en el grafo", "remedio": _REMEDIO_DESFASE}
        for id_ in no_confirmadas
    ]
    salida = {"ok": not desfase, "desfase": desfase}
    avisos = []
    if otros_grupos:
        avisos.append(f"el servidor devolvio episodios de otro(s) group_id: {sorted(otros_grupos)}")
    if no_confirmadas and not ventana_completa:
        salida["no_verificado"] = len(no_confirmadas)
        avisos.append(
            f"{len(no_confirmadas)} entrada(s) sin confirmar: la ventana de `get_episodes` no "
            f"alcanzo el grafo entero (tope de lectura `max_respuesta_kb` o `max_episodes`); "
            f"no se declaran desfase porque no se han podido mirar")
    if tombstones_vivos:
        # Gap #126: migracion de grafos publicados ANTES de fix1 (sucesion y revoke compartian el
        # sufijo `@tombstone`). Se NOMBRA el remedio, nunca se ejecuta (CA-16).
        avisos.append(
            f"tombstone `@tombstone` de entrada(s) que el manifiesto da por vigentes "
            f"({', '.join(tombstones_vivos[:5])}{' …' if len(tombstones_vivos) > 5 else ''}): "
            f"grafo publicado antes de la separacion `@superseded`/`@tombstone`; el lector las "
            f"daria por invalidadas. Republica con `knowledge-sync.py --backend <id> --rebuild`")
    if avisos:
        salida["aviso"] = " · ".join(avisos)
    return salida


_MAX_EPISODIOS_VERIFY = 5000  # tope duro de la ampliacion de ventana de get_episodes (gap #39)


# ------------------------------------------------------------------ lectura enrutada (T-07)
# `consultar` es la funcion OPCIONAL del contrato de adaptador que usa el router por intent de
# `knowledge-find.py --intent` (CA-12): el NUCLEO no sabe que existe Graphiti, solo pregunta al
# adaptador declarado en `taxonomy.json`. Nunca lanza y nunca escribe: solo `search_nodes`,
# `search_memory_facts` y `get_episodes`, los tres acotados al `group_id` propio.

# Gap #121 (fix2 Fase 3): la ventana de procedencia de una consulta ARRANCA pequena y se amplia
# solo si quedan aciertos sin resolver (`_indice_procedencia`), con este tope duro por encima del
# corpus objetivo declarado (500 entradas, `backends/README.md`) y siempre acotada ademas por
# `config.max_episodes` y por `config.max_respuesta_kb` (el tope de lectura de cada respuesta).
_MAX_EPISODIOS_CONSULTA = 2000
_VENTANA_CONSULTA_INICIAL = 50


def _procedencia_de_episodio(episodio):
    """Bloque `--- procedencia ---` de un episodio como dict (`knowledge_id`, `version`, `status`,
    `category`, `evidence_level`, `source_path`, `hash`), o `None` si el episodio no lo trae.
    Es la UNICA fuente de la procedencia que se sirve: lo que no esta aqui no se inventa."""
    if not isinstance(episodio, dict):
        return None
    contenido = episodio.get("content") or episodio.get("episode_body") or ""
    if not isinstance(contenido, str) or _DELIM_PROVENIENCIA not in contenido:
        return None
    cabecera = contenido.split(_DELIM_PROVENIENCIA, 1)[1].split(_DELIM_CONTENIDO, 1)[0]
    datos = {}
    for linea in cabecera.splitlines():
        if ":" not in linea:
            continue
        clave, valor = linea.split(":", 1)
        clave, valor = clave.strip(), valor.strip()
        if clave and valor:
            datos[clave] = valor
    return datos or None


def _error_de_respuesta(contenido):
    """Motivo saneado si el contenido es la variante `ErrorResponse` del `outputSchema` real
    (`{"error": "..."}`, fixture `graphiti-mcp-tools-list-2026-09-18.json`), o `None`. Gap #102
    (Important, fix1 Fase 3): esa variante se leia como «0 aciertos» y el fallo del servidor
    desaparecia -el nucleo servia una respuesta vacia como si fuera autorizada-."""
    if isinstance(contenido, dict):
        error = contenido.get("error")
        if isinstance(error, str) and error.strip():
            return _sanear_detalle(error.strip())
    return None


def _episodio_del_grupo(episodio, group_id, grupos_pedidos):
    """¿Este episodio es del grupo propio? Gap #105 (Minor, CWE-346/863, fix1 Fase 3): el
    `outputSchema` de `get_episodes` declara los episodios como objetos ABIERTOS
    (`additionalProperties: true`), asi que `group_id` NO esta garantizado en la respuesta -y la
    sonda de solo lectura contra el servidor real (2026-09-21) no pudo confirmarlo porque el
    grafo esta vacio (`get_episodes` sin filtro: «No episodes found»)-. Por eso la regla es la
    que permite el arbitraje: un episodio SIN `group_id` se acepta SOLO cuando la consulta se
    acoto a UN unico `group_ids` (es el servidor quien filtro, y solo pudo filtrar por ese); con
    mas de un grupo pedido, o con un `group_id` distinto del propio, fail-closed."""
    if not isinstance(episodio, dict):
        return False
    grupo = episodio.get("group_id")
    if grupo:
        return grupo == group_id
    return grupos_pedidos == 1


def _indice_procedencia_ventana(cliente, group_id, tope):
    """`(procedencia_por_nombre_de_episodio, ids_invalidados, nombres_superados)` del `group_id`
    propio. Los episodios de OTRO grupo se ignoran (aislamiento multi-proyecto, gap #73;
    `_episodio_del_grupo` decide, gap #105), los `@tombstone` marcan invalidada la ENTRADA
    entera (revoke, CA-11) y los `@superseded` marcan invalidado SOLO el episodio de la version
    superada (gap #96: la version vigente sigue aprobada). Lanza `_RespuestaIlegible` -con el
    motivo dentro- si `get_episodes` responde un `ErrorResponse` o una forma inesperada."""
    group_ids = [group_id]
    resultado = cliente.tools_call("get_episodes", {"group_ids": group_ids, "max_episodes": tope})
    contenido = _contenido_tool_call(resultado)
    error = _error_de_respuesta(contenido)
    if error:
        raise _RespuestaIlegible(f"get_episodes: {error}")
    if isinstance(contenido, list):
        episodios = contenido
    elif isinstance(contenido, dict):
        episodios = contenido.get("episodes")
    else:
        episodios = None
    if not isinstance(episodios, list):
        raise _RespuestaIlegible('respuesta de get_episodes ilegible (no es lista ni {"episodes": [...]})')
    por_nombre, invalidados, superados = {}, set(), set()
    for ep in episodios:
        if not _episodio_del_grupo(ep, group_id, len(group_ids)):
            continue
        nombre = ep.get("name") or ""
        if nombre.endswith(_SUFIJO_SUPERSEDED):
            superados.add(nombre[: -len(_SUFIJO_SUPERSEDED)])
            continue
        if nombre.endswith(_SUFIJO_TOMBSTONE):
            invalidados.add(nombre[: -len(_SUFIJO_TOMBSTONE)])
            continue
        procedencia = _procedencia_de_episodio(ep)
        if procedencia and procedencia.get("knowledge_id"):
            por_nombre[nombre] = dict(procedencia, uuid=ep.get("uuid"))
    return por_nombre, invalidados, superados, len(episodios)


def _indice_procedencia(cliente, group_id, tope, nombres_buscados=()):
    """Gap #121 (Important, fix2 Fase 3): `get_episodes` es una ventana de los MAS RECIENTES
    mientras `search_nodes`/`search_memory_facts` buscan en TODO el grafo, asi que una ventana
    FIJA (200 episodios) dejaba fuera -en silencio- casi todo acierto de un grafo poblado (recall
    medido: 100 % con 100 episodios, 5 % con 2 000). El contrato REAL del servidor no tiene
    ninguna herramienta que devuelva un episodio por `uuid` ni un cursor de paginacion
    (`tools/list` de 2026-09-18: `get_episodes` solo acepta `group_ids` y `max_episodes`), asi
    que la unica paginacion posible es AMPLIAR la ventana: se pide x4 hasta resolver todos los
    `nombres_buscados`, hasta que el servidor devuelva menos de lo pedido (ya dio todo lo que
    tiene) o hasta el tope configurado.

    Devuelve `(por_nombre, invalidados, superados, ventana_completa)`. `ventana_completa` es
    `False` SOLO cuando el tope corto la ampliacion con nombres aun sin resolver: es lo que el
    llamador cuenta como `fuera_de_ventana` en vez de callarselo."""
    ventana = min(max(len(nombres_buscados) * 2, _VENTANA_CONSULTA_INICIAL), tope)
    leidos_previo = -1
    while True:
        por_nombre, invalidados, superados, leidos = _indice_procedencia_ventana(
            cliente, group_id, ventana)
        if all(n in por_nombre for n in nombres_buscados):
            return por_nombre, invalidados, superados, True
        if leidos < ventana or leidos == leidos_previo:
            # El servidor ya devolvio TODO lo que tiene: lo que falta NO esta fuera de la ventana
            # (simplemente no es un episodio nuestro), asi que la ventana si esta completa.
            return por_nombre, invalidados, superados, True
        if ventana >= tope:
            return por_nombre, invalidados, superados, False
        leidos_previo = leidos
        ventana = min(ventana * 4, tope)


def _hits_de_busqueda(resultado, clave):
    """`(aciertos, motivo)` de un `search_*` (`{"nodes": [...]}`/`{"facts": [...]}` o lista
    pelada). Gap #102 (fix1 Fase 3): la variante `ErrorResponse` del `outputSchema` real
    (`{"error": "..."}`) devuelve MOTIVO en vez de una lista vacia silenciosa."""
    contenido = _contenido_tool_call(resultado)
    error = _error_de_respuesta(contenido)
    if error:
        return [], f"{clave}: {error}"
    if isinstance(contenido, list):
        return [h for h in contenido if isinstance(h, dict)], ""
    if isinstance(contenido, dict):
        lista = contenido.get(clave)
        if isinstance(lista, list):
            return [h for h in lista if isinstance(h, dict)], ""
    return [], ""


def _ruta_canonica(valor):
    """`source_path` servido por el grafo, normalizado, o `None` si no es una ruta RELATIVA bajo
    `docs/knowledge/`. Gap #106 (Minor, CWE-22, fix1 Fase 3): la ruta se imprime como «ruta
    canonica» junto a un `estado` de doctrina y la consume quien luego abre el fichero; una ruta
    absoluta, con `..` o fuera de `docs/knowledge/` no se sirve (fail-closed), no se recorta."""
    if not isinstance(valor, str):
        return None
    ruta = _sanear_detalle(valor).strip().replace("\\", "/")
    if not ruta or ruta.startswith("/") or ":" in ruta.split("/")[0]:
        return None
    partes = [p for p in ruta.split("/") if p not in ("", ".")]
    if any(p == ".." for p in partes):
        return None
    normalizada = "/".join(partes)
    return normalizada if normalizada.startswith("docs/knowledge/") else None


def _texto_servido(valor):
    """Gap #98 (Important, CWE-117/1007/150, fix1 Fase 3): TODO string de origen servidor
    (`summary`/`fact`/`source_path`/`evidence_level`/`valid_at`... los genera el LLM de Graphiti
    a partir de lo ingerido) se sanea -tope de 200 caracteres, sin controles/ANSI/bidi/C1- ANTES
    de devolverlo, porque acaba en stdout y en el contexto del agente. `None` se conserva."""
    return None if valor is None else _sanear_detalle(valor)


def _nombres_de_hit(hit):
    """Nombres de episodio que cita un acierto de busqueda (nodo o hecho)."""
    nombres = []
    for clave in ("name", "source_node_name", "target_node_name"):
        valor = hit.get(clave)
        if isinstance(valor, str) and valor:
            nombres.append(valor)
    return nombres


def _grupo_ajeno(hit, group_id):
    """Gap #124 (fix2 Fase 3): ¿el acierto de busqueda declara un `group_id` que NO es el propio?
    Un nodo de otro grupo llamado `ADR-001@1` se servia como titular de NUESTRO `ADR-001`, con
    nuestra procedencia. Sin `group_id` declarado no se descarta (la busqueda ya iba acotada)."""
    grupo = hit.get("group_id") if isinstance(hit, dict) else None
    return bool(grupo) and grupo != group_id


def _folder_de_ruta(ruta):
    """`folder` declarado de una ruta canonica `docs/knowledge/approved/<folder>/...` (gap #117,
    respaldo para grafos publicados antes de fix2, sin `local_folder` en la procedencia)."""
    partes = [p for p in (ruta or "").split("/") if p]
    return partes[3] if len(partes) >= 5 and partes[:3] == ["docs", "knowledge", "approved"] else ""


def _version_entera(acierto):
    try:
        return int(str(acierto.get("version")).strip())
    except (TypeError, ValueError):
        return -1


def _mas_vigente(candidato, previo):
    """Gap #118: entre dos episodios del MISMO `knowledge_id`, gana el que no esta invalidado; a
    igualdad de estado, el de `version` mayor. Nunca «el primero que llego»."""
    vivo_c = candidato.get("estado") != "invalidado"
    vivo_p = previo.get("estado") != "invalidado"
    if vivo_c != vivo_p:
        return vivo_c
    return _version_entera(candidato) > _version_entera(previo)


_TOPE_CONSULTA = 100      # tope duro de aciertos por consulta, tambien para `--limit 0`
_LIMITE_CONSULTA_DEFAULT = 10


def _limite_consulta(consulta):
    """Gap #114 (Minor, fix1 Fase 3): `--limit 0` es «sin tope» en el `--help` del nucleo (y es
    lo que usa `session-context.sh`), no «10». Aqui `0` se traduce al tope DOCUMENTADO de la
    consulta (`_TOPE_CONSULTA`); un valor ausente o invalido sigue siendo el default de 10."""
    valor = (consulta or {}).get("limit")
    if isinstance(valor, bool) or not isinstance(valor, int) or valor < 0:
        return _LIMITE_CONSULTA_DEFAULT
    if valor == 0:
        return _TOPE_CONSULTA
    return min(valor, _TOPE_CONSULTA)


def consultar(cfg, consulta):
    """Funcion OPCIONAL del contrato (lectura). Devuelve
    `{"aciertos": [...], "descartados": int, "motivo": str}` y NUNCA lanza.

    Cada acierto trae la terna que lo hace auditable -`estado`, `evidencia` y `ruta` canonica-
    leida del bloque de procedencia del episodio; un acierto de busqueda que no case con ningun
    episodio propio se DESCARTA (fail-closed) en vez de servirse con huecos rellenados a ojo.

    fix1 de la Fase 3: la vigencia la decide el `status` del bloque de procedencia del episodio
    SERVIDO (sin `status` no hay acierto, gap #116) mas los tombstones -`@tombstone` invalida la
    entrada entera (revoke), `@superseded` solo la version superada (gap #96)-; todo texto de
    origen servidor sale saneado (gap #98) y la `ruta` tiene que ser canonica (gap #106). Los
    filtros `tipo`/`area` NO se aplican aqui: la `category` del grafo (DECISION/GOTCHA/...) no es
    el `tipo`/`area` del corpus local y no hay equivalencia declarada en la config del backend
    -el post-filtro lo hace el nucleo sobre los aciertos remotos (gap #104)-."""
    cfg = cfg or {}
    consulta = consulta or {}
    vacio = {"aciertos": [], "descartados": 0}
    permiso = puede_leer(cfg)
    if not permiso.get("puede"):
        return dict(vacio, motivo=permiso.get("razon") or "lectura no autorizada")
    texto = (consulta.get("texto") or "").strip()
    if not texto:
        return dict(vacio, motivo="consulta sin texto: no se pregunta al grafo")
    group_id = cfg.get("group_id")
    if not group_id:
        return dict(vacio, motivo="sin `group_id`: no se consulta un grupo que no es el propio")

    limit = _limite_consulta(consulta)
    tope_episodios = min(_max_episodios_verify(cfg), _MAX_EPISODIOS_CONSULTA)
    try:
        cliente = ClienteMCP(cfg.get("endpoint"), timeout_s=_timeout_s(cfg),
                             allow_remote=bool(cfg.get("allow_remote", False)),
                             max_respuesta_bytes=_max_respuesta_bytes(cfg))
        cliente.initialize()
        nodos, motivo_nodos = _hits_de_busqueda(cliente.tools_call(
            "search_nodes", {"query": texto, "group_ids": [group_id], "max_nodes": limit}), "nodes")
        hechos, motivo_hechos = _hits_de_busqueda(cliente.tools_call(
            "search_memory_facts", {"query": texto, "group_ids": [group_id], "max_facts": limit}), "facts")
        hits = [(h, "nodo") for h in nodos] + [(h, "hecho") for h in hechos]
        # Gap #124 (Minor, CWE-346/863, fix2 Fase 3): un hit que declara OTRO `group_id` no se
        # empareja con nuestra procedencia (se descarta antes de buscar su episodio); un hit sin
        # `group_id` sigue valiendo -la busqueda ya se acoto a `group_ids: [group_id]`, misma
        # regla fail-closed que `_episodio_del_grupo`.
        hits_propios = [(h, c) for h, c in hits if not _grupo_ajeno(h, group_id)]
        descartados = len(hits) - len(hits_propios)
        nombres_buscados = sorted({n for h, _c in hits_propios for n in _nombres_de_hit(h)})
        por_nombre, invalidados, superados, ventana_completa = _indice_procedencia(
            cliente, group_id, tope_episodios, nombres_buscados)
    except _RespuestaIlegible as e:
        return dict(vacio, motivo=str(e) or "respuesta de get_episodes ilegible")
    except Exception as e:  # noqa: BLE001 - mismo contrato que health()/verify(): nunca lanza
        return dict(vacio, motivo=f"no se pudo consultar el grafo: {type(e).__name__}: {_sanear_detalle(e)}")

    candidatos, fuera_de_ventana = {}, 0
    for hit, clase in hits_propios:
        nombre = next((n for n in _nombres_de_hit(hit) if n in por_nombre), None)
        if nombre is None:
            # Gap #121: «no lo he podido mirar» (la ventana no llego) NO es «no cuadra» -se
            # cuenta aparte y sale en el `motivo`, nunca en silencio.
            if not ventana_completa:
                fuera_de_ventana += 1
            else:
                descartados += 1
            continue
        procedencia = por_nombre[nombre]
        knowledge_id = procedencia.get("knowledge_id")
        # Fail-closed (gaps #106/#116): sin `status`, sin nivel de evidencia o con una `ruta` que
        # no es canonica, el acierto NO se sirve -antes `status` caia a `"aprobado"` y la ruta se
        # servia tal cual viniera-.
        status = procedencia.get("status")
        evidencia = procedencia.get("evidence_level")
        ruta = _ruta_canonica(procedencia.get("source_path"))
        if not status or not evidencia or not ruta:
            descartados += 1
            continue
        invalidado = knowledge_id in invalidados or nombre in superados
        acierto = {
            "id": _texto_servido(knowledge_id),
            "version": _texto_servido(procedencia.get("version")),
            "estado": "invalidado" if invalidado else _texto_servido(status),
            "evidencia": _texto_servido(evidencia),
            "ruta": ruta,
            "categoria": _texto_servido(procedencia.get("category")),
            # Gap #117: vocabulario del corpus LOCAL (el `folder` declarado en la taxonomia y el
            # `area` de la entrada), que es lo que el post-filtro `--tipo`/`--area` del nucleo
            # sabe normalizar. Sin `local_folder` en la procedencia (grafo publicado antes de
            # fix2) se deriva de la propia `ruta` canonica, que lleva el mismo `folder`.
            "tipo": _texto_servido(procedencia.get("local_folder") or _folder_de_ruta(ruta)),
            "area": _texto_servido(procedencia.get("area") or ""),
            "titular": _texto_servido(hit.get("summary") or hit.get("fact") or knowledge_id),
            "uuid": _texto_servido(procedencia.get("uuid")),
            "fuente": clase,
        }
        if clase == "hecho":
            # El intent temporal vive de esto: la vigencia la declara el grafo, no el cliente.
            acierto.update({"fact": _texto_servido(hit.get("fact")),
                            "valid_at": _texto_servido(hit.get("valid_at")),
                            "invalid_at": _texto_servido(hit.get("invalid_at"))})
        # Gap #118 (Important, fix2 Fase 3; residual de #96): cuando la busqueda devuelve v1 Y v2
        # del mismo `knowledge_id` -el caso NORMAL: dos versiones de la misma entrada casan la
        # misma query- la deduplicacion se quedaba con el PRIMER hit, asi que `[v1, v2]` servia
        # «version 1 · invalidado» y tiraba la v2 aprobada en silencio. Se agrupa por
        # `knowledge_id` y se sirve la VIGENTE (la no invalidada de mayor `version`).
        previo = candidatos.get(knowledge_id)
        if previo is None or _mas_vigente(acierto, previo):
            candidatos[knowledge_id] = acierto
        # Las versiones descartadas por no ser la vigente NO son «descartados»: la entrada SI se
        # sirve (es el mismo `knowledge_id`), solo que por su version vigente.

    aciertos = list(candidatos.values())
    motivos = [m for m in (motivo_nodos, motivo_hechos) if m]
    if fuera_de_ventana:
        motivos.append(
            f"{fuera_de_ventana} acierto(s) fuera de la ventana de procedencia "
            f"({tope_episodios} episodios, `max_episodes`): sube `max_episodes` o acota la consulta")
    return {"aciertos": aciertos[:limit], "descartados": descartados,
            "fuera_de_ventana": fuera_de_ventana, "motivo": "; ".join(motivos)}
