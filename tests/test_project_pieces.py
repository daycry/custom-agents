"""User declarations must be discovered without executing them or exporting secrets."""
import hashlib
import importlib.util
import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'agent-kits/shared/project-pieces.py'


@pytest.fixture
def reader():
    spec = importlib.util.spec_from_file_location('project_pieces_test', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def locations(tmp_path):
    project, home = tmp_path / 'project', tmp_path / 'home'
    project.mkdir()
    home.mkdir()
    return project, home


def put(root, relative, text):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode('utf-8'))
    return path


def markdown(name, description='Local guidance'):
    return f'---\nname: {name}\ndescription: {description}\n---\nPRIVATE BODY MUST NOT BE EXPORTED\n'


def test_discovers_native_agents_skills_personas_and_tools_without_execution(reader, locations):
    project, home = locations
    put(project, '.claude/agents/billing.md', markdown('billing'))
    put(project, '.claude/skills/billing/SKILL.md', markdown('billing'))
    put(project, '.claude/personas/billing.md', '# Billing persona\nPrivate domain body\n')
    put(project, '.codex/agents/tax.toml', 'name="tax"\ndescription="Tax specialist"\ndeveloper_instructions="private"\n')
    put(project, '.agents/skills/tax/SKILL.md', markdown('tax'))
    put(project, '.opencode/agents/invoice.md', '---\ndescription: Invoice specialist\n---\nPrivate body\n')
    put(project, '.opencode/tools/invoice.ts', 'throw new Error("must never execute");\n')
    result = reader.discover(project, home=home)
    triples = {(x['runtime'], x['kind'], x['name']) for x in result['pieces']}
    assert ('claude-code', 'agent', 'billing') in triples
    assert ('claude-code', 'skill', 'billing') in triples
    assert ('codex', 'agent', 'tax') in triples
    assert ('codex', 'skill', 'tax') in triples
    assert ('opencode', 'agent', 'invoice') in triples
    assert ('opencode', 'tool-source', 'invoice') in triples
    assert {x['runtime'] for x in result['pieces'] if x['kind']=='persona'} == {'claude-code','codex','opencode'}
    assert all(x['availability']=='unverified' for x in result['pieces'])
    assert all(x['ownership']=='unmanaged' for x in result['pieces'])
    assert 'PRIVATE BODY' not in json.dumps(result)
    assert not result['partial']


def test_claude_mcp_scopes_do_not_leak_configuration(reader, locations):
    project, home = locations
    secret='sk-ant-'+('x'*40)
    put(project, '.mcp.json', json.dumps({'mcpServers':{'shared':{'type':'http','url':'https://example.test/?token='+secret,'headers':{'Authorization':secret}}}}))
    put(home, '.claude.json', json.dumps({'mcpServers':{'personal':{'command':'private-command','args':[secret]}},'projects':{str(project):{'mcpServers':{'local':{'command':'private-local'}}},str(home/'other'):{'mcpServers':{'other-project':{'command':'never'}}}}}))
    result=reader.discover(project, home=home, runtime='claude-code')
    servers=[x for x in result['pieces'] if x['kind']=='mcp']
    assert {x['name'] for x in servers} == {'shared','personal','local'}
    assert {x['scope'] for x in servers} == {'project','user','local'}
    assert not any(s in json.dumps(result) for s in (secret,'private-command','private-local','example.test'))


def test_codex_toml_mcp_and_opencode_jsonc_inline_agent(reader, locations):
    project, home=locations
    put(project,'.codex/config.toml','[mcp_servers.docs]\ncommand="private-server"\nenabled=false\n[mcp_servers.docs.env]\nTOKEN="private-token"\n')
    put(project,'opencode.jsonc','''{
      // JSONC comments and trailing commas are valid
      "agent": {"billing": {"description": "Bills", "prompt": "private prompt",},},
      "mcp": {"billing": {"type": "remote", "url": "https://example.test//mcp", "enabled": false,},},
    }''')
    result=reader.discover(project,home=home)
    assert any(x['runtime']=='codex' and x['name']=='docs' and x['enabled'] is False for x in result['pieces'])
    assert any(x['runtime']=='opencode' and x['kind']=='agent' and x['name']=='billing' for x in result['pieces'])
    assert any(x['runtime']=='opencode' and x['kind']=='mcp' and x['transport']=='remote' and x['enabled'] is False for x in result['pieces'])
    assert 'private' not in json.dumps(result)
    assert not result['partial']


def test_nested_and_user_skills_preserve_collisions_and_stable_ids(reader, locations):
    project,home=locations
    cwd=project/'services'/'billing'
    cwd.mkdir(parents=True)
    for base in (project,cwd,home):
        put(base,'.agents/skills/billing/SKILL.md',markdown('billing'))
    before=reader.discover(project,home=home,cwd=cwd,runtime='codex')
    pieces=[x for x in before['pieces'] if x['name']=='billing']
    assert len(pieces)==3 and len({x['id'] for x in pieces})==3
    assert {x['scope'] for x in pieces}=={'project','user'}
    assert len(before['conflicts'])==1
    assert set(before['conflicts'][0]['ids'])=={x['id'] for x in pieces}
    assert before==reader.discover(project,home=home,cwd=cwd,runtime='codex')


