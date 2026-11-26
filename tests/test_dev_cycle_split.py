"""Keep canonical workflow contracts while loading phase details only when needed."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

import pytest
import test_hooks_shell as legacy

ROOT = Path(__file__).resolve().parents[1]
COMMAND = ROOT / 'commands/dev-cycle.md'
KIT = ROOT / 'agent-kits/dev-cycle/references'
REFERENCES = ('phase1-evaluation.md', 'phase2-planning.md', 'phase2-plan-review.md',
              'phase3-subagents.md', 'phase3-jira.md', 'phase4-knowledge-gate.md', 'phase6-close.md')
# phase3-jira.md and phase2-plan-review.md are reached only from another reference,
# never from the core: the visual plan review is optional (audit H-43).
CORE_REFERENCES = tuple(name for name in REFERENCES
                        if name not in ('phase3-jira.md', 'phase2-plan-review.md'))
REPLACEMENTS = ROOT / 'tests/fixtures/dev-cycle-modular-replacements.json'
BASELINE = ROOT / 'tests/fixtures/dev-cycle-paragraphs.json'


def paragraphs(text):
    return [' '.join(part.split()) for part in re.split(r'\n\s*\n', text) if part.strip()]


def corpus():
    return '\n\n'.join([COMMAND.read_text(encoding='utf-8')] +
                       [(KIT / name).read_text(encoding='utf-8') for name in REFERENCES])


def test_phase_details_have_a_private_owner_and_lazy_routes():
    core = COMMAND.read_text(encoding='utf-8')
    for name in REFERENCES:
        assert (KIT / name).is_file(), f'missing private phase detail: {name}'
        if name in CORE_REFERENCES:
            assert name in core
    assert 'agent-kits/dev-cycle' in core and 'solo cuando' in core
    assert 'plan-review:prepare:bash' not in core
    planning = (KIT / 'phase2-planning.md').read_text(encoding='utf-8')
    review = (KIT / 'phase2-plan-review.md').read_text(encoding='utf-8')
    assert 'plan-review:prepare:bash' in review and 'plan-review:prepare:bash' not in planning
    assert 'phase2-plan-review.md' in planning and 'phase2-plan-review.md' not in core
    assert 'subagentes: true' in core and 'project-integrations.md' in core
    assert 'phase3-jira.md' not in core


def test_no_original_paragraph_is_lost():
    original = json.loads(BASELINE.read_text(encoding='utf-8'))
    current = {hashlib.sha256(p.encode('utf-8')).hexdigest() for p in paragraphs(corpus())}
    replacements = json.loads(REPLACEMENTS.read_text(encoding='utf-8'))['replacements']
    quick_file = 'skills/quick-implement/SKILL.md'
    assert set(original['paragraph_sha256']) - current == {row['before_sha256'] for row in replacements
                                                           if row['before_file'] != quick_file}
    for row in replacements:
        own = {hashlib.sha256(p.encode('utf-8')).hexdigest() for p in paragraphs((ROOT/row['after_file']).read_text(encoding='utf-8'))}
        assert row['after_sha256'] in own and row['reason']
    quick = (ROOT / 'skills/quick-implement/SKILL.md').read_text(encoding='utf-8')
    quick_hashes = {hashlib.sha256(p.encode('utf-8')).hexdigest() for p in paragraphs(quick)}
    replaced = {row['before_sha256'] for row in replacements if row['before_file'] == quick_file}
    assert not set(original['quick_paragraph_sha256']) - quick_hashes - replaced


def test_visual_review_recipes_are_byte_identical():
    original = json.loads(BASELINE.read_text(encoding='utf-8'))
    for identity, digest in original['recipes'].items():
        text = (KIT / 'phase2-plan-review.md').read_text(encoding='utf-8')
        match = re.search(r'<!-- plan-review:' + identity + r' -->\s*```[^\n]+\n(.*?)\n```', text, re.S)
        assert match, identity
        assert hashlib.sha256(match[1].encode('utf-8')).hexdigest() == digest


def test_common_review_qa_and_commit_gates_stay_in_the_core():
    original = json.loads(BASELINE.read_text(encoding='utf-8'))
    hashes = {hashlib.sha256(p.encode('utf-8')).hexdigest()
              for p in paragraphs(COMMAND.read_text(encoding='utf-8'))}
    replacements = {row['before_sha256']: row for row in json.loads(REPLACEMENTS.read_text(encoding='utf-8'))['replacements']}
    required = {replacements[old]['after_sha256'] if old in replacements else old for old in original['unconditional_core_paragraph_sha256']}
    # plugin-audit-2 T-16: the branch-closing ritual (verification, commits, PR summary, retro gate)
    # moved verbatim to phase6-close.md, read on reaching Phase 6; nothing else leaves the core.
    closing = {hashlib.sha256(p.encode('utf-8')).hexdigest()
               for p in paragraphs((KIT / 'phase6-close.md').read_text(encoding='utf-8'))}
    assert required - hashes <= closing
    assert required - hashes == _declared_phase6(replacements.values()) & required
    assert any('1. **Verificación final sobre la rama**' in p for p in paragraphs((KIT / 'phase6-close.md').read_text(encoding='utf-8')))
    core = COMMAND.read_text(encoding='utf-8')
    assert '## Fase 4-bis — Knowledge Gate (siempre' in core
    assert 'docs/knowledge/candidates/{pending,needs_changes}/' in core
    assert 'Revisión/QA no aprueban memoria' in core


def test_quick_default_path_saves_at_least_6000_estimated_tokens():
    original = json.loads(BASELINE.read_text(encoding='utf-8'))
    estimate = lambda text: (len(text) + 3) // 4
    # Successful quick path with the documented default opt-ins off, no pending
    # knowledge candidates and no requested documenter/security audit. Common
    # implementation/review/QA/closure gates remain in the core.
    current = estimate(COMMAND.read_text(encoding='utf-8'))
    current += estimate((ROOT / 'skills/quick-implement/SKILL.md').read_text(encoding='utf-8'))
    assert original['quick_default_estimate'] - current >= 6000


def test_default_phase2_load_leaves_the_optional_visual_review_out():
    # H-43: ~15 K characters of optional review recipes were loaded in every full flow.
    planning = (KIT / 'phase2-planning.md').read_text(encoding='utf-8')
    assert len(planning) <= 6000
    assert len((KIT / 'phase2-plan-review.md').read_text(encoding='utf-8')) >= 12000


def test_native_adapters_keep_core_and_references_deferred():
    spec = importlib.util.spec_from_file_location('split_command_export', ROOT / 'scripts/export-interop.py')
    exporter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(exporter)
    generated = exporter.generar(str(ROOT))
    codex = generated['interop/codex/command-skills/custom-agents-dev-cycle/references/command.md']
    opencode = generated['interop/opencode/commands/dev-cycle.md']
    for text in (codex, opencode):
        assert all(name in text for name in CORE_REFERENCES)
        assert "project-integrations.md" in text and "phase3-jira.md" not in text
        assert 'plan-review:prepare:bash' not in text
    assert 'Núcleo' in generated['interop/codex/command-skills/custom-agents-dev-cycle/SKILL.md']


@pytest.mark.parametrize('shell', ['bash', 'powershell'])
@pytest.mark.parametrize('layout', ['own-repo', 'project-codex'])
def test_private_kit_lookup_executes_in_real_shell(tmp_path, shell, layout):
    executable = legacy.BASH if shell == 'bash' else shutil.which('pwsh') or shutil.which('powershell')
    if not executable:
        pytest.skip(f'{shell} unavailable; no shell lookup claim')
    project = tmp_path / 'consumer'
    project.mkdir()
    home = tmp_path / 'home'
    home.mkdir()
    bundle = project if layout == 'own-repo' else project / '.codex/plugins/fixture'
    kit = bundle / 'agent-kits/dev-cycle'
    (kit / 'references').mkdir(parents=True)
    (kit / 'references/phase2-planning.md').write_text('canonical-phase-owner\n', encoding='utf-8')
    (bundle / 'agent-kits/shared').mkdir(parents=True)   # marcador de bundle real (regla 5)
    (bundle / 'agent-kits/shared/ledger-lint.py').write_text('#\n', encoding='utf-8')
    core = COMMAND.read_text(encoding='utf-8')
    section = core.split('## Detalle por fase:', 1)[1].split('## Contexto técnico compartido', 1)[0]
    recipe = re.search(r'```' + shell + r'\n(.*?)\n```', section, re.S)[1]
    if shell == 'bash':
        recipe += '\nprintf "%s\\n" "$DEVKIT"\ncat "$DEVKIT/references/phase2-planning.md"\n'
        args = [executable, '-c', recipe]
    else:
        recipe += '\nWrite-Output $DevCycleKit\nGet-Content -LiteralPath "$DevCycleKit/references/phase2-planning.md"\n'
        args = [executable, '-NoProfile', '-NonInteractive', '-Command', recipe]
    result = subprocess.run(args, cwd=project, env={**os.environ, 'HOME': str(home), 'USERPROFILE': str(home)},
                            capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=60)
    assert result.returncode == 0, result.stderr
    assert result.stderr == ''
    lines = result.stdout.strip().splitlines()
    assert lines[-1] == 'canonical-phase-owner'
    assert lines[-2].replace('\\', '/').endswith('/agent-kits/dev-cycle')


def test_phase6_closing_and_state_table_load_only_at_closing():
    """plugin-audit-2 T-16: Phase 6 and the transition table leave the first turn of every run."""
    core = COMMAND.read_text(encoding='utf-8')
    close = (KIT / 'phase6-close.md').read_text(encoding='utf-8')
    assert 'phase6-close.md' in core and 'solo al llegar a la Fase 6' in core
    for moved in ('1. **Verificación final sobre la rama**', '8. **Retro — PUERTA, no aviso',
                  '| Momento | spec | evaluación |'):
        assert moved not in core and moved in close, moved
    assert 'retro-gate.py' in close and 'changelog-sync' in close
    # The table still reflects T-40: the plugin's scripts move the task states.
    assert '`start`/despacho → `en-progreso`; `close`/`review` → `en-revision`' in close
    assert 'usage-meter.py start' in core and 'ledger-write.py' in core
    # Regression guard on the measured core size (LF characters, context-footprint method).
    assert len(core) <= 23000


PHASE6 = 'agent-kits/dev-cycle/references/phase6-close.md'


def _declared_phase6(rows):
    return {row['after_sha256'] for row in rows if row['after_file'] == PHASE6}


def test_fix1_gap3_only_paragraphs_declared_with_after_file_phase6_leave_the_core():
    """plugin-audit-2 review attempt 1, gap 3: a mandatory core paragraph may leave the core only if
    the fixture declares it with `after_file: phase6-close.md` (exact, by hash). Being present in
    phase6-close.md is not enough: moving «Bucle de corrección de qa ACOTADO» there must fail."""
    original = json.loads(BASELINE.read_text(encoding='utf-8'))
    rows = json.loads(REPLACEMENTS.read_text(encoding='utf-8'))['replacements']
    by_old = {row['before_sha256']: row for row in rows}
    required = {by_old[old]['after_sha256'] if old in by_old else old
                for old in original['unconditional_core_paragraph_sha256']}
    hashes = {hashlib.sha256(p.encode('utf-8')).hexdigest()
              for p in paragraphs(COMMAND.read_text(encoding='utf-8'))}
    left = required - hashes
    assert left == _declared_phase6(rows) & required, sorted(left - _declared_phase6(rows))
    assert left, 'the closing ritual (declared with after_file) is expected to have left the core'


def test_fix1_gap4_relative_links_in_kit_references_resolve():
    """plugin-audit-2 review attempt 1, gap 4: every relative Markdown link of a private kit
    reference resolves from that file (`../docs/COMMIT-SELECTION.md` did not after T-16)."""
    broken = []
    for ref in sorted((ROOT / 'agent-kits').rglob('references/*.md')):
        for target in re.findall(r'\]\(([^)\s]+)\)', ref.read_text(encoding='utf-8')):
            path = target.split('#', 1)[0]
            if path and not re.match(r'[a-z][a-z0-9+.-]*:', path) and not (ref.parent / path).exists():
                broken.append(f'{ref.relative_to(ROOT).as_posix()} -> {target}')
    assert not broken, broken


def _phase6_core_mentions(core):
    table_row = next(line for line in core.splitlines() if line.startswith('| `phase6-close.md`'))
    phase6 = core.split('## Fase 6', 1)[1].split('\n## ', 1)[0]
    transitions = core.split('## Transiciones de estado', 1)[1].split('\n## ', 1)[0]
    return table_row, phase6, transitions


def test_fix1_gap5_one_reading_condition_for_phase6_close():
    """plugin-audit-2 review attempt 1, gap 5: the core gives ONE coherent reading condition for
    phase6-close.md: the transition table at every artefact gate, the closing ritual only in Phase 6."""
    core = COMMAND.read_text(encoding='utf-8')
    for text in _phase6_core_mentions(core):
        flat = ' '.join(text.split())
        assert 'cada puerta de artefacto' in flat, flat
    flat_phase6 = ' '.join(_phase6_core_mentions(core)[1].split())
    assert 'ritual de cierre' in flat_phase6.lower() and 'solo al llegar a la Fase 6' in flat_phase6
    assert 'que lees al aplicar la primera' not in ' '.join(core.split())
    assert 'la primera puerta de estado' not in core
    head = (KIT / 'phase6-close.md').read_text(encoding='utf-8').split('-->', 1)[0]
    assert 'cada puerta' in ' '.join(head.split()), head


def test_fix1_gap8_phase6_and_transition_sentences_are_short():
    """plugin-audit-2 review attempt 1, gap 8 (docs-style rule 1): no sentence over 40 words in the
    core's Phase 6 and transition paragraphs."""
    _, phase6, transitions = _phase6_core_mentions(COMMAND.read_text(encoding='utf-8'))
    for block in (phase6, transitions):
        for sentence in re.split(r'(?<=[.!?:])\s+(?=[A-ZÁÉÍÓÚ«`(])', ' '.join(block.split())):
            assert len(sentence.split()) <= 40, sentence


def test_t42_fix2_gap1_transitions_keep_the_reading_condition_with_the_gate():
    """plugin-audit-2 T-42 review attempt 2, gap 1: the core transitions paragraph names the tool
    (`roadmap-sync.py gate`, `--cerrar`) AND keeps the reading condition of T-16 fix1 gap 5."""
    transitions = ' '.join(_phase6_core_mentions(COMMAND.read_text(encoding='utf-8'))[2].split())
    assert 'roadmap-sync.py gate' in transitions and '--cerrar' in transitions, transitions
    assert 'cada puerta de artefacto' in transitions, transitions
