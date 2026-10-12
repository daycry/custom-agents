"""Bounded projection of native activity signals; freshness is not liveness.

The writer must supply its reception time and pseudonymous identifiers. This
projection has no I/O, reads no transcript and changes no execution state.
"""
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
