"""El escáner del rol del guardarraíl nativo no tiene tope (T-06 fix8, gap 5 del intento 8, ADR-023).

Con más de 64 KiB la clave del rol se busca en TODO el flujo con memoria constante (ventana deslizante), también por
encima de los 16 MiB del tope anterior, y la documentación ya no dice que la entrada grande «continúa».
"""
import json
from pathlib import Path
import subprocess
import sys

import pytest

from test_native_guard_failclosed import IDS, _arbol, _correr, _decision

ROOT = Path(__file__).resolve().parents[1]
GRANDE = 17 * 1024 * 1024


def _cuerpo(runtime, identidad, relleno=GRANDE):
    clave = "agent" if runtime == "opencode" else "agent_type"
    herramienta = "shell" if runtime == "opencode" else "Bash"
    return json.dumps({"session_id": "x", "hook_event_name": "PreToolUse", "cwd": ".", "tool_name": herramienta,
                       "tool_input": {"command": "echo " + "x" * relleno}, clave: identidad})


@pytest.mark.parametrize("runtime", ["claude", "opencode"])
@pytest.mark.parametrize("rol", [0, 1], ids=["implementer", "architect"])
def test_lanzador_clave_del_rol_al_final_de_17_mib_se_deniega(tmp_path, runtime, rol):
    lanzador, proyecto = _arbol(tmp_path)
    salida, _ = _correr(lanzador, proyecto, runtime, _cuerpo(runtime, IDS[runtime][rol]), timeout=120)
    assert _decision(salida, runtime) == "deny", salida


@pytest.mark.parametrize("runtime", ["claude", "opencode"])
def test_lanzador_rol_no_protegido_con_17_mib_continua(tmp_path, runtime):
    lanzador, proyecto = _arbol(tmp_path)
    salida, _ = _correr(lanzador, proyecto, runtime, _cuerpo(runtime, IDS[runtime][2]), timeout=120)
    assert _decision(salida, runtime) == "continue", salida


@pytest.mark.parametrize("runtime", ["claude", "opencode"])
def test_adaptador_python_clave_del_rol_al_final_de_17_mib(runtime):
    def correr(identidad):
        r = subprocess.run([sys.executable, str(ROOT / "agent-kits" / "shared" / "native-guardrail.py"), "--runtime",
                            runtime, "--project-dir", str(ROOT), "--output", "structured"],
                           input=_cuerpo(runtime, identidad), capture_output=True, encoding="utf-8", timeout=120)
        return json.loads(r.stdout)
    deny = correr(IDS[runtime][0])
    assert deny["decision"] == "deny" and deny["role"] == "implementer", deny
    assert correr(IDS[runtime][2])["decision"] == "continue"


@pytest.mark.parametrize("doc", ["docs/INTEROP.md", "docs/en/INTEROP.md"])
def test_interop_no_dice_que_la_entrada_grande_continua(doc):
    texto = (ROOT / doc).read_text(encoding="utf-8")
    plano = " ".join(texto.split())
    for falsa in ("mayor de 64 KiB continúa con diagnóstico", "input above 64 KiB continues with diagnostics"):
        assert falsa not in plano, f"{doc}: la entrada grande se deniega para el rol protegido (ADR-023)"
