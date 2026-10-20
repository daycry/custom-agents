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
import stat
import sys
import time
import unicodedata

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError, ValueError): pass

HERE = Path(__file__).resolve().parent
OWNER = 'custom-agents.agent-activity-v1'
MAX_BYTES = 65536
MAX_EVENTS_FILE = 256 * 1024  # events.json, whole document (I-03)
MAX_INPUT = 2 * 1024 * 1024  # tool events are parsed in memory and never persisted (I-03)
EVENTS = 'events.json'
MAX_CLEAN = 8  # P-EI-1: own old temporaries removed per write
CLEAN_AGE = 60
MAX_REVISION = 2**53 - 1
IGNORE = b'*\n'
# T-43 fix1 (D2) + fix2 (2-1): tool events run asynchronously (I-05: 0 ms synchronous) and wait up to 1 s inside a
# 1.3 s deadline (under the launcher's 2 s child budget), with single attempts that YIELD to a waiting lifecycle
# writer (byte 1 of `.lock`, `StateIO.intent`/`priority`). Lifecycle signals (synchronous) keep 100 ms and 1 s;
# Codex MCP keeps a single attempt (P-EI-3). The ring is read and validated before the lock and reused only if
# its signature is unchanged: a hold with a full 500-event ring went from p50 ~68 / p90 ~84 ms to ~23 / ~37 ms.
TOOL_LOCK_WAIT = 1.0
TOOL_DEADLINE = 1.3


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
try:
    _redact = _load('redact')
except Exception:
    _redact = None  # without the redactor no argument summary is ever produced


def _io(maximum=MAX_BYTES):
    _need(_reader is not None and _state_io is not None and _projection is not None, 'invalid_state')
    return _state_io.StateIO(_reader, _need, _guard, maximum=maximum)


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
    data, signature = io.read(path, MAX_BYTES)
    config = _strict(data)
    _need(type(config) is dict, 'invalid_config')
    session = config.get('sesion', {})
    _need(type(session) is dict, 'invalid_config')
    _need(session.get('actividad') is True, 'disabled')
    return signature


_HEX64 = re.compile(r'[0-9a-f]{64}')
_CONTROL = re.compile(r'[\x00-\x1f\x7f]')


def _hex(value):
    return type(value) is str and len(value) == 64 and _HEX64.fullmatch(value) is not None


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
MAX_TEMPS = 8  # orphans of an interrupted atomic replace; tolerated by readers, never read; writers clean (P-EI-1)
_TEMP = re.compile(r'\.tmp-[a-zA-Z0-9_-]+')


def _inventory(state):
    listing = _reader.list_names(state.parent, state.name, max_entries=len(FIXED_NAMES) + 1 + MAX_TEMPS + 2)
    if listing['status'] == 'ok' and not listing['complete']:
        raise _Failure('state_budget')
    _need(listing['status'] == 'ok' and listing['complete'], 'invalid_state')
    names = set(listing['names'])
    temps = {name for name in names if _TEMP.fullmatch(name)}
    _need(names - temps - {EVENTS} == FIXED_NAMES, 'invalid_state')
    _need(len(temps) <= MAX_TEMPS, 'state_budget')


def _ignore(state, io):
    raw, signature = io.read(state / '.gitignore', len(IGNORE))
    _need(raw == IGNORE, 'invalid_state')
    return signature


def _base(root, state, io):
    io.dirs(state)
    marker, owner_signature = _owner(root, state, io)
    ignore_signature = _ignore(state, io)
    _inventory(state)
    io.file(state / '.lock')
    return marker, owner_signature, ignore_signature


def _clean_temps(state):
    """P-EI-1: under the lock, remove at most MAX_CLEAN own orphan temporaries (regular, nlink 1, > 60 s).
    Nothing happens unless every other name of the directory is the expected inventory."""
    listing = _reader.list_names(state.parent, state.name, max_entries=64)
    if listing['status'] != 'ok' or not listing['complete']:
        return
    names = set(listing['names'])
    temps = sorted(name for name in names if _TEMP.fullmatch(name))
    if names - set(temps) - {EVENTS} != FIXED_NAMES:
        return
    now, removed = time.time(), 0
    for name in temps:
        if removed >= MAX_CLEAN:
            break
        try:
            path = state / name
            info = os.lstat(path)
            if (stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and not _reader._redirected(info)
                    and now - info.st_mtime > CLEAN_AGE):
                path.unlink()
                removed += 1
        except OSError:
            continue


