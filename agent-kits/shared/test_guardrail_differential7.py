#!/usr/bin/env python3
"""Corpus DIFERENCIAL del intento 7 (T-06 fix7, plugin-audit-2, fase 1): todas las sondas de las lentes A, B, C y D.

Mismo método que `test_guardrail_differential.py` (BAD / LEGIT / LIMITE, repo temporal con centinela y bash real; en
Windows, el bash de Git): cada BAD se deniega y su efecto es real en bash (paridad); cada LEGIT se permite; cada LIMITE
lo ejecuta bash y el guardarraíl no lo ve (frontera del modelo de amenaza decidido por el usuario).
"""
import os
import shutil
import subprocess

import pytest

from test_guardrail_differential import (  # noqa: F401  (los fixtures se registran al importarlos)
    BASH, GIT, D_PUSH, D_RESTORE, _decide, _ejecutar_en_bash, _expandir, _id, en_proj, necesita_bash, plantilla_repo)

_BS = chr(92)

BAD7 = [
    # gap 1: bash cierra el heredoc con `D)` y ejecuta lo que sigue entre los dos commits
    "git commit --allow-empty -m \"$(cat <<'D'\nmsg\nD)\"\n{D}\nD\n)\"",
    # gap 2: tras un comentario la forma no abre ningún heredoc; para bash el cuerpo son órdenes
    "true # ok; git commit -m \"$(cat <<'EOF'\n{D}\nEOF\n)\"",
    "true # ok && git commit -m \"$(cat <<'EOF'\n{D}\nEOF\n)\"",
    "true # ok; git commit -F - <<'EOF'\n{D}\nEOF",
    # gap 3: `env -S` con un cambio de base dentro (b.txt es del repo exterior)
    "env -S 'git -C .. restore b.txt'", "env --split-string='git -C .. restore b.txt'",
    "env -S 'git --work-tree=.. restore b.txt'",
    # gap 7: envoltorios con el valor de la opción separado
    "timeout --kill-after 5 30 {D}", "timeout --kill-after=5 30 {D}", "timeout --signal KILL 30 {D}",
    "timeout --signal=KILL 30 {D}", "timeout -k 5 30 {D}", "timeout -s KILL 30 {D}",
    "nice --adjustment 5 {D}", "nice --adjustment=5 {D}", "nice -n 5 {D}", "nice -5 {D}",
    "stdbuf -o 0 {D}", "stdbuf -o L {D}", "stdbuf -oL {D}", "stdbuf --output=0 {D}", "stdbuf --output 0 {D}",
    "sudo --user root {D}", "sudo -u root {D}", "flock /tmp/l {D}", "flock -n /tmp/l {D}", "flock -w 5 /tmp/l {D}",
    "ionice -c 3 {D}", "setsid -w {D}", "xargs -a /dev/null {D}",
    # gap 9: `--` tras `-c`
    "bash -c -- '{D}'", "sh -c -- '{D}'",
    # gap 4: xargs con las rutas por la entrada estándar
    "git diff --name-only | xargs git checkout --", "git diff --name-only | xargs git restore --",
    "git diff --name-only | xargs -r git checkout HEAD --", "git diff --name-only | xargs -I{} git checkout -- {}",
    "git diff --name-only | xargs git restore", "git ls-files -m | xargs git checkout --",
    "echo . | xargs -n1 git restore", "echo . | xargs -I{} git restore {}", "echo . | xargs -0 git restore",
    # gap 5 y 6: regresiones del tokenizador
    "echo $$'" + _BS + "'; {D} #'", "echo pid=$$'" + _BS + "' && {D} && echo x",
    "echo " + _BS + ">& {D}", "echo a" + _BS + "<& {D}", "ls 2>&1 >&2& {D}",
    # sondas de las lentes que ya se denegaban (controles de no regresión)
    "git diff --name-only | while read f; do git checkout -- \"$f\"; done",
    "for f in $(git diff --name-only); do git checkout -- $f; done", "git checkout -- $(git diff --name-only)",
    "git restore $(git diff --name-only)", "git checkout-index -f -a", "git rm -rf --cached . ; git rm -rf .",
    "env -S '{D}'", "env --split-string='{D}'", "timeout 30 {D}", "nice {D}", "time -p {D}", "nohup {D}",
]

