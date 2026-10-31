"""Bounded background snapshots. A slow filesystem never holds an HTTP worker."""
import importlib.util
from pathlib import Path
import threading
import time

_spec=importlib.util.spec_from_file_location('console_snapshot_common',Path(__file__).with_name('console_common.py'))
C=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(C)

class Snapshots:
    def __init__(self,clock=None):
        self.clock=clock or time.monotonic
        self.lock=threading.RLock();self.rows={};self.threads=set();self.closed=False
    def get(self,key,compute,pending,*,max_age):
        with self.lock:
            C.need(not self.closed,'console_closed',503)
            if key not in self.rows:
                C.need(len(self.rows)<96,'snapshot_budget',429)
                self.rows[key]={'value':None,'built':None,'attempted':None,'active':False,'failed':False}
            row=self.rows[key];now=self.clock()
            due=row['attempted'] is None or now-row['attempted']>=max_age
            if due and not row['active'] and len(self.threads)<4:
                row['active']=True;row['attempted']=now
                thread=threading.Thread(target=self._refresh,args=(row,compute),daemon=True)
                self.threads.add(thread);thread.start()
            value=C.json_load(row['value']) if row['value'] is not None else dict(pending)
            state='refreshing' if row['active'] else 'refresh_failed' if row['failed'] else 'current' if row['value'] is not None else 'waiting'
            age=None if row['built'] is None else max(0,round(now-row['built'],1))
            value['freshness']={'state':state,'age_seconds':age}
            if row['failed']:
                value['complete']=False
                value['status']='partial' if row['value'] is not None else 'unavailable'
            return value
    def _refresh(self,row,compute):
        raw=None
        try:
            value=compute()
            C.need(type(value) is dict and value.get('status')!='unavailable','snapshot_unavailable',503)
            raw=C.encoded(value);C.need(len(raw)<=240*1024,'response_budget',503)
        except Exception:raw=None
        finally:
            with self.lock:
                if not self.closed:
                    if raw is not None:row['value']=raw;row['built']=self.clock()
                    row['failed']=raw is None;row['active']=False
                self.threads.discard(threading.current_thread())
    def close(self):
        with self.lock:self.closed=True;threads=list(self.threads)
        for thread in threads:thread.join(timeout=.25)
