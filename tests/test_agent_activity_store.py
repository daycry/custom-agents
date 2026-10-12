import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import shutil
from types import SimpleNamespace

import pytest

SHARED = Path(__file__).resolve().parents[1] / 'agent-kits' / 'shared'


def node_binary():
    node = os.environ.get('ACTIVITY_NODE') or shutil.which('node')
    if not node:
        pytest.skip('Node launcher is unavailable')
    return node


def load(name):
    path = SHARED / (name + '.py')
    if not path.is_file():
        pytest.fail('activity capture/snapshot capability is absent')
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def api():
    if not (SHARED / 'agent-activity-store.py').is_file():
        def absent(*args, **kwargs):
            raise AssertionError('capture/snapshot activity capability is absent')
        return SimpleNamespace(capture=absent, snapshot=absent)
    return load('agent-activity-store')


@pytest.fixture
def project(tmp_path):
    root = tmp_path / 'project'
    (root / '.claude').mkdir(parents=True)
    (root / '.claude' / 'dev.json').write_text('{"sesion":{"actividad":true}}', encoding='utf-8')
    return root


def native(root, event='SubagentStart', agent='agent-secret-id', runtime='claude'):
    return {'hook_event_name': event, 'session_id': 'session-secret-id',
        'agent_id': agent, 'agent_type': 'custom-agents:qa' if runtime == 'claude' else 'custom-agents-qa',
        'cwd': str(root), 'prompt': 'RAW-PROMPT-SENTINEL',
        'last_assistant_message': 'RAW-MESSAGE-SENTINEL', 'transcript_path': 'RAW-PATH-SENTINEL'}


def files(root):
    return {str(path.relative_to(root)): path.read_bytes() for path in root.rglob('*') if path.is_file()}


@pytest.mark.parametrize('runtime', ['claude', 'codex'])
def test_native_boundaries_and_pseudonyms(api, project, runtime):
    assert api.capture(project, runtime=runtime, payload=native(project, runtime=runtime)) == {'status': 'ok', 'reason': None}
    first = api.snapshot(project)
    assert first['status'] == 'ok'
    row = first['records'][0]
    assert row['event'] == 'response_started' and row['role'] == 'qa'
    assert row['source'] == 'native_hook' and row['scope'] == 'subagent'
    assert len(row['session_key']) == len(row['agent_key']) == 64
    assert api.capture(project, runtime=runtime, payload=native(project, 'SubagentStop', runtime=runtime))['status'] == 'ok'
    last = api.snapshot(project)['records']
    assert len(last) == 1 and last[0]['event'] == 'response_finished'
    assert last[0]['session_key'] == row['session_key'] and last[0]['agent_key'] == row['agent_key']
    assert last[0]['revision'] == row['revision'] + 1
    raw = b'\n'.join(files(project).values())
    for secret in (b'session-secret-id', b'agent-secret-id', b'RAW-PROMPT', b'RAW-MESSAGE', b'RAW-PATH'):
        assert secret not in raw


@pytest.mark.parametrize('event, expected', [('session.execution.succeeded', 'execution_finished'),
    ('session.execution.failed', 'execution_finished'), ('session.execution.interrupted', 'execution_finished'),
    ('session.idle', 'session_idle'), ('session.status', 'session_idle')])
def test_opencode_terminal_idle_only(api, project, event, expected):
    payload = {'type': event, 'data': {'sessionID': 'private-session', 'status': {'type': 'idle'}}, 'cwd': str(project)}
    assert api.capture(project, runtime='opencode', payload=payload)['status'] == 'ok'
    row = api.snapshot(project)['records'][0]
    assert row['event'] == expected and row['source'] == 'native_stream'
    assert row['scope'] == 'session' and row['agent_key'] is row['role'] is None


@pytest.mark.parametrize('runtime,event', [('claude', 'UserPromptSubmit'), ('codex', 'Stop'),
    ('claude', 'SessionEnd'), ('opencode', 'session.execution.created'), ('opencode', 'own.completed')])
