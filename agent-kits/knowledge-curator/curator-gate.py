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
que no sea otra cosa que `aprobado` (gap 34). Es una evaluacion de solo lectura,
no una autorizacion de escritura. El Curator decide y `knowledge-curation.py apply`
valida la representacion final (ID, version, estado y SHA original) y la publica;
el agente no mueve el fichero manualmente. `knowledge-index.py` exige `estado: aprobado` en
`approved/` (una entrada aprobada sin `estado` es un error del indice) — ver su docstring. Cada
puerta vigila su propio momento del flujo: este gate el instante de aprobar, el indice el estado
final en disco. Las reglas de categoria/evidencia/denylist se comparten desde
`agent-kits/shared/knowledge-curation-rules.py`, sin un segundo gate de contenido.

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
# Las TRES carpetas del arbol de candidatos (contencion general, gap 48). `rejected/` es TERMINAL
# (gap 49/67, invariante fijado tras el gap 49): un fichero que ya vive ahi solo admite
# `--decision reject` (idempotente, el Curator puede re-rechazar sin que sea un error) — nunca
# `approve` ni `needs_changes`, que reabririan un candidato descartado.
CARPETAS_CANDIDATOS = ("pending", "needs_changes", "rejected")
CARPETAS_ORIGEN_POR_DECISION = {
    "approve": ("pending", "needs_changes"),
    "needs_changes": ("pending", "needs_changes"),
    "reject": ("pending", "needs_changes", "rejected"),
}


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


def _carpeta_candidato(root, ruta):
    """La carpeta (`pending`/`needs_changes`/`rejected`) bajo la que `ruta` resuelve (realpath)
    dentro de `<root>/docs/knowledge/candidates/` (gap 48), o `None` si no vive ahi. Fail-closed:
    cualquier fallo de resolucion (p. ej. unidades de Windows distintas) es "fuera"."""
    base = os.path.realpath(os.path.join(root or ".", "docs", "knowledge", "candidates"))
    ruta_real = os.path.realpath(ruta)
    try:
        rel = os.path.relpath(ruta_real, base)
    except ValueError:
        return None
    if rel == os.curdir or rel.split(os.sep)[0] == os.pardir:
        return None
    primera = rel.split(os.sep, 1)[0]
    return primera if primera in CARPETAS_CANDIDATOS else None


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


_RULES = {}

def _rules():
    key = os.path.abspath(SHARED)
    if key not in _RULES:
        _RULES[key] = _cargar("knowledge-curation-rules.py", "knowledge_curation_rules")
    return _RULES[key]


def validar_categoria(*args, **kwargs):
    return _rules().validar_categoria(*args, **kwargs)


def validar_aprobacion(*args, **kwargs):
    return _rules().validar_aprobacion(*args, **kwargs)


def validar_id_override(*args, **kwargs):
    return _rules().validar_id_override(*args, **kwargs)


def detectar_denylist(*args, **kwargs):
    return _rules().detectar_denylist(*args, **kwargs)


def detectar_colision(ki, root, categoria, fichero, fm, id_override=None):
    """(errores, avisos) de COLISION al aprobar (gap 50): `knowledge-index.py` nunca escanea
    `candidates/**` (T-03), asi que no puede por si solo detectar que un candidato pisaria una
    entrada ya `approved/` — ni por `id` duplicado ni por nombre de fichero repetido en la misma
    carpeta destino. Se comprueba aqui, con el indice YA construido sobre `approved/`.

    Gap 68: la guarda de `id` es INERTE si el candidato no declara `id` en su frontmatter — el caso
    mas expuesto es justo el candidato al que el Curator le va a ASIGNAR el `id` a mano (P4 de
    `agents/knowledge-curator.md`), que en el momento de `approve` todavia no lo trae. `--id` deja
    que el llamador pase el `id` que va a asignar para que la guarda lo compruebe ANTES de escribirlo
    en disco; sin `--id` NI `id` en el frontmatter, la guarda no tiene nada que comprobar y lo dice
    con un aviso explicito (no bloqueante: no es un error del candidato, es una comprobacion que no
    se pudo hacer).

    `id_override` aqui YA llega saneado por `validar_id_override()` (gaps 75/79: `strip()`eado,
    validado en forma/prefijo, y comprobado contra `fm["id"]` si el candidato ya lo trae) — este
    parametro nunca es una cadena en blanco ni un valor que contradiga al del frontmatter."""
    errores = []
    avisos = []
    indice, _errores_indice = ki.build_index(root)
    id_candidato = fm.get("id") or id_override
    if id_candidato:
        if id_candidato in indice:
            errores.append(_error(
                f"ya existe una entrada aprobada con el id `{id_candidato}` "
                f"(`{indice[id_candidato]['ruta']}`): cambia el `id` o resuelve la colision a mano",
                fichero, "id"))
    else:
        avisos.append(_error(
            "sin `id` en el frontmatter ni `--id`: la colision de id no se ha comprobado "
            "(pasa `--id <el-que-vas-a-asignar>` antes de escribirlo en disco)",
            fichero, "id"))
    folder = categoria.get("folder") or ""
    nombre = os.path.basename(fichero)
    ruta_destino = os.path.join(root or ".", "docs", "knowledge", "approved", folder, nombre)
    if os.path.isfile(ruta_destino) and os.path.realpath(ruta_destino) != os.path.realpath(fichero):
        errores.append(_error(
            f"ya existe un fichero con el mismo nombre en `{ruta_destino}`: renombra el candidato "
            f"antes de aprobar",
            fichero, "$"))
    return errores, avisos


