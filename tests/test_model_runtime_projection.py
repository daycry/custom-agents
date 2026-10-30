"""Consumer model projections are explicit data, separate from canonical interop."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tomllib

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXPORT = ROOT / "scripts" / "export-interop.py"


def run_projection(config, runtime):
    return subprocess.run(
        [sys.executable, str(EXPORT), "--root", str(ROOT), "--model-config", str(config),
         "--runtime", runtime, "--projection-json"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)


@pytest.mark.parametrize("runtime,expected", [("codex", "qwen3:32b"), ("opencode", "ollama/qwen3:32b")])
def test_f3_explicit_consumer_projection_contains_native_model_without_provider_override(tmp_path, runtime, expected):
    config = tmp_path / "dev.json"
    config.write_text(json.dumps({"modelos": {"architect": {"model": "ollama/qwen3:32b"}}}), encoding="utf-8")
    before = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in (ROOT / "interop").rglob("*") if p.is_file()}
    result = run_projection(config, runtime)
    assert result.returncode == 0, result.stderr
    plan = json.loads(result.stdout)
    assert plan["version"] == 1 and plan["runtime"] == runtime
    assert len(plan["agents"]) == 1
    agent = plan["agents"][0]
    assert agent["role"] == "architect" and agent["id"] == "custom-agents-architect"
    assert agent["model"] == expected and agent["provider"] == "ollama"
    assert agent["sha256"] == hashlib.sha256(agent["content"].encode()).hexdigest()
    if runtime == "codex":
        native = tomllib.loads(agent["content"])
        assert native["model"] == expected
        assert native["name"] == agent["id"]
        assert "model_provider" not in native
        assert "model_reasoning_effort" not in native
        assert "developer_instructions" in native
    else:
        import yaml
        frontmatter = agent["content"].split("---", 2)[1]
        native = yaml.safe_load(frontmatter)
        assert native["model"] == expected
        assert native["mode"] == "subagent" and "permissions" in native
    after = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in (ROOT / "interop").rglob("*") if p.is_file()}
    assert before == after
    again = run_projection(config, runtime)
    assert again.returncode == 0 and again.stdout == result.stdout


@pytest.mark.parametrize("data", [
    [], {"modelos": []}, {"modelos": {"missing-role": {"model": "ollama/qwen3:32b"}}},
    {"modelos": {"architect": {"model": "ollama/model with spaces"}}},
    {"modelos": {"architect": {"model": "ollama/qwen3:32b", "api_key": "fixture-should-not-be-echoed"}}},
])
def test_f3_invalid_explicit_mapping_fails_without_a_partial_projection(tmp_path, data):
    config = tmp_path / "dev.json"
    config.write_text(json.dumps(data), encoding="utf-8")
    result = run_projection(config, "codex")
    assert result.returncode == 1
    assert result.stdout == ""
    assert "Traceback" not in result.stderr
    assert "fixture-should-not-be-echoed" not in result.stderr


def test_f3_oversized_explicit_config_is_rejected(tmp_path):
    config = tmp_path / "dev.json"
    config.write_text(json.dumps({"modelos": {}, "padding": "x" * 262144}), encoding="utf-8")
    result = run_projection(config, "codex")
    assert result.returncode == 1
    assert result.stdout == ""


def test_f3_shared_hardlink_config_is_not_read_as_an_owned_input(tmp_path):
    import os
    config = tmp_path / "dev.json"
    config.write_text(json.dumps({"modelos": {"architect": {"model": "ollama/qwen3:32b"}}}), encoding="utf-8")
    os.link(config, tmp_path / "shared.json")
    result = run_projection(config, "codex")
    assert result.returncode == 1
    assert result.stdout == ""


def test_f3_opencode_effort_is_not_silently_presented_as_applied(tmp_path):
    config = tmp_path / "dev.json"
    config.write_text(json.dumps({"modelos": {"architect": {"model": "ollama/qwen3:32b", "effort": "low"}}}), encoding="utf-8")
    result = run_projection(config, "opencode")
    assert result.returncode == 0, result.stderr
    plan = json.loads(result.stdout)
    assert plan["agents"][0]["model"] == "ollama/qwen3:32b"
    assert any("effort" in warning and "OpenCode" in warning for warning in plan["warnings"])
    frontmatter = plan["agents"][0]["content"].split("---", 2)[1]
    assert "request:" not in frontmatter and "effort:" not in frontmatter
