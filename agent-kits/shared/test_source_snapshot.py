import importlib.util
import copy
import json
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.fixture
def api():
    path = Path(__file__).with_name('source-snapshot.py')
    spec = importlib.util.spec_from_file_location('source_snapshot_test', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_fresh_receipt_can_be_verified_without_changing_sources(api, tmp_path):
    source = tmp_path / 'module.py'
    source.write_text('value = 1\n', encoding='utf-8')
    receipt = api.snapshot(tmp_path, ['module.py'])
    assert receipt['status'] == 'ok', receipt
    assert receipt['complete']
    assert receipt['sources'][0]['path'] == 'module.py'
    assert len(receipt['sources'][0]['sha256']) == 64
    assert api.verify(tmp_path, receipt)['status'] == 'fresh'
    assert source.read_text() == 'value = 1\n'
    assert sorted(p.name for p in tmp_path.iterdir()) == ['module.py']


def test_changed_missing_and_cross_project_sources_do_not_reuse(api, tmp_path):
    source = tmp_path / 'module.py'
    source.write_text('old\n')
    receipt = api.snapshot(tmp_path, ['module.py'])
    source.write_text('new\n')
    assert api.verify(tmp_path, receipt)['status'] == 'stale'
    source.unlink()
    assert api.verify(tmp_path, receipt)['status'] == 'stale'
    other = tmp_path / 'other'
    other.mkdir()
    (other / 'module.py').write_text('old\n')
    assert api.verify(other, receipt)['status'] == 'different_project'


@pytest.mark.parametrize('paths', [['../outside.py'], ['/absolute.py'], ['.claude/settings.json'],
                                  ['.env'], ['a.py', 'a.py'], [], ['a.py'] * 40])
def test_unsafe_or_unbounded_requests_fail_explicitly(api, tmp_path, paths):
    result = api.snapshot(tmp_path, paths)
    assert not result['complete']
    assert result['status'] in ('invalid_paths', 'path_budget')


def test_unreadable_or_oversized_source_is_not_a_complete_receipt(api, tmp_path):
    assert api.snapshot(tmp_path, ['missing.py'])['status'] == 'incomplete'
    (tmp_path / 'large.py').write_bytes(b'x' * (256 * 1024 + 1))
    assert not api.snapshot(tmp_path, ['large.py'])['complete']


def test_receipt_structure_cannot_hide_sources_or_claim_quality(api, tmp_path):
    (tmp_path / 'a.py').write_text('value = 1')
    receipt = api.snapshot(tmp_path, ['a.py'])
    receipt['approved'] = True
    assert api.verify(tmp_path, receipt)['status'] == 'invalid_receipt'


def test_redirected_source_is_rejected(api, tmp_path):
    actual = tmp_path / 'real.py'
    actual.write_text('original')
    link = tmp_path / 'link.py'
    try:
        link.symlink_to(actual)
    except OSError:
        pytest.skip('symlink privilege unavailable')
    assert not api.snapshot(tmp_path, ['link.py'])['complete']


@pytest.mark.parametrize('path', ['NUL', 'dir/COM1.txt', 'dir/aux.py', 'a\\b.py',
    'a:stream', '.git/config', 'a/../b', 'a//b', 'a.', 'a ', '.env.local', 'x.pem', 'x\x00.py'])
def test_nonportable_paths_are_rejected_before_io(api, tmp_path, path):
    assert api.snapshot(tmp_path, [path])['status'] == 'invalid_paths'


def test_receipt_version_and_byte_count_are_checked(api, tmp_path):
    (tmp_path / 'a.py').write_bytes(b'abc')
    receipt = api.snapshot(tmp_path, ['a.py'])
    invalid = copy.deepcopy(receipt)
    invalid['schema_version'] = True
    assert api.verify(tmp_path, invalid)['status'] == 'invalid_receipt'
    receipt['sources'][0]['bytes'] = 0
    assert api.verify(tmp_path, receipt)['status'] == 'stale'


def test_total_budget_and_missing_dependency_are_visible(api, tmp_path, monkeypatch):
    for i in range(5):
        (tmp_path / f'{i}.py').write_bytes(b'x' * api.MAX_FILE)
    value = api.snapshot(tmp_path, [f'{i}.py' for i in range(5)])
    assert not value['complete'] and value['issues'][-1]['status'] == 'byte_budget'
    monkeypatch.setattr(api, 'HERE', tmp_path / 'absent')
    api._MODULES.clear()
    assert api.snapshot(tmp_path, ['0.py'])['status'] == 'unavailable'


def test_cli_unicode_roundtrip_and_invalid_input(tmp_path):
    source = 'se\u00f1al.py'
    (tmp_path / source).write_bytes(b'abc')
    script = str(Path(__file__).with_name('source-snapshot.py'))
    def run(operation, data=None):
        return subprocess.run([sys.executable, script, operation, '--project', str(tmp_path),
            '--file', source], input=data, capture_output=True, encoding='utf-8')
    made = run('snapshot')
    assert made.returncode == 0 and source in made.stdout
    assert run('verify', made.stdout).returncode == 0
    for invalid in ['{"x":1,"x":2}', '[]', '{', 'x' * (64 * 1024 + 1)]:
        failed = run('verify', invalid)
        assert failed.returncode == 1
        assert json.loads(failed.stdout)['status'] == 'invalid_receipt'
    assert sorted(p.name for p in tmp_path.iterdir()) == [source]


@pytest.mark.parametrize('receipt', [None, [], {}, {'complete': True}])
def test_malformed_receipts_are_invalid(api, tmp_path, receipt):
    assert api.verify(tmp_path, receipt)['status'] == 'invalid_receipt'


def test_snapshot_never_emits_a_complete_receipt_its_cli_cannot_read(api, tmp_path, monkeypatch):
    # Valid portable component lengths, but UTF-8 bytes exceed the stdin budget.
    paths = [('/'.join(['\u6f22' * 80] * 10) + f'/{i}.py') for i in range(32)]
    reader = api.module('local-read.py')
    monkeypatch.setattr(reader, 'read_bytes', lambda *a, **k:
        {'status': 'ok', 'bytes': 1, 'data': b'x', 'sha256': 'a' * 64})
    receipt = api.snapshot(tmp_path, paths)
    assert not receipt['complete']
    assert receipt['status'] == 'receipt_budget'
    assert len((json.dumps(receipt, ensure_ascii=False) + '\n').encode('utf-8')) <= api.MAX_RECEIPT


def test_receipt_budget_reserves_windows_crlf_at_the_exact_boundary(api, tmp_path, monkeypatch):
    paths = [('/'.join(['\u6f22' * 80] * 8) + f'/{i}.py') for i in range(32)]
    paths[0] += 'x' * 197
    assert all(api.valid_path(path) for path in paths)
    rows = [{'path': p, 'sha256': 'a' * 64, 'bytes': 1, 'data': b'x'} for p in paths]
    monkeypatch.setattr(api, 'collect', lambda *a: ('a' * 64, rows, []))
    receipt = api.snapshot(tmp_path, paths)
    assert receipt['status'] == 'receipt_budget'
    assert not receipt['complete']
    assert len((json.dumps(receipt, ensure_ascii=False) + '\r\n').encode('utf-8')) <= api.MAX_RECEIPT
