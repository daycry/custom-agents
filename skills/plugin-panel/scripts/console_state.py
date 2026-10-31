"""Owned, bounded console metadata. Local StateIO remains the sole I/O primitive."""
from datetime import datetime,timezone
import importlib.util
from pathlib import Path
import re
import time

_spec=importlib.util.spec_from_file_location('console_state_common',Path(__file__).with_name('console_common.py'))
C=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(C)
OWNER='custom-agents-control-center-v1'
MAX_BYTES=256*1024
PLAN=re.compile('[a-f0-9]{16}')
KEY=re.compile('[a-f0-9]{32}')
TASK=re.compile('T-[0-9]{1,4}')

def utc():return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')

class Store:
    def __init__(self,root):
        self.root=C.safe_root(str(Path(root).absolute()))
        self.path=self.root/'.claude/control-center'
        self.io=C.bundled('local-state.py').StateIO(C.bundled('local-read.py'),C.need,C.deadline_guard,maximum=MAX_BYTES)
    def _directories(self):
        for path in [self.root/'.claude',self.path]:
            if path.exists() or path.is_symlink():self.io.dirs(path)
    def _owned(self):
        self._directories()
        if not self.path.exists():return False
        raw,_=self.io.read(self.path/'owner.json',4096)
        C.need(C.json_load(raw)=={'owner':OWNER,'version':1},'foreign_state',409)
        return True
    def _initialize(self):
        self._directories()
        if self.path.exists():
            C.need(self._owned(),'foreign_state',409);return
        (self.root/'.claude').mkdir(exist_ok=True)
        self.io.dirs(self.root/'.claude')
        self.path.mkdir()
        self.io.dirs(self.path)
        self.io.write(self.path/'owner.json',C.encoded({'owner':OWNER,'version':1}),time.monotonic()+3,mode=0o600)
        self.io.write(self.path/'.gitignore',b'*\n',time.monotonic()+3,mode=0o600)
    def read(self,name,default):
        C.need(name in ('comments.json','sessions.json'),'invalid_state_name')
        try:
            if not self._owned():return default,None
            path=self.path/name
            if not path.exists() and not path.is_symlink():return default,None
            raw,identity=self.io.read(path,MAX_BYTES)
            envelope=C.json_load(raw)
            C.need(type(envelope) is dict and set(envelope)=={'owner','version','data'} and envelope['owner']==OWNER and type(envelope['version']) is int and envelope['version']==1,'invalid_state',409)
            return envelope['data'],identity
        except OSError:raise C.ConsoleError('state_unavailable',503) from None
    def update(self,name,default,transform):
        try:
            self._initialize()
            deadline=time.monotonic()+3
            with self.io.locked(self.path,deadline,initialize=True,wait=.2):
                data,identity=self.read(name,default)
                result=transform(data)
                raw=C.encoded({'owner':OWNER,'version':1,'data':data})
                C.need(len(raw)<=MAX_BYTES,'state_budget',413)
                self.io.write(self.path/name,raw,deadline,expected=identity,mode=0o600)
                return result
        except OSError:raise C.ConsoleError('state_unavailable',503) from None

class Notes:
    def __init__(self,root):self.store=Store(root)
    def _validate(self,plan,task):
        C.need(type(plan) is str and PLAN.fullmatch(plan) is not None,'invalid_plan')
        C.need(type(task) is str and TASK.fullmatch(task) is not None,'invalid_task')
    def _data(self,data):
        C.need(type(data) is dict and set(data)=={'revision','comments'} and type(data['revision']) is int and data['revision']>=0 and type(data['comments']) is list and len(data['comments'])<=1000,'invalid_notes',409)
        seen=set()
        for note in data['comments']:
            C.need(type(note) is dict and set(note)=={'id','plan','task','text','actor','created_at'},'invalid_notes',409)
            self._validate(note['plan'],note['task'])
            C.need(type(note['id']) is str and KEY.fullmatch(note['id']) is not None and note['id'] not in seen and type(note['text']) is str and 0<len(note['text'])<=2000 and note['actor']=='usuario del dashboard' and type(note['created_at']) is str and len(note['created_at'])<=40,'invalid_notes',409)
            seen.add(note['id'])
        return data
    def list(self,plan,task):
        self._validate(plan,task)
        data,_=self.store.read('comments.json',{'revision':0,'comments':[]});self._data(data)
        return {'revision':data['revision'],'comments':[dict(n,text=C.scrub(n['text'],self.store.root,2000)) for n in data['comments'] if n['plan']==plan and n['task']==task]}
    def add(self,plan,task,text,revision,key):
        self._validate(plan,task)
        C.need(type(text) is str and 0<len(text.strip())<=2000,'invalid_comment')
        C.need(type(revision) is int and revision>=0 and type(key) is str and KEY.fullmatch(key) is not None,'invalid_revision')
        clean=C.scrub(text.strip(),self.store.root,2000)
        def apply(data):
            self._data(data)
            for note in data['comments']:
                if note['id']==key:
                    C.need((note['plan'],note['task'],note['text'])==(plan,task,clean),'request_conflict',409)
                    return {'revision':data['revision'],'comment':note}
            C.need(data['revision']==revision,'version_changed',409)
            C.need(len(data['comments'])<1000,'notes_budget',413)
            note={'id':key,'plan':plan,'task':task,'text':clean,'actor':'usuario del dashboard','created_at':utc()}
            data['comments'].append(note);data['revision']+=1
            return {'revision':data['revision'],'comment':note}
        return self.store.update('comments.json',{'revision':0,'comments':[]},apply)
