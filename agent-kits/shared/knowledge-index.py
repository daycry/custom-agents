#!/usr/bin/env python3
"""
knowledge-index.py — índice canónico determinista sobre la taxonomía configurada
(ADR-018, `knowledge-services` T-02). Sin dependencias externas.

Opera EXCLUSIVAMENTE sobre `docs/knowledge/approved/<folder>/` (una carpeta por cada
`categories[].folder` de `.claude/knowledge-services/taxonomy.json`, o de la plantilla por
defecto del plugin si el proyecto no configura nada — ver `knowledge-schema.py`). NUNCA escanea
`docs/knowledge/candidates/**` (T-03): un candidato no aprobado no puede aparecer en el índice.
Recorre subcarpetas de cada `folder` declarado (gap 17, revisión intento 1): una entrada puede
vivir en un subdirectorio propio (p. ej. adjuntos junto al `.md`).

Decisión de alcance (sin respaldo literal en spec/design, señalada para revisión): este validador
NO toca el corpus heredado `docs/knowledge/{adr,gotchas,lessons}/` (índice manual + `knowledge-
lint.py` diferido por ADR-006 D4, que sigue vigente e intacto). `knowledge-index.py` es un
validador NUEVO, específico del flujo de candidatos/aprobados que introduce `knowledge-services`;
las entradas legadas no llevan `version` ni `enlaces` en su frontmatter y exigírselo retroactivamente
rompería ADR-001..ADR-017/GOT-.../LES-... existentes sin necesidad.

Contrato de frontmatter de una entrada aprobada:
  id (str, obligatorio) · version (int, obligatorio) · enlaces (lista opcional de ids referidos)
  · estado (opcional; si se declara, debe ser "aprobado" — coherente con vivir bajo `approved/`)
  · fuentes (opcional; si se declara, lista no vacía) · tags (opcional; si se declara, lista)

Alcance de la validación de frontmatter (gap 3, revisión intento 1): este índice solo comprueba
la FORMA de `estado`/`fuentes`/`tags` cuando el campo está presente — nunca los exige, y nunca
comprueba `evidencia` contra el `min_evidence` de su categoría (una entrada de `approved/<folder>/`
puede pertenecer a más de una `category` que comparta esa carpeta — p. ej. PATTERN y GOTCHA
comparten `gotchas/` en la plantilla por defecto — así que el `folder` por sí solo no basta para
resolver a qué categoría exacta pertenece y qué evidencia mínima le aplica). Esa comprobación
semántica, y la obligatoriedad de los campos en el momento de aprobar un candidato, son del
`knowledge-curator` (T-04), que sí conoce la categoría exacta que asignó al aprobar.

Cada error es un dict {mensaje, fichero, campo} (mismo contrato que knowledge-schema.validar).

Uso:
  knowledge-index.py [--root <ruta>]   # construye el índice y lista errores; exit 0/1
Exit codes: 0 índice construido sin errores · 1 con errores (taxonomía inválida o entradas
inválidas) · 2 uso.
"""
import argparse
import importlib.util
import os
import re
import sys

# Consola no UTF-8 (Windows cp1252) o tuberías: reconfigurar ANTES de leer/imprimir (GOT-005).
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure, ya leído o None (capsys, pythonw)

HERE = os.path.dirname(os.path.abspath(__file__))


class KnowledgeSchemaNoDisponible(Exception):
    """`knowledge-schema.py` no se pudo cargar (gap 4): degradación explícita en vez de un
    traceback crudo de `importlib` cuando el vecino no viaja junto a este fichero."""


