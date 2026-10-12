"""Read-only native activity projection through the existing guarded transport."""
import importlib.util
import json
import os
from pathlib import Path
import socket
import threading
import types

import pytest

ROOT = Path(__file__).resolve().parents[1]
DATA = {'counts': dict.fromkeys(('agents','skills','commands','tools','hooks'), 0),
        'agents':[], 'skills':[], 'commands':[], 'tools':[], 'hooks':[],
        'runtimes':{}, 'memory':{}, 'warnings':[], 'workflow':{'roles':{}}}

@pytest.fixture
def service():
    path = ROOT/'skills/plugin-panel/scripts/serve_panel.py'
    spec = importlib.util.spec_from_file_location('tested_activity_service',path)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def record(event='response_started', observed_at=100):
    return dict(schema_version=1,runtime='codex',scope='subagent',session_key='a'*64,
        agent_key='b'*64,role='implementer',event=event,source='native_hook',
        observed_at=observed_at,revision=1)


def install(service,monkeypatch,records=None,status='ok',reason=None):
    original=service._load_shared; calls=[]
    def snapshot(project):
        calls.append(project)
        return dict(status=status,reason=reason,records=records if records is not None else [record()],collection_complete=False)
    monkeypatch.setattr(service,'_load_shared',lambda name:types.SimpleNamespace(snapshot=snapshot)
        if name=='agent-activity-store.py' else original(name))
    monkeypatch.setattr(service.time,'time',lambda:105)
    return calls


def tree(root):
    return {p.relative_to(root).as_posix():p.read_bytes() if p.is_file() else None for p in root.rglob('*')}


def test_composition_exact_projector_not_liveness_and_no_io(service,tmp_path,monkeypatch):
    calls=install(service,monkeypatch); before=tree(tmp_path)
    result=service.activity_snapshot(tmp_path)
    assert set(result)=={'schema_version','status','reason','complete','collection_complete','observations'}
    assert result['status']=='ok' and result['complete'] is True and result['collection_complete'] is False
    observation,=result['observations']
    assert observation['age_seconds']==5 and observation['state']=='recent_start'
    assert observation['live_process_proven'] is False and observation['agent_destroyed_proven'] is False
    assert calls==[tmp_path] and tree(tmp_path)==before


@pytest.mark.parametrize('reason',['disabled','state_missing','unsafe_state','invalid_state'])
def test_unavailable_is_not_projected_as_verified_empty(service,tmp_path,monkeypatch,reason):
    install(service,monkeypatch,records=[],status='unavailable',reason=reason)
    original=service._load_shared
    monkeypatch.setattr(service,'_load_shared',lambda name: (_ for _ in ()).throw(AssertionError('must not project unavailable'))
        if name=='agent-activity.py' else original(name))
    result=service.activity_snapshot(tmp_path)
    assert result['status']=='unavailable' and result['reason']==reason
    assert result['complete'] is False and result['collection_complete'] is False and result['observations']==[]
    assert tree(tmp_path)=={}


@pytest.mark.parametrize('mutation',['extra','bad_role','boolean_revision','count','duplicate'])
def test_invalid_complete_snapshot_never_leaks_partial_records(service,tmp_path,monkeypatch,mutation):
    rows=[record()]
    if mutation=='extra':rows[0]['prompt']='PRIVATE_TRANSCRIPT'
    elif mutation=='bad_role':rows[0]['role']='<img src=x onerror=alert(1)>'
    elif mutation=='boolean_revision':rows[0]['revision']=True
    elif mutation=='count':rows=rows*65
    else:rows=rows*2
    install(service,monkeypatch,rows)
    result=service.activity_snapshot(tmp_path)
    assert result['status']=='invalid_snapshot' and result['complete'] is False
    assert result['observations']==[] and 'PRIVATE_' not in json.dumps(result)


def test_helper_failure_has_closed_opaque_reason(service,tmp_path,monkeypatch):
    monkeypatch.setattr(service,'_load_shared',lambda name: (_ for _ in ()).throw(ImportError('/PRIVATE_HOME/transcript')))
    result=service.activity_snapshot(tmp_path)
    assert result['status']=='unavailable' and result['reason']=='reader_unavailable'
    assert 'PRIVATE_' not in json.dumps(result) and tree(tmp_path)=={}


def test_exact_sixty_and_future_timestamps_are_unknown(service,tmp_path,monkeypatch):
    install(service,monkeypatch,[record('response_finished',45)])
    assert service.activity_snapshot(tmp_path)['observations'][0]['state']=='unknown'
    install(service,monkeypatch,[record('response_finished',106)])
    result=service.activity_snapshot(tmp_path)['observations'][0]
    assert result['state']=='unknown' and result['age_seconds'] is None


@pytest.fixture
def running(service,tmp_path,monkeypatch):
    calls=install(service,monkeypatch)
    project=tmp_path/'project';project.mkdir(); (project/'neighbor').write_bytes(b'UNTOUCHED')
    before=tree(project)
    server=service.create_server(project,DATA)
    evidence=tmp_path/'http-evidence';evidence.mkdir()
    (evidence/'server.started.json').write_text(json.dumps({'pid':os.getpid(),'port':server.server_port,'host':'127.0.0.1'}))
    thread=threading.Thread(target=server.serve_forever,kwargs={'poll_interval':0.02},daemon=True)
    thread.start()
    try:yield server,calls,evidence
    finally:
        server.shutdown();server.server_close();thread.join(timeout=5)
        (evidence/'server.terminal.json').write_text(json.dumps({'pid':os.getpid(),'port':server.server_port,'thread_terminal':not thread.is_alive(),'socket_closed':server.socket.fileno()==-1}))
        assert not thread.is_alive() and server.socket.fileno()==-1
        assert tree(project)==before


