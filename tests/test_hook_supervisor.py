"""Containment decisions without operating on any real process tree."""
import importlib.util
import os
from pathlib import Path
import signal
import runpy
import subprocess
from types import SimpleNamespace
import ctypes
from ctypes import wintypes

import pytest


spec = importlib.util.spec_from_file_location("hook_supervisor", Path(__file__).parents[1] / "hooks" / "runtime-supervisor.py")
supervisor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(supervisor)


class _Reloj:
    """Reloj controlado del supervisor: el plazo de 0,25 s de `close_group` no depende de la velocidad del disco."""

    def __init__(self, paso=0.0):
        self.ahora, self.paso = 0.0, paso

    def monotonic(self):
        self.ahora += self.paso
        return self.ahora

    def sleep(self, segundos):
        self.ahora += segundos


@pytest.fixture
def reloj(monkeypatch):
    """Reloj congelado (cada llamada avanza 0 s): el plazo nunca vence salvo que el test lo diga."""
    falso = _Reloj()
    monkeypatch.setattr(supervisor, "time", falso)
    return falso


def test_group_cleanup_keeps_owner_running_and_kills_children(monkeypatch, reloj):
    owner, child = 41001, 41002
    calls = []
    accounting = iter([f"{owner} {owner} S\n{child} {owner} S\n", f"{owner} {owner} S\n"])
    monkeypatch.setattr(supervisor.os, "getppid", lambda: owner)
    monkeypatch.setattr(signal, "SIGSTOP", 19, raising=False)
    monkeypatch.setattr(signal, "SIGCONT", 18, raising=False)
    monkeypatch.setattr(signal, "SIGKILL", 9, raising=False)
    monkeypatch.setattr(supervisor.os, "getpgid", lambda pid: owner, raising=False)
    monkeypatch.setattr(supervisor.os, "getpgrp", lambda: 42000, raising=False)
    monkeypatch.setattr(supervisor.os.path, "isfile", lambda path: True)
    monkeypatch.setattr(supervisor.os, "killpg", lambda pid, sig: calls.append(("group", pid, sig)), raising=False)
    monkeypatch.setattr(supervisor.os, "kill", lambda pid, sig: calls.append(("process", pid, sig)))
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: subprocess.CompletedProcess(a, 0, next(accounting), ""))
    supervisor.close_group(owner)
    assert ("process", child, signal.SIGKILL) in calls
    assert ("process", child, signal.SIGSTOP) in calls
    assert not any(pid == owner and sig in (signal.SIGSTOP, signal.SIGKILL) for _, pid, sig in calls)


def test_group_cleanup_without_ps_reads_proc(monkeypatch, tmp_path, reloj):
    # Minimal images (python:*-slim) ship no procps: accounting falls back to /proc/<pid>/stat.
    owner, child = 41001, 41002
    for pid, group, state, name in ((owner, owner, "S", "node"), (child, owner, "S", "py (x) y"),
                                    (41003, 42000, "S", "other"), (41004, owner, "Z", "dead")):
        (tmp_path / str(pid)).mkdir()
        (tmp_path / str(pid) / "stat").write_text(f"{pid} ({name}) {state} 1 {group} {group} 0 -1\n")
    (tmp_path / "self").mkdir()
    calls = []
    monkeypatch.setattr(supervisor, "PROC_ROOT", str(tmp_path))
    monkeypatch.setattr(supervisor.os, "getppid", lambda: owner)
    monkeypatch.setattr(signal, "SIGSTOP", 19, raising=False)
    monkeypatch.setattr(signal, "SIGKILL", 9, raising=False)
    monkeypatch.setattr(supervisor.os, "getpgid", lambda pid: owner, raising=False)
    monkeypatch.setattr(supervisor.os, "getpgrp", lambda: 42000, raising=False)
    monkeypatch.setattr(supervisor.os.path, "isfile", lambda path: False)
    def kill(pid, sig):
        calls.append((pid, sig))
        if sig == signal.SIGKILL:
            (tmp_path / str(pid) / "stat").unlink()
    monkeypatch.setattr(supervisor.os, "kill", kill)
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: pytest.fail("no ps is installed"))
    supervisor.close_group(owner)
    assert (child, signal.SIGKILL) in calls and (child, signal.SIGSTOP) in calls
    assert all(pid == child for pid, _ in calls), calls


