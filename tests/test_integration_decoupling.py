"""The local lifecycle selects a project port instead of a mandatory provider."""
from pathlib import Path
import re

import pytest

ROOT=Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('role',['analyst','planner','implementer','qa','evaluator','documenter'])
def test_core_role_uses_project_integration_contract(role):
    text=(ROOT/f'agents/{role}.md').read_text(encoding='utf-8')
    assert 'project-integrations.md' in text
    frontmatter=text.split('---',2)[1]
    assert not re.search(r'^\s+- (jira-sync|confluence-publish|confluence-pull)\s*(?:#.*)?$',frontmatter,re.M)


def test_setup_chooses_functions_before_vendors():
    text=(ROOT/'commands/setup.md').read_text(encoding='utf-8')
    assert '.claude/integrations.json' in text
    assert 'Redmine' in text
    assert 'project-integrations.md' in text
    assert '¿Sincronizar la documentación con Confluence?' not in text


def test_core_workflow_has_no_direct_jira_flow_execution():
    for path in [ROOT/'commands/dev-cycle.md',ROOT/'skills/adversarial-review/SKILL.md']:
        text=path.read_text(encoding='utf-8')
        assert 'project-integrations.md' in text
        assert 'jira-flow.py' not in text


def test_gap_a01_confluence_skill_map_respects_constitution():
    assert len((ROOT/'skills/confluence-publish/SKILL.md').read_text(encoding='utf-8').splitlines())<=200


def test_gap_a02_documenter_contract_has_no_direct_provider_callback():
    text=(ROOT/'docs/agents/documenter.md').read_text(encoding='utf-8')
    assert 'invoca la skill compartida `confluence-publish`' not in text
    for file in ['docs/agents/ROLES.md','docs/agents/CONTRACTS.md']:
        text=(ROOT/file).read_text(encoding='utf-8')
        assert 'project-integrations.md' in text
        assert 'tabla única en `commands/dev-cycle.md`' not in text


def test_gap_a03_core_outputs_degrade_without_optional_presentation_modules():
    qa=(ROOT/'agents/qa.md').read_text(encoding='utf-8')
    assert 'PDF opcional' in qa
    assert 'plantilla `report.md` + PDF vía' not in qa
    for command in ['roadmap-status','roadmap-brief']:
        text=(ROOT/f'commands/{command}.md').read_text(encoding='utf-8')
        assert 'sin bloquear' in text and 'opcional' in text.lower()
        assert 'disponible' in text


def test_gaps_a04_a05_phase3_descriptions_use_the_optional_adapter():
    for file,old in [('docs/FLOWS.md','subagentes o Jira'),('docs/en/FLOWS.md','subagents or Jira')]:
        text=(ROOT/file).read_text(encoding='utf-8')
        assert old not in text
        assert 'project-integrations.md' in text

    es=(ROOT/'docs/FLOWS.md').read_text(encoding='utf-8')
    en=(ROOT/'docs/en/FLOWS.md').read_text(encoding='utf-8')
    assert 'núcleo de `commands/dev-cycle.md` (fuente única)' not in es
    assert 'the `commands/dev-cycle.md` core (single source)' not in en