def _read_snapshot(root, state, io):
    marker, owner_signature, ignore_signature = _base(root, state, io)
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


_DOC = frozenset(('schema_version', 'owner', 'scope_id', 'revision', 'config_sig', 'recortado',
    'descartados_por_tamano', 'runs', 'ventanas', 'events'))
_WINDOW_FIELDS = frozenset(('run_key', 'tarea', 'estado', 'abierta_at', 'fin_at'))
_EVENT_FIELDS = frozenset(('schema_version', 'runtime', 'run_key', 'role', 'tool', 'resumen', 'tarea',
    'duracion_ms', 'resultado', 'observed_at', 'revision'))


def _count(value):
    return type(value) is int and 0 <= value <= MAX_REVISION


def _clean_text(value, limit):
    """Same rule as before (no code point below 32 nor 127), as one C-level regex search: the writer
    re-validates the whole 500-event ring under the lock, so a per-character loop held it ~120 ms (T-43 fix1, D2)."""
    return type(value) is str and len(value) <= limit and _CONTROL.search(value) is None


def _valid_window(row):
    return (type(row) is dict and set(row) == _WINDOW_FIELDS and _hex(row['run_key'])
        and _projection.normalize_tarea(row['tarea']) == row['tarea'] and row['estado'] in _projection.WINDOW_STATES
        and _projection._number(row['abierta_at']) and _projection._opt_number(row['fin_at'])
        and (row['estado'] == 'abierta') == (row['fin_at'] is None))


def _valid_event(row, revision):
    return (type(row) is dict and set(row) == _EVENT_FIELDS and row['schema_version'] == 1
        and type(row['schema_version']) is int and row['runtime'] in ('claude', 'codex', 'opencode')
        and _hex(row['run_key']) and (row['role'] is None or row['role'] in _projection.ROLES)
        and _clean_text(row['tool'], 64) and _clean_text(row['resumen'], _projection.SUMMARY_MAX)
        and (row['tarea'] is None or _projection.normalize_tarea(row['tarea']) == row['tarea'])
        and _projection._opt_number(row['duracion_ms']) and row['resultado'] in (None, 'ok', 'error')
        and _projection._number(row['observed_at']) and type(row['revision']) is int
        and 1 <= row['revision'] <= revision)


def _new_events(marker):
    return {'schema_version': 1, 'owner': OWNER, 'scope_id': marker['scope_id'], 'revision': 0, 'config_sig': None,
        'recortado': 0, 'descartados_por_tamano': 0, 'runs': [], 'ventanas': [], 'events': []}


def _validate_events(value, marker):
    _need(type(value) is dict and set(value) == _DOC and type(value['schema_version']) is int
        and value['schema_version'] == 1 and value['owner'] == OWNER and value['scope_id'] == marker['scope_id'],
        'invalid_state')
    _need(_count(value['revision']) and _count(value['recortado']) and _count(value['descartados_por_tamano']), 'invalid_state')
    _need(value['config_sig'] is None or _hex(value['config_sig']), 'invalid_state')
    _need(_projection.project_runs(value['runs'], now=0)['status'] == 'ok', 'invalid_state')
    windows, events = value['ventanas'], value['events']
    _need(type(windows) is list and len(windows) <= _projection.MAX_WINDOWS and all(_valid_window(w) for w in windows), 'invalid_state')
    _need(type(events) is list and len(events) <= _projection.MAX_EVENTS
        and all(_valid_event(e, value['revision']) for e in events), 'invalid_state')
    revisions = [e['revision'] for e in events]
    _need(revisions == sorted(set(revisions)), 'invalid_state')
    return value


def _load_events(root, state, io, marker):
    """The validated document and its file signature (None when the file does not exist yet)."""
    path = state / EVENTS
    if not path.exists():
        return _new_events(marker), None
    raw, signature = io.read(path, MAX_EVENTS_FILE)
    return _validate_events(_strict(raw), marker), signature


