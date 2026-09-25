#!/usr/bin/env python3
"""
case-recorder.py — recorder determinista de casos de `training-data-services` (design.md O1).

Graba cada intento del proyecto como una VERSION inmutable del case store, en el `root` que declara
`.claude/knowledge-services/training.json` (fuera de Git y de `docs/knowledge/`, ADR-019). Opt-in:
sin config, o con `enabled: false`, se niega a grabar y no escribe nada (CA-01). El plugin valida
FORMA, nunca dominio (CA-04): las metricas llegan ya calculadas por el proyecto.

`grabar(caso, config, raiz_proyecto, approved_by_human=False)`, en este orden:
  0. convierte el caso a tipos JSON PLANOS (dict/list/str/int/float/bool/None, leidos con los
     metodos de `dict`/`list`, no con los del objeto): cualquier otro tipo -> rechazo (gap #62);
  1. valida el caso ORIGINAL con `case_schema.validar_caso` (forma y chain-of-thought) y rechaza
     `NaN`/`Infinity` y un `arguments` en texto JSON con claves duplicadas (JSON ambiguo, gap #64);
  2. redacta con `agent-kits/shared/redact.py` (fuente unica; sin el -> `RedaccionNoDisponible`,
     CA-09) TODO el texto libre que se escribe: `request`, `context`, `constraints`, `trajectory`
     (un `arguments` en texto JSON se redacta como estructura: parsear -> redactar -> reserializar),
     las cadenas de `metrics`, `created_at`, `artifacts[]` salvo `hash`, y `validation.reviewer_note`
     / `approved_at`. Mas de `case_schema.PROFUNDIDAD_MAX` niveles en un campo -> rechazo (gap #57).
     Quedan SIN redactar solo los campos de forma cerrada que valida el esquema:
     `case_id`, `family`, `variant`, `version`, `outcome`, `supersedes_case`, `validation.status`,
     `validation.approved_by_human` y `artifacts[].hash`;
  3. valida el caso YA redactado (basta que falle uno de los dos para rechazar);
  4. solo entonces escribe, en dos secciones CORTAS con el bloqueo (diseno D-fix2, E1): S1 reserva
     la version (`os.mkdir`, con la comprobacion de mayusculas y de «mismo numero con otro ancho»);
     sin bloqueo se mueven los ficheros (W); S2 RELEE `validation.json` del disco e indexa ESE
     estado (A). Si el bloqueo no llega en S1 -> exit 3 sin escribir nada; si no llega en S2 la
     version YA esta grabada: exit 0 con aviso «index rebuild» (nunca exit 3 despues de W).
  - Sin `version`, se asigna la siguiente libre (mayor existente + 1, sea cual sea el ancho del
    directorio); con `version` que ya existe (con cualquier ancho) -> rechazo: nunca sobrescribe
    (CA-02). Los ficheros se escriben en un temporal `cases/.tmp-*`; `metadata.json` se mueve el
    ULTIMO: una version sin el esta a medio escribir (grabacion en curso o interrumpida): se
    conserva, la automatica la salta e `index check` la reporta.
  - Un caso no nace `approved` (Gold) por `record` salvo con `approved_by_human is True`
    (`--approved-by-human`): la MISMA puerta que `set-status` (`es_confirmacion_humana`).
  - `corrected` + `supersedes_case`: la version citada (buscada por NUMERO, con cualquier ancho)
    debe existir completa en el store y ser `failure` o `corrected` (CA-12).
  - Sin `validation`, el caso nace `pending`. Sin `case_id`, se construye con la config.
  - No hay operacion de borrado: rechazados y fallidos se conservan (CA-02).
  - Nunca se escribe a traves de un enlace (symlink/junction) que saque `cases/`, el directorio
    del caso, el indice o el bloqueo fuera de `realpath(root)` o dentro de
    `<proyecto>/docs/knowledge/` (ADR-019, CWE-59), ni en un indice/bloqueo con enlaces duros.
    Sin `raiz_proyecto`, la raiz del proyecto es el cwd (la misma que usa `config_activa`).

`cambiar_estado(case_id, version, status, config, raiz_proyecto, approved_by_human=False,
reviewer_note=None)` — puerta humana para Gold (T-05): `approved` exige `approved_by_human is True`
(`--approved-by-human`) y fija `approved_by_human: true` + `approved_at`; sin el flag, rechazo
explicito. `needs_changes`/`rejected`/`pending` no lo requieren y dejan `approved_by_human: false`.
Solo se reescribe `validation.json` (temporal + `os.replace`), con `reviewer_note` redactada; el
resto de la version es inmutable. La version se localiza por NUMERO (cualquier ancho; dos
directorios con el mismo numero -> rechazo); `metadata.json`/`validation.json` que sean enlace se
rechazan antes de leerlos. Lectura + escritura + linea del indice, con el bloqueo (O(1)).

Indice `<root>/cases_index.jsonl` (T-06): append-only, una linea por alta y por cambio de estado
con las claves exactas `case_id, version, family, variant, status, outcome, updated_at`; vale la
ultima por `(case_id, version)`. Es una CACHE; el ensamblador (T-09) leera `validation.json`.
  - `index rebuild` en tres fases, serializado por `<root>/.cases_rebuild.lock` (se toma ANTES que
    el del indice; los escritores nunca lo toman): F0 (bloqueo) anota tamano e identidad del indice;
    F1 (SIN bloqueo) recorre `cases/` y escribe un temporal; F2 (bloqueo, O(cola)) comprueba la
    identidad, RELEE del disco cada version que aparece en la cola (lineas anadidas durante F1) y
    sustituye el indice. Identidad cambiada o `PermissionError` al sustituir -> exit 3 sin tocar.
  - `index check` sigue el mismo esquema sin escribir y devuelve exit 1 si hay alguna diferencia:
    una version en `cases/` y no en el indice (o al reves), un campo distinto, una linea corrupta
    del indice, y toda version que el recorrido omite: incompleta (sin `metadata.json` o
    `validation.json`), duplicada (mismo numero con dos anchos), enlazada (symlink/junction), con un
    fichero que no es un fichero regular, no legible tras los reintentos (bloqueada o sin permisos),
    JSON ilegible, `metadata.json` que no casa con su ruta o con el esquema, o `validation.json`
    incoherente. Es INFORMATIVO (exit 0) lo que esta «en curso»: una version sin `metadata.json`
    cuyo directorio se modifico hace menos de `GRACIA_EN_CURSO_S` (60 s), o una completa sin linea
    con `metadata.json` de hace menos de 60 s; un `mtime` futuro nunca esta «en curso».
  - Las lineas corruptas se ignoran con aviso al leer; se lee en streaming (linea a linea).
  - Los lectores detectan enlaces por entrada sin `realpath` (`is_symlink()` o el bit «name
    surrogate» de `st_reparse_tag`; un placeholder de OneDrive no es enlace).

Bloqueo `<root>/.cases_index.lock` (`flock`/`msvcrt`, fichero que no se borra nunca): solo protege
secciones O(1) (una linea del indice, un `validation.json`, la reserva de una version). Espera con
retroceso exponencial y jitter (5 -> 50 ms) hasta `ESPERA_BLOQUEO_S`; si no llega, no se escribe
nada (`BloqueoNoDisponible`, exit 3: transitorio, reintenta). El SO lo libera al morir el proceso.

Estructura (`case_schema.directorio_version`, ancho `ids.version_width`):
  <root>/cases/<family>.<variant>/v<NNN>/{metadata.json, request.json ({"request": ...}),
  context.json, constraints.json, trajectory.jsonl, metrics.json, validation.json,
  final/artifacts.json}  — JSON UTF-8 sin escapar (`ensure_ascii=False`), fin de linea LF.

Uso (exit 0 ok · 1 rechazo/validacion · 2 uso/JSON ilegible/error de E/S · 3 transitorio: el
bloqueo no llego o el indice cambio durante `rebuild`; no se escribio nada, reintenta):
  case-recorder.py record <caso.json> [--config <training.json>] [--project-root <dir>] [--approved-by-human]
  case-recorder.py set-status <case_id> <version> <status> [--approved-by-human] [--note <texto>] [...]
  case-recorder.py index {rebuild|check} [...]     # check: exit 1 si el indice difiere de cases/
  case-recorder.py list [--status S] [--family F] [--outcome O] [--json] [...]
"""
import argparse
import datetime
import hashlib
import importlib.util
import json
import math
import os
import random
import stat
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
_WINDOWS = os.name == "nt"
NAME_SURROGATE = 0x20000000        # bit «name surrogate» de st_reparse_tag: symlink y junction (E4)


