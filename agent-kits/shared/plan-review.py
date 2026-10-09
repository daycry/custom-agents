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
import tempfile
import time

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001

HERE = Path(__file__).resolve().parent
OWNER = 'custom-agents.plan-review'
VIEW_VERSION = 'plan-text-v1'
MAX_PLAN_BYTES = 256 * 1024
MAX_RECORD_BYTES = 96 * 1024
MAX_REQUEST_BYTES = 16 * 1024
MAX_RESPONSE_BYTES = 512 * 1024
MAX_RECORDS = 64
HASH = re.compile(r'[a-f0-9]{64}')
INITIATIVE = re.compile(r'docs/roadmap/[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z0-9]+(?:-[a-z0-9]+)*')
CONTROLS = re.compile(r'[\x00-\x08\x0b-\x1f\x7f-\x9f\u2028\u2029\u202a-\u202e\u2066-\u2069]')
RECORD_KEYS = {'schema_version', 'owner', 'review_id', 'scope_id', 'initiative', 'artifact', 'gate_key', 'version', 'created_at', 'revision', 'state', 'consumer_registration', 'draft_comments', 'decision', 'delivery', 'ack'}

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

def _dirs(path, reader):
    for entry in [*reversed(path.parents), path]:
        info = entry.lstat()
        _need(stat.S_ISDIR(info.st_mode) and not reader._redirected(info), 'unsafe_state')

def _file(path, reader):
    info = path.lstat()
    _need(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and not reader._redirected(info), 'unsafe_state')
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)

def _read(path, reader, maximum):
    _dirs(path.parent, reader)
    before = _file(path, reader)
    row = reader.read_bytes(path.parent, path.name, max_bytes=maximum)
    _need(row['status'] == 'ok', 'invalid_state')
    _need(_file(path, reader) == before, 'unsafe_state')
    return _strict(row['data']), before

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
    redactor = _helper('redact.py')
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
    if os.name == 'nt': return  # Windows file fsync is used; no portable directory flush guarantee.
    fd = os.open(path, os.O_RDONLY)
    try: os.fsync(fd)
    finally: os.close(fd)

def _durable(path):
    try:
        with path.open('r+b') as handle: os.fsync(handle.fileno())
        _sync_dir(path.parent)
    except OSError: raise _Failure('durability_degraded') from None

def _write(path, value, reader, deadline, expected=None):
    raw = _json(value)
    _need(len(raw) <= MAX_RECORD_BYTES, 'state_budget')
    _guard(deadline); _dirs(path.parent, reader)
    fd, name = tempfile.mkstemp(prefix='.tmp-', dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, 'wb') as handle:
            handle.write(raw); handle.flush()
            try: os.fsync(handle.fileno())
            except OSError: raise _Failure('durability_degraded') from None
        _guard(deadline); _dirs(path.parent, reader)
        if expected is None:
            os.link(temporary, path, follow_symlinks=False)  # Exclusive leaf creation, no overwrite fallback.
        else:
            _need(_file(path, reader) == expected, 'unsafe_state')
            os.replace(temporary, path)  # Only an observed owned record under our process lock.
        if temporary.exists(): temporary.unlink()
        try: _sync_dir(path.parent)
        except OSError: raise _Failure('durability_degraded') from None
    finally:
        if temporary.exists(): temporary.unlink()  # Only this invocation's exact private temporary.

def _marker(project, state, reader, deadline, initialize):
    _dirs(project, reader)
    info = project.lstat()
    root_key = _digest({'path': os.path.normcase(str(project)), 'identity': [info.st_dev, info.st_ino]})
    if not state.exists():
        _need(initialize, 'review_not_found')
        if not state.parent.exists(): state.parent.mkdir(mode=0o700)
        _dirs(state.parent, reader)
        try: state.mkdir(mode=0o700)
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
    path = state / '.lock'
    if not path.exists():
        _need(initialize, 'invalid_state')
        try:
            with path.open('xb') as handle: handle.write(b'0'); handle.flush(); os.fsync(handle.fileno())
            _sync_dir(state)
        except FileExistsError: pass
    before = _file(path, reader)
    fd = os.open(path, os.O_RDWR | getattr(os, 'O_NOFOLLOW', 0))
    unlock = None
    try:
        info = os.fstat(fd)
        _need((info.st_dev, info.st_ino) == before[:2] and _file(path, reader) == before, 'unsafe_state')
        stop = min(deadline, time.monotonic() + 0.1)
        while True:
            _guard(deadline)
            try:
                if os.name == 'nt':
                    import msvcrt
                    msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
                    unlock = lambda: msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    unlock = lambda: fcntl.flock(fd, fcntl.LOCK_UN)
                break
            except OSError:
                _need(time.monotonic() < stop, 'state_busy')
                time.sleep(min(0.005, max(0, stop - time.monotonic())))
        _dirs(state, reader); _need(_file(path, reader) == before, 'unsafe_state')
        yield
    finally:
        if unlock:
            with contextlib.suppress(OSError): unlock()
        os.close(fd)

