"""Project routing describes optional integrations; it never executes an adapter."""
import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT=Path(__file__).resolve().parents[1]/'agent-kits/shared/integration-route.py'

def router():
    assert SCRIPT.is_file(), 'project integration router missing'
    spec=importlib.util.spec_from_file_location('integration_route',SCRIPT)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

def binding(name='redmine-sync',**changes):
    data={'id':'tracker','purpose':'task-tracking','enabled':True,'contract_version':1,
          'adapter':{'kind':'skill','name':name,'origin':'project'},
          'events':['plan.created','task.started'],'capabilities':['plan.export','task.progress']}
    data.update(changes)
    return data

def write(root,data,filename='integrations.json'):
    directory=root/'.claude';directory.mkdir(parents=True,exist_ok=True)
    path=directory/filename;path.write_text(json.dumps(data),encoding='utf-8');return path

def test_absence_never_uses_another_project_or_home(tmp_path,monkeypatch):
    home=tmp_path/'home';write(home,{'version':1,'bindings':[binding()]})
    monkeypatch.setenv('HOME',str(home));monkeypatch.setenv('USERPROFILE',str(home))
    project=tmp_path/'project';project.mkdir()
    result=router().route(project)
    assert result['status']=='absent' and result['bindings']==[]

def test_arbitrary_project_adapter_and_event_filter_are_isolated(tmp_path):
    first=tmp_path/'first';second=tmp_path/'second'
    write(first,{'version':1,'bindings':[binding('company-redmine')]})
    write(second,{'version':1,'bindings':[binding('company-wiki',purpose='documentation',events=['docs.changed'])]})
    result=router().route(first,event='task.started',operation='task.progress')
    assert result['status']=='declared'
    assert result['bindings'][0]['adapter']['name']=='company-redmine'
    assert result['availability']=='unverified' and result['execution']=='not_run'
    assert router().route(second,event='task.started')['status']=='no_match'

def test_explicit_empty_configuration_overrides_legacy_opt_in(tmp_path):
    write(tmp_path,{'enabled':True,'cloudId':'fixture'},'jira.json')
    write(tmp_path,{'version':1,'bindings':[]})
    assert router().route(tmp_path)['status']=='disabled'
    assert router().route(tmp_path)['bindings']==[]

def test_corrupt_configuration_does_not_reset_or_fall_back(tmp_path):
    write(tmp_path,{'enabled':True},'jira.json')
    config=write(tmp_path,{});config.write_text('{"private":"never-print-this",',encoding='utf-8')
    before=config.read_bytes();result=router().route(tmp_path)
    assert result['status']=='invalid' and result['bindings']==[]
    assert 'never-print-this' not in json.dumps(result)
    assert config.read_bytes()==before

def test_one_bad_binding_does_not_suppress_an_independent_binding(tmp_path):
    bad=binding('broken',id='other');bad.pop('adapter')
    write(tmp_path,{'version':1,'bindings':[binding(),bad]})
    result=router().route(tmp_path)
    assert result['status']=='partial' and len(result['bindings'])==1 and result['diagnostics']

@pytest.mark.parametrize('data',[
    {'version':True,'bindings':[]}, {'version':2,'bindings':[]},
    {'version':1,'bindings':[binding(enabled=1)]},
    {'version':1,'bindings':[binding(settings='../another/credentials.json')]},
    {'version':1,'bindings':[binding(),binding()]},
])
def test_invalid_schema_cannot_produce_an_action(tmp_path,data):
    write(tmp_path,data);result=router().route(tmp_path)
    assert result['status']=='invalid' and result['bindings']==[]

def test_legacy_configuration_is_read_only_and_does_not_export_settings(tmp_path):
    config=write(tmp_path,{'enabled':True,'private':'not-output'},'jira.json');before=config.read_bytes()
    result=router().route(tmp_path,event='plan.created')
    assert result['status']=='declared' and result['source']=='legacy'
    assert result['bindings'][0]['adapter']=={'kind':'skill','name':'jira-sync','origin':'bundle'}
    assert 'not-output' not in json.dumps(result) and config.read_bytes()==before

def test_linked_configuration_is_not_followed(tmp_path):
    external=tmp_path/'external.json';external.write_text(json.dumps({'version':1,'bindings':[binding()]}),encoding='utf-8')
    root=tmp_path/'project';(root/'.claude').mkdir(parents=True)
    try:(root/'.claude/integrations.json').symlink_to(external)
    except OSError:pytest.skip('symlink unavailable')
    result=router().route(root)
    assert result['status']=='unavailable' and result['bindings']==[]

@pytest.mark.parametrize('fault',['exception','missing-function'])
def test_bundled_dependency_failure_degrades_without_disclosing_exception(tmp_path,monkeypatch,fault):
    from types import SimpleNamespace
    write(tmp_path,{'version':1,'bindings':[binding()]})
    module=router();original=module._bundled
    def broken(_value):raise RuntimeError('private-fixture-error')
    redactor=SimpleNamespace(redactar=broken) if fault=='exception' else SimpleNamespace()
    monkeypatch.setattr(module,'_bundled',lambda name:redactor if name=='redact' else original(name))
    result=module.route(tmp_path)
    assert result['status']=='unavailable' and result['bindings']==[]
    assert 'private-fixture-error' not in json.dumps(result)

@pytest.mark.parametrize('body',['{"version":1,"version":1,"bindings":[]}', ' '*65537],ids=['duplicate-keys','oversized'])
def test_ambiguous_or_oversized_config_never_uses_legacy_fallback(tmp_path,body):
    write(tmp_path,{'enabled':True},'jira.json')
    p=write(tmp_path,{});p.write_text(body,encoding='utf-8')
    assert router().route(tmp_path)['status']=='invalid'

def test_sensitive_looking_adapter_identifiers_are_not_exported(tmp_path):
    secret='ghp_'+'A'*36
    write(tmp_path,{'version':1,'bindings':[binding(adapter={'kind':'tool','origin':'session','name':secret})]})
    result=router().route(tmp_path)
    assert result['status']=='invalid' and secret not in json.dumps(result)


@pytest.mark.parametrize('encoding',['cp1252','ascii'])
@pytest.mark.parametrize('case',['absent','disabled','declared','invalid','partial','no_match'])
def test_cli_preserves_status_and_never_claims_execution(tmp_path,encoding,case):
    import os
    import subprocess
    import sys
    options=[]
    if case=='disabled':write(tmp_path,{'version':1,'bindings':[]})
    elif case in ('declared','no_match'):write(tmp_path,{'version':1,'bindings':[binding()]})
    elif case=='invalid':write(tmp_path,{'private-note':'do-not-disclose'})
    elif case=='partial':write(tmp_path,{'version':1,'bindings':[binding(),{'id':'invalid'}]})
    if case=='no_match':options=['--operation','another.operation']
    run=subprocess.run([sys.executable,str(SCRIPT),
                        '--project',str(tmp_path),'--check',*options],capture_output=True,
                       env={**os.environ,'PYTHONIOENCODING':encoding})
    assert run.returncode==(2 if case in ('invalid','partial') else 0)
    assert run.stderr==b'' and run.stdout.isascii()
    result=json.loads(run.stdout)
    assert result['status']==case
    assert result['availability']==result['permissions']=='unverified'
    assert result['execution']=='not_run' and b'do-not-disclose' not in run.stdout