def _reloj():
    """Reloj de pared (inyectable en los tests): solo para la gracia «en curso» (E5)."""
    return time.time()


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


class Transitorio(Rechazo):
    """No se ha escrito nada por una condicion pasajera (exit 3): reintentar es seguro."""


class BloqueoNoDisponible(Transitorio):
    """El bloqueo del store no llego a tiempo: no se escribe nada (fail closed, gap #51; exit 3)."""


class _EntradaIlegible(Exception):
    """JSON de entrada ilegible o ausente (exit 2)."""


class ProfundidadExcesiva(ValueError):
    """Una estructura con mas niveles de los que se pueden redactar con garantias (gap #57)."""


class _ClaveDuplicada(ValueError):
    """JSON con una clave repetida en el mismo objeto: ambiguo (gap #64)."""


def es_confirmacion_humana(flag):
    """LA puerta de Gold (gap #31): solo el booleano `True` cuenta. `"false"`, `"no"`, `1`, `[0]`,
    `None`... no son una confirmacion humana. La usan `grabar` y `cambiar_estado`."""
    return flag is True


def _raiz(raiz_proyecto):
    """Raiz del proyecto de TODAS las funciones publicas (gap #56): la dada o el cwd, la misma que
    usa `config_activa` para validar `root`."""
    return raiz_proyecto or os.getcwd()


# ------------------------------------------------------------------ tipos JSON planos (gap #62)

_ESCALARES = (str, int, float, bool, type(None))