def test_only_selected_runtime_and_project_only(reader, locations):
    project,home=locations
    put(project,'.claude/agents/local.md',markdown('local'))
    put(home,'.claude/agents/personal.md',markdown('personal'))
    put(project,'.codex/agents/other.toml','name="other"\ndescription="Other"\ndeveloper_instructions="private"\n')
    result=reader.discover(project,home=home,runtime='claude-code',include_user=False)
    assert [(x['runtime'],x['name']) for x in result['pieces']]==[('claude-code','local')]


@pytest.mark.parametrize('raw',['{"mcp":{"x":{},"x":{}}}', '{"mcp":', '{"mcp":{"x":{"enabled":"yes"}}}'])
def test_invalid_or_ambiguous_config_warns_without_echoing_values(reader,locations,raw):
    project,home=locations
    put(project,'opencode.json',raw)
    result=reader.discover(project,home=home,runtime='opencode')
    assert result['partial'] and result['warnings']
    assert raw not in json.dumps(result)


def test_limits_are_explicit_and_dont_hide_missing_pieces(reader,locations,monkeypatch):
    project,home=locations
    for name in ('one','two','three'):
        put(project,f'.claude/agents/{name}.md',markdown(name))
    monkeypatch.setattr(reader,'MAX_PIECES',2)
    result=reader.discover(project,home=home,runtime='claude-code')
    assert not result['pieces']
    assert result['partial'] and any('limit' in x for x in result['warnings'])


def test_oversized_and_deep_config_degrade(reader,locations,monkeypatch):
    project,home=locations
    monkeypatch.setattr(reader,'MAX_BYTES',64)
    put(project,'.mcp.json','x'*65)
    result=reader.discover(project,home=home,runtime='claude-code')
    assert result['partial'] and not result['pieces']
    monkeypatch.setattr(reader,'MAX_BYTES',1024*1024)
    put(project,'.mcp.json','{"mcpServers":'+('['*40)+'0'+(']'*40)+'}')
    assert reader.discover(project,home=home,runtime='claude-code')['partial']


def test_redirecting_paths_are_excluded(reader,locations):
    project,home=locations
    elsewhere=put(home,'outside/billing.md',markdown('billing'))
    destination=project/'.claude/agents/billing.md'
    destination.parent.mkdir(parents=True)
    try:
        destination.symlink_to(elsewhere)
    except OSError:
        pytest.skip('symlink privilege unavailable')
    result=reader.discover(project,home=home,runtime='claude-code')
    assert not result['pieces'] and result['partial']


def test_metadata_is_redacted_before_summary(reader,locations):
    project,home=locations
    secret='sk-ant-'+('x'*40)
    put(project,'.claude/agents/billing.md',markdown('billing',f'API_KEY="{secret}" '+('x'*2000)))
    result=reader.discover(project,home=home,runtime='claude-code')
    assert secret not in json.dumps(result)
    assert len(result['pieces'][0]['description'])<=480


def test_o1_property_uses_full_content_lf_hash_and_detects_modification(reader,locations):
    project,home=locations
    path=put(project,'.claude/agents/billing.md',markdown('billing'))
    raw=path.read_bytes()
    row={'nombre':'billing','forma':'agente','area':'billing','origen':'generada','creada':'2026-10-06','evidencia':[], 'confirmaciones':{'tools':[],'arbol_plugin':None,'tope':None}, 'destinos':[{'runtime':'claude-code','ruta':'.claude/agents/billing.md','canonica':True,'hash':'sha256:'+hashlib.sha256(raw.replace(b'\r\n',b'\n')).hexdigest()}]}
    put(project,'.claude/pieces.json',json.dumps({'version':1,'hash_version':'sha256-lf-1','piezas':[row]}))
    path.write_bytes(raw.replace(b'\n',b'\r\n'))
    result=reader.discover(project,home=home,runtime='claude-code')
    assert result['registry_status']=='valid' and result['pieces'][0]['ownership']=='managed'
    path.write_bytes(raw+b'changed\n')
    assert reader.discover(project,home=home,runtime='claude-code')['pieces'][0]['ownership']=='modified'


def test_corrupt_registry_cannot_claim_ownership(reader,locations):
    project,home=locations
    put(project,'.claude/agents/billing.md',markdown('billing'))
    put(project,'.claude/pieces.json','{"private":"token", "version":999}')
    result=reader.discover(project,home=home,runtime='claude-code')
    assert result['registry_status']=='invalid'
    assert result['pieces'][0]['ownership']=='unknown'
    assert result['partial'] and 'token' not in json.dumps(result)


def test_cwd_outside_selected_project_is_rejected(reader,locations):
    project,home=locations
    with pytest.raises(ValueError):
        reader.discover(project,home=home,cwd=home)


def test_missing_tomllib_does_not_break_other_runtime_inventory(reader,locations,monkeypatch):
    project,home=locations
    monkeypatch.setattr(reader,'tomllib',None)
    put(project,'.codex/agents/billing.toml','name="billing"\ndescription="Bills"\ndeveloper_instructions="private"\n')
    put(project,'.claude/agents/billing.md',markdown('billing'))
    result=reader.discover(project,home=home)
    assert any(x['runtime']=='claude-code' for x in result['pieces'])
    assert result['partial']