def test_no_invented_boundaries(api, project, runtime, event):
    before = files(project)
    payload = native(project, event, runtime=runtime) if runtime != 'opencode' else {'type': event, 'data': {'sessionID': 'x'}, 'cwd': str(project)}
    assert api.capture(project, runtime=runtime, payload=payload) == {'status': 'unavailable', 'reason': 'unsupported_event'}
    assert files(project) == before


@pytest.mark.parametrize('config', [None, '{}', '{"sesion":{"actividad":false}}', '{"sesion":{"actividad":1}}', 'broken'])
def test_opt_in_required_no_state(api, project, config):
    path = project / '.claude' / 'dev.json'
    if config is None:
        path.unlink()
    else:
        path.write_text(config, encoding='utf-8')
    before = files(project)
    assert api.capture(project, runtime='claude', payload=native(project))['status'] != 'ok'
    assert api.snapshot(project)['status'] != 'ok'
    assert not (project / '.claude' / 'agent-activity').exists()
    assert files(project) == before


def test_read_only_empty_and_corrupt(api, project):
    before = files(project)
    assert api.snapshot(project) == {'status': 'unavailable', 'reason': 'state_missing', 'records': [], 'collection_complete': False}
    assert files(project) == before
    assert api.capture(project, runtime='claude', payload=native(project))['status'] == 'ok'
    state = project / '.claude' / 'agent-activity'
    (state / 'snapshot.json').write_bytes(b'{invalid')
    before = files(project)
    assert api.snapshot(project) == {'status': 'unavailable', 'reason': 'invalid_state', 'records': [], 'collection_complete': False}
    assert api.capture(project, runtime='claude', payload=native(project, 'SubagentStop'))['status'] == 'unavailable'
    assert files(project) == before


def test_foreign_empty_partial_state_not_adopted(api, project):
    (project / '.claude' / 'agent-activity').mkdir()
    before = files(project)
    assert api.capture(project, runtime='claude', payload=native(project)) == {'status': 'unavailable', 'reason': 'unowned_state'}
    assert files(project) == before


def test_root_binding_rejects_copied_state(api, project, tmp_path):
    import shutil
    assert api.capture(project, runtime='claude', payload=native(project))['status'] == 'ok'
    other = tmp_path / 'other'
    shutil.copytree(project, other)
    before = files(other)
    assert api.snapshot(other)['reason'] == 'unowned_state'
    assert api.capture(other, runtime='claude', payload=native(other))['reason'] == 'unowned_state'
    assert files(other) == before


def test_identity_validation_and_wrong_root(api, project):
    before = files(project)
    for key, value in [('session_id', ''), ('agent_id', []), ('agent_id', 'x' * 513), ('cwd', str(project.parent))]:
        payload = native(project); payload[key] = value
        assert api.capture(project, runtime='claude', payload=payload)['status'] == 'unavailable'
    assert files(project) == before


def test_quota_update_and_receive_clock_retention(api, project, monkeypatch):
    now = time.time()
    monkeypatch.setattr(api.time, 'time', lambda: now)
    for index in range(64):
        assert api.capture(project, runtime='claude', payload=native(project, agent='a' + str(index)))['status'] == 'ok'
    before = files(project)
    assert api.capture(project, runtime='claude', payload=native(project, agent='overflow'))['reason'] == 'quota_exceeded'
    assert files(project) == before
    assert api.capture(project, runtime='claude', payload=native(project, 'SubagentStop', agent='a0'))['status'] == 'ok'
    row = api.snapshot(project)['records'][0]
    assert all(r['observed_at'] == now for r in api.snapshot(project)['records'])
    monkeypatch.setattr(api.time, 'time', lambda: now + 60)
    snapshot = api.snapshot(project)
    assert len(snapshot['records']) == 64  # Reading does not purge expired observations.
    projection = load('agent-activity').project_activity(snapshot['records'], now=now + 60)
    assert all(r['state'] == 'unknown' for r in projection['observations'])
    assert api.capture(project, runtime='claude', payload=native(project, agent='new'))['status'] == 'ok'
    assert len(api.snapshot(project)['records']) == 1
    assert api.snapshot(project)['records'][0]['revision'] == 66


