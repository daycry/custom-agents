"""Version markers and Entity relations use the supported Graphiti contracts."""
import copy,importlib.util,json,uuid
from pathlib import Path
import pytest
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('transition_base',HERE/'test_graphiti_publication.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
class Peer:
    def __init__(self,mod):self.mod=mod;self.requests=[];self.remote=[];self.queued=[];self.nodes=[];self.edges=[];self.delay_markers=False;self.lose_link_ack=False
    def initialize(self):return {}
    def output(self,value):return {'isError':False,'structuredContent':{'result':value}}
    def persist(self,args):
        self.remote.append({'uuid':str(uuid.uuid4()),'name':args['name'],'group_id':args['group_id'],'content':args['episode_body'],
            'source':args['source'],'source_description':args['source_description']})
    def tools_call(self,name,args):
        self.requests.append((name,copy.deepcopy(args)))
        if name=='get_episodes':return self.output({'episodes':copy.deepcopy(self.remote)})
        if name=='search_nodes':return self.output({'nodes':copy.deepcopy(self.nodes)})
        if name=='search_memory_facts':return self.output({'facts':copy.deepcopy(self.edges)})
        if name=='add_memory':
            if 'uuid' in args:raise self.mod.ErrorMCP('New marker UUID addresses a nonexistent Episodic node')
            self.queued.append(copy.deepcopy(args))
            if not self.delay_markers or not args['name'].endswith(('@superseded','@withdrawn')):self.persist(args)
            return self.output({'message':'Episode queued'})
        assert name=='add_triplet'
        assert 'source_node_uuid' not in args and 'target_node_uuid' not in args,'Episodic UUIDs must not be passed as Entity identities'
        pair=[]
        for key in ('source_node_name','target_node_name'):
            found=[n for n in self.nodes if n['name']==args[key]]
            if not found:
                node={'uuid':str(uuid.uuid4()),'name':args[key],'group_id':args['group_id'],'labels':['Entity']};self.nodes.append(node);found=[node]
            pair.append(found[0])
        edge={'uuid':str(uuid.uuid4()),'name':args['edge_name'],'fact':args['fact'],'group_id':args['group_id'],
            'source_node_uuid':pair[0]['uuid'],'target_node_uuid':pair[1]['uuid'],'invalid_at':None}
        self.edges.append(edge)
        if self.lose_link_ack:raise ConnectionResetError('Owned link response lost after persistence')
        return self.output({'message':'Triplet added','nodes':copy.deepcopy(pair),'edges':[copy.deepcopy(edge)]})
def fixture(tmp_path,monkeypatch):
    mod=base.load();peer=Peer(mod);monkeypatch.setattr(mod,'ClienteMCP',lambda *a,**k:peer)
    cfg={'_root':str(tmp_path),'endpoint':'http://127.0.0.1:8001/mcp','group_id':'owned-transitions','mode':'shadow','provider':{'llm':'none'},'timeout_ms':1000,'transition_relations':'triplet'}
    first=base.item();assert mod.apply(mod.plan([first],cfg),cfg)['aplicados']==1
    return mod,peer,cfg,first
def public(root):return json.loads((root/'.claude/knowledge-services/graphiti-manifest.json').read_bytes())
def next_version(first):
    value=copy.deepcopy(first);value['version']=2;value['cuerpo']='Project Lyra now uses Borealis for documentation.';return value

def test_version_succession_confirms_marker_and_distinct_entity_relation(tmp_path,monkeypatch):
    mod,peer,cfg,first=fixture(tmp_path,monkeypatch);second=next_version(first)
    assert mod.apply(mod.plan([second],cfg),cfg)['aplicados']==1
    value=public(tmp_path);assert value['entradas'][first['id']]['version']==2
    marker=first['id']+'@1@superseded'
    assert marker in value['transitions'] and value['transitions'][marker]['edge_uuid']==peer.edges[0]['uuid']
    assert {e['name'] for e in peer.remote}=={first['id']+'@1',first['id']+'@2',marker}
    call=next(args for name,args in peer.requests if name=='add_triplet')
    assert call['source_node_name']=='custom-agents:knowledge:'+first['id']+'@2'
    assert call['target_node_name']=='custom-agents:knowledge:'+first['id']+'@1'
    assert mod.verify(cfg)['ok'] is True

def test_withdrawal_is_version_scoped_confirmed_and_keeps_history(tmp_path,monkeypatch):
    mod,peer,cfg,first=fixture(tmp_path,monkeypatch)
    assert mod.apply(mod.plan([],cfg),cfg)['revocados']==1
    value=public(tmp_path);marker=first['id']+'@1@withdrawn'
    assert value['entradas']=={} and marker in value['transitions']
    assert len(peer.remote)==2 and peer.edges[0]['name']=='SUPERSEDES'
    assert mod.verify(cfg)['ok'] is True
    second=next_version(first);assert mod.apply(mod.plan([second],cfg),cfg)['aplicados']==1
    index,invalidated,superseded,_,_=mod._indice_procedencia_ventana(peer,cfg['group_id'],50)
    assert first['id'] not in invalidated and first['id']+'@1' in superseded
    assert first['id']+'@2' in index

def test_unconfirmed_marker_keeps_previous_published_generation(tmp_path,monkeypatch):
    mod,peer,cfg,first=fixture(tmp_path,monkeypatch);second=next_version(first);before=public(tmp_path)
    peer.delay_markers=True
    with pytest.raises(mod.ErrorMCP):mod.apply(mod.plan([second],cfg),cfg)
    assert public(tmp_path)==before and not peer.edges
    marker=next(args for args in peer.queued if args['name'].endswith('@superseded'));peer.persist(marker)
    peer.delay_markers=False
    assert mod.apply(mod.plan([second],cfg),cfg)['aplicados']==1
    assert len([q for q in peer.queued if q['name']==marker['name']])==1 and len(peer.edges)==1

def test_lost_relation_ack_is_recovered_without_duplicate_edge(tmp_path,monkeypatch):
    mod,peer,cfg,first=fixture(tmp_path,monkeypatch);second=next_version(first);before=public(tmp_path)
    peer.lose_link_ack=True
    with pytest.raises(mod.ErrorMCP):mod.apply(mod.plan([second],cfg),cfg)
    assert public(tmp_path)==before and len(peer.edges)==1
    peer.lose_link_ack=False
    assert mod.apply(mod.plan([second],cfg),cfg)['aplicados']==1
    assert len(peer.edges)==1 and len([x for x in peer.requests if x[0]=='add_triplet'])==1

def test_missing_actual_revoke_identity_is_not_fabricated(tmp_path,monkeypatch):
    mod,peer,cfg,first=fixture(tmp_path,monkeypatch)
    with pytest.raises(mod.ErrorMCP):mod._entrada_para_revoke(cfg['group_id'],first['id'],{first['id']:{'version':1}}, {})


def test_replayed_old_upsert_cannot_supersede_the_new_published_version(tmp_path,monkeypatch):
    mod,peer,cfg,first=fixture(tmp_path,monkeypatch);old=mod.plan([first],cfg,force=True)
    second=next_version(first);assert mod.apply(mod.plan([second],cfg),cfg)['aplicados']==1
    before=public(tmp_path);requests=len(peer.requests)
    result=mod.apply(old,cfg)
    assert result['aplicados']==0 and result['omitidos_obsoletos']==1
    assert public(tmp_path)==before and not any(name in ('add_memory','add_triplet') for name,args in peer.requests[requests:])

def test_replayed_revoke_is_bound_to_its_original_generation(tmp_path,monkeypatch):
    mod,peer,cfg,first=fixture(tmp_path,monkeypatch);old_revoke=mod.plan([],cfg)
    assert old_revoke[0].get('version')==1 and old_revoke[0].get('uuid')==public(tmp_path)['entradas'][first['id']]['uuid']
    second=next_version(first);assert mod.apply(mod.plan([second],cfg),cfg)['aplicados']==1
    before=public(tmp_path);requests=len(peer.requests)
    result=mod.apply(old_revoke,cfg)
    assert result['revocados']==0 and result['omitidos_obsoletos']==1
    assert public(tmp_path)==before and not any(name in ('add_memory','add_triplet') for name,args in peer.requests[requests:])


def test_retired_generation_cannot_be_republished_by_old_operation(tmp_path,monkeypatch):
    mod,peer,cfg,first=fixture(tmp_path,monkeypatch);old=mod.plan([first],cfg,force=True)
    assert mod.apply(mod.plan([],cfg),cfg)['revocados']==1
    before=public(tmp_path);requests=len(peer.requests)
    result=mod.apply(old,cfg)
    assert result['aplicados']==0 and result['omitidos_obsoletos']==1
    assert public(tmp_path)==before and not any(name in ('add_memory','add_triplet') for name,args in peer.requests[requests:])


def test_unbound_revoke_is_rejected_before_remote_mutation(tmp_path,monkeypatch):
    mod,peer,cfg,first=fixture(tmp_path,monkeypatch);before=public(tmp_path);requests=len(peer.requests)
    with pytest.raises(mod.ErrorMCP):mod.apply([{'tipo':'revoke','id':first['id']}],cfg)
    assert public(tmp_path)==before and not any(name in ('add_memory','add_triplet') for name,args in peer.requests[requests:])


def test_queued_upsert_cannot_move_to_a_different_group(tmp_path,monkeypatch):
    mod,peer,cfg,first=fixture(tmp_path,monkeypatch);queued=mod.plan([next_version(first)],cfg)
    assert queued[0].get('group_id')==cfg['group_id']
    cfg['group_id']='another-owned-group';requests=len(peer.requests)
    result=mod.apply(queued,cfg)
    assert result['aplicados']==0 and result['omitidos_obsoletos']==1
    assert not any(name in ('add_memory','add_triplet') for name,args in peer.requests[requests:])


def test_manual_revoke_uses_current_generation_binding(tmp_path,monkeypatch):
    mod,peer,cfg,first=fixture(tmp_path,monkeypatch)
    assert mod.revoke(first['id'],cfg)['revocado'] is True
    assert public(tmp_path)['entradas']=={}


def test_same_version_changed_content_requires_a_new_version(tmp_path,monkeypatch):
    mod,peer,cfg,first=fixture(tmp_path,monkeypatch);changed=copy.deepcopy(first);changed['cuerpo']='Different content.'
    before=public(tmp_path);requests=len(peer.requests)
    with pytest.raises(mod.ErrorMCP):mod.apply(mod.plan([changed],cfg),cfg)
    assert public(tmp_path)==before and not any(name in ('add_memory','add_triplet') for name,args in peer.requests[requests:])
