"""Stable project scope and verified generation pointers never select another project."""
import copy,hashlib,importlib.util,json
from pathlib import Path
import pytest
import contextlib
HERE=Path(__file__).resolve().parent
def load():
    spec=importlib.util.spec_from_file_location('scope58',HERE.parent/'backends/graphiti_scope.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
def publication():
    spec=importlib.util.spec_from_file_location('pub58',HERE.parent/'backends/graphiti_publication.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
def adapter():
    spec=importlib.util.spec_from_file_location('adapter58',HERE.parent/'backends/graphiti.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
def peer_module():
    spec=importlib.util.spec_from_file_location('scope_peer58',HERE/'test_graphiti_transitions.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
def inventory(root):return {p.relative_to(root).as_posix():None if p.is_dir() else hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*')}

def test_generation_name_is_stable_project_bound_and_sdk_safe():
    mod=load();nonce='a'*32
    group=mod.generation_group('proyecto-ámbito',nonce)
    assert group==mod.generation_group('proyecto-ámbito',nonce)
    assert group!=mod.generation_group('otro-proyecto',nonce)
    assert group.isascii() and all(c.isalnum() or c=='_' for c in group)

@pytest.mark.parametrize('nonce',['',False,'A'*32,'0'*31,'0'*33,'../escape'])
def test_invalid_generation_nonce_is_rejected(nonce):
    mod=load()
    with pytest.raises(mod.ScopeError):mod.generation_group('project',nonce)

def test_legacy_scope_is_preserved_without_mutating_inputs():
    mod=load();cfg={'group_id':'project','provider':{'llm':'none'}};before=copy.deepcopy(cfg)
    result=mod.resolve_config(cfg,{'group_id':'project','entradas':{}})
    assert result['group_id']=='project' and result['_logical_group_id']=='project' and cfg==before

def test_committed_generation_resolves_to_its_own_physical_group():
    mod=load();physical=mod.generation_group('project','a'*32)
    result=mod.resolve_config({'group_id':'project'},{'group_id':physical,'logical_group_id':'project','entradas':{}})
    assert result['group_id']==physical and result['_logical_group_id']=='project'

def test_generation_from_another_project_is_rejected():
    mod=load();foreign=mod.generation_group('other','a'*32)
    with pytest.raises(mod.ScopeError):mod.resolve_config({'group_id':'project'},{'group_id':foreign,'logical_group_id':'project'})

def test_changed_project_configuration_does_not_adopt_previous_generation():
    mod=load();old=mod.generation_group('old','a'*32)
    result=mod.resolve_config({'group_id':'new'},{'group_id':old,'logical_group_id':'old'})
    assert result['group_id']=='new' and result['_logical_group_id']=='new'

def test_scope_read_is_local_and_does_not_create_state(tmp_path):
    mod=load();pub=publication();cfg={'_root':str(tmp_path),'group_id':'project','endpoint':'http://127.0.0.1:8001/mcp'}
    before=inventory(tmp_path);result=mod.read_config(cfg,pub)
    assert result['group_id']=='project' and inventory(tmp_path)==before

def test_pending_generation_never_becomes_active_by_reading(tmp_path):
    mod=load();pub=publication();cfg={'_root':str(tmp_path),'group_id':'project','endpoint':'http://127.0.0.1:8001/mcp'}
    folder=tmp_path/'.claude/knowledge-services';folder.mkdir(parents=True)
    physical=mod.generation_group('project','a'*32)
    (folder/'graphiti-manifest.pending.json').write_text(json.dumps({'group_id':physical,'logical_group_id':'project','entradas':{}}),encoding='utf8')
    before=inventory(tmp_path);result=mod.read_config(cfg,pub)
    assert result['group_id']=='project' and inventory(tmp_path)==before

def test_published_generation_pointer_is_read_without_mutation(tmp_path):
    mod=load();pub=publication();cfg={'_root':str(tmp_path),'group_id':'project','endpoint':'http://127.0.0.1:8001/mcp'}
    folder=tmp_path/'.claude/knowledge-services';folder.mkdir(parents=True)
    physical=mod.generation_group('project','a'*32)
    (folder/'graphiti-manifest.json').write_text(json.dumps({'group_id':physical,'logical_group_id':'project','entradas':{}}),encoding='utf8')
    before=inventory(tmp_path);assert mod.read_config(cfg,pub)['group_id']==physical
    assert inventory(tmp_path)==before

def test_duplicate_descriptor_fields_are_not_scope_authority(tmp_path):
    mod=load();pub=publication();cfg={'_root':str(tmp_path),'group_id':'project','endpoint':'http://127.0.0.1:8001/mcp'}
    folder=tmp_path/'.claude/knowledge-services';folder.mkdir(parents=True)
    (folder/'graphiti-manifest.json').write_text('{"group_id":"project","group_id":"other","logical_group_id":"project"}',encoding='utf8')
    before=inventory(tmp_path)
    with pytest.raises(mod.ScopeError):mod.read_config(cfg,pub)
    assert inventory(tmp_path)==before


def test_partial_published_descriptor_is_not_an_active_generation():
    mod=load();physical=mod.generation_group('project','a'*32)
    with pytest.raises(mod.ScopeError):mod.resolve_config({'group_id':'project'},{'group_id':physical,'logical_group_id':'project'})


def test_false_exists_result_does_not_hide_an_unsafe_scope_component(tmp_path,monkeypatch):
    mod=load();pub=publication();cfg={'_root':str(tmp_path),'group_id':'project','endpoint':'http://127.0.0.1:8001/mcp'}
    (tmp_path/'.claude').write_text('Owned non-directory fixture',encoding='utf8')
    monkeypatch.setattr(mod.Path,'exists',lambda self:False)
    with pytest.raises(mod.ScopeError):mod.read_config(cfg,pub)


def setup_adapter(tmp_path,monkeypatch):
    scope=load();mod=adapter();base=peer_module();peer=base.Peer(mod)
    monkeypatch.setattr(mod,'ClienteMCP',lambda *a,**k:peer)
    cfg={'_root':str(tmp_path),'group_id':'project','endpoint':'http://127.0.0.1:8001/mcp',
         'provider':{'llm':'none'},'mode':'shadow','timeout_ms':1000}
    physical=scope.generation_group('project','a'*32)
    mod._escribir_manifest(cfg,{'group_id':physical,'logical_group_id':'project','entradas':{},'transitions':{}})
    return scope,mod,peer,cfg,physical,base.base.item()


def test_public_operations_use_the_committed_generation(tmp_path,monkeypatch):
    scope,mod,peer,cfg,physical,item=setup_adapter(tmp_path,monkeypatch)
    ops=mod.plan([item],cfg);assert ops[0]['group_id']==physical
    assert mod.apply(ops,cfg)['aplicados']==1
    value=json.loads((tmp_path/'.claude/knowledge-services/graphiti-manifest.json').read_bytes())
    assert value['group_id']==physical and value['logical_group_id']=='project'
    assert cfg['group_id']=='project' and mod.verify(cfg)['ok'] is True
    assert mod.revoke(item['id'],cfg)['revocado'] is True
    assert all(args.get('group_id',physical)==physical for name,args in peer.requests if name=='add_memory')
    assert all(args['group_ids']==[physical] for name,args in peer.requests if name=='get_episodes')


def test_corrupt_scope_keeps_public_read_and_write_gates_closed(tmp_path,monkeypatch):
    scope,mod,peer,cfg,physical,item=setup_adapter(tmp_path,monkeypatch)
    mod._escribir_manifest(cfg,{'group_id':scope.generation_group('foreign','a'*32),'logical_group_id':'project','entradas':{}})
    before=inventory(tmp_path)
    with pytest.raises(mod.ErrorMCP):mod.plan([item],cfg)
    assert mod.verify(cfg)['ok'] is False and mod.puede_leer(cfg)['puede'] is False
    assert mod.health(cfg)['estado']=='degradado'
    assert mod.consultar(cfg,{'texto':'Lyra'})['aciertos']==[]
    assert inventory(tmp_path)==before and not peer.requests


def test_changed_generation_after_scope_read_never_archives_or_resurrects_it(tmp_path,monkeypatch):
    scope,mod,peer,cfg,physical,item=setup_adapter(tmp_path,monkeypatch)
    ops=mod.plan([item],cfg);next_group=scope.generation_group('project','b'*32)
    original=mod._gpub.session
    @contextlib.contextmanager
    def swapped(c):
        with original(c) as session:
            value={'group_id':next_group,'logical_group_id':'project','entradas':{},'transitions':{}}
            mod._escribir_manifest(c,value)
            yield session
    monkeypatch.setattr(mod._gpub,'session',swapped)
    with pytest.raises(mod.ErrorMCP):mod.apply(ops,cfg)
    value=json.loads((tmp_path/'.claude/knowledge-services/graphiti-manifest.json').read_bytes())
    assert value['group_id']==next_group and not peer.requests
    assert not list((tmp_path/'.claude/knowledge-services').glob('*.archivado*'))


def test_shared_helper_import_reuse_does_not_cache_generation_metadata(tmp_path):
    mod=load();pub=publication();cfg={'_root':str(tmp_path),'group_id':'project','endpoint':'http://127.0.0.1:8001/mcp'}
    assert pub._helper('local-read') is pub._helper('local-read')
    folder=tmp_path/'.claude/knowledge-services';folder.mkdir(parents=True)
    path=folder/'graphiti-manifest.json'
    first=mod.generation_group('project','a'*32);second=mod.generation_group('project','b'*32)
    path.write_text(json.dumps({'group_id':first,'logical_group_id':'project','entradas':{}}),encoding='utf8')
    assert mod.read_config(cfg,pub)['group_id']==first
    path.write_text(json.dumps({'group_id':second,'logical_group_id':'project','entradas':{}}),encoding='utf8')
    assert mod.read_config(cfg,pub)['group_id']==second
