"""Current entries and committed historical identities share a strict read-only gate."""
import copy,hashlib,importlib.util,json
from pathlib import Path
import pytest
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('history_base',HERE/'test_graphiti_transitions.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)

def fixture(tmp_path,monkeypatch,triplet=False):
    mod,peer,cfg,first=base.fixture(tmp_path,monkeypatch)
    if not triplet:cfg.pop('transition_relations')
    assert mod.apply(mod.plan([base.next_version(first)],cfg),cfg)['aplicados']==1
    assert mod.apply(mod.plan([],cfg),cfg)['revocados']==1
    return mod,peer,cfg,first

def inventory(root):return {p.relative_to(root).as_posix():None if p.is_dir() else hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*')}

def test_history_only_verification_observes_all_committed_episode_bindings(tmp_path,monkeypatch):
    mod,peer,cfg,first=fixture(tmp_path,monkeypatch);before=inventory(tmp_path);requests=len(peer.requests)
    result=mod.verify(cfg)
    assert result['ok'] is True and result['historico_verificado']==4
    assert any(name=='get_episodes' for name,args in peer.requests[requests:])
    assert inventory(tmp_path)==before and not any(name in ('add_memory','add_triplet','clear_graph') for name,args in peer.requests[requests:])

def test_history_only_verification_rejects_a_missing_transition_marker(tmp_path,monkeypatch):
    mod,peer,cfg,first=fixture(tmp_path,monkeypatch)
    peer.remote=[value for value in peer.remote if not value['name'].endswith('@superseded')]
    assert mod.verify(cfg)['ok'] is False

@pytest.mark.parametrize('field',['uuid','content','group_id'])
def test_transition_marker_requires_exact_uuid_body_and_group(tmp_path,monkeypatch,field):
    mod,peer,cfg,first=fixture(tmp_path,monkeypatch)
    value=next(v for v in peer.remote if v['name'].endswith('@withdrawn'))
    if field=='group_id':value.pop(field)
    else:value[field]='changed-history-binding'
    assert mod.verify(cfg)['ok'] is False

@pytest.mark.parametrize('version',[1,2])
def test_retired_episode_identity_is_part_of_history_verification(tmp_path,monkeypatch,version):
    mod,peer,cfg,first=fixture(tmp_path,monkeypatch)
    peer.remote=[value for value in peer.remote if value['name']!=first['id']+'@'+str(version)]
    assert mod.verify(cfg)['ok'] is False

def test_incomplete_history_window_is_not_complete_verification(tmp_path,monkeypatch):
    mod,peer,cfg,first=fixture(tmp_path,monkeypatch);cfg['max_episodes']=1;original=peer.tools_call
    def limited(name,args):
        if name=='get_episodes':return peer.output({'episodes':copy.deepcopy(peer.remote[-args['max_episodes']:])})
        return original(name,args)
    peer.tools_call=limited
    result=mod.verify(cfg)
    assert result['ok'] is False and result['estado']=='incompleto'
    assert result['no_verificado']==3 and result['total']==4

def test_foreign_episode_in_history_window_keeps_read_gate_closed(tmp_path,monkeypatch):
    mod,peer,cfg,first=fixture(tmp_path,monkeypatch)
    value=copy.deepcopy(peer.remote[0]);value['group_id']='foreign-group';peer.remote.append(value)
    assert mod.verify(cfg)['ok'] is False

def test_duplicate_expected_episode_name_is_not_unique_confirmation(tmp_path,monkeypatch):
    mod,peer,cfg,first=fixture(tmp_path,monkeypatch)
    value=copy.deepcopy(peer.remote[0]);value['uuid']='another-remote-identity';peer.remote.append(value)
    assert mod.verify(cfg)['ok'] is False

def test_triplet_history_requires_its_committed_edge_binding(tmp_path,monkeypatch):
    mod,peer,cfg,first=fixture(tmp_path,monkeypatch,triplet=True);peer.edges.pop(0)
    assert mod.verify(cfg)['ok'] is False

def test_invalid_retired_binding_is_rejected_before_network(tmp_path,monkeypatch):
    mod,peer,cfg,first=fixture(tmp_path,monkeypatch);value=base.public(tmp_path)
    value['transitions'][first['id']+'@1@superseded']['retired_episode']['name']='different.id@1'
    mod._escribir_manifest(cfg,value);requests=len(peer.requests);before=inventory(tmp_path)
    assert mod.verify(cfg)['ok'] is False
    assert len(peer.requests)==requests and inventory(tmp_path)==before


def test_history_intent_cannot_disagree_with_its_persisted_body_hash(tmp_path,monkeypatch):
    mod,peer,cfg,first=fixture(tmp_path,monkeypatch);value=base.public(tmp_path)
    value['transitions'][first['id']+'@1@superseded']['replacement_episode_uuid']='changed-replacement-identity'
    mod._escribir_manifest(cfg,value);requests=len(peer.requests)
    assert mod.verify(cfg)['ok'] is False
    assert len(peer.requests)==requests


def test_current_binding_cannot_reference_an_already_invalidated_version(tmp_path,monkeypatch):
    mod,peer,cfg,first=fixture(tmp_path,monkeypatch);value=base.public(tmp_path)
    retired=value['transitions'][first['id']+'@1@superseded']['retired_episode']
    value['entradas'][first['id']]={'version':1,'uuid':retired['uuid'],
        'episode_body_sha256':retired['episode_body_sha256'],'binding':'verified_readback'}
    mod._escribir_manifest(cfg,value);requests=len(peer.requests)
    assert mod.verify(cfg)['ok'] is False
    assert len(peer.requests)==requests


def test_actual_captured_history_envelope_and_manifest_are_verified_without_network(tmp_path,monkeypatch):
    fixture_dir=HERE/'fixtures/graphiti'
    published=json.loads((fixture_dir/'graphiti-manifest-history.json').read_bytes())
    response=json.loads((fixture_dir/'graphiti-mcp-history-window.json').read_bytes())
    mod=base.base.load();requests=[]
    class CapturedPeer:
        def initialize(self):return {}
        def tools_call(self,name,args):
            requests.append((name,copy.deepcopy(args)))
            assert name=='get_episodes' and args['group_ids']==[published['group_id']]
            return copy.deepcopy(response)
    monkeypatch.setattr(mod,'ClienteMCP',lambda *a,**k:CapturedPeer())
    cfg={'_root':str(tmp_path),'endpoint':'http://127.0.0.1:8001/mcp','group_id':published['group_id'],
         'mode':'shadow','timeout_ms':1000,'max_episodes':20}
    mod._escribir_manifest(cfg,published);before=inventory(tmp_path)
    result=mod.verify(cfg)
    assert result['ok'] is True and result['historico_verificado']==4
    assert len(requests)==1 and inventory(tmp_path)==before
