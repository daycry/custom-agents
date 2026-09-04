#!/usr/bin/env python3
"""Tests de `scripts/release.py` (distribution T-02) sobre un repo git TEMPORAL.

Cubre las dos trampas del release v1.15.0 (2026-09-02) — `[Unreleased]`/`[Sin publicar]` sin mover y
`.sh` en modo 100644 — más los checks previos, `--dry-run`, `--check` y la ausencia de git.

Ejecutar: python3 -m pytest -q tests/test_release.py
"""
import datetime as dt
import json
import os
import shutil
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts", "release.py")
HOY = dt.date.today().isoformat()

CHANGELOG_EN = """# Changelog

## [Unreleased]

### Added
- Something new.
- Another thing.

## [1.1.0] - 2026-01-01

### Added
- Old.

[1.1.0]: https://github.com/daycry/custom-agents/releases/tag/v1.1.0
[1.0.0]: https://github.com/daycry/custom-agents/releases/tag/v1.0.0
"""
CHANGELOG_ES = CHANGELOG_EN.replace("## [Unreleased]", "## [Sin publicar]").replace("Something new", "Algo nuevo")


def git(repo, *args, check=True):
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args],
                          cwd=repo, capture_output=True, text=True, encoding="utf-8", errors="replace", check=check)


def run(repo, *args):
    return subprocess.run([sys.executable, SCRIPT, "--root", str(repo), *args], capture_output=True, text=True, encoding="utf-8", errors="replace")


def _w(p, s, mode=None):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8")
    if mode is not None:
        os.chmod(p, mode)


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "repo"
    r.mkdir()
    _w(r / ".claude-plugin" / "plugin.json", json.dumps({"name": "x", "version": "1.1.0"}, indent=2) + "\n")
    _w(r / ".claude-plugin" / "marketplace.json", json.dumps(
        {"name": "m", "metadata": {"version": "1.1.0"}, "plugins": [{"name": "x", "version": "1.1.0"}]}, indent=2) + "\n")
    _w(r / "CHANGELOG.md", CHANGELOG_EN)
    _w(r / "CHANGELOG.es.md", CHANGELOG_ES)
    _w(r / "scripts" / "lint_plugin.py", "import sys; sys.exit(0)\n")
    _w(r / "evals" / "check.py", "import sys; sys.exit(0)\n")
    _w(r / "ci.yml.MANUAL-COPY", "name: CI\n")
    _w(r / ".github" / "workflows" / "ci.yml", "name: CI\n")
    _w(r / "hooks" / "hook.sh", "#!/bin/sh\necho hi\n", 0o644)          # la trampa de Windows
    _w(r / "hooks" / "ok.sh", "#!/bin/sh\n", 0o755)
    git(r, "init", "-q")
    # Identidad EN EL REPO, no solo en los `git` del test: `release.py` corre como subproceso y hace
    # su propio `git commit`, que sin `user.email`/`user.name` falla. En una máquina de desarrollo hay
    # identidad global y no se nota; en un runner de CI no hay ninguna y estos tests se ponían rojos
    # (GOT-006). Con esto la fixture es hermética: no depende del git config de quien la ejecute.
    git(r, "config", "user.name", "t")
    git(r, "config", "user.email", "t@t")
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", "init")
    return r


def _versions(repo):
    p = json.loads((repo / ".claude-plugin" / "plugin.json").read_text())["version"]
    m = json.loads((repo / ".claude-plugin" / "marketplace.json").read_text())
    return p, m["metadata"]["version"], m["plugins"][0]["version"]


def _snapshot(repo):
    out = {}
    for dp, dn, fn in os.walk(repo):
        dn[:] = [d for d in dn if d != ".git"]
        for f in fn:
            p = os.path.join(dp, f)
            out[os.path.relpath(p, repo)] = open(p, "rb").read()
    return out


# ------------------------------------------------------------------ release completo

def test_bump_en_los_tres_sitios_y_commit_tag(repo):
    r = run(repo, "1.2.3")
    assert r.returncode == 0, r.stdout + r.stderr
    assert _versions(repo) == ("1.2.3", "1.2.3", "1.2.3")
    assert "v1.2.3" in git(repo, "tag").stdout.split()
    assert git(repo, "log", "-1", "--pretty=%s").stdout.strip() == "chore: release v1.2.3"
    assert git(repo, "status", "--porcelain").stdout == ""          # todo comiteado


