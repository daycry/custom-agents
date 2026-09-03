#!/usr/bin/env python3
"""
coverage-gate.py — gate de cobertura DETERMINISTA y agnóstico de stack (skill `unit-tests`,
iniciativa superiority T-03). Nunca inventa un porcentaje: sin herramienta/stack/parseo, avisa y
sale con 2.

  1. Detecta el stack por los ficheros del proyecto (en este orden):
       pytest   pyproject.toml · pytest.ini · setup.cfg  (o `tests/` + algún `*.py`)
       jest     package.json con "jest" en dependencias/devDependencies, `jest.config.*`
                o `"test"` de `scripts` mencionando jest
       vitest   package.json con "vitest", o `vitest.config.*`
       phpunit  phpunit.xml(.dist) · composer.json con `phpunit/phpunit`
       go       go.mod
  2. Ejecuta la cobertura OFICIAL de ese stack, **solo si la herramienta está en PATH** (o si se
     pasa `--runner`, que sustituye el comando y se ejecuta igualmente — así lo mockean los tests):
       pytest   python3 -m pytest --cov=. --cov-report=json         → coverage.json
       jest     npx jest --coverage --coverageReporters=json-summary → coverage/coverage-summary.json
       vitest   npx vitest run --coverage.enabled --coverage.reporter=json-summary → mismo fichero
       phpunit  <phpunit> --coverage-clover clover.xml              → clover.xml
       go       go test -coverprofile=coverage.out ./...            → coverage.out (perfil crudo)
     y parsea el **% global y por fichero** de ese informe (rutas relativas al proyecto).
  3. `--changed-only [--base <ref>]`: mide SOLO los ficheros de CÓDIGO del diff (`git diff
     --name-only <base>` ∪ untracked; sin tests ni prosa), como la media de sus % individuales del
     informe (no el % global del proyecto). `--base` por defecto: merge-base con `main`/`master`;
     sin ninguna, HEAD (aviso). Sin ficheros de código en el diff → nada que evaluar, exit 0.
  4. Sin `--changed-only`: usa el % GLOBAL del informe.

Exit: 0 (>= --min) · 1 (< --min) · 2 (sin herramienta/stack detectado/error de parseo — uso
incorrecto o degradación explícita; SIEMPRE con aviso en stderr, nunca un % inventado).

Uso:
  coverage-gate.py <ruta> [--min 80] [--changed-only [--base <ref>]] [--json] [--runner <cmd>]
"""
import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

MAIN_BRANCHES = ("main", "master")

# Ficheros de cobertura que cada stack debe DEJAR (propios o vía --runner), relativos a <ruta>.
COV_FILE = {
    "pytest": "coverage.json",
    "jest": os.path.join("coverage", "coverage-summary.json"),
    "vitest": os.path.join("coverage", "coverage-summary.json"),
    "phpunit": "clover.xml",
    "go": "coverage.out",
}

CODE_EXT = {
    "pytest": (".py",),
    "jest": (".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"),
    "vitest": (".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"),
    "phpunit": (".php",),
    "go": (".go",),
}

# Ficheros de test/fixture: no cuentan como "código" para --changed-only (ni pytest ni tests
# vecinos de una skill). Extendida con el patrón PHP `FooTest.php` (sin guion bajo).
TEST_RE = re.compile(
    r"(^|/)(tests?|__tests__|spec|fixtures?)/|(^|/)test_[^/]*$|_test\.[^/]+$|\.(test|spec)\.[^/]+$"
    r"|[A-Za-z0-9]Test\.php$",
    re.IGNORECASE)


def avisar(msg):
    print(f"coverage-gate: {msg}", file=sys.stderr)


# ------------------------------------------------------------------- detección de stack ----

def _leer_json(path):
    try:
        with open(path, encoding="utf-8-sig") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _tiene_py_bajo(ruta):
    for dirpath, dirnames, filenames in os.walk(ruta):
        dirnames[:] = [d for d in dirnames if d not in (".git", "__pycache__", "node_modules", "vendor", ".venv", "venv")]
        if any(fn.endswith(".py") for fn in filenames):
            return True
    return False


