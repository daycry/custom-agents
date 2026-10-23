#!/usr/bin/env python3
"""Explicit local plan review receipts. Delivery repeats until idempotent ack.

Hashes bind observed bytes and the redacted view, not human identity, semantic
approval, an atomic source snapshot or ABA detection. No workflow is launched.
"""
import argparse
import contextlib
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import secrets
import stat
import sys
import time

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001

# Querying a project-local kit must not materialize helper bytecode in the project.
sys.dont_write_bytecode = True


HERE = Path(__file__).resolve().parent
OWNER = 'custom-agents.plan-review'
VIEW_VERSION = 'plan-text-v1'
MAX_PLAN_BYTES = 256 * 1024
MAX_RECORD_BYTES = 96 * 1024
MAX_REQUEST_BYTES = 16 * 1024
MAX_RESPONSE_BYTES = 512 * 1024
MAX_RECORDS = 64
MAX_REMINDERS = 8
MAX_FEEDBACK_BYTES = 48 * 1024
MAX_HISTORY_BYTES = 64 * 1024
MAX_SAFE_REVISION = 9007199254740991
HASH = re.compile(r'[a-f0-9]{64}')
INITIATIVE = re.compile(r'docs/roadmap/[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z0-9]+(?:-[a-z0-9]+)*')
CONTROLS = re.compile(r'[\x00-\x08\x0b-\x1f\x7f-\x9f\u2028\u2029\u202a-\u202e\u2066-\u2069]')
RECORD_KEYS = {'schema_version', 'owner', 'review_id', 'scope_id', 'initiative', 'artifact', 'gate_key', 'version', 'created_at', 'revision', 'state', 'consumer_registration', 'draft_comments', 'decision', 'delivery', 'ack'}

def _mkdir_private(path, **kwargs):
    """0o700 en POSIX. En Windows se heredan los permisos del padre: Python 3.13 convierte
    0o700 en una ACL explícita que deja fuera al usuario restringido del sandbox de Codex."""
    if os.name == 'nt':
        path.mkdir(**kwargs)
    else:
        path.mkdir(mode=0o700, **kwargs)


class _Failure(Exception):
    def __init__(self, reason, status='unavailable'):
        self.reason, self.status = reason, status

def _need(condition, reason='invalid_input', status='unavailable'):
    if not condition: raise _Failure(reason, status)

def _json(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(',', ':')).encode('utf-8')

def _digest(value):
    return hashlib.sha256(_json(value)).hexdigest()

def _hash(value):
    return isinstance(value, str) and HASH.fullmatch(value) is not None

def _strict(raw):
    def pairs(items):
        obj = {}
        for key, value in items:
            _need(key not in obj, 'invalid_state')
            obj[key] = value
        return obj
    def constant(_): raise _Failure('invalid_state')
    return json.loads(raw.decode('utf-8'), object_pairs_hook=pairs, parse_constant=constant)

def _timestamp(value):
    if not isinstance(value, str) or re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,6})?Z', value) is None:
        return False
    try: datetime.fromisoformat(value.replace('Z', '+00:00')); return True
    except ValueError: return False

def _now():
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

def _deadline(value):
    started = time.monotonic()
    if value is None: return started + 3
    _need(type(value) in (int, float) and math.isfinite(value), 'deadline_expired')
    _guard(value)
    return value

def _guard(deadline):
    _need(time.monotonic() < deadline, 'deadline_expired')

def _helper(filename):
    spec = importlib.util.spec_from_file_location('plan_review_' + filename.replace('-', '_'), HERE / filename)
    _need(spec is not None and spec.loader is not None, 'helper_unavailable')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

_STATE_HELPER = None

def _storage_helper():
    global _STATE_HELPER
    if _STATE_HELPER is None:
        _STATE_HELPER = _helper('local-state.py')
    return _STATE_HELPER

def _state_io(reader):
    return _storage_helper().StateIO(reader, _need, _guard,
        maximum=MAX_RECORD_BYTES, sync=_sync_dir)

def _dirs(path, reader):
    return _state_io(reader).dirs(path)

def _file(path, reader):
    return _state_io(reader).file(path)

def _read(path, reader, maximum):
    raw, signature = _state_io(reader).read(path, maximum)
    return _strict(raw), signature
_REDACTORS = {}

def _redactor():
    """`redact.py`, executed once per (size, mtime) of the file: a many-initiative summary validated every record
    (and every plan) with a fresh load. A changed file loads again; a failing load is never cached."""
    info = (HERE / 'redact.py').stat()
    key = (info.st_size, info.st_mtime_ns)
    module = _REDACTORS.get(key)
    if module is None:
        _REDACTORS.clear()
        module = _REDACTORS[key] = _helper('redact.py')
    return module

def _view(project, initiative, reader, deadline):
    _guard(deadline)
    relative = initiative + '/improvement-plan.md'
    row = reader.read_bytes(project, relative, max_bytes=MAX_PLAN_BYTES, include_digest=True)
    reason = {'too_large': 'plan_budget', 'not_found': 'plan_missing'}.get(row['status'], 'plan_unavailable')
    _need(row['status'] == 'ok', reason)
    try: original = row['data'].decode('utf-8-sig').replace('\r\n', '\n')
    except UnicodeError: raise _Failure('invalid_encoding') from None
    code = reader.read_bytes(HERE, 'redact.py', max_bytes=256 * 1024, include_digest=True)
    _need(code['status'] == 'ok', 'helper_unavailable')
    redactor = _redactor()
    sanitized = CONTROLS.sub('', original)
    text = redactor.redactar(sanitized)
    _need(bool(text.strip()), 'empty_plan')
    sections, lines, title, level, fence = [], [], 'Plan', 0, None
    def finish():
        if not lines: return
        body = ''.join(lines)
        identifier = _digest({'raw_sha256': row['sha256'], 'view_version': VIEW_VERSION,
                              'index': len(sections), 'title': title, 'text': body})
        sections.append({'section_id': identifier, 'title': title, 'level': level, 'text': body})
    for line in text.splitlines(keepends=True):
        mark = re.match(r'^[ ]{0,3}(`{3,}|~{3,})(.*)', line)
        heading = re.match(r'^[ ]{0,3}(#{1,6})[ \t]+(.*?)[ \t]*(?:\n|$)', line) if fence is None and mark is None else None
        if heading:
            finish(); lines = []; level = len(heading[1]); title = heading[2]
        lines.append(line)
        if mark:
            if fence is None: fence = (mark[1][0], len(mark[1]))
            elif mark[1][0] == fence[0] and len(mark[1]) >= fence[1] and not mark[2].strip(): fence = None
    finish()
    _need(len(sections) <= 128, 'section_budget')
    view = {'view_version': VIEW_VERSION, 'redactor_sha256': code['sha256'], 'redacted': text != sanitized,
            'controls_sanitized': sanitized != original, 'sections': sections}
    _guard(deadline)
    return {'version': {'raw_sha256': row['sha256'], 'view_sha256': _digest(view), 'view_version': VIEW_VERSION},
            **view, 'complete': True}

