"""Owned fixtures for the common plan-review owner; no services or native runtimes."""
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace

import pytest

HERE = Path(__file__).parent
SCRIPT = HERE / 'plan-review.py'
INITIATIVE = 'docs/roadmap/2026-10-09-owned'

def load():
    if not SCRIPT.exists():
        missing = lambda *a, **k: {'schema_version': 1, 'status': 'unavailable', 'reason': 'missing_owner', 'review': None}
        return SimpleNamespace(**{name: missing for name in ('open_review', 'get_view', 'get_status', 'save_comments', 'submit_decision', 'receive_decision', 'ack_decision')})
    spec = importlib.util.spec_from_file_location('plan_review_test', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

@pytest.fixture
def owned(tmp_path):
    plan = tmp_path / INITIATIVE / 'improvement-plan.md'
    plan.parent.mkdir(parents=True)
    plan.write_bytes(b'\xef\xbb\xbf# Owned plan\r\n\r\n## Scope\r\nPrivate fixture body.\r\n')
    return SimpleNamespace(root=tmp_path, plan=plan, state=tmp_path / '.claude/plan-review', module=load())

def open_(o, **kwargs):
    return o.module.open_review(o.root, INITIATIVE, state_root=o.state, gate_key='plan-ok', **kwargs)

def ready(o):
    result = open_(o)
    assert result['status'] == 'ok', result
    return result['review']

def comment(r, text='Change the scope'):
    return [{'comment_id': 'one', 'section_id': r['sections'][-1]['section_id'], 'text': text}]

def submit(o, r, choice='approve', comments=None, revision=None):
    return o.module.submit_decision(o.root, r['review_id'], r['version'], choice,
        [] if comments is None else comments, expected_revision=r['revision'] if revision is None else revision, state_root=o.state)

def receive(o, r):
    return o.module.receive_decision(o.root, r['review_id'], r['version'], gate_key='plan-ok', state_root=o.state)

def ack(o, r):
    return o.module.ack_decision(o.root, r['review_id'], r['version'], gate_key='plan-ok',
        decision_id=r['decision']['decision_id'], delivery_id=r['delivery']['delivery_id'], state_root=o.state)

def stored(o, r):
    return o.state / ('r-' + r['review_id'] + '.json')

def test_raw_view_and_sections_bind_exact_full_redacted_content(owned):
    o = owned
    secret = 'sk-' + 'AbCd1234' * 6
    raw = ('\ufeff# Owned\r\n\r\n## Duplicate\r\nToken ' + secret + '\r\n'
        '```md\r\n## not a section\r\n```\r\n## Duplicate\r\nEmoji 🐛\u202e end\r\n').encode('utf-8')
    o.plan.write_bytes(raw)
    r = ready(o)
    assert r['version']['raw_sha256'] == hashlib.sha256(raw).hexdigest()
    assert r['complete'] is True and r['redacted'] is True and r['controls_sanitized'] is True
    assert len(r['sections']) == 3 and len({s['section_id'] for s in r['sections']}) == 3
    visible = ''.join(s['text'] for s in r['sections'])
    assert '## not a section' in visible and 'Emoji 🐛' in visible and secret not in visible
    assert r['version'] == ready(o)['version'] and r['review_id'] == ready(o)['review_id']
    assert 'Private fixture body' not in stored(o, r).read_text()
    assert secret not in stored(o, r).read_text()


@pytest.mark.parametrize('control', ['\x00', '\u202e'], ids=['nul', 'bidi'])
def test_gap_b1_c1_sanitized_plan_is_redacted_before_display(owned, control):
    token = 'sk-' + 'AbCd1234' * 6  # Synthetic credential-shaped fixture.
    raw = ('# Plan\nToken s' + control + token[1:] + '\n').encode('utf8')
    owned.plan.write_bytes(raw)
    review = ready(owned)
    assert token not in ''.join(section['text'] for section in review['sections'])
    assert review['redacted'] is True and review['controls_sanitized'] is True
    assert review['version']['raw_sha256'] == hashlib.sha256(raw).hexdigest()
    assert owned.plan.read_bytes() == raw


@pytest.mark.parametrize('control', ['\x00', '\u202e'], ids=['nul', 'bidi'])
@pytest.mark.parametrize('operation', ['save', 'submit'])
def test_gap_b1_c1_comment_roundtrip_keeps_receipts_readable(owned, control, operation):
    review = ready(owned)
    token = 'sk-' + 'AbCd1234' * 6  # Synthetic credential-shaped fixture.
    rows = comment(review, 's' + control + token[1:])
    if operation == 'save':
        result = owned.module.save_comments(owned.root, review['review_id'], review['version'], rows,
            expected_revision=review['revision'], state_root=owned.state)
    else:
        result = submit(owned, review, 'request_changes', rows)
    assert result['status'] == 'ok', result
    status = owned.module.get_status(owned.root, review['review_id'], state_root=owned.state)
    assert status['status'] == 'ok', status
    assert token not in json.dumps(result, ensure_ascii=False)
    assert token not in stored(owned, review).read_text(encoding='utf8')
    if operation == 'submit':
        received = receive(owned, result['review'])
        assert received['status'] == 'ok'
        assert ack(owned, received['review'])['status'] == 'ok'
    owned.plan.write_bytes(owned.plan.read_bytes() + b'Changed version\n')
    assert open_(owned)['status'] == 'ok'  # One receipt must not poison the inventory.

@pytest.mark.parametrize('raw,reason', [(b'', 'empty_plan'), (b'\xff', 'invalid_encoding'), (b'x' * (262144 + 1), 'plan_budget'),
    ((''.join('# Section\n' for _ in range(129))).encode(), 'section_budget')], ids=['empty', 'encoding', 'oversize', 'sections'])
def test_plan_failures_never_create_authorizing_state(owned, raw, reason):
    owned.plan.write_bytes(raw)
    result = open_(owned)
    assert result['status'] == 'unavailable' and result['reason'] == reason
    assert result['review'] is None and not owned.state.exists()

@pytest.mark.parametrize('initiative', ['../escape', '/absolute', 'docs/roadmap/*', 'docs/roadmap/2026-10-09-OWNED'])
def test_selection_scope_rejected_before_state(owned, initiative):
    result = owned.module.open_review(owned.root, initiative, state_root=owned.state)
    assert result['reason'] == 'invalid_input' and not owned.state.exists()

def test_comments_cas_and_sealed_decision(owned):
    o = owned; r = ready(o); comments = comment(r)
    changed = o.module.save_comments(o.root, r['review_id'], r['version'], comments, expected_revision=0, state_root=o.state)
    assert changed['status'] == 'ok' and changed['review']['revision'] == 1
    repeated = o.module.save_comments(o.root, r['review_id'], r['version'], comments, expected_revision=0, state_root=o.state)
    assert repeated['status'] == 'ok' and repeated['review']['revision'] == 1
    conflict = o.module.save_comments(o.root, r['review_id'], r['version'], comment(r, 'Different'), expected_revision=0, state_root=o.state)
    assert conflict['status'] == 'conflict' and conflict['reason'] == 'revision_conflict'
    decision = submit(o, changed['review'], 'request_changes', comments)
    assert decision['status'] == 'ok' and decision['review']['state'] == 'pendiente'
    duplicate = submit(o, r, 'request_changes', comments)
    assert duplicate['review']['decision'] == decision['review']['decision']
    assert submit(o, changed['review'])['reason'] == 'decision_conflict'
    assert o.module.save_comments(o.root, r['review_id'], r['version'], [], expected_revision=1, state_root=o.state)['reason'] == 'decision_sealed'

@pytest.mark.parametrize('comments,choice,reason', [([], 'request_changes', 'comments_required'),
    ([{'comment_id': 'x', 'section_id': '0' * 64, 'text': 'x'}], 'approve', 'invalid_comments'),
    ([{'comment_id': 'x', 'section_id': 'CURRENT', 'text': 'x' * 2001}], 'approve', 'comment_budget')])
def test_invalid_comments_never_freeze_decision(owned, comments, choice, reason):
    r = ready(owned)
    for item in comments:
        if item['section_id'] == 'CURRENT': item['section_id'] = r['sections'][0]['section_id']
    result = submit(owned, r, choice, comments)
    assert result['reason'] == reason
    assert json.loads(stored(owned, r).read_bytes())['decision'] is None

def test_receive_keeps_delivery_until_revalidated_idempotent_ack_and_restart(owned):
    o = owned; r = ready(o)
    assert receive(o, r)['status'] == 'waiting'
    r = submit(o, r)['review']
    r = receive(o, r)['review']; before = stored(o, r).read_bytes()
    assert r['state'] == 'entregada' and r['decision']['choice'] == 'approve'
    assert receive(o, r)['review']['delivery'] == r['delivery']
    assert stored(o, r).read_bytes() == before
    o.module = load()
    assert receive(o, r)['review']['delivery'] == r['delivery']
    consumed = ack(o, r)
    assert consumed['status'] == 'ok' and consumed['review']['state'] == 'consumida'
    assert ack(o, r)['review']['ack'] == consumed['review']['ack']
    assert receive(o, r)['review']['state'] == 'consumida'
    assert json.loads(stored(o, r).read_bytes())['decision'] == r['decision']

@pytest.mark.parametrize('phase', ['submit', 'receive', 'ack'])
def test_changed_plan_blocks_each_decision_boundary_and_retains_old_record(owned, phase):
    o = owned; r = ready(o)
    if phase in ('receive', 'ack'): r = submit(o, r)['review']
    if phase == 'ack': r = receive(o, r)['review']
    before = stored(o, r).read_bytes()
    original = o.plan.read_bytes(); o.plan.write_bytes(original + b'edit\n')
    result = {'submit': lambda: submit(o, r), 'receive': lambda: receive(o, r), 'ack': lambda: ack(o, r)}[phase]()
    assert result['status'] == 'version_changed'
    assert stored(o, r).read_bytes() == before
    assert o.module.get_status(o.root, r['review_id'], state_root=o.state)['review']['validity'] == 'version_changed'
    new = ready(o); assert new['review_id'] != r['review_id'] and new['decision'] is None
    o.plan.write_bytes(original)
    assert o.module.get_view(o.root, r['review_id'], state_root=o.state)['status'] == 'ok'

def test_gate_and_ack_identity_are_not_interchangeable(owned):
    o = owned; r = submit(o, ready(o))['review']
    result = o.module.receive_decision(o.root, r['review_id'], r['version'], gate_key='requested-review', state_root=o.state)
    assert result['reason'] == 'gate_conflict'
    r = receive(o, r)['review']
    result = o.module.ack_decision(o.root, r['review_id'], r['version'], gate_key='plan-ok', decision_id='0' * 64, delivery_id=r['delivery']['delivery_id'], state_root=o.state)
    assert result['reason'] == 'ack_conflict' and json.loads(stored(o, r).read_bytes())['state'] == 'entregada'

def test_poll_is_read_only_and_unknown_id_has_no_state_effect(owned):
    o = owned; r = ready(o)
    before = {p.name: p.read_bytes() for p in o.state.iterdir() if p.is_file()}
    assert o.module.get_status(o.root, r['review_id'], state_root=o.state)['status'] == 'ok'
    assert o.module.get_view(o.root, 'f' * 64, state_root=o.state)['reason'] == 'review_not_found'
    assert before == {p.name: p.read_bytes() for p in o.state.iterdir() if p.is_file()}

def test_existing_unowned_state_and_foreign_record_are_preserved(owned):
    o = owned; o.state.mkdir(parents=True); sentinel = o.state / 'foreign.txt'; sentinel.write_bytes(b'owned by someone else')
    assert open_(o)['reason'] == 'unowned_state'
    assert sentinel.read_bytes() == b'owned by someone else'
    sentinel.unlink(); o.state.rmdir()
    r = ready(o); target = stored(o, r); target.write_bytes(b'{"owner":"foreign"}')
    assert submit(o, r)['reason'] == 'invalid_state' and target.read_bytes() == b'{"owner":"foreign"}'

def test_state_scope_deadline_and_link_rejections(owned):
    o = owned
    assert o.module.open_review(o.root, INITIATIVE, state_root=o.root / 'other')['reason'] == 'state_scope'
    assert open_(o, deadline=time.monotonic() - 1)['reason'] == 'deadline_expired'
    assert not o.state.exists()
    r = ready(o); target = stored(o, r); alias = o.root / 'alias'; os.link(target, alias)
    assert submit(o, r)['reason'] == 'unsafe_state'
    assert target.read_bytes() == alias.read_bytes()

def test_deadline_at_commit_and_fsync_failure_do_not_claim_success(owned, monkeypatch):
    o = owned; r = ready(o); before = stored(o, r).read_bytes()
    monkeypatch.setattr(o.module.os, 'fsync', lambda *_: (_ for _ in ()).throw(OSError('PRIVATE_IO')))
    result = submit(o, r)
    assert result['status'] == 'unavailable' and result['reason'] == 'durability_degraded'
    assert stored(o, r).read_bytes() == before and 'PRIVATE_IO' not in json.dumps(result)

def test_record_and_response_budgets_do_not_truncate_or_drop_prior_receipt(owned, monkeypatch):
    o = owned; r = ready(o); before = stored(o, r).read_bytes()
    monkeypatch.setattr(o.module, 'MAX_RESPONSE_BYTES', 32)
    assert submit(o, r)['reason'] == 'response_budget'
    assert stored(o, r).read_bytes() == before
    monkeypatch.setattr(o.module, 'MAX_RESPONSE_BYTES', 512 * 1024)
    monkeypatch.setattr(o.module, 'MAX_RECORD_BYTES', 32)
    assert submit(o, r)['reason'] == 'state_budget'
    assert stored(o, r).read_bytes() == before

@pytest.mark.parametrize('runtime', ['claude-code', 'codex', 'opencode'])
def test_common_cli_pipeline_and_registration_are_runtime_independent(owned, runtime):
    o = owned
    opened = open_(o, consumer={'caller_id': 'fixture-' + runtime, 'runtime': runtime})
    assert opened['status'] == 'ok', opened
    r = opened['review']
    assert r['consumer_registration']['runtime'] == runtime
    def cli(operation, body=None, extra=()):
        args = [sys.executable, '-X', 'utf8', '-B', str(SCRIPT), operation, '--project', str(o.root), '--state-root', str(o.state), '--review-id', r['review_id'], '--json', *extra]
        p = subprocess.run(args, input='' if body is None else json.dumps(body), text=True, encoding='utf-8', errors='replace', capture_output=True, timeout=10)
        return p.returncode, json.loads(p.stdout)
    version_args = ['--raw-sha256', r['version']['raw_sha256'], '--view-sha256', r['version']['view_sha256'], '--gate-key', 'plan-ok']
    assert cli('status')[0] == 0
    code, decision = cli('submit', {'version': r['version'], 'choice': 'approve', 'comments': [], 'expected_revision': 0})
    assert code == 0 and decision['review']['decision']['choice'] == 'approve'
    code, delivered = cli('receive', extra=version_args)
    d = delivered['review']
    assert code == 0 and d['state'] == 'entregada'
    code, consumed = cli('ack', extra=[*version_args, '--decision-id', d['decision']['decision_id'], '--delivery-id', d['delivery']['delivery_id']])
    assert code == 0 and consumed['review']['state'] == 'consumida'
    assert consumed['review']['consumer_registration']['runtime'] == runtime
@pytest.mark.parametrize('fault', ['comment_shape', 'comment_secret', 'consumer_shape', 'timestamp', 'empty_changes'])
def test_corrupted_nested_state_cannot_be_served_or_consumed(owned, fault):
    o = owned; r = ready(o)
    data = json.loads(stored(o, r).read_bytes())
    if fault == 'comment_shape': data['draft_comments'] = [{'extra': 'foreign'}]
    elif fault == 'comment_secret': data['draft_comments'] = comment(r, 'sk-' + 'AbCd1234' * 6)
    elif fault == 'consumer_shape': data['consumer_registration'] = {'runtime': 'foreign', 'caller_id': 'x'}
    elif fault == 'timestamp': data['created_at'] = 'not a timestamp'
    else:
        data['decision'] = {'decision_id': 'a' * 64, 'choice': 'request_changes', 'comments': [], 'submitted_at': data['created_at']}
    stored(o, r).write_text(json.dumps(data), encoding='utf-8')
    before = stored(o, r).read_bytes()
    result = o.module.get_status(o.root, r['review_id'], state_root=o.state)
    assert result['reason'] == 'invalid_state' and result['review'] is None
    assert stored(o, r).read_bytes() == before

def test_directory_creation_race_never_adopts_foreign_state(owned, monkeypatch):
    o = owned; original = Path.mkdir
    def race(path, *args, **kwargs):
        if path == o.state:
            original(path, *args, **kwargs)
            (path / 'foreign.txt').write_bytes(b'foreign')
            raise FileExistsError('concurrent foreign directory')
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, 'mkdir', race)
    result = open_(o)
    assert result['status'] == 'unavailable' and not (o.state / 'owner.json').exists()
    assert (o.state / 'foreign.txt').read_bytes() == b'foreign'

