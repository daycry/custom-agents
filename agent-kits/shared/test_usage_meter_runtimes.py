"""Synthetic native Codex and OpenCode usage windows for T-40 fix3 gap 4."""

import importlib.util
import json
from datetime import datetime, timedelta
import os
from pathlib import Path
import sqlite3
import subprocess

import pytest


START = "2026-11-24T12:00:00Z"
END = "2026-11-24T12:10:00Z"
STAMP = "2026-11-24T12:05:00Z"


@pytest.fixture
def private_cache(tmp_path_factory, monkeypatch):
    home = tmp_path_factory.mktemp("meter-home")
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))
    return home


@pytest.fixture
def meter(tmp_path, monkeypatch, capsys, private_cache):
    monkeypatch.chdir(tmp_path)
    path = Path(__file__).with_name("usage-meter.py")
    spec = importlib.util.spec_from_file_location("runtime_meter", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    monkeypatch.delenv("CUSTOM_AGENTS_RUNTIME", raising=False)
    monkeypatch.delenv("CODEX_THREAD_ID", raising=False)

    def run(command, runtime, *, at=START, source=None, artifact="fixture"):
        monkeypatch.setattr(mod, "_now_iso", lambda **_: at)
        args = [command, "--artefacto", artifact, "--state", str(tmp_path / "state.json")]
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


def codex_log(root, date, name, cwd, events, *, mtime="2026-11-20T10:00:00Z"):
    path = root.joinpath(*date.split("-"), name + ".jsonl")
    path.parent.mkdir(parents=True, exist_ok=True)
    meta = {"type": "session_meta", "payload": {"cwd": str(cwd)}}
    path.write_text("".join(json.dumps(row) + "\n" for row in [meta, *events]), encoding="utf-8")
    timestamp = datetime.fromisoformat(mtime).timestamp()
    os.utime(path, (timestamp, timestamp))
    return path


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
    repeated = meter("close", None, at=END)
    assert repeated["tokens_reales"] == receipt["tokens_reales"]
    assert repeated["fuente_id"] == receipt["fuente_id"]


@pytest.mark.parametrize("thread_env", [False, True])
def test_fix5_gap1_resumed_sessions(tmp_path, meter, monkeypatch, thread_env):
    sessions = tmp_path / "sessions"
    thread = "00000000-0000-0000-0000-000000000001"
    if thread_env:
        monkeypatch.setenv("CODEX_THREAD_ID", thread)
    day = datetime.fromisoformat(START).date()
    before = codex_usage("2026-11-20T09:00:00Z", 50, 0, 0, 10, 60)
    event = codex_usage(STAMP, 300, 200, 0, 50, 410)
    for age in range(4, 65):
        codex_log(sessions, str(day - timedelta(days=age)), "history", tmp_path, [before])
    old = codex_log(sessions, str(day - timedelta(days=3)), f"rollout-{thread}", tmp_path, [before])
    original = Path.open
    opened = []

    def counted(path, *args, **kwargs):
        if path.suffix == ".jsonl" and "r" in (args[0] if args else kwargs.get("mode", "r")):
            opened.append(path)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", counted)
    meter("start", "codex", source=sessions)
    old_stat = old.stat()
    with old.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(event) + "\n")
    os.utime(old, ns=(old_stat.st_atime_ns, old_stat.st_mtime_ns))
    current = codex_log(sessions, str(day), "sibling", tmp_path, [event])
    first = meter("close", None, at=END)
    assert first["tokens_reales"] == dict(entrada=200, salida=100, cache_creacion=0,
                                          cache_lectura=400, respuestas=2)
    assert first["tokens_cobertura"] == "completa"
    again = meter("close", None, at=END)
    assert again["tokens_reales"] == first["tokens_reales"]
    assert opened.count(old) == opened.count(current) == 1 and len(opened) == 2
    # Appending the previous cumulative sample then one new sample crosses the cursor.
    with old.open("a", encoding="utf-8") as stream:
        for record in (event, codex_usage(END, 80, 0, 0, 5, 495)):
            stream.write(json.dumps(record) + "\n")
    extended = meter("close", None, at=END)
    assert extended["tokens_reales"] == dict(entrada=280, salida=105, cache_creacion=0,
                                             cache_lectura=400, respuestas=3)
    assert opened.count(old) == 2 and opened.count(current) == 1


