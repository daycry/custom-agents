#!/usr/bin/env python3
"""Guardarrail UNICO de las copias declaradas del repo (`agent-kits/shared/copias.json`, ADR-016).

Las piezas del plugin son standalone (una skill se puede instalar sola, sin `agent-kits/`), asi que
lo compartido se REPLICA en vez de importarse. Antes convivian cuatro mecanismos para el mismo
problema -bloque `--8<--` con test byte a byte, canonico + respaldo con test de cadenas, canonico +
respaldo SIN nada y copia independiente con test solo conductual-. Aqui hay UNO: el registro dice
donde vive cada bloque y este test afirma que las copias son identicas BYTE A BYTE tras normalizar
`\\r\\n` -> `\\n` (GOT-007: en Windows con `core.autocrlf` los bytes crudos dan falso positivo).

Si dos copias divergen, esto FALLA (exit code), no avisa. La otra mitad de la puerta la pone
`scripts/lint_plugin.py` (`comprobar_copias_declaradas`): error si aparece un bloque `--8<--` o una
constante `_*_FALLBACK` SIN fila en el registro.
"""
import importlib.util
import json
import os
import re

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRO = os.path.join(ROOT, "agent-kits", "shared", "copias.json")


def _registro():
    with open(REGISTRO, encoding="utf-8") as fh:
        return json.load(fh)


DATOS = _registro()
BLOQUES = DATOS["bloques"]
CODIGO = [b for b in BLOQUES if not b.get("no_codigo")]
NO_CODIGO = [b for b in BLOQUES if b.get("no_codigo")]
IDS_CODIGO = [b["id"] for b in CODIGO]
IDS_NO_CODIGO = [b["id"] for b in NO_CODIGO]
POR_ID = {b["id"]: b for b in BLOQUES}


def _texto(rel):
    """El fichero como texto con los finales de linea normalizados a `\\n`."""
    ruta = os.path.join(ROOT, rel)
    assert os.path.isfile(ruta), f"{rel}: declarado en copias.json y NO existe"
    with open(ruta, encoding="utf-8") as fh:
        return fh.read().replace("\r\n", "\n")


def _lineas(rel):
    return _texto(rel).split("\n")


def _indice_linea(lineas, texto, desde=0):
    """Indice de la primera linea cuyo `strip()` es EXACTAMENTE `texto` (-1 si no hay ninguna).

    Igualdad de LINEA ENTERA, no prefijo (gap 7 de la revision R3 del tramo): con prefijo, un
    centinela nuevo que EXTIENDA a uno declarado (`... COMPARTIDO v2`) se colaba como si fuera el
    declarado. Por eso `copias.json` guarda la linea completa del centinela (tras `strip`).
    """
    for k in range(desde, len(lineas)):
        if lineas[k].strip() == texto:
            return k
    return -1


def _limites(rel, copia):
    """(i, j): linea del `inicio` (incluida) y linea del `fin` (excluida). Sin `fin`, j = i + 1."""
    lineas = _lineas(rel)
    i = _indice_linea(lineas, copia["inicio"])
    assert i >= 0, f"{rel}: ninguna linea es IGUAL al inicio declarado `{copia['inicio']}` (copias.json)"
    if not copia.get("fin"):
        return i, i + 1
    j = _indice_linea(lineas, copia["fin"], i + 1)
    assert j >= 0, f"{rel}: ninguna linea es IGUAL al fin declarado `{copia['fin']}` tras el inicio"
    return i, j


def _rango_copia(rel, copia):
    """(i, j) de `_limites` extendido hacia atras sobre las continuaciones de sentencia (`\\`).

    `_REVISION_HDR_FALLBACK = \\` vive en la linea ANTERIOR al literal declarado: es la misma
    sentencia de Python, asi que pertenece a la copia aunque el texto comparado empiece despues
    (el nombre difiere del canonico y por eso no entra en la comparacion byte a byte).
    """
    lineas = _lineas(rel)
    i, j = _limites(rel, copia)
    while i > 0 and lineas[i - 1].rstrip().endswith("\\"):
        i -= 1
    return i, j


