#!/usr/bin/env python3
"""Tablas de racionalización (activation-reliability T-03, patrón «iron law»).

Afirma, sobre los puntos críticos del plugin (`agents/implementer.md`, `skills/adversarial-review/SKILL.md`,
`agents/qa.md`, `agents/architect.md`, `skills/tdd/SKILL.md`), que la tabla existe con la cabecera EXACTA del fragmento compartido, tiene entre 6 y 8
filas en primera persona (entrecomilladas), cada fila con acción concreta, aparece ANTES del bloque
DoD/veredicto de la pieza y no excede las 25 líneas (token-diet); y que el fragmento
`agent-kits/shared/rationalization-table.md` existe y está inventariado en `agent-kits/shared/README.md`.

Ejecutar: python3 -m pytest -q tests/test_rationalization_tables.py  (o como script: python3 tests/test_rationalization_tables.py)
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CABECERA = "| Excusa que el modelo se da | Por qué no vale | Qué hacer en su lugar |"
SEPARADOR_RE = re.compile(r"^\|\s*-{3,}\s*\|\s*-{3,}\s*\|\s*-{3,}\s*\|$")
MIN_FILAS, MAX_FILAS, MAX_LINEAS = 6, 8, 25

# pieza → (fichero, heading del bloque DoD/veredicto ante el que debe ir la tabla)
PIEZAS = {
    "implementer": ("agents/implementer.md", "## ANTES DE CERRAR (DoD)"),
    "adversarial-review": ("skills/adversarial-review/SKILL.md", "### 6. Salida y traza"),
    "qa": ("agents/qa.md", "## ANTES DE CERRAR (DoD)"),
    "architect": ("agents/architect.md", "## ANTES DE CERRAR (DoD)"),
    "tdd": ("skills/tdd/SKILL.md", "## Salida y traza"),
}
FRAGMENTO = "agent-kits/shared/rationalization-table.md"


def leer(rel):
    return open(os.path.join(ROOT, rel), encoding="utf-8").read()


def tabla_de(texto):
    """(indice_linea_titulo, indice_linea_cabecera, filas) de la ÚNICA tabla con la cabecera exacta."""
    lineas = texto.splitlines()
    idx = [i for i, l in enumerate(lineas) if l.strip() == CABECERA]
    assert len(idx) == 1, f"esperaba exactamente 1 cabecera de tabla, hubo {len(idx)}"
    h = idx[0]
    assert SEPARADOR_RE.match(lineas[h + 1].strip()), f"separador de tabla inválido: {lineas[h+1]!r}"
    filas = []
    j = h + 2
    while j < len(lineas) and lineas[j].startswith("|"):
        filas.append(lineas[j])
        j += 1
    # título: el heading `##`/`###` más cercano por encima
    t = h
    while t > 0 and not lineas[t].startswith("#"):
        t -= 1
    return t, h, filas


def _check_pieza(nombre):
    rel, dod = PIEZAS[nombre]
    texto = leer(rel)
    t, h, filas = tabla_de(texto)
    lineas = texto.splitlines()
    assert MIN_FILAS <= len(filas) <= MAX_FILAS, f"{rel}: {len(filas)} filas (esperado {MIN_FILAS}-{MAX_FILAS})"
    for f in filas:
        celdas = [c.strip() for c in f.strip().strip("|").split("|")]
        assert len(celdas) == 3, f"{rel}: fila con {len(celdas)} celdas: {f!r}"
        excusa, por_que, accion = celdas
        assert excusa.startswith("«") and excusa.endswith("»"), f"{rel}: la excusa va entrecomillada en 1.ª persona: {excusa!r}"
        assert len(por_que) >= 20 and len(accion) >= 20, f"{rel}: celdas demasiado cortas: {f!r}"
    # posición: la tabla va ANTES del bloque DoD/veredicto, y ese bloque existe
    pos_dod = [i for i, l in enumerate(lineas) if l.startswith(dod)]
    assert pos_dod, f"{rel}: no encuentro el heading {dod!r}"
    assert h < pos_dod[0], f"{rel}: la tabla (línea {h+1}) debe ir ANTES de {dod!r} (línea {pos_dod[0]+1})"
    # token-diet: título → última fila ≤ 25 líneas
    ultima = h + 2 + len(filas)
    assert ultima - t <= MAX_LINEAS, f"{rel}: la tabla ocupa {ultima - t} líneas (> {MAX_LINEAS})"
    # referencia al fragmento compartido
    assert "rationalization-table.md" in texto, f"{rel}: debe remitir al fragmento compartido"
    return filas


def test_implementer_tiene_tabla_antes_del_dod():
    filas = _check_pieza("implementer")
    blob = " ".join(filas).lower()
    for clave in ("tests", "alcance", "ledger", "tdd"):
        assert clave in blob, f"implementer: la tabla no cubre «{clave}»"


def test_adversarial_review_tiene_tabla_del_revisor_antes_del_veredicto():
    filas = _check_pieza("adversarial-review")
    blob = " ".join(filas).lower()
    for clave in ("parece correcto", "estilo", "diff", "rebatido", "critical"):
        assert clave in blob, f"adversarial-review: la tabla no cubre «{clave}»"


def test_qa_tiene_tabla_antes_del_dod():
    filas = _check_pieza("qa")
    blob = " ".join(filas).lower()
    for clave in ("flaky", "umbral", "manual", "qa-gate.py"):
        assert clave in blob, f"qa: la tabla no cubre «{clave}»"


def test_architect_tiene_tabla_antes_del_dod():
    filas = _check_pieza("architect")
    blob = " ".join(filas).lower()
    for clave in ("opci", "valida", "adr", "ruta"):
        assert clave in blob, f"architect: la tabla no cubre «{clave}»"


def test_tdd_tiene_tabla_antes_de_la_salida():
    filas = _check_pieza("tdd")
    blob = " ".join(filas).lower()
    for clave in ("al final", "trivial", "ya pasaba", "assert true", "importerror"):
        assert clave in blob, f"tdd: la tabla no cubre «{clave}»"


def test_prosa_equivalente_no_duplicada():
    """Regla 5 del fragmento: una fila sustituye la prosa que decía lo mismo (una sola fuente)."""
    imp = leer("agents/implementer.md")
    assert "**Honesto con el estado:**" not in imp, "implementer: la regla en prosa se sustituyó por la fila de la tabla"
    qa = leer("agents/qa.md")
    assert "NO lo decides tú" not in qa, "qa: la prosa «no lo decides tú» se sustituyó por la fila de la tabla + el heading del DoD"
    assert qa.count("el veredicto lo da qa-gate") == 1, "qa: «el veredicto lo da qa-gate» solo en el heading del DoD"


def test_fragmento_compartido_existe_e_inventariado():
    frag = leer(FRAGMENTO)
    assert CABECERA in frag
    for regla in ("Máximo 8 filas", "Primera persona", "acción concreta", "JUSTO ANTES", "Sustituye prosa equivalente"):
        assert regla in frag, f"fragmento: falta la regla «{regla}»"
    readme = leer("agent-kits/shared/README.md")
    assert "`rationalization-table.md`" in readme and "Excusa que el modelo se da" in readme


def test_cabecera_del_fragmento_es_la_misma_que_en_las_piezas():
    for nombre, (rel, _dod) in PIEZAS.items():
        assert CABECERA in leer(rel), f"{rel}: sin la cabecera exacta"


def main():
    for fn in sorted(n for n in globals() if n.startswith("test_")):
        globals()[fn]()
    print(f"test_rationalization_tables: {len([n for n in globals() if n.startswith('test_')])} tests OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
