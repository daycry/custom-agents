"""Pure approval rules shared by the read-only gate and curation persistence."""
import re
import sys
import unicodedata

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass

ESTADO_APROBADO = "aprobado"
_TAG_CLAVE_VALOR_RE = re.compile(r"^[^:]+:.+$")

def _error(mensaje, fichero, campo):
    return {"mensaje": mensaje, "fichero": fichero, "campo": campo}

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


def _plegar_acentos(texto):
    """NFD + descarta las marcas combinantes: `conversación` -> `conversacion` (gap 64). La lista
    negra por defecto ya viaja sin tildes (design.md, decision deliberada para que el propio gate
    sea ASCII puro), pero la PROSA real de un candidato si las lleva — sin plegar, un termino como
    `conversacion cruda` nunca casaba con «conversación cruda» escrito de verdad."""
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


def _es_caracter_de_palabra(c):
    return bool(c) and re.match(r"\w", c, re.UNICODE) is not None

# Gap 77: el limite IZQUIERDO de un termino que empieza en caracter de palabra (`TODO:`, `codigo
# duplicado`...) no puede ser cualquier caracter "no de palabra" — `(?<!\w)` deja pasar `/`, `:` o
# `.` sin espacio, que es justo como aparece un termino DENTRO de una URL o una ruta
# (`https://x/TODO:1234`, `a.b.TODO:`). El termino solo dispara si lo que precede es el inicio del
# texto, un espacio, o puntuacion de APERTURA de frase — nunca un separador de ruta/URL ni una letra
# u otro simbolo cualquiera.
_PRECEDENTE_PERMITIDO_NEGADO = "[^\\s(\\[\"'¿¡\\-—]"  # ( [ " ' ¿ ¡ - —

# Gap 78/80: el separador entre las PARTES de un termino multi-palabra («conversacion cruda»,
# «chain-of-thought», `chain_of_thought`) casa espacios, guiones y guiones bajos indistintamente
# (gap 80: se sumo `_` al `[\s-]+` original) — pero un salto de linea NO puede colar una frontera de
# lista markdown (gap 78): `\n` seguido (tras espacios) de una viñeta (`- `, `* `, `+ `), una
# numeracion (`1. `/`1) `) o una linea en blanco no cuenta como separador valido, porque eso son dos
# elementos DISTINTOS de una lista, no el mismo termino partido por el formato.
_SEPARADOR_TERMINO = (
    r"(?:[ \t_-]+|\n(?![ \t]*(?:\n|[-*+][ \t]|\d+[.)][ \t])))"
)


def _regex_termino(termino):
    """Un termino de la lista negra puede tener varias palabras («conversacion cruda») o ir unido
    por guion («chain-of-thought») o guion bajo (`chain_of_thought`, gap 80): las tres formas casan
    entre si partiendo el termino por ESPACIOS, GUIONES O GUIONES BAJOS (`[\\s_-]+`) y
    recomponiendolo con el mismo separador flexible entre las partes — cubre saltos de linea (salvo
    que crucen una frontera de lista markdown, gap 78) y la variante con espacios de un termino
    declarado con guion (o al reves).

    Los limites NO son `\\b` literal (gap 41): `\\b` falla en los dos sentidos que este termino
    necesita — no detecta el limite tras un termino que acaba en puntuacion (`TODO:` seguido de un
    espacio: ninguno de los dos lados de esa posicion es un caracter de palabra), y SI detecta como
    "palabra completa" una coincidencia de mayusculas/minusculas que es en realidad OTRA palabra
    (p. ej. `todos`, dentro de "Todos los handlers", es la palabra espanola comun, no el marcador
    `TODOs`). Se usan lookarounds, y SOLO en el lado cuyo caracter de borde del termino es de
    palabra (gap 65): un termino que ya acaba (o empieza) en puntuacion —`TODO:`— no exige nada en
    ese lado, porque el propio termino ya aporta el limite (`TODO:limpiar`, sin espacio, tiene que
    disparar). El lado IZQUIERDO, ademas, exige que el caracter previo sea inicio/espacio/apertura
    de frase (gap 77), nunca un separador de ruta o URL sin espacio."""
    termino_plegado = _plegar_acentos(termino)
    partes = [re.escape(p) for p in re.split(r"[\s_-]+", termino_plegado) if p]
    if not partes:
        return None
    cuerpo = _SEPARADOR_TERMINO.join(partes)
    prefijo = f"(?<!{_PRECEDENTE_PERMITIDO_NEGADO})" if _es_caracter_de_palabra(termino_plegado[:1]) else ""
    sufijo = r"(?!\w)" if _es_caracter_de_palabra(termino_plegado[-1:]) else ""
    return re.compile(prefijo + cuerpo + sufijo, re.IGNORECASE)