def _prune(doc, now):
    """Retention and quotas of runs and windows: oldest first; `recortado` only counts event-ring drops."""
    limit = _projection.RETENTION_SECONDS
    runs = [r for r in doc['runs'] if now - r['last_seen'] < limit]
    runs.sort(key=lambda r: r['last_seen'])
    runs = runs[max(0, len(runs) - _projection.MAX_RUNS):]
    alive = {r['run_key'] for r in runs}
    windows = [w for w in doc['ventanas'] if now - (w['fin_at'] or w['abierta_at']) < limit
        and (w['estado'] == 'abierta' or w['run_key'] in alive)]
    windows.sort(key=lambda w: (w['estado'] == 'abierta', w['fin_at'] or w['abierta_at']))
    doc['runs'] = sorted(runs, key=lambda r: r['run_key'])
    doc['ventanas'] = windows[max(0, len(windows) - _projection.MAX_WINDOWS):]


def _publish_events(root, state, io, doc, signature, ignore_signature, deadline, now, nowait=False):
    """Trim the ring, re-check opt-in and the ignore file, then replace with CAS (`expected=signature`).
    `nowait` (Codex MCP, P-EI-3) makes a single `os.replace` attempt, without the sharing-violation backoff."""
    _prune(doc, now)
    overhead = len(_json(dict(doc, events=[])))
    doc['events'], trimmed = _projection.trim_events(doc['events'], now=now, overhead=overhead)
    doc['recortado'] = min(MAX_REVISION, doc['recortado'] + trimmed)
    raw = _json(doc)
    while len(raw) > MAX_EVENTS_FILE and doc['events']:
        doc['events'].pop(0)
        doc['recortado'] = min(MAX_REVISION, doc['recortado'] + 1)
        raw = _json(doc)
    _need(len(raw) <= MAX_EVENTS_FILE, 'state_budget')
    _enabled(root, io)  # An observed opt-out before publication prevents this update.
    _need(_ignore(state, io) == ignore_signature, 'unsafe_state')
    io.write(state / EVENTS, raw, deadline, expected=signature, retry=not nowait)


def _preload(root, state, io):
    """T-43 fix2 (2-1): the ring read and validated BEFORE the lock (the first open of a freshly replaced
    256 KiB file is the slowest step of a hold); (doc, signature) or None. Never trusted on its own."""
    try:
        marker, _ = _owner(root, state, io)
        doc, signature = _load_events(root, state, io, marker)
        return (doc, signature) if signature is not None else None
    except (_Failure, OSError, ValueError, TypeError, OverflowError, RecursionError, KeyError):
        return None


def _signature(path, io):
    try:
        return io.file(path)
    except (_Failure, OSError):
        return None


def _update_events(root, state, io, config_signature, deadline, mutate, nowait=False, preloaded=None):
    marker, _, ignore_signature = _base(root, state, io)
    now = time.time()
    _need(type(now) in (int, float) and math.isfinite(now) and 0 <= now <= MAX_REVISION, 'invalid_clock')
    if (preloaded is not None and preloaded[0]['scope_id'] == marker['scope_id']
            and _signature(state / EVENTS, io) == preloaded[1]):
        doc, signature = preloaded  # unchanged since it was read and validated: same CAS as the replace
    else:
        doc, signature = _load_events(root, state, io, marker)
    stamp = hashlib.sha256(repr(config_signature).encode('utf-8')).hexdigest()
    if doc['config_sig'] != stamp:  # any edit of dev.json invalidates the open attribution windows (2.5 e)
        doc['ventanas'] = _projection.expire_open(doc['ventanas'], now)
        doc['config_sig'] = stamp
    mutate(doc, marker, now)
    _publish_events(root, state, io, doc, signature, ignore_signature, deadline, now, nowait)


def _run_keys(marker, runtime, scope, session, agent):
    session_key = _key(marker, [runtime, 'session', session])
    if scope == 'subagent':
        return _key(marker, [runtime, 'subagent', session, agent]), session_key, session_key
    return session_key, None, session_key


def _upsert_run(doc, run_key, runtime, scope, session_key, role, now):
    for run in doc['runs']:
        if run['run_key'] == run_key:
            run['last_seen'] = now if run['ended_at'] is None else run['last_seen']
            run['role'] = run['role'] or role
            return run
    run = {'run_key': run_key, 'runtime': runtime, 'scope': scope, 'session_key': session_key, 'role': role,
        'started_at': None, 'last_seen': now, 'ended_at': None}
    doc['runs'].append(run)
    return run


