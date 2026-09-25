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
  4. solo entonces escribe, en dos secciones CORTAS con el bloqueo (D-fix2 E1 + D-fix3 §1/F1): FUERA
     del bloqueo, el recorrido O(C) de mayusculas (la existencia del caso sale del nombre EXACTO de
     `scandir`), el dueño del directorio, la PISTA de la version (O(V)) y los ficheros en un temporal
     `cases/.tmp-*` creados con `O_EXCL` (gap #77); S1 (bloqueo, O(1) en C y V) prueba el numero con
     sus <= 9 anchos y hace `os.mkdir` (mas de 64 numeros ocupados -> suelta, recalcula la pista y
     reintenta, acotado; si no, exit 3), y repite el recorrido de mayusculas SOLO para un caso nuevo;
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
  - `index rebuild`, serializado por `<root>/.cases_rebuild.lock` (se toma ANTES que el del indice;
    los escritores nunca lo toman): F0 (bloqueo, O(1)) anota la identidad del indice y su offset;
    F1 (SIN bloqueo) recorre `cases/`; pasadas SIN bloqueo releen del disco las claves distintas de
    la cola nueva (E3), comprobando la identidad en cada una, hasta que una lee <= 64 lineas o tras
    8 (nunca exit 3 por trafico); F2 (bloqueo, O(bytes del residual), sin relecturas) comprueba la
    identidad, copia el residual TAL CUAL (lineas validas) y sustituye el indice. Limite declarado
    (E3 ampliado por F2): un `set-status` muerto entre W y A cuya clave caiga en el residual queda
    igual que sin rebuild; `index check` lo reporta.
  - `index check` nunca toma `.cases_index.lock` (F3: no bloquea a los escritores): mismo esquema
    sin escribir, con una confirmacion final que relee la cola nueva y, del disco, lo que difiere, y
    comprueba la identidad. Exit 1 si hay alguna diferencia: una version en `cases/` y no en el
    indice (o al reves), un campo distinto, una linea corrupta del indice, un temporal huerfano
    (`.tmp-*` de la raiz, de `cases/` o de un caso, de hace >= 60 s o con `mtime` futuro), una
    entrada con nombre de version que no es un directorio (fichero, enlace roto), y toda version que
    el recorrido omite: incompleta (sin `metadata.json` o `validation.json`), duplicada (mismo
    numero con dos anchos), enlazada (symlink/junction), con un fichero que no es un fichero regular
    o que es un enlace duro, no legible tras los reintentos (bloqueada o sin permisos), JSON
    ilegible, `metadata.json` que no casa con su ruta o con el esquema, o `validation.json`
    incoherente. Es INFORMATIVO (exit 0) lo que esta «en curso»: una version sin `metadata.json`
    cuyo directorio se modifico hace menos de `GRACIA_EN_CURSO_S` (60 s), una completa sin linea con
    `metadata.json` de hace menos de 60 s, o un temporal reciente; un `mtime` futuro nunca esta «en
    curso». Bajo escritura muy intensa cabe un falso positivo transitorio (un segundo `check` ya no
    lo ve).
  - Las lineas corruptas se ignoran con aviso al leer; se lee en streaming (linea a linea).
  - Los lectores detectan enlaces por entrada sin `realpath` (`is_symlink()` o el bit «name
    surrogate» de `st_reparse_tag`; un placeholder de OneDrive no es enlace).

Bloqueo `<root>/.cases_index.lock` (`flock`/`msvcrt`, fichero que no se borra nunca): solo protege
secciones O(1) (una linea del indice, un `validation.json`, la reserva de una version, F0) y el
residual de F2. Espera con retroceso exponencial y jitter (5 -> 50 ms) hasta `ESPERA_BLOQUEO_S`; si
no llega, no se escribe nada (`BloqueoNoDisponible`, exit 3: transitorio, reintenta). Solo la
contencion es transitoria: no poder abrirlo o un fallo que no es contencion (`ENOLCK`) es
permanente (exit 2, gap #76). El SO lo libera al morir el proceso.

Estructura (`case_schema.directorio_version`, ancho `ids.version_width`):
  <root>/cases/<family>.<variant>/v<NNN>/{metadata.json, request.json ({"request": ...}),
  context.json, constraints.json, trajectory.jsonl, metrics.json, validation.json,
  final/artifacts.json}  — JSON UTF-8 sin escapar (`ensure_ascii=False`), fin de linea LF.

Uso (exit 0 ok · 1 rechazo/validacion · 2 uso/JSON ilegible/error de E/S o permanente: permisos,
solo lectura, sin bloqueos · 3 transitorio: no se escribio nada, reintenta). Exit 3 por subcomando:
`record` (el bloqueo de S1 no llego, o mas de 64 numeros ocupados 3 veces seguidas), `set-status`
(el bloqueo no llego), `index rebuild` (algun bloqueo no llego, o la identidad del indice cambio 3
veces seguidas), `index check` (la identidad del indice cambio 3 veces seguidas); `list`, nunca:
  case-recorder.py record <caso.json> [--config <training.json>] [--project-root <dir>] [--approved-by-human]
  case-recorder.py set-status <case_id> <version> <status> [--approved-by-human] [--note <texto>] [...]
  case-recorder.py index {rebuild|check} [...]     # check: exit 1 si el indice difiere de cases/
  case-recorder.py list [--status S] [--family F] [--outcome O] [--json] [...]
"""
import argparse
import datetime
import errno
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


MENSAJE_NO_UTF8 = "texto no codificable en UTF-8 (surrogate suelto): el caso debe ser texto Unicode valido"


def _codificable(texto):
    try:
        texto.encode("utf-8")
        return True
    except UnicodeEncodeError:
        return False


def _errores_no_codificables(caso):
    """gap #73: toda cadena (valor o CLAVE) que se escribiria debe codificarse en UTF-8; un surrogate
    suelto (U+D800..U+DFFF sin pareja) acabaria en `UnicodeEncodeError` al escribir. Tambien dentro
    de un `arguments` en texto JSON (su escape reaparece al parsearlo). Iterativo."""
    errores, pila = [], [("", caso)]
    while pila:
        campo, v = pila.pop()
        if isinstance(v, str):
            if not _codificable(v):
                errores.append({"campo": campo or "(caso)", "mensaje": MENSAJE_NO_UTF8})
        elif isinstance(v, dict):
            for k, x in v.items():
                if isinstance(k, str) and not _codificable(k):
                    errores.append({"campo": campo or "(caso)", "mensaje": f"clave: {MENSAJE_NO_UTF8}"})
                    continue
                sub = f"{campo}.{k}" if campo else str(k)
                pila.append((sub, x))
                if k == "arguments" and isinstance(x, str):
                    try:
                        pila.append((sub, json.loads(x)))
                    except (ValueError, RecursionError):
                        pass
        elif isinstance(v, list):
            pila.extend((f"{campo}[{i}]", x) for i, x in enumerate(v))
    return errores


def _errores_extra(caso):
    errores = _errores_no_finitos(caso) + _errores_arguments_ambiguos(caso) + _errores_no_codificables(caso)
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


def _tipo_entrada(x, ruta):
    """EL criterio de «entrada de version» (gap #74), compartido por el recorrido (`scandir`) y por
    `_localizar_version` (`lstat`): `"dir"` (directorio real: una version), `"enlace"` (symlink o
    junction, rota o no: nunca se sigue) u `"otro"` (fichero suelto u otra cosa); None si no existe.
    Solo `"dir"` es una version; lo demas no cuenta como duplicado e `index check` lo reporta."""
    try:
        st = _stat_sin_seguir(x)
    except FileNotFoundError:
        return None
    except OSError:
        return "otro"
    es = _es_enlace_st(st)
    if es is None:
        es = _motivo_enlace(x, ruta) == MOTIVO_ENLACE
    if es:
        return "enlace"
    return "dir" if stat.S_ISDIR(st.st_mode) else "otro"


def _escanear_caso(dir_caso):
    """`(entradas, temporales)` de `dir_caso` en UN `scandir`: `entradas` = `[(numero, nombre,
    DirEntry, tipo)]` de todo nombre `v<digitos>` (cualquier ancho y tipo, gap #74) y `temporales` =
    los `DirEntry` `.tmp-*` (gap #80)."""
    entradas, temporales = [], []
    try:
        with os.scandir(dir_caso) as it:
            for e in it:
                if _es_version(e.name):
                    entradas.append((int(e.name[1:]), e.name, e, _tipo_entrada(e, e.path)))
                elif e.name.startswith(PREFIJO_TEMPORAL):
                    temporales.append(e)
    except OSError:
        pass
    return entradas, temporales


def _entradas_version(dir_caso):
    """`[(numero, nombre, DirEntry, tipo)]` de los nombres `v<digitos>` de `dir_caso` (gap #46: con
    `os.scandir`, sin un `isdir` por entrada)."""
    return _escanear_caso(dir_caso)[0]


def _dirs_version(dir_caso):
    """`[(numero, nombre)]` de las VERSIONES (directorios reales `v<digitos>`) de `dir_caso`."""
    return [(n, nombre) for n, nombre, _e, tipo in _entradas_version(dir_caso) if tipo == "dir"]


def versiones(dir_caso):
    """Versiones (enteros) presentes en `cases/<family>.<variant>/`, completas o no."""
    return sorted(n for n, _nombre in _dirs_version(dir_caso))


def _siguiente_version(dir_caso):
    """PISTA de la siguiente version (fuera del bloqueo, O(V)): mayor numero OCUPADO + 1, contando
    tambien lo que no es version (un `mkdir` sobre ese nombre fallaria igual)."""
    ns = [n for n, _nombre, _e, _t in _entradas_version(dir_caso)]
    return (max(ns) + 1) if ns else 1


def _nombre_version(version, width):
    return os.path.basename(cs.directorio_version("x", "y", version, width))


def _ocupantes_version(dir_caso, version, width=cs.VERSION_WIDTH_DEFECTO):
    """`{nombre: tipo}` de lo que existe para el NUMERO `version` con cualquier ancho (gaps #40/#60,
    F1): un `lstat` por ancho posible (<= 9), O(1) sea cual sea el numero de versiones del caso."""
    anchos = range(len(str(version)), max(len(str(VERSION_MAX)), width) + 1)
    ocupantes = {}
    for w in anchos:
        nombre = f"v{version:0{w}d}"
        if nombre not in ocupantes:
            ruta = os.path.join(dir_caso, nombre)
            tipo = _tipo_entrada(ruta, ruta)
            if tipo is not None:
                ocupantes[nombre] = tipo
    return ocupantes


def _localizar_version(dir_caso, version, width=cs.VERSION_WIDTH_DEFECTO):
    """Nombres de las VERSIONES (directorios reales, gap #74) del NUMERO `version` con cualquier ancho."""
    return [n for n, tipo in _ocupantes_version(dir_caso, version, width).items() if tipo == "dir"]


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


class _TemporalManipulado(Rechazo):
    """Un fichero del temporal ya existia al crearlo (p. ej. un enlace duro plantado, gap #77)."""


def _escribir_nuevo(ruta, datos):
    """Crea `ruta` con `O_CREAT | O_EXCL` (`"xb"`, gap #77): si ya existe —un enlace duro o simbolico
    plantado en el temporal mientras se esperaba el bloqueo— no se escribe a traves de el."""
    try:
        with open(ruta, "xb") as f:
            f.write(datos)
    except FileExistsError:
        raise _TemporalManipulado(f"{os.path.basename(os.path.dirname(ruta))}/{os.path.basename(ruta)} ya existia en el "
                                  "temporal (¿enlace plantado?, CWE-59/367); no se escribe a traves de el") from None


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


SALTOS_MAX_S1 = 64                 # F1: numeros ocupados que S1 salta con el bloqueo antes de soltarlo
REINTENTOS_S1 = 3                  # ... y veces que recalcula la pista fuera del bloqueo (luego exit 3)


def _reservar(store, dir_caso, caso, width, auto, raiz_proyecto):
    """S1 (con el bloqueo, O(1) en C y en V_caso: D-fix3 §1 + F1): parte de la PISTA calculada fuera
    del bloqueo; «mismo numero con otro ancho» (#40a) por `_ocupantes_version` (<= 9 `lstat`, cubre un
    `v0000001` a mano) y `os.mkdir` del destino (falla si existe: nadie pisa a nadie). En automatico,
    un numero ocupado se salta; mas de `SALTOS_MAX_S1` saltos -> None (el llamador suelta el bloqueo
    y recalcula la pista). Tras crearlo se comprueba su `realpath`. Devuelve la ruta."""
    os.makedirs(dir_caso, exist_ok=True)
    version, saltos = caso["version"], 0
    while True:
        ocupado = bool(_ocupantes_version(dir_caso, version, width))
        destino = os.path.join(dir_caso, _nombre_version(version, width))
        if not ocupado:
            try:
                os.mkdir(destino)
                break
            except FileExistsError:
                ocupado = True
        if not auto:
            raise Rechazo(f"{cs.referencia_version(caso['case_id'], version, width)} ya existe (con este u otro "
                          "ancho de version): el recorder nunca sobrescribe una version (graba sin `version` para "
                          "la siguiente libre)")
        saltos += 1
        if saltos > SALTOS_MAX_S1:
            return None
        version += 1
    _comprobar_contencion(store, [destino], raiz_proyecto)
    caso["version"] = version
    return destino


def _mover_version(store, tmp, destino, ficheros, raiz_proyecto):
    """W (SIN bloqueo): mueve los ficheros ya escritos del temporal a la version reservada;
    `metadata.json` el ultimo. Antes vuelve a comprobar el `realpath` del temporal y del destino
    (un enlace que aparezca despues de S1, gaps #43/#75-M15)."""
    _comprobar_contencion(store, [tmp, destino], raiz_proyecto)
    os.mkdir(os.path.join(destino, "final"))
    for rel in ficheros:
        _reemplazar(os.path.join(tmp, rel), os.path.join(destino, rel))
    _reemplazar(os.path.join(tmp, "metadata.json"), os.path.join(destino, "metadata.json"))


def _leer_metadata_sin_enlace(dir_v):
    """`metadata.json` de una version (None si falta); `Rechazo` si es un enlace, simbolico o duro
    (gaps #66/#79)."""
    ruta = os.path.join(dir_v, "metadata.json")
    if _motivo_enlace(ruta, ruta):
        raise Rechazo(f"{os.path.basename(dir_v)}/metadata.json: {MOTIVO_ENLACE}")
    try:
        if os.lstat(ruta).st_nlink > 1:
            raise Rechazo(f"{os.path.basename(dir_v)}/metadata.json: enlace duro compartido (CWE-59); no se lee")
    except FileNotFoundError:
        return None
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


def _nombres_de_cases(store):
    """Nombres EXACTOS de `cases/` (un `scandir`, O(C)); `[]` si aun no existe."""
    try:
        with os.scandir(os.path.join(store, "cases")) as it:
            return [e.name for e in it]
    except FileNotFoundError:
        return []


def _comprobar_mayusculas(nombres, nombre, case_id):
    """gap #40b: un `case_id` que solo difiere en mayusculas de otro ya grabado compartiria
    directorio en NTFS/APFS: se rechaza (tambien en Linux: la regla peca de estricta)."""
    otros = [n for n in nombres if n != nombre and n.casefold() == nombre.casefold()]
    if otros:
        raise Rechazo(f"`{case_id}`: ya existe `cases/{otros[0]}`, que solo difiere en mayusculas "
                      "(compartirian directorio en Windows/macOS); no se escribe nada")


def _comprobar_directorio_caso(store, fam, var, case_id):
    """FUERA del bloqueo (F1): recorrido O(C) de mayusculas en CADA `record` y, si el directorio del
    caso existe, su `metadata.case_id` (el de su primera version completa) debe ser el mismo.
    Devuelve si el nombre EXACTO del caso aparece en `cases/` —deducido del `scandir`, nunca de
    `isdir`/`lexists`, que en NTFS/APFS no distinguen mayusculas (una reserva muerta `RAMP.steep`
    haria creer que `ramp.steep` existe)."""
    nombre = f"{fam}.{var}"
    nombres = _nombres_de_cases(store)
    _comprobar_mayusculas(nombres, nombre, case_id)
    if nombre not in nombres:
        return False
    for _n, nv in sorted(_dirs_version(os.path.join(store, "cases", nombre))):
        try:
            meta = _leer_metadata_sin_enlace(os.path.join(store, "cases", nombre, nv))
        except (Rechazo, OSError, ValueError, RecursionError):
            continue
        if meta is None:
            continue
        if isinstance(meta, dict) and meta.get("case_id") != case_id:
            raise Rechazo(f"`cases/{nombre}` pertenece a `{meta.get('case_id')}`, no a `{case_id}`; no se escribe nada")
        break
    return True


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
    # comprobaciones de solo lectura ANTES de escribir nada y FUERA del bloqueo (F1): enlaces,
    # mayusculas O(C) y dueño del directorio, `supersedes_case`; con el bloqueo solo lo O(1)
    _comprobar_contencion(store, rutas, raiz)
    _comprobar_fichero_propio(ruta_bloqueo)
    _comprobar_fichero_propio(ruta_indice)
    existia = _comprobar_directorio_caso(store, fam, var, caso["case_id"])
    _comprobar_supersedes(caso, dir_caso, width)
    os.makedirs(os.path.join(store, "cases"), exist_ok=True)
    tmp = tempfile.mkdtemp(prefix=PREFIJO_TEMPORAL, dir=os.path.join(store, "cases"))
    destino = None
    try:
        _comprobar_contencion(store, [tmp], raiz)
        ficheros = _ficheros_de(caso)
        os.mkdir(os.path.join(tmp, "final"))
        for rel, datos in ficheros.items():
            _escribir_nuevo(os.path.join(tmp, rel), datos)                  # O_EXCL (gap #77)
        for _intento in range(REINTENTOS_S1):
            with _Bloqueo(store):                                           # 4a. S1: reservar, O(1)
                _comprobar_contencion(store, rutas, raiz)
                if not existia:
                    # caso nuevo: el nombre exacto no estaba fuera; otro escritor pudo crear a la vez
                    # uno que solo difiere en mayusculas -> O(C) con el bloqueo, UNA vez por caso nuevo
                    _comprobar_mayusculas(_nombres_de_cases(store), f"{fam}.{var}", caso["case_id"])
                destino = _reservar(store, dir_caso, caso, width, auto, raiz)
            if destino is not None:
                break
            caso["version"] = _siguiente_version(dir_caso)                  # pista nueva, sin bloqueo
        else:
            raise Transitorio(f"mas de {SALTOS_MAX_S1} versiones de {caso['case_id']} grabadas a la vez por otros "
                              f"procesos {REINTENTOS_S1} veces seguidas; no se ha escrito nada: reintenta")
        # metadata.json, ya con su version, tambien con O_EXCL: si alguien planto un enlace en el temporal
        # mientras se esperaba S1 -> rechazo; la reserva queda VACIA (no hay borrado, CA-02) y `index
        # check` la reporta como incompleta pasada la gracia
        _escribir_nuevo(os.path.join(tmp, "metadata.json"), _json_bytes(_metadata(caso)))
        _mover_version(store, tmp, destino, ficheros, raiz)                 # 4b. W, sin bloqueo
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
        if _es_permanente(e):
            return [f"{INDICE} no actualizado para {ref} (la version YA esta grabada: no la vuelvas a grabar): {e}; "
                    "despues, `index rebuild`"]
        return [f"{no_act}: {e}"]


# ------------------------------------------------------------------ indice cases_index.jsonl (T-06)

INDICE = "cases_index.jsonl"
BLOQUEO_INDICE = ".cases_index.lock"
BLOQUEO_REBUILD = ".cases_rebuild.lock"
CLAVES_INDICE = ("case_id", "version", "family", "variant", "status", "outcome", "updated_at")
ESPERA_BLOQUEO_S = 10.0
ESPERA_INICIAL_S = 0.005           # retroceso exponencial con jitter: 5 ms -> 50 ms (D-fix2 §4)
ESPERA_MAX_S = 0.05
REINTENTOS_REBUILD = 3             # identidad del indice cambiada -> reintento acotado y luego exit 3 (E3)
GRACIA_EN_CURSO_S = 60.0           # «en curso» (E5)
COLA_MAX_BLOQUEO = 64              # F2: el residual se copia con el bloqueo cuando una pasada lee <= 64 lineas
MAX_PASADAS = 8                    # F2/F3: pasadas SIN bloqueo de puesta al dia (nunca exit 3 por trafico)
VENTANA_IDENTIDAD = 64 * 1024      # F4: con `st_ino == 0`, hash de los 64 KiB previos al offset consumido


class ErrorPermanente(OSError):
    """Fallo PERMANENTE del store (gap #76, exit 2): reintentar no sirve, hay que arreglar la causa
    (permisos, fichero de solo lectura, sistema de ficheros sin bloqueos)."""


def _es_contencion(e):
    """gap #76: SOLO el fallo de la llamada de bloqueo NO bloqueante porque otro lo tiene tomado es
    transitorio: `EAGAIN`/`EWOULDBLOCK`/`EACCES` de `flock`, `EACCES`/`EDEADLOCK` de `msvcrt.locking`.
    `ENOLCK` (unidad sin bloqueos) o cualquier otro codigo es permanente."""
    codigos = {errno.EAGAIN, errno.EWOULDBLOCK, errno.EACCES}
    codigos |= {getattr(errno, n) for n in ("EDEADLOCK", "EDEADLK") if hasattr(errno, n)}
    return getattr(e, "errno", None) in codigos


def _intentar_bloqueo(f):
    """UN intento NO bloqueante de bloquear `f` (`msvcrt.locking` / `flock`); `OSError` si no se puede."""
    if _WINDOWS:
        import msvcrt
        f.seek(0)
        msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
    else:
        import fcntl
        fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)


class _Bloqueo:
    """Exclusion mutua entre recorders (hilos o procesos): `flock` en POSIX, `msvcrt.locking` en
    Windows, sobre `<root>/<nombre>` (fichero que no se borra): `.cases_index.lock` (secciones O(1)
    de los escritores y F0/F2 del `rebuild`) o `.cases_rebuild.lock` (serializa los `rebuild`).
    `index check` no toma ninguno (F3). La espera sondea con retroceso exponencial y jitter; si no
    se obtiene en `ESPERA_BLOQUEO_S`, `BloqueoNoDisponible` (exit 3; quien lo pide no escribe nada).
    No poder abrir el fichero o un fallo del bloqueo que no es contencion -> `ErrorPermanente`
    (exit 2, gap #76). El SO lo libera si el proceso muere: nunca queda un bloqueo huerfano."""

    def __init__(self, store, nombre=BLOQUEO_INDICE):
        self.ruta = os.path.join(store, nombre)
        self.f = None
        self.tomado = False

    def __enter__(self):
        nombre = os.path.basename(self.ruta)
        _comprobar_fichero_propio(self.ruta)
        try:
            os.makedirs(os.path.dirname(self.ruta), exist_ok=True)
            self.f = open(self.ruta, "a+b")
        except OSError as e:
            raise ErrorPermanente(f"no se puede abrir {nombre} ({e}): permanente (permisos, solo lectura o ruta "
                                  "invalida del case store); arreglalo y repite") from None
        try:
            _comprobar_fd_propio(self.f, self.ruta)
        except Rechazo:
            self.f.close()
            raise
        limite = time.monotonic() + ESPERA_BLOQUEO_S
        espera = ESPERA_INICIAL_S
        while True:
            try:
                _intentar_bloqueo(self.f)
                self.tomado = True
                return self
            except OSError as e:
                if not _es_contencion(e):
                    self.f.close()
                    raise ErrorPermanente(f"el sistema no permite bloquear {nombre} ({e}): permanente (p. ej. una "
                                          "unidad de red sin bloqueos, ENOLCK); el case store necesita un sistema "
                                          "de ficheros con bloqueos: arreglalo y repite") from None
                restante = limite - time.monotonic()
                if restante <= 0:
                    self.f.close()
                    raise BloqueoNoDisponible(
                        f"otro proceso tiene el bloqueo del case store ({nombre}) desde hace mas de "
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
    """Una linea al final de `cases_index.jsonl` (append-only; nunca reescribe lo anterior), VALIDADA
    CONTRA EL DISCO (F2): con el bloqueo relee la version que nombra `entrada` (la misma relectura que
    S2) y la rechaza si no esta completa en `cases/` o si difiere de lo grabado (salvo `updated_at`).
    Ninguna via publica mete en el indice —ni en el residual que el `rebuild` copia tal cual— una
    linea que no refleje el disco."""
    motivo = _entrada_valida(entrada)
    if motivo:
        raise Rechazo(f"entrada del indice invalida ({motivo}); no se indexa")
    _comprobar_contencion(store, [os.path.join(store, BLOQUEO_INDICE), os.path.join(store, INDICE)])
    ref = f"{entrada['case_id']}@v{entrada['version']}"
    with _Bloqueo(store):
        e, aviso = _releer_de_linea(store, entrada)
        if e is None:
            raise Rechazo(f"{ref}: no se indexa: {aviso or 'no esta completa en cases/ (grabacion en curso)'}")
        distintos = [k for k in CLAVES_INDICE if k != "updated_at" and e[k] != entrada[k]]
        if distintos:
            raise Rechazo(f"{ref}: la entrada no casa con cases/ ({', '.join(distintos)}); no se indexa")
        _anadir_linea(store, dict(e, updated_at=entrada["updated_at"]))


def _es_permanente(e):
    """Permisos o solo lectura: `index rebuild` no lo arregla (gap #76)."""
    return isinstance(e, (PermissionError, ErrorPermanente)) or getattr(e, "errno", None) in (errno.EROFS, errno.EPERM)


def _indexar(store, entrada):
    """Anade la linea del cambio (bloqueo ya tomado); si el indice no se puede escribir (E/S, o un
    indice ajeno), el cambio YA esta en disco: se devuelve un aviso (el indice es una cache:
    `index rebuild` lo repone) en vez de fallar, para que nadie reintente y duplique. Si la causa es
    permanente (permisos, solo lectura), el aviso manda arreglarla primero (gap #76)."""
    try:
        _anadir_linea(store, entrada)
        return []
    except (OSError, Rechazo) as e:
        if _es_permanente(e):
            return [f"{INDICE} no actualizado: no se puede escribir ({e}); PERMANENTE (permisos o solo lectura): "
                    f"arregla los permisos de {INDICE} y despues `index rebuild`"]
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
    «falta» (a medio escribir), «enlace» (no se lee a traves de el, gap #66), «enlace duro compartido»
    (`st_nlink > 1`: podria ser un fichero de fuera del store, gap #79), «no es un fichero regular»
    (sin reintentos, gap #59), «no legible tras N reintentos (bloqueada o sin permisos)» e «ilegible»
    (JSON roto)."""
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
    if st.st_nlink > 1:
        return None, None, (f"{rel} omitida: {fichero} es un enlace duro compartido ({st.st_nlink} nombres para el "
                            "mismo fichero: podria ser uno de fuera del store, CWE-59); no se lee")
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


def _clasificar_temporal(entrada, rel, avisos, en_curso):
    """gap #80: un `.tmp-*` de `cases/`, de un caso o de la raiz del store. Reciente
    (`0 <= edad < GRACIA_EN_CURSO_S`) -> «en curso» (informativo); si no -> «temporal huerfano»
    (incoherencia de `index check`, con la ruta). Nunca se borra aqui."""
    try:
        mtime = entrada.stat(follow_symlinks=False).st_mtime
    except OSError:
        return
    edad = _edad(mtime)
    if 0 <= edad < GRACIA_EN_CURSO_S:
        en_curso[rel] = (f"{rel}: temporal en curso (modificado hace {edad:.0f} s, < {GRACIA_EN_CURSO_S:g} s): una "
                         "grabacion o un rebuild en marcha")
    else:
        cuando = "con mtime futuro" if edad < 0 else f"modificado hace {edad:.0f} s"
        avisos[rel] = (f"{rel}: temporal huerfano ({cuando}; de una grabacion o un rebuild interrumpidos): se conserva; "
                       "si no hay nada en marcha, revisalo y borralo a mano")


def _estado_de_cases(store, raiz_proyecto=None):
    """`(entradas, avisos, en_curso, mtimes_meta, rels)` recorriendo `cases/` (la FUENTE). `avisos`
    y `en_curso` son dicts `rel -> texto`; `rels` indexa por `(<family>.<variant>, numero)` los `rel`
    de cada version con aviso (gap #69: la cola los retira en O(1)). Enlaces detectados por ENTRADA
    sin `realpath` (E4); solo `cases/` se resuelve (una vez). Una entrada con nombre de version que
    no es un directorio real (fichero, enlace) no es version ni duplicado: aviso (gap #74). Los
    `.tmp-*` de la raiz, de `cases/` y de cada caso: «en curso» o «huerfano» (gap #80)."""
    entradas, avisos, en_curso, mtimes, rels = {}, {}, {}, {}, {}
    try:
        with os.scandir(store) as it:
            for e in it:
                if e.name.startswith(PREFIJO_TEMPORAL):
                    _clasificar_temporal(e, e.name, avisos, en_curso)
    except OSError:
        pass
    base = os.path.join(store, "cases")
    if not os.path.lexists(base):
        return entradas, avisos, en_curso, mtimes, rels
    motivo = _motivo_enlace(base, base) or _escapa(store, base, raiz_proyecto)
    if motivo:
        avisos["cases"] = f"cases/ omitido: {motivo}"
        return entradas, avisos, en_curso, mtimes, rels
    casos = []
    try:
        with os.scandir(base) as it:
            for e in it:
                if e.name.startswith(PREFIJO_TEMPORAL):
                    _clasificar_temporal(e, f"cases/{e.name}", avisos, en_curso)
                elif not e.name.startswith(".") and e.is_dir():
                    casos.append((e.name, e.path, e))
    except OSError:
        return entradas, avisos, en_curso, mtimes, rels
    for nombre, dir_caso, entrada_caso in sorted(casos, key=lambda t: t[0]):
        motivo = _motivo_enlace(entrada_caso, dir_caso)
        if motivo:
            avisos[f"cases/{nombre}"] = f"cases/{nombre} omitido: {motivo}"
            continue
        entradas_v, temporales = _escanear_caso(dir_caso)
        for t in temporales:
            _clasificar_temporal(t, f"cases/{nombre}/{t.name}", avisos, en_curso)
        por_numero = {}
        for v, n, ent, tipo in entradas_v:
            rel = f"cases/{nombre}/{n}"
            if tipo == "dir":
                por_numero.setdefault(v, []).append((n, ent))
            elif tipo == "enlace":
                avisos[rel] = f"{rel} omitida: {MOTIVO_ENLACE}"
            else:
                avisos[rel] = (f"{rel}: no es un directorio de version (fichero u otra entrada con nombre de version): "
                               "no cuenta como version ni como duplicado; retiralo o renombralo")
        for v, lista in sorted(por_numero.items()):
            nombres = [n for n, _e in lista]
            e, aviso, curso, mtime_meta = _estado_version(store, nombre, dir_caso, v, nombres,
                                                          lista[0][1] if len(lista) == 1 else None)
            rel = f"cases/{nombre}/{nombres[0]}"
            if curso:
                en_curso[rel] = aviso
                rels.setdefault((nombre, v), []).append(rel)
            elif aviso:
                avisos[rel] = aviso
                rels.setdefault((nombre, v), []).append(rel)
            else:
                entradas[(e["case_id"], e["version"])] = e
                mtimes[(e["case_id"], e["version"])] = mtime_meta
    return entradas, avisos, en_curso, mtimes, rels


def estado_de_cases(store, raiz_proyecto=None):
    """`(entradas, avisos)` recorriendo `cases/` (la FUENTE; el indice es cache). Se omiten con
    aviso: versiones incompletas o «en curso» (sin `metadata.json`/`validation.json`), enlazadas,
    con ficheros que no son regulares o con enlaces duros, bloqueadas o ilegibles, duplicadas (mismo
    numero con dos anchos), incoherentes con su ruta o con el esquema y `validation.json` incoherente
    con `case_schema` (p. ej. `approved` sin humano, gap #45); y los temporales HUERFANOS (gap #80;
    uno «en curso» no es un aviso para quien lee: solo lo informa `index check`).
    `updated_at` = mtime de `validation.json`."""
    entradas, avisos, en_curso, _m, _r = _estado_de_cases(store, raiz_proyecto)
    return entradas, list(avisos.values()) + [t for rel, t in en_curso.items()
                                              if not rel.rsplit("/", 1)[-1].startswith(PREFIJO_TEMPORAL)]


# ------------------------------------------------------------------ identidad y cola del indice (F2-F4)

def _stat_indice(x):
    """`os.fstat` de un descriptor abierto o `os.stat` de una ruta (inyectable en los tests)."""
    return os.fstat(x) if isinstance(x, int) else os.stat(x)


def _ventana(f, off):
    """F4: sha256 de los <= `VENTANA_IDENTIDAD` bytes previos a `off`, leidos de `f`: O(1), no del
    prefijo entero (gap #70). Probabilistico: solo escapa una sustitucion con los mismos 64 KiB."""
    ini = max(0, off - VENTANA_IDENTIDAD)
    f.seek(ini)
    return hashlib.sha256(f.read(off - ini)).hexdigest()


def _ultimo_salto(f, fin):
    """Offset justo detras del ultimo `\\n` de `f` antes de `fin` (0 si no hay): leido hacia atras
    por trozos, O(ultima linea). Un offset nunca cae a mitad de una linea (F3)."""
    pos = fin
    while pos > 0:
        ini = max(0, pos - VENTANA_IDENTIDAD)
        f.seek(ini)
        i = f.read(pos - ini).rfind(b"\n")
        if i >= 0:
            return ini + i + 1
        pos = ini
    return 0


def _identidad(ruta):
    """F0: `(st_dev, st_ino, offset, ventana|None)` del indice (sobre UN descriptor), con `offset`
    alineado al ultimo `\\n` y, si `st_ino == 0` (FAT/SMB: sin identidad fiable), la ventana de los
    64 KiB previos a `offset` (F4). None si no existe."""
    try:
        f = _abrir_reintentando(ruta)
    except FileNotFoundError:
        return None
    with f:
        st = _stat_indice(f.fileno())
        off = _ultimo_salto(f, st.st_size)
        return (st.st_dev, st.st_ino, off, None if st.st_ino else _ventana(f, off))


def _cursor(ident):
    """`((st_dev, st_ino)|None, offset consumido, ventana|None)` a partir de la identidad de F0."""
    return ((ident[0], ident[1]), ident[2], ident[3]) if ident else (None, 0, None)


def _partir_lineas(datos):
    """Lineas crudas (con su `\\n`; la ultima puede no tenerlo) partiendo SOLO por `\\n`."""
    partes = datos.split(b"\n")
    lineas = [p + b"\n" for p in partes[:-1]]
    return lineas + ([partes[-1]] if partes[-1] else [])


def _leer_cola(ruta, cursor, hasta_eof=False):
    """UNA lectura de la cola, sin bloqueo propio (F2/F3/F4): abre el indice y, sobre el MISMO
    descriptor, comprueba la identidad contra `cursor` (mismo `st_dev`/`st_ino`, no mas corto que lo
    consumido y, con `st_ino == 0`, la misma ventana de 64 KiB previa al offset consumido); despues
    lee desde el offset consumido hasta el ULTIMO `\\n` —una linea a medio escribir se queda para la
    lectura siguiente— o, con `hasta_eof` (el residual, con el bloqueo), hasta el final. Devuelve
    `(lineas_crudas, cursor_nuevo)`, o None si la identidad cambio (sustituido, truncado o
    reescrito). Un indice ausente en F0 adopta la identidad del primero que aparezca."""
    dev_ino, off, ventana = cursor
    try:
        f = _abrir_reintentando(ruta)
    except FileNotFoundError:
        return None if dev_ino else ([], cursor)
    with f:
        st = _stat_indice(f.fileno())
        if dev_ino is None:
            dev_ino = (st.st_dev, st.st_ino)
        elif (st.st_dev, st.st_ino) != dev_ino or st.st_size < off:
            return None
        if not st.st_ino and off and _ventana(f, off) != ventana:
            return None
        f.seek(off)
        datos = f.read(max(0, st.st_size - off))
        if not hasta_eof:
            datos = datos[:datos.rfind(b"\n") + 1]
        nuevo = off + len(datos)
        return _partir_lineas(datos), (dev_ino, nuevo, None if st.st_ino else _ventana(f, nuevo))


def _lineas_validas(crudas, avisos, donde):
    """`{clave: entrada}` de las lineas crudas validas (la ULTIMA por `(case_id, version)`); un aviso
    por cada linea corrupta, que se ignora."""
    out = {}
    for i, cruda in enumerate(crudas, 1):
        if not cruda.strip():
            continue
        e, motivo = _parsear_linea(cruda)
        if motivo:
            avisos.append(f"{INDICE} linea {i} de {donde} ignorada: {motivo}")
            continue
        clave = (e["case_id"], e["version"])
        out.pop(clave, None)
        out[clave] = e
    return out


def _poner_al_dia(ruta, cursor, avisos, al_releer):
    """Pasadas SIN bloqueo (F2 de D-fix3 con F2/F3/F4): cada una lee la cola nueva (hasta el ultimo
    `\\n`, con la identidad comprobada), llama a `al_releer(clave, linea)` una vez por clave DISTINTA
    (el llamador relee esa version del disco, E3) y avanza el offset. Para cuando una pasada lee <=
    `COLA_MAX_BLOQUEO` lineas o tras `MAX_PASADAS`: nunca falla por trafico. Devuelve el cursor, o
    None si la identidad cambio (el llamador vuelve a F0)."""
    for pasada in range(1, MAX_PASADAS + 1):
        r = _leer_cola(ruta, cursor)
        if r is None:
            return None
        crudas, cursor = r
        for clave, linea in _lineas_validas(crudas, avisos, f"la cola (pasada {pasada})").items():
            al_releer(clave, linea)
        if len(crudas) <= COLA_MAX_BLOQUEO:
            break
    return cursor


def _releer_version(store, fam, var, numero, case_id=None):
    """E3: la version `<fam>.<var>` numero `numero` RELEIDA del disco: `(entrada|None, aviso|None,
    en_curso, mtime_meta)`. O(1): la localiza por numero (cualquier ancho) sin recorrer el caso."""
    try:
        cs.directorio_version(fam, var, 1)
    except (ValueError, TypeError):
        return None, f"{INDICE}: family/variant que no son un directorio seguro: se ignora", False, None
    nombre = f"{fam}.{var}"
    base, dir_caso = os.path.join(store, "cases"), os.path.join(store, "cases", nombre)
    for ruta in (base, dir_caso):
        motivo = _motivo_enlace(ruta, ruta)
        if motivo:
            return None, f"{os.path.relpath(ruta, store).replace(os.sep, '/')} omitido: {motivo}", False, None
    ocupantes = _ocupantes_version(dir_caso, numero)
    nombres = [n for n, tipo in ocupantes.items() if tipo == "dir"]
    if not nombres:
        if ocupantes:
            n, tipo = next(iter(ocupantes.items()))
            return None, f"cases/{nombre}/{n}: no es un directorio de version ({tipo}): no se indexa", False, None
        return None, f"{case_id or nombre}@v{numero}: en el indice pero no en cases/", False, None
    e, aviso, curso, mtime_meta = _estado_version(store, nombre, dir_caso, numero, nombres)
    if e is not None and case_id is not None and e["case_id"] != case_id:
        return None, f"cases/{nombre}/{nombres[0]}: la linea dice `{case_id}` y metadata.json `{e['case_id']}`", False, None
    return e, aviso, curso, mtime_meta


def _releer_de_linea(store, linea):
    """La version que nombra una linea del indice, releida del disco: `(entrada|None, aviso|None)`
    («en curso» -> `(None, None)`)."""
    e, aviso, curso, _m = _releer_version(store, linea["family"], linea["variant"], linea["version"], linea["case_id"])
    return e, (aviso if not curso else None)


def _mismos_campos(a, b):
    return all(a[k] == b[k] for k in CLAVES_INDICE if k != "updated_at")


def _comprobar_temporal_propio(f, tmp):
    """gap #78: antes del `os.replace`, el temporal del rebuild (abierto desde F1, nunca reabierto
    por ruta) sigue siendo NUESTRO fichero: un solo nombre (`st_nlink == 1`) y la ruta apunta al
    mismo `st_dev`/`st_ino` que el descriptor; si no -> `Rechazo` sin tocar el indice (CWE-59/367)."""
    st = os.fstat(f.fileno())
    try:
        sl = _stat_sin_seguir(tmp)
    except OSError:
        sl = None
    if (st.st_nlink != 1 or sl is None or _es_enlace_st(sl) or
            (sl.st_dev, sl.st_ino) != (st.st_dev, st.st_ino)):
        raise Rechazo(f"el temporal del rebuild ({os.path.basename(tmp)}) fue sustituido o tiene enlaces duros "
                      f"({st.st_nlink} nombres): no se sustituye {INDICE} (CWE-59/367)")


def _comprobar_indice_escribible(ruta):
    """gap #76: un indice que existe y no se puede escribir (solo lectura, sin permiso) es PERMANENTE:
    exit 2 antes de recorrer nada (reintentar el rebuild no lo arregla)."""
    if os.path.lexists(ruta) and not os.access(ruta, os.W_OK):
        raise ErrorPermanente(f"{INDICE} es de solo lectura o no tiene permiso de escritura: permanente; arregla sus "
                              "permisos y repite `index rebuild`")


def reconstruir_indice(store, raiz_proyecto=None):
    """Reescribe `cases_index.jsonl` desde `cases/` (D-fix2 §3 + D-fix3 §2 con F2/F4), serializado
    por `.cases_rebuild.lock` (tomado ANTES que el del indice):
      - F0 (bloqueo, O(1)): identidad del indice y offset (alineado al ultimo `\\n`).
      - F1 (SIN bloqueo): recorre `cases/`, conservando el `updated_at` de la ultima linea valida
        (hasta el offset) si su estado coincide.
      - Pasadas SIN bloqueo: releen del disco las claves distintas de la cola nueva (E3), comprobando
        la identidad en cada una; paran con <= `COLA_MAX_BLOQUEO` lineas o tras `MAX_PASADAS`.
      - F2 (bloqueo, O(bytes del residual), sin relecturas): identidad, residual copiado TAL CUAL
        (lineas validas; un fragmento final o una linea corrupta se descartan con aviso), comprobacion
        del temporal (gap #78) y `os.replace`.
    Identidad cambiada -> vuelta a F0 (hasta `REINTENTOS_REBUILD`) y despues `Transitorio` (exit 3).
    Indice de solo lectura o `PermissionError` persistente al sustituir -> `ErrorPermanente` (exit
    2, gap #76). Devuelve `(n_versiones, avisos)`."""
    raiz = _raiz(raiz_proyecto)
    ruta = os.path.join(store, INDICE)
    _comprobar_contencion(store, [os.path.join(store, BLOQUEO_INDICE), os.path.join(store, BLOQUEO_REBUILD), ruta], raiz)
    os.makedirs(store, exist_ok=True)
    _comprobar_indice_escribible(ruta)
    with _Bloqueo(store, BLOQUEO_REBUILD):
        for _intento in range(REINTENTOS_REBUILD):
            r = _reconstruir_una_vez(store, ruta, raiz)
            if r is not None:
                return r
    raise Transitorio(f"{INDICE} cambio de identidad (sustituido o truncado) durante el rebuild {REINTENTOS_REBUILD} "
                      "veces seguidas; no se ha tocado: reintenta")


def _reconstruir_una_vez(store, ruta, raiz):
    """Un intento de `reconstruir_indice`; None si la identidad del indice cambio (volver a F0)."""
    with _Bloqueo(store):                                                       # F0
        cursor = _cursor(_identidad(ruta))
    fuente, avisos = estado_de_cases(store, raiz)                               # F1
    previas = leer_indice(store, hasta=cursor[1])[0] if cursor[1] else {}
    lineas = {}
    for clave in sorted(fuente, key=lambda k: (fuente[k]["family"], fuente[k]["variant"], k[1])):
        e = dict(fuente[clave])
        p = previas.get(clave)
        if p and _mismos_campos(p, e):
            e["updated_at"] = p["updated_at"]
        lineas[clave] = e

    def al_releer(clave, linea):                                                # E3: releida del disco
        e, aviso = _releer_de_linea(store, linea)
        if e is None:
            if aviso:
                avisos.append(aviso)
            return
        if _mismos_campos(linea, e):
            e["updated_at"] = linea["updated_at"]
        lineas[clave] = e

    cursor = _poner_al_dia(ruta, cursor, avisos, al_releer)                    # pasadas sin bloqueo
    if cursor is None:
        return None
    fd, tmp = tempfile.mkstemp(prefix=PREFIJO_TEMPORAL, dir=store)
    f = os.fdopen(fd, "wb")          # abierto hasta la sustitucion: NUNCA se reabre por ruta (gap #78)
    try:
        f.write(b"".join(_linea(e) for e in lineas.values()))
        claves = set(lineas)
        with _Bloqueo(store):                                                   # F2: O(residual)
            r = _leer_cola(ruta, cursor, hasta_eof=True)
            if r is None:
                return None
            for i, cruda in enumerate(r[0], 1):                                 # residual TAL CUAL
                if not cruda.strip():
                    continue
                e, motivo = _parsear_linea(cruda)
                if motivo:
                    avisos.append(f"{INDICE} linea {i} del residual ignorada: {motivo}")
                    continue
                f.write(cruda if cruda.endswith(b"\n") else cruda + b"\n")
                claves.add((e["case_id"], e["version"]))
            f.flush()
            _comprobar_temporal_propio(f, tmp)
            f.close()
            try:
                _reemplazar(tmp, ruta)
            except PermissionError as e:
                raise ErrorPermanente(f"{INDICE} no se pudo sustituir tras {REINTENTOS} reintentos ({e}): permanente "
                                      "(solo lectura, sin permisos o abierto de forma persistente por otro proceso); "
                                      "no se ha tocado: arregla la causa y repite `index rebuild`") from None
        return len(claves), avisos
    finally:
        if not f.closed:
            f.close()
        _limpiar_temporal(tmp)


def comprobar_indice_detalle(store, width=cs.VERSION_WIDTH_DEFECTO, raiz_proyecto=None):
    """`(diferencias, en_curso)` entre el indice y `cases/` (E5 + D-fix3 §3 con F3), SIN escribir y
    SIN tomar NUNCA `.cases_index.lock` (no bloquea a los escritores): offset del indice alineado al
    ultimo `\\n`, recorrido de `cases/`, pasadas de puesta al dia sin bloqueo (releyendo del disco lo
    que toca la cola) y una CONFIRMACION final que relee la cola nueva y, del disco, lo que difiere,
    y comprueba la identidad. Identidad cambiada -> reintento acotado y despues `Transitorio` (exit
    3). Bajo escritura muy intensa cabe un falso positivo transitorio que un segundo `check` ya no
    ve. `diferencias` vacia = coherente (exit 0); `en_curso` es informativo."""
    raiz = _raiz(raiz_proyecto)
    ruta = os.path.join(store, INDICE)
    for _intento in range(REINTENTOS_REBUILD):
        r = _comprobar_una_vez(store, ruta, width, raiz)
        if r is not None:
            return r
    raise Transitorio(f"{INDICE} cambio de identidad durante `index check` {REINTENTOS_REBUILD} veces seguidas: reintenta")


def _claves_con_diferencia(fuente, indice):
    return [c for c in set(fuente) | set(indice)
            if c not in indice or c not in fuente or not _mismos_campos(fuente[c], indice[c])]


def _comprobar_una_vez(store, ruta, width, raiz):
    """Un intento de `comprobar_indice_detalle`; None si la identidad del indice cambio."""
    cursor = _cursor(_identidad(ruta))                                          # F0, sin bloqueo
    fuente, avisos, en_curso, mtimes, rels = _estado_de_cases(store, raiz)     # F1
    indice, avisos_idx = leer_indice(store, hasta=cursor[1]) if cursor[1] else ({}, [])
    avisos_cola, cola_fallidas = [], set()

    def releer(fam, var, numero, case_id, origen):
        e, aviso, curso, mtime_meta = _releer_version(store, fam, var, numero, case_id)
        if e is not None:
            clave = (e["case_id"], e["version"])
            fuente[clave] = e
            mtimes[clave] = mtime_meta if origen == "confirmacion" else None
            avisos.pop(f"cola:{clave[0]}@{clave[1]}", None)
            for rel in rels.pop((f"{fam}.{var}", numero), ()):                 # gap #69: O(1)
                avisos.pop(rel, None)
                en_curso.pop(rel, None)
        elif origen == "confirmacion":
            if case_id is not None:          # ya no esta completa en disco: la diferencia la da el cruce
                fuente.pop((case_id, numero), None)
        elif aviso and not curso:
            avisos[f"cola:{case_id}@{numero}"] = aviso
            cola_fallidas.add((case_id, numero))

    def al_releer(clave, linea):
        indice[clave] = linea
        releer(linea["family"], linea["variant"], clave[1], clave[0], "cola")

    cursor = _poner_al_dia(ruta, cursor, avisos_cola, al_releer)
    if cursor is None:
        return None
    r = _leer_cola(ruta, cursor)                                                # confirmacion (F3)
    if r is None:
        return None
    crudas, cursor = r
    for clave, linea in _lineas_validas(crudas, avisos_cola, "la cola (confirmacion)").items():
        al_releer(clave, linea)
    for clave in set(_claves_con_diferencia(fuente, indice)) | cola_fallidas:   # del disco, otra vez
        e = indice.get(clave) or fuente.get(clave)
        if e is not None:
            releer(e["family"], e["variant"], clave[1], clave[0], "confirmacion")
    for (nombre, numero) in list(rels):
        if any(rel in avisos for rel in rels.get((nombre, numero), ())):
            fam, _sep, var = nombre.partition(".")
            releer(fam, var, numero, None, "confirmacion")
    if _leer_cola(ruta, cursor) is None:                                        # identidad al final
        return None
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
    que el recorrido omite (versiones incompletas, duplicadas, enlazadas, ilegibles, incoherentes,
    temporales huerfanos) cuentan como incoherencia (gaps #37/#80); lo «en curso» no (ver
    `comprobar_indice_detalle`)."""
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
    """#66/#79: `metadata.json`/`validation.json` que sean enlace (simbolico o DURO: `st_nlink > 1`)
    se rechazan ANTES de leerlos."""
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
        if st.st_nlink > 1:
            raise Rechazo(f"{ref}: {fichero} es un enlace duro compartido ({st.st_nlink} nombres para el mismo fichero: "
                          "podria ser uno de fuera del store, CWE-59); no se lee ni se escribe")


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
    if reviewer_note is not None and not _codificable(reviewer_note):
        raise Rechazo("nota invalida", [{"campo": "reviewer_note", "mensaje": MENSAJE_NO_UTF8}])
    version = _version_int(version)
    family, variant = _family_variant(case_id, config)
    width = cs.patrones_id(config)[2]
    ref = cs.referencia_version(case_id, version, width)
    store = raiz_store(config, raiz)
    dir_caso = os.path.join(store, "cases", f"{family}.{variant}")
    ruta_bloqueo, ruta_indice = os.path.join(store, BLOQUEO_INDICE), os.path.join(store, INDICE)
    rutas_base = [ruta_bloqueo, ruta_indice, os.path.join(store, "cases"), dir_caso]
    _comprobar_contencion(store, rutas_base, raiz)
    ocupantes = _ocupantes_version(dir_caso, version, width)
    nombres = [n for n, tipo in ocupantes.items() if tipo == "dir"]
    if len(nombres) > 1:
        raise Rechazo(f"{ref}: version {version} duplicada ({', '.join(nombres)}): ambigua; no se cambia el estado")
    if not nombres and "enlace" in ocupantes.values():
        raise Rechazo(f"{ref}: es un {MOTIVO_ENLACE}; no se lee ni se escribe")
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
                                             "1 rechazo, 2 uso/E/S o permanente, 3 transitorio (bloqueo o indice cambiado: reintenta).")
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
    except ErrorPermanente as e:
        # gap #76: permanente (permisos, solo lectura, sin bloqueos): reintentar no sirve
        print(f"error permanente: {e}", file=sys.stderr)
        return 2
    except OSError as e:
        # gap #38: E/S (root que es un fichero, disco lleno, permisos) -> exit 2 con mensaje, sin traceback
        print(f"error de E/S: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
