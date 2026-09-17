#!/usr/bin/env python3
"""
outbox.py — cola atómica de staging con claim, done y dead-letter (agent-kits/shared).

Nace en la iniciativa `session-end-durable-capture` (C-05, `design.md` O1) para que la captura de
`SessionEnd` (`journal.py capture-end`) sea instantánea: escribe un *envelope* aquí y la
materialización (con git, IA opt-in, verificación) corre después, de forma recuperable
(`journal.py replay`). El mismo contrato lo reutilizan otros exportadores de memoria
(`knowledge-services` T-07, `graphiti-memory` T-05): una sola implementación de cola/staging
atómico para toda la cadena, con la MISMA idempotencia y el MISMO dead-letter.

Solo stdlib; sin red; nunca ejecuta git ni IA (eso es responsabilidad del llamador, no de la cola).

Estructura en disco, bajo `<dir>/`:
  outbox/       envelopes pendientes de reclamar (`<clave>.json`)
  processing/   reclamados, en curso de materialización
  done/         materializados con éxito (`<clave>.json` + `<clave>.json.manifest.json`)
  dead-letter/  descartados con causa (`<clave>.json` + `<clave>.json.causa.json`, con `intentos`)

Contrato (todas las funciones son deterministas, no lanzan por errores de disco esperables):
  escribir(dir, clave, payload) -> ruta
      Serializa `payload` a JSON y lo escribe en `outbox/<clave>.json` con temporal + `os.replace`
      (atómico: nunca hay un `.json` a medias). IDEMPOTENTE por `clave`: si ya existe un envelope
      con esa clave en outbox/, processing/, done/ o dead-letter/, no se reescribe — se devuelve la
      ruta ya existente (el primer envelope de una clave manda; capturar el mismo evento varias
      veces produce una única entrada lógica, CA-03 de la spec).
  reclamar(dir) -> item | None
      Mueve UN envelope pendiente de `outbox/` a `processing/` con `os.replace` (mismo nombre de
      fichero en origen y destino): la exclusividad la da el sistema de ficheros, no un cerrojo
      propio — si dos procesos reclaman a la vez, solo uno consigue mover el fichero (el `rename`
      del perdedor falla porque el origen ya no existe) y el otro recibe `None`. `item` es
      {"clave", "path", "payload"}; `payload` es `None` si el JSON no es legible (envelope
      venenoso: lo decide el llamador, normalmente `dead_letter` inmediato). Sin pendientes -> `None`.
  completar(item, manifiesto=None) -> ruta
      Mueve el item de `processing/` a `done/` y escribe `<ruta>.manifest.json` con el
      `manifiesto` dado más `hash` (sha256 del contenido) y `completado_en` (si no vienen ya).
  dead_letter(item, causa) -> ruta
      Mueve el item de `processing/` a `dead-letter/` y escribe `<ruta>.causa.json` con `causa`,
      `intentos` (se incrementa si ya había una causa previa para esa clave) y `en`. Un dead-letter
      nunca bloquea el resto de la cola: es un fichero más, movido y ya.
  estado(dir) -> {"outbox", "processing", "done", "dead-letter"}
      Contadores de envelopes (`.json` que no sean `.manifest.json` ni `.causa.json`) por carpeta.
      Sin `dir` -> todo a 0.
  purgar(dir, confirmar=True) -> bool
      Borra el árbol completo de `dir`. Sin `confirmar=True` no hace nada (devuelve `False`): es el
      único borrado de la cola (CA-12 de la spec: uninstall/upgrade del plugin nunca la toca).
"""
import hashlib
import json
import os
import shutil
import sys
import time

# Consola Windows (cp1252) o tuberías: reconfigurar ANTES de leer o imprimir nada (GOT-005).
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure, ya leído o None (capsys, pythonw)

SUBDIRS = ("outbox", "processing", "done", "dead-letter")


def _iso_now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _escribir_atomico(destino, contenido):
    """Temporal en la misma carpeta + `os.replace`: nunca deja el destino a medias aunque el
    proceso muera a mitad de la escritura (CA-04 de la spec)."""
    tmp = f"{destino}.tmp-{os.getpid()}"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(contenido)
        fh.flush()
        try:
            os.fsync(fh.fileno())
        except OSError:
            pass                     # fsync no disponible (algunos FS de red): degradación, no bloqueo
    os.replace(tmp, destino)


def _localizar(dir_, clave):
    """Ruta del envelope `clave` en cualquiera de las cuatro carpetas, o `None` si no existe en
    ninguna (usado por `escribir` para la idempotencia más allá de `outbox/`)."""
    for sub in SUBDIRS:
        p = os.path.join(dir_, sub, f"{clave}.json")
        if os.path.isfile(p):
            return p
    return None


