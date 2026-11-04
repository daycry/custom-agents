"""The lazy read protocol must remain executable in a portable resource closure."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys


def test_A1_delegation_transmits_read_rules_and_returns_findings():
    root = Path(__file__).resolve().parents[1]
    shared = root / 'agent-kits/shared'
    core = ' '.join((shared / 'read-discipline.md').read_text(encoding='utf-8').split()).casefold()
    assert 'al delegar, transmite estas reglas' in core
    assert 'rutas, líneas y hallazgos, sin volcados' in core
    baseline = json.loads((root / 'docs/roadmap/2026-11-04-token-efficiency/testing/scenario-before.json').read_text(encoding='utf-8'))
    original = baseline['policy_text']['agent-kits/shared/read-discipline.md']
    paragraph = next(line for line in original.splitlines() if line.startswith('Si delegas exploración'))
    assert paragraph in (shared / 'references/source-reuse.md').read_text(encoding='utf-8')


def test_lazy_source_receipt_has_all_portable_dependencies(tmp_path):
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location('token_portable_export', root / 'scripts/export-skills.py')
    exporter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(exporter)
    resources = exporter.fragmentos_shared(str(root), ['agent-kits/shared/read-discipline.md'])
    required = ['references/source-reuse.md', 'source-snapshot.py', 'local-read.py', 'redact.py']
    for name in required:
        assert 'agent-kits/shared/' + name in resources, name
    portable = tmp_path / 'portable'
    for name in resources:
        destination = portable / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / name, destination)
    project = tmp_path / 'project'
    project.mkdir()
    (project / 'source.py').write_bytes(b'value = 1\n')
    command = [sys.executable, '-B', str(portable / 'agent-kits/shared/source-snapshot.py')]
    made = subprocess.run(command + ['snapshot', '--project', str(project), '--file', 'source.py'],
        capture_output=True, encoding='utf-8')
    assert made.returncode == 0, made.stdout + made.stderr
    checked = subprocess.run(command + ['verify', '--project', str(project)], input=made.stdout,
        capture_output=True, encoding='utf-8')
    assert checked.returncode == 0, checked.stdout + checked.stderr
    assert json.loads(checked.stdout)['status'] == 'fresh'
