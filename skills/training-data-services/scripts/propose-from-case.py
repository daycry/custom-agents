#!/usr/bin/env python3
"""
propose-from-case.py — puente OPT-IN de un caso Gold hacia `knowledge-curator` (T-09, CA-05).

PROPONE, nunca aprueba: escribe UN candidato nuevo en `<proyecto>/docs/knowledge/candidates/pending/`
(el buzon del Knowledge Gate, ADR-018; mismo papel que el `documenter` en `docs/agents/ROLES.md`) y
nada mas. La decision (aprobar, pedir cambios, rechazar) y el traslado a `approved/` son del agente
`knowledge-curator` con `curator-gate.py`; que el caso sea Gold no aprueba nada por si solo.

  - Solo con `bridge_to_curator: true` en `training.json` (si no, exit 1 con el motivo).
  - Solo desde un caso GOLD, leido del DISCO con el mismo lector que el ensamblador
    (`dataset-assembler.leer_caso` + `es_gold`: `validation.json` por descriptor, nunca el indice).
  - Candidato con el frontmatter que exige `curator-gate.py` al aprobar: `category` (clave de la
    taxonomia del proyecto, `.claude/knowledge-services/taxonomy.json`, o de la plantilla por
    defecto del plugin; la elige quien llama con `--category`), `evidencia: validated_case`,
    `fuentes: [training-case:<case_id>@v<NNN>]`, `source_cases: [<case_id>@v<NNN>]` y `tags`
    `clave:valor`. Sin `estado` (ese token solo existe en `approved/`). El cuerpo lleva la peticion y
    la nota del revisor en UNA linea cada una (nunca la trayectoria: la conversacion no es
    conocimiento curado). La taxonomia se lee con `agent-kits/shared/knowledge-schema.py`
    (`cargar_taxonomia`); sin ese fichero (paquete parcial) -> exit 2: no se puede validar la categoria.
  - `candidates/pending/caso-<case_id>-v<NNN>.md` se crea con `O_EXCL` (nunca sobrescribe) y se
    comprueba despues (`realpath` igual al esperado, mismo fichero, un solo nombre). Si ese nombre ya
    existe en `pending/`, `needs_changes/`, `rejected/` o bajo `approved/` -> exit 1 (ya propuesto; un
    rechazado no se re-propone). Cada directorio de `docs/knowledge/candidates/pending` que exista no
    puede ser un enlace (nunca se escribe a traves de uno); los que faltan se crean con `os.mkdir`.
  - Anti-leakage: el puente va en UNA direccion (caso -> candidato); nada de `docs/knowledge/`
    alimenta el case store ni el dataset.

Uso (exit 0 candidato creado · 1 rechazo: capacidad apagada, sin `bridge_to_curator`, caso no Gold o
no legible, categoria fuera de la taxonomia, ya propuesto, enlace · 2 uso, taxonomia ilegible o sin
`knowledge-schema.py`, error de E/S; nunca un traceback):
  propose-from-case.py <case_id> <version> --category <KEY> [--title <texto>] [--tag clave:valor ...]
                       [--config <training.json>] [--project-root <dir>]
"""
import argparse
import importlib.util
import os
import re
import stat
import sys

# Consola no UTF-8 (Windows cp1252) o tuberias: reconfigurar ANTES de leer/imprimir (GOT-005).
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure, ya leido o None (capsys, pythonw)

HERE = os.path.dirname(os.path.abspath(__file__))


def _cargar(ruta, nombre):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


asm = _cargar(os.path.join(HERE, "dataset-assembler.py"), "tds_dataset_assembler_pfc")
rec = asm.rec
cs = asm.cs
Rechazo = rec.Rechazo
EVIDENCIA = "validated_case"
CARPETAS_CANDIDATOS = ("pending", "needs_changes", "rejected")
MAX_TEXTO = 500
_TAG = re.compile(r"[^:\s,\[\]]+:[^\s,\[\]]+")


class KnowledgeServicesNoDisponible(Exception):
    """`agent-kits/shared/knowledge-schema.py` no esta: no se puede validar la categoria (exit 2)."""


def _dirs_shared():
    """Donde buscar `knowledge-schema.py` (mismo criterio que la redaccion del recorder)."""
    dirs = [os.path.normpath(os.path.join(HERE, "..", "..", "..", "agent-kits", "shared"))]
    raiz = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if raiz:
        dirs.append(os.path.join(raiz, "agent-kits", "shared"))
    return dirs