def test_configuration_defined_codex_role_keeps_layer_reference(reader,locations):
    project,home=locations
    put(project,'.codex/config.toml','[agents]\nenabled=true\n[agents.billing]\ndescription="Bills"\nconfig_file="roles/billing.toml"\n')
    put(project,'.codex/roles/billing.toml','developer_instructions="Private billing doctrine"\n')
    result=reader.discover(project,home=home,runtime='codex')
    agents=[x for x in result['pieces'] if x['kind']=='agent']
    assert len(agents)==1 and agents[0]['name']=='billing'
    assert agents[0]['definition_source']=='project/.codex/roles/billing.toml'
    assert 'Private billing doctrine' not in json.dumps(result)
    assert not result['partial']


def test_role_config_file_outside_root_is_not_followed(reader,locations):
    project,home=locations
    put(home,'outside.toml','developer_instructions="private"\n')
    put(project,'.codex/config.toml', '[agents.billing]\ndescription="Bills"\nconfig_file="../../home/outside.toml"\n')
    result=reader.discover(project,home=home,runtime='codex')
    assert result['partial']
    assert not any(x['kind']=='agent' for x in result['pieces'])


def test_explicit_runtime_user_root_is_inspected_without_default_root_claim(reader,locations):
    project,home=locations
    custom=home/'portable-codex'
    put(custom,'agents/billing.toml','name="billing"\ndescription="Bills"\ndeveloper_instructions="private"\n')
    put(home,'.codex/agents/default.toml','name="default"\ndescription="Default"\ndeveloper_instructions="private"\n')
    result=reader.discover(project,home=home,runtime='codex',user_roots={'codex':custom})
    assert [x['name'] for x in result['pieces'] if x['kind']=='agent']==['billing']
    assert result['pieces'][0]['source']=='user/agents/billing.toml'


def test_opencode_file_and_config_commands_are_discovered(reader,locations):
    project,home=locations
    put(project,'.opencode/commands/billing.md','---\ndescription: Billing report\n---\nprivate command\n')
    put(project,'opencode.json',json.dumps({'command':{'report':{'description':'Report','template':'private template'}}}))
    result=reader.discover(project,home=home,runtime='opencode')
    assert {x['name'] for x in result['pieces'] if x['kind']=='command'}=={'billing','report'}
    assert 'private' not in json.dumps(result)


def test_embedded_codex_agent_mcp_preserves_agent_scope(reader,locations):
    project,home=locations
    put(project,'.codex/agents/billing.toml','name="billing"\ndescription="Bills"\ndeveloper_instructions="private"\n[mcp_servers.ledger]\nurl="https://example.test"\n')
    result=reader.discover(project,home=home,runtime='codex')
    servers=[x for x in result['pieces'] if x['kind']=='mcp']
    assert len(servers)==1 and servers[0]['owner_agent']=='billing'
    assert servers[0]['locator']=='mcp_servers.ledger'
    assert 'example.test' not in json.dumps(result)


def test_declared_agent_tools_preserve_names_without_permission_claim(reader,locations):
    project,home=locations
    put(project,'.claude/agents/billing.md','---\nname: billing\ndescription: Bills\ntools: Read, Bash, mcp__ledger__read\n---\n')
    result=reader.discover(project,home=home,runtime='claude-code')
    assert result['pieces'][0]['declared_tools']==['Read','Bash','mcp__ledger__read']
    assert result['pieces'][0]['availability']=='unverified'


def test_console_control_characters_are_escaped_in_public_metadata(reader,locations):
    project,home=locations
    put(project,'opencode.json',json.dumps({'agent':{'bad\x1b[2J':{'description':'Bills\x00with controls'}}}))
    result=reader.discover(project,home=home,runtime='opencode')
    assert '\x1b' not in result['pieces'][0]['name']
    assert '\x00' not in result['pieces'][0]['description']


def test_shared_file_is_read_once_per_inventory_and_next_scan_refreshes(reader,locations,monkeypatch):
    project,home=locations
    path=put(project,'.claude/skills/billing/SKILL.md',markdown('billing'))
    original=reader.GUARD._read
    calls=[]
    def observed(filename,*args,**kwargs):
        if filename==path:
            calls.append(filename)
        return original(filename,*args,**kwargs)
    monkeypatch.setattr(reader.GUARD,'_read',observed)
    first=reader.discover(project,home=home)
    assert len(calls)==1
    path.write_bytes(markdown('billing','Changed').encode())
    second=reader.discover(project,home=home)
    assert len(calls)==2
    assert first['pieces'][0]['description']!=second['pieces'][0]['description']


def registry_row(path, origin='generada'):
    return {'nombre':'billing','forma':'agente','area':'billing','origen':origin,
            'creada':'2026-10-06','evidencia':[],
            'confirmaciones':{'tools':[],'arbol_plugin':None,'tope':None},
            'destinos':[{'runtime':'claude-code','ruta':'.claude/agents/billing.md',
                         'canonica':True,'hash':'sha256:'+hashlib.sha256(path.read_bytes().replace(b'\r\n',b'\n')).hexdigest()}]}


