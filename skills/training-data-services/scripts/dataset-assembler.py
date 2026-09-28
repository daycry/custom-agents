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

Uso (exit 0 ok o ya existente · 1 rechazo: capacidad apagada o config invalida, sin benchmark, familia
de benchmark sin Gold, store manipulado, caso cambiado entre pasadas · 2 uso, E/S o sin `redact.py` ·
3 otro ensamblador tiene `exports/.lock`: reintenta; nunca un traceback):
  dataset-assembler.py --benchmark <family>[,<family>…] [--umbral 0.8] [--ventana 3] [--boilerplate 0.5]
                       [--presupuesto 10000000] [--conservar-duplicados] [--fecha AAAAMMDD] [--dry-run]
                       [--espera-bloqueo 120] [--config <training.json>] [--project-root <dir>]
"""
import argparse
import contextlib
import datetime
import errno
import hashlib
import importlib.util
import json
import os
import re
import secrets
import stat
import sys
import time

# Consola no UTF-8 (Windows cp1252) o tuberias: reconfigurar ANTES de leer/imprimir (GOT-005).
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure, ya leido o None (capsys, pythonw)

HERE = os.path.dirname(os.path.abspath(__file__))


def _cargar(fichero, nombre):
    """Un script de la MISMA skill (fuente unica del recorder, del esquema y del dedup)."""
    spec = importlib.util.spec_from_file_location(nombre, os.path.join(HERE, fichero))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


rec = _cargar("case-recorder.py", "tds_case_recorder_asm")
cs = rec.cs
dd = _cargar("dedup.py", "tds_dedup_asm")

Rechazo = rec.Rechazo
FICHEROS = ("metadata.json", "request.json", "context.json", "constraints.json", "trajectory.jsonl",
            "metrics.json", "validation.json", "final/artifacts.json")
CLAVES_TURNO = ("role", "content", "tool_calls", "name")
JSONL = ("train.jsonl", "benchmark.jsonl")
MANIFEST = "manifest.json"
BLOQUEO_EXPORTS = ".lock"
MAX_EXPORTS_MISMO_ID = 99
TOPE_FICHERO = 16 * 1024 * 1024
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
        reutilizado = _reutilizable(dir_v, f, (previos or {}).get(f), antes[dir_v], tope)
        if reutilizado is not None:
            datos[f] = reutilizado
            continue
        leido = []
        obj, _m, aviso = rec._leer_de_version(dir_v, f, rel, leido, decodificar=bytes, tope=tope)
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


def cargar(store, config, raiz, ctx, acumulador=None, tope=TOPE_FICHERO):
    """Pasada 1 (H5): `(gold, otros, avisos_store, avisos)`. `gold`: `{ref, case_id, version, family,
    variant, supersedes_case, sha256, ficheros, content_hash}` (sin el caso: su texto va al
    `acumulador` y se descarta); `otros`: el resto de versiones con su motivo (manifiesto);
    `avisos_store`: los del recorrido (dependen del reloj: solo `stderr`); `avisos`: deterministas."""
    width = cs.patrones_id(config)[2]
    crudos = {}
    entradas, av, en_curso, _mt, _rels = rec._estado_de_cases(store, raiz, crudos=crudos, tope=tope)   # #134
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
            otros.append(dict(base, sha256=None, particion=None, motivo=_motivo(aviso, store)))
            continue
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
    gold, otros, avisos_store, avisos = cargar(store, config, raiz, ctx, acc, tope_fichero)
    r_dd = acc.agrupar(umbral, fraccion_boilerplate,
                       benchmark_ids={g["ref"] for g in gold if g["family"] in benchmark})   # #145
    acc = None
    grupos, cruces = r_dd["grupos"], r_dd.get("cruces", [])
    avisos += [f"{a['id']}: {a['motivo']}" for a in r_dd["avisos"]]
    asignados = particionar([{k: g[k] for k in ("ref", "case_id", "version", "family", "supersedes_case")}
                             for g in gold], benchmark, grupos, conservar_duplicados, cruces)
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

    salida = {"export_id": export_id, "ruta": None, "existente": False, "lineas": None, "avisos_store": avisos_store}
    if escribir:
        salida["ruta"], salida["existente"], salida["manifest"] = _publicar_export(ctx, store, export_id, base, pasada,
                                                                                    espera_bloqueo, pasada1)
    else:
        recoger = devolver_lineas is not False
        sumideros = {f: _Sumidero(recoger=recoger) for f in JSONL}
        pasada(sumideros)
        salida["manifest"] = _manifest(base, export_id, sumideros)
        if recoger:
            salida["lineas"] = {f: sumideros[f].lineas for f in JSONL}
    return salida


# ------------------------------------------------------------------ frescura del dataset (T-10, `/doctor`)

def estado_dataset(store, gold_mtime_ns):
    """Frescura del dataset para `/doctor` (T-10, CA-07), SOLO LECTURA y sin red: `{estado, exports,
    incompletos, ultimo, motivo}`. Un export cuenta si es un directorio real de `exports/` (no un
    enlace: no se sigue) con un `manifest.json` que es un fichero regular sin seguir enlaces (un export
    sin el esta INCOMPLETO: se cuenta aparte y no vale como ultimo export). `ultimo` = el de
    `manifest.json` con `mtime` mas reciente. `estado`: `sin_gold` (ningun Gold: nada que exportar),
    `sin_export` (hay Gold y ningun export completo), `desactualizado` (el `validation.json` Gold mas
    reciente, `gold_mtime_ns`, es posterior al `manifest.json` del ultimo export), `al_dia` o
    `no_verificable` (`exports/` es un enlace o no se puede listar). Limite declarado: compara `mtime`
    (un Gold que DEJA de serlo tras exportar no se detecta aqui; `dataset-assembler.py --dry-run` si)."""
    exports = os.path.join(store, "exports")
    salida = {"estado": None, "exports": 0, "incompletos": 0, "ultimo": None, "motivo": ""}
    tipo = rec._tipo_entrada(exports, exports)
    ultimo_ns = None
    if tipo == "enlace" or tipo == "otro":
        salida.update(estado="no_verificable", motivo=("exports/ es un enlace: no se sigue" if tipo == "enlace"
                                                        else "exports/ no es un directorio"))
        return salida
    if tipo == "dir":
        try:
            with os.scandir(exports) as it:
                entradas = [e for e in it if not e.name.startswith(".")]
        except OSError as e:
            salida.update(estado="no_verificable", motivo=f"exports/ no se puede listar ({type(e).__name__})")
            return salida
        for e in sorted(entradas, key=lambda x: x.name):
            if rec._tipo_entrada(e, e.path) != "dir":
                salida["incompletos"] += 1
                continue
            ruta_m = os.path.join(e.path, MANIFEST)
            try:
                st = rec._stat_sin_seguir(ruta_m)
            except OSError:
                st = None
            enlace = None if st is None else rec._es_enlace_st(st)
            if enlace is None and st is not None:
                enlace = bool(rec._motivo_enlace(ruta_m, ruta_m))
            if st is None or enlace or not stat.S_ISREG(st.st_mode):
                salida["incompletos"] += 1
                continue
            salida["exports"] += 1
            if ultimo_ns is None or st.st_mtime_ns > ultimo_ns:
                ultimo_ns, salida["ultimo"] = st.st_mtime_ns, e.name
    if gold_mtime_ns is None:
        salida.update(estado="sin_gold", motivo="ningun caso Gold: nada que exportar")
    elif ultimo_ns is None:
        salida.update(estado="sin_export", motivo="hay Gold y ningun export con manifest.json todavia")
    elif gold_mtime_ns > ultimo_ns:
        salida.update(estado="desactualizado",
                      motivo=f"hay Gold mas nuevo que el ultimo export `{rec._texto_ruta(salida['ultimo'])}`")
    else:
        salida.update(estado="al_dia", motivo=f"ultimo export `{rec._texto_ruta(salida['ultimo'])}`")
    return salida


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


def _publicar_export(ctx, store, export_id, base, pasada, espera=ESPERA_BLOQUEO_EXPORTS_S, pasada1=0.0):
    """`(ruta, existente, manifest)`. Bajo `exports/.lock` (#124; espera `espera` s, #143): crea
    `exports/<export_id>[.N]/` con `os.mkdir` y los ficheros con `O_EXCL`; nunca sobrescribe ni borra
    (ver docstring del modulo)."""
    exports = os.path.join(store, "exports")
    try:
        os.mkdir(exports)
    except FileExistsError:
        pass
    ctx.comprobar_dir(exports)          # directorio real, `realpath` IGUAL al esperado: un enlace -> rechazo
    esperados = None
    with _bloqueo_exports(exports, espera, pasada1):
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
    ap.add_argument("--config", help="training.json del proyecto (default: <project-root>/.claude/knowledge-services/training.json)")
    ap.add_argument("--project-root", help="raiz del proyecto (default: deducida de --config o cwd)")
    args = ap.parse_args(argv)
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
    for a in r["avisos_store"] + m["avisos"]:
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
