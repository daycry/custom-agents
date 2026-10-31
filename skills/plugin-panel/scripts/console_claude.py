"""Claude Code bidirectional stream-json adapter, without permission bypass flags."""
import importlib.util
import json
import os
from pathlib import Path
import threading
import uuid

_spec=importlib.util.spec_from_file_location('console_claude_common',Path(__file__).with_name('console_common.py'))
C=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(C)
TRANSPORT=C.sibling('console_transport.py')

class Driver:
    def __init__(self,workspace,emit,process_factory=None,command=None):
        self.workspace,self.emit=workspace,emit
        self.factory=process_factory or TRANSPORT.LineProcess
        self.command=command;self.process=None;self.native_id=None
        self.lock=threading.RLock();self.controls={};self.pending={}
        self.message_id=None;self.blocks={};self.interrupt_requested=False;self.closing=False
    def _control(self,request,timeout=30):
        key='console-'+uuid.uuid4().hex;pending={'event':threading.Event()}
        with self.lock:self.controls[key]=pending
        try:
            self.process.send({'type':'control_request','request_id':key,'request':request})
            C.need(pending['event'].wait(timeout),'native_request_timeout',503)
            C.need(pending.get('ok') is True,'native_request_failed',503)
            return pending.get('result')
        finally:
            with self.lock:self.controls.pop(key,None)
    def start(self,resume_id=None):
        if resume_id:
            try:uuid.UUID(resume_id)
            except (ValueError,TypeError,AttributeError):raise C.ConsoleError('invalid_native_identity') from None
        self.native_id=resume_id or str(uuid.uuid4())
        argv=(self.command or TRANSPORT.executable('claude-code',self.workspace.root))+['--print','--input-format','stream-json','--output-format','stream-json',
              '--verbose','--include-partial-messages','--permission-prompt-tool','stdio']
        argv.append(('--resume=' if resume_id else '--session-id=')+self.native_id)
        self.process=self.factory(argv,self.workspace.root,self.handle,self._exit)
        self.process.start();self._control({'subtype':'initialize','hooks':None})
        # Claude history remains in the native runtime. Only sessions created/known
        # by this console can be resumed; no scan of private transcript directories.
        return self.native_id
    def send(self,text):
        self.interrupt_requested=False
        self.process.send({'type':'user','message':{'role':'user','content':text},'session_id':self.native_id,'parent_tool_use_id':None})
    def _reply(self,key,response):
        self.process.send({'type':'control_response','response':{'subtype':'success','request_id':key,'response':response}})
    def _request(self,message):
        key=message.get('request_id');request=message.get('request')
        if type(key) is not str or type(request) is not dict:return
        if request.get('subtype')!='can_use_tool':
            self.process.send({'type':'control_response','response':{'subtype':'error','request_id':key,'error':'Unsupported dashboard control request'}});return
        with self.lock:self.pending[key]=request
        tool=request.get('tool_name','Tool');inputs=request.get('input')
        C.need(type(inputs) is dict,'native_protocol_error',503)
        if tool=='AskUserQuestion':
            questions=inputs.get('questions') or []
            fields=[{'id':f'q-{i}','label':q.get('question',''),'options':[o.get('label','') for o in q.get('options') or []]}
                    for i,q in enumerate(questions) if type(q) is dict]
            self.emit({'type':'question','id':key,'title':'Pregunta de Claude','preview':'','choices':['submit','cancel'],'fields':fields})
        else:
            self.emit({'type':'approval','id':key,'title':str(tool),'preview':json.dumps(inputs,ensure_ascii=False),'choices':['allow','deny']})
    def _assistant(self,message):
        body=message.get('message') or {};content=body.get('content') or []
        ident=body.get('id') or self.message_id or 'message'
        text='\n'.join(b['text'] for b in content if type(b) is dict and b.get('type')=='text' and type(b.get('text')) is str)
        if text:self.emit({'type':'message','id':ident,'role':'assistant','text':text})
        for block in content:
            if type(block) is dict and block.get('type')=='tool_use':
                tool=block.get('name','Tool');inputs=block.get('input') or {}
                actor=inputs.get('subagent_type','') if type(inputs) is dict else ''
                self.emit({'type':'tool','id':str(block.get('id','')),'name':str(tool),'state':'started','actor':str(actor)})
    def _stream(self,event):
        kind=event.get('type')
        if kind=='message_start':
            self.message_id=(event.get('message') or {}).get('id');self.blocks={}
            self.emit({'type':'status','status':'running'})
        elif kind=='content_block_start':
            block=event.get('content_block') or {};index=event.get('index')
            self.blocks[index]=block.get('type')
            if block.get('type')=='tool_use':
                self.emit({'type':'tool','id':str(block.get('id','')),'name':str(block.get('name','Tool')),'state':'started','actor':''})
        elif kind=='content_block_delta':
            delta=event.get('delta') or {}
            if self.blocks.get(event.get('index'))=='text' and delta.get('type')=='text_delta' and type(delta.get('text')) is str:
                self.emit({'type':'message','id':self.message_id or 'message','role':'assistant','text':delta['text'],'delta':True})
    def handle(self,message):
        kind=message.get('type')
        if kind=='control_response':
            response=message.get('response') or {};key=response.get('request_id')
            with self.lock:
                pending=self.controls.get(key)
                if pending:
                    pending['ok']=response.get('subtype')=='success';pending['result']=response.get('response');pending['event'].set()
        elif kind=='control_request':self._request(message)
        elif kind=='control_cancel_request':
            key=message.get('request_id')
            with self.lock:self.pending.pop(key,None)
            self.emit({'type':'resolved','id':str(key)})
        elif kind=='system' and message.get('subtype')=='init':
            directory=message.get('cwd')
            C.need(C.same_root(directory,self.workspace.root),'native_scope_mismatch',403)
            C.need(message.get('session_id')==self.native_id,'native_identity_mismatch',403)
            self.emit({'type':'capabilities','tools':message.get('tools') or [],'agents':message.get('agents') or [],'skills':message.get('skills') or [],
                       'mcp':[m.get('name','') for m in message.get('mcp_servers') or [] if type(m) is dict]})
        elif kind=='stream_event':
            event=message.get('event')
            if type(event) is dict:self._stream(event)
        elif kind=='assistant':self._assistant(message)
        elif kind=='user':
            for block in (message.get('message') or {}).get('content') or []:
                if type(block) is dict and block.get('type')=='tool_result':
                    self.emit({'type':'tool','id':str(block.get('tool_use_id','')),'name':'tool_result','state':'failed' if block.get('is_error') is True else 'completed','actor':''})
        elif kind=='result':
            failed=message.get('is_error') is True or message.get('subtype') not in ('success',None)
            status='interrupted' if failed and self.interrupt_requested else 'failed' if failed else 'idle'
            self.emit({'type':'status','status':status,'error':'native_turn_failed' if failed and not self.interrupt_requested else None})
    def answer(self,key,payload):
        with self.lock:
            C.need(key in self.pending,'native_request_not_pending',409)
            request=self.pending[key];inputs=request['input']
            if request.get('tool_name')=='AskUserQuestion' and 'answers' in payload:
                questions=inputs.get('questions') or []
                answers={q['question']:payload['answers'][f'q-{i}'] for i,q in enumerate(questions)}
                response={'behavior':'allow','updatedInput':{**inputs,'answers':answers}}
            else:
                decision=payload.get('decision');C.need(decision in ('allow','deny','cancel'),'invalid_decision')
                response={'behavior':'allow','updatedInput':inputs} if decision=='allow' else {'behavior':'deny','message':'Declined in custom-agents dashboard'}
            self._reply(key,response);del self.pending[key]
    def interrupt(self):
        self.interrupt_requested=True;self._control({'subtype':'interrupt'},timeout=5)
    def _exit(self,code):
        with self.lock:
            for pending in self.controls.values():pending['ok']=False;pending['event'].set()
        if not self.closing:self.emit({'type':'status','status':'disconnected','error':code})
    def close(self):
        self.closing=True
        if self.process:self.process.close()
