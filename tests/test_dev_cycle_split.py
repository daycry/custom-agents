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
REFERENCES = ('phase1-evaluation.md', 'phase2-planning.md', 'phase3-subagents.md',
              'phase3-jira.md', 'phase4-knowledge-gate.md')
CORE_REFERENCES = tuple(name for name in REFERENCES if name != 'phase3-jira.md')
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
    assert 'plan-review:prepare:bash' in (KIT / 'phase2-planning.md').read_text(encoding='utf-8')
    assert 'subagentes: true' in core and 'project-integrations.md' in core
    assert 'phase3-jira.md' not in core


def test_no_original_paragraph_is_lost():
    original = json.loads(BASELINE.read_text(encoding='utf-8'))
    current = {hashlib.sha256(p.encode('utf-8')).hexdigest() for p in paragraphs(corpus())}
    replacements = json.loads(REPLACEMENTS.read_text(encoding='utf-8'))['replacements']
    assert set(original['paragraph_sha256']) - current == {row['before_sha256'] for row in replacements}
    for row in replacements:
        own = {hashlib.sha256(p.encode('utf-8')).hexdigest() for p in paragraphs((ROOT/row['after_file']).read_text(encoding='utf-8'))}
        assert row['after_sha256'] in own and row['reason']
    quick = (ROOT / 'skills/quick-implement/SKILL.md').read_text(encoding='utf-8')
    quick_hashes = {hashlib.sha256(p.encode('utf-8')).hexdigest() for p in paragraphs(quick)}
    assert not set(original['quick_paragraph_sha256']) - quick_hashes


def test_visual_review_recipes_are_byte_identical():
    original = json.loads(BASELINE.read_text(encoding='utf-8'))
    for identity, digest in original['recipes'].items():
        text = (KIT / 'phase2-planning.md').read_text(encoding='utf-8')
        match = re.search(r'<!-- plan-review:' + identity + r' -->\s*```[^\n]+\n(.*?)\n```', text, re.S)
        assert match, identity
        assert hashlib.sha256(match[1].encode('utf-8')).hexdigest() == digest


def test_common_review_qa_and_commit_gates_stay_in_the_core():
    original = json.loads(BASELINE.read_text(encoding='utf-8'))
    hashes = {hashlib.sha256(p.encode('utf-8')).hexdigest()
              for p in paragraphs(COMMAND.read_text(encoding='utf-8'))}
    replacements = {row['before_sha256']: row for row in json.loads(REPLACEMENTS.read_text(encoding='utf-8'))['replacements']}
    required = {replacements[old]['after_sha256'] if old in replacements else old for old in original['unconditional_core_paragraph_sha256']}
    assert required <= hashes
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
