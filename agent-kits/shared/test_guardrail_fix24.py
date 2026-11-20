#!/usr/bin/env python3
"""Tests de guardrail-check.py: ciclo fix24 de T-06 (plugin-audit-2, fase 1, intento 19). Ejecuta: pytest -q.

Decision del usuario (2026-11-20): la guarda de git del implementer pasa a LISTA BLANCA (politica unica, ADR-023) en lugar de perseguir formas sueltas. Estos tests prueban la CLASE:
  - `DENEGADAS24`: las formas que las lentes de los intentos 18 y 19 encontraron (DWIM de remota, `checkout -`/SHA/ruta homonima, `-C` irresoluble, refspec con `@`, `gc --prune=<fecha>`,
    `branch -m`, `fast-import`, `send-email --*-cmd`, `bisect reset`...) y lo que ninguna lente penso (`tag`, `notes`, `remote`, `clean -f`, `am`, `clone`...): todas en deny;
  - `NORMALES24`: el control negativo (las ordenes normales del implementer en SU rama de trabajo): todas en allow (0 deny);
  - las opciones globales que cambian el repositorio o ejecutan programas, y la resolucion de `-C` (`/c/...`, 8.3, `$PWD`, `~`).
Los envoltorios encadenados siguen siendo limite conocido (la lista blanca se aplica a lo que el guard reconoce como git).
"""
import ctypes
import os

import pytest

from test_guardrail_fix12 import gc
from test_guardrail_fix16 import _git, repo  # noqa: F401  (`repo` es un fixture)
from test_guardrail_fix18 import con_worktrees, repo18  # noqa: F401  (fixtures)


def _id(o):
    return o.encode("unicode_escape").decode("ascii")[:70]


DENEGADAS24 = [
    # ref gana a ruta / DWIM de remota / `-` / SHA / ruta sin `--`
    "git checkout main --", "git checkout foo --", "git switch main --", "git checkout -q main --", "git checkout -", "git switch -", "git checkout main", "git checkout origin/main",
    "git switch feature/y", "git checkout docs", "git checkout src", "git checkout a.txt", "git checkout v1.0",
    # `-C` con destino que solo la shell resuelve y subcomando de escritura
    'git -C "$X" merge feat', "git -C $WT commit -am x", 'git -C "$(pwd)/x" reset --soft HEAD~1', "git -C ~otro/x merge feat", "git -C ../w* pull", "git -C $X add .", "git -C $X checkout -- a.txt",
    # opciones globales que cambian el repositorio o ejecutan programas
    "git --git-dir=.git status", "git --git-dir .git status", "git --work-tree .. status", "git --work-tree=.. status", "git --exec-path=/x status", "git --bare log", "git --namespace=x log", "git --super-prefix=x status", "git --config-env=a=B log",
    "git -c core.pager=x log", "git -c alias.x=!y status", "git --unknown-option status",
    # push solo de la rama actual
    "git push . @:main", "git push . HEAD@{0}:main", "git push origin @:main", "git push origin HEAD:main", "git push origin feature/y:feature/y", "git push origin main", "git push . HEAD:x",
    "git push --force-with-lease", "git push --no-verify", "git push --delete origin x", "git push --mirror", "git push origin +feature/x", "git fetch . +@:main", "git fetch . feature/x:main",
    "git fetch origin +main:main", "git pull . feature/x:main",
    # subcomandos fuera de la lista
    "git gc", "git gc --auto", "git gc --prune=now", "git gc --prune=1.second.ago", "git gc --prune=yesterday", "git prune", "git fast-import --force", "git fast-import",
    "git send-email --to-cmd='git reset --hard #' p.patch", "git send-email --dry-run --sendmail-cmd=x p", "git bisect reset", "git bisect start", "git bisect good HEAD~1", "git bisect run make",
    "git branch -m main old-main", "git branch -m main", "git branch -M main", "git branch -c feature/x main", "git branch -m feature/y", "git branch --move a b", "git branch -D x", "git branch -f main HEAD",
    "git tag v1", "git tag -a v1 -m x", "git tag -d v1", "git tag -f v1", "git notes add -m x", "git remote add o u", "git remote set-url origin x", "git remote remove origin",
    "git clean -fd", "git clean -fdx", "git clean", "git stash drop", "git stash clear", "git stash branch x", "git worktree move a b", "git worktree add --force ../w -b x", "git worktree lock ../w",
    "git update-ref refs/heads/main HEAD", "git symbolic-ref HEAD refs/heads/main", "git filter-branch -- --all", "git am p.patch", "git archive HEAD", "git difftool", "git clone https://e.com/x.git y",
    "git ls-remote origin", "git replace a b", "git hash-object -w f", "git commit-tree HEAD^{tree}", "git checkout-index -f -a", "git read-tree -u HEAD", "git reflog expire --all", "git reflog delete HEAD@{1}",
    "git reset --hard", "git reset --keep HEAD", "git rm -f a.txt", "git submodule add u p", "git submodule deinit sub", "git gui", "git daemon", "git instaweb", "git credential fill",
]

