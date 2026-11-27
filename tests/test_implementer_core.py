"""plugin-audit-2 T-19 (2.2, part of 2.13): the implementer loads a short core.

- `agents/implementer.md` keeps DoD, Verification, RED/GREEN and guardrails; the classic
  flow (no brief) moves to `agent-kits/implementer/references/classic-flow.md`, which the
  core names with its reading condition.
- No rule of the pre-split prompt is lost: every line is in the core or the reference, or
  in a recorded replacement (rewritten or deduplicated) with its reason.
- Every duplicated rule stays once.
- The brief tells a dispatched subagent not to read the classic flow; Codex and OpenCode
  exports carry the pointer and the reference travels in the common payload.
"""
import hashlib
import importlib.util
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / 'agents/implementer.md'
CLASSIC = ROOT / 'agent-kits/implementer/references/classic-flow.md'
BASELINE = ROOT / 'tests/fixtures/implementer-core-lines.json'
TABLE_HEADER = '| Excusa que el modelo se da | Por qué no vale | Qué hacer en su lugar |'


def lf(path):
    return path.read_bytes().decode('utf-8').replace('\r\n', '\n')


def body(text):
    """Text after the YAML frontmatter."""
    return text.split('\n---\n', 1)[1] if text.startswith('---\n') else text


def units(text):
    """Rule units: non-empty lines outside code fences, whitespace-normalised."""
    out, fenced = [], False
    for line in text.splitlines():
        if line.strip().startswith('```'):
            fenced = not fenced
            continue
        norm = ' '.join(line.split())
        if norm and not fenced and norm != '---':
            out.append(norm)
    return out


def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def test_core_is_at_most_sixteen_kibibytes():
    # Criterion adjusted by the user on 2026-11-27 (k6): ≤ 16 KB = 16.384 bytes LF (28.785 before T-19)
    size = len(lf(CORE).encode('utf-8'))
    assert size <= 16384, size


def test_core_keeps_dod_verification_red_green_and_guardrails():
    core = lf(CORE)
    for needed in ('## ANTES DE CERRAR (DoD)', '`Verificación`', 'RED: <test> falló con <error>', 'TDD n/a',
                   'agent-kits/shared/guardrail-check.py', 'Un DENY no es un error', 'ledger-lint.py',
                   'scope-check.py', 'commit-selection.py', 'dueño único de los commits', TABLE_HEADER):
        assert needed in core, needed


def test_without_a_brief_the_core_sends_to_the_classic_flow():
    core = ' '.join(lf(CORE).split())
    assert CLASSIC.is_file(), 'classic-flow.md does not exist'
    assert re.search(r'\*\*Sin brief\*\*[^.]*agent-kits/implementer/references/classic-flow\.md', core), core[:400]
    classic = lf(CLASSIC)
    for needed in ('**P1-bis.', '**P2. Rama (o worktree).**', 'git worktree add', '**P3. Ejecución fase a fase.**',
                   'usage-meter.py" start', 'task.started', 'task.implemented', 'parada por jornada',
                   '**P5. Verificación de fase.**', 'coverage-gate.py', '**P5-bis.', 'phase.completed',
                   '**P6. Cierre + handoff a qa.**', 'output-discipline.md'):
        assert needed in classic, needed
    assert re.search(r'[Ll]éelo solo si trabajas \*\*sin brief\*\*', classic)


def test_no_rule_of_the_previous_prompt_is_lost():
    baseline = json.loads(BASELINE.read_text(encoding='utf-8'))
    present = {sha(u) for u in units(body(lf(CORE))) + units(lf(CLASSIC))}
    replaced = set()
    for row in baseline['replacements']:
        target = units(lf(ROOT / row['after_file']))
        assert row['after_sha256'] in {sha(u) for u in target}, row
        assert len(row['reason']) >= 20, row
        replaced.add(row['before_sha256'])
    lost = [h for h in baseline['line_sha256'] if h not in present and h not in replaced]
    assert not lost, f'{len(lost)} lines lost without a recorded replacement'


def test_each_duplicated_rule_stays_once():
    corpus = lf(CORE) + '\n' + lf(CLASSIC)
    # plugin-audit-2 T-22: 'export-interop.py --check' leaves the agents (custom-agents-repo.md); no agent names it
    for once in ('Ejecuta la `Verificación` declarada', 'usage-meter.py" start',
                 'tabla de resumen de progreso', 'Disciplina al RECIBIR', 'Un DENY no es un error',
                 'dueño único de los commits', 'git worktree add'):
        assert corpus.count(once) == 1, (once, corpus.count(once))
    # prose rules that a rationalization row already states (rule 5 of the shared fragment)
    for gone in ('**Ejecutas, no planificas ni evalúas.**', 'no marques completado lo que no lo está',
                 '**`tasks.md` siempre al día**', 'siguen las reglas de §0'):
        assert gone not in corpus, gone


def test_the_brief_tells_the_subagent_not_to_read_the_classic_flow():
    spec = importlib.util.spec_from_file_location('tb_t19', ROOT / 'agent-kits/shared/task-brief.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert 'no leas `classic-flow.md`' in module.CONTRATO


def test_codex_and_opencode_resolve_the_reference():
    spec = importlib.util.spec_from_file_location('t19_export', ROOT / 'scripts/export-interop.py')
    exporter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(exporter)
    generated = exporter.generar(str(ROOT))
    for rel in ('interop/codex/agents/custom-agents-implementer.toml', 'interop/opencode/agents/custom-agents-implementer.md'):
        assert 'agent-kits/implementer/references/classic-flow.md' in generated[rel], rel
    providers = lf(ROOT / 'install/providers.mjs')
    assert re.search(r'PAYLOAD_COMUN = \[[^\]]*"agent-kits"', providers)
