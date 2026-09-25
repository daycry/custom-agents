#!/usr/bin/env python3
"""
case-recorder.py — recorder determinista de casos de `training-data-services` (design.md O1).

Graba cada intento del proyecto como una VERSION inmutable del case store, en el `root` que declara
`.claude/knowledge-services/training.json` (fuera de Git y de `docs/knowledge/`, ADR-019). Opt-in:
sin config, o con `enabled: false`, se niega a grabar y no escribe nada (CA-01). El plugin valida
FORMA, nunca dominio (CA-04): las metricas llegan ya calculadas por el proyecto.

`grabar(caso, config, raiz_proyecto, approved_by_human=False)`, en este orden:
  1. valida el caso ORIGINAL con `case_schema.validar_caso` (forma y chain-of-thought) y rechaza
     `NaN`/`Infinity` (no son JSON estandar);
  2. redacta con `agent-kits/shared/redact.py` (fuente unica; sin el -> `RedaccionNoDisponible`,
     CA-09) TODO el texto libre que se escribe: `request`, `context`, `constraints`, `trajectory`
     (un `arguments` en texto JSON se redacta como estructura: parsear -> redactar -> reserializar),
     las cadenas de `metrics`, `created_at`, `artifacts[]` salvo `hash`, y `validation.reviewer_note`
     / `approved_at`. Quedan SIN redactar solo los campos de forma cerrada que valida el esquema:
     `case_id`, `family`, `variant`, `version`, `outcome`, `supersedes_case`, `validation.status`,
     `validation.approved_by_human` y `artifacts[].hash`;
  3. valida el caso YA redactado (basta que falle uno de los dos para rechazar);
  4. solo entonces escribe, con el bloqueo del store tomado. Si algo falla antes, no se toca disco.
  - Sin `version`, se asigna la siguiente libre (mayor existente + 1, sea cual sea el ancho del
    directorio); con `version` que ya existe (con cualquier ancho) -> rechazo: nunca sobrescribe
    (CA-02). La version se reserva con `os.mkdir` del destino (falla si existe) tras escribir en un
    temporal hermano `.tmp-*`; `metadata.json` se mueve el ULTIMO: una version sin el esta a medio
    escribir (grabacion interrumpida): se conserva, la automatica la salta e `index check` la
    reporta.
  - Un caso no nace `approved` (Gold) por `record` salvo con `approved_by_human is True`
    (`--approved-by-human`): la MISMA puerta que `set-status` (`es_confirmacion_humana`).
  - `corrected` + `supersedes_case`: la version citada debe existir completa en el store y ser
    `failure` o `corrected` (par fallo -> correccion, o cadena de correcciones; CA-12).
  - Sin `validation`, el caso nace `pending`. Sin `case_id`, se construye con la config.
  - No hay operacion de borrado: rechazados y fallidos se conservan (CA-02).
  - Nunca se escribe a traves de un enlace (symlink/junction) que saque `cases/`, el directorio
    del caso, el indice o el bloqueo fuera de `realpath(root)` o dentro de
    `<proyecto>/docs/knowledge/` (ADR-019, CWE-59).

`cambiar_estado(case_id, version, status, config, raiz_proyecto, approved_by_human=False,
reviewer_note=None)` — puerta humana para Gold (T-05): `approved` exige `approved_by_human is True`
(`--approved-by-human`) y fija `approved_by_human: true` + `approved_at`; sin el flag, rechazo
explicito. `needs_changes`/`rejected`/`pending` no lo requieren y dejan `approved_by_human: false`.
Solo se reescribe `validation.json` (temporal + `os.replace`), con `reviewer_note` redactada; el
resto de la version es inmutable. `metadata.json` se lee y valida ANTES de escribir nada.

Indice `<root>/cases_index.jsonl` (T-06): append-only, una linea por alta y por cambio de estado
con las claves exactas `case_id, version, family, variant, status, outcome, updated_at`; vale la
ultima por `(case_id, version)`. Es una CACHE: `index rebuild` lo reconstruye desde `cases/` y
`index check` lo compara (y reporta versiones incompletas, duplicadas, ilegibles, enlazadas fuera
o con `validation.json` incoherente); el ensamblador (T-09) leera `validation.json`, no el indice.
Las lineas corruptas se ignoran con aviso; se lee en streaming (linea a linea).

Bloqueo `<root>/.cases_index.lock` (`flock`/`msvcrt`, fichero que no se borra nunca): `record`,
`set-status` y `rebuild` hacen TODO su trabajo en disco con el tomado (escritura de la version o
de `validation.json` + su linea del indice; lectura de `cases/` + reescritura del indice). Si no
llega en `ESPERA_BLOQUEO_S`, se aborta sin escribir (fail closed; el SO libera el bloqueo al morir
el proceso). Los lectores (`check`, `list`) no lo toman: reintentan de forma acotada ante un
`PermissionError` transitorio (Windows) y distinguen «ilegible» de «a medio escribir».

Estructura (`case_schema.directorio_version`, ancho `ids.version_width`):
  <root>/cases/<family>.<variant>/v<NNN>/{metadata.json, request.json ({"request": ...}),
  context.json, constraints.json, trajectory.jsonl, metrics.json, validation.json,
  final/artifacts.json}  — JSON UTF-8 sin escapar (`ensure_ascii=False`), fin de linea LF.

Uso (exit 0 ok · 1 rechazo/validacion · 2 uso/JSON ilegible/error de E/S, como `case_schema.py`):
  case-recorder.py record <caso.json> [--config <training.json>] [--project-root <dir>] [--approved-by-human]
  case-recorder.py set-status <case_id> <version> <status> [--approved-by-human] [--note <texto>] [...]
  case-recorder.py index {rebuild|check} [...]     # check: exit 1 si el indice difiere de cases/
  case-recorder.py list [--status S] [--family F] [--outcome O] [--json] [...]
"""
import argparse
import datetime
import importlib.util
import json
import math
import os
import sys
import tempfile
import time

