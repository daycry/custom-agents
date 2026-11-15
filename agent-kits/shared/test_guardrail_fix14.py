#!/usr/bin/env python3
"""Tests de guardrail-check.py: ciclo fix14 de T-06 (plugin-audit-2, fase 1, intento 14). Ejecuta: pytest -q.

Punto 1: una lectura OPACA (`\\c` + no ASCII, `\\U` fuera de rango, anidado de mas de `_MAX_ANIDADO` niveles, LF/VT/FF/CR suelto en
`env -S`) deniega SIEMPRE al rol protegido, haya git o no: el guardarrail pierde texto o no sabe que ejecuta. Punto 2: el resto de
lecturas incompletas busca git sin distinguir mayusculas, en el texto crudo y en cada palabra decodificada, y la marca se hereda
al reanalizar `bash -c`/`eval`. Punto 3: una opcion de envoltorio desconocida deniega con `GIT`/`Git` y si detras viene un
interprete. Punto 4: corpus con bash real en dos locales. Punto 5: los separadores (`;`, `|`, `&`, salto de linea) cuestan O(n).
"""
import itertools
import os
import subprocess

import pytest

from test_guardrail_differential import BASH, necesita_bash
from test_guardrail_fix12 import _es_lineal, decide, gc
from test_guardrail_fix14_corpus import ENV_S14, FORMAS14

BS = chr(92)


def _barrido_sw():
    """El barrido de la lente B (240 formas): 3 envoltorios x 5 preludios con `\\c` x 4 formas de esconder git x 4 caracteres."""
    chars = ["à", "é", "ʁ", "\U0001F600"]
    pre = ["echo ~c{C}#;", "true #~c{C};", "echo a~c{C}#;", "echo ~c{C};", "echo ~c{C} #;"]
    ocultar = ["~x67it", "~147it", "'\"g\"$'it", "'g$'it"]
    envoltorios = ["bash -c", "eval", "bash <<'E'\neval"]
    for w, p, h, c in itertools.product(envoltorios, pre, ocultar, chars):
        cuerpo = "$'" + p.replace("{C}", c) + h + " reset --hard'"
        yield (w + " " + cuerpo + ("\nE" if w.startswith("bash <<") else "")).replace("~", BS)


SW14 = sorted(set(_barrido_sw()))
TODAS14 = sorted(set(FORMAS14) | set(ENV_S14) | set(SW14))


def _id(o):
    return o.encode("unicode_escape").decode("ascii")[:70]


# --------------------------------------------------------------------------- punto 4: todo el corpus deniega ----
@pytest.mark.parametrize("orden", TODAS14, ids=[_id(o) for o in TODAS14])
def test_toda_forma_del_corpus_de_las_lentes_se_deniega(orden):
    assert decide(orden), orden


# --------------------------------------------------------------------------- punto 1: lectura opaca, sin git ----
OPACAS_SIN_GIT = [
    ("echo $'" + BS + "cé'", BS + "c"),
    ("bash -c $'echo " + BS + "cé'", BS + "c"),
    ("printf %s $'a" + BS + "c\U0001F600b'", BS + "c"),
    ("x=$'" + BS + "cà'; echo $x", BS + "c"),
    ("echo $'" + BS + "U00110000'", "fuera de rango"),
    ("echo $'" + BS + "UFFFFFFFF'", "fuera de rango"),
    ("echo " + "$(echo " * 22 + "x" + ")" * 22, "anidad"),
    ("echo " + "<(echo " * 22 + "x" + ")" * 22, "anidad"),
    ("env -S 'echo a\n#x'", "env -S"),
    ("env -S 'echo a\u000b#x'", "env -S"),
    ("env -S 'echo a\u000c#x'", "env -S"),
    ("env -S 'echo a\r#x'", "env -S"),
    ("env --split-string='echo a\n#x'", "env -S"),
]


@pytest.mark.parametrize("orden,forma", OPACAS_SIN_GIT, ids=[_id(o) for o, _ in OPACAS_SIN_GIT])
def test_la_lectura_opaca_se_deniega_sin_git_y_el_motivo_nombra_la_forma(orden, forma):
    razon = decide(orden)
    assert razon and "opaca" in razon and forma in razon, (orden, razon)


@pytest.mark.parametrize("orden", [
    "echo $'" + BS + "cx'",                              # `\c` + ASCII: se emula (fix12)
    "echo $'" + BS + "U0010FFFF'",                       # el ultimo punto de codigo valido
    "echo " + "$(echo " * 20 + "x" + ")" * 20,           # exactamente _MAX_ANIDADO niveles
    "env -S 'echo a'",
    "env -S 'echo \"a\nb\"'",                            # el LF entrecomillado se trocea sin ambiguedad
    "cat <<E\né\nE",
])
def test_lo_que_no_es_opaco_sigue_permitido(orden):
    assert decide(orden) is None, orden


