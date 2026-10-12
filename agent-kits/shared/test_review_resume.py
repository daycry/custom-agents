"""Read-only review reminders: exact scope, current version, no delivery or ack."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

HERE = Path(__file__).parent
INIT = 'docs/roadmap/2026-10-09-owned'

def load(filename):
    spec = importlib.util.spec_from_file_location('review_resume_' + filename.replace('-', '_'), HERE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def snapshot(root):
    return {p.relative_to(root).as_posix(): (p.read_bytes(), p.stat().st_mode, p.stat().st_mtime_ns)
            for p in root.rglob('*') if p.is_file()}

@pytest.fixture
def owned(tmp_path):
    plan = tmp_path / INIT / 'improvement-plan.md'
    plan.parent.mkdir(parents=True)
    plan.write_text('# Owned plan\n\n## Scope\nPrivate body\n', encoding='utf-8')
    (plan.parent / 'tasks.md').write_text('---\nestado: en-progreso\n---\n'
        '## Fase 1 — Trabajo\n### T-01 — Implementación\n- **Estado**: en-progreso\n', encoding='utf-8')
    return SimpleNamespace(root=tmp_path, plan=plan, state=tmp_path / '.claude/plan-review',
        owner=load('plan-review.py'), progress=load('progress-report.py'))

def open_(o, initiative=INIT, gate='plan-ok'):
    result = o.owner.open_review(o.root, initiative, state_root=o.state, gate_key=gate)
    assert result['status'] == 'ok', result
    return result['review']

def listing(o, initiative=INIT):
    before = snapshot(o.root)
    result = o.owner.list_reminders(o.root, initiative, state_root=o.state)
    assert snapshot(o.root) == before, 'reminder mutated file bytes, mode or timestamp'
    return result

def test_absent_store_is_explicit_and_not_created(owned):
    result = listing(owned)
    assert result == {'schema_version': 1, 'status': 'not_registered', 'reason': 'review_not_found',
        'complete': True, 'reviews': [], 'reviews_omitted': 0, 'approval_granted': False}
    assert not owned.state.exists()

def test_open_submitted_delivered_consumed_remain_distinct_without_side_effects(owned):
    o = owned
    r = open_(o)
    row = listing(o)['reviews'][0]
    assert row['review_id'] == r['review_id'] and row['version'] == r['version']
    assert row['state'] == 'pendiente' and row['decision_recorded'] is False
    assert row['version_status'] == 'current' and row['gate_key'] == 'plan-ok'
    result = o.owner.submit_decision(o.root, r['review_id'], r['version'], 'approve', [],
        expected_revision=r['revision'], state_root=o.state)
    assert result['status'] == 'ok'
    row = listing(o)['reviews'][0]
    assert row['state'] == 'pendiente' and row['decision_recorded'] is True
    assert row['approval_granted'] is False
    r = o.owner.receive_decision(o.root, r['review_id'], r['version'], gate_key='plan-ok', state_root=o.state)['review']
    assert listing(o)['reviews'][0]['state'] == 'entregada'
    result = o.owner.ack_decision(o.root, r['review_id'], r['version'], gate_key='plan-ok',
        decision_id=r['decision']['decision_id'], delivery_id=r['delivery']['delivery_id'], state_root=o.state)
    assert result['status'] == 'ok'
    assert listing(o)['reviews'][0]['state'] == 'consumida'

def test_stale_version_visible_and_missing_artifact_not_presented_current(owned):
    o = owned
    r = open_(o)
    o.plan.write_text('# Revised plan\n', encoding='utf-8')
    row = listing(o)['reviews'][0]
    assert row['version_status'] == 'version_changed' and row['version'] == r['version']
    o.plan.unlink()
    result = listing(o)
    assert result['status'] == 'unavailable' and result['reason'] == 'plan_missing'
    assert not result['complete'] and not result['reviews']

def test_exact_initiative_filter_and_foreign_root_marker_rejected(owned, tmp_path):
    o = owned
    open_(o)
    other = 'docs/roadmap/2026-10-09-other'
    path = o.root / other / 'improvement-plan.md'
    path.parent.mkdir()
    path.write_text('# Other\n', encoding='utf-8')
    assert listing(o, other)['reviews'] == []
    assert listing(o, other)['status'] == 'ok'
    marker = o.state / 'owner.json'
    record = json.loads(marker.read_text())
    record['root_key'] = '0'*64
    marker.write_text(json.dumps(record), encoding='utf-8')
    result = listing(o)
    assert result['reason'] == 'unowned_state' and not result['complete']

@pytest.mark.parametrize('fault', ['malformed', 'unknown_leaf', 'oversized'])
def test_invalid_inventory_never_looks_empty(owned, fault):
    o = owned
    r = open_(o)
    record = o.state / ('r-' + r['review_id'] + '.json')
    if fault == 'malformed':
        record.write_text('{}', encoding='utf-8')
    elif fault == 'unknown_leaf':
        (o.state / 'foreign.txt').write_text('private', encoding='utf-8')
    else:
        record.write_bytes(b'x' * (o.owner.MAX_RECORD_BYTES + 1))
    result = listing(o)
    assert result['status'] == 'unavailable' and not result['complete']
    assert result['reviews'] == [] and result['reason'] in ('invalid_state', 'unowned_state')

def test_reader_detects_changed_record_between_inventory_observations(owned, monkeypatch):
    o = owned
    r = open_(o)
    path = o.state / ('r-' + r['review_id'] + '.json')
    original = o.owner._inventory
    count = 0
    def changing(*args, **kwargs):
        nonlocal count
        count += 1
        if count == 2:
            row = json.loads(path.read_text())
            row['revision'] += 1
            path.write_text(json.dumps(row), encoding='utf-8')
        return original(*args, **kwargs)
    monkeypatch.setattr(o.owner, '_inventory', changing)
    result = o.owner.list_reminders(o.root, INIT, state_root=o.state)
    assert result['status'] == 'unavailable' and result['reason'] == 'state_changed'
    assert not result['complete'] and not result['reviews']

def test_bounded_projection_reports_exact_omission_count(owned, monkeypatch):
    o = owned
    open_(o, gate='plan-ok')
    open_(o, gate='requested-review')
    monkeypatch.setattr(o.owner, 'MAX_REMINDERS', 1)
    result = listing(o)
    assert result['complete'] and len(result['reviews']) == 1 and result['reviews_omitted'] == 1

def test_resume_and_session_expose_reminders_without_consuming_or_approving(owned, monkeypatch, capsys):
    o = owned
    r = open_(o)
    before = snapshot(o.root)
    result = o.progress.resume(o.root, initiative='owned')
    assert result['reviews']['reviews'][0]['review_id'] == r['review_id']
    text = o.progress.resume_text(result)
    assert r['review_id'] in text and 'pendiente' in text
    assert 'no acredita aprobación' in text
    monkeypatch.setattr(o.progress, 'marcadores_huerfanos', lambda root: [])
    assert o.progress.cmd_session(SimpleNamespace(root=str(o.root))) == 0
    assert r['review_id'] in capsys.readouterr().out
    assert snapshot(o.root) == before
    assert o.progress.resume(o.root, _history_only=True)['reviews']['status'] == 'unselected'

def test_ambiguous_resume_does_not_pick_any_review(owned):
    o = owned
    open_(o)
    path = o.root / 'docs/roadmap/2026-10-08-other/tasks.md'
    path.parent.mkdir()
    path.write_text('---\nestado: en-progreso\n---\n### T-01 — Other\n- **Estado**: en-progreso\n', encoding='utf-8')
    result = o.progress.resume(o.root)
    assert result['status'] == 'ambiguous' and result['reviews']['status'] == 'unselected'

def test_partial_owner_bundle_degrades_without_private_error(owned, monkeypatch):
    o = owned
    original = o.progress._load_module
    def partial(name, filename):
        if filename == 'plan-review.py':
            raise FileNotFoundError('private-path-secret')
        return original(name, filename)
    monkeypatch.setattr(o.progress, '_load_module', partial)
    result = o.progress.resume(o.root)
    assert result['status'] == 'ok'
    assert result['reviews']['status'] == 'unavailable'
    assert result['reviews']['reason'] == 'helper_unavailable'
    assert 'private-path-secret' not in json.dumps(result)


def test_feedback_counts_are_record_observations_and_superseded_results_do_not_count_twice(owned):
    from test_plan_review_feedback import consumed, result, verify
    o = owned
    o.module = o.owner
    r = consumed(o)
    row = listing(o)['reviews'][0]
    assert row['comments_recorded'] == 1 and row['comments_with_result'] == 0
    assert result(o, r, disposition='needs_clarification')['status'] == 'ok'
    row = listing(o)['reviews'][0]
    assert row['comments_with_result'] == 1 and row['latest_results_needing_clarification'] == 1
    assert row['latest_results_without_verification'] == 1
    assert verify(o, r)['status'] == 'ok'
    row = listing(o)['reviews'][0]
    assert row['latest_results_without_verification'] == 0 and row['approval_granted'] is False
    r = o.owner.get_status(o.root, r['review_id'], state_root=o.state)['review']
    assert result(o, r, result_id='2'*64, supersedes_result_id='1'*64)['status'] == 'ok'
    row = listing(o)['reviews'][0]
    assert row['comments_with_result'] == 1 and row['latest_results_needing_clarification'] == 0
    assert row['latest_results_without_verification'] == 1


def test_current_review_precedes_stale_records_and_session_declares_omissions(owned, monkeypatch, capsys):
    o = owned
    open_(o)
    open_(o, gate='requested-review')
    o.plan.write_text('# Revised\n', encoding='utf-8')
    current = open_(o)
    result = listing(o)
    assert result['reviews'][0]['review_id'] == current['review_id']
    assert result['reviews'][1]['version_status'] == 'version_changed'
    monkeypatch.setattr(o.progress, 'marcadores_huerfanos', lambda root: [])
    o.progress.cmd_session(SimpleNamespace(root=str(o.root)))
    text = capsys.readouterr().out
    assert current['review_id'] in text and 'detalles omitidos' in text
    assert len(text.splitlines()) <= 15


@pytest.mark.parametrize('fault,reason', [('missing_helper', 'helper_unavailable'), ('read_denied', 'invalid_input')])
def test_owner_dependency_or_access_failure_is_visible_without_mutation(owned, monkeypatch, fault, reason):
    o = owned
    open_(o)
    def fail(*args, **kwargs):
        if fault == 'missing_helper':
            raise ImportError('private helper path')
        raise PermissionError('private denied path')
    monkeypatch.setattr(o.owner, '_helper' if fault == 'missing_helper' else '_dirs', fail)
    result = listing(o)
    assert result['status'] == 'unavailable' and result['reason'] == reason
    assert result['complete'] is False and result['approval_granted'] is False
    assert 'private' not in json.dumps(result)


def test_session_partial_reader_reports_limit_and_keeps_progress(owned, monkeypatch, capsys):
    o = owned
    original = o.progress._load_module
    def partial(name, filename):
        if name == 'session_review_reader':
            raise ImportError('private reader')
        return original(name, filename)
    monkeypatch.setattr(o.progress, '_load_module', partial)
    monkeypatch.setattr(o.progress, 'marcadores_huerfanos', lambda root: [])
    before = snapshot(o.root)
    assert o.progress.cmd_session(SimpleNamespace(root=str(o.root))) == 0
    text = capsys.readouterr().out
    assert 'Implementación' in text and 'lector no disponible' in text
    assert snapshot(o.root) == before and 'private reader' not in text


def test_resume_reports_owner_projection_omissions_and_preserves_visible_id(owned, monkeypatch):
    o = owned
    open_(o)
    open_(o, gate='requested-review')
    monkeypatch.setattr(o.owner, 'MAX_REMINDERS', 1)
    original = o.progress._load_module
    monkeypatch.setattr(o.progress, '_load_module', lambda name, filename:
        o.owner if filename == 'plan-review.py' else original(name, filename))
    before = snapshot(o.root)
    result = o.progress.resume(o.root)
    assert result['reviews']['reviews_omitted'] == 1 and result['output_truncated']
    text = o.progress.resume_text(result)
    assert result['reviews']['reviews'][0]['review_id'] in text
    assert '1 referencias omitidas' in text and snapshot(o.root) == before
