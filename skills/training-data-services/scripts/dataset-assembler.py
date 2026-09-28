#!/usr/bin/env python3
"""
dataset-assembler.py — ensamblador de dataset de `training-data-services` (T-08/T-09, design.md O1).

No entrena, no sirve modelos y no corre benchmarks (CA-08): produce ficheros JSONL y un manifiesto.

Solo Gold (T-09, CA-03):
  - Se recorre `cases/` con el lector del recorder (`_estado_de_cases`: sin seguir enlaces; versiones
    incompletas, en curso, duplicadas, enlazadas o incoherentes se OMITEN con aviso) y, de cada version
    `approved`, se leen SUS OCHO FICHEROS por descriptor (`_leer_de_version` con los bytes tal cual:
    fichero regular, un solo nombre, la misma identidad que su `lstat`), con `vNNN` y `final/`
    comprobados antes y despues de leer (directorio real, no enlace, `realpath` igual al esperado,
    misma identidad) y cada fichero en el mismo dispositivo que su version. Gold es
    `validation.status == "approved"` **y** `validation.approved_by_human is True` en los bytes
    LEIDOS de `validation.json` — nunca el indice `cases_index.jsonl` (una cache) ni el recorrido
    previo. El caso reconstruido pasa `case_schema.validar_caso` con la config; JSON ilegible, con
    `NaN`/`Infinity` o que no casa con su ruta -> omitido con aviso.
  - Limite declarado (sin `openat` portable, como el recorder): un tercero con escritura en el store
    que sustituya `vNNN`/`final/` por un enlace Y lo restaure en los microsegundos entre las dos
    comprobaciones podria colar un fichero ajeno; fuera de esa ventana, cualquier sustitucion se ve.

Particion anti-leakage (T-08):
  - Por FAMILIA COMPLETA (CA-11): toda version de una familia va a train o toda a benchmark. Las
    familias de benchmark se declaran EXPLICITAMENTE (`--benchmark <family>[,…]`, repetible); sin al
    menos una, o con una familia declarada que no tiene ningun caso Gold, el ensamblador se NIEGA a
    exportar (exit 1) y explica por que, sin escribir nada.
  - Near-duplicates (`dedup.py`, CA-06/CA-10) sobre los Gold: un grupo que cruza train/benchmark
    EXCLUYE a sus miembros de train (motivo «cruce de particion») y conserva los de benchmark — nunca
    al reves, ni siquiera con `--conservar-duplicados`. Dentro de una misma particion se conserva UN
    miembro por grupo (el de `(case_id, version)` mayor, por numero: `v010` gana a `v009`; en un par
    fallo -> correccion, la correccion, que lleva `supersedes_case`) y el resto sale con «duplicado
    de …», salvo `--conservar-duplicados`.

Salida (`<root>/exports/<export_id>/`):
  - `train.jsonl` / `benchmark.jsonl`: una linea por caso, `{"messages": [...], "ref", "case_id",
    "version", "family", "variant", "outcome"[, "supersedes_case"]}` (CA-12): los turnos de
    `trajectory.jsonl` con `role`/`content`/`tool_calls`/`name` (sin `ts`); ni metricas ni
    artefactos (nada binario ni inline). Orden `(case_id, version)`, JSON con claves ordenadas: la
    misma entrada da los mismos bytes.
  - `manifest.json` (se publica el ULTIMO: un export sin el esta INCOMPLETO): por caso `ref`,
    `sha256` (de los hashes de sus ocho ficheros, en orden fijo) y `ficheros`, `particion` y
    `motivo` de exclusion (no Gold, omitida, duplicado, cruce); los grupos de near-duplicates, los
    avisos del store, los parametros y el `sha256` de cada JSONL. `export_id = <AAAAMMDD>-<12 hex>`
    del hash del contenido (sin la fecha): determinista.
  - NUNCA se destruye ni se sobrescribe nada: `exports/<export_id>/` se crea con `os.mkdir`; si ya
    existe y es IDENTICO (manifiesto y JSONL con los mismos bytes), no se escribe nada (exit 0, «ya
    existe»); si existe y no lo es (incompleto, manipulado, un enlace), se usa `<export_id>.2`,
    `.3`… Cada fichero se crea con `O_EXCL` y se comprueba despues (`realpath` igual al esperado,
    mismo fichero, un solo nombre); `manifest.json` se publica desde un `.tmp-<token>` propio sin
    sobrescribir (Windows `os.rename`, POSIX `os.link` + retirar el temporal, que es LO UNICO que se
    elimina, solo si sigue siendo el mismo fichero). Un fallo a mitad deja el export sin manifiesto
    (incompleto) y lo dice; no se borra nada. `exports/` que sea un enlace -> rechazo sin escribir.

Uso (exit 0 ok o ya existente · 1 rechazo: capacidad apagada o config invalida, sin benchmark, familia
de benchmark sin Gold, store manipulado · 2 uso o error de E/S; nunca un traceback):
  dataset-assembler.py --benchmark <family>[,<family>…] [--umbral 0.8] [--ventana 3] [--boilerplate 0.5]
                       [--conservar-duplicados] [--fecha AAAAMMDD] [--dry-run]
                       [--config <training.json>] [--project-root <dir>]
"""
import argparse
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
MAX_EXPORTS_MISMO_ID = 99
MOTIVO_SIN_BENCHMARK = ("sin familias de benchmark declaradas (`--benchmark <family>[,…]`) no se exporta: la "
                        "particion de evaluacion se reserva por familia COMPLETA antes de generar train.jsonl "
                        "(anti-leakage, CA-06/CA-11); no se ha escrito nada")


