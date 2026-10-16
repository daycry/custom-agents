"""Owned activity exclusion: real Git and fail-closed state, no consumer config."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest
from test_agent_activity_store import api, files, native, project


def test_activity_git_exclusion_is_effective_without_external_rules(api, project, tmp_path):
    git = os.environ.get('ACTIVITY_GIT') or shutil.which('git')
    assert git, 'Git is required for the activity integration oracle'
    pin = hashlib.sha256(Path(git).read_bytes()).hexdigest()
    if os.environ.get('ACTIVITY_GIT_SHA256'):
        assert pin == os.environ['ACTIVITY_GIT_SHA256']
    closed = tmp_path / 'git-environment'
    closed.mkdir()
    env = {key: os.environ[key] for key in ('SystemRoot', 'SYSTEMROOT', 'WINDIR', 'COMSPEC', 'PATHEXT')
           if key in os.environ}
    for key in ('HOME', 'USERPROFILE', 'CODEX_HOME', 'APPDATA', 'LOCALAPPDATA',
                'XDG_CONFIG_HOME', 'XDG_DATA_HOME', 'XDG_CACHE_HOME', 'XDG_STATE_HOME',
                'TMP', 'TEMP', 'TMPDIR'):
        path = closed / key
        path.mkdir()
        env[key] = str(path)
    hooks, template = closed / 'hooks', closed / 'template'
    hooks.mkdir(); template.mkdir()
    env.update(PATH=str(Path(git).parent) + os.pathsep + str(Path(sys.executable).parent),
               GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull,
               GIT_ATTR_NOSYSTEM='1', GIT_TERMINAL_PROMPT='0')
    evidence = Path(os.environ.get('ACTIVITY_EVIDENCE', str(tmp_path / 'evidence'))) / 'git'
    evidence.mkdir(parents=True)
    receipts = []

    def call(*args):
        assert hashlib.sha256(Path(git).read_bytes()).hexdigest() == pin
        argv = [git, '-c', 'core.excludesFile=' + os.devnull,
                '-c', 'core.attributesFile=' + os.devnull, '-c', 'core.fsmonitor=false',
                '-c', 'core.hooksPath=' + str(hooks), '-c', 'commit.gpgsign=false',
                '-c', 'tag.gpgsign=false', '-c', 'commit.signoff=false', *args]
        number = len(receipts)
        stem = evidence / str(number)
        stem.with_suffix('.prelaunch.json').write_text(json.dumps(
            {'argv': argv, 'cwd': str(project), 'env': env, 'executable_sha256': pin}), encoding='utf-8')
        with stem.with_suffix('.stdout.raw').open('xb') as out, stem.with_suffix('.stderr.raw').open('xb') as err:
            child = subprocess.Popen(argv, cwd=project, env=env, stdin=subprocess.DEVNULL,
                                     stdout=out, stderr=err, shell=False)
            stem.with_suffix('.pid.json').write_text(json.dumps({'pid': child.pid}), encoding='utf-8')
            try:
                child.wait(timeout=15)
            finally:
                if child.poll() is None:
                    child.kill()
                    child.wait(timeout=10)
                raw = stem.with_suffix('.stdout.raw').read_bytes()
                error = stem.with_suffix('.stderr.raw').read_bytes()
                receipt = {'pid': child.pid, 'exit': child.returncode, 'terminal': child.poll() is not None,
                           'stdout_sha256': hashlib.sha256(raw).hexdigest(),
                           'stderr_sha256': hashlib.sha256(error).hexdigest()}
                receipts.append(receipt)
                stem.with_suffix('.terminal.json').write_text(json.dumps(receipt), encoding='utf-8')
        assert child.returncode == 0, (argv, error)
        return raw

    call('init', '--quiet', '--template=' + str(template))
    assert api.capture(project, runtime='claude', payload=native(project))['status'] == 'ok'
    assert api.record(project, {'runtime': 'claude', 'scope': 'session', 'session': 's', 'agent': None, 'role': None,
        'tool': 'Bash', 'resumen': 'git status', 'duracion_ms': None, 'resultado': 'ok', 'window': None, 'nowait': False})['status'] == 'ok'
    before = files(project / '.claude')
    status = call('status', '--porcelain=v1', '--untracked-files=all', '-z')
    call('add', '--', '.')
    indexed = call('ls-files', '-z').split(b'\0')
    assert not any(path.startswith(b'.claude/agent-activity/') for path in indexed), indexed
    assert b'agent-activity/' not in status
    ignored = call('check-ignore', '--', '.claude/agent-activity/.gitignore',
                   '.claude/agent-activity/owner.json', '.claude/agent-activity/snapshot.json',
                   '.claude/agent-activity/.lock', '.claude/agent-activity/events.json').splitlines()
    assert len([path for path in ignored if path]) == 5
    assert (project / '.claude/agent-activity/.gitignore').read_bytes() == b'*\n'
    assert files(project / '.claude') == before
    assert not (project / '.claude/.gitignore').exists()


def test_ignore_is_published_before_any_identifying_state(api, project, monkeypatch):
    original = api._state_io.StateIO.write
    order = []
    def write(io, path, raw, deadline, expected=None):
        path = Path(path)
        if path.name in ('owner.json', 'snapshot.json', 'events.json'):
            assert (path.parent / '.gitignore').read_bytes() == b'*\n'
        original(io, path, raw, deadline, expected)
        order.append(path.name)
    monkeypatch.setattr(api._state_io.StateIO, 'write', write)
    assert api.capture(project, runtime='claude', payload=native(project))['status'] == 'ok'
    assert order == ['.gitignore', 'owner.json', 'snapshot.json', 'events.json', 'snapshot.json', 'events.json']


@pytest.mark.parametrize('mutation', ['missing', 'corrupt', 'hardlink'])
def test_missing_corrupt_or_hardlinked_ignore_preserves_state(api, project, mutation):
    assert api.capture(project, runtime='claude', payload=native(project))['status'] == 'ok'
    path = project / '.claude/agent-activity/.gitignore'
    if mutation == 'missing':
        path.unlink()
    elif mutation == 'corrupt':
        path.write_bytes(b'!owner.json\n')
    else:
        os.link(path, project / 'alias-ignore')
    before = files(project)
    assert api.snapshot(project)['status'] == 'unavailable'
    assert api.capture(project, runtime='claude', payload=native(project, 'SubagentStop'))['status'] == 'unavailable'
    assert files(project) == before


@pytest.mark.parametrize('mutation', ['changed_bytes', 'same_bytes_new_identity'])
def test_ignore_change_at_publication_boundary_cannot_publish_snapshot(api, project, monkeypatch, mutation):
    assert api.capture(project, runtime='claude', payload=native(project))['status'] == 'ok'
    state = project / '.claude/agent-activity'
    old_snapshot = (state / 'snapshot.json').read_bytes()
    original = api._enabled
    calls = []
    def enabled(*args):
        original(*args)
        calls.append(True)
        if len(calls) == 2:
            if mutation == 'changed_bytes':
                (state / '.gitignore').write_bytes(b'!snapshot.json\n')
            else:
                replacement = project / 'replacement-ignore'
                replacement.write_bytes(b'*\n')
                os.replace(replacement, state / '.gitignore')
    monkeypatch.setattr(api, '_enabled', enabled)
    assert api.capture(project, runtime='claude', payload=native(project, 'SubagentStop'))['status'] == 'unavailable'
    assert calls == [True, True]
    assert (state / 'snapshot.json').read_bytes() == old_snapshot
    assert (state / '.gitignore').read_bytes() == (b'!snapshot.json\n' if mutation == 'changed_bytes' else b'*\n')


def test_ignore_only_partial_owner_is_never_adopted(api, project):
    state = project / '.claude/agent-activity'
    state.mkdir()
    (state / '.gitignore').write_bytes(b'*\n')
    before = files(project)
    assert api.capture(project, runtime='claude', payload=native(project)) == {'status': 'unavailable', 'reason': 'unowned_state'}
    assert api.snapshot(project)['status'] == 'unavailable'
    assert files(project) == before
