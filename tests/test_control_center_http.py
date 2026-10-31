"""One local console port, authenticated API and workspace-specific plans."""
import hashlib
import http.client
import importlib.util
import json
from pathlib import Path
import threading

import pytest

ROOT=Path(__file__).resolve().parents[1]
SCRIPTS=ROOT/'skills/plugin-panel/scripts'

def load(name):
    path=SCRIPTS/name
    assert path.is_file(), 'shared control center is not implemented'
    spec=importlib.util.spec_from_file_location('http_test_'+name.replace('.','_'),path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

@pytest.fixture
def server(tmp_path):
    workspace=load('console_workspaces.py');workspaces={}
    for name in ['one','two']:
        root=tmp_path/name;folder=root/'docs/roadmap/2026-10-31-pilot';folder.mkdir(parents=True)
        (folder/'improvement-plan.md').write_text('# '+name,encoding='utf-8')
        (folder/'tasks.md').write_text('# Plan '+name+'\n\n## Fase 1\n\n### T-01 — '+name+' only\n\n- **Estado**: borrador\n- **Tipo**: backend\n- **Descripción**: Build\n',encoding='utf-8')
        workspaces[name]=workspace.Workspace(name,name,root,())
    http=load('control_center.py');s=http.create_server(workspaces,port=0)
    thread=threading.Thread(target=s.serve_forever,daemon=True);thread.start()
    yield s
    s.shutdown();s.server_close();thread.join(timeout=5)

def request(server,path,method='GET',data=None,cookie=None,headers=None):
    connection=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=10)
    h={'Origin':f'http://127.0.0.1:{server.server_port}'}
    if cookie:
        h['Cookie']=cookie
        h['Authorization']='Bearer '+server.token
    if data is not None:h['Content-Type']='application/json'
    h.update(headers or {})
    connection.request(method,path,body=json.dumps(data) if data is not None else None,headers=h)
    response=connection.getresponse();body=response.read();status=response.status;heads=dict(response.getheaders());connection.close()
    return status,heads,body

def login(server):
    status,headers,_=request(server,'/api/bootstrap','POST',{'token':server.token})
    assert status==200
    return headers['Set-Cookie'].split(';')[0]

def test_api_requires_capability_and_cookie_is_http_only(server):
    assert request(server,'/api/workspaces')[0]==401
    assert request(server,'/api/bootstrap','POST',{'token':'wrong'})[0]==403
    status,headers,_=request(server,'/api/bootstrap','POST',{'token':server.token})
    assert status==200 and 'HttpOnly' in headers['Set-Cookie'] and 'SameSite=Strict' in headers['Set-Cookie']
    cookie=headers['Set-Cookie'].split(';')[0]
    status,headers,body=request(server,'/api/workspaces',cookie=cookie)
    assert status==200 and [w['id'] for w in json.loads(body)['workspaces']]==['one','two']
    assert server.token.encode() not in body and str(server.workspaces['one'].root).encode() not in body
    assert headers['Cache-Control']=='no-store' and 'Access-Control-Allow-Origin' not in headers

def test_workspace_plans_and_comments_are_independent_on_one_port(server):
    cookie=login(server);plan=hashlib.sha256(b'2026-10-31-pilot').hexdigest()[:16]
    one=request(server,'/api/workspaces/one/plans/'+plan,cookie=cookie)
    two=request(server,'/api/workspaces/two/plans/'+plan,cookie=cookie)
    assert one[0]==two[0]==200
    assert 'one only' in one[2].decode() and 'two only' not in one[2].decode()
    path='/api/workspaces/one/plans/'+plan+'/tasks/T-01/comments'
    assert request(server,path,'POST',{'text':'one private note','expected_revision':0,'request_id':'a'*32},cookie)[0]==200
    assert 'one private note' in request(server,path,cookie=cookie)[2].decode()
    assert 'one private note' not in request(server,path.replace('/one/','/two/'),cookie=cookie)[2].decode()

def test_foreign_origin_host_and_arbitrary_paths_are_rejected(server):
    cookie=login(server)
    for headers in [{'Origin':'https://outside.invalid'},{'Host':'outside.invalid'},{'Sec-Fetch-Site':'cross-site'}]:
        assert request(server,'/api/workspaces',cookie=cookie,headers=headers)[0]==403
    for path in ['/api/workspaces/missing/plans','/.claude/settings.json','/api/workspaces/one/../two/plans','/api/workspaces/one/plans?root=private']:
        assert request(server,path,cookie=cookie)[0] in (400,404)