# BAD sin efecto reproducible (o sin el programa) en el repo de prueba: no se pide paridad, pero se deniegan igual.
SIN_PARIDAD_7 = {
    "git checkout @{-2}", "git checkout origin/HEAD", "git switch --detach origin/HEAD", "git switch --detach",
    "git checkout --detach HEAD~1", "git switch origin/main",
    # su efecto no se reproduce en este repo (o hace falta un programa que un bash puede no traer):
    "env -S 'git --work-tree=.. restore b.txt'", "sudo --user root {D}", "sudo -u root {D}",
    "echo . | xargs -0 git restore", "git rm -rf --cached . ; git rm -rf .", "nice {D}",
}
BAD7 += sorted(SIN_PARIDAD_7)

# Programas que un bash concreto puede no traer (sudo, ionice, setsid, flock…): la paridad se salta si faltan.
PROGRAMAS_OPCIONALES = {"sudo", "flock", "ionice", "setsid", "stdbuf", "timeout", "nice", "xargs"}

LEGIT7 = [
    # lista blanca de commit: lo legítimo (de las lentes B y C) sigue valiendo
    "git add -A && git commit -F - <<'EOF'\ndon't\nEOF",
    "git commit -m \"$(cat <<'EOF'\nmsg\nEOF\n)\" && git log -1",
    "cd . && git commit -m \"$(cat <<'EOF'\nit's\nEOF\n)\"",
    "pytest -q; git commit -m \"$(cat <<'EOF'\nit's\nEOF\n)\"",
    "time pytest && git commit -m \"$(cat <<'EOF'\nit's\nEOF\n)\"",
    "echo ok # nota\ngit commit -F - <<'EOF'\nit's\nEOF",
    # el flujo normal
    "git status && git diff --stat && git log --oneline -5",
    "python -m pytest -q tests/ -k 'not slow' 2>&1 | tail -20",
    "git add -A && git commit -m 'T-01: fix it' && git push origin feat/x",
    "for f in src/*.py; do python -m py_compile \"$f\"; done; git status --short",
    "git diff HEAD~1 -- src/a.py | head -50", "npm run build && npm test -- --watch=false",
    "git log --format='%h %s' -n 20 | grep -i fix", "echo $((3 + 4)) && git status",
    "if [ -f a.txt ]; then git add a.txt; fi", "git stash list; git branch -a", "f() { echo hi; }; f && git status",
    "source .venv/bin/activate 2>/dev/null; git status", "source .venv/bin/activate && git restore src/a.py",
    ". .venv/bin/activate && git restore src/a.py", "git commit -am \"fix: don't break\"", "git -C . status",
    "git checkout -b feat/y && git checkout feat/x", "git restore --staged a.txt", "git restore a.txt",
    "time (python -c 'print(1)') && git status", "export PYTHONPATH=src; python -m pytest -q && git add -A",
    "echo $$; git status", "ls &>/dev/null; git status", "git log 2>&1 >/dev/null",
    # envoltorios sin git destructivo
    "timeout --kill-after 5 30 git status", "nice --adjustment 5 git log --oneline -3", "stdbuf -o L git diff --stat",
    "flock /tmp/l git status", "git diff --name-only | xargs git add", "ls | xargs wc -l",
]

# LIMITE DOCUMENTADO (modelo de amenaza del usuario): bash ejecuta el efecto y el guardarraíl no lo ve.
LIMITE7 = [
    "printf 'git restore .\\n' > s.sh; source ./s.sh", "printf 'cd ..\\n' > s.sh; source ./s.sh; git restore b.txt",
    "printf 'git restore .\\n' > s.sh; . ./s.sh", "x='git restore .'; eval \"$x\"",
    "echo 'git restore .' | xargs -I{} sh -c '{}'",
]

