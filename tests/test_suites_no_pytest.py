#!/usr/bin/env python3
"""La puerta LOCAL es la misma que la de CI (cierre de los gaps del intento 2, T-07).

El hueco que cierra, medido con `pytest --collect-only`:

  · **8 de los 18 `tests/test_*.py` no tienen ni una función `def test_*`** (son scripts con
    `main()`): `test_coverage_check`, `test_dashboard`, `test_ledger_lint`, `test_lint_plugin`,
    `test_mermaid_blocks`, `test_qa_gate`, `test_readme_badges` y `test_worklog`. `pytest -q` los
    IGNORA («no tests collected»), así que sus casos no eran puerta local: se verificó que quitar la
    continuación indentada o el aviso de placeholder de `agent-kits/shared/ledger-lint.py` dejaba
    `python3 -m pytest -q` en VERDE. Solo corrían por el bucle de `ci.yml`.
  · Y al revés: el paso pytest de `ci.yml` listaba carpetas (`agent-kits/shared`, `skills/*/scripts`,
    `evals`) y **no `tests`**, mientras que el bucle ejecuta `python tests/test_X.py` — que en los
    tres ficheros SIN bloque `__main__` (`test_export_skills`, `test_release`,
    `test_roadmap_index`) no ejecuta NADA. Esos 68 casos no corrían en CI en absoluto.

Los dos lados se arreglan sin duplicar ningún caso:
  · aquí: un test de pytest por suite-script, que la ejecuta como subproceso y exige exit 0. Así
    `pytest -q` cubre lo que cubre el bucle de CI.
  · en `ci.yml`: se añade `tests` a las carpetas del paso pytest. Así CI cubre lo que cubre
    `pytest -q`. El bucle se deja intacto (es la vía por la que estas suites imprimen su propio
    resumen, y no molesta que se ejecuten dos veces).

La lista NO es fija: se descubre con AST cada vez, así que un `tests/test_*.py` nuevo entra solo —
igual que el bucle de `ci.yml`, y por el mismo motivo.
"""
import ast
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TESTS = os.path.join(ROOT, "tests")
YO = os.path.basename(os.path.abspath(__file__))


def _tiene_funciones_test(path):
    """¿pytest recogería algo de este fichero? (`def test_*` a nivel de módulo o en una `class
    Test*`). Se usa AST, no pytest, para no depender de la versión ni de la configuración."""
    try:
        arbol = ast.parse(open(path, encoding="utf-8").read())
    except (OSError, SyntaxError):
        return True          # ilegible: que lo cace el paso de sintaxis, no este test
    # `ast.walk` y no solo `arbol.body`: hay suites que definen sus `def test_*` DENTRO de un
    # `if pytest:` (para poder ejecutarse también como script sin pytest instalado), y pytest las
    # recoge igual. Mirar solo el nivel superior las daba por «no recogidas» y las habría
    # ejecutado dos veces.
    for n in ast.walk(arbol):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("test"):
            return True
    return False


def suites_no_pytest():
    """[nombre de fichero] de los `tests/test_*.py` que pytest NO recoge (mismo orden que el
    bucle de `ci.yml`: `sorted`)."""
    if not os.path.isdir(TESTS):
        return []
    return [f for f in sorted(os.listdir(TESTS))
            if f.startswith("test_") and f.endswith(".py") and f != YO
            and not _tiene_funciones_test(os.path.join(TESTS, f))]


SUITES = suites_no_pytest()


def test_hay_suites_que_pytest_no_recoge():
    """Si algún día no queda ninguna (todas convertidas a pytest), este test lo dice en vez de
    quedarse verde sin comprobar nada."""
    assert SUITES, ("ningún tests/test_*.py sin funciones `test_*`: si se han convertido todas, "
                    "borra este fichero y quita `tests` de nada — pero dilo, no lo dejes verde")


@pytest.mark.parametrize("nombre", SUITES)
def test_la_suite_script_pasa(nombre):
    """Ejecuta la suite tal y como la ejecuta el bucle de `ci.yml` (`python <fichero>`) y exige
    exit 0. No duplica sus casos: los ejecuta una vez, en el sitio donde antes no corrían."""
    r = subprocess.run([sys.executable, os.path.join(TESTS, nombre)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       cwd=ROOT)
    assert r.returncode == 0, (f"{nombre} → exit {r.returncode}\n"
                               f"--- stdout ---\n{r.stdout[-4000:]}\n"
                               f"--- stderr ---\n{r.stderr[-4000:]}")


def test_el_paso_pytest_de_ci_incluye_la_carpeta_tests():
    """El otro lado del hueco: los `tests/test_*.py` que pytest SÍ recoge y que NO tienen bloque
    `__main__` no corrían en CI en absoluto (el bucle los ejecuta como script y no hacen nada).
    Se arregla incluyendo `tests` en el paso pytest de `ci.yml`; este test lo fija."""
    p = os.path.join(ROOT, "ci.yml.MANUAL-COPY")
    if not os.path.isfile(p):
        pytest.skip("sin ci.yml.MANUAL-COPY")
    yml = open(p, encoding="utf-8").read()
    linea = next((l for l in yml.split("\n") if "python -m pytest" in l), "")
    assert linea, "el paso pytest de ci.yml no se reconoce: actualiza este test"
    assert " tests " in linea or linea.rstrip().endswith(" tests -q") or " tests" in linea, linea
    sin_main = [f for f in sorted(os.listdir(TESTS))
                if f.startswith("test_") and f.endswith(".py")
                and "__main__" not in open(os.path.join(TESTS, f), encoding="utf-8").read()]
    assert sin_main, "todos los tests/ tienen bloque __main__: revisa este test"


def main():
    return pytest.main([os.path.abspath(__file__), "-q"])


if __name__ == "__main__":
    sys.exit(main())