def _familias_benchmark(valores):
    """`--benchmark a,b --benchmark c` -> {"a", "b", "c"} (sin vacios ni espacios)."""
    return {f.strip() for v in (valores or ()) for f in v.split(",") if f.strip()}


def _clave(c):
    return (c["case_id"], c["version"])


def particionar(casos, benchmark, grupos=(), conservar_duplicados=False):
    """Asigna `particion` (`train`/`benchmark`/None) y `motivo` (None o el de la exclusion) a cada caso
    `{ref, case_id, version, family}` (T-08, ver docstring del modulo). Devuelve copias ordenadas por
    `(case_id, version)`. `Rechazo` sin benchmark o con una familia de benchmark sin casos."""
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
            del_lado = [m for m in miembros if m["particion"] == lado]
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


def leer_caso(ctx, store, entrada, config, width):
    """`(caso, hashes, aviso)` de una version de `cases/` leida del DISCO (ver docstring del modulo):
    `caso` con el esquema de `case_schema` y `hashes = {"sha256", "ficheros"}`; o `(None, None, aviso)`."""
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
        leido = []
        obj, _m, aviso = rec._leer_de_version(dir_v, f, rel, leido, decodificar=bytes)
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
    return caso, {"sha256": total, "ficheros": ficheros}, None


def es_gold(validation):
    """CA-03: la UNICA regla de Gold del ensamblador (sobre lo leido de `validation.json`)."""
    return isinstance(validation, dict) and validation.get("status") == "approved" \
        and validation.get("approved_by_human") is True


