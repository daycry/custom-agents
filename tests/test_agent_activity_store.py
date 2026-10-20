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


def _state(project):
    return project / '.claude' / 'agent-activity'


def test_foreign_name_is_invalid_state_and_preserved(api, project):
    assert api.capture(project, runtime='claude', payload=native(project))['status'] == 'ok'
    (_state(project) / 'otro.json').write_bytes(b'foreign')
    before = files(project)
    assert api.capture(project, runtime='claude', payload=native(project))['reason'] == 'invalid_state'
    assert api.snapshot(project)['reason'] == 'invalid_state'
    assert files(project) == before


def test_orphan_temp_keeps_capture_and_snapshot_ok(api, project):
    assert api.capture(project, runtime='claude', payload=native(project))['status'] == 'ok'
    (_state(project) / '.tmp-x').write_bytes(b'orphan')
    assert api.snapshot(project)['status'] == 'ok'
    assert api.capture(project, runtime='claude', payload=native(project))['status'] == 'ok'
    assert (_state(project) / '.tmp-x').read_bytes() == b'orphan'


def test_temps_are_neither_read_nor_deleted(api, project):
    assert api.capture(project, runtime='claude', payload=native(project))['status'] == 'ok'
    (_state(project) / '.tmp-bad').write_bytes(b'\xff{not json' * 20000)  # unreadable and oversized
    before = files(project)
    assert api.snapshot(project)['status'] == 'ok'
    assert files(project) == before


def test_eight_temps_ok_nine_state_budget(api, project):
    assert api.capture(project, runtime='claude', payload=native(project))['status'] == 'ok'
    for i in range(8):
        (_state(project) / ('.tmp-%d' % i)).write_bytes(b'o')
    assert api.snapshot(project)['status'] == 'ok'
    assert api.capture(project, runtime='claude', payload=native(project))['status'] == 'ok'
    (_state(project) / '.tmp-8').write_bytes(b'o')
    before = files(project)
    assert api.snapshot(project)['reason'] == 'state_budget'
    assert api.capture(project, runtime='claude', payload=native(project))['reason'] == 'state_budget'
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
        live = api.snapshot(project)  # a live temporary is tolerated (design 2.5 c): the committed snapshot is read
        assert live['status'] == 'ok' and len(live['records']) == 1
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


# ---- panel-redesign T-42: whitelisted, redacted summary of the tool argument (CA-16/17/41) ------
SECRETS = [
    ('sk-ant-api03-AbCdEfGhIjKlMnOpQrSt', 'AbCdEfGhIjKlMnOp'),
    ('ghp_AbCdEfGhIjKlMnOpQrStUvWx', 'AbCdEfGhIjKlMnOp'),
    ('Bearer AbCdEfGhIjKlMnOpQrStUvWxYz0123456789', 'AbCdEfGhIjKlMnOpQrSt'),
    ('eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dQw4w9WgXcQ_abcdefghij', 'dQw4w9WgXcQ'),
    ('password=Abc12345!xyz', 'Abc12345'),
    ('"token": "abcdefgh1234ijkl"', 'abcdefgh1234'),
    ('Authorization: Basic dXNlcjpwYXNzd29yZA==', 'dXNlcjpwYXNzd29yZA'),
    ("-H 'Authorization: Basic QWxhZGRpbjpvcGVuIHNlc2FtZQ=='", 'QWxhZGRpbjpvcGVuIHNlc2FtZQ'),
    ('-----BEGIN PRIVATE KEY----- MIIBVQ== -----END PRIVATE KEY-----', 'MIIBVQ'),
]
CASES = [('Bash', 'command'), ('PowerShell', 'command'), ('exec_command', 'cmd'), ('Grep', 'pattern'),
    ('Glob', 'pattern'), ('WebSearch', 'query')]


@pytest.mark.parametrize('tool,field', CASES)
@pytest.mark.parametrize('secret,fragment', SECRETS)
def test_summary_never_carries_a_secret_from_the_corpus(api, project, tool, field, secret, fragment):
    out = api.summarize(project, tool, {field: 'run ' + secret + ' end'})
    assert fragment not in out and len(out) <= 160


def test_whitelist_per_tool(api, project):
    abs_in = str(project / 'src' / 'a.py')
    s = lambda tool, **inp: api.summarize(project, tool, inp)
    assert s('Bash', command='git status\nrm -rf SECOND-LINE') == 'git status'
    assert s('Read', file_path=abs_in) == 'src/a.py'
    assert s('Edit', file_path='src/b.py') == 'src/b.py'
    assert s('MultiEdit', file_path=abs_in, edits=[{'old_string': 'RAW-CONTENT'}]) == 'src/a.py'
    assert s('Write', file_path=abs_in, content='RAW-CONTENT') == 'src/a.py'
    assert s('NotebookEdit', notebook_path=abs_in) == 'src/a.py'
    assert s('Read', paths=['a', 'b', 'c']) == '3 ficheros'
    assert s('Grep', pattern='TODO', path=abs_in) == 'TODO src/a.py'
    assert s('Glob', pattern='**/*.py') == '**/*.py'
    assert s('WebFetch', url='https://user:pw@docs.example.org:8443/a/b?q=secretquery#f') == 'docs.example.org'
    assert s('WebSearch', query='how to cache') == 'how to cache'
    assert s('Agent', subagent_type='custom-agents:qa', prompt='RAW-PROMPT') == 'custom-agents:qa'
    assert s('Task', subagent_type='qa', description='RAW-DESC') == 'qa'
    assert s('spawn_agent', agent_type='worker', message='RAW-PROMPT') == 'worker'
    assert s('Skill', skill='tdd', args='RAW') == 'tdd'


def test_apply_patch_paths_only(api, project):
    patch = '*** Begin Patch\n*** Update File: src/a.py\n@@\n-RAW-OLD\n+RAW-NEW\n*** End Patch'
    assert api.summarize(project, 'apply_patch', {'command': patch}) == 'src/a.py'
    two = patch.replace('*** End Patch', '*** Add File: src/c.py\n+x\n*** End Patch')
    assert api.summarize(project, 'apply_patch', {'command': two}) == '2 ficheros'


@pytest.mark.parametrize('tool', ['mcp__github__create_issue', 'mcp__x__y', 'SomeUnknownTool', '', 'NotebookRead2'])
def test_mcp_and_unknown_tools_have_no_summary(api, project, tool):
    assert api.summarize(project, tool, {'command': 'echo RAW', 'path': 'x', 'query': 'RAW'}) == '\u2014'