def test_changelog_movido_en_ambos_idiomas(repo):
    assert run(repo, "1.2.3").returncode == 0
    en = (repo / "CHANGELOG.md").read_text(encoding="utf-8")
    es = (repo / "CHANGELOG.es.md").read_text(encoding="utf-8")
    assert f"## [Unreleased]\n\n## [1.2.3] - {HOY}\n\n### Added\n- Something new.\n- Another thing.\n\n## [1.1.0]" in en
    assert f"## [Sin publicar]\n\n## [1.2.3] - {HOY}\n\n### Added\n- Algo nuevo.\n- Another thing.\n\n## [1.1.0]" in es
    assert en.count("Something new") == 1 and es.count("Algo nuevo") == 1      # movido, no duplicado
    assert en.count("## [1.2.3]") == 1


def test_enlace_anadido_encima_de_los_existentes(repo):
    assert run(repo, "1.2.3").returncode == 0
    for nombre in ("CHANGELOG.md", "CHANGELOG.es.md"):
        t = (repo / nombre).read_text(encoding="utf-8")
        assert ("[1.2.3]: https://github.com/daycry/custom-agents/releases/tag/v1.2.3\n"
                "[1.1.0]: https://github.com/daycry/custom-agents/releases/tag/v1.1.0\n") in t
        assert t.count("[1.2.3]:") == 1


def test_release_repetido_no_duplica_seccion(repo):
    assert run(repo, "1.2.3").returncode == 0
    (repo / "CHANGELOG.md").write_text((repo / "CHANGELOG.md").read_text(encoding="utf-8")
                                       .replace("## [Unreleased]\n", "## [Unreleased]\n\n- more\n"), encoding="utf-8")
    (repo / "CHANGELOG.es.md").write_text((repo / "CHANGELOG.es.md").read_text(encoding="utf-8")
                                          .replace("## [Sin publicar]\n", "## [Sin publicar]\n\n- más\n"), encoding="utf-8")
    git(repo, "add", "-A"); git(repo, "commit", "-q", "-m", "notes")
    git(repo, "tag", "-d", "v1.2.3")
    r = run(repo, "1.2.3", "--force-version")           # misma versión: solo con --force-version
    assert r.returncode == 0 and "ya existe" in r.stdout
    assert (repo / "CHANGELOG.md").read_text(encoding="utf-8").count("## [1.2.3]") == 1


# ------------------------------------------------------------------ unreleased vacío

def test_unreleased_vacio_aborta_sin_tocar_nada(repo):
    (repo / "CHANGELOG.es.md").write_text(CHANGELOG_ES.replace("### Added\n- Algo nuevo.\n- Another thing.\n\n", "", 1), encoding="utf-8")
    git(repo, "add", "-A"); git(repo, "commit", "-q", "-m", "vacío")
    antes = _snapshot(repo)
    r = run(repo, "1.2.3")
    assert r.returncode == 1
    assert "CHANGELOG.es.md" in r.stderr and "VACÍO" in r.stderr and "--allow-empty-notes" in r.stderr
    assert _snapshot(repo) == antes
    assert "v1.2.3" not in git(repo, "tag").stdout


def test_allow_empty_notes_crea_seccion_con_placeholder(repo):
    (repo / "CHANGELOG.es.md").write_text(CHANGELOG_ES.replace("### Added\n- Algo nuevo.\n- Another thing.\n\n", "", 1), encoding="utf-8")
    git(repo, "add", "-A"); git(repo, "commit", "-q", "-m", "vacío")
    assert run(repo, "1.2.3", "--allow-empty-notes").returncode == 0
    es = (repo / "CHANGELOG.es.md").read_text(encoding="utf-8")
    assert f"## [1.2.3] - {HOY}\n\n_Sin notas._\n" in es
    assert "Something new" in (repo / "CHANGELOG.md").read_text(encoding="utf-8")   # el EN sí tenía notas


# ------------------------------------------------------------------ dry-run y check