@pytest.mark.parametrize('change', ['missing-fields','bad-form','duplicate-name','missing-canonical','bad-confirmations'])
def test_registry_invalid_shape_cannot_claim_managed_state(reader,locations,change):
    project,home=locations
    path=put(project,'.claude/agents/billing.md',markdown('billing'))
    row=registry_row(path)
    if change=='missing-fields':
        del row['nombre']
    elif change=='bad-form':
        row['forma']={'unsafe':'value'}
    elif change=='missing-canonical':
        row['destinos'][0]['canonica']=False
    elif change=='bad-confirmations':
        row['confirmaciones']='not a record'
    rows=[row]
    if change=='duplicate-name':
        other=json.loads(json.dumps(row))
        other['destinos'][0]['ruta']='.codex/agents/billing.toml'
        other['destinos'][0]['runtime']='codex'
        rows.append(other)
    put(project,'.claude/pieces.json',json.dumps({'version':1,'hash_version':'sha256-lf-1','piezas':rows}))
    result=reader.discover(project,home=home,runtime='claude-code')
    assert result['registry_status']=='invalid' and result['partial']
    assert result['pieces'][0]['ownership']=='unknown'


def test_registry_missing_destination_is_reported_as_orphan(reader,locations):
    project,home=locations
    path=put(project,'.claude/agents/billing.md',markdown('billing'))
    row=registry_row(path)
    put(project,'.claude/pieces.json',json.dumps({'version':1,'hash_version':'sha256-lf-1','piezas':[row]}))
    path.unlink()
    result=reader.discover(project,home=home,runtime='claude-code')
    assert result['registry_status']=='valid'
    assert result['orphans']==[{'runtime':'claude-code','source':'project/.claude/agents/billing.md'}]
    assert result['warnings'] and result['partial']


def test_adopted_piece_remains_modified_without_generation_baseline(reader,locations):
    project,home=locations
    path=put(project,'.claude/agents/billing.md',markdown('billing'))
    put(project,'.claude/pieces.json',json.dumps({'version':1,'hash_version':'sha256-lf-1','piezas':[registry_row(path,'adoptada')]}))
    assert reader.discover(project,home=home,runtime='claude-code')['pieces'][0]['ownership']=='modified'


def test_cli_does_not_modify_project_or_user_configuration(locations):
    import subprocess
    import sys
    project,home=locations
    put(project,'.claude/agents/billing.md',markdown('billing'))
    put(home,'.claude.json',json.dumps({'mcpServers':{'local':{'command':'must-not-run'}}}))
    originals={p:p.read_bytes() for root in locations for p in root.rglob('*') if p.is_file()}
    result=subprocess.run([sys.executable,str(SCRIPT),'--project',str(project),'--home',str(home),'--runtime','claude-code','--json'],capture_output=True,encoding='utf-8',timeout=10)
    assert result.returncode==0 and json.loads(result.stdout)['pieces']
    assert originals=={p:p.read_bytes() for root in locations for p in root.rglob('*') if p.is_file()}
    assert 'must-not-run' not in result.stdout


def test_core_role_and_bundled_skill_collision_are_visible(reader, locations):
    project, home = locations
    put(project, '.claude/agents/implementer.md', markdown('implementer'))
    put(project, '.claude/skills/tdd/SKILL.md', markdown('tdd'))
    result = reader.discover(project, home=home, runtime='claude-code')
    conflicts = {c['name']: c for c in result['conflicts']}
    assert conflicts['implementer']['bundled_source'] == 'agents/implementer.md'
    assert conflicts['tdd']['bundled_source'] == 'skills/tdd/SKILL.md'
    assert all(c['resolution'] for c in conflicts.values())
    assert len(result['pieces']) == 2


def test_selection_uses_explicit_ids_and_rechecks_current_inventory(reader, locations):
    project, home = locations
    path = put(project, '.claude/agents/billing.md', markdown('billing'))
    put(project, '.codex/agents/tax.toml', 'name="tax"\ndescription="Tax"\ndeveloper_instructions="private"\n')
    before = reader.discover(project, home=home)
    ids = {p['name']: p['id'] for p in before['pieces']}
    selected = reader.select_pieces(before, [ids['billing'], ids['billing'], ids['tax']], runtime='claude-code')
    assert [p['name'] for p in selected['selected']] == ['billing']
    assert selected['selection_only'] and selected['partial']
    assert selected['selected'][0]['availability'] == 'unverified'
    path.unlink()
    after = reader.discover(project, home=home)
    stale = reader.select_pieces(after, [ids['billing']], runtime='claude-code')
    assert not stale['selected'] and stale['warnings']


def test_selecting_duplicate_names_keeps_sources_and_does_not_resolve_precedence(reader, locations):
    project, home = locations
    for base in locations:
        put(base, '.claude/agents/billing.md', markdown('billing'))
    result = reader.discover(project, home=home, runtime='claude-code')
    chosen = reader.select_pieces(result, [p['id'] for p in result['pieces']], runtime='claude-code')
    assert {p['scope'] for p in chosen['selected']} == {'project', 'user'}
    assert len(chosen['conflicts']) == 1 and chosen['warnings']
    assert all(p['availability'] == 'unverified' for p in chosen['selected'])


@pytest.mark.parametrize('ids', [['../private'], ['ext-' + 'a' * 20] * 21, 'billing'])
def test_invalid_or_excessive_selection_is_rejected(reader, locations, ids):
    with pytest.raises(ValueError):
        reader.select_pieces(reader.discover(locations[0], home=locations[1]), ids)


