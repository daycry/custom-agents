#!/usr/bin/env python3
"""
case-recorder.py — recorder determinista de casos de `training-data-services` (design.md O1).

Graba cada intento del proyecto como una VERSION inmutable del case store, en el `root` que declara
`.claude/knowledge-services/training.json` (fuera de Git y de `docs/knowledge/`, ADR-019). Opt-in:
sin config, o con `enabled: false`, se niega a grabar y no escribe nada (CA-01). El plugin valida
FORMA, nunca dominio (CA-04): las metricas llegan ya calculadas por el proyecto.

`grabar(caso, config, raiz_proyecto, approved_by_human=False)`, en este orden:
  1. redacta secretos de `request`, `context`, `constraints` y `trajectory` con
     `agent-kits/shared/redact.py` (fuente unica; sin el -> `RedaccionNoDisponible`, CA-09);
  2. valida el caso YA redactado con `case_schema.validar_caso` (con la config del proyecto);
  3. solo entonces escribe. Si algo falla antes, no se toca disco.
  - Sin `version`, se asigna la siguiente libre (mayor existente + 1); con `version` que ya
    existe -> rechazo: nunca sobrescribe (CA-02). La reserva es atomica tambien con recorders
    concurrentes: se escribe en un directorio temporal hermano (`.tmp-*`) y la version se reserva
    con `os.mkdir` del destino, que falla si existe (nunca `rename` de directorio, que en POSIX
    sustituye un directorio vacio). `metadata.json` se mueve el ULTIMO: una version sin el esta a
    medio escribir.
  - Un caso no nace `approved` (Gold) por `record` salvo con `approved_by_human=True`
    (`--approved-by-human`): la misma puerta que `set-status`, sin puerta trasera.
  - `corrected` + `supersedes_case`: la version citada debe existir en el store (CA-12).
  - Sin `validation`, el caso nace `pending`. Sin `case_id`, se construye con la config.
  - No hay operacion de borrado: rechazados y fallidos se conservan (CA-02).

`cambiar_estado(case_id, version, status, config, raiz_proyecto, approved_by_human=False,
reviewer_note=None)` — puerta humana para Gold (T-05): `approved` exige `approved_by_human=True`
(`--approved-by-human`) y fija `approved_by_human: true` + `approved_at`; sin el flag, rechazo
explicito. `needs_changes`/`rejected`/`pending` no lo requieren y dejan `approved_by_human: false`.
Solo se reescribe `validation.json` (temporal + `os.replace`); el resto de la version es inmutable.

Indice `<root>/cases_index.jsonl` (T-06): append-only, una linea por alta y por cambio de estado
con las claves exactas `case_id, version, family, variant, status, outcome, updated_at`; vale la
ultima por `(case_id, version)`. Es una CACHE: `index rebuild` lo reconstruye desde `cases/` y
`index check` lo compara. Las lineas corruptas se ignoran con aviso (y `check` las reporta). Los
escritores se excluyen con un bloqueo sobre `<root>/.cases_index.lock` (`flock`/`msvcrt`).

Estructura (`case_schema.directorio_version`, ancho `ids.version_width`):
  <root>/cases/<family>.<variant>/v<NNN>/{metadata.json, request.json ({"request": ...}),
  context.json, constraints.json, trajectory.jsonl, metrics.json, validation.json,
  final/artifacts.json}  — JSON UTF-8 sin escapar (`ensure_ascii=False`), fin de linea LF.

Uso (exit 0 ok · 1 rechazo/validacion · 2 uso/JSON ilegible, como `case_schema.py`):
  case-recorder.py record <caso.json> [--config <training.json>] [--project-root <dir>] [--approved-by-human]
  case-recorder.py set-status <case_id> <version> <status> [--approved-by-human] [--note <texto>] [...]
  case-recorder.py index {rebuild|check} [...]     # check: exit 1 si el indice difiere de cases/
  case-recorder.py list [--status S] [--family F] [--outcome O] [--json] [...]
"""
import argparse
import datetime
import importlib.util
import json
import os
import sys
import tempfile

# Consola no UTF-8 (Windows cp1252) o tuberias: reconfigurar ANTES de leer/imprimir (GOT-005).
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure, ya leido o None (capsys, pythonw)

HERE = os.path.dirname(os.path.abspath(__file__))

CAMPOS_REDACTADOS = ("request", "context", "constraints", "trajectory")
MENSAJE_GOLD = "approved exige --approved-by-human: Gold es siempre una accion humana"
PREFIJO_TEMPORAL = ".tmp-"
DIGITOS = "0123456789"


