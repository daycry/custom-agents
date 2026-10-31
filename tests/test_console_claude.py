"""Claude control messages are scoped to one owned stream-json process."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import uuid

import pytest

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/'skills/plugin-panel/scripts/console_claude.py'

def api():
    assert PATH.is_file(), 'Claude console adapter is not implemented'
    spec=importlib.util.spec_from_file_location('tested_console_claude',PATH)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

class Process:
    def __init__(self,argv,cwd,receive,on_exit,env=None):
        self.argv,self.cwd,self.receive=argv,cwd,receive;self.sent=[];self.closed=False
    def start(self):pass
    def send(self,message):
        self.sent.append(message)
        if message.get('type')=='control_request':
            self.receive({'type':'control_response','response':{'subtype':'success','request_id':message['request_id'],'response':{}}})
    def close(self):self.closed=True

def driver(tmp_path):
    out=[];d=api().Driver(SimpleNamespace(root=tmp_path,id='one'),out.append,process_factory=Process,command=['fake-native'])
    return d,out

def test_create_and_send_use_stream_json_without_shell_prompts_or_bypass(tmp_path):
    d,out=driver(tmp_path);ident=d.start();uuid.UUID(ident)
    assert '--input-format' in d.process.argv and 'stream-json' in d.process.argv
    assert not any('bypass' in arg or 'skip-permissions' in arg for arg in d.process.argv)
    d.send('hello & echo should be text')
    assert d.process.sent[-1]['type']=='user'
    assert d.process.sent[-1]['message']['content']=='hello & echo should be text'

def test_tool_permission_uses_original_input_and_explicit_response(tmp_path):
    d,out=driver(tmp_path);d.start();out.clear()
    d.handle({'type':'control_request','request_id':'r1','request':{'subtype':'can_use_tool','tool_name':'Write','input':{'file_path':'notes.txt','content':'hello'}}})
    assert out[-1]['type']=='approval'
    d.answer('r1',{'decision':'allow'})
    assert d.process.sent[-1]=={'type':'control_response','response':{'subtype':'success','request_id':'r1','response':{'behavior':'allow','updatedInput':{'file_path':'notes.txt','content':'hello'}}}}

def test_thinking_is_ignored_and_failed_result_is_not_green(tmp_path):
    d,out=driver(tmp_path);d.start();out.clear()
    d.handle({'type':'assistant','message':{'id':'m1','content':[{'type':'thinking','thinking':'private thought'},{'type':'text','text':'visible'}]}})
    d.handle({'type':'result','subtype':'success','is_error':True,'result':'API Error'})
    assert out[0]=={'type':'message','id':'m1','role':'assistant','text':'visible'}
    assert out[-1]['status']=='failed'
    assert 'private thought' not in str(out)

def test_foreign_directory_in_init_is_not_accepted(tmp_path):
    d,out=driver(tmp_path);d.start()
    with pytest.raises(ValueError):d.handle({'type':'system','subtype':'init','cwd':str(tmp_path/'foreign'),'session_id':d.native_id})

def test_user_question_returns_answers_without_running_a_tool_automatically(tmp_path):
    d,out=driver(tmp_path);d.start();out.clear()
    d.handle({'type':'control_request','request_id':'r2','request':{'subtype':'can_use_tool','tool_name':'AskUserQuestion','input':{'questions':[{'question':'Which option?','options':[{'label':'One'},{'label':'Two'}]}]}}})
    assert out[-1]['type']=='question' and out[-1]['fields'][0]['id']=='q-0'
    d.answer('r2',{'answers':{'q-0':'One'}})
    assert d.process.sent[-1]['response']['response']['updatedInput']['answers']=={'Which option?':'One'}
