"""Opt-in doctor snapshots never become live hook execution evidence."""
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path
import re

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_plugin_catalog_index_retains_optional_diagnostic_flag():
    index = load('diagnostic_hint_index', 'agent-kits/shared/skill-index.py')
    command = (ROOT/'commands/plugin-catalog.md').read_text(encoding='utf8')
    hint = re.search(r'^argument-hint: (.*)$', command, re.M).group(1)
    assert index.hint_corto(hint) == '[ruta de salida HTML] [--diagnostics-report informe.json] [--serve] [--port PUERTO]'


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT/relative)
    result = importlib.util.module_from_spec(spec); spec.loader.exec_module(result)
    return result


@pytest.fixture
def panel():
    return load('panel_diagnostics', 'skills/plugin-panel/scripts/build_panel.py')


@pytest.fixture
def report(tmp_path):
    project = tmp_path/'project'; project.mkdir()
    helper = load('panel_report_fixture', 'agent-kits/shared/diagnostic-report.py')
    source = {'proyecto': str(project), 'bloques': [{'clave': 'plugin', 'titulo': 'PRIVATE', 'lineas': [
        {'estado': 'error', 'que': 'registro en Codex', 'detalle': 'SECRET', 'arreglo': 'PRIVATE COMMAND'},
        {'estado': 'info', 'que': 'PRIVATE', 'detalle': 'SECRET', 'arreglo': ''}]}],
        'acciones_prioritarias': {'acciones': [{'bloque': 'plugin', 'linea': 1}]}}
    value = helper.project(source, checked_at=dt.datetime.now(dt.timezone.utc)-dt.timedelta(seconds=2))
    path = tmp_path/'report.json'; path.write_text(json.dumps(value), encoding='utf8')
    return project, path, value


def inventory(panel, root, project=None, path=None):
    root.mkdir(parents=True, exist_ok=True)
    return panel.build_inventory(root, project=project, include_user=False, diagnostics_report=path)


def test_no_report_means_unknown_without_importing_checker(panel, tmp_path, monkeypatch):
    monkeypatch.setattr(panel, '_load_shared', lambda name: pytest.fail('Implicit diagnostics import'))
    data = inventory(panel, tmp_path)
    assert data['diagnostics'] == {'status': 'not_provided'}
    assert 'Sin diagnóstico importado' in panel.render_html(data)


def test_explicit_file_is_bound_hashed_and_never_runs_doctor(panel, tmp_path, report, monkeypatch):
    project, path, value = report
    import subprocess
    monkeypatch.setattr(subprocess, 'run', lambda *a, **k: pytest.fail('Diagnostics executed a subprocess'))
    before = {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}
    data = inventory(panel, tmp_path/'empty-bundle', project, path)
    assert data['diagnostics']['status'] == 'accepted'
    assert data['diagnostics']['report'] == value
    assert data['diagnostics']['source_sha256'] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()} == before


@pytest.mark.parametrize('project,status', [(None, 'scope_unbound'), ('another-project', 'scope_mismatch')])
def test_scope_failure_does_not_adopt_report(panel, tmp_path, report, project, status):
    _, path, _ = report
    if project is not None:
        project = tmp_path/project
    result = inventory(panel, tmp_path, project, path)['diagnostics']
    assert result['status'] == status and 'report' not in result


@pytest.mark.parametrize('text,status', [('not-json', 'incompatible'), ('{}', 'incompatible'),
                                      ('{"version":1,"version":1}', 'incompatible'),
                                      ('[NaN]', 'incompatible'), ('x'*65537, 'too_large')],
                         ids=['not-json', 'empty', 'duplicate-key', 'nan', 'oversized'])
def test_rejected_input_retains_catalog_without_echoing_payload(panel, tmp_path, text, status):
    path = tmp_path/'report.json'; path.write_text(text, encoding='utf8')
    result = inventory(panel, tmp_path, path=path)
    assert result['diagnostics']['status'] == status
    assert 'report' not in result['diagnostics'] and text not in result['warnings']


def test_absent_file_is_distinct(panel, tmp_path):
    assert inventory(panel, tmp_path, path=tmp_path/'absent.json')['diagnostics']['status'] == 'not_found'


