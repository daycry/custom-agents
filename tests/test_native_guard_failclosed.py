"""El guardarraíl nativo FALLA CERRADO para el rol protegido (T-06 fix6, punto 1, ADR-023).

Si el guard no puede decidir (plazo agotado, entrada > 64 KB, error del evaluador, intérprete ausente), el lanzador
`hooks/run-hook.mjs` DENIEGA cuando el rol es `implementer` o `architect` (la política de roles de ADR-023) y conserva
`continue` para el resto. Los tres runtimes (Claude Code, Codex, OpenCode) pasan por el mismo lanzador.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import pytest

ROOT = Path(__file__).resolve().parents[1]
NODE = shutil.which("node")
pytestmark = pytest.mark.skipif(not NODE, reason="Node unavailable")

IDS = {"claude": ("custom-agents:implementer", "custom-agents:architect", "custom-agents:qa"),
       "codex": ("custom-agents-implementer", "custom-agents-architect", "custom-agents-qa"),
       "opencode": ("custom-agents-implementer", "custom-agents-architect", "custom-agents-qa")}


def _arbol(tmp_path, guard_source=None):
    hooks = tmp_path / "hooks"
    shared = tmp_path / "agent-kits" / "shared"
    hooks.mkdir()
    shared.mkdir(parents=True)
    for name in ("run-hook.mjs", "runtime-supervisor.py"):
        shutil.copy2(ROOT / "hooks" / name, hooks / name)
    shutil.copy2(ROOT / "agent-kits" / "shared" / "native-roles.json", shared / "native-roles.json")
    if guard_source is None:
        for name in ("native-guardrail.py", "guardrail-check.py"):
            shutil.copy2(ROOT / "agent-kits" / "shared" / name, shared / name)
    else:
        (shared / "native-guardrail.py").write_text(guard_source, encoding="utf-8")
    proyecto = tmp_path / "proj"
    proyecto.mkdir()
    return hooks / "run-hook.mjs", proyecto


def _payload(runtime, identidad, orden, extra=""):
    clave = "agent" if runtime == "opencode" else "agent_type"
    cuerpo = {"session_id": "x", "hook_event_name": "PreToolUse", "cwd": "."}
    if identidad:
        cuerpo[clave] = identidad
    cuerpo.update({"tool_name": "shell" if runtime == "opencode" else "Bash", "tool_input": {"command": orden}})
    return json.dumps(cuerpo)


def _correr(lanzador, proyecto, runtime, payload, *, python=True, timeout=30):
    env = {k: v for k, v in os.environ.items() if k.upper() in {"SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT"}}
    env.update(CLAUDE_PROJECT_DIR=str(proyecto), HOME=str(proyecto), USERPROFILE=str(proyecto),
               TEMP=str(proyecto), TMP=str(proyecto))
    if python:
        env["CUSTOM_AGENTS_PYTHON"] = sys.executable
        env["PATH"] = os.environ.get("PATH", "")
    else:
        env["PATH"] = ""
    t = time.perf_counter()
    r = subprocess.run([NODE, str(lanzador), "native-guardrail", "--runtime=" + runtime], input=payload,
                       cwd=proyecto, env=env, capture_output=True, encoding="utf-8", timeout=timeout)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout) if r.stdout.strip() else None, time.perf_counter() - t


def _decision(salida, runtime):
    """`deny` o `continue` según el formato del runtime."""
    if runtime == "opencode":
        return salida["decision"]
    return "deny" if (salida or {}).get("hookSpecificOutput", {}).get("permissionDecision") == "deny" else "continue"


def _razon(salida, runtime):
    return salida["reason"] if runtime == "opencode" else salida["hookSpecificOutput"]["permissionDecisionReason"]


@pytest.mark.parametrize("runtime", ["claude", "codex", "opencode"])
@pytest.mark.parametrize("rol", [0, 1], ids=["implementer", "architect"])
def test_entrada_de_mas_de_64_kb_se_deniega_para_el_rol_protegido(tmp_path, runtime, rol):
    lanzador, proyecto = _arbol(tmp_path)
    salida, _ = _correr(lanzador, proyecto, runtime, _payload(runtime, IDS[runtime][rol], "echo " + "x" * 70000))
    assert _decision(salida, runtime) == "deny", salida
    razon = _razon(salida, runtime)
    assert "64" in razon or "demasiado" in razon, razon
    if runtime == "opencode":
        assert salida["role"] == ("implementer", "architect")[rol]


@pytest.mark.parametrize("runtime", ["claude", "codex", "opencode"])
def test_entrada_de_mas_de_64_kb_continua_para_un_rol_no_protegido(tmp_path, runtime):
    lanzador, proyecto = _arbol(tmp_path)
    salida, _ = _correr(lanzador, proyecto, runtime, _payload(runtime, IDS[runtime][2], "echo " + "x" * 70000))
    assert _decision(salida, runtime) == "continue", salida


@pytest.mark.parametrize("runtime", ["claude", "opencode"])
def test_entrada_de_mas_de_64_kb_sin_identidad_continua(tmp_path, runtime):
    lanzador, proyecto = _arbol(tmp_path)
    salida, _ = _correr(lanzador, proyecto, runtime, _payload(runtime, None, "echo " + "x" * 70000))
    assert _decision(salida, runtime) == "continue", salida


@pytest.mark.parametrize("runtime", ["claude", "codex", "opencode"])
def test_error_del_guard_se_deniega_para_el_rol_protegido_y_continua_para_el_resto(tmp_path, runtime):
    lanzador, proyecto = _arbol(tmp_path, guard_source="import sys\nsys.stdin.read()\nsys.exit(3)\n")
    salida, _ = _correr(lanzador, proyecto, runtime, _payload(runtime, IDS[runtime][0], "git status"))
    assert _decision(salida, runtime) == "deny", salida
    # un rol no protegido ni siquiera llega al guard (prefiltro): continúa
    salida, _ = _correr(lanzador, proyecto, runtime, _payload(runtime, IDS[runtime][2], "git status"))
    assert _decision(salida, runtime) == "continue", salida


@pytest.mark.parametrize("runtime", ["claude", "opencode"])
def test_salida_basura_del_guard_se_deniega_para_el_rol_protegido(tmp_path, runtime):
    lanzador, proyecto = _arbol(tmp_path, guard_source="import sys\nsys.stdin.read()\nprint('no es json')\n")
    salida, _ = _correr(lanzador, proyecto, runtime, _payload(runtime, IDS[runtime][0], "git status"))
    assert _decision(salida, runtime) == "deny", salida


@pytest.mark.parametrize("runtime", ["claude", "codex", "opencode"])
def test_sin_interprete_se_deniega_para_el_rol_protegido(tmp_path, runtime):
    lanzador, proyecto = _arbol(tmp_path)
    salida, _ = _correr(lanzador, proyecto, runtime, _payload(runtime, IDS[runtime][0], "git status"), python=False)
    assert _decision(salida, runtime) == "deny", salida
    salida, _ = _correr(lanzador, proyecto, runtime, _payload(runtime, IDS[runtime][2], "git status"), python=False)
    assert _decision(salida, runtime) == "continue", salida


@pytest.mark.parametrize("runtime", ["claude", "opencode"])
def test_plazo_agotado_se_deniega_para_el_rol_protegido(tmp_path, runtime):
    """Plazo simulado: el guard duerme MUCHO más que el presupuesto del lanzador (4,5 s). Antes: `continue` con el aviso
    «role guard unavailable». Ahora: deny para el implementer, y el lanzador no espera al hijo.

    Fix7 (gap 16): corre en el paso PARALELO. El hijo duerme 120 s y la cota es 100 s: no mide tiempo de pared fino
    (la carga de `-n auto` no la acerca), solo que el lanzador NO espera al hijo (con una espera, el test tardaría 120 s)."""
    lanzador, proyecto = _arbol(tmp_path, guard_source="import sys,time\nsys.stdin.read()\ntime.sleep(120)\n")
    salida, dt = _correr(lanzador, proyecto, runtime, _payload(runtime, IDS[runtime][0], "git status"), timeout=110)
    assert _decision(salida, runtime) == "deny", salida
    assert dt < 100, dt


@pytest.mark.parametrize("runtime", ["claude", "codex", "opencode"])
def test_una_orden_normal_sigue_pasando_por_el_guard_real(tmp_path, runtime):
    lanzador, proyecto = _arbol(tmp_path)
    salida, _ = _correr(lanzador, proyecto, runtime, _payload(runtime, IDS[runtime][0], "git status"))
    assert _decision(salida, runtime) == "continue", salida
    salida, _ = _correr(lanzador, proyecto, runtime, _payload(runtime, IDS[runtime][0], "git push --force origin master"))
    assert _decision(salida, runtime) == "deny", salida


def test_el_adaptador_python_deniega_la_entrada_grande_del_rol_protegido():
    """`native-guardrail.py` solo (sin lanzador): `input-too-large` ya no es `continue` para el rol protegido."""
    entrada = _payload("claude", IDS["claude"][0], "echo " + "x" * 70000)
    r = subprocess.run([sys.executable, str(ROOT / "agent-kits" / "shared" / "native-guardrail.py"), "--runtime", "claude",
                        "--project-dir", str(ROOT), "--output", "structured"], input=entrada, capture_output=True,
                       encoding="utf-8", timeout=30)
    salida = json.loads(r.stdout)
    assert salida["decision"] == "deny" and salida["role"] == "implementer", salida
    entrada = _payload("claude", IDS["claude"][2], "echo " + "x" * 70000)
    r = subprocess.run([sys.executable, str(ROOT / "agent-kits" / "shared" / "native-guardrail.py"), "--runtime", "claude",
                        "--project-dir", str(ROOT), "--output", "structured"], input=entrada, capture_output=True,
                       encoding="utf-8", timeout=30)
    salida = json.loads(r.stdout)
    assert salida["decision"] == "continue" and salida["diagnostic"] == "input-too-large", salida


def test_el_plugin_de_opencode_deniega_si_el_guard_no_decide_para_el_rol_protegido():
    """OpenCode tiene su propio puente (`hooks/opencode-plugin.js`): cuando el agente es uno de los protegidos y el
    proceso del guard no entrega una decisión válida, el callback LANZA (deniega) en vez de `warnGuard(); return`."""
    fuente = (ROOT / "hooks" / "opencode-plugin.js").read_text(encoding="utf-8")
    inicio = fuente.index("const callbacks = { guard: async event => {")
    cuerpo = fuente[inicio:fuente.index("prompt: async event", inicio)]
    assert "protegido" in cuerpo or "protectedRole" in cuerpo, cuerpo
    assert "catch { warnGuard(); return; }" not in cuerpo, cuerpo