RE_IDENTIFICADOR = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# Los rasgos del glob que el corpus de equivalencia TIENE que ejercitar, copiados LITERAL de
# `equivalencia.categorias` del bloque `glob_to_regex` de copias.json (gap R3-1 del intento 3).
#
# Por que una lista FIJA aqui y no solo la del registro: `categorias` era a la vez la regla y su
# propia medida. `test_el_corpus_de_equivalencia_cubre_todas_las_categorias` solo exige que cada
# categoria DECLARADA tenga entrada, asi que quitar la categoria del interrogante Y sus tres
# entradas (`"?"`, `"a?c"`, `"?*?"`) dejaba todo verde y el mutante `[^/]` -> `[^/]?` en los dos
# respaldos volvia a pasar: el corpus se seguia pudiendo podar, solo que borrando tambien la regla.
# Esta lista es el minimo IRREDUCIBLE y vive en el test, fuera del alcance de quien poda el
# registro: anadir categorias al registro es libre, quitar una de estas es rojo NOMBRANDOLA.
CATEGORIAS_OBLIGATORIAS = {
    "glob_to_regex": [
        "interrogante `?` (un caracter, sin cruzar `/`)",
        "`**` al INICIO del patron",
        "`**` EN MEDIO del patron",
        "`**` al FINAL del patron",
        "clase de caracteres `[...]`",
        "clase negada con `!` (`[!...]`)",
        "clase negada con `^` (`[^...]`)",
        "extension `*.ext`",
        "cadena VACIA",
        "`./` inicial (ruta relativa sin normalizar)",
        "`/` inicial (ancla de raiz)",
        "`/` final (directorio)",
        "espacios dentro de la ruta",
        "contrabarra `\\` (separador de Windows)",
        "metacaracter `.` a escapar",
        "metacaracter `+` a escapar",
        "metacaracteres `(` y `)` a escapar",
        "metacaracter `$` a escapar",
    ],
}


def _bloque(rel, copia, sustituir=True):
    """El texto declarado de una copia, con las `sustituciones` del registro ya aplicadas.

    Desde `inicio` (sin su sangria: cada copia puede tener la suya) hasta `fin` (excluido). Sin
    `fin`, la copia es de una sola linea.

    Las `sustituciones` se aplican con FRONTERA DE PALABRA (`\\b`), no con `str.replace`: son
    renombrados de identificador (el esquema lo exige, ver
    `test_el_registro_tiene_la_forma_que_dice_su_esquema`) y con reemplazo de subcadena un par
    arbitrario podia revertir una divergencia real de comportamiento antes de comparar (gap B-2
    del intento 2). De paso, `\\b` impide que un identificador que sea PREFIJO de otro se cuele.
    """
    src = _texto(rel)
    lineas = src.split("\n")
    i, j = _limites(rel, copia)
    off, acc = [], 0
    for l in lineas:
        off.append(acc)
        acc += len(l) + 1
    ini_ch = off[i] + len(lineas[i]) - len(lineas[i].lstrip())
    fin_ch = (off[j] + len(lineas[j]) - len(lineas[j].lstrip())) if copia.get("fin") \
        else off[i] + len(lineas[i])
    txt = src[ini_ch:fin_ch]
    if sustituir:
        for de, a in copia.get("sustituciones", []):
            txt = re.sub(r"\b" + re.escape(de) + r"\b", a, txt)
    return txt


def _modulo_aislado(rel, nombre):
    """El fichero cargado como modulo suelto (`spec_from_file_location`), sin tocar `sys.path`."""
    ruta = os.path.join(ROOT, rel)
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# --------------------------------------------------------------------------- esquema del registro

