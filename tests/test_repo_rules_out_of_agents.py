"""plugin-audit-2 T-22 (2.8, 2.13): this repo's rules leave the generic agents; qa sin UI on demand.

- No agent prompt names `export-interop` or `CONTRACTS.md`: E2 (regenerate what is generated)
  and E3 (update what describes the piece) become a PROJECT rule in
  `skills/project-extensions/references/custom-agents-repo.md`, which keeps the mechanism.
- planner and implementer keep a generic gate (generated files and describing pieces in the
  same task) so a consumer project loses nothing, plus one pointer to the repo rules.
- qa reads `agent-kits/qa/references/sin-ui.md` only when the plan declares the marker; the
  reference keeps every rule of the old paragraph.
- planner, implementer and qa lose at least 3,500 characters together against the pre-T-22
  baseline in the fixture (figure adjusted by the user on 2026-11-27, k7).
"""
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
REPO_RULES = ROOT / 'skills/project-extensions/references/custom-agents-repo.md'
SIN_UI = ROOT / 'agent-kits/qa/references/sin-ui.md'
BASELINE = ROOT / 'tests/fixtures/repo-rules-baseline.json'
MARKER = 'test-plan: n/a (sin UI)'


def lf(path):
    return path.read_bytes().decode('utf-8').replace('\r\n', '\n')


def flat(text):
    return ' '.join(text.split())


@pytest.mark.parametrize('agent', sorted(p.name for p in (ROOT / 'agents').glob('*.md')))
def test_no_agent_names_export_interop_or_contracts(agent):
    text = lf(ROOT / 'agents' / agent)
    assert 'export-interop' not in text and 'CONTRACTS.md' not in text, agent


def test_repo_rules_keep_the_e2_e3_mechanism():
    rules = flat(lf(REPO_RULES))
    for needed in ('E2', 'E3', '`interop/**`', 'export-interop.py --check', 'docs/agents/CONTRACTS.md',
                   '«Piezas que describen»', 'GOT-009', 'scope-check.py', 'Lente A',
                   'regenerar `interop/`', '`docs/agents/<x>.md`', 'evals/cases/<kind>-<nombre>.json'):
        assert needed in rules, needed
    assert re.search(r'que el `planner` ya puso en `Archivos`', rules) and re.search(r'implementer[^.]*regenera', rules)


@pytest.mark.parametrize('agent', ('planner', 'implementer'))
def test_generic_gate_and_one_pointer_stay_in_the_agent(agent):
    text = flat(lf(ROOT / 'agents' / f'{agent}.md'))
    assert text.count('custom-agents-repo.md') == 1, agent
    assert 'generado' in text.lower() and 'describe' in text.lower(), agent
    assert 'misma tarea' in text, agent


def test_qa_reads_the_sin_ui_reference_only_when_the_marker_is_declared():
    qa = lf(ROOT / 'agents/qa.md')
    line = next(l for l in qa.splitlines() if MARKER in l and 'frontmatter' in l)
    assert 'agent-kits/qa/references/sin-ui.md' in line or '$QAKIT/references/sin-ui.md' in line, line
    assert len(line.encode('utf-8')) <= 900, len(line.encode('utf-8'))
    assert 'ADR-017' in line and 'una sola vez' in line
    ref = flat(lf(SIN_UI))
    for needed in ('ℹ️, no ✅', 'eximidos', 'eximidos_exigidos', 'rutas_ui', 'rutas_ui_origen', 'rutas_ui_degradado',
                   'marcador_no_canonico', 'coverage-check', 'ledger-lint', 'ni instales Playwright'):
        assert needed in ref, needed


def test_the_three_agents_lose_at_least_three_and_a_half_thousand_characters():
    # Criterion adjusted by the user on 2026-11-27 (k7): ≥ 3.500 characters (LF) between the three
    base = json.loads(BASELINE.read_text(encoding='utf-8'))['chars_lf']
    now = {k: len(lf(ROOT / k)) for k in base}
    assert sum(base.values()) - sum(now.values()) >= 3500, (base, now)