def categorias(raiz):
    """Claves de categoria de la taxonomia del proyecto (o la plantilla por defecto)."""
    for d in _dirs_shared():
        ruta = os.path.join(d, "knowledge-schema.py")
        if os.path.isfile(ruta):
            ks = _cargar(ruta, "tds_knowledge_schema")
            break
    else:
        raise KnowledgeServicesNoDisponible("no se encuentra agent-kits/shared/knowledge-schema.py (knowledge-services): "
                                            "reinstala el plugin completo; no se propone nada")
    config, _origen, ruta_tax, errores = ks.cargar_taxonomia(raiz)
    if errores or not isinstance(config, dict):
        raise KnowledgeServicesNoDisponible(f"taxonomia invalida ({rec._texto_ruta(ruta_tax or 'taxonomy.json')}): "
                                            f"{errores[0]['mensaje'] if errores else 'sin categorias'}")
    return [c.get("key") for c in config.get("categories") or () if isinstance(c, dict)]


def _una_linea(texto):
    """Texto libre en UNA linea imprimible (sin saltos ni controles), acotado a `MAX_TEXTO`."""
    plano = texto if isinstance(texto, str) else asm.dd._plano(texto)
    plano = " ".join("".join(c if c.isprintable() else " " for c in plano).split())
    return plano if len(plano) <= MAX_TEXTO else plano[:MAX_TEXTO] + " [recortado]"


def _valor_tag(v):
    return re.sub(r"[\s,\[\]:]+", "-", str(v)) or "-"


def _nombre_candidato(ref):
    return "caso-" + re.sub(r"[^A-Za-z0-9._-]", "-", ref.replace("@", "-")) + ".md"


def _texto_candidato(ref, caso, categoria, titulo, tags):
    val = caso["validation"]
    etiquetas = [f"origen:training-case", f"familia:{_valor_tag(caso['family'])}",
                 f"outcome:{_valor_tag(caso['outcome'])}"] + list(tags)
    lineas = ["---", f"category: {categoria}", f"evidencia: {EVIDENCIA}", f"fuentes: [training-case:{ref}]",
              f"source_cases: [{ref}]", f"tags: [{', '.join(etiquetas)}]", "source: training-data-services", "---",
              f"# {_una_linea(titulo) if titulo else 'Caso Gold ' + ref}", "",
              "Propuesta generada desde un caso Gold del case store (training-data-services). La categoria "
              "definitiva, el texto y la decision son del `knowledge-curator`; venir de un caso Gold no aprueba nada.",
              "", f"- Peticion: {_una_linea(caso['request'])}",
              f"- Resultado: `{caso['outcome']}`" + (f" (corrige `{caso['supersedes_case']}`)" if caso.get("supersedes_case") else "")]
    if val.get("reviewer_note"):
        lineas.append(f"- Nota del revisor: {_una_linea(val['reviewer_note'])}")
    lineas.append(f"- Caso: `{ref}` (Gold, aprobado por un humano)")
    return ("\n".join(lineas) + "\n").encode("utf-8")


def _preparar_pending(raiz):
    """`<raiz>/docs/knowledge/candidates/pending`, creando con `os.mkdir` lo que falte; ningun componente
    que ya exista puede ser un enlace y el resultado tiene que ser EXACTAMENTE la ruta esperada."""
    actual = raiz
    for parte in ("docs", "knowledge", "candidates", "pending"):
        actual = os.path.join(actual, parte)
        if os.path.lexists(actual):
            st = os.lstat(actual)
            if rec._motivo_enlace(actual, actual) or not stat.S_ISDIR(st.st_mode):
                raise Rechazo(f"{rec._texto_ruta(os.path.relpath(actual, raiz))}: no es un directorio real "
                              "(enlace u otra cosa); el puente no escribe a traves de el")
        else:
            os.mkdir(actual)
    esperado = os.path.normcase(os.path.join(os.path.realpath(raiz), "docs", "knowledge", "candidates", "pending"))
    if os.path.normcase(os.path.realpath(actual)) != esperado:
        raise Rechazo("docs/knowledge/candidates/pending no es la ruta esperada (enlace en la ruta); no se escribe nada")
    return actual, esperado


def _ya_propuesto(raiz, nombre):
    base = os.path.join(raiz, "docs", "knowledge")
    for carpeta in CARPETAS_CANDIDATOS:
        if os.path.lexists(os.path.join(base, "candidates", carpeta, nombre)):
            return f"candidates/{carpeta}/{nombre}"
    for d, _dirs, ficheros in os.walk(os.path.join(base, "approved")):
        if nombre in ficheros:
            return os.path.relpath(os.path.join(d, nombre), base).replace(os.sep, "/")
    return None


