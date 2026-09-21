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
                     [--dry-run | --check | --rebuild | --outbox-status]
Modos (excluyentes entre sí):
  (ninguno)       DRENA la outbox propia (envelopes pendientes de este backend con backoff ya
                  vencido, ver `_drenar_outbox_propia`) y luego plan() + apply() reales del sync
                  fresco, con staging/dead-letter de outbox.py
  --dry-run       solo calcula plan() y lo imprime; nunca llama a apply() ni drena la outbox
  --check         health() + verify(); no toca la publicación ni la outbox
  --rebuild       rebuild(entries, cfg) sobre TODAS las entradas ya enrutadas para este backend
  --outbox-status imprime `outbox.estado()` de la cola de este backend y sale (no publica nada)
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

Gaps de la revisión de dos lentes corregidos en este fichero (Fase 3, intento 3, fix3, 2026-09-19,
ronda `T-07-fix3`):
  - **#128 (Critical): la outbox se atascaba de forma ACUMULATIVA.** `main()` solo publicaba los
    `ops` FRESCOS de cada corrida; un envelope reencolado tras un fallo de `apply()` (#116) nunca
    se volvía a aplicar, y en corridas futuras se trataba SIEMPRE como "ajeno" (colisión de clave
    con la corrida actual): cortesía indefinida vía `ceder_paso`, sin incrementar `intentos`, sin
    llegar NUNCA a `MAX_INTENTOS` ni a `dead-letter` — un backend caído dejaba `knowledge-sync`
    inservible para siempre, incluso arreglado. `_drenar_outbox_propia()` corrige esto: ANTES de
    escribir el envelope fresco, reclama y REINTENTA aplicar (`adaptador.apply(item["payload"]
    ["ops"], cfg)`, idempotente porque `plan()` ya deduplica por hash) cualquier envelope PROPIO
    (mismo `backend`) con backoff vencido; si vuelve a fallar, `reencolar_o_dead_letter` incrementa
    `intentos` de verdad y cae a dead-letter con causa real al llegar a `MAX_INTENTOS`. Los
    envelopes de OTRO backend/productor (payload sin `backend` o distinto) ni se tocan para aplicar
    ni cuentan para `_MAX_DRENAJE` como "propios": se les cede el paso igual que antes.
  - #120/#139: `ob.ceder_paso()` (nueva primitiva PÚBLICA de `outbox.py`) sustituye
    `_devolver_envelope_ajeno`, que reimplementaba a mano el formato de los sidecars `.intentos`/
    `.claimed_at` — única fuente de verdad del formato: `outbox.py`.
  - #135: `--outbox-status` ya aparece en `Uso:`/`Modos` de este docstring (y en `SKILL.md`), no
    solo en el mensaje de error que lo citaba.
  - #139: la retención de `done/` (`RETENCION_DONE_DIAS`, documentada arriba) sigue aplicándose
    tras cada publicación real; `_drenar_outbox_propia` no añade una purga adicional (purgar en
    cada drenaje, además de tras `apply()`, no aporta nada nuevo — sigue siendo "como mucho una vez
    por corrida real de publicación", nunca por cada envelope drenado individualmente).
"""
import argparse
import importlib.util
import json
import os
import re
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
_MAX_DRENAJE = 50  # gap 128: tope de vueltas drenando la outbox propia antes del sync fresco
_PURGA_DONE_CADA_S = 24 * 3600  # gap 139: `purgar_antiguos(done)` abre y parsea CADA manifiesto de
                                # `done/` en cada corrida (1.500 envelopes -> 3,17 s con 0 borrados
                                # medido); un marcador de última purga evita pagar ese coste en
                                # todas las corridas reales cuando ya se purgó recientemente
_MARCADOR_ULTIMA_PURGA_DONE = ".ultima-purga-done"


def _purgar_done_con_throttle(ob, dir_outbox, dias, cada_s=_PURGA_DONE_CADA_S, ahora=None):
    """gap 139: envuelve `ob.purgar_antiguos(dir_outbox, "done", dias)` con un marcador de
    fichero (`<dir_outbox>/.ultima-purga-done`, con el epoch de la última purga real) para que el
    barrido de TODO `done/` — que abre y parsea el `.manifest.json` de cada envelope, coste
    proporcional al TAMAÑO de `done/` sin importar cuántos haya que borrar — se pague como mucho
    una vez cada `cada_s` segundos, no en cada publicación real. Un marcador ilegible/ausente se
    trata como "purgar ahora" (fail-safe: purgar de más nunca pierde datos dentro de la retención,
    `purgar_antiguos` solo borra lo que ya superó `dias`). Devuelve el resultado de
    `purgar_antiguos` (`int`) o `None` si se saltó por estar dentro de la ventana."""
    ahora = ahora if ahora is not None else time.time()
    marcador = os.path.join(dir_outbox, _MARCADOR_ULTIMA_PURGA_DONE)
    try:
        with open(marcador, encoding="utf-8") as fh:
            ultima = float(fh.read().strip())
    except (OSError, ValueError):
        ultima = 0.0
    if ahora - ultima < cada_s:
        return None
    borrados = ob.purgar_antiguos(dir_outbox, "done", dias=dias)
    try:
        os.makedirs(dir_outbox, exist_ok=True)
        with open(marcador, "w", encoding="utf-8") as fh:
            fh.write(str(ahora))
    except OSError:
        pass
    return borrados


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


# Gap #93 (Minor, fix5): misma ampliacion que `_sanear_detalle` de los adaptadores -C1
# (\x80-\x9f), separadores Unicode ( / ) y controles bidi (‪-‮,
# ⁦-⁩)-: esta causa se imprime por stderr y se persiste en la dead-letter.
_CONTROL_O_ANSI_RE = re.compile(
    r"\x1b\[[0-9;]*[A-Za-z]|[\x00-\x1f\x7f-\x9f  ‪-‮⁦-⁩]")
_TOPE_CAUSA_CHARS = 400


def _sanear_causa(texto):
    """Gap #72 (Important, CWE-117): la causa de un fallo del adaptador puede traer texto CRUDO
    del servidor (secuencias ANSI que borran la pantalla, CRLF que falsifican una linea de log con
    el prefijo real del CLI, miles de caracteres). Se sanea ANTES de imprimirla por stderr y
    ANTES de persistirla como `causa` en la outbox/dead-letter. No es especifico de ningun
    backend: cualquier adaptador puede propagar texto de un tercero."""
    return _CONTROL_O_ANSI_RE.sub(" ", str(texto))[:_TOPE_CAUSA_CHARS]


def _causa(e):
    return _sanear_causa(f"{type(e).__name__}: {e}")


def _error(mensaje, fichero, campo):
    return {"mensaje": mensaje, "fichero": fichero, "campo": campo}


def _drenar_outbox_propia(ob, adaptador, cfg, dir_outbox, backend_id):
    """gap 128 (fix3, Critical): antes de escribir/reclamar el envelope FRESCO de esta corrida,
    drena la cola de envelopes PENDIENTES de este MISMO backend cuyo backoff ya venció —
    `reclamar()` ya se encarga de saltarse los que siguen en `no_antes_de` futuro. Antes de esta
    función, un envelope reencolado tras un fallo de `apply()` (gap 116) NUNCA se volvía a aplicar:
    `main()` solo publicaba los `ops` frescos de la corrida actual, así que un fallo transitorio
    dejaba el envelope reencolado atascándose en la cola para siempre (o, peor, tratado como
    "ajeno" en cada corrida futura vía `ceder_paso` — cortesía sin incrementar intentos, sin
    llegar NUNCA a `MAX_INTENTOS` ni a dead-letter: la deuda declarada en el gap 116/120 que este
    gap 128 supera).

    Reintenta cada envelope propio (`payload.get("backend") == backend_id`) aplicando
    `item["payload"]["ops"]` (NUNCA los `ops` frescos de esta corrida — sería aplicar la sync
    incorrecta): éxito -> `completar()`; fallo -> `reencolar_o_dead_letter(..., backoff=True)`, que
    SÍ incrementa `intentos` y cae a dead-letter con la causa REAL al llegar a `MAX_INTENTOS`
    (a diferencia de `ceder_paso`, reservado para lo ajeno). Un envelope de OTRO backend/productor
    (payload sin `backend` o con uno distinto, incluida una `clave` que no seguimos nosotros) NI SE
    TOCA para aplicar NI CUENTA para el tope de vueltas de este drenaje: se cede el paso con
    `ob.ceder_paso` (gap 120, ya no reimplementado a mano aquí) y se sigue mirando el siguiente.
    Acotado a `_MAX_DRENAJE` vueltas totales (propias+ajenas) para no bloquear la corrida si la
    cola tiene una acumulación patológica; `--outbox-status` sigue disponible para inspeccionarla.
    Devuelve `(drenados, fallidos, cedidos)`."""
    drenados = fallidos = cedidos = 0
    for _ in range(_MAX_DRENAJE):
        item = ob.reclamar(dir_outbox)
        if item is None:
            break
        payload = item.get("payload") or {}
        if not isinstance(payload, dict) or payload.get("backend") != backend_id or "ops" not in payload:
            ob.ceder_paso(item, cortesia_s=_CORTESIA_BACKOFF_S)
            cedidos += 1
            continue
        try:
            resultado = adaptador.apply(payload["ops"], cfg)
        except Exception as e:  # noqa: BLE001 - un fallo del adaptador se registra, no tumba el CLI
            ob.reencolar_o_dead_letter(item, _causa(e), backoff=True)  # gap #72: saneada
            fallidos += 1
            continue
        manifiesto = resultado if isinstance(resultado, dict) else {"resultado": str(resultado)}
        ob.completar(item, manifiesto=manifiesto)
        drenados += 1
    return drenados, fallidos, cedidos


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
    ap.add_argument("--propose-config", action="store_true", dest="propose_config",
                     help="imprime la propuesta de configuración del adaptador del backend "
                          "(función OPCIONAL `proponer_config` del contrato) y sale, sin aplicar "
                          "nada ni tocar la red (gap #36, CA-13)")
    ap.add_argument("--backends-dir", action="append", default=[], dest="backends_dir",
                     help="carpeta extra donde buscar el adaptador `type` (repetible; CA-12)")
    return ap


def main(argv=None):
    args = _construir_parser().parse_args(argv)
    modos = [args.dry_run, args.check, args.rebuild, args.outbox_status, args.propose_config]
    if sum(bool(m) for m in modos) > 1:
        print("knowledge-sync: --dry-run, --check, --rebuild, --outbox-status y --propose-config "
              "son excluyentes entre sí", file=sys.stderr)
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
    tipo = decl.get("type")
    if not tipo:
        print(f"knowledge-sync: backend `{args.backend}` no declara `type` en taxonomy.json", file=sys.stderr)
        return 2
    cfg = dict(decl.get("config") or {})
    cfg["_root"] = os.path.abspath(args.root)  # gap 88: export_dir se resuelve contra esto, nunca CWD

    if args.propose_config:
        # Gap #36 (CA-13): la propuesta de configuracion no tenia ningun llamador -esta es su
        # unica puerta de entrada prevista por el plan (T-02 la aplazo "a T-04/T-05")-.
        #
        # Gap #61 (Minor): este modo no toca red ni manifiestos -solo propone configuracion a
        # partir de la taxonomia local- así que NO depende de que el backend esté habilitado. El
        # chequeo de `enabled: false` corria ANTES de esta rama, y la plantilla por defecto trae
        # el backend con `enabled: false` -así que `--propose-config` era inalcanzable en la
        # configuración de fábrica, justo el caso de uso mas comun (proponer antes de habilitar).
        #
        # Gap #77 (Important, fix4): el NUCLEO no nombra ningun backend concreto (invariante del
        # plan, `improvement-plan.md:17`, y CA-12 de ADR-018). Antes, esta rama cortaba con
        # `if tipo != "<un backend>"` y cargaba un modulo de ESE backend por ruta: un tercer
        # backend con configuracion proponible no podia usar el flag sin editar este fichero.
        # Ahora es una funcion OPCIONAL del contrato de adaptador: `proponer_config(taxonomy,
        # cfg)`; si el adaptador no la define, se dice y se sale.
        try:
            adaptador_propuesta = binit.cargar_adaptador(
                tipo, directorios=[BACKENDS_DIR, *args.backends_dir])
        except binit.AdaptadorNoDisponible as e:
            print(f"knowledge-sync: {e}", file=sys.stderr)
            return 2
        proponer = getattr(adaptador_propuesta, "proponer_config", None)
        if not callable(proponer):
            print(f"knowledge-sync: el backend `{args.backend}` (`type: {tipo}`) no propone "
                  f"configuración (su adaptador no define `proponer_config`)", file=sys.stderr)
            return 2
        try:
            propuesta = proponer(config, cfg)
        except Exception as e:  # noqa: BLE001 - un adaptador que lanza no tumba el CLI (gap 90)
            print(f"knowledge-sync: `proponer_config` del adaptador `{tipo}` falló: {_causa(e)}",
                  file=sys.stderr)
            return 1
        if args.json:
            print(json.dumps({"backend": args.backend, "propose_config": propuesta},
                              ensure_ascii=False, indent=2))
        elif isinstance(propuesta, dict) and propuesta.get("texto"):
            # `texto` es el render legible que devuelve el propio adaptador (el nucleo no conoce
            # las claves concretas de la propuesta).
            print(propuesta["texto"])
        else:
            print(json.dumps(propuesta, ensure_ascii=False, indent=2))
        return 0

    if not decl.get("enabled", False):
        print(f"knowledge-sync: backend `{args.backend}` tiene `enabled: false` en taxonomy.json", file=sys.stderr)
        return 2

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
                  f"{_causa(e)}", file=sys.stderr)  # gap #72
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
            print(f"knowledge-sync: `rebuild` del adaptador `{tipo}` falló: {_causa(e)}",
                  file=sys.stderr)  # gap #72
            return 1
        print(json.dumps({"backend": args.backend, "rebuild": resultado}, ensure_ascii=False, indent=2)
              if args.json else f"rebuild: {resultado}")
        return 0

    try:
        ops = adaptador.plan(entradas, cfg)
    except Exception as e:  # noqa: BLE001 - gap 90
        print(f"knowledge-sync: `plan` del adaptador `{tipo}` falló: {_causa(e)}",
              file=sys.stderr)  # gap #72
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
    # gap 128 (Critical, fix3): ANTES de escribir el envelope fresco, drena lo que ya estuviera
    # pendiente de ESTE backend con backoff vencido (un fallo de `apply()` de una corrida anterior,
    # gap 116) — sin esto, un envelope reencolado no se volvía a aplicar NUNCA, solo se le "cedía
    # el paso" indefinidamente sin llegar a `MAX_INTENTOS`.
    drenados, fallidos_drenaje, _cedidos = _drenar_outbox_propia(ob, adaptador, cfg, dir_outbox, args.backend)
    if drenados or fallidos_drenaje:
        print(f"knowledge-sync: drenaje de la outbox propia — {drenados} completado(s), "
              f"{fallidos_drenaje} reencolado(s)/dead-letter", file=sys.stderr)
    clave = f"sync-{int(time.time() * 1000)}"
    ob.escribir(dir_outbox, clave, {"backend": args.backend, "type": tipo, "ops": ops})
    # gap 91: `reclamar` devuelve el PRIMERO pendiente alfabéticamente, no necesariamente el que
    # acabamos de escribir (puede haber envelopes de OTRO backend/productor todavía en la cola tras
    # el drenaje de arriba, que solo toca los propios). gap 120 (revisión intento 2 fix2): si el
    # reclamado no es el nuestro, se repone en `outbox/` con `ob.ceder_paso` — SIN tocar su
    # `.intentos` (no es un fallo SUYO, es una colisión de orden alfabético con la corrida actual;
    # `reencolar_o_dead_letter` habría quemado su presupuesto de reintentos por algo que nunca
    # falló) — y se reintenta, acotado a `_MAX_INTENTOS_RECLAMO` vueltas.
    item = None
    for _ in range(_MAX_INTENTOS_RECLAMO):
        candidato = ob.reclamar(dir_outbox)
        if candidato is None:
            break
        if candidato.get("clave") == clave:
            item = candidato
            break
        ob.ceder_paso(candidato, cortesia_s=_CORTESIA_BACKOFF_S)
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
        veredicto = ob.reencolar_o_dead_letter(item, _causa(e), backoff=True)  # gap #72
        print(f"knowledge-sync: apply() del adaptador `{tipo}` falló: {_causa(e)}"
              f" (publicación anterior intacta; envelope: {veredicto})", file=sys.stderr)
        return 1
    manifiesto = resultado if isinstance(resultado, dict) else {"resultado": str(resultado)}
    ob.completar(item, manifiesto=manifiesto)
    # gap 125 (segunda mitad): `done/` no crece sin límite — se purga lo ya viejo tras publicar.
    _purgar_done_con_throttle(ob, dir_outbox, RETENCION_DONE_DIAS, cada_s=_PURGA_DONE_CADA_S)
    print(json.dumps({"backend": args.backend, "entradas": len(entradas), "apply": resultado},
                      ensure_ascii=False, indent=2) if args.json else f"apply: {resultado}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