def test_missing_task_cannot_receive_a_comment(server):
    cookie=login(server);plan=hashlib.sha256(b'2026-10-31-pilot').hexdigest()[:16]
    path='/api/workspaces/one/plans/'+plan+'/tasks/T-99/comments'
    assert request(server,path,'POST',{'text':'bad','expected_revision':0,'request_id':'a'*32},cookie)[0]==404

def test_activity_is_an_explicit_snapshot_when_capture_is_disabled(server):
    cookie=login(server)
    status,_,raw=request(server,'/api/workspaces/one/activity',cookie=cookie)
    value=json.loads(raw)
    assert status==200 and isinstance(value,dict)
    assert value['runs']==[] and value['status']=='unavailable'
    assert value['reason']=='disabled' and value['collection_complete'] is False


def test_slow_portfolio_never_blocks_another_project_http_view(server,monkeypatch):
    import time
    cookie=login(server);release=threading.Event();calls=[]
    module=load('console_service.py')
    # Patch the actual service reader, not a separate imported module instance.
    data=server.service.plans.__func__.__globals__['DATA']
    def slow(root):
        calls.append(root.name)
        if root.name=='one':release.wait(timeout=3)
        return {'status':'ok','complete':True,'iniciativas':[],'observed_at':'2026-10-31T00:00:00Z'}
    monkeypatch.setattr(data,'cartera',slow)
    try:
        start=time.monotonic()
        for _ in range(4):
            status,_,raw=request(server,'/api/workspaces/one/plans',cookie=cookie)
            assert status==200 and json.loads(raw)['status']=='calculating'
        assert time.monotonic()-start<1.0
        deadline=time.monotonic()+2
        while time.monotonic()<deadline:
            status,_,raw=request(server,'/api/workspaces/two/plans',cookie=cookie)
            if json.loads(raw)['status']=='ok':break
            time.sleep(.01)
        assert status==200 and json.loads(raw)['status']=='ok'
        assert calls.count('one')==1 and calls.count('two')==1
    finally:release.set()

def test_prepare_plan_is_read_only_and_stale_context_cannot_start_a_session(server):
    cookie=login(server);plan=hashlib.sha256(b'2026-10-31-pilot').hexdigest()[:16]
    path='/api/workspaces/one/plans/'+plan+'/prepare'
    status,_,body=request(server,path,'POST',{'action':'continue','task':None},cookie)
    assert status==200
    preview=json.loads(body)
    assert 'prompt' in preview and len(preview['context_sha256'])==64
    assert not (server.workspaces['one'].root/'.claude/control-center').exists()
    task=server.workspaces['one'].root/'docs/roadmap/2026-10-31-pilot/tasks.md'
    task.write_text(task.read_text().replace('Build','Changed'))
    result=request(server,path.replace('/prepare','/run'),'POST',{'action':'continue','task':None,'context_sha256':preview['context_sha256'],'session_id':'b'*32,'request_id':'c'*32},cookie)
    assert result[0]==409


def test_cookie_from_another_local_port_cannot_authenticate_without_the_header_capability(server):
    cookie=login(server)
    assert server.token not in cookie
    assert request(server,'/api/workspaces',cookie=cookie,headers={'Authorization':'Bearer wrong'})[0]==401
    assert request(server,'/api/workspaces',cookie=cookie,headers={'Authorization':''})[0]==401


def test_integrations_view_never_exports_unvalidated_backend_settings(server):
    root=server.workspaces['one'].root
    config=root/'.claude/knowledge-services';config.mkdir(parents=True)
    secret='private-value-in-wrong-mode'
    (config/'taxonomy.json').write_text(json.dumps({'backends':{'graphiti':{'type':'graphiti','enabled':False,'config':{'mode':{'private':secret}}}}}))
    cookie=login(server)
    status,_,body=request(server,'/api/workspaces/one/integrations',cookie=cookie)
    assert status==200 and secret not in body.decode()
    assert json.loads(body)['memory_services'][0]['mode'] is None

@pytest.mark.parametrize('contents',[
    '{"backends":{"graphiti":42}}','x'*66000,
    '{"backends":[]}','{"backends":false}','{"backends":0}','{"backends":""}','{"backends":null}',
],ids=['invalid-backend','oversized-config','empty-array','false','zero','empty-string','null'])
def test_unreadable_or_malformed_memory_declarations_are_visible(server,contents):
    config=server.workspaces['one'].root/'.claude/knowledge-services';config.mkdir(parents=True)
    (config/'taxonomy.json').write_text(contents,encoding='utf-8');cookie=login(server)
    status,_,raw=request(server,'/api/workspaces/one/integrations',cookie=cookie)
    assert status==200 and {'status':'invalid_configuration'} in json.loads(raw)['memory_services']

