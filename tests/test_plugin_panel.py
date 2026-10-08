import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / 'skills/plugin-panel/scripts/build_panel.py'


@pytest.mark.parametrize('kind', ['agent', 'skill', 'mcp'])
def test_runtime_filter_is_exclusive_for_extensions_but_hook_only_in_catalog(kind):
    node = shutil.which('node')
    if not node:
        pytest.skip('Node unavailable for panel JavaScript regression')
    template = SCRIPT.parent.parent / 'references/panel.html'
    function = re.search(r'^function connectFilters\([^\n]+', template.read_text(encoding='utf-8'), re.M).group(0)
    harness = r'''
const assert = require('node:assert/strict');
const kind = KIND;
function scenario(sectionId, cards) {
  const controls = {};
  const control = (value) => ({value, handlers:{}, addEventListener(type, callback){this.handlers[type]=callback;}});
  controls.search = control('');
  controls.runtime = control('opencode');
  controls.result = {textContent:''};
  controls[sectionId] = {querySelectorAll(){return cards;}};
  global.document = {getElementById(id){return controls[id];}};
  connectFilters(sectionId,'search','result',[['runtime','runtime']],'items');
  return controls;
}
const extensions = ['codex','opencode'].map(runtime => ({dataset:{kind,runtime},textContent:kind,hidden:false}));
const controls = scenario('extensions',extensions);
assert.deepEqual(extensions.map(card=>card.hidden),[true,false],'extensions runtime must exclude other runtimes');
assert.equal(controls.result.textContent,'1 items visibles');
controls.runtime.value='codex'; controls.runtime.handlers.change();
assert.deepEqual(extensions.map(card=>card.hidden),[false,true]);
controls.runtime.value='all'; controls.runtime.handlers.change();
assert.deepEqual(extensions.map(card=>card.hidden),[false,false]);
const catalog = [
  {dataset:{kind:'agents',runtime:'codex'},textContent:'agent'},
  {dataset:{kind:'hooks',runtime:'codex'},textContent:'hook'},
  {dataset:{kind:'hooks',runtime:'opencode'},textContent:'hook'}
];
scenario('catalog',catalog);
assert.deepEqual(catalog.map(card=>card.hidden),[false,true,false],'catalog runtime selector only filters hooks');
'''.replace('KIND', json.dumps(kind))
    result = subprocess.run([node, '-e', function + '\n' + harness], capture_output=True, text=True, encoding='utf-8')
    assert result.returncode == 0, result.stdout + result.stderr


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
    hook = inventory['hooks'][0]
    assert {key: hook[key] for key in ('event', 'timeout', 'scope')} == {'event': 'SessionStart', 'timeout': 3, 'scope': 'global'}
    assert hook['runtime'] == 'claude-code' and hook['source'] == 'hooks/hooks.json'
    assert hook['load_status'] == hook['execution_status'] == 'unknown'


@pytest.fixture
def extension_sources(tmp_path):
    project, home = tmp_path / 'consumer', tmp_path / 'user'
    project.mkdir()
    home.mkdir()
    for base in (project, home):
        write(base, '.claude/agents/billing.md', '---\nname: billing\ndescription: Billing specialist\n---\nPRIVATE EXTENSION BODY\n')
    write(project, '.claude/personas/billing.md', 'PRIVATE PERSONA BODY\n')
    write(project, '.agents/skills/tax/SKILL.md', '---\nname: tax\ndescription: Tax guidance\n---\nPRIVATE SKILL BODY\n')
    write(project, '.codex/agents/tax.toml', 'name="tax"\ndescription="Tax specialist"\ndeveloper_instructions="PRIVATE INSTRUCTIONS"\n')
    write(project, '.opencode/tools/invoice.ts', 'throw new Error("NEVER EXECUTE THIS");\n')
    write(project, '.mcp.json', json.dumps({'mcpServers': {'ledger': {'type': 'http', 'url': 'https://example.test/private-token', 'headers': {'Authorization': 'private-token'}}}}))
    write(home, '.claude.json', json.dumps({'projects': {str(project): {'disabledMcpServers': ['ledger']}}}))
    return project, home


