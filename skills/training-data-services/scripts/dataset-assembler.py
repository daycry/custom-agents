#!/usr/bin/env python3
"""
dataset-assembler.py — ensamblador de dataset de `training-data-services` (T-08/T-09, design.md O1).

Particion anti-leakage (T-08):
  - Por FAMILIA COMPLETA (CA-11): toda version de una familia va a train o toda a benchmark. Las
    familias de benchmark se declaran EXPLICITAMENTE (`--benchmark <family>[,…]`, repetible); sin al
    menos una, o con una familia declarada que no tiene ningun caso Gold, el ensamblador se NIEGA a
    exportar (exit 1) y explica por que, sin escribir nada.
  - Near-duplicates (`dedup.py`, CA-06/CA-10): un grupo que cruza train/benchmark EXCLUYE a sus
    miembros de train (motivo «cruce de particion») y conserva los de benchmark — nunca al reves, ni
    siquiera con `--conservar-duplicados`. Dentro de una misma particion se conserva UN miembro por
    grupo (el de `(case_id, version)` mayor, por numero: `v010` gana a `v009`; en un par fallo ->
    correccion, la correccion, que lleva `supersedes_case`) y el resto sale con «duplicado de …»,
    salvo `--conservar-duplicados`.

Uso (exit 0 ok · 1 rechazo: capacidad apagada o config invalida, sin benchmark, familia de benchmark
sin Gold · 2 uso o error de E/S; nunca un traceback):
  dataset-assembler.py --benchmark <family>[,<family>…] [--config <training.json>] [--project-root <dir>]
"""
import argparse
import importlib.util
import os
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


# ------------------------------------------------------------------ CLI

def main(argv=None):
    ap = argparse.ArgumentParser(description="Ensamblador de dataset (solo Gold, particion por familia completa). "
                                             "Exit 0 ok, 1 rechazo, 2 uso o E/S.")
    ap.add_argument("--benchmark", action="append", metavar="FAMILIA[,FAMILIA…]",
                    help="familia(s) reservadas COMPLETAS para benchmark (obligatorio; repetible)")
    ap.add_argument("--config", help="training.json del proyecto (default: <project-root>/.claude/knowledge-services/training.json)")
    ap.add_argument("--project-root", help="raiz del proyecto (default: deducida de --config o cwd)")
    args = ap.parse_args(argv)
    try:
        config, raiz = rec._config_cli(args)
        rec.config_activa(config, raiz)
        if not _familias_benchmark(args.benchmark):
            raise Rechazo(MOTIVO_SIN_BENCHMARK)
        print("error: el export llega con T-09", file=sys.stderr)
        return 2
    except rec._EntradaIlegible as e:
        print(f"error: {rec._texto_seguro(e)}", file=sys.stderr)
        return 2
    except Rechazo as e:
        print(f"rechazado: {rec._texto_seguro(e.mensaje)}", file=sys.stderr)
        for err in e.errores:
            print(f"  {rec._texto_seguro(err['campo'])}: {rec._texto_seguro(err['mensaje'])}", file=sys.stderr)
        return 1
    except OSError as e:
        print(f"error de E/S: {rec._texto_seguro(e)}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