def test_group_cleanup_without_ps_or_proc_stays_unavailable(monkeypatch, tmp_path):
    monkeypatch.setattr(supervisor, "PROC_ROOT", str(tmp_path / "missing"))
    monkeypatch.setattr(supervisor.os, "getppid", lambda: 41001)
    monkeypatch.setattr(supervisor.os, "getpgid", lambda pid: 41001, raising=False)
    monkeypatch.setattr(supervisor.os, "getpgrp", lambda: 42000, raising=False)
    monkeypatch.setattr(supervisor.os.path, "isfile", lambda path: False)
    with pytest.raises(OSError, match="accounting unavailable"):
        supervisor.close_group(41001)


def test_group_cleanup_rejects_foreign_owner_before_signals(monkeypatch):
    monkeypatch.setattr(supervisor.os, "getppid", lambda: 41001)
    def forbidden(*args):
        pytest.fail("foreign groups must never receive a signal")
    monkeypatch.setattr(supervisor.os, "killpg", forbidden, raising=False)
    monkeypatch.setattr(supervisor.os, "kill", forbidden)
    with pytest.raises(OSError, match="not owned"):
        supervisor.close_group(41002)


def test_failed_containment_never_runs_business_or_exposes_arguments(monkeypatch, capsys):
    def unavailable(owner):
        raise OSError("PRIVATE_BACKEND_DETAIL")
    monkeypatch.setattr(supervisor, "attach", unavailable)
    monkeypatch.setattr(runpy, "run_path", lambda *a, **kw: pytest.fail("uncontained business ran"))
    assert supervisor.main(["run", "41001", "python", "python", "PRIVATE_CONSUMER_SCRIPT"]) == 1
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == "custom-agents hooks: process supervision unavailable; hook skipped\n"


def test_assignment_failure_releases_local_handles_and_skips_business(monkeypatch):
    # The real structure's basic member is a structure with a flags field.
    class Basic(ctypes.Structure):
        _fields_ = [("flags", ctypes.c_uint32)]
    class Limits(ctypes.Structure):
        _fields_ = [("basic", Basic)]
    closed = []
    def duplicate(source, job, target, remote, access, inherit, flags):
        assert inherit is False and flags == 2
        remote._obj.value = 900
        return 1
    api = SimpleNamespace(OpenProcess=lambda *a: 100, CreateJobObjectW=lambda *a: 200,
                          SetInformationJobObject=lambda *a: 1, DuplicateHandle=duplicate,
                          AssignProcessToJobObject=lambda *a: 0, GetCurrentProcess=lambda: -1,
                          CloseHandle=closed.append)
    monkeypatch.setattr(supervisor, "windows_api", lambda: (ctypes, wintypes, api, Limits, None, None))
    monkeypatch.setattr(supervisor, "validate_owner", lambda *a: None)
    monkeypatch.setattr(supervisor, "checked", lambda value, _: value if value else (_ for _ in ()).throw(OSError("assignment failed")))
    with pytest.raises(OSError, match="assignment failed"):
        supervisor.attach(41001)
    assert closed == [200, 100]


def test_owner_ancestry_accepts_redirector_and_rejects_unrelated_process(monkeypatch):
    class Entry(ctypes.Structure):
        _fields_ = [("size", ctypes.c_uint32), ("pid", ctypes.c_uint32), ("parent", ctypes.c_uint32)]
    rows = []
    closed = []
    def next_entry(snapshot, pointer):
        if not rows:
            return False
        pointer._obj.pid, pointer._obj.parent = rows.pop(0)
        return True
    api = SimpleNamespace(CreateToolhelp32Snapshot=lambda *a: 100,
                          Process32FirstW=next_entry, Process32NextW=next_entry, CloseHandle=closed.append)
    monkeypatch.setattr(supervisor.os, "getppid", lambda: 41002)
    monkeypatch.setattr(supervisor.os, "getpid", lambda: 41003)
    rows[:] = [(41003, 41002), (41002, 41001)]
    supervisor.validate_owner(41001, ctypes, api, Entry)
    rows[:] = [(41003, 41002), (41002, 41004)]
    with pytest.raises(OSError, match="not its ancestor"):
        supervisor.validate_owner(41001, ctypes, api, Entry)
    assert closed == [100, 100]


@pytest.mark.parametrize("args", [[], ["run"], ["run", "bad", "python", "python", "secret.py"],
                                  ["run", "41001", "shell", "python", "secret.py"]])
def test_malformed_bootstrap_is_informational_and_never_attaches(args, monkeypatch, capsys):
    monkeypatch.setattr(supervisor, "attach", lambda *a: pytest.fail("malformed bootstrap attached"))
    assert supervisor.main(args) == 1
    assert capsys.readouterr().err == "custom-agents hooks: process supervision unavailable; hook skipped\n"