def detectar_stack(ruta):
    """Nombre del stack detectado (pytest|jest|vitest|phpunit|go) o None."""
    def existe(*names):
        return any(os.path.isfile(os.path.join(ruta, n)) for n in names)

    if existe("pyproject.toml", "pytest.ini", "setup.cfg"):
        return "pytest"
    if os.path.isdir(os.path.join(ruta, "tests")) and _tiene_py_bajo(ruta):
        return "pytest"

    pkg = _leer_json(os.path.join(ruta, "package.json"))
    if isinstance(pkg, dict):
        deps = {}
        for k in ("dependencies", "devDependencies"):
            v = pkg.get(k)
            if isinstance(v, dict):
                deps.update(v)
        test_script = ""
        scripts = pkg.get("scripts")
        if isinstance(scripts, dict):
            test_script = str(scripts.get("test", ""))
        if "vitest" in deps or existe("vitest.config.js", "vitest.config.ts", "vitest.config.mjs") \
                or "vitest" in test_script:
            return "vitest"
        if "jest" in deps or existe("jest.config.js", "jest.config.ts", "jest.config.cjs") \
                or "jest" in test_script:
            return "jest"

    if existe("phpunit.xml", "phpunit.xml.dist"):
        return "phpunit"
    composer = _leer_json(os.path.join(ruta, "composer.json"))
    if isinstance(composer, dict):
        req = {}
        for k in ("require", "require-dev"):
            v = composer.get(k)
            if isinstance(v, dict):
                req.update(v)
        if "phpunit/phpunit" in req:
            return "phpunit"

    if existe("go.mod"):
        return "go"
    return None


# ------------------------------------------------------------ herramienta disponible ----

def _local_bin(ruta, nombre):
    p = os.path.join(ruta, "node_modules", ".bin", nombre)
    return p if os.path.isfile(p) else None


def herramienta_disponible(stack, ruta):
    """¿Está la herramienta OFICIAL de este stack lista para ejecutar? Nunca lanza."""
    if stack == "pytest":
        try:
            r = subprocess.run([sys.executable, "-c", "import pytest, pytest_cov"],
                               cwd=ruta, capture_output=True, timeout=15)
            return r.returncode == 0
        except (OSError, subprocess.SubprocessError):
            return False
    if stack in ("jest", "vitest"):
        return bool(_local_bin(ruta, stack) or shutil.which(stack))
    if stack == "phpunit":
        local = os.path.join(ruta, "vendor", "bin", "phpunit")
        return os.path.isfile(local) or shutil.which("phpunit") is not None
    if stack == "go":
        return shutil.which("go") is not None
    return False


def comando_defecto(stack, ruta):
    if stack == "pytest":
        return [sys.executable, "-m", "pytest", "--cov=.", "--cov-report=json"]
    if stack == "jest":
        binario = _local_bin(ruta, "jest") or "jest"
        return [binario, "--coverage", "--coverageReporters=json-summary"]
    if stack == "vitest":
        binario = _local_bin(ruta, "vitest") or "vitest"
        return [binario, "run", "--coverage.enabled", "--coverage.reporter=json-summary"]
    if stack == "phpunit":
        binario = os.path.join(ruta, "vendor", "bin", "phpunit")
        if not os.path.isfile(binario):
            binario = "phpunit"
        return [binario, "--coverage-clover", "clover.xml"]
    if stack == "go":
        return ["go", "test", "-coverprofile=coverage.out", "./..."]
    return None


def ejecutar_cobertura(stack, ruta, runner):
    """Corre el comando (runner si se da, si no el de defecto) con cwd=ruta. No lanza."""
    try:
        cmd = shlex.split(runner) if runner else comando_defecto(stack, ruta)
        subprocess.run(cmd, cwd=ruta, capture_output=True, text=True, timeout=600)
    except (OSError, subprocess.SubprocessError, ValueError) as e:
        avisar(f"la ejecución de cobertura falló ({e.__class__.__name__}: {e})")


# --------------------------------------------------------------------- parseo ----

class ParseoError(Exception):
    pass


def parsear_pytest(path):
    data = _leer_json(path)
    if not isinstance(data, dict) or "totals" not in data or "files" not in data:
        raise ParseoError(f"{path}: no parece un coverage.json de coverage.py")
    total = float(data["totals"].get("percent_covered", 0.0))
    files = {}
    for rel, info in data.get("files", {}).items():
        summ = info.get("summary", {}) if isinstance(info, dict) else {}
        if "percent_covered" in summ:
            files[rel.replace("\\", "/")] = float(summ["percent_covered"])
    return total, files


def parsear_jest(path):
    data = _leer_json(path)
    if not isinstance(data, dict) or "total" not in data:
        raise ParseoError(f"{path}: no parece un coverage-summary.json de istanbul")
    total = float(data["total"].get("lines", {}).get("pct", 0.0))
    files = {}
    for rel, info in data.items():
        if rel == "total" or not isinstance(info, dict):
            continue
        pct = info.get("lines", {}).get("pct")
        if isinstance(pct, (int, float)):
            files[rel.replace("\\", "/")] = float(pct)
    return total, files


