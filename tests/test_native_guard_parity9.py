"""Paridad de los dos escaneres del rol del guardarrail nativo (T-06 fix9, gap 3 del intento 9, ADR-023).

`native-guardrail.py` (adaptador Python) y `hooks/run-hook.mjs` (lanzador) buscan la clave del rol con el MISMO patron en
todo el flujo de mas de 64 KiB. Una divergencia (el fix8 dejo la alternativa de escape distinta en uno y otro) hace que el mismo
payload deniegue en un camino y continue en el otro. El mismo corpus (identidades escapadas, clave partida entre dos
lecturas, blancos) pasa por los dos y se exige el mismo rol.
"""
import importlib.util
import io
import json
from pathlib import Path

import pytest

from test_native_guard_failclosed import IDS, _arbol, _correr, _decision

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("native_guardrail_parity9", ROOT / "agent-kits" / "shared" / "native-guardrail.py")
ng = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ng)

BS = chr(92)
RELLENO = "x" * 70000          # el payload pasa de 64 KiB: decide el escaner, no el evaluador
CLAUDE_IMPL = "custom-agents:implementer"


def _clave(runtime):
    return "agent" if runtime == "opencode" else "agent_type"


def _tool(runtime):
    return "shell" if runtime == "opencode" else "Bash"


def _escapada(identidad, letra):
    """La identidad con la primera `letra` escrita como secuencia de escape unicode de JSON (valida)."""
    k = identidad.index(letra)
    return identidad[:k] + BS + "u%04x" % ord(letra) + identidad[k + 1:]


def _cuerpo(runtime, valor_crudo, *, antes="", despues="", clave=None):
    clave = clave or _clave(runtime)
    return ('{"session_id":"x","hook_event_name":"PreToolUse","cwd":".","tool_name":"%s","tool_input":{"command":"echo %s"},'
            '%s"%s"%s:%s%s}' % (_tool(runtime), RELLENO, "", clave, antes, despues, valor_crudo))


def _corpus(runtime):
    """(nombre, cuerpo, ¿deniega?) — el cuerpo es JSON valido salvo `escape_invalido`."""
    impl, arq, qa = IDS[runtime][0], IDS[runtime][1], IDS[runtime][2]
    lit = lambda v: '"' + v + '"'
    c = [
        ("llano", _cuerpo(runtime, lit(impl)), True),
        ("escape_u_en_la_m", _cuerpo(runtime, lit(_escapada(impl, "m"))), True),
        ("escape_u_en_letra", _cuerpo(runtime, lit(_escapada(impl, "e"))), True),
        ("escape_u_architect", _cuerpo(runtime, lit(_escapada(arq, "a"))), True),
        ("blancos_64", _cuerpo(runtime, lit(impl), antes=" " * 64, despues=" " * 64), True),
        ("saltos_y_blancos", _cuerpo(runtime, lit(impl), antes="\n  ", despues="\n\t "), True),
        ("blancos_65_limite_documentado", _cuerpo(runtime, lit(impl), antes=" " * 65, despues=""), False),
        ("rol_no_protegido", _cuerpo(runtime, lit(qa)), False),
        ("rol_no_protegido_escapado", _cuerpo(runtime, lit(_escapada(qa, "q"))), False),
        ("sufijo_extra", _cuerpo(runtime, lit(impl + "X")), False),
        ("escape_invalido", _cuerpo(runtime, lit(impl[:3] + BS + "-" + impl[3:])), False),
        ("clave_forjada_en_un_valor",
         '{"tool_input":{"command":"echo %s %s%s:%s%s"}}' % (RELLENO, BS + '"' + _clave(runtime) + BS + '"', "", BS + '"' + impl + BS + '"', ""), False),
    ]
    return c


def _decide_python(runtime, cuerpo):
    raw = cuerpo.encode("utf-8")
    return ng._role_of_stream(raw[:65537], io.BytesIO(raw[65537:]), runtime) is not None


@pytest.mark.parametrize("runtime", ["claude", "opencode"])
def test_el_escaner_python_da_el_rol_esperado_en_todo_el_corpus(runtime):
    fallos = [(n, esperado) for n, cuerpo, esperado in _corpus(runtime) if _decide_python(runtime, cuerpo) != esperado]
    assert not fallos, f"{runtime}: el escaner del adaptador Python no coincide con lo esperado: {fallos}"


@pytest.mark.parametrize("runtime", ["claude", "opencode"])
def test_lanzador_y_adaptador_python_coinciden_en_todo_el_corpus(tmp_path, runtime):
    lanzador, proyecto = _arbol(tmp_path)
    distintos = []
    for nombre, cuerpo, esperado in _corpus(runtime):
        salida, _ = _correr(lanzador, proyecto, runtime, cuerpo, timeout=120)
        lanza = _decision(salida, runtime) == "deny"
        if not (lanza == _decide_python(runtime, cuerpo) == esperado):
            distintos.append((nombre, esperado, lanza, _decide_python(runtime, cuerpo)))
    assert not distintos, f"{runtime}: (caso, esperado, lanzador, python) {distintos}"


@pytest.mark.parametrize("runtime", ["claude", "opencode"])
def test_clave_partida_entre_dos_lecturas_se_encuentra_igual_en_los_dos(tmp_path, runtime):
    """La clave cae a caballo de la frontera de la segunda lectura del adaptador (`_CHUNK` tras los 64 KiB + 1 iniciales)."""
    clave, impl = _clave(runtime), IDS[runtime][0]
    cola = '"%s":"%s"}' % (clave, _escapada(impl, "m"))
    frontera = 65537 + ng._CHUNK
    lanzador, proyecto = _arbol(tmp_path)
    for desfase in (3, 12, 20):
        pre = '{"tool_input":{"command":"echo '
        relleno = frontera - desfase - len(pre) - 3
        cuerpo = pre + "x" * relleno + '"},' + cola
        assert cuerpo.encode()[frontera - desfase:frontera - desfase + 6] == ('"' + clave).encode()[:6]
        assert _decide_python(runtime, cuerpo), (runtime, desfase)
        salida, _ = _correr(lanzador, proyecto, runtime, cuerpo, timeout=120)
        assert _decision(salida, runtime) == "deny", (runtime, desfase)