@pytest.mark.parametrize('inp', [None, 'RAW', [], {}, {'command': 5}, {'command': ['a']}, {'file_path': {'x': 1}}])
def test_malformed_input_degrades_to_no_summary(api, project, inp):
    for tool in ('Bash', 'Read', 'Grep', 'WebFetch', 'Skill', 'Agent'):
        assert api.summarize(project, tool, inp) == '\u2014'


def test_paths_are_relative_and_outside_paths_lose_their_directories(api, project, tmp_path):
    outside = tmp_path / 'elsewhere' / 'deep' / 'secret-name.txt'
    out = api.summarize(project, 'Read', {'file_path': str(outside)}, home=str(tmp_path / 'nohome'), usuario='nobody')
    assert 'elsewhere' not in out and 'deep' not in out and str(tmp_path) not in out and out.endswith('secret-name.txt')


def test_no_home_user_or_email_in_the_summary(api, project):
    home = r'C:\Users\anaperez2024'
    text = r'cat C:\Users\anaperez2024\notes.txt anaperez2024@corp.example.com /c/Users/anaperez2024/x'
    out = api.summarize(project, 'Bash', {'command': text}, home=home, usuario='anaperez2024')
    for leak in ('anaperez2024', 'corp.example.com', 'C:' + '\\Users'):
        assert leak not in out
    root_text = 'ls ' + str(project) + os.sep + 'src'
    assert str(project) not in api.summarize(project, 'Bash', {'command': root_text}, home=home, usuario='anaperez2024')


def test_order_is_redact_then_anonymize_then_strip_controls_then_clip(api, project):
    # clipping first would leave `token=Abcdef` (6 chars: too short to be recognised as a secret)
    out = api.summarize(project, 'Bash', {'command': 'x' * 146 + ' token=Abcdef123456'})
    assert 'Abcdef' not in out and len(out) == 160
    # a secret cut by the clip never survives; a control char never reaches the output
    out = api.summarize(project, 'Bash', {'command': 'echo \x1b[31mhi\x00\r\x7f there'})
    assert all(ord(c) >= 32 and ord(c) != 127 for c in out) and 'hi' in out and 'there' in out
    # redaction runs before the control strip: a secret split by a control char is not reassembled
    out = api.summarize(project, 'Bash', {'command': 'api_key=\x00AbCdEf123456'})
    assert 'AbCdEf' not in out
    # exact clip at 160 code points
    assert len(api.summarize(project, 'Bash', {'command': 'y' * 500})) == 160
    assert len(api.summarize(project, 'Bash', {'command': '\u00e9' * 500})) == 160


def test_summary_is_unavailable_without_the_redactor(api, project, monkeypatch):
    monkeypatch.setattr(api, '_redact', None)
    assert api.summarize(project, 'Bash', {'command': 'echo hi'}) == '\u2014'


def test_unterminated_pem_never_leaks_its_body_into_the_summary(api, project):
    out = api.summarize(project, 'WebSearch', {'query': 'q -----BEGIN RSA PRIVATE KEY----- MIIEowIBAAKCAQEA7 no end'})
    assert 'MIIEow' not in out and 'PRIVATE KEY' not in out


# ---- panel-redesign T-43: `events.json` ring store (CA-20, CA-21, design 2.5 states a-f) ---------
def entry(**changes):
    row = dict(runtime='claude', scope='subagent', session='session-secret-id', agent='agent-secret-id', role='qa',
        tool='Bash', resumen='git status', duracion_ms=12, resultado='ok', window=None, nowait=False)
    row.update(changes)
    return row


def events_path(project):
    return _state(project) / 'events.json'


def doc(project):
    return json.loads(events_path(project).read_bytes())


def boot(api, project):
    assert api.capture(project, runtime='claude', payload=native(project))['status'] == 'ok'


def seed(api, project, **fields):
    """Replace events.json with a valid document (same owner/scope) carrying `fields`."""
    value = doc(project) if events_path(project).exists() else None
    if value is None:
        scope = json.loads((_state(project) / 'owner.json').read_bytes())['scope_id']
        value = {'schema_version': 1, 'owner': 'custom-agents.agent-activity-v1', 'scope_id': scope, 'revision': 0,
            'config_sig': None, 'recortado': 0, 'descartados_por_tamano': 0, 'runs': [], 'ventanas': [], 'events': []}
    value.update(fields)
    events_path(project).write_bytes(json.dumps(value, sort_keys=True, separators=(',', ':')).encode())


def old_event(i, at):
    return {'schema_version': 1, 'runtime': 'claude', 'run_key': 'a' * 64, 'role': None, 'tool': 'Bash', 'resumen': 'x',
        'tarea': None, 'duracion_ms': None, 'resultado': None, 'observed_at': at, 'revision': i}


def test_lifecycle_creates_events_store_with_five_names_and_ignore(api, project):
    boot(api, project)
    names = sorted(p.name for p in _state(project).iterdir())
    assert names == ['.gitignore', '.lock', 'events.json', 'owner.json', 'snapshot.json']
    assert api.history(project)['status'] == 'ok' and api.history(project)['events'] == []
    runs = api.history(project)['runs']
    assert len(runs) == 1 and runs[0]['started_at'] is not None and runs[0]['ended_at'] is None
    assert api.capture(project, runtime='claude', payload=native(project, 'SubagentStop'))['status'] == 'ok'
    assert api.history(project)['runs'][0]['ended_at'] is not None
    assert len(api.history(project)['runs']) == 1


@pytest.mark.parametrize('config', [None, '{}', '{"sesion":{"actividad":false}}', '{"sesion":{"actividad":1}}', 'broken'])
def test_opt_out_tool_events_change_nothing_on_disk(api, project, config):
    path = project / '.claude' / 'dev.json'
    if config is None:
        path.unlink()
    else:
        path.write_text(config, encoding='utf-8')
    before = files(project)
    assert api.record(project, entry())['status'] == 'unavailable'
    assert api.count_oversize(project)['status'] == 'unavailable'
    assert api.history(project)['status'] == 'unavailable'
    assert files(project) == before and not _state(project).exists()


