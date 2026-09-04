#!/usr/bin/env python3
"""Tests de scope-check.py con repo git temporal. Ejecuta: pytest -q."""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "scope-check.py")
INI = "docs/roadmap/2026-01-01-demo"

LEDGER = """---
tasks: demo
estado: en-progreso
---
# Checklist — demo

> Ledger canónico de progreso.

## Resumen de progreso

| Fase | Completadas | Total | Progreso |
|---|---|---|---|
| Fase 1 — Uno | 0 | 2 | 0% |

## Fase 1 — Uno

### T-01 — Código

- **Descripción**: x
- **Estado**: en-progreso
- **Archivos**: `src/app.py`, `src/util/` (carpeta), `tests/test_*.py` (nuevo), `docs/{a,b}.md`, sus tests, `/tmp/fuera.txt`

**Criterios de aceptación**
- [ ] c

### T-02 — Doc

- **Descripción**: y
- **Estado**: borrador
- **Archivos**: `README.md` (nuevo), `notes/**/*.md`, `agents/*.md`

**Criterios de aceptación**
- [ ] c
"""

GIT_ENV = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
               GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")


def git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, env=GIT_ENV)


def touch(root, rel, content="x"):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w").write(content)


def repo(tmp, main="main", feature=True):
    git(tmp, "init", "-q", "-b", main)
    touch(tmp, INI + "/tasks.md", LEDGER)
    touch(tmp, "base.txt")
    git(tmp, "add", "-A")
    git(tmp, "commit", "-qm", "init")
    if feature:
        git(tmp, "checkout", "-qb", "feature/demo")
    return tmp


def run(tmp, *extra):
    r = subprocess.run([sys.executable, SCRIPT, INI, *extra], cwd=tmp, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, r.stdout, r.stderr


def commit_all(tmp, msg="wip"):
    git(tmp, "add", "-A")
    git(tmp, "commit", "-qm", msg)


def test_en_alcance_exit_0_y_declarados_sin_tocar():
    with tempfile.TemporaryDirectory() as tmp:
        repo(tmp)
        touch(tmp, "src/app.py")
        commit_all(tmp)
        code, out, _ = run(tmp)
        assert code == 0, out
        assert "fuera de alcance (0)" in out
        assert "declarados sin tocar" in out and "README.md (T-02)" in out


def test_fuera_de_alcance_exit_1_y_warn_only_0():
    with tempfile.TemporaryDirectory() as tmp:
        repo(tmp)
        touch(tmp, "src/app.py")
        touch(tmp, "otro/colado.py")
        commit_all(tmp)
        code, out, _ = run(tmp)
        assert code == 1 and "otro/colado.py" in out and "fuera de alcance (1)" in out
        code, out, _ = run(tmp, "--warn-only")
        assert code == 0 and "otro/colado.py" in out


def test_glob_carpeta_nuevo_y_llaves():
    with tempfile.TemporaryDirectory() as tmp:
        repo(tmp)
        touch(tmp, "tests/test_app.py")          # glob tests/test_*.py + «(nuevo)»
        touch(tmp, "src/util/deep/x.py")         # carpeta src/util/
        touch(tmp, "docs/b.md")                  # llaves {a,b}
        touch(tmp, "README.md")                  # (nuevo) sin glob
        commit_all(tmp)
        code, out, _ = run(tmp, "--json")
        d = json.loads(out)
        assert code == 0, out
        assert sorted(d["en_alcance"]) == ["README.md", "docs/b.md", "src/util/deep/x.py", "tests/test_app.py"]
        assert "/tmp/fuera.txt" not in d["patrones"] and "sus tests" not in d["patrones"]


def test_sin_comitear_y_sin_seguimiento_cuentan():
    with tempfile.TemporaryDirectory() as tmp:
        repo(tmp)
        touch(tmp, "base.txt", "modificado")     # modificado sin comitear → fuera
        touch(tmp, "nuevo-sin-add.py")           # untracked → fuera
        code, out, _ = run(tmp)
        assert code == 1 and "base.txt" in out and "nuevo-sin-add.py" in out


def test_tasks_md_propio_y_knowledge_siempre_en_alcance():
    with tempfile.TemporaryDirectory() as tmp:
        repo(tmp)
        touch(tmp, INI + "/tasks.md", LEDGER + "\nnota\n")
        touch(tmp, "docs/knowledge/adr/ADR-001-x.md")
        commit_all(tmp)
        code, out, _ = run(tmp)
        assert code == 0, out
        assert INI + "/tasks.md" in out and "ADR-001-x.md" in out
        # pero OTRO fichero del roadmap (spec.md) sí está fuera
        touch(tmp, INI + "/spec.md")
        code, out, _ = run(tmp)
        assert code == 1 and "spec.md" in out


def test_sin_base_clara_exit_2_y_con_base_explicita():
    with tempfile.TemporaryDirectory() as tmp:
        repo(tmp, main="trunk")                  # ni main ni master; estamos en feature/demo
        touch(tmp, "src/app.py")
        commit_all(tmp)
        code, out, err = run(tmp)
        assert code == 2 and "--base" in err and "trunk" not in out
        code, out, _ = run(tmp, "--base", "trunk")
        assert code == 0 and "src/app.py" in out


def test_en_rama_principal_base_es_head():
    with tempfile.TemporaryDirectory() as tmp:
        repo(tmp, feature=False)                 # seguimos en main
        touch(tmp, "src/app.py")                 # sin comitear
        code, out, _ = run(tmp)
        assert code == 0 and "rama principal" in out and "src/app.py" in out


def test_master_como_principal_y_ledger_inexistente():
    with tempfile.TemporaryDirectory() as tmp:
        repo(tmp, main="master")
        touch(tmp, "src/app.py")
        commit_all(tmp)
        code, out, _ = run(tmp)
        assert code == 0 and "merge-base master" in out
        r = subprocess.run([sys.executable, SCRIPT, "docs/roadmap/no-existe"], cwd=tmp,
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        assert r.returncode == 2 and "no existe" in r.stderr


def test_fix1_doble_asterisco_cero_o_mas_directorios_y_asterisco_un_nivel():
    # (4) `notes/**/*.md` casa notes/x.md (cero directorios) y notes/a/b/c.md; `agents/*.md` NO cruza `/`
    with tempfile.TemporaryDirectory() as tmp:
        repo(tmp)
        touch(tmp, "notes/knowledge_x.md")
        touch(tmp, "notes/a/b/c.md")
        touch(tmp, "agents/x.md")
        touch(tmp, "agents/sub/y.md")             # fuera: `*` es un solo nivel
        commit_all(tmp)
        code, out, _ = run(tmp, "--json")
        d = json.loads(out)
        assert code == 1, out
        assert "notes/knowledge_x.md" in d["en_alcance"] and "notes/a/b/c.md" in d["en_alcance"]
        assert "agents/x.md" in d["en_alcance"] and d["fuera_de_alcance"] == ["agents/sub/y.md"]


def test_fuera_de_git_exit_2():
    with tempfile.TemporaryDirectory() as tmp:
        touch(tmp, INI + "/tasks.md", LEDGER)
        r = subprocess.run([sys.executable, SCRIPT, INI], cwd=tmp, capture_output=True, text=True, encoding="utf-8", errors="replace",
                           env=dict(os.environ, GIT_CEILING_DIRECTORIES=os.path.dirname(tmp)))
        assert r.returncode == 2 and "git" in r.stderr
