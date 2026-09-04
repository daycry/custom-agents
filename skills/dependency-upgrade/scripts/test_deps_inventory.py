#!/usr/bin/env python3
"""Tests de deps-inventory.py (memory-health T-03). Ejecutar: python3 -m pytest -q skills/dependency-upgrade/scripts

Fixtures de los 7 manifiestos + lockfiles generadas en tmp; el «outdated» oficial se MOCKEA inyectando
el ejecutor (nunca se lanza npm/composer/pip/go de verdad). Se afirma: detección, declaradas +
bloqueadas, clasificación patch/minor/major, degradación sin herramienta (latest = —, aviso, nada
inventado), `--no-outdated`, MD/JSON coherentes y exit codes."""
import importlib.util
import json
import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "deps-inventory.py")
spec = importlib.util.spec_from_file_location("deps_inventory", SCRIPT)
di = importlib.util.module_from_spec(spec)
spec.loader.exec_module(di)


def fixture(tmp_path):
    root = tmp_path / "proj"
    (root / "web").mkdir(parents=True)
    (root / "api").mkdir()
    (root / "svc").mkdir()
    (root / "node_modules" / "x").mkdir(parents=True)
    (root / "node_modules" / "x" / "package.json").write_text('{"dependencies": {"ignorado": "1.0.0"}}', encoding="utf-8")
    (root / "web" / "package.json").write_text(json.dumps({
        "dependencies": {"express": "^4.18.2", "lodash": "~4.17.0"},
        "devDependencies": {"jest": "29.0.0"}}), encoding="utf-8")
    (root / "web" / "package-lock.json").write_text(json.dumps({
        "lockfileVersion": 3,
        "packages": {"": {}, "node_modules/express": {"version": "4.18.2"}, "node_modules/lodash": {"version": "4.17.21"},
                     "node_modules/jest": {"version": "29.0.0"}, "node_modules/express/node_modules/x": {"version": "9"}}}), encoding="utf-8")
    (root / "api" / "composer.json").write_text(json.dumps({
        "require": {"php": ">=8.1", "ext-json": "*", "laravel/framework": "^10.0"},
        "require-dev": {"phpunit/phpunit": "^10.1"}}), encoding="utf-8")
    (root / "api" / "composer.lock").write_text(json.dumps({
        "packages": [{"name": "laravel/framework", "version": "v10.48.0"}],
        "packages-dev": [{"name": "phpunit/phpunit", "version": "10.5.0"}]}), encoding="utf-8")
    (root / "requirements.txt").write_text("# deps\nrequests==2.31.0\nDjango>=4.2,<5\n-r other.txt\nuvicorn[standard]~=0.23\n", encoding="utf-8")
    (root / "pyproject.toml").write_text(
        '[project]\nname = "x"\ndependencies = ["httpx>=0.25", "pydantic[email]==2.5.0"]\n'
        '[project.optional-dependencies]\ndev = ["pytest>=7"]\n'
        '[tool.poetry.dependencies]\npython = "^3.11"\nrich = "^13.0"\n', encoding="utf-8")
    (root / "svc" / "go.mod").write_text(
        "module example.com/svc\n\ngo 1.21\n\nrequire (\n\tgithub.com/gin-gonic/gin v1.9.1\n\tgolang.org/x/text v0.13.0 // indirect\n)\n\nrequire github.com/spf13/cobra v1.7.0\n", encoding="utf-8")
    (root / "svc" / "go.sum").write_text(
        "github.com/gin-gonic/gin v1.9.1 h1:abc=\ngithub.com/gin-gonic/gin v1.9.1/go.mod h1:def=\n", encoding="utf-8")
    (root / "Gemfile").write_text("source 'https://rubygems.org'\ngem 'rails', '~> 7.0.8'\ngem 'puma'\ngem \"rspec\", \">= 3.12\", \"< 4\"\n", encoding="utf-8")
    (root / "Gemfile.lock").write_text("GEM\n  specs:\n    rails (7.0.8)\n    puma (6.4.0)\n", encoding="utf-8")
    (root / "App.csproj").write_text(
        '<Project Sdk="Microsoft.NET.Sdk">\n  <ItemGroup>\n    <PackageReference Include="Newtonsoft.Json" Version="13.0.1" />\n'
        '    <PackageReference Include="Serilog" Version="3.1.0" />\n  </ItemGroup>\n</Project>\n', encoding="utf-8")
    return root


