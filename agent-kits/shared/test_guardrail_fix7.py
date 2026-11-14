#!/usr/bin/env python3
"""Tests de guardrail-check.py: ciclo fix7 de T-06 (plugin-audit-2, fase 1, intento 7). Ejecuta: pytest -q.

El modelo de amenaza lo fijó el usuario: el guardarraíl frena los ERRORES de un agente honesto; la indirección
deliberada (variable como programa, código por stdin, `find -exec`, `source` de un fichero) es un límite conocido.
"""
import importlib.util
import os
import time

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "guardrail-check.py")

spec = importlib.util.spec_from_file_location("guardrail_check_fix7", SCRIPT)
gc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gc)

PROJ = "/proy"


def bash(cmd):
    return {"tool_name": "Bash", "tool_input": {"command": cmd}}


def decide(payload, branch="feature/x", cfg=None):
    return gc.decide(payload, PROJ, cfg, branch=branch)


# --- gaps 1 y 2: la lista blanca de las dos formas exactas de `git commit` es a prueba de bash -------------
FORMA_QUE_NO_VALE = [
    # `D)` cierra el heredoc en bash 5.2 (dentro de `$(…)`): lo que sigue lo EJECUTA bash
    "git commit --allow-empty -m \"$(cat <<'D'\nmsg\nD)\"\ngit restore .\nD\n)\"",
    "git commit --allow-empty -m \"$(cat <<'D'\nmsg\nD; git restore .\nD\n)\"",
    "git commit --allow-empty -m \"$(cat <<'D'\nmsg\nD x\nD)\"\ngit restore .\nD\n)\"",
    "git commit --allow-empty -m \"$(cat <<'D'\nmsg\n\tD)\"\ngit restore .\nD\n)\"",
    # detrás de un comentario la forma NO abre un heredoc: para bash todo es comentario y el cuerpo se ejecuta
    "true # ok; git commit -m \"$(cat <<'EOF'\ngit restore .\nEOF\n)\"",
    "true # ok && git commit -m \"$(cat <<'EOF'\ngit restore .\nEOF\n)\"",
    "true # ok; git commit -F - <<'EOF'\ngit restore .\nEOF",
    "echo hola # nota\ngit commit -F - <<'EOF'\nx\nEOF\ntrue # ok; git commit -F - <<'EOF'\ngit restore .\nEOF",
]


@pytest.mark.parametrize("cmd", FORMA_QUE_NO_VALE)
def test_gaps_1_2_la_forma_exacta_no_vale_si_bash_la_lee_distinto(cmd):
    assert decide(bash(cmd)), cmd


@pytest.mark.parametrize("cmd", [
    "git commit -m \"$(cat <<'EOF'\nmensaje don't\nEOF\n)\"",
    "git add -A && git commit -F - <<'EOF'\nit's\nEOF",
    "time pytest && git commit -m \"$(cat <<'EOF'\nit's\nEOF\n)\"",
    "pytest -q; git commit -m \"$(cat <<'EOF'\nit's\nEOF\n)\"",
    "echo ok # nota\ngit commit -F - <<'EOF'\nit's\nEOF",
    "git commit -m \"$(cat <<'EOF'\nx EOFS no cierra y no empieza la linea\nxEOF\nEOF\n)\"",
])
def test_la_forma_exacta_legitima_sigue_valiendo(cmd):
    assert decide(bash(cmd)) is None, cmd


_FORMA = "git commit -F - <<'E'\nE\n"
HOSTILES_DE_COSTE = {
    "formas-seguidas-16k": ("x\n" + ("true;" + _FORMA) * 600)[:16300],
    "formas-tras-punto-y-coma": ('echo "\n' + (";" + _FORMA) * 600)[:16300],
    "formas-sin-cierre": "git commit -m \"$(cat <<'E'\n" * 590,
    "formas-con-heredoc-previo": "cat <<X\nX\n" + "git commit -m \"$(cat <<'E'\nE\n)\"\n" * 450,
    "commit-encadenado": "git commit " * 1450 + "<<",
    "commit-m-encadenado": "git commit -m " * 1100 + "<<",
}


