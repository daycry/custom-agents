#!/usr/bin/env python3
"""
backends/markdown_export.py — adaptador Kwipu (`type: "markdown-export"`, ADR-018, T-08) del
contrato de `backends/__init__.py`. Escribe UN Markdown por entrada `approved/` ya enrutada, con
el frontmatter del Knowledge Gate del stack (CA-17), más `manifest.json` con hashes estables.
`health`/`verify` hablan por HTTP con el bridge de Kwipu, pero NUNCA importan ni ejecutan nada del
stack (`build_view`, reinicios de contenedor, etc.) — el remedio se NOMBRA, no se aplica (CA-16).

Sin dependencias externas; solo stdlib (`hashlib`, `json`, `urllib.request`).

Derivaciones de CA-17 (ningún campo se inventa; documentadas aquí porque no hay otro sitio donde
fijarlas — decisión de T-08, ver también `skills/knowledge-services/backends/README.md`):
  - `knowledge_id` = `entry["id"]` tal cual (el Curator ya lo escribe con el `id_prefix.` del
    proyecto delante, `agents/knowledge-curator.md`).
  - `project`      = el primer segmento de `knowledge_id` antes del primer `.` (el `id_prefix`
    del proyecto — es el único identificador de proyecto disponible sin tocar `knowledge-sync.py`
    ni el contrato de adaptador para pasar la taxonomía completa).
  - `scope`        = `"project"` (constante: esta iniciativa exporta conocimiento de UN proyecto;
    `"global"` sería para conocimiento compartido entre proyectos, fuera de alcance aquí).
  - `source`       = `"agent"` (constante: todo lo que llega a `approved/` pasó por
    `knowledge-curator`, un agente — no hay hoy una vía que marque una entrada como confirmada
    por un humano de forma distinguible en el frontmatter de la entrada).
  - `confidence`   = de `evidencia` vía la escalera POR DEFECTO del plugin (`knowledge-schema.py`
    `_TAXONOMY_FALLBACK["evidence_levels"]`): observation/single_case -> low,
    validated_case/multiple_validated_cases -> medium, human_confirmed_rule -> high; un nivel de
    evidencia que un proyecto haya redefinido en su propio `taxonomy.json` y que no esté en esta
    tabla degrada a `medium` (no se inventa un extremo).

Gaps de la revisión de dos lentes corregidos en este fichero:
  - #82/#109/#115/#118/#123 (intento 2, Fase 3, fix2, 2026-09-18): publicación por intercambio de
    directorio (SUSTITUIDA en fix3, ver bloque siguiente — se deja la referencia histórica porque
    `plan()`/`rebuild()` siguen citando estos números en sus docstrings).
  - **#126/#127/#129/#132/#134/#136/#137/#138 (intento 3, Fase 3, fix3, 2026-09-18): publicación
    por FICHERO con diario, sustituyendo el intercambio de directorio (decisión del orquestador —
    ese diseño resultó en dos Critical nuevos: pérdida de datos en el rollback y borrado de
    ficheros ajenos a `export_dir`).** Algoritmo (`docs/roadmap/2026-09-15-knowledge-services/
    tasks.md`, bloque «Diseño sustitutivo»):
      1. `plan()` como siempre (hash + existencia; `force=True` en `--rebuild`).
      2. `apply()` escribe SOLO los `upsert` en un staging HERMANO (`<export_dir>.staging-<pid>`);
         los `sin_cambios` NUNCA SE TOCAN (ni se mueven ni se reescriben — elimina de raíz la
         regresión O(N) del gap 136: una pasada sin cambios ya no cuesta un rename por fichero).
      3. Antes de publicar nada, escribe `manifest.pending.json` en `export_dir` (tmp+`os.replace`
         atómico, `_escribir_manifest_atomico`) con el estado final previsto (entries + hashes).
      4. Publica cada `upsert` con UN `os.replace` fichero-a-fichero desde el staging al destino
         (nunca el árbol entero — gap 127: un `export_dir` ajeno con ficheros de otros proyectos,
         o `export_dir: "docs"`, ya no puede perder nada que no sea suyo) y ejecuta los `revoke`
         (solo ficheros que estaban en el manifiesto propio, `os.remove` best-effort).
      5. Renombra `manifest.pending.json` -> `manifest.json` (atómico) y borra el staging.
    Si falla en (2)-(3): nada ha cambiado en `export_dir` (staging es hermano, se descarta; el
    `manifest.pending.json` se escribe con tmp+rename, así que un fallo a mitad de esa escritura
    tampoco dejó nada a medias — gap 126, antes un `except BaseException` sin reponer perdía la
    publicación entera aunque fuera puramente `sin_cambios`). Si falla en (4) a mitad (p. ej.
    `PermissionError` porque el indexador tiene un `.md` abierto): los ficheros ya publicados
    quedan intactos, `manifest.pending.json` se conserva, y la SIGUIENTE corrida lo usa como
    manifiesto objetivo en `plan()`: los ficheros cuyo hash en disco ya coincide con el objetivo
    son `sin_cambios`, el resto vuelve a ser `upsert` — así se completa la publicación
    interrumpida sin perder nada, sin necesidad de reintentar dentro de la misma corrida.
    `verify()` con `manifest.pending.json` presente devuelve `ok: False,
    razon: "publicacion_incompleta"` (antes que cualquier otra comprobación). El lock hermano
    (`_LockDirectorio`) se conserva sin cambios. Contención BIDIRECCIONAL en
    `_export_dir_resuelto` (gap 127): `export_dir` no puede contener ni estar contenido en
    `docs/knowledge/`, ni ser el root del proyecto ni un ANCESTRO del root (antes solo se
    comprobaba que `export_dir` no quedara dentro de `docs/knowledge/approved/`; `"docs"` o `".."`
    pasaban todas las validaciones y un solo `apply()` podía barrer medio proyecto). `revoke()`
    público usa el mismo diario (pending -> publica -> manifest.json). Ya no existe `.prev` ni el
    intercambio de directorio: `_purgar_staging_huerfano` (antes `_reparar_publicacion`) solo
    limpia un `.staging-<pid>` hermano de una corrida interrumpida, nunca reconstruye nada.
    Coste: proporcional a los CAMBIOS (una escritura + un rename por fichero cambiado; 0 por
    `sin_cambios`, gap 118/136 corregido).
  - #132/#138: la caché DNS (`_dns_cache`) ya no es indefinida por proceso: cada resolución
    (positiva, negativa o "no resuelta a tiempo") expira a los `_DNS_CACHE_TTL_S` segundos, así que
    un fallo transitorio no queda cacheado en negativo para siempre. El caso "colgado" (agota
    `_DNS_TIMEOUT_S` sin resolver) también se cachea, con un TTL corto (`_DNS_CACHE_TTL_S_LENTO`),
    y un registro `_dns_inflight` evita lanzar un hilo nuevo para el mismo host mientras el
    anterior sigue vivo: llamadas repetidas al mismo host lento se unen (`join`) al hilo YA en
    marcha en vez de acumular uno por llamada.
  - #137: las redirecciones HTTP están acotadas a `_MAX_REDIRECCIONES` saltos, y el presupuesto de
    tiempo de toda la CADENA es el `timeout_ms` configurado UNA VEZ (no por salto): cada hop
    reduce el `timeout` restante del siguiente en vez de heredar el valor original completo, así
    que una cadena de redirecciones ya no puede multiplicar el tiempo total por el número de
    saltos.
  - #87: `verify()` sin manifiesto (o vacío) devuelve `ok: False` con `razon: "nunca_sincronizado"`
    en vez de un `ok: True` trivial (falso positivo: nunca se sincronizó nada).
  - #88/#102: `export_dir` se resuelve contra `cfg["_root"]` (nunca CWD) y se valida que no sea el
    propio root ni quede dentro de `docs/knowledge/approved/`.
  - #89: `timeout_ms` se valida como número positivo; un valor no numérico o `None` cae al
    default (800) en vez de reventar con `TypeError`.
  - #92: `HTTPError` se distingue de `URLError`: 5xx -> `degradado`, 4xx -> `error` (con el cuerpo
    si es JSON parseable); solo fallos de conexión/timeout -> `off`.
  - #93: `plan()` compara el `hash` calculado contra el `hash` ya en `manifest.json`; si coincide,
    la operación es `sin_cambios` en vez de `upsert` (idempotente de verdad, no solo "no rompe").
  - #97/#112 (intento 1 + intento 2 fix2): `health()`/`verify()` rechazan hosts que no sean
    locales/privados (mismo criterio que `agent-kits/nemesis/tools/lib-guardrail.sh`) ANTES de
    abrir conexión, Y revalidan el host de CUALQUIER redirección HTTP antes de seguirla (gap 112,
    CWE-918/601): un bridge local que responda `302 Location: http://<host público>/…` ya no se
    sigue en silencio, se rechaza como `estado: "error"`.
  - #101: `verify()` compara también el `hash` del snapshot cuando el nodo lo trae; si el
    snapshot no expone hash, lo declara (`comparacion: "nombre"`) en vez de fingir que comparó.
  - #103: `_base_url_snapshot` usa `urllib.parse` para quitar el sufijo `/health` de la RUTA
    (con o sin barra final), preservando query/prefijo.
  - #117 (intento 2 fix2): `_host_permitido` resuelve el hostname con un TOPE de tiempo (hilo +
    `join`, `_DNS_TIMEOUT_S`) y cachea el resultado por proceso: un resolutor lento o que agota
    reintentos ya no puede anular el tope de `timeout_ms` de `health()`/`verify()`.
  - #121 (intento 2 fix2): `_export_dir_resuelto` usa `os.path.realpath` (no solo `abspath`) y
    compara con `os.path.normcase` (case-insensitive en Windows): un junction/symlink que apunte
    a `docs/knowledge/approved/`, o una diferencia de mayúsculas, ya no evade la contención.
  - #125 (intento 2 fix2): los `ops` `sin_cambios` NO llevan `cuerpo` (era el campo más pesado del
    envelope de la outbox en una corrida sin cambios; `apply()` no lo necesita para un fichero que
    solo se mueve tal cual).
"""
import contextlib
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

