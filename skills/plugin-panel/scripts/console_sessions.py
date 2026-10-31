"""Workspace-bound native sessions. Chat is bounded process memory, never an export."""
from collections import deque
import copy
from datetime import datetime,timezone
import hashlib
import importlib.util
from pathlib import Path
import re
import threading
import uuid

_spec=importlib.util.spec_from_file_location('console_sessions_common',Path(__file__).with_name('console_common.py'))
C=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(C)
STATE=C.sibling('console_state.py')
KEY=re.compile('[a-f0-9]{32}')
NATIVE=re.compile('[A-Za-z0-9_.:-]{1,160}')
BUSY={'connecting','sending','queued','running','waiting','interrupting','disconnecting'}
STATES=BUSY|{'idle','failed','interrupted','uncertain','disconnected'}

def now():return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')

def native_factory(workspace,runtime,emit):
    module=C.sibling({'codex':'console_codex.py','claude-code':'console_claude.py','opencode':'console_opencode.py'}[runtime])
    return module.Driver(workspace,emit)

class Session:
    def __init__(self,workspace,runtime,title,key,ident=None,native_id=None,created_at=None):
        self.id=ident or uuid.uuid4().hex;self.workspace=workspace
        self.runtime,self.title,self.create_key=runtime,title,key
        self.native_id=native_id;self.created_at=created_at or now();self.updated_at=now()
        self.status='disconnected';self.error=None;self.driver=None
        self.messages=deque(maxlen=20);self.events=deque(maxlen=200)
        self.buffers={};self.pending={};self.sent={};self.truncated=False
        self.seq=0;self.capabilities={};self.closed=False;self.generation=0
    def metadata(self):
        return {'id':self.id,'runtime':self.runtime,'title':self.title,'create_key':self.create_key,
                'native_id':self.native_id,'created_at':self.created_at}
    def summary(self):
        return {'id':self.id,'workspace':self.workspace,'runtime':self.runtime,'title':self.title,
                'status':self.status,'created_at':self.created_at,'updated_at':self.updated_at,
                'error':self.error,'native_id':self.native_id,'seq':self.seq,
                'can_resume':self.native_id is not None and self.driver is None,
                'can_disconnect':self.driver is not None and self.status not in BUSY}