def _lifecycle_mutation(runtime, scope, session, agent, role, event):
    def mutate(doc, marker, now):
        run_key, _, session_key = _run_keys(marker, runtime, scope, session, agent)
        run = _upsert_run(doc, run_key, runtime, scope, session_key, role, now)
        if event in ('response_started', 'execution_started'):
            run.update(started_at=now, ended_at=None, last_seen=now)
        else:
            run.update(ended_at=now, last_seen=now)
    return mutate


def _tool_mutation(entry):
    def mutate(doc, marker, now):
        run_key, parent_key, session_key = _run_keys(marker, entry['runtime'], entry['scope'], entry['session'], entry['agent'])
        _upsert_run(doc, run_key, entry['runtime'], entry['scope'], session_key, entry['role'], now)
        window = entry['window']
        tarea = None if window else _projection.attribute(doc['ventanas'], run_key=run_key, parent_key=parent_key, now=now)
        _need(doc['revision'] < MAX_REVISION, 'revision_exhausted')
        doc['revision'] += 1
        doc['events'].append({'schema_version': 1, 'runtime': entry['runtime'], 'run_key': run_key, 'role': entry['role'],
            'tool': entry['tool'], 'resumen': entry['resumen'], 'tarea': tarea, 'duracion_ms': entry['duracion_ms'],
            'resultado': entry['resultado'], 'observed_at': now, 'revision': doc['revision']})
        if window:
            doc['ventanas'], _ = _projection.apply_window(doc['ventanas'], run_key=run_key, action=window[0],
                tarea=window[1], now=now)
    return mutate


def _id(value):
    return type(value) is str and bool(value) and len(value.encode('utf-8')) <= 512 and all(ord(ch) >= 32 and ord(ch) != 127 for ch in value)


def _role_of(runtime, native_name):
    """Closed role vocabulary for a native agent name; anything unknown is `other`, never the raw name."""
    mapping = _strict(_io().read(HERE / 'native-roles.json', MAX_BYTES)[0])
    _need(type(mapping) is dict and mapping.get('schema_version') == 1
        and type(mapping.get('runtimes')) is dict and type(mapping['runtimes'].get(runtime)) is dict, 'role_map_unavailable')
    return next((role for role, native in mapping['runtimes'][runtime].items()
        if native == native_name and role in _projection.ROLES), 'other')


# ---- tool events (panel-redesign F3): per-runtime payload grammar -------------------------------
# Claude Code: PostToolUse (ok) / PostToolUseFailure (error) carry tool_name, tool_input, optional duration_ms and,
#   inside a subagent, agent_id + agent_type. Codex: PostToolUse only, no agent id (subagents share the parent's
#   session_id), no duration, no result. OpenCode: `tool.execute.after` with sessionID, tool, agent, status, args.
# Neither `tool_response`, prompts nor transcripts are ever read.
_OPENCODE_TOOLS = {'bash': 'Bash', 'read': 'Read', 'write': 'Write', 'edit': 'Edit', 'patch': 'apply_patch',
    'apply_patch': 'apply_patch', 'grep': 'Grep', 'glob': 'Glob', 'webfetch': 'WebFetch', 'task': 'Task', 'skill': 'Skill'}
_INTERPRETER = re.compile(r'(?:python[0-9.]*|pythonw|py)(?:\.exe)?')
_INTERPRETER_FLAG = re.compile(r'-(?:[0-9](?:\.[0-9]+)?|[BIsSuU])')
_TOKEN = re.compile(r'"[^"]*"|\'[^\']*\'|\S+')
_METER_OPTIONS = frozenset(('--state', '--transcript-dir'))
_MAX_DURATION_MS = 2 ** 31


def _is_tool_event(runtime, payload):
    if type(payload) is not dict:
        return False
    if runtime in ('claude', 'codex'):
        return payload.get('hook_event_name') in ('PostToolUse', 'PostToolUseFailure', 'PreToolUse')
    return type(payload.get('type')) is str and payload['type'].startswith('tool.execute.')


def _unquote(token):
    return token[1:-1] if len(token) >= 2 and token[0] == token[-1] and token[0] in '"\'' else token


