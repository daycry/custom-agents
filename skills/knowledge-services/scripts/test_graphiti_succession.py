"""Recover stored succession intent without losing or replaying the remote event."""
import copy,importlib.util,hashlib,json,os,types
from pathlib import Path
import pytest
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('succession_base',HERE/'test_graphiti_transitions.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)

def fixture(tmp_path,monkeypatch,complete=True):
    mod,peer,cfg,first=base.fixture(tmp_path,monkeypatch);cfg.pop('transition_relations')
    second=base.next_version(first);peer.delay_markers=True
    with pytest.raises(mod.ErrorMCP):mod.apply(mod.plan([second],cfg),cfg)
    marker=next(args for args in peer.queued if args['name'].endswith('@superseded'))
    if complete:peer.persist(marker);peer.delay_markers=False
    return mod,peer,cfg,first,second

def inventory(root):return {p.relative_to(root).as_posix():None if p.is_dir() else hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*')}

def test_abandoned_succession_has_read_only_ordered_recovery_plan(tmp_path,monkeypatch):
    mod,peer,cfg,first,second=fixture(tmp_path,monkeypatch);before=inventory(tmp_path);requests=len(peer.requests)
    ops=mod.plan([],cfg)
    assert [op['tipo'] for op in ops]==['recover_transition','retire_submission','revoke']
    assert ops[0]['submission_name']==first['id']+'@1@superseded'
    assert inventory(tmp_path)==before and len(peer.requests)==requests

def test_abandoned_succession_commits_history_and_retires_v2_without_resends(tmp_path,monkeypatch):
    mod,peer,cfg,first,second=fixture(tmp_path,monkeypatch)
    result=mod.apply(mod.plan([],cfg),cfg);value=base.public(tmp_path)
    assert result['transiciones_recuperadas']==1 and result['retirados_pendientes']==1
    assert value['entradas']=={} and set(value['transitions'])=={first['id']+'@1@superseded',first['id']+'@2@withdrawn'}
    assert value['transitions'][first['id']+'@1@superseded']['retired_episode']['name']==first['id']+'@1'
    assert len(peer.queued)==4
    state=mod._gpub.observe(cfg);assert state['unconfirmed']==state['uncommitted']==0
    assert mod.verify(cfg)['ok'] is True

def test_kept_new_version_reuses_confirmed_succession_and_data(tmp_path,monkeypatch):
    mod,peer,cfg,first,second=fixture(tmp_path,monkeypatch)
    result=mod.apply(mod.plan([second],cfg),cfg)
    assert result['aplicados']==1 and result['transiciones_recuperadas']==1
    value=base.public(tmp_path);assert value['entradas'][first['id']]['version']==2
    assert set(value['transitions'])=={first['id']+'@1@superseded'} and len(peer.queued)==3
    assert mod._gpub.observe(cfg)['uncommitted']==0

def test_unconfirmed_succession_defers_dependent_mutations(tmp_path,monkeypatch):
    mod,peer,cfg,first,second=fixture(tmp_path,monkeypatch,complete=False);before=base.public(tmp_path);requests=len(peer.requests)
    with pytest.raises(mod.ErrorMCP):mod.apply(mod.plan([],cfg),cfg)
    assert base.public(tmp_path)==before and len(peer.queued)==3
    assert not any(name in ('add_memory','add_triplet') for name,args in peer.requests[requests:])

def test_changed_remote_marker_cannot_be_adopted(tmp_path,monkeypatch):
    mod,peer,cfg,first,second=fixture(tmp_path,monkeypatch);before=base.public(tmp_path)
    next(value for value in peer.remote if value['name'].endswith('@superseded'))['content']='Changed remote history.'
    with pytest.raises(mod.ErrorMCP):mod.apply(mod.plan([],cfg),cfg)
    assert base.public(tmp_path)==before and len(peer.queued)==3

def test_lost_relation_ack_recovers_same_edge_before_abandoned_version_withdrawal(tmp_path,monkeypatch):
    mod,peer,cfg,first=base.fixture(tmp_path,monkeypatch);second=base.next_version(first);peer.lose_link_ack=True
    with pytest.raises(mod.ErrorMCP):mod.apply(mod.plan([second],cfg),cfg)
    assert len(peer.edges)==1;old_edge=peer.edges[0]['uuid'];peer.lose_link_ack=False
    result=mod.apply(mod.plan([],cfg),cfg);value=base.public(tmp_path)
    assert result['transiciones_recuperadas']==1 and value['entradas']=={}
    assert value['transitions'][first['id']+'@1@superseded']['edge_uuid']==old_edge
    assert len(peer.edges)==2 and len([name for name,args in peer.requests if name=='add_triplet'])==2
    assert mod._gpub.observe(cfg)['unconfirmed']==0

def test_same_version_cannot_undo_a_recovered_succession(tmp_path,monkeypatch):
    mod,peer,cfg,first,second=fixture(tmp_path,monkeypatch)
    result=mod.apply(mod.plan([first],cfg),cfg)
    assert result['transiciones_recuperadas']==1
    assert base.public(tmp_path)['entradas']=={}
    assert first['id']+'@1@superseded' in base.public(tmp_path)['transitions']
    assert mod.apply(mod.plan([first],cfg),cfg)['omitidos_obsoletos']==1

def test_recovery_after_commit_cut_prunes_only_exact_marker_binding(tmp_path,monkeypatch):
    mod,peer,cfg,first,second=fixture(tmp_path,monkeypatch);original=mod._escribir_manifest
    def cut(c,value,sufijo=''):
        if not sufijo and value.get('transitions'):raise OSError('Owned recovered history commit cut')
        return original(c,value,sufijo)
    with monkeypatch.context() as patch:
        patch.setattr(mod,'_escribir_manifest',cut)
        with pytest.raises(OSError):mod.apply(mod.plan([],cfg),cfg)
    assert mod._gpub.observe(cfg)['uncommitted']>0
    mod.apply(mod.plan([],cfg),cfg)
    assert len(peer.queued)==4 and mod._gpub.observe(cfg)['uncommitted']==0


def test_receipt_cannot_enable_triplet_writes_disabled_in_current_configuration(tmp_path,monkeypatch):
    mod,peer,cfg,first,second=fixture(tmp_path,monkeypatch)
    folder=tmp_path/'.claude/knowledge-services/graphiti-submissions'
    path=next(p for p in folder.glob('*.json') if p.name!='_owner.json')
    record=json.loads(path.read_bytes())
    marker=next(v for v in record['operations'].values() if v['name'].endswith('@superseded'))
    marker['transition']['representation']='triplet'
    path.write_text(json.dumps(record),encoding='utf8')
    before=base.public(tmp_path);requests=len(peer.requests)
    with pytest.raises(mod.ErrorMCP):mod.apply(mod.plan([],cfg),cfg)
    assert base.public(tmp_path)==before and not any(name in ('add_triplet','add_memory') for name,args in peer.requests[requests:])


def test_intent_fields_must_match_exact_remote_marker_body(tmp_path,monkeypatch):
    mod,peer,cfg,first,second=fixture(tmp_path,monkeypatch)
    folder=tmp_path/'.claude/knowledge-services/graphiti-submissions'
    path=next(p for p in folder.glob('*.json') if p.name!='_owner.json')
    record=json.loads(path.read_bytes())
    marker=next(v for v in record['operations'].values() if v['name'].endswith('@superseded'))
    marker['transition']['replacement_episode_uuid']='altered-recorded-identity'
    path.write_text(json.dumps(record),encoding='utf8')
    before=base.public(tmp_path)
    with pytest.raises(mod.ErrorMCP):mod.apply(mod.plan([],cfg),cfg)
    assert base.public(tmp_path)==before and len(peer.queued)==3


def test_shared_manifest_writer_retries_transient_windows_denial(tmp_path,monkeypatch):
    mod,peer,cfg,first=base.fixture(tmp_path,monkeypatch);helper=mod._gpub
    state=helper._helper('local-state');original_loader=helper._helper;original_replace=os.replace
    proxy=types.SimpleNamespace(**vars(os));proxy.name='nt';calls=[]
    def denied_once(source,target):
        if Path(target).name=='graphiti-manifest.json':
            calls.append((source,target))
            if len(calls)==1:
                error=PermissionError('Owned transient replacement denial');error.winerror=5;raise error
        return original_replace(source,target)
    proxy.replace=denied_once;monkeypatch.setattr(state,'os',proxy)
    monkeypatch.setattr(helper,'_helper',lambda name:state if name=='local-state' else original_loader(name))
    monkeypatch.setattr(mod.os,'replace',denied_once)
    desired=base.public(tmp_path);desired['writer_probe']='confirmed'
    mod._escribir_manifest(cfg,desired)
    assert len(calls)==2 and base.public(tmp_path)==desired
    assert not list((tmp_path/'.claude/knowledge-services').glob('*.tmp'))


def test_shared_manifest_writer_does_not_replace_a_changed_target_after_denial(tmp_path,monkeypatch):
    mod,peer,cfg,first=base.fixture(tmp_path,monkeypatch);helper=mod._gpub
    state=helper._helper('local-state');original_loader=helper._helper;original_replace=os.replace
    proxy=types.SimpleNamespace(**vars(os));proxy.name='nt';calls=[]
    def changed(source,target):
        if Path(target).name=='graphiti-manifest.json':
            calls.append((source,target))
            Path(target).write_text('{"external":"preserved"}',encoding='utf8')
            error=PermissionError('Owned concurrent target change');error.winerror=5;raise error
        return original_replace(source,target)
    proxy.replace=changed;monkeypatch.setattr(state,'os',proxy)
    monkeypatch.setattr(helper,'_helper',lambda name:state if name=='local-state' else original_loader(name))
    monkeypatch.setattr(mod.os,'replace',changed)
    with pytest.raises(mod.ErrorMCP):mod._escribir_manifest(cfg,{'group_id':cfg['group_id'],'entradas':{}})
    assert base.public(tmp_path)=={'external':'preserved'} and len(calls)==1


def test_read_only_observation_uses_manifest_limit_separate_from_receipt_limit(tmp_path,monkeypatch):
    mod,peer,cfg,first,second=fixture(tmp_path,monkeypatch,complete=False)
    value=base.public(tmp_path);value['owned_padding']='x'*(mod._gpub.MAX_STATE_BYTES+1)
    mod._escribir_manifest(cfg,value)
    before=inventory(tmp_path);requests=len(peer.requests)
    observed=mod._gpub.observe(cfg)
    assert observed['unconfirmed']==1 and observed['uncommitted']==1
    assert inventory(tmp_path)==before and len(peer.requests)==requests
