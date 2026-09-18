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
      Antes de nada, barre `processing/` (protegido con `try/except OSError`: un dead-letter/
      inutilizable no debe abortar el barrido ni el resto de la reclamación, gap 31 de la revisión
      intento 2): un item reclamado hace más de `processing_ttl_s` (un proceso murió entre el
      claim y `completar`/`dead_letter`) se re-encola a `outbox/` SIN backoff (es recuperación de un
      worker muerto, no un fallo repetido) con un contador de intentos (sidecar
      `<clave>.json.intentos`), o va a `dead-letter/` con causa «reintentos agotados» al superar
      MAX_INTENTOS (revisión intento 1, gaps 1/22). Después mueve UN envelope pendiente de
      `outbox/` a `processing/` con `os.replace` (mismo nombre de fichero en origen y destino): la
      exclusividad la da el sistema de ficheros, no un cerrojo propio — si dos procesos reclaman a
      la vez, solo uno consigue mover el fichero (el `rename` del perdedor falla porque el origen
      ya no existe) y el otro recibe `None`. Al mover, el mtime del destino se refresca a "ahora"
      (gap 25 Critical de la revisión intento 2): el TTL de huérfanos se mide desde la RECLAMACIÓN,
      no desde la creación del envelope — sin esto, un envelope que esperó > `processing_ttl_s` en
      `outbox/` (el caso normal: `replay` corre horas después) se entregaba a DOS trabajadores a la
      vez, porque su mtime heredado de `outbox/` ya superaba la TTL nada más reclamarlo. Los
      candidatos con `no_antes_de` en el futuro (backoff tras un fallo TRANSITORIO, gap 26) se
      saltan. `item` es {"clave", "path", "payload"}; `payload` es `None` si el JSON no es legible
      (envelope venenoso: lo decide el llamador, normalmente `dead_letter` inmediato). Sin
      pendientes -> `None`.
  completar(item, manifiesto=None) -> ruta
      Mueve el item de `processing/` a `done/` y escribe `<ruta>.manifest.json` con el
      `manifiesto` dado más `hash` (sha256 del contenido) y `completado_en` (si no vienen ya) —
      `completado_en` es la fecha real de materialización, la que usa `purgar_antiguos` (gap 33 de
      la revisión: purgar por mtime del envelope de creación borraba una sesión que esperó semanas
      en la outbox en la MISMA pasada en que se materializaba, sin barrera de idempotencia).
      Limpia el sidecar `.intentos` si lo hubiera.
  dead_letter(item, causa, intentos=None) -> ruta
      Mueve el item de `processing/` a `dead-letter/` y escribe `<ruta>.causa.json` con `causa`,
      `intentos` (el valor real del sidecar `.intentos` si se pasa —gap 43 de la revisión: antes
      `causa.json` declaraba `intentos: 1` tras 3 reintentos porque no leía el sidecar— o
      incrementado desde una causa previa si no) y `en`. Un dead-letter nunca bloquea el resto de
      la cola: es un fichero más, movido y ya.
  reencolar_o_dead_letter(item, causa, intentos_max=MAX_INTENTOS, backoff=True) -> str
      Tras un fallo materializando (item ya en `processing/`): reencola a `outbox/` con el contador
      de intentos incrementado, o dead-letter si ya alcanzó `intentos_max`. Devuelve uno de
      `REENCOLADO`/`DEAD_LETTER`/`ERROR` (gap 45 de la revisión: antes devolvía `bool`, y el
      llamador contaba «dead-letter» también cuando en realidad ni se pudo MOVER el item — el JSON
      de `replay` mentía). Con `backoff=True` (fallo TRANSITORIO real: disco lleno, permisos), el
      reencolado lleva `no_antes_de = ahora + BACKOFF_S × intentos` (creciente): sin esto, un fallo
      permanente agotaba los 3 intentos en milisegundos dentro de la MISMA pasada de `replay` (el
      bucle lo reclamaba al instante) y la sesión acababa en dead-letter sin haber esperado nada
      entre reintentos (gap 26 Critical). Con `backoff=False` (recuperación de huérfanos de
      `processing/`: no es un fallo del código, es un worker muerto) el reencolado es inmediato.
  reintentar_dead_letter(dir) -> int
      Mueve TODO `dead-letter/` de vuelta a `outbox/` con el contador de intentos a 0 (remedio
      nombrado, gap 26: sin esto una sesión en dead-letter se perdía para siempre — `journal.py
      replay --reintentar-dead-letter`, que `/doctor` nombrará en T-06). Devuelve cuántos se
      movieron.
  estado(dir) -> {"outbox", "processing", "done", "dead-letter", "durabilidad", "permisos"}
      Contadores de envelopes (`.json` que no sean `.manifest.json`/`.causa.json`/`.intentos`) por
      carpeta, más `durabilidad` ("ok"/"degradada" si algún `fsync` de esta cola falló alguna vez,
      best-effort, gap 21) y `permisos` ("ok"/"degradados" si algún `chmod 0700/0600` de esta cola
      falló alguna vez, gap 46). Sin `dir` -> todo a 0.
  purgar_antiguos(dir, sub, dias) -> int
      Borra ficheros de `<dir>/<sub>/` (con sus sidecars) cuyo `completado_en` (del
      `.manifest.json`, NO el mtime del envelope) supera `dias` días; sin ese campo, NO se purga
      (gap 33). Usado por `journal.py replay` para no dejar crecer `done/` para siempre (gap 22);
      `dead-letter/` se conserva a propósito (nunca lo llama el replay).
  limpiar_tmp_huerfanos(dir, ttl_s=PROCESSING_TTL_S) -> int
      Borra temporales huérfanos (un corte a mitad de escritura, o un fichero plantado) cuyo
      nombre EMPIEZA por `.tmp-` (gap 35 de la revisión: decidir por subcadena `".tmp-"` borraba en
      silencio una clave legítima como `export.tmp-2026` que la contuviera) con más de `ttl_s` en
      `outbox/`/`processing/`.
  purgar(dir, confirmar=True) -> bool
      Borra el árbol completo de `dir`. Sin `confirmar=True` no hace nada (devuelve `False`): es el
      único borrado TOTAL de la cola (CA-12 de la spec: uninstall/upgrade del plugin nunca la toca).