@pytest.mark.parametrize("valor", ["git\vstatus", "git\fstatus", "git\rstatus", "git\nstatus", "echo a\n#x"])
def test_env_s_con_un_blanco_suelto_deniega_siempre(valor):
    with pytest.raises(gc._SinTroceo) as e:
        gc._trocea_s(valor, [0])
    assert e.value.siempre is True


# --------------------------------------------------------------------------- punto 2: git sin mayusculas ni literales ----
OCULTAR = ["GIT", "Git", "g''it", 'g""it', "$'" + BS + "x67it'", BS + "git", "$'" + BS + "147it'", "g$'it'", "$'g'it"]
INCOMPLETAS = [
    "echo $(time -p case x in *) {G} status;; esac)",
    "echo $(case esac in x|esac) {G} status;& esac)",
    "echo $(! case x in x) {G} status;;& esac); true",
    "echo $(coproc case x in [x]) {G} status;;\nesac)",
    "echo \"$(time -p case x in *) {G} status;; esac)\"",
]


@pytest.mark.parametrize("g", OCULTAR, ids=[_id(g) for g in OCULTAR])
@pytest.mark.parametrize("plantilla", INCOMPLETAS, ids=[str(k) for k in range(len(INCOMPLETAS))])
def test_lectura_incompleta_con_git_oculto_o_en_mayusculas_se_deniega(plantilla, g):
    razon = decide(plantilla.replace("{G}", g))
    assert razon and "incompleta" in razon, (plantilla, g, razon)


@pytest.mark.parametrize("orden", [
    "echo $(time -p case x in *) echo a;; esac)",
    "echo $(case esac in x|esac) true;& esac); echo b",
])
def test_lectura_incompleta_sin_git_sigue_permitida(orden):
    assert decide(orden) is None, orden


PREFIJO_INCOMPLETO = "echo $(time -p case x in *) true;; esac); "
HEREDADAS = [
    PREFIJO_INCOMPLETO + "bash -c \"g''it status\"",
    PREFIJO_INCOMPLETO + "bash -c \"GIT status\"",
    PREFIJO_INCOMPLETO + "bash -c \"$'" + BS + "x67it' status\"",
    PREFIJO_INCOMPLETO + "eval \"g''it status\"",
    PREFIJO_INCOMPLETO + "eval \"Git status\"",
    PREFIJO_INCOMPLETO + "sh -c 'g\"\"it status'",
]


@pytest.mark.parametrize("orden", HEREDADAS, ids=[_id(o) for o in HEREDADAS])
def test_la_marca_incompleta_se_hereda_al_reanalizar_bash_c_y_eval(orden):
    """El externo es incompleto (un `case` fuera de la lista blanca) y no ve git (va escondido dentro de la cadena); el interno,
    leido solo, es `git status` y se permitiria: con la marca heredada, se deniega."""
    razon = decide(orden)
    assert razon and "incompleta" in razon, (orden, razon)


def test_un_cr_con_git_en_mayusculas_o_escapado_se_deniega():
    for orden in ["GIT status\r", "Git status\r", "echo a\r; g''it status"]:
        assert decide(orden), orden
    assert decide("echo a\r") is None


# --------------------------------------------------------------------------- punto 3: opcion de envoltorio desconocida ----
@pytest.mark.parametrize("orden", [
    "nice -+5 GIT reset --hard",
    "nice -+5 Git restore .",
    "nice --5 GIT status",
    "nice -+5 bash -c \"g''it reset --hard\"",
    "nice --5 bash -c 'GIT reset --hard'",
    "nice -+5 bash -c \"$'" + BS + BS + "x67it' reset --hard\"",
    "nice -+5 sh -c 'echo ok'",                           # ante la duda, un interprete detras de una opcion desconocida deniega
    "nice -+5 eval x",
    "nice -+5 env -S 'x'",
    "nice -+5 xargs echo",
])
def test_opcion_de_envoltorio_desconocida_deniega_con_git_en_mayusculas_o_interprete(orden):
    assert decide(orden), orden


@pytest.mark.parametrize("orden", ["nice -+5 make", "nice -+5 echo ok", "env -S 'A=1 make'", "nice -n 5 make", "timeout 5 make"])
def test_opcion_de_envoltorio_desconocida_sin_git_ni_interprete_se_permite(orden):
    assert decide(orden) is None, orden


