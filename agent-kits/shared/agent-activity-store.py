#!/usr/bin/env python3
"""Owned, opt-in activity metadata. Signals are neither liveness nor teardown."""
import hashlib
import hmac
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import secrets
import sys
import time

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError, ValueError): pass

HERE = Path(__file__).resolve().parent
OWNER = 'custom-agents.agent-activity-v1'
MAX_BYTES = 65536
MAX_REVISION = 2**53 - 1
IGNORE = b'*\n'


def _mkdir_private(path, **kwargs):
    """0o700 en POSIX. En Windows se heredan los permisos del padre: Python 3.13 convierte
    0o700 en una ACL explícita que deja fuera al usuario restringido del sandbox de Codex."""
    if os.name == 'nt':
        path.mkdir(**kwargs)
    else:
        path.mkdir(mode=0o700, **kwargs)


class _Failure(Exception):
    pass


def _need(condition, reason):
    if not condition:
        raise _Failure(reason)


def _guard(deadline):
    _need(time.monotonic() < deadline, 'deadline_exceeded')


def _load(filename):
    spec = importlib.util.spec_from_file_location(filename.replace('-', '_'), HERE / (filename + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


try:
    _reader = _load('local-read')
    _state_io = _load('local-state')
    _projection = _load('agent-activity')
except Exception:
    _reader = _state_io = _projection = None


def _io():
    _need(_reader is not None and _state_io is not None and _projection is not None, 'invalid_state')
    return _state_io.StateIO(_reader, _need, _guard, maximum=MAX_BYTES)


def _json(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def _strict(raw):
    def pairs(items):
        out = {}
        for key, value in items:
            _need(key not in out, 'invalid_state')
            out[key] = value
        return out
    return json.loads(raw.decode('utf-8-sig'), object_pairs_hook=pairs,
        parse_constant=lambda value: (_ for _ in ()).throw(_Failure('invalid_state')))


def _root(project, io):
    root = Path(os.path.abspath(project))
    io.dirs(root)
    return root


def _root_key(root):
    return hashlib.sha256(os.path.normcase(str(root)).encode('utf-8')).hexdigest()


def _enabled(root, io):
    path = root / '.claude' / 'dev.json'
    if not path.exists():
        raise _Failure('disabled')
    config = _strict(io.read(path, MAX_BYTES)[0])
    _need(type(config) is dict, 'invalid_config')
    session = config.get('sesion', {})
    _need(type(session) is dict, 'invalid_config')
    _need(session.get('actividad') is True, 'disabled')


def _hex(value):
    return type(value) is str and len(value) == 64 and all(ch in '0123456789abcdef' for ch in value)


def _owner(root, state, io):
    path = state / 'owner.json'
    _need(path.exists(), 'unowned_state')
    marker, signature = io.read(path, 4096)
    marker = _strict(marker)
    _need(type(marker) is dict and set(marker) == {'schema_version', 'owner', 'scope_id', 'root_key'}
        and type(marker['schema_version']) is int and marker['schema_version'] == 1
        and marker['owner'] == OWNER and _hex(marker['scope_id'])
        and marker['root_key'] == _root_key(root), 'unowned_state')
    return marker, signature


FIXED_NAMES = frozenset({'.gitignore', 'owner.json', 'snapshot.json', '.lock'})
MAX_TEMPS = 8  # orphans of an interrupted atomic replace; tolerated, never read or deleted here
_TEMP = re.compile(r'\.tmp-[a-zA-Z0-9_-]+')


def _inventory(state):
    listing = _reader.list_names(state.parent, state.name, max_entries=len(FIXED_NAMES) + MAX_TEMPS + 2)
    if listing['status'] == 'ok' and not listing['complete']:
        raise _Failure('state_budget')
    _need(listing['status'] == 'ok' and listing['complete'], 'invalid_state')
    names = set(listing['names'])
    temps = {name for name in names if _TEMP.fullmatch(name)}
    _need(names - temps == FIXED_NAMES, 'invalid_state')
    _need(len(temps) <= MAX_TEMPS, 'state_budget')


def _ignore(state, io):
    raw, signature = io.read(state / '.gitignore', len(IGNORE))
    _need(raw == IGNORE, 'invalid_state')
    return signature


def _read_snapshot(root, state, io):
    io.dirs(state)
    marker, owner_signature = _owner(root, state, io)
    ignore_signature = _ignore(state, io)
    _inventory(state)
    io.file(state / '.lock')
    raw, signature = io.read(state / 'snapshot.json', MAX_BYTES)
    value = _strict(raw)
    _need(type(value) is dict and set(value) == {'schema_version', 'owner', 'scope_id', 'revision', 'records'}
        and type(value['schema_version']) is int and value['schema_version'] == 1
        and value['owner'] == OWNER and value['scope_id'] == marker['scope_id']
        and type(value['revision']) is int and 0 <= value['revision'] <= MAX_REVISION, 'invalid_state')
    rows = value['records']
    _need(_projection.project_activity(rows, now=time.time())['status'] == 'ok', 'invalid_state')
    _need(all(row['revision'] <= value['revision'] for row in rows), 'invalid_state')
    _need(io.file(state / 'owner.json') == owner_signature, 'unsafe_state')
    _need(_ignore(state, io) == ignore_signature, 'unsafe_state')
    return marker, value, signature, ignore_signature


def _id(value):
    return type(value) is str and bool(value) and len(value.encode('utf-8')) <= 512 and all(ord(ch) >= 32 and ord(ch) != 127 for ch in value)


def _payload(root, runtime, payload):
    _need(type(runtime) is str and runtime in ('claude', 'codex', 'opencode') and type(payload) is dict, 'invalid_input')
    _need(len(_json(payload)) <= MAX_BYTES, 'input_budget')
    _need(type(payload.get('cwd')) is str and os.path.normcase(os.path.abspath(payload['cwd'])) == os.path.normcase(str(root)), 'project_mismatch')
    if runtime in ('claude', 'codex'):
        event = {'SubagentStart': 'response_started', 'SubagentStop': 'response_finished'}.get(payload.get('hook_event_name'))
        _need(event is not None, 'unsupported_event')
        session, agent = payload.get('session_id'), payload.get('agent_id')
        _need(_id(session) and _id(agent), 'invalid_identity')
        _need(type(payload.get('agent_type')) is str, 'invalid_identity')
        mapping = _strict(_io().read(HERE / 'native-roles.json', MAX_BYTES)[0])
        _need(type(mapping) is dict and mapping.get('schema_version') == 1
            and type(mapping.get('runtimes')) is dict and type(mapping['runtimes'].get(runtime)) is dict, 'role_map_unavailable')
        role = next((role for role, native in mapping['runtimes'][runtime].items()
            if native == payload['agent_type'] and role in _projection.ROLES), 'other')
        return 'subagent', session, agent, role, event, 'native_hook'
    native = payload.get('type')
    data = payload.get('data')
    event = 'execution_started' if native == 'session.execution.started' else 'execution_finished' if native in ('session.execution.succeeded', 'session.execution.failed', 'session.execution.interrupted') else 'session_idle' if native == 'session.idle' else None
    if native == 'session.status' and type(data) is dict and type(data.get('status')) is dict and data['status'].get('type') == 'idle':
        event = 'session_idle'
    _need(event is not None, 'unsupported_event')
    _need(type(data) is dict and _id(data.get('sessionID')), 'invalid_identity')
    return 'session', data['sessionID'], None, None, event, 'native_stream'


def _key(marker, fields):
    return hmac.new(bytes.fromhex(marker['scope_id']), _json(fields), hashlib.sha256).hexdigest()


def capture(project, *, runtime, payload):
    """Receive a native declaration; return an observable status without free text."""
    try:
        deadline, io = time.monotonic() + 1, _io()
        root = _root(project, io)
        scope, session, agent, role, event, source = _payload(root, runtime, payload)
        _enabled(root, io)
        state = root / '.claude' / 'agent-activity'
        created = False
        if not state.exists():
            io.dirs(state.parent)
            try:
                _mkdir_private(state)
                created = True
            except FileExistsError:
                pass
        if created:
            io.write(state / '.gitignore', IGNORE, deadline)
            _ignore(state, io)
            marker = {'schema_version': 1, 'owner': OWNER, 'scope_id': secrets.token_hex(32), 'root_key': _root_key(root)}
            io.write(state / 'owner.json', _json(marker), deadline)
            initial = {'schema_version': 1, 'owner': OWNER, 'scope_id': marker['scope_id'], 'revision': 0, 'records': []}
            io.write(state / 'snapshot.json', _json(initial), deadline)
        else:
            _owner(root, state, io)  # Foreign or partial existing state is never initialized.
        with io.locked(state, deadline, created):
            marker, value, signature, ignore_signature = _read_snapshot(root, state, io)
            now = time.time()
            _need(type(now) in (int, float) and math.isfinite(now) and 0 <= now <= MAX_REVISION, 'invalid_clock')
            session_key = _key(marker, [runtime, 'session', session])
            agent_key = _key(marker, [runtime, 'subagent', session, agent]) if agent is not None else None
            identity = (runtime, scope, session_key, agent_key)
            rows = [row for row in value['records'] if not 0 <= now - row['observed_at'] or now - row['observed_at'] < _projection.FRESH_SECONDS]
            rows = [row for row in rows if (row['runtime'], row['scope'], row['session_key'], row['agent_key']) != identity]
            _need(len(rows) < _projection.MAX_OBSERVATIONS, 'quota_exceeded')
            _need(value['revision'] < MAX_REVISION, 'revision_exhausted')
            value['revision'] += 1
            rows.append({'schema_version': 1, 'runtime': runtime, 'scope': scope, 'session_key': session_key,
                'agent_key': agent_key, 'role': role, 'event': event, 'source': source, 'observed_at': now, 'revision': value['revision']})
            value['records'] = sorted(rows, key=lambda row: (row['runtime'], row['scope'], row['session_key'], row['agent_key'] or ''))
            _enabled(root, io)  # An observed opt-out before publication prevents this update.
            _need(_ignore(state, io) == ignore_signature, 'unsafe_state')
            io.write(state / 'snapshot.json', _json(value), deadline, expected=signature)
        return {'status': 'ok', 'reason': None}
    except _Failure as exc:
        return {'status': 'unavailable', 'reason': str(exc)}
    except (OSError, ValueError, TypeError, OverflowError, RecursionError, KeyError):
        return {'status': 'unavailable', 'reason': 'invalid_state'}


def snapshot(project):
    """Read without initializing, locking, purging, recovering, or executing anything."""
    try:
        io = _io()
        root = _root(project, io)
        _enabled(root, io)
        state = root / '.claude' / 'agent-activity'
        _need(state.exists(), 'state_missing')
        _, value, _, _ = _read_snapshot(root, state, io)
        _enabled(root, io)
        return {'status': 'ok', 'reason': None, 'records': value['records'], 'collection_complete': False}
    except _Failure as exc:
        reason = str(exc)
    except (OSError, ValueError, TypeError, OverflowError, RecursionError, KeyError):
        reason = 'invalid_state'
    return {'status': 'unavailable', 'reason': reason, 'records': [], 'collection_complete': False}


def main(argv=None):
    """An optional informative hook never emits payloads or interrupts work."""
    import argparse
    class QuietParser(argparse.ArgumentParser):
        def error(self, message):
            raise ValueError('invalid_arguments')
    try:
        parser = QuietParser(add_help=False)
        parser.add_argument('--runtime', required=True, choices=('claude', 'codex', 'opencode'))
        parser.add_argument('--root', required=True)
        args = parser.parse_args(argv)
        raw = sys.stdin.buffer.read(MAX_BYTES + 1)
        if len(raw) <= MAX_BYTES:
            capture(args.root, runtime=args.runtime, payload=_strict(raw))
    except (Exception, SystemExit):
        pass
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
