#!/usr/bin/env python3
"""
dataset-assembler.py — ensamblador de dataset de `training-data-services` (T-08/T-09, design.md O1).

No entrena, no sirve modelos y no corre benchmarks (CA-08): produce ficheros JSONL y un manifiesto.

Solo Gold (T-09, CA-03):
  - Se recorre `cases/` con el lector del recorder (`_estado_de_cases`: sin seguir enlaces; versiones
    incompletas, en curso, duplicadas, enlazadas o incoherentes se OMITEN con aviso; #134: con el MISMO
    tope por fichero en `metadata.json`/`validation.json` de TODAS las versiones, Gold o no: una mayor
    se omite con aviso sin cargarla) y, de cada version
    `approved`, se leen SUS OCHO FICHEROS por descriptor (`_leer_de_version` con los bytes tal cual:
    fichero regular, un solo nombre, la misma identidad que su `lstat`, como mucho `tope_fichero`
    bytes —16 MiB por defecto, #122: por encima, el caso se omite con aviso sin cargarlo—), con
    `vNNN` y `final/` comprobados antes y despues de leer (directorio real, no enlace, `realpath`
    igual al esperado, misma identidad) y cada fichero en el mismo dispositivo que su version.
    `metadata.json` y `validation.json` ya leidos en el recorrido se reutilizan si el nombre sigue
    siendo EL MISMO fichero (`lstat` con la identidad del `fstat` de aquella lectura, #130). Gold es
    `validation.status == "approved"` **y** `validation.approved_by_human is True` en los bytes
    LEIDOS de `validation.json` — nunca el indice `cases_index.jsonl` (una cache) ni el recorrido
    previo. El caso reconstruido pasa `case_schema.validar_caso` con la config; JSON ilegible, con
    `NaN`/`Infinity` o que no casa con su ruta -> omitido con aviso.
  - Gold atado al contenido (#132): `set-status approved` guarda `validation.content_hash`
    (`hash_contenido` del recorder: los siete ficheros inmutables). Si no casa con lo leido, el caso
    se EXCLUYE («Gold sin atar al contenido aprobado»); un Gold sin `content_hash` (aprobado antes de
    existir, o con `record --approved-by-human`, que aun no tiene `metadata.json` al escribir
    `validation.json`) se exporta con aviso «sin hash de aprobacion».
  - Limite declarado (sin `openat` portable, como el recorder): un tercero con escritura en el store
    que sustituya `vNNN`/`final/` por un enlace Y lo restaure en los microsegundos entre las dos
    comprobaciones podria colar un fichero ajeno; fuera de esa ventana, cualquier sustitucion se ve.

Dos pasadas en streaming (H5; memoria O(n · muestra), nunca O(tamaño del export)):
  1. Por cada Gold: lectura segura, sha256 de sus ficheros y shingles muestreados para `dedup.py`
     (`Acumulador`: el texto se descarta al shinglearlo). No se guarda ningun caso. Con eso se deciden
     grupos, particion y `export_id`.
  2. Por cada caso INCLUIDO, en orden `(case_id, version)`: relectura segura con comprobacion del
     sha256 de la pasada 1 —si cambio, se aborta SIN publicar `manifest.json` (export incompleto
     reconocible)— y escritura en streaming de su linea, redactada (#119).

Particion anti-leakage (T-08):
  - Por FAMILIA COMPLETA (CA-11): toda version de una familia va a train o toda a benchmark. Las
    familias de benchmark se declaran EXPLICITAMENTE (`--benchmark <family>[,…]`, repetible); sin al
    menos una, o con una familia declarada que no tiene ningun caso Gold, el ensamblador se NIEGA a
    exportar (exit 1) y explica por que, sin escribir nada.
  - Near-duplicates (`dedup.py`, CA-06/CA-10) sobre los Gold: un grupo que cruza train/benchmark
    EXCLUYE a sus miembros de train (motivo «cruce de particion») y conserva los de benchmark — nunca
    al reves, ni siquiera con `--conservar-duplicados`. Con Jaccard muestreado (`r < 1`, #145) el cruce
    es CONSERVADOR: un par train/benchmark con Jaccard muestreado `>= umbral - margen` (`cruces` del
    dedup) tambien saca de train al de train; dentro de una particion manda el umbral. Dentro de una misma particion (#120,
    design.md:42): los miembros de una CADENA `supersedes_case` (el `corrected` y lo que corrige,
    transitivamente, si ambos estan) nunca se descartan por duplicado (el par fallo -> correccion es
    dato de primera clase); entre el resto del grupo se conserva UNO, el de `(case_id, version)`
    mayor por numero (`v010` gana a `v009`), y los demas salen con «duplicado de …», salvo
    `--conservar-duplicados`.

Salida (`<root>/exports/<export_id>/`):
  - `train.jsonl` / `benchmark.jsonl`: una linea por caso, `{"messages": [...], "ref", "case_id",
    "version", "family", "variant", "outcome"[, "supersedes_case"]}` (CA-12): los turnos de
    `trajectory.jsonl` con `role`/`content`/`tool_calls`/`name` (sin `ts`); ni metricas ni
    artefactos (nada binario ni inline). Cada linea pasa por `redactar_estructura` del recorder al
    escribirse (#119: un secreto que llegara al disco sin redactar no sale). Orden
    `(case_id, version)`, JSON con claves ordenadas: la misma entrada da los mismos bytes.
  - `manifest.json` (se publica el ULTIMO: un export sin el esta INCOMPLETO): por caso `ref`,
    `sha256` (de los hashes de sus ocho ficheros, en orden fijo), `ficheros`, `content_hash`,
    `particion` y `motivo` de exclusion (no Gold, omitida, duplicado, cruce, sin atar; motivos
    NORMALIZADOS: rutas relativas al store, nunca el texto de un `OSError`, #123); los grupos de
    near-duplicates, `cruces_near_duplicates` (#145), `near_duplicates` (`jaccard: exacto|muestreado`, `r`,
    `cruce`: el criterio y su margen), los `avisos` deterministas
    (dedup y Gold sin hash), los parametros, `directorio` (el nombre real, `.N` incluido, #131) y el
    `sha256` y las lineas de cada JSONL. Los avisos del RECORRIDO del store (temporales «en curso» o
    «huerfanos», versiones enlazadas…) dependen del reloj: van a `stderr` (`avisos_store`), NUNCA al
    manifiesto ni al hash (#117). TODO el manifiesto pasa por `redactar_estructura` antes del hash
    (#137: un motivo del esquema cita CLAVES de la trayectoria, que pueden ser un secreto).
  - `export_id = <AAAAMMDD>-<12 hex>` del sha256 del NUCLEO: parametros + lista de casos con sus
    sha256, particion y motivo + grupos + avisos deterministas (#117); no depende de los bytes
    escritos (que son funcion de ese nucleo) ni del reloj. `manifest.sha256_contenido` es ese hash.
  - Exclusion entre ensambladores (#124): la comprobacion de «ya existe» y la creacion van bajo
    `exports/.lock` (el `_Bloqueo` del recorder); espera `--espera-bloqueo` s (120 por defecto, #143:
    el otro lo retiene su pasada 2 entera) y despues exit 3 sin escribir nada, con la duracion de la
    pasada 1 propia como referencia de cuanto esperar.
  - NUNCA se destruye ni se sobrescribe nada: `exports/<export_id>/` se crea con `os.mkdir`; si ya
    existe y es IDENTICO (sha256 en streaming del manifiesto y de los JSONL = los que se escribirian,
    #122), no se escribe nada (exit 0, «ya existe»); si existe y no lo es (incompleto, manipulado, un
    enlace), se usa `<export_id>.2`, `.3`… Cada fichero se crea con `O_EXCL` y se comprueba al
    crearlo y al cerrarlo con el contrato G4 del recorder (`_verificar_creado`, #118): `realpath`
    IGUAL al esperado, mismo fichero, un solo nombre; si un tercero con escritura en `exports/`
    sustituyo el directorio por un enlace, el aviso NOMBRA donde quedo el fichero creado (solo si es
    el creado, `samestat`) y nunca pide borrar uno ajeno. Limite declarado: ese tercero puede hacer
    que aparezca un fichero NUEVO del ensamblador fuera; se detecta y se nombra; nunca se sobrescribe
    ni se borra nada. `manifest.json` se publica desde un `.tmp-<token>` propio sin sobrescribir
    (Windows `os.rename`, POSIX `os.link` + retirar el temporal, que es LO UNICO que se elimina, solo
    si sigue siendo el mismo fichero); el temporal se comprueba (G4) ANTES de escribirle un byte y
    otra vez antes de publicarlo (#136), y si ya se retiro el aviso lo dice (no pide retirar nada). Un fallo a mitad deja el export sin manifiesto (incompleto) y
    lo dice. `exports/` que sea un enlace -> rechazo sin escribir.

Marca del ultimo ensamblado y frescura (T-10, D-f4/D-f5): tras un ensamblado real («escrito» o «ya
existe»), con `exports/.lock` tomado, `exports/.ultimo.json` = `{version, export_id, directorio, firma,
gold, creado, parametros, omitidos, omitidos_muestra}` (<= 4 KiB; nunca se reemplaza una que no sea de la
pieza, y nunca se publica una que su propio lector rechazaria). `firma` describe la ENTRADA del ensamblado
(TODOS los Gold humanos con su `content_hash`, `rec.firma_gold`, tambien los que `leer_caso` omitio), no
lo que incluyo; `omitidos` cuenta los Gold que `leer_caso` omitio por un aviso (transitorio o
permanente; D-f5 O2) y `omitidos_muestra` guarda hasta 10 con su clase y su causa. `estado_dataset` (lo
que ejecutan `/doctor` y `--estado`) la compara con la del store sin leer ningun `manifest.json`.

Uso (exit 0 ok o ya existente · 1 rechazo: capacidad apagada o config invalida, sin benchmark, familia
de benchmark sin Gold, store manipulado, caso cambiado entre pasadas · 2 uso, E/S o sin `redact.py` ·
3 otro ensamblador tiene `exports/.lock`: reintenta; nunca un traceback):
  dataset-assembler.py --benchmark <family>[,<family>…] [--umbral 0.8] [--ventana 3] [--boilerplate 0.5]
                       [--presupuesto 10000000] [--conservar-duplicados] [--fecha AAAAMMDD] [--dry-run]
                       [--espera-bloqueo 120] [--config <training.json>] [--project-root <dir>]
  dataset-assembler.py --estado [--json] [--config <training.json>] [--project-root <dir>]
                       (solo lectura; exit 0 al dia o sin Gold · 1 desactualizado, con omisiones o sin export
                       · 2 no verificable)
"""
import argparse
import contextlib
import datetime
import errno
import hashlib
import importlib.util
import json
import math
import os
import re
import secrets
import stat
import sys
import time
import unicodedata

# Consola no UTF-8 (Windows cp1252) o tuberias: reconfigurar ANTES de leer/imprimir (GOT-005).
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure, ya leido o None (capsys, pythonw)