def meter_window(command):
    """(`start`|`close`, `<slug>/T-XX`) only when the whole command is exactly an invocation of usage-meter.py
    with `--artefacto <slug>/T-XX[-fixN]`; any other shape (chaining, redirects, other flags, free text) is None."""
    if type(command) is not str or len(command) > 4096:
        return None
    tokens = [_unquote(token) for token in _TOKEN.findall(command)]
    base = lambda token: re.split(r'[\\/]', token)[-1].lower()
    if tokens and _INTERPRETER.fullmatch(base(tokens[0])):
        tokens = tokens[1:]
        while tokens and _INTERPRETER_FLAG.fullmatch(tokens[0]):
            tokens = tokens[1:]
    if len(tokens) < 3 or base(tokens[0]) != 'usage-meter.py' or tokens[1] not in ('start', 'close'):
        return None
    action, rest, tarea = tokens[1], tokens[2:], None
    while rest:
        head = rest.pop(0)
        if head == '--artefacto' and tarea is None and rest:
            tarea = rest.pop(0)
        elif head.startswith('--artefacto=') and tarea is None:
            tarea = head[len('--artefacto='):]
        elif head in _METER_OPTIONS and rest:
            rest.pop(0)
        else:
            return None
    tarea = _projection.normalize_tarea(tarea)
    return (action, tarea) if tarea else None


def _duration(value):
    ok = type(value) in (int, float) and math.isfinite(value) and 0 <= value <= _MAX_DURATION_MS
    return int(round(value)) if ok else None


def _tool_entry(root, runtime, payload):
    """Validate a tool event and shape the `record` entry; the argument is reduced to a redacted summary."""
    _need(type(payload.get('cwd')) is str and os.path.normcase(os.path.abspath(payload['cwd'])) == os.path.normcase(str(root)), 'project_mismatch')
    if runtime == 'opencode':
        _need(payload['type'] == 'tool.execute.after', 'unsupported_event')
        data = payload.get('data')
        _need(type(data) is dict and _id(data.get('sessionID')), 'invalid_identity')
        name, tool_input, session, agent = data.get('tool'), data.get('args'), data['sessionID'], None
        status = {'completed': 'ok', 'error': 'error'}.get(data.get('status'))
        role = _role_of('opencode', data['agent']) if type(data.get('agent')) is str and data['agent'] else None
        canonical, duration, scope = _OPENCODE_TOOLS.get(name.lower(), name) if type(name) is str else None, None, 'session'
    else:
        event = payload.get('hook_event_name')
        _need(event == 'PostToolUse' or (event == 'PostToolUseFailure' and runtime == 'claude'), 'unsupported_event')
        name, tool_input, session = payload.get('tool_name'), payload.get('tool_input'), payload.get('session_id')
        _need(_id(session), 'invalid_identity')
        agent, role, scope = None, None, 'session'
        if runtime == 'claude' and ('agent_id' in payload or 'agent_type' in payload):
            _need(_id(payload.get('agent_id')) and type(payload.get('agent_type')) is str, 'invalid_identity')
            agent, scope, role = payload['agent_id'], 'subagent', _role_of(runtime, payload['agent_type'])
        status = None if runtime == 'codex' else 'error' if event == 'PostToolUseFailure' else 'ok'
        duration = _duration(payload.get('duration_ms')) if runtime == 'claude' else None
        canonical = name
    _need(type(name) is str and type(tool_input) is dict, 'invalid_input')
    tool = _strip_controls(name).strip()[:64]
    _need(bool(tool), 'invalid_input')
    window = None
    if canonical in _SHELL and status != 'error':
        window = meter_window(_first(tool_input, 'command', 'cmd'))
    return {'runtime': runtime, 'scope': scope, 'session': session, 'agent': agent, 'role': role, 'tool': tool,
        'resumen': summarize(root, canonical, tool_input), 'duracion_ms': duration, 'resultado': status,
        'window': window, 'nowait': runtime == 'codex' and tool.startswith('mcp__')}


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
        role = _role_of(runtime, payload['agent_type'])
        return 'subagent', session, agent, role, event, 'native_hook'
    native = payload.get('type')
    data = payload.get('data')
    event = 'execution_started' if native == 'session.execution.started' else 'execution_finished' if native in ('session.execution.succeeded', 'session.execution.failed', 'session.execution.interrupted') else 'session_idle' if native == 'session.idle' else None
    if native == 'session.status' and type(data) is dict and type(data.get('status')) is dict and data['status'].get('type') == 'idle':
        event = 'session_idle'
    _need(event is not None, 'unsupported_event')
    _need(type(data) is dict and _id(data.get('sessionID')), 'invalid_identity')
    return 'session', data['sessionID'], None, None, event, 'native_stream'


