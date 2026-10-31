"""A slow workspace must not occupy every HTTP worker or poison another workspace."""
import importlib.util
from pathlib import Path
import threading
import time

ROOT=Path(__file__).resolve().parents[1]

def api():
    path=ROOT/'skills/plugin-panel/scripts/console_snapshots.py'
    assert path.is_file(),'asynchronous project snapshots are not implemented'
    spec=importlib.util.spec_from_file_location('tested_console_snapshots',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def wait_for(check):
    limit=time.monotonic()+3
    while time.monotonic()<limit:
        if check():return
        time.sleep(.01)
    raise AssertionError('snapshot did not settle')

def test_slow_project_returns_immediately_and_only_computes_once():
    release=threading.Event();calls=[];cache=api().Snapshots()
    def slow():
        calls.append('one');release.wait(timeout=3)
        return {'status':'ok','complete':True,'observed_at':'original','value':'one only'}
    try:
        start=time.monotonic()
        for _ in range(12):
            value=cache.get(('one','plans'),slow,{'status':'calculating','complete':False},max_age=5)
            assert value['status']=='calculating'
        assert time.monotonic()-start<.5
        wait_for(lambda:calls)
        assert calls==['one']
        assert cache.get(('two','plans'),lambda:{'status':'ok','value':'two only'},
                         {'status':'calculating'},max_age=5)['status'] in ('ok','calculating')
        release.set()
        wait_for(lambda:cache.get(('one','plans'),slow,{},max_age=5).get('value')=='one only')
        assert calls==['one']
    finally:release.set();cache.close()

def test_failed_refresh_preserves_source_time_and_exposes_staleness():
    tick=[0.0];cache=api().Snapshots(clock=lambda:tick[0])
    def initial():return {'status':'ok','complete':True,'observed_at':'source-time','value':'known'}
    try:
        cache.get(('one','memory'),initial,{'status':'calculating'},max_age=5)
        wait_for(lambda:cache.get(('one','memory'),initial,{},max_age=5).get('value')=='known')
        tick[0]=6.0
        def failed():raise ValueError('private failure details')
        cache.get(('one','memory'),failed,{},max_age=5)
        wait_for(lambda:cache.get(('one','memory'),failed,{},max_age=5).get('freshness',{}).get('state')=='refresh_failed')
        row=cache.get(('one','memory'),failed,{},max_age=5)
        assert row['observed_at']=='source-time' and row['value']=='known'
        assert row['complete'] is False and 'private failure' not in str(row)
    finally:cache.close()

def test_global_background_budget_does_not_queue_unbounded_reads():
    release=threading.Event();calls=[];cache=api().Snapshots()
    def slow():
        calls.append(1);release.wait(timeout=3);return {'status':'ok'}
    try:
        for index in range(12):
            cache.get((str(index),'catalog'),slow,{'status':'calculating'},max_age=5)
        wait_for(lambda:len(calls)==4)
        assert len(calls)==4
    finally:release.set();cache.close()
