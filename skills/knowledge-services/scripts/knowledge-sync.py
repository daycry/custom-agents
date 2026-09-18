#!/usr/bin/env python3
"""
knowledge-sync.py — punto de entrada ÚNICO para publicar `docs/knowledge/approved/` a un backend
declarado en `.claude/knowledge-services/taxonomy.json` (ADR-018, `knowledge-services` T-07). Este
fichero NUNCA menciona un backend concreto: carga el adaptador por `type` (contrato de 6 funciones
en `backends/__init__.py` / `backends/README.md`) y aplica `routing` ANTES de llamar a `plan`
(CA-09/CA-11) — una categoría con `routing.<id>: false`, o sin `routing` declarado, NUNCA llega al
adaptador; `"summary"` marca la entrada en modo `resumen` (el adaptador decide qué es un resumen).

Sin dependencias externas; solo stdlib. Reutiliza `agent-kits/shared/knowledge-schema.py`
(taxonomía), `agent-kits/shared/knowledge-index.py` (índice de `approved/`) y
`agent-kits/shared/outbox.py` (staging/dead-letter, CA-15 — nunca reimplementado aquí).

Uso:
  knowledge-sync.py --backend <id> [--root .] [--json] [--backends-dir DIR ...]
                     [--dry-run | --check | --rebuild]
Modos (excluyentes entre sí):
  (ninguno)   plan() + apply() reales: publica, con staging/dead-letter de outbox.py
  --dry-run   solo calcula plan() y lo imprime; nunca llama a apply()
  --check     health() + verify(); no toca la publicación
  --rebuild   rebuild(entries, cfg) sobre TODAS las entradas ya enrutadas para este backend
Exit codes: 0 ok · 1 con errores de índice/taxonomía/salud/desfase/apply · 2 uso/adaptador inválido.

Gaps de la revisión de dos lentes corregidos en este fichero (Fase 3, intento 2, fix2, 2026-09-18):
  - #116: un `apply()` que lanza excepción ya NO manda el envelope directo a `dead_letter` (que
    quema su presupuesto de reintentos de un solo fallo, posiblemente transitorio: red intermitente
    al bridge de Kwipu). Ahora usa `reencolar_o_dead_letter(item, causa, backoff=True)`: reintenta
    con backoff creciente hasta `MAX_INTENTOS` de `outbox.py`, y solo entonces cae a dead-letter —
    mismo criterio que ya se usaba para el envelope "ajeno" bloqueando la cola.
  - #120: un envelope AJENO (no el de esta corrida) que bloquea `reclamar()` ya NO se manda a
    `reencolar_o_dead_letter` sin más — eso quema SU presupuesto de reintentos por una colisión que
    no es culpa suya (tres corridas separadas podían mandarlo a dead-letter sin que fallara nunca).
    Ahora se mueve de vuelta a `outbox/` con `os.replace` sin tocar sus sidecars `.intentos`/
    `.claimed_at` (su historial de reintentos queda intacto), y el bucle de reclamo está acotado a
    `_MAX_INTENTOS_RECLAMO` vueltas; si tras esas vueltas la corrida sigue sin poder reclamar su
    propio envelope, sale con diagnóstico real apuntando al nuevo flag `--outbox-status` (antes
    citaba un inexistente "`--check` de la outbox").
  - #125 (segunda mitad): tras `completar()`, se purga `done/` con `ob.purgar_antiguos(dir_outbox,
    "done", dias=RETENCION_DONE_DIAS)` — sin esto, `done/` crecía sin límite con un `.manifest.json`
    por corrida para siempre.
"""
import argparse
import importlib.util
import json
import os
import sys
import time

# Consola no UTF-8 (Windows cp1252) o tuberías: reconfigurar ANTES de leer/imprimir (GOT-005).
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure, ya leído o None (capsys, pythonw)

HERE = os.path.dirname(os.path.abspath(__file__))
SHARED = os.path.normpath(os.path.join(HERE, "..", "..", "..", "agent-kits", "shared"))
BACKENDS_DIR = os.path.normpath(os.path.join(HERE, "..", "backends"))

