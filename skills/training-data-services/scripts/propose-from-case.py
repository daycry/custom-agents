#!/usr/bin/env python3
"""
propose-from-case.py — puente OPT-IN de un caso Gold hacia `knowledge-curator` (T-09, CA-05).

PROPONE, nunca aprueba: escribe UN candidato nuevo en `<proyecto>/docs/knowledge/candidates/pending/`
(el buzon del Knowledge Gate, ADR-018; mismo papel que el `documenter` en `docs/agents/ROLES.md`) y
nada mas. La decision (aprobar, pedir cambios, rechazar) y el traslado a `approved/` son del agente
`knowledge-curator` con `curator-gate.py`; que el caso sea Gold no aprueba nada por si solo.

  - Solo con `bridge_to_curator: true` en `training.json` (si no, exit 1 con el motivo).
  - Solo desde un caso GOLD, leido del DISCO con el mismo lector que el ensamblador
    (`dataset-assembler.leer_caso` + `es_gold`: `validation.json` por descriptor, nunca el indice) y
    ATADO a su contenido (#132: `validation.content_hash` debe casar con lo leido; sin el, se propone
    con aviso «sin hash de aprobacion»).
  - Candidato con el frontmatter que exige `curator-gate.py` al aprobar: `category` (clave de la
    taxonomia del proyecto, `.claude/knowledge-services/taxonomy.json`, o de la plantilla por
    defecto del plugin; la elige quien llama con `--category`), `evidencia: validated_case`,
    `fuentes: [training-case:<case_id>@v<NNN>]`, `source_cases: [<case_id>@v<NNN>]` y `tags`
    `clave:valor`. Sin `estado` (ese token solo existe en `approved/`). El cuerpo lleva la peticion y
    la nota del revisor en UNA linea cada una (nunca la trayectoria: la conversacion no es
    conocimiento curado). TODO texto que se escribe (peticion, nota, titulo) pasa por
    `redactar_estructura` del recorder en ese momento (#119: el candidato se versiona en Git; un
    secreto que llegara al disco sin redactar no sale); un `--tag` que el redactor cambiaria se rechaza.
    Sin `redact.py` -> exit 2. La taxonomia se lee con `agent-kits/shared/knowledge-schema.py`
    (`cargar_taxonomia`); sin ese fichero (paquete parcial) o con la taxonomia ilegible -> exit 2: no se
    puede validar la categoria (fallo cerrado).
  - `candidates/pending/caso-<slug ASCII>-<10 hex>.md` (#126: el sufijo es el sha256 del
    `case_id@v<NNN>` EXACTO, asi que dos casos que solo difieren en no-ASCII o en mayusculas no
    comparten nombre) lo crea exclusivamente `agent-kits/shared/knowledge-curation.py`, con
    slug acotado a 128 caracteres de nombre total y el nombre historico reservado como alias
    de comparacion cuando difiere (sin cambiar la referencia completa ni nombres ordinarios),
    redaccion del texto completo, cerrojo cooperante, comprobaciones de enlaces y sin sobrescribir.
    Un nombre existente en cualquier estado o approved no se re-propone. Sin servicio compartido
    se informa pendiente (exit 2); nunca se recupera el writer directo como fallback. Las
    verificaciones no son un sandbox frente a renombres hostiles concurrentes durante IO.
  - Anti-leakage: el puente va en UNA direccion (caso -> candidato); nada de `docs/knowledge/`
    alimenta el case store ni el dataset.

Uso (exit 0 candidato creado · 1 rechazo: capacidad apagada, sin `bridge_to_curator`, caso no Gold o
no legible, categoria fuera de la taxonomia, ya propuesto, enlace · 2 uso, taxonomia ilegible o sin
`knowledge-schema.py`, error de E/S; nunca un traceback):
  propose-from-case.py <case_id> <version> --category <KEY> [--title <texto>] [--tag clave:valor ...]
                       [--config <training.json>] [--project-root <dir>]
"""
import argparse
import hashlib
import importlib.util
import os
import re
import sys

# Consola no UTF-8 (Windows cp1252) o tuberias: reconfigurar ANTES de leer/imprimir (GOT-005).
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure, ya leido o None (capsys, pythonw)