# Consola no UTF-8 (Windows cp1252) o tuberías: reconfigurar ANTES de leer/imprimir (GOT-005).
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure, ya leído o None (capsys, pythonw)

MANIFEST_VERSION = 1
MANIFEST_NOMBRE = "manifest.json"
MANIFEST_PENDING_NOMBRE = "manifest.pending.json"  # gap 126/136 (fix3): diario de la publicación
                                                    # por fichero — objetivo escrito ANTES de
                                                    # publicar ningún fichero, renombrado a
                                                    # `manifest.json` al terminar
_LOCK_SUFIJO = ".lock"
_LOCK_TTL_S = 60  # un lock más viejo que esto se considera huérfano (proceso muerto)
_STAGING_PREFIJO = ".staging-"
_STAGING_TTL_S = 60  # gap 82/115: un `.staging-*` hermano más viejo que esto es de una corrida
                     # interrumpida (SIGKILL) — se purga al arrancar `apply()`
_DNS_TIMEOUT_S = 1.0  # gap 117: tope de la resolución DNS de `_host_permitido`, independiente
                      # del `timeout_ms` HTTP configurado
_DNS_CACHE_TTL_S = 300  # gap 132: una resolución (positiva o negativa) expira; un fallo
                        # transitorio ya no queda cacheado en negativo para siempre
_DNS_CACHE_TTL_S_LENTO = 5  # gap 138: el caso "colgado" (agotó _DNS_TIMEOUT_S) se cachea con un
                            # TTL corto para no perforar el `join()` en cada llamada consecutiva,
                            # pero se reintenta pronto (podría ser un pico transitorio del DNS)
_MAX_REDIRECCIONES = 5  # gap 137: tope de saltos de una cadena de redirección HTTP

REMEDIO = "reindexar: `build_view` + reiniciar `kwipu`, `kwipu-bridge`, `kwipu-mcp`"

_MAPA_CONFIANZA = {
    "observation": "low",
    "single_case": "low",
    "validated_case": "medium",
    "multiple_validated_cases": "medium",
    "human_confirmed_rule": "high",
}

# --8<-- hosts locales COMPARTIDO (graphiti-memory T-01-fix1) — REPLICADO LITERAL en skills/knowledge-services/backends/markdown_export.py, agent-kits/shared/knowledge-schema.py y skills/knowledge-services/backends/graphiti.py
_SUFIJOS_LOCALES = (".test", ".local", ".internal")
_HOSTS_LOCALES_LITERALES = {"localhost", "host.docker.internal"}
# --8<-- fin hosts locales COMPARTIDO

_dns_cache = {}  # gap 117/132/138: caché de resolución por proceso — {host: (ip_str_o_None, expira_ts)}
_dns_inflight = {}  # gap 138: {host: threading.Thread} — una resolución lenta en marcha se
                    # reutiliza (join) en vez de lanzar un hilo nuevo por cada llamada concurrente
_dns_inflight_lock = threading.Lock()


class ConfigInvalida(Exception):
    """Error de configuración del adaptador (export_dir/host no permitido/etc.) — el llamador
    (`knowledge-sync.py`) lo convierte en `exit 1` con mensaje, nunca en un traceback."""


class _RedireccionNoPermitida(Exception):
    """gap 112: una redirección HTTP apuntaba a un host que no es local/privado."""

    def __init__(self, url):
        super().__init__(url)
        self.url = url


def _proyecto_de(knowledge_id):
    return knowledge_id.split(".", 1)[0] if "." in knowledge_id else knowledge_id


def _confianza_de(evidencia):
    return _MAPA_CONFIANZA.get(evidencia, "medium")


def _slug_fichero(knowledge_id):
    """`knowledge_id` ya cumple `[A-Za-z0-9._-]+` (lo exige el Curator); es un nombre de fichero
    seguro tal cual, sin necesidad de un slugger nuevo. Defensa en profundidad (gap 96): se
    revalida aquí también, por si un `knowledge-index.py` de otra versión no lo hiciera."""
    import re
    if not isinstance(knowledge_id, str) or not re.match(r"^[A-Za-z0-9._-]+$", knowledge_id):
        raise ConfigInvalida(
            f"`knowledge_id` (`{knowledge_id}`) no cumple la forma `[A-Za-z0-9._-]+`; "
            "se rechaza para no escribir fuera de `export_dir`")
    return f"{knowledge_id}.md"