RETENCION_DONE_DIAS = 14  # gap 125 (segunda mitad): retención de `done/` tras publicar
_MAX_INTENTOS_RECLAMO = 10  # gap 120: tope de vueltas intentando reclamar el envelope propio
_CORTESIA_BACKOFF_S = 5  # gap 120: retraso NO punitivo (no toca `.intentos`) para ceder el turno


class KitCompartidoNoDisponible(Exception):
    """Un módulo del que este script depende (`knowledge-schema.py`, `knowledge-index.py`,
    `outbox.py`, `backends/__init__.py`) no viaja o no cargó — degradación explícita en vez de un
    traceback de `importlib` (mismo criterio que `curator-gate.py`)."""


def _cargar_por_ruta(ruta, nombre_modulo):
    if not os.path.isfile(ruta):
        raise KitCompartidoNoDisponible(f"no se encontró `{ruta}` (debería viajar con el plugin)")
    spec = importlib.util.spec_from_file_location(nombre_modulo, ruta)
    if spec is None or spec.loader is None:
        raise KitCompartidoNoDisponible(f"no se pudo preparar la carga de `{ruta}`")
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as e:  # noqa: BLE001 - cualquier fallo de carga degrada, no tumba el CLI
        raise KitCompartidoNoDisponible(f"{type(e).__name__}: {e}") from e
    return mod


def _error(mensaje, fichero, campo):
    return {"mensaje": mensaje, "fichero": fichero, "campo": campo}


def _devolver_envelope_ajeno(item, dir_outbox):
    """gap 120: repone en `outbox/` un envelope AJENO (no el de esta corrida) que `reclamar()`
    devolvió por delante del nuestro — SIN llamar a `reencolar_o_dead_letter`/`dead_letter`: esas
    funciones incrementan el contador `.intentos` incondicionalmente (backoff solo afecta al
    retraso, no al conteo), así que tratarlo como "nuestro fallo" quemaba su presupuesto de
    reintentos por una colisión que no es culpa suya — tres corridas separadas bastaban para
    mandarlo a dead-letter sin que ninguna llamada a `apply()` hubiera fallado nunca.

    Se mueve el envelope de vuelta a `outbox/` tal cual (mismo nombre), preservando el CONTADOR
    `.intentos` (nunca se incrementa), pero con un `no_antes_de` corto (`_CORTESIA_BACKOFF_S`,
    muy por debajo del `BACKOFF_S` punitivo de `outbox.py`) para que ESTE MISMO proceso no lo
    vuelva a reclamar en la siguiente vuelta del bucle (sin esto, un envelope ajeno que gane el
    orden alfabético se reclama y se devuelve indefinidamente sin dejar nunca paso al propio,
    porque `reclamar()` es determinista y ninguna cantidad de tiempo real transcurre entre
    llamadas consecutivas del mismo bucle). Se borra `.claimed_at` (ya no está reclamado). Devuelve
    `True` si se repuso, `False` si la ruta ya no existía (recogida por otro proceso entre medias
    — no es un error)."""
    src = item["path"] if isinstance(item, dict) else str(item)
    if not os.path.isfile(src):
        return False
    dst = os.path.join(dir_outbox, "outbox", os.path.basename(src))
    try:
        os.replace(src, dst)
    except OSError:
        return False
    intentos_previos = 0
    intentos_src = src + ".intentos"
    if os.path.isfile(intentos_src):
        try:
            with open(intentos_src, encoding="utf-8") as fh:
                intentos_previos = int(json.loads(fh.read() or "{}").get("intentos", 0))
        except (OSError, ValueError, TypeError):
            pass
        try:
            os.remove(intentos_src)
        except OSError:
            pass
    try:
        with open(dst + ".intentos", "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"intentos": intentos_previos,
                                  "no_antes_de": time.time() + _CORTESIA_BACKOFF_S}))
    except OSError:
        pass
    try:
        os.remove(src + ".claimed_at")
    except OSError:
        pass
    return True