def test_fix6_gap3_index_is_private_and_legacy_index_is_ignored(tmp_path, meter, private_cache):
    meter("start", "codex", source=tmp_path / "sessions")
    assert not list(tmp_path.rglob("*.codex-index.json"))
    assert len(list(private_cache.rglob("*.codex-index.json"))) == 1
    repo = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        ["git", "check-ignore", "nested/.claude/usage-state.json.legacy.codex-index.json"],
        cwd=repo, capture_output=True, check=False,
    )
    assert result.returncode == 0, result.stderr


def test_fix6_gap3_prunes_expired_closed_index_and_preserves_repeat(tmp_path, meter, private_cache):
    sessions = tmp_path / "sessions"
    cache = private_cache
    old = codex_log(sessions, "2026-11-20", "resumed", tmp_path,
                    [codex_usage("2026-11-20T09:00:00Z", 1, 0, 0, 1, 2)])
    meter("start", "codex", source=sessions)
    stat = old.stat()
    with old.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(codex_usage(STAMP, 100, 0, 0, 10, 112)) + "\n")
    os.utime(old, ns=(stat.st_atime_ns, stat.st_mtime_ns))
    first = meter("close", None, at=END)
    assert first["tokens_reales"]["respuestas"] == 1
    meter("start", "codex", source=sessions, artifact="open", at="2026-12-01T12:00:00Z")
    opened, = (path for path in cache.rglob("*.codex-index.json") if ".closed." not in path.name)
    recent = datetime.fromisoformat("2026-12-01T12:00:00Z").timestamp()
    os.utime(opened, (recent, recent))
    meter("start", "codex", source=sessions, artifact="different", at="2026-12-25T12:00:00Z")
    assert len(list(cache.rglob("*.closed.codex-index.json"))) == 0
    assert len(list(cache.rglob("*.codex-index.json"))) == 2  # still open + newest
    repeat = meter("close", None, at=END)
    assert repeat["tokens_reales"] == first["tokens_reales"]
    assert repeat["ventana_id"] == first["ventana_id"]


@pytest.mark.parametrize("error", [RuntimeError, OSError, KeyError])
@pytest.mark.parametrize("with_store", [True, False])
def test_fix7_gap2_no_home_keeps_start_and_close_markers(tmp_path, meter, monkeypatch, error, with_store):
    def no_home(cls):
        raise error("home unavailable")

    monkeypatch.setattr(Path, "home", classmethod(no_home))
    monkeypatch.delenv("CODEX_HOME", raising=False)
    sessions = tmp_path / "sessions" if with_store else None
    if sessions:
        codex_log(sessions, "2026-11-24", "current", tmp_path, [codex_usage(STAMP, 10, 0, 0, 5, 15)])
    started = meter("start", "codex", source=sessions)
    assert started["marker_saved"]
    assert any("caché privada" in warning for warning in started["avisos"])
    receipt = meter("close", "codex", at=END)
    assert receipt["tokens_cobertura"] == "parcial"
    assert any("caché privada" in warning for warning in receipt["avisos"])
    if with_store:
        assert receipt["tokens_reales"]["respuestas"] == 1
    marker = json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))["fixture"]
    assert marker["ultimoCierre"] == END


def test_fix7_gap4_prune_race_does_not_discard_new_index(tmp_path, meter, private_cache, monkeypatch):
    sessions = tmp_path / "sessions"
    meter("start", "codex", source=sessions)
    meter("close", "codex", at=END)
    stale, = private_cache.rglob("*.closed.codex-index.json")
    original = Path.lstat

    def concurrent_unlink(path):
        if path == stale:
            path.unlink()
        return original(path)

    monkeypatch.setattr(Path, "lstat", concurrent_unlink)
    started = meter("start", "codex", source=sessions, at="2026-12-26T12:00:00Z")
    marker = json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))["fixture"]
    assert started["marker_saved"]
    assert [path.name for path in private_cache.rglob("*.codex-index.json")] == [
        f'{marker["ventana_id"]}.codex-index.json']


