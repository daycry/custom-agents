import importlib.util
import json
import os
from pathlib import Path
import subprocess

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / 'skills/plugin-panel/scripts/build_panel.py'


@pytest.fixture
def panel():
    spec = importlib.util.spec_from_file_location('plugin_panel', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write(root, path, text):
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding='utf8')


@pytest.fixture
def bundle(tmp_path):
    write(tmp_path, 'agents/demo.md', '\ufeff---\nname: demo\ndescription: >\n  Ayuda con código.\n  token=Password123456\nmodel: sonnet\ntools: Read, Bash\n---\nPRIVATE BODY SHOULD NEVER APPEAR')
    write(tmp_path, 'skills/example/SKILL.md', '---\nname: example\ndescription: "Consulta <script>alert(1)</script>."\n---\nSECRET BODY')
    write(tmp_path, 'commands/demo.md', '---\ndescription: Consulta del catálogo.\n---\n$ARGUMENTS')
    write(tmp_path, 'hooks/hooks.json', json.dumps({'hooks': {'SessionStart': [{'hooks': [{'type': 'command', 'command': 'token=Password123456', 'timeout': 3}]}]}}))
    return tmp_path


def test_catalog_metadata_redacted_without_private_bodies(panel, bundle):
    inventory = panel.build_inventory(bundle)
    assert inventory['counts'] == {'agents': 1, 'skills': 1, 'commands': 1, 'tools': 2, 'hooks': 1}
    assert inventory['agents'][0]['description'] == 'Ayuda con código. token=[secreto redactado]'
    assert inventory['tools'] == ['Bash', 'Read']
    raw = json.dumps(inventory)
    assert 'Password123456' not in raw
    assert 'PRIVATE BODY' not in raw and 'SECRET BODY' not in raw
    assert inventory['hooks'][0] == {'event': 'SessionStart', 'timeout': 3, 'scope': 'global'}


@pytest.mark.parametrize('secret', [
    'token="Password123456"',
    '-----BEGIN PRIVATE KEY-----' + 'TESTKEY123456' * 70 + '-----END PRIVATE KEY-----',
])
def test_redaction_precedes_summary_and_json_encoding(panel, bundle, secret):
    write(bundle, 'agents/demo.md', '---\nname: demo\ndescription: >\n  ' + secret + '\n---')
    data = panel.build_inventory(bundle)
    description = data['agents'][0]['description']
    assert '[secreto redactado]' in description
    assert 'Password123456' not in description
    assert 'TESTKEY' not in description
    assert 'Password123456' not in panel.render_html(data)
    assert 'TESTKEY' not in panel.render_html(data)


def test_html_escapes_metadata_and_has_no_remote_resources(panel, bundle):
    html = panel.render_html(panel.build_inventory(bundle))
    assert '<script>alert(1)</script>' not in html
    assert '&lt;script&gt;alert(1)&lt;/script&gt;' in html
    assert 'https://' not in html and 'fetch(' not in html
    assert 'data-kind="skills"' in html and 'id="search"' in html


def test_bad_frontmatter_and_bad_json_are_visible(panel, bundle):
    write(bundle, 'skills/broken/SKILL.md', '# no frontmatter')
    write(bundle, 'hooks/hooks.json', '{bad json')
    data = panel.build_inventory(bundle)
    assert len(data['warnings']) == 2
    assert data['counts']['hooks'] == 0


def test_symlinks_outside_bundle_are_never_read(panel, bundle, tmp_path):
    outside = tmp_path.parent / (tmp_path.name + '-outside.md')
    outside.write_text('---\nname: leaked\ndescription: PRIVATE\n---', encoding='utf8')
    try:
        (bundle / 'agents/linked.md').symlink_to(outside)
    except OSError:
        pytest.skip('symlinks unavailable')
    data = panel.build_inventory(bundle)
    assert data['counts']['agents'] == 1
    assert any('linked.md' in warning for warning in data['warnings'])


def test_source_presence_does_not_claim_runtime_health(panel, bundle):
    write(bundle, 'interop/codex/hooks.json', '{}')
    data = panel.build_inventory(bundle)
    assert data['runtimes']['codex'] == 'present'
    assert data['runtimes']['opencode'] == 'absent'
    assert data['evidence'] == 'file_inventory; runtime execution not measured'


def test_cli_json_and_owned_html_update(panel, bundle, tmp_path, capsys):
    output = tmp_path / 'panel.html'
    assert panel.main(['--root', str(bundle), '--html', str(output), '--json']) == 0
    assert json.loads(capsys.readouterr().out)['counts']['skills'] == 1
    assert panel.main(['--root', str(bundle), '--html', str(output)]) == 0
    assert output.read_text(encoding='utf8').startswith(panel.MARKER)


def test_cli_never_overwrites_unowned_file(panel, bundle, tmp_path, capsys):
    output = tmp_path / 'mine.html'
    output.write_text('USER CONTENT', encoding='utf8')
    assert panel.main(['--root', str(bundle), '--html', str(output)]) == 2
    assert output.read_text() == 'USER CONTENT'
    assert 'output' in capsys.readouterr().err.lower()


def test_empty_bundle_and_missing_root(panel, tmp_path, capsys):
    assert panel.build_inventory(tmp_path)['counts']['agents'] == 0
    assert panel.main(['--root', str(tmp_path / 'missing')]) == 2
    assert capsys.readouterr().err


def test_memory_is_presence_only_without_reading_bodies(panel, bundle):
    write(bundle, 'docs/knowledge/approved/item.md', 'PRIVATE MEMORY')
    write(bundle, 'graphify-out/graph.json', 'PRIVATE GRAPH')
    data = panel.build_inventory(bundle)
    assert data['memory'] == {'approved_directory': 'present', 'graphify_artifact': 'present'}
    assert 'PRIVATE MEMORY' not in json.dumps(data)


def test_missing_redactor_does_not_emit_metadata(panel, bundle, monkeypatch, capsys):
    monkeypatch.setattr(panel, 'REDACTOR', None)
    assert panel.main(['--root', str(bundle), '--json']) == 2
    assert capsys.readouterr().out == ''


def test_opencode_presence_uses_exporter_path(panel, bundle):
    write(bundle, 'interop/opencode/plugins/custom-agents-hooks.js', '// generated')
    assert panel.build_inventory(bundle)['runtimes']['opencode'] == 'present'


def test_yaml_list_tools_are_counted(panel, bundle):
    write(bundle, 'agents/list.md', '---\nname: list\ndescription: List tools\ntools:\n  - Edit\n  - Write\n---')
    assert panel.build_inventory(bundle)['tools'] == ['Bash', 'Edit', 'Read', 'Write']


@pytest.mark.skipif(os.name != 'nt', reason='Windows junction contract')
def test_windows_directory_junction_is_not_followed(panel, bundle, tmp_path):
    outside = tmp_path.parent / (tmp_path.name + '-junction-target')
    outside.mkdir()
    (outside / 'SKILL.md').write_text('---\nname: private\ndescription: OUTSIDE PRIVATE\n---', encoding='utf8')
    junction = bundle / 'skills/junction'
    result = subprocess.run(['cmd', '/c', 'mklink', '/J', str(junction), str(outside)], capture_output=True, encoding='utf8', errors='replace')
    if result.returncode:
        pytest.skip('junctions unavailable')
    try:
        data = panel.build_inventory(bundle)
        assert 'OUTSIDE PRIVATE' not in json.dumps(data)
        assert data['counts']['skills'] == 1
    finally:
        # Remove only this link; never recursively delete its target.
        os.rmdir(junction)
