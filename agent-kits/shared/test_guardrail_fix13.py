#!/usr/bin/env python3
"""Tests de guardrail-check.py: ciclo fix13 de T-06 (plugin-audit-2, fase 1, intento 13). Ejecuta: pytest -q.

Punto 1: un `\\c` seguido de un caracter NO ASCII (tambien el que sale de un `\\u`/`\\U`/`\\x` anidado) marca la lectura como
incompleta: bash aplica el control al PRIMER BYTE UTF-8 y conserva los de continuacion, y eso depende del locale; no se emula.
Con git o cambio de base se deniega. Diferencial con bash real en los dos locales (sin definir y C.UTF-8). Punto 3: los tests
de coste incluyen `$'...'` y comparan 64 KB con 250 KB (sin git: se analiza entera); con git, por debajo del recorte de 16 KB.
"""
import os
import subprocess
import time

import pytest

from test_guardrail_differential import BASH, necesita_bash
from test_guardrail_fix12 import _cpu, _es_lineal, decide, gc

BS = chr(92)

# Un representante de cada clase de byte inicial UTF-8 (bash aplica `& 0x1F` a ese byte): multiplo de 32 (NUL en el guard viejo),
# = 9 mod 32 (tabulador en el guard viejo), bytes iniciales 0xCA/0xEA (salto de linea solo en bash), 4 bytes y otras.
CLASES = {
    "mult32": [chr(0xE0), chr(0x100), chr(0x80), chr(0x3000), chr(0x10000), chr(0x1F600)],
    "mod9": [chr(0xE9), chr(0x109), chr(0x3009)],
    "lead_ca_ea": [chr(0x281), chr(0xA0A1), chr(0xA001)],
    "otras": [chr(0xF1), chr(0x20AC), chr(0x915), chr(0x10400)],
}
TODOS = [c for lista in CLASES.values() for c in lista]
PLANTILLAS = [
    "bash -c $'echo " + BS + "c{K}; git reset --hard'",
    "sh -c $'echo " + BS + "c{K}; git reset --hard'",
    "eval $'true " + BS + "c{K} && git reset --hard'",
    "bash -c $'echo a" + BS + "c{K}#;git reset --hard'",
    "bash -c $'true #" + BS + "c{K};git reset --hard'",
    "eval $'cat <<E" + BS + "c{K};git reset --hard" + BS + "nE'",
    "bash -c $'echo " + BS + "c{K}" + BS + "ngit reset --hard'",
]
# `\u`/`\U`/`\x` anidados: la cadena externa los decodifica y la interna aplica `\c` al resultado (en C no se decodifican).
ANIDADAS = [
    "bash -c $'eval $" + BS + "'a" + BS + BS + "c" + BS + "u00e9#;git reset --hard" + BS + "''",
    "bash -c $'eval $" + BS + "'true #" + BS + BS + "c" + BS + "u0281;git reset --hard" + BS + "''",
    "bash -c $'eval $" + BS + "'true " + BS + BS + "c" + BS + "U0001F600; git reset --hard" + BS + "''",
    "bash -c $'eval $" + BS + "'a" + BS + BS + "c" + BS + "xc3" + BS + "xa9#;git reset --hard" + BS + "''",
]


def _formas():
    for t in PLANTILLAS:
        for k in TODOS:
            yield t.replace("{K}", k)
    yield from ANIDADAS


# --------------------------------------------------------------------------- punto 1 ----
@pytest.mark.parametrize("orden", sorted(set(_formas())), ids=lambda o: o.encode("unicode_escape").decode("ascii")[:60])
def test_c_con_un_caracter_no_ascii_con_git_se_deniega(orden):
    razon = decide(orden)
    assert razon, orden


@pytest.mark.parametrize("k", TODOS, ids=lambda k: f"U+{ord(k):04X}")
@pytest.mark.parametrize("plantilla", [
    "echo $'a" + BS + "c{K}b'; ls",
    "x=$'" + BS + "c{K}'; echo $x",
    "cat <<E" + chr(10) + "{K}" + chr(10) + "E",
])
def test_c_con_no_ascii_sin_git_ni_cambio_de_base_se_permite(plantilla, k):
    assert decide(plantilla.replace("{K}", k)) is None, plantilla


def test_c_con_no_ascii_marca_incompleta_y_el_ascii_sigue_igual():
    segs, incompleta = gc._segmentos("echo $'" + BS + "c" + chr(0xE0) + "'")
    assert incompleta, segs
    segs, incompleta = gc._segmentos("echo $'" + BS + "cx" + BS + "ca'")          # ASCII: sin cambio (fix12)
    assert not incompleta and ["echo", chr(0x18) + chr(0x01)] in segs, segs


