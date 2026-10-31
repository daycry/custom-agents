"""Native protocol boundaries: recovery, human decisions and confirmed outcomes."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import threading

import pytest

ROOT=Path(__file__).resolve().parents[1]
def fixture(name):
 spec=importlib.util.spec_from_file_location('fixture_'+name,ROOT/'tests'/('test_console_'+name+'.py'))
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def test_codex_resume_preserves_order_and_reports_partial_history(tmp_path):
 d,out=fixture('codex').driver(tmp_path);original=d.peer.call
 def call(method,params,timeout=15):
  if method=='thread/items/list':return {'data':[{'item':{'type':'agentMessage','id':'a','text':'Answer'}},{'item':{'type':'userMessage','id':'u','content':[{'type':'text','text':'Question'}]}}],'nextCursor':'older'}
  if method=='skills/list':return {'data':[{'cwd':str(tmp_path),'skills':[{'name':'go-practices'}]}]}
  return original(method,params,timeout)
 d.peer.call=call;assert d.start('thread-one')=='thread-one'
 assert [row['text'] for row in out if row['type']=='message']==['Question','Answer']
 assert {'type':'history','complete':False} in out
 assert out[-1]=={'type':'capabilities','skills':['go-practices']}
 d.peer.call=lambda *args,**kwargs:(_ for _ in ()).throw(OSError())
 d.history();assert out[-1]=={'type':'history','complete':False}
 d.close();assert d.peer.closed

@pytest.mark.parametrize('method,params,payload,expected',[
 ('item/tool/requestUserInput',{'questions':[{'id':'q','question':'Choose','options':[{'label':'A'}]}]}, {'answers':{'q':'A'}},{'answers':{'q':{'answers':['A']}}}),
 ('mcpServer/elicitation/request',{'mode':'form','requestedSchema':{'properties':{'q':{'type':'string','enum':['A']}}}}, {'answers':{'q':'A'}},{'action':'accept','content':{'q':'A'}}),
 ('mcpServer/elicitation/request',{'mode':'url','message':'Use native'}, {'decision':'cancel'},{'action':'cancel','content':None}),
 ('item/permissions/requestApproval',{'permissions':{'fileSystem':{'read':['file']}}}, {'decision':'deny'},{'permissions':{},'scope':'turn'}),
 ('item/fileChange/requestApproval',{'reason':'Write file'}, {'decision':'cancel'},{'decision':'cancel'}),
])
def test_codex_native_human_requests_keep_their_contract(tmp_path,method,params,payload,expected):
 d,out=fixture('codex').driver(tmp_path);d.start()
 d.handle({'id':7,'method':method,'params':{'threadId':'thread-one',**params}})
 assert out[-1]['type'] in ('question','approval')
 d.answer('7',payload);assert d.peer.sent[-1]=={'id':7,'result':expected}
 with pytest.raises(ValueError):d.answer('7',payload)

def test_codex_resolves_native_requests_and_refuses_unknown_operations(tmp_path):
 d,out=fixture('codex').driver(tmp_path);d.start()
 d.handle({'id':9,'method':'unsupported/request','params':{'threadId':'thread-one'}})
 assert d.peer.sent[-1]['error']['code']==-32601 and '9' not in d.pending
 d.handle({'method':'item/started','params':{'threadId':'thread-one','item':{'type':'mcpToolCall','id':'tool','server':'repo','tool':'read'}}})
 d.handle({'method':'item/completed','params':{'threadId':'thread-one','item':{'type':'fileChange','id':'write','status':'declined'}}})
 assert [row['state'] for row in out if row['type']=='tool']==['started','failed']
 d.pending['12']={};d.handle({'method':'serverRequest/resolved','params':{'threadId':'thread-one','requestId':12}})
 assert '12' not in d.pending and out[-1]=={'type':'resolved','id':'12'}
 d._exit('native_closed');assert out[-1]['status']=='disconnected'

def test_claude_streaming_tools_and_interrupt_use_native_completion(tmp_path):
 d,out=fixture('claude').driver(tmp_path);ident=d.start();out.clear()
 d.handle({'type':'system','subtype':'init','cwd':str(tmp_path),'session_id':ident,'tools':['Read'],'skills':['go'],'agents':['reviewer'],'mcp_servers':[{'name':'docs'}]})
 assert out[-1]['mcp']==['docs']
 for event in [{'type':'message_start','message':{'id':'m'}},
               {'type':'content_block_start','index':0,'content_block':{'type':'text'}},
               {'type':'content_block_delta','index':0,'delta':{'type':'text_delta','text':'Visible'}},
               {'type':'content_block_start','index':1,'content_block':{'type':'tool_use','id':'t','name':'Read'}}]:
  d.handle({'type':'stream_event','event':event})
 assert any(row.get('text')=='Visible' and row['delta'] for row in out)
 d.handle({'type':'assistant','message':{'content':[{'type':'tool_use','id':'agent','name':'Agent','input':{'subagent_type':'reviewer'}}]}})
 assert out[-1]['actor']=='reviewer'
 d.handle({'type':'user','message':{'content':[{'type':'tool_result','tool_use_id':'t','is_error':True}]}})
 assert out[-1]['state']=='failed'
 d.interrupt();assert out[-1].get('status')!='interrupted'
 d.handle({'type':'result','subtype':'error_during_execution','is_error':True})
 assert out[-1]['status']=='interrupted'
 d.close();assert d.process.closed

def test_claude_control_failure_and_cancellation_are_observable(tmp_path):
 d,out=fixture('claude').driver(tmp_path)
 with pytest.raises(ValueError,match='invalid_native_identity'):d.start('not-a-uuid')
 d.start();d.process.send=lambda message:None
 with pytest.raises(ValueError,match='native_request_timeout'):d._control({'subtype':'interrupt'},timeout=.001)
 assert d.controls=={}
 d.process.send=lambda message:d._exit('native_closed')
 with pytest.raises(ValueError,match='native_request_failed'):d._control({'subtype':'interrupt'},timeout=.1)
 assert out[-1]['status']=='disconnected' and d.controls=={}
 d,out=fixture('claude').driver(tmp_path);d.start()
 d.handle({'type':'control_request','request_id':'unsupported','request':{'subtype':'other'}})
 assert d.process.sent[-1]['response']['subtype']=='error'
 d.handle({'type':'control_request','request_id':'r','request':{'subtype':'can_use_tool','tool_name':'Write','input':{'path':'file'}}})
 d.answer('r',{'decision':'deny'});assert d.process.sent[-1]['response']['response']['behavior']=='deny'
 d.handle({'type':'control_cancel_request','request_id':'cancelled'})
 assert out[-1]=={'type':'resolved','id':'cancelled'}

def test_opencode_polling_tracks_human_requests_and_confirmed_outcomes(tmp_path):
 d,c,out=fixture('opencode').driver(tmp_path);d.start();d.send('Question')
 original=c.call;active=True;request=True;idle=1
 def call(method,path,data=None,timeout=15):
  if path=='/api/session/active':return {'data':{'ses_one':{}} if active else {}}
  if path.endswith('/permission'):return {'data':[{'id':'per_1','sessionID':'ses_one','action':'write'}] if request else []}
  value=original(method,path,data,timeout)
  if path=='/api/session/ses_one':value['data']['time']['idle']=idle
  if '/message?' in path:return {'data':[{'id':'u','type':'user','text':'Question'},{'id':'s','type':'skill','name':'go'}],'cursor':{'next':'older'}}
  return value
 c.call=call;d.refresh();assert out[-1]['status']=='waiting'
 assert {'type':'history','complete':False} in out
 d.answer('per_1',{'decision':'deny'});assert c.calls[-1][-1]=={'decision':'reject'}
 request=False;active=False;idle=2;d.refresh();assert out[-1]['status']=='idle' and not d.inflight
 d.permission({'id':'per_2','sessionID':'ses_one','action':'read'});d.refresh()
 assert {'type':'resolved','id':'per_2'} in out
 d.message({'id':'own','type':'user','text':'Duplicate'});before=len(out);d.message({'id':'own','type':'user','text':'Duplicate'});assert len(out)==before

def test_opencode_forms_translate_labels_and_allow_safe_cancellation(tmp_path):
 d,c,out=fixture('opencode').driver(tmp_path);d.native_id='ses_one'
 request={'id':'frm_one','sessionID':'ses_one','fields':[{'key':'q','type':'string','title':'Choose','options':[{'label':'A','value':'native-A'}]}]}
 d.form(request);assert out[-1]['type']=='question'
 d.answer('frm_one',{'answers':{'q':'A'}});assert c.calls[-1][-1]=={'answer':{'q':'native-A'}}
 d.form(request);d.answer('frm_one',{'decision':'cancel'});assert c.calls[-1][0]=='DELETE'
 d.form({**request,'fields':[{'key':'q','type':'number'}]});assert out[-1]['choices']==['cancel']
 d.answer('frm_one',{'decision':'cancel'})
 original=c.call;c.call=lambda *args,**kwargs:{'interrupted':False}
 d.interrupt();assert out[-1]['status']=='uncertain'
 c.call=original;d._exit('native_closed');assert out[-1]['status']=='disconnected'

def test_opencode_native_client_enforces_loopback_auth_and_response_limits(monkeypatch):
 m=fixture('opencode').api()
 with pytest.raises(ValueError):m.Client('http://example.invalid:80','secret')
 state={'body':b'{"data":[]}','status':200,'closed':False}
 class Connection:
  def __init__(self,host,port,timeout):assert host=='127.0.0.1' and port==1234
  def request(self,method,path,body,headers):
   assert headers['Authorization'].startswith('Basic ') and path.startswith('/api/')
   if method=='POST':assert json.loads(body)=={'text':'literal'}
  def getresponse(self):return SimpleNamespace(status=state['status'],read=lambda size:state['body'][:size])
  def close(self):state['closed']=True
 monkeypatch.setattr(m.http.client,'HTTPConnection',Connection);client=m.Client('http://127.0.0.1:1234','secret')
 assert client.call('POST','/api/session',{'text':'literal'})=={'data':[]} and state['closed']
 state['status']=403
 with pytest.raises(ValueError,match='native_http_403'):client.call('GET','/api/info')
 state['status']=200;state['body']=b'x'*(1024*1024+1)
 with pytest.raises(ValueError,match='native_output_budget'):client.call('GET','/api/info')
 with pytest.raises(ValueError):client.call('GET','/outside')
