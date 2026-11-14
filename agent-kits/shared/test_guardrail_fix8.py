#!/usr/bin/env python3
"""Tests de guardrail-check.py: ciclo fix8 de T-06 (plugin-audit-2, fase 1, intento 8). Ejecuta: pytest -q.

Modelo de amenaza (decisión del usuario): el guardarraíl frena los ERRORES de un agente honesto; la indirección
deliberada es un límite conocido. `xargs -I{} sh -c 'git restore {}'` y `env -S 'git "reset" --hard'` son errores
habituales, no indirecciones.
"""
import importlib.util
import os
import time

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("guardrail_check_fix8", os.path.join(HERE, "guardrail-check.py"))
gc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gc)


def decide(cmd):
    return gc.check_git(cmd, "feature/x")


# --- gap 1: `xargs` + `sh -c`: las rutas por stdin se heredan al recursar ------------------------------------------
XARGS_SH_DENY = [
    "git diff --name-only | xargs -I{} sh -c 'git restore {}'",
    "git diff --name-only | xargs -I % bash -c 'git checkout -- %'",
    "git diff --name-only | xargs -I{} sh -c 'echo {}; git restore -- {}'",
    "git diff --name-only | xargs sh -c 'git restore \"$@\"' _",
    "git ls-files -m | xargs bash -c 'git checkout -- .'",
    "git diff --name-only | xargs -I{} sh -c 'git reset -- {}'",
    "git diff --name-only | xargs -n1 sh -c 'git clean -f \"$0\"'",
    "git diff --name-only | xargs -I{} env -S 'git restore {}'",
    "git diff --name-only | xargs -I{} sh -c \"bash -c 'git restore {}'\"",
    "git diff --name-only | xargs -I{} sh -c 'git rm -f {}'",
]


@pytest.mark.parametrize("cmd", XARGS_SH_DENY)
def test_gap1_xargs_hereda_rutas_por_stdin_al_recursar_en_la_shell(cmd):
    assert decide(cmd), cmd


@pytest.mark.parametrize("cmd", [
    "git diff --name-only | xargs -I{} sh -c 'echo {}'",
    "git diff --name-only | xargs -I{} sh -c 'git add {}'",
    "git diff --name-only | xargs -n1 sh -c 'git log -1 -- \"$0\"'",
    "ls | xargs -I{} sh -c 'wc -l {}'",
    "git diff --name-only | xargs -I{} sh -c 'git diff --stat -- {}'",
])
def test_gap1_xargs_con_shell_sin_git_destructivo_sigue_permitido(cmd):
    assert decide(cmd) is None, cmd


# --- gap 2: --replace/--eof/--max-lines de GNU xargs: valor OPCIONAL, solo pegado con `=` --------------------------
@pytest.mark.parametrize("cmd", [
    "xargs --replace git restore {}", "xargs --replace git checkout -- {}", "xargs --eof git restore .",
    "xargs --max-lines git restore .", "xargs --replace=X git restore X", "xargs --eof=Z git checkout -- .",
    "xargs --max-lines=2 git restore .", "echo . | xargs --replace git restore {}", "xargs --frobnicate git status",
    "xargs --repl git restore {}",
])
def test_gap2_opciones_largas_de_xargs_con_valor_opcional(cmd):
    assert decide(cmd), cmd


@pytest.mark.parametrize("cmd", [
    "xargs --replace echo {}", "xargs --replace git add {}", "xargs --eof git status", "xargs --max-lines git add",
    "xargs --max-lines=2 git add",
])
def test_gap2_xargs_con_opcion_opcional_y_git_inocuo_sigue_permitido(cmd):
    assert decide(cmd) is None, cmd


# --- gap 4: `env -S` se trocea como lo hace env (comillas y escapes) -------------------------------------------------
@pytest.mark.parametrize("cmd", [
    "env -S 'git reset \"--hard\"'", "env -S 'git \"reset\" --hard'", "env -S 'git restore \".\"'",
    "env -S 'env -S \"git -C .. restore a.txt\"'", "env -S \"git restore '.'\"", "env -S 'git restore \\.'",
    "env -S 'git \"status' ; git restore .", "env -S 'git \"status'",
])
def test_gap4_env_s_con_comillas_dentro_del_valor(cmd):
    assert decide(cmd), cmd


@pytest.mark.parametrize("cmd", [
    "env -S 'git status'", "env -S 'git log -1 --format=\"%h %s\"'", "env -S 'echo \"hola'", "env FOO=1 git status",
])
def test_gap4_env_s_legitimo_sigue_permitido(cmd):
    assert decide(cmd) is None, cmd


@pytest.mark.parametrize("cmd", [
    "env -S '" + "-S " * 3900 + "git status'",
    "env " + "-S x " * 2900 + "git status",
    "env " + "-S" * 4000 + " git status", "env --split-string=" + "-S" * 3900 + " git status",
    "env -S" + "-i" * 5800 + " git status",
], ids=["spaced", "x", "glued", "split-string", "sw-i"])
def test_gap4_env_s_hostil_cuesta_menos_de_0_2_s_de_cpu(cmd):
    t0 = time.process_time()
    razon = decide(cmd)
    assert time.process_time() - t0 < 0.2
    if cmd.startswith("env -S '-S"):
        assert razon, "una cadena de 3.900 `-S` anidados con git no se puede analizar: se deniega"


# --- gap 12: coste del corpus diferencial ---------------------------------------------------------------------------
import test_guardrail_differential as _dif  # noqa: E402
from test_guardrail_differential import necesita_bash, plantilla_repo  # noqa: E402,F401  (el fixture se registra)


@necesita_bash
def test_gap12_el_estado_de_la_plantilla_se_calcula_una_vez(plantilla_repo, tmp_path, monkeypatch):
    """La copia es idéntica a la plantilla: el estado «antes» no se vuelve a leer (2 procesos git por caso)."""
    llamadas = []
    real = _dif._estado
    monkeypatch.setattr(_dif, "_estado", lambda base: (llamadas.append(base), real(base))[1])
    for i in range(3):
        antes, despues, _ = _dif._ejecutar_en_bash(plantilla_repo, tmp_path / f"q{i}", "git status")
        assert antes == despues
    assert len(llamadas) <= 4, llamadas


def test_gap12_tiene_guarda_su_resultado():
    import test_guardrail_differential7 as d7
    d7._tiene("git")
    d7._tiene("git")
    assert d7._tiene.cache_info().hits >= 1
