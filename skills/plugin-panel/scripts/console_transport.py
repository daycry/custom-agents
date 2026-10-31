"""Owned JSON pipe transport with bounded frames, queues and request deadlines."""
import ctypes
import importlib.util
import os
from pathlib import Path
import queue
import signal
import subprocess
import threading

_spec=importlib.util.spec_from_file_location('console_transport_common',Path(__file__).with_name('console_common.py'))
C=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(C)
MAX_LINE=512*1024


def executable(runtime,project=None):
    names={'codex':'codex','claude-code':'claude','opencode':'opencode'}
    C.need(runtime in names,'unknown_runtime')
    current=Path.cwd().resolve()
    blocked=[Path(project).resolve()] if project is not None else []
    def trusted(path,leaf=False):
        try:
            resolved=path.resolve()
            return resolved!=current and not (leaf and resolved.parent==current) and not any(resolved==root or root in resolved.parents for root in blocked)
        except OSError:return False
    # Search only explicit absolute PATH entries. Windows shutil.which may insert
    # the current directory, even with an explicit PATH; a project cannot supply
    # an executable merely by naming it after a trusted runtime.
    def find(filename):
        for raw in os.get_exec_path():
            folder=Path(raw)
            if not folder.is_absolute() or not trusted(folder):continue
            path=folder/filename
            if path.is_file() and os.access(path,os.X_OK) and trusted(path,leaf=True):return str(path)
        return None
    name=names[runtime]
    if os.name=='nt':
        direct=find(name+'.exe')
        if direct:return [direct]
        shim=find(name+'.cmd')
        if shim and runtime=='opencode':
            candidate=Path(shim).parent/'node_modules/@opencode/cli/bin/opencode.exe'
            if candidate.is_file() and trusted(candidate,leaf=True):return [str(candidate)]
        if shim and runtime=='codex':
            candidate=Path(shim).parent/'node_modules/@openai/codex/bin/codex.js'
            node=find('node.exe')
            if node and candidate.is_file() and trusted(candidate,leaf=True):return [node,str(candidate)]
        raise C.ConsoleError('runtime_not_installed',503)
    found=find(name)
    C.need(found is not None,'runtime_not_installed',503)
    return [found]


class _WindowsJob:
    """A private job owns this process tree; never opens or kills an unrelated PID."""
    def __init__(self):
        from ctypes import wintypes as W
        class Limits(ctypes.Structure):
            _fields_=[('process_time',ctypes.c_longlong),('job_time',ctypes.c_longlong),
                      ('flags',W.DWORD),('min_working',ctypes.c_size_t),('max_working',ctypes.c_size_t),
                      ('active',W.DWORD),('affinity',ctypes.c_size_t),('priority',W.DWORD),('scheduling',W.DWORD)]
        class IO(ctypes.Structure):
            _fields_=[(name,ctypes.c_ulonglong) for name in ('read_ops','write_ops','other_ops','read_bytes','write_bytes','other_bytes')]
        class Extended(ctypes.Structure):
            _fields_=[('basic',Limits),('io',IO),('process_memory',ctypes.c_size_t),('job_memory',ctypes.c_size_t),
                      ('peak_process',ctypes.c_size_t),('peak_job',ctypes.c_size_t)]
        self.api=ctypes.WinDLL('kernel32',use_last_error=True)
        self.api.CreateJobObjectW.argtypes=[ctypes.c_void_p,W.LPCWSTR];self.api.CreateJobObjectW.restype=W.HANDLE
        self.api.SetInformationJobObject.argtypes=[W.HANDLE,ctypes.c_int,ctypes.c_void_p,W.DWORD];self.api.SetInformationJobObject.restype=W.BOOL
        self.api.AssignProcessToJobObject.argtypes=[W.HANDLE,W.HANDLE];self.api.AssignProcessToJobObject.restype=W.BOOL
        self.api.CloseHandle.argtypes=[W.HANDLE];self.api.CloseHandle.restype=W.BOOL
        self.handle=self.api.CreateJobObjectW(None,None)
        C.need(bool(self.handle),'process_job_unavailable',503)
        limits=Extended();limits.basic.flags=0x2000
        if not self.api.SetInformationJobObject(self.handle,9,ctypes.byref(limits),ctypes.sizeof(limits)):
            self.close();raise C.ConsoleError('process_job_unavailable',503)
    def assign(self,process):
        C.need(bool(self.api.AssignProcessToJobObject(self.handle,int(process._handle))),'process_job_unavailable',503)
    def close(self):
        if self.handle:self.api.CloseHandle(self.handle);self.handle=None