# Consola no UTF-8 (Windows cp1252) o tuberias: reconfigurar ANTES de leer/imprimir (GOT-005).
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure, ya leido o None (capsys, pythonw)

HERE = os.path.dirname(os.path.abspath(__file__))

MENSAJE_GOLD = "approved exige --approved-by-human: Gold es siempre una accion humana"
PREFIJO_TEMPORAL = ".tmp-"
DIGITOS = "0123456789"
VERSION_MAX = 999_999_999          # 9 digitos: nunca un `int()` de miles de digitos (gap #38)
REINTENTOS = 40                    # reintentos acotados ante PermissionError (Windows): 40 x 25 ms
ESPERA_REINTENTO_S = 0.025


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


class BloqueoNoDisponible(Rechazo):
    """El bloqueo del store no llego a tiempo: no se escribe nada (fail closed, gap #51)."""


class _EntradaIlegible(Exception):
    """JSON de entrada ilegible o ausente (exit 2)."""


def es_confirmacion_humana(flag):
    """LA puerta de Gold (gap #31): solo el booleano `True` cuenta. `"false"`, `"no"`, `1`, `[0]`,
    `None`... no son una confirmacion humana. La usan `grabar` y `cambiar_estado`."""
    return flag is True


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


class _Literal:
    """Valor YA redactado que `redactar_estructura` no vuelve a tocar (no es str/dict/lista)."""
    __slots__ = ("v",)

    def __init__(self, v):
        self.v = v


