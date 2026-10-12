"""Native Python CLI queries must not create bytecode in a project-local kit."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

HERE = Path(__file__).parent

def snapshot(root):
    return {p.relative_to(root).as_posix(): (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mode)
            for p in root.rglob('*') if p.is_file()}

@pytest.mark.parametrize('query', ['resume', 'review-status'])
def test_project_local_query_preserves_files_without_requiring_python_B(tmp_path, query):
    root = tmp_path / 'project'
    kit = root / '.claude/agent-kits/shared'
    kit.mkdir(parents=True)
    for source in HERE.glob('*.py'):
        if not source.name.startswith('test_'):
            (kit / source.name).write_bytes(source.read_bytes())
    tasks = root / 'docs/roadmap/2026-10-11-owned/tasks.md'
    tasks.parent.mkdir(parents=True)
    tasks.write_text('---\nestado: en-progreso\n---\n### T-01 — Owned\n- **Estado**: en-progreso\n', encoding='utf-8')
    before = snapshot(root)
    dirs_before = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_dir()}
    if query == 'resume':
        args = [str(kit / 'progress-report.py'), 'resume', '--root', str(root), '--json']
        expected_code, expected_status = 0, 'ok'
    else:
        args = [str(kit / 'plan-review.py'), 'status', '--project', str(root),
            '--state-root', str(root / '.claude/plan-review'), '--review-id', '0'*64, '--json']
        expected_code, expected_status = 3, 'unavailable'
    environment = dict(os.environ)
    environment.pop('PYTHONDONTWRITEBYTECODE', None)
    process = subprocess.run([sys.executable, '-I', '-X', 'utf8', *args],
        cwd=root, env=environment, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=30)
    assert process.returncode == expected_code, (process.returncode, process.stderr)
    assert json.loads(process.stdout)['status'] == expected_status, process.stdout
    after = snapshot(root)
    changed = sorted(path for path in before.keys() | after.keys() if before.get(path) != after.get(path))
    dirs_after = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_dir()}
    assert changed == [], ('query changed project files', changed)
    assert dirs_after == dirs_before, ('query created project directories', sorted(dirs_after-dirs_before))
