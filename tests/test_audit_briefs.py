"""R4-R6: retain valid contracts and scope hook side effects to project docs."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load(relative, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_R5_brief_preserves_heading_criteria_and_following_verification(tmp_path):
    tb = load('agent-kits/shared/task-brief.py', 'audit_brief_headers')
    lint = load('agent-kits/shared/ledger-lint.py', 'audit_brief_lint')
    text = ('## Fase 1\n\n### T-01 — Work\n- **Estado**: borrador\n'
            '### Criterios de aceptación\n- [ ] Unique required behavior.\n'
            '- **Verificación**: python check.py → exit 0\n\n### T-02 — Other\n')
    parsed = lint.parse_ledger(text)
    assert parsed['tareas'][0]['criterios'] == ['Unique required behavior.']
    chunk, _ = tb._seccion_tarea(text, 'T-01')
    assert 'Unique required behavior.' in chunk
    assert 'python check.py' in chunk
    assert 'T-02' not in chunk


@pytest.mark.parametrize('design,task', [
    ('src/adapter/', 'src/adapter/client.py'),
    ('src/adapter.py', './src/adapter.py'),
    ('src/adapter/**', 'src/adapter/client.py'),
    ('src/adapter.py', 'src/'),
    ('src/adapter.py', '.'),
])
def test_R6_design_paths_retain_related_approved_decisions(tmp_path, design, task):
    tb = load('agent-kits/shared/task-brief.py', 'audit_brief_design')
    (tmp_path / 'design.md').write_text(
        '## 5. Impacto en módulos y ficheros\n\n| Módulo | Cambio |\n|---|---|\n'
        f'| `{design}` | updated |\n', encoding='utf-8')
    assert tb._tarea_toca_diseno(str(tmp_path), f'- **Archivos**: `{task}`\n')


@pytest.mark.parametrize('path,marked', [
    ('mydocs/note.md', False), ('../outside/docs/note.md', False),
    ('docs/note.md', True), ('docs/confluence/note.md', False),
    ('docs/security-scan/note.md', False),
])
def test_R4_document_marker_is_scoped_to_project_docs(tmp_path, path, marked):
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(tmp_path), CLAUDE_PLUGIN_ROOT=str(ROOT))
    result = subprocess.run(['node', str(ROOT / 'hooks/run-hook.mjs'), 'mark-docs-pending.sh', '--runtime=claude'],
                            input=json.dumps({'tool_name': 'Write', 'tool_input': {'file_path': path}}),
                            cwd=tmp_path, env=env, capture_output=True, text=True, encoding='utf-8', timeout=10)
    assert result.returncode == 0
    assert (tmp_path / '.claude/.confluence-pending').exists() is marked