NO_SUMMARY = '—'
_SHELL = frozenset(('Bash', 'PowerShell', 'exec_command', 'shell', 'local_shell'))
_FILE_TOOLS = frozenset(('Read', 'Write', 'Edit', 'MultiEdit', 'NotebookEdit'))
_SEARCH_TOOLS = frozenset(('Grep', 'Glob'))
_SUBAGENT_TOOLS = frozenset(('Agent', 'Task', 'spawn_agent'))
# Linear (T-44 fix1, C-2): the rest of the line, stripped in Python; `(.+?)\s*$` backtracked
# quadratically on a long run of spaces inside the name.
_PATCH_FILE = re.compile(r'^\*\*\* (?:Add|Update|Delete) File: ([^\n]*)', re.M)
_PEM_OPEN = re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----.*', re.S)
_PRECUT = 8192
# scheme://[userinfo@]host[:port]: only the host is ever kept (no urllib: this hook has no network code)
_URL_HOST = re.compile(r'[A-Za-z][A-Za-z0-9+.\-]*://(?:[^/?#@]*@)?(\[[0-9A-Fa-f:.]+\]|[^/?#:@\[\]\s]+)')


def _text(value):
    return value.strip() if type(value) is str and value.strip() else None


def _first(tool_input, *names):
    for name in names:
        text = _text(tool_input.get(name))
        if text:
            return text
    return None


def _relative(root, value):
    """Project-relative path; an absolute path outside the project keeps only its file name."""
    value = value.strip()
    if re.match(r'[A-Za-z]:[\\/]', value) or value.startswith(('/', '\\')):
        if os.path.isabs(value):
            try:
                rel = os.path.relpath(value, root)
            except ValueError:
                rel = '..'
            if rel != '..' and not rel.startswith('..' + os.sep) and not os.path.isabs(rel):
                return rel.replace(os.sep, '/')
        return '<externa>/' + (re.split(r'[\\/]+', value.rstrip('\\/'))[-1] or '?')
    return value.replace('\\', '/')


def _raw_summary(root, tool, tool_input):
    """Whitelist of what may describe a call; everything else is NO_SUMMARY (never content or output)."""
    if type(tool) is not str or type(tool_input) is not dict:
        return None
    if tool in _SHELL:
        text = _first(tool_input, 'command', 'cmd')
        return re.split(r'\r?\n', text, maxsplit=1)[0] if text else None
    if tool in _FILE_TOOLS:
        many = tool_input.get('paths', tool_input.get('files'))
        if type(many) is list and many:
            return _relative(root, many[0]) if len(many) == 1 and _text(many[0]) else '%d ficheros' % len(many)
        path = _first(tool_input, 'file_path', 'notebook_path', 'filePath', 'path')
        return _relative(root, path) if path else None
    if tool == 'apply_patch':
        found = _PATCH_FILE.findall(tool_input.get('command') if type(tool_input.get('command')) is str else '')
        paths = [path.strip() for path in found if path.strip()]
        return None if not paths else _relative(root, paths[0]) if len(paths) == 1 else '%d ficheros' % len(paths)
    if tool in _SEARCH_TOOLS:
        pattern = _first(tool_input, 'pattern')
        path = _first(tool_input, 'path')
        return None if not pattern else pattern + (' ' + _relative(root, path) if path else '')
    if tool == 'WebFetch':
        match = _URL_HOST.match(_first(tool_input, 'url') or '')
        return match.group(1).lower() if match else None
    if tool == 'WebSearch':
        return _first(tool_input, 'query')
    if tool in _SUBAGENT_TOOLS:
        return _first(tool_input, 'subagent_type', 'agent_type')
    if tool == 'Skill':
        return _first(tool_input, 'skill', 'name')
    return None


def _strip_controls(text):
    text = text.replace('\t', ' ')
    return ''.join(ch for ch in text if unicodedata.category(ch) not in ('Cc', 'Cf', 'Zl', 'Zp'))


