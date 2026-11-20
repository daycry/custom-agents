#!/usr/bin/env python3
"""Tests de guardrail-check.py: ciclo fix24 de T-06 (plugin-audit-2, fase 1, intento 19). Ejecuta: pytest -q.

Gap 4: DWIM de remota (`git checkout main --` sin `main` local, con `origin/main` y un directorio `main`). Gap 5: `-C` hacia un worktree en `main` con rutas de Git Bash, 8.3, `$PWD` y `~`.
Gaps 6-11: `@` como origen de refspec, `gc --prune=<fecha>`, `checkout -`/SHA con fichero homonimo, `branch -m/-c`, `fast-import`, opciones de `send-email` que ejecutan shell.
Gap 24: `git bisect reset` se deniega a proposito (corpus fix18) y ningun mensaje lo recomienda.
"""
import ctypes
import os
from pathlib import Path

import pytest

from test_guardrail_fix12 import gc
from test_guardrail_fix16 import _git, repo  # noqa: F401  (`repo` es un fixture)
from test_guardrail_fix18 import con_worktrees, _sin_git_env  # noqa: F401  (`con_worktrees` es un fixture)

HERE = Path(__file__).resolve().parent


# --------------------------------------------------------------------------- gap 4: DWIM de remota ----
@pytest.fixture
def repo_dwim(repo, monkeypatch):
    """HEAD en `feature/x`, SIN rama local `main` ni `foo`, con `origin/main` y `origin/foo` y un directorio con cada nombre."""
    assert _git(repo, "config", "remote.origin.url", ".").returncode == 0
    assert _git(repo, "config", "remote.origin.fetch", "+refs/heads/*:refs/remotes/origin/*").returncode == 0   # sin la remota configurada git no hace el DWIM
    for r in ("main", "foo"):
        assert _git(repo, "update-ref", "refs/remotes/origin/" + r, "HEAD").returncode == 0
        (repo / r).mkdir()
        (repo / r / "k.txt").write_text("k")
    monkeypatch.chdir(repo)
    _sin_git_env(monkeypatch)
    return repo


@pytest.mark.parametrize("orden", ["git checkout main --", "git checkout foo --", "git switch main --", "git checkout -q main --"])
def test_gap4_la_remota_con_nombre_de_ruta_se_deniega(repo_dwim, orden):
    assert gc.check_git(orden, "feature/x"), orden


def test_gap4_con_las_refs_empaquetadas_tambien(repo_dwim):
    assert _git(repo_dwim, "pack-refs", "--all").returncode == 0
    assert gc.check_git("git checkout main --", "feature/x")


def test_gap4_git_real_crea_la_rama_local_y_cambia(repo_dwim):
    assert _git(repo_dwim, "checkout", "main", "--").returncode == 0
    assert _git(repo_dwim, "symbolic-ref", "--short", "HEAD").stdout.strip() == "main"


def test_gap4_una_ruta_que_no_es_remota_sigue_permitida(repo_dwim):
    (repo_dwim / "solo-ruta").mkdir()
    assert gc.check_git("git checkout solo-ruta", "feature/x") is None
    assert gc.check_git("git checkout -- main", "feature/x") is None


# --------------------------------------------------------------------------- gap 5: `-C` con rutas que el guard no resolvia ----
def _bash_style(p):
    p = p.replace("\\", "/")
    return "/" + p[0].lower() + p[2:] if len(p) > 2 and p[1] == ":" else p


def _corta(p):
    buf = ctypes.create_unicode_buffer(1024)
    return buf.value if ctypes.windll.kernel32.GetShortPathNameW(p, buf, 1024) else p


@pytest.mark.skipif(os.name != "nt", reason="`/c/...` es la ruta de Git Bash en Windows")
def test_gap5_ruta_de_git_bash(con_worktrees):
    prin, wt = con_worktrees
    assert gc.check_git(f"git -C {_bash_style(prin)} merge feature/x", "feature/x"), "`/c/...` es lo que imprime `pwd` en Git Bash"
    assert gc.check_git(f"git -C {_bash_style(wt)} merge main", "feature/x") is None


@pytest.mark.skipif(os.name != "nt", reason="rutas cortas 8.3 de Windows")
def test_gap5_ruta_corta_8_3(con_worktrees):
    prin, wt = con_worktrees
    corta = _corta(prin).replace("\\", "/")
    assert gc.check_git(f"git -C {corta} merge feature/x", "feature/x")


def test_gap5_pwd_y_home_se_expanden(con_worktrees, tmp_path, monkeypatch):
    prin, wt = con_worktrees
    rel = os.path.relpath(prin, wt).replace("\\", "/")
    assert gc.check_git(f'git -C "$PWD/{rel}" merge feature/x', "feature/x")
    assert gc.check_git(f"git -C ${{PWD}}/{rel} merge feature/x", "feature/x")
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    assert gc.check_git("git -C ~/p merge feature/x", "feature/x"), "`~/p` = el repositorio principal del fixture"
    assert gc.check_git("git -C ~/wt-feature merge main", "feature/x") is None