# --------------------------------------------------------------------------- punto 1: diferencial en dos locales ----
def _generar_diferencial():
    ordenes = set(_formas())
    ordenes.update("echo $'" + BS + "c" + k + "'; git reset --hard #'" for k in TODOS)
    ordenes.update("echo $'a" + BS + "c" + k + "b'; git reset --hard" for k in TODOS)
    return sorted(ordenes)


def _ejecutar_en_locale(tmp_path, ordenes, locale):
    """Ejecuta cada orden en su `.sh` con `git` FALSO (funcion exportada y un shim en el PATH delante; no corre ningun git real)."""
    base = tmp_path / ("loc_" + (locale or "sin"))
    base.mkdir()
    shim = base / "shim"
    shim.mkdir()
    (shim / "git").write_bytes(b"#!/bin/sh\necho GITRAN\n")
    os.chmod(shim / "git", 0o755)
    for k, orden in enumerate(ordenes):
        (base / f"s_{k}.sh").write_bytes(("git() { echo GITRAN; }\nexport -f git\n" + orden + "\n").encode("utf-8"))
    entorno = ("export LANG=" + locale + "\n") if locale else "unset LANG LC_ALL LC_CTYPE\n"
    lanzador = base / "l.sh"
    lanzador.write_bytes((entorno + "export PATH=\"$PWD/shim:$PATH\"\n"
                          f"for k in $(seq 0 {len(ordenes) - 1}); do echo \"@@$k\"; bash \"s_$k.sh\" 2>/dev/null </dev/null; done\n").encode())
    env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull}
    env.pop("LANG", None), env.pop("LC_ALL", None)
    r = subprocess.run([BASH, str(lanzador)], cwd=str(base), env=env, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=600, stdin=subprocess.DEVNULL)
    corre, actual = {}, None
    for linea in r.stdout.splitlines():
        if linea.startswith("@@"):
            actual = int(linea[2:])
            corre[actual] = False
        elif linea.strip() == "GITRAN" and actual is not None:
            corre[actual] = True
    assert len(corre) == len(ordenes), (len(corre), len(ordenes), r.stderr[-300:])
    return corre


@necesita_bash
@pytest.mark.parametrize("locale", ["", "C.UTF-8"], ids=["LANG-sin-definir", "C.UTF-8"])
def test_diferencial13_si_bash_ejecuta_git_con_c_no_ascii_el_guardarrail_deniega(tmp_path, locale):
    ordenes = _generar_diferencial()
    corre = _ejecutar_en_locale(tmp_path, ordenes, locale)
    divergencias = [ordenes[k] for k, ejecuto in corre.items() if ejecuto and decide(ordenes[k]) is None]
    assert not divergencias, f"bash ejecuta git y el guardarrail PERMITE ({len(divergencias)}): {divergencias[:6]!r}"
    assert sum(corre.values()) >= 30, f"el arnes casi no ejecuta nada ({sum(corre.values())}): la prueba no discrimina"


# --------------------------------------------------------------------------- punto 3: coste que discrimina ----
def _ansi_formas(tam):
    return [
        "echo $'" + "a" * tam + "'",
        "echo $'" + (BS + "c") * (tam // 2) + "'",
        "echo $'" + (BS + "x{") * (tam // 3) + "'",
        "echo $'" + (BS + "u00e9" + BS + "x41" + BS + "101") * (tam // 14) + "'",
        "echo " + "$'a' " * (tam // 5),
        "echo $'" + (BS + "c" + chr(0xE0)) * (tam // 3) + "'",
    ]


@pytest.mark.parametrize("k", range(6))
def test_las_cadenas_ansi_c_son_lineales_de_64k_a_250k_sin_git(k):
    _es_lineal(lambda tam: _ansi_formas(tam)[k], chico=65536, grande=250000)


@pytest.mark.parametrize("k", range(6))
def test_las_cadenas_ansi_c_con_git_por_debajo_del_recorte_se_analizan(k):
    """Con `git` delante, por encima de 16 KB o 4.000 palabras la orden se deniega SIN analizar (el recorte): estos tamanos
    (2 KB y 8 KB, menos de 4.000 palabras) SI llegan al analizador, asi que el motivo nunca es el del recorte."""
    for tam in (2048, 8192):
        orden = "git status; " + _ansi_formas(tam)[k]
        razon = decide(orden)
        assert not razon or "demasiado larga" not in razon, (tam, razon)
    _es_lineal(lambda tam: "git status; " + _ansi_formas(tam)[k], chico=2048, grande=8192)


def test_el_recorte_de_16kb_con_git_deniega_antes_de_analizar_y_es_barato():
    """Declarado: estas formas con git de 64 KB prueban EL RECORTE (no el analizador): deniegan con su motivo y cuestan casi nada."""
    for k in range(6):
        orden = "git status; " + _ansi_formas(65536)[k]
        t = time.process_time()
        razon = decide(orden)
        assert razon and "demasiado larga" in razon, razon
        assert time.process_time() - t < 0.5
