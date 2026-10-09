"""Local resume readers never traverse redirected paths or read unbounded files."""
import importlib.util
import os
from pathlib import Path
import stat

import pytest


def test_invalid_encoding_still_accounts_for_read_bytes(tmp_path, reader):
    path = tmp_path / 'invalid.md'
    path.write_bytes(b'\xff' * 200)
    result = reader.read_text(tmp_path, 'invalid.md')
    assert result['status'] == 'invalid_encoding' and result['bytes'] == 200


def test_failed_read_charges_allocation_without_echoing_exception(tmp_path, reader, monkeypatch):
    (tmp_path / 'entry.md').write_bytes(b'owned')
    original = reader.os.fdopen
    class FailedHandle:
        def __init__(self, handle):
            self.handle = handle
        def __enter__(self):
            return self
        def __exit__(self, *args):
            self.handle.close()
        def read(self, size):
            raise OSError('PRIVATE_PARTIAL_READ')
    monkeypatch.setattr(reader.os, 'fdopen', lambda *a, **k: FailedHandle(original(*a, **k)))
    assert reader.read_text(tmp_path, 'entry.md', max_bytes=8) == {
        'status': 'unreadable', 'text': None, 'bytes': 9}

SCRIPT = Path(__file__).with_name('local-read.py')