HERE = os.path.dirname(os.path.abspath(__file__))


def _cargar(ruta, nombre):
    """Un script por RUTA sin dejar bytecode (#186: `dont_write_bytecode`, restaurado al salir)."""
    previo = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec = importlib.util.spec_from_file_location(nombre, ruta)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        sys.dont_write_bytecode = previo


asm = _cargar(os.path.join(HERE, "dataset-assembler.py"), "tds_dataset_assembler_pfc")
rec = asm.rec
cs = asm.cs
Rechazo = rec.Rechazo
EVIDENCIA = "validated_case"
MAX_TEXTO = 500
_TAG = re.compile(r"[^:\s,\[\]]+:[^\s,\[\]]+")


class KnowledgeServicesNoDisponible(Exception):
    """Dependencia compartida ausente o persistencia no verificable (exit 2)."""


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


def _servicio_curacion():
    """Carga el unico writer compartido; una instalacion parcial no habilita otro writer."""
    for directorio in _dirs_shared():
        ruta = os.path.join(directorio, "knowledge-curation.py")
        if os.path.isfile(ruta):
            try:
                servicio = _cargar(ruta, "tds_knowledge_curation")
            except (ImportError, OSError, SyntaxError, ValueError):
                raise KnowledgeServicesNoDisponible(
                    "knowledge-curation.py no disponible: reinstala el bundle completo; propuesta pendiente") from None
            if callable(getattr(servicio, "propose", None)):
                return servicio
            break
    raise KnowledgeServicesNoDisponible(
        "no se encuentra knowledge-curation.py con API propose: reinstala el bundle completo; propuesta pendiente")


def _motivo_servicio(resultado):
    if resultado.get("status") == "name_already_reserved":
        return "ese nombre ya se propuso en candidates o approved; nunca se sobrescribe ni se re-propone un candidato"
    mensajes = []
    for item in (resultado.get("errores") or []) + (resultado.get("avisos") or []):
        mensaje = item.get("mensaje", "") if isinstance(item, dict) else str(item)
        if mensaje:
            mensajes.append(_una_linea(rec.redactar_estructura(mensaje)))
    return "; ".join(mensajes) or "el servicio de curacion no confirma la propuesta; pendiente"


def _una_linea(texto):
    """Texto libre en UNA linea imprimible (sin saltos ni controles), acotado a `MAX_TEXTO`."""
    plano = texto if isinstance(texto, str) else asm.dd._plano(texto)
    plano = " ".join("".join(c if c.isprintable() else " " for c in plano).split())
    return plano if len(plano) <= MAX_TEXTO else plano[:MAX_TEXTO] + " [recortado]"


def _valor_tag(v):
    return re.sub(r"[\s,\[\]:]+", "-", str(v)) or "-"


def _nombre_historico(ref):
    """Nombre anterior sin truncar, usado solo para reservar propuestas historicas."""
    sufijo = hashlib.sha256(ref.encode("utf-8")).hexdigest()[:10]
    return "caso-" + re.sub(r"[^A-Za-z0-9._-]", "-", ref.replace("@", "-")) + f"-{sufijo}.md"


def _nombre_candidato(ref):
    """Slug ASCII portable <=128; el sufijo conserva la identidad de la referencia completa."""
    historico = _nombre_historico(ref)
    if len(historico) <= 128:
        return historico
    sufijo = historico[-14:]  # '-' + 10 hex + '.md'; no deriva del slug truncado
    return historico[:128 - len(sufijo)] + sufijo