"""
import calendar
import contextlib
import hashlib
import json
import math
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
CLAIMED_AT_SUFFIX = ".claimed_at"   # sidecar de respaldo con el instante REAL de reclamación (gap 50)
CLAIMING_SUFFIX = ".claiming"       # nombre temporal en processing/ mientras se refresca el mtime (gap 50)
PROCESSING_TTL_S = 600              # un item reclamado más de esto sin completar/dead-letter se re-encola (gap 1)
MAX_INTENTOS = 3                    # tras esto, dead-letter con causa «reintentos agotados» (gap 1/22)
BACKOFF_S = 60                      # backoff base tras un fallo TRANSITORIO; crece × nº de intento (gap 26)
BACKOFF_MAX_S = 3600                # tope de `no_antes_de` (gap 51): un salto de reloj o un sidecar
                                     # corrupto no debe dejar un item inalcanzable para siempre
CLAIMING_TTL_S = 30                 # un `.claiming` en processing/ (reclamación a medias, N-1) con más de
                                     # esto sin llegar al rename final es un proceso muerto entre pasos —
                                     # se devuelve a outbox/, NUNCA queda huérfano para siempre
_DEGRADADO_MARKER = ".durabilidad-degradada"    # sentinela en <dir>/: algún fsync de esta cola falló alguna vez
_PERMISOS_MARKER = ".permisos-degradados"       # sentinela en <dir>/: algún chmod de esta cola falló alguna vez
_RECLAMACION_MARKER = ".reclamacion-degradada"  # sentinela en <dir>/: `os.utime` al reclamar falló alguna vez (gap 50)
_RECUPERADOS_CLAIMING_MARKER = ".claiming-recuperados"  # contador best-effort de `.claiming` huérfanos recuperados (N-1)

REENCOLADO = "reencolado"
DEAD_LETTER = "dead_letter"
ERROR = "error"


def _iso_now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _iso_a_epoch(s):
    """`AAAA-MM-DDTHH:MM:SSZ` (UTC) -> epoch, o `None` si no parsea (gap 33: sin `completado_en`
    legible, `purgar_antiguos` no debe purgar por defecto a mtime)."""
    try:
        return calendar.timegm(time.strptime(str(s), "%Y-%m-%dT%H:%M:%SZ"))
    except (ValueError, TypeError):
        return None


def _marcar_degradado(dir_):
    """Sentinela best-effort: `estado()` lo lee para avisar «durabilidad: degradada» (gap 21)."""
    try:
        os.makedirs(dir_, exist_ok=True)
        open(os.path.join(dir_, _DEGRADADO_MARKER), "a", encoding="utf-8").close()
    except OSError:
        pass


def _marcar_permisos_degradados(dir_):
    """Sentinela best-effort: `estado()` lo lee para avisar «permisos: degradados» (gap 46: un
    `chmod` que falla hoy se traga en silencio sin ninguna señal)."""
    try:
        os.makedirs(dir_, exist_ok=True)
        open(os.path.join(dir_, _PERMISOS_MARKER), "a", encoding="utf-8").close()
    except OSError:
        pass


def _marcar_reclamacion_degradada(dir_):
    """Sentinela best-effort: `estado()` lo lee para avisar «reclamacion: degradada» (gap 50: si
    `os.utime` falla al reclamar, el item vuelve a `outbox/` en vez de arriesgar doble entrega, pero
    eso no debe quedar en silencio)."""
    try:
        os.makedirs(dir_, exist_ok=True)
        open(os.path.join(dir_, _RECLAMACION_MARKER), "a", encoding="utf-8").close()
    except OSError:
        pass


def _incrementar_recuperados_claiming(dir_):
    """Contador best-effort (fichero de texto plano en `<dir_>/`) de cuántos `.claiming` huérfanos ha
    recuperado `_reclamar_huerfanos` a lo largo de la vida de esta cola: `estado()` lo expone en
    `recuperados_claiming` (N-1). Nunca lanza; si no se puede leer/escribir, se degrada en silencio
    (igual que el resto de sentinelas de esta cola)."""
    path = os.path.join(dir_, _RECUPERADOS_CLAIMING_MARKER)
    n = 0
    with contextlib.suppress(OSError, ValueError):
        with open(path, encoding="utf-8") as fh:
            n = int((fh.read() or "0").strip())
    with contextlib.suppress(OSError):
        os.makedirs(dir_, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(str(n + 1))


def _leer_recuperados_claiming(dir_):
    try:
        with open(os.path.join(dir_, _RECUPERADOS_CLAIMING_MARKER), encoding="utf-8") as fh:
            return int((fh.read() or "0").strip())
    except (OSError, ValueError):
        return 0


def _mkdir_privado(path, dir_raiz=None):
    """`makedirs` + `chmod 0700`: la cola puede llevar rutas de disco y `session_id` (gap 9). Si el
    `chmod` falla, se marca `permisos: degradados` en `dir_raiz` (o `path` si no se da) en vez de
    tragarse el fallo en silencio (gap 46)."""
    os.makedirs(path, exist_ok=True)
    try:
        os.chmod(path, 0o700)
    except OSError:
        _marcar_permisos_degradados(dir_raiz or path)


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
    """Temporal en la misma carpeta con prefijo `.tmp-` AL INICIO del nombre (gap 35: un prefijo a
    mitad de camino, `<clave>.tmp-<n>`, es indistinguible por subcadena de una clave legítima que
    contenga `.tmp-`) + `os.replace`: nunca deja el destino a medias aunque el proceso muera a
    mitad de la escritura (CA-04 de la spec). `fsync` del fichero y del directorio; si cualquiera
    de los dos degrada, se marca en `dir_raiz` (o en el padre de `destino` si no se da) para que
    `estado()` lo reporte."""
    carpeta = os.path.dirname(destino) or "."
    fd, tmp = tempfile.mkstemp(dir=carpeta, prefix=".tmp-", suffix=".json")
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
    ninguna (usado por `escribir` para la idempotencia más allá de `outbox/`). Un `.claiming` en
    `processing/` (reclamación a medias o huérfana, N-1) TAMBIÉN cuenta como "existe": sin esto,
    `escribir()` con la misma clave de un envelope que se está reclamando (o que quedó huérfano tras
    un corte) crea un segundo envelope en `outbox/`, rompiendo CA-03."""
    for sub in SUBDIRS:
        p = os.path.join(dir_, sub, f"{clave}.json")
        if os.path.isfile(p):
            return p
    p_claiming = os.path.join(dir_, "processing", f"{clave}.json{CLAIMING_SUFFIX}")
    if os.path.isfile(p_claiming):
        return p_claiming
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
    _mkdir_privado(outbox_dir, dir_raiz=dir_)
    destino = os.path.join(outbox_dir, f"{clave}.json")
    _escribir_atomico(destino, json.dumps(payload, ensure_ascii=False, indent=2), dir_raiz=dir_)
    return destino


