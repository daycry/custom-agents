#!/usr/bin/env python3
"""Tests de guardrail-check.py: ciclo fix9 de T-06 (plugin-audit-2, fase 1, intento 9). Ejecuta: pytest -q.

Modelo de amenaza (decision del usuario): el guardarrail frena los ERRORES de un agente honesto. `xargs -a <(git diff
--name-only) git restore` y `env -S 'git restore\\_.'` son formas que un agente escribe sin querer; la indireccion
deliberada es un limite conocido.
"""
import importlib.util
import os
import shlex

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("guardrail_check_fix9", os.path.join(HERE, "guardrail-check.py"))
gc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gc)

BS = chr(92)


def decide(cmd):
    return gc.check_git(cmd, "feature/x")


# --- gap 1: una sustitucion de proceso dentro de una palabra NO parte el segmento que la contiene -------------------
XARGS_SUSTITUCION_DENY = [
    "xargs -a <(git diff --name-only) git restore",
    "xargs -a <(git diff --name-only) git checkout --",
    "xargs --arg-file=<(git diff --name-only) git checkout --",
    "xargs --arg-file <(git diff --name-only) git restore",
    "xargs -a<(git diff --name-only) git restore",
    "xargs -a <(git diff --name-only) -I{} sh -c 'git restore {}'",
    "xargs -a <(git ls-files -m) -n1 git restore",
    "xargs -0 -a <(git diff -z --name-only) git restore",
    "xargs -a <(echo .) git reset --hard",
    "xargs -a <(git diff --name-only) git clean -f",
    "xargs -a <(git diff --name-only) git rm -f",
    "git diff --name-only | xargs -a <(echo x) git restore",
    "xargs -a >(cat) git restore",
    "xargs -a $(mktemp) git restore",
    "xargs -a `mktemp` git restore",
]


@pytest.mark.parametrize("cmd", XARGS_SUSTITUCION_DENY)
def test_gap1_xargs_con_sustitucion_de_proceso_se_deniega(cmd):
    assert decide(cmd), cmd


@pytest.mark.parametrize("cmd", [
    "xargs -a <(git diff --name-only) git add",
    "xargs -a <(git diff --name-only) git status",
    "xargs -a <(git diff --name-only) git diff --stat --",
    "xargs -a <(git diff --name-only) wc -l",
    "diff <(git show HEAD:a.txt) <(git show HEAD~1:a.txt)",
    "cat <(echo hi) >(cat)",
    "wc -l <(git diff --name-only)",
])
def test_gap1_sustitucion_de_proceso_sin_git_destructivo_sigue_permitida(cmd):
    assert decide(cmd) is None, cmd


@pytest.mark.parametrize("cmd", [
    "cat <(git restore .)",
    "echo x >(git reset --hard)",
    "diff <(git stash drop) <(echo)",
    "cat <(echo $(git restore .))",
    "xargs -a <(git restore .) wc",
])
def test_gap1_el_interior_de_la_sustitucion_se_analiza_como_segmento_propio(cmd):
    assert decide(cmd), cmd


def test_gap1_el_segmento_exterior_conserva_sus_argumentos_tras_la_sustitucion():
    segmentos, incompleta = gc._segmentos("xargs -a <(git diff --name-only) git restore")
    assert not incompleta
    exterior = [s for s in segmentos if s and s[0] == "xargs"]
    assert exterior and exterior[0][-2:] == ["git", "restore"], segmentos
    assert any(s[:2] == ["git", "diff"] for s in segmentos), segmentos       # el interior, aparte


def test_gap1_una_sustitucion_dentro_de_comillas_dobles_es_texto():
    segmentos, _ = gc._segmentos('echo "<(git restore .)"')
    assert segmentos == [["echo", "<(git restore .)"]], segmentos


# --- gap 4: `env -S` que no se puede trocear se deniega SIEMPRE; escapes de GNU env antes del troceo -----------------
RELLENO = "A=" + "y" * 2100
ENV_S_NO_TROCEABLE_DENY = [
    "env -S 'kubectl delete ns prod " + RELLENO + "'",
    "env -S 'docker system prune -f " + RELLENO + "'",
    "env -S 'npm publish " + RELLENO + "'",
    "env -S 'echo " + RELLENO + "'",                       # sin git ni orden peligrosa: tambien se deniega (siempre)
    "env -S 'g\"\"it restore . " + RELLENO + "'",
    "env -S 'git \"restore .'",                            # comilla abierta
    "env -S 'echo \"hi'",                                  # comilla abierta, sin git
    "env -S \"echo 'hi\"",
    "env -S env -S env -S env -S env -S env git restore .",   # quinto troceo
]


