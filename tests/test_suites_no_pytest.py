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


def _yml_ci():
    p = os.path.join(ROOT, "ci.yml.MANUAL-COPY")
    if not os.path.isfile(p):
        pytest.skip("sin ci.yml.MANUAL-COPY")
    return open(p, encoding="utf-8").read()


def test_el_bucle_de_ci_solo_ejecuta_lo_que_pytest_no_recoge():
    """T-23 (plugin-audit-2): el bucle `for t in ...; python "$t"` ejecutaba los ~23 `tests/test_*.py`
    que pytest YA recoge (los corría dos veces). Ahora su lista sale de `grep -L` sobre `def test`:
    el mismo criterio que `suites_no_pytest()` (AST), comprobado fichero a fichero."""
    import re
    yml = _yml_ci()
    m = re.search(r"for t in (.+?); do", yml)
    assert m, "el bucle de tests/ del ci.yml no se reconoce: actualiza este test"
    lista = m.group(1)
    assert "grep -L" in lista, f"el bucle itera todo tests/test_*.py: {lista}"
    patron = re.search(r"grep -LE? ?(?:-E )?'([^']+)'", lista)
    assert patron, f"el filtro del bucle no se reconoce: {lista}"
    rx = re.compile(patron.group(1), re.M)
    sin_def = [f for f in sorted(os.listdir(TESTS))
               if f.startswith("test_") and f.endswith(".py")
               and not rx.search(open(os.path.join(TESTS, f), encoding="utf-8").read())]
    assert sin_def == SUITES, (sin_def, SUITES)


def test_la_ci_paraleliza_pytest_y_publica_durations():
    """T-23: `pytest-xdist` instalado, `-n auto` y `--durations` en el paso pytest de la CI."""
    yml = _yml_ci()
    assert "pytest-xdist" in yml, "falta `pip install pytest-xdist` en la CI"
    linea = next((l for l in yml.splitlines() if "python -m pytest" in l), "")
    assert "-n auto" in linea, linea
    assert "--durations" in linea, linea


def test_los_tests_de_tiempo_van_en_un_paso_serie_aparte():
    """T-23: `-n auto` reparte los tests entre núcleos y los de TIEMPO de pared (`< 1.5 s`) o de marca de
    fichero fallan por la carga ajena (medido en Linux, 4 CPU: 3 fallos en la suite completa). Esos tests
    llevan `@pytest.mark.serie`: el paso paralelo los excluye y un paso aparte los ejecuta SIN xdist."""
    yml = _yml_ci()
    lineas = [l for l in yml.splitlines() if "python -m pytest" in l]
    paralela = [l for l in lineas if "-n auto" in l]
    serie = [l for l in lineas if "-m serie" in l]
    assert len(paralela) == 1 and "-m \"not serie\"" in paralela[0], lineas
    assert len(serie) == 1 and "-n " not in serie[0], lineas
    marcados = []
    for carpeta in ("tests", os.path.join("agent-kits", "shared")):
        base = os.path.join(ROOT, carpeta)
        for f in sorted(os.listdir(base)):
            if f.startswith("test_") and f.endswith(".py") and "pytest.mark.serie" in open(
                    os.path.join(base, f), encoding="utf-8").read():
                marcados.append(f)
    esperados = {"test_redact_fix3.py", "test_redact.py", "test_plan_review_summary.py", "test_bench_session_end.py",
                 "test_agent_activity_store.py"}
    assert esperados <= set(marcados), (esperados - set(marcados), marcados)
    ini = open(os.path.join(ROOT, "pytest.ini"), encoding="utf-8").read() if os.path.isfile(
        os.path.join(ROOT, "pytest.ini")) else ""
    assert "serie:" in ini, "falta registrar el marcador `serie` en pytest.ini"


def main():
    return pytest.main([os.path.abspath(__file__), "-q"])


if __name__ == "__main__":
    sys.exit(main())