def raw_request(running,method='GET',suffix='api/activity',headers=(),capability=True):
    server,_,evidence=running
    target=(server.access_prefix if capability else '/')+suffix
    base=[('Host',f'127.0.0.1:{server.server_port}')]
    if any(name.lower()=='host' for name,_ in headers):base=[]
    request=(f'{method} {target} HTTP/1.1\r\n'+''.join(f'{k}: {v}\r\n' for k,v in base+list(headers))+'Connection: close\r\n\r\n').encode('ascii')
    raw=b''
    with socket.create_connection(('127.0.0.1',server.server_port),timeout=5) as connection:
        connection.sendall(request)
        while True:
            chunk=connection.recv(65536)
            if not chunk:break
            raw+=chunk
    number=len(list(evidence.glob('*.request.raw')))
    (evidence/f'{number}.request.raw').write_bytes(request);(evidence/f'{number}.response.raw').write_bytes(raw)
    header,body=raw.split(b'\r\n\r\n',1)
    return int(header.split(b' ',2)[1]),header,body


def test_http_exact_endpoint_guarded_headers_and_no_creation(running):
    code,headers,body=raw_request(running)
    assert code==200 and b'Cache-Control: no-store' in headers
    assert b'X-Content-Type-Options: nosniff' in headers and b"connect-src 'self'" in headers
    assert b'Access-Control-Allow-Origin' not in headers and b'Set-Cookie' not in headers
    result=json.loads(body)
    assert result['status']=='ok' and result['collection_complete'] is False and len(body)<=65536
    assert len(running[1])==1 and running[0].access_prefix.encode() not in body


@pytest.mark.parametrize('headers',[[('Host','outside.invalid')],[('Origin','null')],
    [('Origin','https://outside.invalid')],[('Sec-Fetch-Site','cross-site')],
    [('Transfer-Encoding','chunked')],[('Content-Length','1')],
    [('Host','outside.invalid'),('Host','outside.invalid')]])
def test_activity_uses_existing_origin_host_and_body_guard(running,headers):
    assert raw_request(running,headers=headers)[0] in (400,403)
    assert running[1]==[]


@pytest.mark.parametrize('suffix',['api/activity?path=PRIVATE','api/%61ctivity','../api/activity','api/activity/'])
def test_only_literal_activity_route_is_allowed(running,suffix):
    assert raw_request(running,suffix=suffix)[0]==404 and running[1]==[]


def test_no_capability_never_calls_snapshot(running):
    assert raw_request(running,capability=False)[0]==404 and running[1]==[]


@pytest.mark.parametrize('method',['POST','PUT','DELETE','PATCH','OPTIONS'])
def test_activity_has_no_browser_writer(running,method):
    assert raw_request(running,method=method)[0]==405 and running[1]==[]


def test_response_budget_is_enforced_before_serving_any_oversize(running,service,monkeypatch):
    monkeypatch.setattr(service,'activity_snapshot',lambda project:{'PRIVATE':'x'*65537})
    code,_,body=raw_request(running)
    assert code in (200,503) and len(body)<=65536 and b'PRIVATE' not in body
    result=json.loads(body)
    assert result['status']=='unavailable' and result['reason']=='response_budget' and result['complete'] is False
@pytest.mark.parametrize('enabled,reason',[(False,'disabled'),(True,'state_missing')])
def test_exact_owner_read_only_opt_in_no_state_creation(service,tmp_path,enabled,reason):
    if enabled:
        (tmp_path/'.claude').mkdir()
        (tmp_path/'.claude/dev.json').write_text('{"sesion":{"actividad":true}}',encoding='utf-8')
    before=tree(tmp_path)
    result=service.activity_snapshot(tmp_path)
    assert result==dict(schema_version=1,status='unavailable',reason=reason,complete=False,collection_complete=False,observations=[])
    assert tree(tmp_path)==before

def test_exact_owner_positive_snapshot_is_read_only_and_projected(service,tmp_path,monkeypatch):
    import hashlib
    config=tmp_path/'.claude';config.mkdir()
    (config/'dev.json').write_text('{"sesion":{"actividad":true}}',encoding='utf-8')
    state=config/'agent-activity';state.mkdir()
    marker=dict(schema_version=1,owner='custom-agents.agent-activity-v1',scope_id='c'*64,
        root_key=hashlib.sha256(os.path.normcase(os.path.abspath(tmp_path)).encode()).hexdigest())
    (state/'owner.json').write_text(json.dumps(marker),encoding='utf-8')
    (state/'snapshot.json').write_text(json.dumps(dict(schema_version=1,owner=marker['owner'],scope_id=marker['scope_id'],revision=1,records=[record()])),encoding='utf-8')
    (state/'.lock').write_bytes(b'')
    (state/'.gitignore').write_bytes(b'*\n')
    monkeypatch.setattr(service.time,'time',lambda:105)
    before=tree(tmp_path)
    result=service.activity_snapshot(tmp_path)
    assert result['status']=='ok' and result['complete'] is True and result['collection_complete'] is False
    assert result['observations'][0]['state']=='recent_start' and result['observations'][0]['age_seconds']==5
    assert tree(tmp_path)==before
