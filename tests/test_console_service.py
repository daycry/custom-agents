"""Project inventory isolation and fairness share the real background reader budget."""
import importlib.util
import json
from pathlib import Path
import threading
import time
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
SCRIPTS=ROOT/'skills/plugin-panel/scripts'

def load(name):
    spec=importlib.util.spec_from_file_location('service_test_'+name.replace('.','_'),SCRIPTS/name)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def test_native_inventory_is_scoped_cached_for_all_three_runtimes(tmp_path,monkeypatch):
    registry=load('console_workspaces.py');module=load('console_service.py')
    project=registry.Workspace('one','One',tmp_path,('codex','claude-code','opencode'))
    service=module.Service({'one':project},sessions=SimpleNamespace(close=lambda:None))
    method=getattr(service,'native_sessions',None)
    assert callable(method), 'Native inventory endpoint is missing'
    calls=[];original=module.C.sibling
    def discover(workspace,**kwargs):
        calls.append(workspace.root)
        return {'status':'ok','complete':True,'sessions':[{'id':'external','title':'Scoped metadata'}],'observed_at':1}
    monkeypatch.setattr(module.C,'sibling',lambda name:SimpleNamespace(discover=discover) if name in ('console_codex.py','console_claude.py','console_opencode.py') else original(name))
    try:
        deadline=time.monotonic()+2
        while time.monotonic()<deadline:
            value=method('one')
            if value['status']!='calculating':break
            time.sleep(.01)
        assert value['sessions'][0]['title']=='Scoped metadata'
        assert value['complete'] is True
        assert {p['runtime']:p['status'] for p in value['providers']}=={'codex':'ok','claude-code':'ok','opencode':'ok'}
        method('one');assert calls==[tmp_path,tmp_path,tmp_path]
        try:method('foreign')
        except ValueError:pass
        else:assert False,'Unregistered project accepted'
    finally:service.close()


def test_shutdown_closes_owned_inventory_peers_and_prevents_late_start(tmp_path,monkeypatch):
    module=load('console_service.py');service=module.Service({},sessions=SimpleNamespace(close=lambda:None))
    factory=getattr(service,'native_peer',None)
    assert callable(factory), 'Inventory process ownership is missing'
    closed=[]
    class FakePeer:
        def __init__(self,*args):pass
        def start(self):pass
        def close(self):closed.append(self)
    original=module.C.sibling
    monkeypatch.setattr(module.C,'sibling',lambda n:SimpleNamespace(JsonPeer=FakePeer) if n=='console_transport.py' else original(n))
    peer=factory([],tmp_path,lambda _:None);peer.start()
    service.close()
    assert peer in closed and not service.discovery_peers
    late=factory([],tmp_path,lambda _:None)
    try:late.start()
    except ValueError:pass
    else:assert False,'Process started after console shutdown'


def test_activity_execution_detail_uses_project_history_and_rejects_unknown_identity(tmp_path,monkeypatch):
    registry=load('console_workspaces.py');module=load('console_service.py')
    service=module.Service({'one':registry.Workspace('one','One',tmp_path,())},sessions=SimpleNamespace(close=lambda:None))
    method=getattr(service,'activity_run',None)
    assert callable(method), 'Activity execution details are missing'
    reads=[]
    monkeypatch.setattr(module.LEGACY,'activity_history',lambda root:(reads.append(root) or {'test':True},None))
    monkeypatch.setattr(module.DATA,'actividad_run',lambda history,key16,now: {'status':'ok','key16':key16,'run':{'role':'reviewer'},'eventos':[]} if key16=='a'*16 else None)
    try:
        assert method('one','a'*16)['run']['role']=='reviewer'
        for invalid in ('../outside','b'*16):
            try:method('one',invalid)
            except ValueError:pass
            else:assert False,'Unknown execution accepted'
        assert all(root==tmp_path for root in reads)
    finally:service.close()

def test_a_slow_catalog_cannot_reserve_all_readers_while_other_projects_wait(tmp_path,monkeypatch):
    registry=load('console_workspaces.py');module=load('console_service.py');workspaces={}
    for name in ['slow','fast-one','fast-two','fast-three','plan']:
        root=tmp_path/name;root.mkdir();workspaces[name]=registry.Workspace(name,name,root,())
    service=module.Service(workspaces,sessions=SimpleNamespace(close=lambda:None))
    release=threading.Event();started=threading.Event();original=module.C.sibling
    def inventory(_root,**kwargs):
        if Path(kwargs['project']).name=='slow':started.set();release.wait(timeout=5)
        return {'agents':[],'skills':[],'commands':[]}
    def sibling(name):
        return SimpleNamespace(build_inventory=inventory) if name=='build_panel.py' else original(name)
    monkeypatch.setattr(module.C,'sibling',sibling)
    try:
        service.catalog('slow');assert started.wait(timeout=2)
        for name in ['fast-one','fast-two','fast-three']:service.catalog(name)
        deadline=time.monotonic()+1.5;value={}
        while time.monotonic()<deadline:
            value=service.plans('plan')
            if value['status']=='not_found':break
            time.sleep(.01)
        assert value.get('status')=='not_found','unrelated plans waited behind a catalog mutex'
    finally:release.set();service.close()


def test_parallel_real_catalogs_keep_project_roots_and_metadata_separate(tmp_path):
    registry=load('console_workspaces.py');module=load('console_service.py');workspaces={}
    for name in ('one','two'):
        root=tmp_path/name;root.mkdir();workspace=registry.Workspace(name,name,root,())
        workspaces[name]=workspace
        agents=root/'.claude/agents';agents.mkdir(parents=True)
        (agents/('private-'+name+'.md')).write_text('---\nname: private-'+name+'\ndescription: '+str(workspace.root)+'\n---\n\nBODY MUST NOT BE EXPORTED\n',encoding='utf-8')
    service=module.Service(workspaces,sessions=SimpleNamespace(close=lambda:None))
    try:
        for name in workspaces:service.catalog(name)
        deadline=time.monotonic()+15;values={}
        while time.monotonic()<deadline:
            values={name:service.catalog(name) for name in workspaces}
            if all(value.get('extensions') for value in values.values()):break
            time.sleep(.05)
        for name,value in values.items():
            raw=json.dumps(value)
            assert value.get('extensions'),value.get('status')
            assert [p['name'] for p in value['extensions']['pieces']]==['private-'+name]
            assert str(workspaces[name].root) not in raw and 'BODY MUST NOT BE EXPORTED' not in raw
    finally:service.close()