def evaluar(ruta_candidato, decision, category_override=None, root=None, id_override=None):
    """(veredicto_dict, exit_code). `veredicto_dict` = {decision, categoria, errores, avisos}.
    `avisos` son notas NO bloqueantes (gap 53: p. ej. `reject`/`needs_changes` sin `category`; gap
    68: colision de `id` no comprobada). `id_override` (gap 68) es el `id` que el Curator va a
    asignar al aprobar un candidato que todavia no lo trae en el frontmatter."""
    if decision not in DECISIONES_VALIDAS:
        return {"decision": decision, "categoria": None,
                "errores": [_error(f"decision `{decision}` invalida ({', '.join(DECISIONES_VALIDAS)})",
                                    ruta_candidato, "decision")], "avisos": []}, 2

    carpeta = _carpeta_candidato(root, ruta_candidato)
    if carpeta is None:
        return {"decision": decision, "categoria": None, "errores": [_error(
            f"`{ruta_candidato}` no es un candidato: debe vivir bajo "
            f"`docs/knowledge/candidates/{{pending,needs_changes,rejected}}/` de `{root or '.'}`",
            ruta_candidato, "$")], "avisos": []}, 2

    if carpeta not in CARPETAS_ORIGEN_POR_DECISION[decision]:
        # gap 67: `rejected/` es terminal (invariante del gap 49) — solo admite `--decision reject`
        # (idempotente, el Curator puede re-rechazar sin que sea un error de uso).
        return {"decision": decision, "categoria": None, "errores": [_error(
            f"`{ruta_candidato}` vive en `rejected/`, que es terminal: solo admite "
            f"`--decision reject` (idempotente), nunca `{decision}`",
            ruta_candidato, "$")], "avisos": []}, 2

    try:
        ks = _cargar("knowledge-schema.py", "knowledge_schema")
        ki = _cargar("knowledge-index.py", "knowledge_index")
        _rules()
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

    # Gaps 75/79: `--id` se sanea ANTES de tocar la guarda de colision — en blanco es un error de
    # USO (exit 2, como cualquier otro argumento mal formado), no un id valido en silencio.
    id_efectivo, errores_id_override, error_uso_id = validar_id_override(id_override, fm, config, ruta_candidato)
    if error_uso_id:
        return {"decision": decision, "categoria": categoria["key"], "errores": [error_uso_id], "avisos": []}, 2

    niveles_por_defecto = ks.default_taxonomy().get("evidence_levels")
    errores = validar_aprobacion(fm, cuerpo, categoria, config, ruta_candidato, niveles_por_defecto, ruta_taxonomia)
    errores.extend(errores_id_override)
    errores_colision, avisos_colision = detectar_colision(ki, root, categoria, ruta_candidato, fm, id_efectivo)
    errores.extend(errores_colision)
    avisos = list(avisos_colision)
    if not (fm.get("category") or fm.get("categoria")):
        # gap 84 (revisión Fase 3 intento 1): `category` llega SOLO por `--category`, no está en
        # el frontmatter del candidato — el gate no escribe el fichero (eso es P4 del agente,
        # `agents/knowledge-curator.md`), así que se lo recuerda explícitamente en vez de dejar
        # que se olvide: `knowledge-index.py` exige `category` en `approved/` (gap 84) y una
        # entrada sin ella ahí es un error de índice, no una omisión silenciosa.
        avisos.append(_error(
            f"`category` viene de --category (`{categoria['key']}`) y no está en el frontmatter "
            f"del candidato: escríbela en el fichero al mover a `approved/` (P4)",
            ruta_candidato, "category"))
    veredicto = {"decision": decision, "categoria": categoria["key"], "errores": errores, "avisos": avisos}
    return veredicto, (1 if errores else 0)


def _construir_parser():
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("candidato", help="ruta al fichero .md del candidato")
    ap.add_argument("--decision", required=True, choices=DECISIONES_VALIDAS)
    ap.add_argument("--category", help="clave de taxonomy.json; si falta, se lee del frontmatter (`category`/`categoria`)")
    ap.add_argument("--id", dest="id_override",
                     help="el `id` que el Curator va a asignar al candidato al aprobarlo (gap 68); "
                          "si falta y el frontmatter tampoco trae `id`, la guarda de colision avisa "
                          "de que no se pudo comprobar. En blanco es un error de uso (gap 79); si "
                          "el frontmatter ya trae `id` y difiere, bloquea (gap 75); debe tener forma "
                          "`[A-Za-z0-9._-]+` y empezar por el `id_prefix.` de la taxonomia (gap 79)")
    ap.add_argument("--root", default=".", help="raiz del proyecto (default: cwd)")
    ap.add_argument("--json", action="store_true", help="salida en JSON")
    return ap


def main(argv=None):
    args = _construir_parser().parse_args(argv)
    veredicto, exit_code = evaluar(args.candidato, args.decision, args.category, args.root, args.id_override)

    if args.json:
        print(json.dumps(veredicto, ensure_ascii=False))
        return exit_code

    # Gap 81: los avisos (p. ej. «colision de id no comprobada») son informativos y pueden convivir
    # con errores bloqueantes (approve incompleto Y sin `--id`) — antes solo se imprimian en la
    # rama `exit_code == 0`, asi que con errores (exit 1/2) desaparecian de la salida en texto (solo
    # sobrevivian en `--json`). Se imprimen SIEMPRE que existan, sea cual sea el exit code.
    if exit_code == 0:
        print(f"curator-gate: `{args.decision}` permitido (categoria `{veredicto['categoria']}`)")
    else:
        for e in veredicto["errores"]:
            print(f"{e['fichero']}: {e['campo']}: {e['mensaje']}")
    for a in veredicto.get("avisos") or []:
        print(f"aviso: {a['fichero']}: {a['campo']}: {a['mensaje']}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
