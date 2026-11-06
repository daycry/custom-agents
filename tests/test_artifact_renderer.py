import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import pytest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'agent-kits/shared/render-artifact.py'
def module():
 spec=importlib.util.spec_from_file_location('artifact_renderer',SCRIPT)
 mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

def config(kind):
 fields={
 'jira-picker':['SERVER_PROJECTS','SERVER_SEARCH','CLOUD_ID'],
 'jira-live':['SERVER_SEARCH','CLOUD_ID','LABEL','TITULO'],
 'confluence-tree':['SERVER','CLOUD_ID','HOME_ID','SPACE_KEY','SPACE_NAME','SPACE_INITIALS','DEFAULT_NAME'],
 }[kind]
 return {key:'demo' for key in fields}

@pytest.mark.parametrize('kind',['jira-picker','jira-live','confluence-tree'])
def test_config_is_data_not_script_or_markup(kind):
 data=config(kind);text='</script><img src=x onerror=alert(1)> á & "\u2028'
 for key in data:data[key]=text
 html=module().render(kind,data)
 assert text not in html
 start=html.index('const CONFIG = ')+len('const CONFIG = ')
 encoded=html[start:html.index(';',start)]
 assert json.loads(encoded)==data
 assert '<' not in encoded and '\\u003c' in encoded
 assert '{{' not in html

@pytest.mark.parametrize('mutation',['missing','extra','nonstring','huge'])
def test_invalid_config_does_not_render(mutation):
 data=config('jira-picker')
 if mutation=='missing':data.pop('CLOUD_ID')
 if mutation=='extra':data['SECRET']='do not echo'
 if mutation=='nonstring':data['CLOUD_ID']={}
 if mutation=='huge':data['CLOUD_ID']='x'*70000
 with pytest.raises(ValueError):module().render('jira-picker',data)

def test_cli_rejects_bad_json_without_echoing_payload():
 r=subprocess.run([sys.executable,str(SCRIPT),'--template','jira-picker','--config','-'],input='{"secret":"PRIVATE-CANARY",',capture_output=True,text=True,encoding='utf-8')
 assert r.returncode!=0
 assert 'PRIVATE-CANARY' not in r.stdout+r.stderr

def test_literal_template_delimiters_in_data_are_preserved():
 data=config('jira-live');data['TITULO']='Meeting {{date}}'
 html=module().render('jira-live',data)
 start=html.index('const CONFIG = ')+len('const CONFIG = ')
 assert json.loads(html[start:html.index(';',start)])==data

def test_Claude06_renderer_references_explicitly_pass_a_json_file_path():
 refs=[ROOT/'skills/jira-sync/references/destination-and-types.md',ROOT/'skills/confluence-publish/references/wizard.md']
 for ref in refs:
  text=ref.read_text(encoding='utf-8')
  assert '--config "$CONFIG_FILE"' in text
  assert 'ruta' in text
 notes=(ROOT/'docs/atlassian-connector-notes.md').read_text(encoding='utf-8')
 assert '{{SERVER_*}}' not in notes
 assert 'render-artifact.py' in notes
