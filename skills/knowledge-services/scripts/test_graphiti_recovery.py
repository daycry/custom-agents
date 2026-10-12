"""Portable transition records and retained generation recovery."""
import importlib.util,json,copy
from pathlib import Path
import pytest
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('recovery_base',HERE/'test_graphiti_transitions.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)

def test_default_transition_delivery_confirms_group_episode_without_direct_triplet(tmp_path,monkeypatch):
    mod,peer,cfg,first=base.fixture(tmp_path,monkeypatch);cfg.pop('transition_relations')
    second=base.next_version(first);assert mod.apply(mod.plan([second],cfg),cfg)['aplicados']==1
    assert not any(name=='add_triplet' for name,args in peer.requests)
    marker=base.public(tmp_path)['transitions'][first['id']+'@1@superseded']
    assert marker['representation']=='episode' and 'edge_uuid' not in marker
    remote=next(e for e in peer.remote if e['uuid']==marker['uuid'])
    assert 'relation: SUPERSEDES' in remote['content']
    assert marker['source_ref'] in remote['content'] and marker['target_ref'] in remote['content']
    assert mod.apply(mod.plan([],cfg),cfg)['revocados']==1
    assert mod.verify(cfg)['ok'] is True

def test_unknown_transition_delivery_rejected_before_submission(tmp_path,monkeypatch):
    mod,peer,cfg,first=base.fixture(tmp_path,monkeypatch);cfg['transition_relations']='unsafe-guess'
    before=base.public(tmp_path);requests=len(peer.requests)
    with pytest.raises(mod.ErrorMCP):mod.apply(mod.plan([base.next_version(first)],cfg),cfg)
    assert base.public(tmp_path)==before and not any(name in ('add_memory','add_triplet') for name,args in peer.requests[requests:])

def test_retained_pending_identity_still_allows_bound_withdrawal(tmp_path,monkeypatch):
    mod,peer,cfg,first=base.fixture(tmp_path,monkeypatch);cfg.pop('transition_relations')
    before=base.public(tmp_path);op=mod.plan([],cfg)
    mod._escribir_manifest(cfg,copy.deepcopy(before),sufijo='.pending')
    peer.remote=[]  # The prior episode no longer appears in the observation window.
    result=mod.apply(op,cfg)
    assert result['revocados']==1 and base.public(tmp_path)['entradas']=={}
    marker=base.public(tmp_path)['transitions'][first['id']+'@1@withdrawn']
    assert marker['uuid'] and not any(name=='add_triplet' for name,args in peer.requests)
    assert before['entradas'][first['id']]['uuid'] in peer.remote[0]['content']


def test_combined_receipt_capacity_rejects_episode_before_corrupting_state(tmp_path,monkeypatch):
    mod,peer,cfg,first=base.fixture(tmp_path,monkeypatch);helper=mod._gpub
    with helper.session(cfg) as context:
        record,write,deadline,io=context
        record['relations']={}
        for index in range(helper.MAX_OPERATIONS):
            request={'source_node_name':f'owned-source-{index}','target_node_name':f'owned-target-{index}',
                     'edge_name':'SUPERSEDES','fact':f'Owned capacity case {index}.','group_id':cfg['group_id']}
            record['relations'][helper._digest(request)]={'phase':'submitting','request':request}
        write()
    folder=tmp_path/'.claude/knowledge-services/graphiti-submissions'
    state=helper._state_path(folder,{'endpoint':cfg['endpoint'],'group_id':cfg['group_id']})
    before=state.read_bytes();requests=len(peer.requests)
    episode={'name':'owned.capacity@1','group_id':cfg['group_id'],'source':'text',
             'source_description':'custom-agents:graphiti-memory','episode_body':'Owned capacity fixture.'}
    with pytest.raises(helper.PublicationError):helper.publish(cfg,episode,peer,mod._contenido_tool_call)
    assert state.read_bytes()==before
    assert not any(name=='add_memory' for name,args in peer.requests[requests:])
