#!/usr/bin/env python3
"""Las cifras de la doc contra la MEDICIÓN VIVA (cierre de los gaps del intento 2, T-07).

El problema que cierra: nueve cifras escritas a mano en la prosa de esta iniciativa no
reproducían (`mediana 354` donde son 350; «los mismos 13 ledgers (63 tareas)» encabezando una
tabla que suma 69; «de 274 a 66 caracteres» donde son 55; «12 de los 14 cerrados» donde son 13;
«los 24 tests nuevos» donde son 27; «las 28 formas» donde `ABREVIATURAS` tiene 26). Corregirlas a
mano garantiza una décima, porque la única fuente de cada cifra era la prosa.

MECANISMO (por qué este y no otro)
  Se eligió **marcar cada cifra verificable** en vez de concentrarlas en un sitio y que los demás
  enlacen, por tres razones medidas en este repo:
    1. La convención del repo es que la prosa AFIRME con la salida medida (`CONVENTIONS` regla 8:
       cada `Verificación` del ledger lleva salidas literales). Un mecanismo que prohibiera escribir
       el número y obligara a enlazar pelearía con esa regla, y dejaría un ADR que no dice su
       consecuencia.
    2. La duplicación es OBLIGATORIA en parte del corpus: `docs/CONVENTIONS.md` y su espejo EN
       tienen que decir lo mismo, así que «una sola copia» no es alcanzable ni deseable. El marcador
       hace la duplicación SEGURA en vez de prohibirla — y además permite comprobar que los dos
       espejos marcan las MISMAS claves.
    3. El marcador es un comentario HTML: invisible al renderizar, y localizable con `grep`.

LAS DOS FORMAS DEL MARCADOR (y ninguna más)
  `<!--m:clave=valor-->`             VIVA: «esto es lo que mide el script HOY». El test compara
                                     contra `changelog-sync.py --medicion` y exige que el número
                                     esté escrito en la prosa que precede al marcador.
  `<!--m@AAAA-MM-DD:clave=valor-->`  FECHADA: «esto es lo que se midió ESE día». No se compara
                                     contra la medición de hoy. El test exige que el valor esté en
                                     la prosa y —en un documento VIVO— que la FECHA también esté
                                     escrita en la prosa, donde la ve quien lee.

  La válvula antigua `<!--m?:motivo-->` está **retirada** (T-19, gaps B-6/B-10 de la revisión de
  R4b). Dos motivos medidos, no de gusto:
    · No tenía guarda de ubicación: congelar con ella 45 marcas vivas de `medicion-escalera.md`
      bajaba la suite de 191 a 75 comprobaciones **en verde y sin un aviso**. Un motivo en prosa no
      es una guarda; una fecha comprobable sí.
    · Perdía la clave. `<!--m?:historico medido el 2026-09-11-->` no dice QUÉ congela, así que nadie
      puede volver a medirlo ni saber si la prosa de al lado sigue siendo esa cifra.
  `test_la_valvula_m_interrogacion_esta_retirada` mantiene la retirada.

VIVO vs HISTÓRICO vs FECHADO (T-19, arista E11 de `docs/agents/CONTRACTS.md`)
  Un documento HISTÓRICO —un ADR, un ledger CERRADO, una entrada de `docs/knowledge/`— ya es una
  foto con fecha: lo que escribe es la medición **del día en que se decidió**, y volver a escribirla
  cada vez que el corpus se mueve no la hace más cierta, la falsifica. Ahí TODA marca es fechada, y
  la fecha vive en el marcador: la prosa histórica no se reescribe.
  Un documento VIVO (`skills/changelog-sync/**`, `docs/CONVENTIONS.md` y su espejo EN) se mantiene
  al día a propósito, así que ahí una cifra puede ser viva… **si es medible de forma estable**. Las
  que dependen del CORPUS COMPLETO (`ledgers_cerrados`, `tareas`, `changelog_mediana`…) se mueven al
  abrir o cerrar cualquier iniciativa: afirmarlas «hoy» pone la suite roja por prosa que nadie
  quería tocar (25 fallos medidos en el experimento de T-19). Esas van FECHADAS, y la fecha se
  escribe también en la prosa — que es la diferencia entre una foto y una afirmación caducada.
  `test_una_cifra_del_corpus_no_puede_marcarse_como_viva` impide volver atrás, y
  `test_no_hay_marcas_vivas_en_documentos_historicos` guarda la regla por UBICACIÓN.

Ejecuta: `python3 -m pytest -q tests/test_cifras_medidas.py` o `python3 tests/test_cifras_medidas.py`
"""
import glob
import importlib.util
import os
import re
import warnings

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "skills", "changelog-sync", "scripts", "changelog-sync.py")