def escribir(dir_, clave, payload):
    """Escribe `payload` en `outbox/<clave>.json` (tmp + rename atómico). Idempotente por clave:
    si ya hay un envelope con esa clave en cualquier carpeta de la cola, no se reescribe."""
    existente = _localizar(dir_, clave)
    if existente is not None:
        return existente
    outbox_dir = os.path.join(dir_, "outbox")
    os.makedirs(outbox_dir, exist_ok=True)
    destino = os.path.join(outbox_dir, f"{clave}.json")
    _escribir_atomico(destino, json.dumps(payload, ensure_ascii=False, indent=2))
    return destino


def reclamar(dir_):
    """Reclama UN envelope pendiente: `outbox/<clave>.json` -> `processing/<clave>.json`.

    La exclusividad frente a un segundo proceso concurrente la da el propio `os.replace`: el
    origen desaparece con la primera reclamación que se ejecuta, así que la segunda falla con
    `FileNotFoundError` (o `PermissionError` en Windows si el fichero ya no está) y se salta ese
    candidato. Devuelve `None` si no hay nada pendiente o si todos los candidatos listados ya
    fueron reclamados por otro proceso entre el `listdir` y el `replace`."""
    outbox_dir = os.path.join(dir_, "outbox")
    proc_dir = os.path.join(dir_, "processing")
    try:
        nombres = sorted(f for f in os.listdir(outbox_dir) if f.endswith(".json"))
    except OSError:
        return None
    if not nombres:
        return None
    os.makedirs(proc_dir, exist_ok=True)
    for nombre in nombres:
        src = os.path.join(outbox_dir, nombre)
        dst = os.path.join(proc_dir, nombre)
        try:
            os.replace(src, dst)
        except OSError:
            continue                # ya reclamado por otro proceso: siguiente candidato
        try:
            with open(dst, encoding="utf-8") as fh:
                payload = json.load(fh)
        except (OSError, ValueError):
            payload = None          # envelope venenoso: el llamador decide (normalmente dead_letter)
        return {"clave": nombre[:-len(".json")], "path": dst, "payload": payload}
    return None


def _mover_desde_processing(item, subdir_destino):
    src = item["path"] if isinstance(item, dict) else str(item)
    dir_ = os.path.dirname(os.path.dirname(src))     # .../processing/<clave>.json -> dir_
    dst_dir = os.path.join(dir_, subdir_destino)
    os.makedirs(dst_dir, exist_ok=True)
    dst = os.path.join(dst_dir, os.path.basename(src))
    os.replace(src, dst)
    return dst


def completar(item, manifiesto=None):
    """`processing/` -> `done/`; escribe `<ruta>.manifest.json` con `hash` (sha256 del contenido)
    y `completado_en` además de lo que traiga `manifiesto`."""
    try:
        with open(item["path"] if isinstance(item, dict) else str(item), "rb") as fh:
            contenido = fh.read()
    except OSError:
        contenido = b""
    dst = _mover_desde_processing(item, "done")
    man = dict(manifiesto or {})
    man.setdefault("hash", hashlib.sha256(contenido).hexdigest())
    man.setdefault("completado_en", _iso_now())
    _escribir_atomico(dst + ".manifest.json", json.dumps(man, ensure_ascii=False, indent=2))
    return dst


def dead_letter(item, causa):
    """`processing/` -> `dead-letter/`; escribe `<ruta>.causa.json` con `causa`, `intentos`
    (incrementado si ya había una causa previa para esa clave) y `en`. Nunca bloquea el resto de
    la cola: es un fichero más, movido y ya (CA-06 de la spec)."""
    dst = _mover_desde_processing(item, "dead-letter")
    causa_path = dst + ".causa.json"
    intentos = 1
    try:
        prev = json.load(open(causa_path, encoding="utf-8"))
        intentos = int(prev.get("intentos", 0)) + 1
    except (OSError, ValueError, TypeError):
        pass
    _escribir_atomico(causa_path, json.dumps({"causa": str(causa), "intentos": intentos, "en": _iso_now()},
                                              ensure_ascii=False, indent=2))
    return dst


def estado(dir_):
    """Contadores de envelopes (excluye `.manifest.json`/`.causa.json`) por carpeta."""
    out = {}
    for sub in SUBDIRS:
        p = os.path.join(dir_, sub)
        try:
            out[sub] = len([f for f in os.listdir(p)
                            if f.endswith(".json") and not f.endswith((".manifest.json", ".causa.json"))])
        except OSError:
            out[sub] = 0
    return out


def purgar(dir_, confirmar=True):
    """Borra el árbol completo de `dir_`. Sin `confirmar=True`, no hace nada (`False`)."""
    if not confirmar:
        return False
    shutil.rmtree(dir_, ignore_errors=True)
    return True
