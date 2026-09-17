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

Estructura en disco, bajo `<dir>/` (directorios 0700, ficheros 0600 — la cola puede llevar rutas
de disco y `session_id`, no es información pública, Lente C gap 9 de la revisión intento 1):
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
      veces produce una única entrada lógica, CA-03 de la spec). `clave` debe casar
      `^[A-Za-z0-9._-]{1,64}$` (ValueError si no: evita escapar de la cola con `../`, CWE-22).
  reclamar(dir, processing_ttl_s=PROCESSING_TTL_S) -> item | None
      Antes de nada, barre `processing/`: un item reclamado hace más de `processing_ttl_s` (un
      proceso murió entre el claim y `completar`/`dead_letter`) se re-encola a `outbox/` con un
      contador de intentos (sidecar `<clave>.json.intentos`), o va a `dead-letter/` con causa
      «reintentos agotados» al superar MAX_INTENTOS (revisión intento 1, gaps 1/22). Después mueve
      UN envelope pendiente de `outbox/` a `processing/` con `os.replace` (mismo nombre de fichero
      en origen y destino): la exclusividad la da el sistema de ficheros, no un cerrojo propio — si
      dos procesos reclaman a la vez, solo uno consigue mover el fichero (el `rename` del perdedor
      falla porque el origen ya no existe) y el otro recibe `None`. `item` es
      {"clave", "path", "payload"}; `payload` es `None` si el JSON no es legible (envelope
      venenoso: lo decide el llamador, normalmente `dead_letter` inmediato). Sin pendientes -> `None`.
  completar(item, manifiesto=None) -> ruta
      Mueve el item de `processing/` a `done/` y escribe `<ruta>.manifest.json` con el
      `manifiesto` dado más `hash` (sha256 del contenido) y `completado_en` (si no vienen ya).
      Limpia el sidecar `.intentos` si lo hubiera.
  dead_letter(item, causa) -> ruta
      Mueve el item de `processing/` a `dead-letter/` y escribe `<ruta>.causa.json` con `causa`,
      `intentos` (se incrementa si ya había una causa previa para esa clave) y `en`. Un dead-letter
      nunca bloquea el resto de la cola: es un fichero más, movido y ya.
  reencolar_o_dead_letter(item, causa, intentos_max=MAX_INTENTOS) -> bool
      Tras un fallo TRANSITORIO materializando (disco lleno, permisos): reencola el item a
      `outbox/` incrementando su contador de intentos, o lo manda a `dead-letter/` si ya alcanzó
      `intentos_max`. Devuelve `True` si se reencoló, `False` si fue a dead-letter.
  estado(dir) -> {"outbox", "processing", "done", "dead-letter", "durabilidad"}
      Contadores de envelopes (`.json` que no sean `.manifest.json`/`.causa.json`/`.intentos`) por
      carpeta, más `durabilidad`: "ok" o "degradada" si algún `fsync` de esta cola falló alguna vez
      (best-effort, gap 21 de la revisión). Sin `dir` -> todo a 0.
  purgar_antiguos(dir, sub, dias) -> int
      Borra ficheros de `<dir>/<sub>/` (con sus sidecars) cuyo mtime supera `dias` días. Usado por
      `journal.py replay` para no dejar crecer `done/` para siempre (gap 22); `dead-letter/` se
      conserva a propósito (nunca lo llama el replay).
  limpiar_tmp_huerfanos(dir, ttl_s=PROCESSING_TTL_S) -> int
      Borra temporales `*.tmp-*` huérfanos (un corte a mitad de escritura, o un fichero plantado)
      con más de `ttl_s` en `outbox/`/`processing/` (gap 3/13 de la revisión).
  purgar(dir, confirmar=True) -> bool
      Borra el árbol completo de `dir`. Sin `confirmar=True` no hace nada (devuelve `False`): es el
      único borrado TOTAL de la cola (CA-12 de la spec: uninstall/upgrade del plugin nunca la toca).