def detectar_denylist(cuerpo, denylist, fichero):
    """Errores por cada termino de la lista negra que aparece, como palabra/frase completa (gap
    41) y sin importar los acentos de la PROSA real (gap 64), en el CUERPO del candidato (nunca en
    su frontmatter) — spec «Lista negra de memoria activa»: chain-of-thought, conversacion cruda,
    TODO:, planes/progreso, logs completos, salidas enormes, codigo duplicado, errores triviales,
    intentos sin aprendizaje, hipotesis como hechos, opiniones, redundancias. Un candidato que cite
    uno de estos terminos NO se aprueba sin que el Curator lo revise a mano (nunca memoria activa,
    spec `Alcance`)."""
    errores = []
    cuerpo_plegado = _plegar_acentos(cuerpo)
    for termino in denylist or []:
        if not termino:
            continue
        patron = _regex_termino(termino)
        if patron is not None and patron.search(cuerpo_plegado):
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


_ID_FORMA_RE = re.compile(r"^[A-Za-z0-9._-]+$")


def validar_id_override(id_override, fm, config, fichero):
    """(id_efectivo_o_None, errores, error_de_uso_o_None). Gaps 75/79: normaliza y valida `--id`
    ANTES de que `detectar_colision()` lo use.
      - `id_override is None` (no se paso `--id`): nada que hacer, `(None, [], None)`.
      - Gap 79: se `strip()`ea primero; en blanco (`--id "   "`) es un error de USO (exit 2), no un
        id valido que apague en silencio el aviso de «colision no comprobada» de detectar_colision.
      - Gap 79: forma — solo `[A-Za-z0-9._-]`, y si la taxonomia declara `id_prefix` (siempre lo
        hace tras `cargar_taxonomia()`, con el slug del proyecto como respaldo — gap 5 de
        `knowledge-schema.py`) el id debe empezar por `<id_prefix>.`.
      - Gap 75: si el frontmatter YA trae `id` y `--id` es OTRO valor, es un error bloqueante que
        nombra los dos — antes `fm.get("id") or id_override` descartaba `--id` en silencio y el
        gate aprobaba usando el `id` del frontmatter sin comprobar el que el Curator pensaba
        asignar de verdad."""
    if id_override is None:
        return None, [], None
    valor = id_override.strip()
    if not valor:
        return None, [], _error("`--id` no puede estar en blanco", fichero, "id")
    errores = []
    if not _ID_FORMA_RE.match(valor):
        errores.append(_error(
            f"`--id` `{valor}` tiene forma invalida (solo se admite [A-Za-z0-9._-])", fichero, "id"))
    prefijo = config.get("id_prefix") if isinstance(config, dict) else None
    if prefijo and not valor.startswith(f"{prefijo}."):
        errores.append(_error(
            f"`--id` `{valor}` no empieza por el prefijo `{prefijo}.` de la taxonomia", fichero, "id"))
    id_frontmatter = fm.get("id")
    if id_frontmatter and id_frontmatter != valor:
        errores.append(_error(
            f"`id` del frontmatter (`{id_frontmatter}`) y `--id` (`{valor}`) no coinciden: "
            f"resuelve la discrepancia antes de aprobar", fichero, "id"))
    return valor, errores, None