def _leer_sidecar(path):
    """`{"intentos": int, "no_antes_de": float}` del sidecar `.intentos` (gap 26: pasa de un
    entero plano a JSON para llevar también el backoff); defaults a ceros si no existe o no
    parsea."""
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.loads(fh.read() or "{}")
        if isinstance(data, dict):
            return {"intentos": int(data.get("intentos", 0)), "no_antes_de": float(data.get("no_antes_de", 0) or 0)}
    except (OSError, ValueError, TypeError):
        pass
    return {"intentos": 0, "no_antes_de": 0.0}


def _escribir_sidecar(path, intentos, no_antes_de, dir_raiz=None):
    with contextlib.suppress(OSError):
        _escribir_atomico(path, json.dumps({"intentos": intentos, "no_antes_de": no_antes_de}), dir_raiz=dir_raiz)


def _no_antes_de_valido(no_antes_de, ahora):
    """Normaliza `no_antes_de` (gap 51 de la revisión intento 3): un salto de reloj hacia delante o
    un sidecar corrupto podían dejar un valor no finito o absurdamente lejano — sin tope, el item
    quedaba inalcanzable PARA SIEMPRE (`reintentar_dead_letter` no mira `outbox/`). Un valor que no
    parsea a `float`, no es finito, o supera `ahora + BACKOFF_MAX_S` se trata como 0.0 (reclamable
    de inmediato) en vez de respetarlo tal cual."""
    try:
        nad = float(no_antes_de)
    except (TypeError, ValueError):
        return 0.0
    if not math.isfinite(nad) or nad - ahora > BACKOFF_MAX_S:
        return 0.0
    return nad


def _leer_claimed_at(path):
    """Instante (epoch, `float`) del sidecar `<clave>.json.claimed_at`, o `None` si no existe o no
    parsea (gap 50: respaldo del mtime para medir el TTL de huérfanos si `os.utime` degradara)."""
    try:
        with open(path, encoding="utf-8") as fh:
            return float(fh.read().strip())
    except (OSError, ValueError):
        return None


