"""Fallo cerrado completo del guardarraíl nativo (T-06 fix7, gap 10 del intento 7, ADR-023).

(a) con más de 64 KiB la clave del rol se busca en TODO el flujo (acotado), también cuando va DETRÁS de `tool_input`;
(b) solo la validación del esquema antes de evaluar produce `input-unrecognized`: una excepción dentro del evaluador es
    `evaluator-unavailable` y el lanzador deniega para el rol protegido.
"""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SHARED = ROOT / "agent-kits" / "shared"
NODE = shutil.which("node")

IDS = {"claude": ("custom-agents:implementer", "custom-agents:architect", "custom-agents:qa"),
       "codex": ("custom-agents-implementer", "custom-agents-architect", "custom-agents-qa"),
       "opencode": ("custom-agents-implementer", "custom-agents-architect", "custom-agents-qa")}


def _cuerpo(runtime, identidad, relleno=70000, detras=True):
    clave = "agent" if runtime == "opencode" else "agent_type"
    herramienta = "shell" if runtime == "opencode" else "Bash"
    base = {"session_id": "x", "hook_event_name": "PreToolUse", "cwd": "."}
    entrada = {"tool_name": herramienta, "tool_input": {"command": "echo " + "x" * relleno}}
    if detras:
        return json.dumps({**base, **entrada, clave: identidad})
    return json.dumps({**base, clave: identidad, **entrada})


def _adaptador(entrada, runtime="claude"):
    r = subprocess.run([sys.executable, str(SHARED / "native-guardrail.py"), "--runtime", runtime,
                        "--project-dir", str(ROOT), "--output", "structured"], input=entrada, capture_output=True,
                       encoding="utf-8", timeout=60)
    return json.loads(r.stdout)


@pytest.mark.parametrize("runtime", ["claude", "codex", "opencode"])
@pytest.mark.parametrize("rol", [0, 1], ids=["implementer", "architect"])
def test_a_la_clave_del_rol_detras_de_tool_input_se_encuentra_con_mas_de_64_kib(runtime, rol):
    salida = _adaptador(_cuerpo(runtime, IDS[runtime][rol]), runtime)
    assert salida["decision"] == "deny" and salida["role"] == ("implementer", "architect")[rol], salida
    assert "edit tool" not in salida["reason"], salida["reason"]


@pytest.mark.parametrize("runtime", ["claude", "opencode"])
def test_a_un_rol_no_protegido_con_la_clave_al_final_continua(runtime):
    salida = _adaptador(_cuerpo(runtime, IDS[runtime][2]), runtime)
    assert salida["decision"] == "continue" and salida["diagnostic"] == "input-too-large", salida


def test_a_una_clave_falsificada_dentro_de_una_cadena_no_elige_el_rol():
    """Las comillas de una cadena JSON van escapadas: el texto de la orden no puede forjar la clave del rol."""
    falsa = json.dumps({"tool_name": "Bash", "agent_type": IDS["claude"][2],
                        "tool_input": {"command": 'echo "agent_type": "' + IDS["claude"][0] + '" ' + "x" * 70000}})
    salida = _adaptador(falsa)
    assert salida["decision"] == "continue", salida


def _evaluador_falso(error):
    spec = importlib.util.spec_from_file_location("native_guardrail_fix7", SHARED / "native-guardrail.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)

    class Falso:
        @staticmethod
        def load_config(*a, **k):
            return {"alcance": True, "ramaPrincipal": True, "git": True}, True

        @staticmethod
        def current_branch(*a, **k):
            return "feature/x"

        @staticmethod
        def decide(*a, **k):
            raise error
    modulo._evaluator = lambda: Falso
    return modulo


@pytest.mark.parametrize("error", [ValueError("x"), TypeError("x"), KeyError("x")])
def test_b_una_excepcion_dentro_del_evaluador_es_evaluator_unavailable(error):
    modulo = _evaluador_falso(error)
    carga = {"agent_type": IDS["claude"][0], "tool_name": "Bash", "tool_input": {"command": "git status"}}
    resultado = modulo.evaluate(carga, "claude", str(ROOT), roles=json.loads((SHARED / "native-roles.json").read_text()))
    assert resultado["diagnostic"] == "evaluator-unavailable" and resultado["role"] == "implementer", resultado


def test_b_el_esquema_invalido_sigue_siendo_input_unrecognized():
    modulo = _evaluador_falso(ValueError("no se llega"))
    carga = {"agent_type": IDS["claude"][0], "tool_name": "Bash", "tool_input": {"command": 3}}
    resultado = modulo.evaluate(carga, "claude", str(ROOT), roles=json.loads((SHARED / "native-roles.json").read_text()))
    assert resultado["diagnostic"] == "input-unrecognized" and resultado["decision"] == "continue", resultado


@pytest.mark.skipif(not NODE, reason="Node unavailable")
@pytest.mark.parametrize("runtime", ["claude", "codex", "opencode"])
def test_a_el_lanzador_deniega_con_la_clave_detras_de_tool_input(tmp_path, runtime):
    from test_native_guard_failclosed import _arbol, _correr, _decision
    lanzador, proyecto = _arbol(tmp_path)
    salida, _ = _correr(lanzador, proyecto, runtime, _cuerpo(runtime, IDS[runtime][0]))
    assert _decision(salida, runtime) == "deny", salida
    razon = salida["reason"] if runtime == "opencode" else salida["hookSpecificOutput"]["permissionDecisionReason"]
    assert "edit tool" not in razon, razon
    salida, _ = _correr(lanzador, proyecto, runtime, _cuerpo(runtime, IDS[runtime][2]))
    assert _decision(salida, runtime) == "continue", salida
