"""Bounded projection of native activity signals; freshness is not liveness.

The writer must supply its reception time and pseudonymous identifiers. This
projection has no I/O, reads no transcript and changes no execution state.
"""
import json
import math
import re

FRESH_SECONDS = 60
MAX_OBSERVATIONS = 64
ROLES = frozenset(('analyst', 'evaluator', 'architect', 'planner', 'implementer',
    'reviewer', 'qa', 'documenter', 'knowledge-curator', 'nemesis', 'other'))
FIELDS = frozenset(('schema_version', 'runtime', 'scope', 'session_key',
    'agent_key', 'role', 'event', 'source', 'observed_at', 'revision'))
STATES = {'response_started': 'recent_start',
    'response_finished': 'recent_response_end', 'execution_started': 'recent_start',
    'execution_finished': 'recent_execution_end', 'session_idle': 'recent_idle'}


def _number(value):
    return type(value) in (int, float) and 0 <= value <= 2**53 - 1 and math.isfinite(value)


def _key(value):
    return type(value) is str and re.fullmatch('[a-f0-9]{64}', value) is not None


def _valid(row):
    if type(row) is not dict or set(row) != FIELDS:
        return False
    if type(row['schema_version']) is not int or row['schema_version'] != 1:
        return False
    if row['runtime'] not in ('claude', 'codex', 'opencode') or not _key(row['session_key']):
        return False
    if not _number(row['observed_at']) or type(row['revision']) is not int or not 1 <= row['revision'] <= 2**53 - 1:
        return False
    if row['scope'] == 'subagent':
        return (row['runtime'] in ('claude', 'codex') and row['source'] == 'native_hook'
            and _key(row['agent_key']) and row['role'] in ROLES
            and row['event'] in ('response_started', 'response_finished'))
    if row['scope'] == 'session':
        return (row['agent_key'] is None and row['role'] is None
            and row['source'] == ('native_stream' if row['runtime'] == 'opencode' else 'native_hook')
            and row['event'] in ('execution_started', 'execution_finished', 'session_idle'))
    return False


def project_activity(records, *, now):
    """Validate the entire snapshot before projecting any signal, with a 60 s TTL.

Recent end signals only describe response/execution boundaries. A future clock
or expired signal yields unknown; neither means that an agent stopped or died.
Identifiers and runtime/source metadata are declarations, not authentication.
"""
    invalid = {'schema_version': 1, 'status': 'invalid_snapshot',
        'complete': False, 'observations': []}
    if not _number(now) or type(records) is not list or len(records) > MAX_OBSERVATIONS:
        return invalid
    try:
        if any(not _valid(row) for row in records):
            return invalid
        identities = {(row['runtime'], row['scope'], row['session_key'], row['agent_key']) for row in records}
        if len(identities) != len(records):
            return invalid
    except (TypeError, ValueError, OverflowError):
        return invalid
    observations = []
    for row in records:
        age = now - row['observed_at']
        recent = 0 <= age < FRESH_SECONDS
        item = {key: row[key] for key in ('runtime', 'scope', 'session_key',
            'agent_key', 'role', 'source', 'observed_at', 'revision')}
        item.update(age_seconds=age if age >= 0 else None,
            state=STATES[row['event']] if recent else 'unknown',
            live_process_proven=False, agent_destroyed_proven=False)
        observations.append(item)
    return {'schema_version': 1, 'status': 'ok', 'complete': True,
        'observations': observations}


# ---- history (panel-redesign F3): pure projection of runs, attribution windows and tool events ---
# No I/O. The store (`agent-activity-store.py`) owns persistence; these are the rules it applies.
MAX_EVENTS = 500
MAX_EVENTS_BYTES = 256 * 1024
RETENTION_SECONDS = 24 * 3600
MAX_INPUT_BYTES = 2 * 1024 * 1024
SUMMARY_MAX = 160
MAX_RUNS = 64
MAX_WINDOWS = 64
QUARANTINE_SECONDS = 5
RUN_STATES = ('en_curso', 'sin_senal_reciente', 'respuesta_terminada')
WINDOW_STATES = ('abierta', 'cerrada', 'reemplazada', 'caducada')
_TAREA = re.compile(r'([a-z0-9][a-z0-9._-]*)/(T-\d+)(?:-fix\d+)?')
_RUN_FIELDS = frozenset(('run_key', 'runtime', 'scope', 'session_key', 'role', 'started_at', 'last_seen', 'ended_at'))


def _opt_number(value):
    return value is None or _number(value)


def _valid_run(row):
    return (type(row) is dict and set(row) == _RUN_FIELDS and _key(row['run_key']) and _key(row['session_key'])
        and row['runtime'] in ('claude', 'codex', 'opencode') and row['scope'] in ('subagent', 'session')
        and (row['role'] is None or row['role'] in ROLES) and _opt_number(row['started_at'])
        and _number(row['last_seen']) and _opt_number(row['ended_at']))