"""
import contextlib
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import time

# Consola Windows (cp1252) o tuberías: reconfigurar ANTES de leer o imprimir nada (GOT-005).
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure, ya leído o None (capsys, pythonw)

SUBDIRS = ("outbox", "processing", "done", "dead-letter")
_CLAVE_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
INTENTOS_SUFFIX = ".intentos"
PROCESSING_TTL_S = 600              # un item reclamado más de esto sin completar/dead-letter se re-encola (gap 1)
MAX_INTENTOS = 3                    # tras esto, dead-letter con causa «reintentos agotados» (gap 1/22)
_DEGRADADO_MARKER = ".durabilidad-degradada"    # sentinela en <dir>/: algún fsync de esta cola falló alguna vez


def _iso_now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _marcar_degradado(dir_):
    """Sentinela best-effort: `estado()` lo lee para avisar «durabilidad: degradada» (gap 21)."""
    try:
        os.makedirs(dir_, exist_ok=True)
        open(os.path.join(dir_, _DEGRADADO_MARKER), "a", encoding="utf-8").close()
    except OSError:
        pass


def _mkdir_privado(path):
    """`makedirs` + `chmod 0700`: la cola puede llevar rutas de disco y `session_id` (gap 9)."""
    os.makedirs(path, exist_ok=True)
    try:
        os.chmod(path, 0o700)
    except OSError:
        pass


def _fsync_dir(dirpath):
    """`fsync` del directorio tras un `os.replace` (POSIX; no aplica en Windows, se ignora ahí):
    sin esto, la entrada del directorio puede no sobrevivir a un corte aunque el fichero sí
    (gap 21). Devuelve True si se pudo, False si se degrada (no bloquea)."""
    if os.name == "nt":
        return True
    try:
        fd = os.open(dirpath, os.O_RDONLY)
    except OSError:
        return False
    try:
        os.fsync(fd)
        return True
    except OSError:
        return False
    finally:
        try:
            os.close(fd)
        except OSError:
            pass


def _escribir_atomico(destino, contenido, dir_raiz=None):
    """Temporal en la misma carpeta (nombre único vía `tempfile.mkstemp`, 0600 por defecto) +
    `os.replace`: nunca deja el destino a medias aunque el proceso muera a mitad de la escritura
    (CA-04 de la spec). `fsync` del fichero y del directorio; si cualquiera de los dos degrada, se
    marca en `dir_raiz` (o en el padre de `destino` si no se da) para que `estado()` lo reporte."""
    carpeta = os.path.dirname(destino) or "."
    fd, tmp = tempfile.mkstemp(dir=carpeta, prefix=os.path.basename(destino) + ".tmp-")
    ok = True
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(contenido)
            fh.flush()
            try:
                os.fsync(fh.fileno())
            except OSError:
                ok = False           # fsync no disponible (algunos FS de red): degradación, no bloqueo
        os.replace(tmp, destino)
    except BaseException:
        with contextlib.suppress(OSError):
            os.remove(tmp)
        raise
    if not _fsync_dir(carpeta):
        ok = False
    if not ok:
        _marcar_degradado(dir_raiz or os.path.dirname(carpeta) or carpeta)


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
    si ya hay un envelope con esa clave en cualquier carpeta de la cola, no se reescribe.
    `ValueError` si `clave` no casa `^[A-Za-z0-9._-]{1,64}$` (gap 23: sin esto, `../../ESCAPE`
    crea fuera de la cola)."""
    if not isinstance(clave, str) or not _CLAVE_RE.match(clave):
        raise ValueError(f"clave de outbox inválida: {clave!r}")
    existente = _localizar(dir_, clave)
    if existente is not None:
        return existente
    outbox_dir = os.path.join(dir_, "outbox")
    _mkdir_privado(outbox_dir)
    destino = os.path.join(outbox_dir, f"{clave}.json")
    _escribir_atomico(destino, json.dumps(payload, ensure_ascii=False, indent=2), dir_raiz=dir_)
    return destino


