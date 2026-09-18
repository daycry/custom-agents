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
  - #82/#109/#115/#118/#123 (intento 2, Fase 3, fix2, 2026-09-18): **publicación por intercambio
    de directorio.** `apply()` ya NO usa un staging DENTRO de `export_dir`: construye el árbol
    completo en un directorio HERMANO (`<export_dir>.staging-<pid>`, fuera de lo que Kwipu
    indexa), mueve (`os.replace`, sin reescribir) los ficheros `sin_cambios`, escribe los
    `upsert` y el `manifest.json` nuevo ahí, y publica con DOS `os.replace` de directorio
    (`export_dir` -> `export_dir.prev`, staging -> `export_dir`), borrando `.prev` al final. La
    ventana no atómica es el instante entre esos dos renames (mucho más corta que escribir 500+
    ficheros uno a uno). `plan()` decide `sin_cambios` SOLO si el hash coincide Y el fichero
    publicado existe todavía (gap 109: antes un fichero borrado a mano nunca se regeneraba).
    `rebuild()` fuerza `upsert` de TODA `entries` (`plan(..., force=True)`): como construye el
    staging desde cero a partir de `entries`, cualquier huérfano que no esté en `entries` muere
    solo (nunca se copia al staging), sin necesidad de barrer ficheros sueltos. Al arrancar
    `apply()`, se repara/purga cualquier `.prev`/`.staging-*` de más de `_STAGING_TTL_S` que haya
    quedado de una corrida interrumpida (`SIGKILL` a medio camino). El lock (`_LockDirectorio`)
    también es un fichero HERMANO (`<export_dir>.lock`), no dentro del árbol que se intercambia.
    Si el rename de directorio no es viable en este sistema de ficheros (p. ej. Windows con un
    handle abierto por un indexador externo dentro de `export_dir`), `apply()` lo propaga como
    `ConfigInvalida` con el motivo real en vez de dejar el árbol a medias.
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
import hashlib
import ipaddress
import json
import os
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
_LOCK_SUFIJO = ".lock"
_LOCK_TTL_S = 60  # un lock más viejo que esto se considera huérfano (proceso muerto)
_STAGING_PREFIJO = ".staging-"
_PREV_SUFIJO = ".prev"
_STAGING_TTL_S = 60  # gap 82/115: un `.staging-*`/`.prev` hermano más viejo que esto es de una
                     # corrida interrumpida (SIGKILL) — se repara/purga al arrancar `apply()`
_DNS_TIMEOUT_S = 1.0  # gap 117: tope de la resolución DNS de `_host_permitido`, independiente
                      # del `timeout_ms` HTTP configurado

REMEDIO = "reindexar: `build_view` + reiniciar `kwipu`, `kwipu-bridge`, `kwipu-mcp`"

_MAPA_CONFIANZA = {
    "observation": "low",
    "single_case": "low",
    "validated_case": "medium",
    "multiple_validated_cases": "medium",
    "human_confirmed_rule": "high",
}

_SUFIJOS_LOCALES = (".test", ".local", ".internal")
_HOSTS_LOCALES_LITERALES = {"localhost", "host.docker.internal"}

