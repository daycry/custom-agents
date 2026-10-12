"""Creation and uncertain submission match the installed Graphiti contract."""
import copy
import importlib.util
import json
from pathlib import Path
import pytest
HERE=Path(__file__).resolve().parent
def load():
    path=HERE.parent/'backends/graphiti.py'
    spec=importlib.util.spec_from_file_location('graphiti_publication_contract',path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
def item():
    return {'id':'owned.gotcha.lyra','version':1,'category':'GOTCHA','evidencia':'validated_case',
        'fuentes':['docs/evidence.md'],'ruta':'docs/knowledge/approved/gotchas/lyra.md',
        'folder':'gotchas','tags':['area:testing'],'modo':'completo','cuerpo':'Project Lyra uses Aurora for documentation.'}
class Peer:
    def __init__(self,mod):self.mod=mod;self.requests=[];self.queued=[];self.remote=[];self.lose_ack=False
    def initialize(self):return {}
    def tools_call(self,name,args):
        self.requests.append((name,copy.deepcopy(args)))
        if name=='get_episodes':return {'isError':False,'structuredContent':{'result':{'episodes':copy.deepcopy(self.remote)}}}
        assert name=='add_memory'
        if args.get('uuid') is not None:raise self.mod.ErrorMCP('node for supplied new UUID not found')
        self.queued.append(copy.deepcopy(args))
        if self.lose_ack:raise ConnectionResetError('Owned acknowledgment lost after enqueue')
        return {'isError':False,'structuredContent':{'result':{'message':'Episode queued for processing'}}}
    def complete(self):
        assert len(self.queued)==1
        args=self.queued[0]
        self.remote=[{'name':args['name'],'uuid':'b5c23186-5b36-4d32-a3ad-1394aee54dd1',
            'group_id':args['group_id'],'content':args['episode_body'],'source':args['source'],
            'source_description':args['source_description']}]
def fixture(tmp_path,monkeypatch):
    mod=load();peer=Peer(mod)
    monkeypatch.setattr(mod,'ClienteMCP',lambda *a,**k:peer)
    cfg={'_root':str(tmp_path),'endpoint':'http://127.0.0.1:8001/mcp','group_id':'owned-publication',
        'mode':'shadow','provider':{'llm':'none'},'timeout_ms':1000}
    return mod,peer,cfg
def submit(mod,cfg):return mod.apply(mod.plan([item()],cfg),cfg)

def test_new_episode_omits_remote_uuid_and_remains_unconfirmed(tmp_path,monkeypatch):
    mod,peer,cfg=fixture(tmp_path,monkeypatch)
    with pytest.raises(mod.ErrorMCP):submit(mod,cfg)
    assert len(peer.queued)==1,'New creation still supplied a nonexistent remote UUID.'
    assert 'uuid' not in peer.queued[0]
    public=tmp_path/'.claude/knowledge-services/graphiti-manifest.json'
    assert not public.exists() or json.loads(public.read_bytes())['entradas']=={}
    state=tmp_path/'.claude/knowledge-services/graphiti-submissions'
    assert state.is_dir() and any('submitting' in p.read_text(encoding='utf8') or 'submitted' in p.read_text(encoding='utf8') for p in state.glob('*.json'))

def test_repeated_sync_observes_pending_without_second_enqueue(tmp_path,monkeypatch):
    mod,peer,cfg=fixture(tmp_path,monkeypatch)
    for _ in range(2):
        with pytest.raises(mod.ErrorMCP):submit(mod,cfg)
    assert len(peer.queued)==1,'Retry duplicated an unresolved asynchronous submission.'

def test_confirmed_readback_binds_real_uuid_without_resubmitting(tmp_path,monkeypatch):
    mod,peer,cfg=fixture(tmp_path,monkeypatch)
    with pytest.raises(mod.ErrorMCP):submit(mod,cfg)
    assert len(peer.queued)==1
    peer.complete();result=submit(mod,cfg)
    assert result['aplicados']==1 and len(peer.queued)==1
    public=json.loads((tmp_path/'.claude/knowledge-services/graphiti-manifest.json').read_bytes())
    assert public['entradas'][item()['id']]['uuid']==peer.remote[0]['uuid']
    assert mod.verify(cfg)['ok'] is True
    assert submit(mod,cfg)['aplicados']==0 and len(peer.queued)==1

def test_lost_ack_never_resends_an_uncertain_submission(tmp_path,monkeypatch):
    mod,peer,cfg=fixture(tmp_path,monkeypatch);peer.lose_ack=True
    for _ in range(2):
        with pytest.raises(mod.ErrorMCP):submit(mod,cfg)
    assert len(peer.queued)==1
    peer.complete();peer.lose_ack=False
    assert submit(mod,cfg)['aplicados']==1 and len(peer.queued)==1


def test_original_submission_error_survives_retry_without_second_send(tmp_path,monkeypatch):
    mod,peer,cfg=fixture(tmp_path,monkeypatch)
    original=peer.tools_call
    sends=[]
    def rejected(name,args):
        if name=='add_memory':
            sends.append(dict(args))
            raise mod.ErrorMCP('Tool isError: Ollama invalid JSON')
        return original(name,args)
    peer.tools_call=rejected
    for _ in range(2):
        with pytest.raises(mod.ErrorMCP,match='Ollama invalid JSON'):
            submit(mod,cfg)
    assert len(sends)==1
    receipt=mod._gpub.submissions(cfg)[0]
    assert receipt['phase']=='submitting'
    assert receipt['error']=={'kind':'ErrorMCP','detail':'Tool isError: Ollama invalid JSON'}


def test_persisted_error_is_redacted_and_contains_no_controls(tmp_path,monkeypatch):
    mod,peer,cfg=fixture(tmp_path,monkeypatch)
    original=peer.tools_call
    secret='sk-'+('F1xtureOnly'*3)
    def rejected(name,args):
        if name=='add_memory':raise mod.ErrorMCP('Ollama failed\n\u202e'+secret)
        return original(name,args)
    peer.tools_call=rejected
    with pytest.raises(mod.ErrorMCP):submit(mod,cfg)
    error=mod._gpub.submissions(cfg)[0]['error']
    assert secret not in error['detail'] and '\u202e' not in error['detail'] and '\n' not in error['detail']
    assert error['detail'].isprintable() and len(error['detail'])<=500


@pytest.mark.parametrize('invalid',[{'kind':1,'detail':'safe'}, {'kind':'ErrorMCP','detail':'\u202ehidden'},
                                  {'kind':'ErrorMCP','detail':'x'*501}])
def test_malformed_error_receipt_is_rejected_before_network(tmp_path,monkeypatch,invalid):
    mod,peer,cfg=fixture(tmp_path,monkeypatch);peer.lose_ack=True
    with pytest.raises(mod.ErrorMCP):submit(mod,cfg)
    paths=[p for p in (tmp_path/'.claude/knowledge-services/graphiti-submissions').glob('*.json') if p.name!='_owner.json']
    assert len(paths)==1
    record=json.loads(paths[0].read_bytes());next(iter(record['operations'].values()))['error']=invalid
    paths[0].write_text(json.dumps(record),encoding='utf8')
    before=list(peer.requests)
    with pytest.raises(mod._gpub.PublicationError,match='invalid_submission_error'):
        mod._gpub.submissions(cfg)
    assert peer.requests==before
def test_conflicting_remote_content_is_not_adopted_or_resent(tmp_path,monkeypatch):
    mod,peer,cfg=fixture(tmp_path,monkeypatch)
    with pytest.raises(mod.ErrorMCP):submit(mod,cfg)
    assert len(peer.queued)==1
    peer.complete();peer.remote[0]['content']='Foreign conflicting bytes.'
    with pytest.raises(mod.ErrorMCP):submit(mod,cfg)
    assert len(peer.queued)==1
    public=tmp_path/'.claude/knowledge-services/graphiti-manifest.json'
    assert not public.exists() or json.loads(public.read_bytes())['entradas']=={}

def test_existing_unowned_submission_directory_is_not_adopted(tmp_path,monkeypatch):
    mod,peer,cfg=fixture(tmp_path,monkeypatch)
    state=tmp_path/'.claude/knowledge-services/graphiti-submissions';state.mkdir(parents=True)
    neighbor=state/'keep.txt';neighbor.write_bytes(b'Unowned bytes.')
    with pytest.raises(mod.ErrorMCP):submit(mod,cfg)
    assert neighbor.read_bytes()==b'Unowned bytes.' and peer.requests==[]


def test_provider_change_during_pending_does_not_enqueue_again(tmp_path,monkeypatch):
    mod,peer,cfg=fixture(tmp_path,monkeypatch)
    with pytest.raises(mod.ErrorMCP):submit(mod,cfg)
    cfg['provider']={'llm':'ollama','model':'owned-model-change'}
    with pytest.raises(mod.ErrorMCP):submit(mod,cfg)
    assert len(peer.queued)==1,'Changing extraction instructions duplicated the pending episode.'

def test_changed_body_with_same_pending_name_is_not_submitted_twice(tmp_path,monkeypatch):
    mod,peer,cfg=fixture(tmp_path,monkeypatch)
    with pytest.raises(mod.ErrorMCP):submit(mod,cfg)
    changed=item();changed['cuerpo']='Different canonical bytes while the previous submission is unresolved.'
    with pytest.raises(mod.ErrorMCP):mod.apply(mod.plan([changed],cfg),cfg)
    assert len(peer.queued)==1,'A conflicting body created a second unresolved episode with the same name.'


def test_redirected_project_state_is_rejected_before_any_write(tmp_path,monkeypatch):
    import os,subprocess
    root=tmp_path/'project';root.mkdir();outside=tmp_path/'outside';outside.mkdir()
    link=root/'.claude'
    if os.name=='nt':
        result=subprocess.run([os.environ['COMSPEC'],'/c','mklink','/J',str(link),str(outside)],capture_output=True)
        if result.returncode:pytest.skip('Native junction unavailable in this fixture')
    else:link.symlink_to(outside,target_is_directory=True)
    mod,peer,cfg=fixture(root,monkeypatch)
    with pytest.raises(Exception):submit(mod,cfg)
    assert list(outside.iterdir())==[],'Publication wrote through redirected project state before checking its journal.'
    assert peer.requests==[]

def test_linked_manifest_is_not_read_or_replaced_before_validation(tmp_path,monkeypatch):
    import os
    mod,peer,cfg=fixture(tmp_path/'project',monkeypatch);Path(cfg['_root']).mkdir()
    folder=Path(cfg['_root'])/'.claude/knowledge-services';folder.mkdir(parents=True)
    outside=tmp_path/'outside.json';outside.write_text(json.dumps({'group_id':cfg['group_id'],'entradas':{}}),encoding='utf8')
    os.link(outside,folder/'graphiti-manifest.json')
    with pytest.raises(Exception):submit(mod,cfg)
    assert peer.requests==[],'Unsafe manifest was used before checking its regular single-link identity.'
    assert not (folder/'graphiti-manifest.pending.json').exists()

def test_apply_lock_covers_confirmation_and_published_manifest_commit(tmp_path,monkeypatch):
    import threading,uuid
    mod,peer,cfg=fixture(tmp_path,monkeypatch)
    original=peer.tools_call
    def immediate(name,args):
        value=original(name,args)
        if name=='add_memory':peer.remote.append({'name':args['name'],'uuid':str(uuid.uuid4()),'group_id':args['group_id'],
            'content':args['episode_body'],'source':args['source'],'source_description':args['source_description']})
        return value
    peer.tools_call=immediate
    first=item();second=item();second['id']='owned.gotcha.second';second['cuerpo']='Second independent approved record.'
    ops1=mod.plan([first],cfg);ops2=mod.plan([second],cfg)
    paused=threading.Event();resume=threading.Event();original_write=mod._escribir_manifest
    def write(c,data,sufijo=''):
        if not sufijo and first['id'] in data['entradas'] and not paused.is_set():
            paused.set();assert resume.wait(3),'Owned synchronization fixture timed out'
        return original_write(c,data,sufijo)
    monkeypatch.setattr(mod,'_escribir_manifest',write)
    result={}
    def worker():
        try:result['value']=mod.apply(ops1,cfg)
        except BaseException as error:result['error']=error
    child=threading.Thread(target=worker);child.start()
    try:
        assert paused.wait(2)
        with pytest.raises(mod.ErrorMCP):mod.apply(ops2,cfg)
        assert len(peer.queued)==1,'Another writer crossed the network while the first publication was not committed.'
    finally:
        resume.set();child.join(3)
    assert not child.is_alive() and 'error' not in result
    assert mod.apply(ops2,cfg)['aplicados']==1
    data=json.loads((tmp_path/'.claude/knowledge-services/graphiti-manifest.json').read_bytes())
    assert set(data['entradas'])=={first['id'],second['id']} and len(peer.queued)==2
