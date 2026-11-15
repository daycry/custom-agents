#!/usr/bin/env python3
"""Tests de guardrail-check.py: ciclo fix10 de T-06 (plugin-audit-2, fase 1, intento 10). Ejecuta: pytest -q.

Gap 1: dentro de `$(...)`, `<(...)` y `>(...)` el `)` de un patron de `case` NO cierra la sustitucion. Gap 5: un LF, VT, FF o CR
suelto en el valor de `env -S` es ambiguo entre coreutils 8.x y 9.x y se deniega si la orden lleva git. El corpus con bash real
vive en `test_guardrail_differential7.py` (`BAD10_PARIDAD`, `BAD10_ENV`, `LEGIT10`); aqui, la lectura y sus limites.
"""
import importlib.util
import os

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("guardrail_check_fix10", os.path.join(HERE, "guardrail-check.py"))
gc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gc)


def decide(cmd):
    return gc.check_git(cmd, "feature/x")


def test_el_patron_de_case_no_cierra_la_sustitucion_y_el_git_interior_se_ve():
    segs, incompleta = gc._segmentos("cat <(case x in x) git reset --hard;; esac)")
    assert ["git", "reset", "--hard"] in segs and ["cat", "<()"] in segs and not incompleta, segs


@pytest.mark.parametrize("orden", [
    "cat <(case x in x) git status;; esac)",
    "echo $(case x in (x) git status;; esac)",
    "diff <(case a in a|b) git show HEAD:a.txt;; esac) /dev/null",
    "cat <(case x in x) git diff;& y) true;;& *) true;; esac)",
])
def test_case_legitimo_con_git_inocuo_sigue_permitido(orden):
    assert decide(orden) is None, orden


@pytest.mark.parametrize("orden", [
    "cat <(case x in x) git status)",                                   # `esac` ausente
    "cat <(case x in x) case y in y) git status;; esac;; esac)",         # `case` anidado en la misma sustitucion
    "cat <(case x git status)",                                         # `in` ausente
    "echo $(case x in x) git status",                                   # sustitucion sin cerrar
])
def test_case_que_no_se_puede_seguir_con_certeza_se_deniega_si_hay_git(orden):
    razon = decide(orden)
    assert razon and "incompleta" in razon, (orden, razon)


@pytest.mark.parametrize("orden", [
    "cat <(case x in x) echo a)",
    "cat <(case x in x) case y in y) echo a;; esac;; esac)",
])
def test_case_que_no_se_puede_seguir_pero_sin_git_no_se_deniega(orden):
    assert decide(orden) is None, orden


@pytest.mark.parametrize("valor", ["git\vstatus", "git\fstatus", "git\rstatus", "git\nstatus", "git -c a=b\n#c status"])
def test_env_s_con_un_blanco_de_control_suelto_es_ambiguo(valor):
    with pytest.raises(gc._SinTroceo) as e:
        gc._trocea_s(valor, [0])
    assert e.value.siempre is True      # fix14 (cambio de contrato): ya no depende de que haya git, es lectura opaca


def test_env_s_con_el_blanco_de_control_entrecomillado_o_escapado_se_trocea():
    assert gc._trocea_s("git 'a\nb' c", [0]) == ["git", "a\nb", "c"]
    assert gc._trocea_s('git "a\nb" c', [0]) == ["git", "a\nb", "c"]
    assert gc._trocea_s("git a" + chr(92) + "nb", [0]) == ["git", "a\nb"]
    assert gc._trocea_s("git\tstatus  -s", [0]) == ["git", "status", "-s"]


def test_env_s_ambiguo_se_deniega_con_git_y_sin_el():
    """fix14 (cambio de contrato): antes un `env -S` ambiguo sin git se permitia; es una lectura opaca y deniega siempre."""
    assert decide("env -S 'git status\n#x'")
    assert decide("env -S 'echo a\n#x'")