def test_project_extensions_are_separate_from_bundle_counts(panel, bundle, extension_sources):
    project, home = extension_sources
    baseline = panel.build_inventory(bundle)
    data = panel.build_inventory(bundle, project=project, home=home)
    assert data['counts'] == baseline['counts']
    extensions = data['extensions']
    assert {p['runtime'] for p in extensions['pieces']} == {'claude-code', 'codex', 'opencode'}
    assert {'agent', 'skill', 'persona', 'tool-source', 'mcp'} <= {p['kind'] for p in extensions['pieces']}
    assert {p['scope'] for p in extensions['pieces']} == {'project', 'user'}
    assert extensions['conflicts'] and all(p['availability']=='unverified' for p in extensions['pieces'])
    public = json.dumps(data)
    assert not any(value in public for value in ('PRIVATE EXTENSION BODY', 'PRIVATE PERSONA BODY', 'PRIVATE SKILL BODY', 'PRIVATE INSTRUCTIONS', 'NEVER EXECUTE THIS', 'private-token', 'example.test'))


def test_extension_cards_have_origins_conflicts_and_unverified_availability(panel, bundle, extension_sources):
    project, home = extension_sources
    output = panel.render_html(panel.build_inventory(bundle, project=project, home=home))
    assert 'id="extensions"' in output and 'href="#extensions"' in output
    assert 'id="extension-scope"' in output and 'id="extension-runtime"' in output
    assert 'id="extension-kind"' in output and 'id="extension-search"' in output
    assert 'data-scope="project"' in output and 'data-scope="user"' in output
    assert 'Nombre repetido' in output and 'Disponibilidad sin verificar' in output
    assert 'Deshabilitado en la configuración' in output
    assert 'PRIVATE EXTENSION BODY' not in output and 'private-token' not in output


def test_invalid_mcp_definition_is_visible_without_claiming_connection(panel, bundle, extension_sources):
    project, home = extension_sources
    write(project, '.mcp.json', json.dumps({'mcpServers': {'ledger': {'url': 'https://example.test/private-token'}}}))
    output = panel.render_html(panel.build_inventory(bundle, project=project, home=home))
    assert 'Declaración MCP inválida' in output and 'Disponibilidad sin verificar' in output
    assert 'private-token' not in output


def test_conflict_card_identifies_the_repeated_invocation_name(panel, bundle, extension_sources):
    project, home = extension_sources
    write(project, '.claude/skills/tdd/SKILL.md', '---\nname: special-guidance\ndescription: Guidance\n---\nPRIVATE BODY\n')
    output = panel.render_html(panel.build_inventory(bundle, project=project, home=home, runtime='claude-code'))
    assert 'Nombre repetido: <code>tdd</code>' in output


def test_extension_metadata_html_is_escaped_and_redacted(panel, bundle, extension_sources):
    project, home = extension_sources
    write(project, '.claude/agents/billing.md', '---\nname: "<img src=x onerror=alert(1)>"\ndescription: "token=Password123456"\n---\n')
    output = panel.render_html(panel.build_inventory(bundle, project=project, home=home, runtime='claude-code'))
    assert '<img src=x onerror=alert(1)>' not in output
    assert '&lt;img src=x onerror=alert(1)&gt;' in output
    assert 'Password123456' not in output and '[secreto redactado]' in output


def test_extension_reader_failure_keeps_bundle_panel_usable(panel, bundle, tmp_path, monkeypatch):
    def missing_reader():
        raise FileNotFoundError('must not echo private path')
    monkeypatch.setattr(panel, '_load_pieces', missing_reader)
    data = panel.build_inventory(bundle, project=tmp_path)
    assert data['counts']['agents']==1 and data['extensions']['partial']
    assert data['extensions']['warnings'] and not data['extensions']['pieces']
    output = panel.render_html(data)
    assert 'demo' in output and 'must not echo private path' not in output