def _version(value):
    _need(type(value) is dict and set(value) == {'raw_sha256', 'view_sha256', 'view_version'}
          and _hash(value['raw_sha256']) and _hash(value['view_sha256']) and value['view_version'] == VIEW_VERSION)

def _review_id(marker, initiative, version, gate):
    return _digest({'scope_id': marker['scope_id'], 'initiative': initiative, 'artifact': 'improvement-plan.md',
                    'raw_sha256': version['raw_sha256'], 'view_sha256': version['view_sha256'], 'gate_key': gate})

def _sync_dir(path):
    return _storage_helper().sync_dir(path)
def _durable(path):
    try:
        with path.open('r+b') as handle: os.fsync(handle.fileno())
        _sync_dir(path.parent)
    except OSError: raise _Failure('durability_degraded') from None

def _write(path, value, reader, deadline, expected=None):
    return _state_io(reader).write(path, _json(value), deadline, expected=expected)
def _marker(project, state, reader, deadline, initialize):
    _dirs(project, reader)
    info = project.lstat()
    root_key = _digest({'path': os.path.normcase(str(project)), 'identity': [info.st_dev, info.st_ino]})
    if not state.exists():
        _need(initialize, 'review_not_found')
        if not state.parent.exists(): _mkdir_private(state.parent)
        _dirs(state.parent, reader)
        try: _mkdir_private(state)
        except FileExistsError: raise _Failure('state_busy') from None
        # A concurrent initializer may win; missing owner is never adopted on later calls.
        marker = {'schema_version': 1, 'owner': OWNER, 'scope_id': secrets.token_hex(32), 'root_key': root_key}
        try: _write(state / 'owner.json', marker, reader, deadline)
        except FileExistsError: pass
    _dirs(state, reader)
    _need((state / 'owner.json').exists(), 'unowned_state')
    marker, _ = _read(state / 'owner.json', reader, 4096)
    _need(type(marker) is dict and set(marker) == {'schema_version', 'owner', 'scope_id', 'root_key'}
          and type(marker['schema_version']) is int and marker['schema_version'] == 1 and marker['owner'] == OWNER
          and _hash(marker['scope_id']) and marker['root_key'] == root_key, 'unowned_state')
    return marker

@contextlib.contextmanager
def _locked(state, reader, deadline, initialize):
    with _state_io(reader).locked(state, deadline, initialize):
        yield
def _inventory(state, reader, marker, deadline, records=None):
    listing = reader.list_names(state.parent, state.name, max_entries=MAX_RECORDS + 18)
    _need(listing['status'] == 'ok' and listing['complete'], 'state_budget')
    for name in listing['names']:
        _need(name in {'owner.json', '.lock'} or re.fullmatch(r'r-[a-f0-9]{64}\.json', name) is not None
              or re.fullmatch(r'\.tmp-[a-zA-Z0-9_-]+', name) is not None, 'unowned_state')
        _guard(deadline); _file(state / name, reader)
        if name.startswith('r-'):
            record, _ = _record(state / name, marker, reader)
            if records is not None: records.append(record)
    return sum(name.startswith('r-') for name in listing['names'])

def _record(path, marker, reader):
    try: record, signature = _read(path, reader, 96 * 1024)
    except FileNotFoundError: raise _Failure('review_not_found') from None
    try:
        _need(type(record) is dict and type(record.get('schema_version')) is int
              and record['schema_version'] in (1, 2)
              and set(record) == RECORD_KEYS | ({'feedback'} if record['schema_version'] == 2 else set()), 'invalid_state')
        _version(record['version'])
        _need(record['owner'] == OWNER
              and record['scope_id'] == marker['scope_id'] and type(record['initiative']) is str
              and INITIATIVE.fullmatch(record['initiative']) is not None and record['artifact'] == 'improvement-plan.md'
              and record['gate_key'] in ('plan-ok', 'requested-review') and type(record['revision']) is int
              and 0 <= record['revision'] <= MAX_SAFE_REVISION and record['state'] in ('pendiente', 'entregada', 'consumida')
              and record['review_id'] == _review_id(marker, record['initiative'], record['version'], record['gate_key'])
              and path.name == 'r-' + record['review_id'] + '.json', 'invalid_state')
        _need(_timestamp(record['created_at']) and _comments(record['draft_comments'], None) == record['draft_comments'], 'invalid_state')
        consumer = record['consumer_registration']
        if consumer is not None:
            _need(type(consumer) is dict and set(consumer) == {'caller_id', 'runtime', 'registered_at'}
                  and isinstance(consumer['caller_id'], str) and re.fullmatch(r'[A-Za-z0-9_-]{1,128}', consumer['caller_id']) is not None
                  and consumer['runtime'] in ('claude-code', 'codex', 'opencode') and _timestamp(consumer['registered_at']), 'invalid_state')
        decision, delivery, ack = record['decision'], record['delivery'], record['ack']
        if decision is not None:
            _need(type(decision) is dict and set(decision) == {'decision_id', 'choice', 'comments', 'submitted_at'}
                  and _hash(decision['decision_id']) and decision['choice'] in ('approve', 'request_changes')
                  and decision['comments'] == record['draft_comments'] and _timestamp(decision['submitted_at'])
                  and (decision['choice'] == 'approve' or bool(decision['comments'])), 'invalid_state')
        if delivery is not None:
            _need(decision is not None and type(delivery) is dict and set(delivery) == {'delivery_id', 'delivered_at'}
                  and _hash(delivery['delivery_id']) and _timestamp(delivery['delivered_at']), 'invalid_state')
        if ack is not None:
            _need(delivery is not None and type(ack) is dict and set(ack) == {'decision_id', 'delivery_id', 'consumed_at'}
                  and ack['decision_id'] == decision['decision_id'] and ack['delivery_id'] == delivery['delivery_id']
                  and _timestamp(ack['consumed_at']), 'invalid_state')
        _need((record['state'] == 'pendiente' and delivery is None and ack is None)
              or (record['state'] == 'entregada' and delivery is not None and ack is None)
              or (record['state'] == 'consumida' and ack is not None), 'invalid_state')
        if record['schema_version'] == 2: _validate_feedback(record)
    except (KeyError, TypeError, ValueError, _Failure): raise _Failure('invalid_state') from None
    return record, signature

