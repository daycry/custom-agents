#!/usr/bin/env python3
"""
curator-gate.py — puerta determinista de aprobacion del agente `knowledge-curator`
(`knowledge-services` T-04, corregido en la revision de dos lentes Fase 2 intento 1). Sin
dependencias externas.

Entrada: la ruta de un candidato, que DEBE vivir bajo
`docs/knowledge/candidates/{pending,needs_changes,rejected}/` del `root` (contencion por
realpath, gap 48) — cualquier otra ruta (un fichero ya en `approved/`, el corpus legado, o
cualquier `.md` fuera del arbol de candidatos) es un error de uso (`exit 2`), no un candidato.
Mas la decision que el Curator quiere tomar. Salida: veredicto + lista de errores
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

Reparto de responsabilidad sobre `estado` (gap 43, Fase 2): este gate NO exige `estado` para
`approve` (un candidato puede no traerlo todavia); lo que SI exige, si el campo esta declarado, es
que no sea otra cosa que `aprobado` (gap 34). Es el CURATOR (el agente, P4 de
`agents/knowledge-curator.md`) quien ESCRIBE `estado: aprobado` al mover el fichero a
`approved/<folder>/`. `knowledge-index.py` es quien exige `estado: aprobado` como OBLIGATORIO en
`approved/` (una entrada aprobada sin `estado` es un error del indice) — ver su docstring. Cada
puerta vigila su propio momento del flujo: este gate el instante de aprobar, el indice el estado
final en disco.

Contrato de un candidato (frontmatter, `docs/knowledge/candidates/**/*.md`):
  category (str, obligatorio para `approve`; clave de `taxonomy.json` -> `categories[].key`;
            para `reject`/`needs_changes` es opcional — gap 53, un candidato incompleto tambien
            se puede rechazar)
  evidencia (str, obligatorio para `approve`; debe estar en `evidence_levels` del proyecto o, si
             el proyecto no declara una escalera propia, en la escalera por defecto del plugin —
             gap 47 — y alcanzar el `min_evidence` de la categoria, segun ese orden)
  fuentes (lista no vacia, obligatoria para `approve`)
  tags (lista de `clave:valor`, obligatoria para `approve`)
  estado (opcional; informativo en candidatos — el token reservado `aprobado` solo tiene sentido
          bajo `approved/`, gap 34; aqui NO se exige su presencia, solo su valor si esta)

`reject`/`needs_changes` NO evaluan lista negra ni `estado` (gap 58, salvedad deliberada): solo
`approve` corre `validar_aprobacion()`. El Curator puede rechazar o pedir cambios sobre un
candidato que ni siquiera declara `category` (gap 53).

Uso:
  curator-gate.py <candidato.md> --decision approve|reject|needs_changes
                  [--category KEY] [--root .] [--json]
Exit codes: 0 decision permitida (sin errores bloqueantes; puede traer `avisos` no bloqueantes) ·
            1 con errores (se listan) · 2 uso/taxonomia invalida/candidato invalido o inexistente.
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
CARPETAS_CANDIDATOS = ("pending", "needs_changes", "rejected")


class KitCompartidoNoDisponible(Exception):
    """`knowledge-schema.py`/`knowledge-index.py` no viajan junto a `agent-kits/shared/`
    (instalacion parcial): degradacion explicita en vez de traceback (mismo criterio que
    `knowledge-index.KnowledgeSchemaNoDisponible`). Gap 45: AMBOS modulos se cargan dentro del
    mismo `try/except` en `evaluar()`, nunca uno de ellos fuera de esa red de seguridad."""


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


def _candidato_dentro_del_arbol(root, ruta):
    """True si `ruta` resuelve (realpath) dentro de
    `<root>/docs/knowledge/candidates/{pending,needs_changes,rejected}/` (gap 48). Fail-closed:
    cualquier fallo de resolucion (p. ej. unidades de Windows distintas) es "fuera"."""
    base = os.path.realpath(os.path.join(root or ".", "docs", "knowledge", "candidates"))
    ruta_real = os.path.realpath(ruta)
    try:
        rel = os.path.relpath(ruta_real, base)
    except ValueError:
        return False
    if rel == os.curdir or rel.split(os.sep)[0] == os.pardir:
        return False
    primera = rel.split(os.sep, 1)[0]
    return primera in CARPETAS_CANDIDATOS


def cargar_candidato(ruta, ki):
    """(frontmatter, cuerpo, error_o_None). `ki` es el modulo `knowledge-index.py` YA CARGADO por
    el llamador (gap 45: dentro del mismo `try/except KitCompartidoNoDisponible` que
    `knowledge-schema.py`, nunca aqui dentro sin red de seguridad). `cuerpo` es el texto del
    candidato SIN su bloque de frontmatter (gap 41: la lista negra solo vigila el CONTENIDO, no
    las claves/valores del propio frontmatter — p. ej. un `tags: [todo:limpiar]` no deberia
    disparar el termino `TODO:` de la lista negra)."""
    if not os.path.isfile(ruta):
        return {}, "", _error(f"no existe el candidato `{ruta}`", ruta, "$")
    try:
        with open(ruta, "r", encoding="utf-8-sig") as f:
            texto = f.read()
    except OSError as e:
        return {}, "", _error(f"no se pudo leer: {e}", ruta, "$")
    except UnicodeDecodeError as e:
        return {}, "", _error(f"no se pudo leer con codificacion utf-8: {e}", ruta, "encoding")
    fm = ki._frontmatter(texto)  # noqa: SLF001 — reuso deliberado, ver docstring del modulo
    cuerpo = ki._FRONTMATTER_RE.sub("", texto, count=1)  # noqa: SLF001 — idem
    return fm, cuerpo, None


def _categoria_por_clave(config, clave):
    for cat in config.get("categories") or []:
        if cat.get("key") == clave:
            return cat
    return None


def _lista_evidencia_declarada(config):
    """La escalera `evidence_levels` del proyecto si es una lista de cadenas no vacia; `None` si
    la taxonomia no la declara (o la declara mal — `knowledge-schema.validar` ya lo reporta aparte,
    esta funcion solo dice si HAY una escalera utilizable)."""
    niveles = config.get("evidence_levels")
    if isinstance(niveles, list) and niveles and all(isinstance(x, str) for x in niveles):
        return niveles
    return None


def _rango_evidencia(niveles, nivel):
    if not niveles or nivel is None:
        return None
    try:
        return niveles.index(nivel)
    except ValueError:
        return None


def _regex_termino(termino):
    """Un termino de la lista negra puede tener varias palabras («conversacion cruda»): se casa
    como secuencia con ESPACIOS FLEXIBLES entre palabras (`\\s+`, cubre saltos de linea), y con
    limites que NO son `\\b` literal (gap 41): `\\b` falla en los dos sentidos que este termino
    necesita — no detecta el limite tras un termino que acaba en puntuacion (`TODO:` seguido de un
    espacio: ninguno de los dos lados de esa posicion es un caracter de palabra), y SI detecta como
    "palabra completa" una coincidencia de mayusculas/minusculas que es en realidad OTRA palabra
    (p. ej. `todos`, dentro de "Todos los handlers", es la palabra espanola comun, no el marcador
    `TODOs`). Se usan lookarounds `(?<!\\w)`/`(?!\\w)`: no exigen un cambio de categoria de
    caracter, solo que el caracter contiguo (si existe) NO sea de palabra — funciona igual de bien
    pegado a un espacio, a un signo de puntuacion o al principio/fin de la cadena."""
    partes = [re.escape(p) for p in termino.split() if p]
    if not partes:
        return None
    cuerpo = r"\s+".join(partes)
    return re.compile(r"(?<!\w)" + cuerpo + r"(?!\w)", re.IGNORECASE)


def detectar_denylist(cuerpo, denylist, fichero):
    """Errores por cada termino de la lista negra que aparece, como palabra/frase completa (gap
    41), en el CUERPO del candidato (nunca en su frontmatter) — spec «Lista negra de memoria
    activa»: chain-of-thought, conversacion cruda, TODO:, planes/progreso, logs completos, salidas
    enormes, codigo duplicado, errores triviales, intentos sin aprendizaje, hipotesis como hechos,
    opiniones, redundancias. Un candidato que cite uno de estos terminos NO se aprueba sin que el
    Curator lo revise a mano (nunca memoria activa, spec `Alcance`)."""
    errores = []
    for termino in denylist or []:
        if not termino:
            continue
        patron = _regex_termino(termino)
        if patron is not None and patron.search(cuerpo):
            errores.append(_error(
                f"contiene un termino de la lista negra (`{termino}`): revision humana antes de aprobar",
                fichero, "denylist"))
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


def validar_aprobacion(fm, cuerpo, categoria, config, fichero, niveles_por_defecto, ruta_taxonomia):
    """Errores que bloquean `approve` (gaps 3 y 34): evidencia obligatoria y suficiente para la
    categoria EXACTA, fuentes y tags obligatorios, lista negra, y el token de `estado` reservado
    para cuando la entrada ya viva bajo `approved/`."""
    errores = []

    evidencia = fm.get("evidencia")
    if not evidencia:
        errores.append(_error("falta `evidencia` (obligatoria al aprobar)", fichero, "evidencia"))
    else:
        niveles_declarados = _lista_evidencia_declarada(config)
        niveles = niveles_declarados if niveles_declarados is not None else niveles_por_defecto
        rango_evidencia = _rango_evidencia(niveles, evidencia)
        if rango_evidencia is None:
            if niveles_declarados is not None:
                errores.append(_error(
                    f"`evidencia` `{evidencia}` no esta en `evidence_levels` de `taxonomy.json`",
                    fichero, "evidencia"))
            else:
                # gap 47: sin `evidence_levels` en el proyecto se usa la escalera por defecto del
                # plugin (arriba); si el nivel NI SIQUIERA esta ahi, la taxonomia es la que se
                # queda corta (no declara su propia escalera ni cubre el nivel que hace falta) —
                # el error apunta a `taxonomy.json`, no al candidato.
                errores.append(_error(
                    f"`evidencia` `{evidencia}` no esta en la escalera por defecto del plugin "
                    f"(`evidence_levels` no declarado en `taxonomy.json`): declara una escalera "
                    f"propia que incluya este nivel, o usa uno de la escalera por defecto",
                    ruta_taxonomia or "taxonomy.json", "evidence_levels"))
        else:
            min_evidence = categoria.get("min_evidence")
            rango_minimo = _rango_evidencia(niveles, min_evidence)
            if rango_minimo is not None and rango_evidencia < rango_minimo:
                errores.append(_error(
                    f"`evidencia` `{evidencia}` no alcanza `min_evidence` (`{min_evidence}`) "
                    f"de la categoria `{categoria.get('key')}`",
                    fichero, "evidencia"))

    fuentes = fm.get("fuentes")
    if "fuentes" not in fm:
        errores.append(_error("falta `fuentes` (lista no vacia, obligatoria al aprobar)", fichero, "fuentes"))
    elif not isinstance(fuentes, list) or not fuentes:
        # gap 52: diagnostico distinto de "falta" cuando el campo SI esta pero no es la forma
        # esperada (mismo criterio que `knowledge-index._validar_frontmatter_forma`).
        errores.append(_error("`fuentes` declarado pero no es una lista no vacia", fichero, "fuentes"))

    tags = fm.get("tags")
    if "tags" not in fm:
        errores.append(_error("falta `tags` (lista no vacia, obligatoria al aprobar)", fichero, "tags"))
    elif not isinstance(tags, list) or not tags:
        errores.append(_error("`tags` declarado pero no es una lista no vacia", fichero, "tags"))
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

    errores.extend(detectar_denylist(cuerpo, config.get("denylist"), fichero))
    return errores


def detectar_colision(ki, root, categoria, fichero, fm):
    """Errores de COLISION al aprobar (gap 50): `knowledge-index.py` nunca escanea
    `candidates/**` (T-03), asi que no puede por si solo detectar que un candidato pisaria una
    entrada ya `approved/` — ni por `id` duplicado ni por nombre de fichero repetido en la misma
    carpeta destino. Se comprueba aqui, con el indice YA construido sobre `approved/`."""
    errores = []
    indice, _errores_indice = ki.build_index(root)
    id_candidato = fm.get("id")
    if id_candidato and id_candidato in indice:
        errores.append(_error(
            f"ya existe una entrada aprobada con el id `{id_candidato}` "
            f"(`{indice[id_candidato]['ruta']}`): cambia el `id` o resuelve la colision a mano",
            fichero, "id"))
    folder = categoria.get("folder") or ""
    nombre = os.path.basename(fichero)
    ruta_destino = os.path.join(root or ".", "docs", "knowledge", "approved", folder, nombre)
    if os.path.isfile(ruta_destino) and os.path.realpath(ruta_destino) != os.path.realpath(fichero):
        errores.append(_error(
            f"ya existe un fichero con el mismo nombre en `{ruta_destino}`: renombra el candidato "
            f"antes de aprobar",
            fichero, "$"))
    return errores


def evaluar(ruta_candidato, decision, category_override=None, root=None):
    """(veredicto_dict, exit_code). `veredicto_dict` = {decision, categoria, errores, avisos}.
    `avisos` son notas NO bloqueantes (gap 53: p. ej. `reject`/`needs_changes` sin `category`)."""
    if decision not in DECISIONES_VALIDAS:
        return {"decision": decision, "categoria": None,
                "errores": [_error(f"decision `{decision}` invalida ({', '.join(DECISIONES_VALIDAS)})",
                                    ruta_candidato, "decision")], "avisos": []}, 2

    if not _candidato_dentro_del_arbol(root, ruta_candidato):
        return {"decision": decision, "categoria": None, "errores": [_error(
            f"`{ruta_candidato}` no es un candidato: debe vivir bajo "
            f"`docs/knowledge/candidates/{{pending,needs_changes,rejected}}/` de `{root or '.'}`",
            ruta_candidato, "$")], "avisos": []}, 2

    try:
        ks = _cargar("knowledge-schema.py", "knowledge_schema")
        ki = _cargar("knowledge-index.py", "knowledge_index")
    except KitCompartidoNoDisponible as e:
        return {"decision": decision, "categoria": None, "errores": [_error(str(e), ruta_candidato, "$")],
                "avisos": []}, 2

    config, _origen, ruta_taxonomia, errores_taxonomia = ks.cargar_taxonomia(root)
    if errores_taxonomia:
        return {"decision": decision, "categoria": None, "errores": errores_taxonomia, "avisos": []}, 2

    fm, cuerpo, error_lectura = cargar_candidato(ruta_candidato, ki)
    if error_lectura:
        return {"decision": decision, "categoria": None, "errores": [error_lectura], "avisos": []}, 2

    clave_categoria = category_override or fm.get("category") or fm.get("categoria")

    if decision != "approve":
        # Rechazar o pedir cambios no exige evidencia/fuentes/tags/lista negra (gap 58): el
        # Curator puede descartar un candidato incompleto sin que el gate se lo impida.
        if not clave_categoria:
            # gap 53: sin `category` se dictamina igual — es EXACTAMENTE el candidato tipico de
            # rechazo. Un aviso no bloqueante, no un error de uso.
            aviso = _error("falta `category`: se dictamina sin ella (no bloquea reject/needs_changes)",
                            ruta_candidato, "category")
            return {"decision": decision, "categoria": None, "errores": [], "avisos": [aviso]}, 0
        categoria, errores_categoria = validar_categoria(config, clave_categoria, ruta_candidato)
        if errores_categoria:
            # `category` SI se declaro pero no es valida: sigue siendo un error de uso.
            return {"decision": decision, "categoria": clave_categoria, "errores": errores_categoria,
                    "avisos": []}, 2
        return {"decision": decision, "categoria": categoria["key"], "errores": [], "avisos": []}, 0

    categoria, errores_categoria = validar_categoria(config, clave_categoria, ruta_candidato)
    if errores_categoria:
        return {"decision": decision, "categoria": clave_categoria, "errores": errores_categoria, "avisos": []}, 2

    niveles_por_defecto = ks.default_taxonomy().get("evidence_levels")
    errores = validar_aprobacion(fm, cuerpo, categoria, config, ruta_candidato, niveles_por_defecto, ruta_taxonomia)
    errores.extend(detectar_colision(ki, root, categoria, ruta_candidato, fm))
    veredicto = {"decision": decision, "categoria": categoria["key"], "errores": errores, "avisos": []}
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
        for a in veredicto.get("avisos") or []:
            print(f"aviso: {a['fichero']}: {a['campo']}: {a['mensaje']}")
    else:
        for e in veredicto["errores"]:
            print(f"{e['fichero']}: {e['campo']}: {e['mensaje']}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