def _unaccounted_group(monkeypatch, tmp_path, rows):
    for pid, group in rows:
        (tmp_path / str(pid)).mkdir()
        (tmp_path / str(pid) / "stat").write_text(f"{pid} (x) S 1 {group} {group} 0 -1\n")
    monkeypatch.setattr(supervisor, "PROC_ROOT", str(tmp_path))
    monkeypatch.setattr(supervisor.os, "getppid", lambda: 41001)
    monkeypatch.setattr(supervisor.os, "getpgid", lambda pid: 41001, raising=False)
    monkeypatch.setattr(supervisor.os, "getpgrp", lambda: 42000, raising=False)
    monkeypatch.setattr(supervisor.os.path, "isfile", lambda path: False)
    monkeypatch.setattr(supervisor.os, "kill", lambda *a: pytest.fail("no signal without accounting"), raising=False)


def test_group_cleanup_fails_closed_when_proc_is_empty(monkeypatch, tmp_path):
    # Review 2-8: /proc mounted but empty must not read as «group finished».
    _unaccounted_group(monkeypatch, tmp_path, [])
    with pytest.raises(OSError, match="accounting unavailable"):
        supervisor.close_group(41001)


def test_group_cleanup_fails_closed_when_accounting_misses_the_owner(monkeypatch, tmp_path):
    _unaccounted_group(monkeypatch, tmp_path, [(41003, 42000)])
    with pytest.raises(OSError, match="accounting unavailable"):
        supervisor.close_group(41001)


def test_group_cleanup_reports_unconfirmed_when_the_deadline_passes(monkeypatch, tmp_path):
    # Con un reloj lento (0,3 s por llamada) el plazo de 0,25 s vence tras el primer barrido: no se confirma.
    owner, child = 41001, 41002
    for pid in (owner, child):
        (tmp_path / str(pid)).mkdir()
        (tmp_path / str(pid) / "stat").write_text(f"{pid} (x) S 1 {owner} {owner} 0 -1\n")
    monkeypatch.setattr(supervisor, "time", _Reloj(paso=0.3))
    monkeypatch.setattr(signal, "SIGSTOP", 19, raising=False)
    monkeypatch.setattr(signal, "SIGKILL", 9, raising=False)
    monkeypatch.setattr(supervisor, "PROC_ROOT", str(tmp_path))
    monkeypatch.setattr(supervisor.os, "getppid", lambda: owner)
    monkeypatch.setattr(supervisor.os, "getpgid", lambda pid: owner, raising=False)
    monkeypatch.setattr(supervisor.os, "getpgrp", lambda: 42000, raising=False)
    monkeypatch.setattr(supervisor.os.path, "isfile", lambda path: False)
    monkeypatch.setattr(supervisor.os, "kill", lambda pid, sig: None)
    with pytest.raises(OSError, match="could not be confirmed"):
        supervisor.close_group(owner)


def test_windows_close_does_not_initialize_business_execution_modules(monkeypatch):
    # Exercise the real close path with a fake Windows API; no real process is signalled.
    import builtins
    observed, calls, closed = [], [], []
    class Accounting(ctypes.Structure):
        _fields_ = [("active", ctypes.c_uint32)]
    def duplicate(owner, remote, process, local, access, inherit, flags):
        assert owner == 100 and remote.value == 900 and flags == 3 and inherit is False
        local._obj.value = 200
        return 1
    def terminate(job, code):
        calls.append(("terminate", job.value, code))
        return 1
    def query(job, kind, accounting, size, needed):
        calls.append(("confirm", job.value, kind))
        accounting._obj.active = 0
        return 1
    api = SimpleNamespace(OpenProcess=lambda *a: 100, DuplicateHandle=duplicate,
                          GetCurrentProcess=lambda: -1, TerminateJobObject=terminate,
                          QueryInformationJobObject=query, CloseHandle=lambda handle: closed.append(getattr(handle, "value", handle)))
    original_import = builtins.__import__
    def record_import(name, *args, **kwargs):
        if name in ("json", "runpy", "subprocess"):
            observed.append(name)
        return original_import(name, *args, **kwargs)
    path = Path(__file__).parents[1] / "hooks" / "runtime-supervisor.py"
    namespace = {"__name__": "cleanup_import_probe", "__file__": str(path)}
    with monkeypatch.context() as patch:
        patch.setattr(builtins, "__import__", record_import)
        exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), namespace)
        namespace["windows_api"] = lambda: (ctypes, wintypes, api, None, Accounting, None)
        namespace["validate_owner"] = lambda *args: None
        assert namespace["main"](["close", "41001", "900"]) == 0
    assert calls == [("terminate", 200, 0), ("confirm", 200, 1)]
    assert closed == [200, 100]
    assert observed == [], f"cleanup initialized business modules: {observed}"