def test_opt_out_after_capture_keeps_existing_history_unchanged_and_hidden(api, project):
    boot(api, project)
    assert api.record(project, entry())['status'] == 'ok'
    (project / '.claude' / 'dev.json').write_text('{"sesion":{"actividad":false}}', encoding='utf-8')
    before = files(project)
    assert api.record(project, entry(tool='Read'))['status'] == 'unavailable'
    assert api.history(project)['reason'] == 'disabled' and api.history(project)['events'] == []
    assert files(project) == before


def test_tool_event_is_stored_with_closed_fields_and_no_identity(api, project):
    boot(api, project)
    assert api.record(project, entry(resumen='src/a.py', tool='Read'))['status'] == 'ok'
    event = doc(project)['events'][0]
    assert set(event) == {'schema_version', 'runtime', 'run_key', 'role', 'tool', 'resumen', 'tarea', 'duracion_ms',
        'resultado', 'observed_at', 'revision'}
    assert event['tool'] == 'Read' and event['resumen'] == 'src/a.py' and event['resultado'] == 'ok' and event['tarea'] is None
    assert len(event['run_key']) == 64 and event['revision'] == 1
    raw = events_path(project).read_bytes()
    for secret in (b'session-secret-id', b'agent-secret-id'):
        assert secret not in raw


def test_501_events_keep_500_and_count_one_trimmed(api, project):
    boot(api, project)
    now = time.time()
    seed(api, project, revision=500, events=[old_event(i, now - 5) for i in range(1, 501)])
    assert api.record(project, entry())['status'] == 'ok'
    value = doc(project)
    assert len(value['events']) == 500 and value['recortado'] == 1
    assert value['events'][0]['revision'] == 2 and value['events'][-1]['revision'] == 501
    assert len(events_path(project).read_bytes()) <= 256 * 1024


def test_retention_24h_purges_on_write_and_filters_on_read(api, project):
    boot(api, project)
    now = time.time()
    seed(api, project, revision=2, events=[old_event(1, now - 25 * 3600), old_event(2, now - 23 * 3600)])
    assert [e['revision'] for e in api.history(project)['events']] == [2]  # the read filters, never purges
    assert len(doc(project)['events']) == 2
    assert api.record(project, entry())['status'] == 'ok'
    assert [e['revision'] for e in doc(project)['events']] == [2, 3] and doc(project)['recortado'] == 0


def test_failed_write_never_breaks_the_caller(api, project, monkeypatch):
    boot(api, project)
    def boom(*args, **kwargs):
        raise OSError('disk full')
    monkeypatch.setattr(api._state_io.StateIO, 'write', boom)
    assert api.record(project, entry())['status'] == 'unavailable'
    assert api.capture(project, runtime='claude', payload=native(project, 'SubagentStop'))['status'] == 'unavailable'


def test_oversize_input_only_increments_an_identityless_counter(api, project):
    boot(api, project)
    assert api.count_oversize(project) == {'status': 'ok', 'reason': None}
    assert api.count_oversize(project)['status'] == 'ok'
    value = doc(project)
    assert value['descartados_por_tamano'] == 2 and value['events'] == []
    assert api.history(project)['descartados_por_tamano'] == 2


def test_cli_input_over_two_mib_is_counted_not_parsed(api, project):
    boot(api, project)
    argv = [sys.executable, '-I', '-X', 'utf8', '-B', str(SHARED / 'agent-activity-store.py'), '--runtime', 'claude', '--root', str(project)]
    big = b'{"x":"' + b'a' * (2 * 1024 * 1024 + 1) + b'"}'
    p = subprocess.run(argv, input=big, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=dict(os.environ), cwd=project, timeout=20)
    assert p.returncode == 0 and p.stdout == p.stderr == b''
    assert doc(project)['descartados_por_tamano'] == 1
    exact = b'{"x":"' + b'a' * (2 * 1024 * 1024 - 20) + b'"}'  # within 2 MiB: parsed, unsupported event, no count
    p = subprocess.run(argv, input=exact, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=dict(os.environ), cwd=project, timeout=20)
    assert p.returncode == 0 and doc(project)['descartados_por_tamano'] == 1


def test_oversize_counter_never_initializes_state(api, project):
    before = files(project)
    assert api.count_oversize(project)['reason'] == 'state_missing'
    assert files(project) == before


def test_concurrent_cli_writers_keep_the_store_valid(api, project):
    boot(api, project)
    seed(api, project)
    children = []
    for index in range(4):
        argv = [sys.executable, '-I', '-X', 'utf8', '-B', '-c',
            'import importlib.util,sys,json;'
            's=importlib.util.spec_from_file_location("s",sys.argv[1]);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);'
            'e=json.loads(sys.argv[3]);e["tool"]="T%s"%sys.argv[4];print(json.dumps(m.record(sys.argv[2],e)))',
            str(SHARED / 'agent-activity-store.py'), str(project), json.dumps(entry()), str(index)]
        children.append(subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=project))
    results = []
    for p in children:
        out, err = p.communicate(timeout=30)
        assert p.returncode == 0, err
        results.append(json.loads(out))
    assert all(r in ({'status': 'ok', 'reason': None}, {'status': 'unavailable', 'reason': 'state_busy'}) for r in results)
    accepted = [r for r in results if r['status'] == 'ok']
    events = doc(project)['events']
    assert len(events) == len(accepted) >= 1
    assert [e['revision'] for e in events] == list(range(1, len(events) + 1))
    assert api.history(project)['status'] == 'ok'


# (a) busy lock: the event is lost, nothing changes, no retry
def test_busy_lock_loses_the_event_without_residue(api, project):
    boot(api, project)
    before = files(project)
    with api._io().locked(_state(project), time.monotonic() + 1, False):
        assert api.record(project, entry())['reason'] == 'state_busy'
    assert files(project) == before


def test_codex_mcp_makes_a_single_attempt_without_waiting(api, project, monkeypatch):
    boot(api, project)
    sleeps = []
    real = api._state_io.time.sleep
    monkeypatch.setattr(api._state_io.time, 'sleep', lambda s: (sleeps.append(s), real(s))[1])
    with api._io().locked(_state(project), time.monotonic() + 1, False):
        sleeps.clear()
        assert api.record(project, entry(runtime='codex', nowait=True))['reason'] == 'state_busy'
        assert sleeps == []
        assert api.record(project, entry())['reason'] == 'state_busy'
        assert sleeps  # the ordinary path still waits up to 100 ms


