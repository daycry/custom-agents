#!/usr/bin/env python3
"""Tests de guardrail-check.py: ciclo fix12 de T-06 (plugin-audit-2, fase 1, intento 12). Ejecuta: pytest -q.

Punto 1: `$'…'` se delimita como el lexer de bash (por pares `\\X`) y despues se decodifica; `\\x{H…}`. Punto 2: la ruta heredada
falla cerrada (`ValueError` del destino y excepcion interna del `main()` de `pre-tool` -> deny). Punto 6: las tres ramas de deny
que llegaron al fix11 sin RED previo (`\\U` fuera de rango, patron vacio, separador en `w`/`i`) tienen aqui su test de regresion:
PASAN contra el codigo del fix11 porque la rama ya existia (se declara en el ledger; no son un RED). Los umbrales de coste de
los guardias no usan el reloj de pared: CPU del proceso o razon de linealidad entre dos tamanos (punto 3).
"""
import importlib.util
import io
import json
import os
import subprocess
import sys
import time

import pytest

from test_guardrail_differential import BASH, necesita_bash

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("guardrail_check_fix12", os.path.join(HERE, "guardrail-check.py"))
gc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gc)

BS = chr(92)


def decide(cmd):
    return gc.check_git(cmd, "feature/x")


# --------------------------------------------------------------------------- punto 1: delimitar como bash ----
@pytest.mark.parametrize("orden", [
    "echo $'" + BS + "c'; git reset --hard #'",                       # gap 1: `\c` NO consume la comilla de cierre
    "echo $'" + BS + "c'; git restore . #'",
    "x=$'" + BS + "c' && git reset --hard && echo '",
    "echo $'" + BS + "c'\ngit reset --hard\n#'",
    "echo $'" + BS + "c" + BS + "' x'; git reset --hard #'",
    "echo $'" + BS + "c" + BS + BS + "'; git reset --hard #'",
    "echo $'" + BS + "c" + BS + BS + BS + "' x'; git reset --hard #'",
    "echo $'" + BS + "cc'; git reset --hard #'",
    "echo $'" + BS + "c" + BS + "c'; git reset --hard #'",
    "echo $'" + BS + "x'; git reset --hard #'",
    "echo $'" + BS + "u'; git reset --hard #'",
    "echo $'" + BS + "U'; git reset --hard #'",
    "echo $'" + BS + "x{}'; git reset --hard #'",
    "echo $'" + BS + "0'; git reset --hard #'",
    "echo $'" + BS + "e'; git reset --hard #'",
])
def test_la_cadena_ansi_c_se_delimita_por_pares_como_bash(orden):
    razon = decide(orden)
    assert razon, orden


def test_ansi_c_delimita_primero_y_decodifica_despues():
    assert gc._ansi_fin("ab" + BS + "c'x'", 0) == 4                    # `\c` es un par; la comilla siguiente CIERRA
    assert gc._ansi_fin("a" + BS + "'b'c", 0) == 4                    # `\'` es un par que no cierra
    assert gc._ansi_fin("sin cierre" + BS, 0) == -1
    segs, _ = gc._segmentos("echo $'" + BS + "c'; git status")
    assert ["echo", BS + "c"] in segs and ["git", "status"] in segs, segs
    segs, _ = gc._segmentos("echo $'" + BS + "c" + BS + BS + "' x")      # `\c\\` = una sola barra de control
    assert ["echo", chr(0x1C), "x"] in segs, segs
    segs, _ = gc._segmentos("echo $'" + BS + "cx" + BS + "ca' y")
    assert ["echo", chr(0x18) + chr(0x01), "y"] in segs, segs