# --------------------------------------------------------------------------- punto 5: separadores lineales ----
def _sep_formas(tam):
    return [
        "echo " + "a;" * (tam // 2),
        "echo " + "a|" * (tam // 2),
        "echo " + "a&" * (tam // 2),
        "echo " + "a\n" * (tam // 2),
        "echo " + "a && " * (tam // 5),
        "echo " + "a; b=1; " * (tam // 8),
    ]


@pytest.mark.parametrize("k", range(6))
def test_los_separadores_son_lineales_de_64k_a_250k_sin_git(k):
    """Sin git se analiza entera: `echo a;a;…` a 250 KB debe costar menos de 1 s de CPU (antes 1,8 a 4,3 s)."""
    _es_lineal(lambda tam: _sep_formas(tam)[k], chico=65536, grande=250000, absoluto=1.0)


@pytest.mark.parametrize("k", range(6))
def test_los_separadores_con_git_por_debajo_del_recorte_se_analizan(k):
    for tam in (2048, 6000):          # 6.000 B: menos de 4.000 palabras en la forma de saltos de linea (3.000)
        razon = decide("git status; " + _sep_formas(tam)[k])
        assert not razon or "demasiado larga" not in razon, (tam, razon)
    _es_lineal(lambda tam: "git status; " + _sep_formas(tam)[k], chico=2048, grande=6000)


# --------------------------------------------------------------------------- punto 4: bash real en dos locales ----
def _ejecutar_en_locale(tmp_path, ordenes, locale):
    """Cada orden en su `.sh`, con `git`, `GIT` y `Git` FALSOS (funciones exportadas, y un shim `git` delante en el PATH para lo que
    pasa por `env`/`nice`/`xargs`): no corre ningun git real. Devuelve {indice: ¿se ejecuto el git falso?}."""
    base = tmp_path / ("loc_" + (locale or "sin"))
    base.mkdir()
    shim = base / "shim"
    shim.mkdir()
    for nombre in ("git", "GIT", "Git"):         # en un sistema de ficheros sin distinguir mayusculas (Windows) los tres son el mismo fichero
        (shim / nombre).write_bytes(b"#!/bin/sh\necho GITRAN\n")
        os.chmod(shim / nombre, 0o755)
    cabecera = "".join(f"{n}() {{ echo GITRAN; }}\nexport -f {n}\n" for n in ("git", "GIT", "Git"))
    for k, orden in enumerate(ordenes):
        (base / f"s_{k}.sh").write_bytes((cabecera + orden + "\n").encode("utf-8"))
    entorno = ("export LANG=" + locale + "\n") if locale else "unset LANG LC_ALL LC_CTYPE\n"
    lanzador = base / "l.sh"
    lanzador.write_bytes((entorno + "export PATH=\"$PWD/shim:$PATH\"\nexport GIT_DIR=/inexistente-fix14\n"
                          "for n in git GIT Git; do case \"$(type -P $n)\" in \"$PWD\"/shim/*) ;; *) echo \"SHIM-NO-$n\"; exit 3;; esac; done\n"
                          f"for k in $(seq 0 {len(ordenes) - 1}); do echo \"@@$k\"; bash \"s_$k.sh\" 2>/dev/null </dev/null; done\n").encode())
    env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull}
    env.pop("LANG", None), env.pop("LC_ALL", None)
    r = subprocess.run([BASH, str(lanzador)], cwd=str(base), env=env, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=900, stdin=subprocess.DEVNULL)
    assert "SHIM-NO-" not in r.stdout, f"el git falso no es el primero del PATH: {r.stdout[:80]!r}"
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
def test_diferencial14_si_bash_ejecuta_git_el_guardarrail_deniega(tmp_path, locale):
    from test_guardrail_fix14_corpus import SIN_PARIDAD14
    ordenes = TODAS14
    corre = _ejecutar_en_locale(tmp_path, ordenes, locale)
    divergencias = [o for k, o in enumerate(ordenes) if corre[k] and decide(o) is None]
    assert not divergencias, f"bash ejecuta git y el guardarrail PERMITE ({len(divergencias)}): {divergencias[:6]!r}"
    sin_efecto = [o for k, o in enumerate(ordenes) if not corre[k] and o not in SIN_PARIDAD14]
    assert not sin_efecto, f"formas del corpus que bash NO ejecuta y no estan declaradas en SIN_PARIDAD14 ({len(sin_efecto)}): {sin_efecto[:4]!r}"
    assert sum(corre.values()) >= len(ordenes) - len(SIN_PARIDAD14), "el arnes casi no ejecuta nada: la prueba no discrimina"
