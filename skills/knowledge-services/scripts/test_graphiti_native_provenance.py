"""Native search provenance is episode UUID linkage, not an Entity name."""
import copy,importlib.util,json
from pathlib import Path
import pytest

here=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('native_provenance_base',here/'test_graphiti_publication.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
wire=json.loads((here/'fixtures/graphiti/graphiti-native-provenance.json').read_bytes())

def decoded(response):return response['structuredContent']['result']
published=wire['manifest'];id_=next(iter(published['entradas']))
active=published['entradas'][id_]['uuid'];retired=published['transitions'][id_+'@1@superseded']['source_episode_uuid']

class Peer:
    def __init__(self):
        self.requests=[]
        self.nodes=copy.deepcopy(decoded(wire['search_nodes'])['nodes'])
        self.facts=copy.deepcopy(decoded(wire['search_memory_facts'])['facts'])
        self.membership_available=True
        self.membership_foreign=False

    def initialize(self):return {}
    def output(self,value):return {'isError':False,'structuredContent':{'result':value}}
    def tools_call(self,name,args):
        self.requests.append((name,copy.deepcopy(args)))
        if name=='get_status':return copy.deepcopy(wire[name])
        if name=='get_episodes':return copy.deepcopy(wire[name])
        if name=='search_nodes':return self.output({'nodes':copy.deepcopy(self.nodes)})
        if name=='search_memory_facts':return self.output({'facts':copy.deepcopy(self.facts)})
        assert name=='get_episode_entities'
        if not self.membership_available:raise ValueError('Tool not available on this fixture peer')
        assert args['group_id']==published['group_id']
        assert len(args['episode_uuids'])==1 and args['episode_uuids'][0]==active
        nodes=copy.deepcopy(self.nodes)
        if self.membership_foreign:
            for node in nodes:node['group_id']='foreign-project'
        return self.output({'nodes':nodes,'edges':[]})

def fixture(tmp_path,monkeypatch):
    mod=base.load();peer=Peer()
    parent=tmp_path/'.claude/knowledge-services';parent.mkdir(parents=True)
    (parent/'graphiti-manifest.json').write_text(json.dumps(published),encoding='utf8')
    cfg={'_root':str(tmp_path),'endpoint':'http://127.0.0.1:8001/mcp','group_id':published['logical_group_id'],
         'mode':'read','provider':{'llm':'none'},'timeout_ms':1000,'max_episodes':20,'max_respuesta_kb':256}
    monkeypatch.setattr(mod,'ClienteMCP',lambda *args,**kwargs:peer)
    monkeypatch.setattr(mod,'health',lambda cfg:{'estado':'sano'})
    return mod,peer,cfg

def query(mod,cfg):return mod.consultar(cfg,{'texto':'Where does Project Lyra store documentation?','limit':5})

def test_real_fact_episode_uuids_resolve_to_current_approved_provenance(tmp_path,monkeypatch):
    mod,peer,cfg=fixture(tmp_path,monkeypatch);peer.nodes=[]
    result=query(mod,cfg)
    assert len(result['aciertos'])==1
    hit=result['aciertos'][0]
    assert hit['id']==id_ and hit['version']=='2' and hit['uuid']==active
    assert hit['ruta']=='docs/knowledge/approved/gotchas/lyra.md' and hit['estado']=='aprobado'
    assert hit['contenido_derivado'] is True and hit['autoridad']=='ninguna'
    assert hit['verificacion']=='no_verificada' and hit['citas_por_afirmacion'] is False

def test_real_entity_node_is_linked_through_exact_episode_membership(tmp_path,monkeypatch):
    mod,peer,cfg=fixture(tmp_path,monkeypatch);peer.facts=[]
    result=query(mod,cfg)
    assert len(result['aciertos'])==1 and result['aciertos'][0]['id']==id_
    assert result['aciertos'][0]['version']=='2' and result['aciertos'][0]['uuid']==active
    assert any(name=='get_episode_entities' for name,args in peer.requests)


def test_coincident_entity_name_cannot_bypass_membership(tmp_path,monkeypatch):
    mod,peer,cfg=fixture(tmp_path,monkeypatch);peer.facts=[];peer.nodes=peer.nodes[:1]
    peer.nodes[0]['name']=id_+'@2';peer.membership_available=False
    result=query(mod,cfg)
    assert result['aciertos']==[] and result['motivo']
    assert any(name=='get_episode_entities' for name,args in peer.requests)


def test_coincident_valid_entity_keeps_derived_labels_and_exact_source(tmp_path,monkeypatch):
    mod,peer,cfg=fixture(tmp_path,monkeypatch);peer.facts=[];peer.nodes=peer.nodes[:1]
    peer.nodes[0]['name']=id_+'@2'
    result=query(mod,cfg)
    assert len(result['aciertos'])==1
    assert result['aciertos'][0]['uuid']==active
    assert result['aciertos'][0]['contenido_derivado'] is True
    assert result['aciertos'][0]['autoridad']=='ninguna'
    assert any(name=='get_episode_entities' for name,args in peer.requests)


def test_modern_fact_missing_episode_references_cannot_use_name(tmp_path,monkeypatch):
    mod,peer,cfg=fixture(tmp_path,monkeypatch);peer.nodes=[]
    peer.facts[0].pop('episodes');peer.facts[0]['name']=id_+'@2'
    assert query(mod,cfg)['aciertos']==[]


def test_exact_episode_hit_is_derived_and_cannot_replace_native_entity_uuid(tmp_path,monkeypatch):
    mod,peer,cfg=fixture(tmp_path,monkeypatch);peer.facts=[];peer.nodes=peer.nodes[:1]
    peer.nodes[0].update(name=id_+'@2',uuid=active)
    result=query(mod,cfg)
    assert len(result['aciertos'])==1 and result['aciertos'][0]['uuid']==active
    assert result['aciertos'][0]['contenido_derivado'] is True


def test_adapter_preserves_exact_long_confirmed_id_and_path(tmp_path,monkeypatch):
    mod=base.load();peer=base.Peer(mod)
    monkeypatch.setattr(mod,'ClienteMCP',lambda *a,**k:peer)
    monkeypatch.setattr(mod,'health',lambda cfg:{'estado':'sano'})
    cfg={'_root':str(tmp_path),'endpoint':'http://127.0.0.1:8001/mcp','group_id':'owned-long-source',
         'mode':'shadow','provider':{'llm':'none'},'timeout_ms':1000}
    entry=base.item();entry['id']='owned.'+'x'*250
    entry['ruta']='docs/knowledge/approved/gotchas/'+'a'*210+'.md'
    with pytest.raises(mod.ErrorMCP):mod.apply(mod.plan([entry],cfg),cfg)
    peer.complete();mod.apply(mod.plan([entry],cfg),cfg)
    original=peer.tools_call
    def search(name,args):
        if name=='search_nodes':return {'structuredContent':{'result':{'nodes':[
            {'uuid':peer.remote[0]['uuid'],'name':peer.remote[0]['name'],
             'group_id':cfg['group_id'],'summary':'Controlled derived text'}]}}}
        if name=='search_memory_facts':return {'structuredContent':{'result':{'facts':[]}}}
        return original(name,args)
    peer.tools_call=search;cfg['mode']='read'
    hits=mod.consultar(cfg,{'texto':'documentation','limit':5})['aciertos']
    assert len(hits)==1 and hits[0]['id']==entry['id'] and hits[0]['ruta']==entry['ruta']


@pytest.mark.parametrize('unsafe',['docs/knowledge/approved/gotchas/'+'x'*210+'/../hidden.md',
                                  'docs/knowledge/approved/gotchas/'+'x'*210+'\u202ehidden.md',
                                  'docs/knowledge/approved/gotchas/'+'x'*4100+'.md'])
def test_long_unsafe_path_cannot_be_made_safe_by_truncation(unsafe):
    mod=base.load()
    assert mod._ruta_canonica(unsafe) is None


@pytest.mark.parametrize('incomplete',['failed','budget','window'])
def test_partial_membership_cannot_claim_an_unambiguous_entity_source(incomplete):
    spec=importlib.util.spec_from_file_location('native_provenance_guard',here.parent/'backends/graphiti_provenance.py')
    helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    count=21 if incomplete=='budget' else 2
    sources={f'episode-{i}':f'doc-{i}@1' for i in range(count)}
    context={'owned':dict(sources),'current':dict(sources),'expected_current':dict(sources),
             'nodes':{},'warnings':[]}
    if incomplete=='window':context['current'].pop('episode-1')
    class Membership:
        def tools_call(self,name,args):
            uid=args['episode_uuids'][0]
            if incomplete=='failed' and uid=='episode-1':raise ValueError('lost response')
            return {'nodes':[{'uuid':'shared-entity','group_id':'owned-group'}] if uid=='episode-0' else []}
    helper.populate_nodes(context,[{'uuid':'shared-entity'}],Membership(),lambda value:value,
                          {'group_id':'owned-group','timeout_ms':1000})
    assert helper.node_name({'uuid':'shared-entity'},context,{name:{} for name in sources.values()}) is None
    assert context['warnings']


def test_fact_with_an_unobserved_current_source_is_ambiguous():
    spec=importlib.util.spec_from_file_location('native_fact_guard',here.parent/'backends/graphiti_provenance.py')
    helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    context={'owned':{'one':'doc-one@1','two':'doc-two@1'},
             'current':{'one':'doc-one@1'},'expected_current':{'one':'doc-one@1','two':'doc-two@1'}}
    assert helper.fact_name({'episodes':['one','two']},context,{'doc-one@1':{}}) is None

def test_mixed_old_and_current_native_sources_select_current_version(tmp_path,monkeypatch):
    mod,peer,cfg=fixture(tmp_path,monkeypatch);peer.nodes=[]
    assert peer.facts[0]['episodes']==[retired,active]
    result=query(mod,cfg)
    assert len(result['aciertos'])==1 and result['aciertos'][0]['version']=='2'

def test_retired_only_native_fact_does_not_resurrect_its_source(tmp_path,monkeypatch):
    mod,peer,cfg=fixture(tmp_path,monkeypatch);peer.nodes=[];peer.facts[0]['episodes']=[retired]
    assert query(mod,cfg)['aciertos']==[]

@pytest.mark.parametrize('references',[None,{},[1],['unknown-episode'],[active,'unknown-episode']])
def test_explicit_invalid_native_reference_cannot_downgrade_to_entity_name(tmp_path,monkeypatch,references):
    mod,peer,cfg=fixture(tmp_path,monkeypatch);peer.nodes=[]
    peer.facts[0]['episodes']=references;peer.facts[0]['name']=id_+'@2'
    assert query(mod,cfg)['aciertos']==[]

def test_unavailable_membership_preserves_independently_bound_fact(tmp_path,monkeypatch):
    mod,peer,cfg=fixture(tmp_path,monkeypatch);peer.membership_available=False
    result=query(mod,cfg)
    assert len(result['aciertos'])==1 and result['aciertos'][0]['fuente']=='hecho'
    assert result['motivo']

def test_foreign_membership_cannot_be_attached_to_current_project(tmp_path,monkeypatch):
    mod,peer,cfg=fixture(tmp_path,monkeypatch);peer.facts=[];peer.membership_foreign=True
    assert query(mod,cfg)['aciertos']==[]

def test_foreign_fact_is_not_mapped_by_a_coincident_episode_uuid(tmp_path,monkeypatch):
    mod,peer,cfg=fixture(tmp_path,monkeypatch);peer.nodes=[];peer.facts[0]['group_id']='foreign-project'
    assert query(mod,cfg)['aciertos']==[]


def test_native_uuid_beyond_initial_window_triggers_bounded_expansion(tmp_path,monkeypatch):
    mod,peer,cfg=fixture(tmp_path,monkeypatch);peer.nodes=[];cfg['max_episodes']=200
    original=peer.tools_call
    episodes=decoded(wire['get_episodes'])['episodes']
    fillers=[{'name':'untracked'+str(index)+'@1','uuid':'untracked-'+str(index),
              'group_id':published['group_id'],'content':'Untracked documentary content'} for index in range(60)]
    def window(name,args):
        if name=='get_episodes':
            peer.requests.append((name,copy.deepcopy(args)))
            return peer.output({'episodes':copy.deepcopy((fillers+episodes)[:args['max_episodes']])})
        return original(name,args)
    peer.tools_call=window
    result=query(mod,cfg)
    assert len(result['aciertos'])==1 and result['aciertos'][0]['uuid']==active
    assert any(args['max_episodes']>50 for name,args in peer.requests if name=='get_episodes')


def test_native_uuid_window_limit_is_reported_without_guessing_a_source(tmp_path,monkeypatch):
    mod,peer,cfg=fixture(tmp_path,monkeypatch);peer.nodes=[]
    original=mod._indice_procedencia_ventana
    def hidden(client,group_id,limit):
        return {},set(),set(),limit,0
    monkeypatch.setattr(mod,'_indice_procedencia_ventana',hidden)
    result=query(mod,cfg)
    assert result['aciertos']==[] and result['fuera_de_ventana']==1 and result['motivo']


def test_entity_membership_source_beyond_initial_window_is_expanded(tmp_path,monkeypatch):
    mod,peer,cfg=fixture(tmp_path,monkeypatch);peer.facts=[];cfg['max_episodes']=200
    original=peer.tools_call
    episodes=decoded(wire['get_episodes'])['episodes']
    fillers=[{'name':'untracked'+str(index)+'@1','uuid':'untracked-'+str(index),
              'group_id':published['group_id'],'content':'Untracked documentary content'} for index in range(60)]
    def window(name,args):
        if name=='get_episodes':
            peer.requests.append((name,copy.deepcopy(args)))
            return peer.output({'episodes':copy.deepcopy((fillers+episodes)[:args['max_episodes']])})
        return original(name,args)
    peer.tools_call=window
    result=query(mod,cfg)
    assert len(result['aciertos'])==1 and result['aciertos'][0]['uuid']==active
    assert any(name=='get_episode_entities' for name,args in peer.requests)