def test_dry_run_muestra_el_plan_y_no_toca_nada(repo):
    antes = _snapshot(repo)
    r = run(repo, "1.2.3", "--dry-run")
    assert r.returncode == 0, r.stderr
    for frase in ("Plan release 1.1.0 -> 1.2.3", "CHANGELOG.md: mover 3 línea(s)", "CHANGELOG.es.md: mover 3 línea(s)",
                  "hooks/hook.sh está en modo 100644", "commit 'chore: release v1.2.3'", "tag v1.2.3",
                  "plugin.json: 1 campo(s) -> 1.2.3", "no se ha tocado nada"):
        assert frase in r.stdout, frase
    assert _snapshot(repo) == antes
    assert git(repo, "status", "--porcelain").stdout == ""
    assert "v1.2.3" not in git(repo, "tag").stdout
    assert git(repo, "ls-files", "-s", "hooks/hook.sh").stdout.startswith("100644")   # tampoco el chmod


def test_check_detecta_seccion_ausente(repo):
    r = run(repo, "--check")
    assert r.returncode == 0 and "sección [1.1.0] presente" in r.stdout
    # bump a mano sin changelog → --check falla
    for p in (repo / ".claude-plugin" / "plugin.json", repo / ".claude-plugin" / "marketplace.json"):
        p.write_text(p.read_text().replace("1.1.0", "1.9.0"))
    r = run(repo, "--check")
    assert r.returncode == 1
    assert "CHANGELOG.md no tiene sección `## [1.9.0]`" in r.stdout
    assert "CHANGELOG.es.md no tiene sección `## [1.9.0]`" in r.stdout
    # versiones incoherentes → también falla
    (repo / ".claude-plugin" / "plugin.json").write_text((repo / ".claude-plugin" / "plugin.json").read_text().replace("1.9.0", "1.8.0"))
    assert run(repo, "--check").returncode == 1


# ------------------------------------------------------------------ modo 100644

def test_sh_100644_se_corrige_y_entra_en_el_commit(repo):
    assert git(repo, "ls-files", "-s", "hooks/hook.sh").stdout.startswith("100644")
    r = run(repo, "1.2.3")
    assert r.returncode == 0
    assert "hooks/hook.sh: modo 100644 → 100755" in r.stdout
    assert git(repo, "ls-files", "-s", "hooks/hook.sh").stdout.startswith("100755")
    assert git(repo, "ls-files", "-s", "hooks/ok.sh").stdout.startswith("100755")
    assert "hooks/hook.sh" in git(repo, "show", "--stat", "--pretty=", "HEAD").stdout
    assert git(repo, "status", "--porcelain").stdout == ""


# ------------------------------------------------------------------ checks previos

def test_lint_fallando_aborta_y_skip_checks_lo_salta(repo):
    (repo / "scripts" / "lint_plugin.py").write_text("import sys; print('boom'); sys.exit(1)\n")
    git(repo, "add", "-A"); git(repo, "commit", "-q", "-m", "lint roto")
    antes = _snapshot(repo)
    r = run(repo, "1.2.3")
    assert r.returncode == 1 and "lint_plugin.py salió con 1" in r.stderr and "boom" in r.stderr
    assert _snapshot(repo) == antes and "v1.2.3" not in git(repo, "tag").stdout
    r = run(repo, "1.2.3", "--skip-checks")
    assert r.returncode == 0 and "--skip-checks" in r.stdout
    assert _versions(repo) == ("1.2.3", "1.2.3", "1.2.3")


# --- el check que CRASHEA no se disfraza de veredicto (windows-console T-02) -------------------
#
# El 2026-09-03 `lint_plugin.py` reventó con `UnicodeEncodeError` (salida a un pipe con locale
# cp1252) y salió con exit 1 — el mismo exit que «hay entradas pendientes» —, así que `release.py`
# imprimió `changelog-sync --check: PENDIENTE` y el usuario creyó que le faltaban notas.

# Crash REAL (traceback en stderr + exit 1), no un mock del mensaje.
CRASH = ("import sys\n"
         "sys.stdout.write('salida parcial\\n')\n"
         "raise UnicodeEncodeError('charmap', 'x', 0, 1, 'character maps to <undefined>')\n")


def _changelog_sync(repo, body):
    _w(repo / "skills" / "changelog-sync" / "scripts" / "changelog-sync.py", body)
    git(repo, "add", "-A"); git(repo, "commit", "-q", "-m", "changelog-sync")