def test_el_registro_tiene_la_forma_que_dice_su_esquema():
    assert DATOS.get("version") == 1
    for clave in ("que_es", "comparacion", "delimitacion", "detecta"):
        assert DATOS.get(clave), f"copias.json: falta la clave `{clave}`"
    assert len(POR_ID) == len(BLOQUES), "copias.json: hay ids repetidos"
    for b in BLOQUES:
        assert b["id"] and b["mecanismo"] and b["que_es"], f"{b.get('id')}: campos obligatorios vacios"
        assert len(b["copias"]) >= 2, f"{b['id']}: una copia sola no es una copia"
        for c in b["copias"]:
            assert os.path.isfile(os.path.join(ROOT, c["ruta"])), f"{b['id']}: {c['ruta']} no existe"
            assert ("inicio" in c) != ("rango" in c), \
                f"{b['id']} / {c['ruta']}: declara `inicio` (bloque comparable) o `rango` (no-codigo), no ambos"
            # Una `sustitucion` es un RENOMBRADO DE IDENTIFICADOR y nada mas (gap B-2 del intento
            # 2): con pares de subcadena arbitrarios se podia declarar
            # `["strip()) > len(cerco)", "strip()) >= len(cerco)"]` y revertir una divergencia REAL
            # de comportamiento justo antes de comparar, dejando el test verde.
            for par in c.get("sustituciones", []):
                assert isinstance(par, list) and len(par) == 2, \
                    f"{b['id']} / {c['ruta']}: cada `sustitucion` es un par [de, a], no {par!r}"
                for lado in par:
                    assert isinstance(lado, str) and RE_IDENTIFICADOR.match(lado), (
                        f"{b['id']} / {c['ruta']}: la sustitucion {par!r} no es un renombrado de "
                        f"identificador: `{lado}` no casa `{RE_IDENTIFICADOR.pattern}`. Las "
                        f"sustituciones toleran renombrados locales, NO parches de texto que "
                        f"borren una divergencia de comportamiento antes de comparar")
            # Y el CONJUNTO de sustituciones de una copia tiene que ser un renombrado INYECTIVO
            # aplicado de una vez (gap R3-2 del intento 3). Con el par a par ya validado quedaban
            # dos formas de colar una tolerancia de mas:
            #   - COLAPSO: `[["_frontmatter_plegado", "_frontmatter"], ["_frontmatter_rapido",
            #     "_frontmatter"]]` funde dos identificadores DISTINTOS del bloque en uno solo, asi
            #     que una copia que llame al simbolo equivocado sale identica al canonico;
            #   - ENCADENADO: `[["a", "b"], ["b", "c"]]` se aplica en cascada (`a` -> `b` -> `c`),
            #     el resultado depende del ORDEN de la lista y acaba tambien en colapso (`a` y `b`
            #     terminan los dos en `c`), esta vez sin que se vea leyendo el registro.
            origenes = [de for de, _ in c.get("sustituciones", [])]
            destinos = [a for _, a in c.get("sustituciones", [])]
            assert len(set(destinos)) == len(destinos), (
                f"{b['id']} / {c['ruta']}: dos `sustituciones` apuntan al MISMO destino "
                f"({sorted(destinos)}): fundir dos identificadores distintos del bloque en uno "
                f"borra la diferencia entre ellos antes de comparar y deja la copia verde aunque "
                f"use el simbolo equivocado")
            encadenados = sorted(set(origenes) & set(destinos))
            assert not encadenados, (
                f"{b['id']} / {c['ruta']}: {encadenados} es a la vez ORIGEN y DESTINO de las "
                f"`sustituciones`: se aplican en cascada, el resultado depende del orden de la "
                f"lista y acaba colapsando identificadores distintos. Declara renombrados "
                f"independientes")


def test_el_canonico_de_cada_bloque_esta_entre_sus_copias_o_lo_declara():
    """El canonico manda; si NO es comparable byte a byte, el registro tiene que decir por que."""
    for b in CODIGO:
        rutas = [c["ruta"] for c in b["copias"]]
        if b.get("canonico_comparable") is False:
            assert b.get("motivo_canonico"), f"{b['id']}: `canonico_comparable: false` sin `motivo_canonico`"
            assert b["canonico"] not in rutas, f"{b['id']}: el canonico SI esta entre las copias comparadas"
            eq = b.get("equivalencia")
            assert eq and eq.get("funcion") and eq.get("cargador") and eq.get("corpus") \
                and eq.get("categorias"), \
                (f"{b['id']}: fuera de la comparacion byte a byte, el canonico necesita guardarrail "
                 f"CONDUCTUAL: `equivalencia` con `funcion`, `cargador`, `corpus` y las "
                 f"`categorias` obligatorias que ese corpus tiene que cubrir")
            for cat in eq["categorias"]:
                assert isinstance(cat, dict) and cat.get("nombre") and cat.get("regex"), \
                    f"{b['id']}: cada categoria de `equivalencia` es {{nombre, regex}}, no {cat!r}"
                re.compile(cat["regex"])
        else:
            assert b["canonico"] in rutas, f"{b['id']}: el canonico `{b['canonico']}` no esta entre las copias"


