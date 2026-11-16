"""Corpus de fix17 (T-06, plugin-audit-2, intento 17): clases que el guardarrail de fix16 dejaba pasar.

Origen: las formas de las lentes B y C del intento 17 (`lb17/p1-p3.txt`, `lc17/p1-p4.txt`, `lc17/realeff.sh`, `lb17/real*.sh`) y su producto cartesiano por clase:
  - gap 1: git que lanza otro git (`submodule foreach`, `rebase -x`, `bisect run`);
  - gap 2: un envoltorio de la tabla o una shell detras de un programa que NO esta en la tabla (`uv run`, `chroot`, `strace`, `xvfb-run`, `dotenv --`...);
  - gaps 11, 14, 15 y 16: salidas de rama sin forma de commit, `-B` sobre otra rama, `update-ref refs/heads/*`, `rebase <upstream> <rama>`, `bisect start <malo> <bueno>`.
Todo ASCII. Los generadores son deterministas (sin azar): el corpus es la lista que producen.
"""

# Destructivos tipicos tras un lanzador (cada uno, solo, ya se deniega en la rama de trabajo).
DESTRUCTIVOS17 = [
    "git reset --hard", "git clean -fdx", "git push --force", "git checkout main", "git restore a.txt", "git checkout -- .", "git switch main",
]

# --- gap 1: git que lanza otro git en sus argumentos
GIT_LANZA_GIT17 = []
for _d in DESTRUCTIVOS17:
    GIT_LANZA_GIT17 += [
        f"git submodule foreach {_d}", f"git submodule foreach --recursive {_d}", f"git submodule foreach '{_d}'",
        f"git submodule foreach --quiet --recursive '{_d}'", f"git submodule --quiet foreach \"{_d}\"",
        f"git rebase -x '{_d}' HEAD~2", f"git rebase --exec '{_d}' HEAD~2", f"git rebase --exec='{_d}' HEAD~2", f"git rebase -x'{_d}' HEAD~2",
        f"git rebase -ix '{_d}' HEAD~2", f"git rebase --exe '{_d}' HEAD~2", f"git bisect run {_d}", f"git bisect run '{_d}'",
        f"git bisect run sh -c '{_d}'", f"git -C . submodule foreach '{_d}'", f"git --no-pager submodule foreach '{_d}'",
    ]
GIT_LANZA_GIT17 += [
    "git filter-branch --tree-filter 'git reset --hard' HEAD", "git filter-branch --msg-filter 'git clean -fdx' HEAD",
    "git fetch --upload-pack 'git reset --hard' origin", "git push --receive-pack='git clean -fdx' origin", "git clone -u 'git reset --hard' x y",
]

# --- gap 2: programa fuera de la tabla que ejecuta lo que sigue (cada uno tiene shim en el arnes con bash real)
PROGRAMAS17 = ["uv run", "uv run --no-project", "chroot /", "strace", "strace -f", "xvfb-run", "dotenv --", "npx", "poetry run", "direnv exec .", "unshare -r", "ltrace"]
INTERIORES17 = [
    "bash -c 'git clean -fdx'", "sh -c 'git push --force'", "bash -c 'git checkout main'", "bash -c 'git reset --hard'", "zsh -c 'git reset --hard'",
    "dash -c 'git reset --hard'", "ksh -c 'git reset --hard'", "busybox sh -c 'git reset --hard'", "env -S 'git reset --hard'",
    "env GIT_WORK_TREE=.. git restore a.txt", "env -C .. git restore a.txt", "env GIT_DIR=../o/.git git checkout -- a.txt", "xargs git restore",
    "xargs -a f.txt git checkout --", "sudo -D .. git restore a.txt", "flock f -c 'git push --force'", "su -c 'git checkout main'", "eval 'git reset --hard'",
    "nice env GIT_DIR=../o/.git git checkout -- a.txt", "timeout 5 env GIT_WORK_TREE=.. git restore a.txt", "env HOME=/tmp/x git commit -m x",
    "env GIT_EDITOR=vim git rebase -i HEAD~3", "env XDG_CONFIG_HOME=/tmp/c git commit -m x",
]
ENVOLTORIO_DETRAS_DE_DESCONOCIDO17 = [f"{p} {i}" for p in PROGRAMAS17 for i in INTERIORES17]
ENVOLTORIO_DETRAS_DE_DESCONOCIDO17 += [
    "strace trap 'git checkout -- .' EXIT", "strace -f git -C .. restore a.txt",
    "strace git --work-tree=.. restore a.txt", "strace GIT_WORK_TREE=.. git restore a.txt",
]

