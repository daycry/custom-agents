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


def test_external_terminal_metadata_is_scoped_without_prompt_or_transcript_access(tmp_path):
    module=api();discover=getattr(module,'discover',None)
    assert callable(discover),'Claude external session discovery is missing'
    calls=[];ident=str(uuid.uuid4())
    def capture(argv,root,**kwargs):
        calls.append((argv,root))
        return [{'cwd':str(tmp_path),'kind':'interactive','sessionId':ident,'startedAt':1000,'pid':123,'name':'Terminal session','prompt':'PRIVATE-CANARY'},
                {'cwd':str(tmp_path/'foreign'),'kind':'interactive','sessionId':str(uuid.uuid4()),'startedAt':1000,'name':'FOREIGN-CANARY'}]
    result=discover(SimpleNamespace(root=tmp_path),capture=capture,command=['native-claude'])
    assert [s['id'] for s in result['sessions']]==[ident]
    assert result['sessions'][0]['read_only'] is True
    assert 'PRIVATE-CANARY' not in str(result) and 'FOREIGN-CANARY' not in str(result)
    argv,root=calls[0]
    assert argv[:3]==['native-claude','agents','--json'] and '--cwd' in argv
    assert '--resume' not in argv and '--print' not in argv and '--all' not in argv
    assert root==tmp_path

def test_external_unnamed_terminal_uses_observed_process_identity_without_claiming_chat_control(tmp_path):
    module=api();discover=getattr(module,'discover',None)
    assert callable(discover),'Claude external session discovery is missing'
    row={'cwd':str(tmp_path),'kind':'interactive','startedAt':1000,'pid':123}
    result=discover(SimpleNamespace(root=tmp_path),capture=lambda *a,**k:[row],command=['native'])
    assert len(result['sessions'])==1
    assert result['sessions'][0]['id'].startswith('observed-')
    assert result['sessions'][0]['status']=='unconfirmed'

def test_external_discovery_failure_never_reports_complete_empty_inventory(tmp_path):
    module=api();discover=getattr(module,'discover',None)
    assert callable(discover),'Claude external session discovery is missing'
    def broken(*args,**kwargs):raise ValueError('PRIVATE-CANARY')
    result=discover(SimpleNamespace(root=tmp_path),capture=broken,command=['native'])
    assert result['status']=='unavailable' and result['complete'] is False
    assert 'PRIVATE-CANARY' not in str(result)


def test_external_inventory_is_bounded_and_invalid_native_shapes_fail_explicitly(tmp_path):
    discover=api().discover
    rows=[{'cwd':str(tmp_path),'kind':'interactive','sessionId':str(uuid.uuid4()),'startedAt':1000} for _ in range(201)]
    result=discover(SimpleNamespace(root=tmp_path),capture=lambda *a,**k:rows,command=['native'])
    assert len(result['sessions'])==200 and result['reason']=='native_inventory_limit' and not result['complete']
    for invalid in ({'agents':[]},[{'cwd':str(tmp_path),'kind':'interactive','sessionId':'invalid','startedAt':1000}]):
        result=discover(SimpleNamespace(root=tmp_path),capture=lambda *a,**k:invalid,command=['native'])
        assert not result['complete'] and result['sessions']==[]


def test_native_background_without_uuid_or_live_pid_keeps_its_native_job_identity(tmp_path):
    value={'cwd':str(tmp_path),'kind':'background','id':'job-one','startedAt':1000,'state':'blocked','name':'Pending background session'}
    result=api().discover(SimpleNamespace(root=tmp_path),capture=lambda *a,**k:[value],command=['native'])
    assert len(result['sessions'])==1,'Valid native background metadata was omitted without UUID/PID'
    assert result['sessions'][0]['id']=='observed-background-job-one'
    assert result['sessions'][0]['read_only'] is True
