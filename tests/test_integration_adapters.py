"""Adapter boundaries and diagnosis use isolated projects, never real services."""
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def load(path,name):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_doctor_reports_new_bindings_without_claiming_connection(tmp_path):
    config=tmp_path/'.claude';config.mkdir()
    (config/'integrations.json').write_text('{"version":1,"bindings":[]}',encoding='utf-8')
    # Explicit empty bindings override obsolete/incomplete provider configuration.
    (config/'jira.json').write_text('{"enabled":true}',encoding='utf-8')
    result=load('agent-kits/shared/doctor.py','integration_doctor').bloque_configs(str(ROOT),str(tmp_path))
    lines=[row for row in result['lineas'] if row['que']=='integrations.json']
    assert len(lines)==1
    assert 'sin verificar' in json.dumps(lines,ensure_ascii=False)
    assert not any(row['que']=='jira.json' for row in result['lineas'])


def test_jira_explicit_root_does_not_inherit_a_parent_optin(tmp_path):
    parent=tmp_path/'parent';(parent/'.claude').mkdir(parents=True)
    (parent/'.claude/jira.json').write_text('{"enabled":true}',encoding='utf-8')
    project=parent/'child';project.mkdir()
    active,_,_=load('skills/jira-sync/scripts/jira-flow.py','isolated_jira')._jira_activo(str(project))
    assert active is False


def test_documented_examples_are_valid_declarations(tmp_path):
    module=load('agent-kits/shared/integration-route.py','example_router')
    config=tmp_path/'.claude';config.mkdir()
    for source in (ROOT/'docs/examples/integrations').glob('*.json'):
        (config/'integrations.json').write_bytes(source.read_bytes())
        result=module.route(str(tmp_path))
        assert result['status']=='declared', (source.name,result)
        assert result['execution']=='not_run'


def test_bundle_adapters_link_the_project_port_and_reconciliation():
    for name in ['jira-sync','confluence-publish','confluence-pull']:
        text=(ROOT/f'skills/{name}/SKILL.md').read_text(encoding='utf-8')
        assert 'project-integrations.md' in text
        assert 'incierto' in text.lower()
        assert not ('find "$PWD/.claude"' in text and "-path '*jira.json'" in text)


def test_atlassian_binding_covers_every_documented_progress_owner(tmp_path):
    module=load('agent-kits/shared/integration-route.py','progress_router')
    config=tmp_path/'.claude';config.mkdir()
    (config/'integrations.json').write_bytes((ROOT/'docs/examples/integrations/atlassian.json').read_bytes())
    for event in ['review.completed','review.gaps','review.worklog','task.qa-failed']:
        result=module.route(str(tmp_path),event=event,purpose='task-tracking')
        assert result['status']=='declared',event
