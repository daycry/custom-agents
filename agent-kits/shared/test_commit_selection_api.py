"""Public contracts of the CLI entry point in process; subprocess tests remain independent."""
import io
import json
from types import SimpleNamespace

import pytest

from test_commit_selection_cli import SCRIPT, cli_module, closed_environment, repo


def invoke(module, monkeypatch, operation, root, *, body=b'', paths=()):
    output = io.BytesIO()
    with monkeypatch.context() as streams:
        streams.setattr(module.sys, 'stdin', SimpleNamespace(buffer=io.BytesIO(body)))
        streams.setattr(module.sys, 'stdout', SimpleNamespace(buffer=output))
        args = [operation, '--root', str(root)]
        for path in paths:
            args.extend(['--path', path])
        code = module.main(args)
    return code, output.getvalue()


@pytest.mark.parametrize('raw', [b'{', b'\xff', b'{"x":1,"x":2}', b'{"x":NaN}',
    b'{"x":Infinity}', b'{"x":-Infinity}'],
    ids=['malformed', 'non_utf8', 'duplicate', 'nan', 'positive_infinity', 'negative_infinity'])
def test_invalid_input_is_closed_before_owner(cli_module, monkeypatch, tmp_path, raw):
    def forbidden():
        raise AssertionError('Invalid transport must not reach Git or the owner')
    monkeypatch.setattr(cli_module, '_owner', forbidden)
    code, output = invoke(cli_module, monkeypatch, 'validate', tmp_path, body=raw)
    assert code == 1
    assert json.loads(output) == {'valido': False, 'motivos': [{'code': 'invalid_snapshot'}]}
    assert output.endswith(b'\n')


def test_deep_json_snapshot_is_closed_without_repository_io(cli_module, monkeypatch, tmp_path):
    # Valid JSON may decode successfully on newer interpreters. Both parser
    # rejection and the real owner's malformed-snapshot rejection must close.
    import subprocess
    def forbidden(*args, **kwargs):
        raise AssertionError('Malformed snapshot must not reach Git')
    monkeypatch.setattr(subprocess, 'run', forbidden)
    root = tmp_path / 'absent-project'
    raw = b'[' * 10000 + b']' * 10000
    code, output = invoke(cli_module, monkeypatch, 'validate', root, body=raw)
    assert code == 1
    assert json.loads(output) == {'valido': False, 'motivos': [{'code': 'invalid_snapshot'}]}
    assert not root.exists()


@pytest.mark.parametrize('extra', [0, 1], ids=['exact', 'one_over'])
def test_input_quota_counts_every_byte_before_owner(cli_module, monkeypatch, tmp_path, extra):
    maximum = 128
    raw = b'{"data":"' + b'x' * (maximum - 11 + extra) + b'"}'
    assert len(raw) == maximum + extra
    calls = []
    expected = {'valido': False, 'motivos': [{'code': 'unsupported_schema'}]}
    def validate(root, snapshot):
        calls.append((root, snapshot))
        return expected
    monkeypatch.setattr(cli_module, 'MAX_SNAPSHOT_BYTES', maximum)
    monkeypatch.setattr(cli_module, '_owner', lambda: SimpleNamespace(validar_seleccion_commit=validate))
    code, output = invoke(cli_module, monkeypatch, 'validate', tmp_path, body=raw)
    assert code == 1
    if extra:
        assert calls == []
        assert json.loads(output) == {'valido': False, 'motivos': [{'code': 'invalid_snapshot'}]}
    else:
        assert calls == [(str(tmp_path), json.loads(raw))]
        assert json.loads(output) == expected


@pytest.mark.parametrize('valid', [True, False])
def test_validator_result_keeps_reasons_and_exit(cli_module, monkeypatch, tmp_path, valid):
    result = {'valido': valid, 'motivos': [] if valid else [{'code': 'selected_changed', 'path': 'á área.txt'}]}
    monkeypatch.setattr(cli_module, '_owner', lambda: SimpleNamespace(validar_seleccion_commit=lambda root, snapshot: result))
    code, output = invoke(cli_module, monkeypatch, 'validate', tmp_path, body=b'{}')
    assert code == (0 if valid else 1)
    assert json.loads(output) == result


@pytest.mark.parametrize('error', [OSError('private path'), ImportError('private path'), RecursionError('private path')])
def test_validate_infrastructure_is_closed_without_local_exception(cli_module, monkeypatch, tmp_path, error):
    def fail(root, snapshot):
        raise error
    monkeypatch.setattr(cli_module, '_owner', lambda: SimpleNamespace(validar_seleccion_commit=fail))
    code, output = invoke(cli_module, monkeypatch, 'validate', tmp_path, body=b'{}')
    assert code == 3
    assert json.loads(output) == {'status': 'unavailable', 'reason': 'projection_unavailable'}
    assert b'private path' not in output


@pytest.mark.parametrize('error,exit_code,expected', [
    (ValueError('private path'), 2, {'status': 'invalid_input', 'reason': 'invalid_selection'}),
    (OSError('private path'), 3, {'status': 'unavailable', 'reason': 'projection_unavailable'}),
    (ImportError('private path'), 3, {'status': 'unavailable', 'reason': 'projection_unavailable'})])
def test_preview_error_classes_remain_distinct(cli_module, monkeypatch, tmp_path, error, exit_code, expected):
    def fail(root, paths):
        raise error
    monkeypatch.setattr(cli_module, '_owner', lambda: SimpleNamespace(proyectar_commit=fail))
    code, output = invoke(cli_module, monkeypatch, 'preview', tmp_path, paths=('chosen.txt',))
    assert code == exit_code and json.loads(output) == expected
    assert b'private path' not in output


def test_real_owner_roundtrip_and_drift_preserve_foreign_stage(cli_module, monkeypatch, repo):
    root, git = repo
    before = (root / '.git/index').read_bytes()
    foreign = git('rev-parse', ':foreign.txt')
    code, preview = invoke(cli_module, monkeypatch, 'preview', root, paths=('selected.txt',))
    assert code == 0
    projected = json.loads(preview)
    assert projected['seleccionados'][0]['path'] == 'selected.txt'
    assert [row['path'] for row in projected['staged_ajenos']] == ['foreign.txt']
    code, checked = invoke(cli_module, monkeypatch, 'validate', root, body=preview)
    assert code == 0 and json.loads(checked) == {'valido': True, 'motivos': []}
    (root / 'selected.txt').write_bytes(b'changed after preview\n')
    code, checked = invoke(cli_module, monkeypatch, 'validate', root, body=preview)
    assert code == 1 and json.loads(checked)['valido'] is False
    assert (root / '.git/index').read_bytes() == before
    assert git('rev-parse', ':foreign.txt') == foreign
    assert git('diff', '--cached', '--name-only') == b'foreign.txt\n'