def _cargar_schema():
    """`case_schema.py` de la MISMA skill (fuente unica del esquema, de los ids y de las rutas)."""
    spec = importlib.util.spec_from_file_location("tds_case_schema", os.path.join(HERE, "case_schema.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


cs = _cargar_schema()


class RedaccionNoDisponible(RuntimeError):
    """`agent-kits/shared/redact.py` no se encuentra: no se puede grabar ningun caso."""


class Rechazo(Exception):
    """El recorder se niega a escribir. `errores` es una lista `{campo, mensaje}`."""

    def __init__(self, mensaje, errores=None):
        self.mensaje = mensaje
        self.errores = list(errores) if errores else [{"campo": "(caso)", "mensaje": mensaje}]
        detalle = "; ".join(f"{e['campo']}: {e['mensaje']}" for e in errores) if errores else ""
        super().__init__(f"{mensaje}: {detalle}" if detalle else mensaje)


class _EntradaIlegible(Exception):
    """JSON de entrada ilegible o ausente (exit 2)."""


# ------------------------------------------------------------------ redaccion (T-02)

def _dirs_redact():
    """Donde buscar `redact.py`: el arbol del plugin (skills/ y agent-kits/ son hermanos, en el repo
    y en la instalacion) y, si el runtime lo exporta, `CLAUDE_PLUGIN_ROOT`."""
    dirs = [os.path.normpath(os.path.join(HERE, "..", "..", "..", "agent-kits", "shared"))]
    raiz = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if raiz:
        dirs.append(os.path.join(raiz, "agent-kits", "shared"))
    return dirs


def cargar_redact(dirs=None):
    """Carga `redact.py` desde el primer directorio de `dirs` que lo contenga."""
    for d in dirs if dirs is not None else _dirs_redact():
        ruta = os.path.join(d, "redact.py")
        if os.path.isfile(ruta):
            spec = importlib.util.spec_from_file_location("tds_redact", ruta)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod
    raise RedaccionNoDisponible(
        "no se encuentra agent-kits/shared/redact.py (fuente unica de la redaccion de secretos); "
        "reinstala el plugin completo: el recorder no graba casos sin redactar")


_REDACT = None


def _redact_mod():
    """`redact.py` cargado la PRIMERA vez que se redacta (gap #8): importar este modulo nunca
    falla por su ausencia; redactar (y por tanto grabar) si, con `RedaccionNoDisponible`."""
    global _REDACT
    if _REDACT is None:
        _REDACT = cargar_redact()
    return _REDACT


def __getattr__(nombre):
    """`redactar`/`REDACTADO` son los de `redact.py` (mismo objeto, no una copia), resueltos
    perezosamente (PEP 562)."""
    if nombre in ("redactar", "REDACTADO"):
        return getattr(_redact_mod(), nombre)
    raise AttributeError(f"module {__name__!r} has no attribute {nombre!r}")


def redactar_estructura(valor):
    """Copia de `valor` con la redaccion de `redact.py` aplicada a cada cadena: valores y CLAVES
    textuales de dicts, elementos de listas, tuplas, sets y frozensets (recursivo, gap #8). Lo no
    textual no se toca; la entrada no muta. Sin `redact.py` -> `RedaccionNoDisponible`.

    Claves (fix2, gap #18): si dos claves distintas se redactan al mismo literal, la segunda y
    siguientes llevan un sufijo estable por orden de aparicion (`<clave redactada> #2`, `#3`...), y
    una clave que NO cambia al redactar conserva siempre su nombre: nunca se pierde un valor. Una
    namedtuple se reconstruye con `_make` (mismo tipo y campos)."""
    redactar_txt = _redact_mod().redactar

    def _dict(v):
        nuevas = {k: (redactar_txt(k) if isinstance(k, str) else k) for k in v}
        intactas = {k for k, n in nuevas.items() if n == k}
        out = {}
        for k, x in v.items():
            nombre = nuevas[k]
            if k not in intactas:
                n = 1
                while nombre in out or nombre in intactas:
                    n += 1
                    nombre = f"{nuevas[k]} #{n}"
            out[nombre] = _rec(x)
        return out

    def _rec(v):
        if isinstance(v, str):
            return redactar_txt(v)
        if isinstance(v, dict):
            return _dict(v)
        if isinstance(v, tuple) and hasattr(type(v), "_make"):
            return type(v)._make(_rec(x) for x in v)
        if isinstance(v, (list, tuple, set, frozenset)):
            return type(v)(_rec(x) for x in v)
        return v

    return _rec(valor)


# ------------------------------------------------------------------ config y rutas

def _ahora():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def config_activa(config, raiz_proyecto=None):
    """Comprueba que la capacidad esta configurada, es valida y esta activada; si no, `Rechazo`
    (nunca se escribe nada con la capacidad apagada, CA-01)."""
    if config is None:
        raise Rechazo("training-data-services no esta configurado: falta .claude/knowledge-services/"
                      "training.json (opt-in); no se escribe nada")
    errores = cs.validar_config(config, raiz_proyecto)
    if errores:
        raise Rechazo("training.json invalido; no se escribe nada", errores)
    if config.get("enabled") is not True:
        raise Rechazo("training-data-services desactivado (enabled: false en training.json); no se escribe nada")


def raiz_store(config, raiz_proyecto=None):
    """Ruta absoluta del case store: `root` de la config, relativo a la raiz del proyecto."""
    return os.path.abspath(os.path.join(raiz_proyecto or ".", config["root"]))


def _es_version(nombre):
    return len(nombre) > 1 and nombre[0] == "v" and all(c in DIGITOS for c in nombre[1:])


def versiones(dir_caso):
    """Versiones (enteros) presentes en `cases/<family>.<variant>/`, completas o no."""
    try:
        nombres = os.listdir(dir_caso)
    except OSError:
        return []
    return sorted(int(n[1:]) for n in nombres if _es_version(n) and os.path.isdir(os.path.join(dir_caso, n)))


def _siguiente_version(dir_caso):
    vs = versiones(dir_caso)
    return (vs[-1] + 1) if vs else 1


def _nombre_version(version, width):
    return os.path.basename(cs.directorio_version("x", "y", version, width))


# ------------------------------------------------------------------ escritura

def _json_bytes(obj):
    return (json.dumps(obj, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _ficheros_de(caso):
    """Contenido (bytes) de cada fichero de la version salvo `metadata.json` (se escribe el ultimo,
    ya con la version reservada)."""
    val = caso["validation"]
    return {
        "request.json": _json_bytes({"request": caso["request"]}),
        "context.json": _json_bytes(caso.get("context", {})),
        "constraints.json": _json_bytes(caso.get("constraints", {})),
        "trajectory.jsonl": "".join(json.dumps(t, ensure_ascii=False) + "\n" for t in caso["trajectory"]).encode("utf-8"),
        "metrics.json": _json_bytes(caso.get("metrics", {})),
        "validation.json": _json_bytes({"status": val["status"], "approved_by_human": val.get("approved_by_human", False),
                                        "approved_at": val.get("approved_at"), "reviewer_note": val.get("reviewer_note")}),
        os.path.join("final", "artifacts.json"): _json_bytes(caso.get("artifacts", [])),
    }


def _metadata(caso):
    meta = {k: caso[k] for k in ("case_id", "family", "variant", "version")}
    meta["created_at"] = caso.get("created_at") or _ahora()
    meta["outcome"] = caso["outcome"]
    if caso.get("supersedes_case") is not None:
        meta["supersedes_case"] = caso["supersedes_case"]
    return meta


def _escribir(ruta, datos):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "wb") as f:
        f.write(datos)


def _reemplazar(origen, destino):
    """`os.replace` con reintentos acotados SOLO ante `PermissionError`: en Windows un handle ajeno
    (antivirus, indexador) puede bloquear un instante el fichero recien escrito."""
    import time
    for intento in range(40):
        try:
            return os.replace(origen, destino)
        except PermissionError:
            if intento == 39:
                raise
            time.sleep(0.025)


def _limpiar_temporal(tmp):
    """Elimina SOLO el temporal propio (`.tmp-*`, fichero o directorio con lo que quede dentro):
    nunca una version. Si ya no existe (se movio a su destino), no hace nada."""
    if not os.path.basename(tmp).startswith(PREFIJO_TEMPORAL) or not os.path.lexists(tmp):
        return
    if not os.path.isdir(tmp):
        try: os.remove(tmp)
        except OSError: pass
        return
    for base, dirs, fs in os.walk(tmp, topdown=False):
        for f in fs:
            try: os.remove(os.path.join(base, f))
            except OSError: pass
        for d in dirs:
            try: os.rmdir(os.path.join(base, d))
            except OSError: pass
    try: os.rmdir(tmp)
    except OSError: pass


def _reservar_y_mover(dir_caso, caso, width, auto):
    """Escribe en `.tmp-*` hermano, reserva `v<NNN>` con `os.mkdir` (falla si existe: nadie pisa a
    nadie) y mueve los ficheros; `metadata.json` el ultimo. Devuelve la ruta de la version."""
    os.makedirs(dir_caso, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix=PREFIJO_TEMPORAL, dir=dir_caso)
    try:
        ficheros = _ficheros_de(caso)
        for rel, datos in ficheros.items():
            _escribir(os.path.join(tmp, rel), datos)
        version = caso["version"]
        while True:
            destino = os.path.join(dir_caso, _nombre_version(version, width))
            try:
                os.mkdir(destino)
                break
            except FileExistsError:
                if not auto:
                    raise Rechazo(f"{cs.referencia_version(caso['case_id'], version, width)} ya existe: el recorder "
                                  "nunca sobrescribe una version (graba sin `version` para la siguiente libre)")
                version = max(version + 1, _siguiente_version(dir_caso))
        caso["version"] = version
        os.mkdir(os.path.join(destino, "final"))
        for rel in ficheros:
            _reemplazar(os.path.join(tmp, rel), os.path.join(destino, rel))
        _escribir(os.path.join(tmp, "metadata.json"), _json_bytes(_metadata(caso)))
        _reemplazar(os.path.join(tmp, "metadata.json"), os.path.join(destino, "metadata.json"))
        return destino
    finally:
        _limpiar_temporal(tmp)


def _comprobar_supersedes(caso, dir_caso, width):
    """CA-12: la version que corrige un `corrected` debe existir (se conserva junto a la correccion)."""
    sup = caso.get("supersedes_case")
    if sup is None:
        return
    m = cs.PATRON_REFERENCIA.fullmatch(sup)
    citada = os.path.join(dir_caso, _nombre_version(int(m.group(2)), width), "metadata.json")
    if not os.path.isfile(citada):
        raise Rechazo("caso invalido: no se escribe nada", [{
            "campo": "supersedes_case",
            "mensaje": f"`{sup}` no existe en el case store: un `corrected` solo corrige una version grabada"}])


def grabar(caso, config, raiz_proyecto=None, approved_by_human=False):
    """Graba `caso` como una version nueva. Devuelve `{case_id, version, ref, path}`; `Rechazo` si
    la capacidad esta apagada o el caso no vale, `RedaccionNoDisponible` sin `redact.py`. En ambos
    casos no se escribe nada."""
    config_activa(config, raiz_proyecto)
    if not isinstance(caso, dict):
        raise Rechazo("caso invalido: no se escribe nada", cs.validar_caso(caso, config))
    caso = dict(caso)
    for campo in CAMPOS_REDACTADOS:                       # 1. redactar
        if campo in caso:
            caso[campo] = redactar_estructura(caso[campo])

    val = caso.get("validation")
    if val is None:
        caso["validation"] = {"status": "pending", "approved_by_human": False}
    elif isinstance(val, dict) and val.get("status") == "approved":
        if not approved_by_human:
            raise Rechazo(MENSAJE_GOLD)
        caso["validation"] = dict(val, approved_by_human=True, approved_at=val.get("approved_at") or _ahora())
    fam, var = caso.get("family"), caso.get("variant")
    if "case_id" not in caso and isinstance(fam, str) and isinstance(var, str):
        caso["case_id"] = cs.construir_case_id(config.get("id_prefix"), fam, var)

    width = cs.patrones_id(config)[2]
    store = raiz_store(config, raiz_proyecto)
    auto = "version" not in caso
    if auto:
        try:
            dir_caso = os.path.join(store, os.path.dirname(cs.directorio_version(fam, var, 1, width)))
            caso["version"] = _siguiente_version(dir_caso)
        except (ValueError, TypeError):
            caso["version"] = 1                              # el validador dira que falla

    errores = cs.validar_caso(caso, config)               # 2. validar lo YA redactado
    if errores:
        raise Rechazo("caso invalido: no se escribe nada", errores)
    dir_caso = os.path.join(store, os.path.dirname(cs.directorio_version(fam, var, caso["version"], width)))
    _comprobar_supersedes(caso, dir_caso, width)
    destino = _reservar_y_mover(dir_caso, caso, width, auto)  # 3. escribir
    return {"case_id": caso["case_id"], "version": caso["version"],
            "ref": cs.referencia_version(caso["case_id"], caso["version"], width), "path": destino,
            "avisos": _indexar(store, _entrada(caso, caso["validation"]["status"], _ahora()))}


# ------------------------------------------------------------------ indice cases_index.jsonl (T-06)

INDICE = "cases_index.jsonl"
BLOQUEO_INDICE = ".cases_index.lock"
CLAVES_INDICE = ("case_id", "version", "family", "variant", "status", "outcome", "updated_at")
ESPERA_BLOQUEO_S = 10.0


class _Bloqueo:
    """Exclusion mutua entre recorders (hilos o procesos) al escribir el indice: `flock` en POSIX,
    `msvcrt.locking` en Windows, sobre `<root>/.cases_index.lock` (fichero que no se borra). El
    append de Windows no es atomico entre descriptores distintos. Si no se obtiene en
    `ESPERA_BLOQUEO_S`, se sigue sin el: el indice es una cache y `index check` lo detectaria."""

    def __init__(self, store):
        self.ruta = os.path.join(store, BLOQUEO_INDICE)
        self.f = None

    def __enter__(self):
        import time
        os.makedirs(os.path.dirname(self.ruta), exist_ok=True)
        self.f = open(self.ruta, "a+b")
        limite = time.monotonic() + ESPERA_BLOQUEO_S
        while True:
            try:
                if os.name == "nt":
                    import msvcrt
                    self.f.seek(0)
                    msvcrt.locking(self.f.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(self.f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                self.tomado = True
                return self
            except OSError:
                if time.monotonic() >= limite:
                    self.tomado = False
                    return self
                time.sleep(0.005)

    def __exit__(self, *_exc):
        try:
            if self.tomado:
                if os.name == "nt":
                    import msvcrt
                    self.f.seek(0)
                    msvcrt.locking(self.f.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(self.f.fileno(), fcntl.LOCK_UN)
        finally:
            self.f.close()
        return False


def _entrada(meta, status, updated_at):
    return {"case_id": meta["case_id"], "version": meta["version"], "family": meta["family"],
            "variant": meta["variant"], "status": status, "outcome": meta["outcome"], "updated_at": updated_at}


def _linea(entrada):
    return (json.dumps(entrada, ensure_ascii=False) + "\n").encode("utf-8")


def anadir_al_indice(store, entrada):
    """Una linea al final de `cases_index.jsonl` (append-only; nunca reescribe lo anterior)."""
    with _Bloqueo(store):
        with open(os.path.join(store, INDICE), "ab") as f:
            f.write(_linea(entrada))


def _indexar(store, entrada):
    """Anade la linea del cambio; si el indice no se puede escribir, la version YA esta grabada:
    se devuelve un aviso (el indice es una cache: `index rebuild` lo repone) en vez de fallar."""
    try:
        anadir_al_indice(store, entrada)
        return []
    except OSError as e:
        return [f"{INDICE} no actualizado ({e}); reponlo con `index rebuild`"]


def _entrada_valida(e):
    """Motivo por el que una linea del indice no vale, o None."""
    if not isinstance(e, dict):
        return "no es un objeto JSON"
    if tuple(sorted(e)) != tuple(sorted(CLAVES_INDICE)):
        return f"claves distintas de {', '.join(CLAVES_INDICE)}"
    if not all(isinstance(e[k], str) for k in CLAVES_INDICE if k != "version"):
        return "valores de texto esperados"
    if not cs._es_int(e["version"]) or e["version"] < 1:
        return "version debe ser entero >= 1"
    if e["status"] not in cs.VALIDATION_STATUS or e["outcome"] not in cs.OUTCOMES:
        return "status/outcome fuera del vocabulario cerrado"
    return None


def leer_indice(store):
    """`(entradas, avisos)`: la ULTIMA linea valida por `(case_id, version)` (orden de aparicion) y
    un aviso por cada linea corrupta, que se ignora (nunca rompe la lectura)."""
    entradas, avisos = {}, []
    ruta = os.path.join(store, INDICE)
    try:
        with open(ruta, "rb") as f:
            crudas = f.read().split(b"\n")
    except FileNotFoundError:
        return entradas, avisos
    except OSError as e:
        return entradas, [f"{INDICE} ilegible: {e}"]
    for n, cruda in enumerate(crudas, 1):
        if not cruda.strip():
            continue
        try:
            e = json.loads(cruda.decode("utf-8"))
            motivo = _entrada_valida(e)
        except RecursionError:
            motivo = "anidamiento excesivo"
        except (ValueError, UnicodeDecodeError):
            motivo = "JSON ilegible"
        if motivo:
            avisos.append(f"{INDICE} linea {n} ignorada: {motivo}")
            continue
        entradas[(e["case_id"], e["version"])] = e
    return entradas, avisos


def _mtime_iso(ruta):
    t = datetime.datetime.fromtimestamp(os.path.getmtime(ruta), datetime.timezone.utc)
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def estado_de_cases(store):
    """`(entradas, avisos)` recorriendo `cases/` (la FUENTE; el indice es cache). Las versiones a
    medio escribir (sin `metadata.json`/`validation.json`) o incoherentes con su ruta se omiten
    con aviso. `updated_at` = mtime de `validation.json`."""
    entradas, avisos = {}, []
    base = os.path.join(store, "cases")
    try:
        casos = sorted(os.listdir(base))
    except OSError:
        return entradas, avisos
    for nombre in casos:
        dir_caso = os.path.join(base, nombre)
        if not os.path.isdir(dir_caso) or nombre.startswith("."):
            continue
        for n in sorted(os.listdir(dir_caso)):
            dir_v = os.path.join(dir_caso, n)
            if _es_version(n) and os.path.isdir(dir_v):
                v = int(n[1:])
                rel = os.path.relpath(dir_v, store).replace(os.sep, "/")
                try:
                    with open(os.path.join(dir_v, "metadata.json"), encoding="utf-8") as f:
                        meta = json.load(f)
                    with open(os.path.join(dir_v, "validation.json"), encoding="utf-8") as f:
                        val = json.load(f)
                except (OSError, ValueError, RecursionError):
                    avisos.append(f"{rel} omitida: a medio escribir o ilegible (sin metadata.json/validation.json validos)")
                    continue
                try:
                    e = _entrada(meta, val.get("status"), _mtime_iso(os.path.join(dir_v, "validation.json")))
                except (AttributeError, KeyError, TypeError):
                    avisos.append(f"{rel} omitida: metadata.json/validation.json incompletos")
                    continue
                if f"{e['family']}.{e['variant']}" != nombre or e["version"] != v or _entrada_valida(e):
                    avisos.append(f"{rel} omitida: metadata.json no casa con su ruta o con el esquema")
                    continue
                entradas[(e["case_id"], e["version"])] = e
    return entradas, avisos


def reconstruir_indice(store):
    """Reescribe `cases_index.jsonl` desde `cases/` (una linea por version, ordenadas). Conserva el
    `updated_at` de la ultima linea valida si su estado coincide. Escritura atomica. Devuelve
    `(n_versiones, avisos)`."""
    fuente, avisos = estado_de_cases(store)
    previas, _ = leer_indice(store)
    lineas = []
    for clave in sorted(fuente, key=lambda k: (fuente[k]["family"], fuente[k]["variant"], k[1])):
        e = dict(fuente[clave])
        p = previas.get(clave)
        if p and all(p[k] == e[k] for k in CLAVES_INDICE if k != "updated_at"):
            e["updated_at"] = p["updated_at"]
        lineas.append(_linea(e))
    os.makedirs(store, exist_ok=True)
    with _Bloqueo(store):
        _escribir_atomico(os.path.join(store, INDICE), b"".join(lineas))
    return len(lineas), avisos


def comprobar_indice(store, width=cs.VERSION_WIDTH_DEFECTO):
    """Diferencias entre el indice y `cases/` (lista vacia = coherente), lineas corruptas incluidas."""
    fuente, _ = estado_de_cases(store)
    indice, avisos = leer_indice(store)
    difs = list(avisos)
    for clave in sorted(set(fuente) | set(indice), key=lambda k: (k[0], k[1])):
        ref = cs.referencia_version(clave[0], clave[1], width)
        if clave not in indice:
            difs.append(f"{ref}: esta en cases/ pero no en el indice")
        elif clave not in fuente:
            difs.append(f"{ref}: esta en el indice pero no en cases/")
        else:
            for k in CLAVES_INDICE:
                if k != "updated_at" and fuente[clave][k] != indice[clave][k]:
                    difs.append(f"{ref}: {k} es `{indice[clave][k]}` en el indice y `{fuente[clave][k]}` en cases/")
    return difs


def listar(store, status=None, family=None, outcome=None):
    """Entradas del indice (ultima por version) filtradas, ordenadas por `case_id` y version."""
    entradas, _ = leer_indice(store)
    out = [e for e in entradas.values()
           if (status is None or e["status"] == status) and (family is None or e["family"] == family)
           and (outcome is None or e["outcome"] == outcome)]
    return sorted(out, key=lambda e: (e["case_id"], e["version"]))


# ------------------------------------------------------------------ puerta humana para Gold (T-05)

def _version_int(version):
    """`1`, `"1"` o `"v001"` -> 1; otra cosa -> `Rechazo`."""
    if isinstance(version, bool):
        version = None
    if isinstance(version, str):
        texto = version[1:] if version[:1] == "v" else version
        version = int(texto) if texto and all(c in DIGITOS for c in texto) else None
    if not isinstance(version, int) or version < 1:
        raise Rechazo("version invalida", [{"campo": "version", "mensaje": "entero >= 1 (`1` o `v001`)"}])
    return version


def _family_variant(case_id, config):
    """`(family, variant)` de `<id_prefix>-<family>.<variant>`; `Rechazo` si no encaja o si no
    es un componente de ruta seguro (nunca se sale de `cases/`)."""
    prefijo = config.get("id_prefix")
    base = case_id[len(prefijo) + 1:] if isinstance(case_id, str) and prefijo and case_id.startswith(prefijo + "-") else None
    partes = base.split(".") if base else []
    if len(partes) != 2:
        raise Rechazo("case_id invalido", [{"campo": "case_id",
                                            "mensaje": f"debe ser `{prefijo}-<family>.<variant>` (id_prefix de training.json)"}])
    try:
        cs.directorio_version(partes[0], partes[1], 1)
    except ValueError as e:
        raise Rechazo("case_id invalido", [{"campo": "case_id", "mensaje": str(e)}]) from None
    return partes[0], partes[1]


def _escribir_atomico(ruta, datos):
    """Temporal en el MISMO directorio + `os.replace`: o queda el fichero viejo o el nuevo entero."""
    fd, tmp = tempfile.mkstemp(prefix=PREFIJO_TEMPORAL, dir=os.path.dirname(ruta))
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(datos)
        _reemplazar(tmp, ruta)
    finally:
        _limpiar_temporal(tmp)


def cambiar_estado(case_id, version, status, config, raiz_proyecto=None, approved_by_human=False, reviewer_note=None):
    """Cambia `validation.status` de una version grabada. Solo reescribe `validation.json` (de forma
    atomica); el resto de la version es inmutable. `approved` (Gold) exige `approved_by_human=True`
    (`--approved-by-human`): sin el, `Rechazo` con mensaje explicito. `needs_changes`, `rejected` y
    `pending` no lo requieren y dejan `approved_by_human: false`. Sin `reviewer_note` se conserva
    la nota anterior. Devuelve `{case_id, version, ref, status, path}`."""
    config_activa(config, raiz_proyecto)
    if status not in cs.VALIDATION_STATUS:
        raise Rechazo("estado invalido", [{"campo": "status", "mensaje": f"uno de {', '.join(cs.VALIDATION_STATUS)}"}])
    if status == "approved" and approved_by_human is not True:
        raise Rechazo(MENSAJE_GOLD)
    if reviewer_note is not None and not isinstance(reviewer_note, str):
        raise Rechazo("nota invalida", [{"campo": "reviewer_note", "mensaje": "debe ser texto"}])
    version = _version_int(version)
    family, variant = _family_variant(case_id, config)
    width = cs.patrones_id(config)[2]
    ref = cs.referencia_version(case_id, version, width)
    destino = os.path.join(raiz_store(config, raiz_proyecto), cs.directorio_version(family, variant, version, width))
    ruta_meta, ruta_val = os.path.join(destino, "metadata.json"), os.path.join(destino, "validation.json")
    if not (os.path.isfile(ruta_meta) and os.path.isfile(ruta_val)):
        raise Rechazo(f"{ref} no existe en el case store (o esta a medio escribir)")
    try:
        with open(ruta_meta, encoding="utf-8") as f:
            meta = json.load(f)
        with open(ruta_val, encoding="utf-8") as f:
            previa = json.load(f)
    except (OSError, ValueError, RecursionError) as e:
        raise Rechazo(f"{ref}: metadata.json/validation.json ilegibles: {e}") from None
    if not isinstance(meta, dict) or meta.get("case_id") != case_id:
        raise Rechazo(f"{ref}: metadata.json no corresponde a `{case_id}`")
    previa = previa if isinstance(previa, dict) else {}
    gold = status == "approved"
    nueva = {"status": status, "approved_by_human": gold, "approved_at": _ahora() if gold else None,
             "reviewer_note": reviewer_note if reviewer_note is not None else previa.get("reviewer_note")}
    _escribir_atomico(ruta_val, _json_bytes(nueva))
    return {"case_id": case_id, "version": version, "ref": ref, "status": status, "path": destino,
            "avisos": _indexar(raiz_store(config, raiz_proyecto), _entrada(meta, status, _ahora()))}


# ------------------------------------------------------------------ CLI

def _leer_json(ruta):
    try:
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)
    except RecursionError:
        raise _EntradaIlegible(f"{ruta}: {cs.ANIDAMIENTO_JSON}") from None
    except (OSError, ValueError) as e:
        raise _EntradaIlegible(f"{ruta}: JSON ilegible o fichero ausente: {e}") from None


def _config_cli(args):
    """`(config|None, raiz_proyecto)`: `--config` explicito (raiz deducida de su ruta o
    `--project-root`) o el `training.json` del proyecto (`--project-root` o cwd)."""
    if args.config:
        return _leer_json(args.config), cs._raiz_de(args.config, args.project_root)
    raiz = args.project_root or os.getcwd()
    cfg, ruta, errores = cs.cargar_config(raiz)
    if errores and any(e["campo"] == "(fichero)" for e in errores):
        raise _EntradaIlegible(f"{ruta}: {errores[0]['mensaje']}")
    if errores:
        raise Rechazo("training.json invalido; no se escribe nada", errores)
    return cfg, raiz


def _avisar(avisos):
    for a in avisos:
        print(f"aviso: {a}", file=sys.stderr)


def _comunes(p):
    p.add_argument("--config", help="training.json del proyecto (default: <project-root>/.claude/knowledge-services/training.json)")
    p.add_argument("--project-root", help="raiz del proyecto (default: deducida de --config o cwd)")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Recorder determinista de casos (training-data-services).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_rec = sub.add_parser("record", help="graba un caso como version nueva (nunca sobrescribe)")
    p_rec.add_argument("fichero", help="caso en JSON (el formato de case_schema.py)")
    p_rec.add_argument("--approved-by-human", action="store_true",
                       help="confirmacion HUMANA explicita para grabar un caso ya `approved` (Gold)")
    _comunes(p_rec)
    p_st = sub.add_parser("set-status", help="cambia validation.status; `approved` (Gold) exige --approved-by-human")
    p_st.add_argument("case_id")
    p_st.add_argument("version", help="`1` o `v001`")
    p_st.add_argument("status", choices=cs.VALIDATION_STATUS)
    p_st.add_argument("--approved-by-human", action="store_true",
                      help="confirmacion HUMANA explicita: la unica forma de marcar Gold")
    p_st.add_argument("--note", help="reviewer_note (sin ella se conserva la anterior)")
    _comunes(p_st)
    p_ix = sub.add_parser("index", help="indice cases_index.jsonl (cache): rebuild lo reconstruye desde cases/, check lo compara")
    p_ix.add_argument("accion", choices=("rebuild", "check"))
    _comunes(p_ix)
    p_ls = sub.add_parser("list", help="lista las versiones del indice (ultima linea por version)")
    p_ls.add_argument("--status", choices=cs.VALIDATION_STATUS)
    p_ls.add_argument("--family")
    p_ls.add_argument("--outcome", choices=cs.OUTCOMES)
    p_ls.add_argument("--json", action="store_true", help="salida JSON (lista de lineas del indice)")
    _comunes(p_ls)
    args = ap.parse_args(argv)
    try:
        config, raiz = _config_cli(args)
        if args.cmd == "record":
            caso = _leer_json(args.fichero)
            r = grabar(caso, config, raiz, approved_by_human=args.approved_by_human)
            _avisar(r["avisos"])
            print(json.dumps(r, ensure_ascii=False))
            return 0
        if args.cmd == "set-status":
            r = cambiar_estado(args.case_id, args.version, args.status, config, raiz,
                               approved_by_human=args.approved_by_human, reviewer_note=args.note)
            _avisar(r["avisos"])
            print(f"OK {r['ref']}: {r['status']}")
            return 0
        config_activa(config, raiz)
        store, width = raiz_store(config, raiz), cs.patrones_id(config)[2]
        if args.cmd == "index" and args.accion == "rebuild":
            n, avisos = reconstruir_indice(store)
            _avisar(avisos)
            print(f"OK {INDICE} reconstruido desde cases/: {n} version(es)")
            return 0
        if args.cmd == "index":
            difs = comprobar_indice(store, width)
            if difs:
                for d in difs:
                    print(f"{INDICE}: {d}")
                print(f"{len(difs)} diferencia(s): reconstruye con `index rebuild`", file=sys.stderr)
                return 1
            print(f"OK {INDICE} coherente con cases/")
            return 0
        entradas = listar(store, status=args.status, family=args.family, outcome=args.outcome)
        _avisar(leer_indice(store)[1])
        if args.json:
            print(json.dumps(entradas, ensure_ascii=False))
        for e in entradas if not args.json else ():
            print(f"{cs.referencia_version(e['case_id'], e['version'], width)}  {e['status']}  {e['outcome']}  {e['updated_at']}")
        return 0
    except _EntradaIlegible as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    except Rechazo as e:
        print(f"rechazado: {e.mensaje}", file=sys.stderr)
        for err in e.errores:
            print(f"  {err['campo']}: {err['mensaje']}", file=sys.stderr)
        return 1
    except RedaccionNoDisponible as e:
        print(f"rechazado: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