def _desenvolver(v):
    if isinstance(v, _Literal):
        return v.v
    if isinstance(v, dict):
        return {k: _desenvolver(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_desenvolver(x) for x in v]
    return v


def _redactar_arguments_texto(texto):
    """gap #32: `arguments` en texto JSON se redacta como ESTRUCTURA (parsear -> redactar ->
    reserializar): el patron de texto podria comerse un `\\"` y romper el JSON. Si no es JSON, se
    redacta como texto; si no hay nada que redactar, se conserva byte a byte."""
    try:
        datos = json.loads(texto)
    except (ValueError, RecursionError):
        return _redact_mod().redactar(texto)
    red = redactar_estructura(datos)
    return texto if red == datos else json.dumps(red, ensure_ascii=False)


def _marcar_arguments(v):
    """Copia de `v` con cada `arguments` de texto (a cualquier profundidad, como lo recorre
    `case_schema._buscar_cot`) ya redactado y envuelto en `_Literal`."""
    if isinstance(v, dict):
        return {k: (_Literal(_redactar_arguments_texto(x)) if k == "arguments" and isinstance(x, str)
                    else _marcar_arguments(x)) for k, x in v.items()}
    if isinstance(v, list):
        return [_marcar_arguments(x) for x in v]
    return v


def _redactar_caso(caso):
    """Copia de `caso` con TODO el texto libre que se escribe redactado (ver docstring del modulo);
    los campos de forma cerrada quedan intactos."""
    red = dict(caso)
    for campo in ("request", "context", "constraints", "metrics", "created_at"):
        if campo in red:
            red[campo] = redactar_estructura(red[campo])
    if "trajectory" in red:
        red["trajectory"] = _desenvolver(redactar_estructura(_marcar_arguments(red["trajectory"])))
    if isinstance(red.get("artifacts"), list):
        red["artifacts"] = [_desenvolver(redactar_estructura(
            {k: (_Literal(x) if k == "hash" else x) for k, x in a.items()})) if isinstance(a, dict)
            else redactar_estructura(a) for a in red["artifacts"]]
    if isinstance(red.get("validation"), dict):
        red["validation"] = {k: (redactar_estructura(x) if k in ("reviewer_note", "approved_at") else x)
                             for k, x in red["validation"].items()}
    return red


def _errores_redactados(errores):
    """Los mensajes de error del caso ORIGINAL salen por stderr: sin secretos (gap #32)."""
    r = _redact_mod().redactar
    return [{"campo": r(e["campo"]), "mensaje": r(e["mensaje"])} for e in errores]


def _errores_no_finitos(caso):
    """gap #41: `NaN`/`Infinity` no son JSON estandar; `{campo, mensaje}` por cada uno (iterativo)."""
    errores, pila = [], [(k, v) for k, v in reversed(list(caso.items()))] if isinstance(caso, dict) else []
    while pila:
        campo, v = pila.pop()
        if isinstance(v, float) and not math.isfinite(v):
            errores.append({"campo": campo, "mensaje": "NaN/Infinity no son JSON estandar: usa null o un numero finito"})
        elif isinstance(v, dict):
            pila.extend((f"{campo}.{k}", x) for k, x in reversed(list(v.items())))
        elif isinstance(v, (list, tuple)):
            pila.extend((f"{campo}[{i}]", x) for i, x in reversed(list(enumerate(v))))
    return errores


def _errores_extra(caso):
    errores = _errores_no_finitos(caso)
    v = caso.get("version")
    if cs._es_int(v) and v > VERSION_MAX:
        errores.append({"campo": "version", "mensaje": f"fuera de rango (1..{VERSION_MAX})"})
    return errores


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


def _dirs_version(dir_caso):
    """`[(numero, nombre)]` de los directorios `v<digitos>` de `dir_caso` (cualquier ancho), con
    `os.scandir` (sin un `isdir` por entrada, gap #46)."""
    try:
        with os.scandir(dir_caso) as it:
            return [(int(e.name[1:]), e.name) for e in it if _es_version(e.name) and e.is_dir()]
    except OSError:
        return []


def versiones(dir_caso):
    """Versiones (enteros) presentes en `cases/<family>.<variant>/`, completas o no."""
    return sorted(n for n, _nombre in _dirs_version(dir_caso))


def _siguiente_version(dir_caso):
    vs = versiones(dir_caso)
    return (vs[-1] + 1) if vs else 1


def _nombre_version(version, width):
    return os.path.basename(cs.directorio_version("x", "y", version, width))


def _dentro(ruta_canon, base_canon):
    base = base_canon.rstrip("\\/")
    return ruta_canon == base_canon or ruta_canon.startswith(base + os.sep) or ruta_canon.startswith(base + "/")


def _escapa(store, ruta, raiz_proyecto=None):
    """Motivo por el que `ruta` (resuelta con `realpath`: symlinks y junctions) sale del case store
    o cae en `<proyecto>/docs/knowledge/`, o None (gap #43, CWE-59)."""
    try:
        if not _dentro(cs._canon(ruta), cs._canon(store)):
            return "enlace que sale del case store"
        if raiz_proyecto is not None and cs._root_en_docs_knowledge(os.path.realpath(ruta), raiz_proyecto):
            return "enlace hacia docs/knowledge/ (ADR-019)"
    except (OSError, ValueError):
        return "ruta que no se puede resolver"
    return None


def _comprobar_contencion(store, rutas, raiz_proyecto=None):
    """`Rechazo` si alguna de `rutas` escapa del store por un enlace (antes de escribir nada)."""
    for ruta in rutas:
        motivo = _escapa(store, ruta, raiz_proyecto)
        if motivo:
            rel = os.path.relpath(ruta, store).replace(os.sep, "/")
            raise Rechazo(f"{rel}: {motivo}; no se escribe nada (el case store no sigue enlaces fuera de root)")


# ------------------------------------------------------------------ lectura y escritura

def _json_bytes(obj):
    return (json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def _leer_json_reintentando(ruta):
    """`(objeto, mtime)` de un JSON, reintentando de forma ACOTADA ante `PermissionError` (en
    Windows, abrir durante un `os.replace` ajeno falla un instante, gap #33). `FileNotFoundError`,
    JSON ilegible o el `PermissionError` persistente se propagan: el llamador los distingue."""
    for intento in range(REINTENTOS):
        try:
            with open(ruta, "rb") as f:
                datos = f.read()
                mtime = os.fstat(f.fileno()).st_mtime
            return json.loads(datos.decode("utf-8")), mtime
        except PermissionError:
            if intento == REINTENTOS - 1:
                raise
            time.sleep(ESPERA_REINTENTO_S)


def _ficheros_de(caso):
    """Contenido (bytes) de cada fichero de la version salvo `metadata.json` (se escribe el ultimo,
    ya con la version reservada)."""
    val = caso["validation"]
    return {
        "request.json": _json_bytes({"request": caso["request"]}),
        "context.json": _json_bytes(caso.get("context", {})),
        "constraints.json": _json_bytes(caso.get("constraints", {})),
        "trajectory.jsonl": "".join(json.dumps(t, ensure_ascii=False, allow_nan=False) + "\n"
                                    for t in caso["trajectory"]).encode("utf-8"),
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
    (antivirus, indexador, un lector) puede bloquear un instante el fichero."""
    for intento in range(REINTENTOS):
        try:
            return os.replace(origen, destino)
        except PermissionError:
            if intento == REINTENTOS - 1:
                raise
            time.sleep(ESPERA_REINTENTO_S)


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


def _reservar_y_mover(store, dir_caso, caso, width, auto, raiz_proyecto):
    """Escribe en `.tmp-*` hermano, reserva `v<NNN>` con `os.mkdir` (falla si existe: nadie pisa a
    nadie) y mueve los ficheros; `metadata.json` el ultimo. Tras crear el temporal y el destino se
    vuelve a comprobar que su `realpath` sigue dentro del store (un enlace que aparezca despues de
    la primera comprobacion, gap #43). Devuelve la ruta de la version."""
    os.makedirs(dir_caso, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix=PREFIJO_TEMPORAL, dir=dir_caso)
    try:
        _comprobar_contencion(store, [tmp], raiz_proyecto)
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
        _comprobar_contencion(store, [destino], raiz_proyecto)
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
    """CA-12: la version que corrige un `corrected` debe existir COMPLETA (con `metadata.json`) y ser
    `failure` o `corrected` (gap #39): un `corrected` nunca «corrige» un `success`."""
    sup = caso.get("supersedes_case")
    if sup is None:
        return
    m = cs.PATRON_REFERENCIA.fullmatch(sup)
    citada = os.path.join(dir_caso, _nombre_version(int(m.group(2)), width), "metadata.json")
    try:
        meta, _mtime = _leer_json_reintentando(citada)
    except FileNotFoundError:
        meta = None
    except (OSError, ValueError, RecursionError) as e:
        raise Rechazo("caso invalido: no se escribe nada", [{
            "campo": "supersedes_case", "mensaje": f"`{sup}` ilegible: {e}"}]) from None
    if meta is None:
        raise Rechazo("caso invalido: no se escribe nada", [{
            "campo": "supersedes_case",
            "mensaje": f"`{sup}` no existe en el case store (o esta a medio escribir): un `corrected` solo corrige una version grabada"}])
    outcome = meta.get("outcome") if isinstance(meta, dict) else None
    if not isinstance(meta, dict) or meta.get("case_id") != caso["case_id"] or outcome not in ("failure", "corrected"):
        raise Rechazo("caso invalido: no se escribe nada", [{
            "campo": "supersedes_case",
            "mensaje": f"`{sup}` tiene outcome `{outcome}`: un `corrected` solo corrige un `failure` o un `corrected` "
                       "del mismo case_id (par fallo -> correccion)"}])


def _comprobar_directorio_caso(store, fam, var, case_id):
    """gap #40b: un `case_id` que solo difiere en mayusculas de otro ya grabado compartiria
    directorio en NTFS/APFS: se rechaza (tambien en Linux: la regla peca de estricta). Y si el
    directorio del caso existe, su `metadata.case_id` debe ser el mismo."""
    nombre = f"{fam}.{var}"
    try:
        with os.scandir(os.path.join(store, "cases")) as it:
            otros = [e.name for e in it if e.name != nombre and e.name.casefold() == nombre.casefold()]
    except FileNotFoundError:
        return
    if otros:
        raise Rechazo(f"`{case_id}`: ya existe `cases/{otros[0]}`, que solo difiere en mayusculas "
                      "(compartirian directorio en Windows/macOS); no se escribe nada")
    for _n, nv in sorted(_dirs_version(os.path.join(store, "cases", nombre))):
        try:
            meta, _mtime = _leer_json_reintentando(os.path.join(store, "cases", nombre, nv, "metadata.json"))
        except (OSError, ValueError, RecursionError):
            continue
        if isinstance(meta, dict) and meta.get("case_id") != case_id:
            raise Rechazo(f"`cases/{nombre}` pertenece a `{meta.get('case_id')}`, no a `{case_id}`; no se escribe nada")
        return


def grabar(caso, config, raiz_proyecto=None, approved_by_human=False):
    """Graba `caso` como una version nueva. Devuelve `{case_id, version, ref, path, avisos}`;
    `Rechazo` si la capacidad esta apagada, el caso no vale o el bloqueo no llega a tiempo;
    `RedaccionNoDisponible` sin `redact.py`. En todos esos casos no se escribe nada."""
    config_activa(config, raiz_proyecto)
    if not isinstance(caso, dict):
        raise Rechazo("caso invalido: no se escribe nada", cs.validar_caso(caso, config))
    caso = dict(caso)
    val = caso.get("validation")
    if val is None:
        caso["validation"] = {"status": "pending", "approved_by_human": False}
    elif isinstance(val, dict) and val.get("status") == "approved":
        if not es_confirmacion_humana(approved_by_human):
            raise Rechazo(MENSAJE_GOLD)
        caso["validation"] = dict(val, approved_by_human=True, approved_at=val.get("approved_at") or _ahora())
    fam, var = caso.get("family"), caso.get("variant")
    if "case_id" not in caso and isinstance(fam, str) and isinstance(var, str):
        caso["case_id"] = cs.construir_case_id(config.get("id_prefix"), fam, var)

    width = cs.patrones_id(config)[2]
    store = raiz_store(config, raiz_proyecto)
    auto = "version" not in caso
    if auto:                                                # pista; la definitiva, con el bloqueo
        try:
            caso["version"] = _siguiente_version(os.path.join(store, os.path.dirname(cs.directorio_version(fam, var, 1, width))))
        except (ValueError, TypeError):
            caso["version"] = 1                              # el validador dira que falla

    errores = cs.validar_caso(caso, config) + _errores_extra(caso)          # 1. el ORIGINAL
    if errores:
        raise Rechazo("caso invalido: no se escribe nada", _errores_redactados(errores))
    caso = _redactar_caso(caso)                                             # 2. redactar
    errores = cs.validar_caso(caso, config) + _errores_extra(caso)          # 3. lo YA redactado
    if errores:
        raise Rechazo("caso invalido (tras redactar): no se escribe nada", errores)

    dir_caso = os.path.join(store, os.path.dirname(cs.directorio_version(fam, var, 1, width)))
    rutas = [os.path.join(store, BLOQUEO_INDICE), os.path.join(store, INDICE), os.path.join(store, "cases"), dir_caso]
    # comprobaciones de solo lectura ANTES de tomar el bloqueo (crearlo ya es escribir): la version
    # citada por `supersedes_case` es inmutable una vez completa, basta comprobarla aqui
    _comprobar_contencion(store, rutas, raiz_proyecto)
    _comprobar_directorio_caso(store, fam, var, caso["case_id"])
    _comprobar_supersedes(caso, dir_caso, width)
    with _Bloqueo(store):                                                   # 4. escribir
        _comprobar_contencion(store, rutas, raiz_proyecto)
        _comprobar_directorio_caso(store, fam, var, caso["case_id"])
        existentes = set(versiones(dir_caso))
        if auto:
            caso["version"] = max([caso["version"]] + [v + 1 for v in existentes])
        elif caso["version"] in existentes:
            raise Rechazo(f"{cs.referencia_version(caso['case_id'], caso['version'], width)} ya existe (con este u otro "
                          "ancho de version): el recorder nunca sobrescribe una version (graba sin `version` para la "
                          "siguiente libre)")
        destino = _reservar_y_mover(store, dir_caso, caso, width, auto, raiz_proyecto)
        avisos = _indexar(store, _entrada(caso, caso["validation"]["status"], _ahora()))
    return {"case_id": caso["case_id"], "version": caso["version"],
            "ref": cs.referencia_version(caso["case_id"], caso["version"], width), "path": destino, "avisos": avisos}


# ------------------------------------------------------------------ indice cases_index.jsonl (T-06)

INDICE = "cases_index.jsonl"
BLOQUEO_INDICE = ".cases_index.lock"
CLAVES_INDICE = ("case_id", "version", "family", "variant", "status", "outcome", "updated_at")
ESPERA_BLOQUEO_S = 10.0


class _Bloqueo:
    """Exclusion mutua entre recorders (hilos o procesos): `flock` en POSIX, `msvcrt.locking` en
    Windows, sobre `<root>/.cases_index.lock` (fichero que no se borra). Si no se obtiene en
    `ESPERA_BLOQUEO_S`, `BloqueoNoDisponible` (fail closed, gap #51): quien lo pide no escribe
    nada. El SO lo libera si el proceso muere: nunca queda un bloqueo huerfano."""

    def __init__(self, store):
        self.ruta = os.path.join(store, BLOQUEO_INDICE)
        self.f = None
        self.tomado = False

    def __enter__(self):
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
                    self.f.close()
                    raise BloqueoNoDisponible(
                        f"otro proceso tiene el bloqueo del case store ({BLOQUEO_INDICE}) desde hace mas de "
                        f"{ESPERA_BLOQUEO_S:g} s; no se escribe nada (reintentalo)") from None
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
    return (json.dumps(entrada, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def _anadir_linea(store, entrada):
    """Una linea al final del indice (append-only); CON el bloqueo ya tomado por el llamador. Si el
    fichero no termina en `\\n` (escritor muerto a mitad de linea), se antepone uno (gap #42)."""
    with open(os.path.join(store, INDICE), "a+b") as f:
        f.seek(0, os.SEEK_END)
        prefijo = b""
        if f.tell():
            f.seek(-1, os.SEEK_END)
            prefijo = b"" if f.read(1) == b"\n" else b"\n"
        f.write(prefijo + _linea(entrada))


def anadir_al_indice(store, entrada):
    """Una linea al final de `cases_index.jsonl` (append-only; nunca reescribe lo anterior)."""
    _comprobar_contencion(store, [os.path.join(store, BLOQUEO_INDICE), os.path.join(store, INDICE)])
    with _Bloqueo(store):
        _anadir_linea(store, entrada)


def _indexar(store, entrada):
    """Anade la linea del cambio (bloqueo ya tomado); si el indice no se puede escribir, el cambio
    YA esta en disco: se devuelve un aviso (el indice es una cache: `index rebuild` lo repone) en
    vez de fallar, para que nadie reintente y duplique."""
    try:
        _anadir_linea(store, entrada)
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


def _abrir_reintentando(ruta):
    for intento in range(REINTENTOS):
        try:
            return open(ruta, "rb")
        except PermissionError:
            if intento == REINTENTOS - 1:
                raise
            time.sleep(ESPERA_REINTENTO_S)


def leer_indice(store):
    """`(entradas, avisos)` en UNA pasada en streaming (linea a linea, gap #34): la ULTIMA linea
    valida por `(case_id, version)` (orden de aparicion) y un aviso por cada linea corrupta, que se
    ignora (nunca rompe la lectura). Las lineas vacias o de solo espacios se saltan sin aviso."""
    entradas, avisos = {}, []
    ruta = os.path.join(store, INDICE)
    try:
        f = _abrir_reintentando(ruta)
    except FileNotFoundError:
        return entradas, avisos
    except OSError as e:
        return entradas, [f"{INDICE} ilegible: {e}"]
    with f:
        for n, cruda in enumerate(f, 1):
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


def _iso(ts):
    return datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _leer_de_version(dir_v, fichero, rel):
    """`(objeto, mtime, aviso)`: distingue «a medio escribir» (falta el fichero), «bloqueada»
    (`PermissionError` tras los reintentos: transitorio, gap #33b) e «ilegible» (JSON roto)."""
    try:
        obj, mtime = _leer_json_reintentando(os.path.join(dir_v, fichero))
        return obj, mtime, None
    except FileNotFoundError:
        que = "a medio escribir o grabacion interrumpida" if fichero == "metadata.json" else "danada"
        return None, None, f"{rel} incompleta: sin {fichero} ({que}); se conserva, reparala o graba otra version"
    except PermissionError as e:
        return None, None, f"{rel} bloqueada por otro proceso tras {REINTENTOS} reintentos ({e}): no se pudo leer {fichero}"
    except (OSError, ValueError, RecursionError) as e:
        return None, None, f"{rel} ilegible: {fichero} no es JSON valido ({type(e).__name__})"


def estado_de_cases(store, raiz_proyecto=None):
    """`(entradas, avisos)` recorriendo `cases/` (la FUENTE; el indice es cache). Se omiten con
    aviso: versiones incompletas (sin `metadata.json`/`validation.json`), bloqueadas o ilegibles,
    duplicadas (mismo numero con dos anchos), incoherentes con su ruta o con el esquema,
    `validation.json` incoherente con `case_schema` (p. ej. `approved` sin humano, gap #45) y
    directorios que un enlace saca del store (gap #43). `updated_at` = mtime de `validation.json`."""
    entradas, avisos = {}, []
    base = os.path.join(store, "cases")
    try:
        with os.scandir(base) as it:
            casos = sorted((e.name, e.path) for e in it if not e.name.startswith(".") and e.is_dir())
    except OSError:
        return entradas, avisos
    for nombre, dir_caso in casos:
        motivo = _escapa(store, dir_caso, raiz_proyecto)
        if motivo:
            avisos.append(f"cases/{nombre} omitido: {motivo}")
            continue
        por_numero = {}
        for v, n in _dirs_version(dir_caso):
            por_numero.setdefault(v, []).append(n)
        for v, nombres in sorted(por_numero.items()):
            if len(nombres) > 1:
                avisos.append(f"cases/{nombre}: version {v} duplicada ({', '.join(sorted(nombres))}): se omiten")
                continue
            dir_v = os.path.join(dir_caso, nombres[0])
            rel = f"cases/{nombre}/{nombres[0]}"
            motivo = _escapa(store, dir_v, raiz_proyecto)
            if motivo:
                avisos.append(f"{rel} omitida: {motivo}")
                continue
            meta, _m, aviso = _leer_de_version(dir_v, "metadata.json", rel)
            if aviso is None:
                val, mtime, aviso = _leer_de_version(dir_v, "validation.json", rel)
            if aviso:
                avisos.append(aviso)
                continue
            errores_val = []
            cs._validar_validation(val, errores_val)
            if errores_val:
                avisos.append(f"{rel} omitida: validation.json incoherente ({errores_val[0]['campo']}: "
                              f"{errores_val[0]['mensaje']}); no se indexa")
                continue
            try:
                e = _entrada(meta, val.get("status"), _iso(mtime))
            except (AttributeError, KeyError, TypeError):
                avisos.append(f"{rel} omitida: metadata.json incompleto")
                continue
            if f"{e['family']}.{e['variant']}" != nombre or e["version"] != v or _entrada_valida(e):
                avisos.append(f"{rel} omitida: metadata.json no casa con su ruta o con el esquema")
                continue
            entradas[(e["case_id"], e["version"])] = e
    return entradas, avisos


def reconstruir_indice(store, raiz_proyecto=None):
    """Reescribe `cases_index.jsonl` desde `cases/` (una linea por version, ordenadas). LEE y
    ESCRIBE con el MISMO bloqueo tomado (gap #33a: un `set-status` intermedio no se pierde).
    Conserva el `updated_at` de la ultima linea valida si su estado coincide. Escritura atomica.
    Devuelve `(n_versiones, avisos)`."""
    ruta = os.path.join(store, INDICE)
    _comprobar_contencion(store, [os.path.join(store, BLOQUEO_INDICE), ruta], raiz_proyecto)
    os.makedirs(store, exist_ok=True)
    with _Bloqueo(store):
        fuente, avisos = estado_de_cases(store, raiz_proyecto)
        previas, _ = leer_indice(store)
        lineas = []
        for clave in sorted(fuente, key=lambda k: (fuente[k]["family"], fuente[k]["variant"], k[1])):
            e = dict(fuente[clave])
            p = previas.get(clave)
            if p and all(p[k] == e[k] for k in CLAVES_INDICE if k != "updated_at"):
                e["updated_at"] = p["updated_at"]
            lineas.append(_linea(e))
        _escribir_atomico(ruta, b"".join(lineas))
    return len(lineas), avisos


def comprobar_indice(store, width=cs.VERSION_WIDTH_DEFECTO, raiz_proyecto=None):
    """Diferencias entre el indice y `cases/` (lista vacia = coherente): lineas corruptas y todo lo
    que `estado_de_cases` omite (versiones incompletas, duplicadas, enlazadas fuera, incoherentes)
    cuentan como incoherencia (gap #37). Lector: no toma el bloqueo."""
    fuente, avisos_fuente = estado_de_cases(store, raiz_proyecto)
    indice, avisos = leer_indice(store)
    difs = list(avisos_fuente) + list(avisos)
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


def listar_con_avisos(store, status=None, family=None, outcome=None):
    """`(entradas, avisos)` del indice en UNA lectura (gap #34): la ultima linea por version,
    filtrada y ordenada por `case_id` y version, y los avisos de lineas corruptas."""
    entradas, avisos = leer_indice(store)
    out = [e for e in entradas.values()
           if (status is None or e["status"] == status) and (family is None or e["family"] == family)
           and (outcome is None or e["outcome"] == outcome)]
    return sorted(out, key=lambda e: (e["case_id"], e["version"])), avisos


def listar(store, status=None, family=None, outcome=None):
    """Entradas del indice (ultima por version) filtradas, ordenadas por `case_id` y version."""
    return listar_con_avisos(store, status, family, outcome)[0]


# ------------------------------------------------------------------ puerta humana para Gold (T-05)

def _version_int(version):
    """`1`, `"1"` o `"v001"` -> 1; otra cosa (o mas de 9 digitos, gap #38) -> `Rechazo`."""
    if isinstance(version, bool):
        version = None
    if isinstance(version, str):
        texto = version[1:] if version[:1] == "v" else version
        ok = texto and len(texto) <= len(str(VERSION_MAX)) and all(c in DIGITOS for c in texto)
        version = int(texto) if ok else None
    if not isinstance(version, int) or not 1 <= version <= VERSION_MAX:
        raise Rechazo("version invalida", [{"campo": "version", "mensaje": f"entero entre 1 y {VERSION_MAX} (`1` o `v001`)"}])
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
    atomica); el resto de la version es inmutable. `approved` (Gold) exige `approved_by_human is
    True` (`--approved-by-human`): sin el, `Rechazo` con mensaje explicito. `needs_changes`,
    `rejected` y `pending` no lo requieren y dejan `approved_by_human: false`. Sin `reviewer_note`
    se conserva la nota anterior; la nueva se redacta. La escritura de `validation.json` y su linea
    del indice van bajo el MISMO bloqueo (gap #35); `metadata.json` se lee y valida antes de
    escribir nada (gap #36). Devuelve `{case_id, version, ref, status, path, avisos}`."""
    config_activa(config, raiz_proyecto)
    if status not in cs.VALIDATION_STATUS:
        raise Rechazo("estado invalido", [{"campo": "status", "mensaje": f"uno de {', '.join(cs.VALIDATION_STATUS)}"}])
    if status == "approved" and not es_confirmacion_humana(approved_by_human):
        raise Rechazo(MENSAJE_GOLD)
    if reviewer_note is not None and not isinstance(reviewer_note, str):
        raise Rechazo("nota invalida", [{"campo": "reviewer_note", "mensaje": "debe ser texto"}])
    version = _version_int(version)
    family, variant = _family_variant(case_id, config)
    width = cs.patrones_id(config)[2]
    ref = cs.referencia_version(case_id, version, width)
    store = raiz_store(config, raiz_proyecto)
    destino = os.path.join(store, cs.directorio_version(family, variant, version, width))
    ruta_meta, ruta_val = os.path.join(destino, "metadata.json"), os.path.join(destino, "validation.json")
    nota = redactar_estructura(reviewer_note) if reviewer_note is not None else None
    rutas = [os.path.join(store, BLOQUEO_INDICE), os.path.join(store, INDICE), destino]
    _comprobar_contencion(store, rutas, raiz_proyecto)
    if not (os.path.isfile(ruta_meta) and os.path.isfile(ruta_val)):
        raise Rechazo(f"{ref} no existe en el case store (o esta a medio escribir)")
    with _Bloqueo(store):
        _comprobar_contencion(store, rutas, raiz_proyecto)
        try:
            meta, _m = _leer_json_reintentando(ruta_meta)
            previa, _m = _leer_json_reintentando(ruta_val)
        except FileNotFoundError:
            raise Rechazo(f"{ref} no existe en el case store (o esta a medio escribir)") from None
        except (OSError, ValueError, RecursionError) as e:
            raise Rechazo(f"{ref}: metadata.json/validation.json ilegibles: {e}") from None
        if not isinstance(meta, dict) or meta.get("case_id") != case_id:
            raise Rechazo(f"{ref}: metadata.json no corresponde a `{case_id}`")
        try:
            entrada = _entrada(meta, status, _ahora())
        except KeyError as e:
            raise Rechazo(f"{ref}: metadata.json incompleto (falta {e}); no se escribe nada") from None
        if _entrada_valida(entrada) or entrada["version"] != version:
            raise Rechazo(f"{ref}: metadata.json no casa con el esquema o con su ruta; no se escribe nada")
        previa = previa if isinstance(previa, dict) else {}
        gold = status == "approved"
        nueva = {"status": status, "approved_by_human": gold, "approved_at": _ahora() if gold else None,
                 "reviewer_note": nota if nota is not None else previa.get("reviewer_note")}
        _escribir_atomico(ruta_val, _json_bytes(nueva))
        avisos = _indexar(store, entrada)
    return {"case_id": case_id, "version": version, "ref": ref, "status": status, "path": destino, "avisos": avisos}


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
    p_rec.add_argument("fichero", help="caso en JSON: el esquema de case_schema.py, pero `version` es opcional "
                                       "(sin `version` se asigna la siguiente libre; con ella, se rechaza si ya existe)")
    p_rec.add_argument("--approved-by-human", action="store_true",
                       help="confirmacion HUMANA explicita para grabar un caso ya `approved` (Gold)")
    _comunes(p_rec)
    p_st = sub.add_parser("set-status", help="cambia validation.status; `approved` (Gold) exige --approved-by-human")
    p_st.add_argument("case_id")
    p_st.add_argument("version", help="`1` o `v001`")
    p_st.add_argument("status", choices=cs.VALIDATION_STATUS)
    p_st.add_argument("--approved-by-human", action="store_true",
                      help="confirmacion HUMANA explicita para marcar Gold (la misma puerta que record)")
    p_st.add_argument("--note", help="reviewer_note, redactada (sin ella se conserva la anterior)")
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
            n, avisos = reconstruir_indice(store, raiz)
            _avisar(avisos)
            print(f"OK {INDICE} reconstruido desde cases/: {n} version(es)")
            return 0
        if args.cmd == "index":
            difs = comprobar_indice(store, width, raiz)
            if difs:
                for d in difs:
                    print(f"{INDICE}: {d}")
                print(f"{len(difs)} diferencia(s): reconstruye con `index rebuild`", file=sys.stderr)
                return 1
            print(f"OK {INDICE} coherente con cases/")
            return 0
        entradas, avisos = listar_con_avisos(store, status=args.status, family=args.family, outcome=args.outcome)
        _avisar(avisos)
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
    except OSError as e:
        # gap #38: E/S (root que es un fichero, disco lleno, permisos) -> exit 2 con mensaje, sin traceback
        print(f"error de E/S: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