class SessionManager:
    def __init__(self,workspaces,factory=None):
        self.workspaces=workspaces;self.factory=factory or native_factory
        self.lock=threading.RLock();self.sessions={};self.errors={};self.threads=set();self.closed=False
        for workspace in workspaces.values():
            try:
                data,_=STATE.Store(workspace.root).read('sessions.json',{'sessions':[]})
                C.need(type(data) is dict and set(data)=={'sessions'} and type(data['sessions']) is list and len(data['sessions'])<=128,'invalid_sessions',409)
                for record in data['sessions']:
                    C.need(type(record) is dict and set(record)=={'id','runtime','title','create_key','native_id','created_at'},'invalid_sessions',409)
                    C.need(type(record['id']) is str and KEY.fullmatch(record['id']) and record['id'] not in self.sessions and type(record['create_key']) is str and KEY.fullmatch(record['create_key']),'invalid_sessions',409)
                    C.need(record['runtime'] in workspace.runtimes and type(record['title']) is str and len(record['title'])<=100 and type(record['created_at']) is str and len(record['created_at'])<=40,'invalid_sessions',409)
                    C.need(record['native_id'] is None or type(record['native_id']) is str and NATIVE.fullmatch(record['native_id']),'invalid_sessions',409)
                    session=Session(workspace.id,record['runtime'],C.scrub(record['title'],workspace.root,100),record['create_key'],record['id'],record['native_id'],record['created_at'])
                    self.sessions[session.id]=session
            except Exception:
                self.errors[workspace.id]='session_state_unavailable'
                self.sessions={k:s for k,s in self.sessions.items() if s.workspace!=workspace.id}
    def _workspace(self,ident):
        C.need(type(ident) is str and ident in self.workspaces,'workspace_not_found',404)
        workspace=self.workspaces[ident];workspace.validate();return workspace
    def _session(self,workspace,ident):
        self._workspace(workspace)
        C.need(type(ident) is str and KEY.fullmatch(ident) and ident in self.sessions and self.sessions[ident].workspace==workspace,'session_not_found',404)
        return self.sessions[ident]
    def _save(self,workspace):
        records=[s.metadata() for s in self.sessions.values() if s.workspace==workspace.id]
        C.need(len(records)<=128,'session_budget',413)
        STATE.Store(workspace.root).update('sessions.json',{'sessions':[]},lambda data:data.update(sessions=records))
    def _connection_count(self):
        # A startup reserves capacity before the background factory has returned.
        return sum(s.driver is not None or s.status=='connecting' for s in self.sessions.values())
    def _background(self,fn):
        def run():
            try:fn()
            finally:
                with self.lock:self.threads.discard(threading.current_thread())
        thread=threading.Thread(target=run,daemon=True)
        self.threads.add(thread);thread.start()
    def _start(self,session,resume=False):
        workspace=self.workspaces[session.workspace]
        session.generation+=1;generation=session.generation
        def run():
            driver=None
            try:
                workspace.validate();driver=self.factory(workspace,session.runtime,lambda event:self.emit(session.id,event,generation))
                with self.lock:
                    if self.closed or session.closed or session.generation!=generation:driver.close();return
                    session.driver=driver
                native_id=driver.start(session.native_id if resume else None)
                C.need(type(native_id) is str and NATIVE.fullmatch(native_id),'invalid_native_identity',503)
                with self.lock:
                    if self.closed or session.closed or session.generation!=generation:driver.close();return
                    session.native_id=native_id
                    if session.status=='connecting':session.status='idle'
                    session.error=None
                    session.updated_at=now();session.seq+=1;self._save(workspace)
            except Exception as error:
                with self.lock:
                    if session.generation==generation:
                        session.status='failed';session.error=getattr(error,'code','native_start_failed');session.seq+=1
                        session.driver=None
                if driver:
                    try:driver.close()
                    except Exception:pass
        self._background(run)
    def create(self,workspace,runtime,title,request_id):
        with self.lock:
            selected=self._workspace(workspace)
            C.need(not self.closed,'console_closed',503)
            C.need(runtime in selected.runtimes,'runtime_not_enabled',403)
            C.need(type(title) is str and 0<len(title.strip())<=100 and type(request_id) is str and KEY.fullmatch(request_id),'invalid_session')
            clean=C.scrub(title.strip(),selected.root,100)
            for s in self.sessions.values():
                if s.workspace==workspace and s.create_key==request_id:
                    C.need(s.runtime==runtime and s.title==clean,'request_conflict',409);return s.summary()
            C.need(workspace not in self.errors,'session_state_unavailable',503)
            C.need(self._connection_count()<8 and sum(s.workspace==workspace for s in self.sessions.values())<128,'session_budget',429)
            s=Session(workspace,runtime,clean,request_id);self.sessions[s.id]=s
            try:self._save(selected)
            except Exception:self.sessions.pop(s.id,None);raise
            s.status='connecting';self._start(s);return s.summary()
    def resume(self,workspace,ident):
        with self.lock:
            s=self._session(workspace,ident)
            C.need(s.native_id is not None and s.status in ('disconnected','failed','interrupted','uncertain') and s.driver is None,'session_not_resumable',409)
            C.need(not self.closed and self._connection_count()<8,'session_budget',429)
            s.closed=False;s.status='connecting';self._start(s,resume=True);return s.summary()
    def list(self,workspace):
        with self.lock:
            self._workspace(workspace)
            return sorted((s.summary() for s in self.sessions.values() if s.workspace==workspace),key=lambda s:s['updated_at'],reverse=True)
    def get(self,workspace,ident):
        with self.lock:
            s=self._session(workspace,ident);root=self.workspaces[workspace].root
            value={**s.summary(),'messages':[dict(m) for m in s.messages],
                   'events':[dict(e) for e in s.events],'pending':copy.deepcopy(list(s.pending.values())),
                   'capabilities':copy.deepcopy(s.capabilities),'truncated':s.truncated}
        # Projection work must not hold the cross-project session lock.
        for message in value['messages']:message['text']=C.scrub(message['text'],root,20000)
        size=len(C.encoded(value))
        if size>240*1024:
            overflow=size-(240*1024-128)
            for name in ('events','messages'):
                rows=value[name];cut=0
                while cut<len(rows) and overflow>0:
                    overflow-=len(C.encoded(rows[cut]))+1;cut+=1
                if cut:del rows[:cut]
                if overflow<=0:break
            value['truncated']=True
            C.need(len(C.encoded(value))<=240*1024,'response_budget',413)
        return value
    def emit(self,ident,event,generation=None):
        with self.lock:
            s=self.sessions.get(ident)
            if s is None or s.closed or self.closed or type(event) is not dict or (generation is not None and generation!=s.generation):return
            kind=event.get('type');root=self.workspaces[s.workspace].root
            if kind=='message':
                role=event.get('role');key=event.get('id');text=event.get('text')
                if role not in ('user','assistant') or type(key) is not str or len(key)>160 or type(text) is not str:return
                previous=s.buffers.get(key,'') if event.get('delta') is True else ''
                combined=previous+text
                if len(combined)>20000:s.truncated=True
                combined=combined[:20000]
                if key not in s.buffers and len(s.buffers)>=20:s.buffers.pop(next(iter(s.buffers)));s.truncated=True
                s.buffers[key]=combined
                message=next((m for m in s.messages if m['id']==key),None)
                if message:message['text']=combined
                else:
                    if len(s.messages)==s.messages.maxlen:s.truncated=True
                    s.messages.append({'id':key,'role':role,'text':combined,'created_at':now()})
            elif kind=='status':
                if event.get('status') not in STATES:return
                s.status=event['status']
                if s.status in ('idle','failed','interrupted'):
                    s.pending.clear()
                if event.get('error'):s.error=C.scrub(str(event['error']),root,200)
            elif kind=='tool':
                if event.get('state') not in ('started','completed','failed'):return
                if len(s.events)==s.events.maxlen:s.truncated=True
                s.events.append({'id':C.scrub(str(event.get('id','')),root,160),'type':'tool','name':C.scrub(str(event.get('name','Tool')),root,160),
                                 'state':event['state'],'actor':C.scrub(str(event.get('actor','')),root,100),'at':now()})
            elif kind in ('approval','question'):
                key=event.get('id')
                if type(key) is not str or len(key)>160 or len(s.pending)>=8:return
                preview=event.get('preview','');preview=preview if type(preview) is str else ''
                clean_preview=C.scrub(preview,root,maximum=None)
                clean_title=C.scrub(str(event.get('title','Solicitud')),root,maximum=None)
                raw_choices=event.get('choices',[])
                choices=[x for x in raw_choices if x in ('allow','deny','cancel','submit')] if type(raw_choices) is list else []
                truncated=len(preview)>2000 or len(clean_preview)>2000 or len(clean_title)>300
                if truncated:choices=[x for x in choices if x in ('deny','cancel')]
                request={'id':key,'type':kind,'title':clean_title[:300],
                         'preview':clean_preview[:2000],'choices':choices,'truncated':truncated}
                if kind=='question':
                    fields=event.get('fields',[])
                    valid=type(fields) is list and 0<len(fields)<=8
                    request['fields']=[]
                    for field in fields if valid else []:
                        if type(field) is not dict or type(field.get('id')) is not str or not NATIVE.fullmatch(field['id']):valid=False;break
                        options=field.get('options',[])
                        label=field.get('label','Respuesta')
                        if type(label) is not str or len(label)>500 or type(options) is not list or len(options)>20 or any(type(o) is not str or len(o)>200 for o in options):valid=False;break
                        clean_label=C.scrub(label,root,maximum=None)
                        clean_options=[C.scrub(o,root,maximum=None) for o in options]
                        if len(clean_label)>500 or any(len(o)>200 for o in clean_options):valid=False;break
                        request['fields'].append({'id':field['id'],'label':clean_label,'options':clean_options})
                    if len({f['id'] for f in request['fields']})!=len(request['fields']):valid=False
                    if not valid or len(C.encoded(request))>8192:
                        request['fields']=[];request['truncated']=True
                    if request['truncated']:request['choices']=[x for x in choices if x=='cancel']
                s.pending[key]=request;s.status='waiting'
            elif kind=='resolved':
                s.pending.pop(str(event.get('id','')),None)
                if not s.pending and s.status=='waiting':s.status='running'
            elif kind=='history':
                if event.get('complete') is False:s.truncated=True
            elif kind=='capabilities':
                caps={}
                for name in ('agents','skills','tools','mcp'):
                    values=event.get(name,[])
                    if type(values) is list:
                        caps[name]=[];size=2
                        if len(values)>100:s.truncated=True
                        for value in values[:100]:
                            clean=C.scrub(str(value),root,160);cost=len(C.encoded(clean))+1
                            if size+cost>8192:s.truncated=True;break
                            caps[name].append(clean);size+=cost
                s.capabilities=caps
            else:return  # thinking/reasoning and unknown native payloads never enter the view
            s.updated_at=now();s.seq+=1
    def send(self,workspace,ident,text,request_id):
        with self.lock:
            s=self._session(workspace,ident)
            C.need(type(text) is str and 0<len(text.strip())<=16000 and type(request_id) is str and KEY.fullmatch(request_id),'invalid_message')
            clean=C.scrub(text,maximum=16000);signature=hashlib.sha256(clean.encode('utf-8')).hexdigest()
            if request_id in s.sent:
                C.need(s.sent[request_id]==signature,'request_conflict',409);return s.summary()
            C.need(not s.closed and s.status in ('idle','interrupted') and s.driver is not None,'session_busy',409)
            C.need(len(s.sent)<256,'turn_budget',429)
            s.sent[request_id]=signature;s.status='sending';s.seq+=1
            self.emit(ident,{'type':'message','id':request_id,'role':'user','text':clean})
            driver=s.driver;generation=s.generation
            def run():
                try:
                    driver.send(clean)
                    with self.lock:
                        if s.generation==generation and s.driver is driver and s.status=='sending':s.status='queued';s.seq+=1
                except Exception as error:
                    with self.lock:
                        if s.generation==generation and s.driver is driver:
                            s.status='uncertain';s.error=getattr(error,'code','delivery_uncertain');s.seq+=1
            self._background(run);return s.summary()
    def answer(self,workspace,ident,request_id,payload):
        with self.lock:
            s=self._session(workspace,ident);C.need(request_id in s.pending and type(payload) is dict,'request_not_pending',409)
            request=s.pending[request_id]
            if request['type']=='approval':
                C.need(set(payload)=={'decision'} and payload['decision'] in request['choices'],'invalid_decision')
            else:
                cancellation=set(payload)=={'decision'} and payload['decision']=='cancel' and 'cancel' in request['choices']
                submission=set(payload)=={'answers'} and type(payload['answers']) is dict and 'submit' in request['choices']
                C.need(cancellation or submission,'invalid_answers')
                if 'answers' in payload:
                    C.need(set(payload['answers'])=={f['id'] for f in request['fields']} and all(type(v) is str and len(v)<=2000 for v in payload['answers'].values()),'invalid_answers')
                    payload={'answers':{k:C.scrub(v,maximum=2000) for k,v in payload['answers'].items()}}
            # Reserve before I/O. Lost responses are uncertain and cannot be approved twice.
            del s.pending[request_id];s.seq+=1
            driver=s.driver;generation=s.generation
        try:driver.answer(request_id,payload)
        except Exception as error:
            with self.lock:
                if s.generation==generation and s.driver is driver:
                    s.status='uncertain';s.error=getattr(error,'code','decision_uncertain');s.seq+=1
            raise C.ConsoleError('decision_uncertain',503) from None
        with self.lock:
            C.need(s.generation==generation and s.driver is driver,'session_changed',409)
            if not s.pending and s.status=='waiting':s.status='running'
            return s.summary()
    def interrupt(self,workspace,ident):
        with self.lock:
            s=self._session(workspace,ident)
            C.need(s.driver is not None and s.status in BUSY-{'connecting','disconnecting'},'session_not_running',409)
            s.status='interrupting';s.seq+=1
            driver=s.driver;generation=s.generation
            def run():
                try:driver.interrupt()
                except Exception:
                    with self.lock:
                        if s.generation==generation and s.driver is driver:
                            s.status='uncertain';s.error='interrupt_uncertain';s.seq+=1
            self._background(run);return s.summary()
    def disconnect(self,workspace,ident):
        with self.lock:
            s=self._session(workspace,ident)
            C.need(s.status not in BUSY,'session_busy',409)
            driver=s.driver;s.closed=True;s.generation+=1;s.status='disconnecting';s.seq+=1
        try:
            if driver:driver.close()
        except Exception:
            with self.lock:s.status='uncertain';s.error='cleanup_incomplete';s.seq+=1
            raise C.ConsoleError('cleanup_incomplete',503) from None
        with self.lock:
            s.driver=None;s.status='disconnected';s.pending.clear();s.seq+=1
            return s.summary()
    def close(self):
        with self.lock:
            if self.closed:return
            self.closed=True;drivers=[]
            for s in self.sessions.values():
                s.closed=True
                if s.driver:drivers.append(s.driver)
        for driver in drivers:
            try:driver.close()
            except Exception:pass
        for thread in list(self.threads):thread.join(timeout=1)
