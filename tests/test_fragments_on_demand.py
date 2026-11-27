"""plugin-audit-2 T-18 (2.3, 2.12): fragments are paid once, only when they apply.

- `capability-check.md` is a core of at most 2 KB; project/user extensions and stack
  detection move to `capability-check-detail.md`, read only when they apply. No paragraph
  of the original is lost (baseline + recorded replacements with their reason).
- The capability output is unchanged: the core keeps the exact router command.
- implementer, qa, planner and evaluator carry the constitution rule in one line and do
  not send the reader to `constitution-check.md` (that fragment is for review lens A).
- Their memory rule runs the query first and opens `knowledge-check.md` only with hits,
  without losing the duty to respect applicable ADR/lessons.
- The rationalization table is an authoring guide: implementer and qa keep their table
  but no longer point at `rationalization-table.md`.
"""
import hashlib
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SHARED = ROOT / 'agent-kits/shared'
CORE = SHARED / 'capability-check.md'
DETAIL = SHARED / 'capability-check-detail.md'
BASELINE = ROOT / 'tests/fixtures/capability-check-paragraphs.json'
WRITERS = ('implementer', 'qa', 'planner', 'evaluator')
ROUTER = 'python3 "$SHAREDKIT/capability-route.py" --project <paquete-de-la-tarea> --role <agente> --area <area> --json'


def lf(path):
    return path.read_bytes().decode('utf-8').replace('\r\n', '\n')


def paragraphs(text):
    return [' '.join(part.split()) for part in re.split(r'\n\s*\n', text) if part.strip()]


def agent(name):
    return lf(ROOT / 'agents' / f'{name}.md')


def bullet(body, title):
    match = re.search(r'^- \*\*' + re.escape(title) + r'.*$', body, re.M)
    assert match, title
    return match[0]


def test_capability_core_is_at_most_two_kilobytes():
    # ≤ 2 KB in decimal (the criterion's figure), stricter than 2 KiB
    assert len(lf(CORE).encode('utf-8')) <= 2000, len(lf(CORE).encode('utf-8'))


def test_capability_output_is_unchanged_the_core_keeps_the_exact_router_command():
    core = lf(CORE)
    assert ROUTER in core
    for needed in ('capability-catalog.json', '- **Capacidades**:', '- **Procedencia de capacidades**:',
                   'research, api, data', 'documentation', '--stack', 'knowledge-check'):
        assert needed in core, needed


def test_extensions_and_stacks_are_read_only_when_they_apply():
    core = ' '.join(lf(CORE).split())
    assert DETAIL.is_file(), 'capability-check-detail.md does not exist'
    assert 'capability-check-detail.md' in core
    assert re.search(r'[Ss]olo si[^.]*piezas propias[^.]*capability-check-detail\.md', core), core
    assert 'project-pieces.py' not in core
    detail = lf(DETAIL)
    for needed in ('project-pieces.py', '- **Extensiones**: ext-', '- **Procedencia de extensiones**:',
                   '--select <id>', '## Stacks y detección', 'codeigniter4/framework'):
        assert needed in detail, needed


def test_no_original_capability_paragraph_is_lost():
    baseline = json.loads(BASELINE.read_text(encoding='utf-8'))
    corpus = lf(CORE) + '\n\n' + lf(DETAIL)
    hashes = {hashlib.sha256(p.encode('utf-8')).hexdigest() for p in paragraphs(corpus)}
    replaced = set()
    for row in baseline['replacements']:
        own = {hashlib.sha256(p.encode('utf-8')).hexdigest() for p in paragraphs(lf(ROOT / row['after_file']))}
        assert row['after_sha256'] in own, row
        assert len(row['reason']) >= 20, row
        replaced.add(row['before_sha256'])
    lost = set(baseline['paragraph_sha256']) - hashes - replaced
    assert not lost, lost


@pytest.mark.parametrize('name', WRITERS)
def test_constitution_rule_is_one_line_without_reading_the_fragment(name):
    rule = bullet(agent(name), 'Constitución del proyecto')
    assert 'docs/CONSTITUTION.md' in rule and 'respétala' in rule and 'cita el principio' in rule
    assert 'nunca bloquea' in rule
    assert 'Aplica el paso compartido' not in rule
    assert 'no abras `constitution-check.md`' in rule


@pytest.mark.parametrize('name', WRITERS)
def test_memory_fragment_is_read_only_with_hits_and_adr_duty_is_kept(name):
    rule = bullet(agent(name), 'Memoria técnica del proyecto — lectura')
    assert 'knowledge-find.py' in rule
    assert 'Aplica el paso compartido' not in rule
    assert re.search(r'[Ss]olo con aciertos[^.]*`"\$SHAREDKIT/knowledge-check\.md"`', rule), rule
    assert re.search(r'respeta[^.]*(ADR|lecci)', rule), rule
    assert 'no bloquea' in rule


@pytest.mark.parametrize('name', ('implementer', 'qa'))
def test_rationalization_table_pointer_is_gone_but_the_table_stays(name):
    body = agent(name)
    assert 'rationalization-table.md' not in body
    assert '| Excusa que el modelo se da | Por qué no vale | Qué hacer en su lugar |' in body


def test_rationalization_fragment_says_it_is_an_authoring_guide():
    frag = ' '.join(lf(SHARED / 'rationalization-table.md').split())
    assert 'guía de autoría' in frag


def test_evaluator_stays_within_its_byte_budget():
    assert len(agent('evaluator').encode('utf-8')) <= 15513