def en_backoff(dir_):
    """`(n, proxima_iso)`: cuántos items de `outbox/` tienen `no_antes_de` válido en el futuro, y la
    fecha ISO del más próximo a liberarse (`None` si ninguno). Gap 51: antes `replay` no distinguía
    «outbox vacío» de «outbox con backoff pendiente» — devolvía `restantes: 1, avisos: []` sin
    explicar por qué no avanzaba."""
    outbox_dir = os.path.join(dir_, "outbox")
    try:
        nombres = [f for f in os.listdir(outbox_dir) if f.endswith(".json") and not f.startswith(".tmp-")]
    except OSError:
        return 0, None
    ahora = time.time()
    pendientes = []
    for nombre in nombres:
        sidecar = _leer_sidecar(os.path.join(outbox_dir, nombre) + INTENTOS_SUFFIX)
        nad = _no_antes_de_valido(sidecar["no_antes_de"], ahora)
        if nad > ahora:
            pendientes.append(nad)
    if not pendientes:
        return 0, None
    return len(pendientes), time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(min(pendientes)))


def reintentar_ahora(dir_):
    """Pone `no_antes_de` a 0 en TODOS los sidecars de `outbox/` (gap 51): complementario a
    `reintentar_dead_letter` (que opera sobre `dead-letter/`) — `journal.py replay
    --reintentar-ahora` para un salto de reloj o un skew que dejó items en backoff que ya deberían
    ser reclamables. Devuelve cuántos tenían backoff pendiente y se liberaron."""
    outbox_dir = os.path.join(dir_, "outbox")
    try:
        nombres = [f for f in os.listdir(outbox_dir) if f.endswith(".json") and not f.startswith(".tmp-")]
    except OSError:
        return 0
    ahora = time.time()
    liberados = 0
    for nombre in nombres:
        sidecar_path = os.path.join(outbox_dir, nombre) + INTENTOS_SUFFIX
        if not os.path.isfile(sidecar_path):
            continue
        sc = _leer_sidecar(sidecar_path)
        if _no_antes_de_valido(sc["no_antes_de"], ahora) > ahora:
            liberados += 1
        _escribir_sidecar(sidecar_path, sc["intentos"], 0.0, dir_raiz=dir_)
    return liberados


def _mover_a_outbox_con_intentos(src, intentos, no_antes_de=0.0):
    """`processing/<clave>.json` -> `outbox/<clave>.json`, dejando `.intentos` al día (con
    `no_antes_de` para el backoff, gap 26). Devuelve `True` si se movió."""
    dir_ = os.path.dirname(os.path.dirname(src))
    outbox_dir = os.path.join(dir_, "outbox")
    _mkdir_privado(outbox_dir, dir_raiz=dir_)
    dst = os.path.join(outbox_dir, os.path.basename(src))
    try:
        os.replace(src, dst)
    except OSError:
        return False
    _escribir_sidecar(dst + INTENTOS_SUFFIX, intentos, no_antes_de, dir_raiz=dir_)
    with contextlib.suppress(OSError):
        os.remove(src + INTENTOS_SUFFIX)
    with contextlib.suppress(OSError):
        os.remove(src + CLAIMED_AT_SUFFIX)     # gap 50: reencolado a outbox/ ya no está "reclamado"
    return True


def dead_letter(item, causa, intentos=None):
    """`processing/` -> `dead-letter/`; escribe `<ruta>.causa.json` con `causa`, `intentos` (el
    valor REAL pasado por el llamador —del sidecar `.intentos`, gap 43— o incrementado desde una
    causa previa si no se da) y `en`. Nunca bloquea el resto de la cola: es un fichero más, movido
    y ya (CA-06 de la spec)."""
    dst = _mover_desde_processing(item, "dead-letter")
    causa_path = dst + ".causa.json"
    if intentos is None:
        intentos = 1
        try:
            with open(causa_path, encoding="utf-8") as fh:      # cerrado explícitamente (gap 23: fugaba el fd)
                prev = json.load(fh)
            intentos = int(prev.get("intentos", 0)) + 1
        except (OSError, ValueError, TypeError):
            pass
    _escribir_atomico(causa_path, json.dumps({"causa": str(causa), "intentos": int(intentos), "en": _iso_now()},
                                              ensure_ascii=False, indent=2))
    return dst


