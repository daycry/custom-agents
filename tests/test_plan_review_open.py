"""Validate caller input without granting approval or writing review state."""
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
CHECK = ROOT / 'agent-kits/shared/plan-review-open.py'
INITIATIVE = 'docs/roadmap/2026-10-10-caller-regression'


def environment(tmp_path):
    env = {key: value for key, value in os.environ.items()
           if key.upper() in {'SYSTEMROOT', 'WINDIR', 'COMSPEC', 'PATHEXT'}}
    home = tmp_path / 'home'
    home.mkdir(exist_ok=True)
    env.update({'HOME': str(home), 'USERPROFILE': str(home), 'APPDATA': str(home / 'appdata'),
                'LOCALAPPDATA': str(home / 'localappdata'), 'TEMP': str(tmp_path), 'TMP': str(tmp_path),
                'PATH': '', 'PYTHONDONTWRITEBYTECODE': '1', 'CUSTOM_AGENTS_IA': '0'})
    return env


def envelope():
    version = {'raw_sha256': 'b' * 64, 'view_sha256': 'c' * 64, 'view_version': 'plan-text-v1'}
    return {'schema_version': 1, 'status': 'ok', 'review': {
        'review_id': 'a' * 64, 'initiative': INITIATIVE, 'artifact': 'improvement-plan.md',
        'gate_key': 'plan-ok', 'complete': True, 'validity': 'current',
        'version': version, 'current_version': copy.deepcopy(version), 'consumer_registration': None}}


def check(tmp_path, value=None, raw=None):
    assert CHECK.is_file(), 'B1 requires executable opening validation'
    if raw is None:
        raw = json.dumps(value, ensure_ascii=False).encode('utf-8')
    return subprocess.run([sys.executable, '-I', '-X', 'utf8', '-B', str(CHECK),
                           '--initiative', INITIATIVE], input=raw, cwd=tmp_path,
                          env=environment(tmp_path), capture_output=True, timeout=15)


@pytest.mark.parametrize('first_runtime', ['codex', None])
def test_B1_resume_validates_real_owner_historical_consumer(tmp_path, first_runtime):
    """Cross-runtime and panel-first openings retain history and pass caller validation."""
    assert CHECK.is_file(), 'B1 requires executable opening validation'
    kit = tmp_path / 'bundle/agent-kits/shared'
    kit.mkdir(parents=True)
    for name in ('plan-review.py', 'local-read.py', 'redact.py'):
        shutil.copyfile(ROOT / 'agent-kits/shared' / name, kit / name)
    project = tmp_path / 'project ü'
    folder = project / INITIATIVE
    folder.mkdir(parents=True)
    (folder / 'improvement-plan.md').write_text('# Plan\n\nAlcance sintético.\n', encoding='utf-8')
    argv = [sys.executable, '-I', '-X', 'utf8', '-B', str(kit / 'plan-review.py'), 'open',
            '--project', str(project), '--state-root', str(project / '.claude/plan-review'),
            '--initiative', INITIATIVE, '--gate-key', 'plan-ok', '--json']
    observed = []
    for args in ([['--caller-id', 'dev-cycle', '--runtime', first_runtime] if first_runtime else [],
                  ['--caller-id', 'dev-cycle', '--runtime', 'claude-code']]):
        run = subprocess.run(argv + args, cwd=project, env=environment(tmp_path),
                             capture_output=True, timeout=15)
        assert run.returncode == 0, run.stderr
        observed.append(json.loads(run.stdout))
    first, resumed = [value['review'] for value in observed]
    assert first['review_id'] == resumed['review_id']
    assert first['version'] == resumed['version']
    assert first['consumer_registration'] == resumed['consumer_registration']
    assert (resumed['consumer_registration']['runtime'] if first_runtime else None) == first_runtime
    before = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
              for path in (project / '.claude/plan-review').iterdir() if path.is_file()}
    validated = check(tmp_path, observed[-1])
    assert validated.returncode == 0, validated.stderr
    result = json.loads(validated.stdout)
    assert result['review_id'] == resumed['review_id'] and result['version'] == resumed['version']
    assert result['approval_granted'] is False
    after = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
             for path in (project / '.claude/plan-review').iterdir() if path.is_file()}
    assert before == after


@pytest.mark.parametrize('change', [
    'schema_bool', 'waiting', 'other_initiative', 'other_artifact', 'other_gate',
    'partial', 'stale', 'missing_review', 'invalid_id', 'invalid_hash',
    'other_view_version', 'different_current_version'])
def test_invalid_open_never_validates(tmp_path, change):
    value = envelope()
    review = value['review']
    if change == 'schema_bool': value['schema_version'] = True
    elif change == 'waiting': value['status'] = 'waiting'
    elif change == 'other_initiative': review['initiative'] += '-other'
    elif change == 'other_artifact': review['artifact'] = 'tasks.md'
    elif change == 'other_gate': review['gate_key'] = 'requested-review'
    elif change == 'partial': review['complete'] = False
    elif change == 'stale': review['validity'] = 'version_changed'
    elif change == 'missing_review': del value['review']
    elif change == 'invalid_id': review['review_id'] = 'a' * 63
    elif change == 'invalid_hash': review['version']['raw_sha256'] = 'z' * 64
    elif change == 'other_view_version': review['version']['view_version'] = 'plan-text-v2'
    elif change == 'different_current_version': review['current_version']['raw_sha256'] = 'd' * 64
    result = check(tmp_path, value)
    assert result.returncode == 2
    assert json.loads(result.stdout)['status'] == 'unavailable'
    assert not (tmp_path / '.claude').exists()


@pytest.mark.parametrize('raw', [b'{}', b'{', b'\xff', b'[]', b'null',
                                b'{"schema_version":1,"schema_version":1}',
                                b'{"status":NaN}', b' ' * (512 * 1024 + 1)],
                         ids=['empty', 'broken', 'encoding', 'array', 'null',
                              'duplicate', 'nonfinite', 'budget'])
def test_invalid_json_and_input_budget_fail_closed(tmp_path, raw):
    result = check(tmp_path, raw=raw)
    assert result.returncode == 2
    assert json.loads(result.stdout)['status'] == 'unavailable'


@pytest.mark.parametrize('boundary', ['overflow_positive', 'overflow_negative', 'depth'])
def test_B3_json_boundaries_fail_closed(tmp_path, boundary):
    if boundary == 'depth':
        raw = b'[' * 12000 + b'0' + b']' * 12000
    else:
        value = envelope()
        value['metadata'] = 'OVERFLOW'
        raw = json.dumps(value).replace('"OVERFLOW"', '-1e999' if boundary.endswith('negative') else '1e999').encode()
    result = check(tmp_path, raw=raw)
    assert result.returncode == 2
    assert json.loads(result.stdout)['status'] == 'unavailable'
    assert not result.stderr


def test_validated_output_contains_only_binding_not_plan_or_history(tmp_path):
    value = envelope()
    value['review']['sections'] = [{'text': 'sensitive plan body'}]
    value['review']['draft_comments'] = [{'text': 'sensitive comment'}]
    result = check(tmp_path, value)
    assert result.returncode == 0
    out = json.loads(result.stdout)
    assert set(out) == {'schema_version', 'status', 'review_id', 'version', 'approval_granted'}
    assert out['approval_granted'] is False
    assert b'sensitive' not in result.stdout
