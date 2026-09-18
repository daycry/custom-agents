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

Gaps de la revisión de dos lentes — intento 1, fix1 (2026-09-18), corregidos en este fichero:
  - #82 (Critical): `apply()` publica sobre un staging propio (sibling de `export_dir`) con un
    lock de directorio; solo hace `os.replace` final por fichero + manifiesto cuando TODAS las
    operaciones ya escribieron en staging sin excepción — un fallo a medias deja la publicación
    anterior intacta.
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
  - #97: `health()` y `verify()` rechazan hosts que no sean locales/privados (mismo criterio que
    `agent-kits/nemesis/tools/lib-guardrail.sh`) ANTES de abrir conexión — invariante de seguridad
    del plugin, nunca solo documental.
  - #101: `verify()` compara también el `hash` del snapshot cuando el nodo lo trae; si el
    snapshot no expone hash, lo declara (`comparacion: "nombre"`) en vez de fingir que comparó.
  - #103: `_base_url_snapshot` usa `urllib.parse` para quitar el sufijo `/health` de la RUTA
    (con o sin barra final), preservando query/prefijo.
"""
import hashlib
import ipaddress
import json
import os
import socket
import sys
import tempfile
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
_LOCK_NOMBRE = ".knowledge-services.lock"
_LOCK_TTL_S = 60  # un lock más viejo que esto se considera huérfano (proceso muerto)

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


class ConfigInvalida(Exception):
    """Error de configuración del adaptador (export_dir/host no permitido/etc.) — el llamador
    (`knowledge-sync.py`) lo convierte en `exit 1` con mensaje, nunca en un traceback."""


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


def _host_permitido(url):
    """Invariante de seguridad del plugin (gap 97, CWE-918): solo hosts locales/privados, mismo
    criterio que `agent-kits/nemesis/tools/lib-guardrail.sh`. Se resuelve el hostname y se
    comprueba la IP resultante; si no resuelve, se rechaza (fail-closed)."""
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
        try:
            ip = ipaddress.ip_address(socket.gethostbyname(host))
        except (OSError, ValueError):
            return False
    return bool(ip.is_loopback or ip.is_private)


def _export_dir_resuelto(cfg):
    """Resuelve `export_dir` contra `cfg["_root"]` (gap 88: nunca CWD) y valida que no sea el
    propio root ni un subdirectorio de `docs/knowledge/approved/` (gap 102: no se pisa la fuente
    canónica). `knowledge-sync.py`/`doctor.py` deben inyectar `_root` en el `cfg` del adaptador."""
    export_dir = (cfg or {}).get("export_dir")
    if not export_dir:
        raise ConfigInvalida("falta `export_dir` en la config del backend")
    root = (cfg or {}).get("_root") or "."
    root_abs = os.path.abspath(root)
    resuelto = export_dir if os.path.isabs(export_dir) else os.path.join(root_abs, export_dir)
    resuelto_abs = os.path.abspath(resuelto)
    if resuelto_abs == root_abs:
        raise ConfigInvalida(
            f"`export_dir` (`{export_dir}`) no puede ser la raíz del proyecto (`{root_abs}`)")
    approved_abs = os.path.abspath(os.path.join(root_abs, "docs", "knowledge", "approved"))
    if resuelto_abs == approved_abs or resuelto_abs.startswith(approved_abs + os.sep):
        raise ConfigInvalida(
            f"`export_dir` (`{export_dir}`) no puede quedar dentro de "
            "`docs/knowledge/approved/` (pisaría la fuente canónica)")
    return resuelto_abs


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


def _escribir_atomico(destino, contenido):
    carpeta = os.path.dirname(destino) or "."
    os.makedirs(carpeta, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=carpeta, prefix=".tmp-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(contenido)
        os.replace(tmp, destino)
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise


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


def _escribir_manifest(export_dir, manifest):
    ruta = os.path.join(export_dir, MANIFEST_NOMBRE)
    _escribir_atomico(ruta, json.dumps(manifest, ensure_ascii=False, indent=2))


class _LockDirectorio:
    """Lock de exclusión mutua entre `apply()` concurrentes sobre el mismo `export_dir` (gap 82):
    un fichero creado con `O_CREAT|O_EXCL` (atómico a nivel de SO); si el lock existe pero es más
    viejo que `_LOCK_TTL_S`, se considera huérfano (proceso muerto sin limpiar) y se reclama."""

    def __init__(self, export_dir):
        self._ruta = os.path.join(export_dir, _LOCK_NOMBRE)
        self._propio = False

    def __enter__(self):
        os.makedirs(os.path.dirname(self._ruta), exist_ok=True)
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
        with urllib.request.urlopen(url, timeout=timeout_s) as resp:
            cuerpo = resp.read()
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


def plan(entries, cfg):
    """Idempotente: mismas `entries` -> mismo `ops`. Compara contra `manifest.json` en
    `export_dir` para calcular los `revoke` de entradas que ya no están en `entries` (salieron de
    `approved/` o dejaron de enrutar a este backend). Gap 93: si el hash calculado ya coincide con
    el del manifiesto, la operación es `sin_cambios` (no reescribe lo que no cambió)."""
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
        accion = "sin_cambios" if entrada_previa and entrada_previa.get("hash") == hash_ else "upsert"
        ops.append({
            "accion": accion,
            "knowledge_id": e["id"],
            "project": _proyecto_de(e["id"]),
            "category": category,
            "version": version,
            "confidence": _confianza_de(e.get("evidencia")),
            "cuerpo": cuerpo,
            "hash": hash_,
        })
    for id_antiguo in sorted(manifest["entries"]):
        if id_antiguo not in ids_actuales:
            ops.append({"accion": "revoke", "knowledge_id": id_antiguo})
    return ops


def apply(ops, cfg):
    """Publica de forma ATÓMICA (gap 82): cada `upsert`/`revoke` se materializa primero en un
    staging propio (sibling de `export_dir`, mismo filesystem para que `os.replace` sea atómico);
    solo si TODAS las operaciones preparan sin excepción se publican con `os.replace` — incluido
    el `manifest.json` nuevo. Un fallo a medias no toca nada de lo ya publicado. Un lock de
    directorio serializa `apply()` concurrentes sobre el mismo `export_dir`."""
    export_dir = _export_dir_resuelto(cfg)
    os.makedirs(export_dir, exist_ok=True)
    with _LockDirectorio(export_dir):
        manifest = _leer_manifest(export_dir)
        preparados = []  # [(ruta_destino, ruta_staging_o_None)] — None = borrar destino
        escritos = 0
        sin_cambios = 0
        revocados = 0
        staging_dir = tempfile.mkdtemp(dir=export_dir, prefix=".staging-")
        try:
            for op in ops:
                if op["accion"] == "upsert":
                    contenido, hash_ = _render_markdown(op)
                    ruta_relativa = _slug_fichero(op["knowledge_id"])
                    ruta_staging = os.path.join(staging_dir, ruta_relativa)
                    os.makedirs(os.path.dirname(ruta_staging) or staging_dir, exist_ok=True)
                    with open(ruta_staging, "w", encoding="utf-8") as fh:
                        fh.write(contenido)
                    preparados.append(("upsert", op["knowledge_id"], ruta_relativa, ruta_staging, hash_, op))
                    escritos += 1
                elif op["accion"] == "sin_cambios":
                    sin_cambios += 1
                elif op["accion"] == "revoke":
                    preparados.append(("revoke", op["knowledge_id"], None, None, None, op))
                    revocados += 1
            # Todo preparado sin excepción: publicar.
            for tipo, knowledge_id, ruta_relativa, ruta_staging, hash_, op in preparados:
                if tipo == "upsert":
                    destino = os.path.join(export_dir, ruta_relativa)
                    os.makedirs(os.path.dirname(destino) or export_dir, exist_ok=True)
                    os.replace(ruta_staging, destino)
                    manifest["entries"][knowledge_id] = {
                        "ruta_relativa": ruta_relativa, "hash": hash_,
                        "version": op.get("version"), "category": op.get("category"),
                    }
                else:  # revoke
                    _quitar_fichero(export_dir, manifest, knowledge_id)
            manifest["version"] = MANIFEST_VERSION
            _escribir_manifest(export_dir, manifest)
        finally:
            _borrar_arbol(staging_dir)
        return {
            "escritos": escritos, "sin_cambios": sin_cambios, "revocados": revocados,
            "export_dir": export_dir,
        }


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


def _quitar_fichero(export_dir, manifest, knowledge_id):
    entrada = manifest["entries"].pop(knowledge_id, None)
    if entrada is None:
        return False
    ruta = os.path.join(export_dir, entrada["ruta_relativa"])
    try:
        os.remove(ruta)
    except OSError:
        pass
    return True


def rebuild(entries, cfg):
    """Reconstruye la proyección ENTERA desde `entries` — mismo resultado que borrar la
    publicación y repetir `plan`+`apply`, reutilizándolos directamente (T-07, desviación
    documentada de la firma de `design.md`: `rebuild` recibe `entries`, no solo `cfg`)."""
    ops = plan(entries, cfg)
    return apply(ops, cfg)


def revoke(knowledge_id, cfg):
    """No-op declarado si `knowledge_id` no está publicado (nunca lanza)."""
    export_dir = _export_dir_resuelto(cfg)
    manifest = _leer_manifest(export_dir)
    quitado = _quitar_fichero(export_dir, manifest, knowledge_id)
    if quitado:
        _escribir_manifest(export_dir, manifest)
    return {"revocado": quitado, "knowledge_id": knowledge_id}


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
    contenido, no solo el nombre; si no lo trae, se declara `comparacion: "nombre"`."""
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
        with urllib.request.urlopen(snapshot_url, timeout=timeout_s) as resp:
            cuerpo = resp.read()
        snapshot = json.loads(cuerpo.decode("utf-8"))
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
