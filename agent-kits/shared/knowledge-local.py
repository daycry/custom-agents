"""Private pure local approved reader; full index validation delegates here.

The original frontmatter parser, shape checks, containment and scan are shared,
not duplicated. Retrieval includes source snapshots; the full wrapper retains
its original result and complete service taxonomy validation.
"""
import importlib.util
import os
import re
import sys

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "knowledge_taxonomy_local", os.path.join(HERE, "knowledge-taxonomy-local.py"))
_TAXONOMY = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_TAXONOMY)

def _error(mensaje, fichero, campo):
    return {"mensaje": mensaje, "fichero": fichero, "campo": campo}


_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_LISTA_RE = re.compile(r"^\[(.*)\]$")
_ITEM_BLOQUE_RE = re.compile(r"^-\s*(.+)$")


def _normalizar_item_lista(valor):
    """YAML-simple: trim outer whitespace and remove one matching quote pair.

    Preserve inner whitespace and malformed/unmatched quotes for fail-closed
    validation. This does not decode escapes or commas inside quoted scalars.
    """
    valor = valor.strip()
    if len(valor) >= 2 and valor[0] in ('"', "'") and valor[-1] == valor[0]:
        return valor[1:-1]
    return valor


def _recortar_comentario_inline(contenido):
    """Recorta el comentario inline (si lo hay) de un item de lista en bloque (gap 172/173,
    revisión de dos lentes Fase 4 intento 2). Reglas, por orden:

    - Un `#` DENTRO de un valor entrecomillado (`'` o `"`) nunca es un comentario — se ignora
      mientras se está dentro de las comillas, tanto si el `#` viene precedido de espacio como si
      no (`- "a  # b"` conserva `a  # b` completo, no solo `a`).
    - Fuera de comillas, un `#` precedido de un espacio o un tab SÍ es un comentario YAML (basta
      UN espacio, no dos) y todo desde ahí (incluido ese espacio) se descarta.
    - Un `#` pegado al valor sin espacio delante (`https://a#frag`, `C#`, `ADR-001#sec`) no es un
      comentario: no se recorta.

    Gap 183 (revisión Fase 4 intento 3): una comilla NO abre cadena salvo que sea el PRIMER
    carácter no-blanco del valor — igual que YAML, donde un escalar entrecomillado empieza en el
    propio carácter de apertura. La versión anterior trataba CUALQUIER comilla como apertura, así
    que un apóstrofo dentro de una palabra normal (`Don't  # nota`) dejaba todo lo que seguía
    «dentro de comillas» sin cerrar nunca, y el comentario ya no se recortaba."""
    lstripped = contenido.lstrip()
    if lstripped[:1] in ('"', "'"):
        comilla = lstripped[0]
        offset = len(contenido) - len(lstripped)
        cierre = contenido.find(comilla, offset + 1)
        inicio_busqueda = cierre + 1 if cierre != -1 else len(contenido)
    else:
        inicio_busqueda = 0
    resto = contenido[inicio_busqueda:]
    for j, c in enumerate(resto):
        if c == "#" and j > 0 and resto[j - 1] in (" ", "\t"):
            corte = inicio_busqueda + j
            return contenido[: corte - 1].rstrip()
    return contenido