def _timeout_s(cfg_dict, default_ms=800):
    """Valida `timeout_ms`: solo números positivos; cualquier otra cosa (None, str, 0, negativo)
    cae al default (gap 89) en vez de propagar un `TypeError` a mitad de una llamada de red."""
    valor = (cfg_dict or {}).get("timeout_ms")
    if not isinstance(valor, (int, float)) or isinstance(valor, bool) or valor <= 0:
        valor = default_ms
    return max(0.01, valor / 1000.0)


def _resolver_host_con_tope(host, timeout_s=_DNS_TIMEOUT_S):
    """gap 117: `socket.gethostbyname` no acepta un timeout propio y puede colgarse (resolutor
    lento, reintentos agotados) mucho más de lo que pide `timeout_ms`. Se resuelve en un hilo
    aparte con `join(timeout_s)`: si no termina a tiempo, se trata como "no resuelto" ESTA vez
    (fail-closed en `_host_permitido`) sin esperar más, y NO se cachea (podría resolver más tarde).
    Cachea por proceso el resultado positivo o negativo, con TTL (gap 132: antes la caché era
    indefinida por proceso — un fallo transitorio de DNS quedaba cacheado en negativo para
    siempre; ahora expira a los `_DNS_CACHE_TTL_S` segundos). El caso "colgado" también se cachea,
    con un TTL corto (`_DNS_CACHE_TTL_S_LENTO`), y usa un registro de resoluciones en marcha
    (`_dns_inflight`, gap 138) para que llamadas concurrentes/consecutivas al mismo host lento se
    UNAN (`join`) al hilo ya lanzado en vez de acumular un hilo nuevo por cada llamada — sin esto,
    un bridge que tarda en resolver podía acabar con un hilo colgado por cada `health()`/`verify()`
    que le llegara mientras tanto."""
    ahora = time.time()
    entrada = _dns_cache.get(host)
    if entrada is not None and entrada[1] > ahora:
        return entrada[0]

    with _dns_inflight_lock:
        hilo = _dns_inflight.get(host)
        if hilo is None:
            resultado = {}

            def _resolver():
                try:
                    resultado["ip"] = socket.gethostbyname(host)
                except OSError:
                    resultado["ip"] = None

            hilo = threading.Thread(target=_resolver, daemon=True)
            hilo.resultado = resultado
            _dns_inflight[host] = hilo
            es_propio = True
        else:
            es_propio = False
        # gap 138 (fix3b): `start()` DENTRO del lock — si se lanzara fuera, otro hilo podia leer
        # `_dns_inflight[host]` y llamar `join()` ANTES de que este hilo arrancara
        # (`RuntimeError: cannot join thread before it is started`, visto en corridas concurrentes
        # reales de 3 hilos contra el mismo host lento). `start()` es no bloqueante y barata: no
        # amplia la seccion critica de forma perceptible.
        if es_propio:
            hilo.start()

    hilo.join(timeout_s)
    if hilo.is_alive():
        # gap 138: colgado esta vez — se cachea "no resuelto" con TTL corto (no perfora el tope en
        # llamadas consecutivas inmediatas, pero se reintenta pronto). El hilo sigue en marcha en
        # `_dns_inflight`: quien lo lanzó lo retirará cuando termine (abajo).
        _dns_cache[host] = (None, time.time() + _DNS_CACHE_TTL_S_LENTO)
        return None

    ip = getattr(hilo, "resultado", {}).get("ip")
    if es_propio:
        with _dns_inflight_lock:
            _dns_inflight.pop(host, None)
    _dns_cache[host] = (ip, time.time() + _DNS_CACHE_TTL_S)
    return ip


def _host_permitido(url):
    """Invariante de seguridad del plugin (gap 97, CWE-918): solo hosts locales/privados, mismo
    criterio que `agent-kits/nemesis/tools/lib-guardrail.sh`. Se resuelve el hostname (con tope y
    caché, gap 117) y se comprueba la IP resultante; si no resuelve, se rechaza (fail-closed)."""
    try:
        partes = urllib.parse.urlsplit(url)
    except ValueError:
        return False
    if partes.scheme not in ("http", "https"):
        return False
    host = partes.hostname
    if not host:
        return False
    host_lower = host.lower()
    if host_lower in _HOSTS_LOCALES_LITERALES or host_lower.endswith(_SUFIJOS_LOCALES):
        return True
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        resuelto = _resolver_host_con_tope(host)
        if resuelto is None:
            return False
        try:
            ip = ipaddress.ip_address(resuelto)
        except ValueError:
            return False
    return bool(ip.is_loopback or ip.is_private)