NORMALES24 = [
    # lectura
    "git status", "git status -sb", "git diff", "git diff --stat HEAD~1", "git diff --cached", "git log --oneline -5", "git log -p -- src", "git show HEAD", "git show HEAD:a.txt",
    "git rev-parse HEAD", "git rev-parse --abbrev-ref HEAD", "git ls-files", "git blame a.txt", "git grep foo", "git grep -n -e foo -- src", "git config --get user.name", "git config --list",
    "git remote -v", "git remote show origin", "git merge-base main HEAD", "git describe --tags", "git cat-file -p HEAD", "git shortlog -sn", "git worktree list", "git branch", "git branch --show-current",
    "git branch -a", "git tag", "git tag -l", "git tag --contains HEAD", "git notes list", "git reflog", "git reflog show HEAD", "git stash list", "git bisect log", "git bisect visualize",
    "git ls-tree HEAD", "git rev-list --count HEAD", "git show-ref", "git for-each-ref refs/heads", "git diff-tree --no-commit-id -r HEAD",
    # escritura en la rama de trabajo
    "git add -- a.txt", "git add src/main.py", "git add -A", "git commit -m 'T-01: x'", "git commit --amend --no-edit", "git mv a.txt b.txt", "git rm a.txt", "git rm --cached a.txt", "git revert HEAD",
    "git reset --soft HEAD~1", "git reset --mixed HEAD~1", "git reset HEAD a.txt", "git cherry-pick abc1234", "git merge main", "git merge --abort", "git rebase main", "git rebase -i HEAD~3", "git rebase -S main",
    "git switch -c feature/y", "git checkout -b feature/y", "git checkout feature/x", "git switch feature/x", "git checkout HEAD", "git checkout -- a.txt", "git checkout HEAD -- a.txt",
    "git checkout main -- a.txt", "git restore --staged a.txt", "git restore --staged .", "git stash", "git stash push -m x", "git stash pop", "git stash apply", "git stash show -p",
    "git branch feature/n", "git branch -d feature/old", "git push", "git push -u origin feature/x", "git push origin feature/x", "git push origin HEAD", "git push origin HEAD:feature/x",
    "git push origin feature/x:feature/x", "git fetch", "git fetch origin", "git fetch --all --prune", "git pull", "git pull --ff-only", "git pull origin feature/x",
    "git worktree add ../wt -b feature/y", "git worktree remove ../wt", "git worktree prune", "git apply --check p.patch", "git apply p.patch", "git format-patch -1", "git clean -n", "git clean --dry-run -d",
    "git submodule status", "git submodule update --init --recursive",
    # opciones globales inocuas y `-C` de lectura
    "git -C sub status", "git -C ../other-repo log --oneline", "git --no-pager log", "git -c color.ui=always diff", "git -c core.quotepath=false status", "git -C sub add a.txt", 'git -C "$X" status',
    'git -C "$X" log --oneline', "git -C $WT diff", 'git -C "$X" show HEAD', "git -C ~otro/x rev-parse HEAD",
]


@pytest.mark.parametrize("orden", DENEGADAS24, ids=[_id(o) for o in DENEGADAS24])
def test_la_lista_blanca_deniega_la_clase(repo18, orden):
    assert gc.check_git(orden, "feature/x"), orden


@pytest.mark.parametrize("orden", NORMALES24, ids=[_id(o) for o in NORMALES24])
def test_el_control_negativo_las_ordenes_normales_siguen_permitidas(repo18, orden):
    assert gc.check_git(orden, "feature/x") is None, orden


