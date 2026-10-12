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