def test_distinct_custom_user_roots_have_distinct_ids_even_for_same_relative_source(reader, locations):
    project, home = locations
    ids = []
    for name in ('portable-a', 'portable-b'):
        root = home / name
        put(root, 'agents/billing.toml', 'name="billing"\ndescription="Bills"\ndeveloper_instructions="private"\n')
        result = reader.discover(project, home=home, runtime='codex', user_roots={'codex': root})
        ids.append(result['pieces'][0]['id'])
        assert str(root) not in json.dumps(result)
    assert len(set(ids)) == 2


def test_cli_explicit_selection_only_exports_chosen_references(locations):
    import subprocess
    import sys
    project, home = locations
    put(project, '.claude/agents/billing.md', markdown('billing'))
    args = [sys.executable, str(SCRIPT), '--project', str(project), '--home', str(home), '--runtime', 'claude-code', '--json']
    inventory = json.loads(subprocess.run(args, capture_output=True, encoding='utf-8', timeout=10).stdout)
    result = subprocess.run(args + ['--select', inventory['pieces'][0]['id']], capture_output=True, encoding='utf-8', timeout=10)
    assert result.returncode == 0
    chosen = json.loads(result.stdout)
    assert [p['name'] for p in chosen['selected']] == ['billing']
    assert 'PRIVATE BODY' not in result.stdout


def test_total_read_budget_reports_partial_inventory(reader, locations, monkeypatch):
    project, home = locations
    raw = markdown('billing')
    monkeypatch.setattr(reader, 'MAX_TOTAL_BYTES', len(raw.encode()) + 8)
    put(project, '.claude/agents/a.md', raw)
    put(project, '.claude/agents/b.md', markdown('other'))
    result = reader.discover(project, home=home, runtime='claude-code')
    assert len(result['pieces']) == 1 and result['partial'] and result['warnings']


def test_missing_bundled_dependencies_produces_clean_cli_failure(tmp_path):
    import shutil
    import subprocess
    import sys
    copy = tmp_path / 'project-pieces.py'
    shutil.copyfile(SCRIPT, copy)
    result = subprocess.run([sys.executable, str(copy), '--project', str(tmp_path), '--project-only', '--json'], capture_output=True, encoding='utf-8', timeout=10)
    assert result.returncode == 2 and 'Traceback' not in result.stderr
    assert not result.stdout and 'unavailable' in result.stderr


def test_opencode_markdown_tool_policy_is_declared_without_permission_claim(reader, locations):
    project, home = locations
    put(project, '.opencode/agents/billing.md', '---\ndescription: Billing\ntools:\n  write: false\n  bash: true\n---\nprivate\n')
    result = reader.discover(project, home=home, runtime='opencode')
    assert result['pieces'][0]['declared_tools'] == ['write', 'bash']
    assert result['pieces'][0]['availability'] == 'unverified'


@pytest.mark.parametrize('format', ['json', 'markdown'])
def test_opencode_permissions_expose_only_keys_and_actions_not_patterns(reader, locations, format):
    project, home = locations
    if format == 'json':
        put(project, 'opencode.json', json.dumps({'agent': {'billing': {'description': 'Billing', 'permission': {'edit': 'deny', 'bash': {'private-secret-pattern': 'ask'}}}}}))
    else:
        put(project, '.opencode/agents/billing.md', '---\ndescription: Billing\npermission:\n  edit: deny\n  bash:\n    "private-secret-pattern": ask\n---\nprivate\n')
    result = reader.discover(project, home=home, runtime='opencode')
    assert result['pieces'][0]['declared_permissions'] == {'edit': 'deny', 'bash': 'pattern-rules'}
    assert 'private-secret-pattern' not in json.dumps(result)
    assert result['pieces'][0]['availability'] == 'unverified' and not result['partial']


@pytest.mark.parametrize('inline', [False, True])
def test_claude_agent_scoped_mcp_preserves_reference_or_inline_kind(reader, locations, inline):
    project, home = locations
    value = ('  - ledger:\n      type: stdio\n      command: private-command\n      env:\n        TOKEN: private-token\n' if inline else '  - ledger\n')
    put(project, '.claude/agents/billing.md', '---\nname: billing\ndescription: Billing\nmcpServers:\n' + value + '---\nPrivate body\n')
    result = reader.discover(project, home=home, runtime='claude-code')
    server = next(piece for piece in result['pieces'] if piece['kind'] == 'mcp')
    assert server['name'] == 'ledger' and server['owner_agent'] == 'billing'
    assert server['declaration'] == ('inline' if inline else 'reference')
    assert server['availability'] == 'unverified'
    assert 'private-command' not in json.dumps(result) and 'private-token' not in json.dumps(result)


def test_rejected_oversized_reads_still_consume_the_global_budget(reader, locations, monkeypatch):
    project, home = locations
    monkeypatch.setattr(reader, 'MAX_BYTES', 64)
    monkeypatch.setattr(reader, 'MAX_TOTAL_BYTES', 70)
    for name in ('a', 'b', 'c'):
        put(project, '.claude/agents/' + name + '.md', 'x' * 100)
    observed = []
    original = reader.GUARD._read
    def bounded(path, *args, **kwargs):
        observed.append(kwargs['max_bytes'] + 1)
        return original(path, *args, **kwargs)
    monkeypatch.setattr(reader.GUARD, '_read', bounded)
    result = reader.discover(project, home=home, runtime='claude-code')
    assert result['partial'] and not result['pieces']
    assert sum(observed) <= 70