def test_lint_que_crashea_se_reporta_como_error_no_como_falla(repo):
    (repo / "scripts" / "lint_plugin.py").write_text(CRASH, encoding="utf-8")
    git(repo, "add", "-A"); git(repo, "commit", "-q", "-m", "lint que revienta")
    antes = _snapshot(repo)
    r = run(repo, "1.2.3")
    salida = r.stdout + r.stderr
    assert r.returncode == 1, salida
    assert "ERROR al ejecutar (exit 1)" in r.stdout, r.stdout
    assert "FALLA" not in r.stdout, "un traceback no es un veredicto"
    assert "UnicodeEncodeError" in salida, "faltan las últimas líneas de stderr"
    assert "NO se pudo ejecutar" in r.stderr and "NO es su veredicto" in r.stderr, r.stderr
    assert _snapshot(repo) == antes and "v1.2.3" not in git(repo, "tag").stdout


def test_changelog_sync_que_crashea_bloquea_en_vez_de_decir_pendiente(repo):
    _changelog_sync(repo, CRASH)
    antes = _snapshot(repo)
    r = run(repo, "1.2.3")
    assert r.returncode == 1, r.stdout + r.stderr
    assert "changelog-sync --check: ERROR al ejecutar (exit 1)" in r.stdout, r.stdout
    assert "PENDIENTE" not in r.stdout, "el bug era exactamente presentar el crash como PENDIENTE"
    assert "UnicodeEncodeError" in r.stdout + r.stderr
    assert _snapshot(repo) == antes, "un entorno roto no debe publicar nada"


def test_changelog_sync_con_entradas_pendientes_sigue_siendo_aviso_que_no_bloquea(repo):
    _changelog_sync(repo, "import sys\n"
                          "print('changelog-sync --check: entradas PENDIENTES en el CHANGELOG:')\n"
                          "print('  \\u00b7 mi-slug (2026-09-03) \\u2014 Fixed')\n"
                          "sys.exit(1)\n")
    r = run(repo, "1.2.3")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "changelog-sync --check: PENDIENTE" in r.stdout and "mi-slug" in r.stdout
    assert "ERROR al ejecutar" not in r.stdout
    assert _versions(repo) == ("1.2.3", "1.2.3", "1.2.3"), "la deuda de notas no bloquea el release"


