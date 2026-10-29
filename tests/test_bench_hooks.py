"""Contract tests for hook baselines; no wall-clock thresholds in CI."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/bench-hooks.py"


@pytest.fixture
def bench():
    assert SCRIPT.is_file(), "missing reproducible hook benchmark"
    spec = importlib.util.spec_from_file_location("bench_hooks", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_cli_rejects_zero_runs_with_usage_error():
    result = subprocess.run([sys.executable, str(SCRIPT), "--runs", "0", "--json"],
                            capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert result.returncode == 2
    assert "--runs must be at least 1" in result.stderr


def test_statistics_exclude_warmup(bench, monkeypatch):
    durations = iter([9000, 8000, 1, 2, 3, 4])
    calls = []
    def invoke(root, case, payload, project, timeout):
        calls.append(project)
        assert project != ROOT and project.is_dir()
        return {"ms": next(durations), "error": None}
    monkeypatch.setattr(bench, "invoke", invoke)
    result = bench.measure_case(ROOT, bench.registered_hooks(ROOT)[0], "claude", 4, 2, 30)
    assert len(calls) == 6
    assert result["muestras_ms"] == [1, 2, 3, 4]
    assert result["mediana_ms"] == 2.5
    assert result["p95_ms"] == 3.85
    assert result["max_ms"] == 4
    assert result["estado"] == "OK"
    assert all(not project.exists() for project in calls)


def test_all_registrations_have_payloads_for_each_runtime(bench, tmp_path):
    cases = bench.registered_hooks(ROOT)
    assert {case["evento"] for case in cases} >= {"PreToolUse", "SessionStart", "SessionEnd"}
    for runtime in bench.RUNTIMES:
        for case in cases:
            payload = bench.load_payload(ROOT, runtime, case["evento"], tmp_path)
            assert payload["hook_event_name"] == case["evento"]
            assert payload["cwd"] == str(tmp_path)
            if case["evento"] == "PostToolUse":
                assert "docs/roadmap/bench/tasks.md" in payload["tool_input"]["file_path"].replace(chr(92), "/")


def test_timeout_is_structured_failure_without_success_timings(bench, monkeypatch):
    monkeypatch.setattr(bench, "invoke", lambda *args: {"ms": 30, "error": "timeout"})
    result = bench.measure_case(ROOT, bench.registered_hooks(ROOT)[0], "codex", 10, 1, .1)
    assert result["estado"] == "FALLO"
    assert result["fallo"] == "timeout"
    assert result["mediana_ms"] is None
    assert result["muestras_ms"] == []


def test_tokens_declare_estimate_and_count_exact_source_characters(bench):
    result = bench.token_report(ROOT)
    assert "estimación" in result["tokens_fijos"]["metodo"]
    desc = result["tokens_fijos"]["descriptions"]
    assert desc["caracteres"] > 10000
    for runtime in bench.RUNTIMES:
        assert result["tokens_fijos"]["por_runtime"][runtime] > desc["tokens_estimados"]
    for relative in ["commands/dev-cycle.md", "agent-kits/shared/knowledge-check.md"]:
        assert result["tokens_bajo_demanda"][relative]["caracteres"] == len((ROOT / relative).read_text(encoding="utf-8"))


def test_reports_json_markdown_and_failure_exit_code(bench, monkeypatch, capsys):
    monkeypatch.setattr(bench, "registered_hooks", lambda root: [{"hook": "probe", "evento": "PreToolUse", "registro": "PreToolUse:0:0"}])
    monkeypatch.setattr(bench, "measure_case", lambda *args: {
        "runtime": args[2], "hook": "probe", "evento": "PreToolUse", "registro": "PreToolUse:0:0",
        "estado": "FALLO", "fallo": "process exit 1", "mediana_ms": None,
        "p95_ms": None, "max_ms": None, "muestras_ms": []})
    assert bench.main(["--runs", "10", "--json"]) == 1
    report = json.loads(capsys.readouterr().out)
    assert report["estado"] == "FALLO"
    assert report["linea_base"] is False
    assert len(report["hooks"]) == 3
    assert report["maquina"]["sistema"]
    rendered = bench.markdown(report)
    assert "| Runtime | Evento | Hook |" in rendered
    assert "FALLO" in rendered and "process exit 1" in rendered
    assert "estimación" in rendered


@pytest.mark.parametrize("outcome,expected", [
    (subprocess.TimeoutExpired("node", 1), "timeout after 1s"),
    (FileNotFoundError(2, "missing"), "cannot start launcher: FileNotFoundError"),
    (subprocess.CompletedProcess([], 3, "", ""), "process exit 3"),
    (subprocess.CompletedProcess([], 0, "", "Python unavailable; hook skipped"), "launcher diagnostic"),
    (subprocess.CompletedProcess([], 0, "not json", ""), "invalid SessionStart output"),
    (subprocess.CompletedProcess([], 0, "{}", ""), "missing SessionStart context"),
])
def test_invoke_never_counts_degradation_as_fast_success(bench, monkeypatch, tmp_path, outcome, expected):
    def run(command, **kwargs):
        assert kwargs["cwd"] == tmp_path
        assert kwargs["env"]["CLAUDE_PROJECT_DIR"] == str(tmp_path)
        assert kwargs["env"]["CUSTOM_AGENTS_PYTHON"] == sys.executable
        assert kwargs["encoding"] == "utf-8" and kwargs["errors"] == "replace"
        assert "shell" not in kwargs
        if isinstance(outcome, Exception):
            raise outcome
        return outcome
    monkeypatch.setattr(bench.subprocess, "run", run)
    case = {"hook": "session-context.sh", "runtime": "codex"}
    result = bench.invoke(ROOT, case, {}, tmp_path, 1)
    assert expected in result["error"]


def test_invoke_accepts_valid_context_and_explicit_runtime(bench, monkeypatch, tmp_path):
    def run(command, **kwargs):
        assert command[-1] == "--runtime=opencode"
        return subprocess.CompletedProcess(command, 0, json.dumps({"hookSpecificOutput": {"additionalContext": "fixture"}}), "")
    monkeypatch.setattr(bench.subprocess, "run", run)
    result = bench.invoke(ROOT, {"hook": "session-context.sh", "runtime": "opencode"}, {}, tmp_path, 1)
    assert result["error"] is None and result["ms"] >= 0


@pytest.mark.parametrize("handler", [
    {"command": "echo unsafe"},
    {"command": "node", "args": ["${CLAUDE_PLUGIN_ROOT}/hooks/run-hook.mjs", "../escape"]},
])
def test_unknown_registration_cannot_be_executed(bench, tmp_path, handler):
    (tmp_path / "hooks").mkdir()
    (tmp_path / "hooks/hooks.json").write_text(json.dumps({"hooks": {"SessionStart": [{"hooks": [handler]}]}}))
    with pytest.raises(ValueError):
        bench.registered_hooks(tmp_path)


def test_empty_registry_and_missing_payload_are_errors(bench, tmp_path):
    (tmp_path / "hooks").mkdir()
    (tmp_path / "hooks/hooks.json").write_text('{"hooks":{}}')
    with pytest.raises(ValueError, match="no hook"):
        bench.registered_hooks(tmp_path)
    with pytest.raises(ValueError, match="missing or invalid fixture"):
        bench.load_payload(ROOT, "claude", "UnknownEvent", tmp_path)


def test_tokens_only_markdown_does_not_launch_hooks(bench, monkeypatch, capsys):
    monkeypatch.setattr(bench, "measure_case", lambda *args: pytest.fail("tokens-only launched a hook"))
    assert bench.main(["--tokens-only", "--md"]) == 0
    output = capsys.readouterr().out
    assert "Tokens fijos estimados" in output and "commands/dev-cycle.md" in output


def test_unknown_hook_is_structured_cli_error(bench, capsys):
    assert bench.main(["--hook", "not-registered", "--json"]) == 1
    report = json.loads(capsys.readouterr().out)
    assert report["estado"] == "FALLO" and "not registered" in report["fallo"]
    assert "FALLO" in bench.markdown(report)


@pytest.mark.parametrize("args", [["--warmup", "-1"], ["--timeout", "nan"], ["--timeout", "0"], ["--runs", "0"]])
def test_invalid_cli_bounds(bench, args):
    with pytest.raises(SystemExit) as error:
        bench.main(args)
    assert error.value.code == 2


@pytest.mark.parametrize("hook", ["session-journal.sh", "user-prompt-capture.sh"])
def test_silent_capture_without_persistence_is_failure(bench, monkeypatch, tmp_path, hook):
    monkeypatch.setattr(bench.subprocess, "run", lambda *args, **kwargs: subprocess.CompletedProcess([], 0, "", ""))
    result = bench.invoke(ROOT, {"hook": hook, "runtime": "codex"}, {"session_id": "bench-hooks"}, tmp_path, 1)
    assert result["error"] is not None
    assert "capture did not persist" in result["error"]


@pytest.mark.parametrize("hook,receipt,record", [
    ("session-journal.sh", ".claude/journal/outbox/fixture.json", {"session_id": "bench-hooks"}),
    ("user-prompt-capture.sh", ".claude/session-prompts-bench-hooks.log", {"prompt": "fixture"}),
])
def test_capture_requires_matching_persisted_fixture(bench, monkeypatch, tmp_path, hook, receipt, record):
    monkeypatch.setattr(bench.subprocess, "run", lambda *args, **kwargs: subprocess.CompletedProcess([], 0, "", ""))
    path = tmp_path / receipt
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(record), encoding="utf-8")
    case = {"hook": hook, "runtime": "codex"}
    payload = {"session_id": "bench-hooks", "prompt": "fixture"}
    assert bench.invoke(ROOT, case, payload, tmp_path, 1)["error"] is None
    path.write_text("invalid json", encoding="utf-8")
    assert "capture did not persist" in bench.invoke(ROOT, case, payload, tmp_path, 1)["error"]
    path.write_text('{"session_id":"other","prompt":"other"}', encoding="utf-8")
    assert "capture did not persist" in bench.invoke(ROOT, case, payload, tmp_path, 1)["error"]


def test_baseline_requires_discarded_warmup(bench, monkeypatch, capsys):
    monkeypatch.setattr(bench, "measure_case", lambda root, case, runtime, *args: {
        **case, "runtime": runtime, "estado": "OK", "muestras_ms": [1] * 10,
        "mediana_ms": 1, "p95_ms": 1, "max_ms": 1})
    assert bench.main(["--runs", "10", "--warmup", "0", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["linea_base"] is False
    assert bench.main(["--runs", "10", "--warmup", "1", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["linea_base"] is True


def test_fail_fast_retains_first_failure_and_reports_incomplete_inventory(bench, monkeypatch, capsys):
    calls = []
    def fail(root, case, runtime, *args):
        calls.append((case, runtime))
        return {**case, "runtime": runtime, "estado": "FALLO", "fallo": "cleanup timeout",
                "muestras_ms": [20], "mediana_ms": None, "p95_ms": None, "max_ms": None}
    monkeypatch.setattr(bench, "measure_case", fail)
    assert bench.main(["--runs", "10", "--fail-fast", "--json"]) == 1
    report = json.loads(capsys.readouterr().out)
    assert len(calls) == 1
    assert report["estado"] == "FALLO" and report["linea_base"] is False
    assert report["casos_ejecutados"] == 1
    assert report["casos_previstos"] == len(bench.registered_hooks(ROOT)) * len(bench.RUNTIMES)
    assert report["hooks"][0]["muestras_ms"] == [20]
    assert report["hooks"][0]["fallo"] == "cleanup timeout"
    assert f"Casos ejecutados: 1/{report['casos_previstos']}" in bench.markdown(report)
