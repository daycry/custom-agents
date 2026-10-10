"""Execute the command's shell recipes on synthetic bundles; no native host or UI claim."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
COMMAND = ROOT / 'commands/dev-cycle.md'
INITIATIVE = 'docs/roadmap/2026-10-10-shell-proof'


def recipe(shell, step):
    text = COMMAND.read_text(encoding='utf-8')
    pattern = r'<!-- plan-review:' + step + ':' + shell + r' -->\s*```' + shell + r'\n(.*?)\n```'
    matches = re.findall(pattern, text, re.S)
    assert len(matches) == 1, f'missing unique {shell}/{step} executable recipe'
    return matches[0]


def executable(shell):
    if shell == 'bash':
        path = os.environ.get('TEST_PLAN_REVIEW_BASH') or (shutil.which('bash') if os.name != 'nt' else None)
    else:
        path = os.environ.get('TEST_PLAN_REVIEW_POWERSHELL') or shutil.which('pwsh') or shutil.which('powershell')
    if not path:
        pytest.skip(f'{shell} executable unavailable; no shell acceptance')
    return path


def bundle(path, *, complete=True):
    owner = path / 'agent-kits/shared/plan-review.py'
    owner.parent.mkdir(parents=True)
    owner.write_text('''import json, os, sys
from pathlib import Path
with Path(os.environ['CALLER_CAPTURE']).open('a', encoding='utf-8') as out:
    out.write(json.dumps({'script': __file__, 'argv': sys.argv[1:]}, ensure_ascii=False) + '\\n')
if os.environ.get('CALLER_FAIL_OPEN') == '1' and sys.argv[1] == 'open':
    sys.exit(3)
version = {'raw_sha256': 'b'*64, 'view_sha256': 'c'*64, 'view_version': 'plan-text-v1'}
review = {'review_id': 'a'*64, 'initiative': sys.argv[sys.argv.index('--initiative')+1] if '--initiative' in sys.argv else '', 'artifact': 'improvement-plan.md', 'gate_key': 'plan-ok', 'complete': True, 'validity': 'current', 'version': version, 'current_version': version, 'consumer_registration': None, 'sections': [{'text': 'Plan ü'}]}
if os.environ.get('CALLER_INVALID_OPEN') == '1': review['gate_key'] = 'requested-review'
print(json.dumps({'schema_version': 1, 'status': 'ok', 'review': review}, ensure_ascii=False))
''', encoding='utf-8')
    if complete:
        shutil.copyfile(ROOT / 'agent-kits/shared/plan-review-open.py',
                        owner.parent / 'plan-review-open.py')
        builder = path / 'skills/plugin-panel/scripts/build_panel.py'
        builder.parent.mkdir(parents=True)
        shutil.copyfile(owner, builder)
    return path


def run_recipe(tmp_path, shell, steps, *, layout='project', runtime='codex', root_index=None, fail_open=False, invalid_open=False):
    shell_path = executable(shell)
    project = tmp_path / 'project ü & literal $(touch sentinel)'
    home = tmp_path / 'home personal'
    project.mkdir(); home.mkdir()
    if root_index is not None:
        roots = [project / '.claude', project / '.codex', project / '.opencode',
                 home / '.claude', home / '.codex', home / '.config/opencode']
        expected = bundle(roots[root_index] / 'chosen bundle')
    elif layout == 'global':
        bundle(project / '.claude/partial bundle', complete=False)
        expected = bundle(home / '.config/opencode/chosen bundle')
    else:
        expected = bundle(project / '.codex/plugins/chosen bundle')
        if layout == 'ambiguous':
            bundle(project / '.codex/plugins/other bundle')
        elif layout == 'precedence':
            bundle(home / '.claude/global bundle')
    capture = tmp_path / 'argv.jsonl'
    env = {key: value for key, value in os.environ.items()
           if key.upper() in {'SYSTEMROOT', 'WINDIR', 'COMSPEC', 'PATHEXT'}}
    env.update({'HOME': str(home), 'USERPROFILE': str(home), 'APPDATA': str(home / 'appdata'),
                'LOCALAPPDATA': str(home / 'localappdata'), 'TEMP': str(tmp_path), 'TMP': str(tmp_path),
                'PROJECT_ROOT': project.as_posix(), 'REVIEW_INITIATIVE': INITIATIVE,
                'REVIEW_RUNTIME': runtime, 'REVIEW_PYTHON': sys.executable,
                'CALLER_CAPTURE': str(capture), 'PYTHONDONTWRITEBYTECODE': '1'})
    if fail_open:
        env['CALLER_FAIL_OPEN'] = '1'
    if invalid_open:
        env['CALLER_INVALID_OPEN'] = '1'
    if shell == 'bash':
        env['PATH'] = str(Path(shell_path).parent)
        script = '\n'.join(recipe(shell, step) for step in steps)
        argv = [shell_path, '--noprofile', '--norc', '-c', script]
    else:
        env['PATH'] = ''
        script = '''$ErrorActionPreference='Stop'
$ProjectRoot=$env:PROJECT_ROOT
$ReviewInitiative=$env:REVIEW_INITIATIVE
$ReviewRuntime=$env:REVIEW_RUNTIME
$ReviewPython=$env:REVIEW_PYTHON
$ReviewHome=$env:USERPROFILE
''' + '\n'.join(recipe(shell, step) for step in steps)
        script_file = tmp_path / 'recipe.ps1'
        script_file.write_bytes(b'\xef\xbb\xbf' + script.encode('utf-8'))
        argv = [shell_path, '-NoLogo', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', str(script_file)]
    process = subprocess.run(argv, cwd=project, env=env, capture_output=True, timeout=30)
    records = [json.loads(line) for line in capture.read_text(encoding='utf-8').splitlines()] if capture.exists() else []
    return process, records, expected, project, tmp_path


@pytest.mark.parametrize('shell', ['bash', 'powershell'])
@pytest.mark.parametrize('layout', ['project', 'global', 'precedence'])
def test_open_and_serve_use_same_complete_bundle_with_literal_arguments(tmp_path, shell, layout):
    result, records, expected, project, owned = run_recipe(tmp_path, shell, ['prepare', 'open', 'serve'], layout=layout)
    assert result.returncode == 0, result.stderr.decode('utf-8', errors='replace')
    assert len(records) == 2
    assert Path(records[0]['script']).resolve() == expected / 'agent-kits/shared/plan-review.py'
    assert Path(records[1]['script']).resolve() == expected / 'skills/plugin-panel/scripts/build_panel.py'
    assert records[0]['argv'] == ['open', '--project', str(project).replace('\\', '/'),
        '--state-root', project.as_posix() + '/.claude/plan-review', '--initiative', INITIATIVE,
        '--gate-key', 'plan-ok', '--caller-id', 'dev-cycle', '--runtime', 'codex', '--json']
    assert records[1]['argv'] == ['--serve', '--project', project.as_posix(), '--review-initiative', INITIATIVE,
        '--review-state-root', project.as_posix() + '/.claude/plan-review', '--review-gate-key', 'plan-ok']
    assert not (owned / 'sentinel').exists() and not (project / 'sentinel').exists()


@pytest.mark.parametrize('shell', ['bash', 'powershell'])
def test_ambiguous_bundle_does_not_open_or_serve(tmp_path, shell):
    result, records, *_ = run_recipe(tmp_path, shell, ['prepare', 'open', 'serve'], layout='ambiguous')
    assert result.returncode != 0 and records == []


@pytest.mark.parametrize('shell', ['bash', 'powershell'])
def test_invalid_runtime_does_not_open_or_serve(tmp_path, shell):
    result, records, *_ = run_recipe(tmp_path, shell, ['prepare', 'open', 'serve'], runtime='foreign')
    assert result.returncode != 0 and records == []


@pytest.mark.parametrize('shell', ['bash', 'powershell'])
@pytest.mark.parametrize('root_index', range(6))
def test_all_six_roots_are_supported_without_mixing_bundles(tmp_path, shell, root_index):
    result, records, expected, *_ = run_recipe(tmp_path, shell, ['prepare', 'open', 'serve'], root_index=root_index)
    assert result.returncode == 0, result.stderr.decode('utf-8', errors='replace')
    assert len(records) == 2
    assert Path(records[0]['script']).resolve() == expected / 'agent-kits/shared/plan-review.py'
    assert Path(records[1]['script']).resolve() == expected / 'skills/plugin-panel/scripts/build_panel.py'


@pytest.mark.parametrize('shell', ['bash', 'powershell'])
def test_open_failure_never_starts_server(tmp_path, shell):
    result, records, *_ = run_recipe(tmp_path, shell, ['prepare', 'open', 'serve'], fail_open=True)
    assert result.returncode != 0
    assert len(records) == 1 and records[0]['argv'][0] == 'open'


@pytest.mark.parametrize('shell', ['bash', 'powershell'])
def test_B1_invalid_open_exit_zero_never_starts_server(tmp_path, shell):
    result, records, *_ = run_recipe(tmp_path, shell, ['prepare', 'open', 'serve'], invalid_open=True)
    assert result.returncode != 0
    assert len(records) == 1 and records[0]['argv'][0] == 'open'
