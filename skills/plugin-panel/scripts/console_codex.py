"""Codex app-server adapter. Native policies stay owned by Codex."""
import importlib.util
import json
import os
from pathlib import Path
import threading

_spec=importlib.util.spec_from_file_location('console_codex_common',Path(__file__).with_name('console_common.py'))
C=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(C)
TRANSPORT=C.sibling('console_transport.py')

def command_choices(params):
    available=params.get('availableDecisions')
    if available is None:available=['accept','decline','cancel']
    if type(available) is not list:return []
    return [ui for native,ui in [('accept','allow'),('decline','deny'),('cancel','cancel')] if native in available]

class Driver:
    def __init__(self,workspace,emit,peer_factory=None,command=None):
        self.workspace,self.emit=workspace,emit;self.thread_id=None;self.turn_id=None
        self.pending={};self.lock=threading.RLock();self.closing=False
        self.turn_revision=0
        factory=peer_factory or TRANSPORT.JsonPeer
        self.peer=factory((command or TRANSPORT.executable('codex',self.workspace.root))+['app-server'],workspace.root,self.handle,self._exit)
    def _scope(self,thread):
        C.need(type(thread) is dict and type(thread.get('cwd')) is str,'native_scope_unverified',503)
        C.need(C.same_root(thread['cwd'],self.workspace.root),'native_scope_mismatch',403)
    def start(self,resume_id=None):
        self.peer.start()
        self.peer.call('initialize',{'clientInfo':{'name':'custom_agents_dashboard','title':'custom-agents dashboard','version':'1.0.0'}})
        self.peer.send({'method':'initialized','params':{}})
        if resume_id:
            existing=self.peer.call('thread/read',{'threadId':resume_id,'includeTurns':False})
            thread=existing.get('thread');self._scope(thread)
            C.need((thread.get('status') or {}).get('type')!='active','native_session_active',409)
            result=self.peer.call('thread/resume',{'threadId':resume_id,'cwd':str(self.workspace.root),'excludeTurns':True})
        else:result=self.peer.call('thread/start',{'cwd':str(self.workspace.root)})
        thread=result.get('thread');self._scope(thread)
        C.need(type(thread.get('id')) is str,'native_identity_missing',503)
        self.thread_id=thread['id']
        if resume_id:self.history()
        try:
            result=self.peer.call('skills/list',{'cwds':[str(self.workspace.root)]},timeout=5)
            skills=[]
            for group in result.get('data',[]):
                if group.get('cwd')==str(self.workspace.root):
                    skills.extend(s['name'] for s in group.get('skills',[]) if type(s) is dict and type(s.get('name')) is str)
            if skills:self.emit({'type':'capabilities','skills':skills})
        except Exception:pass
        return self.thread_id
    def history(self):
        try:
            result=self.peer.call('thread/items/list',{'threadId':self.thread_id,'limit':20,'sortDirection':'desc'})
            for entry in reversed(result.get('data',[])):
                item=entry.get('item') if type(entry) is dict else None
                if type(item) is dict:self._item(item,history=True)
            if result.get('nextCursor'):self.emit({'type':'history','complete':False})
        except Exception:self.emit({'type':'history','complete':False})
    def send(self,text):
        with self.lock:revision=self.turn_revision
        result=self.peer.call('turn/start',{'threadId':self.thread_id,'input':[{'type':'text','text':text}]})
        turn=result.get('turn');C.need(type(turn) is dict and type(turn.get('id')) is str,'native_turn_unverified',503)
        with self.lock:
            if self.turn_revision==revision:
                self.turn_id=turn['id']
                self.emit({'type':'status','status':'running'})
    def _item(self,item,state=None,history=False):
        kind=item.get('type');ident=item.get('id','native-item')
        if kind=='agentMessage' and type(item.get('text')) is str:
            self.emit({'type':'message','id':ident,'role':'assistant','text':item['text']})
        elif kind=='userMessage' and history:
            content=item.get('content',[])
            text='\n'.join(p.get('text','') for p in content if type(p) is dict and p.get('type')=='text' and type(p.get('text')) is str)
            if text:self.emit({'type':'message','id':ident,'role':'user','text':text})
        elif kind in ('commandExecution','mcpToolCall','dynamicToolCall','collabAgentToolCall','webSearch','fileChange') and state:
            name=(str(item.get('server',''))+'/'+str(item.get('tool',''))) if kind=='mcpToolCall' else str(item.get('tool') or kind)
            self.emit({'type':'tool','id':ident,'name':name,'state':state,'actor':str(item.get('senderThreadId') or '')})
    def _request(self,message):
        method=message['method'];params=message.get('params') or {};key=str(message['id'])
        allowed={'item/commandExecution/requestApproval','item/fileChange/requestApproval','item/permissions/requestApproval',
                 'item/tool/requestUserInput','mcpServer/elicitation/request'}
        if method not in allowed:
            self.peer.send({'id':message['id'],'error':{'code':-32601,'message':'Unsupported dashboard request'}});return
        with self.lock:self.pending[key]=message
        if method=='item/tool/requestUserInput':
            questions=params.get('questions',[])
            fields=[{'id':q['id'],'label':q.get('question',''),'options':[o.get('label','') for o in q.get('options') or []]}
                    for q in questions if type(q) is dict and type(q.get('id')) is str]
            self.emit({'type':'question','id':key,'title':'Pregunta de Codex','preview':'','choices':['submit','cancel'],'fields':fields});return
        if method=='mcpServer/elicitation/request':
            schema=params.get('requestedSchema') or {};properties=schema.get('properties') or {}
            supported=params.get('mode') in ('form','openai/form') and type(properties) is dict and 0<len(properties)<=8
            supported=supported and all(type(v) is dict and v.get('type')=='string' for v in properties.values())
            if supported:
                self.emit({'type':'question','id':key,'title':params.get('message','Formulario MCP'),'preview':'','choices':['submit','cancel'],
                           'fields':[{'id':k,'label':v.get('title') or k,'options':v.get('enum') or []} for k,v in properties.items()]});return
            self.emit({'type':'approval','id':key,'title':'Solicitud MCP requiere la interfaz nativa','preview':params.get('message',''),'choices':['cancel']});return
        choices=['allow','deny','cancel']
        if method=='item/commandExecution/requestApproval':
            choices=command_choices(params)
        preview=json.dumps({k:v for k,v in params.items() if k not in ('threadId','turnId')},ensure_ascii=False)
        self.emit({'type':'approval','id':key,'title':params.get('reason') or method.rsplit('/',1)[0],
                   'preview':preview,'choices':choices})
    def handle(self,message):
        method=message.get('method');params=message.get('params')
        if type(method) is not str or type(params) is not dict:return
        if params.get('threadId')!=self.thread_id:return
        if 'id' in message:self._request(message);return
        if method=='item/agentMessage/delta' and type(params.get('delta')) is str:
            self.emit({'type':'message','id':str(params.get('itemId','message')),'role':'assistant','text':params['delta'],'delta':True})
        elif method in ('item/started','item/completed'):
            item=params.get('item')
            if type(item) is dict:
                state='started' if method=='item/started' else 'failed' if item.get('status') in ('failed','declined') else 'completed'
                self._item(item,state)
        elif method=='turn/started':
            with self.lock:
                self.turn_revision+=1;self.turn_id=(params.get('turn') or {}).get('id')
                self.emit({'type':'status','status':'running'})
        elif method=='turn/completed':
            with self.lock:
                self.turn_revision+=1;status=(params.get('turn') or {}).get('status');self.turn_id=None
                self.emit({'type':'status','status':{'completed':'idle','failed':'failed','interrupted':'interrupted'}.get(status,'uncertain')})
        elif method=='serverRequest/resolved':
            key=str(params.get('requestId',''))
            with self.lock:self.pending.pop(key,None)
            self.emit({'type':'resolved','id':key})
    def answer(self,key,payload):
        with self.lock:
            C.need(key in self.pending,'native_request_not_pending',409)
            request=self.pending[key];method=request['method'];params=request['params']
            if method=='item/tool/requestUserInput':
                result={'answers':{k:{'answers':[v]} for k,v in payload.get('answers',{}).items()}}
            elif method=='mcpServer/elicitation/request':
                result={'action':'accept','content':payload['answers']} if 'answers' in payload else {'action':'cancel','content':None}
            elif method=='item/permissions/requestApproval':
                decision=payload.get('decision');C.need(decision in ('allow','deny','cancel'),'invalid_decision')
                result={'permissions':params.get('permissions',{}) if decision=='allow' else {},'scope':'turn'}
            else:
                decision=payload.get('decision');C.need(decision in ('allow','deny','cancel'),'invalid_decision')
                if method=='item/commandExecution/requestApproval':C.need(decision in command_choices(params),'invalid_decision')
                result={'decision':{'allow':'accept','deny':'decline','cancel':'cancel'}[decision]}
            self.peer.send({'id':request['id'],'result':result});del self.pending[key]
    def interrupt(self):
        C.need(self.turn_id is not None,'native_turn_unknown',409)
        self.peer.call('turn/interrupt',{'threadId':self.thread_id,'turnId':self.turn_id})
    def _exit(self,code):
        if not self.closing:self.emit({'type':'status','status':'disconnected','error':code})
    def close(self):
        self.closing=True;self.peer.close()
