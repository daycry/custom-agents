"""Corpus de fix18 (T-06, plugin-audit-2, intento 18): las clases que el guardarrail de fix17 dejaba pasar.

Origen: las formas de las lentes A, B y C del intento 18 (`lb18/p1-p7.txt`, `lc18/p1-p2.txt`, `real*.sh`). Todo ASCII; los generadores son deterministas.
  - gap 1: rama con nombre de ruta (`git checkout main` con un directorio `main`); gap 6: salidas de rama o movimientos de `refs/heads/*`;
  - gaps 2 y 9: subcomandos que destruyen (`submodule update --force`, `gc --prune=now`, `reflog expire`);
  - gap 7: opciones de git cuyo valor ejecuta una shell (`difftool -x`, `grep -O`, `archive --exec`, `fetch-pack --upload-pack`).
`LIMITE18` es la clase de envoltorios encadenados declarada limite por el usuario (2026-11-17): se fija como PERMITIDA con su motivo.
"""

DESTRUCTIVOS18 = ["git reset --hard", "git clean -fdx", "git checkout -- .", "git restore ."]

# --- gaps 2 y 9: destruyen sin pasar por las reglas de checkout/reset
DESTRUYEN18 = [
    "git submodule update --force", "git submodule update -f", "git submodule update --init --recursive --force", "git submodule update --recursive -f sub",
    "git submodule deinit -f sub", "git submodule deinit --force sub", "git submodule deinit -f --all", "git submodule --quiet update --force",
    "git submodule update --forc", "git submodule deinit -qf sub",
    "git gc --prune=now", "git gc --prune=all", "git gc --aggressive --prune=now", "git prune", "git prune --expire now",
    "git reflog expire --expire=now --all", "git reflog expire --all", "git reflog delete HEAD@{1}", "git reflog expire --expire-unreachable=now --all",
    "git worktree remove --force ../wt", "git worktree remove -f ../wt",
    # (anadidas tras el RED, k8) el resto de formas de lc18/p1: el ayudante interno de submodulos y la config del clon
    "git submodule--helper update --force", "git clone -c core.hooksPath=h . ../c", "git clone --config core.sshCommand='git reset --hard' . ../c", "git clone -ccore.pager=x . ../c",
]

# --- gap 7: opciones cuyo valor ejecuta git con una shell (el valor se analiza como codigo: con una forma destructiva dentro, deny)
CODIGO18 = []
for _d in DESTRUCTIVOS18:
    CODIGO18 += [
        f"git difftool -y -x '{_d}' HEAD~1", f"git difftool --extcmd='{_d}' HEAD~1", f"git difftool --extcmd '{_d}' HEAD~1", f"git difftool -x'{_d}' HEAD",
        f"git grep -O'{_d}' foo", f"git grep --open-files-in-pager='{_d}' foo", f"git grep --open-files-in-pager '{_d}' foo",
        f"git archive --exec='{_d}' HEAD", f"git archive --exec '{_d}' --remote=. HEAD", f"git fetch-pack --upload-pack='{_d}' . HEAD",
        f"git send-pack --receive-pack='{_d}' . HEAD", f"git instaweb --httpd='{_d}'",
        f"git submodule--helper foreach '{_d}'", f"git filter-branch --setup '{_d}' HEAD", f"git -C sub difftool -y --extcmd='{_d}' HEAD~1", f"git --no-pager grep --open-files-in-pager='{_d}' v1",
    ]

# --- gap 6: salidas de rama o movimientos de refs/heads/* (rama de trabajo `feature/x`)
MUEVEN_RAMAS18 = [
    "git rebase -S main other", "git rebase -S main feature/y", "git rebase -s ours main other", "git rebase -X theirs main other", "git rebase -x true main other",
    "git bisect start", "git bisect start && git bisect bad && git bisect good HEAD~10", "git bisect good HEAD~6", "git bisect bad HEAD", "git bisect good", "git bisect skip",
    "git bisect reset", "git bisect new HEAD", "git bisect old HEAD~3", "git bisect run make test", "git bisect replay log.txt",
    "git fetch origin +main:main", "git fetch -f origin main:main", "git fetch origin '+refs/heads/*:refs/heads/*'", "git fetch . +feature/x:main", "git fetch . feature/x:main",
    "git fetch --force origin main:main", "git pull --force origin +main:main", "git pull . feature/x:main", "git fetch . feature/y:refs/heads/z",
    "git push . HEAD:main", "git push . feature/x:main", "git push . HEAD:refs/heads/main", "git push origin HEAD:main", "git push origin feature/x:main",
    "git push origin HEAD:refs/heads/master", "git push -u origin HEAD:master",
    "git worktree add -B main ../wt origin/main", "git worktree add -B main ../wt HEAD", "git worktree add --force -B main ../wt", "git worktree add ../wt -B feature/y",
    "git filter-branch --index-filter 'git rm --cached --ignore-unmatch b.txt' -- --all", "git filter-branch -f --tree-filter 'rm -f b.txt' -- --all",
    "git filter-repo --path b.txt --invert-paths --force", "git filter-repo --path b.txt --invert-paths",
]