def test_inspected_root_cannot_supply_executable_extension_reader(panel, bundle, extension_sources):
    project, home = extension_sources
    write(bundle, 'agent-kits/shared/project-pieces.py', 'raise RuntimeError("UNTRUSTED READER EXECUTED")')
    data = panel.build_inventory(bundle, project=project, home=home, runtime='codex')
    assert data['extensions']['pieces'] and not data['extensions']['partial']
    assert {p['runtime'] for p in data['extensions']['pieces']} == {'codex'}


def test_cli_accepts_project_and_explicit_custom_user_root(panel, bundle, extension_sources, capsys):
    project, home = extension_sources
    custom = home / 'portable'
    write(custom, 'agents/custom.toml', 'name="custom"\ndescription="Personal"\ndeveloper_instructions="private"\n')
    assert panel.main(['--root', str(bundle), '--project', str(project), '--home', str(home), '--runtime', 'codex', '--user-root', 'codex='+str(custom), '--json']) == 0
    data = json.loads(capsys.readouterr().out)
    assert any(p['name']=='custom' and p['scope']=='user' for p in data['extensions']['pieces'])


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
    assert '<strong>2</strong><span>Registros de hook</span>' in rendered
    assert rendered.count('class="card"') == sum(data['counts'].values()) - 4 + 2
    assert 'PRIVATE COMMAND' not in rendered and 'Password123456' not in rendered


def test_grouped_hook_event_escapes_names_and_empty_inventory_counts_zero(panel, bundle):
    data = panel.build_inventory(bundle)
    data['hooks'] = [{'event': '<script>hook()</script>', 'timeout': None, 'scope': 'global'}] * 2
    rendered = panel.render_html(data)
    assert rendered.count('<h2>&lt;script&gt;hook()&lt;/script&gt;</h2>') == 1
    assert '<script>hook()</script>' not in rendered
    data['hooks'] = []
    assert '<strong>0</strong><span>Registros de hook</span>' in panel.render_html(data)


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
    data = panel.build_inventory(bundle, runtime='claude-code')
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
    write(bundle, 'interop/opencode/plugins/custom-agents/index.js', '// generated')
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


def native_hook(root, runtime, *, timeout=3, handler='native-guardrail'):
    launcher = '${CLAUDE_PLUGIN_ROOT}/hooks/run-hook.mjs'
    path = 'hooks/hooks.json' if runtime == 'claude-code' else 'interop/codex/hooks.json'
    suffix = 'claude' if runtime == 'claude-code' else runtime
    write(root, path, json.dumps({'hooks': {
        'PreToolUse': [{'matcher': '^apply_patch$', 'hooks': [{'command': 'node',
            'args': [launcher, handler, '--runtime=' + suffix], 'timeout': 10}]}],
        'SessionEnd': [{'hooks': [{'command': 'node "' + launcher + '" "session-journal.sh" --runtime=' + suffix,
                                'timeout': timeout}]}],
    }}))
    write(root, 'agent-kits/shared/native-roles.json', json.dumps({'schema_version': 1, 'runtimes': {
        'claude': {'implementer': 'custom-agents:implementer', 'architect': 'custom-agents:architect'},
        'codex': {'implementer': 'custom-agents-implementer', 'architect': 'custom-agents-architect'},
    }}))


def test_hooks_use_selected_runtime_and_show_native_guard_identity(panel, bundle):
    native_hook(bundle, 'claude-code', timeout=5)
    native_hook(bundle, 'codex', timeout=3)
    for runtime, timeout, source in [('claude-code', 5, 'hooks/hooks.json'), ('codex', 3, 'interop/codex/hooks.json')]:
        data = panel.build_inventory(bundle, runtime=runtime)
        guard, end = data['hooks']
        assert {item['runtime'] for item in data['hooks']} == {runtime}
        assert guard['handler'] == 'native-guardrail' and guard['behavior'] == 'guard'
        assert len(guard['role_ids']) == 2 and 'custom-agents' in guard['role_ids'][0]
        assert guard['source'] == source and guard['load_status'] == guard['execution_status'] == 'unknown'
        assert end['timeout'] == timeout and end['timeout_unit'] == 's'
        assert end['timeout_provenance'] == 'runtime-registration'
        output = panel.render_html(data)
        assert 'Guardia de roles' in output and 'Carga sin verificar' in output
        assert source in output and '--runtime=' not in output and 'run-hook.mjs' not in output