def _frontmatter(texto):
    """Owner del frontmatter YAML-simple compartido con el índice y la lectura local.

    Admite escalares, listas inline separadas por coma y listas en bloque. Los items
    de ambas listas normalizan un par de comillas simples o dobles emparejadas;
    no interpreta escapes ni comas dentro de escalares entrecomillados. No es YAML completo.
    """
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
                datos[clave] = [_normalizar_item_lista(v) for v in ml.group(1).split(",") if v.strip()]
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
            sub_strip = sub.strip()
            if not sub_strip:
                j += 1
                continue
            indent_sub = len(sub) - len(sub.lstrip())
            if indent_sub < indent_clave:
                break
            # gap heredado (revisión Fase 2 intento 2, T-10): un comentario `#` intercalado entre
            # los items de una lista en bloque paraba el escaneo en seco (no casaba con `- X`) y
            # truncaba en silencio el resto de la lista. Se salta sin consumir el item.
            if sub_strip.startswith("#"):
                j += 1
                continue
            mi = _ITEM_BLOQUE_RE.match(sub_strip)
            if not mi:
                # gap heredado (T-10): un item vacío (`-` sin contenido) tampoco casa con
                # `_ITEM_BLOQUE_RE` (exige al menos un carácter tras el guion); se descarta el
                # item vacío en vez de interpretarlo como el fin de la lista.
                if sub_strip == "-":
                    j += 1
                    continue
                break
            # gap 143 (revisión de dos lentes, Fase 4 intento 1): el fix heredado de arriba solo
            # saltaba un comentario en SU PROPIA línea (`  # nota`, sin guion) — una línea
            # `- # nota` SÍ casa con `_ITEM_BLOQUE_RE` (guion + contenido) y colaba `"# nota"`
            # como item basura. Se trata igual que un comentario suelto: se salta sin consumir el
            # item.
            contenido_item = mi.group(1)
            if contenido_item.strip().startswith("#"):
                j += 1
                continue
            # gap 172/173 (revisión de dos lentes, Fase 4 intento 2): el recorte exigía DOS
            # espacios antes de `#` (`partition("  #")`), pero YAML marca un comentario inline con
            # UN solo espacio o tab delante — `- ADR-002 # ver` (un espacio) colaba `"ADR-002 # ver"`
            # entero como item, produciendo un falso «enlace roto». Además se recortaba ANTES de
            # quitar comillas: `- "a  # b"` perdía todo lo que seguía a `#` aunque estuviera DENTRO
            # de la cadena entrecomillada. `_recortar_comentario_inline` distingue: (a) un `#`
            # precedido de espacio/tab y FUERA de comillas es un comentario y se recorta; (b) un
            # `#` dentro de un valor entrecomillado nunca es un comentario, se conserva íntegro; (c)
            # un `#` pegado al valor sin espacio delante (`https://a#frag`, `C#`, `ADR-001#sec`)
            # tampoco se recorta.
            valor_item = _recortar_comentario_inline(contenido_item)
            items.append(_normalizar_item_lista(valor_item))
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


def _ruta_segura_dentro(base, ruta, base_real=None):
    """True si `ruta` (ya unida a `base`) resuelve DENTRO de `base` tras normalizar symlinks/`..`
    (gap 6, defensa en profundidad: `knowledge-schema.validar` ya rechaza un `folder` con `..`/
    absoluto/unidad de Windows en la config, pero esta comprobación cubre además symlinks y
    cualquier otra vía de escape que el fichero de config no controle).

    `base_real` (gap heredado, revisión Fase 2 intento 2, T-10 — coste lineal de `realpath` por
    fichero en Windows, donde resolver symlinks es una llamada al sistema cara): `realpath(base)`
    es el MISMO valor durante todo el recorrido de una carpeta declarada, así que `build_index` lo
    calcula UNA vez por carpeta y lo pasa aquí en vez de dejar que se recalcule por cada candidato.
    Si no se pasa (p. ej. desde un test que llama a esta función directamente), se calcula como
    antes — el parámetro es opt-in, no rompe el contrato existente."""
    if base_real is None:
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

# gap 84/96 (revisión Fase 3 intento 1): `id` tiene que cumplir la MISMA forma que ya asume
# `markdown_export.py` («`knowledge_id` ya cumple `[A-Za-z0-9._-]+`, lo exige el Curator») — pero
# nadie lo comprobaba aquí. Sin este chequeo, `id: "../../ESCAPE"` pasaba el índice intacto y
# cualquier adaptador que componga una ruta con ese `id` (p. ej. `<export_dir>/<id>.md`) escribe
# fuera de `export_dir` (CWE-22). Defensa en profundidad: el adaptador vuelve a validar la misma
# forma por su cuenta, nunca confía en que el índice ya lo hizo.
_ID_VALIDO_RE = re.compile(r"^[A-Za-z0-9._-]+$")