class _SinRedireccionAutomatica(urllib.request.HTTPRedirectHandler):
    """gap 137: NO sigue redirecciones automáticamente (`redirect_request` -> `None` hace que la
    cadena de manejadores de `urllib` termine propagando el `HTTPError` 30x tal cual, en vez de
    perseguir el `Location` por su cuenta). `_urlopen_local` las sigue A MANO, con un presupuesto
    de tiempo TOTAL para toda la cadena en vez de por salto — el `HTTPRedirectHandler` de serie
    reutiliza el `timeout` original en CADA salto (`OpenerDirector.open()` se lo reasigna al
    request nuevo en cada `self.parent.open(new, timeout=req.timeout)`), así que antes una cadena
    de N redirecciones podía tardar hasta N veces `timeout_ms` en vez de, como mucho, una vez."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: N802 — API de urllib
        return None


def _urlopen_local(url, timeout_s):
    """Sigue redirecciones a mano (gap 137, ver `_SinRedireccionAutomatica`): revalida CADA salto
    contra `_host_permitido` ANTES de seguirlo (gap 112 — un bridge local comprometido no puede
    usar un `302` para hablar con un host público), acota el número de saltos a
    `_MAX_REDIRECCIONES`, y reparte un presupuesto de tiempo ÚNICO (`timeout_s`) entre toda la
    cadena: cada hop resta lo que ya ha tardado del tiempo que le queda al siguiente, en vez de
    heredar `timeout_s` completo en cada salto. Usa un `opener` nuevo por llamada: es barato (sin
    estado que compartir) y evita cualquier fuga de configuración entre llamadas de
    `health()`/`verify()` en el mismo proceso."""
    opener = urllib.request.build_opener(_SinRedireccionAutomatica)
    deadline = time.time() + timeout_s
    url_actual = url
    saltos = 0
    while True:
        if not _host_permitido(url_actual):
            raise _RedireccionNoPermitida(url_actual)
        restante = deadline - time.time()
        if restante <= 0:
            raise TimeoutError(
                f"tiempo agotado (presupuesto total {timeout_s:.3f}s) siguiendo la cadena de "
                f"redirecciones hacia `{url_actual}`")
        try:
            return opener.open(url_actual, timeout=restante)
        except urllib.error.HTTPError as e:
            if e.code not in (301, 302, 303, 307, 308):
                raise
            newurl = e.headers.get("Location") if e.headers else None
            if not newurl:
                raise
            saltos += 1
            if saltos > _MAX_REDIRECCIONES:
                raise _RedireccionNoPermitida(
                    urllib.parse.urljoin(url_actual, newurl)) from e
            url_actual = urllib.parse.urljoin(url_actual, newurl)


def _export_dir_resuelto(cfg):
    """Resuelve `export_dir` contra `cfg["_root"]` (gap 88: nunca CWD) y valida la contención
    BIDIRECCIONAL con `docs/knowledge/` y con el root del proyecto (gap 127, fix3): antes solo se
    comprobaba que `export_dir` no quedara DENTRO de `docs/knowledge/approved/` y que no fuera el
    root exacto — `export_dir: "docs"` (que CONTIENE `docs/knowledge/`) o `export_dir: ".."` (un
    ANCESTRO del root) pasaban esa comprobación sin problema, y con la publicación por fichero
    (gap 126) un `apply()`/`rebuild()` sobre esa config podía escribir/borrar fuera del árbol que
    el adaptador tiene permiso de tocar. Ahora se rechazan las CUATRO formas de solape:
    `export_dir` == root, `export_dir` ANCESTRO del root, `export_dir` DENTRO de
    `docs/knowledge/`, `export_dir` CONTIENE `docs/knowledge/`. `knowledge-sync.py`/`doctor.py`
    deben inyectar `_root` en el `cfg` del adaptador.

    Gap 121: la contención usa `os.path.realpath` (no solo `abspath`, que no sigue symlinks ni
    junctions) y compara con `os.path.normcase` (en Windows, insensible a mayúsculas): sin esto,
    un junction/symlink que apuntara a `docs/knowledge/`, o una ruta con mayúsculas distintas,
    evadía la comprobación."""
    export_dir = (cfg or {}).get("export_dir")
    if not export_dir:
        raise ConfigInvalida("falta `export_dir` en la config del backend")
    root = (cfg or {}).get("_root") or "."
    root_abs = os.path.realpath(root)
    resuelto = export_dir if os.path.isabs(export_dir) else os.path.join(root_abs, export_dir)
    resuelto_real = os.path.realpath(resuelto)
    sep_nc = os.path.normcase(os.sep)
    resuelto_nc = os.path.normcase(resuelto_real)
    root_nc = os.path.normcase(root_abs)
    if resuelto_nc == root_nc:
        raise ConfigInvalida(
            f"`export_dir` (`{export_dir}`) no puede ser la raíz del proyecto (`{root_abs}`)")
    if root_nc.startswith(resuelto_nc + sep_nc):
        raise ConfigInvalida(
            f"`export_dir` (`{export_dir}`) no puede ser un ANCESTRO de la raíz del proyecto "
            f"(`{root_abs}` quedaría dentro de `{resuelto_real}`)")
    conocimiento_real = os.path.realpath(os.path.join(root_abs, "docs", "knowledge"))
    conocimiento_nc = os.path.normcase(conocimiento_real)
    if resuelto_nc == conocimiento_nc or resuelto_nc.startswith(conocimiento_nc + sep_nc):
        raise ConfigInvalida(
            f"`export_dir` (`{export_dir}`) no puede quedar dentro de "
            "`docs/knowledge/` (pisaría la fuente canónica)")
    if conocimiento_nc == resuelto_nc or conocimiento_nc.startswith(resuelto_nc + sep_nc):
        raise ConfigInvalida(
            f"`export_dir` (`{export_dir}`) no puede CONTENER `docs/knowledge/` "
            f"(`{conocimiento_real}` quedaría dentro de `{resuelto_real}`)")
    return resuelto_real


def _resumen_de(cuerpo):
    """gap 83: "resumen" = el primer párrafo del cuerpo (hasta la primera línea en blanco tras
    contenido), o el `resumen:` explícito del frontmatter si la entrada lo trae — el adaptador es
    quien decide qué es un resumen (SKILL.md, `references/kwipu-adapter.md`), el núcleo solo pasa
    `modo` y el cuerpo completo."""
    lineas = cuerpo.strip("\n").splitlines()
    parrafo = []
    for linea in lineas:
        if not linea.strip() and parrafo:
            break
        if linea.strip():
            parrafo.append(linea)
    return "\n".join(parrafo).strip()


def _cuerpo_segun_modo(entry):
    cuerpo = entry.get("cuerpo") or ""
    if entry.get("modo") != "resumen":
        return cuerpo
    resumen_explicito = entry.get("resumen")
    if isinstance(resumen_explicito, str) and resumen_explicito.strip():
        return resumen_explicito.strip()
    return _resumen_de(cuerpo)


def _hash_contenido(knowledge_id, version, category, cuerpo):
    """sha256 del contenido SEMÁNTICO (no de los bytes finales del fichero, que ya incluyen este
    mismo hash en su frontmatter — evita la circularidad). Estable entre corridas: mismo
    `knowledge_id`+`version`+`category`+`cuerpo` -> mismo hash."""
    base = f"{knowledge_id}\n{version}\n{category}\n{cuerpo}".encode("utf-8")
    return hashlib.sha256(base).hexdigest()


def _render_markdown(op):
    hash_ = _hash_contenido(op["knowledge_id"], op["version"], op["category"], op["cuerpo"])
    frontmatter = (
        "---\n"
        f"knowledge_id: {op['knowledge_id']}\n"
        f"project: {op['project']}\n"
        "scope: project\n"
        f"category: {op['category']}\n"
        "source: agent\n"
        f"confidence: {op['confidence']}\n"
        f"version: {op['version']}\n"
        f"hash: {hash_}\n"
        "---\n\n"
    )
    return frontmatter + op["cuerpo"].rstrip() + "\n", hash_


def _hash_publicado_en(ruta):
    """Lee el `hash: ...` del frontmatter YA ESCRITO en disco (gap 126/136, fix3): decidir
    `sin_cambios` comparando solo el hash GUARDADO en el manifiesto/pending contra el hash
    recién calculado no basta cuando el objetivo viene de `manifest.pending.json` — ese fichero
    describe lo que `apply()` PRETENDÍA dejar publicado, no necesariamente lo que ya está en disco
    (una entrada puede figurar en el pending con su hash NUEVO sin que el `os.replace` que la
    publica haya llegado a ejecutarse todavía). Comparar el hash calculado contra el que el propio
    FICHERO dice tener (su frontmatter) es la única forma fiable de saber si ese fichero concreto
    ya refleja ese contenido, venga el objetivo de `manifest.json` o de una publicación
    interrumpida. `None` si el fichero no existe, no es legible, o no trae la línea (fichero
    ajeno/corrupto) — nunca lanza."""
    try:
        with open(ruta, "r", encoding="utf-8") as fh:
            for _ in range(15):  # el frontmatter de `_render_markdown` cabe en ~10 líneas
                linea = fh.readline()
                if not linea:
                    break
                if linea.startswith("hash: "):
                    return linea[len("hash: "):].strip()
    except OSError:
        return None
    return None


def _leer_manifest_json(ruta):
    """Lee un fichero de manifiesto (nombre indistinto: `manifest.json` o
    `manifest.pending.json`) desde una ruta concreta. `None` si no existe o es ilegible/inválido
    (nunca lanza: un manifiesto corrupto se trata como ausente, no como error fatal)."""
    if not os.path.isfile(ruta):
        return None
    try:
        with open(ruta, "r", encoding="utf-8-sig") as f:
            datos = json.load(f)
    except (OSError, ValueError):
        return None
    if not isinstance(datos, dict) or not isinstance(datos.get("entries"), dict):
        return None
    return datos


def _leer_manifest(export_dir):
    """`manifest.json` PUBLICADO; `{"version": ..., "entries": {}}` si no existe o es inválido."""
    return _leer_manifest_json(os.path.join(export_dir, MANIFEST_NOMBRE)) or \
        {"version": MANIFEST_VERSION, "entries": {}}


def _leer_pending(export_dir):
    """gap 126/136 (fix3): `manifest.pending.json` de una publicación interrumpida, o `None` si no
    hay ninguna en curso. `plan()`/`apply()`/`revoke()` lo usan como manifiesto OBJETIVO cuando
    existe (en vez del `manifest.json` ya publicado) para retomar exactamente donde se quedó."""
    return _leer_manifest_json(os.path.join(export_dir, MANIFEST_PENDING_NOMBRE))


def _escribir_manifest_atomico(ruta, manifest):
    """tmp + `os.replace` en el MISMO directorio (atómico a nivel de SO, gap 126): un fallo
    escribiendo el contenido (disco lleno, permisos, proceso matado a mitad) nunca deja un
    `manifest.pending.json`/`manifest.json` a medias legible como JSON roto — o se escribe
    entero, o no se toca nada de lo que había antes en `ruta`."""
    directorio = os.path.dirname(ruta) or "."
    fd, tmp = tempfile.mkstemp(prefix=".tmp-manifest-", dir=directorio)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(manifest, ensure_ascii=False, indent=2))
        os.replace(tmp, ruta)
    except BaseException:
        with contextlib.suppress(OSError):
            os.remove(tmp)
        raise


class _LockDirectorio:
    """Lock de exclusión mutua entre `apply()`/`revoke()` concurrentes sobre el mismo `export_dir`
    (gap 82/115): un fichero HERMANO (`<export_dir>.lock`, fuera del árbol que se intercambia)
    creado con `O_CREAT|O_EXCL` (atómico a nivel de SO); si el lock existe pero es más viejo que
    `_LOCK_TTL_S`, se considera huérfano (proceso muerto sin limpiar) y se reclama."""

    def __init__(self, lock_path):
        self._ruta = lock_path
        self._propio = False

    def __enter__(self):
        os.makedirs(os.path.dirname(self._ruta) or ".", exist_ok=True)
        for _ in range(2):
            try:
                fd = os.open(self._ruta, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.close(fd)
                self._propio = True
                return self
            except FileExistsError:
                try:
                    edad = time.time() - os.path.getmtime(self._ruta)
                except OSError:
                    edad = 0
                if edad > _LOCK_TTL_S:
                    try:
                        os.remove(self._ruta)
                    except OSError:
                        pass
                    continue
                raise ConfigInvalida(
                    "hay otra publicación en curso sobre este `export_dir` "
                    f"(lock `{self._ruta}`); reintenta cuando termine")
        raise ConfigInvalida(f"no se pudo adquirir el lock de publicación (`{self._ruta}`)")

    def __exit__(self, *exc):
        if self._propio:
            try:
                os.remove(self._ruta)
            except OSError:
                pass


def _lock_path(export_dir):
    return export_dir.rstrip(os.sep) + _LOCK_SUFIJO


# gap 182 (revisión Fase 4 intento 3): la alternativa ANSI (`\x1b\[[0-9;]*[A-Za-z]`) era
# INALCANZABLE porque `re` prueba las alternativas de un `|` EN ORDEN en cada posición y se queda
# con la PRIMERA que casa (no la más larga) — como `\x1b` ya cae dentro de `[\x00-\x1f\x7f]`
# (primera alternativa), el motor nunca llegaba a intentar la segunda: solo se sustituía el propio
# `ESC` y el resto de la secuencia (`[31m`, `[0m`) quedaba intacto en el texto. Se reordena para
# que la alternativa ANSI (más específica) se intente PRIMERO.
#
# gap 176 (CWE-117, fuera de lente, señalado por la Lente B): `health()`/`verify()` embebían el
# mensaje de la excepción de red — que en el caso de `http.client.HTTPException`/`OSError` puede
# contener bytes CRUDOS de lo que respondió el servidor (p. ej. `BadStatusLine` incluye la primera
# línea recibida tal cual) — directamente en `detalle`/`motivo`, que acaban impresos por `/doctor`.
# Un servidor (aunque sea local, ya pasó `_host_permitido`) que devuelva CRLF o secuencias de
# escape ANSI podía así inyectar saltos de línea o color en esa salida.
#
# gap 182 (revisión Fase 4 intento 3): el tope de 200 debe aplicarse SOLO al texto NO CONFIABLE (lo
# que viene del servidor) — los llamadores NUNCA deben pasar el prefijo propio (de confianza,
# f"... de {url}: ") dentro de este saneado: si lo hacen, el prefijo se come parte del tope (o lo
# desplaza fuera de los 200 caracteres) sin ganar nada, porque el prefijo no es el dato peligroso.
# El prefijo se antepone DESPUÉS, sobre el resultado ya saneado y recortado.
#
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


def health(cfg):
    """Nunca lanza: cualquier fallo de red/parseo degrada a un `estado` del enum
    `off · sano · degradado · error` (design.md, tabla del contrato de adaptador)."""
    health_cfg = (cfg or {}).get("health") or {}
    url = health_cfg.get("url")
    if not url:
        return {"estado": "off", "detalle": "sin `health.url` configurada"}
    if not _host_permitido(url):
        return {"estado": "error", "detalle": f"host no local/privado, rechazado: {url}"}
    timeout_s = _timeout_s(health_cfg)
    try:
        with _urlopen_local(url, timeout_s) as resp:
            cuerpo = resp.read()
    except _RedireccionNoPermitida as e:
        # gap 180: `e.url` viene del cabecera `Location` del servidor (no confiable) — se sanea
        # ANTES de anteponer el prefijo de confianza, igual que en el resto de ramas (gap 182).
        return {"estado": "error",
                "detalle": f"redirección a host no local/privado, rechazada: {_sanear_detalle(e.url)}"}
    except urllib.error.HTTPError as e:
        # gap 180: `cuerpo_err` es JSON ya parseado, pero sus valores de cadena vienen del
        # servidor tal cual (CRLF/ANSI, sin tope) — se sanea su representación antes de embeberla.
        cuerpo_err = _cuerpo_json_o_none(e)
        detalle = f"HTTP {e.code} de {url}" + (f": {_sanear_detalle(cuerpo_err)}" if cuerpo_err else "")
        return {"estado": "degradado" if 500 <= e.code < 600 else "error", "detalle": detalle}
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return {"estado": "off", "detalle": f"sin conexión a {url}: {type(e).__name__}: {e}"}
    except http.client.HTTPException as e:
        # gap 155: un servidor local (permitido, ya pasó `_host_permitido`) puede responder algo
        # que no es HTTP en absoluto (`BadStatusLine`, etc.) — `http.client.HTTPException` NO es
        # subclase de `OSError`, así que sin este `except` explícito escapaba hasta el llamador
        # pese a que este docstring promete «nunca lanza».
        # gap 176 (CWE-117): el mensaje de `BadStatusLine` incluye la primera línea CRUDA que
        # respondió el servidor — se sanea (control/ANSI fuera, tope 200) antes de devolverla.
        # gap 182: el tope de 200 se aplica SOLO a `{e}` (lo no confiable), no al prefijo propio
        # (`respuesta no HTTP de {url}: {type(e).__name__}: `, de confianza) — si no, el prefijo
        # se come parte del tope o lo desplaza fuera de los 200 caracteres.
        return {"estado": "error",
                "detalle": f"respuesta no HTTP de {url}: {type(e).__name__}: {_sanear_detalle(e)}"}
    except ValueError as e:
        # gap 184: un `Location` mal formado (p. ej. `http://[` con un corchete de IPv6 sin
        # cerrar) hace que `urllib.parse.urljoin`/`urlsplit`, dentro de `_urlopen_local`, lancen
        # `ValueError` — antes escapaba de `health()` pese al docstring («nunca lanza»); `verify()`
        # ya lo capturaba porque su propio bloque agrupa `ValueError` (por otra razón: el `json.
        # loads` del snapshot). Mismo tratamiento que las demás ramas de red: nunca lanza, degrada.
        return {"estado": "error",
                "detalle": f"URL o redirección mal formada en {url}: {_sanear_detalle(e)}"}
    try:
        datos = json.loads(cuerpo.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as e:
        return {"estado": "error", "detalle": f"respuesta no es JSON válido: {e}"}
    if not isinstance(datos, dict):
        return {"estado": "error", "detalle": "respuesta JSON no es un objeto"}
    status = datos.get("status")
    pg_status = ((datos.get("property_graph") or {}).get("status")
                 if isinstance(datos.get("property_graph"), dict) else None)
    ollama_status = ((datos.get("ollama") or {}).get("status")
                     if isinstance(datos.get("ollama"), dict) else None)
    detalle = f"status={status}, property_graph={pg_status}, ollama={ollama_status}"
    if status == "ok" and pg_status in (None, "ok") and ollama_status in (None, "ok"):
        return {"estado": "sano", "detalle": detalle}
    if status in ("ok", "degraded", None):
        return {"estado": "degradado", "detalle": detalle}
    return {"estado": "error", "detalle": detalle}


def _cuerpo_json_o_none(http_error):
    try:
        return json.loads(http_error.read().decode("utf-8"))
    except Exception:  # noqa: BLE001 — el cuerpo de un HTTPError es best-effort
        return None


def plan(entries, cfg, force=False):
    """Idempotente: mismas `entries` -> mismo `ops`. Compara contra el manifiesto OBJETIVO en
    `export_dir` para calcular los `revoke` de entradas que ya no están en `entries` (salieron de
    `approved/` o dejaron de enrutar a este backend). Gap 126/136 (fix3): si hay una publicación
    interrumpida (`manifest.pending.json`), se usa ESE como objetivo en vez de `manifest.json` —
    así una corrida que retoma tras un corte compara contra lo que se PRETENDÍA publicar, no
    contra el estado (parcial) que quedó en disco, y completa exactamente lo que falta.

    Gap 93: si el hash calculado ya coincide con el del manifiesto, la operación es `sin_cambios`
    (no reescribe lo que no cambió). Gap 109/126 (fix3): además del hash declarado en el
    manifiesto, se comprueba el hash EMBEBIDO EN EL FICHERO en disco (`_hash_publicado_en`) — no
    solo que exista. Sin esto, un objetivo tomado de `manifest.pending.json` (que puede listar el
    hash NUEVO de un `upsert` que aún no llegó a publicarse) haría pasar por `sin_cambios` un
    fichero que en realidad sigue con el contenido VIEJO; comparando contra el hash que el propio
    fichero dice tener en su frontmatter, esa entrada vuelve a ser `upsert` hasta que de verdad se
    publique. `force=True` (usado por `rebuild()`) ignora cualquier pendiente y usa `manifest.json`
    publicado, con TODO como `upsert`, para reconstruir la proyección entera desde cero. Gap 125:
    los `sin_cambios` no llevan `cuerpo` — `apply()` no lo necesita para un fichero que no se
    toca."""
    export_dir = _export_dir_resuelto(cfg)
    pending = None if force else _leer_pending(export_dir)
    manifest = pending if pending is not None else _leer_manifest(export_dir)
    ids_actuales = {e["id"] for e in entries}
    ops = []
    for e in entries:
        category = e.get("category")
        version = e.get("version")
        cuerpo = _cuerpo_segun_modo(e)
        hash_ = _hash_contenido(e["id"], version, category, cuerpo)
        entrada_previa = manifest["entries"].get(e["id"])
        ruta_relativa_previa = (entrada_previa or {}).get("ruta_relativa")
        publicado_existe = bool(ruta_relativa_previa) and _hash_publicado_en(
            os.path.join(export_dir, ruta_relativa_previa)) == (entrada_previa or {}).get("hash")
        sin_cambios = (not force) and bool(entrada_previa) and \
            entrada_previa.get("hash") == hash_ and publicado_existe
        op = {
            "accion": "sin_cambios" if sin_cambios else "upsert",
            "knowledge_id": e["id"],
            "project": _proyecto_de(e["id"]),
            "category": category,
            "version": version,
            "confidence": _confianza_de(e.get("evidencia")),
            "hash": hash_,
        }
        if sin_cambios:
            op["ruta_relativa"] = ruta_relativa_previa
        else:
            op["cuerpo"] = cuerpo  # solo los upsert cargan el cuerpo (gap 125)
        ops.append(op)
    for id_antiguo in sorted(manifest["entries"]):
        if id_antiguo not in ids_actuales:
            ops.append({"accion": "revoke", "knowledge_id": id_antiguo})
    return ops


def _purgar_staging_huerfano(export_dir):
    """gap 82/115/126 (fix3): al arrancar `apply()` (ya bajo el lock), purga cualquier
    `.staging-*` HERMANO de una corrida interrumpida (`SIGKILL` entre crear el staging y publicar)
    más viejo que `_STAGING_TTL_S`. Ya no hay `.prev` que reparar: la publicación por fichero
    (ver docstring del módulo) nunca intercambia el directorio entero, así que un corte a medias
    solo puede dejar (a) un staging HERMANO con `upsert` sin publicar — inofensivo, se reconstruye
    desde `entries` en la próxima corrida, esta función solo limpia el directorio sobrante — o
    (b) un `manifest.pending.json` DENTRO de `export_dir`, que `plan()`/`verify()` ya saben leer y
    que esta función NUNCA toca (es la prueba de qué falta publicar, no basura)."""
    padre = os.path.dirname(export_dir) or "."
    base = os.path.basename(export_dir)
    try:
        nombres = os.listdir(padre)
    except OSError:
        nombres = []
    ahora = time.time()
    for nombre in nombres:
        if not nombre.startswith(base + _STAGING_PREFIJO):
            continue
        ruta = os.path.join(padre, nombre)
        try:
            edad = ahora - os.path.getmtime(ruta)
        except OSError:
            edad = 0
        if edad > _STAGING_TTL_S:
            _borrar_arbol(ruta)


def _manifest_objetivo_de(ops):
    """El manifiesto que `apply()` PRETENDE dejar publicado al terminar `ops` (se escribe como
    `manifest.pending.json` ANTES de tocar ningún fichero — gap 126/136). Usa el `hash` que
    `plan()` ya calculó para cada op (upsert y sin_cambios lo llevan siempre); los `revoke` no
    aportan entrada."""
    entries = {}
    for op in ops:
        accion = op["accion"]
        if accion == "revoke":
            continue
        ruta_relativa = op.get("ruta_relativa") or _slug_fichero(op["knowledge_id"])
        entries[op["knowledge_id"]] = {
            "ruta_relativa": ruta_relativa, "hash": op.get("hash"),
            "version": op.get("version"), "category": op.get("category"),
        }
    return {"version": MANIFEST_VERSION, "entries": entries}


def apply(ops, cfg):
    """Publica FICHERO A FICHERO con un diario (gap 82/109/115/118/123/126/127/136, ver docstring
    del módulo): renderiza los `upsert` en un staging HERMANO de `export_dir` (los `sin_cambios`
    NUNCA se tocan), escribe `manifest.pending.json` con el objetivo ANTES de publicar nada, y
    publica cada fichero con UN `os.replace` (nunca el árbol entero). Un fallo antes de escribir
    el pending no toca `export_dir` para nada. Un fallo publicando a mitad deja lo ya publicado
    intacto y el `manifest.pending.json` en disco para que la SIGUIENTE corrida complete el resto
    (`plan()` lo usa como objetivo). Un lock hermano (`<export_dir>.lock`) serializa
    `apply()`/`revoke()` concurrentes."""
    export_dir = _export_dir_resuelto(cfg)
    with _LockDirectorio(_lock_path(export_dir)):
        os.makedirs(export_dir, exist_ok=True)
        _purgar_staging_huerfano(export_dir)
        pending_previo = _leer_pending(export_dir)
        manifest_previo_efectivo = pending_previo if pending_previo is not None \
            else _leer_manifest(export_dir)
        manifest_objetivo = _manifest_objetivo_de(ops)
        staging_dir = f"{export_dir}{_STAGING_PREFIJO}{os.getpid()}"
        if os.path.isdir(staging_dir):
            _borrar_arbol(staging_dir)  # pid reutilizado de una corrida anterior: empezar limpio
        os.makedirs(staging_dir, exist_ok=True)
        escritos = sin_cambios = revocados = 0
        rutas_upsert = []
        try:
            for op in ops:
                accion = op["accion"]
                if accion == "upsert":
                    contenido, _hash = _render_markdown(op)
                    ruta_relativa = _slug_fichero(op["knowledge_id"])
                    tmp = os.path.join(staging_dir, ruta_relativa)
                    os.makedirs(os.path.dirname(tmp) or staging_dir, exist_ok=True)
                    with open(tmp, "w", encoding="utf-8") as fh:
                        fh.write(contenido)
                    rutas_upsert.append(ruta_relativa)
                    escritos += 1
                elif accion == "sin_cambios":
                    sin_cambios += 1  # nunca se toca (diseño sustitutivo, gap 118/136)
                elif accion == "revoke":
                    revocados += 1
            pending_path = os.path.join(export_dir, MANIFEST_PENDING_NOMBRE)
            _escribir_manifest_atomico(pending_path, manifest_objetivo)
        except BaseException:
            _borrar_arbol(staging_dir)
            raise
        try:
            _publicar_por_fichero(
                staging_dir, export_dir, rutas_upsert,
                [op["knowledge_id"] for op in ops if op["accion"] == "revoke"],
                manifest_previo_efectivo)
        finally:
            _borrar_arbol(staging_dir)
        return {
            "escritos": escritos, "sin_cambios": sin_cambios, "revocados": revocados,
            "export_dir": export_dir,
        }


def _publicar_por_fichero(staging_dir, export_dir, rutas_upsert, ids_a_revocar,
                           manifest_previo_efectivo):
    """El paso (4)-(5) del diario (ver docstring del módulo): publica cada `upsert` con UN
    `os.replace` fichero-a-fichero, ejecuta los `revoke` (best-effort — un fichero ya borrado a
    mano no es un error), y renombra `manifest.pending.json` -> `manifest.json`. Si un `os.replace`
    de un `upsert` falla a mitad (p. ej. el indexador tiene el `.md` abierto en Windows), los
    ficheros ya publicados quedan intactos y `manifest.pending.json` se conserva sin renombrar:
    la SIGUIENTE corrida lo lee en `plan()` y reintenta solo lo que falta — no hace falta repetir
    dentro de esta misma llamada (gap 126/127: nunca se pierde ni se toca nada ajeno)."""
    for ruta_relativa in rutas_upsert:
        origen = os.path.join(staging_dir, ruta_relativa)
        destino = os.path.join(export_dir, ruta_relativa)
        try:
            os.replace(origen, destino)
        except OSError as e:
            raise ConfigInvalida(
                f"no se pudo publicar `{ruta_relativa}` (`{origen}` -> `{destino}`): "
                f"{type(e).__name__}: {e}; `manifest.pending.json` queda en `{export_dir}` para "
                "completar la publicación en la próxima corrida (nada más se ha perdido)") from e
    for knowledge_id in ids_a_revocar:
        entrada = manifest_previo_efectivo["entries"].get(knowledge_id)
        if not entrada:
            continue
        ruta = os.path.join(export_dir, entrada.get("ruta_relativa") or "")
        with contextlib.suppress(OSError):
            os.remove(ruta)
    pending_path = os.path.join(export_dir, MANIFEST_PENDING_NOMBRE)
    manifest_path = os.path.join(export_dir, MANIFEST_NOMBRE)
    try:
        os.replace(pending_path, manifest_path)
    except OSError as e:
        raise ConfigInvalida(
            f"no se pudo finalizar la publicación (`{pending_path}` -> `{manifest_path}`): "
            f"{type(e).__name__}: {e}; `manifest.pending.json` queda para reintentar") from e


def _borrar_arbol(ruta):
    for raiz, dirs, ficheros in os.walk(ruta, topdown=False):
        for nombre in ficheros:
            try:
                os.remove(os.path.join(raiz, nombre))
            except OSError:
                pass
        for nombre in dirs:
            try:
                os.rmdir(os.path.join(raiz, nombre))
            except OSError:
                pass
    try:
        os.rmdir(ruta)
    except OSError:
        pass


def rebuild(entries, cfg):
    """Reconstruye la proyección ENTERA desde `entries` (gap 109): `plan(..., force=True)` marca
    TODO como `upsert` contra el `manifest.json` publicado (ignora cualquier pendiente), y
    `apply()` publica cada `upsert` fichero a fichero y ejecuta los `revoke` de lo que ya no esté
    en `entries` — mismo resultado que borrar la publicación y repetir `plan()`+`apply()`, sin
    pasar por ese borrado manual (T-07, desviación documentada de la firma de `design.md`:
    `rebuild` recibe `entries`, no solo `cfg`)."""
    ops = plan(entries, cfg, force=True)
    return apply(ops, cfg)


def revoke(knowledge_id, cfg):
    """No-op declarado si `knowledge_id` no está publicado (nunca lanza). Usa el mismo diario que
    `apply()` (gap 126/127, fix3: pending -> borra el fichero -> `manifest.json`), y la misma
    lectura pending-o-manifest para saber cuál es el estado objetivo actual; serializada con el
    mismo lock hermano que `apply()` para no pisarse con una publicación en curso."""
    export_dir = _export_dir_resuelto(cfg)
    with _LockDirectorio(_lock_path(export_dir)):
        os.makedirs(export_dir, exist_ok=True)
        pending_previo = _leer_pending(export_dir)
        manifest_actual = pending_previo if pending_previo is not None else _leer_manifest(export_dir)
        entrada = manifest_actual["entries"].get(knowledge_id)
        if entrada is None:
            return {"revocado": False, "knowledge_id": knowledge_id}
        objetivo = {
            "version": MANIFEST_VERSION,
            "entries": {k: v for k, v in manifest_actual["entries"].items() if k != knowledge_id},
        }
        pending_path = os.path.join(export_dir, MANIFEST_PENDING_NOMBRE)
        manifest_path = os.path.join(export_dir, MANIFEST_NOMBRE)
        _escribir_manifest_atomico(pending_path, objetivo)
        ruta = os.path.join(export_dir, entrada.get("ruta_relativa") or "")
        with contextlib.suppress(OSError):
            os.remove(ruta)
        try:
            os.replace(pending_path, manifest_path)
        except OSError as e:
            raise ConfigInvalida(
                f"no se pudo finalizar la revocación (`{pending_path}` -> `{manifest_path}`): "
                f"{type(e).__name__}: {e}; `manifest.pending.json` queda para reintentar") from e
        return {"revocado": True, "knowledge_id": knowledge_id}


def _base_url_snapshot(health_url):
    """Quita el sufijo `/health` de la RUTA (gap 103), no del string completo: preserva query y
    cualquier prefijo delante, y tolera una barra final (`/health/`)."""
    partes = urllib.parse.urlsplit(health_url)
    ruta = partes.path
    if ruta.endswith("/health/"):
        ruta = ruta[: -len("/health/")]
    elif ruta.endswith("/health"):
        ruta = ruta[: -len("/health")]
    return urllib.parse.urlunsplit((partes.scheme, partes.netloc, ruta, "", ""))


def verify(cfg):
    """Compara `manifest.json` (local) contra `GET <base>/graph/snapshot` (Kwipu). Un export
    publicado cuyo fichero no aparece entre los nodos `chunk` del snapshot es desfase: Kwipu aún
    no lo indexó. Nombra el remedio SIN ejecutarlo (CA-16) — nunca lanza, nunca hace red en frío
    sin capturar el error.

    Gap 87: manifiesto vacío/ausente ya NO es `ok: True` trivial — nunca se sincronizó nada, así
    que se declara `ok: False` con `razon: "nunca_sincronizado"` (doctor.py lo muestra como aviso,
    no como desfase real). Gap 101: si el snapshot trae `hash` por nodo, se compara también el
    contenido, no solo el nombre; si no lo trae, se declara `comparacion: "nombre"`. Gap 112: la
    petición al snapshot revalida el host de cualquier redirección antes de seguirla. Gap 126/136
    (fix3): un `manifest.pending.json` presente significa una publicación interrumpida a medio
    completar — se declara ANTES que cualquier otra comprobación (`razon: "publicacion_incompleta"`
    en vez de comparar contra un `manifest.json` que ya sabemos que no refleja el objetivo)."""
    export_dir = _export_dir_resuelto(cfg)
    if _leer_pending(export_dir) is not None:
        return {"ok": False, "desfase": [], "razon": "publicacion_incompleta",
                "detalle": "hay una publicación interrumpida (`manifest.pending.json` en "
                           f"`{export_dir}`); repite la sincronización (`plan()`+`apply()`, o la "
                           "publicación normal) para completarla"}
    manifest = _leer_manifest(export_dir)
    if not manifest["entries"]:
        return {"ok": False, "desfase": [], "razon": "nunca_sincronizado",
                "detalle": "no hay `manifest.json` (o está vacío): nunca se publicó nada todavía"}
    health_url = ((cfg or {}).get("health") or {}).get("url")
    timeout_s = _timeout_s((cfg or {}).get("health"))
    if not health_url:
        return {"ok": False, "desfase": [{"knowledge_id": None,
                "motivo": "sin `health.url` configurada, no se puede localizar `/graph/snapshot`",
                "remedio": REMEDIO}]}
    if not _host_permitido(health_url):
        return {"ok": False, "desfase": [{"knowledge_id": None,
                "motivo": f"host no local/privado, rechazado: {health_url}",
                "remedio": REMEDIO}]}
    snapshot_url = _base_url_snapshot(health_url) + "/graph/snapshot"
    try:
        with _urlopen_local(snapshot_url, timeout_s) as resp:
            cuerpo = resp.read()
        snapshot = json.loads(cuerpo.decode("utf-8"))
    except _RedireccionNoPermitida as e:
        # gap 180: `e.url` viene de un cabecera `Location` no confiable — se sanea antes del
        # prefijo propio, igual que en `health()`.
        return {"ok": False, "desfase": [{"knowledge_id": None,
                "motivo": f"redirección a host no local/privado, rechazada: {_sanear_detalle(e.url)}",
                "remedio": REMEDIO}]}
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError,
            ValueError, UnicodeDecodeError, http.client.HTTPException) as e:
        # gap 155: `http.client.HTTPException` (respuesta no HTTP de un host local permitido)
        # no es subclase de `OSError`; se captura explícitamente, igual que en `health()`.
        # gap 176 (CWE-117): mismo saneado que en `health()` — el mensaje de excepción puede
        # traer bytes crudos del servidor (CRLF, ANSI) que acaban impresos por `/doctor`.
        # gap 182: el tope de 200 se aplica SOLO a `{e}` (lo no confiable) para no comerse el
        # prefijo propio (`no se pudo conectar a {snapshot_url}: {type(e).__name__}: `).
        return {"ok": False, "desfase": [{"knowledge_id": None,
                "motivo": f"no se pudo conectar a {snapshot_url}: {type(e).__name__}: "
                          f"{_sanear_detalle(e)}",
                "remedio": REMEDIO}]}
    nodos_por_nombre = {
        n.get("file_name"): n for n in (snapshot.get("nodes") or [])
        if isinstance(n, dict) and n.get("type") == "chunk" and n.get("file_name")
    }
    comparacion_hash_disponible = any("hash" in n for n in nodos_por_nombre.values())
    desfase = []
    for knowledge_id, entrada in sorted(manifest["entries"].items()):
        nombre = os.path.basename(entrada.get("ruta_relativa") or "")
        nodo = nodos_por_nombre.get(nombre)
        if nodo is None:
            desfase.append({
                "knowledge_id": knowledge_id,
                "motivo": f"`{nombre}` publicado pero no aparece en `/graph/snapshot`",
                "remedio": REMEDIO,
            })
        elif comparacion_hash_disponible and nodo.get("hash") and nodo["hash"] != entrada.get("hash"):
            desfase.append({
                "knowledge_id": knowledge_id,
                "motivo": f"`{nombre}` indexado pero con contenido distinto (hash no coincide)",
                "remedio": REMEDIO,
            })
    return {
        "ok": not desfase, "desfase": desfase,
        "comparacion": "hash" if comparacion_hash_disponible else "nombre",
    }
