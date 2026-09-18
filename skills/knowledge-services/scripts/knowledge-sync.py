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
    ap.add_argument("--backends-dir", action="append", default=[], dest="backends_dir",
                     help="carpeta extra donde buscar el adaptador `type` (repetible; CA-12)")
    return ap


def main(argv=None):
    args = _construir_parser().parse_args(argv)
    modos = [args.dry_run, args.check, args.rebuild]
    if sum(bool(m) for m in modos) > 1:
        print("knowledge-sync: --dry-run, --check y --rebuild son excluyentes entre sí", file=sys.stderr)
        return 2

    try:
        ks = _cargar_por_ruta(os.path.join(SHARED, "knowledge-schema.py"), "ks_knowledge_schema")
        ki = _cargar_por_ruta(os.path.join(SHARED, "knowledge-index.py"), "ks_knowledge_index")
        ob = _cargar_por_ruta(os.path.join(SHARED, "outbox.py"), "ks_outbox")
        binit = _cargar_por_ruta(os.path.join(BACKENDS_DIR, "__init__.py"), "ks_backends_init")
    except KitCompartidoNoDisponible as e:
        print(f"knowledge-sync: {e}", file=sys.stderr)
        return 2

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
    # Si el reclamado no es el nuestro, se reencola CON backoff (para que la propia corrida no lo
    # vuelva a reclamar en el siguiente intento y así deje paso al nuestro; sin backoff se
    # reengancharía de inmediato y agotaría sus reintentos en esta misma corrida por algo que no
    # es un fallo suyo) y se reintenta, acotado en intentos.
    item = None
    for _ in range(10):
        candidato = ob.reclamar(dir_outbox)
        if candidato is None:
            break
        if candidato.get("clave") == clave:
            item = candidato
            break
        ob.reencolar_o_dead_letter(candidato, "no es el envelope reclamado por esta corrida")
    if item is None:
        print("knowledge-sync: no se pudo reclamar el envelope propio de esta corrida en la outbox "
              "(otro envelope sigue bloqueando la cola; ver `--check` de la outbox)", file=sys.stderr)
        return 1
    try:
        resultado = adaptador.apply(ops, cfg)
    except Exception as e:  # noqa: BLE001 - un fallo del adaptador se registra, no tumba el CLI
        ob.dead_letter(item, f"{type(e).__name__}: {e}")
        print(f"knowledge-sync: apply() del adaptador `{tipo}` falló: {type(e).__name__}: {e}"
              f" (publicación anterior intacta; envelope en dead-letter)", file=sys.stderr)
        return 1
    manifiesto = resultado if isinstance(resultado, dict) else {"resultado": str(resultado)}
    ob.completar(item, manifiesto=manifiesto)
    print(json.dumps({"backend": args.backend, "entradas": len(entradas), "apply": resultado},
                      ensure_ascii=False, indent=2) if args.json else f"apply: {resultado}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
