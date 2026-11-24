"""Synthetic native Codex and OpenCode usage windows for T-40 fix3 gap 4."""

import importlib.util
import json
from datetime import datetime
from pathlib import Path
import sqlite3

import pytest


START = "2026-11-24T12:00:00Z"
END = "2026-11-24T12:10:00Z"
STAMP = "2026-11-24T12:05:00Z"


@pytest.fixture
def meter(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    path = Path(__file__).with_name("usage-meter.py")
    spec = importlib.util.spec_from_file_location("runtime_meter", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    monkeypatch.delenv("CUSTOM_AGENTS_RUNTIME", raising=False)

    def run(command, runtime, *, at=START, source=None):
        monkeypatch.setattr(mod, "_now_iso", lambda: at)
        args = [command, "--artefacto", "fixture", "--state", str(tmp_path / "state.json")]
        if runtime:
            args.extend(["--runtime", runtime])
        if source:
            args.extend(["--transcript-dir", str(source)])
        if command == "close":
            args.extend(["--ratio", "1000"])
        assert mod.main(args) == 0
        return json.loads(capsys.readouterr().out)

    return run


def codex_usage(time, input_tokens, cached, written, output, total):
    return {"timestamp": time, "type": "event_msg", "payload": {
        "type": "token_count", "info": {"total_token_usage": {"total_tokens": total},
        "last_token_usage": {"input_tokens": input_tokens, "cached_input_tokens": cached,
                             "cache_write_input_tokens": written, "output_tokens": output,
                             "reasoning_output_tokens": 30, "total_tokens": input_tokens + output}}}}


def codex_log(root, date, name, cwd, events):
    path = root.joinpath(*date.split("-"), name + ".jsonl")
    path.parent.mkdir(parents=True, exist_ok=True)
    meta = {"type": "session_meta", "payload": {"cwd": str(cwd)}}
    path.write_text("".join(json.dumps(row) + "\n" for row in [meta, *events]), encoding="utf-8")


def test_fix3_gap4_codex_measures_window_and_project_without_duplicate_tokens(tmp_path, meter):
    sessions = tmp_path / "sessions"
    meter("start", "codex", source=sessions)
    event = codex_usage(STAMP, 1100, 300, 100, 90, 1500)
    codex_log(sessions, "2026-11-23", "resumed", tmp_path, [
        codex_usage("2026-11-24T11:59:59Z", 300, 0, 0, 10, 310), event, event,
        codex_usage("2026-11-24T12:10:01Z", 1000, 0, 0, 300, 2800)])
    codex_log(sessions, "2026-11-24", "subagent", tmp_path, [
        codex_usage(STAMP, 800, 200, 0, 20, 820)])
    codex_log(sessions, "2026-11-24", "other", tmp_path / "other", [event])
    receipt = meter("close", None, at=END)
    assert receipt["fuente"] == "medido"
    assert receipt["tokens_reales"] == {
        "entrada": 1300, "salida": 110, "cache_creacion": 100, "cache_lectura": 500, "respuestas": 2}
    assert receipt["horas_ia"] == 1.51
    assert receipt["transcripts_leidos"] == 2
    assert receipt["medicion_persistida"]


def test_fix3_gap4_codex_explicit_close_recovers_pre_fix_marker(tmp_path, meter, monkeypatch):
    codex_home = tmp_path / "codex"
    monkeypatch.setenv("CODEX_HOME", str(codex_home))
    meter("start", None, source=tmp_path / "claude")
    codex_log(codex_home / "sessions", "2026-11-24", "current", tmp_path, [
        codex_usage(STAMP, 300, 200, 0, 50, 350)])
    receipt = meter("close", "codex", at=END)
    assert receipt["fuente"] == "medido"
    assert receipt["tokens_reales"]["respuestas"] == 1


def opencode_fixture(path, project):
    with sqlite3.connect(path) as db:
        db.executescript("""
            CREATE TABLE session_v2 (id TEXT PRIMARY KEY, directory TEXT);
            CREATE TABLE session_message (
                id TEXT PRIMARY KEY, session_id TEXT, type TEXT, time_created INTEGER,
                time_updated INTEGER, data TEXT);
        """)
        db.executemany("INSERT INTO session_v2 VALUES (?, ?)", [
            ("target", str(project)), ("foreign", str(project / "other"))])
        tokens = {"input": 400, "output": 60, "reasoning": 40, "cache": {"read": 200, "write": 10}}
        for index, (session, kind, time, usage) in enumerate([
            ("target", "assistant", "2026-11-24T11:59:59Z", tokens),
            ("target", "assistant", STAMP, tokens),
            ("target", "assistant", END, tokens),
            ("target", "assistant", "2026-11-24T12:10:01Z", tokens),
            ("target", "assistant", None, tokens),
            ("target", "assistant", STAMP, None),
            ("foreign", "assistant", STAMP, tokens),
            ("target", "user", STAMP, tokens),
        ]):
            completed = int(datetime.fromisoformat(time.replace("Z", "+00:00")).timestamp() * 1000) if time else None
            data = {"time": {"completed": completed}, "tokens": usage, "text": "synthetic text"}
            db.execute("INSERT INTO session_message VALUES (?, ?, ?, ?, ?, ?)",
                       (str(index), session, kind, 1, 2, json.dumps(data)))


def test_fix3_gap4_opencode_measures_completed_messages_for_project_and_window(tmp_path, meter):
    store = tmp_path / "opencode"
    meter("start", "opencode", source=store)
    store.mkdir()
    opencode_fixture(store / "opencode.db", tmp_path)
    receipt = meter("close", "opencode", at=END)
    assert receipt["fuente"] == "medido"
    assert receipt["tokens_reales"] == {
        "entrada": 800, "salida": 200, "cache_creacion": 20, "cache_lectura": 400, "respuestas": 2}
    assert receipt["horas_ia"] == 1.02
    assert "synthetic text" not in json.dumps(receipt)


@pytest.mark.parametrize("runtime,expected", [
    ("codex", "estimado"), ("opencode", "no-disponible"),
])
def test_fix3_gap4_missing_native_source_never_reports_measured_zero(tmp_path, meter, runtime, expected):
    missing = tmp_path / "missing"
    meter("start", runtime, source=missing)
    receipt = meter("close", runtime, at=END)
    assert receipt["fuente"] == expected
    assert receipt["tokens_reales"] is None and receipt["horas_ia"] is None
    assert any(runtime.lower() in warning.lower() for warning in receipt["avisos"])
