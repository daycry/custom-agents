"""Portable doctor snapshot: privacy, scope, time and bounded structure."""
import copy
import datetime as dt
import importlib.util
import json
from pathlib import Path

import pytest

HERE = Path(__file__).parent
NOW = dt.datetime(2026, 10, 9, 12, tzinfo=dt.timezone.utc)


def module():
    spec = importlib.util.spec_from_file_location('diagnostic_report_test', HERE/'diagnostic-report.py')
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def raw(project):
    return {'proyecto': str(project), 'plugin_root': 'PRIVATE ROOT',
            'bloques': [{'clave': 'plugin', 'titulo': 'PRIVATE TITLE', 'lineas': [
                {'estado': 'error', 'que': 'PRIVATE CHECK', 'detalle': 'SECRET DETAILS', 'arreglo': 'PRIVATE COMMAND'},
                {'estado': 'info', 'que': 'token=Secret1234', 'detalle': 'PRIVATE MEMORY', 'arreglo': ''}]}],
            'resumen': {'ok': 9999}, 'exit': 1,
            'acciones_prioritarias': {'total': 1, 'limite': 3, 'acciones': [
                {'bloque': 'plugin', 'linea': 1, 'estado': 'error', 'que': 'PRIVATE', 'detalle': 'SECRET', 'arreglo': 'RUN COMMAND'}]}}


def make(project):
    return module().project(raw(project), checked_at=NOW)


def test_projection_excludes_private_fields_and_recomputes_summary(tmp_path):
    report = make(tmp_path)
    text = json.dumps(report)
    for hidden in ('PRIVATE', 'SECRET', 'Secret1234', str(tmp_path)):
        assert hidden not in text
    assert report['summary'] == {'ok': 0, 'aviso': 0, 'error': 1, 'info': 1}
    assert report['blocks'][0]['id'] == 'plugin'
    assert report['priorities'] == [{'block': 'plugin', 'row': 1}]
    assert report['checked_at'] == '2026-10-09T12:00:00Z'


def test_consumer_accepts_matching_scope_and_preserves_snapshot(tmp_path):
    report = make(tmp_path)
    out = module().consume(report, project=tmp_path, now=NOW)
    assert out['status'] == 'accepted'
    assert out['age_status'] == 'recent_snapshot'
    assert out['report'] == report


@pytest.mark.parametrize('project,status', [(None, 'scope_unbound'), ('other-project', 'scope_mismatch')])
def test_no_fallback_from_unbound_or_other_scope(tmp_path, project, status):
    out = module().consume(make(tmp_path), project=project, now=NOW)
    assert out['status'] == status and 'report' not in out


def test_old_report_remains_historical(tmp_path):
    out = module().consume(make(tmp_path), project=tmp_path, now=NOW+dt.timedelta(days=2))
    assert out['status'] == 'accepted' and out['age_status'] == 'old_snapshot'


def test_future_report_is_not_treated_as_current(tmp_path):
    assert module().consume(make(tmp_path), project=tmp_path, now=NOW-dt.timedelta(seconds=1))['status'] == 'future_timestamp'


@pytest.mark.parametrize('field,value', [('version', True), ('version', 2), ('producer', 'someone-else'),
                                      ('checked_at', '2026-10-09'), ('checked_at', '2026-99-99T12:00:00Z'),
                                      ('complete', 1), ('scope_key', 'unknown'), ('blocks', 'bad')])
def test_incompatible_top_level_fields(tmp_path, field, value):
    report = make(tmp_path); report[field] = value
    assert module().consume(report, project=tmp_path, now=NOW)['status'] == 'incompatible'


def test_unknown_or_sensitive_keys_are_rejected(tmp_path):
    report = make(tmp_path); report['details'] = 'token=Secret1234'
    assert module().consume(report, project=tmp_path, now=NOW)['status'] == 'incompatible'


@pytest.mark.parametrize('mutation', ['block', 'state', 'summary', 'duplicate', 'priority', 'bool-row', 'extra-row-field'])
def test_inconsistent_nested_data_is_rejected(tmp_path, mutation):
    report = make(tmp_path)
    if mutation == 'block': report['blocks'][0]['id'] = '<script>secret</script>'
    elif mutation == 'state': report['blocks'][0]['rows'][0]['state'] = 'healthy'
    elif mutation == 'summary': report['summary']['error'] = 0
    elif mutation == 'duplicate': report['blocks'].append(copy.deepcopy(report['blocks'][0]))
    elif mutation == 'priority': report['priorities'][0]['row'] = 3
    elif mutation == 'bool-row': report['priorities'][0]['row'] = True
    else: report['blocks'][0]['rows'][0]['arreglo'] = 'RUN THIS'
    assert module().consume(report, project=tmp_path, now=NOW)['status'] == 'incompatible'


def test_projection_budget_is_explicit_and_never_selects_partial_priorities(tmp_path):
    source = raw(tmp_path); source['bloques'][0]['lineas'] *= 300
    report = module().project(source, checked_at=NOW)
    assert report['complete'] is False and sum(len(b['rows']) for b in report['blocks']) == 512
    assert report['priorities'] == [] and len(json.dumps(report).encode()) <= 65536
    assert module().consume(report, project=tmp_path, now=NOW)['status'] == 'incomplete'


def test_consumer_rejects_unbounded_arrays(tmp_path):
    report = make(tmp_path); report['blocks'][0]['rows'] *= 257
    assert module().consume(report, project=tmp_path, now=NOW)['status'] == 'incompatible'


def test_scope_key_normalizes_relative_path_without_exposing_it(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert module().scope_key('.') == module().scope_key(tmp_path)
    assert len(module().scope_key(tmp_path)) == 64


def test_only_exact_public_labels_are_exported(tmp_path):
    source = raw(tmp_path)
    source['bloques'][0]['lineas'][0]['que'] = 'registro en Codex'
    source['bloques'][0]['lineas'][1]['que'] = 'registro en Codex PRIVATE'
    report = module().project(source, checked_at=NOW)
    assert [row['label'] for row in report['blocks'][0]['rows']] == ['registro en Codex', '']


def test_largest_public_label_fits_the_actual_cli_json_format(tmp_path):
    source = raw(tmp_path)
    label = max(module().PUBLIC_CHECK_TITLES, key=lambda value: len(json.dumps(value)))
    source['bloques'][0]['lineas'] = [{'estado': 'error', 'que': label} for _ in range(512)]
    report = module().project(source, checked_at=NOW)
    assert report['complete'] is True
    for escaped in (True, False):
        assert len(json.dumps(report, ensure_ascii=escaped, indent=2).encode('utf8')) <= module().MAX_BYTES
