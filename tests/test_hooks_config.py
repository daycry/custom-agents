#!/usr/bin/env python3
"""hooks/hooks.json en exec form (session-end-durable-capture T-03, CA-09):
`SessionEnd` declara `command: bash` + `args: [...]` (no una línea de shell) y `timeout: 5` (era
45: el trabajo pesado ya no corre en el teardown). `scripts/lint_plugin.py` sigue resolviendo el
script referenciado en `args` (antes solo miraba `command`). Ejecutar:
python3 -m pytest -q tests/test_hooks_config.py"""
import importlib.util
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOKS_JSON = os.path.join(ROOT, "hooks", "hooks.json")
LINT_SCRIPT = os.path.join(ROOT, "scripts", "lint_plugin.py")

spec = importlib.util.spec_from_file_location("lint_plugin_hooks", LINT_SCRIPT)
lint_plugin = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lint_plugin)


def _session_end_hook():
    data = json.load(open(HOOKS_JSON, encoding="utf-8"))
    grupos = data["hooks"]["SessionEnd"]
    return grupos[0]["hooks"][0]


def test_session_end_usa_exec_form_con_timeout_5():
    h = _session_end_hook()
    assert h["type"] == "command"
    assert h["command"] == "bash"
    assert h["args"] == ["${CLAUDE_PLUGIN_ROOT}/hooks/session-journal.sh"]
    assert h["timeout"] == 5


def test_lint_plugin_resuelve_el_script_referenciado_en_args():
    """El linter escanea `args` además de `command`: sin ese escaneo, `command: bash` solo no
    referencia ningún fichero del repo y el guardarrail de rutas rotas quedaría ciego a esta forma."""
    errs, warns = lint_plugin.lint_hooks(ROOT)
    assert not any("session-journal.sh" in e for e in errs), errs


def test_lint_plugin_da_error_si_el_script_de_args_no_existe(tmp_path):
    (tmp_path / "hooks").mkdir()
    (tmp_path / "hooks" / "hooks.json").write_text(json.dumps({
        "hooks": {"SessionEnd": [{"hooks": [
            {"type": "command", "command": "bash", "args": ["${CLAUDE_PLUGIN_ROOT}/hooks/no-existe.sh"], "timeout": 5}
        ]}]}
    }), encoding="utf-8")
    errs, warns = lint_plugin.lint_hooks(str(tmp_path))
    assert any("hooks/no-existe.sh" in e and "no existe" in e for e in errs), errs
