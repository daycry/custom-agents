"""Audit H-45: the active bundle's kit path is injected, so no `find` of 7.7 s per block."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys

import pytest

import test_hooks_shell as legacy

ROOT = Path(__file__).resolve().parents[1]
SHARED = (ROOT / 'agent-kits/shared').as_posix()
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


def session_module():
    import importlib.util
    spec = importlib.util.spec_from_file_location('kit_session_context', ROOT / 'hooks/session-context.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_session_start_block_carries_the_active_kit(tmp_path, monkeypatch):
    project, _ = legacy.proyecto(tmp_path)
    (project / '.claude/dev.json').write_text('{"sesion":{"memoria":false}}', encoding='utf-8')
    monkeypatch.setenv('CLAUDE_PLUGIN_ROOT', str(ROOT))
    out = session_module().compose({'source': 'startup', 'session_id': 'h45'}, root=str(project))
    context = json.loads(out)['hookSpecificOutput']['additionalContext']
    lines = [l for l in context.splitlines() if 'SHAREDKIT=' in l]
    assert len(lines) == 1 and f'SHAREDKIT="{SHARED}"' in lines[0]
    assert 'find' in lines[0] and context.splitlines()[0] == lines[0]


def run_brief(tmp_path, *extra):
    folder = tmp_path / 'proyecto/docs/roadmap/2026-01-01-demo'
    folder.mkdir(parents=True)
    (folder / 'tasks.md').write_text(LEDGER, encoding='utf-8')
    env = {k: v for k, v in os.environ.items() if k != 'CLAUDE_PLUGIN_ROOT'}
    result = subprocess.run([sys.executable, str(ROOT / 'agent-kits/shared/task-brief.py'), str(folder), 'T-01',
                             '--sin-lint', '--constitucion', str(folder / 'no.md'), *extra],
                            capture_output=True, text=True, encoding='utf-8', env=env, timeout=120)
    assert result.returncode == 0, result.stderr
    return result.stdout


def test_the_brief_carries_the_kit_and_a_subagent_needs_no_find(tmp_path):
    brief = run_brief(tmp_path)
    match = re.search(r'SHAREDKIT="([^"]+)"', brief)
    assert match and match[1] == SHARED
    assert '(úsalo; sin `find`)' in brief
    # A bash without CLAUDE_PLUGIN_ROOT and without any bundle in cwd resolves the kit from the brief alone.
    bash = legacy.BASH
    if not bash:
        pytest.skip('bash unavailable')
    env = {k: v for k, v in os.environ.items() if k != 'CLAUDE_PLUGIN_ROOT'}
    proc = subprocess.run([bash, '-c', f'SHAREDKIT="{match[1]}"; [ -f "$SHAREDKIT/ledger-lint.py" ] && echo resolved'],
                          cwd=tmp_path, capture_output=True, text=True, encoding='utf-8', errors='replace', env=env, timeout=60)
    assert proc.stdout.strip() == 'resolved', proc.stderr


def test_the_convention_documents_the_injected_kit_first():
    for rel in ('docs/CONVENTIONS.md', 'docs/en/CONVENTIONS.md'):
        text = (ROOT / rel).read_text(encoding='utf-8')
        assert 'SHAREDKIT=' in text and 'SessionStart' in text, rel