def proponer(config, raiz_proyecto, case_id, version, categoria, titulo=None, tags=()):
    """Crea el candidato (ver docstring del modulo). Devuelve `{ruta, ref, categoria}`."""
    raiz = rec._raiz(raiz_proyecto)
    rec.config_activa(config, raiz)
    if config.get("bridge_to_curator") is not True:
        raise Rechazo("el puente a knowledge-curator esta apagado (`bridge_to_curator: true` en training.json lo "
                      "activa); no se propone nada")
    claves = categorias(raiz)
    if categoria not in claves:
        raise Rechazo(f"categoria {rec._texto_ruta(categoria)} fuera de la taxonomia del proyecto "
                      f"({', '.join(map(str, claves))}); no se propone nada")
    version = rec._version_int(version)
    family, variant = rec._family_variant(case_id, config)
    width = cs.patrones_id(config)[2]
    store = rec.raiz_store(config, raiz)
    entrada = {"case_id": case_id, "family": family, "variant": variant, "version": version}
    caso, _hashes, aviso = asm.leer_caso(rec._Canon(store, raiz), store, entrada, config, width)
    ref = cs.referencia_version(case_id, version, width)
    if aviso:
        raise Rechazo(f"{rec._texto_ruta(ref)}: no se puede leer del case store ({aviso}); no se propone nada")
    if not asm.es_gold(caso["validation"]):
        raise Rechazo(f"{rec._texto_ruta(ref)} no es Gold (validation.status = {caso['validation'].get('status')}): solo "
                      "un caso aprobado por un humano se puede proponer; no se propone nada")
    nombre = _nombre_candidato(ref)
    previo = _ya_propuesto(raiz, nombre)
    if previo:
        raise Rechazo(f"{rec._texto_ruta(ref)} ya se propuso ({rec._texto_ruta(previo)}): nunca se sobrescribe ni se "
                      "re-propone un candidato")
    pending, esperado = _preparar_pending(raiz)
    ruta = os.path.join(pending, nombre)
    try:
        f = open(ruta, "xb")
    except FileExistsError:
        raise Rechazo(f"candidates/pending/{rec._texto_ruta(nombre)} ya existe: nunca se sobrescribe") from None
    with f:
        st = os.fstat(f.fileno())
        f.write(_texto_candidato(ref, caso, categoria, titulo, tags))
    try:
        sl = os.lstat(ruta)
        ok = (os.path.normcase(os.path.realpath(ruta)) == os.path.join(esperado, os.path.normcase(nombre))
              and os.path.samestat(sl, st) and sl.st_nlink == 1 and not rec._es_enlace_st(sl))
    except OSError:
        ok = False
    if not ok:
        raise Rechazo(f"candidates/pending/{rec._texto_ruta(nombre)}: el directorio cambio durante la escritura "
                      "(¿enlace plantado? CWE-59/367); no se borra nada: revisa el buzon a mano")
    return {"ruta": ruta, "ref": ref, "categoria": categoria}


def _tag(valor):
    if not _TAG.fullmatch(valor):
        raise argparse.ArgumentTypeError(f"tag {valor!r}: forma `clave:valor`, sin espacios, comas ni corchetes")
    return valor


def main(argv=None):
    ap = argparse.ArgumentParser(description="Propone un caso Gold como candidato para knowledge-curator (nunca "
                                             "aprueba). Exit 0 creado, 1 rechazo, 2 uso o E/S.")
    ap.add_argument("case_id")
    ap.add_argument("version", help="`1` o `v001`")
    ap.add_argument("--category", required=True, help="clave de la taxonomia (categories[].key)")
    ap.add_argument("--title", help="titulo del candidato (una linea; default: «Caso Gold <ref>»)")
    ap.add_argument("--tag", action="append", type=_tag, default=[], help="tag adicional `clave:valor` (repetible)")
    ap.add_argument("--config", help="training.json del proyecto (default: <project-root>/.claude/knowledge-services/training.json)")
    ap.add_argument("--project-root", help="raiz del proyecto (default: deducida de --config o cwd)")
    args = ap.parse_args(argv)
    try:
        config, raiz = rec._config_cli(args)
        r = proponer(config, raiz, args.case_id, args.version, args.category, args.title, args.tag)
    except (rec._EntradaIlegible, KnowledgeServicesNoDisponible) as e:
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
    rel = os.path.relpath(r["ruta"], raiz).replace(os.sep, "/")
    print(f"OK candidato {rec._texto_ruta(rel)} ({r['categoria']}, desde {r['ref']}): pendiente de knowledge-curator "
          "(curator-gate.py); no se ha aprobado nada")
    return 0


if __name__ == "__main__":
    sys.exit(main())
