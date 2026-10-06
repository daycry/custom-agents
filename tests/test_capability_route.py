"""Contract tests for bounded, local selection of bundled capabilities."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'agent-kits/shared/capability-route.py'
spec = importlib.util.spec_from_file_location('capability_route', SCRIPT)
route = importlib.util.module_from_spec(spec)
spec.loader.exec_module(route)


def write_json(root, name, value):
    (root / name).write_text(json.dumps(value), encoding='utf-8')


def test_detects_three_stacks_from_manifests_without_executing_code(tmp_path):
    write_json(tmp_path, 'composer.json', {'require': {'php': '^8.2', 'codeigniter4/framework': '^4.6'}})
    write_json(tmp_path, 'package.json', {'dependencies': {'react': '^19.0'}, 'scripts': {'prepare': 'raise alarm'}})
    (tmp_path / 'pyproject.toml').write_text('[project]\nname="demo"\n', encoding='utf-8')
    result = route.detect(tmp_path)
    assert result['stacks'] == ['codeigniter4', 'php', 'python', 'react']
    assert result['sources'] == ['composer.json', 'package.json', 'pyproject.toml']


def test_node_and_typescript_do_not_imply_react(tmp_path):
    write_json(tmp_path, 'package.json', {'devDependencies': {'typescript': '*'}})
    assert route.detect(tmp_path)['stacks'] == []


@pytest.mark.parametrize('name,body', [('composer.json', '{bad'), ('package.json', '[]'), ('pyproject.toml', '=bad')])
def test_corrupt_manifests_are_visible_without_raw_contents(tmp_path, name, body):
    (tmp_path / name).write_text(body + ' private-data', encoding='utf-8')
    result = route.detect(tmp_path)
    assert result['stacks'] == []
    assert len(result['warnings']) == 1
    assert 'private-data' not in json.dumps(result)


def test_oversized_manifest_is_not_read_as_context(tmp_path):
    (tmp_path / 'composer.json').write_bytes(b' ' * (route.MAX_BYTES + 1))
    assert route.detect(tmp_path)['warnings']


def test_partial_project_has_no_invented_stack(tmp_path):
    assert route.detect(tmp_path) == {'stacks': [], 'sources': [], 'warnings': []}


def test_registry_references_real_bundled_skills():
    registry = route.load_catalog()
    assert registry['version'] == 1
    assert route.validate_catalog(registry) == []


def test_role_and_stack_selection_excludes_irrelevant_context():
    result = route.select(route.load_catalog(), 'implementer', ['python'], [])
    assert any(entry['id'] == 'stack-practices' for entry in result)
    assert not any(entry['id'] == 'frontend-quality' for entry in result)
    assert not any(entry['id'] == 'research-first' for entry in result)


def test_area_explicitly_enables_backend_criteria():
    result = route.select(route.load_catalog(), 'architect', [], ['api'])
    assert any(entry['id'] == 'backend-practices' for entry in result)


@pytest.mark.parametrize('mutation', ['duplicate', 'traversal', 'missing', 'role', 'stack', 'area', 'unknown', 'badtype'])
def test_bad_catalog_is_rejected(mutation):
    data = {'version': 1, 'capabilities': [{'id': 'research-first', 'roles': ['analyst'], 'stacks': [], 'areas': ['research']}]}
    entry = data['capabilities'][0]
    if mutation == 'duplicate':
        data['capabilities'].append(dict(entry))
    elif mutation == 'traversal':
        entry['id'] = '../outside'
    elif mutation == 'missing':
        entry['id'] = 'missing-piece'
    elif mutation == 'role':
        entry['roles'] = ['foreign-agent']
    elif mutation == 'stack':
        entry['stacks'] = ['foreign-stack']
    elif mutation == 'area':
        entry['areas'] = ['foreign-area']
    elif mutation == 'unknown':
        entry['exec'] = 'malicious-script'
    else:
        data['capabilities'] = 'bad'
    assert route.validate_catalog(data)


def test_cli_keeps_foreign_code_and_secrets_out_of_output(tmp_path):
    write_json(tmp_path, 'package.json', {'dependencies': {'react': '*'}, 'password': 'dont-export-me'})
    (tmp_path / 'capability-route.py').write_text('raise RuntimeError("EXECUTED")', encoding='utf-8')
    result = subprocess.run([sys.executable, str(SCRIPT), '--project', str(tmp_path), '--role', 'qa', '--json'], capture_output=True, text=True, encoding='utf-8')
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data['stacks'] == ['react']
    assert data['selection_only'] is True
    assert 'dont-export-me' not in result.stdout and 'EXECUTED' not in result.stdout


def test_linked_manifest_is_rejected(tmp_path):
    outside = tmp_path / 'outside.json'
    write_json(tmp_path, 'outside.json', {'dependencies': {'react': '*'}})
    try:
        (tmp_path / 'package.json').symlink_to(outside)
    except OSError:
        pytest.skip('symlink creation is unavailable')
    assert route.detect(tmp_path)['stacks'] == []
    assert route.detect(tmp_path)['warnings']


def test_cli_check_and_invalid_project(tmp_path):
    check = subprocess.run([sys.executable, str(SCRIPT), '--check'], capture_output=True)
    assert check.returncode == 0
    missing = subprocess.run([sys.executable, str(SCRIPT), '--project', str(tmp_path / 'missing')], capture_output=True)
    assert missing.returncode == 2


def test_deeply_nested_manifest_degrades_to_warning(tmp_path):
    (tmp_path / 'package.json').write_text('{"nested":' * 2000 + '0' + '}' * 2000, encoding='utf-8')
    assert route.detect(tmp_path)['warnings']


@pytest.mark.parametrize('data', [None, {}, {'version': True, 'capabilities': []}, {'version': 2, 'capabilities': []}, {'version': 1, 'capabilities': [None]}, {'version': 1, 'capabilities': [{}] * 101}])
def test_catalog_envelope_and_limit(data):
    assert route.validate_catalog(data)


@pytest.mark.parametrize('field,value', [('id', []), ('roles', []), ('roles', ['analyst', 'analyst']), ('stacks', [None]), ('areas', {})])
def test_catalog_field_types(field, value):
    entry = {'id': 'research-first', 'roles': ['analyst'], 'stacks': [], 'areas': ['research']}
    entry[field] = value
    assert route.validate_catalog({'version': 1, 'capabilities': [entry]})


@pytest.mark.parametrize('role,stacks,areas', [('foreign', [], []), ('qa', ['foreign'], []), ('qa', [], ['foreign'])])
def test_bad_selection_filters_raise(role, stacks, areas):
    with pytest.raises(ValueError):
        route.select(route.load_catalog(), role, stacks, areas)


def test_phase_and_explicit_stack_provenance(tmp_path, capsys):
    assert route.main(['--project', str(tmp_path), '--phase', 'design', '--stack', 'python', '--area', 'api', '--json']) == 0
    data = json.loads(capsys.readouterr().out)
    assert data['role'] == 'architect'
    assert data['explicit_stacks'] == ['python'] and data['sources'] == []
    assert data['selection_only'] is True


def test_disagreeing_phase_and_role_are_rejected(tmp_path, capsys):
    assert route.main(['--project', str(tmp_path), '--role', 'qa', '--phase', 'design']) == 2
    assert 'unavailable' in capsys.readouterr().err


def test_cli_text_lists_sources_and_warnings(tmp_path, capsys):
    (tmp_path / 'composer.json').write_text('{', encoding='utf-8')
    assert route.main(['--project', str(tmp_path), '--stack', 'react']) == 0
    output = capsys.readouterr().out
    assert 'stack-practices' in output and 'warning:' in output


def test_missing_redactor_does_not_export_metadata(tmp_path, monkeypatch, capsys):
    (tmp_path / 'capability-route.py').write_text('', encoding='utf-8')
    monkeypatch.setattr(route, '__file__', str(tmp_path / 'capability-route.py'))
    assert route.main(['--check', '--json']) == 2
    output = capsys.readouterr()
    assert output.out == '' and 'unavailable' in output.err


def test_invalid_catalog_diagnostics_never_echo_raw_data(monkeypatch, capsys):
    monkeypatch.setattr(route, 'load_catalog', lambda: {'secret': 'private-data'})
    assert route.main(['--check']) == 2
    assert 'private-data' not in str(capsys.readouterr())


def test_check_json_has_counts(capsys):
    assert route.main(['--check', '--json']) == 0
    assert json.loads(capsys.readouterr().out)['capabilities'] > 0


def test_manifest_dependency_sections_must_be_objects(tmp_path):
    write_json(tmp_path, 'package.json', {'dependencies': []})
    assert route.detect(tmp_path)['warnings']


def test_python_performance_does_not_select_frontend_guidance():
    result = route.select(route.load_catalog(), 'reviewer', ['python'], ['performance'])
    assert 'code-health' in [entry['id'] for entry in result]
    assert 'frontend-quality' not in [entry['id'] for entry in result]