def _plano(valor):
    """`(copia, errores)`: `valor` reconstruido con tipos JSON PLANOS recorriendo (iterativo) con los
    metodos de `dict`/`list` —no con los del objeto, que podrian mentir—. Otro tipo (o una clave no
    textual) es un error `{campo, mensaje}`."""
    errores, raiz = [], [None]
    pila = [(valor, raiz, 0, "")]
    while pila:
        x, destino, k, campo = pila.pop()
        if type(x) in _ESCALARES:
            destino[k] = x
        elif isinstance(x, dict):
            nuevo = destino[k] = {}
            for clave, sub in dict.items(x):
                if type(clave) is not str:
                    errores.append({"campo": campo or "(caso)", "mensaje": f"clave no textual ({type(clave).__name__}): el caso debe ser JSON"})
                    continue
                nuevo[clave] = None
                pila.append((sub, nuevo, clave, f"{campo}.{clave}" if campo else clave))
        elif isinstance(x, list):
            nuevo = destino[k] = [None] * list.__len__(x)
            for i, sub in enumerate(list.__iter__(x)):
                pila.append((sub, nuevo, i, f"{campo}[{i}]"))
        else:
            destino[k] = None
            errores.append({"campo": campo or "(caso)", "mensaje": f"tipo no JSON ({type(x).__name__})"})
    return raiz[0], errores


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
    textual no se toca; la entrada no muta. Sin `redact.py` -> `RedaccionNoDisponible`. Un valor a
    mas de `case_schema.PROFUNDIDAD_MAX` niveles -> `ProfundidadExcesiva` (gap #57: fail closed,
    nunca `RecursionError`).

    Claves (fix2, gap #18): si dos claves distintas se redactan al mismo literal, la segunda y
    siguientes llevan un sufijo estable por orden de aparicion (`<clave redactada> #2`, `#3`...), y
    una clave que NO cambia al redactar conserva siempre su nombre: nunca se pierde un valor. Una
    namedtuple se reconstruye con `_make` (mismo tipo y campos)."""
    redactar_txt = _redact_mod().redactar
    tope = cs.PROFUNDIDAD_MAX

    def _dict(v, d):
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
            out[nombre] = _rec(x, d + 1)
        return out

    def _rec(v, d):
        if d > tope:
            raise ProfundidadExcesiva(f"anidamiento > {tope} niveles: no se puede redactar con garantias")
        if isinstance(v, str):
            return redactar_txt(v)
        if isinstance(v, dict):
            return _dict(v, d)
        if isinstance(v, tuple) and hasattr(type(v), "_make"):
            return type(v)._make(_rec(x, d + 1) for x in v)
        if isinstance(v, (list, tuple, set, frozenset)):
            return type(v)(_rec(x, d + 1) for x in v)
        return v

    return _rec(valor, 0)


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


def _sin_duplicadas(pares):
    """`object_pairs_hook` que rechaza una clave repetida en el mismo objeto (gap #64)."""
    out = {}
    for k, v in pares:
        if k in out:
            raise _ClaveDuplicada(k)
        out[k] = v
    return out


def _redactar_arguments_texto(texto):
    """gap #32: `arguments` en texto JSON se redacta como ESTRUCTURA (parsear -> redactar ->
    reserializar): el patron de texto podria comerse un `\\"` y romper el JSON. Si no es JSON (o es
    JSON ambiguo, con claves duplicadas: gap #64), se redacta como texto; si no hay nada que
    redactar, se conserva byte a byte."""
    try:
        datos = json.loads(texto, object_pairs_hook=_sin_duplicadas)
        red = redactar_estructura(datos)
    except (ValueError, RecursionError):
        return _redact_mod().redactar(texto)
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
    los campos de forma cerrada quedan intactos. Un campo demasiado profundo -> `Rechazo` con el
    campo (gap #57)."""
    red, errores = dict(caso), []

    def _campo(campo, fn):
        try:
            return fn()
        except ProfundidadExcesiva as e:
            errores.append({"campo": campo, "mensaje": str(e)})
            return None

    for campo in ("request", "context", "constraints", "metrics", "created_at"):
        if campo in red:
            red[campo] = _campo(campo, lambda c=campo: redactar_estructura(red[c]))
    if isinstance(red.get("trajectory"), list):
        red["trajectory"] = [_campo(f"trajectory[{i}]", lambda t=t: _desenvolver(redactar_estructura(_marcar_arguments(t))))
                             for i, t in enumerate(red["trajectory"])]
    if isinstance(red.get("artifacts"), list):
        red["artifacts"] = [_campo(f"artifacts[{i}]", lambda a=a: _desenvolver(redactar_estructura(
            {k: (_Literal(x) if k == "hash" else x) for k, x in a.items()})) if isinstance(a, dict)
            else redactar_estructura(a)) for i, a in enumerate(red["artifacts"])]
    if isinstance(red.get("validation"), dict):
        red["validation"] = {k: (_campo(f"validation.{k}", lambda x=x: redactar_estructura(x))
                                 if k in ("reviewer_note", "approved_at") else x)
                             for k, x in red["validation"].items()}
    if errores:
        raise Rechazo("caso invalido: no se escribe nada", errores)
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


def _errores_arguments_ambiguos(caso):
    """gap #64: un `arguments` en texto JSON (a cualquier profundidad de la trayectoria, tambien
    dentro de otro `arguments` ya parseado) con una clave repetida es JSON AMBIGUO: `json.loads` se
    queda con el ultimo valor y el primero (quiza un secreto) no se veria al redactar. Iterativo."""
    errores = []
    tr = caso.get("trajectory") if isinstance(caso, dict) else None
    pila = [(f"trajectory[{i}]", t) for i, t in enumerate(tr)] if isinstance(tr, list) else []
    while pila:
        campo, v = pila.pop()
        if isinstance(v, dict):
            for k, x in v.items():
                sub = f"{campo}.{k}"
                if k == "arguments" and isinstance(x, str):
                    try:
                        pila.append((sub, json.loads(x, object_pairs_hook=_sin_duplicadas)))
                    except _ClaveDuplicada as e:
                        errores.append({"campo": sub, "mensaje": f"JSON ambiguo: clave duplicada `{e.args[0]}` (se rechaza: "
                                                                 "no se puede redactar con garantias)"})
                    except (ValueError, RecursionError):
                        pass
                else:
                    pila.append((sub, x))
        elif isinstance(v, list):
            pila.extend((f"{campo}[{i}]", x) for i, x in enumerate(v))
    return errores


def _errores_extra(caso):
    errores = _errores_no_finitos(caso) + _errores_arguments_ambiguos(caso)
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
    return os.path.abspath(os.path.join(_raiz(raiz_proyecto), config["root"]))


def _es_version(nombre):
    return len(nombre) > 1 and nombre[0] == "v" and all(c in DIGITOS for c in nombre[1:])


def _entradas_version(dir_caso):
    """`[(numero, nombre, DirEntry)]` de los directorios `v<digitos>` de `dir_caso` (cualquier
    ancho, enlaces incluidos: ocupan su numero), con `os.scandir` (sin un `isdir` por entrada)."""
    try:
        with os.scandir(dir_caso) as it:
            return [(int(e.name[1:]), e.name, e) for e in it if _es_version(e.name) and e.is_dir()]
    except OSError:
        return []


def _dirs_version(dir_caso):
    """`[(numero, nombre)]` de los directorios `v<digitos>` de `dir_caso` (gap #46)."""
    return [(n, nombre) for n, nombre, _e in _entradas_version(dir_caso)]


def versiones(dir_caso):
    """Versiones (enteros) presentes en `cases/<family>.<variant>/`, completas o no."""
    return sorted(n for n, _nombre in _dirs_version(dir_caso))


def _siguiente_version(dir_caso):
    vs = versiones(dir_caso)
    return (vs[-1] + 1) if vs else 1


def _nombre_version(version, width):
    return os.path.basename(cs.directorio_version("x", "y", version, width))


def _localizar_version(dir_caso, version, width=cs.VERSION_WIDTH_DEFECTO):
    """Nombres de directorio que existen para el NUMERO `version` con cualquier ancho (gaps #40/#60):
    un `lstat` por ancho posible, O(1) sea cual sea el numero de versiones del caso."""
    anchos = range(len(str(version)), max(len(str(VERSION_MAX)), width) + 1)
    nombres = []
    for w in anchos:
        nombre = f"v{version:0{w}d}"
        if nombre not in nombres and os.path.lexists(os.path.join(dir_caso, nombre)):
            nombres.append(nombre)
    return nombres


def _dentro(ruta_canon, base_canon):
    base = base_canon.rstrip("\\/")
    return ruta_canon == base_canon or ruta_canon.startswith(base + os.sep) or ruta_canon.startswith(base + "/")


def _escapa(store, ruta, raiz_proyecto=None):
    """Motivo por el que `ruta` (resuelta con `realpath`: symlinks y junctions) sale del case store
    o cae en `<proyecto>/docs/knowledge/` (raiz por defecto: cwd, gap #56), o None (gap #43)."""
    try:
        if not _dentro(cs._canon(ruta), cs._canon(store)):
            return "enlace que sale del case store"
        if cs._root_en_docs_knowledge(os.path.realpath(ruta), _raiz(raiz_proyecto)):
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


def _stat_sin_seguir(x):
    """`lstat` de una ruta, o `DirEntry.stat(follow_symlinks=False)` (en Windows viene cacheado por
    `scandir`, con `st_reparse_tag`)."""
    if isinstance(x, os.DirEntry):
        return x.stat(follow_symlinks=False)
    return os.lstat(x)


def _es_enlace_st(st):
    """True si el `stat` (sin seguir) es un enlace: symlink, o un punto de reanalisis con el bit
    «name surrogate» (`0x20000000`: symlink y junction; NO los placeholders de nube, E4). None si no
    se puede saber (Windows sin `st_reparse_tag`): el llamador degrada a `realpath`."""
    if stat.S_ISLNK(st.st_mode):
        return True
    tag = getattr(st, "st_reparse_tag", None)
    if tag is None:
        return None if _WINDOWS else False
    return bool(tag & NAME_SURROGATE)


MOTIVO_ENLACE = "enlace (symlink/junction): el case store no sigue enlaces"


def _motivo_enlace(x, ruta):
    """`MOTIVO_ENLACE` si la entrada `x` (DirEntry o ruta) es un enlace, o None. Sin `realpath`
    salvo en la degradacion (Windows sin `st_reparse_tag`), y entonces solo del ULTIMO componente."""
    try:
        st = _stat_sin_seguir(x)
    except FileNotFoundError:
        return None
    except OSError:
        return "ruta que no se puede examinar"
    es = _es_enlace_st(st)
    if es is None:
        padre = os.path.realpath(os.path.dirname(ruta))
        es = os.path.normcase(os.path.realpath(ruta)) != os.path.normcase(os.path.join(padre, os.path.basename(ruta)))
    return MOTIVO_ENLACE if es else None


def _comprobar_fichero_propio(ruta):
    """El indice y los bloqueos se abren para escribir IN SITU: si ya existen, no pueden ser un
    enlace ni tener enlaces duros (`realpath` no ve un hardlink a un ADR curado, gap #63, CWE-59)."""
    try:
        st = _stat_sin_seguir(ruta)
    except FileNotFoundError:
        return
    nombre = os.path.basename(ruta)
    if _es_enlace_st(st):
        raise Rechazo(f"{nombre}: es un enlace; no se escribe a traves de el (CWE-59)")
    if stat.S_ISREG(st.st_mode) and st.st_nlink > 1:
        raise Rechazo(f"{nombre}: es un enlace duro compartido ({st.st_nlink} nombres para el mismo fichero: podria "
                      "ser otro fichero del proyecto, CWE-59); no se escribe nada")


def _comprobar_fd_propio(f, ruta):
    """Lo mismo sobre el descriptor YA abierto (sin carrera entre comprobar y abrir)."""
    st = os.fstat(f.fileno())
    if stat.S_ISREG(st.st_mode) and st.st_nlink > 1:
        raise Rechazo(f"{os.path.basename(ruta)}: es un enlace duro compartido ({st.st_nlink} nombres, CWE-59); "
                      "no se escribe nada")


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
    nunca una version. Recorrido propio con `scandir` que NUNCA desciende por un enlace o punto de
    reanalisis: elimina el ENLACE (`rmdir` de una junction/symlink de directorio, `remove` de un
    symlink), nunca su destino (gap #65). Si ya no existe, no hace nada."""
    if not os.path.basename(tmp).startswith(PREFIJO_TEMPORAL) or not os.path.lexists(tmp):
        return
    enlaces, ficheros, orden, pila = [], [], [], []
    try:
        es_dir = stat.S_ISDIR(_stat_sin_seguir(tmp).st_mode)
    except OSError:
        return
    if _motivo_enlace(tmp, tmp):
        enlaces.append(tmp)
    elif es_dir:
        pila.append(tmp)
    else:
        ficheros.append(tmp)
    while pila:
        d = pila.pop()
        orden.append(d)
        try:
            with os.scandir(d) as it:
                entradas = list(it)
        except OSError:
            continue
        for e in entradas:
            if _motivo_enlace(e, e.path):
                enlaces.append(e.path)
            elif e.is_dir(follow_symlinks=False):
                pila.append(e.path)
            else:
                ficheros.append(e.path)
    for ruta in enlaces:                       # el enlace, no lo que hay detras
        for quitar in ((os.rmdir, os.remove) if _WINDOWS else (os.remove, os.rmdir)):
            try:
                quitar(ruta)
                break
            except OSError:
                pass
    for ruta in ficheros:
        try: os.remove(ruta)
        except OSError: pass
    for d in reversed(orden):
        try: os.rmdir(d)
        except OSError: pass


def _reservar(store, dir_caso, caso, width, auto, raiz_proyecto):
    """S1 (con el bloqueo): numero de version con cualquier ancho (#40a) y `os.mkdir` del destino
    (falla si existe: nadie pisa a nadie). Tras crearlo se comprueba su `realpath`. Devuelve la ruta."""
    existentes = set(versiones(dir_caso))
    if auto:
        caso["version"] = max([caso["version"]] + [v + 1 for v in existentes])
    elif caso["version"] in existentes:
        raise Rechazo(f"{cs.referencia_version(caso['case_id'], caso['version'], width)} ya existe (con este u otro "
                      "ancho de version): el recorder nunca sobrescribe una version (graba sin `version` para la "
                      "siguiente libre)")
    os.makedirs(dir_caso, exist_ok=True)
    version = caso["version"]
    while True:
        destino = os.path.join(dir_caso, _nombre_version(version, width))
        try:
            os.mkdir(destino)
            break
        except FileExistsError:
            if not auto:
                raise Rechazo(f"{cs.referencia_version(caso['case_id'], version, width)} ya existe: el recorder "
                              "nunca sobrescribe una version (graba sin `version` para la siguiente libre)") from None
            version = max(version + 1, _siguiente_version(dir_caso))
    _comprobar_contencion(store, [destino], raiz_proyecto)
    caso["version"] = version
    return destino


def _mover_version(store, tmp, destino, ficheros, meta_bytes, raiz_proyecto):
    """W (SIN bloqueo): mueve los ficheros ya escritos del temporal a la version reservada;
    `metadata.json` el ultimo. Antes vuelve a comprobar el `realpath` del destino (un enlace que
    aparezca despues de S1, gap #43)."""
    _comprobar_contencion(store, [destino], raiz_proyecto)
    os.mkdir(os.path.join(destino, "final"))
    for rel in ficheros:
        _reemplazar(os.path.join(tmp, rel), os.path.join(destino, rel))
    _escribir(os.path.join(tmp, "metadata.json"), meta_bytes)
    _reemplazar(os.path.join(tmp, "metadata.json"), os.path.join(destino, "metadata.json"))


def _leer_metadata_sin_enlace(dir_v):
    """`metadata.json` de una version (None si falta); `Rechazo` si es un enlace (gap #66)."""
    ruta = os.path.join(dir_v, "metadata.json")
    if _motivo_enlace(ruta, ruta):
        raise Rechazo(f"{os.path.basename(dir_v)}/metadata.json: {MOTIVO_ENLACE}")
    try:
        return _leer_json_reintentando(ruta)[0]
    except FileNotFoundError:
        return None


def _comprobar_supersedes(caso, dir_caso, width):
    """CA-12: la version que corrige un `corrected` (buscada por NUMERO, cualquier ancho: gap #60)
    debe existir COMPLETA (con `metadata.json`) y ser `failure` o `corrected` (gap #39)."""
    sup = caso.get("supersedes_case")
    if sup is None:
        return
    m = cs.PATRON_REFERENCIA.fullmatch(sup)
    nombres = _localizar_version(dir_caso, int(m.group(2)), width)
    if len(nombres) > 1:
        raise Rechazo("caso invalido: no se escribe nada", [{
            "campo": "supersedes_case", "mensaje": f"`{sup}`: version duplicada ({', '.join(nombres)}): ambigua"}])
    try:
        meta = _leer_metadata_sin_enlace(os.path.join(dir_caso, nombres[0])) if nombres else None
    except Rechazo as e:
        raise Rechazo("caso invalido: no se escribe nada", [{"campo": "supersedes_case", "mensaje": e.mensaje}]) from None
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
            meta = _leer_metadata_sin_enlace(os.path.join(store, "cases", nombre, nv))
        except (Rechazo, OSError, ValueError, RecursionError):
            continue
        if meta is None:
            continue
        if isinstance(meta, dict) and meta.get("case_id") != case_id:
            raise Rechazo(f"`cases/{nombre}` pertenece a `{meta.get('case_id')}`, no a `{case_id}`; no se escribe nada")
        return


def grabar(caso, config, raiz_proyecto=None, approved_by_human=False):
    """Graba `caso` como una version nueva. Devuelve `{case_id, version, ref, path, avisos}`;
    `Rechazo` si la capacidad esta apagada o el caso no vale, `BloqueoNoDisponible` (un
    `Transitorio`, exit 3) si el bloqueo no llega en S1, `RedaccionNoDisponible` sin `redact.py`:
    en todos esos casos no se escribe nada. Si el bloqueo no llega en S2 (la version ya esta en
    disco), se devuelve con un aviso: nunca se invita a reintentar despues de grabar (E2)."""
    config_activa(config, raiz_proyecto)
    raiz = _raiz(raiz_proyecto)
    if not isinstance(caso, dict):
        raise Rechazo("caso invalido: no se escribe nada", cs.validar_caso(caso, config))
    caso, errores = _plano(caso)                                            # 0. tipos JSON planos
    if errores:
        raise Rechazo("caso invalido: no se escribe nada", _errores_redactados(errores))
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
    store = raiz_store(config, raiz)
    auto = "version" not in caso
    if auto:                                                # pista; la definitiva, en S1
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
    ruta_bloqueo, ruta_indice = os.path.join(store, BLOQUEO_INDICE), os.path.join(store, INDICE)
    rutas = [ruta_bloqueo, ruta_indice, os.path.join(store, "cases"), dir_caso]
    # comprobaciones de solo lectura ANTES de escribir nada; las que dependen de otros escritores
    # (mayusculas, numero de version, enlaces) se repiten en S1
    _comprobar_contencion(store, rutas, raiz)
    _comprobar_fichero_propio(ruta_bloqueo)
    _comprobar_fichero_propio(ruta_indice)
    _comprobar_directorio_caso(store, fam, var, caso["case_id"])
    _comprobar_supersedes(caso, dir_caso, width)
    os.makedirs(os.path.join(store, "cases"), exist_ok=True)
    tmp = tempfile.mkdtemp(prefix=PREFIJO_TEMPORAL, dir=os.path.join(store, "cases"))
    try:
        _comprobar_contencion(store, [tmp], raiz)
        ficheros = _ficheros_de(caso)
        for rel, datos in ficheros.items():
            _escribir(os.path.join(tmp, rel), datos)
        with _Bloqueo(store):                                               # 4a. S1: reservar
            _comprobar_contencion(store, rutas, raiz)
            _comprobar_directorio_caso(store, fam, var, caso["case_id"])
            destino = _reservar(store, dir_caso, caso, width, auto, raiz)
        _mover_version(store, tmp, destino, ficheros, _json_bytes(_metadata(caso)), raiz)   # 4b. W
    finally:
        _limpiar_temporal(tmp)
    avisos = _indexar_alta(store, destino, caso, width)                     # 4c. S2: A
    return {"case_id": caso["case_id"], "version": caso["version"],
            "ref": cs.referencia_version(caso["case_id"], caso["version"], width), "path": destino, "avisos": avisos}


def _indexar_alta(store, destino, meta, width):
    """S2 (E1/E2): con el bloqueo, RELEE `validation.json` del disco (un `set-status` pudo entrar
    entre W y A) e indexa ESE estado. Cualquier fallo aqui —bloqueo que no llega, indice no
    escribible o ajeno, `validation.json` ilegible— deja la version grabada y devuelve un aviso."""
    ref = cs.referencia_version(meta["case_id"], meta["version"], width)
    rel = os.path.relpath(destino, store).replace(os.sep, "/")
    no_act = f"{INDICE} no actualizado para {ref} (la version YA esta grabada: no la vuelvas a grabar); reponlo con `index rebuild`"
    try:
        with _Bloqueo(store):
            val, _m, aviso = _leer_de_version(destino, "validation.json", rel)
            if aviso is None:
                errores = []
                cs._validar_validation(val, errores)
                if errores:
                    aviso = f"{rel}: validation.json incoherente ({errores[0]['campo']}: {errores[0]['mensaje']})"
            if aviso:
                return [f"{no_act}: {aviso}"]
            return _indexar(store, _entrada(meta, val["status"], _ahora()))
    except Rechazo as e:
        return [f"{no_act}: {e.mensaje}"]
    except OSError as e:
        return [f"{no_act}: {e}"]


# ------------------------------------------------------------------ indice cases_index.jsonl (T-06)

INDICE = "cases_index.jsonl"
BLOQUEO_INDICE = ".cases_index.lock"
BLOQUEO_REBUILD = ".cases_rebuild.lock"
CLAVES_INDICE = ("case_id", "version", "family", "variant", "status", "outcome", "updated_at")
ESPERA_BLOQUEO_S = 10.0
ESPERA_INICIAL_S = 0.005           # retroceso exponencial con jitter: 5 ms -> 50 ms (D-fix2 §4)
ESPERA_MAX_S = 0.05
REINTENTOS_REBUILD = 3             # identidad del indice cambiada durante F1 -> reintento acotado (E3)
GRACIA_EN_CURSO_S = 60.0           # «en curso» (E5)


class _Bloqueo:
    """Exclusion mutua entre recorders (hilos o procesos): `flock` en POSIX, `msvcrt.locking` en
    Windows, sobre `<root>/<nombre>` (fichero que no se borra): `.cases_index.lock` (secciones O(1)
    de los escritores y F0/F2 del `rebuild`) o `.cases_rebuild.lock` (serializa los `rebuild`). La
    espera sondea con retroceso exponencial y jitter; si no se obtiene en `ESPERA_BLOQUEO_S`,
    `BloqueoNoDisponible` (exit 3; quien lo pide no escribe nada). `solo_lectura` (`index check`)
    abre el fichero sin crearlo: si no existe, ningun escritor paso por aqui y no hay que excluir a
    nadie. El SO lo libera si el proceso muere: nunca queda un bloqueo huerfano."""

    def __init__(self, store, nombre=BLOQUEO_INDICE, solo_lectura=False):
        self.ruta = os.path.join(store, nombre)
        self.solo_lectura = solo_lectura
        self.f = None
        self.tomado = False

    def __enter__(self):
        _comprobar_fichero_propio(self.ruta)
        if self.solo_lectura:
            try:
                self.f = open(self.ruta, "rb")
            except FileNotFoundError:
                return self
        else:
            os.makedirs(os.path.dirname(self.ruta), exist_ok=True)
            self.f = open(self.ruta, "a+b")
        try:
            _comprobar_fd_propio(self.f, self.ruta)
        except Rechazo:
            self.f.close()
            raise
        limite = time.monotonic() + ESPERA_BLOQUEO_S
        espera = ESPERA_INICIAL_S
        while True:
            try:
                if _WINDOWS:
                    import msvcrt
                    self.f.seek(0)
                    msvcrt.locking(self.f.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(self.f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                self.tomado = True
                return self
            except OSError:
                restante = limite - time.monotonic()
                if restante <= 0:
                    self.f.close()
                    raise BloqueoNoDisponible(
                        f"otro proceso tiene el bloqueo del case store ({os.path.basename(self.ruta)}) desde hace mas de "
                        f"{ESPERA_BLOQUEO_S:g} s; no se ha escrito nada: reintenta") from None
                time.sleep(min(espera * random.uniform(0.5, 1.0), restante))
                espera = min(espera * 2, ESPERA_MAX_S)

    def __exit__(self, *_exc):
        if self.f is None:
            return False
        try:
            if self.tomado:
                if _WINDOWS:
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
    """Una linea al final del indice (append-only); CON el bloqueo ya tomado por el llamador. Abre
    el indice POR RUTA cada vez (nunca un descriptor cacheado: tras el `os.replace` de un `rebuild`
    la linea cae en el fichero nuevo, E3) y rechaza un indice con enlaces duros (gap #63). Si el
    fichero no termina en `\\n` (escritor muerto a mitad de linea), se antepone uno (gap #42)."""
    ruta = os.path.join(store, INDICE)
    _comprobar_fichero_propio(ruta)
    with open(ruta, "a+b") as f:
        _comprobar_fd_propio(f, ruta)
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
    """Anade la linea del cambio (bloqueo ya tomado); si el indice no se puede escribir (E/S, o un
    indice ajeno), el cambio YA esta en disco: se devuelve un aviso (el indice es una cache:
    `index rebuild` lo repone) en vez de fallar, para que nadie reintente y duplique."""
    try:
        _anadir_linea(store, entrada)
        return []
    except (OSError, Rechazo) as e:
        return [f"{INDICE} no actualizado ({getattr(e, 'mensaje', e)}); reponlo con `index rebuild`"]


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


def _parsear_linea(cruda):
    """`(entrada, motivo)` de una linea del indice."""
    try:
        e = json.loads(cruda.decode("utf-8"))
        motivo = _entrada_valida(e)
    except RecursionError:
        e, motivo = None, "anidamiento excesivo"
    except (ValueError, UnicodeDecodeError):
        e, motivo = None, "JSON ilegible"
    return e, motivo


def leer_indice(store, hasta=None, desde=0):
    """`(entradas, avisos)` en UNA pasada en streaming (linea a linea, gap #34): la ULTIMA linea
    valida por `(case_id, version)` (orden de aparicion) y un aviso por cada linea corrupta, que se
    ignora (nunca rompe la lectura). Las lineas vacias o de solo espacios se saltan sin aviso.
    `desde`/`hasta`: rango de bytes (F1 lee hasta `offset0`; F2, la cola desde `offset0`)."""
    entradas, avisos = {}, []
    ruta = os.path.join(store, INDICE)
    try:
        f = _abrir_reintentando(ruta)
    except FileNotFoundError:
        return entradas, avisos
    except OSError as e:
        return entradas, [f"{INDICE} ilegible: {e}"]
    with f:
        if desde:
            f.seek(desde)
        pos = desde
        n = 0
        for cruda in f:
            if hasta is not None and pos >= hasta:
                break
            pos += len(cruda)
            n += 1
            if not cruda.strip():
                continue
            e, motivo = _parsear_linea(cruda)
            if motivo:
                donde = f"linea {n}" if not desde else f"linea {n} de la cola (byte {desde})"
                avisos.append(f"{INDICE} {donde} ignorada: {motivo}")
                continue
            entradas[(e["case_id"], e["version"])] = e
    return entradas, avisos


def _iso(ts):
    return datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _leer_de_version(dir_v, fichero, rel):
    """`(objeto, mtime, aviso)` de un fichero de version, con `lstat` ANTES de abrir: distingue
    «falta» (a medio escribir), «enlace» (no se lee a traves de el, gap #66), «no es un fichero
    regular» (sin reintentos, gap #59), «no legible tras N reintentos (bloqueada o sin permisos)»
    e «ilegible» (JSON roto)."""
    ruta = os.path.join(dir_v, fichero)
    try:
        st = _stat_sin_seguir(ruta)
    except FileNotFoundError:
        que = "a medio escribir o grabacion interrumpida" if fichero == "metadata.json" else "danada"
        return None, None, f"{rel} incompleta: sin {fichero} ({que}); se conserva, reparala o graba otra version"
    except OSError as e:
        return None, None, f"{rel} ilegible: {fichero} no se puede examinar ({e})"
    if _motivo_enlace(ruta, ruta) if _es_enlace_st(st) is None else _es_enlace_st(st):
        return None, None, f"{rel} omitida: {fichero} es un {MOTIVO_ENLACE}"
    if not stat.S_ISREG(st.st_mode):
        return None, None, f"{rel} ilegible: {fichero} no es un fichero regular"
    try:
        obj, mtime = _leer_json_reintentando(ruta)
        return obj, mtime, None
    except FileNotFoundError:
        return None, None, f"{rel} incompleta: sin {fichero} (desaparecio al leerla)"
    except PermissionError as e:
        return None, None, (f"{rel} ilegible: {fichero} no legible tras {REINTENTOS} reintentos "
                            f"(bloqueada o sin permisos): {e}")
    except (OSError, ValueError, RecursionError) as e:
        return None, None, f"{rel} ilegible: {fichero} no es JSON valido ({type(e).__name__})"


def _edad(mtime):
    return _reloj() - mtime


def _estado_version(store, nombre, dir_caso, numero, nombres, entrada_dir=None):
    """Estado de UNA version desde el disco: `(entrada|None, aviso|None, en_curso, mtime_meta)`."""
    if len(nombres) > 1:
        return None, f"cases/{nombre}: version {numero} duplicada ({', '.join(sorted(nombres))}): se omiten", False, None
    dir_v = os.path.join(dir_caso, nombres[0])
    rel = f"cases/{nombre}/{nombres[0]}"
    motivo = _motivo_enlace(entrada_dir if entrada_dir is not None else dir_v, dir_v)
    if motivo:
        return None, f"{rel} omitida: {motivo}", False, None
    meta, mtime_meta, aviso = _leer_de_version(dir_v, "metadata.json", rel)
    if aviso and meta is None and "sin metadata.json" in aviso and "incompleta" in aviso:
        try:
            mtime_dir = _stat_sin_seguir(entrada_dir if entrada_dir is not None else dir_v).st_mtime
        except OSError:
            mtime_dir = None
        if mtime_dir is not None:
            edad = _edad(mtime_dir)
            if edad < 0:
                return None, (f"{rel} incompleta: sin metadata.json y con mtime futuro ({_iso(mtime_dir)}): no puede "
                              "estar en curso; reparala o graba otra version"), False, None
            if edad < GRACIA_EN_CURSO_S:
                return None, (f"{rel} en curso: sin metadata.json, directorio modificado hace {edad:.0f} s "
                              f"(< {GRACIA_EN_CURSO_S:g} s): una grabacion en marcha"), True, None
        return None, aviso, False, None
    if aviso is None:
        val, mtime, aviso = _leer_de_version(dir_v, "validation.json", rel)
    if aviso:
        return None, aviso, False, None
    errores_val = []
    cs._validar_validation(val, errores_val)
    if errores_val:
        return None, (f"{rel} omitida: validation.json incoherente ({errores_val[0]['campo']}: "
                      f"{errores_val[0]['mensaje']}); no se indexa"), False, None
    try:
        e = _entrada(meta, val.get("status"), _iso(mtime))
    except (AttributeError, KeyError, TypeError):
        return None, f"{rel} omitida: metadata.json incompleto", False, None
    if f"{e['family']}.{e['variant']}" != nombre or e["version"] != numero or _entrada_valida(e):
        return None, f"{rel} omitida: metadata.json no casa con su ruta o con el esquema", False, None
    return e, None, False, mtime_meta


def _estado_de_cases(store, raiz_proyecto=None):
    """`(entradas, avisos, en_curso, mtimes_meta)` recorriendo `cases/` (la FUENTE). `avisos` y
    `en_curso` son dicts `rel -> texto`. Enlaces detectados por ENTRADA sin `realpath` (E4); solo
    `cases/` se resuelve (una vez)."""
    entradas, avisos, en_curso, mtimes = {}, {}, {}, {}
    base = os.path.join(store, "cases")
    if not os.path.lexists(base):
        return entradas, avisos, en_curso, mtimes
    motivo = _motivo_enlace(base, base) or _escapa(store, base, raiz_proyecto)
    if motivo:
        avisos["cases"] = f"cases/ omitido: {motivo}"
        return entradas, avisos, en_curso, mtimes
    try:
        with os.scandir(base) as it:
            casos = sorted(((e.name, e.path, e) for e in it if not e.name.startswith(".") and e.is_dir()),
                           key=lambda t: t[0])
    except OSError:
        return entradas, avisos, en_curso, mtimes
    for nombre, dir_caso, entrada_caso in casos:
        motivo = _motivo_enlace(entrada_caso, dir_caso)
        if motivo:
            avisos[f"cases/{nombre}"] = f"cases/{nombre} omitido: {motivo}"
            continue
        por_numero = {}
        for v, n, ent in _entradas_version(dir_caso):
            por_numero.setdefault(v, []).append((n, ent))
        for v, lista in sorted(por_numero.items()):
            nombres = [n for n, _e in lista]
            e, aviso, curso, mtime_meta = _estado_version(store, nombre, dir_caso, v, nombres,
                                                          lista[0][1] if len(lista) == 1 else None)
            rel = f"cases/{nombre}/{nombres[0]}"
            if curso:
                en_curso[rel] = aviso
            elif aviso:
                avisos[rel] = aviso
            else:
                entradas[(e["case_id"], e["version"])] = e
                mtimes[(e["case_id"], e["version"])] = mtime_meta
    return entradas, avisos, en_curso, mtimes


def estado_de_cases(store, raiz_proyecto=None):
    """`(entradas, avisos)` recorriendo `cases/` (la FUENTE; el indice es cache). Se omiten con
    aviso: versiones incompletas o «en curso» (sin `metadata.json`/`validation.json`), enlazadas,
    con ficheros que no son regulares, bloqueadas o ilegibles, duplicadas (mismo numero con dos
    anchos), incoherentes con su ruta o con el esquema y `validation.json` incoherente con
    `case_schema` (p. ej. `approved` sin humano, gap #45). `updated_at` = mtime de `validation.json`."""
    entradas, avisos, en_curso, _m = _estado_de_cases(store, raiz_proyecto)
    return entradas, list(avisos.values()) + list(en_curso.values())


def _stat_indice(ruta):
    return os.stat(ruta)


def _hash_prefijo(ruta, n):
    h = hashlib.sha256()
    with _abrir_reintentando(ruta) as f:
        while n > 0:
            trozo = f.read(min(n, 1 << 20))
            if not trozo:
                break
            h.update(trozo)
            n -= len(trozo)
    return h.hexdigest()


def _identidad(ruta):
    """`(st_dev, st_ino, tamano, hash|None)` del indice, o None si no existe. Con `st_ino == 0`
    (FAT/SMB: sin identidad fiable) se anade el hash de sus bytes (E3)."""
    try:
        st = _stat_indice(ruta)
    except FileNotFoundError:
        return None
    return (st.st_dev, st.st_ino, st.st_size, None if st.st_ino else _hash_prefijo(ruta, st.st_size))


def _misma_identidad(ruta, ident0):
    """True si el indice sigue siendo el de F0 (mismo fichero, no mas corto; con `st_ino == 0`, mismos
    bytes hasta `offset0`). Un indice ausente en F0 no dispara el reintento (E3)."""
    if ident0 is None:
        return True
    cur = _identidad(ruta)
    if cur is None or cur[:2] != ident0[:2] or cur[2] < ident0[2]:
        return False
    if not ident0[1]:
        return _hash_prefijo(ruta, ident0[2]) == ident0[3]
    return True


def _releer_de_linea(store, linea):
    """E3: la version que nombra una linea de la cola, RELEIDA del disco: `(entrada|None, aviso|None)`.
    O(1): localiza el directorio por numero (cualquier ancho) sin recorrer el caso."""
    fam, var, numero = linea["family"], linea["variant"], linea["version"]
    try:
        cs.directorio_version(fam, var, 1)
    except ValueError:
        return None, f"{INDICE}: linea de la cola con family/variant que no son un directorio seguro: se ignora"
    nombre = f"{fam}.{var}"
    base, dir_caso = os.path.join(store, "cases"), os.path.join(store, "cases", nombre)
    for ruta in (base, dir_caso):
        motivo = _motivo_enlace(ruta, ruta)
        if motivo:
            return None, f"{os.path.relpath(ruta, store).replace(os.sep, '/')} omitido: {motivo}"
    nombres = _localizar_version(dir_caso, numero)
    if not nombres:
        return None, f"{linea['case_id']}@v{numero}: en la cola del indice pero no en cases/"
    e, aviso, curso, _m = _estado_version(store, nombre, dir_caso, numero, nombres)
    if e is not None and e["case_id"] != linea["case_id"]:
        return None, f"cases/{nombre}/{nombres[0]}: la linea de la cola dice `{linea['case_id']}` y metadata.json `{e['case_id']}`"
    return e, (aviso if not curso else None)


def reconstruir_indice(store, raiz_proyecto=None):
    """Reescribe `cases_index.jsonl` desde `cases/` en tres fases (D-fix2 §3 + E3), serializado por
    `.cases_rebuild.lock` (tomado ANTES que el del indice): F0 (bloqueo, O(1)) anota tamano e
    identidad; F1 (SIN bloqueo) recorre `cases/` y escribe las lineas en un temporal hermano,
    conservando el `updated_at` de la ultima linea valida (hasta `offset0`) si su estado coincide;
    F2 (bloqueo, O(cola)) comprueba la identidad, RELEE del disco cada version que aparece en la
    cola y anade esas lineas al temporal, y lo sustituye con `os.replace`. Identidad cambiada ->
    reintento acotado y despues `Transitorio`; `PermissionError` al sustituir -> `Transitorio` sin
    tocar el indice. Devuelve `(n_versiones, avisos)`."""
    raiz = _raiz(raiz_proyecto)
    ruta = os.path.join(store, INDICE)
    _comprobar_contencion(store, [os.path.join(store, BLOQUEO_INDICE), os.path.join(store, BLOQUEO_REBUILD), ruta], raiz)
    os.makedirs(store, exist_ok=True)
    with _Bloqueo(store, BLOQUEO_REBUILD):
        for _intento in range(REINTENTOS_REBUILD):
            with _Bloqueo(store):                                               # F0
                ident0 = _identidad(ruta)
            offset0 = ident0[2] if ident0 else 0
            fuente, avisos = estado_de_cases(store, raiz)                       # F1
            previas, _ = leer_indice(store, hasta=offset0) if offset0 else ({}, [])
            claves = set()
            lineas = []
            for clave in sorted(fuente, key=lambda k: (fuente[k]["family"], fuente[k]["variant"], k[1])):
                e = dict(fuente[clave])
                p = previas.get(clave)
                if p and all(p[k] == e[k] for k in CLAVES_INDICE if k != "updated_at"):
                    e["updated_at"] = p["updated_at"]
                lineas.append(_linea(e))
                claves.add(clave)
            fd, tmp = tempfile.mkstemp(prefix=PREFIJO_TEMPORAL, dir=store)
            try:
                with os.fdopen(fd, "wb") as f:
                    f.write(b"".join(lineas))
                with _Bloqueo(store):                                           # F2
                    if not _misma_identidad(ruta, ident0):
                        continue
                    cola, avisos_cola = leer_indice(store, desde=offset0)
                    avisos += avisos_cola
                    extra = []
                    for clave, linea in cola.items():
                        e, aviso = _releer_de_linea(store, linea)
                        if e is None:
                            if aviso:
                                avisos.append(aviso)
                            continue
                        if all(linea[k] == e[k] for k in CLAVES_INDICE if k != "updated_at"):
                            e["updated_at"] = linea["updated_at"]
                        extra.append(_linea(e))
                        claves.add(clave)
                    with open(tmp, "ab") as f:
                        f.write(b"".join(extra))
                    try:
                        _reemplazar(tmp, ruta)
                    except PermissionError as e:
                        raise Transitorio(f"{INDICE} en uso por otro proceso al sustituirlo ({e}); no se ha tocado: "
                                          "reintenta el rebuild") from None
                return len(claves), avisos
            finally:
                _limpiar_temporal(tmp)
    raise Transitorio(f"{INDICE} cambio de identidad (sustituido o truncado) durante el rebuild {REINTENTOS_REBUILD} "
                      "veces seguidas; no se ha tocado: reintenta")


def comprobar_indice_detalle(store, width=cs.VERSION_WIDTH_DEFECTO, raiz_proyecto=None):
    """`(diferencias, en_curso)` entre el indice y `cases/`, con el esquema de F0/F1/F2 del rebuild
    SIN escribir (E5): tamano del indice (bloqueo de solo lectura, si existe el fichero), recorrido
    de `cases/`, y la cola (lineas anadidas durante el recorrido) releyendo del disco lo que toca,
    ANTES de reportar. `diferencias` vacia = coherente (exit 0); `en_curso` es informativo."""
    raiz = _raiz(raiz_proyecto)
    ruta = os.path.join(store, INDICE)
    for _intento in range(REINTENTOS_REBUILD):
        with _Bloqueo(store, solo_lectura=True):                                # F0
            ident0 = _identidad(ruta)
        offset0 = ident0[2] if ident0 else 0
        fuente, avisos, en_curso, mtimes = _estado_de_cases(store, raiz)        # F1
        indice, avisos_idx = leer_indice(store, hasta=offset0) if offset0 else ({}, [])
        with _Bloqueo(store, solo_lectura=True):                                # F2
            if not _misma_identidad(ruta, ident0):
                continue
            cola, avisos_cola = leer_indice(store, desde=offset0)
            for clave, linea in cola.items():
                indice[clave] = linea
                e, aviso = _releer_de_linea(store, linea)
                if e is not None:
                    fuente[clave] = e
                    mtimes[clave] = None
                    for d in (avisos, en_curso):
                        for rel in [r for r in d if r.startswith(f"cases/{e['family']}.{e['variant']}/v")
                                    and _es_version(r.rsplit("/", 1)[1]) and int(r.rsplit("/", 1)[1][1:]) == clave[1]]:
                            del d[rel]
                elif aviso:
                    avisos[f"cola:{clave}"] = aviso
        break
    else:
        raise Transitorio(f"{INDICE} cambio de identidad durante `index check` {REINTENTOS_REBUILD} veces seguidas: reintenta")
    difs = list(avisos.values()) + avisos_idx + avisos_cola
    curso = list(en_curso.values())
    for clave in sorted(set(fuente) | set(indice), key=lambda k: (k[0], k[1])):
        ref = cs.referencia_version(clave[0], clave[1], width)
        if clave not in indice:
            m = mtimes.get(clave)
            if m is not None and 0 <= _edad(m) < GRACIA_EN_CURSO_S:
                curso.append(f"{ref}: en curso: esta en cases/ y aun no en el indice (metadata.json de hace "
                             f"{_edad(m):.0f} s, < {GRACIA_EN_CURSO_S:g} s)")
            else:
                difs.append(f"{ref}: esta en cases/ pero no en el indice")
        elif clave not in fuente:
            difs.append(f"{ref}: esta en el indice pero no en cases/")
        else:
            for k in CLAVES_INDICE:
                if k != "updated_at" and fuente[clave][k] != indice[clave][k]:
                    difs.append(f"{ref}: {k} es `{indice[clave][k]}` en el indice y `{fuente[clave][k]}` en cases/")
    return difs, curso


def comprobar_indice(store, width=cs.VERSION_WIDTH_DEFECTO, raiz_proyecto=None):
    """Diferencias entre el indice y `cases/` (lista vacia = coherente): lineas corruptas y todo lo
    que el recorrido omite (versiones incompletas, duplicadas, enlazadas, ilegibles, incoherentes)
    cuentan como incoherencia (gap #37); lo «en curso» no (ver `comprobar_indice_detalle`)."""
    return comprobar_indice_detalle(store, width, raiz_proyecto)[0]


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


def _ficheros_sin_enlace(destino, ref):
    """#66: `metadata.json`/`validation.json` que sean enlace se rechazan ANTES de leerlos."""
    for fichero in ("metadata.json", "validation.json"):
        ruta = os.path.join(destino, fichero)
        try:
            st = _stat_sin_seguir(ruta)
        except FileNotFoundError:
            raise Rechazo(f"{ref} no existe en el case store (o esta a medio escribir)") from None
        es = _es_enlace_st(st)
        if es or (es is None and _motivo_enlace(ruta, ruta)):
            raise Rechazo(f"{ref}: {fichero} es un {MOTIVO_ENLACE}; no se lee ni se escribe")
        if not stat.S_ISREG(st.st_mode):
            raise Rechazo(f"{ref}: {fichero} no es un fichero regular; no se escribe nada")


def cambiar_estado(case_id, version, status, config, raiz_proyecto=None, approved_by_human=False, reviewer_note=None):
    """Cambia `validation.status` de una version grabada. Solo reescribe `validation.json` (de forma
    atomica); el resto de la version es inmutable. `approved` (Gold) exige `approved_by_human is
    True` (`--approved-by-human`): sin el, `Rechazo` con mensaje explicito. `needs_changes`,
    `rejected` y `pending` no lo requieren y dejan `approved_by_human: false`. Sin `reviewer_note`
    se conserva la nota anterior; la nueva se redacta. La version se localiza por NUMERO (cualquier
    ancho, gap #60). Lectura, escritura de `validation.json` y su linea del indice van bajo el MISMO
    bloqueo (gap #35, O(1)); `metadata.json` se lee y valida antes de escribir nada (gap #36).
    Devuelve `{case_id, version, ref, status, path, avisos}`."""
    config_activa(config, raiz_proyecto)
    raiz = _raiz(raiz_proyecto)
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
    store = raiz_store(config, raiz)
    dir_caso = os.path.join(store, "cases", f"{family}.{variant}")
    ruta_bloqueo, ruta_indice = os.path.join(store, BLOQUEO_INDICE), os.path.join(store, INDICE)
    rutas_base = [ruta_bloqueo, ruta_indice, os.path.join(store, "cases"), dir_caso]
    _comprobar_contencion(store, rutas_base, raiz)
    nombres = _localizar_version(dir_caso, version, width)
    if len(nombres) > 1:
        raise Rechazo(f"{ref}: version {version} duplicada ({', '.join(nombres)}): ambigua; no se cambia el estado")
    if not nombres:
        raise Rechazo(f"{ref} no existe en el case store (o esta a medio escribir)")
    destino = os.path.join(dir_caso, nombres[0])
    ruta_meta, ruta_val = os.path.join(destino, "metadata.json"), os.path.join(destino, "validation.json")
    nota = redactar_estructura(reviewer_note) if reviewer_note is not None else None
    rutas = rutas_base + [destino]
    _comprobar_contencion(store, rutas, raiz)
    _comprobar_fichero_propio(ruta_indice)
    _ficheros_sin_enlace(destino, ref)
    with _Bloqueo(store):
        _comprobar_contencion(store, rutas, raiz)
        _comprobar_fichero_propio(ruta_indice)
        _ficheros_sin_enlace(destino, ref)
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


def _avisar(avisos, prefijo="aviso"):
    for a in avisos:
        print(f"{prefijo}: {a}", file=sys.stderr)


def _comunes(p):
    p.add_argument("--config", help="training.json del proyecto (default: <project-root>/.claude/knowledge-services/training.json)")
    p.add_argument("--project-root", help="raiz del proyecto (default: deducida de --config o cwd)")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Recorder determinista de casos (training-data-services). Exit 0 ok, "
                                             "1 rechazo, 2 uso/E/S, 3 transitorio (bloqueo o indice cambiado: reintenta).")
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
            difs, en_curso = comprobar_indice_detalle(store, width, raiz)
            _avisar(en_curso, "info")
            if difs:
                for d in difs:
                    print(f"{INDICE}: {d}")
                print(f"{len(difs)} diferencia(s): reconstruye con `index rebuild`", file=sys.stderr)
                return 1
            print(f"OK {INDICE} coherente con cases/" + (f" ({len(en_curso)} en curso)" if en_curso else ""))
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
    except Transitorio as e:
        # E2: exit 3 SOLO si no se escribio nada (S1 de record, set-status, F0/F2 de rebuild): reintentar es seguro
        print(f"transitorio: {e.mensaje}", file=sys.stderr)
        print("no se ha escrito nada: reintenta (exit 3)", file=sys.stderr)
        return 3
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
