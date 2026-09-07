#!/usr/bin/env python3
"""El índice `docs/knowledge/README.md` es una BIYECCIÓN con los ficheros de `adr/`, `gotchas/` y
`lessons/`, y cada fila lleva «Área» (iniciativa `memory-retrieval`, T-04; spec CA-07).

Por qué existe (`analysis.md` §1.4-5, «la asimetría demostrable»): `tests/test_roadmap_index.py` vigila
el índice hermano del roadmap y el de memoria no lo vigilaba nada. Una entrada SIN FILA es invisible
para el único camino de lectura —el índice— y no hay grep de respaldo; y para los ADR el `area` SOLO
vive en la fila: perder la fila es perder el enrutado sin poder reconstruirlo.

El criterio es UNO y vive en `scripts/lint_plugin.py` (`lint_knowledge_index`: ERROR, no aviso — una
entrada sin fila rompe la única puerta de entrada); este test lo importa por ruta y (a) lo afirma sobre
el repo de hoy, (b) lo prueba con MUTACIONES sobre un corpus sintético y sobre una copia del real, para
demostrar que caza cada caso nombrando el fichero o el ID. Es deliberadamente barato: no ejecuta nada,
solo lee el índice y lista tres carpetas (como su hermano).

Ejecutar: python3 -m pytest -q tests/test_knowledge_index.py
"""
import importlib.util
import os
import re
import shutil

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KNOWLEDGE = os.path.join(ROOT, "docs", "knowledge")
INDICE = os.path.join(KNOWLEDGE, "README.md")
CARPETAS = ("adr", "gotchas", "lessons")