def test_document_memory_and_runtime_views_keep_missing_data_explicit(server):
    cookie=login(server);plan=hashlib.sha256(b'2026-10-31-pilot').hexdigest()[:16]
    status,_,raw=request(server,'/api/workspaces/one/plans/'+plan+'/documents/plan',cookie=cookie)
    assert status==200 and json.loads(raw)['text']=='# one'
    assert request(server,'/api/workspaces/one/plans/'+plan+'/documents/spec',cookie=cookie)[0]==404
    status,_,raw=request(server,'/api/workspaces/one/runtimes',cookie=cookie)
    assert status==200 and len(json.loads(raw)['runtimes'])==3
    assert all(not row['enabled'] and row['capabilities']['desktop_window_control'] is False for row in json.loads(raw)['runtimes'])
    status,_,raw=request(server,'/api/workspaces/one/memory/query','POST',{'operation':'search','text':'missing'},cookie)
    assert status==200 and json.loads(raw)['entries']==[]
    assert request(server,'/api/workspaces/one/memory/query','POST',{'operation':'publish','text':'unsafe'},cookie)[0]==400
    for method in ['PUT','DELETE','PATCH','OPTIONS']:
        assert request(server,'/api/workspaces',method,cookie=cookie)[0]==405
    status,headers,body=request(server,'/assets/console-dom.js',method='HEAD')
    assert status==200 and not body and int(headers['Content-Length'])>0

def test_prepare_selected_task_includes_local_notes_and_requires_fresh_sources(server):
    cookie=login(server);plan=hashlib.sha256(b'2026-10-31-pilot').hexdigest()[:16]
    base='/api/workspaces/one/plans/'+plan
    payload={'text':'Please check the error path','expected_revision':0,'request_id':'a'*32}
    assert request(server,base+'/tasks/T-01/comments','POST',payload,cookie)[0]==200
    status,_,raw=request(server,base+'/prepare','POST',{'action':'review','task':'T-01'},cookie)
    assert status==200 and 'Please check the error path' in json.loads(raw)['prompt']
    assert request(server,base+'/prepare','POST',{'action':'approve','task':'T-01'},cookie)[0]==400
    folder=server.workspaces['one'].root/'docs/roadmap/2026-10-31-pilot'
    (folder/'improvement-plan.md').unlink()
    assert request(server,base+'/prepare','POST',{'action':'continue','task':None},cookie)[0]==503

def test_native_session_routes_use_the_registered_project_and_single_use_controls(server):
    import time
    class Native:
        def __init__(self,workspace,runtime,emit):self.emit=emit;self.closed=False
        def start(self,resume_id=None):return resume_id or 'native-one'
        def send(self,text):self.emit({'type':'status','status':'running'})
        def interrupt(self):self.emit({'type':'status','status':'interrupted'})
        def answer(self,key,payload):self.emit({'type':'status','status':'idle'})
        def close(self):self.closed=True
    server.workspaces['one'].runtimes=('codex',)
    manager=server.service.sessions;manager.factory=Native;cookie=login(server)
    base='/api/workspaces/one/sessions'
    status,_,raw=request(server,base,'POST',{'runtime':'codex','title':'Test','request_id':'a'*32},cookie)
    assert status==200;ident=json.loads(raw)['id'];path=base+'/'+ident
    def settled(expected):
        deadline=time.monotonic()+3
        while time.monotonic()<deadline:
            status,_,body=request(server,path,cookie=cookie);value=json.loads(body)
            if value.get('status')==expected:return value
            time.sleep(.01)
        pytest.fail('native fixture did not settle')
    settled('idle')
    assert request(server,base,cookie=cookie)[0]==200
    assert request(server,path+'/messages','POST',{'text':'Test','request_id':'b'*32},cookie)[0]==200
    settled('running')
    assert request(server,path+'/interrupt','POST',{},cookie)[0]==200;settled('interrupted')
    manager.emit(ident,{'type':'approval','id':'r','title':'Choose','preview':'file.txt','choices':['deny']})
    assert request(server,path+'/answer','POST',{'request_id':'r','response':{'decision':'deny'}},cookie)[0]==200
    assert request(server,path+'/answer','POST',{'request_id':'r','response':{'decision':'deny'}},cookie)[0]==409
    assert request(server,path+'/disconnect','POST',{},cookie)[0]==200;settled('disconnected')
    assert request(server,path+'/resume','POST',{},cookie)[0]==200;settled('idle')
    assert request(server,path.replace('/one/','/two/'),cookie=cookie)[0]==404