# (b) CAS failure: another actor changed the file between the read and the replace
def test_cas_failure_loses_the_event_and_removes_the_temporary(api, project, monkeypatch):
    boot(api, project)
    original = api._state_io.StateIO.write

    def write(io, path, raw, deadline, expected=None):
        if Path(path).name == 'events.json':
            os.utime(path, ns=(1, 1))  # foreign actor touches the file
        return original(io, path, raw, deadline, expected)

    monkeypatch.setattr(api._state_io.StateIO, 'write', write)
    assert api.record(project, entry())['reason'] == 'unsafe_state'
    assert not [p for p in _state(project).iterdir() if p.name.startswith('.tmp-')]
    assert doc(project)['events'] == []
    monkeypatch.undo()
    assert api.record(project, entry())['status'] == 'ok'  # the next capture re-reads and continues


# (c) torn writes
def test_truncated_events_json_is_never_repaired_and_does_not_block_the_snapshot(api, project):
    boot(api, project)
    events_path(project).write_bytes(b'{"schema_version":1,"owner"')
    broken = events_path(project).read_bytes()
    assert api.history(project)['reason'] == 'invalid_state'
    assert api.record(project, entry())['reason'] == 'invalid_state'
    assert api.capture(project, runtime='claude', payload=native(project, 'SubagentStop'))['status'] == 'ok'
    assert api.snapshot(project)['records'][0]['event'] == 'response_finished'
    assert events_path(project).read_bytes() == broken


@pytest.mark.parametrize('mutate', ['duplicate_revision', 'extra_field', 'foreign_scope', 'future_revision', 'too_many_runs'])
def test_schema_corruption_of_events_is_invalid_state_and_preserved(api, project, mutate):
    boot(api, project)
    assert api.record(project, entry())['status'] == 'ok'
    value = doc(project)
    if mutate == 'duplicate_revision': value['events'] *= 2
    elif mutate == 'extra_field': value['events'][0]['tool_response'] = 'RAW'
    elif mutate == 'foreign_scope': value['scope_id'] = '0' * 64
    elif mutate == 'future_revision': value['revision'] = 0
    else: value['runs'] = value['runs'] * 65
    events_path(project).write_text(json.dumps(value), encoding='utf-8')
    before = files(project)
    assert api.history(project)['status'] == 'unavailable'
    assert api.record(project, entry())['status'] == 'unavailable'
    assert files(project) == before


def test_missing_events_json_in_a_valid_store_is_created_on_write_and_empty_on_read(api, project):
    boot(api, project)
    events_path(project).unlink()
    assert api.history(project)['status'] == 'ok' and api.history(project)['events'] == []
    assert not events_path(project).exists()  # the reader never creates
    assert api.record(project, entry())['status'] == 'ok'
    assert len(doc(project)['events']) == 1


def test_hardlinked_events_json_is_unsafe_and_untouched(api, project):
    boot(api, project)
    os.link(events_path(project), project / 'alias-events')
    before = files(project)
    assert api.history(project)['reason'] == 'unsafe_state'
    assert api.record(project, entry())['reason'] == 'unsafe_state'
    assert files(project) == before


def test_five_names_inventory_tolerates_eight_temps_and_rejects_nine(api, project):
    boot(api, project)
    for i in range(8):
        (_state(project) / ('.tmp-%d' % i)).write_bytes(b'o')
    assert api.history(project)['status'] == 'ok'
    assert api.record(project, entry())['status'] == 'ok'
    (_state(project) / '.tmp-8').write_bytes(b'o')
    before = files(project)
    assert api.history(project)['reason'] == 'state_budget'
    assert api.record(project, entry())['reason'] == 'state_budget'
    assert files(project) == before


# P-EI-1: the writer removes at most 8 of its own old orphan temporaries per write, under the lock
def _age(path, seconds):
    stamp = time.time() - seconds
    os.utime(path, (stamp, stamp))


def test_writer_cleans_only_old_regular_unlinked_temporaries(api, project):
    boot(api, project)
    old = [_state(project) / ('.tmp-old%d' % i) for i in range(3)]
    for p in old:
        p.write_bytes(b'o'); _age(p, 120)
    fresh = _state(project) / '.tmp-fresh'
    fresh.write_bytes(b'o'); _age(fresh, 30)
    linked = _state(project) / '.tmp-linked'
    linked.write_bytes(b'o'); _age(linked, 120)
    os.link(linked, project / 'outside-alias')
    adir = _state(project) / '.tmp-dir'
    adir.mkdir(); _age(adir, 120)
    assert api.record(project, entry())['status'] == 'ok'
    assert not any(p.exists() for p in old)
    assert fresh.exists() and linked.exists() and adir.exists()
    assert (project / 'outside-alias').read_bytes() == b'o'


def test_cleanup_is_capped_at_eight_per_write_and_runs_before_the_budget_check(api, project):
    boot(api, project)
    temps = [_state(project) / ('.tmp-o%02d' % i) for i in range(12)]
    for p in temps:
        p.write_bytes(b'o'); _age(p, 300)
    assert api.record(project, entry())['status'] == 'ok'  # 12 > 8 would be state_budget without the cleanup
    assert len([p for p in temps if p.exists()]) == 4
    assert api.record(project, entry())['status'] == 'ok'
    assert not any(p.exists() for p in temps)


def test_cleanup_never_touches_foreign_names_and_readers_never_delete(api, project):
    boot(api, project)
    old = _state(project) / '.tmp-old'
    old.write_bytes(b'o'); _age(old, 300)
    assert api.history(project)['status'] == 'ok' and api.snapshot(project)['status'] == 'ok'
    assert old.exists()
    (_state(project) / 'otro.json').write_bytes(b'foreign'); _age(_state(project) / 'otro.json', 300)
    assert api.record(project, entry())['reason'] == 'invalid_state'
    assert (_state(project) / 'otro.json').exists() and old.exists()  # a foreign name stops everything first


def test_lifecycle_write_also_cleans_old_temporaries(api, project):
    boot(api, project)
    old = _state(project) / '.tmp-old'
    old.write_bytes(b'o'); _age(old, 300)
    assert api.capture(project, runtime='claude', payload=native(project, 'SubagentStop'))['status'] == 'ok'
    assert not old.exists()