def test_las_sustituciones_declaradas_se_usan_de_verdad():
    """Una sustitucion que no aparece EN EL BLOQUE es una tolerancia muerta que tapa divergencias.

    Se busca dentro del rango declarado, no en todo el fichero (gap 11 de la revision R3): un `de`
    que solo aparezca en otra funcion del mismo script no guarda nada y deja pasar el renombrado.
    """
    for b in CODIGO:
        for c in b["copias"]:
            for de, a in c.get("sustituciones", []):
                assert de in _bloque(c["ruta"], c, sustituir=False), \
                    f"{b['id']} / {c['ruta']}: sustitucion `{de}` -> `{a}` sin uso DENTRO del bloque"


def test_cada_respaldo_declarado_esta_definido_en_su_copia():
    """`respaldos` silencia a `lint_plugin.py`: una entrada muerta seria un permiso en blanco.

    `respaldos` es POR COPIA (`copias[i].respaldos`), no por bloque (gap B-3 del intento 2): al
    declararlo en el bloque, la tolerancia se repartia a las N rutas y renombrar la constante
    CANONICA (`REVISION_HDR_PATTERN` de ledger-lint.py) a `_REVISION_HDR_FALLBACK` pasaba. Aqui se
    exige que cada nombre este DEFINIDO (`^NOMBRE =`) dentro del rango de SU PROPIA copia, y que
    ningun bloque siga declarando `respaldos` a nivel de bloque (donde ya nadie lo lee).
    """
    for b in CODIGO:
        assert "respaldos" not in b, (
            f"{b['id']}: `respaldos` va POR COPIA (`copias[i].respaldos`), no en el bloque: en el "
            f"bloque la tolerancia se reparte a rutas que NO definen la constante y `lint_plugin.py` "
            f"ya no lo lee de ahi, asi que seria una entrada muerta")
        for c in b["copias"]:
            for nombre in c.get("respaldos", []):
                rx = re.compile(r"^[ \t]*" + re.escape(nombre) + r"[ \t]*=", re.M)
                trozo = "\n".join(_lineas(c["ruta"])[slice(*_rango_copia(c["ruta"], c))])
                assert rx.search(trozo), (
                    f"{b['id']} / {c['ruta']}: el respaldo `{nombre}` NO esta definido dentro del "
                    f"rango de ESTA copia: entrada muerta en copias.json que silencia a "
                    f"lint_plugin.py en un fichero que no define la constante")


def test_cada_centinela_declarado_aparece_exactamente_una_vez_en_su_ruta():
    """Una SEGUNDA copia del bloque en un fichero ya declarado tiene que ser visible (gap B-4).

    El comparador se queda con la PRIMERA linea igual al `inicio`, asi que una copia divergida
    pegada mas abajo en el mismo fichero no la compara nadie; y el linter, si solo mira
    pertenencia, la da por declarada. Aqui la cuenta es exacta: uno y solo uno por ruta.
    """
    for b in CODIGO:
        for c in b["copias"]:
            lineas = _lineas(c["ruta"])
            for clave in ("inicio", "fin"):
                texto = c.get(clave)
                if not texto:
                    continue
                n = sum(1 for l in lineas if l.strip() == texto)
                assert n == 1, (
                    f"{b['id']} / {c['ruta']}: el centinela `{clave}` `{texto[:70]}` aparece {n} "
                    f"veces (se espera 1). Con mas de una, el bloque comparado es solo el primero "
                    f"y el resto son copias que no guarda nadie: quitalas o declaralas aparte")


# ------------------------------------------------------------------------------- identidad byte a byte

@pytest.mark.parametrize("bloque_id", IDS_CODIGO)
def test_las_copias_declaradas_son_identicas(bloque_id):
    b = POR_ID[bloque_id]
    textos = {c["ruta"]: _bloque(c["ruta"], c) for c in b["copias"]}
    assert all(t.strip() for t in textos.values()), f"{bloque_id}: alguna copia quedo vacia (centinelas mal puestos)"
    distintos = set(textos.values())
    if len(distintos) != 1:
        rutas = list(textos)
        ref = textos[rutas[0]]
        divergen = [r for r in rutas[1:] if textos[r] != ref]
        pytest.fail(f"el bloque `{bloque_id}` ha divergido entre {rutas[0]} y {', '.join(divergen)}: "
                    f"copialo LITERAL del canonico ({b['canonico']}) o actualiza agent-kits/shared/copias.json")


# --------------------------------------------------- equivalencia conductual con el canonico

IDS_EQUIVALENCIA = [b["id"] for b in BLOQUES if b.get("equivalencia")]