def reencolar_o_dead_letter(item, causa, intentos_max=MAX_INTENTOS, backoff=True):
    """Tras un fallo materializando (item ya en `processing/`): reencola a `outbox/` con el
    contador de intentos incrementado (con backoff creciente si `backoff=True`: fallo TRANSITORIO
    real), o dead-letter si ya alcanzó `intentos_max` (con el contador REAL, gap 43). Devuelve
    `REENCOLADO`/`DEAD_LETTER`/`ERROR` (gap 45: nunca un `bool` que el llamador podía malinterpretar
    como «se movió a dead-letter» cuando en realidad ni se pudo mover)."""
    src = item["path"] if isinstance(item, dict) else str(item)
    intentos = _leer_sidecar(src + INTENTOS_SUFFIX)["intentos"] + 1
    if intentos >= intentos_max:
        try:
            dead_letter(item, f"{causa} (reintentos agotados)", intentos=intentos)
        except OSError:
            # el sidecar `.intentos` se conserva TAL CUAL en el fallo (no se toca aquí): si se
            # borrara también en el camino de error, el próximo intento perdería la cuenta de
            # escaladas y volvería a reencolar en vez de seguir camino a dead-letter (gap 31/43).
            return ERROR
        return DEAD_LETTER
    # gap 51: tope también al ESCRIBIR (además de al leer en `reclamar`/`en_backoff`) — nunca se
    # persiste un `no_antes_de` más allá de `BACKOFF_MAX_S`, aunque `BACKOFF_S × intentos` fuera a más.
    no_antes_de = min(time.time() + BACKOFF_S * intentos, time.time() + BACKOFF_MAX_S) if backoff else 0.0
    try:
        ok = _mover_a_outbox_con_intentos(src, intentos, no_antes_de)
    except OSError:
        return ERROR
    return REENCOLADO if ok else ERROR


def reintentar_dead_letter(dir_):
    """Mueve TODO `dead-letter/` de vuelta a `outbox/` con el contador de intentos a 0: remedio
    nombrado para una sesión que se creía perdida para siempre (gap 26; `/doctor`, T-06, lo
    nombrará). Borra los sidecars `.causa.json`/`.intentos`. Devuelve cuántos se movieron."""
    dl_dir = os.path.join(dir_, "dead-letter")
    try:
        nombres = [f for f in os.listdir(dl_dir)
                   if f.endswith(".json") and not f.endswith((".causa.json", ".manifest.json"))]
    except OSError:
        return 0
    outbox_dir = os.path.join(dir_, "outbox")
    _mkdir_privado(outbox_dir, dir_raiz=dir_)
    movidos = 0
    for nombre in nombres:
        src = os.path.join(dl_dir, nombre)
        dst = os.path.join(outbox_dir, nombre)
        try:
            os.replace(src, dst)
        except OSError:
            continue
        with contextlib.suppress(OSError):
            os.remove(src + ".causa.json")
        with contextlib.suppress(OSError):
            os.remove(src + INTENTOS_SUFFIX)
        movidos += 1
    return movidos


def _recuperar_claiming_huerfanos(dir_, proc_dir, nombres_todos, claiming_ttl_s, errores):
    """Devuelve a `outbox/` los `.claiming` de `processing/` con más de `claiming_ttl_s` sin llegar
    al rename final de `reclamar()` (N-1 Critical): un proceso muerto ENTRE el `os.replace` a
    `.claiming` y el rename final (o entre `.claiming` y `os.utime`) dejaba antes un huérfano que
    NINGÚN barrido veía (`endswith('.json')` no casa con `.claiming`). Si ya hay un envelope con esa
    clave en `outbox/` (otro proceso lo repuso primero), el `.claiming` sobrante se borra en vez de
    pisar el existente. Cuenta cada recuperación en el sentinela `recuperados_claiming` de `estado()`."""
    claimings = [f for f in nombres_todos if f.endswith(CLAIMING_SUFFIX)]
    if not claimings:
        return
    outbox_dir = os.path.join(dir_, "outbox")
    ahora = time.time()
    for nombre in claimings:
        src = os.path.join(proc_dir, nombre)
        try:
            edad = ahora - os.stat(src).st_mtime
        except OSError:
            continue
        if edad <= claiming_ttl_s:
            continue                # reclamación en curso legítima (otro `reclamar()` a mitad de camino)
        clave_json = nombre[:-len(CLAIMING_SUFFIX)]           # "<clave>.json"
        dst = os.path.join(outbox_dir, clave_json)
        try:
            _mkdir_privado(outbox_dir, dir_raiz=dir_)
            if os.path.exists(dst):
                os.remove(src)                                 # ya hay uno en outbox/: el claiming sobra
            else:
                os.replace(src, dst)
            _incrementar_recuperados_claiming(dir_)
        except OSError as e:
            errores.append({"clave": clave_json[:-len(".json")], "causa": f"claiming huérfano: {e}"})