def test_unknown_role_is_closed_other(api, project):
    p = native(project); p['agent_type'] = 'invented-RAW-ROLE'
    assert api.capture(project, runtime='claude', payload=p)['status'] == 'ok'
    assert api.snapshot(project)['records'][0]['role'] == 'other'
    assert b'invented-RAW-ROLE' not in b''.join(files(project).values())


def test_hardlink_rejected_without_mutation(api, project):
    assert api.capture(project, runtime='claude', payload=native(project))['status'] == 'ok'
    path = project / '.claude' / 'agent-activity' / 'snapshot.json'
    os.link(path, project / 'alias')
    before = files(project)
    assert api.snapshot(project)['reason'] == 'unsafe_state'
    assert api.capture(project, runtime='claude', payload=native(project))['status'] == 'unavailable'
    assert files(project) == before


def test_foreign_temp_preserved(api, project):
    assert api.capture(project, runtime='claude', payload=native(project))['status'] == 'ok'
    (project / '.claude' / 'agent-activity' / '.tmp-foreign').write_bytes(b'foreign')
    before = files(project)
    assert api.capture(project, runtime='claude', payload=native(project))['reason'] == 'invalid_state'
    assert api.snapshot(project)['status'] == 'unavailable'
    assert files(project) == before


def test_busy_lock_observable_and_unchanged(api, project):
    assert api.capture(project, runtime='claude', payload=native(project))['status'] == 'ok'
    io = api._io()
    state = project / '.claude' / 'agent-activity'
    before = files(project)
    with io.locked(state, time.monotonic() + 1, False):
        assert api.capture(project, runtime='claude', payload=native(project, 'SubagentStop'))['reason'] == 'state_busy'
    assert files(project) == before


def test_real_cli_concurrent_and_silent(api, project, tmp_path, monkeypatch):
    evidence = Path(os.environ.get('ACTIVITY_EVIDENCE', str(tmp_path / 'evidence')))
    evidence.mkdir(exist_ok=True)
    monkeypatch.setenv('ACTIVITY_EVIDENCE', str(evidence))
    assert api.capture(project, runtime='claude', payload=native(project))['status'] == 'ok'
    receipts = []
    for event in ('SubagentStart', 'SubagentStop'):
        children = []
        for index in range(4):
            child_receipt = Path(os.environ['ACTIVITY_EVIDENCE']) / (event + '-' + str(index) + '.json')
            argv = [sys.executable, '-I', '-X', 'utf8', '-B', str(SHARED.parents[1] / 'tests/helpers/agent_activity_cli_observer.py'), str(child_receipt), '--runtime', 'codex', '--root', str(project)]
            payload = json.dumps(native(project, event, agent='worker' + str(index), runtime='codex')).encode()
            p = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=dict(os.environ), cwd=project)
            p.stdin.write(payload); p.stdin.close(); p.stdin = None
            children.append((p, argv, child_receipt, index))
        for p, argv, child_receipt, index in children:
            out, err = p.communicate(timeout=15)
            receipts.append({'pid': p.pid, 'index': index, 'event': event, 'argv': argv, 'exit': p.returncode, 'stdout': out.hex(), 'stderr': err.hex(), 'api': json.loads(child_receipt.read_text(encoding='utf-8'))})
            assert p.returncode == 0 and out == err == b''
    dest = Path(os.environ['ACTIVITY_EVIDENCE']) / 'cli-children.json'
    dest.write_text(json.dumps(receipts, indent=2), encoding='utf-8')
    rows = api.snapshot(project)['records']
    for receipt in receipts:
        assert receipt['api']['result'] in ({'status': 'ok', 'reason': None}, {'status': 'unavailable', 'reason': 'state_busy'})
    accepted = [r for r in receipts if r['api']['result']['status'] == 'ok']
    assert accepted
    assert len(rows) == 1 + len({r['index'] for r in accepted})
    assert len([r for r in rows if r['runtime'] == 'codex' and r['event'] == 'response_finished']) == len([r for r in accepted if r['event'] == 'SubagentStop'])
    assert max(r['revision'] for r in rows) == 1 + len(accepted)