# --- gaps 11, 14, 15 y 16: la regla de rama por lista blanca (con la rama de trabajo `feature/x`)
SALIDAS_RAMA17 = [
    "git checkout v1.0", "git checkout v1.2.0", "git checkout FETCH_HEAD", "git checkout ORIG_HEAD", "git checkout MERGE_HEAD", "git checkout fork/main",
    "git checkout abc12", "git checkout abc1", "git checkout origin", "git checkout @", "git checkout Main", "git checkout MASTER", "git checkout refs/remotes/fork/main",
    "git switch --detach v1.2.0", "git checkout feature/y", "git switch feature/y", "git switch feature/y --", "git checkout other/feature/y",
    "git checkout -B feature/y", "git checkout -B feature/y origin/feature/y", "git switch -C feature/y", "git switch -C feature/y main", "git checkout -Bfeature/y",
    "git checkout --force-create feature/y", "git checkout -B feature/x HEAD~1", "git switch -C feature/x origin/feature/x", "git checkout -Bfeature/x origin/feature/x",
    "git checkout @{u}", "git checkout feature/x@{1}", "git checkout -", "git switch -", "git checkout @{-1}",
    "git update-ref refs/heads/main HEAD", "git update-ref refs/heads/feature/x HEAD~1", "git update-ref refs/heads/feature/x origin/main",
    "git update-ref -m msg refs/heads/z HEAD", "git update-ref --no-deref refs/heads/main feature/x", "git update-ref refs/heads/feature/x HEAD",
    "git rebase origin/main main", "git rebase main main", "git rebase --onto origin/main HEAD~2 main", "git rebase HEAD~1 main", "git rebase -i HEAD~2 main",
    "git rebase --root main", "git rebase -s ours main feature/y",
    "git bisect start HEAD HEAD~3", "git bisect start HEAD~1", "git bisect start main", "git bisect reset main", "git bisect reset HEAD~3",
    "git switch -t origin/main", "git checkout --track origin/main", "git checkout -t origin/master", "git checkout --conflict merge main",
]
# Lo que sigue permitido en `feature/x`: la rama actual, un no-op, restaurar ficheros, crear ramas, rebase y bisect sin sacar de la rama.
PERMITIDAS_RAMA17 = [
    "git checkout HEAD", "git checkout feature/x", "git switch feature/x", "git checkout -B feature/x", "git switch -C feature/x", "git checkout --force-create feature/x",
    "git checkout -- src/a.py", "git checkout main -- src/a.py", "git checkout HEAD -- a.py", "git checkout HEAD~1 -- src/a.py", "git checkout abc1234 -- a.py",
    "git checkout main src/a.py", "git checkout HEAD src/a.py", "git checkout -p src/a.py", "git checkout --patch main src/a.py", "git checkout --ours a.txt",
    "git checkout -b feature/y", "git switch -c feature/y", "git switch -c feature/y main", "git checkout -b feature/y origin/main", "git checkout --orphan tmp",
    "git switch -c feature/y --track origin/feature/y", "git checkout -b feature/y --track origin/feature/y",
    "git rebase main", "git rebase -i HEAD~3", "git rebase --onto main HEAD~2", "git rebase --continue", "git rebase --abort", "git rebase feature/x",
    "git rebase -s ours main", "git rebase --root", "git rebase --root --onto main",
    "git bisect start", "git bisect reset", "git bisect log", "git bisect run make test", "git bisect run sh -c 'make test'",
    "git update-ref refs/tags/v1 HEAD", "git update-ref refs/stash HEAD", "git status", "git log --oneline",
    "git submodule foreach 'git status'", "git submodule foreach --recursive git pull", "git rebase -x 'make test' HEAD~2", "git rebase --exec 'npm test' main",
    "git submodule update --init", "git bisect run git status",
]