HERE = os.path.dirname(os.path.abspath(__file__))


def _cargar(fichero, nombre):
    """Un script de la MISMA skill (fuente unica del recorder, del esquema y del dedup), sin dejar
    bytecode (#186: `--estado` es de solo lectura; `dont_write_bytecode`, restaurado al salir)."""
    previo = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec = importlib.util.spec_from_file_location(nombre, os.path.join(HERE, fichero))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        sys.dont_write_bytecode = previo


rec = _cargar("case-recorder.py", "tds_case_recorder_asm")
cs = rec.cs
dd = _cargar("dedup.py", "tds_dedup_asm")

Rechazo = rec.Rechazo
FICHEROS = ("metadata.json", "request.json", "context.json", "constraints.json", "trajectory.jsonl",
            "metrics.json", "validation.json", "final/artifacts.json")
FICHEROS_JSON_CASO = ("metadata.json", "validation.json")      # #171: los de `TOPE_JSON_CASO`
CLAVES_TURNO = ("role", "content", "tool_calls", "name")
JSONL = ("train.jsonl", "benchmark.jsonl")
MANIFEST = "manifest.json"
BLOQUEO_EXPORTS = ".lock"
MAX_EXPORTS_MISMO_ID = 99
TOPE_FICHERO = rec.TOPE_FICHERO                 # #148: el MISMO tope por fichero que aplica `/doctor`
BLOQUE = 64 * 1024
ESPERA_BLOQUEO_EXPORTS_S = 120                  # #143: espera de `exports/.lock` (`--espera-bloqueo`)
QUIEN = "el ensamblador"
MOTIVO_SIN_BENCHMARK = ("sin familias de benchmark declaradas (`--benchmark <family>[,…]`) no se exporta: la "
                        "particion de evaluacion se reserva por familia COMPLETA antes de generar train.jsonl "
                        "(anti-leakage, CA-06/CA-11); no se ha escrito nada")
MOTIVO_SIN_ATAR = ("Gold sin atar al contenido aprobado: el content_hash de validation.json no casa con sus ficheros "
                   "(cambiaron despues de aprobarlo); no se exporta: revisalo y vuelve a aprobarlo")
MOTIVO_CRUCE_CONSERVADOR = ("cruce de particion (criterio conservador con Jaccard muestreado: >= umbral - margen): "
                            "near-duplicate probable de {ref} (benchmark); anti-leakage")
MENSAJE_BLOQUEO = ("otro ensamblador tiene exports/.lock desde hace mas de {espera:g} s: no se ha escrito nada y la "
                   "pasada 1 (solo lectura del store) no deja nada a medias; el otro termina en lo que dura una pasada "
                   "sobre este store (la pasada 1 de este ha tardado {pasada:.1f} s): reintenta o espera mas con "
                   "`--espera-bloqueo <s>` (ahora {espera:g} s)")
AVISO_SIN_HASH = ("{ref}: Gold sin hash de aprobacion (sin content_hash: aprobado antes de que existiera o con "
                  "`record --approved-by-human`); se exporta; `set-status … approved --approved-by-human` lo ata")


def _familias_benchmark(valores):
    """`--benchmark a,b --benchmark c` -> {"a", "b", "c"} (sin vacios ni espacios)."""
    return {f.strip() for v in (valores or ()) for f in v.split(",") if f.strip()}


def _clave(c):
    return (c["case_id"], c["version"])


def _cadenas(casos):
    """#120: refs que forman parte de una cadena fallo -> correccion (`supersedes_case` cuyo objetivo
    tambien esta entre `casos`; transitiva por pares)."""
    refs = {c["ref"] for c in casos}
    cadena = set()
    for c in casos:
        sup = c.get("supersedes_case")
        if sup and sup in refs and sup != c["ref"]:
            cadena.update((c["ref"], sup))
    return cadena


def particionar(casos, benchmark, grupos=(), conservar_duplicados=False, cruces=()):
    """Asigna `particion` (`train`/`benchmark`/None) y `motivo` (None o el de la exclusion) a cada caso
    `{ref, case_id, version, family[, supersedes_case]}` (T-08, ver docstring del modulo). Devuelve
    copias ordenadas por `(case_id, version)`. `Rechazo` sin benchmark o con una familia de benchmark
    sin casos. `cruces` (#145, solo con Jaccard muestreado): pares `[ref de train, ref de benchmark]`
    con Jaccard muestreado >= `umbral - margen`: sacan de train al primero ANTES de agrupar (solo la
    exclusion anti-leakage; dentro de una particion manda el umbral)."""
    benchmark = set(benchmark or ())
    if not benchmark:
        raise Rechazo(MOTIVO_SIN_BENCHMARK)
    familias = {c["family"] for c in casos}
    faltan = sorted(benchmark - familias)
    if faltan:
        raise Rechazo("familia(s) de benchmark sin ningun caso Gold: " + ", ".join(rec._texto_ruta(f) for f in faltan)
                      + "; el benchmark quedaria vacio o incompleto: revisa `--benchmark`; no se ha escrito nada")
    salida = {c["ref"]: dict(c, particion="benchmark" if c["family"] in benchmark else "train", motivo=None)
              for c in casos}
    cadena = _cadenas(casos)
    for tr, be in cruces:
        a, b = salida.get(tr), salida.get(be)
        if a and b and a["particion"] == "train" and b["particion"] == "benchmark":
            a["particion"] = None
            a["motivo"] = MOTIVO_CRUCE_CONSERVADOR.format(ref=be)
    for grupo in grupos:
        miembros = sorted((salida[r] for r in grupo if r in salida), key=_clave)
        bench = [m for m in miembros if m["particion"] == "benchmark"]
        if bench:
            for m in miembros:
                if m["particion"] == "train":
                    m["particion"] = None
                    m["motivo"] = f"cruce de particion: near-duplicate de {bench[-1]['ref']} (benchmark); anti-leakage"
        if conservar_duplicados:
            continue
        for lado in ("train", "benchmark"):
            del_lado = [m for m in miembros if m["particion"] == lado and m["ref"] not in cadena]
            for m in del_lado[:-1]:
                m["particion"] = None
                m["motivo"] = f"duplicado de {del_lado[-1]['ref']} (near-duplicate; se conserva uno por grupo)"
    return sorted(salida.values(), key=_clave)


# ------------------------------------------------------------------ lectura de un caso Gold (T-09)

def _no_finito(valor):
    raise ValueError(f"valor no finito {valor}")


def _json(datos):
    return json.loads(datos.decode("utf-8"), parse_constant=_no_finito)


def _jsonl(datos):
    return [_json(l.encode("utf-8")) for l in datos.decode("utf-8").split("\n") if l.strip()]


def _dir_real(ctx, ruta):
    """`lstat` de un directorio de version (o `final/`) si es EXACTAMENTE el esperado (`realpath` por
    igualdad) y no es un enlace; si no, None."""
    ok, _r = ctx.igual(ruta)
    if not ok:
        return None
    try:
        st = os.lstat(ruta)
    except OSError:
        return None
    return st if stat.S_ISDIR(st.st_mode) and not rec._es_enlace_st(st) else None


def _sha(datos):
    return hashlib.sha256(datos).hexdigest()


def _reutilizable(dir_v, fichero, previo, st_dir, tope):
    """#130: los bytes de `fichero` leidos en el recorrido (`previo = (bytes, fstat)`) si el nombre
    sigue siendo EXACTAMENTE ese fichero (`lstat` ahora, dentro de la ventana de comprobacion de
    `vNNN`: regular, no enlace, un solo nombre, el dispositivo de su version y la identidad del `fstat`
    de aquella lectura); si no, None y se lee de nuevo."""
    if not previo:
        return None
    datos, st_prev = previo
    try:
        sl = os.lstat(os.path.join(dir_v, fichero))
    except OSError:
        return None
    if not stat.S_ISREG(sl.st_mode) or rec._es_enlace_st(sl) is not False or sl.st_nlink != 1 \
            or sl.st_dev != st_dir.st_dev or not rec._misma_identidad(st_prev, sl) or len(datos) > tope:
        return None
    return datos


def leer_caso(ctx, store, entrada, config, width, previos=None, tope=TOPE_FICHERO):
    """`(caso, hashes, aviso)` de una version de `cases/` leida del DISCO (ver docstring del modulo):
    `caso` con el esquema de `case_schema` y `hashes = {"sha256", "ficheros", "content_hash"}`; o
    `(None, None, aviso)`. `previos`: lo leido en el recorrido (#130)."""
    nombre = f"{entrada['family']}.{entrada['variant']}"
    dir_caso = os.path.join(store, "cases", nombre)
    nombres = rec._localizar_version(dir_caso, entrada["version"], width)
    ref = cs.referencia_version(entrada["case_id"], entrada["version"], width)
    if len(nombres) != 1:
        return None, None, f"{rec._texto_ruta(ref)} omitida: la version ya no esta (o esta duplicada) en cases/"
    dir_v = os.path.join(dir_caso, nombres[0])
    final = os.path.join(dir_v, "final")
    rel = rec._texto_ruta(f"cases/{nombre}/{nombres[0]}")
    antes = {d: _dir_real(ctx, d) for d in (dir_v, final)}
    for d, st in antes.items():
        if st is None:
            sub = "final/" if d == final else "el directorio de la version"
            return None, None, f"{rel} omitida: {sub} no es el directorio esperado (enlace o sustituido; no se sigue)"
    datos = {}
    for f in FICHEROS:
        reutilizado = _reutilizable(dir_v, f, (previos or {}).get(f), antes[dir_v],
                                    min(tope, rec.TOPE_JSON_CASO) if f in FICHEROS_JSON_CASO else tope)
        if reutilizado is not None:
            datos[f] = reutilizado
            continue
        leido = []
        t = min(tope, rec.TOPE_JSON_CASO) if f in FICHEROS_JSON_CASO else tope   # #171: el tope del recorrido
        obj, _m, aviso = rec._leer_de_version(dir_v, f, rel, leido, decodificar=bytes, tope=t)
        if aviso:
            return None, None, aviso
        if leido[-1].st_dev != antes[dir_v].st_dev:
            return None, None, f"{rel} omitida: {f} esta en otro dispositivo que su version (enlace; no se lee)"
        datos[f] = obj
    for d, st in antes.items():
        despues = _dir_real(ctx, d)
        if despues is None or not os.path.samestat(st, despues):
            return None, None, f"{rel} omitida: el directorio cambio durante la lectura (sustituido; no se usa)"
    leidos = {}
    for f, b in datos.items():
        try:
            leidos[f] = (_jsonl if f.endswith(".jsonl") else _json)(b)
        except (ValueError, RecursionError) as e:
            return None, None, f"{rel} omitida: {f} ilegible ({type(e).__name__}: JSON invalido o no finito)"
    meta, req = leidos["metadata.json"], leidos["request.json"]
    if not isinstance(meta, dict) or not isinstance(req, dict) or "request" not in req:
        return None, None, f"{rel} omitida: metadata.json o request.json sin la forma del recorder"
    caso = {k: meta.get(k) for k in ("case_id", "family", "variant", "version", "outcome", "created_at")}
    if meta.get("supersedes_case") is not None:
        caso["supersedes_case"] = meta["supersedes_case"]
    caso.update(request=req["request"], context=leidos["context.json"], constraints=leidos["constraints.json"],
                trajectory=leidos["trajectory.jsonl"], metrics=leidos["metrics.json"],
                validation=leidos["validation.json"], artifacts=leidos["final/artifacts.json"])
    if (caso["case_id"], caso["family"], caso["variant"], caso["version"]) != \
            (entrada["case_id"], entrada["family"], entrada["variant"], entrada["version"]):
        return None, None, f"{rel} omitida: metadata.json no casa con su ruta"
    errores = cs.validar_caso(caso, config)
    if errores:
        return None, None, f"{rel} omitida: no pasa el esquema ({errores[0]['campo']}: {errores[0]['mensaje']})"
    ficheros = {f: _sha(datos[f]) for f in FICHEROS}
    total = _sha("".join(f"{f}\0{ficheros[f]}\n" for f in FICHEROS).encode("utf-8"))
    return caso, {"sha256": total, "ficheros": ficheros, "content_hash": rec.hash_contenido(ficheros)}, None


