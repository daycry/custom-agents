"""A shared port must not become a cross-project data reader."""
import importlib.util
import json
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/'skills/plugin-panel/scripts/console_workspaces.py'

def api():
    assert PATH.is_file(), 'workspace registry is not implemented'
    spec=importlib.util.spec_from_file_location('tested_console_workspaces',PATH)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

def registry(tmp_path,workspaces):
    p=tmp_path/'workspaces.json'
    p.write_text(json.dumps({'version':1,'workspaces':workspaces}),encoding='utf-8')
    return p

def row(root,ident='portal'):
    return {'id':ident,'name':ident.title(),'root':str(root),'runtimes':['codex']}

def test_one_registry_contains_independent_workspaces_without_exposing_paths(tmp_path):
    first=tmp_path/'first';second=tmp_path/'second';first.mkdir();second.mkdir()
    result=api().load_workspaces(registry(tmp_path,[row(first),row(second,'billing')]))
    assert set(result)=={'portal','billing'}
    assert result['portal'].root==first.resolve()
    public=json.dumps([w.public() for w in result.values()])
    assert str(first) not in public and str(second) not in public
    assert [w.public()['id'] for w in result.values()]==['portal','billing']

@pytest.mark.parametrize('defect',['id','duplicate','same-root','unknown-runtime','extra','missing-root','relative'])
def test_invalid_registry_cannot_expand_its_scope(tmp_path,defect):
    root=tmp_path/'project';root.mkdir();rows=[row(root)]
    if defect=='id':rows[0]['id']='../private'
    elif defect=='duplicate':rows.append(row(root,'portal'))
    elif defect=='same-root':rows.append(row(root,'other'))
    elif defect=='unknown-runtime':rows[0]['runtimes']=['sh']
    elif defect=='extra':rows[0]['shell']='echo run'
    elif defect=='missing-root':rows[0]['root']=str(root/'missing')
    elif defect=='relative':rows[0]['root']='project'
    with pytest.raises(ValueError):api().load_workspaces(registry(tmp_path,rows))

def test_linked_registry_and_project_are_rejected(tmp_path):
    root=tmp_path/'project';root.mkdir();p=registry(tmp_path,[row(root)])
    linked=tmp_path/'link.json'
    try:linked.symlink_to(p)
    except OSError:pytest.skip('symlink unavailable')
    with pytest.raises(ValueError):api().load_workspaces(linked)

def test_duplicate_json_keys_and_oversized_config_fail_closed(tmp_path):
    p=tmp_path/'workspaces.json';p.write_text('{"version":1,"version":2,"workspaces":[]}')
    with pytest.raises(ValueError):api().load_workspaces(p)
    p.write_bytes(b' '*65537)
    with pytest.raises(ValueError):api().load_workspaces(p)


def test_replacing_a_registered_root_cannot_reuse_its_authority(tmp_path):
    root=tmp_path/'project';root.mkdir()
    workspace=api().load_workspaces(registry(tmp_path,[row(root)]))['portal']
    root.rename(tmp_path/'original')
    root.mkdir()
    with pytest.raises(ValueError):workspace.validate()

def test_direct_workspace_constructor_canonicalizes_the_registered_root(tmp_path):
    root=tmp_path/'project';root.mkdir()
    workspace=api().Workspace('portal','Portal',root/'..'/'project',('codex',))
    workspace.validate()
    assert workspace.root==root.resolve()