# (d) out-of-order delivery
def test_late_tool_event_after_stop_does_not_reopen_or_extend_the_run(api, project, monkeypatch):
    now = time.time()
    monkeypatch.setattr(api.time, 'time', lambda: now)
    boot(api, project)
    monkeypatch.setattr(api.time, 'time', lambda: now + 20)
    assert api.capture(project, runtime='claude', payload=native(project, 'SubagentStop'))['status'] == 'ok'
    monkeypatch.setattr(api.time, 'time', lambda: now + 30)
    assert api.record(project, entry())['status'] == 'ok'
    run = api.history(project)['runs'][0]
    assert run['ended_at'] == now + 20
    shown = load('agent-activity').project_runs([run], now=now + 31)['runs'][0]
    assert shown['estado'] == 'respuesta_terminada' and shown['duration_seconds'] == 20
    assert len(api.history(project)['events']) == 1  # listed, by reception order


def test_tool_event_without_a_start_creates_a_run_never_finished_without_stop(api, project):
    boot(api, project)
    assert api.record(project, entry(agent='never-started'))['status'] == 'ok'
    runs = api.history(project)['runs']
    assert len(runs) == 2 and sorted(r['started_at'] is None for r in runs) == [False, True]
    orphan = next(r for r in runs if r['started_at'] is None)
    assert orphan['ended_at'] is None


# attribution through the stored windows
def test_window_start_attributes_later_events_with_quarantine_and_closes(api, project, monkeypatch):
    now = time.time()
    clock = [now]
    monkeypatch.setattr(api.time, 'time', lambda: clock[0])
    boot(api, project)
    main = dict(scope='session', agent=None, role=None)
    assert api.record(project, entry(**main, window=('start', 'plan/T-07'), tool='Bash'))['status'] == 'ok'
    clock[0] = now + 2
    assert api.record(project, entry(**main))['status'] == 'ok'          # inside the 5 s quarantine
    clock[0] = now + 10
    assert api.record(project, entry(**main))['status'] == 'ok'
    assert api.record(project, entry(tool='Grep'))['status'] == 'ok'     # a subagent: the parent's single window
    assert [e['tarea'] for e in doc(project)['events']] == [None, None, 'plan/T-07', 'plan/T-07']
    clock[0] = now + 20
    assert api.record(project, entry(**main, window=('close', 'plan/T-07')))['status'] == 'ok'
    clock[0] = now + 40
    assert api.record(project, entry(**main))['status'] == 'ok'
    assert doc(project)['events'][-1]['tarea'] is None
    assert [w['estado'] for w in doc(project)['ventanas']] == ['cerrada']


def test_rejected_close_stores_the_event_without_inventing_a_window(api, project):
    boot(api, project)
    assert api.record(project, entry(scope='session', agent=None, role=None, window=('close', 'plan/T-07')))['status'] == 'ok'
    assert doc(project)['ventanas'] == []


# (e) opt-out in flight and re-enable
def test_opt_out_between_the_two_checks_publishes_nothing(api, project, monkeypatch):
    boot(api, project)
    original = api._enabled
    calls = []

    def enabled(*args):
        sig = original(*args)
        calls.append(True)
        if len(calls) == 1:
            (project / '.claude' / 'dev.json').write_text('{"sesion":{"actividad":false}}', encoding='utf-8')
        return sig

    monkeypatch.setattr(api, '_enabled', enabled)
    before = events_path(project).read_bytes()
    assert api.record(project, entry())['status'] == 'unavailable'
    assert events_path(project).read_bytes() == before and len(calls) == 1


def test_config_change_expires_open_windows_on_the_next_write(api, project):
    boot(api, project)
    main = dict(scope='session', agent=None, role=None)
    assert api.record(project, entry(**main, window=('start', 'plan/T-07')))['status'] == 'ok'
    assert [w['estado'] for w in doc(project)['ventanas']] == ['abierta']
    path = project / '.claude' / 'dev.json'
    path.write_text('{"sesion":{"actividad":true,"journal":false}}', encoding='utf-8')
    assert api.record(project, entry(**main))['status'] == 'ok'
    assert [w['estado'] for w in doc(project)['ventanas']] == ['caducada']
    assert doc(project)['events'][-1]['tarea'] is None


# (f) directory deleted by hand
def test_deleted_directory_reads_as_missing_and_is_recreated_with_a_new_scope(api, project):
    boot(api, project)
    assert api.record(project, entry())['status'] == 'ok'
    first_scope = json.loads((_state(project) / 'owner.json').read_bytes())['scope_id']
    shutil.rmtree(_state(project))
    assert api.history(project)['reason'] == 'state_missing'
    assert api.record(project, entry())['status'] == 'ok'  # the next capture recreates the directory
    assert json.loads((_state(project) / 'owner.json').read_bytes())['scope_id'] != first_scope
    assert len(api.history(project)['events']) == 1 and len(api.history(project)['runs']) == 1
    assert sorted(p.name for p in _state(project).iterdir()) == ['.gitignore', '.lock', 'events.json', 'owner.json', 'snapshot.json']


def test_half_deleted_directory_is_reported_never_adopted(api, project):
    boot(api, project)
    (_state(project) / 'owner.json').unlink()
    before = files(project)
    assert api.history(project)['reason'] == 'unowned_state'
    assert api.record(project, entry())['reason'] == 'unowned_state'
    assert files(project) == before


def test_quota_of_runs_windows_and_snapshot_contract_unchanged(api, project):
    boot(api, project)
    rows = [{'run_key': '%064x' % i, 'runtime': 'claude', 'scope': 'session', 'session_key': 'b' * 64, 'role': None,
        'started_at': None, 'last_seen': time.time() - 100 + i * 0.001, 'ended_at': None} for i in range(64)]
    seed(api, project, runs=rows)
    assert api.record(project, entry(agent='one-more'))['status'] == 'ok'
    value = doc(project)
    assert len(value['runs']) == 64 and not any(r['run_key'] == rows[0]['run_key'] for r in value['runs'])
    assert api.snapshot(project)['status'] == 'ok' and api.snapshot(project)['collection_complete'] is False


# ---- panel-redesign T-44: tool events per runtime and attribution windows by exact grammar ------
def tool_payload(root, runtime='claude', name='Bash', inp=None, event=None, agent=None, **extra):
    inp = {'command': 'git status'} if inp is None else inp
    if runtime == 'opencode':
        data = {'sessionID': 'session-secret-id', 'tool': name, 'args': inp, 'status': 'completed'}
        data.update(extra.pop('data', {}))
        return dict({'type': 'tool.execute.after', 'data': data, 'cwd': str(root)}, **extra)
    row = {'hook_event_name': event or 'PostToolUse', 'session_id': 'session-secret-id', 'cwd': str(root),
        'tool_name': name, 'tool_input': inp, 'tool_use_id': 'toolu_1', 'tool_response': {'stdout': 'RAW-RESPONSE-SENTINEL'},
        'prompt': 'RAW-PROMPT-SENTINEL', 'transcript_path': 'RAW-PATH-SENTINEL'}
    if agent:
        row.update(agent_id=agent, agent_type='custom-agents:qa' if runtime == 'claude' else 'custom-agents-qa')
    row.update(extra)
    return row