def project_runs(runs, *, now, events=None):
    """One row per run. `sin_senal_reciente` freezes the duration at the last signal; `respuesta_terminada`
    needs an observed stop. Neither state proves a live process or a destroyed agent."""
    invalid = {'schema_version': 1, 'status': 'invalid_runs', 'runs': []}
    if not _number(now) or type(runs) is not list or len(runs) > MAX_RUNS:
        return invalid
    try:
        if any(not _valid_run(row) for row in runs) or len({row['run_key'] for row in runs}) != len(runs):
            return invalid
    except (TypeError, ValueError, OverflowError):
        return invalid
    last_tool = {}
    for event in sorted((e for e in (events or []) if type(e) is dict), key=lambda e: e.get('revision', 0)):
        last_tool[event.get('run_key')] = event.get('tool')
    out = []
    for row in runs:
        age = now - row['last_seen']
        if row['ended_at'] is not None:
            state, end = 'respuesta_terminada', row['ended_at']
        elif 0 <= age < FRESH_SECONDS:
            state, end = 'en_curso', now
        else:
            state, end = 'sin_senal_reciente', row['last_seen']
        started = row['started_at']
        out.append(dict(row, estado=state, age_seconds=age if age >= 0 else None,
            duration_seconds=None if started is None else max(0, end - started),
            last_tool=last_tool.get(row['run_key']), live_process_proven=False, agent_destroyed_proven=False))
    return {'schema_version': 1, 'status': 'ok', 'runs': out}


def normalize_tarea(text):
    """`<slug>/T-07` or `<slug>/T-07-fix2` -> `<slug>/T-07`; anything else (incl. `lote-<n>`) -> None."""
    match = _TAREA.fullmatch(text) if type(text) is str else None
    return match.group(1) + '/' + match.group(2) if match else None


def transition_window(window, estado, now):
    """`abierta` is the only state that can change; every other state is terminal."""
    if window.get('estado') != 'abierta' or estado not in WINDOW_STATES or estado == 'abierta':
        raise ValueError('invalid_window_transition')
    return dict(window, estado=estado, fin_at=now)


def apply_window(windows, *, run_key, action, tarea, now):
    """`start` replaces the run's open window; `close` needs an open window of that task.
    Returns (windows, accepted); a rejected action leaves the windows unchanged."""
    tarea = normalize_tarea(tarea)
    if tarea is None or action not in ('start', 'close'):
        return list(windows), False
    out, accepted = [], False
    for window in windows:
        if window['run_key'] == run_key and window['estado'] == 'abierta':
            if action == 'start':
                window = transition_window(window, 'reemplazada', now)
            elif window['tarea'] == tarea and not accepted:
                window, accepted = transition_window(window, 'cerrada', now), True
        out.append(window)
    if action == 'start':
        out.append({'run_key': run_key, 'tarea': tarea, 'estado': 'abierta', 'abierta_at': now, 'fin_at': None})
        accepted = True
    return (out if accepted else list(windows)), accepted


def expire_open(windows, now):
    """A stale configuration signature invalidates every open window (design 2.5 e)."""
    return [transition_window(w, 'caducada', now) if w['estado'] == 'abierta' else w for w in windows]


def attribute(windows, *, run_key, parent_key, now):
    """Task of an event: the run's only open window or, with none, the parent session's only open window.
    Zero or several -> None ("sin atribuir"); `lote-<n>` never attributes. Events within QUARANTINE_SECONDS
    of any transition in those scopes are not attributed (the 5 s bound of out-of-order delivery)."""
    scopes = [k for k in (run_key, parent_key) if k]
    for window in windows:
        if window['run_key'] in scopes:
            for at in (window.get('abierta_at'), window.get('fin_at')):
                if at is not None and 0 <= now - at < QUARANTINE_SECONDS:
                    return None
    for scope in scopes:
        tasks = [w['tarea'] for w in windows if w['run_key'] == scope and w['estado'] == 'abierta'
            and normalize_tarea(w['tarea']) == w['tarea']]
        if tasks:
            return tasks[0] if len(tasks) == 1 else None
    return None


def trim_events(events, *, now, overhead=0):
    """Retention (24 h) then the ring caps, oldest first. Returns (kept, trimmed): only cap drops count."""
    kept = [e for e in events if now - e['observed_at'] < RETENTION_SECONDS]
    trimmed = max(0, len(kept) - MAX_EVENTS)
    kept = kept[trimmed:]
    sizes = [len(json.dumps(e, separators=(',', ':'), ensure_ascii=True)) + 1 for e in kept]
    total = sum(sizes) + overhead
    drop = 0
    while drop < len(kept) and total > MAX_EVENTS_BYTES:
        total -= sizes[drop]
        drop += 1
    return kept[drop:], trimmed + drop


def project_events(events, *, now, run_key=None):
    """Reception order (`revision`), not execution order; drops what exceeded the retention."""
    return sorted((e for e in events if now - e['observed_at'] < RETENTION_SECONDS
        and (run_key is None or e['run_key'] == run_key)), key=lambda e: e['revision'])
