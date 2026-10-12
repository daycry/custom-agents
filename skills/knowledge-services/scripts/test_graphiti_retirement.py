"""Pending submissions withdrawn before publication retain exact remote provenance."""
import copy,importlib.util,json
from pathlib import Path
import pytest
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('retirement_base',HERE/'test_graphiti_transitions.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)

class Peer(base.Peer):
    def __init__(self,mod):super().__init__(mod);self.delay_data=True;self.lose_data_ack=False
    def tools_call(self,name,args):
        if self.delay_data and name=='add_memory' and not args['name'].endswith(('@withdrawn','@superseded')):
            self.requests.append((name,copy.deepcopy(args)));self.queued.append(copy.deepcopy(args))
            if self.lose_data_ack:raise ConnectionResetError('Owned data acknowledgment lost')
            return self.output({'message':'Episode queued'})
        return super().tools_call(name,args)

def fixture(tmp_path,monkeypatch,lost=False):
    mod=base.base.load();peer=Peer(mod);peer.lose_data_ack=lost
    monkeypatch.setattr(mod,'ClienteMCP',lambda *a,**k:peer)
    cfg={'_root':str(tmp_path),'endpoint':'http://127.0.0.1:8001/mcp','group_id':'owned-retirement',
         'mode':'shadow','provider':{'llm':'none'},'timeout_ms':1000}
    first=base.base.item()
    with pytest.raises(mod.ErrorMCP):mod.apply(mod.plan([first],cfg),cfg)
    return mod,peer,cfg,first

def inventory(root):return {p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()}

def test_removed_pending_entry_has_read_only_retirement_plan(tmp_path,monkeypatch):
    mod,peer,cfg,first=fixture(tmp_path,monkeypatch);before=inventory(tmp_path);requests=len(peer.requests)
    ops=mod.plan([],cfg)
    assert len(ops)==1 and ops[0]['tipo']=='retire_submission'
    assert ops[0]['id']==first['id'] and ops[0]['version']==1 and ops[0]['group_id']==cfg['group_id']
    assert ops[0]['submission_name']==first['id']+'@1' and len(ops[0]['episode_body_sha256'])==64
    assert inventory(tmp_path)==before and len(peer.requests)==requests

def test_late_persisted_submission_is_withdrawn_without_republication(tmp_path,monkeypatch):
    mod,peer,cfg,first=fixture(tmp_path,monkeypatch);peer.persist(peer.queued[0])
    result=mod.apply(mod.plan([],cfg),cfg)
    assert result['revocados']==1 and result['retirados_pendientes']==1
    public=base.public(tmp_path);assert public['entradas']=={}
    marker=public['transitions'][first['id']+'@1@withdrawn']
    assert marker['retired_episode']['uuid']==peer.remote[0]['uuid']
    assert marker['retired_episode']['name']==first['id']+'@1'
    assert len(peer.queued)==2 and mod.verify(cfg)['ok'] is True
    assert mod._gpub.observe(cfg)['unconfirmed']==mod._gpub.observe(cfg)['uncommitted']==0
    before=copy.deepcopy(public);requests=len(peer.requests)
    assert mod.apply(mod.plan([],cfg),cfg)['revocados']==0
    assert base.public(tmp_path)==before and not any(name=='add_memory' for name,args in peer.requests[requests:])

def test_unknown_persistence_remains_pending_without_resend(tmp_path,monkeypatch):
    mod,peer,cfg,first=fixture(tmp_path,monkeypatch);ops=mod.plan([],cfg)
    with pytest.raises(mod.ErrorMCP):mod.apply(ops,cfg)
    assert len(peer.queued)==1 and not peer.remote
    assert mod._gpub.observe(cfg)['unconfirmed']==1

def test_lost_initial_ack_can_be_retired_after_exact_readback(tmp_path,monkeypatch):
    mod,peer,cfg,first=fixture(tmp_path,monkeypatch,lost=True);peer.persist(peer.queued[0])
    assert mod.apply(mod.plan([],cfg),cfg)['retirados_pendientes']==1
    assert len(peer.queued)==2 and base.public(tmp_path)['entradas']=={}

def test_still_approved_submission_is_confirmed_instead_of_retired(tmp_path,monkeypatch):
    mod,peer,cfg,first=fixture(tmp_path,monkeypatch)
    ops=mod.plan([first],cfg)
    assert len(ops)==1 and ops[0]['tipo']=='upsert'
    peer.persist(peer.queued[0]);assert mod.apply(ops,cfg)['aplicados']==1
    assert len(peer.queued)==1 and not base.public(tmp_path)['transitions']

def test_conflicting_late_episode_is_not_retired_or_adopted(tmp_path,monkeypatch):
    mod,peer,cfg,first=fixture(tmp_path,monkeypatch);peer.persist(peer.queued[0]);peer.remote[0]['content']='Foreign changed body.'
    public=tmp_path/'.claude/knowledge-services/graphiti-manifest.json'
    before=public.read_bytes() if public.exists() else None
    with pytest.raises(mod.ErrorMCP):mod.apply(mod.plan([],cfg),cfg)
    assert len(peer.queued)==1 and (public.read_bytes() if public.exists() else None)==before

def test_retirement_of_pending_v1_preserves_new_approved_v2(tmp_path,monkeypatch):
    mod,peer,cfg,first=fixture(tmp_path,monkeypatch);peer.persist(peer.queued[0]);peer.delay_data=False
    second=base.next_version(first);ops=mod.plan([second],cfg)
    assert [op['tipo'] for op in ops]==['retire_submission','upsert']
    result=mod.apply(ops,cfg);assert result['aplicados']==1 and result['retirados_pendientes']==1
    assert base.public(tmp_path)['entradas'][first['id']]['version']==2
    assert len(peer.queued)==3 and mod.verify(cfg)['ok'] is True

def test_pending_withdrawal_marker_recovers_without_duplicate_queue(tmp_path,monkeypatch):
    mod,peer,cfg,first=fixture(tmp_path,monkeypatch);peer.persist(peer.queued[0]);peer.delay_markers=True
    with pytest.raises(mod.ErrorMCP):mod.apply(mod.plan([],cfg),cfg)
    assert len(peer.queued)==2
    peer.persist(peer.queued[1]);peer.delay_markers=False
    assert mod.apply(mod.plan([],cfg),cfg)['retirados_pendientes']==1
    assert len(peer.queued)==2 and mod._gpub.observe(cfg)['uncommitted']==0


def test_commit_interruption_retains_receipts_until_exact_withdrawal_binding(tmp_path,monkeypatch):
    mod,peer,cfg,first=fixture(tmp_path,monkeypatch);peer.persist(peer.queued[0])
    original=mod._escribir_manifest
    def cut(c,value,sufijo=''):
        if not sufijo and value.get('transitions'):raise OSError('Owned publication commit interruption')
        return original(c,value,sufijo)
    with monkeypatch.context() as patch:
        patch.setattr(mod,'_escribir_manifest',cut)
        with pytest.raises(OSError):mod.apply(mod.plan([],cfg),cfg)
    assert mod._gpub.observe(cfg)['uncommitted']==2
    assert len(peer.queued)==2
    mod.apply(mod.plan([],cfg),cfg)
    assert len(peer.queued)==2 and mod._gpub.observe(cfg)['uncommitted']==0
    assert base.public(tmp_path)['entradas']=={} and mod.verify(cfg)['ok'] is True


def test_replayed_retirement_never_removes_a_new_published_generation(tmp_path,monkeypatch):
    mod,peer,cfg,first=fixture(tmp_path,monkeypatch);old=mod.plan([],cfg)
    peer.persist(peer.queued[0]);peer.delay_data=False
    mod.apply(mod.plan([base.next_version(first)],cfg),cfg)
    before=base.public(tmp_path);requests=len(peer.requests)
    result=mod.apply(old,cfg)
    assert result['revocados']==0 and result['omitidos_obsoletos']==1
    assert base.public(tmp_path)==before and not any(name in ('add_memory','add_triplet') for name,args in peer.requests[requests:])


def test_retirement_request_cannot_change_the_owned_receipt_hash(tmp_path,monkeypatch):
    mod,peer,cfg,first=fixture(tmp_path,monkeypatch);peer.persist(peer.queued[0])
    ops=mod.plan([],cfg);ops[0]['episode_body_sha256']='0'*64
    with pytest.raises(mod.ErrorMCP):mod.apply(ops,cfg)
    assert len(peer.queued)==1 and mod._gpub.observe(cfg)['unconfirmed']==1


def test_retirement_refuses_a_remote_episode_from_another_group(tmp_path,monkeypatch):
    mod,peer,cfg,first=fixture(tmp_path,monkeypatch);peer.persist(peer.queued[0]);peer.remote[0]['group_id']='foreign-group'
    with pytest.raises(mod.ErrorMCP):mod.apply(mod.plan([],cfg),cfg)
    assert len(peer.queued)==1 and mod._gpub.observe(cfg)['unconfirmed']==1
