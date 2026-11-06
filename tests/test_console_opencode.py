"""OpenCode V2 API fixtures are pinned to its 2.0.12 published protocol."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/'skills/plugin-panel/scripts/console_opencode.py'

def api():
    assert PATH.is_file(), 'OpenCode V2 console adapter is not implemented'
    spec=importlib.util.spec_from_file_location('tested_console_opencode',PATH)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

class Client:
    def __init__(self,root):self.root=root;self.calls=[];self.foreign=False
    def call(self,method,path,data=None,timeout=15):
        self.calls.append((method,path,data))
        if path=='/api/info':return {'version':'2.0.12'}
        if path=='/api/session' or path=='/api/session/ses_one':return {'data':{'id':'ses_one','location':{'directory':str(self.root/'foreign' if self.foreign else self.root)},'time':{'idle':1},'outcome':'succeeded'}}
        if path.endswith('/prompt'):return {'data':{'id':data['id']}}
        if path.endswith('/interrupt'):return {'interrupted':True}
        if '/message?' in path:return {'data':[],'cursor':{}}
        return {'data':[]}

def driver(tmp_path):
    out=[];client=Client(tmp_path)
    d=api().Driver(SimpleNamespace(root=tmp_path,id='one'),out.append,client=client,monitor=False)
    return d,client,out

def test_v2_creation_and_prompt_use_location_and_durable_admission(tmp_path):
    d,c,out=driver(tmp_path);assert d.start()=='ses_one';d.send('hello & echo literal')
    created=next(p for m,path,p in c.calls if m=='POST' and path=='/api/session')
    assert created['location']=={'directory':str(tmp_path)}
    prompt=next(p for m,path,p in c.calls if path.endswith('/prompt'))
    assert prompt['text']=='hello & echo literal' and prompt['id'].startswith('msg_')
    assert not any('/shell' in path for _,path,_ in c.calls)
    d.close()

def test_foreign_session_is_rejected_before_prompt_or_history(tmp_path):
    d,c,out=driver(tmp_path);c.foreign=True
    with pytest.raises(ValueError):d.start('ses_one')
    assert not any('/message' in path or path.endswith('/prompt') for _,path,_ in c.calls)
    d.close()

def test_messages_keep_native_text_and_tool_states_but_ignore_reasoning(tmp_path):
    d,c,out=driver(tmp_path);d.native_id='ses_one'
    d.message({'id':'msg_1','type':'assistant','agent':'implementer','content':[
      {'type':'reasoning','text':'private thought'}, {'type':'text','text':'visible'},
      {'type':'tool','id':'tool1','name':'read','state':{'status':'completed'}}]})
    assert out[0]=={'type':'message','id':'msg_1','role':'assistant','text':'visible'}
    assert out[1]['name']=='read' and out[1]['state']=='completed'
    assert 'private thought' not in str(out)

def test_permission_reply_is_once_or_reject_never_always(tmp_path):
    d,c,out=driver(tmp_path);d.native_id='ses_one'
    d.permission({'id':'per_one','sessionID':'ses_one','action':'write','resources':['file.txt']})
    assert out[-1]['choices']==['allow','deny']
    d.answer('per_one',{'decision':'allow'})
    assert c.calls[-1]==('POST','/api/session/ses_one/permission/per_one/reply',{'decision':'once'})
    d.close()

def test_interrupt_uses_v2_result_without_fabricating_success(tmp_path):
    d,c,out=driver(tmp_path);d.native_id='ses_one';d.interrupt()
    assert c.calls[-1][1]=='/api/session/ses_one/interrupt'
    assert out[-1]['status']=='interrupted'
    d.close()


def test_external_inventory_uses_get_metadata_only_with_exact_project_scope_and_cleanup(tmp_path):
    module=api();discover=getattr(module,'discover',None)
    assert callable(discover),'OpenCode external session discovery is missing'
    class InventoryClient(Client):
        def call(self,method,path,data=None,timeout=15):
            if path.startswith('/api/session?'):
                self.calls.append((method,path,data))
                return {'data':[{'id':'ses_one','title':'Native terminal','location':{'directory':str(tmp_path)},'time':{'created':1000,'updated':2000},'messages':['PRIVATE-CANARY']}], 'cursor':{}}
            return super().call(method,path,data,timeout)
    client=InventoryClient(tmp_path)
    result=discover(SimpleNamespace(root=tmp_path),client=client)
    assert [row['id'] for row in result['sessions']]==['ses_one']
    assert result['complete'] is True and result['sessions'][0]['read_only'] is True
    assert all(method=='GET' for method,_,_ in client.calls)
    assert not any('/message' in path for _,path,_ in client.calls)
    from urllib.parse import urlsplit,parse_qs
    query=parse_qs(urlsplit(client.calls[-1][1]).query)
    assert query['directory']==[str(tmp_path)] and query['archived']==['false']
    assert 'PRIVATE-CANARY' not in str(result)

def test_external_inventory_cursor_or_wrong_scope_reports_partial_and_never_adopts(tmp_path):
    module=api();discover=getattr(module,'discover',None)
    assert callable(discover),'OpenCode external session discovery is missing'
    class InventoryClient(Client):
        def call(self,method,path,data=None,timeout=15):
            if path.startswith('/api/session?'):
                return {'data':[{'id':'ses_foreign','title':'FOREIGN-CANARY','location':{'directory':str(tmp_path/'foreign')}}], 'cursor':{'next':'more'}}
            return super().call(method,path,data,timeout)
    result=discover(SimpleNamespace(root=tmp_path),client=InventoryClient(tmp_path))
    assert result['sessions']==[] and result['complete'] is False and result['status']!='ok'
    assert 'FOREIGN-CANARY' not in str(result)


def test_external_inventory_owns_and_closes_lease_without_creating_session(tmp_path,monkeypatch):
    module=api();client=Client(tmp_path);processes=[]
    original=client.call
    def call(method,path,data=None,timeout=15):
        if path.startswith('/api/session?'):
            client.calls.append((method,path,data));return {'data':[],'cursor':{}}
        return original(method,path,data,timeout)
    client.call=call
    monkeypatch.setattr(module,'Client',lambda url,password:client)
    class Process:
        def __init__(self,argv,cwd,message,exit,env=None):
            self.argv=argv;self.message=message;self.closed=False;processes.append(self)
        def start(self):self.message({'url':'http://127.0.0.1:12345'})
        def close(self):self.closed=True
    monkeypatch.setattr(module.TRANSPORT,'executable',lambda *a:['native-opencode'])
    result=module.discover(SimpleNamespace(root=tmp_path),process_factory=Process)
    assert result['complete'] and result['sessions']==[]
    assert len(processes)==1 and processes[0].closed
    assert processes[0].argv[1:]==['serve','--stdio','--hostname','127.0.0.1','--port','0']
    assert all(method=='GET' for method,_,_ in client.calls)
