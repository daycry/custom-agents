"""Synthetic restore publication: bounded Windows sharing contention only."""
import ctypes
import importlib.util
import os
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "restore_publication_protocol", Path(__file__).with_name("memory_local_recovery_support") / "protocol.py")
protocol = importlib.util.module_from_spec(spec)
spec.loader.exec_module(protocol)


@pytest.fixture
def snapshot(tmp_path):
    root = tmp_path / "source"
    file = root / "docs/knowledge/approved/adr/synthetic.md"
    file.parent.mkdir(parents=True)
    file.write_bytes(b"Synthetic canonical bytes\n")
    backup = tmp_path / "backup"
    files = protocol.backup_drill(root, backup, own=tmp_path)
    return backup, tmp_path / "restored", files


def contention(code):
    error = PermissionError("synthetic Windows sharing contention")
    error.winerror = code
    return error


@pytest.mark.parametrize("code", [5, 32])
def test_restore_retries_only_transient_windows_publication(snapshot, tmp_path, monkeypatch, code):
    backup, target, files = snapshot
    rename = protocol.os.rename
    attempts, waits = [], []
    def interrupted(stage, destination):
        attempts.append((stage, destination))
        if len(attempts) <= 3:
            raise contention(code)
        return rename(stage, destination)
    monkeypatch.setattr(protocol.os, "rename", interrupted)
    monkeypatch.setattr(protocol.time, "sleep", waits.append)
    assert protocol.restore_drill(backup, target, own=tmp_path) == files
    assert protocol.inventory(target) == files
    assert len(attempts) == 4 and waits == [0.02, 0.04, 0.08]


@pytest.mark.parametrize("code,expected_attempts", [(5, 4), (32, 4), (None, 1), (87, 1)])
def test_restore_failure_retains_verified_staging(snapshot, tmp_path, monkeypatch, code, expected_attempts):
    backup, target, files = snapshot
    attempts, waits = [], []
    def denied(*args):
        attempts.append(args)
        error = PermissionError("persistent publication failure")
        if code is not None:
            error.winerror = code
        raise error
    monkeypatch.setattr(protocol.os, "rename", denied)
    monkeypatch.setattr(protocol.time, "sleep", waits.append)
    with pytest.raises(PermissionError):
        protocol.restore_drill(backup, target, own=tmp_path)
    assert not target.exists()
    assert protocol.inventory(target.with_name(target.name + ".restore-staging")) == files
    assert len(attempts) == expected_attempts
    assert len(waits) == expected_attempts - 1


def test_restore_retry_does_not_overwrite_new_destination(snapshot, tmp_path, monkeypatch):
    backup, target, files = snapshot
    attempts = []
    def denied(*args):
        attempts.append(args)
        raise contention(32)
    def appeared(_):
        target.mkdir()
        (target / "sentinel").write_bytes(b"preserve")
    monkeypatch.setattr(protocol.os, "rename", denied)
    monkeypatch.setattr(protocol.time, "sleep", appeared)
    with pytest.raises(protocol.RestoreRejected, match="destination appeared"):
        protocol.restore_drill(backup, target, own=tmp_path)
    assert len(attempts) == 1
    assert (target / "sentinel").read_bytes() == b"preserve"
    assert protocol.inventory(target.with_name(target.name + ".restore-staging")) == files


