"""Fase 4, intento 1 de la revisión (fix1): gaps menores sueltos (8, 9, 12-17)."""
import importlib.util
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))


def test_f4fix1_8_the_red_line_is_recognised_in_its_real_shapes():
    spec = importlib.util.spec_from_file_location('f4fix1_lint', ROOT / 'agent-kits/shared/ledger-lint.py')
    lint = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(lint)
    for body in ('RED: `t` falló · 2026-11-10', '  - RED: `t` falló', '- RED: `t` falló', '**RED**: `t` falló',
                 '- **RED**: `t` falló', 'RED (fix2): `t` falló', '  - RED (fix2): `t` falló', 'RED fix1: `t`',
                 '**RED fix1**: `t`', 'TDD n/a: prosa'):
        assert lint._RED_RE.search('\n' + body + '\n'), body
    for body in ('REDUCE: algo', 'RED', 'la nota RED: no es una línea de evidencia', 'RED (sin dos puntos)'):
        assert not lint._RED_RE.search('\n' + body + '\n'), body


def _journal():
    spec = importlib.util.spec_from_file_location('f4fix1_journal', ROOT / 'agent-kits/shared/journal.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_f4fix1_9_a_late_replay_from_the_queue_does_not_claim_the_current_initiative(tmp_path):
    import time
    journal = _journal()
    journal.iniciativa_activa = lambda root: 'demo'
    def stamp(age):
        return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(time.time() - age))
    fresh = journal.draft(str(tmp_path), 'sid-1', None, 'other', captured_at=stamp(60))
    late = journal.draft(str(tmp_path), 'sid-2', None, 'other', captured_at=stamp(3 * 86400))
    assert fresh.get('regla_iniciativa') == 'vigente'
    assert 'regla_iniciativa' not in late      # not cited as the history of any initiative


def test_f4fix1_4_the_doctor_notes_travel_with_every_runtime():
    import re
    note = 'agent-kits/shared/doctor-reference.md'
    assert (ROOT / note).is_file()
    # The installer payloads ship the whole agent-kits tree to Claude Code, Codex and OpenCode.
    providers = (ROOT / 'install/providers.mjs').read_text(encoding='utf-8')
    for name in ('PAYLOAD_CLAUDE', 'PAYLOAD_COMUN'):
        assert '"agent-kits"' in re.search(name + r' = \[(.*?)\]', providers, re.S)[1], name
    # Every copy of the command names the note with the resolved root, never a project-relative path.
    copies = ['commands/doctor.md', 'interop/codex/command-skills/custom-agents-doctor/references/command.md',
              'interop/opencode/commands/doctor.md']
    for rel in copies:
        text = (ROOT / rel).read_text(encoding='utf-8')
        assert '$R/' + note in text, rel
        assert 'docs/reference/doctor.md' not in text, rel


def _sentences(path, start, end):
    import re
    text = (ROOT / path).read_text(encoding='utf-8')
    block = text[text.index(start):text.index(end)]
    return [s for s in re.split(r'(?<=[.!?])\s+', ' '.join(block.split())) if s]


def test_f4fix1_15_the_declared_growth_is_not_one_long_nested_sentence():
    for path, start, end in (('docs/TOKEN-EFFICIENCY.md', 'Lo que sube se declara', '## Evitar contexto'),
                             ('docs/en/TOKEN-EFFICIENCY.md', 'What grows is declared', '## Tool results')):
        for sentence in _sentences(path, start, end):
            assert len(sentence.split()) <= 40, (path, sentence)
            assert sentence.count('«') <= 2, (path, sentence)


def test_f4fix1_16_the_cache_is_not_attributed_to_codex():
    ledger = (ROOT / 'docs/roadmap/2026-11-09-plugin-audit-remediation/tasks.md').read_text(encoding='utf-8')
    block = ledger[ledger.index('### T-20'):ledger.index('### T-21')]
    line = next(l for l in block.splitlines() if l.startswith('- **Changelog**'))
    assert 'OpenCode y Codex' not in line, line
    for changelog in ('CHANGELOG.md', 'CHANGELOG.es.md'):
        text = (ROOT / changelog).read_text(encoding='utf-8')
        bullet = next(l for l in text.splitlines() if l.startswith('- OpenCode reu'))
        assert bullet.index('Codex') > bullet.index('Agent'), changelog   # Codex only in the delegation clause


def test_f4fix1_13_the_quick_path_margin_deviation_is_recorded():
    ledger = (ROOT / 'docs/roadmap/2026-11-09-plugin-audit-remediation/tasks.md').read_text(encoding='utf-8')
    assert '6.158 → 6.066' in ledger