def test_snapshot_does_not_claim_complete_capture(api, project):
    assert api.capture(project, runtime='claude', payload=native(project))['status'] == 'ok'
    snapshot = api.snapshot(project)
    assert snapshot['collection_complete'] is False
    view = load('agent-activity').project_activity(snapshot['records'], now=time.time())
    assert view['complete'] is True
    assert all(r['live_process_proven'] is False and r['agent_destroyed_proven'] is False for r in view['observations'])


def test_real_shared_launcher_captures_metadata(api, project):
    node = node_binary()
    env = dict(os.environ, CUSTOM_AGENTS_PYTHON=sys.executable, CLAUDE_PROJECT_DIR=str(project))
    argv = [node, str(SHARED.parents[1] / 'hooks' / 'run-hook.mjs'), 'agent-activity', '--runtime=codex']
    p = subprocess.run(argv, input=json.dumps(native(project, 'SubagentStop', runtime='codex')).encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, cwd=project, timeout=20)
    assert p.returncode == 0 and p.stdout == p.stderr == b''
    assert api.snapshot(project)['records'][0]['event'] == 'response_finished'


def test_real_opencode_v2_adapter_location_and_idle(api, project, tmp_path):
    (project / '.claude' / 'dev.json').write_text('{"sesion":{"actividad":true,"journal":false}}', encoding='utf-8')
    assert api.capture(project, runtime='claude', payload=native(project))['status'] == 'ok'
    node = node_binary()
    env = dict(os.environ, CUSTOM_AGENTS_PYTHON=sys.executable)
    # The Node discovery path stays owned; no shell or user runtime/config.
    env['PATH'] = str(Path(node).parent) + os.pathsep + str(Path(sys.executable).parent)
    argv = [node, str(SHARED.parents[1] / 'tests/helpers/opencode_activity_observer.mjs'), str(project), str(tmp_path / 'foreign')]
    p = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, cwd=project, timeout=20)
    assert p.returncode == 0, p.stderr.decode('utf-8', 'replace')
    observed = json.loads(p.stdout)
    assert observed == {'foreign_location_checked': True, 'cleanup_completed': True, 'subagent_callbacks_invented': False}
    rows = api.snapshot(project)['records']
    assert len(rows) == 2
    row = next(row for row in rows if row['runtime'] == 'opencode')
    assert row['event'] == 'session_idle' and row['agent_key'] is row['role'] is None
    assert b'RAW-MESSAGE-FORBIDDEN' not in b''.join(files(project).values())


def test_codex_export_preserves_existing_and_adds_exact_runtime(api):
    root = SHARED.parents[1]
    path = root / 'scripts' / 'export-interop.py'
    spec = importlib.util.spec_from_file_location('export_interop', path)
    exporter = importlib.util.module_from_spec(spec); spec.loader.exec_module(exporter)
    hooks = json.loads(exporter.codex_hooks_json(str(root)))['hooks']
    assert hooks['SubagentStart'][0]['hooks'][0]['command'].endswith('agent-activity --runtime=codex')
    stop = hooks['SubagentStop'][0]['hooks']
    assert any(h['command'].endswith('agent-activity --runtime=codex') for h in stop)
    assert any(h['command'].endswith('subagent-progress.sh --runtime=codex') for h in stop)
    assert not any('agent-activity' in h['command'] for g in hooks['SessionEnd'] for h in g['hooks'])