@pytest.mark.skipif(os.name != "nt", reason="actual Windows directory sharing")
def test_restore_native_directory_handle_without_delete_sharing(snapshot, tmp_path, monkeypatch):
    backup, target, files = snapshot
    api = ctypes.WinDLL("kernel32", use_last_error=True)
    api.CreateFileW.argtypes = [ctypes.c_wchar_p, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p,
                              ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p]
    api.CreateFileW.restype = ctypes.c_void_p
    api.CloseHandle.argtypes = [ctypes.c_void_p]
    api.CloseHandle.restype = ctypes.c_int
    inventory = protocol.inventory
    handles, waits = [], []
    def observe(root):
        result = inventory(root)
        if Path(root).name.endswith(".restore-staging"):
            handle = api.CreateFileW(str(root), 0x80000000, 3, None, 3, 0x02000000, None)
            assert handle not in (None, ctypes.c_void_p(-1).value), ctypes.get_last_error()
            handles.append(handle)
        return result
    def release(delay):
        waits.append(delay)
        assert api.CloseHandle(handles.pop())
    monkeypatch.setattr(protocol, "inventory", observe)
    monkeypatch.setattr(protocol.time, "sleep", release)
    try:
        assert protocol.restore_drill(backup, target, own=tmp_path) == files
        assert inventory(target) == files and waits == [0.02]
    finally:
        for handle in handles:
            assert api.CloseHandle(handle)


@pytest.mark.parametrize("code", [5, 32])
def test_atomic_record_retries_native_contention(tmp_path, monkeypatch, code):
    target = tmp_path / "audit.json"
    target.write_bytes(b'{"previous": true}')
    replace = protocol.os.replace
    attempts, waits = [], []
    def interrupted(*args):
        attempts.append(args)
        if len(attempts) <= 3:
            raise contention(code)
        return replace(*args)
    monkeypatch.setattr(protocol.os, "replace", interrupted)
    monkeypatch.setattr(protocol.time, "sleep", waits.append)
    protocol.atomic_record(target, {"current": True})
    assert target.read_bytes() == b'{"current": true}\n'
    assert len(attempts) == 4 and waits == [0.02, 0.04, 0.08]


@pytest.mark.parametrize("code,expected_attempts", [(5, 4), (32, 4), (None, 1), (87, 1)])
def test_atomic_record_persistent_failure_preserves_original_and_receipt(tmp_path, monkeypatch, code, expected_attempts):
    target = tmp_path / "audit.json"
    previous = b'{"previous": true}'
    target.write_bytes(previous)
    attempts, waits = [], []
    def denied(*args):
        attempts.append(args)
        error = PermissionError("persistent audit publication failure")
        if code is not None:
            error.winerror = code
        raise error
    monkeypatch.setattr(protocol.os, "replace", denied)
    monkeypatch.setattr(protocol.time, "sleep", waits.append)
    with pytest.raises(protocol.InfrastructureError) as caught:
        protocol.atomic_record(target, {"current": True})
    assert caught.value.record_failure['stage'] == 'replace'
    assert target.read_bytes() == previous
    assert target.with_name('audit.json.own-tmp').read_bytes() == b'{"current": true}\n'
    assert len(attempts) == expected_attempts and len(waits) == expected_attempts - 1


@pytest.mark.skipif(os.name != 'nt', reason='actual Windows file sharing')
def test_atomic_record_native_reader_without_delete_sharing(tmp_path, monkeypatch):
    target = tmp_path / 'audit.json'
    target.write_bytes(b'{"previous": true}')
    api = ctypes.WinDLL('kernel32', use_last_error=True)
    api.CreateFileW.argtypes = [ctypes.c_wchar_p, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p,
                              ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p]
    api.CreateFileW.restype = ctypes.c_void_p
    api.CloseHandle.argtypes = [ctypes.c_void_p]
    api.CloseHandle.restype = ctypes.c_int
    handle = api.CreateFileW(str(target), 0x80000000, 3, None, 3, 0, None)
    assert handle not in (None, ctypes.c_void_p(-1).value), ctypes.get_last_error()
    waits, handles = [], [handle]
    def release(delay):
        waits.append(delay)
        assert api.CloseHandle(handles.pop())
    monkeypatch.setattr(protocol.time, 'sleep', release)
    try:
        protocol.atomic_record(target, {"current": True})
        assert target.read_bytes() == b'{"current": true}\n' and waits == [0.02]
    finally:
        for handle in handles:
            assert api.CloseHandle(handle)