def _projection(record, view, validity='current', include_view=True, history=None):
    result = {key: value for key, value in record.items() if key not in {'owner', 'schema_version', 'scope_id'}}
    result.update(validity=validity, observed_at=_now())
    result['feedback'] = _feedback_projection(record)
    result['feedback_history'] = history if history is not None else {'schema_version': 1, 'complete': True, 'reviews': []}
    if validity == 'unavailable':
        result.update(complete=False, redacted=None, controls_sanitized=None, current_version=None)
        if include_view: result['sections'] = []
    if view is not None:
        result.update(complete=view['complete'], redacted=view['redacted'], controls_sanitized=view['controls_sanitized'],
                      current_version=view['version'])
        if include_view and validity == 'current': result['sections'] = view['sections']
    return result

def _envelope(status='ok', reason=None, review=None):
    result = {'schema_version': 1, 'status': status, 'reason': reason, 'review': review}
    # Drop whole optional history rows; never truncate an authorizing view/result.
    if review is not None and review.get('feedback_history') is not None:
        history = review['feedback_history']
        while len(_json(result)) > MAX_RESPONSE_BYTES and history['reviews']:
            history['reviews'].pop(); history['complete'] = False
        if len(_json(result)) > MAX_RESPONSE_BYTES: review['feedback_history'] = None
    _need(len(_json(result)) <= MAX_RESPONSE_BYTES, 'response_budget')
    return result

def _comments(value, view):
    _need(type(value) is list and len(value) <= 20, 'comment_budget')
    allowed = {s['section_id'] for s in view['sections']} if view is not None else None; seen = set(); cleaned = []
    redactor = _redactor()
    for item in value:
        _need(type(item) is dict and set(item) == {'comment_id', 'section_id', 'text'}, 'invalid_comments')
        identifier = item['comment_id']
        _need(type(identifier) is str and re.fullmatch(r'[A-Za-z0-9_-]{1,64}', identifier) is not None
              and identifier not in seen and _hash(item['section_id']) and (allowed is None or item['section_id'] in allowed) and type(item['text']) is str, 'invalid_comments')
        _need(len(item['text']) <= 2000, 'comment_budget')
        text = redactor.redactar(CONTROLS.sub('', item['text'].replace('\r\n', '\n')))
        _need(bool(text.strip()), 'invalid_comments')
        _need(len(text) <= 2000, 'comment_budget')
        seen.add(identifier); cleaned.append({'comment_id': identifier, 'section_id': item['section_id'], 'text': text})
    _need(sum(len(c['text'].encode('utf-8')) for c in cleaned) <= 10 * 1024 and len(_json(cleaned)) <= MAX_REQUEST_BYTES - 1024, 'comment_budget')
    return cleaned

def _empty_feedback():
    return {'schema_version': 1, 'results': [], 'verifications': []}

def _producer(value, stored=False):
    keys = {'caller_id', 'runtime', 'actor_id'} | ({'identity_basis'} if stored else set())
    _need(type(value) is dict and set(value) == keys and type(value['caller_id']) is str
          and re.fullmatch(r'[A-Za-z0-9_-]{1,128}', value['caller_id']) is not None
          and value['runtime'] in ('claude-code', 'codex', 'opencode')
          and (value['actor_id'] is None or _hash(value['actor_id']))
          and (not stored or value['identity_basis'] == 'declared'), 'invalid_feedback')
    return {**value, 'identity_basis': 'declared'}

def _feedback_text(value, verification=False):
    _need(type(value) is str, 'invalid_feedback')
    characters, maximum = (500, 1024) if verification else (1000, 2048)
    _need(len(value) <= characters and len(value.encode('utf8')) <= maximum, 'feedback_text_budget')
    normalized = value.replace('\r\n', '\n')
    sanitized = CONTROLS.sub('', normalized)
    text = _redactor().redactar(sanitized)
    _need(verification or bool(text.strip()), 'invalid_feedback')
    _need(len(text) <= characters and len(text.encode('utf8')) <= maximum, 'feedback_text_budget')
    return text, {'redacted': text != sanitized, 'controls_sanitized': sanitized != normalized}

def _feedback_limits(feedback):
    _need(len(feedback['results']) <= 40 and len(feedback['verifications']) <= 40
          and sum(len(row['response_text'].encode('utf8')) for row in feedback['results']) <= 16384
          and sum(len(row['note'].encode('utf8')) for row in feedback['verifications']) <= 4096
          and len(_json(feedback)) <= MAX_FEEDBACK_BYTES, 'feedback_budget')

def _validate_feedback(record):
    feedback = record['feedback']
    _need(type(feedback) is dict and set(feedback) == {'schema_version', 'results', 'verifications'}
          and type(feedback['schema_version']) is int and feedback['schema_version'] == 1
          and type(feedback['results']) is list and type(feedback['verifications']) is list, 'invalid_state')
    _need(all(type(row) is dict and type(row.get('response_text')) is str for row in feedback['results'])
          and all(type(row) is dict and type(row.get('note')) is str for row in feedback['verifications']), 'invalid_state')
    _feedback_limits(feedback)
    if not feedback['results'] and not feedback['verifications']: return
    _need(record['state'] == 'consumida' and record['ack'] is not None, 'invalid_state')
    comments = {row['comment_id'] for row in record['decision']['comments']}
    ids, latest, counts, results, verified = set(), {}, {}, {}, set()
    common = {'comment_id', 'producer', 'recorded_at', 'text_flags'}
    for row in feedback['results']:
        _need(type(row) is dict and set(row) == common | {'result_id', 'supersedes_result_id', 'disposition', 'response_text', 'artifact_observation'}, 'invalid_state')
        _need(_hash(row['result_id']) and row['result_id'] not in ids and row['comment_id'] in comments
              and row['disposition'] in ('addressed', 'not_applied', 'needs_clarification')
              and _timestamp(row['recorded_at']), 'invalid_state')
        _producer(row['producer'], True)
        _need(_feedback_text(row['response_text'])[0] == row['response_text'], 'invalid_state')
        _need(type(row['text_flags']) is dict and set(row['text_flags']) == {'redacted', 'controls_sanitized'}
              and all(type(v) is bool for v in row['text_flags'].values()), 'invalid_state')
        key = row['comment_id']; count = counts.get(key, 0)
        _need(count < 2 and row['supersedes_result_id'] == latest.get(key), 'invalid_state')
        observation = row['artifact_observation']
        _need(type(observation) is dict and set(observation) == {'status', 'version', 'observed_at'}
              and observation['status'] in ('available', 'unavailable') and _timestamp(observation['observed_at']), 'invalid_state')
        if observation['status'] == 'available': _version(observation['version'])
        else: _need(observation['version'] is None, 'invalid_state')
        ids.add(row['result_id']); latest[key] = row['result_id']; counts[key] = count+1; results[row['result_id']] = row
    for row in feedback['verifications']:
        _need(type(row) is dict and set(row) == common | {'verification_id', 'result_id', 'assessment', 'note', 'basis'}, 'invalid_state')
        _need(_hash(row['verification_id']) and row['verification_id'] not in ids
              and row['result_id'] in results and row['result_id'] not in verified
              and row['comment_id'] == results[row['result_id']]['comment_id']
              and row['assessment'] in ('confirmed', 'not_confirmed')
              and row['basis'] == 'human_instruction_declared' and _timestamp(row['recorded_at']), 'invalid_state')
        _producer(row['producer'], True)
        _need(_feedback_text(row['note'], True)[0] == row['note'], 'invalid_state')
        _need(type(row['text_flags']) is dict and set(row['text_flags']) == {'redacted', 'controls_sanitized'}
              and all(type(v) is bool for v in row['text_flags'].values()), 'invalid_state')
        ids.add(row['verification_id']); verified.add(row['result_id'])

