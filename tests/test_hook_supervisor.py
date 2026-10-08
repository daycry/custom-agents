"""Containment decisions without operating on any real process tree."""
import importlib.util
import os
from pathlib import Path
import signal
import subprocess
from types import SimpleNamespace
import ctypes
from ctypes import wintypes

import pytest


spec = importlib.util.spec_from_file_location("hook_supervisor", Path(__file__).parents[1] / "hooks" / "runtime-supervisor.py")
supervisor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(supervisor)


def test_group_cleanup_keeps_owner_running_and_kills_children(monkeypatch):
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
    monkeypatch.setattr(supervisor.subprocess, "run", lambda *a, **kw: subprocess.CompletedProcess(a, 0, next(accounting), ""))
    supervisor.close_group(owner)
    assert ("process", child, signal.SIGKILL) in calls
    assert ("process", child, signal.SIGSTOP) in calls
    assert not any(pid == owner and sig in (signal.SIGSTOP, signal.SIGKILL) for _, pid, sig in calls)


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
    monkeypatch.setattr(supervisor.runpy, "run_path", lambda *a, **kw: pytest.fail("uncontained business ran"))
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