@pytest.mark.parametrize("orden", ['git -C "$X" merge feat', "git -C $WT commit -am x", 'git -C "$(pwd)/x" reset --soft HEAD~1', "git -C ~otro/x merge feat", "git -C ../w* pull"])
def test_gap5_un_destino_irresoluble_con_una_orden_que_mueve_historia_se_deniega(con_worktrees, orden):
    assert gc.check_git(orden, "feature/x"), orden


@pytest.mark.parametrize("orden", ['git -C "$X" status', 'git -C "$X" log --oneline', "git -C $WT diff", 'git -C "$X" show HEAD', "git -C ~otro/x branch"])
def test_gap5_las_ordenes_de_lectura_con_destino_irresoluble_siguen_permitidas(con_worktrees, orden):
    assert gc.check_git(orden, "feature/x") is None, orden


# --------------------------------------------------------------------------- gaps 6-11 ----
@pytest.mark.parametrize("orden", ["git push . @:main", "git push . HEAD@{0}:main", "git fetch . +@:main", "git push origin @:main", "git push . feature/x@{0}:main"])
def test_gap6_arroba_como_origen_del_refspec(orden):
    assert gc.check_git(orden, "feature/x"), orden


@pytest.mark.parametrize("orden", ["git push git@host:grp/x.git", "git push origin feature/x", "git fetch git@host:grp/x.git main:refs/remotes/o/main"])
def test_gap6_las_urls_scp_siguen_permitidas(orden):
    assert gc.check_git(orden, "feature/x") is None, orden


@pytest.mark.parametrize("orden", ["git gc --prune=1.second.ago", "git gc --prune=yesterday", "git gc --prune=2020-01-01", "git gc --prune=now", "git gc --prune=all", "git gc --prune=1.hour.ago"])
def test_gap7_prune_con_una_fecha_corta_se_deniega(orden):
    assert gc.check_git(orden, "feature/x"), orden


@pytest.mark.parametrize("orden", ["git gc", "git gc --auto", "git gc --prune=2.weeks.ago", "git gc --prune=never", "git gc --prune=3.months.ago", "git gc --aggressive"])
def test_gap7_gc_a_secas_y_la_gracia_por_defecto_siguen_permitidos(orden):
    assert gc.check_git(orden, "feature/x") is None, orden


@pytest.fixture
def repo_ficheros(repo, monkeypatch):
    sha = _git(repo, "rev-parse", "--short=7", "HEAD").stdout.strip()
    (repo / "-").write_text("x")
    (repo / sha).write_text("x")
    _git(repo, "branch", "main")
    monkeypatch.chdir(repo)
    _sin_git_env(monkeypatch)
    return repo, sha


def test_gap8_menos_y_sha_cuentan_como_ref_aunque_haya_un_fichero_homonimo(repo_ficheros):
    repo, sha = repo_ficheros
    assert gc.check_git("git checkout -", "feature/x")
    assert gc.check_git(f"git checkout {sha}", "feature/x")
    assert gc.check_git("git switch -", "feature/x")
    assert gc.check_git("git checkout -- -", "feature/x") is None
    assert gc.check_git(f"git checkout -- {sha}", "feature/x") is None
    assert gc.check_git("git checkout HEAD", "feature/x") is None


@pytest.mark.parametrize("orden", ["git branch -m main old-main", "git branch -m main", "git branch -M main", "git branch -m feature/x main", "git branch --move main x", "git branch -mf main",
                                   "git branch -C feature/x main", "git branch -c feature/x main", "git branch --copy -f feature/x master"])
def test_gap9_branch_move_o_copy_sobre_la_rama_principal(orden):
    assert gc.check_git(orden, "feature/x"), orden


@pytest.mark.parametrize("orden", ["git branch -m feature/y", "git branch -m feature/x feature/z", "git branch -c feature/x feature/copia", "git branch feature/n", "git branch -d feature/old", "git branch"])
def test_gap9_branch_move_entre_ramas_de_trabajo_sigue_permitido(orden):
    assert gc.check_git(orden, "feature/x") is None, orden


@pytest.mark.parametrize("orden", ["git fast-import --force", "git fast-import", "git fast-import --quiet < stream", "git -C . fast-import --force"])
def test_gap10_fast_import_se_deniega(orden):
    assert gc.check_git(orden, "feature/x"), orden


@pytest.mark.parametrize("opcion", ["--to-cmd", "--cc-cmd", "--header-cmd", "--sendmail-cmd"])
def test_gap11_send_email_ejecuta_shell(opcion):
    assert gc.check_git(f"git send-email --dry-run --confirm=never {opcion}='git reset --hard #' p.patch", "feature/x")
    assert gc.check_git(f"git send-email {opcion} 'git clean -fdx' p.patch", "feature/x")
    assert gc.check_git(f"git send-email --dry-run {opcion}='echo a@b' p.patch", "feature/x") is None


# --------------------------------------------------------------------------- gap 24 ----
def test_gap24_bisect_reset_se_deniega_y_ningun_mensaje_lo_recomienda():
    assert gc.check_git("git bisect reset", "feature/x")
    assert "bisect reset" not in (HERE / "guardrail-check.py").read_text(encoding="utf-8")