@pytest.mark.parametrize("cmd", ENV_S_NO_TROCEABLE_DENY)
def test_gap4_env_s_no_troceable_se_deniega_siempre(cmd):
    assert decide(cmd), cmd


def _anidado(n):
    s = "git restore ."
    for _ in range(n):
        s = "env -S " + shlex.quote(s)
    return s


@pytest.mark.parametrize("n", [3, 4, 5, 6])
def test_gap4_env_s_anidado_se_deniega_con_git(n):
    assert decide(_anidado(n)), n


def test_gap4_sin_git_un_valor_no_troceable_tambien_se_deniega():
    """El ejemplo del gap sin `git` literal: antes solo se denegaba si aparecia `git`."""
    assert decide("env -S 'kubectl delete ns prod " + RELLENO + "'")
    assert decide("env -S 'echo \"hi'")


ENV_S_ESCAPES_DENY = [
    "env -S 'git restore" + BS + "_.'",
    "env -S 'git" + BS + "_restore" + BS + "_.'",
    "env -S 'git restore ." + BS + "c'",
    "env -S 'git restore ." + BS + "c junk'",
    "env -S 'git reset --hard" + BS + "c'",
    "env -S 'git restore \".\"'",
    "env -S 'git restore " + BS + ".'",                    # un escape desconocido con git se deniega
    "env -S 'git restore " + BS + "x .'",
    "env -S 'git restore ." + BS + "'",                    # barra final
    "env -S 'git reset \"" + BS + "-" + BS + "-hard\"'",
    "env --split-string='git restore" + BS + "_.'",
    "env -S'git restore" + BS + "_.'",
    "env -S 'env -S \"git" + BS + "_restore" + BS + "_.\"'",
]


@pytest.mark.parametrize("cmd", ENV_S_ESCAPES_DENY)
def test_gap4_escapes_de_gnu_env_antes_del_troceo(cmd):
    assert decide(cmd), cmd


@pytest.mark.parametrize("cmd", [
    "env -S 'git status'",
    "env -S 'echo \"a b\"'",
    "env -S 'FOO=bar git restore src/a.py'",
    "env -S 'echo a" + BS + "_b'",
    "env -S 'git log --oneline -1'",
    "env -S 'git restore src/a.py'",
    "env -S 'git commit -m \"x y\"'",
    "env -S 'echo " + BS + "x'",                            # escape desconocido SIN git: env falla, nada que frenar
    "env -S 'echo " + BS + "#'",
    "env -i -S 'git status'",
])
def test_gap4_env_s_legitimo_sigue_permitido(cmd):
    assert decide(cmd) is None, cmd


def test_gap4_trocea_s_aplica_los_escapes_de_env():
    assert gc._trocea_s("git restore" + BS + "_.", [0]) == ["git", "restore", "."]
    assert gc._trocea_s("git restore ." + BS + "c ignorado", [0]) == ["git", "restore", "."]
    assert gc._trocea_s('echo "a' + BS + '_b"', [0]) == ["echo", "a b"]
    assert gc._trocea_s("echo a" + BS + "tb", [0]) == ["echo", "a\tb"]
    assert gc._trocea_s("echo '" + BS + BS + "x'", [0]) == ["echo", BS + "x"]
    assert gc._trocea_s("echo " + BS + '"q' + BS + '"', [0]) == ["echo", '"q"']


def test_gap4_valor_no_troceable_se_marca_distinto_de_una_opcion_desconocida():
    resto, _b, _c, desconocida, _x = gc._desenvuelve(["env", "-S", "echo \"hi"])
    assert desconocida and getattr(desconocida, "siempre", False), desconocida
    resto, _b, _c, desconocida, _x = gc._desenvuelve(["env", "-S", "git " + BS + "x"])
    assert desconocida and not getattr(desconocida, "siempre", False), desconocida
