"""Owned native processes exchange JSON over pipes, never shell-composed prompts."""
import importlib.util
from pathlib import Path
import sys
import threading
import time

import pytest

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/'skills/plugin-panel/scripts/console_transport.py'

def api():
    assert PATH.is_file(), 'bounded native transport is not implemented'
    spec=importlib.util.spec_from_file_location('tested_console_transport',PATH)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def wait_for(check):
    deadline=time.monotonic()+5
    while time.monotonic()<deadline:
        if check():return
        time.sleep(.01)
    pytest.fail('native transport did not settle')

def test_prompt_metacharacters_remain_json_data_and_process_stops(tmp_path):
    child=tmp_path/'child.py'
    child.write_text('import sys,json\nfor line in sys.stdin:\n print(line.strip(),flush=True)\n')
    got=[];exits=[]
    p=api().LineProcess([sys.executable,str(child)],tmp_path,got.append,exits.append)
    p.start();payload={'prompt':'& echo private | $(oops) `x` <file> %PATH% !test!'}
    p.send(payload);wait_for(lambda:got)
    assert got==[payload]
    p.close();assert not p.alive

def test_oversized_line_fails_closed_and_is_not_forwarded(tmp_path):
    child=tmp_path/'child.py';child.write_text('print("x"*600000,flush=True)\nimport time;time.sleep(10)\n')
    got=[];exits=[];p=api().LineProcess([sys.executable,str(child)],tmp_path,got.append,exits.append)
    p.start();wait_for(lambda:exits)
    assert got==[] and exits[0]=='native_output_budget'
    p.close();assert not p.alive

def test_rpc_matches_responses_and_preserves_server_requests(tmp_path):
    child=tmp_path/'child.py';child.write_text('import sys,json\nfor line in sys.stdin:\n m=json.loads(line)\n print(json.dumps({"id":99,"method":"approval","params":{}}),flush=True)\n print(json.dumps({"id":m["id"],"result":{"ok":True}}),flush=True)\n')
    messages=[];peer=api().JsonPeer([sys.executable,str(child)],tmp_path,messages.append)
    peer.start()
    assert peer.call('initialize',{})=={'ok':True}
    wait_for(lambda:messages)
    assert messages[0]['method']=='approval' and messages[0]['id']==99
    peer.close();assert not peer.process.alive

def test_stalled_rpc_has_deadline_and_no_unbounded_wait(tmp_path):
    child=tmp_path/'child.py';child.write_text('import time;time.sleep(10)\n')
    peer=api().JsonPeer([sys.executable,str(child)],tmp_path,lambda _:None);peer.start()
    started=time.monotonic()
    with pytest.raises(ValueError):peer.call('initialize',{},timeout=.1)
    assert time.monotonic()-started<2
    peer.close();assert not peer.process.alive


def test_eof_closes_the_owned_process_instead_of_leaving_a_background_worker(tmp_path):
    child=tmp_path/'closed-output.py'
    child.write_text('import os,time\nos.close(1)\ntime.sleep(20)\n')
    exits=[];p=api().LineProcess([sys.executable,str(child)],tmp_path,lambda _:None,exits.append)
    p.start()
    try:
        wait_for(lambda:exits)
        wait_for(lambda:not p.alive)
    finally:p.close()


def test_posix_cleanup_signals_its_group_even_after_the_parent_has_exited(tmp_path,monkeypatch):
    import io
    from types import SimpleNamespace
    module=api();signals=[]
    p=module.LineProcess([sys.executable],tmp_path,lambda _:None,lambda _:None)
    p.process=SimpleNamespace(pid=12345,poll=lambda:0,wait=lambda timeout:0,
        stdin=io.BytesIO(),stdout=io.BytesIO(),stderr=io.BytesIO())
    monkeypatch.setattr(module,'os',SimpleNamespace(name='posix',killpg=lambda pid,sig:signals.append((pid,sig))))
    monkeypatch.setattr(module,'signal',SimpleNamespace(SIGTERM=15,SIGKILL=9))
    p.close()
    assert signals and signals[0]==(12345,module.signal.SIGTERM)

def test_runtime_discovery_never_prefers_an_executable_from_the_project(tmp_path,monkeypatch):
    import os
    project=tmp_path/'project';trusted=tmp_path/'installed';project.mkdir();trusted.mkdir()
    name='codex.exe' if os.name=='nt' else 'codex'
    for folder in (project,trusted):
        binary=folder/name;binary.write_text('test executable metadata only');binary.chmod(0o755)
    monkeypatch.chdir(project);monkeypatch.setenv('PATH',str(project)+os.pathsep+str(trusted))
    assert api().executable('codex')[0]==str(trusted/name)


def test_explicit_user_bin_is_usable_when_dashboard_starts_from_home(tmp_path,monkeypatch):
    import os
    home=tmp_path/'home';project=tmp_path/'project';binary_dir=home/'.local/bin'
    binary_dir.mkdir(parents=True);project.mkdir()
    name='codex.exe' if os.name=='nt' else 'codex';binary=binary_dir/name
    binary.write_text('test executable metadata only');binary.chmod(0o755)
    monkeypatch.chdir(home);monkeypatch.setenv('PATH',str(binary_dir))
    assert api().executable('codex',project)[0]==str(binary)