def _texto_candidato(ref, caso, categoria, titulo, tags):
    val = caso["validation"]
    redactar = rec.redactar_estructura                                  # #119: al escribir, siempre
    titulo = redactar(titulo) if titulo else titulo
    etiquetas = [f"origen:training-case", f"familia:{_valor_tag(caso['family'])}",
                 f"outcome:{_valor_tag(caso['outcome'])}"] + list(tags)
    lineas = ["---", f"category: {categoria}", f"evidencia: {EVIDENCIA}", f"fuentes: [training-case:{ref}]",
              f"source_cases: [{ref}]", f"tags: [{', '.join(etiquetas)}]", "source: training-data-services", "---",
              f"# {_una_linea(titulo) if titulo else 'Caso Gold ' + ref}", "",
              "Propuesta generada desde un caso Gold del case store (training-data-services). La categoria "
              "definitiva, el texto y la decision son del `knowledge-curator`; venir de un caso Gold no aprueba nada.",
              "", f"- Peticion: {_una_linea(redactar(caso['request']))}",
              f"- Resultado: `{caso['outcome']}`" + (f" (corrige `{caso['supersedes_case']}`)" if caso.get("supersedes_case") else "")]
    if val.get("reviewer_note"):
        lineas.append(f"- Nota del revisor: {_una_linea(redactar(val['reviewer_note']))}")
    lineas.append(f"- Caso: `{ref}` (Gold, aprobado por un humano)")
    return ("\n".join(lineas) + "\n").encode("utf-8")


def proponer(config, raiz_proyecto, case_id, version, categoria, titulo=None, tags=()):
    """Crea el candidato. Devuelve `{ruta, sha256, ref, categoria, avisos}` del servicio."""
    raiz = rec._raiz(raiz_proyecto)
    rec.config_activa(config, raiz)                                     # #125: `enabled: true` obligatorio
    if config.get("bridge_to_curator") is not True:
        raise Rechazo("el puente a knowledge-curator esta apagado (`bridge_to_curator: true` en training.json lo "
                      "activa); no se propone nada")
    rec._redact_mod()                                                    # #119: fail closed, antes de nada
    for t in tags:
        if rec.redactar_estructura(t) != t:
            raise Rechazo(f"tag {rec._texto_ruta(t)}: el redactor lo cambiaria (parece un secreto); no se propone nada")
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
    avisos = []
    estado = asm.atado(caso["validation"], _hashes["content_hash"])
    if estado == "distinto":
        raise Rechazo(f"{rec._texto_ruta(ref)}: {asm.MOTIVO_SIN_ATAR.replace('no se exporta', 'no se propone')}")
    if estado == "sin":
        avisos.append(asm.AVISO_SIN_HASH.format(ref=rec._texto_ruta(ref)).replace("se exporta", "se propone"))
    nombre = _nombre_candidato(ref)
    historico = _nombre_historico(ref)
    servicio = _servicio_curacion()
    resultado, codigo = servicio.propose(raiz, nombre,
        _texto_candidato(ref, caso, categoria, titulo, tags).decode("utf-8"), producer="training-data-services",
        reserved_aliases=(historico,) if historico != nombre else ())
    if codigo == 1:
        raise Rechazo(_motivo_servicio(resultado))
    if codigo != 0:
        raise KnowledgeServicesNoDisponible(_motivo_servicio(resultado))
    relativa = "docs/knowledge/candidates/pending/" + nombre
    if resultado.get("ruta") != relativa:
        raise KnowledgeServicesNoDisponible("knowledge-curation.py no confirma la ruta pending esperada; pendiente")
    sha256 = resultado.get("sha256")
    if not isinstance(sha256, str) or not re.fullmatch(r"[a-fA-F0-9]{64}", sha256):
        raise KnowledgeServicesNoDisponible("knowledge-curation.py no confirma el SHA256 del candidato; pendiente")
    for aviso in resultado.get("avisos") or []:
        texto = aviso.get("mensaje", "") if isinstance(aviso, dict) else str(aviso)
        if texto:
            avisos.append(_una_linea(rec.redactar_estructura(texto)))
    ruta = os.path.join(raiz, *relativa.split("/"))
    return {"ruta": ruta, "sha256": sha256, "ref": ref, "categoria": categoria, "avisos": avisos}


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
    except (rec._EntradaIlegible, KnowledgeServicesNoDisponible, rec.RedaccionNoDisponible) as e:
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
    for a in r["avisos"]:
        print(f"aviso: {rec._texto_seguro(a)}", file=sys.stderr)
    rel = os.path.relpath(r["ruta"], raiz).replace(os.sep, "/")
    print(f"OK candidato {rec._texto_ruta(rel)} ({r['categoria']}, desde {r['ref']}): pendiente de knowledge-curator "
          f"(curator-gate.py); SHA256 {r['sha256']}; no se ha aprobado nada")
    return 0


if __name__ == "__main__":
    sys.exit(main())
