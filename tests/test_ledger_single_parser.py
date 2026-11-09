"""H-22, H-23, H-26 y menores de ledger-lint (auditoría 2026-11-09): un solo troceo del ledger.

`scope-check.py`, `coverage-check.py` y `jira-flow.py` trocean las tareas con el parser de
`ledger-lint.py`: lo que está dentro de un bloque de código o en una sección posterior (`## …`)
no es de ninguna tarea. El resumen dentro de un bloque de código no cuenta y el `estado` del
ledger se valida contra el vocabulario.
"""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load(rel, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


LINT = load('agent-kits/shared/ledger-lint.py', 'single_parser_lint')
SCOPE = load('agent-kits/shared/scope-check.py', 'single_parser_scope')
JIRA = load('skills/jira-sync/scripts/jira-flow.py', 'single_parser_jira')

FENCE = "```"
LEDGER = f"""---
tasks: demo
estado: en-progreso
---
# Demo

> Ledger canónico de progreso.

## Resumen de progreso

| Fase | Completadas | Total | Progreso |
|---|---|---|---|
| Fase 1 | 0 | 1 | 0% |

## Fase 1 — Trabajo

### T-01 — Real

- **Estado**: en-progreso
- **Archivos**: `src/real.py`
- **Cubre (tests)**: —
- **Verificación**:
  - `pytest tests/test_a.py` → pasa
  - `pytest tests/test_b.py` → pasa

**Criterios de aceptación**
- [ ] a

Ejemplo citado en la tarea:

{FENCE}markdown
- **Archivos**: `**/*`
### T-99 — Fantasma
- **Archivos**: `**/*`
- **Cubre (tests)**: E2E-99
{FENCE}

## Notas

- **Archivos**: `docs/**`
"""


def test_h22_scope_check_ignora_archivos_en_bloques_de_codigo_y_secciones_posteriores():
    patrones = SCOPE.patrones_del_ledger(LEDGER, LINT.parse_ledger)
    assert patrones == [('src/real.py', 'T-01')], patrones
    sin_valla = LEDGER.split('Ejemplo citado', 1)[0] + '## Notas\n\n- **Archivos**: `docs/**`\n'
    assert SCOPE.patrones_del_ledger(sin_valla, LINT.parse_ledger) == [('src/real.py', 'T-01')]


def test_h23_coverage_check_no_crea_tareas_fantasma_desde_un_bloque_de_codigo(tmp_path):
    tasks = tmp_path / 'tasks.md'
    tasks.write_text(LEDGER, encoding='utf-8')
    plan = tmp_path / 'test-plan.md'
    plan.write_text('# Test plan\n## E2E-01 — flujo\n', encoding='utf-8')
    run = subprocess.run([sys.executable, str(ROOT / 'agent-kits/qa/coverage-check.py'), str(tasks), str(plan)],
                         capture_output=True, text=True, encoding='utf-8', errors='replace')
    data = json.loads(run.stdout.strip().splitlines()[-1])
    assert data['broken_refs'] == 0, run.stdout
    assert data['tasks_sin_cobertura'] == ['T-01'], data


def test_h26_jira_flow_lleva_la_verificacion_entera_y_no_cruza_lineas():
    detalle = JIRA.detalle_tarea(LEDGER, 'T-01', LINT)
    assert 'test_a.py' in detalle['verificacion'] and 'test_b.py' in detalle['verificacion'], detalle
    assert JIRA._campo('- **Descripción**:\n- **Archivos**: `x`', 'Descripción') is None
    assert JIRA.detalle_tarea(LEDGER, 'T-99', LINT) is None, 'una tarea citada en un bloque de código no existe'


def test_ledger_lint_ignora_el_resumen_dentro_de_un_bloque_de_codigo():
    citado = LEDGER.replace('## Notas', f'## Notas\n\n{FENCE}\n| Fase 1 | 7 | 9 | 77% |\n{FENCE}')
    errors, _ = LINT.lint('tasks.md', text=citado)
    assert not [e for e in errors if 'resumen' in e], errors


def test_ledger_lint_valida_el_vocabulario_del_estado_del_ledger():
    errors, _ = LINT.lint('tasks.md', text=LEDGER.replace('estado: en-progreso', 'estado: terminado', 1))
    assert any('estado del ledger' in e for e in errors), errors
    errors, _ = LINT.lint('tasks.md', text=LEDGER)
    assert not errors, errors


def test_los_ledgers_del_repo_siguen_validos():
    ledgers = sorted((ROOT / 'docs/roadmap').glob('*/tasks.md'))
    assert len(ledgers) >= 67
    malos = {}
    for path in ledgers:
        errors, _ = LINT.lint(str(path))
        if errors:
            malos[path.parent.name] = errors[:2]
    assert not malos, malos


def test_h23_coverage_check_sin_el_kit_compartido_aplica_el_mismo_troceo(tmp_path):
    kit = tmp_path / 'agent-kits/qa'
    kit.mkdir(parents=True)
    (kit / 'coverage-check.py').write_bytes((ROOT / 'agent-kits/qa/coverage-check.py').read_bytes())
    tasks = tmp_path / 'tasks.md'
    tasks.write_text(LEDGER, encoding='utf-8')
    plan = tmp_path / 'test-plan.md'
    plan.write_text('# Test plan\n## E2E-01 — flujo\n', encoding='utf-8')
    run = subprocess.run([sys.executable, str(kit / 'coverage-check.py'), str(tasks), str(plan)],
                         capture_output=True, text=True, encoding='utf-8', errors='replace')
    data = json.loads(run.stdout.strip().splitlines()[-1])
    assert (data['broken_refs'], data['tasks_sin_cobertura']) == (0, ['T-01']), run.stdout
