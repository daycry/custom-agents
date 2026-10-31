"""Small stdlib boundaries shared by the local console; no runtime starts here."""
from functools import lru_cache
import importlib.util
import json
from pathlib import Path
import re
import time

HERE=Path(__file__).resolve().parent
BUNDLE=HERE.parents[2]
RUNTIMES=('claude-code','codex','opencode')
ID=re.compile(r'[a-z][a-z0-9]*(?:-[a-z0-9]+)*')

class ConsoleError(ValueError):
    def __init__(self,code,status=400):
        super().__init__(code);self.code=code;self.status=status

def need(condition,code='invalid_request',status=400):
    if not condition:raise ConsoleError(code,status)

def deadline_guard(deadline):
    need(time.monotonic()<deadline,'deadline_exceeded',503)

@lru_cache(maxsize=32)
def bundled(name):
    path=BUNDLE/'agent-kits/shared'/name
    spec=importlib.util.spec_from_file_location('console_shared_'+name.replace('-','_'),path)
    need(spec is not None and spec.loader is not None,'helper_unavailable',503)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

def sibling(name):
    spec=importlib.util.spec_from_file_location('console_'+name.replace('-','_'),HERE/name)
    need(spec is not None and spec.loader is not None,'helper_unavailable',503)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

def json_load(raw):
    def pairs(items):
        result={}
        for key,value in items:
            need(key not in result,'duplicate_json_key')
            result[key]=value
        return result
    try:
        data=json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda _:need(False,'invalid_json'))
        pending=[(data,0)];count=0
        while pending:
            value,depth=pending.pop();count+=1
            need(depth<=32 and count<=20000,'json_budget',413)
            if isinstance(value,dict):pending.extend((v,depth+1) for v in value.values())
            elif isinstance(value,list):pending.extend((v,depth+1) for v in value)
        return data
    except (UnicodeError,json.JSONDecodeError,RecursionError):
        raise ConsoleError('invalid_json') from None

def encoded(data):
    try:return json.dumps(data,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode('utf-8')
    except (ValueError,UnicodeError,RecursionError):raise ConsoleError('invalid_payload') from None

def scrub(text,root=None,maximum=12000):
    need(type(text) is str,'invalid_text')
    redactor=bundled('redact.py')
    clean=redactor.redactar(text)
    if root is not None:
        import getpass
        clean=redactor.anonimizar(clean,str(root),str(Path.home()),getpass.getuser())
    clean=''.join(c for c in clean if c in '\n\t' or ord(c)>=32 and not 0x7f<=ord(c)<=0x9f and c not in '\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069')
    return clean[:maximum]

def safe_root(raw):
    import stat
    need(type(raw) is str and 0<len(raw)<=2048 and not raw.startswith(('\\\\','//')),'invalid_project')
    root=Path(raw)
    need(root.is_absolute() and root.parent!=root,'invalid_project')
    reader=bundled('local-read.py')
    try:
        for part in [*reversed(root.parents),root]:
            info=part.lstat()
            need(stat.S_ISDIR(info.st_mode) and not reader._redirected(info),'unsafe_project')
        return root.resolve(strict=True)
    except OSError:raise ConsoleError('project_unavailable') from None


def same_root(native,root):
    """Accept the native Windows extended drive spelling, never UNC/device paths."""
    import os
    if type(native) is not str:return False
    prefix=chr(92)*2+'?'+chr(92)
    if os.name=='nt' and native.startswith(prefix):
        native=native[len(prefix):]
        if re.match(r'^[A-Za-z]:[\\/]',native) is None:return False
    if native.startswith((chr(92)*2,'//')):return False
    try:
        candidate=safe_root(native)
        return os.path.samefile(candidate,safe_root(str(root)))
    except (OSError,ValueError):return False
