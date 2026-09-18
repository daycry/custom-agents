#!/usr/bin/env python3
"""
curator-gate.py — puerta determinista de aprobacion del agente `knowledge-curator`
(`knowledge-services` T-04). Sin dependencias externas.

Entrada: la ruta de un candidato bajo `docs/knowledge/candidates/{pending,needs_changes,rejected}/`
mas la decision que el Curator quiere tomar. Salida: veredicto + lista de errores
`{mensaje, fichero, campo}` (mismo contrato que `knowledge-schema.validar`/`knowledge-index.build_index`).
El Curator (el agente, con juicio) decide QUE categoria y QUE decision toma; este script solo
comprueba que esa decision cumple el contrato — nunca decide por si mismo.

Delegado desde la revision de dos lentes de T-01/T-02 (gaps 3 y 34):
  - gap 3: `knowledge-index.py` solo valida la FORMA de `estado`/`fuentes`/`tags`/`evidencia`
    cuando estan presentes, nunca su presencia, y no puede comparar `evidencia` contra el
    `min_evidence` de la categoria EXACTA (una carpeta puede servir a varias categorias). Este
    gate lo hace aqui, en el momento de aprobar, con la categoria que el Curator ya decidio.
  - gap 34: el unico token valido para `estado` de una entrada `approved/` es `aprobado` (nunca
    `approved`/`pending`/`needs_changes`/`rejected`, que son nombres de CARPETA del flujo de
    candidatos). `validar_aprobacion()` lo exige literal.

Contrato de un candidato (frontmatter, `docs/knowledge/candidates/**/*.md`):
  category (str, obligatorio para `approve`; clave de `taxonomy.json` -> `categories[].key`)
  evidencia (str, obligatorio para `approve`; debe estar en `evidence_levels` y alcanzar el
             `min_evidence` de la categoria, segun el orden de `evidence_levels`)
  fuentes (lista no vacia, obligatoria para `approve`)
  tags (lista de `clave:valor`, obligatoria para `approve`)
  estado (opcional; informativo en candidatos — el token reservado `aprobado` solo tiene sentido
          bajo `approved/`, gap 34; aqui NO se exige)

Uso:
  curator-gate.py <candidato.md> --decision approve|reject|needs_changes
                  [--category KEY] [--root .] [--json]
Exit codes: 0 decision permitida (sin errores bloqueantes) · 1 con errores (se listan) ·
            2 uso/taxonomia invalida/fichero no encontrado.
"""
import argparse
import importlib.util
import json
import os
import re
import sys

# Consola no UTF-8 (Windows cp1252) o tuberias: reconfigurar ANTES de leer/imprimir (GOT-005).
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure, ya leido o None (capsys, pythonw)

HERE = os.path.dirname(os.path.abspath(__file__))
SHARED = os.path.normpath(os.path.join(HERE, "..", "shared"))

DECISIONES_VALIDAS = ("approve", "reject", "needs_changes")
ESTADO_APROBADO = "aprobado"
_TAG_CLAVE_VALOR_RE = re.compile(r"^[^:]+:.+$")


class KitCompartidoNoDisponible(Exception):
    """`knowledge-schema.py`/`knowledge-index.py` no viajan junto a `agent-kits/shared/`
    (instalacion parcial): degradacion explicita en vez de traceback (mismo criterio que
    `knowledge-index.KnowledgeSchemaNoDisponible`)."""


def _cargar(nombre_fichero, nombre_modulo):
    ruta = os.path.join(SHARED, nombre_fichero)
    if not os.path.isfile(ruta):
        raise KitCompartidoNoDisponible(f"no se encontro `{ruta}` (deberia viajar en agent-kits/shared/)")
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


def cargar_candidato(ruta):
    """(frontmatter, texto, error_o_None). Reutiliza el parser de `knowledge-index.py` (mismo
    formato de frontmatter que las entradas aprobadas: escalares + listas inline/bloque)."""
    ki = _cargar("knowledge-index.py", "knowledge_index")
    if not os.path.isfile(ruta):
        return {}, "", _error(f"no existe el candidato `{ruta}`", ruta, "$")
    try:
        with open(ruta, "r", encoding="utf-8-sig") as f:
            texto = f.read()
    except OSError as e:
        return {}, "", _error(f"no se pudo leer: {e}", ruta, "$")
    except UnicodeDecodeError as e:
        return {}, "", _error(f"no se pudo leer con codificacion utf-8: {e}", ruta, "encoding")
    return ki._frontmatter(texto), texto, None  # noqa: SLF001 — reuso deliberado, ver docstring


def _categoria_por_clave(config, clave):
    for cat in config.get("categories") or []:
        if cat.get("key") == clave:
            return cat
    return None


def _rango_evidencia(config, nivel):
    niveles = config.get("evidence_levels") or []
    try:
        return niveles.index(nivel)
    except ValueError:
        return None


def detectar_denylist(texto, denylist):
    """Errores por cada termino de la lista negra que aparece literal (sin distinguir
    mayusculas/minusculas) en el candidato — spec «Lista negra de memoria activa»: chain-of-
    thought, conversacion cruda, TODOs, planes/progreso, logs completos, salidas enormes, codigo
    duplicado, errores triviales, intentos sin aprendizaje, hipotesis como hechos, opiniones,
    redundancias. Un candidato que cite uno de estos terminos NO se aprueba sin que el Curator lo
    revise a mano (nunca memoria activa, spec `Alcance`)."""
    errores = []
    texto_low = texto.lower()
    for termino in denylist or []:
        if termino and termino.lower() in texto_low:
            errores.append(_error(
                f"contiene un termino de la lista negra (`{termino}`): revision humana antes de aprobar",
                "$", "denylist"))
    return errores