@pytest.mark.parametrize("bloque_id", IDS_EQUIVALENCIA)
def test_el_corpus_de_equivalencia_cubre_todas_las_categorias(bloque_id):
    """El corpus esta FIJADO POR CATEGORIAS, no por numero minimo (gap B-1 del intento 2).

    Con `len(corpus) >= 25` como unico requisito, el corpus se podia PODAR: borrando las tres
    entradas con `?` (`"?"`, `"a?c"`, `"?*?"`) quedaban 29 y el mutante `[^/]` -> `[^/]?` en los
    dos respaldos seguia verde. Como la equivalencia conductual es el UNICO guardarrail del
    canonico, podarla la desactiva sin nada rojo. Aqui cada rasgo del glob que el corpus tiene que
    ejercitar esta declarado en `equivalencia.categorias` y necesita AL MENOS UNA entrada: quitar
    la ultima de una categoria pone esto rojo NOMBRANDO la categoria que se ha quedado sin cubrir.
    """
    eq = POR_ID[bloque_id]["equivalencia"]
    corpus = eq["corpus"]
    huerfanas = [cat for cat in eq["categorias"]
                 if not any(re.search(cat["regex"], entrada) for entrada in corpus)]
    assert not huerfanas, (
        f"{bloque_id}: el corpus de `equivalencia` ({len(corpus)} entradas) ya no cubre "
        f"{len(huerfanas)} categoria(s) obligatoria(s) de copias.json: "
        + "; ".join(f"{cat['nombre']} (ninguna entrada casa `{cat['regex']}`)" for cat in huerfanas)
        + ". Repon una entrada de esa categoria: sin ella, un cambio semantico del canonico o de "
          "los dos respaldos en ese rasgo pasa sin nada rojo")


@pytest.mark.parametrize("bloque_id", sorted(CATEGORIAS_OBLIGATORIAS))
def test_las_categorias_obligatorias_siguen_declaradas_en_el_registro(bloque_id):
    """El minimo de categorias no lo decide el registro: lo decide esta lista (gap R3-1).

    Con la cobertura del corpus como unica puerta, podarlo seguia siendo posible en dos pasos:
    quitas la categoria de `copias.json` y, ya sin regla, quitas sus entradas del corpus. Todo
    verde, y el mutante que esa categoria vigilaba (`[^/]` -> `[^/]?` para el `?`) vuelve a pasar
    en los dos respaldos. Aqui los 18 nombres estan FIJOS en el test: el registro puede anadir
    categorias, nunca quitarlas.
    """
    b = POR_ID.get(bloque_id)
    assert b and b.get("equivalencia"), \
        f"{bloque_id}: el bloque con `equivalencia` ha desaparecido de copias.json"
    declaradas = {cat["nombre"] for cat in b["equivalencia"]["categorias"]}
    faltan = [n for n in CATEGORIAS_OBLIGATORIAS[bloque_id] if n not in declaradas]
    assert not faltan, (
        f"{bloque_id}: copias.json ya no declara {len(faltan)} categoria(s) OBLIGATORIA(S) de "
        f"`equivalencia.categorias`: " + "; ".join(f"`{n}`" for n in faltan)
        + ". Quitar una categoria desactiva el unico guardarrail del canonico para ese rasgo del "
          "glob y deja podar el corpus sin nada rojo: repon la categoria (y al menos una entrada "
          "suya en el corpus) o, si el rasgo de verdad ya no existe, quitala tambien de "
          "CATEGORIAS_OBLIGATORIAS en este test, diciendo por que")


def _funcion_del_bloque(mod, eq, monkeypatch):
    """La funcion definida DENTRO de los centinelas, no la que devuelve el cargador.

    Los respaldos con `canonico_comparable: false` viven en un cargador (`equivalencia.cargador`)
    que, si el canonico esta instalado, lo carga por `importlib` y DEVUELVE EL CANONICO. Llamarlo
    tal cual probaria el canonico N veces y el respaldo cero: ese fue justamente el gap 1 de la
    revision R3 (mutante semantico en los dos respaldos, 0 rojos). Aqui se le hace creer que el
    canonico no esta (`os.path.isfile` -> False solo durante la llamada), de modo que el simbolo
    que se ejecuta es la funcion local del bloque `--8<--`.
    """
    monkeypatch.setattr(os.path, "isfile", lambda p: False)
    try:
        return getattr(mod, eq["cargador"])()
    finally:
        monkeypatch.undo()


