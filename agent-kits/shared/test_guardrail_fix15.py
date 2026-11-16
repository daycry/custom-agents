#!/usr/bin/env python3
"""Tests de guardrail-check.py: ciclo fix15 de T-06 (plugin-audit-2, fase 1, intento 15). Ejecuta: pytest -q.

Punto 1: la rama se consulta SIEMPRE (con un `branch_fn` real, no `branch=`). Punto 2: la decodificacion de una lectura incompleta
llega a un punto fijo (maximo 8 rondas; si no se estabiliza, es lectura opaca). Punto 3: los envoltorios van en una tabla unica
(`flock -c`, `nohup --`, `chrt`, `taskset`, `doas`, `winpty`, `/usr/bin/time`, abreviaturas de `env -S`, sin la ventana `toks[:6]`).
Punto 4: los limites declarados (`LIMITE15`). Los diferenciales con bash real ejecutan un git FALSO (`git`, `GIT`, `Git`, `git.exe`, `GIT.EXE`).
"""
import os
import subprocess
import time

import pytest

from test_guardrail_differential import BASH, necesita_bash
from test_guardrail_fix12 import _cpu, _es_lineal, decide, gc
from test_guardrail_fix15_corpus import (BS, DOBLE15, ENVOLTORIOS15, HITS15, LEGITIMAS15, LIMITE15, LIMITE15_SOLO_ALLOW,
                                         SIN_PARIDAD15, codificado)

NOMBRES_GIT = ("git", "GIT", "Git", "git.exe", "GIT.EXE")


def _id(o):
    return o.encode("unicode_escape").decode("ascii")[:70]


# --------------------------------------------------------------------------- punto 1: la rama siempre se consulta ----
@pytest.fixture
def proyecto_en_rama(tmp_path):
    """Un repositorio real en la rama de trabajo `feature/x` (sin commits: HEAD simbolico)."""
    r = subprocess.run(["git", "init", "-q", "-b", "feature/x", str(tmp_path)], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    return str(tmp_path)


def _decide_real(orden, proyecto):
    """`decide()` con el `branch_fn` REAL (`current_branch`): sin `branch=` fijado, como lo llama el hook."""
    return gc.decide({"tool_name": "Bash", "tool_input": {"command": orden}}, proyecto, None, branch_fn=gc.current_branch)


SALIDAS_DE_RAMA = [
    "GIT switch main", "Git checkout master", "g''it switch main", "$'" + BS + "x67it' checkout main",
    "GIT.EXE checkout main", "git.exe switch master", BS + "git checkout origin/main", "g\"\"it checkout -",
    "bash -c \"GIT switch main\"", "eval $'" + BS + "x67it' checkout main",
    "echo $(time -p case x in *) GIT switch main;; esac)",
]


@pytest.mark.parametrize("orden", SALIDAS_DE_RAMA, ids=[_id(o) for o in SALIDAS_DE_RAMA])
def test_salir_de_la_rama_se_deniega_con_git_en_cualquier_grafia_y_branch_fn_real(orden, proyecto_en_rama):
    razon = _decide_real(orden, proyecto_en_rama)
    assert razon, orden
    assert "rama de trabajo" in razon or "incompleta" in razon, (orden, razon)


def test_la_forma_en_minusculas_sigue_denegando(proyecto_en_rama):
    assert "rama de trabajo" in _decide_real("git switch main", proyecto_en_rama)
    assert _decide_real("git switch -c feature/otra", proyecto_en_rama) is None


def test_branch_fn_se_consulta_en_cualquier_orden_bash_no_vacia(tmp_path):
    """Ninguna decision depende de `\\bgit\\b` en minusculas: la rama se pide siempre (una sola vez por orden)."""
    llamadas = []
    for orden in ("echo hola", "GIT status", "ls -la", "g''it status"):
        gc.decide({"tool_name": "Bash", "tool_input": {"command": orden}}, str(tmp_path), None,
                  branch_fn=lambda d: llamadas.append(d) or "feature/x")
    assert len(llamadas) == 4, llamadas
    gc.decide({"tool_name": "Bash", "tool_input": {"command": "   "}}, str(tmp_path), None,
              branch_fn=lambda d: llamadas.append(d) or "feature/x")
    assert len(llamadas) == 4, "una orden vacia no consulta la rama"


def test_la_busqueda_de_git_en_minusculas_ya_no_condiciona_ninguna_decision():
    """Se repite el grep de todas las apariciones de `\\bgit\\b` sin `re.I` en el guardarrail: quedan solo las de UNA expresion
    regular de texto (`_ARIT_GIT_RE`, de la aritmetica de bash) y la definicion de `_GIT_TEXTO_RE` (con `re.I`)."""
    import re
    fuente = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "guardrail-check.py"), encoding="utf-8").read()
    sin_re_i = [l.strip() for l in fuente.splitlines() if 're.search(r"\\bgit\\b"' in l]
    assert not sin_re_i, sin_re_i