def _validar_frontmatter_forma(fm, ruta, categorias_validas):
    """Comprobaciones de FORMA (no de semántica de categoría, ver docstring del módulo) sobre
    el frontmatter de una entrada aprobada (gap 3). `estado` es OBLIGATORIO bajo `approved/`
    (gap 43, revisión intento 1): antes de esta versión solo se validaba su forma cuando estaba
    presente, lo que permitía una entrada `approved/` sin `estado` en absoluto; el gate de
    aprobación (`curator-gate.py`, T-04) siempre lo escribe, así que ausente aquí es señal de
    una entrada tocada a mano o por un flujo que se saltó el gate. `fuentes`/`tags` siguen
    siendo opcionales (solo se valida su forma si están presentes). `category` pasa a ser
    OBLIGATORIA (gap 84, revisión Fase 3 intento 1) con el MISMO criterio que `estado`: sin ella,
    `knowledge-sync.py` no puede decidir el `routing` de la entrada y antes la descartaba en
    silencio, indistinguible del fail-closed por routing declarado a `false`."""
    errores = []
    if "category" not in fm:
        errores.append(_error(
            "falta `category` (obligatorio en una entrada bajo `approved/`; el curador la escribe "
            "al aprobar, ver `agents/knowledge-curator.md` P4)", ruta, "category"))
    else:
        category = fm["category"]
        if category == "":
            errores.append(_error("`category` presente sin valor", ruta, "category"))
        elif not isinstance(category, str) or category not in categorias_validas:
            errores.append(_error(
                f"`category` declarada (`{category}`) no existe en la taxonomía "
                f"(declaradas: {sorted(categorias_validas) or 'ninguna'})", ruta, "category"))
    if "estado" not in fm:
        errores.append(_error(
            "falta `estado` (obligatorio en una entrada bajo `approved/`; debe ser `aprobado`)",
            ruta, "estado"))
    else:
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


def build_index(root=None, config=None, include_source=False):
    """(indice, errores). indice: {id: {"ruta", "version", "folder", "enlaces"}}.
    errores: lista de {mensaje, fichero, campo}. Taxonomía inválida -> índice vacío y los
    errores de la taxonomía (no se intenta construir nada sobre un contrato roto). Un
    `knowledge-schema.py` ausente o roto (gap 4) degrada igual: índice vacío + un único error
    claro, nunca un traceback."""
    root = root or "."
    if config is None:
        config, _origin, _path, errors = _TAXONOMY.cargar_taxonomia(root)
        if errors:
            return {}, errors

    base = os.path.join(root, "docs", "knowledge", "approved")
    if include_source:
        canonical = os.path.join(os.path.realpath(root), "docs", "knowledge", "approved")
        if os.path.normcase(os.path.realpath(base)) != os.path.normcase(canonical):
            return {}, [_error("approved resuelve fuera del árbol canónico", base, "$")]
    carpetas = _carpetas_declaradas(config)
    errores = []
    # gap 30: dos `folder` declarados pueden anidarse legalmente segun `_folder_seguro`
    # (`"adr"` y `"adr/legacy"`); sin dedupe, `os.walk` visitaba el MISMO fichero fisico dos
    # veces (una por carpeta) y el chequeo de `id` duplicado (mas abajo) lo reportaba como error
    # contra si mismo. Se deduplica por `os.path.realpath`, no por ruta cruda.
    rutas_vistas_real = set()
    sources = []

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
        if include_source and not _ruta_segura_dentro(base, d):
            errores.append(_error("carpeta approved fuera del árbol canónico", d, "$"))
            continue
        # gap heredado (T-10): calculado UNA vez por carpeta, no por cada fichero candidato (ver
        # docstring de `_ruta_segura_dentro`).
        d_real = os.path.realpath(d)
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
                if not _ruta_segura_dentro(d, candidata, base_real=d_real):
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
                with open(ruta, "r", encoding="utf-8-sig", newline="" if include_source else None) as f:
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
            sources.append((ruta, folder, texto))

    parsed, validation_errors = index_snapshot(sources, config, include_source=include_source, root=root)
    return parsed, errores + validation_errors