class LineProcess:
    def __init__(self,argv,cwd,on_message,on_exit,env=None):
        C.need(type(argv) is list and 0<len(argv)<=32 and all(type(x) is str and len(x)<=4096 for x in argv),'invalid_native_command')
        C.need(Path(argv[0]).suffix.lower() not in ('.cmd','.bat','.ps1'),'native_batch_not_allowed')
        self.argv,self.cwd,self.on_message,self.on_exit,self.env=argv,Path(cwd),on_message,on_exit,env
        self.process=None;self.job=None;self.lock=threading.RLock();self.queue=queue.Queue(maxsize=16)
        self.threads=[];self.closing=False;self.close_owner=None;self.closed=threading.Event();self.notified=False
        self.last_error=''
    @property
    def alive(self):return self.process is not None and self.process.poll() is None
    def start(self):
        with self.lock:
            C.need(self.process is None and not self.closing,'native_already_started',409)
            kwargs={'cwd':self.cwd,'stdin':subprocess.PIPE,'stdout':subprocess.PIPE,'stderr':subprocess.PIPE,
                    'bufsize':0,'env':self.env}
            if os.name=='nt':
                self.job=_WindowsJob();kwargs['creationflags']=subprocess.CREATE_NO_WINDOW|subprocess.CREATE_NEW_PROCESS_GROUP
            else:kwargs['start_new_session']=True
            try:
                self.process=subprocess.Popen(self.argv,**kwargs)
                if self.job:self.job.assign(self.process)
            except Exception:
                if self.process:
                    self.process.kill();self.process.wait(timeout=3)
                if self.job:self.job.close()
                raise C.ConsoleError('native_start_failed',503) from None
            for target in (self._read,self._write,self._stderr):
                thread=threading.Thread(target=target,daemon=True);self.threads.append(thread);thread.start()
    def _notify(self,code):
        with self.lock:
            if self.notified or self.closing:return
            self.notified=True
        try:self.on_exit(code)
        except Exception:pass
    def _fail(self,code):
        self._notify(code);self.close()
    def _read(self):
        try:
            while not self.closing:
                raw=self.process.stdout.readline(MAX_LINE+1)
                if not raw:break
                if len(raw)>MAX_LINE or not raw.endswith(b'\n'):
                    self._fail('native_output_budget');return
                try:
                    message=C.json_load(raw)
                    C.need(type(message) is dict,'native_protocol_error')
                    self.on_message(message)
                except Exception:
                    self._fail('native_protocol_error');return
            if not self.closing:self._fail('native_closed')
        except (OSError,ValueError):
            if not self.closing:self._fail('native_closed')
    def _stderr(self):
        try:
            while not self.closing:
                raw=self.process.stderr.readline(4096)
                if not raw:return
                self.last_error=C.scrub(raw.decode('utf-8',errors='replace'),self.cwd,500)
        except (OSError,ValueError):pass
    def _write(self):
        while not self.closing:
            try:raw=self.queue.get(timeout=.2)
            except queue.Empty:continue
            try:
                view=memoryview(raw)
                while view:
                    count=self.process.stdin.write(view)
                    if not count:raise BrokenPipeError
                    view=view[count:]
                self.process.stdin.flush()
            except (OSError,ValueError):self._fail('native_closed');return
    def send(self,message):
        raw=C.encoded(message)+b'\n'
        C.need(len(raw)<=65536,'native_input_budget',413)
        with self.lock:
            C.need(self.alive and not self.closing,'native_disconnected',503)
            try:self.queue.put_nowait(raw)
            except queue.Full:raise C.ConsoleError('native_input_backpressure',429) from None
    def close(self):
        with self.lock:
            if self.closing:
                owner=self.close_owner
            else:
                self.closing=True;self.close_owner=threading.current_thread();owner=None
        if owner is not None:
            if owner is not threading.current_thread():self.closed.wait(timeout=5)
            return
        try:
            if self.job:self.job.close()
            elif self.process and os.name!='nt':
                try:os.killpg(self.process.pid,signal.SIGTERM)
                except ProcessLookupError:pass
            if self.process:
                try:self.process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    if os.name!='nt':
                        try:os.killpg(self.process.pid,signal.SIGKILL)
                        except ProcessLookupError:pass
                    else:self.process.kill()
                    self.process.wait(timeout=2)
                if os.name!='nt':
                    # The group can outlive its leader, including a leader that
                    # exited before close(). Do not leave owned descendants behind.
                    try:os.killpg(self.process.pid,signal.SIGKILL)
                    except ProcessLookupError:pass
                for thread in self.threads:
                    if thread is not threading.current_thread():thread.join(timeout=.5)
                for stream in (self.process.stdin,self.process.stdout,self.process.stderr):
                    try:stream.close()
                    except OSError:pass
        finally:self.closed.set()


class JsonPeer:
    def __init__(self,argv,cwd,on_message,on_exit=None):
        self.on_message=on_message;self.on_exit=on_exit or (lambda _:None)
        self.pending={};self.lock=threading.RLock();self.sequence=0
        self.process=LineProcess(argv,cwd,self._receive,self._exit)
    def start(self):self.process.start()
    def send(self,message):self.process.send(message)
    def _receive(self,message):
        with self.lock:
            key=message.get('id')
            if type(key) is int and 'method' not in message and key in self.pending:
                pending=self.pending[key];pending['value']=message;pending['event'].set();return
        self.on_message(message)
    def _exit(self,code):
        with self.lock:
            for pending in self.pending.values():pending['error']=code;pending['event'].set()
        self.on_exit(code)
    def call(self,method,params,timeout=15):
        with self.lock:
            C.need(len(self.pending)<16,'native_request_budget',429)
            self.sequence+=1;key=self.sequence
            pending={'event':threading.Event()};self.pending[key]=pending
        try:
            self.send({'id':key,'method':method,'params':params})
            C.need(pending['event'].wait(timeout),'native_request_timeout',503)
            C.need('error' not in pending,'native_disconnected',503)
            message=pending['value']
            C.need('error' not in message and 'result' in message,'native_request_failed',503)
            return message['result']
        finally:
            with self.lock:self.pending.pop(key,None)
    def close(self):
        self._exit('native_closed');self.process.close()
