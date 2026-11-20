#!/usr/bin/env python3
"""Tests de guardrail-check.py: ciclo fix25 de T-06 (plugin-audit-2, fase 1, intento 20). Ejecuta: pytest -q.

El intento 20 mostro que la lista blanca de fix24 filtraba SUBCOMANDOS pero no sus OPCIONES ni la rama sobre la que actuan. fix25 la extiende por clase:
  - `DENEGADAS25`: las formas reproducidas (`rebase --update-refs`, `--refmap`/`-u` en fetch|pull, borrar y recrear la principal, `-C <wt en la principal>`, `--no-verify`...) y una
    opcion desconocida por cada subcomando que escribe: todas en deny;
  - `PERMITIDAS25`: la fluidez del gap 6 (`$(git branch --show-current)`, `refs/heads/<rama>`) y las ordenes normales nuevas del control negativo: 0 deny.
"""
import pytest

from test_guardrail_fix12 import gc
from test_guardrail_fix16 import _git, repo  # noqa: F401
from test_guardrail_fix18 import con_worktrees, repo18  # noqa: F401  (fixtures)


def _id(o):
    return o.encode("unicode_escape").decode("ascii")[:70]


DENEGADAS25 = [
    # 1: --update-refs reescribe otras ramas locales
    "git rebase --update-refs --onto nb HEAD~3", "git rebase --update-refs main", "git rebase --update-r main", "git rebase -i --update-refs main",
    # 2: --refmap / -u / --update-head-ok mueven ramas locales en fetch y pull
    "git fetch --refmap=+refs/heads/*:refs/heads/* origin main", "git fetch --refmap=+refs/heads/feature/x:refs/heads/main origin main",
    "git fetch --update-head-ok --refmap=+HEAD:refs/heads/main origin main", "git pull --no-rebase --refmap=+refs/heads/*:refs/heads/* origin main",
    'git fetch "--refmap=+refs/heads/*:refs/heads/*" origin main', "git fetch -u origin main", "git fetch --update-head-ok origin", "git pull -u origin main", "git fetch --refmap= origin",
    "/mingw64/bin/git fetch --refmap=+refs/heads/*:refs/heads/* origin main",
    # 3: borrar la principal / la rama actual y recrearla
    "git branch -d main", "git branch --delete main", "git branch -d master", "git branch -d feature/x", "git branch -d refs/heads/main", "git branch main HEAD", "git branch main", "git branch -t main origin/main",
    "git switch -c main", "git switch --create main", "git switch -cmain", "git checkout -b main", "git checkout -bmain", "git worktree add ../w -b main", "git worktree add ../w main",
    "git worktree add ../w", "git worktree add --detach ../w main",
    # 4: comillas: la shell no expande `~` ni `$VAR` entre comillas simples, ni `~` entre dobles
    "git -C '~/m' merge feature/x", 'git -C "~/m" merge feature/x', "git -C '$PWD/m' merge feature/x", "git worktree add '~/m' main",
    # 7: --no-verify en merge/pull/rebase como en commit/push
    "git merge --no-verify main", "git pull --no-verify", "git rebase --no-verify main",
    # clase: una opcion desconocida por subcomando que escribe
    "git merge --strategy=ours x", "git merge -s ours x", "git merge --unknown x", "git commit --unknown", "git commit -m x --exec=y", "git stash push --unknown", "git reset --unknown",
    "git restore --unknown a", "git rm --unknown a", "git mv --unknown a b", "git cherry-pick --unknown x", "git revert --unknown HEAD", "git apply --unknown p", "git add --unknown a",
    "git switch --unknown x", "git checkout --unknown x", "git worktree add --unknown ../w -b x", "git pull --unknown", "git fetch --unknown", "git branch --unknown", "git rebase --unknown x",
    "git commit -Z", "git merge -Z x", "git rebase -Z x", "git push --unknown",
]