def _feedback_projection(record):
    feedback = record.get('feedback', _empty_feedback())
    comments = {row['comment_id']: row['section_id'] for row in (record['decision']['comments'] if record['decision'] else [])}
    return {'schema_version': 1, **{key: [{**row, 'section_id': comments[row['comment_id']]} for row in feedback[key]]
                                   for key in ('results', 'verifications')}}

def _feedback_history(record, inventory):
    eligible = [r for r in inventory if r['review_id'] != record['review_id']
                and all(r[key] == record[key] for key in ('scope_id', 'initiative', 'artifact', 'gate_key'))
                and (r.get('feedback', _empty_feedback())['results'] or r.get('feedback', _empty_feedback())['verifications'])]
    eligible.sort(key=lambda row: row['review_id'])
    eligible.sort(key=lambda row: datetime.fromisoformat(row['created_at'].replace('Z', '+00:00')), reverse=True)
    history = {'schema_version': 1, 'complete': True, 'reviews': []}
    for row in eligible:
        item = {key: row[key] for key in ('review_id', 'version', 'created_at', 'revision', 'state')}
        item.update(decision_id=row['decision']['decision_id'], delivery_id=row['delivery']['delivery_id'],
                    consumed_at=row['ack']['consumed_at'], comments=row['decision']['comments'], feedback=_feedback_projection(row))
        if len(history['reviews']) >= 8 or len(_json({**history, 'reviews': [*history['reviews'], item]})) > MAX_HISTORY_BYTES:
            history['complete'] = False; break
        history['reviews'].append(item)
    return history

def _observe_artifact(project, record, reader, deadline):
    _guard(deadline)
    # Fail closed on path/reader failures; absence/encoding/budget is an honest unavailable observation.
    checked = reader.read_bytes(project, record['initiative']+'/improvement-plan.md', max_bytes=MAX_PLAN_BYTES)
    _need(checked['status'] in ('ok', 'not_found', 'too_large'), 'unsafe_state')
    observation = {'status': 'unavailable', 'version': None, 'observed_at': _now()}
    if checked['status'] != 'ok': return observation
    try:
        view = _view(project, record['initiative'], reader, deadline)
    except _Failure as exc:
        if exc.reason not in ('plan_missing', 'plan_budget', 'invalid_encoding', 'empty_plan', 'section_budget'): raise
    else: observation.update(status='available', version=view['version'])
    return observation

def _feedback_receipt(operation, record, row):
    result = {'schema_version': 1, 'status': 'ok', 'reason': None, 'review': None, 'approval_granted': False,
              'feedback_receipt': {'operation': operation, **{key: record[key] for key in ('review_id', 'version', 'gate_key', 'revision')},
                'decision_id': record['decision']['decision_id'], 'delivery_id': record['delivery']['delivery_id'],
                'comment_id': row['comment_id'], 'result_id': row['result_id'],
                'verification_id': row.get('verification_id'), 'recorded_at': row['recorded_at']}}
    _need(len(_json(result)) <= MAX_RESPONSE_BYTES, 'response_budget')
    return result

def _feedback_operation(operation, project, record, path, signature, reader, deadline, args):
    _need(len(_json(args)) <= MAX_REQUEST_BYTES, 'request_budget')
    _version(args['version']); _need(args['version'] == record['version'], 'version_conflict', 'conflict')
    _need(args['gate_key'] == record['gate_key'], 'gate_conflict', 'conflict')
    _need(record['state'] == 'consumida' and record['ack'] is not None, 'decision_not_consumed')
    _need(args['decision_id'] == record['decision']['decision_id'] and args['delivery_id'] == record['delivery']['delivery_id'], 'ack_conflict', 'conflict')
    _need(type(args['comment_id']) is str and any(c['comment_id'] == args['comment_id'] for c in record['decision']['comments']), 'comment_not_found')
    revision = args['expected_revision']
    _need(type(revision) is int and 0 <= revision <= MAX_SAFE_REVISION and _hash(args['result_id']), 'invalid_feedback')
    producer = _producer(args['producer'])
    verification = operation == 'verify-result'
    if verification:
        _need(_hash(args['verification_id']) and args['assessment'] in ('confirmed', 'not_confirmed'), 'invalid_feedback')
        text, flags = _feedback_text(args['note'], True)
        accepted = {key: args[key] for key in ('verification_id', 'result_id', 'comment_id', 'assessment')}
        accepted.update(note=text, basis='human_instruction_declared', producer=producer)
        operation_id = args['verification_id']; collection = 'verifications'
    else:
        _need(args['disposition'] in ('addressed', 'not_applied', 'needs_clarification')
              and (args['supersedes_result_id'] is None or _hash(args['supersedes_result_id'])), 'invalid_feedback')
        text, flags = _feedback_text(args['response_text'])
        accepted = {key: args[key] for key in ('result_id', 'comment_id', 'disposition', 'supersedes_result_id')}
        accepted.update(response_text=text, producer=producer)
        operation_id = args['result_id']; collection = 'results'
    feedback = record.get('feedback', _empty_feedback())
    for kind in ('results', 'verifications'):
        for row in feedback[kind]:
            if row.get('verification_id', row['result_id']) == operation_id:
                _need(kind == collection and all(row.get(k) == v for k, v in accepted.items()), 'operation_conflict', 'conflict')
                receipt = _feedback_receipt(operation, record, row); _guard(deadline); _durable(path); _guard(deadline)
                return receipt
    _need(revision == record['revision'], 'revision_conflict', 'conflict')
    _need(record['revision'] < MAX_SAFE_REVISION, 'revision_budget')
    previous = [row for row in feedback['results'] if row['comment_id'] == args['comment_id']]
    if verification:
        target = next((row for row in previous if row['result_id'] == args['result_id']), None)
        _need(target is not None, 'result_conflict', 'conflict')
        _need(previous[-1]['result_id'] == args['result_id'], 'result_superseded', 'conflict')
        _need(not any(row['result_id'] == args['result_id'] for row in feedback['verifications']), 'verification_conflict', 'conflict')
    else:
        _need(len(previous) < 2, 'feedback_budget')
        _need(args['supersedes_result_id'] == (previous[-1]['result_id'] if previous else None), 'result_conflict', 'conflict')
    row = {**accepted, 'text_flags': flags, 'recorded_at': _now()}
    if not verification: row['artifact_observation'] = _observe_artifact(project, record, reader, deadline)
    feedback = {**feedback, collection: [*feedback[collection], row]}
    _feedback_limits(feedback)
    record.update(schema_version=2, feedback=feedback, revision=record['revision']+1)
    receipt = _feedback_receipt(operation, record, row)
    _need(len(_json(record)) <= MAX_RECORD_BYTES, 'state_budget')
    _guard(deadline); _write(path, record, reader, deadline, signature); _guard(deadline)
    return receipt