@pytest.mark.parametrize("nombre", sorted(HOSTILES_DE_COSTE))
def test_gap_11_la_lista_blanca_de_commit_es_lineal(nombre):
    """Las posiciones de `git commit` salen de UNA pasada del tokenizador y las opciones se acotan a su línea:
    15 KB de formas costaban 6-14 s (retroceso de `_OPCIONES` y una relectura de `previo` por coincidencia)."""
    orden = HOSTILES_DE_COSTE[nombre]
    assert len(orden) <= 16384
    inicio = time.process_time()
    gc._quitar_mensajes_de_commit(orden)
    assert time.process_time() - inicio < 0.3, nombre


def test_gap_11_los_comentarios_no_prometen_lo_que_el_guard_no_cumple():
    with open(SCRIPT, encoding="utf-8") as f:
        assert "nunca agota el plazo" not in f.read()


# --- gaps 3, 7 y 9: una sola implementación de envoltorios -----------------------------------------------------
BASE_EN_ENVOLTORIOS = [
    "env -S 'git -C .. restore a.txt'", "env --split-string='git -C .. restore a.txt'",
    "env -iS 'git -C .. restore a.txt'", "env -S 'env -C .. git restore a.txt'",
    "timeout 30 env -S 'git --work-tree=.. restore a.txt'", "env -S 'cd .. ' && git restore a.txt",
    ". <(echo cd ..); git restore b.txt", "source <(echo cd ..); git restore b.txt",
]


@pytest.mark.parametrize("cmd", BASE_EN_ENVOLTORIOS)
def test_gap_3_el_cambio_de_base_dentro_de_un_envoltorio_se_ve(cmd):
    assert gc._cambia_base_en(gc._segmentos(cmd)[0]) is True, cmd
    razon = decide(bash(cmd))
    assert razon and "base" in razon, (cmd, razon)


ENVOLTORIOS_CON_VALOR_SEPARADO = [
    "timeout --kill-after 5 30 git restore .", "timeout --kill-after=5 30 git restore .",
    "timeout --signal KILL 30 git restore .", "timeout --signal=KILL 30 git restore .",
    "timeout -k 5 30 git restore .", "timeout -s KILL 30 git restore .",
    "nice --adjustment 5 git restore .", "nice --adjustment=5 git restore .", "nice -n 5 git restore .",
    "nice -5 git restore .", "stdbuf -o 0 git restore .", "stdbuf -o L git restore .", "stdbuf -oL git restore .",
    "stdbuf --output 0 git restore .", "stdbuf --output=0 git restore .", "sudo --user root git restore .",
    "sudo -u root git restore .", "sudo --group wheel git restore .", "flock /tmp/l git restore .",
    "flock -n /tmp/l git restore .", "flock -w 5 /tmp/l git restore .", "ionice -c 3 git restore .",
    "ionice -c3 -n 7 git restore .", "setsid -w git restore .", "xargs -n 1 git restore .",
    "xargs -I {} git restore {}", "xargs -a /dev/null git restore .", "bash -c -- 'git reset --hard'",
    "sh -c -- 'git restore .'", 'bash -c -- "git push --force origin master"',
]


@pytest.mark.parametrize("cmd", ENVOLTORIOS_CON_VALOR_SEPARADO)
def test_gaps_7_9_envoltorios_con_el_valor_de_la_opcion_separado(cmd):
    assert decide(bash(cmd)), cmd


@pytest.mark.parametrize("cmd", [
    "timeout --frobnicate 30 git status", "nice --frobnicate git status", "sudo --frobnicate git status",
    "stdbuf --frobnicate git status", "flock --frobnicate /tmp/l git status", "env --frobnicate git status",
    "xargs --frobnicate git status", "timeout -Z 30 git status",
])
def test_gap_7_una_opcion_desconocida_de_un_envoltorio_con_git_se_deniega(cmd):
    razon = decide(bash(cmd))
    assert razon and "envoltorio" in razon, (cmd, razon)