def last(api, project):
    return api.history(project)['events'][-1]


def test_claude_post_tool_use_is_ok_with_duration_and_never_stores_the_response(api, project):
    p = tool_payload(project, duration_ms=42)
    assert api.capture(project, runtime='claude', payload=p) == {'status': 'ok', 'reason': None}
    event = last(api, project)
    assert (event['tool'], event['resumen'], event['resultado'], event['duracion_ms'], event['tarea']) == ('Bash', 'git status', 'ok', 42, None)
    assert event['runtime'] == 'claude' and event['role'] is None
    raw = b'\n'.join(files(project).values())
    for secret in (b'RAW-RESPONSE', b'RAW-PROMPT', b'RAW-PATH', b'session-secret-id', b'toolu_1'):
        assert secret not in raw


def test_claude_failure_is_error_and_subagent_events_join_the_lifecycle_run(api, project):
    assert api.capture(project, runtime='claude', payload=native(project))['status'] == 'ok'
    p = tool_payload(project, event='PostToolUseFailure', agent='agent-secret-id', duration_ms=7)
    assert api.capture(project, runtime='claude', payload=p)['status'] == 'ok'
    history = api.history(project)
    event = history['events'][-1]
    assert event['resultado'] == 'error' and event['duracion_ms'] == 7 and event['role'] == 'qa'
    assert len(history['runs']) == 1 and history['runs'][0]['run_key'] == event['run_key']
    assert history['runs'][0]['scope'] == 'subagent'


def test_codex_has_no_duration_no_result_and_groups_by_session(api, project):
    p = tool_payload(project, 'codex', duration_ms=99, agent='ignored-agent')
    assert api.capture(project, runtime='codex', payload=p)['status'] == 'ok'
    assert api.capture(project, runtime='codex', payload=tool_payload(project, 'codex', 'apply_patch', {'command': '*** Begin Patch\n*** Update File: a.py\n*** End Patch'}))['status'] == 'ok'
    history = api.history(project)
    assert [(e['duracion_ms'], e['resultado'], e['role']) for e in history['events']] == [(None, None, None)] * 2
    assert len(history['runs']) == 1 and history['runs'][0]['scope'] == 'session'
    assert history['events'][1]['resumen'] == 'a.py'


def test_codex_has_no_failure_event_and_pre_tool_use_is_not_recorded(api, project):
    before = files(project)
    for event in ('PostToolUseFailure', 'PreToolUse'):
        assert api.capture(project, runtime='codex', payload=tool_payload(project, 'codex', event=event)) == {'status': 'unavailable', 'reason': 'unsupported_event'}
    assert api.capture(project, runtime='claude', payload=tool_payload(project, event='PreToolUse'))['reason'] == 'unsupported_event'
    assert files(project) == before


@pytest.mark.parametrize('status,expected', [('completed', 'ok'), ('error', 'error'), ('running', None), (None, None)])
def test_opencode_after_event_maps_status_without_duration(api, project, status, expected):
    p = tool_payload(project, 'opencode', 'bash', {'command': 'ls'}, data={'status': status, 'agent': 'custom-agents-qa'})
    assert api.capture(project, runtime='opencode', payload=p)['status'] == 'ok'
    event = last(api, project)
    assert event['resultado'] == expected and event['duracion_ms'] is None and event['runtime'] == 'opencode'
    assert event['tool'] == 'bash' and event['resumen'] == 'ls'


@pytest.mark.parametrize('runtime,changes', [
    ('claude', {'tool_name': ''}), ('claude', {'tool_name': 5}), ('claude', {'session_id': ''}),
    ('claude', {'tool_input': 'RAW'}), ('claude', {'agent_id': 5, 'agent_type': 'x'}), ('claude', {'cwd': 'elsewhere'}),
    ('cursor', {}), ('claude', {'hook_event_name': 'Elicitation'}), ('opencode', {})])
def test_invalid_or_unknown_events_are_discarded_with_a_code_and_never_raise(api, project, runtime, changes):
    assert api.capture(project, runtime='claude', payload=native(project))['status'] == 'ok'
    before = files(project)
    result = api.capture(project, runtime=runtime, payload=dict(tool_payload(project), **changes))
    assert result['status'] == 'unavailable' and type(result['reason']) is str
    assert files(project) == before


@pytest.mark.parametrize('duration', [-1, True, '5', 10 ** 12, None])
def test_duration_is_a_bounded_number_or_null(api, project, duration):
    assert api.capture(project, runtime='claude', payload=tool_payload(project, duration_ms=duration))['status'] == 'ok'
    assert last(api, project)['duracion_ms'] is None


def test_no_absolute_path_home_or_user_is_persisted(api, project):
    inp = {'file_path': str(project / 'src' / 'a.py')}
    assert api.capture(project, runtime='claude', payload=tool_payload(project, name='Read', inp=inp))['status'] == 'ok'
    assert last(api, project)['resumen'] == 'src/a.py'
    cmd = {'command': 'cat ' + str(project) + os.sep + 'notes.txt ' + os.path.expanduser('~')}
    assert api.capture(project, runtime='claude', payload=tool_payload(project, inp=cmd))['status'] == 'ok'
    raw = events_path(project).read_bytes()
    assert str(project).encode().replace(b'\\', b'\\\\') not in raw and os.path.expanduser('~').encode().replace(b'\\', b'\\\\') not in raw


def test_secret_in_the_argument_never_reaches_disk(api, project):
    cmd = {'command': "curl -H 'Authorization: Basic dXNlcjpwYXNzd29yZA==' -H 'x: sk-ant-api03-AbCdEfGhIjKlMnOpQrSt' https://h.test"}
    assert api.capture(project, runtime='claude', payload=tool_payload(project, inp=cmd))['status'] == 'ok'
    raw = b'\n'.join(files(project).values())
    assert b'dXNlcjpwYXNzd29yZA' not in raw and b'AbCdEfGhIjKlMnOp' not in raw
    assert last(api, project)['resumen'].startswith('curl -H')


