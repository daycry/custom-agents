from pathlib import Path
import re
import pytest
yaml=pytest.importorskip("yaml")
ROOT=Path(__file__).resolve().parents[1]

def workflow(name):
 return yaml.safe_load((ROOT/'.github/workflows'/name).read_text(encoding='utf-8'))

@pytest.mark.parametrize('name',['ci.yml','headless.yml','release.yml'])
def test_actions_are_immutable_and_default_token_is_readonly(name):
 data=workflow(name)
 assert data.get('permissions')=={'contents':'read'}
 for job in data['jobs'].values():
  for step in job.get('steps',[]):
   if 'uses' in step:
    assert re.fullmatch(r'[^@]+@[0-9a-f]{40}',step['uses']),step['uses']
   if str(step.get('uses','')).startswith('actions/checkout@'):
    assert step.get('with',{}).get('persist-credentials') is False

def test_headless_secrets_are_limited_to_llm_consumers():
 job=workflow('headless.yml')['jobs']['headless']
 assert 'ANTHROPIC_API_KEY' not in job.get('env',{})
 for step in job['steps']:
  env=step.get('env',{});run=step.get('run','')
  consumer='evals/run.py' in run or 'claude -p' in run
  assert ('ANTHROPIC_API_KEY' in env)==consumer,step.get('name',step.get('uses'))
  if consumer:assert env['ANTHROPIC_API_KEY']=='${{ secrets.ANTHROPIC_API_KEY }}'
  if step.get('id') and step['id']!='gate':
   assert "steps.gate.outputs.skip == 'false'" in step.get('if',''),step['id']
 gate=next(step for step in job['steps'] if step.get('id')=='gate')
 assert gate['env']['HAS_ANTHROPIC_KEY']=="${{ secrets.ANTHROPIC_API_KEY != '' }}"
 installer=next(step for step in job['steps'] if step.get('id')=='install')
 assert re.search(r'@anthropic-ai/claude-code@\d+\.\d+\.\d+',installer['run'])

def test_release_build_has_no_write_token_and_publish_is_separate():
 data=workflow('release.yml')
 build=data['jobs']['build'];publish=data['jobs']['publish']
 assert build.get('permissions',data['permissions'])=={'contents':'read'}
 assert publish.get('permissions')=={'contents':'write'}
 assert publish['needs']=='build'
 assert not any('run' in step for step in publish['steps'])