def cargar(store, config, raiz, ctx):
    """`(gold, otros, avisos)`: los Gold leidos del disco (`{ref, case_id, version, family, variant,
    caso, sha256, ficheros}`), el resto de versiones con su motivo (manifiesto) y los avisos del store."""
    width = cs.patrones_id(config)[2]
    entradas, avisos, en_curso, _mt, _rels = rec._estado_de_cases(store, raiz)
    avisos_store = [avisos[k] for k in sorted(avisos)] + [en_curso[k] for k in sorted(en_curso)]
    gold, otros = [], []
    for clave in sorted(entradas):
        e = entradas[clave]
        base = {"ref": cs.referencia_version(e["case_id"], e["version"], width), "case_id": e["case_id"],
                "version": e["version"], "family": e["family"]}
        if e["status"] != "approved":
            otros.append(dict(base, sha256=None, particion=None, motivo=f"no Gold (validation.status = {e['status']})"))
            continue
        caso, hashes, aviso = leer_caso(ctx, store, e, config, width)
        if aviso:
            motivo = aviso if " omitida: " in aviso else f"omitida: {aviso}"
            otros.append(dict(base, sha256=None, particion=None, motivo=motivo))
        elif not es_gold(caso["validation"]):
            otros.append(dict(base, sha256=None, particion=None, motivo=(
                f"no Gold (validation.status = {caso['validation'].get('status')}, releido del disco)")))
        else:
            gold.append(dict(base, variant=e["variant"], caso=caso, **hashes))
    return gold, otros, avisos_store


def linea_de(g):
    """Una linea chat/SFT (`messages`) con su procedencia (CA-12)."""
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


