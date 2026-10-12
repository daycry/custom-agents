"""Real owned Git boundaries for the CLI used by the delivery workflow."""
import importlib.util
import json
import os
import shutil
from pathlib import Path
import subprocess
import sys

import pytest

SCRIPT = Path(__file__).resolve().with_name('commit-selection.py')


@pytest.fixture(autouse=True)
def closed_environment(tmp_path, monkeypatch):
    home = tmp_path / 'closed-environment'
    homes = {'HOME': home / 'home', 'USERPROFILE': home / 'home',
             'CODEX_HOME': home / 'codex', 'APPDATA': home / 'appdata',
             'LOCALAPPDATA': home / 'localappdata', 'TMP': home / 'tmp',
             'TEMP': home / 'tmp', 'TMPDIR': home / 'tmp',
             'XDG_CONFIG_HOME': home / 'xdg/config', 'XDG_DATA_HOME': home / 'xdg/data',
             'XDG_CACHE_HOME': home / 'xdg/cache', 'XDG_STATE_HOME': home / 'xdg/state',
             'XDG_RUNTIME_DIR': home / 'xdg/runtime'}
    for name, path in homes.items():
        path.mkdir(parents=True, exist_ok=True)
        monkeypatch.setenv(name, str(path))
    # Inherited Git overrides must not select another index/repository/config.
    for name in list(os.environ):
        if name.startswith('GIT_'):
            monkeypatch.delenv(name)
    hooks = home / 'empty-hooks'
    template = home / 'empty-template'
    hooks.mkdir()
    template.mkdir()
    for name, value in {'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': os.devnull,
            'GIT_CONFIG_SYSTEM': os.devnull, 'GIT_OPTIONAL_LOCKS': '0',
            'GIT_TERMINAL_PROMPT': '0', 'GIT_CONFIG_COUNT': '3',
            'GIT_CONFIG_KEY_0': 'core.fsmonitor', 'GIT_CONFIG_VALUE_0': 'false',
            'GIT_CONFIG_KEY_1': 'core.hooksPath', 'GIT_CONFIG_VALUE_1': str(hooks),
            'GIT_CONFIG_KEY_2': 'commit.gpgSign', 'GIT_CONFIG_VALUE_2': 'false'}.items():
        monkeypatch.setenv(name, value)
    return template


@pytest.fixture
def repo(tmp_path, closed_environment):
    executable = shutil.which('git')
    if executable is None:
        pytest.skip('Git executable unavailable')
    root = tmp_path / 'repo'
    root.mkdir()
    def git(*args):
        return subprocess.run([executable, *args], cwd=root,
            capture_output=True, check=True, timeout=10).stdout
    git('init', '-q', '--template=' + str(closed_environment))
    git('config', 'user.name', 'Owned fixture')
    git('config', 'user.email', 'owned@example.invalid')
    (root / 'selected.txt').write_bytes(b'old selected\n')
    (root / 'foreign.txt').write_bytes(b'old foreign\n')
    git('add', '--', 'selected.txt', 'foreign.txt')
    git('commit', '-q', '-m', 'owned baseline')
    (root / 'selected.txt').write_bytes(b'reviewed selected\n')
    (root / 'foreign.txt').write_bytes(b'foreign staged\n')
    git('add', '--', 'foreign.txt')
    return root, git

def cli(root, operation, *, body=None, args=()):
    return subprocess.run([sys.executable, '-I', '-X', 'utf8', '-B', str(SCRIPT), operation,
        '--root', str(root), *args], input=body, capture_output=True, timeout=15)


def test_preview_validate_exact_roundtrip_is_readonly(repo):
    root, git = repo
    before = (root / '.git/index').read_bytes()
    preview = cli(root, 'preview', args=('--path', 'selected.txt'))
    assert preview.returncode == 0, preview.stderr
    data = json.loads(preview.stdout)
    assert data['seleccionados'][0]['path'] == 'selected.txt'
    assert [r['path'] for r in data['staged_ajenos']] == ['foreign.txt']
    checked = cli(root, 'validate', body=preview.stdout)
    assert checked.returncode == 0, checked.stderr
    assert json.loads(checked.stdout) == {'valido': True, 'motivos': []}
    assert (root / '.git/index').read_bytes() == before
    assert git('diff', '--cached', '--name-only') == b'foreign.txt\n'