def _cargar_knowledge_schema():
    """Carga knowledge-schema.py (T-01) desde el mismo directorio. Replicado a propósito en vez
    de un import de paquete: cada script del kit compartido es standalone (ver comentario
    celdas_md en knowledge-find.py), pero ambos ficheros viajan siempre juntos en
    agent-kits/shared/, así que cargar el vecino por ruta relativa es seguro y evita duplicar
    ~200 líneas de validación de taxonomy.json.

    Mecanismo B de ADR-016 (canónico + degradación, no respaldo copiado): si el fichero falta o
    no carga, se levanta `KnowledgeSchemaNoDisponible` con un mensaje claro — el llamador
    (`build_index`) lo convierte en un error `{fichero, campo, mensaje}` normal (exit 1), nunca en
    un traceback (gap 4; `capabilities.py` ya degradaba así a través de `_resolver`, este fichero
    no)."""
    ruta = os.path.join(HERE, "knowledge-schema.py")
    if not os.path.isfile(ruta):
        raise KnowledgeSchemaNoDisponible(f"no se encontró `{ruta}` (debería viajar junto a este fichero)")
    spec = importlib.util.spec_from_file_location("knowledge_schema", ruta)
    if spec is None or spec.loader is None:
        raise KnowledgeSchemaNoDisponible(f"no se pudo preparar la carga de `{ruta}`")
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as e:  # noqa: BLE001 - cualquier fallo de carga degrada, no tumba el CLI
        raise KnowledgeSchemaNoDisponible(f"{type(e).__name__}: {e}") from e
    return mod


def _error(mensaje, fichero, campo):
    return {"mensaje": mensaje, "fichero": fichero, "campo": campo}


_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_LISTA_RE = re.compile(r"^\[(.*)\]$")
_ITEM_BLOQUE_RE = re.compile(r"^-\s*(.+)$")


def _frontmatter(texto):
    """Parser mínimo de frontmatter YAML-simple: escalares, listas `[a, b]` de una línea y listas
    en bloque (`enlaces:` seguido de líneas `  - X`, gap 9 — el `knowledge-curator`/documenter
    suele emitir listas en bloque, no inline). Replicado deliberadamente en vez de importar el
    parser de knowledge-find.py (mismo criterio standalone que arriba, pero ese script cubre
    muchos más casos que no necesitamos aquí)."""
    m = _FRONTMATTER_RE.match(texto)
    if not m:
        return {}
    datos = {}
    lineas = m.group(1).splitlines()
    i = 0
    while i < len(lineas):
        linea = lineas[i]
        cruda = linea
        linea = linea.strip()
        if not linea or linea.startswith("#") or ":" not in linea:
            i += 1
            continue
        clave, _, valor = linea.partition(":")
        clave = clave.strip()
        valor = valor.strip()
        if valor:
            ml = _LISTA_RE.match(valor)
            if ml:
                datos[clave] = [v.strip() for v in ml.group(1).split(",") if v.strip()]
            else:
                datos[clave] = valor.strip('"').strip("'")
            i += 1
            continue
        # Clave sin valor en la misma línea: puede ser una lista en bloque (líneas siguientes con
        # "- X", indentadas o a la MISMA sangría que la clave — gap 25: PyYAML por defecto emite
        # los items de una secuencia de bloque SIN indentar respecto a su clave, así que exigir
        # `indent_sub > indent_clave` dejaba esa forma, perfectamente válida, sin parsear). Si no
        # hay ninguna, la clave queda vacía (cadena "").
        indent_clave = len(cruda) - len(cruda.lstrip())
        items = []
        j = i + 1
        while j < len(lineas):
            sub = lineas[j]
            if not sub.strip():
                j += 1
                continue
            indent_sub = len(sub) - len(sub.lstrip())
            if indent_sub < indent_clave:
                break
            mi = _ITEM_BLOQUE_RE.match(sub.strip())
            if not mi:
                break
            items.append(mi.group(1).strip().strip('"').strip("'"))
            j += 1
        if items:
            datos[clave] = items
            i = j
        else:
            datos[clave] = ""
            i += 1
    return datos


def _carpetas_declaradas(config):
    """folder -> lista de categorías (una carpeta puede servir a varias categorías, p. ej.
    PATTERN y GOTCHA comparten gotchas/ en la plantilla por defecto)."""
    out = {}
    for cat in config.get("categories") or []:
        folder = cat.get("folder")
        if folder:
            out.setdefault(folder, []).append(cat.get("key"))
    return out