@pytest.mark.parametrize('mutate', ['duplicate', 'revision', 'fields', 'owner'])
def test_schema_corruption_preserves_exact_bytes(api, project, mutate):
    assert api.capture(project, runtime='claude', payload=native(project))['status'] == 'ok'
    path = project / '.claude' / 'agent-activity' / 'snapshot.json'
    value = json.loads(path.read_bytes())
    if mutate == 'duplicate': value['records'] *= 2
    elif mutate == 'revision': value['revision'] = True
    elif mutate == 'fields': value['records'][0]['content'] = 'forbidden'
    else: value['owner'] = 'foreign'
    path.write_text(json.dumps(value), encoding='utf-8')
    before = files(project)
    assert api.snapshot(project)['status'] == 'unavailable'
    assert api.capture(project, runtime='claude', payload=native(project))['status'] == 'unavailable'
    assert files(project) == before


def test_redirected_state_not_followed(api, project, tmp_path):
    target = tmp_path / 'target'; target.mkdir()
    try:
        os.symlink(target, project / '.claude' / 'agent-activity', target_is_directory=True)
    except OSError as exc:
        pytest.skip('OS refused test symlink creation: ' + type(exc).__name__)
    assert api.snapshot(project)['status'] == 'unavailable'
    assert api.capture(project, runtime='claude', payload=native(project))['status'] == 'unavailable'
    assert not list(target.iterdir())


def test_partial_installation_cli_and_launcher_are_silent(api, project, tmp_path):
    import shutil
    partial = tmp_path / 'partial'
    shared = partial / 'agent-kits' / 'shared'; shared.mkdir(parents=True)
    shutil.copyfile(SHARED / 'agent-activity-store.py', shared / 'agent-activity-store.py')
    hooks = partial / 'hooks'; hooks.mkdir()
    for name in ('run-hook.mjs', 'runtime-supervisor.py'):
        shutil.copyfile(SHARED.parents[1] / 'hooks' / name, hooks / name)
    before = files(project)
    raw = json.dumps(native(project)).encode()
    direct = [sys.executable, '-I', '-X', 'utf8', '-B', str(shared / 'agent-activity-store.py'), '--runtime', 'claude', '--root', str(project)]
    p = subprocess.run(direct, input=raw, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=dict(os.environ), cwd=project, timeout=15)
    assert p.returncode == 0 and p.stdout == p.stderr == b''
    node = node_binary()
    env = dict(os.environ, CUSTOM_AGENTS_PYTHON=sys.executable, CLAUDE_PROJECT_DIR=str(project))
    p = subprocess.run([node, str(hooks / 'run-hook.mjs'), 'agent-activity', '--runtime=claude'], input=raw, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, cwd=project, timeout=15)
    assert p.returncode == 0 and p.stdout == p.stderr == b''
    assert files(project) == before


def test_initial_publication_barrier_rejects_partial_without_adoption(api, project, monkeypatch):
    import threading
    published, release = threading.Event(), threading.Event()
    original = api._state_io.StateIO.write
    results = []

    def write(io, path, raw, deadline, expected=None):
        original(io, path, raw, deadline, expected)
        if Path(path).name == 'owner.json':
            published.set()
            assert release.wait(1), 'test owner publication barrier was not released'

    monkeypatch.setattr(api._state_io.StateIO, 'write', write)
    worker = threading.Thread(target=lambda: results.append(api.capture(project, runtime='claude', payload=native(project))), name='initializer')
    worker.start()
    assert published.wait(1)
    try:
        assert api.snapshot(project)['status'] == 'unavailable'
        partial = files(project)
        assert api.capture(project, runtime='codex', payload=native(project, runtime='codex')) == {'status': 'unavailable', 'reason': 'invalid_state'}
        assert files(project) == partial
    finally:
        release.set(); worker.join(2)
    assert not worker.is_alive()
    assert results == [{'status': 'ok', 'reason': None}]
    assert len(api.snapshot(project)['records']) == 1


