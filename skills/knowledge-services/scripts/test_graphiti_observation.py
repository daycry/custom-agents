"""Read-only pending-state observation precedes cached external-read permissions."""
import hashlib,importlib.util,json
from pathlib import Path
import pytest
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('publication_fixture',HERE/'test_graphiti_publication.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
def inventory(root):
    return {p.relative_to(root).as_posix():None if p.is_dir() else hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*')}
def pending(tmp_path,monkeypatch):
    mod,peer,cfg=base.fixture(tmp_path,monkeypatch);cfg['mode']='read'
    mod._escribir_manifest(cfg, {'group_id':cfg['group_id'],'entradas':{},'transitions':{}})
    with pytest.raises(mod.ErrorMCP):base.submit(mod,cfg)
    with pytest.raises(mod.ErrorMCP):mod.apply(mod.plan([],cfg),cfg)
    monkeypatch.setattr(mod,'health',lambda cfg:{'estado':'sano'})
    return mod,peer,cfg
def state_file(root):
    return next(p for p in (root/'.claude/knowledge-services/graphiti-submissions').glob('*.json') if p.name!='_owner.json')

def test_retired_unconfirmed_submission_keeps_verify_and_reads_closed(tmp_path,monkeypatch):
    mod,peer,cfg=pending(tmp_path,monkeypatch);before=inventory(tmp_path)
    verified=mod.verify(cfg)
    assert verified['ok'] is not True,'Empty published manifest hid an unresolved external submission.'
    assert verified.get('razon')=='submissions_pending'
    assert mod.puede_leer(cfg)['puede'] is False
    assert mod.consultar(cfg,{'texto':'Lyra'})['aciertos']==[]
    assert inventory(tmp_path)==before,'Observing pending state mutated local files or directories.'
    assert not any(name.startswith('search_') for name,args in peer.requests)

def test_external_writer_invalidates_effect_of_cached_read_permission(tmp_path,monkeypatch):
    reader,peer,cfg=base.fixture(tmp_path,monkeypatch);cfg['mode']='read'
    monkeypatch.setattr(reader,'health',lambda cfg:{'estado':'sano'})
    assert reader.puede_leer(cfg)['puede'] is True
    writer=base.load();monkeypatch.setattr(writer,'ClienteMCP',lambda *a,**k:peer)
    with pytest.raises(writer.ErrorMCP):base.submit(writer,cfg)
    with pytest.raises(writer.ErrorMCP):writer.apply(writer.plan([],cfg),cfg)
    before=inventory(tmp_path)
    assert reader.puede_leer(cfg)['puede'] is False,'Cached success ignored another writer pending receipt.'
    assert inventory(tmp_path)==before

@pytest.mark.parametrize('corruption',['boolean-marker','duplicate-json-key','invalid-operation'])
def test_corrupt_receipts_are_visible_and_never_treated_as_no_pending(tmp_path,monkeypatch,corruption):
    mod,peer,cfg=pending(tmp_path,monkeypatch)
    file=state_file(tmp_path)
    if corruption=='boolean-marker':
        marker=file.parent/'_owner.json';value=json.loads(marker.read_bytes());value['schema']=True;marker.write_text(json.dumps(value),encoding='utf8')
    elif corruption=='duplicate-json-key':
        raw=file.read_text(encoding='utf8');file.write_text('{"operations":{},'+raw[1:],encoding='utf8')
    else:
        value=json.loads(file.read_bytes());next(iter(value['operations'].values()))['phase']='invented';file.write_text(json.dumps(value),encoding='utf8')
    before=inventory(tmp_path);verified=mod.verify(cfg)
    assert verified['ok'] is not True and verified['estado']=='no_verificable'
    assert mod.puede_leer(cfg)['puede'] is False
    assert inventory(tmp_path)==before and not any(name.startswith('search_') for name,args in peer.requests)

def test_endpoint_change_cannot_bypass_unknown_submission_identity(tmp_path,monkeypatch):
    mod,peer,cfg=pending(tmp_path,monkeypatch);before=inventory(tmp_path)
    cfg['endpoint']='http://localhost:8001/mcp'
    with pytest.raises(mod.ErrorMCP):base.submit(mod,cfg)
    assert len(peer.queued)==1,'Changing endpoint spelling bypassed the unresolved operation identity.'
    assert inventory(tmp_path)==before

def test_absent_receipts_are_observed_without_creating_state(tmp_path,monkeypatch):
    mod,peer,cfg=base.fixture(tmp_path,monkeypatch);cfg['mode']='read'
    monkeypatch.setattr(mod,'health',lambda cfg:{'estado':'sano'})
    before=inventory(tmp_path)
    assert mod.verify(cfg)['ok'] is True
    assert mod.puede_leer(cfg)['puede'] is True
    assert inventory(tmp_path)==before


def test_confirmed_receipt_without_published_commit_remains_closed(tmp_path,monkeypatch):
    mod,peer,cfg=base.fixture(tmp_path,monkeypatch);cfg['mode']='read'
    original_call=peer.tools_call
    def immediate(name,args):
        result=original_call(name,args)
        if name=='add_memory':peer.complete()
        return result
    peer.tools_call=immediate
    original_write=mod._escribir_manifest
    def cut(c,value,sufijo=''):
        if base.item()['id'] in value['entradas']:raise OSError('Owned interruption after confirmed remote receipt')
        return original_write(c,value,sufijo)
    with monkeypatch.context() as patch:
        patch.setattr(mod,'_escribir_manifest',cut)
        with pytest.raises(Exception):base.submit(mod,cfg)
    # Isolate read authorization for a confirmed receipt whose publication never committed.
    # Recovering a removed submission is now a separate mutating workflow.
    mod._escribir_manifest(cfg, {'group_id':cfg['group_id'],'entradas':{},'transitions':{}})
    before=inventory(tmp_path);verified=mod.verify(cfg)
    assert verified['ok'] is not True,'A confirmed receipt was mistaken for a published canonical binding.'
    assert inventory(tmp_path)==before

@pytest.mark.parametrize('changed',['uuid','content','group_id'])
def test_verified_publication_requires_its_exact_remote_binding(tmp_path,monkeypatch,changed):
    mod,peer,cfg=base.fixture(tmp_path,monkeypatch)
    with pytest.raises(mod.ErrorMCP):base.submit(mod,cfg)
    peer.complete();assert base.submit(mod,cfg)['aplicados']==1
    if changed=='uuid':peer.remote[0]['uuid']='47997018-89f7-486d-b86f-bacfcceafce1'
    elif changed=='content':peer.remote[0]['content']='Replacement content under the original name and UUID.'
    else:peer.remote[0].pop('group_id')
    before=inventory(tmp_path);verified=mod.verify(cfg)
    assert verified['ok'] is not True,'Verify accepted an episode name without its exact confirmed UUID/group/body binding.'
    assert inventory(tmp_path)==before
