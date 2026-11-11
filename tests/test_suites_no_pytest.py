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
    `pytest -q` cubre lo que cubre la CI.
  · en `ci.yml`: se añade `tests` a las carpetas del paso pytest. Así CI cubre lo que cubre
    `pytest -q`. Desde T-23 fix1 el bucle `for t in …; python "$t"` YA NO EXISTE: pytest es el único
    ejecutor (antes las suites-script corrían dos veces, y las suites mixtas perdían su `main()`).

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


# ── T-23 fix1 (gap 1): las suites MIXTAS (tienen algún `def test_*` Y casos que solo cuelgan de
# `if __name__ == "__main__"`) no pueden dejar casos fuera de pytest ───────────────────────────────
import glob


def _llamadas(nodo):
    return {c.func.id for c in ast.walk(nodo)
            if isinstance(c, ast.Call) and isinstance(c.func, ast.Name)}


def casos_solo_desde_main(codigo):
    """Funciones NO `test*` con `assert` propio que se alcanzan desde el bloque `__main__` y desde
    ninguna función `test*`. Si el fichero no tiene `def test*` devuelve []: de esas suites-script se
    ocupa `test_la_suite_script_pasa`. Cada nombre devuelto es un caso que pytest NO ejecuta."""
    arbol = ast.parse(codigo)
    fns = {n.name: n for n in ast.walk(arbol)
           if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    tests = {n for n in fns if n.startswith("test")}
    if not tests:
        return []
    guardas = [n for n in arbol.body if isinstance(n, ast.If) and "__main__" in ast.dump(n.test)]

    def alcanza(inicio):
        vistos, pend = set(), list(inicio)
        while pend:
            x = pend.pop()
            if x in vistos or x not in fns:
                continue
            vistos.add(x)
            pend += _llamadas(fns[x])
        return vistos

    desde_main = alcanza(set().union(*[_llamadas(g) for g in guardas]) if guardas else set())
    desde_test = alcanza(tests)
    return sorted(f for f in desde_main - desde_test if not f.startswith("test")
                  and any(isinstance(a, ast.Assert) for a in ast.walk(fns[f])))


def _ficheros_de_la_ci():
    """Los `test_*.py` de las carpetas del paso pytest de `ci.yml` (las mismas que lista la CI)."""
    carpetas = (["tests", os.path.join("agent-kits", "shared"), os.path.join("agent-kits", "knowledge-curator"),
                 "evals"] + [os.path.relpath(d, ROOT) for d in sorted(glob.glob(os.path.join(ROOT, "skills", "*", "scripts")))])
    for c in carpetas:
        for f in sorted(glob.glob(os.path.join(ROOT, c, "test_*.py"))):
            yield f


def _src(*lineas):
    return chr(10).join(lineas) + chr(10)


def test_el_detector_ve_un_caso_que_solo_cuelga_de_main():
    mixto = _src("def test_a():", "    assert 1", "def main():", "    assert 2",
                 "if __name__ == '__main__':", "    main()")
    assert casos_solo_desde_main(mixto) == ["main"]
    envuelto = mixto + _src("def test_legado():", "    main()")
    assert casos_solo_desde_main(envuelto) == []
    solo_script = _src("def main():", "    assert 1", "if __name__ == '__main__':", "    main()")
    assert casos_solo_desde_main(solo_script) == []


def test_ningun_caso_de_la_ci_queda_solo_en_main():
    """Gap 1 (T-23 fix1): el bucle de `ci.yml` ya no ejecuta los scripts; todo lo que corre la CI es
    pytest. Una suite con `def test_*` cuyo `main()`/`run()` guarda casos propios los perdería en
    silencio: cada uno ha de colgar de una función `test_*` (p. ej. `def test_suite_legada(): main()`)."""
    huecos = {}
    for f in _ficheros_de_la_ci():
        solo_main = casos_solo_desde_main(open(f, encoding="utf-8").read())
        if solo_main:
            huecos[os.path.relpath(f, ROOT)] = solo_main
    assert not huecos, huecos


def test_el_bucle_de_ci_no_existe_y_nada_corre_dos_veces():
    """Gap 14 (T-23 fix1): las suites-script las ejecuta `test_la_suite_script_pasa` bajo pytest; el
    bucle `for t in ...; python "$t"` las corría una segunda vez. La CI no lo lleva."""
    yml = _yml_ci()
    assert 'python "$t"' not in yml and "for t in" not in yml, "el bucle de scripts sigue en la CI"


def test_los_tests_de_tiempo_de_pared_de_redact_estan_marcados_serie():
    """T-23 fix1 (gap 3): `test_bounded_memory_inputs_redact_without_superlinear_delay` mide `< 1.5 s` con un
    subproceso por caso; bajo `-n auto` (4 procesos en 1 GiB) `curl_args` y `mysql_args` tardaron 1,72 s y 1,60 s.
    Es un test de tiempo de pared: va al paso serie como los demás."""
    codigo = open(os.path.join(ROOT, "agent-kits", "shared", "test_redact.py"), encoding="utf-8").read()
    i = codigo.index("def test_bounded_memory_inputs_redact_without_superlinear_delay")
    previas = codigo[:i].rstrip().split(chr(10))[-4:]
    assert any("pytest.mark.serie" in l for l in previas), previas


def main():
    return pytest.main([os.path.abspath(__file__), "-q"])


if __name__ == "__main__":
    sys.exit(main())