@pytest.fixture
def reader():
    assert SCRIPT.is_file(), 'bounded local reader is not implemented'
    spec = importlib.util.spec_from_file_location('tested_local_reader', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('data,text', [(b'', ''), (b'\xef\xbb\xbfhello\r\n', 'hello\r\n'),
                                      ('Unicode ñ 🐍'.encode(), 'Unicode ñ 🐍')])
def test_valid_utf8_empty_bom_crlf_and_unicode_are_read_without_mutation(tmp_path, reader, data, text):
    target = tmp_path / 'docs' / 'entry.md'
    target.parent.mkdir()
    target.write_bytes(data)
    before = target.stat()
    result = reader.read_text(tmp_path, 'docs/entry.md', max_bytes=100)
    assert result == {'status': 'ok', 'text': text, 'bytes': len(data)}
    assert target.read_bytes() == data and target.stat().st_mtime_ns == before.st_mtime_ns


def test_missing_file_is_distinct_from_missing_root(tmp_path, reader):
    assert reader.read_text(tmp_path, 'missing.md')['status'] == 'not_found'
    assert reader.read_text(tmp_path / 'absent', 'missing.md')['status'] == 'root_unavailable'


@pytest.mark.parametrize('name', ['../outside.md', '/outside.md', 'C:/outside.md',
                                 'C:outside.md', '//server/share/file', 'docs/../outside.md',
                                 'docs\\..\\outside.md', 'docs/file.md:stream', ''])
def test_explicit_relative_paths_cannot_escape_or_address_ntfs_streams(tmp_path, reader, name):
    assert reader.read_text(tmp_path, name)['status'] == 'invalid_path'


def test_byte_limit_checks_before_open_when_file_already_too_large(tmp_path, reader, monkeypatch):
    target = tmp_path / 'large.md'
    target.write_bytes(b'a' * 20)
    monkeypatch.setattr(reader.os, 'open', lambda *a, **k: pytest.fail('must not open oversized file'))
    assert reader.read_text(tmp_path, 'large.md', max_bytes=10)['status'] == 'too_large'


def test_bounded_read_handles_growth_after_initial_stat(tmp_path, reader, monkeypatch):
    target = tmp_path / 'growing.md'
    target.write_bytes(b'a')
    original = reader.os.open
    def grow(path, flags, *args, **kwargs):
        target.write_bytes(b'a' * 100)
        return original(path, flags, *args, **kwargs)
    monkeypatch.setattr(reader.os, 'open', grow)
    assert reader.read_text(tmp_path, 'growing.md', max_bytes=10)['status'] == 'too_large'


def test_invalid_utf8_has_a_distinct_status(tmp_path, reader):
    (tmp_path / 'entry.md').write_bytes(b'\xff\xfe')
    assert reader.read_text(tmp_path, 'entry.md')['status'] == 'invalid_encoding'


def test_permission_failure_does_not_echo_exception_or_become_absence(tmp_path, reader, monkeypatch):
    (tmp_path / 'entry.md').write_text('owned', encoding='utf8')
    def denied(*args, **kwargs):
        raise PermissionError('PRIVATE_EXCEPTION_SENTINEL')
    monkeypatch.setattr(reader.os, 'open', denied)
    result = reader.read_text(tmp_path, 'entry.md')
    assert result == {'status': 'unreadable', 'text': None, 'bytes': 0}
    assert 'PRIVATE_EXCEPTION_SENTINEL' not in str(result)


@pytest.mark.parametrize('where', ['file', 'parent', 'root'])
def test_symlink_is_rejected_before_opening_external_sentinel(tmp_path, reader, monkeypatch, where):
    root = tmp_path / 'root'; root.mkdir()
    outside = tmp_path / 'outside'; outside.mkdir()
    (outside / 'entry.md').write_text('EXTERNAL_SENTINEL', encoding='utf8')
    try:
        if where == 'file':
            (root / 'entry.md').symlink_to(outside / 'entry.md')
        elif where == 'parent':
            (root / 'docs').symlink_to(outside, target_is_directory=True)
        else:
            link = tmp_path / 'root-link'; link.symlink_to(root, target_is_directory=True); root = link
            (tmp_path / 'root' / 'entry.md').write_text('owned', encoding='utf8')
    except OSError as exc:
        pytest.skip('native symlink privilege unavailable: ' + str(exc.winerror if os.name == 'nt' else exc.errno))
    monkeypatch.setattr(reader.os, 'open', lambda *a, **k: pytest.fail('must not open redirected file'))
    relative = 'docs/entry.md' if where == 'parent' else 'entry.md'
    assert reader.read_text(root, relative)['status'] == 'redirected_path'


@pytest.mark.parametrize('tag,status', [(0xA0000003, 'redirected_path'),
                                       (0xA000000C, 'redirected_path'),
                                       (0x9000001A, 'ok'), (0x9000101A, 'ok')])
def test_windows_junction_symlink_and_cloud_tags_are_distinguished(tmp_path, reader, monkeypatch, tag, status):
    target = tmp_path / 'entry.md'; target.write_text('owned', encoding='utf8')
    original = reader.os.lstat
    class Tagged:
        def __init__(self, info):
            self.__dict__.update({k: getattr(info, k) for k in dir(info) if k.startswith('st_')})
            self.st_file_attributes = 0x400
            self.st_reparse_tag = tag
    def tagged(path, *args, **kwargs):
        info = original(path, *args, **kwargs)
        return Tagged(info) if Path(path) == target else info
    monkeypatch.setattr(reader.os, 'lstat', tagged)
    assert reader.read_text(tmp_path, 'entry.md')['status'] == status


def test_directory_and_fifo_are_not_read_as_files(tmp_path, reader):
    (tmp_path / 'dir').mkdir()
    assert reader.read_text(tmp_path, 'dir')['status'] == 'not_regular'
    if hasattr(os, 'mkfifo'):
        os.mkfifo(tmp_path / 'pipe')
        assert reader.read_text(tmp_path, 'pipe')['status'] == 'not_regular'


def test_replaced_file_identity_is_rejected_before_reading(tmp_path, reader, monkeypatch):
    target = tmp_path / 'entry.md'; target.write_text('owned', encoding='utf8')
    replacement = tmp_path / 'replacement.md'; replacement.write_text('EXTERNAL_SENTINEL', encoding='utf8')
    original = reader.os.open
    def swap(path, flags, *args, **kwargs):
        os.replace(replacement, target)
        return original(path, flags, *args, **kwargs)
    monkeypatch.setattr(reader.os, 'open', swap)
    assert reader.read_text(tmp_path, 'entry.md')['status'] == 'changed_path'


@pytest.mark.parametrize('limit', [0, -1, True, '10', None])
def test_invalid_read_limit_is_reported_without_opening(tmp_path, reader, limit):
    assert reader.read_text(tmp_path, 'entry.md', max_bytes=limit)['status'] == 'invalid_limit'


def test_unexpected_value_error_does_not_disclose_exception_text(tmp_path, reader, monkeypatch):
    (tmp_path / 'entry.md').write_text('owned', encoding='utf8')
    def failed(*args, **kwargs):
        raise ValueError('PRIVATE_EXCEPTION_SENTINEL')
    monkeypatch.setattr(reader.os, 'open', failed)
    assert reader.read_text(tmp_path, 'entry.md') == {'status': 'unreadable', 'text': None, 'bytes': 0}


def test_directory_listing_returns_sorted_names_without_reading_files(tmp_path, reader, monkeypatch):
    directory = tmp_path / 'docs'; directory.mkdir()
    for name in ['z.md', 'README.md', 'a.txt']:
        (directory / name).write_text('owned', encoding='utf8')
    (directory / 'subdir').mkdir()
    monkeypatch.setattr(reader.os, 'open', lambda *a, **k: pytest.fail('listing never reads bodies'))
    assert reader.list_names(tmp_path, 'docs') == {
        'status': 'ok', 'names': ['README.md', 'a.txt', 'subdir', 'z.md'], 'complete': True}


def test_empty_directory_is_distinct_from_missing_entry_and_root(tmp_path, reader):
    (tmp_path / 'docs').mkdir()
    assert reader.list_names(tmp_path, 'docs') == {'status': 'ok', 'names': [], 'complete': True}
    assert reader.list_names(tmp_path, 'missing')['status'] == 'not_found'
    assert reader.list_names(tmp_path / 'absent', 'docs')['status'] == 'root_unavailable'


@pytest.mark.parametrize('limit', [0, -1, True, '10', None])
def test_listing_invalid_limit_is_reported_without_enumerating(tmp_path, reader, limit, monkeypatch):
    monkeypatch.setattr(reader.os, 'scandir', lambda *a: pytest.fail('invalid limit must not enumerate'))
    assert reader.list_names(tmp_path, 'docs', max_entries=limit) == {
        'status': 'invalid_limit', 'names': [], 'complete': False}


@pytest.mark.parametrize('name', ['../outside', '/outside', 'C:/outside', 'docs/../outside', 'docs:stream', ''])
def test_listing_relative_paths_cannot_escape(tmp_path, reader, name):
    assert reader.list_names(tmp_path, name)['status'] == 'invalid_path'


def test_listing_reads_at_most_limit_plus_one_and_counts_all_names(tmp_path, reader, monkeypatch):
    (tmp_path / 'docs').mkdir()
    class Entry:
        def __init__(self, name):
            self.name = name
    class Scan:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def __iter__(self):
            for name in ['z.txt', 'README.md', 'hidden', 'must-not-read']:
                assert name != 'must-not-read', 'enumeration exceeded limit plus one'
                yield Entry(name)
    monkeypatch.setattr(reader.os, 'scandir', lambda *a: Scan())
    assert reader.list_names(tmp_path, 'docs', max_entries=2) == {
        'status': 'incomplete', 'names': ['README.md', 'z.txt'], 'complete': False}


def test_listing_exact_limit_is_complete(tmp_path, reader):
    directory = tmp_path / 'docs'; directory.mkdir()
    (directory / 'a').touch(); (directory / 'b').touch()
    assert reader.list_names(tmp_path, 'docs', max_entries=2) == {
        'status': 'ok', 'names': ['a', 'b'], 'complete': True}


def test_listing_file_is_not_a_directory(tmp_path, reader):
    (tmp_path / 'docs').write_text('owned', encoding='utf8')
    assert reader.list_names(tmp_path, 'docs')['status'] == 'not_regular'


@pytest.mark.parametrize('exception', [PermissionError, ValueError])
def test_listing_failure_is_not_absence_and_does_not_disclose_text(tmp_path, reader, monkeypatch, exception):
    (tmp_path / 'docs').mkdir()
    def failed(*args, **kwargs):
        raise exception('PRIVATE_EXCEPTION_SENTINEL')
    monkeypatch.setattr(reader.os, 'scandir', failed)
    assert reader.list_names(tmp_path, 'docs') == {'status': 'unreadable', 'names': [], 'complete': False}


@pytest.mark.parametrize('where', ['directory', 'parent', 'root'])
def test_listing_rejects_symlink_before_scandir(tmp_path, reader, monkeypatch, where):
    root = tmp_path / 'root'; root.mkdir()
    outside = tmp_path / 'outside'; outside.mkdir()
    try:
        if where == 'directory':
            (root / 'docs').symlink_to(outside, target_is_directory=True)
            relative = 'docs'
        elif where == 'parent':
            (outside / 'nested').mkdir()
            (root / 'docs').symlink_to(outside, target_is_directory=True)
            relative = 'docs/nested'
        else:
            (root / 'docs').mkdir()
            link = tmp_path / 'root-link'; link.symlink_to(root, target_is_directory=True)
            root = link; relative = 'docs'
    except OSError as exc:
        pytest.skip('native symlink privilege unavailable: ' + str(exc.winerror if os.name == 'nt' else exc.errno))
    monkeypatch.setattr(reader.os, 'scandir', lambda *a: pytest.fail('redirected directory must not enumerate'))
    assert reader.list_names(root, relative)['status'] == 'redirected_path'


@pytest.mark.parametrize('tag,status', [(0xA0000003, 'redirected_path'),
                                       (0xA000000C, 'redirected_path'),
                                       (0x9000001A, 'ok'), (0x9000101A, 'ok')])
def test_listing_distinguishes_windows_redirects_and_cloud_storage(tmp_path, reader, monkeypatch, tag, status):
    target = tmp_path / 'docs'; target.mkdir()
    original = reader.os.lstat
    class Tagged:
        def __init__(self, info):
            self.__dict__.update({k: getattr(info, k) for k in dir(info) if k.startswith('st_')})
            self.st_file_attributes = 0x400
            self.st_reparse_tag = tag
    def tagged(path, *args, **kwargs):
        info = original(path, *args, **kwargs)
        return Tagged(info) if Path(path) == target else info
    monkeypatch.setattr(reader.os, 'lstat', tagged)
    assert reader.list_names(tmp_path, 'docs')['status'] == status


def test_directory_replacement_at_open_is_rejected_before_iteration(tmp_path, reader, monkeypatch):
    target = tmp_path / 'docs'; target.mkdir()
    original = reader.os.scandir
    class ForbiddenScan:
        def __init__(self, scan):
            self.scan = scan
        def __enter__(self):
            return self
        def __exit__(self, *args):
            self.scan.close()
        def __iter__(self):
            pytest.fail('changed directory must not enumerate')
    def replaced(path):
        target.rename(tmp_path / 'previous')
        target.mkdir()
        return ForbiddenScan(original(path))
    monkeypatch.setattr(reader.os, 'scandir', replaced)
    assert reader.list_names(tmp_path, 'docs')['status'] == 'changed_path'


def test_directory_replacement_during_iteration_discards_partial_names(tmp_path, reader, monkeypatch):
    target = tmp_path / 'docs'; target.mkdir()
    class Entry:
        name = 'owned.md'
    class ReplacedScan:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def __iter__(self):
            yield Entry()
            target.rename(tmp_path / 'previous')
            target.mkdir()
    monkeypatch.setattr(reader.os, 'scandir', lambda *a: ReplacedScan())
    assert reader.list_names(tmp_path, 'docs') == {'status': 'changed_path', 'names': [], 'complete': False}


def test_directory_content_changes_during_iteration_discard_partial_names(tmp_path, reader, monkeypatch):
    target = tmp_path / 'docs'; target.mkdir()
    before = target.stat()
    class Entry:
        name = 'owned.md'
    class ChangedScan:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def __iter__(self):
            yield Entry()
            (target / 'new.md').touch()
            os.utime(target, ns=(before.st_atime_ns, before.st_mtime_ns + 2_000_000_000))
    monkeypatch.setattr(reader.os, 'scandir', lambda *a: ChangedScan())
    assert reader.list_names(tmp_path, 'docs') == {'status': 'changed_path', 'names': [], 'complete': False}


def test_file_change_after_read_is_reported_without_returning_stale_content(tmp_path, reader, monkeypatch):
    target = tmp_path / 'entry.md'; target.write_bytes(b'owned')
    before = target.stat()
    original = reader.os.fdopen
    class ChangedHandle:
        def __init__(self, handle):
            self.handle = handle
        def __enter__(self):
            return self
        def __exit__(self, *args):
            self.handle.close()
        def fileno(self):
            return self.handle.fileno()
        def read(self, size):
            data = self.handle.read(size)
            target.write_bytes(b'other')
            os.utime(target, ns=(before.st_atime_ns, before.st_mtime_ns + 2_000_000_000))
            return data
    monkeypatch.setattr(reader.os, 'fdopen', lambda *a, **k: ChangedHandle(original(*a, **k)))
    assert reader.read_text(tmp_path, 'entry.md') == {'status': 'changed_path', 'text': None, 'bytes': 5}
