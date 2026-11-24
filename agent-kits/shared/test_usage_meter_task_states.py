import importlib.util
import json
import subprocess
import sys

import pytest

from test_ledger_write_transitions import BASE, KIT, SLUG, cli, ledger, load_script, source, writer


def meter(ledger, operation, task, *args):
    return cli(ledger, "usage-meter", operation, "--artefacto", f"{SLUG}/{task}",
               "--state", "usage.json", *args)


@pytest.mark.parametrize("runtime,reviewer", [("claude", "codex"), ("codex", "opencode"),
                                             ("opencode", "claude")])
def test_estado_tarea_handoffs_and_events(ledger, runtime, reviewer):
    args = ("--runtime", runtime)
    assert meter(ledger, "start", "T-01", *args).returncode == 0
    assert "- **Estado**: en-progreso" in source(ledger)
    assert meter(ledger, "close", "T-01", *args).returncode == 0
    assert "- **Estado**: en-revision" in source(ledger)
    review = ("--tasks", "T-01", "--attempt", "1", "--runtime", reviewer)
    assert writer(ledger, "review", *review, "--summary", "Fixture").returncode == 0
    assert writer(ledger, "verdict", *review, "--result", "gaps", "--gap-tasks", "T-01").returncode == 0
    assert meter(ledger, "start", "T-01-fix2", *args).returncode == 0
    assert "- **Estado**: en-progreso" in source(ledger)
    assert meter(ledger, "close", "T-01-fix2", *args).returncode == 0
    assert "- **Estado**: en-revision" in source(ledger)

    spec = importlib.util.spec_from_file_location("activity", KIT / "agent-activity-store.py")
    activity = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(activity)
    events = activity.task_transitions(ledger.parents[3])
    assert [(e["from"], e["to"], e["runtime"], e["role"], e["source"]) for e in events] == [
        ("borrador", "en-progreso", runtime, "implementer", "usage-meter"),
        ("en-progreso", "en-revision", runtime, "implementer", "usage-meter"),
        ("en-revision", "en-progreso", reviewer, "reviewer", "ledger-write"),
        ("en-progreso", "en-revision", runtime, "implementer", "usage-meter"),
    ]
    assert all(e["task"] == "T-01" and e["schema_version"] == 1 for e in events)
    assert str(ledger.parents[3]) not in json.dumps(events)


@pytest.mark.parametrize("state", ["completado", "cancelado"])
def test_estado_tarea_preserves_terminal_states(ledger, state):
    result = writer(ledger, "state", "--task", "T-01", "--state", state)
    assert result.returncode == 0
    before = ledger.read_bytes()
    assert meter(ledger, "start", "T-01-fix2").returncode == 0
    assert meter(ledger, "close", "T-01-fix2").returncode == 0
    assert ledger.read_bytes() == before


@pytest.mark.parametrize("data", [b"\xff", b"a" * (256 * 1024 + 1)], ids=["invalid-utf8", "oversize"])
def test_estado_tarea_meter_degrades_without_writing_ledger(ledger, data):
    ledger.write_bytes(data)
    started = meter(ledger, "start", "T-01")
    assert started.returncode == 0
    assert any("ledger" in message for message in json.loads(started.stdout)["avisos"])
    assert ledger.read_bytes() == data


def test_estado_tarea_busy_writer_is_nonblocking_and_next_handoff_recovers(ledger):
    import time
    spec = importlib.util.spec_from_file_location("writer", KIT / "ledger-write.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    lock = ledger.parent / ".ledger-write"
    lock.mkdir()
    with module.IO.locked(lock, time.monotonic() + 8, True):
        result = meter(ledger, "start", "T-01")
        assert result.returncode == 0, result.stderr
        assert any("state_busy" in message for message in json.loads(result.stdout)["avisos"])
        assert source(ledger) == BASE
    assert meter(ledger, "close", "T-01").returncode == 0
    assert "- **Estado**: en-revision" in source(ledger)


def test_fix1_gap3_parallel_close_and_start_preserve_both_markers(ledger):
    assert meter(ledger, "start", "T-01").returncode == 0
    # An isolated process stops at the actual handoff boundary. A second process
    # writes a different marker, then releases it. No timing assumptions.
    wrapper = """
import importlib.util
import subprocess
import sys
spec = importlib.util.spec_from_file_location('meter', sys.argv[1])
meter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(meter)
handoff = meter._task_handoff
def interleave(args, target, warnings):
    result = subprocess.run([sys.executable, sys.argv[1], 'start', '--artefacto', sys.argv[3],
                             '--state', 'usage.json'], capture_output=True, timeout=10, check=True)
    assert b'\"ok\": true' in result.stdout
    return handoff(args, target, warnings)
meter._task_handoff = interleave
sys.exit(meter.main(['close', '--artefacto', sys.argv[2], '--state', 'usage.json']))
"""
    first, second = f"{SLUG}/T-01", f"{SLUG}/T-02"
    result = subprocess.run([sys.executable, "-c", wrapper, str(KIT / "usage-meter.py"), first, second],
                            cwd=ledger.parents[3], capture_output=True, encoding="utf-8", timeout=20)
    assert result.returncode == 0, result.stderr
    markers = json.loads((ledger.parents[3] / "usage.json").read_text(encoding="utf-8"))
    assert second in markers, "parallel start marker was lost"
    assert markers[first]["ultimoCierre"] and markers[first]["ledgerClose"] is True


def test_fix2_gap7_start_reports_unsaved_marker_when_state_locked(ledger):
    module = load_script(KIT / "usage-meter.py")
    path = ledger.parents[3] / "usage.json"
    with module._locked_state(path, []):
        result = meter(ledger, "start", "T-01")
        assert result.returncode == 0, result.stderr
        started = json.loads(result.stdout)
        assert started.get("marker_saved") is False
        assert any("marcador" in message and "state_busy" in message for message in started["avisos"])
        assert not path.exists()
        assert "- **Estado**: en-progreso" in source(ledger)
    result = meter(ledger, "start", "T-01")
    assert json.loads(result.stdout)["marker_saved"] is True
    assert f"{SLUG}/T-01" in json.loads(path.read_text(encoding="utf-8"))


def test_fix2_gap3_meter_handoff_avoids_second_interpreter(ledger, monkeypatch, capsys):
    module = load_script(KIT / "usage-meter.py")
    monkeypatch.chdir(ledger.parents[3])

    def unexpected(*args, **kwargs):
        pytest.fail("meter handoff started a second interpreter")

    monkeypatch.setattr(subprocess, "run", unexpected)
    args = ["--artefacto", f"{SLUG}/T-01", "--runtime", "codex", "--state", "usage.json"]
    for command, state in (("start", "en-progreso"), ("close", "en-revision")):
        assert module.main([command, *args]) == 0
        report = json.loads(capsys.readouterr().out)
        assert not any("transición pendiente" in warning for warning in report.get("avisos", []))
        assert f"- **Estado**: {state}" in source(ledger)