def summarize(root, tool, tool_input, *, home=None, usuario=None):
    """<= 160 code points describing a call, or NO_SUMMARY. Fixed order: redact, anonymize, strip
    controls, clip (CA-17, CA-41). Without `redact.py` nothing is ever persisted."""
    try:
        text = _raw_summary(root, tool, tool_input)
        if not text or _redact is None:
            return NO_SUMMARY
        text = _PEM_OPEN.sub(_redact.REDACTADO, _redact.redactar(text[:_PRECUT]))
        root = os.path.abspath(root)
        home = os.path.expanduser('~') if home is None else home
        if usuario is None:
            usuario = os.environ.get('USERNAME') or os.environ.get('USER') or ''
        text = _redact.anonimizar(text, sorted({root, os.path.realpath(root)}), home, usuario)
        text = _strip_controls(text).strip()
        return text[:_projection.SUMMARY_MAX] if text else NO_SUMMARY
    except (OSError, ValueError, TypeError, AttributeError, RecursionError):
        return NO_SUMMARY


def _key(marker, fields):
    return hmac.new(bytes.fromhex(marker['scope_id']), _json(fields), hashlib.sha256).hexdigest()


def _ensure_state(root, state, io, deadline):
    """Create the owned directory when absent (ignore file first, then owner, snapshot and events);
    an existing but foreign or partial one is never adopted. Returns True when this call created it."""
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
        io.write(state / EVENTS, _json(_new_events(marker)), deadline)
    else:
        _owner(root, state, io)  # Foreign or partial existing state is never initialized.
    return created


_ENTRY = {'runtime': str, 'scope': str, 'session': str, 'tool': str, 'resumen': str}


def _entry(value):
    _need(type(value) is dict and set(value) == {'runtime', 'scope', 'session', 'agent', 'role', 'tool', 'resumen',
        'duracion_ms', 'resultado', 'window', 'nowait'}, 'invalid_input')
    _need(all(type(value[k]) is kind for k, kind in _ENTRY.items()), 'invalid_input')
    _need(value['runtime'] in ('claude', 'codex', 'opencode') and value['scope'] in ('subagent', 'session'), 'invalid_input')
    _need(_id(value['session']) and (value['agent'] is None if value['scope'] == 'session' else _id(value['agent'])), 'invalid_identity')
    _need(value['role'] is None or value['role'] in _projection.ROLES, 'invalid_input')
    _need(_clean_text(value['tool'], 64) and _clean_text(value['resumen'], _projection.SUMMARY_MAX), 'invalid_input')
    _need(_projection._opt_number(value['duracion_ms']) and value['resultado'] in (None, 'ok', 'error')
        and type(value['nowait']) is bool, 'invalid_input')
    window = value['window']
    _need(window is None or (type(window) is tuple and len(window) == 2 and window[0] in ('start', 'close')
        and _projection.normalize_tarea(window[1]) == window[1]), 'invalid_input')
    return value


def record(project, entry):
    """Append one tool event to the ring (design 2.5). The hook never retries: a lost event stays lost.
    `entry['nowait']` makes a single lock and replace attempt (Codex MCP tools run synchronously, P-EI-3)."""
    try:
        started, io = time.monotonic(), _io(MAX_EVENTS_FILE)
        entry = _entry(entry)
        deadline = started + (1 if entry['nowait'] else TOOL_DEADLINE)
        root = _root(project, io)
        config_signature = _enabled(root, io)
        state = root / '.claude' / 'agent-activity'
        created = _ensure_state(root, state, io, deadline)
        stop = min(deadline, started + (0 if entry['nowait'] else TOOL_LOCK_WAIT))
        preloaded = _preload(root, state, io)
        while True:  # single non-blocking attempts that yield to a waiting lifecycle writer (2-1)
            try:
                with io.locked(state, deadline, created, wait=0, priority='yield'):
                    _clean_temps(state)
                    _update_events(root, state, io, config_signature, deadline, _tool_mutation(entry),
                        entry['nowait'], preloaded)
                return {'status': 'ok', 'reason': None}
            except _Failure as exc:
                if str(exc) != 'state_busy' or time.monotonic() >= stop:
                    raise
            time.sleep(min(0.005, max(0, stop - time.monotonic())))

    except _Failure as exc:
        return {'status': 'unavailable', 'reason': str(exc)}
    except (OSError, ValueError, TypeError, OverflowError, RecursionError, KeyError):
        return {'status': 'unavailable', 'reason': 'invalid_state'}