# --- attribution grammar (CA-18) ---
METER = 'python3 agent-kits/shared/usage-meter.py'


def window_states(api, project):
    return [(w['tarea'], w['estado']) for w in api.history(project)['ventanas']]


@pytest.mark.parametrize('command,action,tarea', [
    (METER + ' start --artefacto panel/T-07', 'start', 'panel/T-07'),
    (METER + ' close --artefacto panel/T-07', 'close', 'panel/T-07'),
    (METER + ' start --artefacto panel/T-07-fix2', 'start', 'panel/T-07'),
    (METER + ' start --artefacto=panel/T-12', 'start', 'panel/T-12'),
    ('python agent-kits/shared/usage-meter.py start --artefacto "panel/T-03"', 'start', 'panel/T-03'),
    ('"C:\\Program Files\\Python\\python.exe" "C:\\x y\\usage-meter.py" close --artefacto panel/T-3-fix10', 'close', 'panel/T-3'),
    ('.venv/Scripts/python.exe agent-kits/shared/usage-meter.py start --artefacto plan/T-12 --state .claude/usage-state.json', 'start', 'plan/T-12'),
    ('usage-meter.py start --artefacto a-b.c/T-1', 'start', 'a-b.c/T-1'),
    ('py -3 usage-meter.py start --artefacto panel/T-09', 'start', 'panel/T-09'),
])
def test_exact_meter_argv_opens_or_closes_a_window(api, project, command, action, tarea):
    if action == 'close':
        assert api.capture(project, runtime='claude', payload=tool_payload(project, inp={'command': command.replace('close', 'start')}))['status'] == 'ok'
    assert api.capture(project, runtime='claude', payload=tool_payload(project, inp={'command': command}))['status'] == 'ok'
    assert window_states(api, project)[-1] == (tarea, 'cerrada' if action == 'close' else 'abierta')


@pytest.mark.parametrize('name,key', [('PowerShell', 'command'), ('exec_command', 'cmd'), ('shell', 'command')])
def test_other_shell_tools_open_windows_too(api, project, name, key):
    p = tool_payload(project, name=name, inp={key: METER + ' start --artefacto panel/T-07'})
    assert api.capture(project, runtime='claude', payload=p)['status'] == 'ok'
    assert window_states(api, project) == [('panel/T-07', 'abierta')]


@pytest.mark.parametrize('command', [
    'git commit -m "T-07: fix the thing"', 'grep -rn "T-07" docs', 'echo ' + METER + ' start --artefacto panel/T-07',
    METER + ' start --artefacto panel/lote-3', METER + ' start --artefacto panel/T-07 && rm -rf x',
    METER + ' start --artefacto panel/T-07; rm x', METER + ' report --artefacto panel/T-07',
    METER + ' start --artefacto panel/T-07\nrm -rf x', 'cat agent-kits/shared/usage-meter.py start --artefacto panel/T-07',
    METER + ' start --artefacto docs/roadmap/x/spec.md', METER + ' start --artefacto T-07',
    METER + ' start --artefacto panel/T-07 --artefacto panel/T-08', METER + ' start', METER + ' --artefacto panel/T-07 start',
    METER + ' start --artefacto panel/T-07 --evil x', METER + ' start --artefacto "panel/T-07 extra"',
    'nohup ' + METER + ' start --artefacto panel/T-07 &', '$(' + METER + ' start --artefacto panel/T-07)',
    'sudo python3 evil/usage-meter.py.bak start --artefacto panel/T-07', 'python3 -c "x" usage-meter.py start --artefacto panel/T-07',
])
def test_free_text_and_inexact_commands_never_open_a_window(api, project, command):
    assert api.capture(project, runtime='claude', payload=tool_payload(project, inp={'command': command}))['status'] == 'ok'
    assert api.history(project)['ventanas'] == []


@pytest.mark.parametrize('name,inp', [('Grep', {'pattern': METER + ' start --artefacto panel/T-07'}),
    ('Agent', {'subagent_type': 'qa', 'prompt': METER + ' start --artefacto panel/T-07'}),
    ('Write', {'file_path': 'a', 'content': METER + ' start --artefacto panel/T-07'}),
    ('mcp__x__y', {'command': METER + ' start --artefacto panel/T-07'})])
def test_only_shell_tools_can_open_windows(api, project, name, inp):
    assert api.capture(project, runtime='claude', payload=tool_payload(project, name=name, inp=inp))['status'] == 'ok'
    assert api.history(project)['ventanas'] == []


def test_a_failed_meter_command_does_not_open_a_window(api, project):
    p = tool_payload(project, event='PostToolUseFailure', inp={'command': METER + ' start --artefacto panel/T-07'})
    assert api.capture(project, runtime='claude', payload=p)['status'] == 'ok'
    assert api.history(project)['ventanas'] == [] and last(api, project)['resultado'] == 'error'
    p = tool_payload(project, 'opencode', 'bash', {'command': METER + ' start --artefacto panel/T-07'}, data={'status': 'error'})
    assert api.capture(project, runtime='opencode', payload=p)['status'] == 'ok'
    assert api.history(project)['ventanas'] == []


def test_opencode_shell_tool_opens_a_window(api, project):
    p = tool_payload(project, 'opencode', 'bash', {'command': METER + ' start --artefacto panel/T-07'})
    assert api.capture(project, runtime='opencode', payload=p)['status'] == 'ok'
    assert window_states(api, project) == [('panel/T-07', 'abierta')]


def test_free_text_t_xx_never_attributes_with_or_without_a_window(api, project, monkeypatch):
    now = time.time()
    clock = [now]
    monkeypatch.setattr(api.time, 'time', lambda: clock[0])
    texts = [('Bash', {'command': 'git commit -m "T-07: msg"'}), ('Agent', {'subagent_type': 'qa', 'prompt': 'work on T-07'}),
        ('Grep', {'pattern': 'T-07'}), ('Bash', {'command': 'echo panel/T-07'})]
    for name, inp in texts:
        assert api.capture(project, runtime='claude', payload=tool_payload(project, name=name, inp=inp))['status'] == 'ok'
    assert [e['tarea'] for e in api.history(project)['events']] == [None] * 4
    clock[0] = now + 1
    assert api.capture(project, runtime='claude', payload=tool_payload(project, inp={'command': METER + ' start --artefacto panel/T-09'}))['status'] == 'ok'
    clock[0] = now + 20
    for name, inp in texts:
        assert api.capture(project, runtime='claude', payload=tool_payload(project, name=name, inp=inp))['status'] == 'ok'
    assert {e['tarea'] for e in api.history(project)['events'][5:]} == {'panel/T-09'}  # the window decides, never the text