def _ruta_segura_dentro(base, ruta):
    """True si `ruta` (ya unida a `base`) resuelve DENTRO de `base` tras normalizar symlinks/`..`
    (gap 6, defensa en profundidad: `knowledge-schema.validar` ya rechaza un `folder` con `..`/
    absoluto/unidad de Windows en la config, pero esta comprobación cubre además symlinks y
    cualquier otra vía de escape que el fichero de config no controle)."""
    base_real = os.path.realpath(base)
    ruta_real = os.path.realpath(ruta)
    try:
        return os.path.commonpath([base_real, ruta_real]) == base_real
    except ValueError:
        # gap 31: un symlink/junction a OTRA unidad de Windows hace que `commonpath` lance
        # "Paths don't have the same drive" en vez de devolver un booleano; sin unidad comun no
        # puede estar DENTRO de `base`, así que degrada a "fuera" (fail-closed) sin traceback.
        return False


_ESTADOS_VALIDOS_APROBADO = {"aprobado"}


def _validar_frontmatter_forma(fm, ruta):
    """Comprobaciones de FORMA (no de semántica de categoría, ver docstring del módulo) sobre
    campos opcionales del frontmatter de una entrada aprobada (gap 3)."""
    errores = []
    if "estado" in fm:
        estado = fm["estado"]
        if estado == "":
            # gap 33: `_frontmatter()` devuelve `""` para una clave presente SIN valor (ni
            # escalar ni lista de bloque) — un mensaje que dice `(``)` "no es valido" confunde
            # esto con un valor explicito mal escrito.
            errores.append(_error(
                "`estado` presente sin valor (se esperaba `aprobado`)", ruta, "estado"))
        elif not isinstance(estado, str) or estado not in _ESTADOS_VALIDOS_APROBADO:
            errores.append(_error(
                f"`estado` declarado (`{estado}`) no es válido para una entrada bajo `approved/` "
                f"(se esperaba `aprobado`)", ruta, "estado"))
    if "fuentes" in fm:
        fuentes = fm["fuentes"]
        if not isinstance(fuentes, list) or not fuentes:
            errores.append(_error(
                "`fuentes` declarado pero no es una lista no vacía", ruta, "fuentes"))
    if "tags" in fm:
        tags = fm["tags"]
        if not isinstance(tags, list):
            errores.append(_error("`tags` declarado pero no es una lista", ruta, "tags"))
    return errores