@pytest.mark.parametrize('timeout', [True, False, float('nan'), float('inf'), -2, 0, '3', 10 ** 400])
def test_invalid_timeouts_are_diagnostic_not_budget_claims(panel, bundle, timeout):
    native_hook(bundle, 'codex', timeout=timeout)
    data = panel.build_inventory(bundle, runtime='codex')
    end = next(item for item in data['hooks'] if item['event'] == 'SessionEnd')
    assert end['timeout'] is None and end['timeout_status'] == 'invalid'
    assert data['warnings'] and 'Presupuesto inválido' in panel.render_html(data)


def test_runtime_source_failure_never_falls_back_to_claude(panel, bundle):
    data = panel.build_inventory(bundle, runtime='codex')
    assert data['hooks'] == [] and data['hook_sources']['codex']['status'] == 'missing'
    assert data['warnings']
    native_hook(bundle, 'codex')
    write(bundle, 'interop/codex/hooks.json', '{private invalid source')
    data = panel.build_inventory(bundle, runtime='all')
    assert data['hook_sources']['codex']['status'] == 'invalid'
    assert any(item['runtime'] == 'claude-code' for item in data['hooks'])
    assert 'private invalid' not in json.dumps(data)


def test_all_groups_by_runtime_event_without_collapsing_handlers(panel, bundle):
    native_hook(bundle, 'claude-code', timeout=5)
    native_hook(bundle, 'codex', timeout=3)
    data = panel.build_inventory(bundle, runtime='all')
    assert data['counts']['hooks'] == 4
    assert data['hook_group_count'] == 4
    output = panel.render_html(data)
    assert output.count('<h2>SessionEnd</h2>') == 2
    assert 'id="hook-runtime"' in output and 'data-runtime="codex"' in output
    assert 'Registros de hook' in output


def test_opencode_reads_only_literal_data_and_exposes_adapter_budget(panel, bundle):
    source = Path(__file__).resolve().parents[1] / 'hooks/opencode-plugin.js'
    raw = source.read_text(encoding='utf-8')
    write(bundle, 'hooks/opencode-plugin.js', 'throw new Error("FOREIGN CODE");\n' + raw)
    data = panel.build_inventory(bundle, runtime='opencode')
    assert len(data['hooks']) == 7
    guard = next(item for item in data['hooks'] if item['behavior'] == 'guard')
    assert guard['native_event'] == 'tool.execute.before' and guard['timeout'] == 10500
    assert guard['timeout_unit'] == 'ms' and guard['timeout_provenance'] == 'adapter-supervision'
    assert guard['role_ids'] == [] and data['warnings']  # No role map in this fixture.
    end = next(item for item in data['hooks'] if item['event'] == 'SessionEnd')
    assert end['timeout'] == 20000 and 'session.execution.succeeded' in end['native_event']
    assert 'FOREIGN CODE' not in panel.render_html(data)


@pytest.mark.parametrize('alteration', ['missing', 'duplicate', 'invalid', 'oversized'])
def test_opencode_contract_drift_is_unknown_without_executing_source(panel, bundle, alteration):
    raw = (Path(__file__).resolve().parents[1] / 'hooks/opencode-plugin.js').read_text(encoding='utf-8')
    marker = '// custom-agents hook-catalog:start'
    assert marker in raw
    if alteration == 'missing': raw = raw.replace(marker, '// missing')
    elif alteration == 'duplicate': raw += '\n' + marker
    elif alteration == 'invalid': raw = raw.replace('"schema_version": 1', '"schema_version": 99')
    else: raw += 'x' * (panel.MAX_BYTES + 1)
    write(bundle, 'hooks/opencode-plugin.js', raw)
    data = panel.build_inventory(bundle, runtime='opencode')
    assert data['hooks'] == [] and data['hook_sources']['opencode']['status'] == 'invalid'
    assert data['warnings']


