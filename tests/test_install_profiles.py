"""Profiles change delivered files, without changing any runtime configuration."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


def exporter():
    spec = importlib.util.spec_from_file_location('profile_export', ROOT/'scripts/export-skills.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_export_core_materializes_only_portable_core(tmp_path):
    out = tmp_path/'package'
    result = exporter().exportar(str(ROOT), str(out), 'all', quiet=True, profile='core')
    assert 'tdd' in result['skills']
    assert not (out/'skills/jira-sync').exists()
    assert not (out/'skills/plugin-panel').exists()
    assert not (out/'commands').exists()
    selection = json.loads((out/'module-selection.json').read_text(encoding='utf-8'))
    assert selection['modules'] == ['core']
    assert selection['delivered_skills'] == result['skills']
    assert exporter().check(str(out)) == []


def test_explicit_integration_modules_are_delivered(tmp_path):
    result = exporter().exportar(str(ROOT), str(tmp_path/'package'), 'claude', quiet=True,
                                profile='core', include=['jira', 'confluence'])
    assert {'jira-sync', 'confluence-publish', 'confluence-pull'} <= set(result['skills'])


def test_invalid_selection_does_not_clear_existing_output(tmp_path):
    out = tmp_path/'package'
    out.mkdir()
    sentinel = out/'user.txt'
    sentinel.write_text('mine', encoding='utf-8')
    with pytest.raises(ValueError):
        exporter().exportar(str(ROOT), str(out), 'all', quiet=True, profile='missing')
    assert sentinel.read_text(encoding='utf-8') == 'mine'


def test_modified_package_is_never_cleared_on_profile_change(tmp_path):
    out = tmp_path/'package'
    module = exporter()
    module.exportar(str(ROOT), str(out), 'claude', quiet=True, profile='full')
    sentinel = out/'skills/tdd/SKILL.md'
    sentinel.write_text('local modifications', encoding='utf-8')
    with pytest.raises(SystemExit):
        module.exportar(str(ROOT), str(out), 'claude', quiet=True, profile='core')
    assert sentinel.read_text(encoding='utf-8') == 'local modifications'


def test_modified_readme_is_preserved_when_regenerating(tmp_path):
    out=tmp_path/'package'
    module=exporter()
    module.exportar(str(ROOT),str(out),'claude',quiet=True,profile='core')
    readme=out/'README.md'
    before=readme.read_text(encoding='utf-8')+'\nUser notes\n'
    readme.write_text(before,encoding='utf-8')
    with pytest.raises(SystemExit):
        module.exportar(str(ROOT),str(out),'claude',quiet=True,profile='core')
    assert readme.read_text(encoding='utf-8')==before


def test_cli_profile_and_dependency_closure(tmp_path):
    out = tmp_path/'package'
    run = subprocess.run([sys.executable, str(ROOT/'scripts/export-skills.py'), '--out', str(out),
                          '--profile', 'core', '--with', 'content', '--quiet'],
                         capture_output=True, text=True, encoding='utf-8', errors='replace')
    assert run.returncode == 0, run.stderr
    selection = json.loads((out/'module-selection.json').read_text(encoding='utf-8'))
    assert selection['modules'] == ['content', 'core', 'voice']
    assert (out/'skills/voice-profile/SKILL.md').is_file()