@pytest.mark.parametrize("cmd", [
    "timeout --frobnicate 30 ls", "sudo --frobnicate ls", "timeout --kill-after 5 30 git status",
    "timeout 30 git status", "nice -n 5 git log --oneline -3", "stdbuf -o L git diff --stat",
    "flock /tmp/l git status", "sudo --user root git status", "xargs echo", "ls | xargs wc -l",
    "git diff --name-only | xargs git add", "git diff --name-only | xargs -n 1 git add",
    "env -i FOO=1 git status", "env -u X git status", "nohup git status",
])
def test_lo_legitimo_con_envoltorios_sigue_permitido(cmd):
    assert decide(bash(cmd)) is None, cmd


# --- gap 4: xargs con rutas desconocidas ----------------------------------------------------------------------
@pytest.mark.parametrize("cmd", [
    "git diff --name-only | xargs git checkout --", "git diff --name-only | xargs git checkout",
    "git diff --name-only | xargs git restore --", "git diff --name-only | xargs git restore",
    "git diff --name-only | xargs -r git checkout HEAD --", "git diff --name-only | xargs -I{} git checkout -- {}",
    "git diff --name-only | xargs -I {} git restore {}", "git ls-files -m | xargs -0 git checkout --",
    "echo . | xargs git reset --hard", "echo a | xargs git clean -f", "echo a | xargs git rm",
    "echo a | xargs git checkout-index -f", "echo a | xargs -n1 git restore --staged --worktree",
])
def test_gap_4_xargs_con_un_subcomando_destructivo_de_ficheros_se_deniega(cmd):
    razon = decide(bash(cmd))
    assert razon and "xargs" in razon, (cmd, razon)


# --- gaps 5 y 6: regresiones del tokenizador -------------------------------------------------------------------
@pytest.mark.parametrize("cmd", [
    "echo $$'\\'; git reset --hard #'", "echo pid=$$'\\' && git reset --hard && echo '",
    'echo $$"x"; git reset --hard', "echo \\>& git reset --hard", "echo a\\<& git reset --hard",
    "ls 2>&1 >&2& git reset --hard",
])
def test_gaps_5_6_regresiones_del_tokenizador(cmd):
    assert decide(bash(cmd)), cmd


@pytest.mark.parametrize("cmd", ["echo $'a\\'b'; git status", "git log 2>&1 >/dev/null", "ls &>/dev/null; git status",
                                 "echo $$; git status"])
def test_gaps_5_6_lo_que_ya_se_leia_bien_sigue_igual(cmd):
    assert decide(bash(cmd)) is None, cmd


# --- gap 8: rama protegida -------------------------------------------------------------------------------------
@pytest.mark.parametrize("cmd", [
    "git checkout @{-2}", "git checkout @{-1}", "git checkout origin/HEAD", "git checkout upstream/main",
    "git checkout refs/remotes/origin/master", "git switch --detach origin/HEAD", "git switch --detach",
    "git switch -d HEAD~1", "git checkout --detach HEAD~2", "git switch origin/main",
])
def test_gap_8_checkout_o_switch_fuera_de_la_rama_de_trabajo(cmd):
    razon = decide(bash(cmd))
    assert razon and "rama de trabajo" in razon, (cmd, razon)


@pytest.mark.parametrize("cmd", ["git checkout feature/y", "git switch feature/y", "git checkout -b feature/z",
                                 "git switch -c feature/z", "git checkout feature/x"])
def test_gap_8_cambiar_a_otra_rama_de_trabajo_sigue_permitido(cmd):
    assert decide(bash(cmd)) is None, cmd


# --- gap 12: `source`/`.` con un fichero normal no es un cambio de base (límite conocido) -----------------------
def test_gap_12_source_de_un_fichero_normal_no_es_un_cambio_de_base():
    for cmd in ("source .venv/bin/activate && git restore src/a.py", ". .venv/bin/activate && git restore src/a.py",
                "source ./env.sh; git restore src/a.py"):
        assert decide(bash(cmd)) is None, cmd
        assert gc._cambia_base_en(gc._segmentos(cmd)[0]) is False, cmd


def test_gap_12_el_mensaje_de_deny_nombra_la_causa_real():
    razon = decide(bash(". <(echo cd ..); git restore b.txt"))
    assert razon and "source" in razon and "eval" in razon, razon
    razon = decide(bash("eval 'cd ..'; git restore b.txt"))
    assert razon and "eval" in razon, razon