def build_index(root=None):
    """(indice, errores). indice: {id: {"ruta", "version", "folder", "enlaces"}}.
    errores: lista de {mensaje, fichero, campo}. Taxonomía inválida -> índice vacío y los
    errores de la taxonomía (no se intenta construir nada sobre un contrato roto). Un
    `knowledge-schema.py` ausente o roto (gap 4) degrada igual: índice vacío + un único error
    claro, nunca un traceback."""
    root = root or "."
    try:
        ks = _cargar_knowledge_schema()
    except KnowledgeSchemaNoDisponible as e:
        return {}, [_error(str(e), os.path.join(HERE, "knowledge-schema.py"), "$")]
    config, _origen, _ruta_taxonomia, errores_taxonomia = ks.cargar_taxonomia(root)
    if errores_taxonomia:
        return {}, errores_taxonomia

    base = os.path.join(root, "docs", "knowledge", "approved")
    carpetas = _carpetas_declaradas(config)

    indice = {}
    errores = []
    vistos_en = {}  # id -> primera ruta donde se vio (para el mensaje de duplicado)
    # gap 30: dos `folder` declarados pueden anidarse legalmente segun `_folder_seguro`
    # (`"adr"` y `"adr/legacy"`); sin dedupe, `os.walk` visitaba el MISMO fichero fisico dos
    # veces (una por carpeta) y el chequeo de `id` duplicado (mas abajo) lo reportaba como error
    # contra si mismo. Se deduplica por `os.path.realpath`, no por ruta cruda.
    rutas_vistas_real = set()

    # gap 38 (fix4): procesar los `folder` MAS ANIDADOS primero (mas segmentos `/`) para que, con
    # `"adr"` y `"adr/legacy"` declarados, el fichero fisico que vive bajo `adr/legacy/` se asigne
    # a la carpeta MAS ESPECIFICA (gana el dedupe de `rutas_vistas_real`) en vez de a la carpeta
    # exterior que `os.walk` recorre igual por recursion. A igual profundidad, orden alfabetico
    # (mismo criterio que el `sorted(carpetas)` original) para que el resto de casos (carpetas no
    # relacionadas) sean deterministas y no cambien de comportamiento.
    for folder in sorted(carpetas, key=lambda f: (-f.count("/"), f)):
        d = os.path.join(base, folder)
        if not os.path.isdir(d):
            continue
        rutas_md = []
        for dirpath, dirnames, filenames in os.walk(d):
            dirnames.sort()
            for nombre in sorted(filenames):
                if not nombre.lower().endswith(".md") or nombre.upper() == "README.MD":
                    continue
                candidata = os.path.join(dirpath, nombre)
                # gap 37 (fix4, regresion del dedupe del gap 30): la contencion se comprueba
                # ANTES de registrar la `realpath` en `rutas_vistas_real`, no despues. Con el
                # orden antiguo, una ruta ILEGITIMA (p. ej. una junction que resuelve al mismo
                # fichero fisico que una entrada legitima de OTRA carpeta) consumia la entrada del
                # dedupe antes de ser rechazada, y la entrada legitima desaparecia del indice al
                # encontrarla ya "vista". Rechazar sin registrar deja la entrada legitima intacta
                # para cuando le toque su turno.
                if not _ruta_segura_dentro(d, candidata):
                    errores.append(_error(
                        "ruta fuera de la carpeta aprobada declarada (posible symlink/escape)",
                        candidata, "$"))
                    continue
                real = os.path.realpath(candidata)
                if real in rutas_vistas_real:
                    continue
                rutas_vistas_real.add(real)
                rutas_md.append(candidata)
        for ruta in sorted(rutas_md):
            try:
                with open(ruta, "r", encoding="utf-8-sig") as f:
                    texto = f.read()
            except OSError as e:
                errores.append(_error(f"no se pudo leer: {e}", ruta, "$"))
                continue
            except UnicodeDecodeError as e:
                # gap 26: un .md en cp1252/latin-1 no descodifica como utf-8-sig; se reporta como
                # error de ESTA entrada (campo "encoding") y el índice sigue con el resto, en vez
                # de tumbar `build_index` entero con un traceback.
                errores.append(_error(f"no se pudo leer con codificacion utf-8: {e}", ruta, "encoding"))
                continue
            fm = _frontmatter(texto)
            id_ = fm.get("id")
            if not id_:
                errores.append(_error("falta `id` en el frontmatter", ruta, "id"))
                continue
            if id_ in indice:
                errores.append(_error(
                    f"id duplicado `{id_}` (ya declarado en `{vistos_en[id_]}`)", ruta, "id"))
                continue
            if "version" not in fm:
                errores.append(_error("falta `version` en el frontmatter", ruta, "version"))
                version = None
            else:
                try:
                    version = int(fm["version"])
                except (TypeError, ValueError):
                    errores.append(_error("`version` debe ser un entero", ruta, "version"))
                    version = None
            enlaces = fm.get("enlaces") or []
            if isinstance(enlaces, str):
                enlaces = [enlaces]
            errores.extend(_validar_frontmatter_forma(fm, ruta))
            indice[id_] = {"ruta": ruta, "version": version, "folder": folder, "enlaces": enlaces}
            vistos_en[id_] = ruta

    # Enlaces rotos: se resuelven una vez que TODO el índice está construido (un enlace puede
    # citar una entrada de otra carpeta que aún no se había escaneado).
    for id_, entrada in indice.items():
        for destino in entrada["enlaces"]:
            if destino not in indice:
                errores.append(_error(
                    f"enlace roto: `{id_}` cita `{destino}`, que no existe en el índice",
                    entrada["ruta"], "enlaces"))

    return indice, errores


def _construir_parser():
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--root", default=".", help="raíz del proyecto (default: cwd)")
    return ap


def main(argv=None):
    args = _construir_parser().parse_args(argv)
    indice, errores = build_index(args.root)
    if not errores:
        print(f"knowledge-index: {len(indice)} entrada(s), sin errores")
        return 0
    for e in errores:
        print(f"{e['fichero']}: {e['campo']}: {e['mensaje']}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