def test_valid_four_space_policy_indentation_is_supported(reader, locations):
    project, home = locations
    put(project, '.opencode/agents/billing.md', '---\ndescription: Billing\ntools:\n    bash: false\npermission:\n    edit: deny\n    bash:\n        "private-pattern": ask\n---\n')
    result = reader.discover(project, home=home, runtime='opencode')
    assert result['pieces'][0]['declared_tools'] == ['bash']
    assert result['pieces'][0]['declared_permissions'] == {'edit': 'deny', 'bash': 'pattern-rules'}
    assert not result['partial']


def test_duplicate_empty_agent_mcp_fields_warn_instead_of_being_silently_merged(reader, locations):
    project, home = locations
    put(project, '.claude/agents/billing.md', '---\nname: billing\ndescription: Billing\nmcpServers: []\nmodel: inherit\nmcpServers:\n  - ledger\n---\n')
    result = reader.discover(project, home=home, runtime='claude-code')
    assert result['partial']
    assert not [p for p in result['pieces'] if p['kind']=='mcp']


def test_absent_bundle_agent_is_not_reported_as_a_present_file_collision(reader, locations, tmp_path, monkeypatch):
    project, home = locations
    portable = tmp_path / 'portable'
    portable.mkdir()
    monkeypatch.setattr(reader.GUARD, 'BUNDLE', portable)
    put(project, '.claude/agents/implementer.md', markdown('implementer'))
    result = reader.discover(project, home=home, runtime='claude-code')
    assert not result['conflicts']


def test_permission_keys_are_redacted_before_export(reader, locations):
    project, home = locations
    secret = 'sk-ant-' + 'x' * 40
    put(project, 'opencode.json', json.dumps({'agent': {'billing': {'description': 'Bills', 'permission': {secret: 'deny'}}}}))
    result = reader.discover(project, home=home, runtime='opencode')
    assert secret not in json.dumps(result)
    assert '[secreto redactado]' in json.dumps(result)


@pytest.mark.parametrize('json_output', [False, True])
def test_main_emits_inventory_and_explicit_selection_in_both_formats(reader, locations, capsys, json_output):
    project, home = locations
    put(project, '.claude/agents/billing.md', markdown('billing', 'Facturación 🐛'))
    arguments = ['--project', str(project), '--home', str(home), '--runtime', 'claude-code', '--project-only']
    if json_output:
        arguments.append('--json')
    assert reader.main(arguments) == 0
    inventory = capsys.readouterr().out
    assert 'billing' in inventory and 'PRIVATE BODY' not in inventory
    identity = reader.discover(project, home=home, runtime='claude-code', include_user=False)['pieces'][0]['id']
    assert reader.main(arguments + ['--select', identity]) == 0
    chosen = capsys.readouterr().out
    assert identity in chosen
    if json_output:
        assert json.loads(chosen)['selected'][0]['description']=='Facturación 🐛'


@pytest.mark.parametrize('arguments', [['--user-root', 'unknown=x'], ['--user-root', 'codex=x', '--user-root', 'codex=y'], ['--user-root', 'codex'], ['--select', '../private']])
def test_bad_cli_selection_or_roots_return_diagnostic_without_traceback(reader, locations, capsys, arguments):
    assert reader.main(['--project', str(locations[0]), '--home', str(locations[1]), '--json'] + arguments) == 2
    output = capsys.readouterr()
    assert not output.out and 'unavailable' in output.err and 'Traceback' not in output.err


@pytest.mark.parametrize('change', ['version-bool', 'extra-header', 'invalid-date', 'bad-evidence', 'bad-confirmation', 'bad-origin', 'bad-hash', 'bad-path', 'duplicate-path', 'canonical-number'])
def test_registry_corruption_never_grants_ownership_or_leaks_values(reader, locations, change):
    project, home = locations
    path = put(project, '.claude/agents/billing.md', markdown('billing'))
    row = registry_row(path)
    data = {'version': 1, 'hash_version': 'sha256-lf-1', 'piezas': [row]}
    if change=='version-bool': data['version']=True
    elif change=='extra-header': data['private-field']='PRIVATE VALUE'
    elif change=='invalid-date': row['creada']='2026-13-31'
    elif change=='bad-evidence': row['evidencia']=[{'private':'PRIVATE VALUE'}]
    elif change=='bad-confirmation': row['confirmaciones']['tope']=False
    elif change=='bad-origin': row['origen']=['generada']
    elif change=='bad-hash': row['destinos'][0]['hash']='sha256:not-a-hash'
    elif change=='bad-path': row['destinos'][0]['ruta']='.claude/../private'
    elif change=='duplicate-path': row['destinos'].append(dict(row['destinos'][0], canonica=False))
    elif change=='canonical-number': row['destinos'][0]['canonica']=1
    put(project, '.claude/pieces.json', json.dumps(data))
    result = reader.discover(project, home=home, runtime='claude-code')
    assert result['registry_status']=='invalid' and result['pieces'][0]['ownership']=='unknown'
    assert 'PRIVATE VALUE' not in json.dumps(result)


