"""Freshness describes an observed signal, never an indefinite live process."""
import copy
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

HERE = Path(__file__).parent
SCRIPT = HERE / 'agent-activity.py'


def load():
    if not SCRIPT.exists():
        return SimpleNamespace(project_activity=lambda *a, **k:
            {'schema_version': 1, 'status': 'unavailable', 'observations': []})
    spec = importlib.util.spec_from_file_location('activity_test_owner', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def signal(**changes):
    row = dict(schema_version=1, runtime='codex', scope='subagent',
        session_key='1' * 64, agent_key='2' * 64, role='implementer',
        event='response_started', source='native_hook', observed_at=1000,
        revision=1)
    row.update(changes)
    return row


@pytest.mark.parametrize('age,expected', [(0, 'recent_start'), (59.999, 'recent_start'),
    (60, 'unknown'), (3600, 'unknown')])
def test_start_signal_expires_without_inventing_a_stop(age, expected):
    result = load().project_activity([signal()], now=1000 + age)
    assert result['status'] == 'ok'
    assert result['observations'][0]['state'] == expected
    assert result['observations'][0]['live_process_proven'] is False


@pytest.mark.parametrize('runtime', ['claude', 'codex'])
def test_recent_response_end_is_not_agent_destruction(runtime):
    result = load().project_activity([signal(runtime=runtime, event='response_finished')], now=1001)
    assert result['status'] == 'ok'
    assert result['observations'][0]['state'] == 'recent_response_end'
    assert result['observations'][0]['agent_destroyed_proven'] is False


def test_opencode_execution_signal_does_not_invent_a_subagent():
    row = signal(runtime='opencode', scope='session', agent_key=None, role=None,
        source='native_stream', event='execution_finished')
    result = load().project_activity([row], now=1001)
    assert result['status'] == 'ok'
    assert result['observations'][0]['state'] == 'recent_execution_end'
    assert result['observations'][0]['agent_destroyed_proven'] is False


def test_projection_is_readonly_and_uses_no_free_text_or_raw_identifiers():
    rows = [signal()]
    before = copy.deepcopy(rows)
    result = load().project_activity(rows, now=1001)
    assert rows == before and result['status'] == 'ok'
    item = result['observations'][0]
    assert set(item) == {'runtime', 'scope', 'session_key', 'agent_key', 'role',
        'source', 'observed_at', 'age_seconds', 'state', 'revision',
        'live_process_proven', 'agent_destroyed_proven'}


@pytest.mark.parametrize('changes', [{'prompt': 'private'}, {'tool_input': {'command': 'private'}},
    {'role': '<script>private</script>'}, {'runtime': 'unknown'}, {'scope': 'pid'},
    {'event': 'destroyed'}, {'session_key': 'raw-session'}, {'agent_key': '../escape'},
    {'observed_at': True}, {'observed_at': float('nan')}, {'revision': True},
    {'revision': 0}, {'source': 'claimed'}])
def test_malformed_snapshot_is_not_partially_accepted(changes):
    other = signal(agent_key='3' * 64)
    other.update(changes)
    result = load().project_activity([signal(), other], now=1001)
    assert result['status'] == 'invalid_snapshot' and result['observations'] == []


def test_duplicate_identity_and_future_clock_are_explicit():
    owner = load()
    assert owner.project_activity([signal(), signal(revision=2)], now=1001)['status'] == 'invalid_snapshot'
    result = owner.project_activity([signal()], now=999)
    assert result['status'] == 'ok'
    assert result['observations'][0]['state'] == 'unknown'
    assert result['observations'][0]['age_seconds'] is None


def test_no_data_and_aggregate_limit():
    owner = load()
    assert owner.project_activity([], now=1000)['status'] == 'ok'
    rows = [signal(agent_key=format(i + 1, '064x')) for i in range(64)]
    assert len(owner.project_activity(rows, now=1001)['observations']) == 64
    assert owner.project_activity(rows + [signal(agent_key='f' * 64)], now=1001)['status'] == 'invalid_snapshot'


@pytest.mark.parametrize('now', [True, float('nan'), float('inf'), -1])
def test_invalid_reader_clock_never_claims_freshness(now):
    result = load().project_activity([signal()], now=now)
    assert result['status'] == 'invalid_snapshot' and result['observations'] == []


# ---- panel-redesign T-41: pure projection of runs, windows and events (no I/O) ------------------
K1, K2, K3 = 'a' * 64, 'b' * 64, 'c' * 64


def run(**changes):
    row = dict(run_key=K1, runtime='claude', scope='subagent', session_key=K3, role='implementer',
        started_at=1000.0, last_seen=1010.0, ended_at=None)
    row.update(changes)
    return row


def test_history_constants_and_snapshot_contract_unchanged():
    m = load()
    assert (m.MAX_EVENTS, m.MAX_EVENTS_BYTES, m.RETENTION_SECONDS) == (500, 256 * 1024, 24 * 3600)
    assert (m.MAX_INPUT_BYTES, m.SUMMARY_MAX, m.MAX_RUNS, m.MAX_WINDOWS) == (2 * 1024 * 1024, 160, 64, 64)
    assert (m.FRESH_SECONDS, m.MAX_OBSERVATIONS) == (60, 64)


def test_run_61_seconds_is_without_recent_signal_with_frozen_duration():
    m = load()
    fresh = m.project_runs([run()], now=1030)['runs'][0]
    assert fresh['estado'] == 'en_curso' and fresh['duration_seconds'] == 30
    stale = m.project_runs([run()], now=1010 + 61)['runs'][0]
    assert stale['estado'] == 'sin_senal_reciente' and stale['duration_seconds'] == 10
    later = m.project_runs([run()], now=1010 + 9999)['runs'][0]
    assert later['duration_seconds'] == 10 and later['estado'] == 'sin_senal_reciente'
    assert stale['live_process_proven'] is False and stale['agent_destroyed_proven'] is False
    assert 'terminad' not in stale['estado'] and 'muert' not in stale['estado']


def test_ended_run_is_finished_and_late_tool_does_not_extend_it():
    m = load()
    row = run(ended_at=1020.0, last_seen=1500.0)  # a late PostToolUse moved last_seen, not the end
    out = m.project_runs([row], now=1600)['runs'][0]
    assert out['estado'] == 'respuesta_terminada' and out['duration_seconds'] == 20


def test_run_without_start_never_becomes_finished_without_stop():
    m = load()
    out = m.project_runs([run(started_at=None)], now=1015)['runs'][0]
    assert out['estado'] == 'en_curso' and out['duration_seconds'] is None
    assert m.project_runs([run(started_at=None)], now=5000)['runs'][0]['estado'] == 'sin_senal_reciente'


def test_future_last_seen_gives_unknown_age_never_a_conclusion():
    m = load()
    out = m.project_runs([run(last_seen=9000.0)], now=1100)['runs'][0]
    assert out['age_seconds'] is None and out['estado'] == 'sin_senal_reciente'


def test_runs_validated_as_a_whole_and_last_tool_from_events():
    m = load()
    assert m.project_runs([run(), run(run_key='x')], now=1)['status'] == 'invalid_runs'
    assert m.project_runs([run(), run()], now=1)['status'] == 'invalid_runs'
    assert m.project_runs([run(role='x' * 5, runtime='nope')], now=1)['status'] == 'invalid_runs'
    events = [dict(run_key=K1, tool='Read', revision=3, observed_at=1005.0),
        dict(run_key=K1, tool='Bash', revision=7, observed_at=1008.0), dict(run_key=K2, tool='Grep', revision=9, observed_at=1009.0)]
    out = m.project_runs([run()], now=1030, events=events)['runs'][0]
    assert out['last_tool'] == 'Bash'


def window(**changes):
    row = dict(run_key=K1, tarea='plan/T-07', estado='abierta', abierta_at=1000.0, fin_at=None)
    row.update(changes)
    return row


def test_window_start_close_and_replace_vocabulary():
    m = load()
    ws, ok = m.apply_window([], run_key=K1, action='start', tarea='plan/T-07', now=1000)
    assert ok and [w['estado'] for w in ws] == ['abierta']
    ws, ok = m.apply_window(ws, run_key=K1, action='start', tarea='plan/T-08', now=1100)
    assert ok and sorted(w['estado'] for w in ws) == ['abierta', 'reemplazada']
    ws, ok = m.apply_window(ws, run_key=K1, action='close', tarea='plan/T-08', now=1200)
    assert ok and sorted(w['estado'] for w in ws) == ['cerrada', 'reemplazada']
    assert all(w['fin_at'] is not None for w in ws)


def test_close_without_matching_open_window_is_rejected_unchanged():
    m = load()
    ws = [window(estado='cerrada', fin_at=1100.0)]
    again, ok = m.apply_window(ws, run_key=K1, action='close', tarea='plan/T-07', now=1200)
    assert not ok and again == ws
    other, ok = m.apply_window([window()], run_key=K1, action='close', tarea='plan/T-09', now=1200)
    assert not ok and other[0]['estado'] == 'abierta'


def test_closed_to_open_without_start_is_rejected():
    m = load()
    with pytest.raises(ValueError):
        m.transition_window(window(estado='cerrada', fin_at=1.0), 'abierta', 5)
    with pytest.raises(ValueError):
        m.transition_window(window(estado='reemplazada', fin_at=1.0), 'cerrada', 5)
    assert m.transition_window(window(), 'caducada', 5)['estado'] == 'caducada'


def test_expire_open_windows_marks_only_open_ones():
    m = load()
    ws = m.expire_open([window(), window(estado='cerrada', fin_at=3.0, tarea='plan/T-08')], now=50)
    assert [w['estado'] for w in ws] == ['caducada', 'cerrada']


@pytest.mark.parametrize('text,expected', [('plan/T-07', 'plan/T-07'), ('plan/T-07-fix2', 'plan/T-07'),
    ('plan/T-7-fix10', 'plan/T-7'), ('plan/lote-3', None), ('T-07', None), ('plan/T-07; rm', None), ('', None), (None, None)])
def test_task_key_grammar_and_fix_normalization(text, expected):
    assert load().normalize_tarea(text) == expected


def test_lote_never_opens_a_window():
    m = load()
    ws, ok = m.apply_window([], run_key=K1, action='start', tarea='plan/lote-3', now=1)
    assert not ok and ws == []


def test_attribution_exactly_one_window_in_run_else_parent_else_none():
    m = load()
    now = 2000
    assert m.attribute([window()], run_key=K1, parent_key=K3, now=now) == 'plan/T-07'
    assert m.attribute([window(), window(tarea='plan/T-08')], run_key=K1, parent_key=K3, now=now) is None
    parent = window(run_key=K3, tarea='plan/T-09')
    assert m.attribute([parent], run_key=K1, parent_key=K3, now=now) == 'plan/T-09'
    assert m.attribute([parent, window(run_key=K3, tarea='plan/T-10')], run_key=K1, parent_key=K3, now=now) is None
    # the run's own single window wins over the parent's
    assert m.attribute([window(), parent], run_key=K1, parent_key=K3, now=now) == 'plan/T-07'
    # closed / replaced / expired windows never attribute; nothing at all is «sin atribuir»
    assert m.attribute([window(estado='cerrada', fin_at=1.0)], run_key=K1, parent_key=K3, now=now) is None
    assert m.attribute([], run_key=K1, parent_key=None, now=now) is None


def test_lote_window_present_in_data_never_attributes():
    m = load()
    assert m.attribute([window(tarea='plan/lote-2')], run_key=K1, parent_key=K3, now=2000) is None


def test_quarantine_after_any_window_transition_for_five_seconds():
    m = load()
    w = window(abierta_at=1000.0)
    assert m.attribute([w], run_key=K1, parent_key=None, now=1004.9) is None
    assert m.attribute([w], run_key=K1, parent_key=None, now=1005.0) == 'plan/T-07'
    closed = window(estado='cerrada', abierta_at=1000.0, fin_at=1100.0)
    other = window(tarea='plan/T-08', abierta_at=1100.0)
    assert m.attribute([closed, other], run_key=K1, parent_key=None, now=1102) is None
    assert m.attribute([closed, other], run_key=K1, parent_key=None, now=1106) == 'plan/T-08'
    # a transition of the parent's window also quarantines the child's events
    parent = window(run_key=K3, tarea='plan/T-09', abierta_at=1000.0)
    assert m.attribute([parent], run_key=K1, parent_key=K3, now=1003) is None


def ev(i, at, size=0):
    return dict(schema_version=1, runtime='claude', run_key=K1, role=None, tool='Bash', resumen='x' * size,
        tarea=None, duracion_ms=None, resultado=None, observed_at=float(at), revision=i)


def test_ring_cap_501_events_keeps_500_and_counts_one_trimmed():
    m = load()
    kept, trimmed = m.trim_events([ev(i, 1000) for i in range(1, 502)], now=1001)
    assert len(kept) == 500 and trimmed == 1 and kept[0]['revision'] == 2 and kept[-1]['revision'] == 501


def test_ring_cap_by_bytes_drops_oldest_first():
    m = load()
    events = [ev(i, 1000, size=10000) for i in range(1, 41)]  # ~400 KB
    kept, trimmed = m.trim_events(events, now=1001)
    import json
    assert len(json.dumps(kept, separators=(',', ':'))) <= m.MAX_EVENTS_BYTES
    assert trimmed == 40 - len(kept) > 0 and kept[-1]['revision'] == 40


def test_retention_24h_purges_old_events_without_counting_them_as_trimmed():
    m = load()
    now = 1_000_000
    kept, trimmed = m.trim_events([ev(1, now - 24 * 3600 - 1), ev(2, now - 24 * 3600 + 1)], now=now)
    assert [e['revision'] for e in kept] == [2] and trimmed == 0


def test_project_events_orders_by_reception_and_filters_retention():
    m = load()
    now = 500_000
    events = [ev(5, now - 10), ev(2, now - 20), ev(9, now - 90_000)]
    out = m.project_events(events, now=now)
    assert [e['revision'] for e in out] == [2, 5]
    assert [e['revision'] for e in m.project_events(events, now=now, run_key=K2)] == []