def mock_ejecutor(salidas):
    """Ejecutor falso: devuelve la salida preparada por binario; registra las llamadas."""
    llamadas = []

    def run(cmd, cwd, timeout):
        llamadas.append((os.path.basename(cmd[0]), cmd[1:], cwd))
        return salidas.get(os.path.basename(cmd[0]), ""), None
    run.llamadas = llamadas
    return run


def run_cli(*args):
    r = subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    return r.returncode, r.stdout, r.stderr


# ------------------------------------------------------------------ detección y parseo

def test_detecta_los_7_manifiestos_y_lockfiles_fuera_node_modules(tmp_path):
    ms = di.manifiestos(str(fixture(tmp_path)))
    por = {m["ecosistema"]: m for m in ms}
    assert set(por) == {"npm", "composer", "pip", "python", "go", "bundler", "nuget"} and len(ms) == 7
    assert por["npm"]["manifiesto"] == "web/package.json" and por["npm"]["lockfiles"] == ["package-lock.json"]
    assert por["composer"]["lockfiles"] == ["composer.lock"] and por["go"]["lockfiles"] == ["go.sum"]
    assert por["bundler"]["lockfiles"] == ["Gemfile.lock"] and por["pip"]["lockfiles"] == [] and por["nuget"]["lockfiles"] == []


def test_declaradas_por_ecosistema(tmp_path):
    root = str(fixture(tmp_path))
    r = di.inventario(root, con_outdated=False)
    deps = {e["ecosistema"]: {d["nombre"]: d for d in e["dependencias"]} for e in r["ecosistemas"]}
    assert deps["npm"]["express"]["declarada"] == "^4.18.2" and deps["npm"]["jest"]["grupo"] == "devDependencies"
    assert set(deps["composer"]) == {"laravel/framework", "phpunit/phpunit"}          # php y ext-* fuera
    assert deps["pip"]["requests"]["declarada"] == "==2.31.0" and deps["pip"]["Django"]["declarada"] == ">=4.2,<5"
    assert deps["pip"]["uvicorn"]["declarada"] == "~=0.23"                           # extras [standard] fuera
    assert deps["python"]["httpx"]["declarada"] == ">=0.25" and deps["python"]["pydantic"]["declarada"] == "==2.5.0"
    assert deps["python"]["pytest"]["grupo"] == "optional.dev" and deps["python"]["rich"]["grupo"] == "poetry.dependencies"
    assert "python" not in deps["python"]
    assert deps["go"]["github.com/gin-gonic/gin"]["declarada"] == "v1.9.1" and deps["go"]["golang.org/x/text"]["grupo"] == "indirect"
    assert deps["go"]["github.com/spf13/cobra"]["declarada"] == "v1.7.0"
    assert deps["bundler"]["rails"]["declarada"] == "~> 7.0.8" and deps["bundler"]["puma"]["declarada"] == "*"
    assert deps["bundler"]["rspec"]["declarada"] == ">= 3.12, < 4"
    assert deps["nuget"]["Newtonsoft.Json"]["declarada"] == "13.0.1" and deps["nuget"]["Serilog"]["declarada"] == "3.1.0"
    assert r["manifiestos"] == 7 and r["dependencias"] == 20


def test_bloqueadas_desde_lockfiles_parseables(tmp_path):
    r = di.inventario(str(fixture(tmp_path)), con_outdated=False)
    deps = {e["ecosistema"]: {d["nombre"]: d for d in e["dependencias"]} for e in r["ecosistemas"]}
    assert deps["npm"]["lodash"]["bloqueada"] == "4.17.21" and deps["npm"]["express"]["bloqueada"] == "4.18.2"
    assert deps["composer"]["laravel/framework"]["bloqueada"] == "10.48.0"           # sin la `v`
    assert deps["bundler"]["puma"]["bloqueada"] == "6.4.0"
    assert deps["go"]["github.com/gin-gonic/gin"]["bloqueada"] == "v1.9.1" and deps["go"]["github.com/spf13/cobra"]["bloqueada"] is None
    assert deps["pip"]["requests"]["bloqueada"] is None                              # requirements sin lock


# ------------------------------------------------------------------ outdated mockeado y clasificación

