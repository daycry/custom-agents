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