def _asegurar_gitignore_local(dirpath):
    """`.gitignore` propio dentro de la carpeta de staging: aunque viva bajo `.claude/`, que ya
    está fuera de git en la mayoría de proyectos, esto la protege igual si un proyecto versiona
    `.claude/` a propósito (mismo criterio que `journal._asegurar_gitignore_local`, replicado en
    pequeño porque aquí no hay marcador de cola que mantener)."""
    try:
        os.makedirs(dirpath, exist_ok=True)
        gi = os.path.join(dirpath, ".gitignore")
        if not os.path.isfile(gi):
            with open(gi, "w", encoding="utf-8") as fh:
                fh.write("# knowledge-services: staging de sincronizacion, nunca versionar\n*\n")
    except OSError:
        pass


def _construir_entradas_enrutadas(ki, ks, root, config, backend_id, indice):
    """Entradas de `approved/` YA filtradas por `routing[backend_id]` (fail-closed: sin `routing`
    declarado, o `routing.<backend_id>: false`, la entrada NUNCA se construye aquí, así que el
    adaptador jamás la ve — CA-09/CA-11).

    Gap 104 (fix1): `build_index()` ahora incluye `category`/`evidencia`/`fuentes`/`tags`/`cuerpo`
    directamente en el índice (ya se abrió y parseó el fichero para construirlo) — este helper ya
    NO reabre ni reparsea cada `.md`, solo lee lo que el índice ya trae.

    Devuelve `(entradas, errores, omitidas_por_routing)`: `omitidas_por_routing` es la lista de
    `id` que existen en `approved/` pero no llegaron al adaptador por falta de `routing` (gap 84:
    visibilidad de por qué una entrada "no se publicó", en vez de desaparecer en silencio)."""
    valor_por_categoria = {
        cat.get("key"): valor
        for cat, valor in ks.categorias_por_backend_con_valor(config, backend_id)
    }
    entradas = []
    errores = []
    omitidas_por_routing = []
    for id_ in sorted(indice):
        meta = indice[id_]
        categoria_key = meta.get("category")
        valor = valor_por_categoria.get(categoria_key, False)
        if not valor:
            omitidas_por_routing.append(id_)
            continue  # fail-closed: categoría sin routing para este backend, o routing false
        entradas.append({
            "id": id_,
            "version": meta["version"],
            "folder": meta["folder"],
            "enlaces": meta["enlaces"],
            "category": categoria_key,
            "evidencia": meta.get("evidencia"),
            "fuentes": meta.get("fuentes") or [],
            "tags": meta.get("tags") or [],
            "modo": "resumen" if valor == "summary" else "completo",
            "cuerpo": meta.get("cuerpo") or "",
            # gap 110 (revision de dos lentes, intento 2 fix2): propaga el `resumen:` explicito
            # del frontmatter (ya lo extrae `build_index()`) hasta el adaptador, que lo prefiere
            # sobre el primer parrafo automatico cuando `modo == "resumen"`.
            "resumen": meta.get("resumen"),
            "ruta": meta["ruta"],
        })
    return entradas, errores, omitidas_por_routing


def _construir_parser():
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--backend", required=True, help="id declarado en taxonomy.json -> backends")
    ap.add_argument("--root", default=".", help="raíz del proyecto (default: cwd)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--dry-run", action="store_true", dest="dry_run")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--rebuild", action="store_true")
    ap.add_argument("--outbox-status", action="store_true", dest="outbox_status",
                     help="imprime `outbox.estado()` de la cola de este backend y sale (gap 120)")
    ap.add_argument("--backends-dir", action="append", default=[], dest="backends_dir",
                     help="carpeta extra donde buscar el adaptador `type` (repetible; CA-12)")
    return ap


