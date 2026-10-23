"""Run the documented consume recipes against the real owner on private plans."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
INITIATIVE = 'docs/roadmap/2026-10-12-consume-proof'


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CALLER = load(ROOT / 'tests/test_plan_review_caller.py', 'consume_caller_recipes')


@pytest.mark.parametrize('shell', ['bash', 'powershell'])
@pytest.mark.parametrize('choice', ['approve', 'request_changes', 'waiting', 'stale'])
def test_literal_consume_recipe_preserves_real_decision_and_current_version(tmp_path, shell, choice):
    shell_path = CALLER.executable(shell)
    project = tmp_path / 'project with spaces & literal $(touch sentinel)'
    home = tmp_path / 'private home'
    home.mkdir()
    bundle = project / '.codex/plugins/owned bundle'
    shutil.copytree(ROOT / 'agent-kits/shared', bundle / 'agent-kits/shared')
    builder = bundle / 'skills/plugin-panel/scripts/build_panel.py'
    builder.parent.mkdir(parents=True)
    shutil.copyfile(ROOT / 'skills/plugin-panel/scripts/build_panel.py', builder)
    plan = project / INITIATIVE / 'improvement-plan.md'
    plan.parent.mkdir(parents=True)
    plan.write_bytes(b'# Owned plan\r\n\r\n## Scope\r\nLiteral $(touch sentinel).\r\n')
    tasks = plan.parent / 'tasks.md'
    tasks.write_bytes(b'# Owned ledger\nNo workflow effects authorized.\n')
    state = project / '.claude/plan-review'
    owner = load(bundle / 'agent-kits/shared/plan-review.py', 'consume_recipe_owner')
    opened = owner.open_review(project, INITIATIVE, state_root=state, gate_key='plan-ok')
    assert opened['status'] == 'ok', opened
    review = opened['review']
    if choice != 'waiting':
        comments = [{'comment_id': 'scope-feedback', 'section_id': review['sections'][-1]['section_id'],
                     'text': 'Please revise the scope; $(touch sentinel) is literal data.'}] if choice == 'request_changes' else []
        submitted = owner.submit_decision(project, review['review_id'], review['version'],
            'request_changes' if choice == 'request_changes' else 'approve', comments,
            expected_revision=review['revision'], state_root=state)
        assert submitted['status'] == 'ok', submitted
        review = submitted['review']
    if choice == 'stale':
        plan.write_bytes(plan.read_bytes() + b'New scope requires its own decision.\n')
    plan_bytes, tasks_bytes = plan.read_bytes(), tasks.read_bytes()
    record = state / ('r-' + review['review_id'] + '.json')
    previous_record = record.read_bytes()
    env = {key: value for key, value in os.environ.items()
           if key.upper() in {'SYSTEMROOT', 'WINDIR', 'COMSPEC', 'PATHEXT'}}
    env.update({'HOME': str(home), 'USERPROFILE': str(home), 'APPDATA': str(home / 'appdata'),
        'LOCALAPPDATA': str(home / 'localappdata'), 'TEMP': str(tmp_path), 'TMP': str(tmp_path),
        'PROJECT_ROOT': project.as_posix(), 'REVIEW_INITIATIVE': INITIATIVE, 'REVIEW_RUNTIME': 'codex',
        'REVIEW_PYTHON': sys.executable, 'REVIEW_BUNDLE': bundle.as_posix(),
        'REVIEW_ID': review['review_id'], 'RAW_SHA256': review['version']['raw_sha256'],
        'VIEW_SHA256': review['version']['view_sha256'], 'PYTHONDONTWRITEBYTECODE': '1'})
    if shell == 'bash':
        env['PATH'] = str(Path(shell_path).parent)
        text = CALLER.recipe(shell, 'prepare') + '\n' + CALLER.recipe(shell, 'consume')
        script = tmp_path / 'consume.sh'
        script.write_text(text, encoding='utf-8', newline='\n')
        argv = [shell_path, '--noprofile', '--norc', script.as_posix()]
    else:
        env['PATH'] = ''
        text = '''$ErrorActionPreference='Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
$ProjectRoot=$env:PROJECT_ROOT
$ReviewInitiative=$env:REVIEW_INITIATIVE
$ReviewRuntime=$env:REVIEW_RUNTIME
$ReviewPython=$env:REVIEW_PYTHON
$ReviewHome=$env:USERPROFILE
$ReviewBundle=$env:REVIEW_BUNDLE
$ReviewId=$env:REVIEW_ID
$RawSha256=$env:RAW_SHA256
$ViewSha256=$env:VIEW_SHA256
''' + CALLER.recipe(shell, 'prepare') + '\n' + CALLER.recipe(shell, 'consume') + '\nexit $LASTEXITCODE\n'
        script = tmp_path / 'consume.ps1'
        script.write_bytes(b'\xef\xbb\xbf' + text.encode('utf-8'))
        argv = [shell_path, '-NoLogo', '-NoProfile', '-NonInteractive', '-File', str(script)]

    def run():
        result = subprocess.run(argv, cwd=project, env=env, capture_output=True, timeout=30)
        assert result.stdout, result.stderr.decode('utf-8', errors='replace')
        return result, json.loads(result.stdout.decode('utf-8-sig'))

    result, response = run()
    observed = owner.get_view(project, review['review_id'], state_root=state)['review']
    assert response['schema_version'] == 1
    assert response['review']['review_id'] == review['review_id']
    assert response['review']['initiative'] == INITIATIVE
    assert response['review']['gate_key'] == 'plan-ok'
    assert response['review']['version'] == review['version']
    if choice in {'approve', 'request_changes'}:
        current = response['review']
        assert result.returncode == 0 and response['status'] == 'ok'
        assert current['complete'] is True and current['validity'] == 'current'
        assert current['state'] == 'consumida' and current['current_version'] == review['version']
        assert current['decision'] == review['decision']
        assert current['ack']['decision_id'] == current['decision']['decision_id']
        assert current['ack']['delivery_id'] == current['delivery']['delivery_id']
        assert observed['ack'] == current['ack']
        consumed_bytes = record.read_bytes()
        retry, repeated = run()
        assert retry.returncode == 0 and repeated['status'] == 'ok'
        assert repeated['review']['ack'] == current['ack']
        assert repeated['review']['delivery'] == current['delivery']
        assert record.read_bytes() == consumed_bytes
    else:
        assert response['status'] == ('waiting' if choice == 'waiting' else 'version_changed')
        assert result.returncode == (0 if choice == 'waiting' else 2)
        assert response['review']['ack'] is None and response['review']['delivery'] is None
        assert observed['ack'] is None and record.read_bytes() == previous_record
    assert plan.read_bytes() == plan_bytes and tasks.read_bytes() == tasks_bytes
    assert not (project / 'sentinel').exists() and not (tmp_path / 'sentinel').exists()
