"""OpenCode V2 adapter: a private stdio lease and authenticated loopback API."""
import base64
import http.client
import importlib.util
import json
import os
from pathlib import Path
import re
import secrets
import threading
import uuid
from urllib.parse import urlsplit

_spec=importlib.util.spec_from_file_location('console_opencode_common',Path(__file__).with_name('console_common.py'))
C=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(C)
TRANSPORT=C.sibling('console_transport.py')
SESSION=re.compile('ses[A-Za-z0-9_-]{1,150}')

class Client:
    def __init__(self,url,password):
        parsed=urlsplit(url)
        C.need(parsed.scheme=='http' and parsed.hostname=='127.0.0.1' and parsed.port is not None and not parsed.username and not parsed.password
               and parsed.path in ('','/') and not parsed.query and not parsed.fragment,'native_endpoint_invalid',503)
        self.port=parsed.port
        self.authorization='Basic '+base64.b64encode(('opencode:'+password).encode()).decode('ascii')
    def call(self,method,path,data=None,timeout=15):
        C.need(method in ('GET','POST','DELETE') and path.startswith('/api/') and '\r' not in path and '\n' not in path,'invalid_native_operation')
        connection=http.client.HTTPConnection('127.0.0.1',self.port,timeout=timeout)
        try:
            headers={'Authorization':self.authorization,'Accept':'application/json'}
            raw=None
            if data is not None:raw=C.encoded(data);headers['Content-Type']='application/json'
            connection.request(method,path,body=raw,headers=headers)
            response=connection.getresponse();body=response.read(1024*1024+1)
            C.need(len(body)<=1024*1024,'native_output_budget',503)
            C.need(response.status in (200,201,204),'native_http_'+str(response.status),response.status if response.status in (400,401,403,404,409,422) else 503)
            return C.json_load(body) if body else {}
        except (OSError,http.client.HTTPException):raise C.ConsoleError('native_connection_lost',503) from None
        finally:connection.close()

