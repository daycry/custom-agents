"""Executable arithmetic and drift checks for the documented PM estimate."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
FOLDER = Path('docs/roadmap/2026-11-04-token-efficiency/testing')
SCRIPT = ROOT / FOLDER / 'audit-token-estimates.py'
ROLES = ['analyst', 'evaluator', 'architect', 'planner']
READ = 'agent-kits/shared/read-discipline.md'
OUTPUT = 'agent-kits/shared/output-discipline.md'
REFS = ['agent-kits/planner/references/task-types.md',
        'agent-kits/planner/references/plan-maintenance.md',
        'agent-kits/evaluator/references/code-health.md',
        'agent-kits/shared/references/source-reuse.md']


@pytest.fixture
def audit():
    spec = importlib.util.spec_from_file_location('test_token_audit', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def project(tmp_path):
    before = []
    for role in ROLES:
        path = 'agents/' + role + '.md'
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes('read-discipline.md output-discipline.md'.ljust(60, 'x').encode())
        before.append({'path': path, 'characters': 100})
    for path, now, old in [(READ, 8, 20), (OUTPUT, 12, 40)]:
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b'x' * now)
        before.append({'path': path, 'characters': old})
    for path in REFS:
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b'r' * 16)
    data = {'source_revision': '9c109c592e5a152a7ad311ad6c13080764fd00f1',
        'footprint': {'schema_version': 1, 'kind': 'source_footprint',
            'method': 'characters/4', 'normalization': 'utf8-lf', 'complete': True, 'files': before},
        'role_policy_paths': {'analyst': [], 'evaluator': [READ, OUTPUT],
                              'architect': [READ, OUTPUT], 'planner': [OUTPUT]}}
    folder = tmp_path / FOLDER
    folder.mkdir(parents=True)
    (folder / 'scenario-before.json').write_text(json.dumps(data), encoding='utf-8')
    after = {'footprint': {'schema_version': 1, 'kind': 'source_footprint',
        'method': 'characters/4', 'normalization': 'utf8-lf', 'complete': True,
        'files': [{'path': 'agents/' + r + '.md', 'characters': 60} for r in ROLES]
            + [{'path': READ, 'characters': 8}, {'path': OUTPUT, 'characters': 12}]
            + [{'path': p, 'characters': 16} for p in REFS]},
        'role_policy_paths': {r: [READ, OUTPUT] for r in ROLES}}
    (folder / 'scenario-after.json').write_text(json.dumps(after), encoding='utf-8')
    return tmp_path


def test_scenario_counts_repeated_policies_and_keeps_conditional_cost_separate(audit, project):
    report = audit.calculate(project)
    assert [r['estimated_input_tokens_saved'] for r in report['roles']] == [5, 20, 20, 15]
    assert report['estimated_input_tokens_saved_total'] == 60
    assert sum(report['conditional_reference_estimated_tokens'].values()) == 16
    assert report['native_usage'] is None and report['output_token_savings'] is None
    assert report['quality_or_billing_guarantee'] is False


def test_current_report_is_reproducible(audit):
    assert audit.calculate(ROOT) == json.loads((ROOT / FOLDER / 'token-estimates.json').read_text(encoding='utf-8'))


def test_recorded_inventory_and_table_are_calculated(audit, project):
    folder = project / FOLDER
    before = json.loads((folder / 'scenario-before.json').read_text())['footprint']
    after = json.loads((folder / 'scenario-after.json').read_text())['footprint']
    for name, source in [('context-before.json', before), ('context-after.json', after)]:
        source['files'] = [r for r in source['files'] if r['path'].startswith('agents/')]
        (folder / name).write_text(json.dumps(source), encoding='utf-8')
    summary = audit.inventory(project)
    assert summary['all_references_and_shared_loaded_delta'] == -136
    assert summary['pm_four_roles'] == {'before': 400, 'after': 240}
    (folder / 'measurement-summary.json').write_text(json.dumps(summary), encoding='utf-8')
    (folder / 'measurements.md').write_text(audit.inventory_table(summary), encoding='utf-8')
    assert audit.main(['--root', str(project), '--inventory']) == 0
    assert audit.main(['--root', str(project), '--inventory', '--generate']) == 0
    assert audit.main(['--root', str(project), '--inventory', '--generate', '--markdown']) == 0
    (folder / 'measurements.md').write_text('stale table', encoding='utf-8')
    assert audit.main(['--root', str(project), '--inventory']) == 1


def test_capture_is_explicit_and_current_sources_must_be_complete(project):
    command = [sys.executable, str(SCRIPT), '--root', str(project), '--capture-current']
    result = subprocess.run(command, capture_output=True, encoding='utf-8')
    assert result.returncode == 0
    snapshot = json.loads(result.stdout)
    assert snapshot['footprint']['complete']
    assert snapshot['role_policy_paths']['analyst'] == [READ, OUTPUT]
    (project / 'agents/analyst.md').unlink()
    result = subprocess.run(command, capture_output=True, encoding='utf-8')
    assert result.returncode == 2 and json.loads(result.stdout)['status'] == 'unavailable'


def test_cli_generate_check_and_changed_source(project):
    command = [sys.executable, str(SCRIPT), '--root', str(project)]
    made = subprocess.run(command + ['--generate'], capture_output=True, encoding='utf-8')
    assert made.returncode == 0, made.stdout + made.stderr
    report = json.loads(made.stdout)
    assert report['estimated_input_tokens_saved_total'] == 60
    (project / FOLDER / 'token-estimates.json').write_text(made.stdout, encoding='utf-8')
    markdown = subprocess.run(command + ['--generate', '--markdown'], capture_output=True, encoding='utf-8')
    assert markdown.returncode == 0
    (project / FOLDER / 'token-estimates.md').write_text(markdown.stdout, encoding='utf-8')
    assert subprocess.run(command, capture_output=True).returncode == 0
    (project / READ).write_bytes(b'x' * 12)
    stale = subprocess.run(command + ['--current'], capture_output=True, encoding='utf-8')
    assert stale.returncode == 1 and json.loads(stale.stdout)['status'] == 'stale'
    assert subprocess.run(command, capture_output=True).returncode == 0  # Historical evidence stays reproducible.
    (project / FOLDER / 'token-estimates.md').write_text('stale numbers', encoding='utf-8')
    assert subprocess.run(command, capture_output=True).returncode == 1


@pytest.mark.parametrize('mutation', ['missing_source', 'bad_size', 'duplicate_policy', 'missing_role'])
def test_incomplete_baselines_or_sources_cannot_be_reported_as_savings(audit, project, mutation):
    source = project / FOLDER / 'scenario-before.json'
    data = json.loads(source.read_text())
    if mutation == 'missing_source': (project / REFS[0]).unlink()
    if mutation == 'bad_size': data['footprint']['files'][0]['characters'] = True
    if mutation == 'duplicate_policy': data['role_policy_paths']['analyst'] = [READ, READ]
    if mutation == 'missing_role': data['role_policy_paths'].pop('planner')
    source.write_text(json.dumps(data), encoding='utf-8')
    with pytest.raises(ValueError):
        audit.calculate(project, current=mutation == 'missing_source')


@pytest.mark.parametrize('data', ['{', '[]', '[' * 5000 + '0' + ']' * 5000,
                                'x' * (1024 * 1024 + 1)],
                         ids=['malformed', 'array', 'deep', 'oversized'])
def test_invalid_input_has_explicit_cli_failure(project, data):
    (project / FOLDER / 'scenario-before.json').write_text(data, encoding='utf-8')
    process = subprocess.run([sys.executable, str(SCRIPT), '--root', str(project), '--generate'],
        capture_output=True, encoding='utf-8')
    assert process.returncode == 2
    assert json.loads(process.stdout)['status'] == 'unavailable'