@pytest.mark.parametrize("bloque_id", IDS_EQUIVALENCIA)
def test_el_respaldo_es_equivalente_al_canonico(bloque_id, monkeypatch):
    """Guardarrail del canonico cuando la identidad byte a byte no es posible (`equivalencia`).

    Canonico y cada respaldo, cargados como modulos SUELTOS, tienen que compilar el MISMO patron
    para todo el corpus declarado en `copias.json`. Un cambio semantico en el canonico, en un
    respaldo o en los dos a la vez pone esto rojo.
    """
    b = POR_ID[bloque_id]
    eq = b["equivalencia"]
    corpus = eq["corpus"]
    canonico = getattr(_modulo_aislado(b["canonico"], f"canonico_{bloque_id}"), eq["funcion"])
    for k, c in enumerate(b["copias"]):
        mod = _modulo_aislado(c["ruta"], f"respaldo_{bloque_id}_{k}")
        local = _funcion_del_bloque(mod, eq, monkeypatch)
        # El simbolo ejecutado queda a la vista: `<cargador>.<locals>.<algo>` = la funcion anidada
        # del bloque. Si el cargador hubiera devuelto el canonico, el qualname seria el suyo.
        assert local.__qualname__.startswith(eq["cargador"] + ".<locals>."), (
            f"{bloque_id} / {c['ruta']}: el cargador devolvio `{local.__qualname__}` "
            f"(de {local.__module__}), no la funcion local del bloque `--8<--`")
        for patron in corpus:
            esperado, obtenido = canonico(patron).pattern, local(patron).pattern
            assert esperado == obtenido, (
                f"el respaldo `{eq['funcion']}` de {c['ruta']} NO es equivalente al canonico "
                f"({b['canonico']}) para el glob {patron!r}: canonico -> {esperado!r}, "
                f"respaldo -> {obtenido!r}. Copia la semantica del canonico o actualiza "
                f"agent-kits/shared/copias.json")


@pytest.mark.parametrize("bloque_id", IDS_NO_CODIGO)
def test_los_bloques_no_codigo_estan_declarados_pero_no_se_comparan(bloque_id):
    """Imports de stdlib y docstrings de convencion: coinciden por convencion, no por copia."""
    b = POR_ID[bloque_id]
    assert b.get("canonico") is None, f"{bloque_id}: un bloque no-codigo no tiene canonico"
    contiene = b.get("contiene") or []
    assert contiene, f"{bloque_id}: un bloque no-codigo declara `contiene` (que tiene que haber en el rango)"
    for c in b["copias"]:
        desde, hasta = (int(x) for x in c["rango"].split("-"))
        lineas = _texto(c["ruta"]).split("\n")
        assert 0 < desde <= hasta, f"{bloque_id} / {c['ruta']}: rango `{c['rango']}` invalido"
        assert hasta <= len(lineas), \
            f"{bloque_id} / {c['ruta']}: el rango `{c['rango']}` se sale del fichero"
        # El rango de un bloque no comparado deriva en silencio cuando el fichero crece (gap 2):
        # `contiene` es el ancla minima que dice que ahi sigue estando lo que el registro describe.
        trozo = "\n".join(lineas[desde - 1:hasta])
        for aguja in contiene:
            assert aguja in trozo, (
                f"{bloque_id} / {c['ruta']}: el rango `{c['rango']}` ya no contiene `{aguja}` "
                f"(el bloque se ha desplazado: corrige el rango en copias.json)")


# ------------------------------------------------------------------ los guardarrailes previos siguen

def test_los_tests_de_identidad_previos_no_se_han_borrado():
    """C-03 los ABSORBE en el registro, no los sustituye: seguian siendo la unica prueba de A."""
    previos = {
        "tests/test_console_encoding.py": "test_linter_y_suite_replican_el_mismo_bloque",
        "tests/test_knowledge_index.py": "test_los_tres_scripts_replican_el_mismo_bloque_de_celdas",
        "agent-kits/shared/test_task_brief.py": "_REVISION_HDR_FALLBACK",
        "skills/jira-sync/scripts/test_jira_flow.py": "_REVISION_HDR_FALLBACK",
    }
    for rel, marca in previos.items():
        assert marca in _texto(rel), f"{rel}: ha desaparecido `{marca}` (guardarrail previo borrado, no absorbido)"
