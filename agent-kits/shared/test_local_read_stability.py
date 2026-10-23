"""Metadata recovery must repeat stable checks, identical bytes and total read bounds."""
import hashlib
import importlib.util
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

SCRIPT = Path(__file__).with_name('local-read.py')

@pytest.fixture
def reader():
    spec = importlib.util.spec_from_file_location('stable_read_tests', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def controlled(reader, monkeypatch, *, windows=True, continuous=False, changed=None, payloads=None, failed_seek=False):
    monkeypatch.setattr(reader, '_WINDOWS_READ', windows, raising=False)
    original_stat, original_open = reader.os.fstat, reader.os.fdopen
    observations, reads = [], []
    def observe(fd):
        info = original_stat(fd)
        fields = {k: getattr(info, k) for k in dir(info) if k.startswith('st_')}
        fields['st_ctime_ns'] = 1000 if not observations else (1000 + len(observations)*100 if continuous else 1100)
        if changed and observations:
            key, value = changed
            fields[key] = value(fields[key])
        result = SimpleNamespace(**fields)
        observations.append(result)
        return result
    class Handle:
        def __init__(self, handle): self.handle = handle
        def __enter__(self): return self
        def __exit__(self, *args): self.handle.close()
        def fileno(self): return self.handle.fileno()
        def seek(self, *args):
            if failed_seek:
                raise OSError('PRIVATE_SEEK_FAILURE')
            return self.handle.seek(*args)
        def read(self, size):
            data = self.handle.read(size)
            if payloads is not None:
                data = payloads[min(len(reads), len(payloads)-1)]
            reads.append((size, data))
            return data
    monkeypatch.setattr(reader.os, 'fstat', observe)
    monkeypatch.setattr(reader.os, 'fdopen', lambda *a, **k: Handle(original_open(*a, **k)))
    return reads, observations

def test_windows_metadata_settles_only_after_identical_stable_reread(tmp_path, reader, monkeypatch):
    raw = b'\xef\xbb\xbfowned\r\n'
    (tmp_path / 'entry.bin').write_bytes(raw)
    reads, observed = controlled(reader, monkeypatch)
    result = reader.read_bytes(tmp_path, 'entry.bin', max_bytes=64, include_identity=True, include_digest=True)
    assert result['status'] == 'ok', result
    assert result['data'] == raw and result['sha256'] == hashlib.sha256(raw).hexdigest()
    assert result['bytes'] == 2*len(raw)
    assert len(reads) == 2 and observed[-1].st_ctime_ns == result['generation'][2]
    assert result['generation'] == reader._generation(observed[-1])

def test_windows_recovery_budget_includes_both_reads_and_text_decode(tmp_path, reader, monkeypatch):
    (tmp_path / 'entry.md').write_bytes(b'owned')
    reads, _ = controlled(reader, monkeypatch)
    result = reader.read_text(tmp_path, 'entry.md', max_bytes=10)
    assert result == {'status': 'ok', 'text': 'owned', 'bytes': 10}
    assert len(reads) == 2 and reads[1][0] == 6

def test_windows_persistent_metadata_change_returns_no_data_and_stops_after_two_reads(tmp_path, reader, monkeypatch):
    (tmp_path / 'entry.md').write_bytes(b'owned')
    reads, _ = controlled(reader, monkeypatch, continuous=True)
    result = reader.read_bytes(tmp_path, 'entry.md', max_bytes=64, include_digest=True)
    assert result == {'status': 'changed_path', 'data': None, 'bytes': 10}
    assert len(reads) == 2

def test_windows_different_reread_bytes_never_receive_a_successful_digest(tmp_path, reader, monkeypatch):
    (tmp_path / 'entry.md').write_bytes(b'owned')
    reads, _ = controlled(reader, monkeypatch, payloads=[b'owned', b'other'])
    assert reader.read_bytes(tmp_path, 'entry.md', max_bytes=64, include_digest=True) == {
        'status': 'changed_path', 'data': None, 'bytes': 10}
    assert len(reads) == 2

@pytest.mark.parametrize('field', ['st_size', 'st_mtime_ns', 'st_ino', 'st_nlink', 'st_mode'])
def test_content_identity_or_link_changes_are_rejected_without_reread(tmp_path, reader, monkeypatch, field):
    (tmp_path / 'entry.md').write_bytes(b'owned')
    value = (lambda n: 0) if field == 'st_mode' else (lambda n: n+1)
    reads, _ = controlled(reader, monkeypatch, changed=(field, value))
    assert reader.read_bytes(tmp_path, 'entry.md', max_bytes=64) == {
        'status': 'changed_path', 'data': None, 'bytes': 5}
    assert len(reads) == 1

def test_posix_metadata_change_preserves_existing_failure_without_reread(tmp_path, reader, monkeypatch):
    (tmp_path / 'entry.md').write_bytes(b'owned')
    reads, _ = controlled(reader, monkeypatch, windows=False)
    assert reader.read_bytes(tmp_path, 'entry.md') == {'status': 'changed_path', 'data': None, 'bytes': 5}
    assert len(reads) == 1

def test_insufficient_remaining_budget_never_starts_another_read(tmp_path, reader, monkeypatch):
    (tmp_path / 'entry.md').write_bytes(b'owned')
    reads, _ = controlled(reader, monkeypatch)
    assert reader.read_bytes(tmp_path, 'entry.md', max_bytes=5) == {
        'status': 'changed_path', 'data': None, 'bytes': 5}
    assert len(reads) == 1

def test_reread_seek_failure_is_visible_and_does_not_disclose_private_text(tmp_path, reader, monkeypatch):
    (tmp_path / 'entry.md').write_bytes(b'owned')
    reads, _ = controlled(reader, monkeypatch, failed_seek=True)
    assert reader.read_bytes(tmp_path, 'entry.md', max_bytes=64) == {
        'status': 'unreadable', 'data': None, 'bytes': 5}
    assert len(reads) == 1

def test_path_redirect_between_reads_is_rejected_without_consuming_external_data(tmp_path, reader, monkeypatch):
    target = tmp_path / 'entry.md'
    target.write_bytes(b'owned')
    reads, _ = controlled(reader, monkeypatch)
    original = reader._unchanged
    def redirect(snapshots):
        if reads:
            return False
        return original(snapshots)
    monkeypatch.setattr(reader, '_unchanged', redirect)
    assert reader.read_bytes(tmp_path, 'entry.md') == {'status': 'changed_path', 'data': None, 'bytes': 5}
    assert len(reads) == 1

def test_second_read_failure_reserves_only_remaining_allocation(tmp_path, reader, monkeypatch):
    (tmp_path / 'entry.md').write_bytes(b'owned')
    controlled(reader, monkeypatch)
    original = reader.os.fdopen
    def fail_second(*args, **kwargs):
        wrapped = original(*args, **kwargs)
        original_read = wrapped.read
        calls = 0
        def read(size):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError('PRIVATE_SECOND_READ_FAILURE')
            return original_read(size)
        wrapped.read = read
        return wrapped
    monkeypatch.setattr(reader.os, 'fdopen', fail_second)
    assert reader.read_bytes(tmp_path, 'entry.md', max_bytes=64) == {
        'status': 'unreadable', 'data': None, 'bytes': 65}


@pytest.mark.skipif(os.name != 'nt', reason='Windows metadata control uses actual owned native handle')
@pytest.mark.parametrize('change_payload', [False, True], ids=['metadata-only', 'different-bytes'])
@pytest.mark.parametrize('length', [5, 8191, 8192, 8193], ids=['small', 'before-buffer', 'buffer', 'after-buffer'])
def test_native_windows_metadata_control_requires_identical_stable_bytes(tmp_path, reader, monkeypatch, change_payload, length):
    import ctypes
    from ctypes import wintypes
    target = tmp_path / 'native.bin'
    raw = b'owned' + b'x'*(length-5)
    target.write_bytes(raw)
    initial = target.stat()
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    class BasicInfo(ctypes.Structure):
        _fields_ = [(name, ctypes.c_longlong) for name in
            ('CreationTime', 'LastAccessTime', 'LastWriteTime', 'ChangeTime')] + [('FileAttributes', wintypes.DWORD)]
    kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
        ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.GetFileInformationByHandleEx.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    kernel.GetFileInformationByHandleEx.restype = wintypes.BOOL
    kernel.SetFileInformationByHandle.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    kernel.SetFileInformationByHandle.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    observed, reads = [], []
    original_stat, original_open = reader.os.fstat, reader.os.fdopen
    def stat_(fd):
        info = original_stat(fd)
        observed.append((info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns))
        return info
    def change_metadata():
        handle = kernel.CreateFileW(str(target), 0x100, 7, None, 3, 0, None)
        assert handle != ctypes.c_void_p(-1).value, ctypes.get_last_error()
        try:
            current = BasicInfo()
            assert kernel.GetFileInformationByHandleEx(handle, 0, ctypes.byref(current), ctypes.sizeof(current)), ctypes.get_last_error()
            update = BasicInfo()
            update.ChangeTime = current.ChangeTime + 1000000
            assert kernel.SetFileInformationByHandle(handle, 0, ctypes.byref(update), ctypes.sizeof(update)), ctypes.get_last_error()
        finally:
            assert kernel.CloseHandle(handle), ctypes.get_last_error()
    class Handle:
        def __init__(self, handle): self.handle = handle
        def __enter__(self): return self
        def __exit__(self, *args): self.handle.close()
        def fileno(self): return self.handle.fileno()
        def seek(self, *args): return self.handle.seek(*args)
        def read(self, limit):
            raw = self.handle.read(limit)
            reads.append(raw)
            if len(reads) == 1:
                if change_payload:
                    target.write_bytes(b'other' + b'x'*(length-5))
                    os.utime(target, ns=(initial.st_atime_ns, initial.st_mtime_ns))
                change_metadata()
            return raw
    monkeypatch.setattr(reader.os, 'fstat', stat_)
    monkeypatch.setattr(reader.os, 'fdopen', lambda *a, **k: Handle(original_open(*a, **k)))
    result = reader.read_bytes(tmp_path, 'native.bin', max_bytes=2*length, include_digest=True)
    assert observed[0][:3] == observed[1][:3] and observed[0][3] != observed[1][3], observed
    assert len(reads) == 2, (reads, result, observed)
    assert result['bytes'] == 2*length
    if change_payload:
        assert result['status'] == 'changed_path' and result['data'] is None, (result, observed)
    else:
        assert result['status'] == 'ok' and result['data'] == raw, (result, observed)
        assert result['sha256'] == hashlib.sha256(raw).hexdigest()


def test_metadata_recovery_rejects_link_change_before_second_read(tmp_path, reader, monkeypatch):
    (tmp_path / 'entry.md').write_bytes(b'owned')
    reads, _ = controlled(reader, monkeypatch)
    original = reader.os.fstat
    calls = 0
    def later_change(fd):
        nonlocal calls
        calls += 1
        observed = original(fd)
        if calls == 3:
            observed.st_nlink += 1
        return observed
    monkeypatch.setattr(reader.os, 'fstat', later_change)
    assert reader.read_bytes(tmp_path, 'entry.md') == {'status': 'changed_path', 'data': None, 'bytes': 5}
    assert len(reads) == 1


def test_metadata_recovery_rechecks_parent_before_second_read(tmp_path, reader, monkeypatch):
    (tmp_path / 'entry.md').write_bytes(b'owned')
    reads, _ = controlled(reader, monkeypatch)
    original = reader._unchanged
    calls = 0
    def moved_parent(snapshots):
        nonlocal calls
        calls += 1
        return False if calls == 3 else original(snapshots)
    monkeypatch.setattr(reader, '_unchanged', moved_parent)
    assert reader.read_bytes(tmp_path, 'entry.md') == {'status': 'changed_path', 'data': None, 'bytes': 5}
    assert len(reads) == 1
