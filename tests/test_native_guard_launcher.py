"""Native guard entry uses the contained Python path, without shell startup."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
NODE = shutil.which("node")


def launcher_fixture(tmp_path):
    hooks = tmp_path / "hooks"
    shared = tmp_path / "agent-kits" / "shared"
    hooks.mkdir()
    shared.mkdir(parents=True)
    for name in ("run-hook.mjs", "runtime-supervisor.py"):
        shutil.copy2(ROOT / "hooks" / name, hooks / name)
    # This records the launch contract; policy selection has its own real tests.
    (shared / "native-guardrail.py").write_text(
        "import argparse,json,sys\n"
        "assert sys.flags.isolated and sys.flags.no_site\n"
        "p=argparse.ArgumentParser();p.add_argument('--runtime');p.add_argument('--output');"
        "p.add_argument('--project-dir');a=p.parse_args()\n"
        "event=json.load(sys.stdin)\n"
        "assert event['own_marker']=='UTF8 \\u00f1 \\U0001f40d'\n"
        "if a.output=='structured':\n"
        " print(json.dumps({'decision':'deny','role':'architect','reason':a.runtime,'diagnostic':None}))\n"
        "else:\n"
        " print(json.dumps({'hookSpecificOutput':{'hookEventName':'PreToolUse',"
        "'permissionDecision':'deny','permissionDecisionReason':a.runtime}}))\n",
        encoding="utf-8",
    )
    env = {key: value for key, value in os.environ.items()
           if key.upper() in {"SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT"}}
    env.update(PATH="", HOME=str(tmp_path / "home"), USERPROFILE=str(tmp_path / "home"),
               TEMP=str(tmp_path), TMP=str(tmp_path), CUSTOM_AGENTS_PYTHON=sys.executable,
               CLAUDE_PROJECT_DIR=str(tmp_path), PYTHONPATH=str(tmp_path))
    (tmp_path / "sitecustomize.py").write_text("raise RuntimeError('must not load consumer startup')\n", encoding="utf-8")
    return hooks / "run-hook.mjs", env


@pytest.mark.skipif(not NODE, reason="Node unavailable")
@pytest.mark.parametrize("runtime", ["claude", "codex", "opencode"])
def test_native_guard_uses_isolated_python_and_fixed_runtime(tmp_path, runtime):
    launcher, env = launcher_fixture(tmp_path)
    result = subprocess.run([NODE, str(launcher), "native-guardrail", "--runtime=" + runtime],
                            input=json.dumps({"own_marker": "UTF8 \u00f1 \U0001f40d"}, ensure_ascii=False),
                            cwd=tmp_path, env=env, capture_output=True, encoding="utf-8", timeout=15)
    assert result.returncode == 0
    assert result.stdout.strip(), result.stderr
    output = json.loads(result.stdout)
    if runtime == "opencode":
        assert output == {"decision": "deny", "role": "architect", "reason": runtime, "diagnostic": None}
    else:
        assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert output["hookSpecificOutput"]["permissionDecisionReason"] == runtime
    assert "unavailable" not in result.stderr


@pytest.mark.skipif(not NODE, reason="Node unavailable")
def test_native_guard_rejects_unknown_runtime_without_executing_payload(tmp_path):
    launcher, env = launcher_fixture(tmp_path)
    result = subprocess.run([NODE, str(launcher), "native-guardrail", "--runtime=unknown"],
                            input='{"own_marker":"not executed"}', cwd=tmp_path, env=env,
                            capture_output=True, encoding="utf-8", timeout=15)
    assert result.returncode == 0 and not result.stdout
    assert "unknown runtime" in result.stderr


def test_runtime_entry_preserves_fixed_context_argument(tmp_path):
    bash = "C:/Program Files/Git/bin/bash.exe" if os.name == "nt" else shutil.which("bash")
    if not bash or not Path(bash).is_file():
        pytest.skip("Native Bash unavailable")
    shutil.copy2(ROOT / "hooks/runtime-entry.sh", tmp_path / "runtime-entry.sh")
    (tmp_path / "session-context.sh").write_text('printf "%s" "${1:-missing}"\n', encoding="utf-8")
    result = subprocess.run([bash, str(tmp_path / "runtime-entry.sh"), "session-context.sh", "--runtime=codex"],
                            capture_output=True, encoding="utf-8", timeout=10)
    assert result.returncode == 0
    assert result.stdout == "--runtime=codex"