def test_outdated_mockeado_clasifica_patch_minor_major(tmp_path, monkeypatch):
    root = str(fixture(tmp_path))
    monkeypatch.setattr(di.shutil, "which", lambda b: f"/usr/bin/{b}")
    ej = mock_ejecutor({
        "npm": json.dumps({"express": {"current": "4.18.2", "wanted": "4.18.3", "latest": "5.0.0"},
                           "lodash": {"current": "4.17.21", "latest": "4.17.22"}}),
        "composer": json.dumps({"installed": [{"name": "laravel/framework", "version": "v10.48.0", "latest": "v11.0.0"},
                                              {"name": "phpunit/phpunit", "version": "10.5.0", "latest": "10.6.0"}]}),
        "pip": json.dumps([{"name": "requests", "version": "2.31.0", "latest_version": "2.32.0"},
                           {"name": "Django", "version": "4.2.0", "latest_version": "5.0.0"}]),
        "go": '{\n\t"Path": "github.com/gin-gonic/gin",\n\t"Version": "v1.9.1",\n\t"Update": {\n\t\t"Path": "github.com/gin-gonic/gin",\n\t\t"Version": "v1.10.0"\n\t}\n}\n{\n\t"Path": "golang.org/x/text",\n\t"Version": "v0.13.0"\n}\n',
    })
    r = di.inventario(root, con_outdated=True, ejecutor=ej)
    deps = {e["ecosistema"]: {d["nombre"]: d for d in e["dependencias"]} for e in r["ecosistemas"]}
    assert deps["npm"]["express"]["latest"] == "5.0.0" and deps["npm"]["express"]["salto"] == "major"
    assert deps["npm"]["lodash"]["salto"] == "patch" and deps["npm"]["jest"]["salto"] == "desconocido"
    assert deps["composer"]["laravel/framework"]["latest"] == "11.0.0" and deps["composer"]["laravel/framework"]["salto"] == "major"
    assert deps["composer"]["phpunit/phpunit"]["salto"] == "minor"
    assert deps["pip"]["requests"]["salto"] == "minor" and deps["pip"]["Django"]["salto"] == "major"   # case-insensitive
    assert deps["go"]["github.com/gin-gonic/gin"]["latest"] == "v1.10.0" and deps["go"]["github.com/gin-gonic/gin"]["salto"] == "minor"
    assert deps["go"]["golang.org/x/text"]["salto"] == "desconocido"
    assert r["por_salto"]["major"] == 3
    # cada herramienta se ejecutó en el directorio de SU manifiesto, con los argumentos oficiales
    llamadas = {b: (args, cwd) for b, args, cwd in ej.llamadas}
    assert llamadas["npm"][0] == ["outdated", "--json"] and llamadas["npm"][1].endswith("web")
    assert llamadas["composer"][0] == ["outdated", "--format=json"] and llamadas["composer"][1].endswith("api")
    assert llamadas["go"][0] == ["list", "-u", "-m", "-json", "all"]
    assert llamadas["pip"][0] == ["list", "--outdated", "--format=json"]
    # bundler y nuget: sin comando integrado → aviso, latest —
    assert any("bundler" in a for a in r["avisos"]) and any("nuget" in a for a in r["avisos"])


def test_sin_herramienta_en_path_latest_vacio_con_aviso_y_nada_inventado(tmp_path, monkeypatch):
    root = str(fixture(tmp_path))
    monkeypatch.setattr(di.shutil, "which", lambda b: None)
    ej = mock_ejecutor({})
    r = di.inventario(root, con_outdated=True, ejecutor=ej)
    assert ej.llamadas == []
    assert all(d["latest"] is None and d["salto"] == "desconocido" for e in r["ecosistemas"] for d in e["dependencias"])
    assert any("`npm` no está en PATH" in a and "no se inventa" in a for a in r["avisos"])
    assert "major" not in r["por_salto"] and r["por_salto"]["desconocido"] == 20


def test_timeout_y_salida_no_parseable_degradan_con_aviso(tmp_path, monkeypatch):
    root = str(fixture(tmp_path))
    monkeypatch.setattr(di.shutil, "which", lambda b: f"/usr/bin/{b}")

    def ej(cmd, cwd, timeout):
        b = os.path.basename(cmd[0])
        if b == "npm":
            return "", "`npm outdated --json` superó 1 s (¿sin red?)"
        return "esto no es json", None
    r = di.inventario(root, con_outdated=True, timeout=1, ejecutor=ej)
    assert any("superó 1 s" in a for a in r["avisos"]) and any("no parseable" in a for a in r["avisos"])
    assert all(d["latest"] is None for e in r["ecosistemas"] for d in e["dependencias"])