def test_mutable_snapshot_validation_occurs_under_lock(api, project, monkeypatch):
    import contextlib
    import threading
    assert api.capture(project, runtime='claude', payload=native(project))['status'] == 'ok'
    temporary_ready, release = threading.Event(), threading.Event()
    held = threading.local()
    original_lock = api._state_io.StateIO.locked
    original_mkstemp = api._state_io.tempfile.mkstemp
    original_read = api._read_snapshot
    observed, results = [], []

    @contextlib.contextmanager
    def locked(io, *args):
        with original_lock(io, *args):
            held.value = True
            try: yield
            finally: held.value = False

    def mkstemp(*args, **kwargs):
        answer = original_mkstemp(*args, **kwargs)
        if threading.current_thread().name == 'publisher':
            temporary_ready.set()
            assert release.wait(1), 'test temporary publication barrier was not released'
        return answer

    def read_snapshot(*args):
        observed.append((threading.current_thread().name, getattr(held, 'value', False)))
        return original_read(*args)

    monkeypatch.setattr(api._state_io.StateIO, 'locked', locked)
    monkeypatch.setattr(api._state_io.tempfile, 'mkstemp', mkstemp)
    monkeypatch.setattr(api, '_read_snapshot', read_snapshot)
    worker = threading.Thread(target=lambda: results.append(api.capture(project, runtime='claude', payload=native(project, 'SubagentStop'))), name='publisher')
    worker.start()
    assert temporary_ready.wait(1)
    try:
        assert api.snapshot(project) == {'status': 'unavailable', 'reason': 'invalid_state', 'records': [], 'collection_complete': False}
        assert api.capture(project, runtime='codex', payload=native(project, runtime='codex')) == {'status': 'unavailable', 'reason': 'state_busy'}
        assert observed == [('publisher', True), (threading.current_thread().name, False)]
    finally:
        release.set(); worker.join(2)
    assert not worker.is_alive()
    assert results == [{'status': 'ok', 'reason': None}]
    assert api.snapshot(project)['records'][0]['event'] == 'response_finished'


@pytest.mark.parametrize('raw', [b'{', b'[]', b'{"x":1,"x":2}', b'x' * 65537], ids=['invalid', 'array', 'duplicate', 'oversize'])
def test_cli_bad_payload_silent_no_state(api, project, raw):
    before = files(project)
    argv = [sys.executable, '-I', '-X', 'utf8', '-B', str(SHARED / 'agent-activity-store.py'), '--runtime', 'claude', '--root', str(project)]
    p = subprocess.run(argv, input=raw, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=dict(os.environ), cwd=project, timeout=15)
    assert p.returncode == 0 and p.stdout == p.stderr == b''
    assert files(project) == before


def test_opencode_native_start_and_finish_share_identity(api, project):
    payload = {'type': 'session.execution.started', 'data': {'sessionID': 'private-session',
               'prompt': 'RAW-START-PROMPT'}, 'cwd': str(project)}
    assert api.capture(project, runtime='opencode', payload=payload)['status'] == 'ok'
    first = api.snapshot(project)['records'][0]
    assert first['event'] == 'execution_started' and first['scope'] == 'session'
    assert first['source'] == 'native_stream' and first['agent_key'] is first['role'] is None
    payload['type'] = 'session.execution.succeeded'
    assert api.capture(project, runtime='opencode', payload=payload)['status'] == 'ok'
    rows = api.snapshot(project)['records']
    assert len(rows) == 1 and rows[0]['event'] == 'execution_finished'
    assert rows[0]['session_key'] == first['session_key'] and rows[0]['revision'] == first['revision'] + 1
    assert b'RAW-START-PROMPT' not in b'\n'.join(files(project).values())