@pytest.mark.parametrize('frontmatter', ['name: billing\ndescription: "Quoted bills"\ntools:\n  - Read\n  - Bash', "name: 'billing'\ndescription: 'It''s billing'\n", 'name: billing\ndescription: Billing\nmcpServers: [ledger, "reports"]\n'])
def test_supported_quoted_scalars_tool_lists_and_agent_mcp_references(reader, locations, frontmatter):
    project, home = locations
    put(project, '.claude/agents/billing.md', '---\n' + frontmatter + '\n---\nPRIVATE BODY\n')
    result = reader.discover(project, home=home, runtime='claude-code')
    assert not result['partial'] and any(p['name']=='billing' for p in result['pieces'])
    assert 'PRIVATE BODY' not in json.dumps(result)


@pytest.mark.parametrize('raw', ['{/* comment */"agent":{"billing":{"description":"Bills"}},}', '{/* unclosed', '{"agent":{"billing":{"description":"Escaped \\\"quote\\\""}}}'])
def test_jsonc_comments_and_escaped_strings_preserve_data_or_report_partial(reader, locations, raw):
    project, home = locations
    put(project, 'opencode.jsonc', raw)
    result = reader.discover(project, home=home, runtime='opencode')
    if raw=='{/* unclosed':
        assert result['partial'] and not result['pieces']
    else:
        assert not result['partial'] and result['pieces'][0]['name']=='billing'


def test_claude_disabled_state_comes_from_selected_project_preferences_not_enabled_field(reader, locations):
    project, home = locations
    put(project, '.mcp.json', json.dumps({'mcpServers': {'ledger': {'type': 'http', 'url': 'https://example.test', 'enabled': True}}}))
    put(home, '.claude.json', json.dumps({'projects': {str(project): {'disabledMcpServers': ['ledger']}, str(home / 'other'): {'disabledMcpServers': ['other']}}}))
    result = reader.discover(project, home=home, runtime='claude-code')
    server = next(p for p in result['pieces'] if p['kind']=='mcp')
    assert server['enabled'] is False and server['enabled_source'].endswith('disabledMcpServers')
    assert server['availability']=='unverified'
    assert reader.discover(project, home=home, runtime='claude-code', include_user=False)['pieces'][0]['enabled'] is None


@pytest.mark.parametrize('transport,expected', [('ws','ws'), ('streamable-http','http')])
def test_claude_native_mcp_transports_are_recognized_without_opening_urls(reader, locations, transport, expected):
    project, home = locations
    put(project, '.mcp.json', json.dumps({'mcpServers': {'ledger': {'type': transport, 'url': 'https://example.test/private'}}}))
    result = reader.discover(project, home=home, runtime='claude-code')
    assert result['pieces'][0]['transport']==expected and not result['partial']
    assert 'example.test' not in json.dumps(result)


def test_claude_url_without_type_is_invalid_rather_than_inferred_http(reader, locations):
    project, home = locations
    put(project, '.mcp.json', json.dumps({'mcpServers': {'ledger': {'url': 'https://example.test/private'}}}))
    result = reader.discover(project, home=home, runtime='claude-code')
    assert result['pieces'][0]['transport']=='unknown' and result['partial']
    assert result['pieces'][0]['definition_status']=='invalid'


@pytest.mark.parametrize('server', [{'type': 'sdk'}, {'type': 'stdio'}, {'type': 'http'}, {'type': 'custom', 'command': 'private-command'}])
def test_invalid_claude_server_keeps_identity_without_claiming_a_valid_definition(reader, locations, server):
    project, home = locations
    put(project, '.mcp.json', json.dumps({'mcpServers': {'ledger': server}}))
    result = reader.discover(project, home=home, runtime='claude-code')
    assert result['partial'] and result['pieces'][0]['definition_status']=='invalid'
    assert result['pieces'][0]['transport']=='unknown'
    assert result['pieces'][0]['availability']=='unverified'


@pytest.mark.parametrize('disabled', ['ledger', [False], ['ledger', {}]])
def test_invalid_claude_disable_preferences_do_not_assign_an_enabled_state(reader, locations, disabled):
    project, home = locations
    put(project, '.mcp.json', json.dumps({'mcpServers': {'ledger': {'command': 'private-command'}}}))
    put(home, '.claude.json', json.dumps({'projects': {str(project): {'disabledMcpServers': disabled}}}))
    result = reader.discover(project, home=home, runtime='claude-code')
    assert result['partial'] and result['pieces'][0]['enabled'] is None


@pytest.mark.parametrize('indent', [2, 4])
def test_agent_mcp_nested_private_lists_are_not_server_identities(reader, locations, indent):
    project, home = locations
    pad = ' ' * indent
    child = pad + ' ' * 4
    raw = ('---\nname: billing\ndescription: Bills\nmcpServers:\n' + pad + '- ledger:\n'
           + child + 'command: private-command\n' + child + 'args:\n'
           + child + '  - private-customer-argument\n' + child + '  - private-credential-value\n'
           + pad + '- reports\n---\nPRIVATE BODY\n')
    put(project, '.claude/agents/billing.md', raw)
    result = reader.discover(project, home=home, runtime='claude-code')
    assert {p['name'] for p in result['pieces'] if p['kind']=='mcp'} == {'ledger', 'reports'}
    assert not result['partial']
    assert 'private-customer-argument' not in json.dumps(result)
    assert 'private-credential-value' not in json.dumps(result)