def es_gold(validation):
    """CA-03: la UNICA regla de Gold del ensamblador (sobre lo leido de `validation.json`)."""
    return isinstance(validation, dict) and validation.get("status") == "approved" \
        and validation.get("approved_by_human") is True


def atado(validation, content_hash):
    """#132: `ok` si el Gold esta atado a este contenido, `sin` si no guarda `content_hash`, `distinto`
    si guarda otro (o algo que no es un hash)."""
    h = validation.get("content_hash") if isinstance(validation, dict) else None
    if h is None:
        return "sin"
    return "ok" if h == content_hash else "distinto"


_MARCAS_OS = ("(bloqueada o sin permisos)", "no se puede examinar")


def _motivo(aviso, store):
    """#123: motivo NORMALIZADO para el manifiesto: sin el texto de un `OSError` (lleva la ruta
    absoluta y depende del idioma del sistema) ni ninguna ruta del store; prefijo `omitida:`."""
    for marca in _MARCAS_OS:
        i = aviso.find(marca)
        if i >= 0:
            aviso = aviso[:i + len(marca)] + " (detalle del sistema omitido)"
    fugas = {store, os.path.realpath(store), os.path.dirname(os.path.abspath(store))}
    fugas |= {ascii(x)[1:-1] for x in list(fugas)} | {json.dumps(x)[1:-1] for x in list(fugas)}
    if any(x and x in aviso for x in fugas) or "Errno" in aviso or "WinError" in aviso:
        aviso = (aviso.split(" ", 1)[0] if aviso.startswith("cases/") or aviso.startswith("'cases/") else "version") \
            + " omitida: ilegible (detalle del sistema omitido)"
    return aviso if " omitida: " in aviso else f"omitida: {aviso}"


def _omision_transitoria(aviso):
    """D-f5 O2: el aviso con el que `leer_caso` omitio un Gold tiene causa TRANSITORIA
    (`_aviso_transitorio` del recorder: bloqueado, sustituido, desaparecido, no examinable; N6: en POSIX
    `EACCES`/`EPERM` no lo son) o el directorio cambio mientras se leia: basta con reensamblar."""
    return rec._aviso_transitorio(aviso) or "cambio durante la lectura" in aviso


def _omision(ref, aviso):
    """D-f5 O2 + N3/N6: una omision de la marca: la referencia CRUDA (se escapa solo al mostrarla), la
    clase del aviso y su causa normalizada (`rec.causa_aviso`)."""
    return {"ref": ref, "clase": "transitorio" if _omision_transitoria(aviso) else "permanente",
            "causa": rec.causa_aviso(aviso)}


def cargar(store, config, raiz, ctx, acumulador=None, tope=TOPE_FICHERO, entrada=None, omisiones=None, codigos=None):
    """Pasada 1 (H5): `(gold, otros, avisos_store, avisos)`. `gold`: `{ref, case_id, version, family,
    variant, supersedes_case, sha256, ficheros, content_hash}` (sin el caso: su texto va al
    `acumulador` y se descarta); `otros`: el resto de versiones con su motivo (manifiesto);
    `avisos_store`: los del recorrido (dependen del reloj: solo `stderr`); `avisos`: deterministas.
    `entrada` (dict opcional, D-f4 F1): recibe `{(case_id, version): h}` de la ENTRADA del ensamblado
    para su firma (`rec.firma_gold`), con la lectura de `validation.json` que DECIDIO el destino de
    cada version (M4): la de `leer_caso` si devolvio el caso (sin entrada si ya no es Gold); si lo
    omitio con aviso (transitorio o permanente), el `content_hash` del recorrido (`_estado_de_cases`,
    el MISMO de `/doctor`; D-f5 O1). Un Gold excluido (sin atar, duplicado, benchmark) sigue en la firma
    con su `content_hash` tal cual (saneado, M5). `omisiones` (lista opcional, D-f5 O2) recibe una
    `_omision` por cada Gold vigente que `leer_caso` omitio por un aviso (dedup, benchmark y «sin atar»
    NO son omisiones: son el resultado del ensamblado). El recorrido lee `metadata.json`/
    `validation.json` con `TOPE_JSON_CASO` (#171), no con `tope`, y exige el `id_prefix` de la config
    (#181/N2). `codigos` (dict opcional, #190) recibe el codigo de cada aviso del recorrido (`otro_prefijo`…)."""
    width = cs.patrones_id(config)[2]
    crudos, gold_rec = {}, {}
    entradas, av, en_curso, _mt, _rels = rec._estado_de_cases(store, raiz, crudos=crudos, tope=rec.TOPE_JSON_CASO,
                                                              gold=gold_rec,   # #134/#171
                                                              id_prefix=config.get("id_prefix"),   # #181/N2
                                                              **({"codigos": codigos} if codigos is not None else {}))
    avisos_store = [av[k] for k in sorted(av)] + [en_curso[k] for k in sorted(en_curso)]
    gold, otros, avisos = [], [], []
    for clave in sorted(entradas):
        e = entradas[clave]
        previos = crudos.pop(clave, None)
        base = {"ref": cs.referencia_version(e["case_id"], e["version"], width), "case_id": e["case_id"],
                "version": e["version"], "family": e["family"]}
        if e["status"] != "approved":
            otros.append(dict(base, sha256=None, particion=None, motivo=f"no Gold (validation.status = {e['status']})"))
            continue
        caso, hashes, aviso = leer_caso(ctx, store, e, config, width, previos, tope)
        if aviso:
            if clave in gold_rec:                                  # un Gold vigente (el que ve `/doctor`)
                if entrada is not None:
                    entrada[clave] = gold_rec[clave]                                   # D-f5 O1 (M4)
                if omisiones is not None:
                    omisiones.append(_omision(base["ref"], aviso))                     # D-f5 O2
            otros.append(dict(base, sha256=None, particion=None, motivo=_motivo(aviso, store)))
            continue
        h = rec.gold_de_version(caso["validation"])
        if entrada is not None and h is not rec.NO_GOLD:
            entrada[clave] = h                                                         # M4: la de `leer_caso`
        if not es_gold(caso["validation"]):
            otros.append(dict(base, sha256=None, particion=None, motivo=(
                f"no Gold (validation.status = {caso['validation'].get('status')}, releido del disco)")))
            continue
        estado = atado(caso["validation"], hashes["content_hash"])
        if estado == "distinto":
            otros.append(dict(base, sha256=None, particion=None, motivo=MOTIVO_SIN_ATAR))
            continue
        if estado == "sin":
            avisos.append(AVISO_SIN_HASH.format(ref=base["ref"]))
        if acumulador is not None:
            acumulador.anadir(base["ref"], e["family"], dd.texto_de_caso(caso))
        gold.append(dict(base, variant=e["variant"], supersedes_case=caso.get("supersedes_case"), **hashes))
        caso = None                                                     # H5: no se guarda
    return gold, otros, avisos_store, avisos


def linea_de(g):
    """Una linea chat/SFT (`messages`) con su procedencia (CA-12). `g` lleva el `caso` leido."""
    caso = g["caso"]
    linea = {"messages": [{k: t[k] for k in CLAVES_TURNO if k in t} for t in caso["trajectory"]],
             "ref": g["ref"], "case_id": g["case_id"], "version": g["version"], "family": g["family"],
             "variant": g["variant"], "outcome": caso["outcome"]}
    if caso.get("supersedes_case") is not None:
        linea["supersedes_case"] = caso["supersedes_case"]
    return linea