def test_el_slug_pendiente_se_lee_aunque_la_vineta_no_sobreviva(repo):
    """El hijo aquí NO lleva el snippet de T-01: bajo cp1252 escribe `·` en cp1252 y el padre, que
    decodifica UTF-8, lo ve como `�`. El resumen debe seguir nombrando la iniciativa."""
    _changelog_sync(repo, "import sys\n"
                          "print('changelog-sync --check: entradas PENDIENTES en el CHANGELOG:')\n"
                          "print('  \\u00b7 mi-slug (2026-09-03) \\u2014 Fixed')\n"
                          "sys.exit(1)\n")
    env = dict(os.environ, PYTHONIOENCODING="cp1252")
    r = subprocess.run([sys.executable, SCRIPT, "--root", str(repo), "1.2.3", "--dry-run"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "changelog-sync --check: PENDIENTE" in r.stdout, r.stdout
    assert "mi-slug" in r.stdout, r.stdout


def test_exit_que_no_es_0_ni_1_es_error_aunque_no_haya_traceback(repo):
    (repo / "evals" / "check.py").write_text(
        "import sys\nsys.stderr.write('uno\\ndos\\ntres\\ncuatro\\n')\nsys.exit(3)\n", encoding="utf-8")
    git(repo, "add", "-A"); git(repo, "commit", "-q", "-m", "evals con exit 3")
    r = run(repo, "1.2.3")
    assert r.returncode == 1
    assert "ERROR al ejecutar (exit 3)" in r.stdout, r.stdout
    # exactamente las 3 ÚLTIMAS líneas de stderr, no la primera
    assert "dos" in r.stdout and "tres" in r.stdout and "cuatro" in r.stdout, r.stdout
    assert "uno" not in r.stdout.split("ERROR al ejecutar")[1], r.stdout


def test_clasificar_distingue_veredicto_de_crash():
    """La regla, sin subprocess: `Traceback` en stderr manda sobre el exit code."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("release_mod", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    class R:
        def __init__(self, code, err=""):
            self.returncode, self.stderr = code, err

    assert mod.clasificar(R(0)) == "ok"
    assert mod.clasificar(R(1)) == "falla"
    assert mod.clasificar(R(2)) == "error" and mod.clasificar(R(127)) == "error"
    assert mod.clasificar(R(1, "Traceback (most recent call last):\n  ...\n")) == "error"
    assert mod.clasificar(R(0, "Traceback (most recent call last):\n")) == "error"
    assert mod.cola_stderr(R(1, "a\n\nb\nc\nd\n")) == ["b", "c", "d"]
    assert mod.cola_stderr(R(1, "")) == ["(sin stderr)"]


def test_copia_manual_divergente_aborta(repo):
    (repo / ".github" / "workflows" / "ci.yml").write_text("name: CI\n# atrasada\n")
    git(repo, "add", "-A"); git(repo, "commit", "-q", "-m", "copia atrasada")
    r = run(repo, "1.2.3")
    assert r.returncode == 1
    assert "cp ci.yml.MANUAL-COPY .github/workflows/ci.yml" in r.stderr
    assert _versions(repo) == ("1.1.0", "1.1.0", "1.1.0")


def test_arbol_github_templates_manual_copy_se_compara(repo):
    (repo / "github-templates.MANUAL-COPY" / "ISSUE_TEMPLATE").mkdir(parents=True)
    (repo / "github-templates.MANUAL-COPY" / "ISSUE_TEMPLATE" / "bug.yml").write_text("name: Bug\n")
    (repo / ".github" / "ISSUE_TEMPLATE").mkdir(parents=True)
    (repo / ".github" / "ISSUE_TEMPLATE" / "bug.yml").write_text("name: Bug\n# otra\n")
    git(repo, "add", "-A"); git(repo, "commit", "-q", "-m", "templates")
    r = run(repo, "1.2.3", "--dry-run")
    assert r.returncode == 1
    assert os.path.join("github-templates.MANUAL-COPY", "ISSUE_TEMPLATE", "bug.yml") in r.stderr


# ------------------------------------------------------------------ sin git

def test_sin_repo_git_aborta_y_no_git_escribe_ficheros(tmp_path, repo):
    plano = tmp_path / "plano"
    shutil.copytree(repo, plano, ignore=shutil.ignore_patterns(".git"))
    r = run(plano, "1.2.3")
    assert r.returncode == 1 and "no es un repositorio git" in r.stderr
    assert _versions(plano) == ("1.1.0", "1.1.0", "1.1.0")
    r = run(plano, "1.2.3", "--no-git")
    assert r.returncode == 0 and "Hecho (sin git)" in r.stdout
    assert _versions(plano) == ("1.2.3", "1.2.3", "1.2.3")
    assert f"## [1.2.3] - {HOY}" in (plano / "CHANGELOG.md").read_text(encoding="utf-8")


def test_semver_invalido(repo):
    r = run(repo, "1.2")
    assert r.returncode == 1 and "semver" in r.stderr


# ------------------------------------------------------------------ revisión intento 1 (T-fix1)

def test_arbol_sucio_aborta_antes_de_escribir(repo):
    (repo / "CHANGELOG.md").write_text(CHANGELOG_EN.replace("- Another thing.", "- Another thing.\n- A medias."), encoding="utf-8")
    antes = _snapshot(repo)
    r = run(repo, "1.2.3")
    assert r.returncode == 1 and "NO está limpio" in r.stderr and "CHANGELOG.md" in r.stderr and "--allow-dirty" in r.stderr
    assert _snapshot(repo) == antes and "v1.2.3" not in git(repo, "tag").stdout
    assert _versions(repo) == ("1.1.0", "1.1.0", "1.1.0")
    # --dry-run lo marca pero no se corta; --allow-dirty sigue
    r = run(repo, "1.2.3", "--dry-run")
    assert r.returncode == 0 and "ABORTARÍA" in r.stdout and "NO está limpio" in r.stdout
    assert _snapshot(repo) == antes
    r = run(repo, "1.2.3", "--allow-dirty")
    assert r.returncode == 0 and "A medias." in (repo / "CHANGELOG.md").read_text(encoding="utf-8")


def test_version_menor_o_igual_aborta_salvo_force(repo):
    for v in ("0.9.0", "1.1.0", "1.0.99"):
        r = run(repo, v)
        assert r.returncode == 1 and "no es mayor que la actual 1.1.0" in r.stderr and "--force-version" in r.stderr, v
    assert _versions(repo) == ("1.1.0", "1.1.0", "1.1.0") and git(repo, "tag").stdout == ""
    r = run(repo, "0.9.0", "--force-version")
    assert r.returncode == 0 and "--force-version" in r.stdout
    assert _versions(repo) == ("0.9.0", "0.9.0", "0.9.0")


def test_tag_existente_aborta_en_los_checks_previos(repo):
    git(repo, "tag", "v1.2.3")
    head = git(repo, "rev-parse", "HEAD").stdout
    antes = _snapshot(repo)
    r = run(repo, "1.2.3")
    assert r.returncode == 1 and "el tag v1.2.3 ya existe" in r.stderr
    assert _snapshot(repo) == antes
    assert git(repo, "rev-parse", "HEAD").stdout == head          # ningún commit creado
    assert "Aplicando" not in r.stdout


def test_crlf_se_conserva(repo):
    for nombre in ("CHANGELOG.md", "CHANGELOG.es.md"):
        p = repo / nombre
        p.write_bytes(p.read_text(encoding="utf-8").replace("\n", "\r\n").encode("utf-8"))
    git(repo, "add", "-A"); git(repo, "commit", "-q", "-m", "crlf")
    r = run(repo, "1.2.3")
    assert r.returncode == 0 and "CRLF conservado" in r.stdout
    for nombre in ("CHANGELOG.md", "CHANGELOG.es.md"):
        raw = (repo / nombre).read_bytes()
        assert b"\r\n" in raw
        assert raw.count(b"\n") == raw.count(b"\r\n"), nombre        # ni una sola línea con LF suelto
        assert f"## [1.2.3] - {HOY}\r\n".encode() in raw
        assert b"[1.2.3]: https://github.com/daycry/custom-agents/releases/tag/v1.2.3\r\n" in raw
    # y un fichero LF sigue LF
    (repo / "CHANGELOG.md").write_text(CHANGELOG_EN.replace("## [1.1.0]", "## [1.2.3] - x\n\n## [1.1.0]"), encoding="utf-8")
    assert b"\r\n" not in (repo / "CHANGELOG.md").read_bytes()


# --------------------------------------------------------- identidad de git: la trampa del runner

def test_la_fixture_configura_la_identidad_DENTRO_del_repo(repo):
    """La fixture no puede depender del `git config --global` de quien ejecute la suite (GOT-006).

    `release.py` corre como SUBPROCESO y hace su propio `git commit`. Los `git` del test pasan
    `-c user.name/-c user.email`, pero eso no alcanza al subproceso: la identidad tiene que estar
    en el repo. En una máquina de desarrollo hay identidad global y estos 11 tests pasaban; en un
    runner de GitHub Actions no hay ninguna y se ponían rojos — y no se vio antes porque
    `tests/test_release.py` no entraba en el `pytest` de la CI hasta `changelog-brief` T-07.
    """
    for clave in ("user.name", "user.email"):
        r = subprocess.run(["git", "config", "--local", "--get", clave], cwd=repo,
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        assert r.returncode == 0 and r.stdout.strip(), (
            f"la fixture debe fijar {clave} en el repo: sin identidad LOCAL, el `git commit` de "
            f"release.py falla en cualquier entorno sin identidad global (CI)")


def test_sin_identidad_release_degrada_con_mensaje_y_no_revienta(repo):
    """Y el contrato del PRODUCTO bajo esa misma condición: degrada, no revienta.

    Un usuario con git recién instalado y sin identidad configurada existe. `release.py` debe
    escribir los ficheros, decir qué falta y dar el comando a mano — nunca un traceback.
    """
    subprocess.run(["git", "config", "--local", "--unset-all", "user.name"], cwd=repo, capture_output=True)  # bytes: solo se mira el rc
    subprocess.run(["git", "config", "--local", "--unset-all", "user.email"], cwd=repo, capture_output=True)  # bytes: solo se mira el rc
    entorno = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull}
    r = subprocess.run([sys.executable, SCRIPT, "--root", str(repo), "1.2.3"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env=entorno)
    assert "Traceback" not in r.stderr, f"no debe reventar; stderr:\n{r.stderr[-400:]}"
    assert r.returncode == 1
    # el aviso de degradación va a stderr (es un error de entorno, no salida del plan)
    assert "git commit" in r.stderr, f"debe dar el comando a mano; stderr:\n{r.stderr[-400:]}"
    assert "los ficheros quedaron actualizados" in r.stderr
    # y los ficheros SÍ quedaron escritos: el trabajo no se pierde por no poder comitear
    assert _versions(repo) == ("1.2.3", "1.2.3", "1.2.3")
