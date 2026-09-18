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
"""
import hashlib
import json
import os
import sys
import tempfile
import urllib.error
import urllib.request

# Consola no UTF-8 (Windows cp1252) o tuberías: reconfigurar ANTES de leer/imprimir (GOT-005).
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure, ya leído o None (capsys, pythonw)

MANIFEST_VERSION = 1
MANIFEST_NOMBRE = "manifest.json"

REMEDIO = "reindexar: `build_view` + reiniciar `kwipu`, `kwipu-bridge`, `kwipu-mcp`"

_MAPA_CONFIANZA = {
    "observation": "low",
    "single_case": "low",
    "validated_case": "medium",
    "multiple_validated_cases": "medium",
    "human_confirmed_rule": "high",
}


def _proyecto_de(knowledge_id):
    return knowledge_id.split(".", 1)[0] if "." in knowledge_id else knowledge_id


def _confianza_de(evidencia):
    return _MAPA_CONFIANZA.get(evidencia, "medium")


def _slug_fichero(knowledge_id):
    """`knowledge_id` ya cumple `[A-Za-z0-9._-]+` (lo exige el Curator); es un nombre de fichero
    seguro tal cual, sin necesidad de un slugger nuevo."""
    return f"{knowledge_id}.md"


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


def health(cfg):
    """Nunca lanza: cualquier fallo de red/parseo degrada a un `estado` del enum
    `off · sano · degradado · error` (design.md, tabla del contrato de adaptador)."""
    health_cfg = (cfg or {}).get("health") or {}
    url = health_cfg.get("url")
    if not url:
        return {"estado": "off", "detalle": "sin `health.url` configurada"}
    timeout_s = max(0.01, (health_cfg.get("timeout_ms") or 800) / 1000.0)
    try:
        with urllib.request.urlopen(url, timeout=timeout_s) as resp:
            cuerpo = resp.read()
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


def plan(entries, cfg):
    """Idempotente: mismas `entries` -> mismo `ops`. Compara contra `manifest.json` en
    `export_dir` para calcular los `revoke` de entradas que ya no están en `entries` (salieron de
    `approved/` o dejaron de enrutar a este backend)."""
    export_dir = (cfg or {}).get("export_dir") or "."
    manifest = _leer_manifest(export_dir)
    ids_actuales = {e["id"] for e in entries}
    ops = []
    for e in entries:
        ops.append({
            "accion": "upsert",
            "knowledge_id": e["id"],
            "project": _proyecto_de(e["id"]),
            "category": e.get("category"),
            "version": e.get("version"),
            "confidence": _confianza_de(e.get("evidencia")),
            "cuerpo": e.get("cuerpo") or "",
        })
    for id_antiguo in sorted(manifest["entries"]):
        if id_antiguo not in ids_actuales:
            ops.append({"accion": "revoke", "knowledge_id": id_antiguo})
    return ops


def apply(ops, cfg):
    """Publica de forma atómica (fichero a fichero + `manifest.json` al final). Un fallo a medias
    nunca deja el `manifest.json` apuntando a un estado inconsistente: se reescribe entero solo al
    terminar de procesar todas las `ops`."""
    export_dir = (cfg or {}).get("export_dir") or "."
    manifest = _leer_manifest(export_dir)
    escritos = 0
    revocados = 0
    for op in ops:
        if op["accion"] == "upsert":
            contenido, hash_ = _render_markdown(op)
            ruta_relativa = _slug_fichero(op["knowledge_id"])
            _escribir_atomico(os.path.join(export_dir, ruta_relativa), contenido)
            manifest["entries"][op["knowledge_id"]] = {
                "ruta_relativa": ruta_relativa, "hash": hash_,
                "version": op.get("version"), "category": op.get("category"),
            }
            escritos += 1
        elif op["accion"] == "revoke":
            _quitar_fichero(export_dir, manifest, op["knowledge_id"])
            revocados += 1
    manifest["version"] = MANIFEST_VERSION
    _escribir_manifest(export_dir, manifest)
    return {"escritos": escritos, "revocados": revocados, "export_dir": export_dir}


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
    export_dir = (cfg or {}).get("export_dir") or "."
    manifest = _leer_manifest(export_dir)
    quitado = _quitar_fichero(export_dir, manifest, knowledge_id)
    if quitado:
        _escribir_manifest(export_dir, manifest)
    return {"revocado": quitado, "knowledge_id": knowledge_id}


def _base_url_snapshot(health_url):
    if health_url.endswith("/health"):
        return health_url[: -len("/health")]
    return health_url


def verify(cfg):
    """Compara `manifest.json` (local) contra `GET <base>/graph/snapshot` (Kwipu). Un export
    publicado cuyo fichero no aparece entre los nodos `chunk` del snapshot es desfase: Kwipu aún
    no lo indexó. Nombra el remedio SIN ejecutarlo (CA-16) — nunca lanza, nunca hace red en frío
    sin capturar el error."""
    export_dir = (cfg or {}).get("export_dir") or "."
    manifest = _leer_manifest(export_dir)
    if not manifest["entries"]:
        return {"ok": True, "desfase": []}
    health_url = ((cfg or {}).get("health") or {}).get("url")
    timeout_s = max(0.01, ((cfg or {}).get("health") or {}).get("timeout_ms", 800) / 1000.0)
    if not health_url:
        return {"ok": False, "desfase": [{"knowledge_id": None,
                "motivo": "sin `health.url` configurada, no se puede localizar `/graph/snapshot`",
                "remedio": REMEDIO}]}
    snapshot_url = _base_url_snapshot(health_url) + "/graph/snapshot"
    try:
        with urllib.request.urlopen(snapshot_url, timeout=timeout_s) as resp:
            cuerpo = resp.read()
        snapshot = json.loads(cuerpo.decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, OSError, ValueError, UnicodeDecodeError) as e:
        return {"ok": False, "desfase": [{"knowledge_id": None,
                "motivo": f"no se pudo conectar a {snapshot_url}: {type(e).__name__}: {e}",
                "remedio": REMEDIO}]}
    nombres_indexados = {
        n.get("file_name") for n in (snapshot.get("nodes") or [])
        if isinstance(n, dict) and n.get("type") == "chunk" and n.get("file_name")
    }
    desfase = []
    for knowledge_id, entrada in sorted(manifest["entries"].items()):
        nombre = os.path.basename(entrada.get("ruta_relativa") or "")
        if nombre not in nombres_indexados:
            desfase.append({
                "knowledge_id": knowledge_id,
                "motivo": f"`{nombre}` publicado pero no aparece en `/graph/snapshot`",
                "remedio": REMEDIO,
            })
    return {"ok": not desfase, "desfase": desfase}