def _execute(operation, project, review_id=None, *, state_root, deadline=None, **args):
    try:
        deadline = _deadline(deadline)
        _need(isinstance(project, (str, os.PathLike)) and not str(project).replace('\\', '/').startswith('//'))
        project = Path(project).absolute()
        _need('..' not in project.parts)
        _need(isinstance(state_root, (str, os.PathLike)), 'state_scope')
        state = Path(state_root).absolute()
        _need('..' not in state.parts and state == project / '.claude/plan-review', 'state_scope')
        reader = _helper('local-read.py'); _guard(deadline)
        if operation == 'open':
            initiative = args['initiative']; gate = args['gate_key']; consumer = args['consumer']
            _need(type(initiative) is str and len(initiative) <= 180 and INITIATIVE.fullmatch(initiative) is not None)
            _need(gate in ('plan-ok', 'requested-review'))
            if consumer is not None:
                _need(type(consumer) is dict and set(consumer) == {'caller_id', 'runtime'} and type(consumer['caller_id']) is str
                      and re.fullmatch(r'[A-Za-z0-9_-]{1,128}', consumer['caller_id']) is not None
                      and consumer['runtime'] in ('claude-code', 'codex', 'opencode'))
            view = _view(project, initiative, reader, deadline)
        else: _need(_hash(review_id))
        marker = _marker(project, state, reader, deadline, operation == 'open')
        with _locked(state, reader, deadline, operation == 'open'):
            inventory = []
            count = _inventory(state, reader, marker, deadline, inventory)
            if operation == 'open':
                review_id = _review_id(marker, initiative, view['version'], gate)
            path = state / ('r-' + review_id + '.json')
            if operation == 'open' and not path.exists():
                _need(count < MAX_RECORDS, 'state_budget')
                record = dict(schema_version=2, owner=OWNER, review_id=review_id, scope_id=marker['scope_id'], initiative=initiative,
                    artifact='improvement-plan.md', gate_key=gate, version=view['version'], created_at=_now(), revision=0,
                    state='pendiente', consumer_registration={**consumer, 'registered_at': _now()} if consumer else None,
                    draft_comments=[], decision=None, delivery=None, ack=None, feedback=_empty_feedback())
                signature, changed = None, True
            else:
                record, signature = _record(path, marker, reader); changed = False
                if operation in ('result', 'verify-result'):
                    return _feedback_operation(operation, project, record, path, signature, reader, deadline, args)
                try: view = _view(project, record['initiative'], reader, deadline)
                except _Failure as exc:
                    if operation not in ('view', 'status') or exc.reason == 'deadline_expired': raise
                    return _envelope('unavailable', exc.reason, _projection(record, None, 'unavailable', operation == 'view', _feedback_history(record, inventory)))
            if view['version'] != record['version']:
                return _envelope('version_changed', 'plan_version_changed', _projection(record, view, 'version_changed', False, _feedback_history(record, inventory)))
            if operation in ('comments', 'submit', 'receive', 'ack'):
                _version(args['version'])
                _need(args['version'] == record['version'], 'version_conflict', 'conflict')
            if operation in ('comments', 'submit'):
                comments = _comments(args['comments'], view)
                revision = args['expected_revision']
                _need(type(revision) is int and revision >= 0)
                if operation == 'submit':
                    choice = args['choice']; _need(choice in ('approve', 'request_changes'))
                    _need(choice != 'request_changes' or bool(comments), 'comments_required')
                    if record['decision'] is not None:
                        _need(record['decision']['choice'] == choice and record['decision']['comments'] == comments, 'decision_conflict', 'conflict')
                    else:
                        _need(revision == record['revision'], 'revision_conflict', 'conflict')
                        record['draft_comments'] = comments
                        record['decision'] = {'decision_id': secrets.token_hex(32), 'choice': choice, 'comments': comments, 'submitted_at': _now()}
                        changed = True
                else:
                    _need(record['decision'] is None, 'decision_sealed', 'conflict')
                    if comments != record['draft_comments']:
                        _need(revision == record['revision'], 'revision_conflict', 'conflict')
                        record['draft_comments'] = comments; changed = True
            if operation in ('receive', 'ack'):
                _need(args['gate_key'] == record['gate_key'], 'gate_conflict', 'conflict')
                if operation == 'receive' and record['decision'] is None:
                    return _envelope('waiting', None, _projection(record, view, include_view=False))
                if operation == 'receive' and record['state'] == 'pendiente':
                    record['delivery'] = {'delivery_id': secrets.token_hex(32), 'delivered_at': _now()}
                    record['state'] = 'entregada'; changed = True
                elif operation == 'ack':
                    _need(record['delivery'] is not None and args['decision_id'] == record['decision']['decision_id']
                          and args['delivery_id'] == record['delivery']['delivery_id'], 'ack_conflict', 'conflict')
                    if record['state'] != 'consumida':
                        record['ack'] = {'decision_id': args['decision_id'], 'delivery_id': args['delivery_id'], 'consumed_at': _now()}
                        record['state'] = 'consumida'; changed = True
            if changed and signature is not None:
                _need(record['revision'] < MAX_SAFE_REVISION, 'revision_budget'); record['revision'] += 1
            result = _envelope(review=_projection(record, view, include_view=operation in ('open', 'view', 'comments', 'submit'), history=_feedback_history(record, inventory)))
            _guard(deadline)
            if operation not in ('view', 'status'):
                current = _view(project, record['initiative'], reader, deadline)
                if current['version'] != record['version']:
                    return _envelope('version_changed', 'plan_version_changed', _projection(record, current, 'version_changed', False))
                if changed: _write(path, record, reader, deadline, signature)
                else: _durable(path)  # Retry after a lost response re-establishes observed persistence.
            _guard(deadline)
            return result
    except _Failure as exc:
        result = {'schema_version': 1, 'status': exc.status, 'reason': exc.reason, 'review': None}
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, RecursionError):
        result = {'schema_version': 1, 'status': 'unavailable', 'reason': 'invalid_input', 'review': None}
    except (ImportError, AttributeError, SyntaxError):
        result = {'schema_version': 1, 'status': 'unavailable', 'reason': 'helper_unavailable', 'review': None}
    if operation in ('result', 'verify-result'): result.update(approval_granted=False, feedback_receipt=None)
    return result