_dns_cache = {}  # gap 117: caché de resolución por proceso — {host: ip_str}


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
    Cachea por proceso el resultado positivo o negativo para no repetir la resolución en cada
    llamada de `health()`/`verify()` sobre el mismo host."""
    if host in _dns_cache:
        return _dns_cache[host]
    resultado = {}

    def _resolver():
        try:
            resultado["ip"] = socket.gethostbyname(host)
        except OSError:
            resultado["ip"] = None

    hilo = threading.Thread(target=_resolver, daemon=True)
    hilo.start()
    hilo.join(timeout_s)
    if hilo.is_alive():
        return None  # colgado: no se cachea, se reintentará en la próxima llamada
    ip = resultado.get("ip")
    _dns_cache[host] = ip
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


class _RedirectHandlerLocalOnly(urllib.request.HTTPRedirectHandler):
    """gap 112: revalida CADA salto de una redirección HTTP contra `_host_permitido` antes de
    seguirlo — el `HTTPRedirectHandler` por defecto de `urllib` sigue redirecciones sin mirar el
    host destino, así que un bridge local comprometido (o mal configurado) podía usar un `302` para
    hacer que `health()`/`verify()` hablaran con un host público."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: N802 — API de urllib
        if not _host_permitido(newurl):
            raise _RedireccionNoPermitida(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _urlopen_local(url, timeout_s):
    """`urlopen` con un `opener` que revalida el host en cada redirección (gap 112). Usa un
    `opener` nuevo por llamada: es barato (sin estado que compartir) y evita cualquier fuga de
    configuración entre llamadas a `health()`/`verify()` en el mismo proceso."""
    opener = urllib.request.build_opener(_RedirectHandlerLocalOnly)
    return opener.open(url, timeout=timeout_s)


def _export_dir_resuelto(cfg):
    """Resuelve `export_dir` contra `cfg["_root"]` (gap 88: nunca CWD) y valida que no sea el
    propio root ni un subdirectorio de `docs/knowledge/approved/` (gap 102: no se pisa la fuente
    canónica). `knowledge-sync.py`/`doctor.py` deben inyectar `_root` en el `cfg` del adaptador.

    Gap 121: la contención usa `os.path.realpath` (no solo `abspath`, que no sigue symlinks ni
    junctions) y compara con `os.path.normcase` (en Windows, insensible a mayúsculas): sin esto,
    un junction/symlink que apuntara a `approved/`, o una ruta con mayúsculas distintas, evadía la
    comprobación."""
    export_dir = (cfg or {}).get("export_dir")
    if not export_dir:
        raise ConfigInvalida("falta `export_dir` en la config del backend")
    root = (cfg or {}).get("_root") or "."
    root_abs = os.path.realpath(root)
    resuelto = export_dir if os.path.isabs(export_dir) else os.path.join(root_abs, export_dir)
    resuelto_real = os.path.realpath(resuelto)
    if os.path.normcase(resuelto_real) == os.path.normcase(root_abs):
        raise ConfigInvalida(
            f"`export_dir` (`{export_dir}`) no puede ser la raíz del proyecto (`{root_abs}`)")
    approved_real = os.path.realpath(os.path.join(root_abs, "docs", "knowledge", "approved"))
    approved_nc = os.path.normcase(approved_real)
    resuelto_nc = os.path.normcase(resuelto_real)
    if resuelto_nc == approved_nc or resuelto_nc.startswith(approved_nc + os.path.normcase(os.sep)):
        raise ConfigInvalida(
            f"`export_dir` (`{export_dir}`) no puede quedar dentro de "
            "`docs/knowledge/approved/` (pisaría la fuente canónica)")
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


def _leer_manifest(export_dir):
    ruta = os.path.join(export_dir, MANIFEST_NOMBRE)
    if not os.path.isfile(ruta):
        return {"version": MANIFEST_VERSION, "entries": {}}
    try:
        with open(ruta, "r", encoding="utf-8-sig") as f:
            datos = json.load(f)
    except (OSError, ValueError):
        return {"version": MANIFEST_VERSION, "entries": {}}
    if not isinstance(datos, dict) or not isinstance(datos.get("entries"), dict):
        return {"version": MANIFEST_VERSION, "entries": {}}
    return datos


def _escribir_manifest_en(destino_dir, manifest):
    ruta = os.path.join(destino_dir, MANIFEST_NOMBRE)
    with open(ruta, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(manifest, ensure_ascii=False, indent=2))


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
        return {"estado": "error", "detalle": f"redirección a host no local/privado, rechazada: {e.url}"}
    except urllib.error.HTTPError as e:
        cuerpo_err = _cuerpo_json_o_none(e)
        detalle = f"HTTP {e.code} de {url}" + (f": {cuerpo_err}" if cuerpo_err else "")
        return {"estado": "degradado" if 500 <= e.code < 600 else "error", "detalle": detalle}
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return {"estado": "off", "detalle": f"sin conexión a {url}: {type(e).__name__}: {e}"}
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
    """Idempotente: mismas `entries` -> mismo `ops`. Compara contra `manifest.json` en
    `export_dir` para calcular los `revoke` de entradas que ya no están en `entries` (salieron de
    `approved/` o dejaron de enrutar a este backend).

    Gap 93: si el hash calculado ya coincide con el del manifiesto, la operación es `sin_cambios`
    (no reescribe lo que no cambió). Gap 109: además del hash, se exige que el fichero publicado
    siga existiendo — si se borró a mano (indexador, antivirus, limpieza), la operación vuelve a
    ser `upsert` aunque el hash no haya cambiado, en vez de un `sin_cambios` que nunca regenera
    nada. `force=True` (usado por `rebuild()`) ignora el manifiesto por completo: TODO es `upsert`,
    para reconstruir la proyección entera desde cero. Gap 125: los `sin_cambios` no llevan
    `cuerpo` — `apply()` no lo necesita para mover un fichero tal cual."""
    export_dir = _export_dir_resuelto(cfg)
    manifest = _leer_manifest(export_dir)
    ids_actuales = {e["id"] for e in entries}
    ops = []
    for e in entries:
        category = e.get("category")
        version = e.get("version")
        cuerpo = _cuerpo_segun_modo(e)
        hash_ = _hash_contenido(e["id"], version, category, cuerpo)
        entrada_previa = manifest["entries"].get(e["id"])
        ruta_relativa_previa = (entrada_previa or {}).get("ruta_relativa")
        publicado_existe = bool(ruta_relativa_previa) and os.path.isfile(
            os.path.join(export_dir, ruta_relativa_previa))
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


def _sibling(export_dir, sufijo):
    return export_dir.rstrip(os.sep) + sufijo


def _reparar_publicacion(export_dir):
    """gap 82/115: al arrancar `apply()` (ya bajo el lock), repone/purga cualquier resto de una
    corrida interrumpida (`SIGKILL` entre los dos renames, o antes de llegar a ellos):
      - `<export_dir>.prev` presente y `export_dir` AUSENTE: el primer rename (export_dir ->
        .prev) se completó pero el segundo (staging -> export_dir) nunca llegó a ejecutarse (o el
        propio staging se perdió) — se repone `.prev` a `export_dir` para no dejar el proyecto sin
        publicación.
      - `<export_dir>.prev` presente y `export_dir` TAMBIÉN presente: el intercambio se completó
        de verdad, solo faltó borrar `.prev` — se borra sin más.
      - `<export_dir>.staging-*` más viejo que `_STAGING_TTL_S`: staging de una corrida que murió
        antes de llegar a los renames — se purga (el `export_dir` de entonces, si existía, sigue
        intacto porque el intercambio nunca empezó)."""
    prev_dir = _sibling(export_dir, _PREV_SUFIJO)
    if os.path.isdir(prev_dir):
        if not os.path.isdir(export_dir):
            os.replace(prev_dir, export_dir)
        else:
            _borrar_arbol(prev_dir)
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


def apply(ops, cfg):
    """Publica por INTERCAMBIO DE DIRECTORIO (gap 82/109/115/118/123): construye el árbol completo
    en un staging HERMANO de `export_dir` (fuera del árbol que Kwipu indexa), y solo al final lo
    intercambia por `export_dir` con dos `os.replace` de directorio. Un fallo mientras se construye
    el staging no toca `export_dir` para nada — se borra el staging y se relanza la excepción. Un
    lock hermano (`<export_dir>.lock`) serializa `apply()`/`revoke()` concurrentes."""
    export_dir = _export_dir_resuelto(cfg)
    with _LockDirectorio(_lock_path(export_dir)):
        _reparar_publicacion(export_dir)
        manifest_previo = _leer_manifest(export_dir)
        staging_dir = f"{export_dir}{_STAGING_PREFIJO}{os.getpid()}"
        if os.path.isdir(staging_dir):
            _borrar_arbol(staging_dir)  # pid reutilizado de una corrida anterior: empezar limpio
        os.makedirs(staging_dir, exist_ok=True)
        manifest = {"version": MANIFEST_VERSION, "entries": {}}
        escritos = sin_cambios = revocados = 0
        try:
            for op in ops:
                if op["accion"] == "upsert":
                    contenido, hash_ = _render_markdown(op)
                    ruta_relativa = _slug_fichero(op["knowledge_id"])
                    destino = os.path.join(staging_dir, ruta_relativa)
                    os.makedirs(os.path.dirname(destino) or staging_dir, exist_ok=True)
                    with open(destino, "w", encoding="utf-8") as fh:
                        fh.write(contenido)
                    manifest["entries"][op["knowledge_id"]] = {
                        "ruta_relativa": ruta_relativa, "hash": hash_,
                        "version": op.get("version"), "category": op.get("category"),
                    }
                    escritos += 1
                elif op["accion"] == "sin_cambios":
                    ruta_relativa = op.get("ruta_relativa") or _slug_fichero(op["knowledge_id"])
                    origen = os.path.join(export_dir, ruta_relativa)
                    destino = os.path.join(staging_dir, ruta_relativa)
                    os.makedirs(os.path.dirname(destino) or staging_dir, exist_ok=True)
                    if os.path.isfile(origen):
                        os.replace(origen, destino)  # mueve, mtime intacto — nunca reescribe
                    else:
                        # Carrera rara (el fichero desapareció entre `plan()` y `apply()`, algo
                        # que `plan()` ya no debería dejar pasar en el camino normal): se
                        # reconstruye a partir del manifiesto previo con lo que se conozca, en
                        # vez de perder la entrada en silencio.
                        entrada_previa = manifest_previo["entries"].get(op["knowledge_id"]) or {}
                        raise ConfigInvalida(
                            f"`{origen}` se esperaba `sin_cambios` pero ya no existe "
                            f"(hash previo `{entrada_previa.get('hash', '?')}`); repite `plan()` "
                            "y `apply()` — posible carrera con un borrado externo")
                    manifest["entries"][op["knowledge_id"]] = {
                        "ruta_relativa": ruta_relativa, "hash": op.get("hash"),
                        "version": op.get("version"), "category": op.get("category"),
                    }
                    sin_cambios += 1
                elif op["accion"] == "revoke":
                    revocados += 1  # gap: revoke = NO mover el fichero al staging; muere solo
            manifest["version"] = MANIFEST_VERSION
            _escribir_manifest_en(staging_dir, manifest)
        except BaseException:
            _borrar_arbol(staging_dir)
            raise
        _publicar_intercambio(export_dir, staging_dir)
        return {
            "escritos": escritos, "sin_cambios": sin_cambios, "revocados": revocados,
            "export_dir": export_dir,
        }


def _publicar_intercambio(export_dir, staging_dir):
    """Los dos `os.replace` de directorio que materializan la publicación (gap 82): si
    `export_dir` ya existe, se aparta a `.prev` primero (un `rename` no puede pisar un directorio
    NO VACÍO en POSIX/Windows) y se borra al final; si el segundo rename fallara, se repone `.prev`
    para no dejar el proyecto sin publicación. Si el filesystem no admite el rename de un
    directorio en este punto (p. ej. Windows con un handle abierto dentro por un indexador
    externo), se propaga como `ConfigInvalida` con el motivo real — no hay forma segura de
    reintentar automáticamente sin saber qué lo tiene abierto (documentado en el módulo)."""
    prev_dir = _sibling(export_dir, _PREV_SUFIJO)
    habia_previo = os.path.isdir(export_dir)
    if habia_previo:
        try:
            os.replace(export_dir, prev_dir)
        except OSError as e:
            _borrar_arbol(staging_dir)
            raise ConfigInvalida(
                f"no se pudo apartar la publicación anterior (`{export_dir}` -> `{prev_dir}`): "
                f"{type(e).__name__}: {e} (publicación anterior intacta; staging descartado)") from e
    try:
        os.replace(staging_dir, export_dir)
    except OSError as e:
        if habia_previo:
            try:
                os.replace(prev_dir, export_dir)
            except OSError:
                pass  # no se pudo ni siquiera reponer: la próxima `apply()` lo repara (`_reparar_publicacion`)
        _borrar_arbol(staging_dir)
        raise ConfigInvalida(
            f"no se pudo publicar el staging (`{staging_dir}` -> `{export_dir}`): "
            f"{type(e).__name__}: {e} (publicación anterior repuesta si fue posible)") from e
    if habia_previo:
        _borrar_arbol(prev_dir)


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
    TODO como `upsert` (ignora el manifiesto), y como `apply()` construye el staging desde cero
    solo con lo que hay en `ops`, cualquier fichero huérfano del `export_dir` anterior (borrado de
    `entries`, o nunca reflejado en el manifiesto) simplemente no se copia al staging nuevo — mismo
    resultado que borrar la publicación y repetir `plan()`+`apply()`, sin pasar por ese borrado
    manual (T-07, desviación documentada de la firma de `design.md`: `rebuild` recibe `entries`,
    no solo `cfg`)."""
    ops = plan(entries, cfg, force=True)
    return apply(ops, cfg)


def revoke(knowledge_id, cfg):
    """No-op declarado si `knowledge_id` no está publicado (nunca lanza). Ruta directa (no pasa
    por el intercambio de directorio completo: es UN fichero), pero sigue serializada con el mismo
    lock hermano que `apply()` para no pisarse con una publicación en curso."""
    export_dir = _export_dir_resuelto(cfg)
    with _LockDirectorio(_lock_path(export_dir)):
        manifest = _leer_manifest(export_dir)
        entrada = manifest["entries"].pop(knowledge_id, None)
        if entrada is None:
            return {"revocado": False, "knowledge_id": knowledge_id}
        ruta = os.path.join(export_dir, entrada["ruta_relativa"])
        try:
            os.remove(ruta)
        except OSError:
            pass
        _escribir_manifest_en(export_dir, manifest)
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
    petición al snapshot revalida el host de cualquier redirección antes de seguirla."""
    export_dir = _export_dir_resuelto(cfg)
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
        return {"ok": False, "desfase": [{"knowledge_id": None,
                "motivo": f"redirección a host no local/privado, rechazada: {e.url}",
                "remedio": REMEDIO}]}
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError,
            ValueError, UnicodeDecodeError) as e:
        return {"ok": False, "desfase": [{"knowledge_id": None,
                "motivo": f"no se pudo conectar a {snapshot_url}: {type(e).__name__}: {e}",
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
