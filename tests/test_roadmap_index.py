#!/usr/bin/env python3
"""El índice `docs/roadmap/README.md` tiene una fila por iniciativa, y DENTRO de la tabla.

windows-console T-04 (IMPORTANT 7): la fila de `windows-console` se añadió al final del fichero,
DESPUÉS del párrafo `**Calibración:** …` y de una línea en blanco. En Markdown eso no forma tabla —
se renderiza como un párrafo con las barras crudas—, y la verificación que se declaró entonces
(`grep -c "windows-console" docs/roadmap/README.md` → 1) no podía detectarlo: contaba la cadena,
no su posición. Este test mira la POSICIÓN, que es lo que estaba roto.

Es deliberadamente barato: solo lee dos cosas del disco y no ejecuta nada.

Ejecutar: python3 -m pytest -q tests/test_roadmap_index.py
"""
import os
import re

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROADMAP = os.path.join(ROOT, "docs", "roadmap")
INDICE = os.path.join(ROADMAP, "README.md")

DIR_INICIATIVA = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9][a-z0-9-]*$")


def iniciativas():
    """Los directorios `docs/roadmap/<fecha>-<slug>/` que tienen `tasks.md`."""
    if not os.path.isdir(ROADMAP):
        return []
    return sorted(d for d in os.listdir(ROADMAP)
                  if DIR_INICIATIVA.match(d) and os.path.isfile(os.path.join(ROADMAP, d, "tasks.md")))


def tabla_y_cola(texto):
    """(filas DENTRO de la tabla, líneas de tipo fila que quedaron FUERA, tras cerrarse).

    La tabla es el bloque CONTIGUO de líneas que empiezan por `|` desde su cabecera. En Markdown
    basta una línea en blanco para cerrarla: lo que venga después con barras es texto, no tabla.
    """
    lineas = texto.split("\n")
    ini = next((i for i, l in enumerate(lineas) if l.startswith("| Fecha |")), None)
    if ini is None:
        return [], []
    fin = ini
    while fin < len(lineas) and lineas[fin].startswith("|"):
        fin += 1
    dentro = [l for l in lineas[ini + 2:fin]]          # sin cabecera ni separador `|---|`
    fuera = [l for l in lineas[fin:] if l.startswith("|")]
    return dentro, fuera


@pytest.fixture(scope="module")
def indice():
    if not os.path.isfile(INDICE):
        pytest.skip("no hay docs/roadmap/README.md")
    with open(INDICE, encoding="utf-8") as f:
        return tabla_y_cola(f.read())


def test_la_tabla_existe_y_tiene_filas(indice):
    dentro, _fuera = indice
    assert len(dentro) >= 10, f"esperaba la tabla de iniciativas, encontré {len(dentro)} filas"


def test_ninguna_fila_se_queda_fuera_de_la_tabla(indice):
    """Una fila tras el cierre de la tabla se renderiza como texto con las barras crudas."""
    _dentro, fuera = indice
    assert not fuera, (
        "hay líneas con forma de fila DESPUÉS de que la tabla se cierre (una línea en blanco la "
        "cierra en Markdown): se renderizarán como texto plano con las barras a la vista. "
        "Muévelas dentro de la tabla, en su sitio cronológico:\n  " + "\n  ".join(fuera))


@pytest.mark.parametrize("carpeta", iniciativas())
def test_cada_iniciativa_con_ledger_tiene_su_fila_dentro_de_la_tabla(carpeta, indice):
    dentro, fuera = indice
    enlace = f"({carpeta}/tasks.md)"
    assert not any(enlace in l for l in fuera), (
        f"la fila de «{carpeta}» está FUERA de la tabla (después de que se cierre): en Markdown no "
        f"se renderiza como fila. Muévela dentro, en su sitio cronológico.")
    assert any(enlace in l for l in dentro), (
        f"«{carpeta}» tiene tasks.md pero no aparece en la tabla de docs/roadmap/README.md — "
        f"añade su fila con el enlace `[tasks]({carpeta}/tasks.md)` (CONVENTIONS regla 7).")


def test_el_detector_pilla_la_fila_suelta():
    """La regla en sí, sin depender del estado del repo: fila tras el cierre → `fuera`."""
    bueno = ("| Fecha | Iniciativa |\n|---|---|\n| 2026-01-01 | a — x | [tasks](2026-01-01-a/tasks.md) |\n"
             "| 2026-01-02 | b — y | [tasks](2026-01-02-b/tasks.md) |\n\n**Calibración:** …\n")
    malo = ("| Fecha | Iniciativa |\n|---|---|\n| 2026-01-01 | a — x | [tasks](2026-01-01-a/tasks.md) |\n"
            "\n**Calibración:** …\n\n| 2026-01-02 | b — y | [tasks](2026-01-02-b/tasks.md) |\n")
    dentro, fuera = tabla_y_cola(bueno)
    assert len(dentro) == 2 and not fuera
    dentro, fuera = tabla_y_cola(malo)
    assert len(dentro) == 1 and len(fuera) == 1 and "2026-01-02-b" in fuera[0]