def list_reminders(project, initiative, *, state_root, deadline=None):
    """Bounded read-only observations; never initialize, lock, deliver or ack.

    Repeated inventories reject observed changes. They do not provide an atomic
    snapshot, ABA protection, model attention or permission to continue a gate.
    """
    def envelope(status, reason=None, *, complete=False, reviews=None, omitted=0):
        return {'schema_version': 1, 'status': status, 'reason': reason,
                'complete': complete, 'reviews': reviews or [], 'reviews_omitted': omitted,
                'approval_granted': False}
    try:
        deadline = _deadline(deadline)
        _need(isinstance(project, (str, os.PathLike)) and not str(project).replace('\\', '/').startswith('//'))
        project = Path(project).absolute()
        _need('..' not in project.parts)
        _need(isinstance(state_root, (str, os.PathLike)), 'state_scope')
        state = Path(state_root).absolute()
        _need('..' not in state.parts and state == project / '.claude/plan-review', 'state_scope')
        _need(type(initiative) is str and len(initiative) <= 180 and INITIATIVE.fullmatch(initiative) is not None)
        reader = _helper('local-read.py')
        _guard(deadline); _dirs(project, reader)
        for path in (state.parent, state):
            try: path.lstat()
            except FileNotFoundError:
                return envelope('not_registered', 'review_not_found', complete=True)
            _dirs(path, reader)
        marker = _marker(project, state, reader, deadline, False)
        first, second = [], []
        _inventory(state, reader, marker, deadline, first)
        _need(len(first) <= MAX_RECORDS, 'state_budget')
        selected = sorted((r for r in first if r['initiative'] == initiative), key=lambda r: r['review_id'])
        view = _view(project, initiative, reader, deadline) if selected else None
        selected.sort(key=lambda r: (r['version'] != view['version'],
            {'pendiente': 0, 'entregada': 1, 'consumida': 2}[r['state']], r['review_id']))
        _inventory(state, reader, marker, deadline, second)
        _need(_json(sorted(first, key=lambda r: r['review_id'])) ==
              _json(sorted(second, key=lambda r: r['review_id'])), 'state_changed')
        _need(_marker(project, state, reader, deadline, False) == marker, 'state_changed')
        if selected:
            _need(_view(project, initiative, reader, deadline)['version'] == view['version'], 'plan_changed')
        reminders = []
        for record in selected[:MAX_REMINDERS]:
            feedback = record.get('feedback', _empty_feedback())
            latest = {row['comment_id']: row for row in feedback['results']}
            verified = {row['result_id'] for row in feedback['verifications']}
            reminders.append({key: record[key] for key in ('review_id', 'initiative', 'gate_key', 'version', 'revision', 'state')})
            reminders[-1].update(version_status='current' if record['version'] == view['version'] else 'version_changed',
                decision_recorded=record['decision'] is not None,
                comments_recorded=len(record['decision']['comments'] if record['decision'] else record['draft_comments']),
                comments_with_result=len(latest),
                latest_results_needing_clarification=sum(row['disposition'] == 'needs_clarification' for row in latest.values()),
                latest_results_without_verification=sum(row['result_id'] not in verified for row in latest.values()),
                approval_granted=False)
        _guard(deadline)
        return envelope('ok', complete=True, reviews=reminders, omitted=max(0, len(selected)-len(reminders)))
    except _Failure as exc:
        return envelope(exc.status, exc.reason)
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, RecursionError):
        return envelope('unavailable', 'invalid_input')
    except (ImportError, AttributeError, SyntaxError):
        return envelope('unavailable', 'helper_unavailable')