def _bytes_linea(linea):
    return (json.dumps(linea, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")


def _fecha_valida(fecha):
    if not isinstance(fecha, str) or not re.fullmatch(r"[0-9]{8}", fecha):
        raise ValueError(f"fecha invalida {fecha!r}: AAAAMMDD")
    datetime.datetime.strptime(fecha, "%Y%m%d")
    return fecha


class _CambioEntrePasadas(Rechazo):
    """H5: un caso incluido no es, en la segunda pasada, el que se leyo en la primera."""


class _Sumidero:
    """Destino en streaming de un JSONL: fichero (o nada, en `--dry-run`), sha256 y lineas contadas."""

    def __init__(self, f=None, recoger=False):
        self.f, self.h, self.n = f, hashlib.sha256(), 0
        self.lineas = [] if recoger else None

    def escribir(self, linea, datos):
        if self.f is not None:
            self.f.write(datos)
        self.h.update(datos)
        self.n += 1
        if self.lineas is not None:
            self.lineas.append(linea)


def _segunda_pasada(ctx, store, config, width, incluidos, sumideros, tope=TOPE_FICHERO):
    """Pasada 2 (H5): relee cada caso incluido, comprueba su sha256 de la pasada 1 y escribe su linea
    redactada (#119) en el sumidero de su particion. `_CambioEntrePasadas` si cambio."""
    for g in sorted(incluidos, key=_clave):
        entrada = {k: g[k] for k in ("case_id", "family", "variant", "version")}
        caso, hashes, aviso = leer_caso(ctx, store, entrada, config, width, tope=tope)
        if aviso or hashes["sha256"] != g["sha256"]:
            que = _motivo(aviso, store) if aviso else "sus ficheros ya no tienen el sha256 de la primera pasada"
            raise _CambioEntrePasadas(f"{rec._texto_ruta(g['ref'])} cambio entre pasadas ({que}); no se publica "
                                      "manifest.json: vuelve a ensamblar")
        linea = rec.redactar_estructura(linea_de(dict(g, caso=caso)))
        caso = None
        sumideros[f"{g['particion']}.jsonl"].escribir(linea, _bytes_linea(linea))


def _manifest(base, directorio, sumideros):
    return dict(base, directorio=directorio,
                ficheros={f: {"sha256": sumideros[f].h.hexdigest(), "lineas": sumideros[f].n} for f in JSONL})


def _bytes_manifest(manifest):
    return (json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def ensamblar(config, raiz_proyecto, benchmark, umbral=dd.UMBRAL_DEFECTO, ventana=dd.VENTANA_DEFECTO,
              fraccion_boilerplate=dd.BOILERPLATE_DEFECTO, conservar_duplicados=False, fecha=None, escribir=True,
              presupuesto=dd.PRESUPUESTO_DEFECTO, tope_fichero=TOPE_FICHERO, devolver_lineas=None,
              espera_bloqueo=ESPERA_BLOQUEO_EXPORTS_S):
    """Ensambla el dataset (ver docstring del modulo). Devuelve `{export_id, ruta, existente, manifest,
    lineas, avisos_store}`; con `escribir=False` no toca el disco (`ruta` None) y, salvo
    `devolver_lineas=False`, devuelve las lineas (el modo de prueba es O(export); el export real no).
    `Rechazo` si la capacidad no esta activa, sin benchmark o con el store manipulado; `ValueError` con
    parametros invalidos; `RedaccionNoDisponible` sin `redact.py` (antes de leer nada)."""
    raiz = rec._raiz(raiz_proyecto)
    rec.config_activa(config, raiz)
    benchmark = set(benchmark or ())
    if not benchmark:
        raise Rechazo(MOTIVO_SIN_BENCHMARK)
    fecha = _fecha_valida(fecha or datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d"))
    dd._fraccion(umbral)
    dd._validar_parametros(ventana, fraccion_boilerplate, presupuesto)
    if isinstance(tope_fichero, bool) or not isinstance(tope_fichero, int) or tope_fichero < 1:
        raise ValueError(f"tope por fichero invalido: {tope_fichero!r}")
    if isinstance(espera_bloqueo, bool) or not isinstance(espera_bloqueo, (int, float)) \
            or not 0 < espera_bloqueo < float("inf"):
        raise ValueError(f"espera del bloqueo invalida: {espera_bloqueo!r} (segundos > 0)")
    rec._redact_mod()                                                    # #119: fail closed, antes de nada
    store = rec.raiz_store(config, raiz)
    ctx = rec._Canon(store, raiz)
    width = cs.patrones_id(config)[2]
    t0 = time.monotonic()
    acc = dd.Acumulador(ventana, presupuesto)
    entrada, omisiones, codigos = {}, [], {}
    gold, otros, avisos_store, avisos = cargar(store, config, raiz, ctx, acc, tope_fichero, entrada, omisiones,
                                               codigos)
    n_otro = sum(1 for c in codigos.values() if c == "otro_prefijo")
    codigos = None
    firma, n_entrada = rec.firma_gold(entrada), len(entrada)                      # D-f4 F1
    entrada = None
    r_dd = acc.agrupar(umbral, fraccion_boilerplate,
                       benchmark_ids={g["ref"] for g in gold if g["family"] in benchmark})   # #145
    acc = None
    grupos, cruces = r_dd["grupos"], r_dd.get("cruces", [])
    avisos += [f"{a['id']}: {a['motivo']}" for a in r_dd["avisos"]]
    try:
        asignados = particionar([{k: g[k] for k in ("ref", "case_id", "version", "family", "supersedes_case")}
                                 for g in gold], benchmark, grupos, conservar_duplicados, cruces)
    except Rechazo as e:
        if n_otro:                                                   # #190: la causa, PRIMERO
            raise Rechazo(f"{causa_otro_prefijo(n_otro)}; {e.mensaje}") from None
        raise
    por_ref = {g["ref"]: g for g in gold}
    casos = [dict({k: a[k] for k in ("ref", "case_id", "version", "family", "particion", "motivo")},
                  **{k: por_ref[a["ref"]][k] for k in ("sha256", "ficheros", "content_hash")}) for a in asignados]
    nucleo = {"version": 1,
              "parametros": {"benchmark": sorted(benchmark), "umbral": umbral, "ventana": ventana,
                             "fraccion_boilerplate": fraccion_boilerplate, "n_min_boilerplate": dd.N_MIN_BOILERPLATE,
                             "presupuesto": presupuesto, "tope_fichero": tope_fichero,
                             "conservar_duplicados": bool(conservar_duplicados)},
              "casos": sorted(casos + otros, key=_clave), "grupos_near_duplicates": grupos, "avisos": sorted(avisos),
              "cruces_near_duplicates": cruces,
              "near_duplicates": {"jaccard": r_dd["jaccard"], "muestreo": r_dd["muestreo"],
                                  "cruce": r_dd.get("cruce", {"criterio": "umbral"})}}
    # #137 (CWE-312/532): TODO texto del manifiesto (motivos con claves de la trayectoria, avisos, refs)
    # pasa por la redaccion (fuente unica), ANTES del hash: el `export_id` es el del manifiesto redactado
    nucleo = rec.redactar_estructura(nucleo)
    pasada1 = time.monotonic() - t0
    sha = _sha(json.dumps(nucleo, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    export_id = f"{fecha}-{sha[:12]}"
    base = dict(nucleo, export_id=export_id, fecha=fecha, sha256_contenido=sha)
    incluidos = [dict(por_ref[a["ref"]], particion=a["particion"]) for a in asignados if a["particion"]]
    gold = por_ref = casos = None

    def pasada(sumideros):
        _segunda_pasada(ctx, store, config, width, incluidos, sumideros, tope_fichero)

    salida = {"export_id": export_id, "ruta": None, "existente": False, "lineas": None, "avisos_store": avisos_store,
              "aviso_marca": None}
    if escribir:
        marca = {"version": 1, "export_id": export_id, "firma": firma, "gold": n_entrada,
                 "parametros": nucleo["parametros"],                           # F2/M6 (ya redactados, #137)
                 "omitidos": len(omisiones), "omitidos_muestra": _muestra(omisiones)}   # D-f5 O2
        salida["ruta"], salida["existente"], salida["manifest"], salida["aviso_marca"] = _publicar_export(
            ctx, store, export_id, base, pasada, espera_bloqueo, pasada1, marca)
    else:
        recoger = devolver_lineas is not False
        sumideros = {f: _Sumidero(recoger=recoger) for f in JSONL}
        pasada(sumideros)
        salida["manifest"] = _manifest(base, export_id, sumideros)
        if recoger:
            salida["lineas"] = {f: sumideros[f].lineas for f in JSONL}
    return salida


# ------------------------------------------------------------------ frescura del dataset (T-10, `/doctor`)

def _bloqueo_tomado(exports):
    """#156: True si OTRO ensamblador tiene `exports/.lock` tomado AHORA. Sondeo de solo lectura: abre
    el fichero de bloqueo SIN crearlo (`O_RDONLY`, sin seguir un enlace), prueba UN bloqueo no bloqueante
    y lo suelta al instante; sin fichero, o si no se puede ni abrir ni sondear, False (no se inventa un
    «en curso»)."""
    ruta = os.path.join(exports, BLOQUEO_EXPORTS)
    try:
        st = rec._stat_sin_seguir(ruta)
        if rec._es_enlace_st(st) or not stat.S_ISREG(st.st_mode):
            return False
        f = open(ruta, "rb", opener=rec._abrir_sin_seguir)
    except OSError:
        return False
    with f:
        try:
            rec._intentar_bloqueo(f)
        except OSError as e:
            return rec._es_contencion(e)
        try:
            if rec._WINDOWS:
                import msvcrt
                f.seek(0)
                msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except OSError:
            pass
    return False


MARCA = ".ultimo.json"                          # D-f4 F2: marca del ultimo ensamblado (empieza por `.`: no es un export)
TOPE_MARCA = 4 * 1024
CLAVES_MARCA = ("version", "export_id", "directorio", "firma", "gold", "creado", "parametros", "omitidos",
                "omitidos_muestra")
PATRON_EXPORT_ID = re.compile(r"[0-9]{8}-[0-9a-f]{12}")
PATRON_DIRECTORIO = re.compile(r"[0-9]{8}-[0-9a-f]{12}(\.([2-9]|[1-9][0-9]))?")        # M3: `.2`…`.99`
PATRON_FIRMA = re.compile(r"[0-9a-f]{64}")
MARGEN_ESTADO_S = 0.3                           # M10: margen propio de `estado_dataset` tras el recuento
REMEDIO_MARCA = "retira `exports/.ultimo.json` a mano (solo ese nombre) y vuelve a ensamblar"
MARCA_BLOQUEADA = ("bloqueada por otro proceso o sin permisos: vuelve a pasar /doctor; si persiste, revisa los "
                   "permisos de `exports/.ultimo.json`")                   # #184/N8: NUNCA `REMEDIO_MARCA`
UMBRAL_DOCTOR = ("el recuento de /doctor corta entre ~1 000 y ~2 000 versiones en caliente, segun la carga de la "
                 "maquina (en frio depende del antivirus y del sistema de ficheros; medido, Windows); "
                 "`dataset-assembler.py --estado` lo verifica sin tope: ~1-2 ms por version en caliente")   # #188
MUESTRA_OMITIDOS = 10                           # D-f5 O2: Gold omitidos que guarda la marca como ejemplo
CLASES_OMISION = ("transitorio", "permanente")
FRACCIONES_PARAMETROS = ("umbral", "fraccion_boilerplate")                 # #180/N1: (0, 1], finitos
ENTEROS_PARAMETROS = ("ventana", "n_min_boilerplate", "presupuesto", "tope_fichero")   # >= 1, nunca bool
CLAVES_PARAMETROS = FRACCIONES_PARAMETROS + ENTEROS_PARAMETROS + ("conservar_duplicados",)
BENCHMARK_MAX = 256                             # #180/N1: caracteres por familia de `benchmark`
PATRON_BENCHMARK_RESUMIDO = re.compile(r"[0-9]{1,9} familias")          # el fallback de `_bytes_marca`


class _MarcaBloqueada(str):
    """#184/N8: el motivo de una marca que no se pudo examinar o leer por un bloqueo o por permisos
    (antivirus, backup): no es una marca ajena, asi que nunca lleva `REMEDIO_MARCA`."""


def _motivo_parametros(p):
    """#180/N1: None si `p` es EXACTAMENTE lo que escribe el ensamblador (o `{}`, el fallback), o por que
    no. El motivo nunca repite un valor de la entrada."""
    if not isinstance(p, dict):
        return "parametros invalidos (no es un objeto)"
    if not p:
        return None
    if set(p) - {"benchmark"} != set(CLAVES_PARAMETROS):
        return "parametros invalidos (claves distintas de las del ensamblador)"
    for k in FRACCIONES_PARAMETROS:
        v = p[k]
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or not 0 < v <= 1:
            return f"parametros invalidos ({k} fuera de (0, 1])"
    for k in ENTEROS_PARAMETROS:
        if isinstance(p[k], bool) or not isinstance(p[k], int) or p[k] < 1:
            return f"parametros invalidos ({k} no es un entero >= 1)"
    if not isinstance(p["conservar_duplicados"], bool):
        return "parametros invalidos (conservar_duplicados no es booleano)"
    if "benchmark" in p:
        b = p["benchmark"]
        if isinstance(b, str):
            if not PATRON_BENCHMARK_RESUMIDO.fullmatch(b):
                return "parametros invalidos (benchmark resumido sin la forma `<n> familias`)"
        elif not isinstance(b, list) or not all(isinstance(x, str) and len(x) <= BENCHMARK_MAX for x in b):
            return f"parametros invalidos (benchmark: lista de familias de <= {BENCHMARK_MAX} caracteres)"
    return None


def _motivo_referencia(ref):
    """#189: None si `ref` es una referencia `<case_id>@v<N>` que acepta el lector de la marca, o por que
    no. FUENTE UNICA (la usan `_motivo_omisiones` y `_muestra`): la MISMA regla que un `case_id`
    (`rpartition("@v")`; la parte izquierda con `rec._motivo_case_id` sin `id_prefix` —longitud— y sin
    controles ni caracteres de formato Unicode, `cs.CATEGORIAS_PROHIBIDAS_ROOT`) y un numero de version
    de 1 a 9 cifras ASCII. Admite lo que `validar_config`/`validar_caso` admiten en `family`/`variant`
    (un espacio interior, no ASCII); el motivo nunca repite la referencia."""
    if not isinstance(ref, str):
        return "referencia que no es texto"
    case_id, sep, numero = ref.rpartition("@v")
    if not sep or not case_id:
        return "referencia sin la forma `<case_id>@v<N>`"
    motivo = rec._motivo_case_id({"case_id": case_id}, None)
    if motivo:
        return motivo
    if any(ord(c) < 32 or unicodedata.category(c) in cs.CATEGORIAS_PROHIBIDAS_ROOT for c in case_id):
        return "referencia con caracteres de control o de formato Unicode"
    if not (numero.isascii() and numero.isdigit()) or len(numero) > 9:
        return "referencia con una version que no es de 1 a 9 cifras ASCII"
    return None


def _motivo_omisiones(n, muestra):
    """D-f5 O2 + N3: None si `omitidos`/`omitidos_muestra` tienen el esquema de la marca, o por que no:
    entero >= 0 (nunca bool) y lista de <= `MUESTRA_OMITIDOS` (y <= `n`) objetos `{ref, clase, causa}`,
    con `ref` CRUDA que acepta `_motivo_referencia` (#189: la regla de un `case_id`, no `\\S+`)."""
    if isinstance(n, bool) or not isinstance(n, int) or n < 0:
        return "numero de Gold omitidos invalido"
    if not isinstance(muestra, list) or len(muestra) > MUESTRA_OMITIDOS or len(muestra) > n:
        return "muestra de Gold omitidos invalida"
    for o in muestra:
        if not isinstance(o, dict) or sorted(o) != ["causa", "clase", "ref"]:
            return "muestra de Gold omitidos invalida"
        if _motivo_referencia(o["ref"]):
            return "referencia de la muestra de omitidos invalida"
        if o["clase"] not in CLASES_OMISION or o["causa"] not in rec.CAUSAS_AVISO:
            return "clase o causa de la muestra de omitidos invalida"
    return None


def _muestra(omisiones):
    """D-f5 O2: las primeras `MUESTRA_OMITIDOS` omisiones (en orden `(case_id, version)`), SIN las que la
    redaccion cambiaria (lo que se persiste va redactado; una referencia redactada no se guarda) y SIN
    las que su lector rechazaria (#189: `_motivo_referencia`, la fuente unica de esa validacion)."""
    muestra = []
    for o in omisiones:
        if len(muestra) == MUESTRA_OMITIDOS:
            break
        if _motivo_referencia(o["ref"]) is None and rec.redactar_estructura(o["ref"]) == o["ref"]:
            muestra.append(o)
    return muestra


def _motivo_marca(m):
    """None si `m` es una marca con el esquema de F2, o por que no lo es."""
    if not isinstance(m, dict) or tuple(sorted(m)) != tuple(sorted(CLAVES_MARCA)):
        return "no tiene el esquema de la marca"
    if m["version"] != 1 or isinstance(m["version"], bool):
        return "version de la marca desconocida"
    if not isinstance(m["export_id"], str) or not PATRON_EXPORT_ID.fullmatch(m["export_id"]):
        return "export_id invalido"
    d = m["directorio"]
    if not isinstance(d, str) or not PATRON_DIRECTORIO.fullmatch(d) or d.split(".", 1)[0] != m["export_id"]:
        return "directorio invalido"
    if not isinstance(m["firma"], str) or not PATRON_FIRMA.fullmatch(m["firma"]):
        return "firma invalida"
    if isinstance(m["gold"], bool) or not isinstance(m["gold"], int) or m["gold"] < 0:
        return "numero de Gold invalido"
    if not isinstance(m["creado"], str) or len(m["creado"]) > 64:
        return "creado o parametros invalidos"
    return _motivo_parametros(m["parametros"]) or _motivo_omisiones(m["omitidos"], m["omitidos_muestra"])


def _leer_marca(exports, hasta=None):
    """F3: `(marca, None)` si `exports/.ultimo.json` es una marca VALIDA de la pieza; `(None, None)` si
    no existe; `(None, motivo)` si existe y no lo es (enlace, no regular, con enlaces duros, mayor de
    `TOPE_MARCA`, ilegible o sin el esquema: ajena). Se abre sin seguir enlaces y se lee del
    DESCRIPTOR comprobado (`rec._leer_json_reintentando`: misma identidad que su `lstat`, un solo
    nombre, tope), con los reintentos acotados por `hasta` (#170: `rec._PlazoAgotado` se propaga)."""
    ruta = os.path.join(exports, MARCA)
    try:
        st = rec._stat_sin_seguir(ruta)
    except FileNotFoundError:
        return None, None
    except OSError:
        return None, _MarcaBloqueada(f"exports/{MARCA} no se puede examinar: {MARCA_BLOQUEADA}")   # #184/N8
    enlace = rec._es_enlace_st(st)
    if enlace is None:
        enlace = bool(rec._motivo_enlace(ruta, ruta))
    if enlace:
        return None, f"exports/{MARCA} es un {rec.MOTIVO_ENLACE}"
    if not stat.S_ISREG(st.st_mode):
        return None, f"exports/{MARCA} no es un fichero regular"
    if st.st_nlink != 1:
        return None, f"exports/{MARCA} es un enlace duro compartido ({st.st_nlink} nombres, CWE-59)"
    if st.st_size > TOPE_MARCA:
        return None, f"exports/{MARCA} ocupa {st.st_size} bytes, por encima de {TOPE_MARCA}"
    try:
        m, _mt = rec._leer_json_reintentando(ruta, st, None, _json, TOPE_MARCA, hasta)
    except rec._FicheroNoPropio as e:
        return None, f"exports/{MARCA}: {e.mensaje}"
    except PermissionError:                                                  # #184/N8: agotados los reintentos
        return None, _MarcaBloqueada(f"exports/{MARCA} {MARCA_BLOQUEADA}")
    except (OSError, ValueError, RecursionError) as e:
        return None, f"exports/{MARCA} no se puede leer ({type(e).__name__})"
    motivo = _motivo_marca(m)
    return (None, f"exports/{MARCA}: {motivo}") if motivo else (m, None)


def _serializar_marca(marca):
    return (json.dumps(marca, ensure_ascii=True, sort_keys=True) + "\n").encode("utf-8")


def _bytes_json(valor):
    """Bytes de `valor` DENTRO de la marca (mismo `ensure_ascii`/`sort_keys` que `_serializar_marca`)."""
    return len(json.dumps(valor, ensure_ascii=True, sort_keys=True))


def _bytes_marca(marca):
    """Bytes de la marca (<= `TOPE_MARCA`, N3), con COMO MUCHO 3 serializaciones de la marca (#196: nunca
    en bucle, y solo la primera es la entera): si no cabe ni sin la muestra de omitidos, lo que no cabe
    es `benchmark` y se resume ANTES en su numero de familias (y, como ultimo recurso, `parametros`
    queda en `{}`: informativos, M6); despues la muestra se recorta DE UNA VEZ, con los bytes de cada
    entrada (`omitidos` sigue siendo el numero real). Con `ensure_ascii`, un caracter es un byte, asi
    que la cuenta es exacta; `_escribir_marca` valida igual los bytes que va a publicar."""
    marca = dict(marca)
    datos = _serializar_marca(marca)                                     # 1: la entera
    if len(datos) <= TOPE_MARCA:
        return datos
    muestra = marca.get("omitidos_muestra")
    muestra = list(muestra) if isinstance(muestra, list) else None
    tamanos = [_bytes_json(o) for o in muestra or ()]

    def lista(k):                                                        # bytes de `[e1, …, ek]`
        return 2 + sum(tamanos[:k]) + 2 * max(0, k - 1)
    base = len(datos) - (lista(len(tamanos)) - 2 if muestra is not None else 0)   # la marca con la muestra vacia
    params = marca.get("parametros")
    bench = params.get("benchmark") if isinstance(params, dict) else None
    if base > TOPE_MARCA and isinstance(bench, list):                   # lo que no cabe es el benchmark
        marca["parametros"] = dict(params, benchmark=f"{len(bench)} familias")
        if muestra is not None:
            marca["omitidos_muestra"] = []
        base = len(_serializar_marca(marca))                            # 2: ya pequeña
    if base > TOPE_MARCA:
        base -= _bytes_json(marca.get("parametros")) - 2
        marca["parametros"] = {}
    if muestra is not None:
        k = len(muestra)
        while k and base - 2 + lista(k) > TOPE_MARCA:                   # aritmetica, sin serializar
            k -= 1
        marca["omitidos_muestra"] = muestra[:k]
    return _serializar_marca(marca)                                     # 2 o 3


def _motivo_bytes_marca(datos):
    """N3: None si `datos` (los bytes EXACTOS que se van a publicar) pasan el lector de la marca
    (`TOPE_MARCA` y `_motivo_marca`), o por que no."""
    if len(datos) > TOPE_MARCA:
        return f"{len(datos)} bytes, por encima de {TOPE_MARCA}"
    try:
        return _motivo_marca(_json(datos))
    except (ValueError, RecursionError):
        return "no es JSON"


def _escribir_marca(ctx, exports, marca):
    """F2/M8: publica `exports/.ultimo.json` CON `exports/.lock` tomado: `.tmp-<token>` propio con
    `O_EXCL`, comprobado (G4) antes y despues de escribirle, `fsync`, y `rec._reemplazar` (reintentos
    acotados; el reemplazo sustituye el NOMBRE: nunca escribe a traves de un enlace). Una marca
    existente que no es de la pieza (`_leer_marca`) NO se reemplaza. El temporal se retira SIEMPRE en
    un `finally` (`_retirar_temporal_propio`). Devuelve None o el aviso (el export es valido igual; el
    siguiente ensamblado, «ya existe», la reescribe). Limite declarado (el G3 del recorder): entre la
    comprobacion de la marca vigente y el reemplazo, un tercero con escritura en `exports/` puede
    sustituirla; el reemplazo solo cambia ese nombre."""
    nombre = f"exports/{MARCA}"
    _m, ajena = _leer_marca(exports)
    if isinstance(ajena, _MarcaBloqueada):                                   # #184/N8
        return f"{ajena} (no se ha reescrito: el export es valido; el siguiente ensamblado la reescribe)"
    if ajena:
        return f"{ajena}: no se reemplaza (no es una marca valida del ensamblador); {REMEDIO_MARCA}"
    datos = _bytes_marca(dict(marca, creado=datetime.datetime.now(datetime.timezone.utc)
                              .strftime("%Y-%m-%dT%H:%M:%SZ")))
    motivo = _motivo_bytes_marca(datos)                                      # N3: nunca una que su lector rechace
    if motivo:
        return (f"{nombre} no se publica: la marca que se iba a escribir no pasaria su propio lector "
                f"({motivo}); el export es valido, pero /doctor y `--estado` siguen comparando con la marca "
                "anterior (si la hay): su frescura no describe este ensamblado")   # #189 (c)
    tmp = os.path.join(exports, rec.PREFIJO_TEMPORAL + secrets.token_hex(8))
    st = None
    try:
        f = rec._abrir_exclusivo(tmp)
        with f:
            st = os.fstat(f.fileno())
            _verificar(ctx, tmp, st)
            f.write(datos)
            f.flush()
            os.fsync(f.fileno())
            _verificar(ctx, tmp, st)
        _m, ajena = _leer_marca(exports)
        if isinstance(ajena, _MarcaBloqueada):                               # #184/N8
            return f"{ajena} (no se ha reescrito: el export es valido; el siguiente ensamblado la reescribe)"
        if ajena:
            return f"{ajena}: no se reemplaza (no es una marca valida del ensamblador); {REMEDIO_MARCA}"
        rec._reemplazar(tmp, os.path.join(exports, MARCA))
    except PermissionError:                                                  # #184/N8: bloqueada al reemplazar
        return (f"{nombre} {MARCA_BLOQUEADA} (no se ha reescrito: el export es valido; el siguiente ensamblado "
                "la reescribe)")
    except (OSError, Rechazo) as e:
        detalle = e.mensaje if isinstance(e, Rechazo) else type(e).__name__
        return (f"{nombre} no se pudo publicar ({rec._texto_seguro(detalle)}): el export es valido; el siguiente "
                "ensamblado («ya existe») la reescribe")
    finally:
        if st is not None:
            rec._retirar_temporal_propio(tmp, st)
    return None


def _texto_parametros(p):
    """M6: los parametros del ultimo ensamblado, compactos (informativos). #180 (b, defensa en
    profundidad): TODO valor pasa por `rec._texto_ruta`, aunque `_motivo_marca` ya valida su esquema."""
    if not p:
        return "sin parametros registrados"
    t = rec._texto_ruta
    bench = p.get("benchmark")
    bench = ",".join(t(b) for b in bench) if isinstance(bench, list) else t(bench)
    duplicados = "conservados" if p.get("conservar_duplicados") is True else "uno por grupo"
    return (f"benchmark={bench} umbral={t(p.get('umbral'))} ventana={t(p.get('ventana'))} "
            f"boilerplate={t(p.get('fraccion_boilerplate'))} duplicados={duplicados}")


def _texto_omisiones(marca, nombre):
    """D-f5 O3 + N6: el motivo de `con_omisiones`: cuantos Gold omitio el ultimo ensamblado, un ejemplo
    (la referencia ESCAPADA, su causa y su clase) y los remedios."""
    n, muestra = marca["omitidos"], marca["omitidos_muestra"]
    texto = f"{n} Gold omitido{'s' if n != 1 else ''} en el ultimo ensamblado `{nombre}`"
    if muestra:
        o = muestra[0]
        texto += f" (p. ej. {rec._texto_ruta(o['ref'])}: {o['causa']}, {o['clase']})"
    texto += (": corrige la causa y reensambla; si era transitoria, basta con reensamblar; si el contenido no se "
              "puede recuperar, rechazalo (`set-status <case_id> <version> rejected`)")
    if any(o["causa"] == "sin permisos" for o in muestra):
        texto += "; sin permisos: revisa los permisos y reensambla"
    return texto


def causa_otro_prefijo(n):
    """#190: la causa de `n` versiones omitidas por otro `id_prefix` (primero en `/doctor`, `--estado` y
    el rechazo del ensamblador)."""
    return (f"{n} version{'es' if n != 1 else ''} con otro `id_prefix` que el de training.json: restauralo o "
            "usa otro `root`")


def causa_validacion_ilegible(n):
    """#191/#197: la causa de `n` versiones con `validation.json` ilegible por una causa PERMANENTE
    (permisos, JSON roto o esquema)."""
    return (f"{n} version{'es' if n != 1 else ''} con validation.json ilegible: no se sabe si "
            f"{'son' if n != 1 else 'es'} Gold (revisa sus permisos y su contenido)")


def _export_completo(exports, directorio):
    """F3: `exports/<directorio>/` es un directorio real (no enlace) con un `manifest.json` REGULAR (no se lee)."""
    d = os.path.join(exports, directorio)
    if rec._tipo_entrada(d, d) != "dir":
        return False
    ruta_m = os.path.join(d, MANIFEST)
    try:
        st = rec._stat_sin_seguir(ruta_m)
    except OSError:
        return False
    enlace = rec._es_enlace_st(st)
    if enlace is None:
        enlace = bool(rec._motivo_enlace(ruta_m, ruta_m))
    return not enlace and stat.S_ISREG(st.st_mode)


def estado_dataset(store, resumen=None, hasta=None):
    """Frescura del dataset (T-10, CA-07; D-f4), SOLO LECTURA y sin red, para `/doctor` y `--estado`:
    `{estado, exports, incompletos, en_curso, otros, ultimo, export_id, parametros, motivo}`. Responde a
    «¿reensamblar ahora cambiaria la ENTRADA del ultimo ensamblado?», no a «¿que incluyo el export?»:
    compara la `firma` de `resumen` (`rec.resumen_store`: los Gold humanos con su `content_hash`
    saneado) con la de la marca `exports/.ultimo.json` (F2), sin leer ningun `manifest.json`. `hasta`
    (default: el del resumen) = instante de `rec._crono()` en que vencio el plazo del recuento; esta
    funcion tiene un margen PROPIO (`MARGEN_ESTADO_S`, M10) para listar `exports/` y leer la marca.
    Cada entrada de `exports/` (#156): `export` (directorio real con un `manifest.json` regular, sin
    seguir enlaces), `en_curso` (sin `manifest.json` y modificado dentro de `rec.GRACIA_EN_CURSO_S`, o
    el mas reciente si otro ensamblador tiene `exports/.lock` tomado), `incompleto` (sin
    `manifest.json` y mas viejo) u `otros` (un fichero suelto, un enlace); los nombres con `.` (la
    marca, el bloqueo, temporales) no cuentan. `estado`: `sin_gold`; `sin_export` (hay Gold y ningun
    export completo); `no_verificable` (sin marca —«reensambla para registrar el ultimo ensamblado»—,
    marca ajena o invalida —`REMEDIO_MARCA`—, bloqueada o sin permisos —`MARCA_BLOQUEADA`, #184—, su
    export ya no esta completo, o `exports/` no se puede recorrer); `parcial` (el recuento se CORTO o hubo
    un aviso TRANSITORIO, M1: «no verificado» con `--estado`; salvo que los Gold ya contados superen los
    de la marca, M10: `desactualizado`); `al_dia` (misma firma y ningun Gold omitido: mismo
    train/benchmark con los parametros del ultimo ensamblado, M6); `con_omisiones` (misma firma y
    `omitidos > 0`: D-f5 O3, «corrige la causa y reensambla»); o `desactualizado` (otra firma, el motivo
    por RECUENTO sin nombrar casos; o 0 Gold vigentes frente a los de una marca valida cuyo export sigue
    completo, #183). Dos causas van PRIMERO: versiones con otro `id_prefix` (#190: `con_omisiones`,
    antes que todo lo demas tras recorrer `exports/`, tambien que #183) y, con la firma igual, versiones
    con `validation.json` ilegible por una causa permanente (#191: `con_omisiones`, nunca `al_dia`)."""
    res = resumen if isinstance(resumen, dict) else {}
    n_gold = res.get("n_gold") or 0
    parcial = bool(res.get("truncado"))
    transitorias = res.get("transitorias") or 0
    hasta = res.get("hasta") if hasta is None else hasta
    limite = None if hasta is None else hasta + MARGEN_ESTADO_S
    exports = os.path.join(store, "exports")
    salida = {"estado": None, "exports": 0, "incompletos": 0, "en_curso": 0, "otros": 0, "ultimo": None,
              "export_id": None, "parametros": None, "motivo": ""}

    def agotado():
        return limite is not None and rec._crono() >= limite

    def cortar():
        salida.update(estado="parcial", motivo=f"se agoto el tope de tiempo de /doctor antes de recorrer exports/ ({UMBRAL_DOCTOR})")
        return salida
    if agotado():
        return cortar()
    tipo = rec._tipo_entrada(exports, exports)
    if tipo == "enlace" or tipo == "otro":
        salida.update(estado="no_verificable", motivo=("exports/ es un enlace: no se sigue" if tipo == "enlace"
                                                        else "exports/ no es un directorio"))
        return salida
    if tipo == "dir":
        entradas = []
        try:
            with os.scandir(exports) as it:
                for i, e in enumerate(it, 1):
                    if i % rec.LISTADO_CADA == 0 and agotado():
                        return cortar()
                    if not e.name.startswith("."):
                        entradas.append(e)
        except OSError as e:
            salida.update(estado="no_verificable", motivo=f"exports/ no se puede listar ({type(e).__name__})")
            return salida
        sin_manifest = []
        for i, e in enumerate(sorted(entradas, key=lambda x: x.name), 1):
            if i % rec.LISTADO_CADA == 0 and agotado():
                return cortar()
            if rec._tipo_entrada(e, e.path) != "dir":
                salida["otros"] += 1
            elif _export_completo(exports, e.name):
                salida["exports"] += 1
            else:
                try:
                    mtime = rec._stat_sin_seguir(e.path).st_mtime
                except OSError:
                    mtime = None
                sin_manifest.append((mtime, e.name))
        vivo = _bloqueo_tomado(exports) if sin_manifest else False
        reciente = max(sin_manifest, key=lambda x: (x[0] or 0, x[1])) if vivo else None
        for mtime, nombre in sin_manifest:
            edad = None if mtime is None else rec._edad(mtime)
            if (mtime, nombre) == reciente or (edad is not None and 0 <= edad < rec.GRACIA_EN_CURSO_S):
                salida["en_curso"] += 1
            else:
                salida["incompletos"] += 1
    n_otro = res.get("otro_prefijo") or 0
    if n_otro:                                                              # #190: la causa, PRIMERO
        salida.update(estado="con_omisiones", motivo=causa_otro_prefijo(n_otro))
        return salida
    dudoso = parcial or transitorias
    if not n_gold and not dudoso:
        if salida["exports"] and not agotado():                             # #183/N7: solo si hay exports
            try:
                marca, _ajena = _leer_marca(exports, limite)
            except rec._PlazoAgotado:
                marca = None
            if marca is not None and marca["gold"] > 0 and _export_completo(exports, marca["directorio"]):
                salida.update(estado="desactualizado", ultimo=marca["directorio"], export_id=marca["export_id"],
                              parametros=marca["parametros"], motivo=(
                                  f"0 Gold vigentes frente a {marca['gold']} en el ultimo ensamblado "
                                  f"`{marca['directorio']}`: ese export contiene casos que ya no son Gold y no se "
                                  "puede reensamblar sin Gold; si no debe usarse, archivalo a mano"))
                return salida
        salida.update(estado="sin_gold", motivo="ningun caso Gold: nada que exportar")
        return salida
    if not salida["exports"]:
        if n_gold:
            salida.update(estado="sin_export", motivo="hay Gold y ningun export con manifest.json todavia")
        else:
            salida.update(estado="parcial", motivo=f"recuento PARCIAL sin ningun Gold contado todavia ({UMBRAL_DOCTOR})")
        return salida
    if agotado():
        return cortar()
    try:
        marca, ajena = _leer_marca(exports, limite)
    except rec._PlazoAgotado:                                               # #170
        salida.update(estado="parcial", motivo=f"exports/{MARCA} no se pudo leer antes del tope de /doctor "
                                               f"(bloqueada); {UMBRAL_DOCTOR}")
        return salida
    if marca is None:
        if isinstance(ajena, _MarcaBloqueada):                              # #184/N8: nunca retirarla
            salida.update(estado="no_verificable", motivo=str(ajena))
            return salida
        salida.update(estado="no_verificable", motivo=(f"{ajena}: {REMEDIO_MARCA}" if ajena else
                                                        f"sin marca del ultimo ensamblado (exports/{MARCA}): "
                                                        "reensambla para registrarlo"))
        return salida
    nombre = marca["directorio"]
    salida.update(export_id=marca["export_id"], parametros=marca["parametros"])
    if not _export_completo(exports, nombre):
        salida.update(estado="no_verificable", motivo=(f"el export `{nombre}` del ultimo ensamblado ya no esta "
                                                        "completo en exports/: reensambla"))
        return salida
    salida["ultimo"] = nombre
    if dudoso:
        if n_gold > marca["gold"]:                                          # M10: cierto aun siendo parcial
            salida.update(estado="desactualizado", motivo=(f"al menos {n_gold} Gold vigentes frente a {marca['gold']} en "
                                                            f"el ultimo ensamblado `{nombre}` (recuento parcial)"))
        else:
            que = "recuento PARCIAL" if parcial else f"aviso transitorio en {transitorias} version(es)"
            salida.update(estado="parcial", motivo=(f"{que}: no se compara con el ultimo ensamblado `{nombre}`; "
                                                     f"{UMBRAL_DOCTOR}"))
        return salida
    n_val = res.get("validacion_ilegible") or 0
    if res.get("firma") == marca["firma"] and (marca["omitidos"] or n_val):   # D-f5 O3 + #191
        partes = ([causa_validacion_ilegible(n_val)] if n_val else []) + (
            [_texto_omisiones(marca, nombre)] if marca["omitidos"] else [])
        salida.update(estado="con_omisiones", motivo="; ".join(partes))
    elif res.get("firma") == marca["firma"]:
        salida.update(estado="al_dia", motivo=(f"ultimo ensamblado `{nombre}`, con los parametros del ultimo ensamblado "
                                               f"({_texto_parametros(marca['parametros'])})"))
    elif n_gold != marca["gold"]:
        salida.update(estado="desactualizado", motivo=(f"{n_gold} Gold vigentes frente a {marca['gold']} en el ultimo "
                                                        f"ensamblado `{nombre}`"))
    else:
        salida.update(estado="desactualizado", motivo=(f"mismo numero de Gold ({n_gold}) que el ultimo ensamblado "
                                                        f"`{nombre}`, contenido distinto"))
    return salida


TEXTO_DATASET = {"sin_gold": "sin Gold", "sin_export": "desactualizado", "desactualizado": "desactualizado",
                 "al_dia": "al dia", "con_omisiones": "\u26a0\ufe0f con omisiones", "no_verificable": "no verificable",
                 "parcial": "no verificado (PARCIAL)"}


def texto_estado(res, ds):
    """Texto del recuento del case store y de la frescura del dataset (T-10): el MISMO en `/doctor`
    (la capacidad `training` lo pinta) y en `--estado` (F4). `res` = `rec.resumen_store`, `ds` =
    `estado_dataset`."""
    estados = " · ".join(f"{k} {n}" for k, n in res["por_estado"].items())
    partes = [f"casos: {estados} ({res['versiones']} versiones)",
              f"incompletas {res['incompletas']} · temporales huerfanos {res['huerfanos']}"
              + (f" · demasiado grandes {res['grandes']} (sin leer)" if res.get("grandes") else "")
              + (f" · cortadas por el tope {res['cortadas']}" if res.get("cortadas") else "")
              + (f" · otros avisos {res['otros_avisos']}" if res["otros_avisos"] else "")
              + (f" · en curso {res['en_curso']}" if res["en_curso"] else "")]
    if res["truncado"]:
        total = f"al menos {res['casos_total']}" if res.get("listado_parcial") else f"{res['casos_total']}"
        partes.append(f"recuento PARCIAL: {res['casos_vistos']} de {total} casos (tope de "
                      f"{res['plazo_s']:g} s; el total lo da `case-recorder.py index check` y la frescura "
                      "`dataset-assembler.py --estado`)")
    dataset = f"dataset: {TEXTO_DATASET.get(ds['estado'], ds['estado'])} ({ds['motivo']})"
    for clave, que in (("incompletos", "export(s) incompleto(s)"), ("en_curso", "export(s) en curso"),
                       ("otros", "entrada(s) de exports/ que no son un export")):
        if ds.get(clave):
            dataset += f" · {ds[clave]} {que}"
    partes.append(dataset)
    return " · ".join(partes)


# ------------------------------------------------------------------ escritura del export (sin destruir nada)

def _verificar(ctx, ruta, st_propio):
    """Contrato G4 del recorder (#118): `realpath` EXACTAMENTE el esperado y el nombre sigue siendo el
    fichero creado; si no -> `_Manipulado` que nombra donde quedo SOLO si es el creado; nunca borra."""
    rec._verificar_creado(ctx, ruta, st_propio, QUIEN)


def _abrir_export(ctx, ruta):
    """`(fichero, fstat)`: crea `ruta` con `O_CREAT | O_EXCL` (nunca abre un nombre existente) y la
    comprueba YA, antes de escribir un byte (#118: nada fluye a traves de un directorio sustituido)."""
    try:
        f = rec._abrir_exclusivo(ruta)
    except FileExistsError:
        raise rec._Manipulado(f"{ctx.rel(ruta)} ya existia en el export recien creado (¿nombre plantado? "
                              "CWE-59/367); no se escribe a traves de el") from None
    try:
        st = os.fstat(f.fileno())
        _verificar(ctx, ruta, st)
    except BaseException:
        f.close()
        raise
    return f, st


def _publicar_manifest(ctx, destino, datos):
    """`manifest.json` (el que marca el export como COMPLETO) desde un `.tmp-<token>` propio, publicado
    sin sobrescribir (`_enlazar_sin_sobrescribir`) y retirando el temporal por la regla del recorder;
    comprobado despues (#125/#133)."""
    final = os.path.join(destino, MANIFEST)
    tmp = os.path.join(destino, rec.PREFIJO_TEMPORAL + secrets.token_hex(8))
    try:
        f = rec._abrir_exclusivo(tmp)
    except FileExistsError:
        raise rec._Manipulado(f"{ctx.rel(tmp)} ya existia (¿nombre plantado?); no se escribe a traves de el") from None
    st, publicado, fallo_tmp = None, False, None
    try:
        with f:
            st = os.fstat(f.fileno())
            try:
                _verificar(ctx, tmp, st)                 # #136: ANTES de escribir un byte (regla de #118)
                f.write(datos)
                f.flush()
                _verificar(ctx, tmp, st)
            except rec._Manipulado as e:
                fallo_tmp = e
        if fallo_tmp is None:
            try:
                rec._enlazar_sin_sobrescribir(tmp, final)
            except FileExistsError:
                raise rec._Manipulado(f"{ctx.rel(final)} ya existia en el export recien creado; no se sobrescribe") from None
            publicado = True
    finally:
        retirado = st is not None and rec._retirar_temporal_propio(tmp, st)
    if fallo_tmp is not None:
        if retirado:                                     # #136: el aviso solo nombra lo que sigue existiendo
            raise rec._Manipulado(f"{ctx.rel(tmp)}: el directorio cambio antes de publicar el manifiesto (CWE-59/367); "
                                  "el temporal propio ya se retiro (no queda nada que retirar a mano; nada del "
                                  f"manifiesto se escribio fuera); {QUIEN} no borra nada mas") from None
        raise fallo_tmp
    if publicado and not retirado:
        raise OSError(errno.EIO, f"{ctx.rel(final)} publicado pero su temporal {os.path.basename(tmp)} no se pudo "
                                 "retirar: retira ese temporal a mano (solo ese nombre)")
    _verificar(ctx, final, st)


def _sha_fichero(directorio, nombre):
    """sha256 en STREAMING (bloques de 64 KiB, #122) de un fichero de un export, leido por descriptor sin
    seguir enlaces (regular, un solo nombre, la identidad de su `lstat`); None si no se puede o no vale."""
    ruta = os.path.join(directorio, nombre)
    try:
        st = rec._stat_sin_seguir(ruta)
    except OSError:
        return None
    enlace = rec._es_enlace_st(st)
    if enlace is None:
        enlace = bool(rec._motivo_enlace(ruta, ruta))
    if enlace or not stat.S_ISREG(st.st_mode) or st.st_nlink != 1:
        return None
    try:
        f, st_fd = rec._abrir_lectura(ruta)                              # #135: un FIFO no bloquea (OSError)
        with f:
            if rec._motivo_descriptor(st_fd, st)[0]:
                return None
            h = hashlib.sha256()
            for bloque in iter(lambda: f.read(BLOQUE), b""):
                h.update(bloque)
            return h.hexdigest()
    except OSError:
        return None


def _identico(dir_export, datos_manifest, esperados):
    """True si `dir_export` (ya existente) es un export COMPLETO con EXACTAMENTE estos bytes: el sha256
    en streaming de su `manifest.json` es el de `datos_manifest` y el de cada JSONL el de `esperados`.
    Un enlace, uno incompleto o manipulado -> False (no se toca)."""
    if rec._motivo_enlace(dir_export, dir_export):
        return False
    if _sha_fichero(dir_export, MANIFEST) != _sha(datos_manifest):
        return False
    return all(_sha_fichero(dir_export, f) == esperados[f].h.hexdigest() for f in JSONL)


@contextlib.contextmanager
def _bloqueo_exports(exports, espera, pasada1):
    """`exports/.lock` (#124) con la espera del ensamblador (#143): si no llega en `espera` s,
    `BloqueoNoDisponible` (exit 3) con lo que hay que saber para reintentar."""
    bloqueo = rec._Bloqueo(exports, BLOQUEO_EXPORTS, espera)
    try:
        bloqueo.__enter__()
    except rec.BloqueoNoDisponible:
        raise rec.BloqueoNoDisponible(MENSAJE_BLOQUEO.format(espera=espera, pasada=pasada1)) from None
    try:
        yield
    finally:
        bloqueo.__exit__(None, None, None)


def _publicar_export(ctx, store, export_id, base, pasada, espera=ESPERA_BLOQUEO_EXPORTS_S, pasada1=0.0, marca=None):
    """`(ruta, existente, manifest, aviso_marca)`. Bajo `exports/.lock` (#124; espera `espera` s, #143):
    crea `exports/<export_id>[.N]/` con `os.mkdir` y los ficheros con `O_EXCL`; nunca sobrescribe ni
    borra (ver docstring del modulo). Con `marca` (D-f4 F2), al acabar bien («escrito» o «ya existe»)
    y AUN con el bloqueo, escribe `exports/.ultimo.json` con el directorio REAL (M3); `aviso_marca` =
    None o por que no se pudo (el export es valido igual, M8)."""
    exports = os.path.join(store, "exports")
    try:
        os.mkdir(exports)
    except FileExistsError:
        pass
    ctx.comprobar_dir(exports)          # directorio real, `realpath` IGUAL al esperado: un enlace -> rechazo
    with _bloqueo_exports(exports, espera, pasada1):
        destino, existente, manifest = _publicar_en(ctx, store, export_id, base, pasada)
        aviso = None
        if marca is not None:
            aviso = _escribir_marca(ctx, os.path.join(store, "exports"),
                                    dict(marca, directorio=os.path.basename(destino)))
    return destino, existente, manifest, aviso


def _publicar_en(ctx, store, export_id, base, pasada):
    """`(ruta, existente, manifest)` CON `exports/.lock` ya tomado (ver `_publicar_export`)."""
    exports = os.path.join(store, "exports")
    esperados = None
    ctx.comprobar_dir(exports)
    for n in range(1, MAX_EXPORTS_MISMO_ID + 1):
        nombre = export_id if n == 1 else f"{export_id}.{n}"
        destino = os.path.join(exports, nombre)
        try:
            os.mkdir(destino)
        except FileExistsError:
            if esperados is None:                                   # lo que se escribiria, sin escribir
                esperados = {f: _Sumidero() for f in JSONL}
                pasada(esperados)
            manifest = _manifest(base, nombre, esperados)
            if _identico(destino, _bytes_manifest(manifest), esperados):
                return destino, True, manifest
            continue
        try:
            ctx.comprobar_dir(destino)
            abiertos = []
            try:
                for f in JSONL:
                    abiertos.append((f,) + _abrir_export(ctx, os.path.join(destino, f)))
                sumideros = {f: _Sumidero(fh) for f, fh, _st in abiertos}
                pasada(sumideros)
            finally:
                for _f, fh, _st in abiertos:
                    fh.close()
            for f, _fh, st in abiertos:
                _verificar(ctx, os.path.join(destino, f), st)
            manifest = _manifest(base, nombre, sumideros)
            _publicar_manifest(ctx, destino, _bytes_manifest(manifest))
        except Rechazo as e:
            raise type(e)(f"{e.mensaje}; export incompleto en exports/{rec._texto_ruta(nombre)} (sin manifest.json): "
                          "se conserva") from None
        except OSError as e:
            raise OSError(e.errno, f"{e.strerror or e}; export incompleto en exports/{rec._texto_ruta(nombre)} (sin "
                                   "manifest.json): se conserva; vuelve a ensamblar (usara el siguiente sufijo)") from None
        return destino, False, manifest
    raise Rechazo(f"exports/{export_id}…{MAX_EXPORTS_MISMO_ID}: todos ocupados por exports incompletos o distintos; "
                  "revisa exports/ a mano; no se ha escrito nada")


# ------------------------------------------------------------------ CLI

EXIT_ESTADO = {"al_dia": 0, "sin_gold": 0, "desactualizado": 1, "con_omisiones": 1, "sin_export": 1,
               "no_verificable": 2, "parcial": 2}


def _main_estado(args):
    """F4 (#176): `--estado`: `rec.resumen_store` COMPLETO (sin plazo) + `estado_dataset`, con el MISMO
    texto que `/doctor` (`texto_estado`) o `--json`. Solo lectura: no toma `exports/.lock` ni escribe
    nada. Exit 0 `al_dia`/`sin_gold` · 1 `desactualizado`/`con_omisiones`/`sin_export` · 2
    `no_verificable`/`parcial` y cualquier config o E/S que no permita verificarlo."""
    try:
        config, raiz = rec._config_cli(args)
        rec.config_activa(config, raiz)
        store = rec.raiz_store(config, rec._raiz(raiz))
        res = rec.resumen_store(store, raiz, plazo_s=None, id_prefix=config.get("id_prefix"))   # #181/N2
        ds = estado_dataset(store, res)
    except (Rechazo, OSError, ValueError, rec._EntradaIlegible, rec.RedaccionNoDisponible) as e:
        print(f"no verificable: {rec._texto_seguro(getattr(e, 'mensaje', e))}", file=sys.stderr)
        return 2
    texto = texto_estado(res, ds)
    if args.json:
        recuento = {k: v for k, v in res.items() if k not in ("gold", "hasta")}
        print(json.dumps({"store": store, "recuento": recuento, "dataset": ds, "texto": texto}, ensure_ascii=True,
                         sort_keys=True, indent=2))
    else:
        print(texto)
    return EXIT_ESTADO.get(ds["estado"], 2)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Ensamblador de dataset (solo Gold, particion por familia completa). "
                                             "Exit 0 ok, 1 rechazo, 2 uso o E/S, 3 otro ensamblador en curso.")
    ap.add_argument("--benchmark", action="append", metavar="FAMILIA[,FAMILIA…]",
                    help="familia(s) reservadas COMPLETAS para benchmark (obligatorio; repetible)")
    ap.add_argument("--umbral", type=float, default=dd.UMBRAL_DEFECTO, help=f"Jaccard de near-duplicate (default {dd.UMBRAL_DEFECTO})")
    ap.add_argument("--ventana", type=int, default=dd.VENTANA_DEFECTO, help=f"palabras por shingle (default {dd.VENTANA_DEFECTO})")
    ap.add_argument("--boilerplate", type=float, default=dd.BOILERPLATE_DEFECTO,
                    help=f"fraccion de casos por encima de la cual un shingle es texto fijo (default {dd.BOILERPLATE_DEFECTO})")
    ap.add_argument("--presupuesto", type=int, default=dd.PRESUPUESTO_DEFECTO,
                    help=f"shingles muestreados en total para el dedup; por debajo, exacto (default {dd.PRESUPUESTO_DEFECTO})")
    ap.add_argument("--conservar-duplicados", action="store_true",
                    help="conserva todos los near-duplicates de una MISMA particion (el cruce train/benchmark se excluye igual)")
    ap.add_argument("--fecha", help="AAAAMMDD del export_id (default: hoy, UTC)")
    ap.add_argument("--espera-bloqueo", type=float, default=ESPERA_BLOQUEO_EXPORTS_S, metavar="S",
                    help=f"segundos de espera de exports/.lock si otro ensamblador lo tiene (default "
                         f"{ESPERA_BLOQUEO_EXPORTS_S}; despues, exit 3 sin escribir nada)")
    ap.add_argument("--dry-run", action="store_true", help="imprime el manifiesto sin escribir nada")
    ap.add_argument("--estado", action="store_true",
                    help="solo lectura: recuento COMPLETO del store y frescura del dataset (lo mismo que /doctor, sin "
                         "tope de tiempo ni exports/.lock); exit 0 al dia o sin Gold, 1 desactualizado, con omisiones "
                         "o sin export, 2 no verificable")
    ap.add_argument("--json", action="store_true", help="con --estado: la salida en JSON")
    ap.add_argument("--config", help="training.json del proyecto (default: <project-root>/.claude/knowledge-services/training.json)")
    ap.add_argument("--project-root", help="raiz del proyecto (default: deducida de --config o cwd)")
    args = ap.parse_args(argv)
    if args.estado:
        return _main_estado(args)
    try:
        config, raiz = rec._config_cli(args)
        rec.config_activa(config, raiz)
        benchmark = _familias_benchmark(args.benchmark)
        if not benchmark:
            raise Rechazo(MOTIVO_SIN_BENCHMARK)
        r = ensamblar(config, raiz, benchmark, args.umbral, args.ventana, args.boilerplate,
                      args.conservar_duplicados, args.fecha, escribir=not args.dry_run, presupuesto=args.presupuesto,
                      devolver_lineas=False, espera_bloqueo=args.espera_bloqueo)
    except (rec._EntradaIlegible, rec.RedaccionNoDisponible) as e:
        print(f"error: {rec._texto_seguro(e)}", file=sys.stderr)
        return 2
    except ValueError as e:
        print(f"error de uso: {rec._texto_seguro(e)}", file=sys.stderr)
        return 2
    except rec.Transitorio as e:
        print(f"no disponible: {rec._texto_seguro(e.mensaje)}", file=sys.stderr)
        return 3
    except Rechazo as e:
        print(f"rechazado: {rec._texto_seguro(e.mensaje)}", file=sys.stderr)
        for err in e.errores:
            print(f"  {rec._texto_seguro(err['campo'])}: {rec._texto_seguro(err['mensaje'])}", file=sys.stderr)
        return 1
    except OSError as e:
        print(f"error de E/S: {rec._texto_seguro(e)}", file=sys.stderr)
        return 2
    m = r["manifest"]
    for a in r["avisos_store"] + m["avisos"] + ([r["aviso_marca"]] if r.get("aviso_marca") else []):
        print(f"aviso: {rec._texto_seguro(a)}", file=sys.stderr)
    if args.dry_run:
        print(json.dumps(m, ensure_ascii=False, sort_keys=True, indent=2))
        return 0
    rel = "exports/" + rec._texto_ruta(os.path.basename(r["ruta"]))
    excluidos = sum(1 for c in m["casos"] if c["particion"] is None)
    estado = "ya existe (identico: no se ha escrito nada)" if r["existente"] else "escrito"
    print(f"OK {rel} {estado}: train {m['ficheros']['train.jsonl']['lineas']}, "
          f"benchmark {m['ficheros']['benchmark.jsonl']['lineas']}, excluidos {excluidos}, "
          f"grupos de near-duplicates {len(m['grupos_near_duplicates'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