def test_fix7_gap4_prunes_abandoned_open_index(tmp_path, meter, private_cache):
    sessions = tmp_path / "sessions"
    meter("start", "codex", source=sessions, artifact="abandoned")
    stale, = private_cache.rglob("*.codex-index.json")
    old = datetime.fromisoformat(START).timestamp()
    os.utime(stale, (old, old))
    meter("start", "codex", source=sessions, artifact="recent", at="2026-12-24T12:00:00Z")
    recent, = set(private_cache.rglob("*.codex-index.json")) - {stale}
    boundary = datetime.fromisoformat("2026-11-25T12:00:00Z").timestamp()
    os.utime(recent, (boundary, boundary))
    meter("start", "codex", source=sessions, at="2026-12-25T12:00:00Z")
    assert not stale.exists()
    assert recent.is_file()


def test_fix4_gap5_codex_limits_days_and_skips_stale_files(tmp_path, meter, monkeypatch):
    sessions = tmp_path / "sessions"
    day = datetime.fromisoformat(START).date()
    stale = codex_usage("2026-11-20T09:00:00Z", 30, 0, 0, 5, 35)
    for age in range(3, 65):
        codex_log(sessions, str(day - timedelta(days=age)), "history", tmp_path, [stale])
    meter("start", "codex", source=sessions)
    # A new path outside the measurement dates can appear after start, even with old mtime.
    active = codex_log(sessions, str(day - timedelta(days=7)), "resumed", tmp_path,
                       [codex_usage(STAMP, 100, 0, 0, 10, 110)])
    opened = []
    original = Path.open

    def counted(path, *args, **kwargs):
        if path.suffix == ".jsonl":
            opened.append(path)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", counted)
    receipt = meter("close", None, at=END)
    assert opened == [active]
    assert receipt["tokens_reales"]["respuestas"] == 1


def test_fix5_gap1_cold_history_warns_and_includes_thread(tmp_path, meter, monkeypatch):
    sessions = tmp_path / "sessions"
    thread = "00000000-0000-0000-0000-000000000001"
    monkeypatch.setenv("CODEX_THREAD_ID", thread)
    event = codex_usage(STAMP, 300, 200, 0, 50, 350)
    for day, name in [("2026-11-20", "unindexed"), ("2026-11-21", f"rollout-{thread}"),
                      ("2026-11-24", "today")]:
        codex_log(sessions, day, name, tmp_path, [event], mtime=STAMP if name == "today" else "2026-11-20T09:00:00Z")
    # Existing v2 marker predating the Codex inventory.
    marker = {"version": 2, "inicio": START, "runtime": "codex", "offsets": {},
              "transcriptDir": str(sessions)}
    (tmp_path / "state.json").write_text(json.dumps({"fixture": marker}), encoding="utf-8")
    receipt = meter("close", None, at=END)
    assert receipt["tokens_reales"]["respuestas"] >= 2
    if receipt["tokens_reales"]["respuestas"] < 3:
        assert receipt["tokens_cobertura"] == "parcial"
        assert any("parcial" in warning for warning in receipt["avisos"])


def test_fix4_gap5_explicit_claude_runtime_overrides_global_codex(tmp_path, meter, monkeypatch):
    monkeypatch.setenv("CUSTOM_AGENTS_RUNTIME", "codex")
    source = tmp_path / "claude"
    source.mkdir()
    meter("start", "claude", source=source)
    log = source / "session.jsonl"
    log.write_text(json.dumps({"timestamp": STAMP, "type": "assistant", "message": {
        "id": "fixture", "usage": {"input_tokens": 12, "output_tokens": 8},
    }}) + "\n", encoding="utf-8")
    receipt = meter("close", "claude", at=END)
    assert receipt["fuente"] == "medido"
    assert receipt["tokens_reales"]["entrada"] == 12


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
