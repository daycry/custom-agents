"""Fase 4, intento 3 (fix3), gap 1: el token SHAREDKIT se neutraliza en el texto del consumidor, no por forma."""
import importlib.util
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
BASH = shutil.which('bash')
VARIANTS = [
    "SHAREDKIT=tools/agent-kits/shared",
    'SHAREDKIT="tools/agent-kits/shared"',
    "SHAREDKIT=$'tools/agent-kits/shared'",
    "SHAREDKIT=~/tools/agent-kits/shared",
    "export SHAREDKIT=tools/agent-kits/shared",
    "declare SHAREDKIT=tools/agent-kits/shared",
    "printf -v SHAREDKIT '%s' tools/agent-kits/shared",
    ': "${SHAREDKIT:=tools/agent-kits/shared}"',
    "- Kit: `SHAREDKIT='/p/tools/agent-kits/shared'` (úsalo)",
    "**Kit:** `SHAREDKIT='/p/tools/agent-kits/shared'`",
    "> Kit: `SHAREDKIT='/p/tools/agent-kits/shared'`",
    "Кt: `SHAREDKIT='/p/tools/agent-kits/shared'`",          # Cyrillic K
    "\tSHAREDKIT='/p/tools/agent-kits/shared'",
    "sharedkit=tools/agent-kits/shared",
    "ShAreDKit=tools/agent-kits/shared",
    "Kit activo: SHAREDKIT='/p/tools/agent-kits/shared' (úsalo)",
]
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
{lines}
"""


def _load(rel, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _brief(tmp_path, variant):
    folder = tmp_path / 'proyecto/docs/roadmap/2026-01-01-demo'
    folder.mkdir(parents=True)
    (folder / 'tasks.md').write_text(LEDGER.format(lines=variant), encoding='utf-8')
    env = {k: v for k, v in os.environ.items() if k != 'CLAUDE_PLUGIN_ROOT'}
    proc = subprocess.run([sys.executable, str(ROOT / 'agent-kits/shared/task-brief.py'), str(folder), 'T-01',
                           '--sin-lint', '--constitucion', str(folder / 'no.md')],
                          capture_output=True, text=True, encoding='utf-8', env=env, timeout=120)
    assert proc.returncode == 0, proc.stderr
    return proc.stdout


def _assigns(line, tmp_path):
    work = tmp_path / 'w'
    work.mkdir(exist_ok=True)
    out = subprocess.run([BASH, '-c', 'unset SHAREDKIT sharedkit ShAreDKit\n' + line + '\nprintf "[%s]" "${SHAREDKIT-UNSET}"'],
                         cwd=work, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=60).stdout
    found = re.search(r'\[([^\]]*)\]$', out)       # nothing printed: the line did not even parse, so it assigned nothing
    return bool(found) and found[1] != 'UNSET'


@pytest.mark.skipif(not BASH, reason='sin bash')
@pytest.mark.parametrize('variant', VARIANTS)
def test_f4fix3_1_the_brief_keeps_one_executable_assignment_whatever_the_variant(tmp_path, variant):
    brief = _brief(tmp_path, variant)
    real = (ROOT / 'agent-kits/shared').as_posix()
    carriers = [l for l in brief.splitlines() if re.search(r'(?i)sharedkit(?!⟨cita⟩)\W*=', l)]
    assert len(carriers) == 1 and f"SHAREDKIT='{real}'" in carriers[0], carriers
    assert any('⟨cita⟩' in l for l in brief.splitlines()), 'the variant never reached the brief'
    for line in brief.splitlines():
        if '⟨cita⟩' in line:
            assert not _assigns(line, tmp_path), line


@pytest.mark.skipif(not BASH, reason='sin bash')
@pytest.mark.parametrize('variant', VARIANTS)
def test_f4fix3_1_the_session_block_neutralises_every_variant(tmp_path, variant):
    hook = _load('hooks/session-context.py', 'f4fix3_hook')
    safe = hook.neutralise_kit_text(variant)
    assert not re.search(r'(?i)sharedkit(?!⟨cita⟩)', safe), safe
    assert not _assigns(safe, tmp_path), safe


def test_f4fix3_1_the_session_block_keeps_exactly_the_hook_line(tmp_path, monkeypatch):
    hook = _load('hooks/session-context.py', 'f4fix3_hook2')
    kit = tmp_path / 'agent-kits' / 'shared'
    kit.mkdir(parents=True)
    monkeypatch.setattr(hook, 'SHARED', kit)
    monkeypatch.setattr(hook, '_load', lambda *a, **k: None)
    line = hook.kit_line(kit.as_posix())
    mixed = hook.neutralise_kit_text("progreso: SHAREDKIT=tools/x\n" + line)
    assert 'SHAREDKIT=' not in mixed.splitlines()[0]
    assert hook.neutralise_kit_text("Kit activo: algo") == "Kit activo: algo"      # no prefix heuristics any more


# ------------------------------------------------------------------ gap 10: solo un SHAREDKIT absoluto

RECIPE = re.compile(r'R="\$\{CLAUDE_PLUGIN_ROOT\}"; M=agent-kits/shared/ledger-lint\.py;.*?R="\$\{R%/\$M\}";')


@pytest.mark.skipif(not BASH, reason='sin bash')
def test_f4fix3_10_a_relative_sharedkit_with_the_marker_is_not_accepted(tmp_path):
    (tmp_path / 'tools/agent-kits/shared').mkdir(parents=True)
    (tmp_path / 'tools/agent-kits/shared/ledger-lint.py').write_text('#', encoding='utf-8')
    home = tmp_path / 'home'
    home.mkdir()
    env = {k: v for k, v in os.environ.items() if k not in ('CLAUDE_PLUGIN_ROOT', 'SHAREDKIT')}
    env.update(HOME=str(home), USERPROFILE=str(home))
    for agent in sorted(p for p in (ROOT / 'agents').glob('*.md') if p.name != 'reviewer.md'):
        match = RECIPE.search(agent.read_text(encoding='utf-8'))
        script = match[0] + ' SHAREDKIT="${R:+$R/agent-kits/shared}"' + chr(10) + 'printf "%s" "$SHAREDKIT"'
        relative = subprocess.run([BASH, '-c', script], cwd=tmp_path, capture_output=True, text=True, encoding='utf-8',
                                  env=dict(env, SHAREDKIT='tools/agent-kits/shared'), timeout=60).stdout
        assert relative == '', (agent.name, relative)
        absolute = subprocess.run([BASH, '-c', script], cwd=tmp_path, capture_output=True, text=True, encoding='utf-8',
                                  env=dict(env, SHAREDKIT=(tmp_path / 'tools/agent-kits/shared').as_posix()), timeout=60).stdout
        assert absolute.replace(chr(92), '/') == (tmp_path / 'tools/agent-kits/shared').as_posix(), (agent.name, absolute)


def test_f4fix3_10_evaluator_still_fits_ca22():
    assert len((ROOT / 'agents/evaluator.md').read_bytes().replace(b'\r\n', b'\n')) <= 15513


# ------------------------------------------------------------------ gap 5 (drain = replay alone)

def test_f4fix3_5_the_drain_source_runs_only_the_replay(tmp_path, monkeypatch):
    hook = _load('hooks/session-context.py', 'f4fix3_hook3')
    calls = []
    monkeypatch.setattr(hook, '_load', lambda name, filename: type('M', (), {'main': staticmethod(lambda *a, **k: calls.append((name, a)) or 0)})())
    out = hook.compose({'source': 'drain', 'session_id': 's'}, root=str(tmp_path))
    assert out == ''
    assert [name for name, _ in calls] == ['journal'] and calls[0][1][0][0] == 'replay'