def test_cifra_del_control_negativo(repo18):
    denegadas = [o for o in NORMALES24 if gc.check_git(o, "feature/x")]
    print("control negativo: %d ordenes normales, %d denegadas" % (len(NORMALES24), len(denegadas)))
    assert denegadas == []


def test_el_sha_corto_con_un_fichero_homonimo_se_deniega(repo18):
    sha = _git(repo18, "rev-parse", "--short=7", "HEAD").stdout.strip()
    (repo18 / sha).write_text("x")
    (repo18 / "-").write_text("x")
    assert gc.check_git(f"git checkout {sha}", "feature/x")
    assert gc.check_git("git checkout -", "feature/x")
    assert gc.check_git(f"git checkout -- {sha}", "feature/x") is None
    assert gc.check_git("git checkout -- -", "feature/x") is None


def test_git_real_dwim_de_remota_crea_la_rama_local_y_se_deniega(repo, monkeypatch):
    assert _git(repo, "config", "remote.origin.url", ".").returncode == 0
    assert _git(repo, "config", "remote.origin.fetch", "+refs/heads/*:refs/remotes/origin/*").returncode == 0   # sin la remota configurada git no hace el DWIM
    assert _git(repo, "update-ref", "refs/remotes/origin/main", "HEAD").returncode == 0
    (repo / "main").mkdir()
    (repo / "main" / "k.txt").write_text("k")
    monkeypatch.chdir(repo)
    assert gc.check_git("git checkout main --", "feature/x")
    assert _git(repo, "checkout", "main", "--").returncode == 0
    assert _git(repo, "symbolic-ref", "--short", "HEAD").stdout.strip() == "main"


@pytest.mark.parametrize("orden", ["git merge x", "git cherry-pick abc", "git pull", "git rebase x", "git revert HEAD"])
def test_integrar_solo_hacia_la_rama_de_trabajo(repo18, orden):
    assert gc.check_git(orden, "main"), orden
    assert gc.check_git(orden, "feature/x") is None


def test_el_mensaje_de_deny_dice_que_se_permite(repo18):
    razon = gc.check_git("git gc", "feature/x")
    assert razon and "lista blanca" in razon and "status" in razon and "push" in razon
    assert "bisect reset" not in open(gc.__file__, encoding="utf-8").read()


# --------------------------------------------------------------------------- resolucion de `-C` (gap 5) ----
def _bash_style(p):
    p = p.replace("\\", "/")
    return "/" + p[0].lower() + p[2:] if len(p) > 2 and p[1] == ":" else p


def _corta(p):
    buf = ctypes.create_unicode_buffer(1024)
    return buf.value if ctypes.windll.kernel32.GetShortPathNameW(p, buf, 1024) else p


@pytest.mark.skipif(os.name != "nt", reason="`/c/...` es la ruta de Git Bash en Windows")
def test_C_ruta_de_git_bash(con_worktrees):
    prin, wt = con_worktrees
    assert gc.check_git(f"git -C {_bash_style(prin)} merge feature/x", "feature/x"), "`/c/...` es lo que imprime `pwd` en Git Bash"
    assert gc.check_git(f"git -C {_bash_style(wt)} merge main", "feature/x") is None


@pytest.mark.skipif(os.name != "nt", reason="rutas cortas 8.3 de Windows")
def test_C_ruta_corta_8_3(con_worktrees):
    prin, wt = con_worktrees
    assert gc.check_git(f"git -C {_corta(prin).replace(chr(92), '/')} merge feature/x", "feature/x")


def test_C_pwd_y_home_se_expanden(con_worktrees, tmp_path, monkeypatch):
    prin, wt = con_worktrees
    rel = os.path.relpath(prin, wt).replace("\\", "/")
    assert gc.check_git(f'git -C "$PWD/{rel}" merge feature/x', "feature/x")
    assert gc.check_git(f"git -C ${{PWD}}/{rel} merge feature/x", "feature/x")
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    assert gc.check_git("git -C ~/p merge feature/x", "feature/x"), "`~/p` = el repositorio principal del fixture"
    assert gc.check_git("git -C ~/wt-feature merge main", "feature/x") is None