PERMITIDAS25 = [
    # 6: fluidez
    'git push -u origin "$(git branch --show-current)"', "git push -u origin $(git rev-parse --abbrev-ref HEAD)", 'git push origin "$(git branch --show-current)"',
    "git push origin refs/heads/feature/x", "git push origin refs/heads/feature/x:refs/heads/feature/x", "git push -u origin refs/heads/feature/x",
    # control negativo ampliado (B20 a)
    "git add -p", "git add -u", "git commit -m 'T-01: x' -- a.txt", "git commit --amend", "git commit -am x", "git commit -S -m x", "git commit --fixup=abc1234", "git commit --allow-empty -m x",
    "git commit -s -m x", "git stash push -m x", "git stash push -u -m x", "git stash show -p", "git diff --stat main...HEAD", "git log origin/main..HEAD", "git push -u origin feature/x",
    "git switch -c feature/z", "git checkout -b feature/z", "git restore --staged a.txt", "git restore --source=HEAD~1 a.txt", "git rm --cached a.txt", "git rm -r --cached d", "git mv a.txt b.txt",
    "git merge main", "git merge --no-ff -m x main", "git merge --squash main", "git merge --ff-only main", "git merge --abort", "git merge --continue",
    "git rebase --continue", "git rebase --abort", "git rebase --skip", "git rebase --autosquash -i main", "git rebase --onto main HEAD~3", "git rebase -x 'make test' main", "git rebase --autostash main",
    "git rebase --no-update-refs main", "git --no-pager log", "git -c color.ui=false -C sub commit -m x", "git pull --rebase", "git pull --no-rebase", "git pull --ff-only", "git pull --rebase --autostash",
    "git fetch --tags", "git fetch --all --prune", "git fetch -p origin", "git fetch --depth=1 origin", "git branch -vv", "git branch --list 'feat*'", "git branch -d old-branch", "git branch -a",
    "git branch --contains HEAD", "git branch --merged", "git reset --soft HEAD~1", "git reset -q HEAD a.txt", "git cherry-pick -x abc1234", "git cherry-pick --continue", "git revert --no-edit HEAD",
    "git apply --check --stat p.patch", "git apply -3 p.patch", "git worktree add ../wt -b feature/y", "git worktree add -b feature/y ../wt", "git worktree list --porcelain", "git worktree prune -n",
    "git checkout -- a.txt", "git checkout --ours -- a.txt", "git switch feature/x", "git stash pop --index",
    "git commit -m \"$(cat <<'EOF'\nT-01: x\n\nCuerpo\nEOF\n)\"",
]


@pytest.mark.parametrize("orden", DENEGADAS25, ids=[_id(o) for o in DENEGADAS25])
def test_fix25_deniega_la_clase(repo18, orden):
    assert gc.check_git(orden, "feature/x"), orden


@pytest.mark.parametrize("orden", PERMITIDAS25, ids=[_id(o) for o in PERMITIDAS25])
def test_fix25_control_negativo_y_fluidez(repo18, orden):
    assert gc.check_git(orden, "feature/x") is None, orden


def test_fix25_cifras(repo18):
    den = [o for o in PERMITIDAS25 if gc.check_git(o, "feature/x")]
    no_den = [o for o in DENEGADAS25 if not gc.check_git(o, "feature/x")]
    print("fix25: corpus deny %d (sin denegar: %d) · control negativo %d (denegadas: %d)" % (len(DENEGADAS25), len(no_den), len(PERMITIDAS25), len(den)))
    assert den == [] and no_den == []


def test_la_sustitucion_solo_vale_si_es_la_rama_actual_exacta(repo18):
    assert gc.check_git('git push origin "$(echo main)"', "feature/x")
    assert gc.check_git('git push origin "$(git branch --show-current; echo main)"', "feature/x")
    assert gc.check_git("git push origin $(git branch --show-current) $(echo x)", "feature/x")


def test_el_mensaje_de_opcion_dice_que_se_acepta(repo18):
    razon = gc.check_git("git rebase --update-refs main", "feature/x")
    assert razon and "--update-refs" in razon and "--continue" in razon


def test_C_hacia_un_worktree_con_head_en_la_principal_solo_lee(con_worktrees):
    prin, wt = con_worktrees
    for o in ("git -C P push origin main", "git -C P push", "git -C P add a.txt", "git -C P commit -m x", "git -C P stash push", "git -C P fetch", "git -C P branch -d x", "git -C P branch"):   # `branch` escribe: no es de lectura aunque liste
        assert gc.check_git(o.replace("P", prin, 1), "feature/x"), o
    for o in ("git -C P status", "git -C P log --oneline", "git -C P diff", "git -C P rev-parse HEAD", "git -C P show HEAD"):
        assert gc.check_git(o.replace("P", prin, 1), "feature/x") is None, o
    for o in ("git -C P status", "git -C P commit -m x", "git -C P push origin feature/x", "git -C P add a.txt"):
        assert gc.check_git(o.replace("P", wt, 1), "feature/x") is None, o