def test_unknown_role_map_does_not_invent_guarded_identity(panel, bundle):
    native_hook(bundle, 'codex')
    write(bundle, 'agent-kits/shared/native-roles.json', '{bad private role map')
    data = panel.build_inventory(bundle, runtime='codex')
    guard = data['hooks'][0]
    assert guard['role_ids'] == [] and guard['identity_status'] == 'unknown'
    assert 'bad private' not in panel.render_html(data)


def test_boolean_native_role_map_version_is_unknown(panel, bundle):
    native_hook(bundle, 'codex')
    path = bundle / 'agent-kits/shared/native-roles.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    data['schema_version'] = True
    path.write_text(json.dumps(data), encoding='utf-8')
    guard = panel.build_inventory(bundle, runtime='codex')['hooks'][0]
    assert guard['role_ids'] == [] and guard['identity_status'] == 'unknown'


def test_unidentified_hook_behavior_is_unknown(panel, bundle):
    hook = panel.build_inventory(bundle, runtime='claude-code')['hooks'][0]
    assert hook['behavior'] == 'unknown'
    assert 'Comportamiento: Sin identificar' in panel.render_html(panel.build_inventory(bundle, runtime='claude-code'))


@pytest.mark.parametrize('identifier,handler', [('post', 'native-guardrail'), ('prompt', 'progress-line.sh'),
                                             ('context', 'session-journal.sh'), ('capture', 'session-context.sh')])
def test_opencode_contract_rejects_handlers_incompatible_with_callback(panel, bundle, identifier, handler):
    raw = (Path(__file__).resolve().parents[1] / 'hooks/opencode-plugin.js').read_text(encoding='utf-8')
    expression = r'(const hookCatalog = JSON\.parse\(`)([\s\S]*?)(`\);)'
    import re
    found = re.search(expression, raw)
    catalog = json.loads(found.group(2))
    binding = next(item for item in catalog['bindings'] if item['id'] == identifier)
    binding['handlers'].append(handler) if identifier == 'post' else binding.update(handlers=[handler])
    raw = re.sub(expression, lambda match: match[1] + json.dumps(catalog) + match[3], raw, count=1)
    write(bundle, 'hooks/opencode-plugin.js', raw)
    data = panel.build_inventory(bundle, runtime='opencode')
    assert data['hooks'] == [] and data['hook_sources']['opencode']['status'] == 'invalid'


@pytest.mark.parametrize('change', [
    'non_object', 'duplicate_key', 'no_bindings', 'duplicate_id', 'wrong_domain',
    'empty_handlers', 'multiple_single_handler', 'invalid_budget', 'invalid_event',
    'invalid_activation', 'invalid_idle', 'invalid_tools', 'interpolation', 'wrong_literal',
])
def test_malformed_opencode_literal_is_unknown_and_keeps_catalog(panel, bundle, change):
    import re
    raw = (Path(__file__).resolve().parents[1] / 'hooks/opencode-plugin.js').read_text(encoding='utf-8')
    expression = r'(const hookCatalog = JSON\.parse\(`)([\s\S]*?)(`\);)'
    catalog = json.loads(re.search(expression, raw)[2])
    if change == 'non_object': catalog = []
    elif change == 'no_bindings': catalog['bindings'] = []
    elif change == 'duplicate_id': catalog['bindings'][1]['id'] = 'guard'
    elif change == 'wrong_domain': catalog['bindings'][1]['domain'] = 'event'
    elif change == 'empty_handlers': catalog['bindings'][1]['handlers'] = []
    elif change == 'multiple_single_handler': catalog['bindings'][1]['handlers'] *= 2
    elif change == 'invalid_budget': catalog['bindings'][1]['timeout_ms'] = True
    elif change == 'invalid_event': catalog['bindings'][1]['native_event'] = 'Bad<script>'
    elif change == 'invalid_activation': catalog['bindings'][1]['activation'] = None
    elif change == 'invalid_idle': catalog['bindings'][-1]['idle_status'] = 'running'
    elif change == 'invalid_tools': catalog['bindings'][-2]['tools'] = ['bad/tool']
    payload = json.dumps(catalog)
    if change == 'duplicate_key': payload = payload.replace('"schema_version": 1', '"schema_version": 1, "schema_version": 1')
    if change == 'interpolation': payload = payload.replace('Text prompt', '${privateExpression()} Text prompt')
    raw = re.sub(expression, lambda match: match[1] + payload + match[3], raw, count=1)
    if change == 'wrong_literal': raw = raw.replace('const hookCatalog = JSON.parse(`', 'const hookCatalog = JSON.parse(String.raw`')
    write(bundle, 'hooks/opencode-plugin.js', raw)
    data = panel.build_inventory(bundle, runtime='opencode')
    assert data['hooks'] == [] and data['hook_sources']['opencode']['status'] == 'invalid'
    assert data['counts']['agents'] == 1
    assert 'privateExpression' not in panel.render_html(data)


