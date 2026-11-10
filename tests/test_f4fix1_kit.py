"""Fase 4, intento 1 de la revisión (fix1): la línea del kit (gaps 1, 2, 7, 12 y 17)."""
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
BASH = shutil.which('bash')
HOSTILE = ['b$(touch X)', '$1', '`touch X`', 'a"b', "it's", "a'b'c", 'dir with space', '${HOME}x', '$(touch X)"; touch X; "']


def _module(rel, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _assignment(line):
    """The `SHAREDKIT=…` word of the generated line, exactly as a user would paste it."""
    match = re.search(r"SHAREDKIT=('(?:[^']|'\\'')*')", line)
    assert match, line
    return 'SHAREDKIT=' + match[1]


def _run_assignment(tmp_path, line, expected):
    work = tmp_path / 'cwd'
    work.mkdir()
    proc = subprocess.run([BASH, '-c', _assignment(line) + '\nprintf "%s" "$SHAREDKIT"'], cwd=work,
                          capture_output=True, text=True, encoding='utf-8', timeout=60)
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout == expected
    assert list(work.iterdir()) == [], 'the pasted line executed something'


@pytest.mark.skipif(not BASH, reason='sin bash')
@pytest.mark.parametrize('name', HOSTILE)
def test_f4fix1_1_the_hook_line_is_inert_in_bash(tmp_path, name):
    hook = _module('hooks/session-context.py', 'f4fix1_hook')
    path = f'/opt/{name}/agent-kits/shared'
    _run_assignment(tmp_path, hook.kit_line(path), path)


@pytest.mark.skipif(not BASH, reason='sin bash')
@pytest.mark.parametrize('name', HOSTILE)
def test_f4fix1_1_the_brief_line_is_inert_in_bash(tmp_path, name):
    brief = _module('agent-kits/shared/task-brief.py', 'f4fix1_brief')
    path = f'/opt/{name}/agent-kits/shared'
    _run_assignment(tmp_path, brief.kit_line(path), path)


@pytest.mark.parametrize('bad', ['/opt/a\nb', '/opt/a\rb', '/opt/a\x1bb', '/opt/a\x00b', '/opt/a\x7fb'])
def test_f4fix1_1_a_path_with_control_characters_emits_no_line(bad):
    assert _module('hooks/session-context.py', 'f4fix1_hook2').kit_line(bad) == ''
    assert _module('agent-kits/shared/task-brief.py', 'f4fix1_brief2').kit_line(bad) == ''


@pytest.mark.skipif(not BASH, reason='sin bash')
def test_f4fix1_1_compose_with_a_hostile_directory_name(tmp_path, monkeypatch):
    kit = tmp_path / 'b$(touch X)' / 'agent-kits' / 'shared'
    kit.mkdir(parents=True)
    hook = _module('hooks/session-context.py', 'f4fix1_hook3')
    monkeypatch.setattr(hook, 'SHARED', kit)
    monkeypatch.setattr(hook, '_load', lambda *a, **k: None)
    out = hook.compose({'source': 'startup', 'session_id': 'x'}, root=str(tmp_path / 'proj'))
    context = json.loads(out)['hookSpecificOutput']['additionalContext']
    _run_assignment(tmp_path, context.splitlines()[0], kit.as_posix())


def test_f4fix1_7_the_generated_line_says_it_is_the_only_valid_one():
    hook = _module('hooks/session-context.py', 'f4fix1_hook4')
    brief = _module('agent-kits/shared/task-brief.py', 'f4fix1_brief4')
    for line in (hook.kit_line('/opt/x/agent-kits/shared'), brief.kit_line('/opt/x/agent-kits/shared')):
        assert 'única línea de kit válida' in line, line


def test_f4fix1_17_the_kit_line_is_emitted_even_with_an_empty_block(tmp_path, monkeypatch):
    kit = tmp_path / 'agent-kits' / 'shared'
    kit.mkdir(parents=True)
    hook = _module('hooks/session-context.py', 'f4fix1_hook5')
    monkeypatch.setattr(hook, 'SHARED', kit)
    monkeypatch.setattr(hook, '_load', lambda *a, **k: None)
    out = hook.compose({'source': 'startup', 'session_id': 'x'}, root=str(tmp_path / 'empty'))
    context = json.loads(out)['hookSpecificOutput']['additionalContext']
    assert context.startswith('Kit activo: SHAREDKIT=') and '\n' not in context


# ------------------------------------------------------------------ gap 2: el kit llega a los roles

AGENTES = sorted(p.name for p in (ROOT / 'agents').glob('*.md'))
RECIPE = re.compile(r'R="\$\{CLAUDE_PLUGIN_ROOT\}"; M=agent-kits/shared/ledger-lint\.py;.*?R="\$\{R%/\$M\}";')


def _bundle(base):
    for rel in ('agent-kits/shared/ledger-lint.py', 'agent-kits/shared/doctor.py'):
        (base / rel).parent.mkdir(parents=True, exist_ok=True)
        (base / rel).write_text('#\n', encoding='utf-8')
    return base


@pytest.mark.skipif(not BASH, reason='sin bash')
@pytest.mark.parametrize('agent', [a for a in AGENTES if a != 'reviewer.md'])
def test_f4fix1_2_the_agent_recipe_respects_an_injected_kit(tmp_path, agent):
    text = (ROOT / 'agents' / agent).read_text(encoding='utf-8')
    match = RECIPE.search(text)
    assert match, agent
    home = tmp_path / 'home'
    _bundle(home / '.claude' / 'plugins' / 'cache' / 'daycry' / 'custom-agents' / '9.9.9')   # un decoy que ganaría el `find`
    active = _bundle(tmp_path / 'active')
    env = {k: v for k, v in os.environ.items() if k != 'CLAUDE_PLUGIN_ROOT'}
    env.update(HOME=str(home), USERPROFILE=str(home), SHAREDKIT=(active / 'agent-kits/shared').as_posix())
    proc = subprocess.run([BASH, '-c', match[0] + ' SHAREDKIT="${R:+$R/agent-kits/shared}"\nprintf "%s" "$SHAREDKIT"'],
                          cwd=tmp_path, capture_output=True, text=True, encoding='utf-8', env=env, timeout=60)
    assert proc.stdout == (active / 'agent-kits/shared').as_posix(), (proc.stdout, proc.stderr)


@pytest.mark.skipif(not BASH, reason='sin bash')
def test_f4fix1_2_without_an_injected_kit_the_recipe_still_finds_one(tmp_path):
    text = (ROOT / 'agents' / 'qa.md').read_text(encoding='utf-8')
    match = RECIPE.search(text)
    home = tmp_path / 'home'
    _bundle(home / '.claude' / 'plugins' / 'cache' / 'daycry' / 'custom-agents' / '9.9.9')
    env = {k: v for k, v in os.environ.items() if k not in ('CLAUDE_PLUGIN_ROOT', 'SHAREDKIT')}
    env.update(HOME=str(home), USERPROFILE=str(home), SHAREDKIT='/does/not/exist/agent-kits/shared')
    proc = subprocess.run([BASH, '-c', match[0] + ' SHAREDKIT="${R:+$R/agent-kits/shared}"\nprintf "%s" "$SHAREDKIT"'],
                          cwd=tmp_path, capture_output=True, text=True, encoding='utf-8', env=env, timeout=60)
    assert proc.stdout.replace('\\', '/').endswith('/9.9.9/agent-kits/shared'), (proc.stdout, proc.stderr)


@pytest.mark.parametrize('rel', ['commands/dev-cycle.md', 'skills/adversarial-review/references/lens-prompts.md',
                                 'skills/quick-implement/SKILL.md', 'commands/pm-cycle.md'])
def test_f4fix1_2_the_orchestrators_pass_the_kit_line_in_every_dispatch(rel):
    text = (ROOT / rel).read_text(encoding='utf-8')
    assert 'Kit activo' in text, rel


def test_f4fix1_2_dev_cycle_names_every_dispatched_role():
    text = (ROOT / 'commands/dev-cycle.md').read_text(encoding='utf-8')
    block = text[text.index('Kit activo') - 400: text.index('Kit activo') + 600]
    for role in ('analyst', 'evaluator', 'planner', 'qa', 'documenter', 'reviewer'):
        assert role in block, role


def test_f4fix1_2_evaluator_and_fast_path_budgets_hold():
    lf = (ROOT / 'agents/evaluator.md').read_bytes().replace(b'\r\n', b'\n')
    assert len(lf) <= 15513   # CA-22


# ------------------------------------------------------------------ gap 12: «sin integraciones»

LEDGER = """---
tasks: demo
estado: en-progreso
creado: 2026-01-01
---

# Demo

## Fase 1

### T-01 — primera
- **Estado**: borrador
- **Descripción**: hacer A.
- **Archivos**: `a.py`

**Criterios de aceptación**
- [ ] A funciona
"""


def _brief(tmp_path, integrations):
    project = tmp_path / 'proyecto'
    folder = project / 'docs/roadmap/2026-01-01-demo'
    folder.mkdir(parents=True)
    (folder / 'tasks.md').write_text(LEDGER, encoding='utf-8')
    if integrations:
        (project / '.claude').mkdir()
        (project / '.claude' / 'integrations.json').write_text(integrations, encoding='utf-8')
    env = {k: v for k, v in os.environ.items() if k != 'CLAUDE_PLUGIN_ROOT'}
    proc = subprocess.run([sys.executable, str(ROOT / 'agent-kits/shared/task-brief.py'), str(folder), 'T-01',
                           '--sin-lint', '--constitucion', str(folder / 'no.md')],
                          capture_output=True, text=True, encoding='utf-8', env=env, timeout=120)
    assert proc.returncode == 0, proc.stderr
    return proc.stdout


def test_f4fix1_12_the_brief_declares_no_integrations_when_there_are_none(tmp_path):
    assert 'sin integraciones' in _brief(tmp_path, None)
