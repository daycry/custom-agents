"""Owned state publication boundaries, including real Windows sharing denial."""
import contextlib
import ctypes
import importlib.util
import os
from pathlib import Path
import time

import pytest


HERE = Path(__file__).resolve().parent


class Failure(Exception):
    pass


def need(ok, reason):
    if not ok:
        raise Failure(reason)


def load(name):
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), HERE / name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def owner():
    module = load('local-state.py')
    io = module.StateIO(load('local-read.py'), need,
        lambda deadline: need(time.monotonic() < deadline, 'deadline_expired'), maximum=4096)
    return module, io


@contextlib.contextmanager
def deny_delete_sharing(path):
    """Open a real reader sharing read/write, but retaining the existing leaf."""
    from ctypes import wintypes
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
        wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    handle = kernel.CreateFileW(str(path), 0x80000000, 3, None, 3, 128, None)
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    closed = False

    def release():
        nonlocal closed
        if not closed:
            if not kernel.CloseHandle(handle):
                raise ctypes.WinError(ctypes.get_last_error())
            closed = True

    try:
        yield release
    finally:
        release()


@pytest.mark.skipif(os.name != 'nt', reason='Requires native Windows file sharing')
def test_native_reader_released_after_first_denial_allows_owned_publication(tmp_path, monkeypatch):
    module, io = owner()
    path = tmp_path / 'state.json'
    path.write_bytes(b'old')
    calls, rejected = [], []
    original_replace = os.replace
    with deny_delete_sharing(path) as release:
        expected = io.file(path)

        def replace(source, target):
            calls.append((source, target))
            try:
                return original_replace(source, target)
            except OSError as error:
                rejected.append(error.winerror)
                assert path.read_bytes() == b'old'
                release()
                raise

        monkeypatch.setattr(module.os, 'replace', replace)
        io.write(path, b'new', time.monotonic() + 2, expected=expected)
    assert rejected and all(code in (5, 32, 33) for code in rejected)
    assert len(calls) == 2
    assert len({source for source, _ in calls}) == 1
    assert path.read_bytes() == b'new'
    assert sorted(p.name for p in tmp_path.iterdir()) == ['state.json']


@pytest.mark.skipif(os.name != 'nt', reason='Requires native Windows file sharing')
def test_native_persistent_reader_denial_is_bounded_and_keeps_previous_state(tmp_path, monkeypatch):
    module, io = owner()
    path = tmp_path / 'state.json'
    path.write_bytes(b'old')
    rejected, pauses = [], []
    original_replace = os.replace

    def replace(source, target):
        try:
            return original_replace(source, target)
        except OSError as error:
            rejected.append(error.winerror)
            raise

    monkeypatch.setattr(module.os, 'replace', replace)
    monkeypatch.setattr(module.time, 'sleep', pauses.append)
    with deny_delete_sharing(path):
        expected = io.file(path)
        with pytest.raises(OSError) as caught:
            io.write(path, b'new', time.monotonic() + 2, expected=expected)
    assert caught.value.winerror in (5, 32, 33)
    assert len(rejected) == 4
    assert pauses == [0.02, 0.04, 0.08]
    assert path.read_bytes() == b'old'
    assert sorted(p.name for p in tmp_path.iterdir()) == ['state.json']


@pytest.mark.skipif(os.name != 'nt', reason='Windows bounded replacement recovery')
@pytest.mark.parametrize('code', [5, 32, 33])
def test_recoverable_denial_rechecks_owned_generation_before_retry(tmp_path, monkeypatch, code):
    module, io = owner()
    path = tmp_path / 'state.json'
    path.write_bytes(b'old')
    expected = io.file(path)
    calls = []

    def replace(source, target):
        calls.append((source, target))
        path.write_bytes(b'foreign generation')
        error = PermissionError('controlled denial')
        error.winerror = code
        raise error

    monkeypatch.setattr(module.os, 'replace', replace)
    with pytest.raises(Failure, match='unsafe_state'):
        io.write(path, b'new', time.monotonic() + 2, expected=expected)
    assert len(calls) == 1
    assert path.read_bytes() == b'foreign generation'
    assert sorted(p.name for p in tmp_path.iterdir()) == ['state.json']


@pytest.mark.skipif(os.name != 'nt', reason='Windows bounded replacement recovery')
def test_retry_stops_at_caller_deadline_without_a_second_replace(tmp_path, monkeypatch):
    module, io = owner()
    path = tmp_path / 'state.json'
    path.write_bytes(b'old')
    expected = io.file(path)
    calls = []
    expired = []
    io.guard = lambda deadline: need(not expired, 'deadline_expired')

    def replace(source, target):
        calls.append((source, target))
        expired.append(True)
        error = PermissionError('controlled denial')
        error.winerror = 32
        raise error

    monkeypatch.setattr(module.os, 'replace', replace)
    with pytest.raises(Failure, match='deadline_expired'):
        io.write(path, b'new', time.monotonic() + 2, expected=expected)
    assert len(calls) == 1
    assert path.read_bytes() == b'old'
    assert sorted(p.name for p in tmp_path.iterdir()) == ['state.json']


@pytest.mark.parametrize('code', [None, 2, 64])
def test_unrelated_error_has_no_retry_or_overwrite_fallback(tmp_path, monkeypatch, code):
    module, io = owner()
    path = tmp_path / 'state.json'
    path.write_bytes(b'old')
    expected = io.file(path)
    calls, pauses = [], []
    error = OSError('controlled non-recoverable failure')
    if code is not None:
        error.winerror = code

    def replace(source, target):
        calls.append((source, target))
        raise error

    monkeypatch.setattr(module.os, 'replace', replace)
    monkeypatch.setattr(module.time, 'sleep', pauses.append)
    with pytest.raises(OSError) as caught:
        io.write(path, b'new', time.monotonic() + 2, expected=expected)
    assert caught.value is error
    assert len(calls) == 1 and pauses == []
    assert path.read_bytes() == b'old'
    assert sorted(p.name for p in tmp_path.iterdir()) == ['state.json']


def test_exclusive_creation_failure_is_never_retried(tmp_path, monkeypatch):
    module, io = owner()
    path = tmp_path / 'state.json'
    path.write_bytes(b'foreign')
    calls = []
    original_link = os.link

    def link(source, target, **kwargs):
        calls.append((source, target))
        return original_link(source, target, **kwargs)

    monkeypatch.setattr(module.os, 'link', link)
    with pytest.raises(FileExistsError):
        io.write(path, b'new', time.monotonic() + 2)
    assert len(calls) == 1
    assert path.read_bytes() == b'foreign'
    assert sorted(p.name for p in tmp_path.iterdir()) == ['state.json']


@pytest.mark.skipif(os.name == 'nt', reason='POSIX replacement does not retry Windows codes')
def test_posix_never_retries_an_error_carrying_a_windows_code(tmp_path, monkeypatch):
    module, io = owner()
    path = tmp_path / 'state.json'
    path.write_bytes(b'old')
    calls, pauses = [], []
    error = PermissionError('controlled POSIX denial')
    error.winerror = 5

    def replace(source, target):
        calls.append((source, target))
        raise error

    monkeypatch.setattr(module.os, 'replace', replace)
    monkeypatch.setattr(module.time, 'sleep', pauses.append)
    with pytest.raises(OSError) as caught:
        io.write(path, b'new', time.monotonic() + 2, expected=io.file(path))
    assert caught.value is error
    assert len(calls) == 1 and pauses == []
    assert path.read_bytes() == b'old'
    assert sorted(p.name for p in tmp_path.iterdir()) == ['state.json']