def parsear_clover(path):
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as e:
        raise ParseoError(f"{path}: XML clover inválido ({e})")
    proyecto = root.find("project")
    if proyecto is None:
        raise ParseoError(f"{path}: no parece un clover.xml (falta <project>)")

    def pct(metrics):
        if metrics is None:
            return 0.0
        st = int(metrics.get("statements", 0) or 0)
        cov = int(metrics.get("coveredstatements", 0) or 0)
        return (cov / st * 100.0) if st else 100.0

    total = pct(proyecto.find("metrics"))
    files = {}
    base = os.path.dirname(os.path.abspath(path))
    for fnode in proyecto.findall("file"):
        nombre = fnode.get("name", "")
        rel = os.path.relpath(nombre, base) if os.path.isabs(nombre) else nombre
        files[rel.replace("\\", "/")] = pct(fnode.find("metrics"))
    return total, files


GO_LINE_RE = re.compile(r"^(.+\.go):\d+\.\d+,\d+\.\d+\s+(\d+)\s+(\d+)\s*$")


def parsear_go(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            lineas = f.readlines()
    except OSError as e:
        raise ParseoError(f"{path}: illegible ({e})")
    if not lineas or not lineas[0].startswith("mode:"):
        raise ParseoError(f"{path}: no parece un perfil de `go test -coverprofile`")
    stmts, cubiertos = {}, {}
    for ln in lineas[1:]:
        m = GO_LINE_RE.match(ln.strip())
        if not m:
            continue
        fichero, n, cnt = m.group(1), int(m.group(2)), int(m.group(3))
        stmts[fichero] = stmts.get(fichero, 0) + n
        cubiertos[fichero] = cubiertos.get(fichero, 0) + (n if int(cnt) > 0 else 0)
    if not stmts:
        raise ParseoError(f"{path}: perfil sin bloques de statements")
    files = {f: (cubiertos[f] / stmts[f] * 100.0 if stmts[f] else 100.0) for f in stmts}
    total = (sum(cubiertos.values()) / sum(stmts.values()) * 100.0) if sum(stmts.values()) else 0.0
    return total, files


PARSERS = {"pytest": parsear_pytest, "jest": parsear_jest, "vitest": parsear_jest,
          "phpunit": parsear_clover, "go": parsear_go}


# ------------------------------------------------------------------------ git ----

def git(ruta, *args):
    r = subprocess.run(["git", *args], cwd=ruta, capture_output=True, text=True, errors="replace")
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout


def repo_root(ruta):
    try:
        return os.path.realpath(git(ruta, "rev-parse", "--show-toplevel").strip())
    except (RuntimeError, OSError):
        return None


def resolver_base(root, base):
    if base:
        return base, None
    try:
        actual = git(root, "rev-parse", "--abbrev-ref", "HEAD").strip()
    except RuntimeError:
        return "HEAD", "repo sin commits: solo ficheros sin comitear"
    if actual in MAIN_BRANCHES:
        return "HEAD", None
    for b in MAIN_BRANCHES:
        if subprocess.run(["git", "rev-parse", "--verify", "--quiet", b], cwd=root,
                          capture_output=True).returncode == 0:
            return git(root, "merge-base", b, "HEAD").strip(), None
    return "HEAD", f"sin base clara (rama «{actual}», sin main/master): pasa --base <ref> para el rango completo"


def ficheros_cambiados(root, base):
    tracked = [l.strip() for l in git(root, "diff", "--name-only", base, "--").splitlines() if l.strip()] \
        if subprocess.run(["git", "rev-parse", "--verify", "--quiet", "HEAD"], cwd=root,
                          capture_output=True).returncode == 0 else []
    untracked = [l[3:].strip() for l in git(root, "status", "--porcelain", "--untracked-files=all").splitlines()
                if l.startswith("??")]
    return sorted(set(tracked) | set(untracked))


def es_codigo(rel, stack):
    if TEST_RE.search(rel):
        return False
    return rel.lower().endswith(CODE_EXT.get(stack, ()))


# --------------------------------------------------------------------- gate ----

def _match_pct(rel, files):
    """% de `rel` en el informe: exacto o por sufijo de ruta (los reportes usan rutas propias)."""
    rel = rel.replace("\\", "/")
    if rel in files:
        return files[rel]
    for k, v in files.items():
        if k == rel or k.endswith("/" + rel) or rel.endswith("/" + k):
            return v
    return None


def evaluar(ruta, minimo, changed_only, base_ref, runner, root_arg=None):
    """dict con el resultado completo. Nunca lanza: los fallos se traducen en exit 2 + aviso."""
    stack = detectar_stack(ruta)
    if not stack:
        return {"ok": False, "exit": 2, "aviso": "no se detectó ningún stack soportado "
                "(pytest/jest/vitest/phpunit/go): ¿faltan sus ficheros de manifiesto?"}

    if not runner and not herramienta_disponible(stack, ruta):
        return {"ok": False, "exit": 2, "stack": stack,
               "aviso": f"stack «{stack}» detectado pero su herramienta de cobertura no está "
                        f"disponible (PATH/paquete) — nunca se inventa un porcentaje"}

    ejecutar_cobertura(stack, ruta, runner)
    cov_path = os.path.join(ruta, COV_FILE[stack])
    if not os.path.isfile(cov_path):
        return {"ok": False, "exit": 2, "stack": stack,
               "aviso": f"no se generó el fichero de cobertura esperado ({COV_FILE[stack]}): "
                        f"revisa que la ejecución haya terminado bien"}
    try:
        total, files = PARSERS[stack](cov_path)
    except ParseoError as e:
        return {"ok": False, "exit": 2, "stack": stack, "aviso": f"no se pudo parsear el informe: {e}"}

    detalle = {"stack": stack, "informe": os.path.relpath(cov_path, ruta), "global": round(total, 2)}
    avisos = []

    if not changed_only:
        pct = total
        detalle["modo"] = "global"
    else:
        detalle["modo"] = "changed-only"
        groot = root_arg or repo_root(ruta)
        if not groot:
            avisos.append("fuera de un repositorio git: --changed-only no puede filtrar por diff")
            detalle["ficheros"] = []
            pct = None
        else:
            base, av = resolver_base(groot, base_ref)
            if av:
                avisos.append(av)
            detalle["base"] = base
            cambiados = [os.path.relpath(os.path.join(groot, f), ruta).replace("\\", "/")
                        for f in ficheros_cambiados(groot, base)]
            codigo = sorted({f for f in cambiados if es_codigo(f, stack)})
            porfichero, sin_datos = {}, []
            for f in codigo:
                p = _match_pct(f, files)
                if p is None:
                    sin_datos.append(f)
                else:
                    porfichero[f] = round(p, 2)
            detalle["ficheros"] = porfichero
            if sin_datos:
                avisos.append(f"sin datos de cobertura para: {', '.join(sin_datos)} (excluidos de la media)")
            pct = (sum(porfichero.values()) / len(porfichero)) if porfichero else None

    if pct is None:
        return {"ok": True, "exit": 0, "stack": stack, "detalle": detalle, "avisos": avisos + (
            [] if changed_only else []) + (["sin ficheros de código en el diff: nada que evaluar"] if changed_only and not avisos else [])}

    aprueba = pct >= minimo
    detalle["porcentaje"] = round(pct, 2)
    detalle["minimo"] = minimo
    return {"ok": aprueba, "exit": 0 if aprueba else 1, "stack": stack, "detalle": detalle, "avisos": avisos}


# --------------------------------------------------------------------- salida ----

def render_md(res):
    d = res.get("detalle", {})
    if not res.get("ok") and "detalle" not in res:
        return f"coverage-gate: {res.get('aviso', 'error')}"
    out = [f"# Gate de cobertura — {d.get('stack', '?')}", ""]
    out.append(f"- Informe: `{d.get('informe', '—')}`")
    out.append(f"- Cobertura global: {d.get('global', '—')}%")
    if d.get("modo") == "changed-only":
        out.append(f"- Modo: solo ficheros cambiados (base `{d.get('base', '—')}`)")
        for f, p in sorted(d.get("ficheros", {}).items()):
            out.append(f"  - `{f}`: {p}%")
    if "porcentaje" in d:
        veredicto = "✅ CUMPLE" if res["exit"] == 0 else "❌ NO CUMPLE"
        out.append(f"- Porcentaje evaluado: **{d['porcentaje']}%** (mínimo {d['minimo']}%) → {veredicto}")
    for a in res.get("avisos", []):
        out.append(f"- ⚠️ {a}")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("ruta")
    ap.add_argument("--min", type=float, default=80.0)
    ap.add_argument("--changed-only", action="store_true")
    ap.add_argument("--base", default=None)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--runner", default=None, help="comando que sustituye al oficial del stack (tests)")
    args = ap.parse_args(argv)

    ruta = os.path.abspath(args.ruta)
    if not os.path.isdir(ruta):
        print(f"coverage-gate: ruta inexistente: {args.ruta}", file=sys.stderr)
        return 2

    res = evaluar(ruta, args.min, args.changed_only, args.base, args.runner)
    for a in res.get("avisos", []):
        avisar(a)
    if "aviso" in res:
        avisar(res["aviso"])
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print(render_md(res))
    return res["exit"]


if __name__ == "__main__":
    sys.exit(main())