@pytest.mark.parametrize('events', [[], {'SessionStart': None}, {'SessionStart': [None]},
                                  {'SessionStart': [{'hooks': None}]},
                                  {'SessionStart': [{'hooks': [None]}]},
                                  {'SessionStart': [{'hooks': [{}] * 1001}]}])
def test_malformed_native_hook_groups_fail_independently(panel, bundle, events):
    write(bundle, 'interop/codex/hooks.json', json.dumps({'hooks': events}))
    data = panel.build_inventory(bundle, runtime='all')
    assert data['hook_sources']['codex']['status'] == 'invalid'
    assert len(data['hooks']) == 1 and data['hooks'][0]['runtime'] == 'claude-code'


def test_absent_timeout_and_mismatched_runtime_launcher_are_explicit(panel, bundle):
    native_hook(bundle, 'codex', timeout=None)
    data = panel.build_inventory(bundle, runtime='codex')
    assert data['hooks'][-1]['timeout_status'] == 'absent'
    assert 'Timeout: no declarado' in panel.render_html(data)
    path = bundle / 'interop/codex/hooks.json'
    path.write_text(path.read_text(encoding='utf-8').replace('--runtime=codex', '--runtime=claude'), encoding='utf-8')
    hooks = panel.build_inventory(bundle, runtime='codex')['hooks']
    assert all('handler' not in item and item['behavior'] == 'unknown' for item in hooks)


def test_empty_native_declaration_differs_from_missing_source(panel, bundle):
    write(bundle, 'interop/codex/hooks.json', '{"hooks":{}}')
    data = panel.build_inventory(bundle, runtime='codex')
    assert data['hooks'] == [] and data['hook_sources']['codex']['status'] == 'declared'
    assert data['warnings'] == []


def test_oversized_role_map_is_unknown_without_exporting_contents(panel, bundle):
    native_hook(bundle, 'codex')
    write(bundle, 'agent-kits/shared/native-roles.json', '{"private":"' + 'x' * 65537 + '"}')
    data = panel.build_inventory(bundle, runtime='codex')
    assert data['hooks'][0]['role_ids'] == [] and data['warnings']


def test_linked_runtime_declaration_is_rejected(panel, bundle, tmp_path):
    outside = tmp_path / 'own-outside.json'
    outside.write_text('{"hooks":{"PRIVATE":[]}}', encoding='utf-8')
    target = bundle / 'interop/codex/hooks.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    try: target.symlink_to(outside)
    except OSError: pytest.skip('symlinks unavailable')
    data = panel.build_inventory(bundle, runtime='codex')
    assert data['hooks'] == [] and data['hook_sources']['codex']['status'] == 'invalid'
    assert 'PRIVATE' not in json.dumps(data)


def test_runtime_filter_navigation_and_mobile_sources_preserve_stage_controls(panel, bundle):
    output = panel.render_html(panel.build_inventory(bundle))
    assert 'href="#main"' in output and 'id="main"' in output
    assert 'id="navigation-status"' in output and 'aria-live="polite"' in output
    assert '.sidebar nav a:last-child{display:none}' not in output
    assert 'Las guardias pertenecen a los agentes' not in output
    assert 'syncNavigation' in output and 'aria-pressed' in output and '.flow-detail' in output