def test_drift_returns_invalid_before_commit(repo):
    root, _ = repo
    preview = cli(root, 'preview', args=('--path', 'selected.txt'))
    assert preview.returncode == 0, preview.stderr
    (root / 'selected.txt').write_bytes(b'changed after preview\n')
    checked = cli(root, 'validate', body=preview.stdout)
    assert checked.returncode == 1
    assert json.loads(checked.stdout)['valido'] is False


def test_conflicting_selection_is_reported_without_staging(repo):
    root, git = repo
    before = (root / '.git/index').read_bytes()
    preview = cli(root, 'preview', args=('--path', 'foreign.txt'))
    assert preview.returncode == 1
    assert any(r['code'] == 'staged_conflict' for r in json.loads(preview.stdout)['conflictos'])
    assert (root / '.git/index').read_bytes() == before


@pytest.mark.parametrize('body', [b'{', b'{"schema_version":1,"schema_version":1}', b'[' * 2000 + b']' * 2000])
def test_invalid_json_returns_closed_result_without_exception(repo, body):
    root, _ = repo
    checked = cli(root, 'validate', body=body)
    assert checked.returncode == 1
    assert json.loads(checked.stdout) == {'valido': False, 'motivos': [{'code': 'invalid_snapshot'}]}
    assert checked.stderr == b''


def test_missing_git_metadata_does_not_echo_local_exception(tmp_path):
    result = cli(tmp_path, 'preview', args=('--path', 'selected.txt'))
    assert result.returncode == 3
    assert json.loads(result.stdout) == {'status': 'unavailable', 'reason': 'projection_unavailable'}
    assert result.stderr == b''


def test_invalid_path_has_closed_json_without_stderr(repo):
    root, _ = repo
    result = cli(root, 'preview', args=('--path', '../invalid'))
    assert result.returncode == 2
    assert json.loads(result.stdout) == {'status': 'invalid_input', 'reason': 'invalid_selection'}
    assert result.stderr == b''

@pytest.fixture
def cli_module():
    spec = importlib.util.spec_from_file_location('commit_cli_output_boundary', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def emitted_boundary(cli_module, monkeypatch, total_budget):
    import io
    value = {'valido': False, 'motivos': [{'code': 'selected_changed',
                                          'path': 'é área selected.txt' * 8}]}
    expected = json.dumps(value, ensure_ascii=True, allow_nan=False,
                          separators=(',', ':')).encode('utf-8') + b'\n'
    target = io.BytesIO()
    class Output:
        buffer = target
    monkeypatch.setattr(cli_module, 'MAX_SNAPSHOT_BYTES', total_budget(len(expected)))
    monkeypatch.setattr(cli_module.sys, 'stdout', Output())
    code = cli_module._emit(value, 1)
    return code, target.getvalue(), expected, cli_module.MAX_SNAPSHOT_BYTES


def test_output_total_byte_limit_accepts_exact_record(cli_module, monkeypatch):
    code, raw, expected, quota = emitted_boundary(cli_module, monkeypatch, lambda size: size)
    assert code == 1 and raw == expected
    assert len(raw) == quota and json.loads(raw)['valido'] is False


def test_output_total_byte_limit_rejects_one_byte_over(cli_module, monkeypatch):
    code, raw, expected, quota = emitted_boundary(cli_module, monkeypatch, lambda size: size - 1)
    assert len(expected) == quota + 1
    assert code == 3 and json.loads(raw) == {'status': 'unavailable', 'reason': 'response_budget'}
    assert raw.endswith(b'\n') and len(raw) <= quota