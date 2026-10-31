"""Project inventory isolation and fairness share the real background reader budget."""
import importlib.util
import json
from pathlib import Path
import threading
import time
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
SCRIPTS=ROOT/'skills/plugin-panel/scripts'

def load(name):
    spec=importlib.util.spec_from_file_location('service_test_'+name.replace('.','_'),SCRIPTS/name)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def test_a_slow_catalog_cannot_reserve_all_readers_while_other_projects_wait(tmp_path,monkeypatch):
    registry=load('console_workspaces.py');module=load('console_service.py');workspaces={}
    for name in ['slow','fast-one','fast-two','fast-three','plan']:
        root=tmp_path/name;root.mkdir();workspaces[name]=registry.Workspace(name,name,root,())
    service=module.Service(workspaces,sessions=SimpleNamespace(close=lambda:None))
    release=threading.Event();started=threading.Event();original=module.C.sibling
    def inventory(_root,**kwargs):
        if Path(kwargs['project']).name=='slow':started.set();release.wait(timeout=5)
        return {'agents':[],'skills':[],'commands':[]}
    def sibling(name):
        return SimpleNamespace(build_inventory=inventory) if name=='build_panel.py' else original(name)
    monkeypatch.setattr(module.C,'sibling',sibling)
    try:
        service.catalog('slow');assert started.wait(timeout=2)
        for name in ['fast-one','fast-two','fast-three']:service.catalog(name)
        deadline=time.monotonic()+1.5;value={}
        while time.monotonic()<deadline:
            value=service.plans('plan')
            if value['status']=='not_found':break
            time.sleep(.01)
        assert value.get('status')=='not_found','unrelated plans waited behind a catalog mutex'
    finally:release.set();service.close()


def test_parallel_real_catalogs_keep_project_roots_and_metadata_separate(tmp_path):
    registry=load('console_workspaces.py');module=load('console_service.py');workspaces={}
    for name in ('one','two'):
        root=tmp_path/name;root.mkdir();workspace=registry.Workspace(name,name,root,())
        workspaces[name]=workspace
        agents=root/'.claude/agents';agents.mkdir(parents=True)
        (agents/('private-'+name+'.md')).write_text('---\nname: private-'+name+'\ndescription: '+str(workspace.root)+'\n---\n\nBODY MUST NOT BE EXPORTED\n',encoding='utf-8')
    service=module.Service(workspaces,sessions=SimpleNamespace(close=lambda:None))
    try:
        for name in workspaces:service.catalog(name)
        deadline=time.monotonic()+15;values={}
        while time.monotonic()<deadline:
            values={name:service.catalog(name) for name in workspaces}
            if all(value.get('extensions') for value in values.values()):break
            time.sleep(.05)
        for name,value in values.items():
            raw=json.dumps(value)
            assert value.get('extensions'),value.get('status')
            assert [p['name'] for p in value['extensions']['pieces']]==['private-'+name]
            assert str(workspaces[name].root) not in raw and 'BODY MUST NOT BE EXPORTED' not in raw
    finally:service.close()