def test_salto_semver_casos():
    assert di.salto("^4.18.2", "4.18.2", "5.0.0") == "major"
    assert di.salto("^4.18.2", None, "4.19.0") == "minor"
    assert di.salto("~4.17.0", "4.17.21", "4.17.22") == "patch"
    assert di.salto("1.0.0", None, "1.0.0") == "igual"
    assert di.salto("1.0.0", None, None) == "desconocido"
    assert di.salto("*", None, "2.0.0") == "desconocido"
    assert di.salto("2.0.0", None, "1.9.0") == "desconocido"          # latest < base: no es un salto
    assert di.salto("v1.9.1", "v1.9.1", "v1.10.0") == "minor"


# ------------------------------------------------------------------ CLI

def test_cli_no_outdated_md_y_json_coherentes(tmp_path):
    root = str(fixture(tmp_path))
    rc, out, _ = run_cli(root, "--no-outdated")
    rc2, js, _ = run_cli(root, "--no-outdated", "--json")
    assert rc == 0 and rc2 == 0
    j = json.loads(js)
    assert out.startswith("# Inventario de dependencias") and "## npm — `web/package.json` (package-lock.json)" in out
    assert f"**{j['manifiestos']} manifiesto(s) · {j['dependencias']} dependencias**" in out
    assert "| `express` | `^4.18.2` | 4.18.2 | — | desconocido | dependencies | registro |" in out
    assert "breaking probable" in out                                    # la leyenda siempre está
    assert all("`--no-outdated`" in a for a in j["avisos"]) and len(j["avisos"]) == 7


def test_cli_sin_manifiestos_y_ruta_inexistente(tmp_path):
    vacio = tmp_path / "vacio"
    vacio.mkdir()
    rc, out, _ = run_cli(str(vacio))
    assert rc == 0 and "Sin manifiestos reconocidos" in out
    rc, _, err = run_cli(str(tmp_path / "no-existe"))
    assert rc == 2 and "no existe" in err


def test_requirements_marcadores_comentarios_local_y_vcs(tmp_path):
    """T-fix1 (M3): marcador de entorno en su campo, comentario fuera, -e/git+/@ url como deps tipo
    local|vcs|url sin versión (no desaparecen), opciones de pip fuera. 8 líneas → 6 dependencias."""
    root = tmp_path / "p"
    root.mkdir()
    (root / "requirements.txt").write_text(
        "requests>=2.31 ; python_version>\"3.8\"  # comentario\n"
        "# solo comentario\n"
        "-e .\n"
        "-e git+https://github.com/org/tool.git@v1.2#egg=tool\n"
        "git+https://github.com/org/lib.git@main#egg=lib\n"
        "pkg @ https://example.com/pkg-1.0.tar.gz\n"
        "--index-url https://example.com/simple\n"
        "Django==4.2\t# tab-comentario\n", encoding="utf-8")
    r = di.inventario(str(root), con_outdated=False)
    deps = {d["nombre"]: d for d in r["ecosistemas"][0]["dependencias"]}
    assert set(deps) == {"requests", ".", "tool", "lib", "pkg", "Django"}
    assert deps["requests"]["declarada"] == ">=2.31" and deps["requests"]["marcador"] == 'python_version>"3.8"'
    assert deps["Django"]["declarada"] == "==4.2" and deps["Django"]["marcador"] is None
    assert deps["."]["tipo"] == "local" and deps["."]["declarada"] == "*" and deps["."]["salto"] == "desconocido"
    assert deps["tool"]["tipo"] == "vcs" and deps["tool"]["origen"].startswith("git+https://") and deps["tool"]["latest"] is None
    assert deps["lib"]["tipo"] == "vcs" and deps["pkg"]["tipo"] == "url" and deps["pkg"]["origen"].startswith("https://")
    assert deps["requests"]["tipo"] == "registro"
    md = di.md(r)
    assert "| **local** `.` |" in md and "**vcs** `git+https://github.com/org/lib.git@main#egg=lib` |" in md
    assert '`; python_version>"3.8"`' in md and "comentario" not in md


def test_manifiesto_ilegible_avisa_y_sigue(tmp_path):
    root = tmp_path / "p"
    root.mkdir()
    (root / "package.json").write_text("{ roto", encoding="utf-8")
    (root / "requirements.txt").write_text("flask==3.0.0\n", encoding="utf-8")
    r = di.inventario(str(root), con_outdated=False)
    assert any("JSON ilegible" in a for a in r["avisos"]) and r["dependencias"] == 1