# --------------------------------------------------------------------------- punto 2: punto fijo de la decodificacion ----
TODAS_DOBLES = DOBLE15 + HITS15


@pytest.mark.parametrize("orden", TODAS_DOBLES, ids=[_id(o) for o in TODAS_DOBLES])
def test_git_codificado_dos_veces_en_una_lectura_incompleta_se_deniega(orden):
    assert decide(orden), orden


@pytest.mark.parametrize("n", [2, 3, 5, 7])
def test_git_codificado_n_veces_hasta_8_rondas_se_deniega_por_git(n):
    """`codificado(n)` necesita n + 1 rondas (n de `\x5c` y la ultima de `\x67`): con n = 7 son 8, el maximo."""
    orden = "echo $(time -p case x in *) bash -c $'" + codificado(n) + " reset --hard';; esac)"
    razon = decide(orden)
    assert razon, (n, orden)
    assert "opaca" not in razon, (n, razon)              # hasta 8 rondas se DECODIFICA y se deniega por git: no por no poder leerla (mata el mutante de 1 ronda)


@pytest.mark.parametrize("n", [8, 9, 10, 20])
def test_si_la_decodificacion_no_se_estabiliza_en_8_rondas_es_lectura_opaca(n):
    orden = "echo $(time -p case x in *) bash -c $'" + codificado(n) + " reset --hard';; esac)"
    razon = decide(orden)
    assert razon and "opaca" in razon, (n, razon)


def test_una_lectura_incompleta_sin_git_ni_escapes_sigue_permitida():
    for orden in ("echo $(time -p case x in *) echo a;; esac)", "echo $(case x in *) printf '%s' '" + BS + "x41';; esac)"):
        assert decide(orden) is None, orden


