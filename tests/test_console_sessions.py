"""Native execution must remain workspace-bound, bounded and observable."""
import importlib.util
import json
from pathlib import Path
import time

import pytest

ROOT=Path(__file__).resolve().parents[1]
SCRIPTS=ROOT/'skills/plugin-panel/scripts'

def load(name):
    path=SCRIPTS/name
    assert path.is_file(), 'session manager is not implemented'
    spec=importlib.util.spec_from_file_location('tested_'+name.replace('.','_'),path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

class Driver:
    def __init__(self,workspace,runtime,emit):
        self.workspace,self.runtime,self.emit=workspace,runtime,emit
        self.sent=[];self.closed=False;self.answers=[]
    def start(self,resume_id=None):return resume_id or 'native-'+self.workspace.id
    def send(self,text):self.sent.append(text)
    def interrupt(self):self.emit({'type':'status','status':'interrupted'})
    def answer(self,key,payload):self.answers.append((key,payload))
    def close(self):self.closed=True

@pytest.fixture
def manager(tmp_path):
    w=load('console_workspaces.py');workspaces={}
    for name in ['one','two']:
        p=tmp_path/name;p.mkdir();workspaces[name]=w.Workspace(name,name,p,('codex',))
    made=[]
    def factory(*args):
        driver=Driver(*args);made.append(driver);return driver
    m=load('console_sessions.py').SessionManager(workspaces,factory=factory)
    yield m,made
    m.close()

def ready(manager):
    session=manager.create('one','codex','Portal','a'*32)
    deadline=time.monotonic()+3
    while time.monotonic()<deadline:
        session=manager.get('one',session['id'])
        if session['status']=='idle':return session
        time.sleep(.01)
    pytest.fail('session did not become ready')


def test_connecting_sessions_reserve_the_global_connection_budget(tmp_path):
    import threading
    w=load('console_workspaces.py');workspace=w.Workspace('one','One',tmp_path,('codex',))
    release=threading.Event()
    def blocked_factory(*args):
        release.wait(timeout=5)
        return Driver(*args)
    manager=load('console_sessions.py').SessionManager({'one':workspace},factory=blocked_factory)
    try:
        for index in range(8):manager.create('one','codex','Session '+str(index),format(index,'032x'))
        with pytest.raises(ValueError,match='session_budget'):
            manager.create('one','codex','Overflow',format(9,'032x'))
    finally:release.set();manager.close()


def test_truncated_question_cannot_be_submitted_through_the_api(manager):
    m,made=manager;s=ready(m)
    made[0].emit({'type':'question','id':'q','title':'Check full details','preview':'x'*3000,
                 'choices':['submit','cancel'],'fields':[{'id':'answer','label':'Answer','options':[]}]})
    with pytest.raises(ValueError):m.answer('one',s['id'],'q',{'answers':{'answer':'approve'}})
    assert made[0].answers==[]
    assert m.get('one',s['id'])['pending'][0]['choices']==['cancel']


def test_many_large_questions_stay_readable_and_only_offer_safe_cancellation(manager):
    m,made=manager;s=ready(m)
    fields=[{'id':'field-'+str(n),'label':'L'*500,'options':['X'*200]*20} for n in range(8)]
    for n in range(8):
        made[0].emit({'type':'question','id':'question-'+str(n),'title':'Large form','preview':'',
                     'choices':['submit','cancel'],'fields':fields})
    snapshot=m.get('one',s['id'])
    assert len(json.dumps(snapshot).encode('utf-8'))<240*1024
    assert len(snapshot['pending'])==8
    assert all(row['truncated'] and row['choices']==['cancel'] for row in snapshot['pending'])

def test_unicode_capabilities_cannot_crowd_out_pending_human_decisions(manager):
    m,made=manager;s=ready(m)
    names=['\U0001f40d'*160]*100
    made[0].emit({'type':'capabilities',**{key:names for key in ('agents','skills','tools','mcp')}})
    made[0].emit({'type':'approval','id':'important','title':'Choose','preview':'file.txt','choices':['deny']})
    snapshot=m.get('one',s['id'])
    assert len(json.dumps(snapshot,ensure_ascii=False).encode())<240*1024
    assert snapshot['pending'][0]['id']=='important' and snapshot['truncated']

def test_messages_and_controls_never_cross_workspace(manager):
    m,made=manager;s=ready(m)
    with pytest.raises(ValueError):m.get('two',s['id'])
    with pytest.raises(ValueError):m.send('two',s['id'],'hello','b'*32)
    assert made[0].sent==[]
    m.send('one',s['id'],'hello','b'*32)
    deadline=time.monotonic()+2
    while not made[0].sent and time.monotonic()<deadline:time.sleep(.01)
    assert made[0].sent==['hello']
    assert m.list('two')==[]


def test_slow_permission_reply_does_not_block_other_projects(manager):
    import threading
    m,made=manager;s=ready(m);entered=threading.Event();release=threading.Event();listed=threading.Event()
    def slow(*_):entered.set();release.wait(timeout=3)
    made[0].answer=slow
    made[0].emit({'type':'approval','id':'slow','title':'Permission','preview':'file.txt','choices':['deny']})
    answering=threading.Thread(target=lambda:m.answer('one',s['id'],'slow',{'decision':'deny'}))
    reader=threading.Thread(target=lambda:(m.list('two'),listed.set()))
    try:
        answering.start();assert entered.wait(timeout=2);reader.start()
        assert listed.wait(timeout=.5),'a native permission response blocked another project'
    finally:release.set();answering.join(timeout=3);reader.join(timeout=3)


def test_disconnect_reserves_its_slot_and_cannot_admit_a_turn_while_closing(manager):
    import threading
    m,made=manager;s=ready(m);entered=threading.Event();release=threading.Event()
    def slow_close():entered.set();release.wait(timeout=3);made[0].closed=True
    made[0].close=slow_close
    closer=threading.Thread(target=lambda:m.disconnect('one',s['id']))
    try:
        closer.start();assert entered.wait(timeout=2)
        with pytest.raises(ValueError):m.send('one',s['id'],'must not run','b'*32)
        assert made[0].sent==[]
        assert m._connection_count()==1
        assert m.get('one',s['id'])['status']=='disconnecting'
    finally:release.set();closer.join(timeout=3)


def test_redaction_expansion_cannot_leave_an_incomplete_preview_approvable(manager):
    m,made=manager;s=ready(m)
    preview='echo '+'token=a1b2c3d4 '*30+'X'*1380+' ; REMOVE_CRITICAL_FILES'
    made[0].emit({'type':'approval','id':'expanded','title':'Command','preview':preview,'choices':['allow','deny']})
    request=m.get('one',s['id'])['pending'][0]
    assert request['truncated'] is True and request['choices']==['deny']
    with pytest.raises(ValueError):m.answer('one',s['id'],'expanded',{'decision':'allow'})
    assert made[0].answers==[]


def test_large_projection_does_not_hold_the_global_session_lock(manager,monkeypatch):
    import threading
    m,made=manager;s=ready(m)
    for n in range(20):made[0].emit({'type':'message','id':'large-'+str(n),'role':'assistant','text':'X'*20000})
    for n in range(200):made[0].emit({'type':'tool','id':str(n),'name':'Read','state':'completed'})
    module=m.get.__func__.__globals__['C'];original=module.encoded
    entered=threading.Event();release=threading.Event();listed=threading.Event();result=[]
    def slow(value):
        if isinstance(value,dict) and 'messages' in value and not entered.is_set():entered.set();release.wait(timeout=3)
        return original(value)
    monkeypatch.setattr(module,'encoded',slow)
    reader=threading.Thread(target=lambda:result.append(m.get('one',s['id'])))
    other=threading.Thread(target=lambda:(m.list('two'),listed.set()))
    try:
        reader.start();assert entered.wait(timeout=2);other.start()
        assert listed.wait(timeout=.5),'snapshot serialization held the cross-project lock'
    finally:release.set();reader.join(timeout=4);other.join(timeout=3)
    assert result and len(original(result[0]))<=240*1024
    assert result[0]['messages'][-1]['id']=='large-19' and result[0]['truncated']


def test_failure_from_an_old_send_cannot_change_a_resumed_connection(manager):
    import threading
    m,made=manager;s=ready(m);entered=threading.Event();release=threading.Event()
    def slow(_):
        entered.set();release.wait(timeout=3);raise ValueError('old connection failed')
    made[0].send=slow
    try:
        m.send('one',s['id'],'hello','b'*32);assert entered.wait(timeout=2)
        made[0].emit({'type':'status','status':'idle'})
        m.disconnect('one',s['id']);m.resume('one',s['id'])
        deadline=time.monotonic()+2
        while time.monotonic()<deadline and m.get('one',s['id'])['status']!='idle':time.sleep(.01)
        assert m.get('one',s['id'])['status']=='idle'
        release.set()
        deadline=time.monotonic()+2
        while m.threads and time.monotonic()<deadline:time.sleep(.01)
        assert m.get('one',s['id'])['status']=='idle'
    finally:release.set()

def test_retry_does_not_send_again_and_busy_does_not_admit_second_turn(manager):
    m,made=manager;s=ready(m)
    m.send('one',s['id'],'hello','b'*32)
    m.send('one',s['id'],'hello','b'*32)
    with pytest.raises(ValueError):m.send('one',s['id'],'other','c'*32)
    deadline=time.monotonic()+2
    while not made[0].sent and time.monotonic()<deadline:time.sleep(.01)
    assert made[0].sent==['hello']

def test_stream_redacts_across_deltas_and_drops_reasoning_without_persisting_chat(manager):
    m,made=manager;s=ready(m);emit=made[0].emit
    emit({'type':'message','id':'msg-1','role':'assistant','text':'Key ghp_','delta':True})
    emit({'type':'message','id':'msg-1','role':'assistant','text':'A'*36,'delta':True})
    emit({'type':'thinking','text':'private internal reasoning'})
    snapshot=m.get('one',s['id']);raw=json.dumps(snapshot)
    assert 'ghp_'+'A'*36 not in raw and 'private internal reasoning' not in raw
    assert snapshot['messages'][-1]['role']=='assistant'
    state=list(m.workspaces['one'].root.rglob('*.json'))
    assert state and all('msg-1' not in p.read_text() and 'private internal reasoning' not in p.read_text() for p in state)

def test_permission_reply_is_scoped_exactly_and_consumed_once(manager):
    m,made=manager;s=ready(m)
    made[0].emit({'type':'approval','id':'req-1','title':'Write file','preview':'safe.txt','choices':['allow','deny']})
    with pytest.raises(ValueError):m.answer('two',s['id'],'req-1',{'decision':'allow'})
    with pytest.raises(ValueError):m.answer('one',s['id'],'req-1',{'decision':'bypass'})
    m.answer('one',s['id'],'req-1',{'decision':'deny'})
    with pytest.raises(ValueError):m.answer('one',s['id'],'req-1',{'decision':'allow'})
    assert made[0].answers==[('req-1',{'decision':'deny'})]

def test_interrupt_waits_for_native_confirmation_and_shutdown_closes_owned_drivers(manager):
    m,made=manager;s=ready(m)
    m.send('one',s['id'],'hello','b'*32)
    m.interrupt('one',s['id'])
    deadline=time.monotonic()+2
    while m.get('one',s['id'])['status']!='interrupted' and time.monotonic()<deadline:time.sleep(.01)
    assert m.get('one',s['id'])['status']=='interrupted'
    m.close();assert all(d.closed for d in made)

def test_output_is_bounded_and_reports_truncation(manager):
    m,made=manager;s=ready(m)
    for i in range(250):made[0].emit({'type':'tool','id':str(i),'name':'Read','state':'completed','actor':'implementer'})
    snap=m.get('one',s['id'])
    assert len(snap['events'])<=200 and snap['truncated'] is True
    assert len(json.dumps(snap).encode())<256*1024

def test_permission_ack_does_not_overwrite_a_native_completion(manager):
    m,made=manager;s=ready(m)
    made[0].emit({'type':'approval','id':'r1','title':'Write','preview':'file','choices':['allow','deny']})
    made[0].answer=lambda key,payload:made[0].emit({'type':'status','status':'idle'})
    m.answer('one',s['id'],'r1',{'decision':'deny'})
    assert m.get('one',s['id'])['status']=='idle'

def test_disconnect_releases_the_owned_driver_and_late_events_cannot_change_resume(manager):
    m,made=manager;s=ready(m);old_emit=made[0].emit
    assert callable(getattr(m,'disconnect',None)), 'session disconnect is not implemented'
    m.disconnect('one',s['id'])
    assert made[0].closed and m.get('one',s['id'])['can_resume'] is True
    m.resume('one',s['id'])
    deadline=time.monotonic()+2
    while m.get('one',s['id'])['status']!='idle' and time.monotonic()<deadline:time.sleep(.01)
    old_emit({'type':'status','status':'failed'})
    assert m.get('one',s['id'])['status']=='idle' and len(made)==2

def test_native_history_truncation_is_visible(manager):
    m,made=manager;s=ready(m)
    made[0].emit({'type':'history','complete':False})
    assert m.get('one',s['id'])['truncated'] is True

def test_pipe_admission_without_native_activity_is_queued_not_running(manager):
    m,made=manager;s=ready(m)
    m.send('one',s['id'],'hello','b'*32)
    deadline=time.monotonic()+2
    while m.get('one',s['id'])['status']=='sending' and time.monotonic()<deadline:time.sleep(.01)
    assert m.get('one',s['id'])['status']=='queued'