def summarize_reviews(project, initiatives, *, state_root, deadline=None):
    """Read-only review state for many initiatives; never initialize, lock, fsync or write.

    Same double inventory as list_reminders: observed changes are rejected, but
    this is neither an atomic snapshot nor permission to continue a gate.
    """
    def envelope(status, reason=None, *, complete=False, rows=None, omitted=0):
        return {'schema_version': 1, 'status': status, 'reason': reason, 'complete': complete,
                'observed_at': _now(), 'initiatives': rows or [], 'omitted': omitted, 'approval_granted': False}
    def row(initiative, estado, **extra):
        base = {'initiative': initiative, 'estado': estado, 'version_ordinal': None, 'gate_key': None,
                'review_state': None, 'plan': None, 'comments': 0, 'comments_with_result': 0,
                'needs_clarification': 0, 'results_without_verification': 0, 'other_current_reviews': 0,
                'review_id': None}
        base.update(extra)
        return base
    try:
        deadline = _deadline(deadline)
        _need(isinstance(project, (str, os.PathLike)) and not str(project).replace('\\', '/').startswith('//'))
        project = Path(project).absolute()
        _need('..' not in project.parts)
        _need(isinstance(state_root, (str, os.PathLike)), 'state_scope')
        state = Path(state_root).absolute()
        _need('..' not in state.parts and state == project / '.claude/plan-review', 'state_scope')
        _need(type(initiatives) is list and len(initiatives) <= MAX_RECORDS and len(set(map(str, initiatives))) == len(initiatives))
        _need(all(type(i) is str and len(i) <= 180 and INITIATIVE.fullmatch(i) is not None for i in initiatives))
        reader = _helper('local-read.py')
        _guard(deadline); _dirs(project, reader)
        for path in (state.parent, state):
            try: path.lstat()
            except FileNotFoundError:
                return envelope('ok', complete=True, rows=[row(i, 'sin_revision') for i in initiatives])
            _dirs(path, reader)
        marker = _marker(project, state, reader, deadline, False)
        first, second = [], []
        _inventory(state, reader, marker, deadline, first)
        _need(len(first) <= MAX_RECORDS, 'state_budget')
        rows, seen, expired = [], {}, False
        for initiative in initiatives:
            records = sorted((r for r in first if r['initiative'] == initiative), key=lambda r: (r['created_at'], r['review_id']))
            if not records:
                rows.append(row(initiative, 'sin_revision')); continue
            if expired:
                rows.append(row(initiative, 'no_disponible', plan='unavailable')); continue
            try:
                _guard(deadline)
                plan = reader.read_bytes(project, initiative + '/improvement-plan.md', max_bytes=MAX_PLAN_BYTES, include_digest=True)
                if plan['status'] != 'ok':
                    rows.append(row(initiative, 'no_disponible', plan='missing' if plan['status'] == 'not_found' else 'unavailable')); continue
                seen[initiative] = plan['sha256']
                same = [r for r in records if r['version']['raw_sha256'] == plan['sha256']]
                view = _view(project, initiative, reader, deadline)['version'] if same else None
            except _Failure as exc:
                if exc.reason == 'deadline_expired': expired = True
                rows.append(row(initiative, 'no_disponible', plan='unavailable')); continue
            current = [r for r in same if r['version']['view_sha256'] == view['view_sha256']]
            pool = current or records
            # The panel can only act on its own `requested-review`: a later `plan-ok` of the orchestrator on the same
            # plan must not hide it (it still counts in `other_current_reviews`).
            principal = ([r for r in pool if r['gate_key'] == 'requested-review'] or pool)[-1]
            order = []
            for r in records:
                if r['version'] not in order: order.append(r['version'])
            feedback = principal.get('feedback', _empty_feedback())
            latest = {x['comment_id']: x for x in feedback['results']}
            verified = {x['result_id'] for x in feedback['verifications']}
            decision = principal['decision']
            estado = ('obsoleta' if not current else 'pendiente' if decision is None
                      else 'aprobada' if decision['choice'] == 'approve' else 'cambios_pedidos')
            rows.append(row(initiative, estado, version_ordinal=order.index(principal['version']) + 1,
                gate_key=principal['gate_key'], review_state=principal['state'], plan='ok',
                comments=len(decision['comments'] if decision else principal['draft_comments']),
                comments_with_result=len(latest),
                needs_clarification=sum(x['disposition'] == 'needs_clarification' for x in latest.values()),
                results_without_verification=sum(x['result_id'] not in verified for x in latest.values()),
                other_current_reviews=max(0, len(current) - 1),
                review_id=principal['review_id']))
        # An expired deadline already made the answer `partial`; the consistency check still needs a little time
        # of its own, small and bounded (a second `_guard` on the spent deadline would turn what was read into
        # `unavailable`; a long grace would outlast the client's own window).
        recheck = time.monotonic() + 0.25 if expired and time.monotonic() >= deadline else deadline
        _inventory(state, reader, marker, recheck, second)
        _need(_json(sorted(first, key=lambda r: r['review_id'])) ==
              _json(sorted(second, key=lambda r: r['review_id'])), 'state_changed')
        _need(_marker(project, state, reader, recheck, False) == marker, 'state_changed')
        for initiative, sha in seen.items():
            _guard(recheck)
            again = reader.read_bytes(project, initiative + '/improvement-plan.md', max_bytes=MAX_PLAN_BYTES, include_digest=True)
            _need(again['status'] == 'ok' and again['sha256'] == sha, 'state_changed')
        result = envelope('partial' if expired else 'ok', 'deadline_expired' if expired else None,
                          complete=not expired, rows=rows)
        _need(len(_json(result)) <= 64 * 1024, 'response_budget')
        return result
    except _Failure as exc:
        return envelope(exc.status, exc.reason)
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, RecursionError):
        return envelope('unavailable', 'invalid_input')
    except (ImportError, AttributeError, SyntaxError):
        return envelope('unavailable', 'helper_unavailable')


def open_review(project, initiative, *, state_root, gate_key='requested-review', consumer=None, deadline=None):
    return _execute('open', project, state_root=state_root, deadline=deadline, initiative=initiative, gate_key=gate_key, consumer=consumer)

def get_view(project, review_id, *, state_root, deadline=None):
    return _execute('view', project, review_id, state_root=state_root, deadline=deadline)

def get_status(project, review_id, *, state_root, deadline=None):
    return _execute('status', project, review_id, state_root=state_root, deadline=deadline)

def save_comments(project, review_id, version, comments, *, expected_revision, state_root, deadline=None):
    return _execute('comments', project, review_id, state_root=state_root, deadline=deadline, version=version, comments=comments, expected_revision=expected_revision)

def submit_decision(project, review_id, version, choice, comments, *, expected_revision, state_root, deadline=None):
    return _execute('submit', project, review_id, state_root=state_root, deadline=deadline, version=version, choice=choice, comments=comments, expected_revision=expected_revision)

def receive_decision(project, review_id, version, *, gate_key, state_root, deadline=None):
    return _execute('receive', project, review_id, state_root=state_root, deadline=deadline, version=version, gate_key=gate_key)

def ack_decision(project, review_id, version, *, gate_key, decision_id, delivery_id, state_root, deadline=None):
    return _execute('ack', project, review_id, state_root=state_root, deadline=deadline, version=version, gate_key=gate_key, decision_id=decision_id, delivery_id=delivery_id)

def _consume_review(result, review_id, version, initiative, gate_key, states):
    """Validate a bound response before its IDs can drive the next owner call."""
    _need(type(result) is dict and type(result.get('schema_version')) is int
          and result['schema_version'] == 1
          and result.get('status') in ('ok', 'waiting', 'conflict', 'version_changed', 'unavailable'),
          'consume_response_invalid')
    if result['status'] not in ('ok', 'waiting'):
        return None
    review = result.get('review')
    _need(type(review) is dict, 'consume_response_invalid')
    _need(review.get('review_id') == review_id and review.get('initiative') == initiative
          and review.get('artifact') == 'improvement-plan.md', 'selection_conflict', 'conflict')
    _need(review.get('gate_key') == gate_key, 'gate_conflict', 'conflict')
    _need(review.get('version') == version and review.get('current_version') == version,
          'version_conflict', 'conflict')
    _need(review.get('complete') is True and review.get('validity') == 'current'
          and review.get('state') in states, 'consume_response_invalid')
    return review