# Ficheros donde vive alguna cifra de la escalera. Añadir uno aquí es la forma de meterlo en la
# puerta; una cifra en un fichero que no esté en la lista no la vigila nadie (limitación honesta:
# el test verifica lo MARCADO, no descubre copias sin marcar).
FICHEROS = [
    "skills/changelog-sync/references/medicion-escalera.md",
    "skills/changelog-sync/SKILL.md",
    "docs/knowledge/adr/ADR-012-resumen-del-changelog-lo-escribe-quien-cierra-la-tarea.md",
    "docs/knowledge/README.md",
    "docs/CONVENTIONS.md",
    "docs/en/CONVENTIONS.md",
    "docs/roadmap/2026-09-04-changelog-brief/tasks.md",
]
ESPEJOS = [("docs/CONVENTIONS.md", "docs/en/CONVENTIONS.md")]

# Claves que TIENEN que estar marcadas en algún sitio: si desaparece el marcador, la cifra se
# escaparía de la puerta sin que nada fallase. Son las que la revisión de dos lentes cazó mal.
COBERTURA_MINIMA = ("base_ledgers", "base_tareas", "ledgers_cerrados", "tareas",
                    "changelog_mediana", "bullet_max", "abreviaturas",
                    "placeholder_plantilla", "cerrados_con_cola", "resumen_max")

# Mínimo de comprobaciones VIVAS por fichero (gap B-6 de la revisión de R4b). Un umbral GLOBAL no
# sirve: `medicion-escalera.md` aporta el 90 % de las marcas, así que se pueden congelar 45 de sus
# comprobaciones sin que un mínimo global se entere. Estas cifras son las medidas hoy menos un
# margen corto: bajar de aquí es haber sacado comprobaciones de la puerta, y hay que justificarlo
# tocando esta tabla (que se ve en el diff) en vez de en silencio.
MINIMO_VIVAS_POR_FICHERO = {
    "skills/changelog-sync/references/medicion-escalera.md": 120,   # hoy 132
    "skills/changelog-sync/SKILL.md": 8,                            # hoy 9
    "docs/CONVENTIONS.md": 2,                                       # hoy 2
    "docs/en/CONVENTIONS.md": 2,                                    # hoy 2
}

# Claves que NO dependen del corpus completo y por eso pueden afirmarse en presente:
#   · las `base_*` miden el corpus BASE, congelado por `CORPUS_BASE_HASTA` en `changelog-sync.py`;
#   · estas siete son constantes del código (topes y tablas), no cuentas de ledgers.
CONSTANTES_DE_CODIGO = ("resumen_max", "resumen_frases_max", "archivos_max",
                        "archivos_max_tocados", "corte_min_palabras", "abreviaturas",
                        "placeholder_plantilla")

# Ubicaciones donde una marca VIVA (`m:`) es un error de clase: lo que se escribe ahí es
# histórico por naturaleza. Un ADR registra la medición del día en que se decidió; un ledger
# cerrado, la del día en que se cerró; un gotcha o una lección, la del día que costó el error.
# `docs/knowledge/**` entero, no solo `adr/`: el índice de la memoria se quedaba fuera (gap B-9).
GLOBS_HISTORICOS = ("docs/knowledge/**/*.md", "docs/roadmap/**/*.md")
# Excepción: el ledger de la iniciativa EN CURSO todavía se escribe, así que sus marcas pueden ser
# vivas mientras no se cierre. Se reconoce por su `estado:` de frontmatter, no por una lista de
# slugs que habría que mantener a mano — y la ausencia de `estado:` NO exime (gap B-9: 14 de los
# ledgers del repo no lo declaran y la guarda fallaba ABIERTA justo donde más marcas hay).
RE_ESTADO_ABIERTO = re.compile(r"^estado:\s*(borrador|en-progreso|aprobada|propuesta)\b", re.M)