def _reclamar_huerfanos(dir_, ttl_s, claiming_ttl_s=CLAIMING_TTL_S):
    """Barre `processing/`: los items reclamados hace más de `ttl_s` (un proceso murió entre el
    claim y `completar`/`dead_letter`, gap 1 Critical de la revisión) se re-encolan SIN backoff
    (`backoff=False`: no es un fallo repetido del código, es un worker muerto) con contador de
    intentos, o van a `dead-letter/` al superar MAX_INTENTOS. Protegido con `try/except OSError`
    (gap 31 de la revisión intento 2): un `dead-letter/` inutilizable (p.ej. un fichero en vez de
    carpeta) no debe abortar el barrido — se cuenta en `errores` y el resto de la reclamación
    sigue. Además (N-1 Critical), recupera los `.claiming` huérfanos con más de `claiming_ttl_s`
    (reclamación de `reclamar()` interrumpida a medias, ver `_recuperar_claiming_huerfanos`)."""
    proc_dir = os.path.join(dir_, "processing")
    errores = []
    try:
        nombres_todos = os.listdir(proc_dir)
    except OSError:
        return errores
    _recuperar_claiming_huerfanos(dir_, proc_dir, nombres_todos, claiming_ttl_s, errores)
    nombres = [f for f in nombres_todos if f.endswith(".json") and not f.startswith(".tmp-")
               and not f.endswith((".manifest.json", ".causa.json"))]
    ahora = time.time()
    for nombre in nombres:
        src = os.path.join(proc_dir, nombre)
        claimed = _leer_claimed_at(src + CLAIMED_AT_SUFFIX)   # gap 50: respaldo si `os.utime` degradó
        if claimed is not None:
            edad = ahora - claimed
        else:
            try:
                edad = ahora - os.stat(src).st_mtime
            except OSError:
                continue
        if edad <= ttl_s:
            continue
        item = {"clave": nombre[:-len(".json")], "path": src, "payload": None}
        try:
            resultado = reencolar_o_dead_letter(item, "envelope huérfano en processing/ (proceso interrumpido)",
                                                backoff=False)
        except Exception as e:  # noqa: BLE001 — defensa extra: nada de esto debe abortar el barrido
            errores.append({"clave": item["clave"], "causa": str(e)})
            continue
        if resultado == ERROR:
            errores.append({"clave": item["clave"], "causa": "no se pudo reencolar ni mandar a dead-letter"})
    return errores


def reclamar(dir_, processing_ttl_s=PROCESSING_TTL_S, errores=None, claiming_ttl_s=CLAIMING_TTL_S):
    """Reclama UN envelope pendiente: primero re-encola/dead-letter los huérfanos de `processing/`
    (gap 1; si se pasa una lista en `errores`, se le añaden los errores del barrido — gap 52 de la
    revisión intento 3: antes `_reclamar_huerfanos` los calculaba y `reclamar` los descartaba, así
    que un envelope atascado en `processing/` era invisible en el JSON de `replay`), luego mueve
    `outbox/<clave>.json` a `processing/` EN DOS PASOS (gap 50 de la revisión intento 3):

      1. `os.replace` a un nombre TEMPORAL `<clave>.json.claiming` dentro de `processing/`.
      2. `os.utime` sobre ese temporal para refrescar el mtime a "ahora" (gap 25 Critical: el TTL de
         huérfanos se mide desde la RECLAMACIÓN, no desde la creación del envelope).
      3. `os.replace` del temporal al nombre FINAL `<clave>.json` — visible como reclamado solo
         ENTONCES, nunca antes de que el mtime esté al día.

    Si el `os.utime` del paso 2 falla (SMB/FUSE/FS sin `utime`, o un `owner` distinto), el item
    vuelve a `outbox/` SIN reclamarse (nunca queda a medias en `processing/` con un mtime heredado
    de `outbox/` que arriesgaría doble entrega): se marca `estado()["reclamacion"] = "degradada"`
    con un sentinela y se sigue con el siguiente candidato. Como respaldo adicional para el TTL de
    huérfanos (por si `os.utime` degradara de forma silenciosa en algún FS), la reclamación exitosa
    también escribe un sidecar `<clave>.json.claimed_at` con el instante real (`_reclamar_huerfanos`
    lo lee ANTES que el mtime). Los candidatos con backoff pendiente (`no_antes_de` en el futuro,
    validado y con tope por `_no_antes_de_valido`, gap 26/51) se saltan.

    La exclusividad frente a un segundo proceso concurrente la da el propio `os.replace`: el
    origen desaparece con la primera reclamación que se ejecuta, así que la segunda falla con
    `FileNotFoundError` (o `PermissionError` en Windows si el fichero ya no está) y se salta ese
    candidato. Devuelve `None` si no hay nada pendiente, si todos los candidatos listados ya fueron
    reclamados por otro proceso entre el `listdir` y el `replace`, si tienen backoff pendiente, o si
    ninguno pudo refrescar su mtime al reclamarlo. `claiming_ttl_s` (N-1 Critical) es el tope para
    recuperar un `.claiming` huérfano de una reclamación interrumpida a medias (ver
    `_recuperar_claiming_huerfanos`)."""
    barrido_errores = _reclamar_huerfanos(dir_, processing_ttl_s, claiming_ttl_s=claiming_ttl_s)
    if errores is not None:
        errores.extend(barrido_errores)
    outbox_dir = os.path.join(dir_, "outbox")
    proc_dir = os.path.join(dir_, "processing")
    try:
        nombres = sorted(f for f in os.listdir(outbox_dir) if f.endswith(".json") and not f.startswith(".tmp-")
                          and not f.endswith((".manifest.json", ".causa.json")))
    except OSError:
        return None
    if not nombres:
        return None
    ahora = time.time()
    _mkdir_privado(proc_dir, dir_raiz=dir_)
    for nombre in nombres:
        src = os.path.join(outbox_dir, nombre)
        sidecar = _leer_sidecar(src + INTENTOS_SUFFIX)
        if _no_antes_de_valido(sidecar["no_antes_de"], ahora) > ahora:
            continue                # backoff pendiente (gap 26/51): no se reclama todavía
        claiming = os.path.join(proc_dir, nombre + CLAIMING_SUFFIX)
        dst = os.path.join(proc_dir, nombre)
        try:
            os.replace(src, claiming)
        except OSError:
            continue                # ya reclamado por otro proceso: siguiente candidato
        try:
            os.utime(claiming, None)   # gap 25: TTL de huérfanos medido desde AHORA, no desde la creación
        except OSError:
            # gap 50: sin mtime fiable, el item NO se reclama — vuelve a outbox/ tal cual estaba,
            # en vez de quedar visible en processing/ con un mtime que arriesgaría doble entrega.
            with contextlib.suppress(OSError):
                os.replace(claiming, src)
            _marcar_reclamacion_degradada(dir_)
            continue
        try:
            os.replace(claiming, dst)
        except OSError:
            # N-1 (d): deshacer el paso en vez de un `continue` a secas — sin esto, el `.claiming`
            # queda varado en `processing/` donde NINGÚN barrido lo veía antes de esta corrección.
            # Si mientras tanto ya hay un envelope con ese nombre en outbox/ (carrera con otro
            # proceso que lo repuso), el `.claiming` sobrante se descarta en vez de pisarlo.
            with contextlib.suppress(OSError):
                if os.path.exists(src):
                    os.remove(claiming)
                else:
                    os.replace(claiming, src)
            continue
        with contextlib.suppress(OSError):
            _escribir_atomico(dst + CLAIMED_AT_SUFFIX, str(time.time()), dir_raiz=dir_)
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
    _mkdir_privado(dst_dir, dir_raiz=dir_)
    dst = os.path.join(dst_dir, os.path.basename(src))
    os.replace(src, dst)
    with contextlib.suppress(OSError):
        os.remove(src + INTENTOS_SUFFIX)
    with contextlib.suppress(OSError):
        os.remove(src + CLAIMED_AT_SUFFIX)
    return dst