def consume_decision(project, review_id, version, *, initiative, gate_key, state_root, deadline=None):
    """Consume a current decision through the existing owner, without workflow effects.

    A delivered receipt survives failed ack for retry. Consumption of an old version
    remains historical if the final observation changes; it never authorizes effects.
    The observations do not provide an atomic plan snapshot or ABA detection.
    """
    try:
        budget = _deadline(deadline)
        _need(type(initiative) is str and INITIATIVE.fullmatch(initiative) is not None)
        _need(_hash(review_id) and gate_key in ('plan-ok', 'requested-review'))
        _version(version)
        version = dict(version)
        common = {'state_root': state_root, 'deadline': budget}
        preflight = get_view(project, review_id, **common)
        prior = _consume_review(preflight, review_id, version, initiative, gate_key,
                                ('pendiente', 'entregada', 'consumida'))
        if preflight['status'] != 'ok':
            return preflight
        _guard(budget)
        delivered = receive_decision(project, review_id, version, gate_key=gate_key, **common)
        review = _consume_review(delivered, review_id, version, initiative, gate_key,
                                 ('pendiente', 'entregada', 'consumida'))
        if delivered['status'] != 'ok':
            return delivered
        decision, delivery = review.get('decision'), review.get('delivery')
        _need(review['state'] in ('entregada', 'consumida') and type(decision) is dict
              and _hash(decision.get('decision_id')) and decision.get('choice') in ('approve', 'request_changes')
              and type(decision.get('comments')) is list
              and (decision['choice'] != 'request_changes' or bool(decision['comments']))
              and type(delivery) is dict and _hash(delivery.get('delivery_id')), 'consume_response_invalid')
        _need(prior.get('decision') is None or prior['decision'] == decision, 'consume_response_invalid')
        _need(prior.get('delivery') is None or prior['delivery'] == delivery, 'consume_response_invalid')
        _guard(budget)
        confirmed = ack_decision(project, review_id, version, gate_key=gate_key,
                                 decision_id=decision['decision_id'], delivery_id=delivery['delivery_id'], **common)
        receipt = _consume_review(confirmed, review_id, version, initiative, gate_key, ('consumida',))
        if confirmed['status'] != 'ok':
            return confirmed
        ack = receipt.get('ack')
        _need(receipt.get('decision') == decision and receipt.get('delivery') == delivery
              and type(ack) is dict and ack.get('decision_id') == decision['decision_id']
              and ack.get('delivery_id') == delivery['delivery_id'] and _timestamp(ack.get('consumed_at')),
              'consume_response_invalid')
        _guard(budget)
        current = get_view(project, review_id, **common)
        final = _consume_review(current, review_id, version, initiative, gate_key, ('consumida',))
        if current['status'] != 'ok':
            return current
        _need(final.get('decision') == decision and final.get('delivery') == delivery
              and final.get('ack') == ack, 'consume_response_invalid')
        _guard(budget)
        return current
    except _Failure as exc:
        return _envelope(exc.status, exc.reason)
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, RecursionError):
        return _envelope('unavailable', 'consume_response_invalid')

def record_feedback_result(project, review_id, version, *, gate_key, decision_id, delivery_id, comment_id,
                           result_id, expected_revision, disposition, response_text, supersedes_result_id,
                           producer, state_root, deadline=None):
    return _execute('result', project, review_id, state_root=state_root, deadline=deadline, version=version,
                    gate_key=gate_key, decision_id=decision_id, delivery_id=delivery_id, comment_id=comment_id,
                    result_id=result_id, expected_revision=expected_revision, disposition=disposition,
                    response_text=response_text, supersedes_result_id=supersedes_result_id, producer=producer)

def record_feedback_verification(project, review_id, version, *, gate_key, decision_id, delivery_id, comment_id,
                                 result_id, verification_id, expected_revision, assessment, note,
                                 producer, state_root, deadline=None):
    return _execute('verify-result', project, review_id, state_root=state_root, deadline=deadline, version=version,
                    gate_key=gate_key, decision_id=decision_id, delivery_id=delivery_id, comment_id=comment_id,
                    result_id=result_id, verification_id=verification_id, expected_revision=expected_revision,
                    assessment=assessment, note=note, producer=producer)

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['open', 'summary', 'view', 'status', 'comments', 'submit', 'receive', 'ack', 'consume', 'result', 'verify-result'])
    for name in ('project', 'state-root'): parser.add_argument('--' + name, required=True)
    for name in ('initiative', 'review-id', 'raw-sha256', 'view-sha256', 'decision-id', 'delivery-id', 'caller-id', 'runtime'):
        parser.add_argument('--' + name)
    parser.add_argument('--gate-key', choices=['plan-ok', 'requested-review'], default='requested-review')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)
    common = {'state_root': args.state_root, 'deadline': time.monotonic() + 3}
    try:
        if args.operation == 'open':
            consumer = {'caller_id': args.caller_id, 'runtime': args.runtime} if args.caller_id is not None or args.runtime is not None else None
            result = open_review(args.project, args.initiative, gate_key=args.gate_key, consumer=consumer, **common)
        elif args.operation == 'summary':
            raw = sys.stdin.buffer.read(MAX_REQUEST_BYTES + 1)
            _need(len(raw) <= MAX_REQUEST_BYTES, 'request_budget')
            result = summarize_reviews(args.project, _strict(raw), **common)
        elif args.operation in ('view', 'status'):
            result = {'view': get_view, 'status': get_status}[args.operation](args.project, args.review_id, **common)
        elif args.operation in ('comments', 'submit', 'result', 'verify-result'):
            raw = sys.stdin.buffer.read(MAX_REQUEST_BYTES + 1)
            _need(len(raw) <= MAX_REQUEST_BYTES, 'request_budget')
            payload = _strict(raw)
            if args.operation in ('result', 'verify-result'):
                keys = {'version', 'gate_key', 'decision_id', 'delivery_id', 'comment_id', 'result_id', 'expected_revision', 'producer'}
                keys |= {'disposition', 'response_text', 'supersedes_result_id'} if args.operation == 'result' else {'verification_id', 'assessment', 'note'}
            else: keys = {'version', 'comments', 'expected_revision'} | ({'choice'} if args.operation == 'submit' else set())
            _need(type(payload) is dict and set(payload) == keys)
            fn = {'comments': save_comments, 'submit': submit_decision, 'result': record_feedback_result,
                  'verify-result': record_feedback_verification}[args.operation]
            result = fn(args.project, args.review_id, **payload, **common)
        else:
            version = {'raw_sha256': args.raw_sha256, 'view_sha256': args.view_sha256, 'view_version': VIEW_VERSION}
            extra = {'gate_key': args.gate_key}
            if args.operation == 'ack': extra.update(decision_id=args.decision_id, delivery_id=args.delivery_id)
            if args.operation == 'consume': extra['initiative'] = args.initiative
            fn = {'receive': receive_decision, 'ack': ack_decision, 'consume': consume_decision}[args.operation]
            result = fn(args.project, args.review_id, version, **extra, **common)
    except (OSError, ValueError, TypeError, _Failure, RecursionError) as exc:
        result = {'schema_version': 1, 'status': 'unavailable', 'reason': exc.reason if isinstance(exc, _Failure) else 'invalid_input', 'review': None}
        if args.operation in ('result', 'verify-result'): result.update(approval_granted=False, feedback_receipt=None)
    if args.operation == 'summary':
        print(_json(result).decode('utf-8'))
        return 0 if result['status'] in ('ok', 'partial') else 3
    print(_json(result).decode('utf-8'))
    return 0 if result['status'] in ('ok', 'waiting') else 2 if result['status'] in ('conflict', 'version_changed') else 3

if __name__ == '__main__':
    raise SystemExit(main())
