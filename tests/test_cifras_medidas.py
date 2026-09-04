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

  Forma: `<!--m:clave=valor-->` (una o varias claves separadas por comas) justo después de la
  cifra. El test comprueba DOS cosas por marcador: que `valor` es lo que mide el script HOY, y que
  ese `valor` aparece literalmente en el texto que precede al marcador (para que no se pueda
  actualizar el marcador dejando la prosa vieja). Una cifra que NO es medible de forma determinista
  —un RED histórico, el «antes» medido con el script de `a7a11b0`, que en un clon superficial de CI
  no existe— se marca `<!--m?:motivo-->` y el test exige el motivo, en vez de fingir que reproduce.

Ejecuta: `python3 -m pytest -q tests/test_cifras_medidas.py` o `python3 tests/test_cifras_medidas.py`
"""
import importlib.util
import os
import re

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

RE_MARCA = re.compile(r"<!--m:([^>]*?)-->")
RE_NO_VERIFICABLE = re.compile(r"<!--m\?:([^>]*?)-->")
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


def _marcas():
    """[(fichero, linea, `clave=valor`, contexto)] de todos los `<!--m:…-->` del corpus."""
    out = []
    for rel in FICHEROS:
        p = os.path.join(ROOT, rel)
        if not os.path.isfile(p):
            continue
        texto = open(p, encoding="utf-8").read()
        for m in RE_MARCA.finditer(texto):
            if en_tramo_de_codigo(texto, m.start()):
                continue     # marca CITADA para documentar la forma, no una cifra que medir
            linea = texto.count("\n", 0, m.start()) + 1
            ctx = texto[max(0, m.start() - VENTANA):m.start()]
            for par in m.group(1).split(","):
                out.append((rel, linea, par.strip(), ctx))
    return out


MARCAS = _marcas()


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
    formas = {str(valor), f"{valor:,}".replace(",", ".")}
    assert any(re.search(rf"(?<!\d){re.escape(f)}(?!\d)", ctx) for f in formas), (
        f"{rel}:{linea}: la marca dice {clave} = {valor} pero el texto que la precede no lo "
        f"escribe: «{ctx[-90:]}»")


def test_las_cifras_no_verificables_declaran_su_motivo():
    """Una cifra histórica (medida con el script de `a7a11b0`, o un RED de un commit anterior) no
    se puede re-medir en un clon superficial: se marca como NO verificable CON motivo, en vez de
    fingir que reproduce."""
    vistas = 0
    for rel in FICHEROS:
        p = os.path.join(ROOT, rel)
        if not os.path.isfile(p):
            continue
        texto = open(p, encoding="utf-8").read()
        for m in RE_NO_VERIFICABLE.finditer(texto):
            n = texto.count("\n", 0, m.start()) + 1
            motivo = m.group(1).strip()
            assert len(motivo) >= 12, f"{rel}:{n}: `m?` sin motivo utilizable («{motivo}»)"
            assert not RE_PAR.match(motivo), \
                f"{rel}:{n}: `m?` con forma de clave=valor: si es medible, márcala con `m:`"
            vistas += 1
    assert vistas, "ninguna cifra marcada como no verificable: ¿se han borrado las marcas `m?`?"


@pytest.mark.parametrize("clave", COBERTURA_MINIMA)
def test_las_cifras_que_la_revision_cazo_siguen_marcadas(clave):
    """Guarda contra el escape fácil: borrar el marcador saca la cifra de la puerta."""
    assert any(p.startswith(f"{clave}=") for _r, _n, p, _c in MARCAS), \
        f"la cifra «{clave}» ya no está marcada en ningún fichero de FICHEROS"


@pytest.mark.parametrize("es,en", ESPEJOS, ids=[f"{a}|{b}" for a, b in ESPEJOS])
def test_los_espejos_marcan_las_mismas_cifras(es, en):
    """Regla de espejos: si el ES afirma una cifra, el EN afirma la misma. Comparar las CLAVES
    marcadas lo comprueba sin comparar traducciones."""
    def claves(rel):
        p = os.path.join(ROOT, rel)
        return sorted(par.strip().split("=")[0]
                      for _r, _n, par, _c in MARCAS if _r == rel) if os.path.isfile(p) else []
    assert claves(es) == claves(en), (f"{es} marca {claves(es)} y {en} marca {claves(en)}: "
                                      f"los espejos deben afirmar las mismas cifras")


def main():
    import sys
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
