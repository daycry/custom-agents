"""A shared catalog must have identical meaning in both supported selection runtimes."""
import importlib.util
import json
from pathlib import Path
import subprocess
import shutil

import pytest

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/'agent-kits/shared/module-selection.py'

def api():
    assert PATH.is_file(), 'module selection API missing'
    spec=importlib.util.spec_from_file_location('module_selection',PATH)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_core_is_not_the_complete_catalog():
    result=api().resolve_selection(profile='core')
    assert 'tdd' in result['skills']
    assert not set(result['skills']) & {'jira-sync','confluence-publish','confluence-pull','voice-profile'}

@pytest.mark.parametrize('options',[
    {'profile':'core'}, {'profile':'full'},
    {'profile':'core','include':['content','jira']},
    {'profile':'developer','exclude':['application-data']},
])
def test_python_and_node_resolve_identically(options):
    result=api().resolve_selection(**options)
    code="import {resolveSelection} from './install/modules.mjs'; process.stdout.write(JSON.stringify(resolveSelection(JSON.parse(process.argv[1]))))"
    other=subprocess.run(['node','--input-type=module','-e',code,json.dumps(options)],cwd=ROOT,
                         capture_output=True,text=True,encoding='utf-8',errors='replace',check=True)
    assert result==json.loads(other.stdout)

def test_invalid_catalog_and_dependency_cycle_are_rejected():
    module=api()
    bad={'version':1,'modules':{'a':{'skills':['one'],'commands':[],'requires':['b']},
                              'b':{'skills':['two'],'commands':[],'requires':['a']}},
         'profiles':{'core':['a']}}
    with pytest.raises(ValueError):module.resolve_selection(catalog=bad,profile='core')

def test_selection_reader_ships_with_copied_shared_kit(tmp_path):
    source=ROOT/'agent-kits/shared/modules.json'
    assert source.is_file(), 'runtime catalog must ship in shared kit, not installer directory'
    shared=tmp_path/'agent-kits/shared';shared.mkdir(parents=True)
    shutil.copyfile(PATH,shared/'module-selection.py')
    shutil.copyfile(source,shared/'modules.json')
    import sys
    run=subprocess.run([sys.executable,str(shared/'module-selection.py'),'--profile','core'],
                       capture_output=True,text=True,encoding='utf-8',errors='replace',check=True)
    assert 'jira-sync' not in json.loads(run.stdout)['skills']

def test_empty_selection_is_not_a_silent_install():
    with pytest.raises(ValueError):api().resolve_selection(profile='core',exclude=['core'])


@pytest.mark.parametrize('defect',[
    'version','identifier','fields','list','duplicate','unknown-dependency','duplicate-owner','unknown-profile-module',
])
def test_malformed_catalogs_cannot_be_delivered_by_either_reader(defect):
    catalog={'version':1,'modules':{'core':{'skills':['tdd'],'commands':[],'requires':[]}},'profiles':{'core':['core']}}
    if defect=='version':catalog['version']=True
    elif defect=='identifier':catalog['profiles']['../outside']=[]
    elif defect=='fields':catalog['modules']['core']['extra']=True
    elif defect=='list':catalog['modules']['core']['skills']='tdd'
    elif defect=='duplicate':catalog['modules']['core']['skills']=['tdd','tdd']
    elif defect=='unknown-dependency':catalog['modules']['core']['requires']=['absent']
    elif defect=='duplicate-owner':catalog['modules']['other']={'skills':['tdd'],'commands':[],'requires':[]}
    elif defect=='unknown-profile-module':catalog['profiles']['core']=['absent']
    with pytest.raises(ValueError):api().resolve_selection(catalog=catalog)
    code="import {resolveSelection} from './install/modules.mjs'; try {resolveSelection({catalog:JSON.parse(process.argv[1])}); process.exit(3)} catch {process.exit(0)}"
    run=subprocess.run(['node','--input-type=module','-e',code,json.dumps(catalog)],cwd=ROOT,capture_output=True)
    assert run.returncode==0, run.stderr


@pytest.mark.parametrize('options',[
    ['--profile','missing'], ['--with','missing'], ['--with','jira','--without','jira'],
    ['--with','content','--without','voice'], ['--without','core'],
])
def test_selection_cli_rejects_invalid_requests_without_partial_json(options):
    import sys
    run=subprocess.run([sys.executable,str(PATH),*options],capture_output=True)
    assert run.returncode==2 and run.stdout==b''
    assert b'module selection unavailable' in run.stderr and b'Traceback' not in run.stderr


def test_bounded_catalog_read_does_not_accept_truncated_metadata(tmp_path,monkeypatch):
    path=tmp_path/'modules.json';path.write_bytes(b' '*65537)
    module=api();monkeypatch.setattr(module,'CATALOG',path)
    with pytest.raises(ValueError,match='exceeds limit'):module.resolve_selection()