RE_MARCA = re.compile(r"<!--m:([^>]*?)-->")
RE_FECHADA = re.compile(r"<!--m@(\d{4}-\d{2}-\d{2}):([^>]*?)-->")
RE_VALVULA_RETIRADA = re.compile(r"<!--m\?:([^>]*?)-->")
RE_PAR = re.compile(r"^([a-z0-9_]+)=(-?\d+)$")


def _medicion():
    spec = importlib.util.spec_from_file_location("changelog_sync_cifras", SCRIPT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.medicion(ROOT)


MEDIDO = _medicion()


# Ventana de texto ANTES del marcador donde se busca la cifra escrita. Es un párrafo, no una
# línea: la prosa va justificada a 100 columnas y el número casi nunca cae en la misma línea que
# el marcador.
VENTANA = 260
# La FECHA de una cifra fechada se busca en una ventana más larga, y no por comodidad: una tabla de
# cinco filas lleva la fecha UNA vez en la frase que la encabeza, y repetirla en cada fila la hace
# ilegible. 1.200 caracteres son, medidos en `medicion-escalera.md`, la distancia de la cabecera de
# la tabla más larga a su última fila, con margen.
VENTANA_FECHA = 1200


def es_clave_de_corpus(clave):
    """¿La cifra se mueve al abrir o cerrar CUALQUIER iniciativa?

    Es la pregunta que decide si una marca puede ser viva. `base_*` mide el corpus congelado y las
    de `CONSTANTES_DE_CODIGO` son topes del script: esas no se mueven. Todo lo demás cuenta ledgers
    o tareas del corpus de hoy, y afirmarlo en presente es prometer algo que caduca solo.
    """
    return not clave.startswith("base_") and clave not in CONSTANTES_DE_CODIGO


def en_tramo_de_codigo(texto, pos):
    """¿La posición cae dentro de un tramo de código en línea (acentos graves) de su propia línea?

    Documentar la FORMA del marcador es legítimo: la doc de este mecanismo, y la traza de la
    revisión que lo explica, escriben `<!--m:clave=valor-->` entre acentos graves como ejemplo.
    Contarlo como cifra a medir convierte la doc en imposible de escribir — el mismo patrón que
    `es_placeholder()` resuelve con `{{…}}`: una CITA no es una instancia. Se cuentan los acentos
    graves de la línea hasta `pos`: número impar → estamos dentro de un tramo abierto.
    """
    ini = texto.rfind("\n", 0, pos) + 1
    return texto.count("`", ini, pos) % 2 == 1


def _formas(valor):
    """El mismo número tal y como puede estar escrito en la prosa ES o EN (1944 · 1.944 · 1,944)."""
    return {str(valor), f"{valor:,}".replace(",", "."), f"{valor:,}"}


def _escrito_en(ctx, aguja):
    return re.search(rf"(?<!\d){re.escape(aguja)}(?!\d)", ctx) is not None


def _recorrer(patron, grupo_pares, ventana=VENTANA):
    out = []
    for rel in FICHEROS:
        p = os.path.join(ROOT, rel)
        if not os.path.isfile(p):
            continue
        texto = open(p, encoding="utf-8").read()
        for m in patron.finditer(texto):
            if en_tramo_de_codigo(texto, m.start()):
                continue     # marca CITADA para documentar la forma, no una cifra que medir
            linea = texto.count("\n", 0, m.start()) + 1
            ctx = texto[max(0, m.start() - ventana):m.start()]
            for par in m.group(grupo_pares).split(","):
                out.append((rel, linea, par.strip(), ctx, m))
    return out


def _marcas():
    """[(fichero, linea, `clave=valor`, contexto)] de todos los `<!--m:…-->` del corpus."""
    return [(r, n, p, c) for r, n, p, c, _m in _recorrer(RE_MARCA, 1)]


def _fechadas():
    """[(fichero, linea, fecha, `clave=valor`, contexto)] de los `<!--m@AAAA-MM-DD:…-->`."""
    return [(r, n, m.group(1), p, c) for r, n, p, c, m in _recorrer(RE_FECHADA, 2, VENTANA_FECHA)]


MARCAS = _marcas()
FECHADAS = _fechadas()


def _historicos_de_ficheros():
    """Los ficheros que caen en una ubicación histórica (ahí la fecha vive en el marcador y la
    prosa no se reescribe)."""
    hist = set()
    for patron in GLOBS_HISTORICOS:
        for p in glob.glob(os.path.join(ROOT, patron), recursive=True):
            hist.add(os.path.relpath(p, ROOT).replace(os.sep, "/"))
    return hist


HISTORICOS = _historicos_de_ficheros()


def test_hay_cifras_marcadas():
    """Sin esto, un `FICHEROS` mal escrito dejaría el test verde sin comprobar nada."""
    assert len(MARCAS) >= 40, f"solo {len(MARCAS)} cifras marcadas: ¿se ha vaciado el corpus?"


@pytest.mark.parametrize("rel,linea,par,ctx", MARCAS,
                         ids=[f"{r}:{n}:{p}" for r, n, p, _c in MARCAS])
def test_cada_cifra_marcada_es_la_que_mide_el_script(rel, linea, par, ctx):
    m = RE_PAR.match(par)
    assert m, f"{rel}:{linea}: marca mal formada «{par}» (forma: `<!--m:clave=valor-->`)"
    clave, valor = m.group(1), int(m.group(2))
    assert clave in MEDIDO, (f"{rel}:{linea}: la clave «{clave}» no la mide "
                             f"`changelog-sync.py --medicion` (¿errata?)")
    assert MEDIDO[clave] == valor, (f"{rel}:{linea}: la doc dice {clave} = {valor} y la medición "
                                    f"de hoy dice {MEDIDO[clave]} — corrige la prosa (o el código)")
    # …y la prosa dice de verdad ese número (con o sin separador de millares)
    assert any(_escrito_en(ctx, f) for f in _formas(valor)), (
        f"{rel}:{linea}: la marca dice {clave} = {valor} pero el texto que la precede no lo "
        f"escribe: «{ctx[-90:]}»")


@pytest.mark.parametrize("rel,linea,par,ctx", MARCAS,
                         ids=[f"{r}:{n}:{p}" for r, n, p, _c in MARCAS])
def test_una_cifra_del_corpus_no_puede_marcarse_como_viva(rel, linea, par, ctx):
    """T-19 / gap A-1 de R4b: la cifra que se mueve al abrir una iniciativa NO es una afirmación
    sobre hoy, es una foto — y tratarla como viva es lo que ponía la suite roja por prosa que nadie
    tocó. Se marca fechada, con su fecha escrita en la prosa."""
    clave = par.split("=")[0]
    assert not es_clave_de_corpus(clave), (
        f"{rel}:{linea}: «{clave}» depende del corpus completo y se mueve al abrir o cerrar "
        f"cualquier iniciativa: márcala fechada, `<!--m@AAAA-MM-DD:{par}-->`, y escribe la fecha "
        f"de medición en la prosa")


@pytest.mark.parametrize("rel,linea,fecha,par,ctx", FECHADAS,
                         ids=[f"{r}:{n}:{p}@{f}" for r, n, f, p, _c in FECHADAS])
def test_cada_cifra_fechada_dice_su_cifra_y_su_fecha(rel, linea, fecha, par, ctx):
    """Una cifra fechada no se compara contra hoy, así que su guarda es otra: que diga QUÉ congela
    (clave y valor, lo que la válvula `m?:` perdía) y que la prosa escriba ese número. En un
    documento VIVO, además, la FECHA tiene que estar en la prosa: es lo único que distingue una
    foto honesta de una cifra caducada, y quien lee la doc no ve los comentarios HTML."""
    m = RE_PAR.match(par)
    assert m, (f"{rel}:{linea}: marca fechada mal formada «{par}» "
               f"(forma: `<!--m@{fecha}:clave=valor-->`)")
    valor = int(m.group(2))
    assert any(_escrito_en(ctx, f) for f in _formas(valor)), (
        f"{rel}:{linea}: la marca fechada dice {par} pero el texto que la precede no escribe ese "
        f"número: «{ctx[-90:]}»")
    if rel not in HISTORICOS:
        assert fecha in ctx, (
            f"{rel}:{linea}: documento VIVO con cifra fechada {par}: escribe «{fecha}» en la prosa "
            f"(p. ej. «… (medido el {fecha})»), no solo en el marcador")


@pytest.mark.parametrize("clave", COBERTURA_MINIMA)
def test_las_cifras_que_la_revision_cazo_siguen_marcadas(clave):
    """Guarda contra el escape fácil: borrar el marcador saca la cifra de la puerta. Vale marcada
    viva o fechada — lo que no vale es que desaparezca."""
    todas = [p for _r, _n, p, _c in MARCAS] + [p for _r, _n, _f, p, _c in FECHADAS]
    assert any(p.startswith(f"{clave}=") for p in todas), \
        f"la cifra «{clave}» ya no está marcada en ningún fichero de FICHEROS"


@pytest.mark.parametrize("rel,minimo", sorted(MINIMO_VIVAS_POR_FICHERO.items()))
def test_cada_fichero_vivo_conserva_sus_comprobaciones(rel, minimo):
    """Gap B-6: el umbral GLOBAL es laxo por construcción. `medicion-escalera.md` aporta el 90 % de
    las marcas, así que se pueden congelar 45 de sus comprobaciones y seguir por encima de
    cualquier mínimo global. El mínimo va POR FICHERO."""
    vivas = sum(1 for r, _n, _p, _c in MARCAS if r == rel)
    assert vivas >= minimo, (
        f"{rel}: {vivas} comprobaciones vivas, por debajo del mínimo declarado ({minimo}). "
        f"Congelar marcas vivas apaga la puerta: si la bajada es legítima, baja el mínimo en "
        f"`MINIMO_VIVAS_POR_FICHERO` y justifícalo ahí")


@pytest.mark.parametrize("es,en", ESPEJOS, ids=[f"{a}|{b}" for a, b in ESPEJOS])
def test_los_espejos_marcan_las_mismas_cifras(es, en):
    """Regla de espejos: si el ES afirma una cifra, el EN afirma la misma. Comparar las CLAVES
    marcadas lo comprueba sin comparar traducciones — vivas y fechadas por separado, porque una
    cifra viva en un espejo y fechada en el otro también es un desacuerdo."""
    def claves(rel):
        if not os.path.isfile(os.path.join(ROOT, rel)):
            return []
        return sorted([f"m:{p.split('=')[0]}" for r, _n, p, _c in MARCAS if r == rel]
                      + [f"m@:{p.split('=')[0]}" for r, _n, _f, p, _c in FECHADAS if r == rel])
    assert claves(es) == claves(en), (f"{es} marca {claves(es)} y {en} marca {claves(en)}: "
                                      f"los espejos deben afirmar las mismas cifras")


def test_la_valvula_m_interrogacion_esta_retirada():
    """Gap B-6/B-10: `<!--m?:motivo-->` dejaba congelar una marca VIVA sin guarda ni aviso, y
    perdía la clave al hacerlo. La sustituye `<!--m@AAAA-MM-DD:clave=valor-->`, que dice qué
    congela y cuándo se midió. Este test impide que la válvula vuelva por la puerta de atrás."""
    quedan = []
    for rel in FICHEROS:
        p = os.path.join(ROOT, rel)
        if not os.path.isfile(p):
            continue
        texto = open(p, encoding="utf-8").read()
        for m in RE_VALVULA_RETIRADA.finditer(texto):
            if en_tramo_de_codigo(texto, m.start()):
                continue      # cita de la forma retirada al explicar por qué se retiró
            quedan.append(f"{rel}:{texto.count(chr(10), 0, m.start()) + 1}")
    assert not quedan, (
        "la válvula `<!--m?:…-->` está retirada (pierde la clave y no tiene guarda de ubicación): "
        "usa `<!--m@AAAA-MM-DD:clave=valor-->` en " + ", ".join(quedan))


def _historicos_con_marca_viva():
    """[(fichero, línea, marca)] de las marcas `m:` que viven donde solo caben fechadas."""
    out = []
    for rel in sorted(HISTORICOS):
        p = os.path.join(ROOT, rel)
        try:
            texto = open(p, encoding="utf-8").read()
        except (OSError, UnicodeDecodeError):
            continue
        if rel.startswith("docs/roadmap/") and RE_ESTADO_ABIERTO.search(texto):
            continue          # ledger todavía en curso: sus cifras aún pueden ser vivas
        for m in RE_MARCA.finditer(texto):
            if en_tramo_de_codigo(texto, m.start()):
                continue      # cita de la FORMA, no una cifra
            out.append((rel, texto.count("\n", 0, m.start()) + 1, m.group(1)))
    return out


def test_no_hay_marcas_vivas_en_documentos_historicos():
    """T-19 (arista E11): una marca `m:` en un ADR, en una entrada de `docs/knowledge/` o en un
    ledger CERRADO es histórica disfrazada de viva, y el precio de la confusión es que abrir o
    cerrar cualquier iniciativa pone la suite roja por prosa que nadie debería reescribir.

    Es **aviso**, no fallo, y a propósito: los ficheros de `docs/roadmap/**` son del proyecto que
    usa el plugin, no del plugin, y no queremos que un ledger ajeno tumbe la suite. Sobre el corpus
    de `FICHEROS` —que sí es nuestro— la exigencia es dura: ahí no puede quedar ninguna.

    La exención es solo para el ledger que declara un estado ABIERTO. Un ledger sin línea
    `estado:` NO se exime (gap B-9): eran 14 en este repo, justo los más viejos, y la guarda
    fallaba abierta exactamente donde más cifras congeladas hay.
    """
    hallazgos = _historicos_con_marca_viva()
    for rel, linea, marca in hallazgos:
        warnings.warn(
            f"{rel}:{linea}: marca VIVA `<!--m:{marca}-->` en un documento histórico. "
            f"Congélala: `<!--m@AAAA-MM-DD:{marca}-->` "
            f"(la cifra y su clave se conservan; deja de compararse contra la medición de hoy).",
            UserWarning, stacklevel=2)
    del_corpus = [h for h in hallazgos if h[0] in FICHEROS]
    assert not del_corpus, (
        "marcas vivas en documentos históricos DE ESTE REPO (congélalas con `m@`): "
        + ", ".join(f"{r}:{n}" for r, n, _m in del_corpus))


def main():
    return pytest.main([os.path.abspath(__file__), "-q"])


if __name__ == "__main__":
    import sys
    sys.exit(main())


def test_una_marca_CITADA_entre_acentos_graves_no_cuenta_como_cifra():
    """La doc del mecanismo tiene que poder escribir su propia forma (revisión, intento 3).

    La primera versión del test contaba cualquier `<!--m:…-->` del corpus, así que la traza de la
    revisión que documentaba la forma `clave=valor` se puso roja a sí misma:
    `FAILED …[tasks.md:453:clave=valor]`. Una marca entre acentos graves es una cita.
    """
    citada = "la forma es `<!--m:total=7-->` y se pone tras la cifra"
    real = "hay 7 tareas<!--m:total=7-->"
    assert en_tramo_de_codigo(citada, citada.index("<!--m:"))
    assert not en_tramo_de_codigo(real, real.index("<!--m:"))
    # y en un fichero de verdad: la propia traza de la revisión no aporta ni una marca
    de_la_traza = [x for x in MARCAS if x[2] == "clave=valor"]
    assert not de_la_traza, f"marca citada contada como cifra: {de_la_traza}"
