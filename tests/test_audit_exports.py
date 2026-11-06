import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location('audit_export_' + name.replace('-', '_'), ROOT / 'scripts' / name)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('profile', [None, 'core'])
def test_r18_portable_router_has_a_catalog_matching_delivered_skills(tmp_path, profile):
    mod = load('export-skills.py')
    out = tmp_path / 'portable'
    mod.exportar(str(ROOT), str(out), 'all', quiet=True, profile=profile)
    catalog = out / 'agent-kits/shared/capability-catalog.json'
    assert catalog.is_file(), 'The router data dependency did not travel.'
    entries = json.loads(catalog.read_bytes())['capabilities']
    assert entries and all((out / 'skills' / row['id'] / 'SKILL.md').is_file() for row in entries)
    result = subprocess.run([sys.executable, '-B', str(out / 'agent-kits/shared/capability-route.py'), '--check', '--json'],
                            cwd=tmp_path, capture_output=True, text=True, encoding='utf8', timeout=30)
    assert result.returncode == 0, result.stderr


def test_r19_preflight_rejects_hardlink_before_any_export_is_written(tmp_path):
    mod = load('export-interop.py')
    root = tmp_path / 'delivery'; root.mkdir()
    outside = tmp_path / 'unrelated.md'; outside.write_bytes(b'Unrelated canary.\n')
    linked = root / 'interop/opencode/commands/setup.md'; linked.parent.mkdir(parents=True)
    os.link(outside, linked)
    plan = {'interop/opencode/commands/new.md': 'New generated text.\n',
            'interop/opencode/commands/setup.md': 'Replacement generated text.\n'}
    with pytest.raises((ValueError, OSError)):
        mod.escribir(str(root), plan, quiet=True)
    assert outside.read_bytes() == b'Unrelated canary.\n'
    assert not linked.with_name('new.md').exists()