def validar_categoria(config, clave, fichero):
    """(categoria_o_None, errores). `clave` vacia o no declarada en `taxonomy.json` es siempre
    un error de uso, decision aparte."""
    if not clave:
        return None, [_error("falta `category` (frontmatter o --category)", fichero, "category")]
    cat = _categoria_por_clave(config, clave)
    if cat is None:
        return None, [_error(f"categoria `{clave}` no declarada en `taxonomy.json`", fichero, "category")]
    return cat, []


def validar_aprobacion(fm, texto, categoria, config, fichero):
    """Errores que bloquean `approve` (gaps 3 y 34): evidencia obligatoria y suficiente para la
    categoria EXACTA, fuentes y tags obligatorios, lista negra, y el token de `estado` reservado
    para cuando la entrada ya viva bajo `approved/`."""
    errores = []

    evidencia = fm.get("evidencia")
    if not evidencia:
        errores.append(_error("falta `evidencia` (obligatoria al aprobar)", fichero, "evidencia"))
    else:
        rango_evidencia = _rango_evidencia(config, evidencia)
        if rango_evidencia is None:
            errores.append(_error(
                f"`evidencia` `{evidencia}` no esta en `evidence_levels` de `taxonomy.json`",
                fichero, "evidencia"))
        else:
            min_evidence = categoria.get("min_evidence")
            rango_minimo = _rango_evidencia(config, min_evidence)
            if rango_minimo is not None and rango_evidencia < rango_minimo:
                errores.append(_error(
                    f"`evidencia` `{evidencia}` no alcanza `min_evidence` (`{min_evidence}`) "
                    f"de la categoria `{categoria.get('key')}`",
                    fichero, "evidencia"))

    fuentes = fm.get("fuentes")
    if not isinstance(fuentes, list) or not fuentes:
        errores.append(_error("falta `fuentes` (lista no vacia, obligatoria al aprobar)", fichero, "fuentes"))

    tags = fm.get("tags")
    if not isinstance(tags, list) or not tags:
        errores.append(_error("falta `tags` (lista no vacia, obligatoria al aprobar)", fichero, "tags"))
    else:
        for tag in tags:
            if not isinstance(tag, str) or not _TAG_CLAVE_VALOR_RE.match(tag):
                errores.append(_error(f"tag `{tag}` no tiene forma `clave:valor`", fichero, "tags"))

    if "estado" in fm and fm["estado"] and fm["estado"] != ESTADO_APROBADO:
        # gap 34: nunca `approved`/`pending`/`needs_changes`/`rejected` como valor de `estado`.
        errores.append(_error(
            f"`estado` declarado (`{fm['estado']}`) no es `{ESTADO_APROBADO}`: al aprobar, el "
            f"Curator escribe el token `{ESTADO_APROBADO}` (nunca el nombre de una carpeta)",
            fichero, "estado"))

    errores.extend(detectar_denylist(texto, config.get("denylist")))
    return errores


def evaluar(ruta_candidato, decision, category_override=None, root=None):
    """(veredicto_dict, exit_code). `veredicto_dict` = {decision, categoria, errores}."""
    if decision not in DECISIONES_VALIDAS:
        return {"decision": decision, "categoria": None,
                "errores": [_error(f"decision `{decision}` invalida ({', '.join(DECISIONES_VALIDAS)})",
                                    ruta_candidato, "decision")]}, 2

    try:
        ks = _cargar("knowledge-schema.py", "knowledge_schema")
    except KitCompartidoNoDisponible as e:
        return {"decision": decision, "categoria": None, "errores": [_error(str(e), ruta_candidato, "$")]}, 2

    config, _origen, _ruta_taxonomia, errores_taxonomia = ks.cargar_taxonomia(root)
    if errores_taxonomia:
        return {"decision": decision, "categoria": None, "errores": errores_taxonomia}, 2

    fm, texto, error_lectura = cargar_candidato(ruta_candidato)
    if error_lectura:
        return {"decision": decision, "categoria": None, "errores": [error_lectura]}, 2

    clave_categoria = category_override or fm.get("category") or fm.get("categoria")
    categoria, errores_categoria = validar_categoria(config, clave_categoria, ruta_candidato)
    if errores_categoria:
        return {"decision": decision, "categoria": clave_categoria, "errores": errores_categoria}, 2

    if decision != "approve":
        # Rechazar o pedir cambios no exige evidencia/fuentes/tags: el Curator puede descartar
        # un candidato incompleto sin que el gate se lo impida.
        return {"decision": decision, "categoria": categoria["key"], "errores": []}, 0

    errores = validar_aprobacion(fm, texto, categoria, config, ruta_candidato)
    veredicto = {"decision": decision, "categoria": categoria["key"], "errores": errores}
    return veredicto, (1 if errores else 0)


def _construir_parser():
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("candidato", help="ruta al fichero .md del candidato")
    ap.add_argument("--decision", required=True, choices=DECISIONES_VALIDAS)
    ap.add_argument("--category", help="clave de taxonomy.json; si falta, se lee del frontmatter (`category`/`categoria`)")
    ap.add_argument("--root", default=".", help="raiz del proyecto (default: cwd)")
    ap.add_argument("--json", action="store_true", help="salida en JSON")
    return ap


def main(argv=None):
    args = _construir_parser().parse_args(argv)
    veredicto, exit_code = evaluar(args.candidato, args.decision, args.category, args.root)

    if args.json:
        print(json.dumps(veredicto, ensure_ascii=False))
        return exit_code

    if exit_code == 0:
        print(f"curator-gate: `{args.decision}` permitido (categoria `{veredicto['categoria']}`)")
    else:
        for e in veredicto["errores"]:
            print(f"{e['fichero']}: {e['campo']}: {e['mensaje']}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
