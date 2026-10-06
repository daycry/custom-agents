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


def test_hook_event_card_groups_handlers_without_changing_json_inventory(panel, bundle):
    write(bundle, 'hooks/hooks.json', json.dumps({'hooks': {
        'PostToolUse': [
            {'hooks': [{'command': 'PRIVATE COMMAND', 'timeout': 3}, {'command': 'token=Password123456'}]},
            {'hooks': [{'command': 'ANOTHER PRIVATE COMMAND', 'timeout': 8}]},
        ],
        'SessionStart': [{'hooks': [{'timeout': 5}]}],
    }}))
    data = panel.build_inventory(bundle)
    rendered = panel.render_html(data)
    assert data['counts']['hooks'] == len(data['hooks']) == 4
    assert rendered.count('<h2>PostToolUse</h2>') == 1
    assert '3 acciones configuradas' in rendered
    assert '<strong>Acción 1</strong>' in rendered and 'Timeout: 3 s' in rendered
    assert '<strong>Acción 2</strong>' in rendered and 'not declared' not in rendered
    assert '<strong>Acción 3</strong>' in rendered and 'Timeout: 8 s' in rendered
    assert '<strong>2</strong><span>Eventos de hook</span>' in rendered
    assert rendered.count('class="card"') == sum(data['counts'].values()) - 4 + 2
    assert 'PRIVATE COMMAND' not in rendered and 'Password123456' not in rendered


def test_grouped_hook_event_escapes_names_and_empty_inventory_counts_zero(panel, bundle):
    data = panel.build_inventory(bundle)
    data['hooks'] = [{'event': '<script>hook()</script>', 'timeout': None, 'scope': 'global'}] * 2
    rendered = panel.render_html(data)
    assert rendered.count('<h2>&lt;script&gt;hook()&lt;/script&gt;</h2>') == 1
    assert '<script>hook()</script>' not in rendered
    data['hooks'] = []
    assert '<strong>0</strong><span>Eventos de hook</span>' in panel.render_html(data)


def test_hook_handlers_show_public_purpose_script_and_matcher_without_commands(panel, bundle):
    write(bundle, 'hooks/mark-docs-pending.sh', '#!/bin/sh\n# panel-description: Mark edited docs pending. token="Password123456"\nPRIVATE SCRIPT BODY')
    write(bundle, 'hooks/session-journal.sh', '#!/bin/sh\n# panel-description: Capture <end> envelope locally.\nPRIVATE SCRIPT BODY')
    write(bundle, 'hooks/hooks.json', json.dumps({'hooks': {
        'PostToolUse': [{'matcher': 'Write|Edit|MultiEdit', 'hooks': [{'command': 'node "${CLAUDE_PLUGIN_ROOT}/hooks/run-hook.mjs" mark-docs-pending.sh'}]}],
        'SessionEnd': [{'hooks': [{'command': 'node', 'args': ['${CLAUDE_PLUGIN_ROOT}/hooks/run-hook.mjs', 'session-journal.sh'], 'timeout': 5}]}],
    }}))
    data = panel.build_inventory(bundle)
    rendered = panel.render_html(data)
    assert data['hooks'][0]['handler'] == 'mark-docs-pending.sh'
    assert data['hooks'][0]['matcher'] == 'Write|Edit|MultiEdit'
    assert 'Mark edited docs pending. token=&quot;[secreto redactado]&quot;' in rendered
    assert 'mark-docs-pending.sh' in rendered and 'Write · Edit · MultiEdit' in rendered
    assert 'session-journal.sh' in rendered and 'Capture &lt;end&gt; envelope locally.' in rendered
    assert 'Password123456' not in rendered and 'PRIVATE SCRIPT BODY' not in rendered
    assert 'run-hook.mjs' not in rendered and 'CLAUDE_PLUGIN_ROOT' not in rendered


def test_hook_command_variations_cannot_choose_external_sources(panel, bundle):
    write(bundle, 'hooks/hooks.json', json.dumps({'hooks': {'PostToolUse': [{'hooks': [
        {'command': 'node "${CLAUDE_PLUGIN_ROOT}/hooks/run-hook.mjs" ../private.sh'},
        {'command': 'node', 'args': ['PRIVATE LAUNCHER', 'private.sh']},
    ]}]}}))
    data = panel.build_inventory(bundle)
    assert all('handler' not in hook for hook in data['hooks'])
    assert 'PRIVATE LAUNCHER' not in panel.render_html(data)