def test_fix_suffix_is_normalized_and_a_subagent_inherits_the_parent_window(api, project, monkeypatch):
    now = time.time()
    clock = [now]
    monkeypatch.setattr(api.time, 'time', lambda: clock[0])
    assert api.capture(project, runtime='claude', payload=tool_payload(project, inp={'command': METER + ' start --artefacto panel/T-07-fix2'}))['status'] == 'ok'
    clock[0] = now + 30
    assert api.capture(project, runtime='claude', payload=tool_payload(project, name='Read', inp={'file_path': 'a.py'}, agent='worker-1'))['status'] == 'ok'
    assert last(api, project)['tarea'] == 'panel/T-07'
    assert api.capture(project, runtime='claude', payload=tool_payload(project, inp={'command': METER + ' start --artefacto panel/T-08'}, agent='worker-2'))['status'] == 'ok'
    clock[0] = now + 60
    # two open windows now (the parent's T-07 and worker-2's T-08): worker-2 owns exactly one -> T-08; worker-1 sees the parent's only
    assert api.capture(project, runtime='claude', payload=tool_payload(project, name='Read', inp={'file_path': 'a.py'}, agent='worker-2'))['status'] == 'ok'
    assert last(api, project)['tarea'] == 'panel/T-08'


def test_codex_without_subagent_identity_is_one_session_run_and_attributes_by_window(api, project, monkeypatch):
    now = time.time()
    clock = [now]
    monkeypatch.setattr(api.time, 'time', lambda: clock[0])
    assert api.capture(project, runtime='codex', payload=tool_payload(project, 'codex', inp={'command': METER + ' start --artefacto panel/T-07'}))['status'] == 'ok'
    clock[0] = now + 10
    assert api.capture(project, runtime='codex', payload=tool_payload(project, 'codex', name='apply_patch', inp={'command': '*** Update File: a.py'}, agent='some-agent'))['status'] == 'ok'
    history = api.history(project)
    assert len(history['runs']) == 1 and history['events'][-1]['tarea'] == 'panel/T-07'


def test_codex_mcp_tool_makes_one_attempt_without_waiting_and_others_wait(api, project, monkeypatch):
    seen = []
    monkeypatch.setattr(api, 'record', lambda proj, entry: (seen.append(entry), {'status': 'ok', 'reason': None})[1])
    assert api.capture(project, runtime='codex', payload=tool_payload(project, 'codex', name='mcp__srv__tool', inp={}))['status'] == 'ok'
    assert api.capture(project, runtime='codex', payload=tool_payload(project, 'codex'))['status'] == 'ok'
    assert api.capture(project, runtime='claude', payload=tool_payload(project, name='mcp__srv__tool', inp={}))['status'] == 'ok'
    assert [(e['runtime'], e['tool'], e['nowait'], e['resumen']) for e in seen] == [
        ('codex', 'mcp__srv__tool', True, '\u2014'), ('codex', 'Bash', False, 'git status'), ('claude', 'mcp__srv__tool', False, '\u2014')]


def test_tool_input_over_two_mib_is_counted_and_never_parsed_into_an_event(api, project):
    assert api.capture(project, runtime='claude', payload=native(project))['status'] == 'ok'
    big = tool_payload(project, tool_response={'stdout': 'x' * (2 * 1024 * 1024 + 1)})
    assert api.capture(project, runtime='claude', payload=big) == {'status': 'unavailable', 'reason': 'input_budget'}
    assert doc(project)['descartados_por_tamano'] == 1 and doc(project)['events'] == []
    medium = tool_payload(project, tool_response={'stdout': 'x' * (200 * 1024)})  # a large Read response is fine
    assert api.capture(project, runtime='claude', payload=medium)['status'] == 'ok'
    assert len(doc(project)['events']) == 1 and doc(project)['descartados_por_tamano'] == 1
    assert b'xxxxxxxx' not in events_path(project).read_bytes()
    life = native(project); life['last_assistant_message'] = 'x' * (70 * 1024)  # a lifecycle payload keeps the 64 KiB cap
    assert api.capture(project, runtime='claude', payload=life)['reason'] == 'input_budget'
    assert doc(project)['descartados_por_tamano'] == 1


def test_tool_event_creates_the_store_when_the_first_signal_is_a_tool(api, project):
    assert not _state(project).exists()
    assert api.capture(project, runtime='claude', payload=tool_payload(project))['status'] == 'ok'
    assert sorted(p.name for p in _state(project).iterdir()) == ['.gitignore', '.lock', 'events.json', 'owner.json', 'snapshot.json']
    assert api.snapshot(project)['status'] == 'ok' and api.snapshot(project)['records'] == []


def test_real_cli_records_a_tool_event_silently(api, project):
    argv = [sys.executable, '-I', '-X', 'utf8', '-B', str(SHARED / 'agent-activity-store.py'), '--runtime', 'claude', '--root', str(project)]
    p = subprocess.run(argv, input=json.dumps(tool_payload(project)).encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env=dict(os.environ), cwd=project, timeout=20)
    assert p.returncode == 0 and p.stdout == p.stderr == b''
    assert last(api, project)['tool'] == 'Bash'


# ---- panel-redesign T-42 fix1 (C-1): prefixed secrets never reach events.json nor the history -----
def test_c1_prefixed_and_argument_secrets_are_redacted_in_events_and_history(api, project):
    secrets_in = {'DB_PASSWORD=Hunter2xyz! psql -h db': b'Hunter2xyz!',
                  'curl -u admin:S3cretPw! https://x.test': b'S3cretPw!',
                  'mysql -uroot -pMyS3cret9 appdb': b'MyS3cret9'}
    for command in secrets_in:
        assert api.capture(project, runtime='claude', payload=tool_payload(project, inp={'command': command}))['status'] == 'ok'
    raw = events_path(project).read_bytes()
    shown = json.dumps(api.history(project)['events']).encode()
    for secret in secrets_in.values():
        assert secret not in raw and secret not in shown, secret
    assert raw.count(b'[secreto redactado]') == 3
