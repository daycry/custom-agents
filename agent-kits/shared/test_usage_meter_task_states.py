import importlib.util
import json

import pytest

from test_ledger_write_transitions import BASE, KIT, SLUG, cli, ledger, source, writer


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
