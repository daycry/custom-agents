"""Explicit workspace registration. Names never become filesystem paths in HTTP."""
import importlib.util
import os
from pathlib import Path

_spec=importlib.util.spec_from_file_location('console_workspace_common',Path(__file__).with_name('console_common.py'))
C=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(C)

class Workspace:
    def __init__(self,ident,name,root,runtimes):
        root=C.safe_root(str(root))
        self.id,self.name,self.root,self.runtimes=ident,name,root,tuple(runtimes)
        info=root.stat();self.identity=(info.st_dev,info.st_ino)
    def public(self):
        return {'id':self.id,'name':C.scrub(self.name,maximum=100),'runtimes':list(self.runtimes)}
    def validate(self):
        C.need(C.safe_root(str(self.root))==self.root,'project_changed',409)
        info=self.root.stat()
        C.need((info.st_dev,info.st_ino)==self.identity,'project_changed',409)

def load_workspaces(path):
    path=Path(path).absolute()
    try:
        reader=C.bundled('local-read.py')
        row=reader.read_bytes(path.parent,path.name,max_bytes=65536)
        C.need(row['status']=='ok','registry_unavailable')
        data=C.json_load(row['data'])
        C.need(type(data) is dict and set(data)=={'version','workspaces'} and type(data['version']) is int and data['version']==1,'invalid_registry')
        rows=data['workspaces']
        C.need(type(rows) is list and 0<len(rows)<=32,'invalid_registry')
        result={};roots=set()
        for item in rows:
            C.need(type(item) is dict and set(item)=={'id','name','root','runtimes'},'invalid_workspace')
            ident,name=item['id'],item['name']
            C.need(type(ident) is str and len(ident)<=64 and C.ID.fullmatch(ident) is not None and ident not in result,'invalid_workspace_id')
            C.need(type(name) is str and 0<len(name.strip())<=100 and all(ord(c)>=32 for c in name),'invalid_workspace_name')
            runtimes=item['runtimes']
            C.need(type(runtimes) is list and len(runtimes)<=len(C.RUNTIMES) and all(type(r) is str and r in C.RUNTIMES for r in runtimes) and len(set(runtimes))==len(runtimes),'invalid_runtimes')
            root=C.safe_root(item['root']);key=os.path.normcase(str(root))
            C.need(key not in roots,'duplicate_workspace_root');roots.add(key)
            # Nested workspaces are allowed only as distinct roots: every native session
            # and API lookup must still match the selected root exactly.
            result[ident]=Workspace(ident,name.strip(),root,runtimes)
        return result
    except C.ConsoleError:raise
    except (OSError,TypeError,KeyError):raise C.ConsoleError('invalid_registry') from None