def count_oversize(project):
    """An input over MAX_INPUT was not parsed: only an identity-less counter changes. Never initializes."""
    try:
        deadline, io = time.monotonic() + 1, _io(MAX_EVENTS_FILE)
        root = _root(project, io)
        config_signature = _enabled(root, io)
        state = root / '.claude' / 'agent-activity'
        _need(state.exists(), 'state_missing')
        _owner(root, state, io)
        with io.locked(state, deadline, False):
            _clean_temps(state)
            def mutate(doc, marker, now):
                doc['descartados_por_tamano'] = min(MAX_REVISION, doc['descartados_por_tamano'] + 1)
            _update_events(root, state, io, config_signature, deadline, mutate)
        return {'status': 'ok', 'reason': None}
    except _Failure as exc:
        return {'status': 'unavailable', 'reason': str(exc)}
    except (OSError, ValueError, TypeError, OverflowError, RecursionError, KeyError):
        return {'status': 'unavailable', 'reason': 'invalid_state'}


def capture(project, *, runtime, payload):
    """Receive a native declaration; return an observable status without free text."""
    try:
        deadline, io = time.monotonic() + 1, _io(MAX_EVENTS_FILE)
        root = _root(project, io)
        if _is_tool_event(runtime, payload):
            _need(runtime in ('claude', 'codex', 'opencode') and payload.get('hook_event_name') != 'PreToolUse', 'unsupported_event')
            if len(_json(payload)) > MAX_INPUT:
                count_oversize(root)
                raise _Failure('input_budget')
            return record(root, _tool_entry(root, runtime, payload))
        scope, session, agent, role, event, source = _payload(root, runtime, payload)
        config_signature = _enabled(root, io)
        state = root / '.claude' / 'agent-activity'
        created = _ensure_state(root, state, io, deadline)
        with io.intent(state):  # 2-1: tool writers stop entering while this one prepares and waits
            return _capture_locked(root, state, io, deadline, created, config_signature,
                runtime, scope, session, agent, role, event, source)
    except _Failure as exc:
        return {'status': 'unavailable', 'reason': str(exc)}
    except (OSError, ValueError, TypeError, OverflowError, RecursionError, KeyError):
        return {'status': 'unavailable', 'reason': 'invalid_state'}


def _capture_locked(root, state, io, deadline, created, config_signature, runtime, scope, session, agent, role, event,
        source):
    """The lifecycle write: snapshot first, then the (secondary) history, under one hold."""
    preloaded = _preload(root, state, io)
    with io.locked(state, deadline, created, priority='claim'):  # tool writers yield to it (2-1)
        _clean_temps(state)
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
        try:  # the history is secondary: a damaged events.json never stops the live snapshot
            _update_events(root, state, io, config_signature, deadline,
                _lifecycle_mutation(runtime, scope, session, agent, role, event), preloaded=preloaded)
        except (_Failure, OSError, ValueError, TypeError, OverflowError, RecursionError, KeyError):
            pass
    return {'status': 'ok', 'reason': None}


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


def history(project):
    """Read the run/window/event history without initializing, locking, purging or repairing anything."""
    empty = {'runs': [], 'ventanas': [], 'events': [], 'recortado': 0, 'descartados_por_tamano': 0}
    try:
        io = _io(MAX_EVENTS_FILE)
        root = _root(project, io)
        _enabled(root, io)
        state = root / '.claude' / 'agent-activity'
        _need(state.exists(), 'state_missing')
        marker, owner_signature, ignore_signature = _base(root, state, io)
        doc, _ = _load_events(root, state, io, marker)
        _need(io.file(state / 'owner.json') == owner_signature and _ignore(state, io) == ignore_signature, 'unsafe_state')
        _enabled(root, io)
        now = time.time()
        return {'status': 'ok', 'reason': None, 'runs': doc['runs'], 'ventanas': doc['ventanas'],
            'events': _projection.project_events(doc['events'], now=now), 'recortado': doc['recortado'],
            'descartados_por_tamano': doc['descartados_por_tamano'], 'collection_complete': False}
    except _Failure as exc:
        reason = str(exc)
    except (OSError, ValueError, TypeError, OverflowError, RecursionError, KeyError):
        reason = 'invalid_state'
    return dict(empty, status='unavailable', reason=reason, collection_complete=False)


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
        raw = sys.stdin.buffer.read(MAX_INPUT + 1)
        if len(raw) > MAX_INPUT:
            count_oversize(args.root)
        else:
            capture(args.root, runtime=args.runtime, payload=_strict(raw))
    except (Exception, SystemExit):
        pass
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