def main(argv=None):
    args = _construir_parser().parse_args(argv)
    modos = [args.dry_run, args.check, args.rebuild, args.outbox_status]
    if sum(bool(m) for m in modos) > 1:
        print("knowledge-sync: --dry-run, --check, --rebuild y --outbox-status son excluyentes entre sí",
              file=sys.stderr)
        return 2

    try:
        ks = _cargar_por_ruta(os.path.join(SHARED, "knowledge-schema.py"), "ks_knowledge_schema")
        ki = _cargar_por_ruta(os.path.join(SHARED, "knowledge-index.py"), "ks_knowledge_index")
        ob = _cargar_por_ruta(os.path.join(SHARED, "outbox.py"), "ks_outbox")
        binit = _cargar_por_ruta(os.path.join(BACKENDS_DIR, "__init__.py"), "ks_backends_init")
    except KitCompartidoNoDisponible as e:
        print(f"knowledge-sync: {e}", file=sys.stderr)
        return 2

    if args.outbox_status:
        # gap 120: no necesita taxonomía/adaptador — solo el estado de la cola de este backend.
        dir_outbox = os.path.join(args.root, ".claude", "knowledge-services", "_sync-outbox", args.backend)
        estado_cola = ob.estado(dir_outbox)
        print(json.dumps({"backend": args.backend, "outbox": estado_cola}, ensure_ascii=False, indent=2)
              if args.json else f"outbox `{args.backend}`: {estado_cola}")
        return 0

    config, _origen, _ruta_tax, errores_tax = ks.cargar_taxonomia(args.root)
    if errores_tax:
        for e in errores_tax:
            print(f"{e['fichero']}: {e['campo']}: {e['mensaje']}", file=sys.stderr)
        return 2

    backends_declarados = config.get("backends") or {}
    if args.backend not in backends_declarados:
        print(f"knowledge-sync: backend `{args.backend}` no declarado en taxonomy.json -> backends "
              f"(declarados: {sorted(backends_declarados) or 'ninguno'})", file=sys.stderr)
        return 2
    decl = backends_declarados[args.backend] or {}
    if not decl.get("enabled", False):
        print(f"knowledge-sync: backend `{args.backend}` tiene `enabled: false` en taxonomy.json", file=sys.stderr)
        return 2
    tipo = decl.get("type")
    if not tipo:
        print(f"knowledge-sync: backend `{args.backend}` no declara `type` en taxonomy.json", file=sys.stderr)
        return 2
    cfg = dict(decl.get("config") or {})
    cfg["_root"] = os.path.abspath(args.root)  # gap 88: export_dir se resuelve contra esto, nunca CWD

    try:
        adaptador = binit.cargar_adaptador(tipo, directorios=[BACKENDS_DIR, *args.backends_dir])
    except binit.AdaptadorNoDisponible as e:
        print(f"knowledge-sync: {e}", file=sys.stderr)
        return 2

    if args.check:
        try:
            salud = adaptador.health(cfg)
            verificacion = adaptador.verify(cfg)
        except Exception as e:  # noqa: BLE001 - gap 90: un adaptador que lanza no tumba el CLI
            print(f"knowledge-sync: `health`/`verify` del adaptador `{tipo}` falló: "
                  f"{type(e).__name__}: {e}", file=sys.stderr)
            return 1
        salida = {"backend": args.backend, "type": tipo, "health": salud, "verify": verificacion}
        print(json.dumps(salida, ensure_ascii=False, indent=2) if args.json else
              f"health: {salud.get('estado')} ({salud.get('detalle', '')})\n"
              f"verify: {'ok' if verificacion.get('ok') else 'desfase'} {verificacion.get('desfase', [])}")
        return 0 if salud.get("estado") == "sano" and verificacion.get("ok") else 1

    indice, errores_indice = ki.build_index(args.root)
    if errores_indice:
        for e in errores_indice:
            print(f"{e['fichero']}: {e['campo']}: {e['mensaje']}", file=sys.stderr)
        return 1

    entradas, errores_entradas, omitidas_por_routing = _construir_entradas_enrutadas(
        ki, ks, args.root, config, args.backend, indice)
    if errores_entradas:
        for e in errores_entradas:
            print(f"{e['fichero']}: {e['campo']}: {e['mensaje']}", file=sys.stderr)
        return 1
    if omitidas_por_routing:
        print(f"knowledge-sync: {len(omitidas_por_routing)} entrada(s) omitida(s) por routing "
              f"(sin `routing.{args.backend}` o `false`): {omitidas_por_routing}", file=sys.stderr)

    if args.rebuild:
        try:
            resultado = adaptador.rebuild(entradas, cfg)
        except Exception as e:  # noqa: BLE001 - gap 90
            print(f"knowledge-sync: `rebuild` del adaptador `{tipo}` falló: {type(e).__name__}: {e}",
                  file=sys.stderr)
            return 1
        print(json.dumps({"backend": args.backend, "rebuild": resultado}, ensure_ascii=False, indent=2)
              if args.json else f"rebuild: {resultado}")
        return 0

    try:
        ops = adaptador.plan(entradas, cfg)
    except Exception as e:  # noqa: BLE001 - gap 90
        print(f"knowledge-sync: `plan` del adaptador `{tipo}` falló: {type(e).__name__}: {e}",
              file=sys.stderr)
        return 1

    if args.dry_run:
        print(json.dumps({"backend": args.backend, "entradas": len(entradas), "ops": ops},
                          ensure_ascii=False, indent=2) if args.json
              else f"dry-run: {len(entradas)} entrada(s) enrutada(s), {len(ops)} operacion(es):\n"
                   + json.dumps(ops, ensure_ascii=False, indent=2))
        return 0

    # Publicación real: staging (idempotente por clave) + apply. Un error de apply() nunca borra
    # la publicación anterior: se manda a dead-letter y el CLI sale con 1, sin tocar `apply()` de
    # nuevo dentro de esta misma corrida (CA-15).
    dir_outbox = os.path.join(args.root, ".claude", "knowledge-services", "_sync-outbox", args.backend)
    _asegurar_gitignore_local(dir_outbox)
    clave = f"sync-{int(time.time() * 1000)}"
    ob.escribir(dir_outbox, clave, {"backend": args.backend, "type": tipo, "ops": ops})
    # gap 91: `reclamar` devuelve el PRIMERO pendiente alfabéticamente, no necesariamente el que
    # acabamos de escribir (puede haber envelopes de una corrida anterior atascados en `outbox/`).
    # gap 120 (revisión intento 2 fix2): si el reclamado no es el nuestro, se repone en `outbox/`
    # SIN tocar su `.intentos` (`_devolver_envelope_ajeno` — no es un fallo SUYO, es una colisión
    # de orden alfabético con la corrida actual; `reencolar_o_dead_letter` habría quemado su
    # presupuesto de reintentos por algo que nunca falló) y se reintenta, acotado a
    # `_MAX_INTENTOS_RECLAMO` vueltas.
    item = None
    for _ in range(_MAX_INTENTOS_RECLAMO):
        candidato = ob.reclamar(dir_outbox)
        if candidato is None:
            break
        if candidato.get("clave") == clave:
            item = candidato
            break
        _devolver_envelope_ajeno(candidato, dir_outbox)
    if item is None:
        print("knowledge-sync: no se pudo reclamar el envelope propio de esta corrida en la outbox "
              "(otro envelope sigue bloqueando la cola; usa `--outbox-status` para inspeccionarla)",
              file=sys.stderr)
        return 1
    try:
        resultado = adaptador.apply(ops, cfg)
    except Exception as e:  # noqa: BLE001 - un fallo del adaptador se registra, no tumba el CLI
        # gap 116: reintenta con backoff antes de dead-letter (un fallo de `apply()` puede ser
        # transitorio — red intermitente al bridge — y no merece perder el envelope al primer golpe).
        veredicto = ob.reencolar_o_dead_letter(item, f"{type(e).__name__}: {e}", backoff=True)
        print(f"knowledge-sync: apply() del adaptador `{tipo}` falló: {type(e).__name__}: {e}"
              f" (publicación anterior intacta; envelope: {veredicto})", file=sys.stderr)
        return 1
    manifiesto = resultado if isinstance(resultado, dict) else {"resultado": str(resultado)}
    ob.completar(item, manifiesto=manifiesto)
    # gap 125 (segunda mitad): `done/` no crece sin límite — se purga lo ya viejo tras publicar.
    ob.purgar_antiguos(dir_outbox, "done", dias=RETENCION_DONE_DIAS)
    print(json.dumps({"backend": args.backend, "entradas": len(entradas), "apply": resultado},
                      ensure_ascii=False, indent=2) if args.json else f"apply: {resultado}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