def completar(item, manifiesto=None):
    """`processing/` -> `done/`; escribe `<ruta>.manifest.json` con `hash` (sha256 del contenido)
    y `completado_en` además de lo que traiga `manifiesto` — `completado_en` es la fecha REAL de
    materialización que usa `purgar_antiguos` (gap 33).

    El manifiesto se escribe ANTES de mover el envelope a `done/` (gap 59 de la revisión intento 3):
    si escribirlo falla (ENOSPC, permisos), la excepción se propaga con el item TODAVÍA en
    `processing/` — el llamador (`journal.py replay`) lo reencola o lo manda a dead-letter con
    normalidad. Antes, el manifiesto se escribía DESPUÉS de mover a `done/`: un fallo ahí dejaba la
    sesión YA materializada pero con `replay` reportando `materializados: 0` y el envelope varado en
    `done/` sin `completado_en` (nunca lo purga `purgar_antiguos`, que exige ese campo) — una pérdida
    de visibilidad silenciosa, no de datos.

    El manifiesto se escribe DIRECTAMENTE en su destino final `done/<clave>.json.manifest.json`
    (N-2: el fix del gap 59 lo escribía en `processing/<clave>.json.manifest.json`, un nombre que
    también casa `endswith('.json')` — un manifiesto huérfano ahí se reencolaba como un envelope más
    y `reclamar` lo devolvía con clave `<clave>.json.manifest`, una dead-letter falsa). Escribirlo
    directo en `done/` ANTES de mover el envelope elimina esa ventana: si el corte ocurre justo
    DESPUÉS del manifiesto y ANTES del `os.replace` a `done/`, el envelope simplemente sigue en
    `processing/` (nunca a medias en ninguna carpeta) y el manifiesto huérfano en `done/` es
    inofensivo — `purgar_antiguos` lo purga por su propio `completado_en` (ver más abajo), y ni
    `reclamar` ni `estado()` lo confunden con un envelope porque no viven en `outbox/`/`processing/`."""
    src = item["path"] if isinstance(item, dict) else str(item)
    dir_ = os.path.dirname(os.path.dirname(src))          # .../processing/<clave>.json -> dir_
    try:
        with open(src, "rb") as fh:
            contenido = fh.read()
    except OSError:
        contenido = b""
    man = dict(manifiesto or {})
    man.setdefault("hash", hashlib.sha256(contenido).hexdigest())
    man.setdefault("completado_en", _iso_now())
    done_dir = os.path.join(dir_, "done")
    _mkdir_privado(done_dir, dir_raiz=dir_)
    manifest_dst = os.path.join(done_dir, os.path.basename(src) + ".manifest.json")
    _escribir_atomico(manifest_dst, json.dumps(man, ensure_ascii=False, indent=2),
                       dir_raiz=dir_)                     # puede lanzar: item sigue en processing/
    return _mover_desde_processing(item, "done")


