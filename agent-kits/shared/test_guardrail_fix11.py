#!/usr/bin/env python3
"""Tests de guardrail-check.py: ciclo fix11 de T-06 (plugin-audit-2, fase 1, intento 11). Ejecuta: pytest -q.

Punto 1: dentro de `$(...)`, `<(...)`, `>(...)` y backticks el lector de `case` sigue SOLO la forma simple (lista blanca); cualquier
otra aparicion de `case`/`esac` deja la lectura incompleta. Punto 2: coste lineal (saber si una palabra empieza orden es O(1)).
Punto 3: `$'...'` se decodifica con la semantica de bash. El corpus con bash real vive en `test_guardrail_differential7.py`.
"""
import importlib.util
import os
import time

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("guardrail_check_fix11", os.path.join(HERE, "guardrail-check.py"))
gc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gc)

_BS = chr(92)


def decide(cmd):
    return gc.check_git(cmd, "feature/x")


@pytest.mark.parametrize("orden", [
    "cat <( (case x in x) git status;; esac) )",                       # gap 1: subshell dentro de la sustitucion
    "echo $(true; (case x in x) git status;; esac))",
    "echo $(case x in(x) git status;; esac)",                          # gap 2: `in(` sin espacio
    "cat <(time -p case x in x) git status;; esac)",                   # gap 3: tras un prefijo
    "cat <(coproc case x in x) git status;; esac)",
    "cat <(function f case x in x) git status;; esac; f)",
    'cat <("case" x in; git status; "esac")',                          # gap 5: cabeceras citadas
    "cat <(" + _BS + "then case x in ; git status; " + _BS + "esac)",
    'cat <(case x in "esac"|*) git status;; esac)',                    # gap 6: `esac` como patron
    "cat <(case esac in x|" + _BS + "esac) git status;; esac)",
    "cat <(case x in x) echo esac; git status;; esac)",                # `esac` como argumento
    "echo $(echo case; git status)",                                   # `case` como argumento
    "cat <(case x in [a-z]) git status;; esac)",                       # patron fuera de la lista blanca
    "cat <(case x in @(x|y)) git status;; esac)",
    "cat <(case x in x;) git status;; esac)",
])
def test_toda_forma_fuera_de_la_lista_blanca_deja_la_lectura_incompleta(orden):
    segs, incompleta = gc._segmentos(orden)
    assert incompleta, (orden, segs)
    razon = decide(orden)
    assert razon and "incompleta" in razon, (orden, razon)


@pytest.mark.parametrize("orden", [
    "cat <(case x in x) echo a;; esac)",
    "cat <(time -p case x in x) echo a;; esac)",
    "cat <( (case x in x) echo ok;; esac) )",
])
def test_la_lectura_incompleta_sin_git_no_se_deniega(orden):
    assert decide(orden) is None, orden


@pytest.mark.parametrize("orden", [
    "cat <(case x in x) git status;; esac)",
    'echo $(case "$f" in *.py|*.js) git status;; esac)',
    "diff <(case a in a|b) git show HEAD:a.txt;; esac) /dev/null",
    "echo $(case x in (x) git diff;& y) true;;& *) true;; esac)",
    "echo $(case x in\n  x) git status\n  ;;\nesac)",
    "echo $(echo a; case x in x) git log -1;; esac)",
])
def test_la_forma_simple_sigue_leyendose_entera(orden):
    segs, incompleta = gc._segmentos(orden)
    assert not incompleta, (orden, segs)
    assert decide(orden) is None, orden


def test_la_forma_simple_con_git_destructivo_dentro_del_cuerpo_se_deniega():
    for orden in ("cat <(case x in x) git reset --hard;; esac)", "echo $(case x in x) git restore .;; esac)"):
        assert decide(orden) and "incompleta" not in decide(orden), orden


@pytest.mark.parametrize("prefijo", ["! ", "{ ", "then ", "if ", "time -p ", "do "])
@pytest.mark.parametrize("con_git", [False, True], ids=["sin-git", "con-git"])
def test_las_palabras_de_prefijo_no_son_cuadraticas(prefijo, con_git):
    n = 65536 // len(prefijo)
    orden = ("git status; " if con_git else "") + "echo $(" + prefijo * n + ")"
    t = time.perf_counter()
    decide(orden)
    dt = time.perf_counter() - t
    assert dt < 0.3, f"{dt:.2f}s con {len(orden)} caracteres"


@pytest.mark.parametrize("con_git", [False, True], ids=["sin-git", "con-git"])
def test_los_patrones_y_cuerpos_de_prefijos_son_lineales(con_git):
    cabeza = "git status; " if con_git else ""
    for orden in (
        cabeza + "echo $(case x in " + "x) ! ! ! ;; " * 5000 + "esac)",
        cabeza + "echo $(case x in x) " + "! " * 30000 + ";; esac)",
        cabeza + "echo $({ " * 3000 + "a; " + "} )" * 3000,
        cabeza + "echo $(" + "{ " * 30000 + ")",
    ):
        t = time.perf_counter()
        decide(orden)
        dt = time.perf_counter() - t
        assert dt < 0.3, f"{dt:.2f}s con {len(orden)} caracteres"


@pytest.mark.parametrize("orden", [
    "env -S $'git" + _BS + "trestore .'",
    "env -S $'git" + _BS + "x20restore" + _BS + "x20.'",
    "env -S $'git restore" + _BS + "x20.'",
    "env -S $'git" + _BS + "040restore .'",
])
def test_env_s_con_ansi_c_se_decodifica_como_bash(orden):
    razon = decide(orden)
    assert razon, orden


def test_ansi_c_se_decodifica_en_las_palabras_de_la_orden():
    segs, _ = gc._segmentos("git $'" + _BS + "x72estore' .")
    assert ["git", "restore", "."] in segs, segs
    segs, _ = gc._segmentos("$'" + _BS + "x67it' status")
    assert ["git", "status"] in segs, segs
    segs, _ = gc._segmentos("echo $'a" + _BS + "tb" + _BS + "u00e9" + _BS + "q" + _BS + _BS + _BS + "'' x")
    assert ["echo", "a" + chr(9) + "b" + chr(0xe9) + _BS + "q" + _BS + "'", "x"] in segs, segs


def test_ansi_c_con_nul_corta_la_palabra():
    segs, _ = gc._segmentos("echo $'ab" + _BS + "0cd' x")
    assert ["echo", "ab", "x"] in segs, segs