def test_unknown_reader_is_explicit(panel, tmp_path, monkeypatch):
    monkeypatch.setattr(panel, '_load_shared', lambda name: (_ for _ in ()).throw(FileNotFoundError('PRIVATE')))
    result = inventory(panel, tmp_path, path=tmp_path/'report.json')
    assert result['diagnostics']['status'] == 'reader_unavailable'
    assert 'PRIVATE' not in json.dumps(result)


def test_invalid_encoding_is_not_absence(panel, tmp_path):
    path = tmp_path/'report.json'; path.write_bytes(b'\xff')
    assert inventory(panel, tmp_path, path=path)['diagnostics']['status'] == 'invalid_encoding'


def test_bom_digest_identifies_decoded_text(panel, tmp_path, report):
    project, path, value = report
    text = json.dumps(value, ensure_ascii=False)
    path.write_bytes(b'\xef\xbb\xbf' + text.encode('utf8'))
    result = inventory(panel, tmp_path/'bundle', project, path)['diagnostics']
    assert result['status'] == 'accepted'
    assert result['digest_method'] == 'decoded-utf8-text'
    assert result['source_sha256'] == hashlib.sha256(text.encode('utf8')).hexdigest()
    assert result['source_sha256'] != hashlib.sha256(path.read_bytes()).hexdigest()


def test_deep_json_is_rejected_without_recursion_error(panel, tmp_path):
    path = tmp_path/'report.json'
    path.write_text('[' * 2000 + '0' + ']' * 2000, encoding='utf8')
    result = inventory(panel, tmp_path/'bundle', path=path)
    assert result['diagnostics']['status'] == 'incompatible'
    assert 'report' not in result['diagnostics']


def test_report_directory_is_not_read_as_data(panel, tmp_path):
    path = tmp_path/'report.json'; path.mkdir()
    result = inventory(panel, tmp_path/'bundle', path=path)['diagnostics']
    assert result['status'] == 'not_regular' and 'report' not in result


def test_future_report_has_no_results_or_recommendations(panel, tmp_path, report):
    project, path, value = report
    value['checked_at'] = '9999-01-01T00:00:00Z'
    path.write_text(json.dumps(value), encoding='utf8')
    data = inventory(panel, tmp_path/'bundle', project, path)
    assert data['diagnostics']['status'] == 'future_timestamp'
    page = panel.render_html(data)
    assert 'id="diagnostic-plugin-1"' not in page
    assert 'id="diagnostic-state"' not in page


def test_partial_report_keeps_prefix_counts_without_priorities(panel, tmp_path, report):
    project, path, value = report
    value['complete'] = False; value['priorities'] = []
    path.write_text(json.dumps(value), encoding='utf8')
    data = inventory(panel, tmp_path/'bundle', project, path)
    assert data['diagnostics']['status'] == 'incomplete'
    assert data['diagnostics']['report']['summary'] == {'ok': 0, 'aviso': 0, 'error': 1, 'info': 1}
    page = panel.render_html(data)
    assert 'id="diagnostic-plugin-1"' in page
    assert 'href="#diagnostic-plugin-1"' not in page


def test_old_snapshot_and_current_hook_unknown_states_remain_separate(panel, tmp_path, report):
    project, path, value = report
    value['checked_at'] = '2026-01-01T00:00:00Z'; path.write_text(json.dumps(value), encoding='utf8')
    hooks = tmp_path/'bundle/hooks'; hooks.mkdir(parents=True)
    (hooks/'hooks.json').write_text(json.dumps({'hooks': {'SessionEnd': [{'hooks': [
        {'type': 'command', 'command': 'unrecognized', 'timeout': 3}]}]}}), encoding='utf8')
    data = inventory(panel, tmp_path/'bundle', project, path)
    assert data['diagnostics']['age_status'] == 'old_snapshot'
    assert data['hooks'][0]['load_status'] == data['hooks'][0]['execution_status'] == 'unknown'


def test_render_shows_source_scope_and_safe_recommendation(panel, tmp_path, report):
    project, path, _ = report
    data = inventory(panel, tmp_path, project, path)
    page = panel.render_html(data)
    for expected in ('id="diagnostics"', 'href="#diagnostics"', 'id="diagnostic-state"',
                     'id="diagnostic-plugin-1"', 'registro en Codex', '/doctor',
                     'no acredita carga ni ejecución', data['diagnostics']['source_sha256']):
        assert expected in page
    assert 'PRIVATE' not in page and 'SECRET' not in page and str(project) not in page