def _inventory(state, reader, marker, deadline):
    listing = reader.list_names(state.parent, state.name, max_entries=MAX_RECORDS + 18)
    _need(listing['status'] == 'ok' and listing['complete'], 'state_budget')
    for name in listing['names']:
        _need(name in {'owner.json', '.lock'} or re.fullmatch(r'r-[a-f0-9]{64}\.json', name) is not None
              or re.fullmatch(r'\.tmp-[a-zA-Z0-9_-]+', name) is not None, 'unowned_state')
        _guard(deadline); _file(state / name, reader)
        if name.startswith('r-'): _record(state / name, marker, reader)
    return sum(name.startswith('r-') for name in listing['names'])

def _record(path, marker, reader):
    try: record, signature = _read(path, reader, 96 * 1024)
    except FileNotFoundError: raise _Failure('review_not_found') from None
    try:
        _need(type(record) is dict and set(record) == RECORD_KEYS, 'invalid_state')
        _version(record['version'])
        _need(type(record['schema_version']) is int and record['schema_version'] == 1 and record['owner'] == OWNER
              and record['scope_id'] == marker['scope_id'] and type(record['initiative']) is str
              and INITIATIVE.fullmatch(record['initiative']) is not None and record['artifact'] == 'improvement-plan.md'
              and record['gate_key'] in ('plan-ok', 'requested-review') and type(record['revision']) is int
              and record['revision'] >= 0 and record['state'] in ('pendiente', 'entregada', 'consumida')
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
    except (KeyError, TypeError, ValueError, _Failure): raise _Failure('invalid_state') from None
    return record, signature

def _projection(record, view, validity='current', include_view=True):
    result = {key: value for key, value in record.items() if key not in {'owner', 'schema_version', 'scope_id'}}
    result.update(validity=validity, observed_at=_now())
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
    _need(len(_json(result)) <= MAX_RESPONSE_BYTES, 'response_budget')
    return result

def _comments(value, view):
    _need(type(value) is list and len(value) <= 20, 'comment_budget')
    allowed = {s['section_id'] for s in view['sections']} if view is not None else None; seen = set(); cleaned = []
    redactor = _helper('redact.py')
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
            count = _inventory(state, reader, marker, deadline)
            if operation == 'open':
                review_id = _review_id(marker, initiative, view['version'], gate)
            path = state / ('r-' + review_id + '.json')
            if operation == 'open' and not path.exists():
                _need(count < MAX_RECORDS, 'state_budget')
                record = dict(schema_version=1, owner=OWNER, review_id=review_id, scope_id=marker['scope_id'], initiative=initiative,
                    artifact='improvement-plan.md', gate_key=gate, version=view['version'], created_at=_now(), revision=0,
                    state='pendiente', consumer_registration={**consumer, 'registered_at': _now()} if consumer else None,
                    draft_comments=[], decision=None, delivery=None, ack=None)
                signature, changed = None, True
            else:
                record, signature = _record(path, marker, reader); changed = False
                try: view = _view(project, record['initiative'], reader, deadline)
                except _Failure as exc:
                    if operation not in ('view', 'status') or exc.reason == 'deadline_expired': raise
                    return _envelope('unavailable', exc.reason, _projection(record, None, 'unavailable', operation == 'view'))
            if view['version'] != record['version']:
                return _envelope('version_changed', 'plan_version_changed', _projection(record, view, 'version_changed', False))
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
            if changed and signature is not None: record['revision'] += 1
            result = _envelope(review=_projection(record, view, include_view=operation in ('open', 'view', 'comments', 'submit')))
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
        return {'schema_version': 1, 'status': exc.status, 'reason': exc.reason, 'review': None}
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, RecursionError):
        return {'schema_version': 1, 'status': 'unavailable', 'reason': 'invalid_input', 'review': None}
    except (ImportError, AttributeError, SyntaxError):
        return {'schema_version': 1, 'status': 'unavailable', 'reason': 'helper_unavailable', 'review': None}

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

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['open', 'view', 'status', 'comments', 'submit', 'receive', 'ack'])
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
        elif args.operation in ('view', 'status'):
            result = {'view': get_view, 'status': get_status}[args.operation](args.project, args.review_id, **common)
        elif args.operation in ('comments', 'submit'):
            raw = sys.stdin.buffer.read(MAX_REQUEST_BYTES + 1)
            _need(len(raw) <= MAX_REQUEST_BYTES, 'request_budget')
            payload = _strict(raw)
            keys = {'version', 'comments', 'expected_revision'} | ({'choice'} if args.operation == 'submit' else set())
            _need(type(payload) is dict and set(payload) == keys)
            fn = save_comments if args.operation == 'comments' else submit_decision
            result = fn(args.project, args.review_id, **payload, **common)
        else:
            version = {'raw_sha256': args.raw_sha256, 'view_sha256': args.view_sha256, 'view_version': VIEW_VERSION}
            extra = {'gate_key': args.gate_key}
            if args.operation == 'ack': extra.update(decision_id=args.decision_id, delivery_id=args.delivery_id)
            fn = receive_decision if args.operation == 'receive' else ack_decision
            result = fn(args.project, args.review_id, version, **extra, **common)
    except (OSError, ValueError, TypeError, _Failure, RecursionError) as exc:
        result = {'schema_version': 1, 'status': 'unavailable', 'reason': exc.reason if isinstance(exc, _Failure) else 'invalid_input', 'review': None}
    print(_json(result).decode('utf-8'))
    return 0 if result['status'] in ('ok', 'waiting') else 2 if result['status'] in ('conflict', 'version_changed') else 3

if __name__ == '__main__':
    raise SystemExit(main())