def test_el_aplanado_iterado_es_lineal_en_el_tamano():
    base = "echo $(time -p case x in *) {} ;; esac); true"
    _es_lineal(lambda tam: base.replace("{}", "echo a; " * (tam // 8)), chico=65536, grande=250000)


# --------------------------------------------------------------------------- punto 3: envoltorios por tabla ----
@pytest.mark.parametrize("orden", [o for o, _ in ENVOLTORIOS15], ids=[_id(o) for o, _ in ENVOLTORIOS15])
def test_los_envoltorios_de_las_lentes_se_deniegan(orden):
    assert decide(orden), orden


@pytest.mark.parametrize("orden", LEGITIMAS15, ids=[_id(o) for o in LEGITIMAS15])
def test_los_envoltorios_sin_git_destructivo_siguen_permitidos(orden):
    assert decide(orden) is None, orden


def test_la_cadena_de_flock_c_se_analiza_como_bash_c_y_hereda_la_marca():
    assert decide("echo $(time -p case x in *) true;; esac); flock F -c \"g''it status\"")
    assert decide("flock F -c 'bash -c \"git reset --hard\"'")
    assert decide("flock F -c 'cd .. && git restore src/x.py'")        # el cambio de base dentro de la cadena


def test_nice_busca_el_interprete_en_toda_la_orden_no_en_una_ventana_de_seis_palabras():
    for k in (6, 12, 40):
        assert decide("nice -+5 " + "-n 1 " * k + "bash -c \"g''it reset --hard\""), k
        assert decide("nice -+5 " + "nice " * k + "bash -c \"g''it reset --hard\""), k


def test_la_busqueda_del_interprete_tras_una_opcion_desconocida_es_lineal():
    _es_lineal(lambda tam: "nice -+5 " + "-n 1 " * (tam // 5) + "make", chico=16384, grande=65536)


def test_las_abreviaturas_de_env_s_equivalen_a_s():
    for forma in ("--split", "--spli", "--s"):
        assert decide("env " + forma + " 'git reset --hard'"), forma
        assert decide("env " + forma + "='git reset --hard'"), forma
    assert decide("env --s 'make test'") is None


def test_env_con_una_abreviatura_ambigua_deniega_con_git():
    assert decide("env --i git reset --hard"), "`--i` es ambigua (`--ignore-environment`, `--ignore-signal`)"


def test_nohup_ya_no_esta_en_control_y_acepta_el_doble_guion():
    assert "nohup" not in gc._CONTROL
    assert "nohup" in gc._ENVOLTORIOS
    assert decide("nohup -- git reset --hard")


def test_la_tabla_de_envoltorios_declara_los_nuevos():
    for nombre in ("chrt", "taskset", "doas", "winpty", "time", "su", "flock", "nohup"):
        assert nombre in gc._ENVOLTORIOS, nombre


# --------------------------------------------------------------------------- punto 4: limites declarados ----
@pytest.mark.parametrize("orden,clase", LIMITE15 + LIMITE15_SOLO_ALLOW, ids=[_id(o) for o, _ in LIMITE15 + LIMITE15_SOLO_ALLOW])
def test_limite15_el_guardarrail_no_ve_la_expansion_en_la_palabra_de_mando(orden, clase):
    """LIMITE declarado: bash expande la palabra de mando hasta `git` y el guardarrail lee lo que la orden DICE."""
    assert decide(orden) is None, (clase, orden)


def test_el_limite_esta_en_la_documentacion_del_rol():
    doc = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "docs", "agents", "implementer.md"),
               encoding="utf-8").read()
    for pista in ("{git,}", "g${x}it", "xargs git", "NUL", "LIMITE15"):
        assert pista in doc, pista


# --------------------------------------------------------------------------- diferencial con bash real ----
def _ejecutar15(tmp_path, ordenes, locale, binarios):
    """Cada orden en su `.sh`, con `git`, `GIT`, `Git`, `git.exe` y `GIT.EXE` FALSOS (funciones exportadas y un shim delante en el PATH):
    no corre ningun git real. Devuelve ({indice: ¿git falso?}, {binario ausente})."""
    base = tmp_path / ("l15_" + (locale or "sin"))
    base.mkdir()
    shim = base / "shim"
    shim.mkdir()
    for nombre in NOMBRES_GIT:
        (shim / nombre).write_bytes(b"#!/bin/sh\necho GITRAN\n")
        os.chmod(shim / nombre, 0o755)
    cabecera = "".join(f"{n}() {{ echo GITRAN; }}\nexport -f {n}\n" for n in NOMBRES_GIT)
    for k, orden in enumerate(ordenes):
        (base / f"s_{k}.sh").write_bytes((cabecera + orden + "\n").encode("utf-8"))
    entorno = ("export LANG=" + locale + "\n") if locale else "unset LANG LC_ALL LC_CTYPE\n"
    comprobar = "for n in " + " ".join(NOMBRES_GIT) + "; do case \"$(type -P $n)\" in \"$PWD\"/shim/*) ;; *) echo \"SHIM-NO-$n\"; exit 3;; esac; done\n"
    ausentes = "".join(f"[ -x {b} ] || type -P {b} >/dev/null || echo \"AUSENTE-{b}\"\n" for b in sorted(set(binarios)))
    lanzador = base / "l.sh"
    lanzador.write_bytes((entorno + "export PATH=\"$PWD/shim:$PATH\"\nexport GIT_DIR=/inexistente-fix15\n" + comprobar + ausentes +
                          f"for k in $(seq 0 {len(ordenes) - 1}); do echo \"@@$k\"; timeout 20 bash \"s_$k.sh\" 2>/dev/null </dev/null; done\n").encode())
    env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull}
    env.pop("LANG", None), env.pop("LC_ALL", None)
    r = subprocess.run([BASH, str(lanzador)], cwd=str(base), env=env, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=900, stdin=subprocess.DEVNULL)
    assert "SHIM-NO-" not in r.stdout, f"el git falso no es el primero del PATH: {r.stdout[:80]!r}"
    corre, actual, ausente = {}, None, set()
    for linea in r.stdout.splitlines():
        if linea.startswith("@@"):
            actual = int(linea[2:])
            corre[actual] = False
        elif linea.startswith("AUSENTE-"):
            ausente.add(linea[8:])
        elif linea.strip() == "GITRAN" and actual is not None:
            corre[actual] = True
    assert len(corre) == len(ordenes), (len(corre), len(ordenes), r.stderr[-300:])
    return corre, ausente


CORPUS_BASH15 = sorted(set(DOBLE15) | set(HITS15) | {o for o, _ in ENVOLTORIOS15})
BINARIO_DE = {o: b for o, b in ENVOLTORIOS15}


@necesita_bash
@pytest.mark.parametrize("locale", ["", "C.UTF-8"], ids=["LANG-sin-definir", "C.UTF-8"])
def test_diferencial15_si_bash_ejecuta_git_el_guardarrail_deniega(tmp_path, locale):
    corre, ausente = _ejecutar15(tmp_path, CORPUS_BASH15, locale, [b for _, b in ENVOLTORIOS15 if not b.startswith("/")])
    divergencias = [o for k, o in enumerate(CORPUS_BASH15) if corre[k] and decide(o) is None]
    assert not divergencias, f"bash ejecuta git y el guardarrail PERMITE ({len(divergencias)}): {divergencias[:6]!r}"
    sin_efecto = [o for k, o in enumerate(CORPUS_BASH15) if not corre[k] and o not in SIN_PARIDAD15 and BINARIO_DE.get(o) not in ausente
                  and not (BINARIO_DE.get(o, "").startswith("/") and not os.path.exists(BINARIO_DE[o]))]
    assert not sin_efecto, f"formas que bash NO ejecuta, con su binario presente, y no declaradas en SIN_PARIDAD15 ({len(sin_efecto)}): {sin_efecto[:4]!r}"
    ejecutadas = sum(corre.values())
    assert ejecutadas >= len(DOBLE15) + len(HITS15) - 2, f"el arnes casi no ejecuta las formas de punto 2 ({ejecutadas})"


@necesita_bash
def test_limite15_bash_ejecuta_las_formas_de_llaves_y_parametros(tmp_path):
    ordenes = [o for o, _ in LIMITE15]
    corre, _ = _ejecutar15(tmp_path, ordenes, "", ["bash"])
    ejecutadas = [o for k, o in enumerate(ordenes) if corre[k]]
    assert len(ejecutadas) >= 4, ejecutadas      # las llaves, los parametros y xargs: bash 5.2 las ejecuta; el limite es real


@necesita_bash
def test_el_shim_de_git_cubre_las_cinco_grafias(tmp_path):
    corre, _ = _ejecutar15(tmp_path, [n + " status" for n in NOMBRES_GIT], "", ["bash"])
    assert all(corre.values()), corre