@pytest.mark.parametrize('relative,raw,name', [
    ('.claude/skills/no-name/SKILL.md', '---\ndescription: Declared guide\n---\nPRIVATE BODY\n', 'no-name'),
    ('.claude/skills/no-header/SKILL.md', 'PRIVATE BODY WITHOUT FRONTMATTER\n', 'no-header'),
    ('.claude/commands/no-header.md', 'PRIVATE BODY WITHOUT FRONTMATTER\n', 'no-header'),
])
def test_native_claude_optional_skill_and_command_metadata_preserves_sources(reader, locations, relative, raw, name):
    project, home = locations
    put(project, relative, raw)
    result = reader.discover(project, home=home, runtime='claude-code')
    assert not result['partial'] and result['pieces'][0]['name']==name
    assert result['pieces'][0]['source']=='project/' + relative
    assert 'PRIVATE BODY' not in json.dumps(result)


def test_claude_command_and_skill_share_invocation_conflicts(reader, locations):
    project, home = locations
    put(project, '.claude/commands/deploy.md', markdown('deploy'))
    put(project, '.claude/skills/deploy/SKILL.md', markdown('deploy'))
    result = reader.discover(project, home=home, runtime='claude-code')
    assert len(result['conflicts'])==1
    assert set(result['conflicts'][0]['ids'])=={p['id'] for p in result['pieces']}


@pytest.mark.parametrize('relative,name,bundled', [
    ('.claude/commands/tdd.md', 'tdd', 'skills/tdd/SKILL.md'),
    ('.claude/skills/dev-cycle/SKILL.md', 'dev-cycle', 'commands/dev-cycle.md'),
])
def test_claude_cross_kind_bundle_invocation_conflict(reader, locations, relative, name, bundled):
    project, home = locations
    put(project, relative, markdown(name))
    result = reader.discover(project, home=home, runtime='claude-code')
    assert result['conflicts'][0]['bundled_source']==bundled


def test_oversized_directory_never_exports_an_order_dependent_subset(reader, locations, monkeypatch):
    project, home = locations
    directory = project / '.claude/agents'
    paths = [put(project, f'.claude/agents/piece-{i}.md', markdown(f'piece-{i}')) for i in range(3)]
    put(project, '.claude/skills/kept/SKILL.md', markdown('kept'))
    monkeypatch.setattr(reader, 'MAX_PIECES', 2)
    original = Path.iterdir
    monkeypatch.setattr(Path, 'iterdir', lambda path: iter(paths) if path==directory else original(path))
    forward = reader.discover(project, home=home, runtime='claude-code')
    monkeypatch.setattr(Path, 'iterdir', lambda path: iter(reversed(paths)) if path==directory else original(path))
    backward = reader.discover(project, home=home, runtime='claude-code')
    assert forward==backward
    assert forward['partial'] and [p['name'] for p in forward['pieces']]==['kept']


def test_multiline_metadata_within_read_budget_finishes_before_panel_timeout(locations):
    import subprocess
    import sys
    project, home = locations
    for i in range(16):
        raw = f'---\nname: heavy-{i}\ndescription: |\n' + ' x\n' * 174660 + '---\n'
        assert len(raw.encode('utf-8')) < 512 * 1024
        put(project, f'.claude/agents/heavy-{i}.md', raw)
    result = subprocess.run([sys.executable, str(SCRIPT), '--project', str(project), '--home', str(home), '--project-only', '--runtime', 'claude-code', '--json'], capture_output=True, encoding='utf-8', timeout=15)
    inventory = json.loads(result.stdout)
    assert result.returncode==0 and not inventory['partial'] and len(inventory['pieces'])==16
    assert all(len(piece['description'])==480 for piece in inventory['pieces'])


@pytest.mark.parametrize('runtime,relative,kind', [
    ('claude-code', '.claude/commands/tdd.md', 'command'),
    ('opencode', '.opencode/commands/tdd.md', 'command'),
    ('opencode', '.opencode/agents/tdd.md', 'agent'),
])
def test_native_file_named_components_ignore_frontmatter_name(reader, locations, runtime, relative, kind):
    project, home = locations
    put(project, relative, markdown('misleading'))
    result = reader.discover(project, home=home, runtime=runtime)
    piece = next(p for p in result['pieces'] if p['kind']==kind)
    assert piece['name']=='tdd'
    if runtime=='claude-code':
        assert result['conflicts'][0]['bundled_source']=='skills/tdd/SKILL.md'


def test_claude_skill_directory_alias_participates_in_invocation_conflicts(reader, locations):
    project, home = locations
    put(project, '.claude/commands/tdd.md', markdown('misleading-command'))
    put(project, '.claude/skills/tdd/SKILL.md', markdown('special-guidance'))
    result = reader.discover(project, home=home, runtime='claude-code')
    skill = next(p for p in result['pieces'] if p['kind']=='skill')
    assert set(skill['invocation_names'])=={'special-guidance', 'tdd'}
    conflict = next(c for c in result['conflicts'] if c['name']=='tdd' and 'bundled_source' not in c)
    assert set(conflict['ids'])=={p['id'] for p in result['pieces']}
