"""Audit H-41/H-42: capabilities and integrations are resolved once per cycle.

A role whose brief, ledger or prompt already carries the selection (or says
"no integrations") must not re-read the fragment nor re-run the router.
"""
import importlib.util
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
AGENTS = ('analyst', 'architect', 'documenter', 'evaluator', 'implementer',
          'knowledge-curator', 'nemesis', 'planner', 'qa', 'reviewer')
WITH_EVENTS = ('analyst', 'documenter', 'evaluator', 'implementer', 'planner', 'qa')


def text(agent):
    return (ROOT / 'agents' / f'{agent}.md').read_text(encoding='utf-8')


def section(body, title):
    match = re.search(r'^## ' + re.escape(title) + r'\n(.*?)(?=^#{1,2} )', body, re.S | re.M)
    assert match, title
    return ' '.join(match[1].split())


@pytest.mark.parametrize('agent', AGENTS)
def test_capabilities_already_in_the_brief_are_not_recomputed(agent):
    body = section(text(agent), 'Contexto de capacidades')
    assert 'ya traen la selección' in body
    assert 'no leas `capability-check.md`' in body
    assert 'capability-route.py' in body


@pytest.mark.parametrize('agent', WITH_EVENTS)
def test_integrations_resolved_by_the_orchestrator_are_not_rerun(agent):
    first = ' '.join(text(agent).split('\n## ', 1)[0].split('---', 2)[2].split())
    assert 'Integraciones opcionales' in first
    assert '«sin integraciones»' in first
    assert 'integration-route.py' in first


def test_the_orchestrator_resolves_both_once_per_cycle():
    core = ' '.join((ROOT / 'commands/dev-cycle.md').read_text(encoding='utf-8').split()).lower()
    assert 'una vez por ciclo' in core
    assert '«sin integraciones»' in core


def test_the_brief_tells_the_role_not_to_read_the_fragment():
    spec = importlib.util.spec_from_file_location('tb_once', ROOT / 'agent-kits/shared/task-brief.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    mounted = '\n'.join(module._seccion_capacidades('- **Capacidades**: stack-practices'))
    assert 'no leas `capability-check.md`' in mounted
    assert 'skills/stack-practices/SKILL.md' in mounted