class Driver:
    def __init__(self,workspace,emit,client=None,monitor=True):
        self.workspace,self.emit,self.client=workspace,emit,client
        self.monitor=monitor;self.native_id=None;self.process=None
        self.ready=threading.Event();self.stopped=threading.Event();self.wake=threading.Event()
        self.lock=threading.RLock();self.pending={};self.messages={};self.tool_states={}
        self.password=secrets.token_urlsafe(32);self.inflight=False;self.last_idle=0;self.last_prompt=None;self.own_prompts=set()
        self.monitor_thread=None;self.start_error=None
    def _lease(self,message):
        url=message.get('url')
        if type(url) is str:self.client=Client(url,self.password);self.ready.set()
    def _exit(self,code):
        self.start_error=code;self.ready.set()
        if not self.stopped.is_set():self.emit({'type':'status','status':'disconnected','error':code})
    def _scope(self,session):
        C.need(type(session) is dict and C.same_root((session.get('location') or {}).get('directory'),self.workspace.root),'native_scope_mismatch',403)
        C.need(type(session.get('id')) is str and SESSION.fullmatch(session['id']),'native_identity_missing',503)
    def start(self,resume_id=None):
        if self.client is None:
            env=dict(os.environ);env['OPENCODE_PASSWORD']=self.password;env['OPENCODE_SERVER_PASSWORD']=self.password
            argv=TRANSPORT.executable('opencode',self.workspace.root)+['serve','--stdio','--hostname','127.0.0.1','--port','0']
            self.process=TRANSPORT.LineProcess(argv,self.workspace.root,self._lease,self._exit,env=env)
            self.process.start();C.need(self.ready.wait(30) and self.client is not None and self.start_error is None,'native_start_timeout',503)
        info=self.client.call('GET','/api/info')
        C.need(type(info.get('version')) is str and re.match('^v?2[.]',info['version']),'native_v2_required',503)
        if resume_id:
            C.need(type(resume_id) is str and SESSION.fullmatch(resume_id),'invalid_native_identity')
            result=self.client.call('GET','/api/session/'+resume_id)
        else:result=self.client.call('POST','/api/session',{'title':'custom-agents','location':{'directory':str(self.workspace.root)}})
        session=result.get('data');self._scope(session);self.native_id=session['id']
        self.last_idle=(session.get('time') or {}).get('idle') or 0
        if resume_id:self.refresh()
        if self.monitor:
            self.monitor_thread=threading.Thread(target=self._monitor,daemon=True);self.monitor_thread.start()
        return self.native_id
    def send(self,text):
        with self.lock:
            current=self.client.call('GET','/api/session/'+self.native_id).get('data');self._scope(current)
            self.last_idle=(current.get('time') or {}).get('idle') or 0
            ident='msg_'+uuid.uuid4().hex;self.own_prompts.add(ident);self.last_prompt=ident;self.inflight=True
            result=self.client.call('POST','/api/session/'+self.native_id+'/prompt',{'id':ident,'text':text})
            C.need((result.get('data') or {}).get('id')==ident,'native_admission_unverified',503)
            self.wake.set()
    def message(self,message):
        kind=message.get('type');ident=message.get('id')
        if type(ident) is not str:return
        if kind=='user' and ident not in self.own_prompts and type(message.get('text')) is str:
            text=message['text']
            if self.messages.get(ident)!=text:self.emit({'type':'message','id':ident,'role':'user','text':text});self.messages[ident]=text[:20000]
        elif kind=='assistant':
            content=message.get('content') or []
            text='\n'.join(b['text'] for b in content if type(b) is dict and b.get('type')=='text' and type(b.get('text')) is str)
            if text and self.messages.get(ident)!=text:self.emit({'type':'message','id':ident,'role':'assistant','text':text});self.messages[ident]=text[:20000]
            for block in content:
                if type(block) is not dict or block.get('type')!='tool':continue
                state=(block.get('state') or {}).get('status');tool_id=block.get('id')
                if type(tool_id) is not str:continue
                mapped={'running':'started','streaming':'started','completed':'completed','error':'failed'}.get(state)
                if mapped and self.tool_states.get(tool_id)!=mapped:
                    self.tool_states[tool_id]=mapped
                    self.emit({'type':'tool','id':tool_id,'name':str(block.get('name','Tool')),'state':mapped,'actor':str(message.get('agent',''))})
        elif kind=='skill' and ident not in self.messages:
            self.messages[ident]='skill';self.emit({'type':'tool','id':ident,'name':'Skill: '+str(message.get('name') or message.get('skill','')),'state':'completed','actor':''})
        while len(self.messages)>32:self.messages.pop(next(iter(self.messages)))
        while len(self.tool_states)>200:self.tool_states.pop(next(iter(self.tool_states)))
    def permission(self,request):
        if request.get('sessionID')!=self.native_id:return
        key=request.get('id')
        if type(key) is not str or re.fullmatch('per[A-Za-z0-9_-]{1,150}',key) is None or key in self.pending:return
        C.need(len(self.pending)<8,'native_request_budget',503)
        self.pending[key]={'kind':'permission','request':request}
        preview=json.dumps({'action':request.get('action'),'resources':request.get('resources',[]),'message':request.get('message')},ensure_ascii=False)
        self.emit({'type':'approval','id':key,'title':str(request.get('action','Permiso OpenCode')),'preview':preview,'choices':['allow','deny']})
    def form(self,request):
        if request.get('sessionID')!=self.native_id:return
        key=request.get('id')
        if type(key) is not str or re.fullmatch('frm_[A-Za-z0-9_-]{1,150}',key) is None or key in self.pending:return
        C.need(len(self.pending)<8,'native_request_budget',503)
        fields=request.get('fields') or []
        self.pending[key]={'kind':'form','request':request}
        supported=0<len(fields)<=8 and all(type(f) is dict and f.get('type')=='string' and not f.get('hidden') and not f.get('when') for f in fields)
        if supported:
            self.emit({'type':'question','id':key,'title':request.get('title','Pregunta OpenCode'),'preview':'','choices':['submit','cancel'],
                       'fields':[{'id':f['key'],'label':f.get('title') or f['key'],'options':[o['label'] for o in f.get('options') or []]} for f in fields]})
        else:self.emit({'type':'approval','id':key,'title':'Formulario requiere la interfaz nativa','preview':request.get('title','Formulario avanzado'),'choices':['cancel']})
    def refresh(self):
        with self.lock:
            base='/api/session/'+self.native_id
            result=self.client.call('GET',base);session=result.get('data');self._scope(session)
            active=self.client.call('GET','/api/session/active').get('data') or {}
            history=self.client.call('GET',base+'/message?limit=20&order=desc')
            rows=history.get('data') or [];C.need(type(rows) is list and len(rows)<=20,'native_output_budget',503)
            for message in reversed(rows):
                if type(message) is dict:self.message(message)
            if (history.get('cursor') or {}).get('next'):self.emit({'type':'history','complete':False})
            live=set()
            for endpoint,handler in [('permission',self.permission),('form',self.form)]:
                requests=self.client.call('GET',base+'/'+endpoint).get('data') or []
                C.need(type(requests) is list and len(requests)<=8,'native_request_budget',503)
                for request in requests:
                    if type(request) is dict and request.get('sessionID')==self.native_id:
                        live.add(request.get('id'));handler(request)
            for key in list(self.pending):
                if key not in live:self.pending.pop(key,None);self.emit({'type':'resolved','id':key})
            idle=(session.get('time') or {}).get('idle') or 0
            if self.native_id in active:self.emit({'type':'status','status':'waiting' if self.pending else 'running'})
            elif self.inflight and type(idle) in (int,float) and idle>self.last_idle:
                self.inflight=False;self.last_idle=idle
                self.emit({'type':'status','status':{'succeeded':'idle','failed':'failed','interrupted':'interrupted'}.get(session.get('outcome'),'uncertain')})
    def _monitor(self):
        while not self.stopped.is_set():
            try:self.refresh()
            except Exception as error:
                self.emit({'type':'status','status':'uncertain','error':getattr(error,'code','native_refresh_failed')})
            self.wake.wait(1 if self.inflight else 3);self.wake.clear()
    def answer(self,key,payload):
        with self.lock:
            C.need(key in self.pending,'native_request_not_pending',409)
            item=self.pending[key];base='/api/session/'+self.native_id
            if item['kind']=='permission':
                C.need(payload.get('decision') in ('allow','deny'),'invalid_decision')
                self.client.call('POST',base+'/permission/'+key+'/reply',{'decision':'once' if payload['decision']=='allow' else 'reject'})
            elif 'answers' in payload:
                fields=item['request'].get('fields') or [];answer={}
                for field in fields:
                    value=payload['answers'][field['key']]
                    options=field.get('options') or []
                    matches=[o['value'] for o in options if o['label']==value]
                    C.need(len(matches)<=1,'ambiguous_native_option')
                    answer[field['key']]=matches[0] if matches else value
                self.client.call('POST',base+'/form/'+key+'/reply',{'answer':answer})
            else:
                C.need(payload.get('decision')=='cancel','invalid_decision')
                self.client.call('DELETE',base+'/form/'+key)
            del self.pending[key];self.wake.set()
    def interrupt(self):
        result=self.client.call('POST','/api/session/'+self.native_id+'/interrupt')
        if result.get('interrupted') is True:self.inflight=False;self.emit({'type':'status','status':'interrupted'})
        else:self.emit({'type':'status','status':'uncertain','error':'native_interrupt_no_active_execution'})
        self.wake.set()
    def close(self):
        self.stopped.set();self.wake.set()
        if self.process:self.process.close()
        if self.monitor_thread and self.monitor_thread is not threading.current_thread():self.monitor_thread.join(timeout=2)