@pytest.mark.parametrize("orden,esperado", [
    ("$'" + BS + "x{67}it' status", "git"),
    ("$'" + BS + "x{0067}it' status", "git"),
    ("$'" + BS + "x{000000067}it' status", "git"),
    ("$'" + BS + "x{67'it status", "git"),                 # sin llave de cierre: bash toma las cifras y sigue
    ("$'" + BS + "x{6' status", chr(6)),
    ("$'" + BS + "x{67}}' status", "g}"),
    ("$'" + BS + "x{1F600}x' status", ""),                 # modulo 256 = 0: NUL, corta la cadena
])
def test_ansi_c_decodifica_x_con_llaves_como_bash_5_2(orden, esperado):
    segs, _ = gc._segmentos(orden)
    assert [esperado, "status"] in segs, (orden, segs)


@pytest.mark.parametrize("orden", [
    "bash -c $'" + BS + "x{67}it reset --hard'",
    "env -S $'" + BS + "x{67}it reset --hard'",
    "eval $'" + BS + "x{67}it reset --hard'",
    "$'" + BS + "x{67}it' reset --hard",
    "$'" + BS + "x{67}'it reset --hard",
    "$'" + BS + "x{0067}it' reset --hard",
    "echo $'" + BS + "x{27}'; git reset --hard #'",
    "env -S $'" + BS + "x{67}it" + BS + "x{9}restore .'",
])
def test_x_con_llaves_no_oculta_git(orden):
    assert decide(orden), orden


# --------------------------------------------------------------------------- punto 2: fallo cerrado ----
def test_destino_con_surrogate_suelto_no_lanza_y_cae_en_cambia_la_base(monkeypatch):
    real = os.path.realpath

    def como_posix(p, *a, **k):
        os.fspath(p).encode("utf-8", "surrogateescape")        # os.fsencode en Linux/macOS: U+D800 no es codificable
        return real(p, *a, **k)

    monkeypatch.setattr(os.path, "realpath", como_posix)
    assert gc._destino_es_el_propio_directorio(chr(0xD800)) is False
    assert decide("cd $'" + BS + "ud800'; git reset --hard")


def test_destino_con_valueerror_de_realpath_no_lanza(monkeypatch):
    def rota(*a, **k):
        raise ValueError("embedded null byte")

    monkeypatch.setattr(os.path, "realpath", rota)
    assert gc._destino_es_el_propio_directorio("sub") is False


def _correr_main(monkeypatch, capsys, payload, proyecto):
    monkeypatch.setattr(sys, "argv", ["guardrail-check.py", "pre-tool", "--project-dir", str(proyecto), "--agent", "implementer"])
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
    code = gc.main()
    return code, capsys.readouterr()