def test_missing_bundled_template_is_diagnostic_and_keeps_json_available(panel, bundle, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(panel, 'TEMPLATE', bundle / 'missing-template.html', raising=False)
    assert panel.main(['--root', str(bundle), '--html', str(tmp_path / 'panel.html')]) == 2
    assert 'bundled panel template unavailable' in capsys.readouterr().err
    assert panel.main(['--root', str(bundle), '--json']) == 0
    assert json.loads(capsys.readouterr().out)['counts']['agents'] == 1


def test_template_markers_inside_metadata_remain_plain_text(panel, bundle):
    write(bundle, 'agents/demo.md', '---\nname: demo\ndescription: @@WORKFLOW@@ @@NOTES@@\n---')
    rendered = panel.render_html(panel.build_inventory(bundle))
    assert '@@WORKFLOW@@ @@NOTES@@' in rendered
    assert rendered.count('id="workflow"') == 1


def test_hook_public_metadata_is_read_once_per_script_per_inventory(panel, bundle, monkeypatch):
    write(bundle, 'hooks/progress-line.sh', '#!/bin/sh\n# panel-title: Progress\n# panel-description: Shows progress.\n')
    write(bundle, 'hooks/hooks.json', json.dumps({'hooks': {'PostToolUse': [
        {'matcher': 'Write', 'hooks': [{'command': 'node "${CLAUDE_PLUGIN_ROOT}/hooks/run-hook.mjs" progress-line.sh'}]},
        {'matcher': 'Edit', 'hooks': [{'command': 'node "${CLAUDE_PLUGIN_ROOT}/hooks/run-hook.mjs" progress-line.sh'}]},
    ]}}))
    original = panel._read
    reads = []
    def track(root, path):
        if path.name == 'progress-line.sh':
            reads.append(path)
        return original(root, path)
    monkeypatch.setattr(panel, '_read', track)
    data = panel.build_inventory(bundle)
    assert len(reads) == 1
    assert [hook['matcher'] for hook in data['hooks']] == ['Write', 'Edit']
    panel.build_inventory(bundle)
    assert len(reads) == 2


def test_flow_links_only_point_to_present_rendered_native_roles(panel, bundle):
    data = panel.build_inventory(bundle)
    data['agents'].append({'name': 'architect', 'description': 'Designs architecture.', 'model': '', 'tools': [], 'source': 'agents/architect.md'})
    data['workflow']['roles'] = {'architect': []}
    rendered = panel.render_html(data)
    assert 'href="#role-architect"' in rendered and 'id="role-architect"' in rendered
    assert 'href="#role-qa"' not in rendered
    assert 'Roles no disponibles en esta instantánea.' in rendered


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


def test_workflow_role_guides_use_inspected_sources_and_no_execution_claim(panel, bundle):
    write(bundle, 'agent-kits/shared/capability-catalog.json', json.dumps({'version': 1, 'capabilities': [{'id': 'research-first', 'roles': ['analyst'], 'stacks': [], 'areas': ['research']}]}))
    write(bundle, 'skills/research-first/SKILL.md', '---\nname: research-first\ndescription: Research\n---\n')
    data = panel.build_inventory(bundle)
    assert data['workflow']['source'] == 'agent-kits/shared/capability-catalog.json'
    assert data['workflow']['selection_only'] is True
    assert data['workflow']['roles']['analyst'] == ['research-first']
    html = panel.render_html(data)
    assert 'Tu workflow, rol a rol' in html and 'workflow-role' in html
    assert 'research-first' in html


def test_foreign_routing_code_is_never_imported(panel, bundle):
    write(bundle, 'agent-kits/shared/capability-route.py', 'raise RuntimeError("FOREIGN CODE")')
    write(bundle, 'agent-kits/shared/capability-catalog.json', '{invalid private text')
    data = panel.build_inventory(bundle)
    assert data['workflow']['roles'] == {}
    assert any('capability-catalog.json' in warning for warning in data['warnings'])
    assert 'private text' not in json.dumps(data)


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


def test_workflow_responsibilities_use_redacted_role_definitions(panel, bundle):
    data = panel.build_inventory(bundle)
    data['workflow']['roles'] = {'demo': ['example'], 'absent': []}
    rendered = panel.render_html(data)
    assert 'Responsabilidad: Ayuda con código. token=[secreto redactado]' in rendered
    assert 'Definición del rol no disponible en esta instantánea' in rendered
    assert 'Password123456' not in rendered


def test_workflow_responsibility_is_html_escaped(panel, bundle):
    write(bundle, 'agents/demo.md', '---\nname: demo\ndescription: <script>private()</script>\n---')
    data = panel.build_inventory(bundle)
    data['workflow']['roles'] = {'demo': []}
    rendered = panel.render_html(data)
    assert 'Responsabilidad: &lt;script&gt;private()&lt;/script&gt;' in rendered
    assert '<script>private()</script>' not in rendered


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