def _leer_intentos(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return int((fh.read() or "0").strip() or "0")
    except (OSError, ValueError):
        return 0


def _mover_a_outbox_con_intentos(src, intentos):
    """`processing/<clave>.json` -> `outbox/<clave>.json`, dejando `.intentos` al día. Devuelve
    `True` si se movió."""
    dir_ = os.path.dirname(os.path.dirname(src))
    outbox_dir = os.path.join(dir_, "outbox")
    _mkdir_privado(outbox_dir)
    dst = os.path.join(outbox_dir, os.path.basename(src))
    try:
        os.replace(src, dst)
    except OSError:
        return False
    with contextlib.suppress(OSError):
        _escribir_atomico(dst + INTENTOS_SUFFIX, str(intentos), dir_raiz=dir_)
    with contextlib.suppress(OSError):
        os.remove(src + INTENTOS_SUFFIX)
    return True


def reencolar_o_dead_letter(item, causa, intentos_max=MAX_INTENTOS):
    """Tras un fallo TRANSITORIO materializando (item ya en `processing/`): reencola a `outbox/`
    con el contador de intentos incrementado, o dead-letter si ya alcanzó `intentos_max`. Devuelve
    `True` si se reencoló (`False` si fue a dead-letter o si ni siquiera se pudo mover)."""
    src = item["path"] if isinstance(item, dict) else str(item)
    intentos = _leer_intentos(src + INTENTOS_SUFFIX) + 1
    if intentos >= intentos_max:
        dead_letter(item, f"{causa} (reintentos agotados)")
        with contextlib.suppress(OSError):
            os.remove(src + INTENTOS_SUFFIX)
        return False
    return _mover_a_outbox_con_intentos(src, intentos)


def _reclamar_huerfanos(dir_, ttl_s):
    """Barre `processing/`: los items reclamados hace más de `ttl_s` (un proceso murió entre el
    claim y `completar`/`dead_letter`, gap 1 Critical de la revisión) se re-encolan con contador de
    intentos, o van a `dead-letter/` al superar MAX_INTENTOS."""
    proc_dir = os.path.join(dir_, "processing")
    try:
        nombres = [f for f in os.listdir(proc_dir) if f.endswith(".json")]
    except OSError:
        return
    ahora = time.time()
    for nombre in nombres:
        src = os.path.join(proc_dir, nombre)
        try:
            edad = ahora - os.stat(src).st_mtime
        except OSError:
            continue
        if edad <= ttl_s:
            continue
        item = {"clave": nombre[:-len(".json")], "path": src, "payload": None}
        reencolar_o_dead_letter(item, "envelope huérfano en processing/ (proceso interrumpido)")


def reclamar(dir_, processing_ttl_s=PROCESSING_TTL_S):
    """Reclama UN envelope pendiente: primero re-encola/dead-letter los huérfanos de `processing/`
    (gap 1), luego mueve `outbox/<clave>.json` -> `processing/<clave>.json`.

    La exclusividad frente a un segundo proceso concurrente la da el propio `os.replace`: el
    origen desaparece con la primera reclamación que se ejecuta, así que la segunda falla con
    `FileNotFoundError` (o `PermissionError` en Windows si el fichero ya no está) y se salta ese
    candidato. Devuelve `None` si no hay nada pendiente o si todos los candidatos listados ya
    fueron reclamados por otro proceso entre el `listdir` y el `replace`."""
    _reclamar_huerfanos(dir_, processing_ttl_s)
    outbox_dir = os.path.join(dir_, "outbox")
    proc_dir = os.path.join(dir_, "processing")
    try:
        nombres = sorted(f for f in os.listdir(outbox_dir) if f.endswith(".json"))
    except OSError:
        return None
    if not nombres:
        return None
    _mkdir_privado(proc_dir)
    for nombre in nombres:
        src = os.path.join(outbox_dir, nombre)
        dst = os.path.join(proc_dir, nombre)
        try:
            os.replace(src, dst)
        except OSError:
            continue                # ya reclamado por otro proceso: siguiente candidato
        intentos_src = src + INTENTOS_SUFFIX
        if os.path.isfile(intentos_src):
            with contextlib.suppress(OSError):
                os.replace(intentos_src, dst + INTENTOS_SUFFIX)
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
    _mkdir_privado(dst_dir)
    dst = os.path.join(dst_dir, os.path.basename(src))
    os.replace(src, dst)
    with contextlib.suppress(OSError):
        os.remove(src + INTENTOS_SUFFIX)
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
        with open(causa_path, encoding="utf-8") as fh:      # cerrado explícitamente (gap 23: fugaba el fd)
            prev = json.load(fh)
        intentos = int(prev.get("intentos", 0)) + 1
    except (OSError, ValueError, TypeError):
        pass
    _escribir_atomico(causa_path, json.dumps({"causa": str(causa), "intentos": intentos, "en": _iso_now()},
                                              ensure_ascii=False, indent=2))
    return dst


def estado(dir_):
    """Contadores de envelopes (excluye `.manifest.json`/`.causa.json`/`.intentos`) por carpeta,
    más `durabilidad` («ok» / «degradada» si algún `fsync` de esta cola falló alguna vez)."""
    out = {}
    for sub in SUBDIRS:
        p = os.path.join(dir_, sub)
        try:
            out[sub] = len([f for f in os.listdir(p)
                            if f.endswith(".json") and not f.endswith((".manifest.json", ".causa.json"))])
        except OSError:
            out[sub] = 0
    out["durabilidad"] = "degradada" if os.path.isfile(os.path.join(dir_, _DEGRADADO_MARKER)) else "ok"
    return out


def purgar_antiguos(dir_, sub, dias):
    """Borra ficheros de `<dir_>/<sub>/` (con sus sidecars `.manifest.json`/`.causa.json`) con más
    de `dias` días (mtime). Devuelve cuántos se borraron. Pensado para `done/` (gap 22); nunca se
    llama sobre `dead-letter/` (se conserva a propósito) ni sobre `outbox/`/`processing/`."""
    p = os.path.join(dir_, sub)
    try:
        nombres = [f for f in os.listdir(p) if f.endswith(".json")
                   and not f.endswith((".manifest.json", ".causa.json"))]
    except OSError:
        return 0
    limite = time.time() - dias * 86400
    borrados = 0
    for fn in nombres:
        fp = os.path.join(p, fn)
        try:
            vieja = os.stat(fp).st_mtime < limite
        except OSError:
            continue
        if not vieja:
            continue
        for cand in (fp, fp + ".manifest.json", fp + ".causa.json"):
            with contextlib.suppress(OSError):
                os.remove(cand)
        borrados += 1
    return borrados


def limpiar_tmp_huerfanos(dir_, ttl_s=PROCESSING_TTL_S):
    """Borra temporales `*.tmp-*` huérfanos (un corte a mitad de escritura, o un fichero plantado
    por fuera) con más de `ttl_s` en `outbox/`/`processing/`. Devuelve cuántos se borraron."""
    borrados = 0
    limite = time.time() - ttl_s
    for sub in ("outbox", "processing"):
        p = os.path.join(dir_, sub)
        try:
            nombres = os.listdir(p)
        except OSError:
            continue
        for fn in nombres:
            if ".tmp-" not in fn:
                continue
            fp = os.path.join(p, fn)
            try:
                if os.stat(fp).st_mtime < limite:
                    os.remove(fp)
                    borrados += 1
            except OSError:
                continue
    return borrados


def purgar(dir_, confirmar=True):
    """Borra el árbol completo de `dir_`. Sin `confirmar=True`, no hace nada (`False`)."""
    if not confirmar:
        return False
    shutil.rmtree(dir_, ignore_errors=True)
    return True