def _bash_payload(orden, cwd):
    return {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": orden}, "cwd": str(cwd)}


def test_main_deniega_con_el_surrogate_en_la_ruta_heredada(tmp_path, monkeypatch, capsys):
    real = os.path.realpath

    def como_posix(p, *a, **k):
        os.fspath(p).encode("utf-8", "surrogateescape")
        return real(p, *a, **k)

    monkeypatch.setattr(os.path, "realpath", como_posix)
    code, cap = _correr_main(monkeypatch, capsys, _bash_payload("cd $'" + BS + "ud800'; git reset --hard", tmp_path), tmp_path)
    assert code == 0
    salida = json.loads(cap.out)
    assert salida["hookSpecificOutput"]["permissionDecision"] == "deny", cap


def test_main_deniega_ante_una_excepcion_interna_con_motivo_explicito(tmp_path, monkeypatch, capsys):
    def rota(*a, **k):
        raise RuntimeError("fallo inyectado")

    monkeypatch.setattr(gc, "decide", rota)
    code, cap = _correr_main(monkeypatch, capsys, _bash_payload("git status", tmp_path), tmp_path)
    assert code == 0
    salida = json.loads(cap.out)["hookSpecificOutput"]
    assert salida["permissionDecision"] == "deny"
    assert "error interno" in salida["permissionDecisionReason"] and "fallo inyectado" in salida["permissionDecisionReason"]


def test_main_sigue_permitiendo_un_json_ilegible(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["guardrail-check.py", "pre-tool", "--project-dir", str(tmp_path)])
    monkeypatch.setattr(sys, "stdin", io.StringIO("{ no es json"))
    assert gc.main() == 0
    cap = capsys.readouterr()
    assert cap.out == "" and "se permite" in cap.err


# --------------------------------------------------------------------------- punto 6: ramas sin RED previo ----
@pytest.mark.parametrize("orden", [
    "git log $'" + BS + "UFFFFFFFF'",                                  # `\U` fuera de rango: lectura incompleta
    "echo $(case x in ) true;; esac); git status",                     # patron vacio
    "echo $(case x; in x) true;; esac); git status",                   # separador en el estado `w`
    "echo $(case ; x in x) true;; esac); git status",                  # separador en el estado `w` (espera el sujeto)
    "echo $(case x ; in x) true;; esac); git status",                  # separador en el estado `i`
])
def test_regresion_de_las_tres_ramas_de_deny_declaradas_sin_red(orden):
    segs, incompleta = gc._segmentos(orden)
    assert incompleta, (orden, segs)
    razon = decide(orden)
    assert razon and "incompleta" in razon, (orden, razon)


# --------------------------------------------------------------------------- punto 3: coste sin reloj de pared ----
def _cpu(orden):
    t = time.process_time()
    decide(orden)
    return time.process_time() - t


def _es_lineal(construir, chico=16384, grande=65536):
    """CPU de `construir(chico)` frente a `construir(grande)`: multiplicar la entrada por ~4 no multiplica el coste por 16 (fix13:
    sin git se analizan entera las ordenes de hasta 256 KB, asi que se compara 64 KB con 250 KB; con git, por debajo del recorte).
    Cada medida es la mejor de dos (el ruido de la CPU solo suma)."""
    c = min(_cpu(construir(chico)) for _ in range(2))
    g = min(_cpu(construir(grande)) for _ in range(2))
    assert g < 10 * max(c, 0.08) + 0.05 and g < 1.0, f"{c:.3f}s -> {g:.3f}s al pasar de {chico} a {grande}"


@pytest.mark.parametrize("prefijo", ["! ", "{ ", "then ", "if ", "time -p ", "do "])
def test_las_palabras_de_prefijo_son_lineales_en_cpu(prefijo):
    _es_lineal(lambda tam: "echo $(" + prefijo * (tam // len(prefijo)) + ")", chico=65536, grande=250000)


@pytest.mark.parametrize("prefijo", ["! ", "{ ", "then ", "if ", "time -p ", "do "])
def test_las_palabras_de_prefijo_con_git_por_debajo_del_recorte_llegan_al_analizador(prefijo):
    """Con git delante y mas de 16 KB o 4.000 palabras el recorte deniega antes de analizar: aqui 1 KB y 4 KB (fix13)."""
    for tam in (1024, 4096):
        orden = "git status; echo $(" + prefijo * (tam // (2 * len(prefijo))) + ")"
        assert "demasiado larga" not in (decide(orden) or ""), (tam, orden[:40])
    _es_lineal(lambda tam: "git status; echo $(" + prefijo * (tam // (2 * len(prefijo))) + ")", chico=1024, grande=4096)


def test_los_patrones_y_cuerpos_de_prefijos_son_lineales_en_cpu():
    for construir in (
        lambda tam: "echo $(case x in " + "x) ! ! ! ;; " * (tam // 12) + "esac)",
        lambda tam: "echo $(case x in x) " + "! " * (tam // 2) + ";; esac)",
        lambda tam: "echo $({ " * (tam // 21) + "a; " + "} )" * (tam // 21),
        lambda tam: "echo $(" + "{ " * (tam // 2) + ")",
    ):
        _es_lineal(construir, chico=65536, grande=250000)


def test_los_patrones_y_cuerpos_de_prefijos_con_git_por_debajo_del_recorte_llegan_al_analizador():
    for construir in (
        lambda tam: "git status; echo $(case x in " + "x) ! ! ! ;; " * (tam // 24) + "esac)",
        lambda tam: "git status; echo $(case x in x) " + "! " * (tam // 4) + ";; esac)",
        lambda tam: "git status; echo $({ " * 1 + "{ " * (tam // 8) + "a; " + "} " * (tam // 8) + ")",
    ):
        for tam in (1024, 4096):
            assert "demasiado larga" not in (decide(construir(tam)) or ""), tam
        _es_lineal(construir, chico=1024, grande=4096)


# --------------------------------------------------------------------------- punto 1: diferencial generado con bash real ----
# Cada escape de bash seguido de `'`, `\\` o `\'` y de `; git reset --hard #'`: si bash ejecuta git, el guardarrail deniega.
# `git` es una FUNCION dentro de cada script (no se ejecuta ningun git real), y cada script es un fichero `.sh` (con `bash -c`
# desde Python MSYS altera las barras invertidas).
ESCAPES = ["", "a", BS + "c", BS + "cx", BS + "cc", BS + "x", BS + "x6", BS + "x{}", BS + "x{67}", BS + "x{27}", BS + "u", BS + "u0067",
           BS + "U", BS + "U00000067", BS + "0", BS + "012", BS + "047", BS + "e", BS + "a", BS + "q", BS + "?", BS + "c?"]
CIERRES = ["'", BS + BS + "'", BS + "''", BS + BS + BS + "''", BS + BS + BS + BS + "'"]
FORMAS = ["echo $'@E@@S@; git reset --hard #'",
          "x=$'@E@@S@ && git reset --hard && echo '",
          "echo $'@E@@S@\ngit reset --hard\n#'",
          "echo $'@E@@S@' && git reset --hard #'"]
NOMBRES = [BS + "x67it", BS + "x{67}it", BS + "147it", BS + "u0067it", BS + "U00000067it", BS + "x{0067}it", "gi" + BS + "x{74}",
           "g" + BS + "x69t", BS + "x{67}" + BS + "x{69}t"]


def _generar():
    for e in ESCAPES:
        for s in CIERRES:
            for forma in FORMAS:
                yield forma.replace("@E@", e).replace("@S@", s)
    for nombre in NOMBRES:
        yield "$'" + nombre + "' reset --hard"
        yield "echo $'" + nombre + "'; $'" + nombre + "' restore ."


@necesita_bash
def test_diferencial12_si_bash_ejecuta_git_el_guardarrail_deniega(tmp_path):
    ordenes = sorted(set(_generar()))
    for k, orden in enumerate(ordenes):
        (tmp_path / f"s_{k}.sh").write_bytes(("git() { echo GITRAN; }\n" + orden + "\n").encode("utf-8"))
    lanzador = tmp_path / "l.sh"
    lanzador.write_bytes((f"for k in $(seq 0 {len(ordenes) - 1}); do echo \"@@$k\"; bash \"s_$k.sh\" 2>/dev/null </dev/null; done\n").encode())
    env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull}
    r = subprocess.run([BASH, str(lanzador)], cwd=str(tmp_path), env=env, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=300, stdin=subprocess.DEVNULL)
    corre = {}
    actual = None
    for linea in r.stdout.splitlines():
        if linea.startswith("@@"):
            actual = int(linea[2:])
            corre[actual] = False
        elif linea.strip() == "GITRAN" and actual is not None:
            corre[actual] = True
    assert len(corre) == len(ordenes), (len(corre), len(ordenes), r.stderr[-300:])
    divergencias = [ordenes[k] for k, ejecuto in corre.items() if ejecuto and decide(ordenes[k]) is None]
    assert not divergencias, f"bash ejecuta git y el guardarrail PERMITE ({len(divergencias)}): {divergencias[:8]}"
    assert sum(corre.values()) >= 40, f"el arnes casi no ejecuta nada ({sum(corre.values())}): la prueba no discrimina"