def estado(dir_):
    """Contadores de envelopes (excluye `.manifest.json`/`.causa.json`/`.intentos`) por carpeta,
    más `durabilidad` («ok» / «degradada» si algún `fsync` de esta cola falló alguna vez),
    `permisos` («ok» / «degradados» si algún `chmod` de esta cola falló alguna vez, gap 46),
    `reclamacion` («ok» / «degradada» si algún `os.utime` al reclamar falló alguna vez, gap 50),
    `en_backoff` (cuántos items de `outbox/` tienen `no_antes_de` pendiente ahora mismo, gap 51) y
    `recuperados_claiming` (cuántos `.claiming` huérfanos de `processing/` ha recuperado
    `_reclamar_huerfanos` a lo largo de la vida de esta cola, N-1 Critical)."""
    out = {}
    for sub in SUBDIRS:
        p = os.path.join(dir_, sub)
        try:
            out[sub] = len([f for f in os.listdir(p)
                            if f.endswith(".json") and not f.startswith(".tmp-")
                            and not f.endswith((".manifest.json", ".causa.json"))])
        except OSError:
            out[sub] = 0
    out["durabilidad"] = "degradada" if os.path.isfile(os.path.join(dir_, _DEGRADADO_MARKER)) else "ok"
    out["permisos"] = "degradados" if os.path.isfile(os.path.join(dir_, _PERMISOS_MARKER)) else "ok"
    out["reclamacion"] = "degradada" if os.path.isfile(os.path.join(dir_, _RECLAMACION_MARKER)) else "ok"
    out["en_backoff"], _ = en_backoff(dir_)
    out["recuperados_claiming"] = _leer_recuperados_claiming(dir_)
    return out


def _leer_completado_en(manifest_path):
    try:
        with open(manifest_path, encoding="utf-8") as fh:
            return json.load(fh).get("completado_en")
    except (OSError, ValueError):
        return None


def purgar_antiguos(dir_, sub, dias):
    """Borra ficheros de `<dir_>/<sub>/` (con sus sidecars `.manifest.json`/`.causa.json`) cuyo
    `completado_en` (del manifiesto, gap 33 de la revisión intento 2 — NO el mtime del envelope de
    creación) supera `dias` días; sin ese campo, NO se purga (mejor conservar de más que borrar una
    entrada recién materializada porque su envelope esperó semanas en la outbox). Devuelve cuántos
    se borraron. Pensado para `done/` (gap 22); nunca se llama sobre `dead-letter/` (se conserva a
    propósito) ni sobre `outbox/`/`processing/`.

    N-2: un manifiesto HUÉRFANO (sin su envelope — p.ej. un corte entre `completar()` escribiendo el
    manifiesto en `done/` y moviendo el envelope ahí) también se purga por su propio `completado_en`,
    en vez de crecer para siempre porque el bucle principal solo enumera envelopes existentes."""
    p = os.path.join(dir_, sub)
    try:
        todos = os.listdir(p)
    except OSError:
        return 0
    limite = time.time() - dias * 86400
    borrados = 0
    procesados = set()
    nombres = [f for f in todos if f.endswith(".json") and not f.startswith(".tmp-")
               and not f.endswith((".manifest.json", ".causa.json"))]
    for fn in nombres:
        procesados.add(fn)
        fp = os.path.join(p, fn)
        manifest_path = fp + ".manifest.json"
        epoch = _iso_a_epoch(_leer_completado_en(manifest_path))
        if epoch is None or epoch >= limite:
            continue                # sin `completado_en` legible, o aún dentro de la retención
        for cand in (fp, manifest_path, fp + ".causa.json"):
            with contextlib.suppress(OSError):
                os.remove(cand)
        borrados += 1
    huerfanos = [f for f in todos if f.endswith(".manifest.json")
                 and f[:-len(".manifest.json")] not in procesados]
    for fn in huerfanos:
        manifest_path = os.path.join(p, fn)
        epoch = _iso_a_epoch(_leer_completado_en(manifest_path))
        if epoch is None or epoch >= limite:
            continue
        with contextlib.suppress(OSError):
            os.remove(manifest_path)
        borrados += 1
    return borrados


def limpiar_tmp_huerfanos(dir_, ttl_s=PROCESSING_TTL_S):
    """Borra temporales huérfanos (un corte a mitad de escritura, o un fichero plantado por fuera)
    cuyo nombre EMPIEZA por `.tmp-` (gap 35: decidir por subcadena `".tmp-"` borraba en silencio
    una clave legítima como `export.tmp-2026` que la contuviera) con más de `ttl_s` en
    `outbox/`/`processing/`. Devuelve cuántos se borraron."""
    borrados = 0
    limite = time.time() - ttl_s
    for sub in ("outbox", "processing"):
        p = os.path.join(dir_, sub)
        try:
            nombres = os.listdir(p)
        except OSError:
            continue
        for fn in nombres:
            if not fn.startswith(".tmp-"):
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