def _linter():
    spec = importlib.util.spec_from_file_location("lint_plugin_knowledge", os.path.join(ROOT, "scripts", "lint_plugin.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


lp = _linter()


def ficheros(base):
    out = []
    for c in CARPETAS:
        d = os.path.join(base, c)
        if os.path.isdir(d):
            out += [f"{c}/{f}" for f in sorted(os.listdir(d)) if f.endswith(".md") and f.lower() != "readme.md"]
    return out


# --------------------------------------------------------------- el repo de hoy

@pytest.fixture(scope="module")
def real():
    if not os.path.isfile(INDICE):
        pytest.skip("no hay docs/knowledge/README.md")
    return ROOT


def test_el_indice_real_es_biyectivo_y_toda_fila_tiene_area(real):
    errores = lp.lint_knowledge_index(real)
    assert errores == [], "\n".join(errores)


def test_las_cifras_del_corpus_de_hoy(real):
    """32 ficheros ↔ 32 filas (la spec decía 31: `GOT-006` entró el 2026-09-04, después del análisis)."""
    filas, fuera = lp.filas_knowledge_index(open(INDICE, encoding="utf-8").read())
    fs = ficheros(KNOWLEDGE)
    assert not fuera
    assert len(filas) == len(fs) >= 31
    assert sorted(f["ruta"] for f in filas) == fs
    assert all(f["area"] for f in filas)
    assert all(f["id"] and re.match(r"^(ADR|GOT|LES)-\d{3}$", f["id"]) for f in filas)


def test_para_los_adr_el_area_solo_vive_en_el_indice(real):
    """Es el motivo de la regla: si la fila se pierde, el `area` de un ADR no se puede reconstruir."""
    adrs = [f for f in ficheros(KNOWLEDGE) if f.startswith("adr/")]
    assert adrs
    for rel in adrs:
        cabecera = open(os.path.join(KNOWLEDGE, rel), encoding="utf-8").read().split("\n---", 2)[0]
        assert not re.search(r"^area:", cabecera, re.M), f"{rel} ya trae `area:` en el frontmatter; revisa el docstring"


# --------------------------------------------------------------- corpus sintético + mutaciones

FILA = "| [`{ruta}`]({ruta}) — {titular} | {id} | {tipo} | {area} | aceptada | `x/tasks.md` |"
CABECERA = "# índice\n\nprosa | con barra\n\n## Índice\n\n| Entrada | ID | Tipo | Área | Estado | Fuente |\n|---|---|---|---|---|---|\n"


def _corpus(tmp_path, filas, ficheros_extra=()):
    kn = tmp_path / "docs" / "knowledge"
    for rel in ("adr/ADR-001-a.md", "gotchas/GOT-001-g.md", "lessons/LES-001-evaluator-l.md", *ficheros_extra):
        p = kn / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f"---\nid: {rel.split('/')[1][:7]}\nestado: aceptada\n---\n# x\n", encoding="utf-8")
    (kn / "README.md").write_text(CABECERA + "\n".join(filas) + "\n\nCola.\n", encoding="utf-8")
    return str(tmp_path)


FILAS_OK = [
    FILA.format(ruta="adr/ADR-001-a.md", titular="a", id="ADR-001", tipo="ADR", area="Hooks / implementer"),
    FILA.format(ruta="gotchas/GOT-001-g.md", titular="g", id="GOT-001", tipo="Gotcha", area="Tests / CI"),
    FILA.format(ruta="lessons/LES-001-evaluator-l.md", titular="l", id="LES-001", tipo="Lección", area="Estimación / calibración"),
]


def test_el_corpus_sintetico_correcto_no_da_errores(tmp_path):
    assert lp.lint_knowledge_index(_corpus(tmp_path, FILAS_OK)) == []


def test_una_entrada_sin_fila_falla_nombrando_el_fichero(tmp_path):
    errores = lp.lint_knowledge_index(_corpus(tmp_path, FILAS_OK[:2]))
    assert len(errores) == 1 and "lessons/LES-001-evaluator-l.md" in errores[0] and "sin fila" in errores[0], errores


def test_una_fila_sin_area_falla_nombrando_el_id(tmp_path):
    filas = FILAS_OK[:2] + [FILA.format(ruta="lessons/LES-001-evaluator-l.md", titular="l", id="LES-001", tipo="Lección", area="")]
    errores = lp.lint_knowledge_index(_corpus(tmp_path, filas))
    assert len(errores) == 1 and "LES-001" in errores[0] and "Área" in errores[0], errores


def test_una_fila_que_apunta_a_un_fichero_inexistente_falla(tmp_path):
    """La biyección va en los dos sentidos."""
    filas = FILAS_OK + [FILA.format(ruta="adr/ADR-002-fantasma.md", titular="f", id="ADR-002", tipo="ADR", area="Roles")]
    errores = lp.lint_knowledge_index(_corpus(tmp_path, filas))
    assert len(errores) == 1 and "adr/ADR-002-fantasma.md" in errores[0] and "ADR-002" in errores[0], errores


def test_una_fila_fuera_de_la_tabla_falla_como_en_el_indice_del_roadmap(tmp_path):
    """Una línea en blanco cierra la tabla en Markdown: la fila de después es texto con barras (T-04 de
    windows-console lo sufrió en el índice hermano)."""
    filas = FILAS_OK[:2] + ["", "**Nota.**", "", FILAS_OK[2]]
    errores = lp.lint_knowledge_index(_corpus(tmp_path, filas))
    assert any("fuera de la tabla" in e and "LES-001" in e for e in errores), errores


def test_un_id_o_una_ruta_repetidos_fallan(tmp_path):
    errores = lp.lint_knowledge_index(_corpus(tmp_path, FILAS_OK + [FILAS_OK[0]]))
    assert any("repetid" in e and "ADR-001" in e for e in errores), errores


def test_sin_docs_knowledge_no_hay_nada_que_vigilar(tmp_path):
    assert lp.lint_knowledge_index(str(tmp_path)) == []


def test_entradas_sin_indice_es_un_error_no_un_silencio(tmp_path):
    root = _corpus(tmp_path, FILAS_OK)
    os.unlink(os.path.join(root, "docs", "knowledge", "README.md"))
    errores = lp.lint_knowledge_index(root)
    assert len(errores) == 1 and "README.md" in errores[0], errores


# --------------------------------------------------------------- mutaciones sobre una COPIA del corpus real

@pytest.fixture
def copia_real(tmp_path, real):
    dst = tmp_path / "docs" / "knowledge"
    shutil.copytree(KNOWLEDGE, dst, ignore=shutil.ignore_patterns("journal"))
    return tmp_path


def test_quitar_una_fila_del_indice_real_pone_rojo_nombrando_el_fichero(copia_real):
    idx = copia_real / "docs" / "knowledge" / "README.md"
    lineas = idx.read_text(encoding="utf-8").split("\n")
    victima = next(l for l in lineas if "| ADR-007 |" in l)
    idx.write_text("\n".join(l for l in lineas if l != victima), encoding="utf-8")
    errores = lp.lint_knowledge_index(str(copia_real))
    assert len(errores) == 1 and "adr/ADR-007-deny-solo-con-alcance-de-agente.md" in errores[0], errores


def test_vaciar_el_area_de_una_fila_real_pone_rojo_nombrando_el_id(copia_real):
    idx = copia_real / "docs" / "knowledge" / "README.md"
    texto = idx.read_text(encoding="utf-8")
    assert "| GOT-005 | Gotcha | Scripts / consola y codificación |" in texto
    idx.write_text(texto.replace("| GOT-005 | Gotcha | Scripts / consola y codificación |", "| GOT-005 | Gotcha |  |"), encoding="utf-8")
    errores = lp.lint_knowledge_index(str(copia_real))
    assert len(errores) == 1 and "GOT-005" in errores[0] and "Área" in errores[0], errores