def test_plan_edit_during_comment_preparation_is_rechecked_before_commit(owned, monkeypatch):
    o = owned; r = ready(o); before = stored(o, r).read_bytes(); original = o.module._comments
    def edit(*args, **kwargs):
        result = original(*args, **kwargs)
        o.plan.write_bytes(o.plan.read_bytes() + b'late mutation\n')
        return result
    monkeypatch.setattr(o.module, '_comments', edit)
    assert submit(o, r, comments=comment(r))['status'] == 'version_changed'
    assert stored(o, r).read_bytes() == before

def test_cross_process_lock_contention_prevents_mutation(owned):
    o = owned; r = ready(o); lock = o.state / '.lock'
    code = "import os,sys,time;f=open(sys.argv[1],'r+b');\nif os.name=='nt':\n import msvcrt;msvcrt.locking(f.fileno(),msvcrt.LK_NBLCK,1)\nelse:\n import fcntl;fcntl.flock(f.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)\nprint('locked',flush=True);sys.stdin.readline()"
    process = subprocess.Popen([sys.executable, '-X', 'utf8', '-B', '-c', code, str(lock)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace')
    try:
        assert process.stdout.readline().strip() == 'locked'
        before = stored(o, r).read_bytes(); started = time.monotonic()
        assert submit(o, r)['reason'] == 'state_busy'
        assert time.monotonic() - started < 0.5 and stored(o, r).read_bytes() == before
    finally:
        process.communicate('\n', timeout=5)
    assert submit(o, r)['status'] == 'ok'
def test_foreign_record_in_owned_namespace_is_not_adopted_by_new_open(owned):
    o = owned; r = ready(o)
    foreign = o.state / ('r-' + 'f' * 64 + '.json'); foreign.write_bytes(b'{"owner":"foreign"}')
    o.plan.write_bytes(o.plan.read_bytes() + b'new version\n')
    before = {p.name: p.read_bytes() for p in o.state.iterdir()}
    result = open_(o)
    assert result['reason'] == 'invalid_state'
    assert before == {p.name: p.read_bytes() for p in o.state.iterdir()}

def test_two_cli_submitters_cannot_persist_contradictory_decisions(owned):
    from concurrent.futures import ThreadPoolExecutor
    import threading
    o = owned; r = ready(o); barrier = threading.Barrier(2)
    args = [sys.executable, '-X', 'utf8', '-B', str(SCRIPT), 'submit', '--project', str(o.root), '--state-root', str(o.state), '--review-id', r['review_id'], '--json']
    def run(choice):
        body = json.dumps({'version': r['version'], 'choice': choice, 'comments': comment(r) if choice == 'request_changes' else [], 'expected_revision': 0})
        barrier.wait(timeout=5)
        p = subprocess.run(args, input=body, text=True, encoding='utf-8', errors='replace', capture_output=True, timeout=10)
        return choice, json.loads(p.stdout)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(run, ['approve', 'request_changes']))
    assert sum(result['status'] == 'ok' for _, result in results) == 1
    persisted = json.loads(stored(o, r).read_bytes())
    winner = next(choice for choice, result in results if result['status'] == 'ok')
    assert persisted['decision']['choice'] == winner and persisted['revision'] == 1
    loser = next(choice for choice, result in results if result['status'] != 'ok')
    assert submit(o, r, loser, comment(r) if loser == 'request_changes' else [])['reason'] == 'decision_conflict'
    assert len(list(o.state.glob('r-*.json'))) == 1

@pytest.mark.parametrize('body,reason', [('{"version":{},"version":{}}', 'invalid_state'),
    ('{"x":NaN}', 'invalid_state'), ('[]', 'invalid_input'), ('x' * 16385, 'request_budget')], ids=['duplicate', 'nan', 'shape', 'bytes'])
def test_cli_rejects_malformed_or_oversize_json_without_mutation(owned, body, reason):
    o = owned; r = ready(o); before = stored(o, r).read_bytes()
    args = [sys.executable, '-X', 'utf8', '-B', str(SCRIPT), 'submit', '--project', str(o.root), '--state-root', str(o.state), '--review-id', r['review_id'], '--json']
    p = subprocess.run(args, input=body, text=True, encoding='utf-8', errors='replace', capture_output=True, timeout=10)
    result = json.loads(p.stdout)
    assert p.returncode == 3 and result['reason'] == reason and result['review'] is None
    assert stored(o, r).read_bytes() == before

def test_deadline_expires_during_comment_validation_before_any_write(owned, monkeypatch):
    o = owned; r = ready(o); before = stored(o, r).read_bytes(); original = o.module._comments
    clock = [100.0]
    monkeypatch.setattr(o.module.time, 'monotonic', lambda: clock[0])
    def slow(value, view):
        result = original(value, view)
        if view is not None: clock[0] = 104.0
        return result
    monkeypatch.setattr(o.module, '_comments', slow)
    result = o.module.submit_decision(o.root, r['review_id'], r['version'], 'approve', [], expected_revision=0, state_root=o.state, deadline=103.0)
    assert result['reason'] == 'deadline_expired' and stored(o, r).read_bytes() == before

def test_registered_consumer_is_metadata_and_missing_redactor_fails_closed(owned, monkeypatch):
    o = owned
    r = ready(o)
    assert r['consumer_registration'] is None and r['state'] == 'pendiente'
    original = o.module._helper
    def absent(name):
        if name == 'redact.py': raise ImportError('PRIVATE_HELPER_DETAIL')
        return original(name)
    monkeypatch.setattr(o.module, '_helper', absent)
    before = stored(o, r).read_bytes()
    result = submit(o, r)
    assert result['reason'] == 'helper_unavailable' and 'PRIVATE_' not in json.dumps(result)
    assert stored(o, r).read_bytes() == before

@pytest.mark.parametrize('fault', ['missing', 'encoding', 'empty'])
def test_unavailable_plan_serves_history_readonly_and_never_consumes(owned, fault):
    o = owned; r = receive(o, submit(o, ready(o))['review'])['review']
    before = {p.name: p.read_bytes() for p in o.state.iterdir()}
    if fault == 'missing': o.plan.unlink()
    else: o.plan.write_bytes(b'\xff' if fault == 'encoding' else b'')
    for fn in (o.module.get_status, o.module.get_view):
        result = fn(o.root, r['review_id'], state_root=o.state)
        assert result['status'] == 'unavailable' and result['review'] is not None
        history = result['review']
        assert history['validity'] == 'unavailable' and history['complete'] is False
        assert history['current_version'] is None and history['redacted'] is None and history['controls_sanitized'] is None
        assert history['decision'] == r['decision'] and history['delivery'] == r['delivery'] and history['ack'] is None
        assert history.get('sections', []) == []
    for result in (submit(o, r), receive(o, r), ack(o, r)):
        assert result['status'] == 'unavailable' and result['review'] is None
    assert before == {p.name: p.read_bytes() for p in o.state.iterdir()}

def test_cli_entrypoint_forms_bind_transport_and_exit_statuses(owned, monkeypatch, capsys):
    o = owned
    def cli(operation, body='', extra=()):
        monkeypatch.setattr(sys, 'stdin', io.TextIOWrapper(io.BytesIO(body.encode('utf-8')), encoding='utf-8'))
        code = o.module.main([operation, '--project', str(o.root), '--state-root', str(o.state), '--json', *extra])
        return code, json.loads(capsys.readouterr().out)
    code, opened = cli('open', extra=['--initiative', INITIATIVE, '--gate-key', 'plan-ok', '--caller-id', 'local-cli', '--runtime', 'codex'])
    r = opened['review']; selection = ['--review-id', r['review_id']]
    assert code == 0 and r['consumer_registration']['caller_id'] == 'local-cli'
    assert cli('view', extra=selection)[1]['review']['sections'] == r['sections']
    assert 'sections' not in cli('status', extra=selection)[1]['review']
    version = ['--raw-sha256', r['version']['raw_sha256'], '--view-sha256', r['version']['view_sha256'], '--gate-key', 'plan-ok']
    assert cli('receive', extra=selection + version)[1]['status'] == 'waiting'
    payload = {'version': r['version'], 'comments': comment(r), 'expected_revision': 0}
    code, saved = cli('comments', json.dumps(payload), selection)
    assert code == 0 and saved['review']['revision'] == 1
    payload.update(expected_revision=1, choice='request_changes')
    code, submitted = cli('submit', json.dumps(payload), selection)
    assert code == 0 and submitted['review']['decision']['choice'] == 'request_changes'
    payload['choice'] = 'approve'
    assert cli('submit', json.dumps(payload), selection)[0] == 2
    assert cli('submit', '{"x":NaN}', selection)[0] == 3
    code, delivered = cli('receive', extra=selection + version)
    d = delivered['review']
    assert code == 0 and d['state'] == 'entregada'
    code, consumed = cli('ack', extra=selection + version + ['--decision-id', d['decision']['decision_id'], '--delivery-id', d['delivery']['delivery_id']])
    assert code == 0 and consumed['review']['state'] == 'consumida'