# --- gap 6, `-C <directorio>`: el HEAD que cuenta es el del directorio (el test sustituye `WT-MAIN` por un worktree cuyo HEAD es `main`)
EN_OTRO_DIRECTORIO18 = [
    "git -C WT-MAIN merge feature/x", "git -C WT-MAIN reset --soft HEAD~1", "git -C WT-MAIN commit -am x", "git -C WT-MAIN pull", "git -C WT-MAIN rebase feature/x",
    "git -C WT-MAIN cherry-pick abc1234", "git -C WT-MAIN revert HEAD", "git -C WT-MAIN merge --ff-only feature/x",
]

# --- gap 1: la rama con nombre de ruta (el test crea la rama y el directorio con el mismo nombre)
NOMBRES_RAMA_Y_RUTA18 = ["main", "master", "docs", "origin/main", "feature/y", "v1.0"]
RAMA_COMO_RUTA18 = []
for _n in NOMBRES_RAMA_Y_RUTA18:
    RAMA_COMO_RUTA18 += [f"git checkout {_n}", f"git checkout {_n} --", f"git switch {_n}", f"git switch {_n} --", f"git checkout -q {_n}", f"git checkout --quiet {_n} --"]

# --- permitidas (el implementer las usa a diario)
PERMITIDAS18 = [
    "git checkout -- a.txt", "git checkout -- main", "git checkout HEAD", "git checkout HEAD -- a.txt", "git checkout main -- a.txt", "git checkout main -- src/",
    "git checkout feature/x", "git switch feature/x", "git status", "git diff", "git diff --stat HEAD~1", "git add -- a.txt", "git add src/main.py", "git commit -m 'T-01: x'",
    "git commit --amend --no-edit", "git log --oneline -5", "git log -p -- src", "git stash", "git stash pop", "git stash list", "git stash push -m x", "git restore --staged a.txt",
    "git restore --staged .", "git branch", "git branch --show-current", "git branch -d feature/old", "git fetch", "git fetch origin", "git fetch --all --prune", "git pull",
    "git pull --ff-only", "git pull origin feature/x", "git push", "git push -u origin feature/x", "git push origin feature/x", "git push origin HEAD", "git push origin HEAD:feature/x",
    "git push origin feature/x:feature/x", "git merge main", "git rebase main", "git rebase -S main", "git rebase -S", "git rebase -i HEAD~3", "git rebase --whitespace fix main",
    "git rebase --onto main HEAD~2", "git rebase -x 'make test' HEAD~2", "git worktree add ../wt -b feature/y", "git worktree add ../wt feature/y", "git worktree list",
    "git worktree remove ../wt", "git worktree prune", "git submodule update", "git submodule update --init --recursive", "git submodule status", "git submodule foreach 'git status'",
    "git reflog", "git reflog show HEAD", "git grep -O v1", "git grep foo", "git grep -n -e foo -- src", "git bisect log", "git bisect visualize", "git bisect view", "git show HEAD",
    "git merge --abort", "git mv -f b.txt a.txt",
    "git -C sub status", "git -C ../other-repo log --oneline", ]

# --- limite declarado (usuario, 2026-11-17): cadenas de programas fuera de la tabla; el sufijo desenvuelto no se re-ancla otra vez
LIMITE18 = [
    ("uv run env -S 'strace git reset --hard'", "env -S desenvuelve a `strace git …`: un segundo programa fuera de la tabla"),
    ("uv run xargs -a f strace git restore", "xargs tras un programa desconocido y un segundo programa desconocido antes de git"),
    ("uv run --no-project env GIT_WORK_TREE=.. chroot / git restore a.txt", "env fija el estado y un segundo programa desconocido lo oculta"),
    ("chroot / env GIT_WORK_TREE=.. chroot / git restore a.txt", "dos envoltorios desconocidos con estado entre ellos"),
    ("echo a.txt | chroot / xargs chroot / git restore", "xargs entre dos programas desconocidos"),
    ("env -S 'ash -c \"git reset --hard\"'", "`ash` no es shell de la tabla"),
    ("uv run mksh -c 'git reset --hard'", "`mksh` no es shell de la tabla"),
    ("uv run fish -c 'git reset --hard'", "`fish` no es shell de la tabla"),
]