def ensamblar(config, raiz_proyecto, benchmark, umbral=dd.UMBRAL_DEFECTO, ventana=dd.VENTANA_DEFECTO,
              fraccion_boilerplate=dd.BOILERPLATE_DEFECTO, conservar_duplicados=False, fecha=None, escribir=True):
    """Ensambla el dataset (ver docstring del modulo). Devuelve `{export_id, ruta, existente, manifest,
    lineas}`; con `escribir=False` no toca el disco (`ruta` None). `Rechazo` si la capacidad no esta
    activa, sin benchmark o con el store manipulado; `ValueError` con parametros invalidos."""
    raiz = rec._raiz(raiz_proyecto)
    rec.config_activa(config, raiz)
    benchmark = set(benchmark or ())
    if not benchmark:
        raise Rechazo(MOTIVO_SIN_BENCHMARK)
    fecha = _fecha_valida(fecha or datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d"))
    dd._fraccion(umbral)
    dd._validar((), ventana, fraccion_boilerplate)
    store = rec.raiz_store(config, raiz)
    ctx = rec._Canon(store, raiz)
    gold, otros, avisos = cargar(store, config, raiz, ctx)
    grupos = dd.agrupar([(g["ref"], g["family"], dd.texto_de_caso(g["caso"])) for g in gold],
                        umbral, ventana, fraccion_boilerplate)["grupos"]
    asignados = particionar([{k: g[k] for k in ("ref", "case_id", "version", "family")} for g in gold],
                            benchmark, grupos, conservar_duplicados)
    por_ref = {g["ref"]: g for g in gold}
    lineas = {f: [] for f in JSONL}
    casos = []
    for a in asignados:
        g = por_ref[a["ref"]]
        casos.append(dict(a, sha256=g["sha256"], ficheros=g["ficheros"]))
        if a["particion"]:
            lineas[f"{a['particion']}.jsonl"].append(linea_de(g))
    casos = sorted(casos + otros, key=_clave)
    contenido = {f: b"".join(_bytes_linea(l) for l in lineas[f]) for f in JSONL}
    nucleo = {"version": 1,
              "parametros": {"benchmark": sorted(benchmark), "umbral": umbral, "ventana": ventana,
                             "fraccion_boilerplate": fraccion_boilerplate,
                             "min_familias_boilerplate": dd.MIN_FAMILIAS_BOILERPLATE,
                             "conservar_duplicados": bool(conservar_duplicados)},
              "ficheros": {f: {"sha256": _sha(contenido[f]), "lineas": len(lineas[f])} for f in JSONL},
              "casos": casos, "grupos_near_duplicates": grupos, "avisos": avisos}
    sha = _sha(json.dumps(nucleo, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    export_id = f"{fecha}-{sha[:12]}"
    manifest = dict(nucleo, export_id=export_id, fecha=fecha, sha256_contenido=sha)
    datos_manifest = (json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    salida = {"export_id": export_id, "ruta": None, "existente": False, "manifest": manifest, "lineas": lineas}
    if escribir:
        salida["ruta"], salida["existente"] = _publicar_export(ctx, store, export_id, contenido, datos_manifest)
    return salida


# ------------------------------------------------------------------ escritura del export (sin destruir nada)

def _verificar(ctx, ruta, st_propio):
    """Comprobacion POSTERIOR a crear `ruta`: su `realpath` es EXACTAMENTE el esperado y el nombre sigue
    siendo el fichero creado (un solo nombre, no un enlace). Si no -> `_Manipulado`, sin borrar nada."""
    ok, _r = ctx.igual(ruta)
    if ok:
        try:
            sl = os.lstat(ruta)
            ok = os.path.samestat(sl, st_propio) and not rec._es_enlace_st(sl) and sl.st_nlink == 1
        except OSError:
            ok = False
    if not ok:
        raise rec._Manipulado(f"{ctx.rel(ruta)}: el export cambio durante la escritura (¿enlace plantado? "
                              "CWE-59/367); el ensamblador no borra nada: revisa exports/ a mano")


def _crear(ctx, ruta, datos):
    """Crea `ruta` con `O_CREAT | O_EXCL` (nunca abre un nombre existente) y la comprueba despues."""
    try:
        f = rec._abrir_exclusivo(ruta)
    except FileExistsError:
        raise rec._Manipulado(f"{ctx.rel(ruta)} ya existia en el export recien creado (¿nombre plantado? "
                              "CWE-59/367); no se escribe a traves de el") from None
    with f:
        st = os.fstat(f.fileno())
        f.write(datos)
    _verificar(ctx, ruta, st)


def _publicar_manifest(ctx, destino, datos):
    """`manifest.json` (el que marca el export como COMPLETO) desde un `.tmp-<token>` propio, publicado
    sin sobrescribir (`_enlazar_sin_sobrescribir`) y retirando el temporal por la regla del recorder."""
    final = os.path.join(destino, MANIFEST)
    tmp = os.path.join(destino, rec.PREFIJO_TEMPORAL + secrets.token_hex(8))
    try:
        f = rec._abrir_exclusivo(tmp)
    except FileExistsError:
        raise rec._Manipulado(f"{ctx.rel(tmp)} ya existia (¿nombre plantado?); no se escribe a traves de el") from None
    st, publicado = None, False
    try:
        with f:
            st = os.fstat(f.fileno())
            f.write(datos)
        try:
            rec._enlazar_sin_sobrescribir(tmp, final)
        except FileExistsError:
            raise rec._Manipulado(f"{ctx.rel(final)} ya existia en el export recien creado; no se sobrescribe") from None
        publicado = True
    finally:
        retirado = st is not None and rec._retirar_temporal_propio(tmp, st)
    if publicado and not retirado:
        raise OSError(errno.EIO, f"{ctx.rel(final)} publicado pero su temporal {os.path.basename(tmp)} no se pudo "
                                 "retirar: retira ese temporal a mano (solo ese nombre)")
    _verificar(ctx, final, st)


def _identico(dir_export, contenido, datos_manifest):
    """True si `dir_export` (ya existente) es un export COMPLETO con EXACTAMENTE estos bytes (leidos por
    descriptor, sin seguir enlaces). Un enlace, uno incompleto o manipulado -> False (no se toca)."""
    if rec._motivo_enlace(dir_export, dir_export):
        return False
    rel = rec._texto_ruta(os.path.basename(dir_export))
    for f, datos in ((MANIFEST, datos_manifest),) + tuple(contenido.items()):
        leido, _m, aviso = rec._leer_de_version(dir_export, f, rel, decodificar=bytes)
        if aviso or leido != datos:
            return False
    return True


def _publicar_export(ctx, store, export_id, contenido, datos_manifest):
    """`(ruta, existente)`. Crea `exports/<export_id>[.N]/` con `os.mkdir` y los ficheros con `O_EXCL`;
    nunca sobrescribe ni borra (ver docstring del modulo)."""
    exports = os.path.join(store, "exports")
    try:
        os.mkdir(exports)
    except FileExistsError:
        pass
    ctx.comprobar_dir(exports)          # directorio real, `realpath` IGUAL al esperado: un enlace -> rechazo
    for n in range(1, MAX_EXPORTS_MISMO_ID + 1):
        nombre = export_id if n == 1 else f"{export_id}.{n}"
        destino = os.path.join(exports, nombre)
        try:
            os.mkdir(destino)
        except FileExistsError:
            if _identico(destino, contenido, datos_manifest):
                return destino, True
            continue
        try:
            ctx.comprobar_dir(destino)
            for f in JSONL:
                _crear(ctx, os.path.join(destino, f), contenido[f])
            _publicar_manifest(ctx, destino, datos_manifest)
        except Rechazo as e:
            raise type(e)(f"{e.mensaje}; export incompleto en exports/{nombre} (sin manifest.json): se conserva") from None
        except OSError as e:
            raise OSError(e.errno, f"{e.strerror or e}; export incompleto en exports/{nombre} (sin manifest.json): se "
                                   "conserva; vuelve a ensamblar (usara el siguiente sufijo)") from None
        return destino, False
    raise Rechazo(f"exports/{export_id}…{MAX_EXPORTS_MISMO_ID}: todos ocupados por exports incompletos o distintos; "
                  "revisa exports/ a mano; no se ha escrito nada")


# ------------------------------------------------------------------ CLI

def main(argv=None):
    ap = argparse.ArgumentParser(description="Ensamblador de dataset (solo Gold, particion por familia completa). "
                                             "Exit 0 ok, 1 rechazo, 2 uso o E/S.")
    ap.add_argument("--benchmark", action="append", metavar="FAMILIA[,FAMILIA…]",
                    help="familia(s) reservadas COMPLETAS para benchmark (obligatorio; repetible)")
    ap.add_argument("--umbral", type=float, default=dd.UMBRAL_DEFECTO, help=f"Jaccard de near-duplicate (default {dd.UMBRAL_DEFECTO})")
    ap.add_argument("--ventana", type=int, default=dd.VENTANA_DEFECTO, help=f"palabras por shingle (default {dd.VENTANA_DEFECTO})")
    ap.add_argument("--boilerplate", type=float, default=dd.BOILERPLATE_DEFECTO,
                    help=f"fraccion de casos por encima de la cual un shingle es texto fijo (default {dd.BOILERPLATE_DEFECTO})")
    ap.add_argument("--conservar-duplicados", action="store_true",
                    help="conserva todos los near-duplicates de una MISMA particion (el cruce train/benchmark se excluye igual)")
    ap.add_argument("--fecha", help="AAAAMMDD del export_id (default: hoy, UTC)")
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
                      args.conservar_duplicados, args.fecha, escribir=not args.dry_run)
    except rec._EntradaIlegible as e:
        print(f"error: {rec._texto_seguro(e)}", file=sys.stderr)
        return 2
    except ValueError as e:
        print(f"error de uso: {rec._texto_seguro(e)}", file=sys.stderr)
        return 2
    except Rechazo as e:
        print(f"rechazado: {rec._texto_seguro(e.mensaje)}", file=sys.stderr)
        for err in e.errores:
            print(f"  {rec._texto_seguro(err['campo'])}: {rec._texto_seguro(err['mensaje'])}", file=sys.stderr)
        return 1
    except OSError as e:
        print(f"error de E/S: {rec._texto_seguro(e)}", file=sys.stderr)
        return 2
    m = r["manifest"]
    for a in m["avisos"]:
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