# Falso deny aceptado: una línea del cuerpo que EMPIEZA por el delimitador deja la forma exacta fuera de la lista blanca
# (bash 5.2 cierra el heredoc con `D)`); el cuerpo se analiza entonces como órdenes y el mensaje explica la salida.
FALSO_DENY_ACEPTADO_7 = [
    "git add a.txt && git commit -m \"$(cat <<'EOF'\nit's a fix with \"quotes\" and $HOME\nEOF \n line\nEOF\n)\"",
]


def _tiene(programa):
    try:
        r = subprocess.run([BASH, "-c", f"command -v {programa}"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
        return r.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


@pytest.mark.parametrize("d", [D_RESTORE, D_PUSH], ids=["restore", "push-force"])
@pytest.mark.parametrize("plantilla", BAD7, ids=[_id(p) for p in BAD7])
def test_bad7_el_guardarrail_deniega(plantilla, d, en_proj):
    orden = _expandir(plantilla, d, en_proj.as_posix())
    assert _decide(orden), f"DENY esperado: {orden!r}"


@pytest.mark.parametrize("plantilla", LEGIT7, ids=[_id(p) for p in LEGIT7])
def test_legit7_el_flujo_normal_sigue_permitido(plantilla, en_proj):
    orden = _expandir(plantilla, D_RESTORE, en_proj.as_posix())
    razon = _decide(orden)
    assert razon is None, f"ALLOW esperado: {orden!r} -> {razon}"


@pytest.mark.parametrize("plantilla", FALSO_DENY_ACEPTADO_7, ids=[_id(p) for p in FALSO_DENY_ACEPTADO_7])
def test_falso_deny_aceptado_7(plantilla, en_proj):
    razon = _decide(plantilla)
    assert razon and "herramienta de edición" in razon, razon


@necesita_bash
@pytest.mark.parametrize("plantilla", [p for p in BAD7 if p not in SIN_PARIDAD_7],
                         ids=[_id(p) for p in BAD7 if p not in SIN_PARIDAD_7])
def test_paridad7_cada_bad_cambia_el_centinela_en_bash_real(plantilla, plantilla_repo, tmp_path):
    orden = _expandir(plantilla, D_RESTORE, "/nada")
    programa = orden.split()[0]
    if programa in PROGRAMAS_OPCIONALES and not _tiene(programa):
        pytest.skip(f"este bash no trae `{programa}`")
    antes, despues, _ = _ejecutar_en_bash(plantilla_repo, tmp_path, orden)
    assert antes != despues, f"bash NO ejecutó el efecto de {orden!r}"


@necesita_bash
@pytest.mark.parametrize("plantilla", LIMITE7, ids=[_id(p) for p in LIMITE7])
def test_limite7_bash_lo_ejecuta_y_el_guardarrail_no_lo_ve(plantilla, plantilla_repo, tmp_path, en_proj):
    orden = _expandir(plantilla, D_RESTORE, en_proj.as_posix())
    assert _decide(orden) is None, f"el límite documentado ya se detecta, muévelo a BAD7: {orden!r}"
    antes, despues, _ = _ejecutar_en_bash(plantilla_repo, tmp_path, orden)
    assert antes != despues, f"bash NO ejecutó {orden!r}: no es un límite real"


@necesita_bash
def test_propiedad7_si_el_guardarrail_permite_bash_no_toca_el_centinela(plantilla_repo, tmp_path, monkeypatch):
    proj = plantilla_repo / "outer" / "proj"
    monkeypatch.chdir(proj)
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(proj))
    fallos, n = [], 0
    for plantilla in BAD7:
        if plantilla in SIN_PARIDAD_7:
            continue
        programa = plantilla.replace("{D}", D_RESTORE).split()[0]
        if programa in PROGRAMAS_OPCIONALES and not _tiene(programa):
            continue
        for d in (D_RESTORE, "git reset --hard"):
            orden = _expandir(plantilla, d, proj.as_posix())
            if _decide(orden):
                continue
            n += 1
            antes, despues, _ = _ejecutar_en_bash(plantilla_repo, tmp_path / f"q{n}", orden)
            if antes != despues:
                fallos.append(orden)
    assert not fallos, f"el guardarraíl PERMITIÓ órdenes que bash ejecutó: {fallos}"