def index_snapshot(sources, config, include_source=False, root="."):
    """Validate already-read (path, declared folder, text) snapshots without I/O.

    The full index and bounded retrieval use these same metadata/link rules.
    """
    categorias_validas = {cat.get("key") for cat in (config.get("categories") or []) if cat.get("key")}
    indice, errores, vistos_en = {}, [], {}
    for ruta, folder, texto in sources:
        fm = _frontmatter(texto)
        id_ = fm.get("id")
        if not id_:
            errores.append(_error("falta `id` en el frontmatter", ruta, "id"))
            continue
        if not isinstance(id_, str) or not _ID_VALIDO_RE.match(id_):
            # gap 96 (CWE-22): sin este chequeo, un `id` con `../` o separadores de ruta
            # (`/`, `\`) llega intacto a cualquier adaptador que componga
            # `<export_dir>/<id>.<ext>` y escribe fuera de `export_dir`.
            errores.append(_error(
                f"`id` (`{id_}`) no cumple la forma `[A-Za-z0-9._-]+` (sin `/`, `\\` ni rutas)",
                ruta, "id"))
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
        errores.extend(_validar_frontmatter_forma(fm, ruta, categorias_validas))
        if include_source:
            # Retrieval labels must be scalar; full indexing keeps its existing shape policy.
            for campo in ("area", "titulo", "iniciativa", "fecha", "fuente", "evidencia"):
                if campo in fm and not isinstance(fm[campo], str):
                    errores.append(_error(f"metadato local `{campo}` debe ser una cadena", ruta, campo))
            if "tags" in fm and (not isinstance(fm["tags"], list)
                                 or not all(isinstance(tag, str) for tag in fm["tags"])):
                errores.append(_error("metadato local `tags` debe ser una lista de cadenas", ruta, "tags"))
        cuerpo = _FRONTMATTER_RE.sub("", texto, count=1).strip()
        fuentes = fm.get("fuentes") or []
        if isinstance(fuentes, str):
            fuentes = [fuentes]
        tags = fm.get("tags") or []
        if isinstance(tags, str):
            tags = [tags]
        indice[id_] = {
            "ruta": ruta, "version": version, "folder": folder, "enlaces": enlaces,
            # gap 104 (rendimiento): el frontmatter YA se parseó y el cuerpo YA se leyó para
            # construir este índice — se guardan aquí para que `knowledge-sync.py` (y
            # cualquier otro consumidor) NUNCA tenga que reabrir el fichero solo para
            # recuperar `category`/`evidencia`/`fuentes`/`tags`/`cuerpo` (antes: 1000 open()
            # para 500 entradas indexadas con 10 enrutadas; ahora, 500 — uno por entrada).
            "category": fm.get("category"), "evidencia": fm.get("evidencia"),
            "fuentes": fuentes, "tags": tags, "cuerpo": cuerpo,
            # gap 110 (revision de dos lentes, intento 2 fix2): `resumen` explicito del
            # frontmatter, si el autor lo escribio - se propaga tal cual hasta el adaptador
            # (`markdown_export._cuerpo_segun_modo`), que ya lo usaba pero nunca lo recibia
            # porque ni el indice ni `knowledge-sync.py` lo extraian.
            "resumen": fm.get("resumen"),
        }
        if include_source:
            indice[id_].update(frontmatter=fm, texto=texto,
                              ruta_rel=os.path.relpath(ruta, os.path.join(root, "docs", "knowledge")).replace("\\", "/"))
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


