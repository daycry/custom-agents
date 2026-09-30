#!/usr/bin/env python3
"""Tests de coverage-gate.py (skill `unit-tests`, superiority T-03). Ejecutar: pytest -q
skills/unit-tests/scripts

Runner mockeado con `--runner` (deja el fichero de cobertura sin ejecutar la herramienta real);
fixtures de los 4 formatos de informe; repo git temporal para `--changed-only`."""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "coverage-gate.py")

spec = importlib.util.spec_from_file_location("coverage_gate", SCRIPT)
cg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cg)


def sh(cwd, *args):
    subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")


def write(d, rel, text):
    p = os.path.join(d, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)


def run(cwd, *args, env_extra=None):
    env = dict(os.environ)
    env.update(env_extra or {})
    r = subprocess.run([sys.executable, SCRIPT, "--json", *args], cwd=cwd,
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    data = json.loads(r.stdout) if r.stdout.strip() else None
    return r.returncode, data, r.stderr


# ------------------------------------------------------------ detección de stack ----

def test_detecta_pytest_por_pyproject():
    d = tempfile.mkdtemp(prefix="cg-")
    write(d, "pyproject.toml", "[project]\nname='x'\n")
    assert cg.detectar_stack(d) == "pytest"


def test_detecta_pytest_por_carpeta_tests_y_py():
    d = tempfile.mkdtemp(prefix="cg-")
    write(d, "tests/test_x.py", "def test_x():\n    assert 1\n")
    assert cg.detectar_stack(d) == "pytest"


def test_detecta_jest_por_package_json():
    d = tempfile.mkdtemp(prefix="cg-")
    write(d, "package.json", json.dumps({"devDependencies": {"jest": "29.0.0"}}))
    assert cg.detectar_stack(d) == "jest"


def test_detecta_vitest_por_package_json():
    d = tempfile.mkdtemp(prefix="cg-")
    write(d, "package.json", json.dumps({"devDependencies": {"vitest": "1.0.0"}}))
    assert cg.detectar_stack(d) == "vitest"


def test_detecta_phpunit_por_xml():
    d = tempfile.mkdtemp(prefix="cg-")
    write(d, "phpunit.xml", "<phpunit></phpunit>\n")
    assert cg.detectar_stack(d) == "phpunit"


def test_detecta_phpunit_por_composer():
    d = tempfile.mkdtemp(prefix="cg-")
    write(d, "composer.json", json.dumps({"require-dev": {"phpunit/phpunit": "^10"}}))
    assert cg.detectar_stack(d) == "phpunit"


def test_detecta_go_por_gomod():
    d = tempfile.mkdtemp(prefix="cg-")
    write(d, "go.mod", "module x\n\ngo 1.21\n")
    assert cg.detectar_stack(d) == "go"


def test_sin_manifiestos_no_detecta_stack():
    d = tempfile.mkdtemp(prefix="cg-")
    write(d, "README.md", "# nada\n")
    assert cg.detectar_stack(d) is None


# ------------------------------------------------------------------------- parseo ----

def test_parsear_pytest_coverage_json(tmp_path):
    p = tmp_path / "coverage.json"
    p.write_text(json.dumps({
        "totals": {"percent_covered": 82.5},
        "files": {"a.py": {"summary": {"percent_covered": 90.0}},
                 "b.py": {"summary": {"percent_covered": 60.0}}}}), encoding="utf-8")
    total, files = cg.parsear_pytest(str(p))
    assert total == 82.5 and files == {"a.py": 90.0, "b.py": 60.0}


def test_parsear_jest_coverage_summary(tmp_path):
    p = tmp_path / "coverage-summary.json"
    p.write_text(json.dumps({
        "total": {"lines": {"pct": 75.0}},
        "src/a.js": {"lines": {"pct": 100.0}},
        "src/b.js": {"lines": {"pct": 50.0}}}), encoding="utf-8")
    total, files = cg.parsear_jest(str(p))
    assert total == 75.0 and files == {"src/a.js": 100.0, "src/b.js": 50.0}


def test_parsear_clover(tmp_path):
    p = tmp_path / "clover.xml"
    p.write_text("""<coverage><project>
      <file name=\"""" + str(tmp_path) + """/src/A.php\">
        <metrics statements=\"10\" coveredstatements=\"8\"/>
      </file>
      <metrics statements=\"10\" coveredstatements=\"8\"/>
    </project></coverage>""", encoding="utf-8")
    total, files = cg.parsear_clover(str(p))
    assert total == 80.0
    assert files == {"src/A.php": 80.0}


def test_parsear_go_profile(tmp_path):
    p = tmp_path / "coverage.out"
    p.write_text(
        "mode: set\n"
        "example.com/x/a.go:10.16,12.3 2 1\n"
        "example.com/x/a.go:15.2,17.3 1 0\n"
        "example.com/x/b.go:5.1,6.2 3 1\n",
        encoding="utf-8")
    total, files = cg.parsear_go(str(p))
    assert round(files["example.com/x/a.go"], 2) == round(2 / 3 * 100, 2)
    assert files["example.com/x/b.go"] == 100.0
    assert round(total, 2) == round(5 / 6 * 100, 2)


def test_parsear_go_perfil_invalido_lanza_parseoerror(tmp_path):
    p = tmp_path / "coverage.out"
    p.write_text("no es un perfil\n", encoding="utf-8")
    try:
        cg.parsear_go(str(p))
        assert False, "debía lanzar ParseoError"
    except cg.ParseoError:
        pass


# ------------------------------------------------------------------------- CLI ----

def _runner_que_escribe(d, rel, contenido):
    """Comando de un solo uso: copia `contenido` a `rel` dentro de `d` vía python3 -c."""
    script = os.path.join(d, "_runner.py")
    write(d, "_runner.py", "import pathlib,sys\n"
         f"pathlib.Path({rel!r}).parent.mkdir(parents=True, exist_ok=True)\n"
         f"pathlib.Path({rel!r}).write_text({contenido!r}, encoding='utf-8')\n")
    return f"{sys.executable} {script}"


def test_min_0_siempre_aprueba():
    d = tempfile.mkdtemp(prefix="cg-")
    write(d, "pyproject.toml", "[project]\nname='x'\n")
    cov = json.dumps({"totals": {"percent_covered": 3.0}, "files": {"a.py": {"summary": {"percent_covered": 3.0}}}})
    runner = _runner_que_escribe(d, "coverage.json", cov)
    code, data, _ = run(d, ".", "--min", "0", "--runner", runner)
    assert code == 0 and data["exit"] == 0


def test_min_100_con_menos_cobertura_falla_exit_1():
    d = tempfile.mkdtemp(prefix="cg-")
    write(d, "pyproject.toml", "[project]\nname='x'\n")
    cov = json.dumps({"totals": {"percent_covered": 50.0}, "files": {"a.py": {"summary": {"percent_covered": 50.0}}}})
    runner = _runner_que_escribe(d, "coverage.json", cov)
    code, data, _ = run(d, ".", "--min", "100", "--runner", runner)
    assert code == 1 and data["exit"] == 1
    assert data["detalle"]["porcentaje"] == 50.0


def test_sin_herramienta_exit_2_sin_inventar_porcentaje():
    """package.json con jest pero sin binario local ni global (temp dir aislado): exit 2, sin --runner."""
    d = tempfile.mkdtemp(prefix="cg-")
    write(d, "package.json", json.dumps({"devDependencies": {"jest": "29.0.0"}}))
    code, data, err = run(d, ".", "--min", "80")
    assert code == 2 and data["exit"] == 2
    assert "no está disponible" in data["aviso"]
    assert "coverage-gate" in err


def test_sin_stack_exit_2():
    d = tempfile.mkdtemp(prefix="cg-")
    write(d, "README.md", "nada de manifiestos aquí\n")
    code, data, _ = run(d, ".")
    assert code == 2 and "no se detectó ningún stack" in data["aviso"]


def test_changed_only_filtra_por_diff_en_repo_git_temporal():
    d = tempfile.mkdtemp(prefix="cg-")
    sh(d, "git", "init", "-q", "-b", "master")
    sh(d, "git", "config", "user.email", "t@t")
    sh(d, "git", "config", "user.name", "t")
    write(d, "pyproject.toml", "[project]\nname='x'\n")
    write(d, "a.py", "def a():\n    return 1\n")
    write(d, "b.py", "def b():\n    return 2\n")
    sh(d, "git", "add", "-A")
    sh(d, "git", "commit", "-q", "-m", "init")
    sh(d, "git", "checkout", "-q", "-b", "feature/x")
    write(d, "b.py", "def b():\n    return 22\n")   # solo b.py cambia
    # El informe cubre TODO el proyecto: a.py al 20% (no cambiado) y b.py al 90% (cambiado).
    cov = json.dumps({"totals": {"percent_covered": 55.0},
                      "files": {"a.py": {"summary": {"percent_covered": 20.0}},
                               "b.py": {"summary": {"percent_covered": 90.0}}}})
    runner = _runner_que_escribe(d, "coverage.json", cov)
    code, data, _ = run(d, ".", "--changed-only", "--base", "master", "--min", "80", "--runner", runner)
    assert code == 0, data
    assert data["detalle"]["modo"] == "changed-only"
    assert data["detalle"]["ficheros"] == {"b.py": 90.0}          # NO incluye a.py
    assert data["detalle"]["porcentaje"] == 90.0                  # global (55.0) habría dado exit 1


def test_changed_only_ignora_ficheros_de_test():
    d = tempfile.mkdtemp(prefix="cg-")
    sh(d, "git", "init", "-q", "-b", "master")
    sh(d, "git", "config", "user.email", "t@t")
    sh(d, "git", "config", "user.name", "t")
    write(d, "pyproject.toml", "[project]\nname='x'\n")
    write(d, "a.py", "def a():\n    return 1\n")
    sh(d, "git", "add", "-A")
    sh(d, "git", "commit", "-q", "-m", "init")
    sh(d, "git", "checkout", "-q", "-b", "feature/x")
    write(d, "tests/test_a.py", "def test_a():\n    assert True\n")   # solo test añadido, sin código
    cov = json.dumps({"totals": {"percent_covered": 10.0}, "files": {"a.py": {"summary": {"percent_covered": 10.0}}}})
    runner = _runner_que_escribe(d, "coverage.json", cov)
    code, data, avisos = run(d, ".", "--changed-only", "--base", "master", "--min", "80", "--runner", runner)
    assert code == 0          # nada de código cambiado → nada que evaluar, no falla
    assert data["detalle"]["ficheros"] == {}


def test_json_y_md_coherentes_en_exit():
    d = tempfile.mkdtemp(prefix="cg-")
    write(d, "pyproject.toml", "[project]\nname='x'\n")
    cov = json.dumps({"totals": {"percent_covered": 90.0}, "files": {"a.py": {"summary": {"percent_covered": 90.0}}}})
    runner = _runner_que_escribe(d, "coverage.json", cov)
    code_json, data, _ = run(d, ".", "--min", "80", "--runner", runner)
    r_md = subprocess.run([sys.executable, SCRIPT, ".", "--min", "80", "--runner", runner],
                          cwd=d, capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert code_json == 0 and r_md.returncode == 0
    assert "CUMPLE" in r_md.stdout and "90.0" in r_md.stdout
    assert data["detalle"]["porcentaje"] == 90.0


def test_ruta_inexistente_exit_2():
    r = subprocess.run([sys.executable, SCRIPT, "/no/existe/esta/ruta"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert r.returncode == 2


def test_runner_que_no_deja_fichero_exit_2():
    d = tempfile.mkdtemp(prefix="cg-")
    write(d, "pyproject.toml", "[project]\nname='x'\n")
    code, data, _ = run(d, ".", "--runner", f"{sys.executable} -c \"pass\"")
    assert code == 2 and "no se generó" in data["aviso"]


# ------------------------------------------------------------ C-04: timeout != ausente ----

def _sonda_falsa(secuencia):
    """subprocess.run falso: cada elemento es un returncode (int) o una excepción a lanzar."""
    llamadas = []

    def fake(cmd, **kw):
        llamadas.append(kw.get("timeout"))
        r = secuencia[min(len(llamadas) - 1, len(secuencia) - 1)]
        if isinstance(r, BaseException):
            raise r
        return subprocess.CompletedProcess(cmd, r, b"", b"")
    return fake, llamadas


def _con_subprocess_falso(secuencia, ruta="."):
    fake, llamadas = _sonda_falsa(secuencia)
    real = cg.subprocess.run
    cg.subprocess.run = fake
    try:
        return cg.sondear_herramienta("pytest", ruta), llamadas
    finally:
        cg.subprocess.run = real


def test_timeout_con_modulo_presente_reintenta_y_no_dice_no_disponible():
    estado, llamadas = _con_subprocess_falso([subprocess.TimeoutExpired("x", 15), 0])
    assert estado == "disponible"
    assert len(llamadas) == 2 and llamadas[1] > llamadas[0], llamadas


def test_timeout_persistente_es_no_verificado_no_no_disponible():
    estado, llamadas = _con_subprocess_falso([subprocess.TimeoutExpired("x", 15)])
    assert estado == "no_verificado"
    assert len(llamadas) == 2, "reintento acotado: una sola repetición"


def test_import_fallido_real_es_ausente():
    estado, llamadas = _con_subprocess_falso([1])
    assert estado == "ausente" and len(llamadas) == 1, "un import fallido no se reintenta"


def test_herramienta_disponible_sigue_siendo_bool():
    fake, _ = _sonda_falsa([0])
    real = cg.subprocess.run
    cg.subprocess.run = fake
    try:
        assert cg.herramienta_disponible("pytest", ".") is True
    finally:
        cg.subprocess.run = real


def test_evaluar_timeout_persistente_exit_2_con_aviso_no_verificado_sin_porcentaje():
    d = tempfile.mkdtemp(prefix="cg-")
    write(d, "pyproject.toml", "[project]\nname='x'\n")
    fake, _ = _sonda_falsa([subprocess.TimeoutExpired("x", 15)])
    real = cg.subprocess.run
    cg.subprocess.run = fake
    try:
        res = cg.evaluar(d, 80, False, None, None)
    finally:
        cg.subprocess.run = real
    assert res["exit"] == 2 and "no verificado" in res["aviso"] and "no está disponible" not in res["aviso"]
    assert "global" not in res


def test_evaluar_modulo_ausente_sigue_dando_exit_2_no_disponible():
    d = tempfile.mkdtemp(prefix="cg-")
    write(d, "pyproject.toml", "[project]\nname='x'\n")
    fake, _ = _sonda_falsa([1])
    real = cg.subprocess.run
    cg.subprocess.run = fake
    try:
        res = cg.evaluar(d, 80, False, None, None)
    finally:
        cg.subprocess.run = real
    assert res["exit"] == 2 and "no está disponible" in res["aviso"]



def test_sondear_herramienta_stacks_no_pytest_y_desconocido(monkeypatch=None):
    d = tempfile.mkdtemp(prefix="cg-")
    real_which = cg.shutil.which
    try:
        cg.shutil.which = lambda nombre: "/x/" + nombre
        assert cg.sondear_herramienta("jest", d) == "disponible"
        assert cg.sondear_herramienta("vitest", d) == "disponible"
        assert cg.sondear_herramienta("phpunit", d) == "disponible"
        assert cg.sondear_herramienta("go", d) == "disponible"
        cg.shutil.which = lambda nombre: None
        for stack in ("jest", "vitest", "phpunit", "go", "desconocido"):
            assert cg.sondear_herramienta(stack, d) == "ausente", stack
    finally:
        cg.shutil.which = real_which


def test_sondear_herramienta_pytest_oserror_es_ausente():
    fake, _ = _sonda_falsa([OSError("sin python")])
    real = cg.subprocess.run
    cg.subprocess.run = fake
    try:
        assert cg.sondear_herramienta("pytest", ".") == "ausente"
    finally:
        cg.subprocess.run = real
