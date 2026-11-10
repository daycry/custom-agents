"""Fase 4, intento 3 (fix3): gaps menores (6 y la documentación)."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _lint():
    spec = importlib.util.spec_from_file_location('f4fix3_lint', ROOT / 'agent-kits/shared/ledger-lint.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_f4fix3_6_prose_that_denies_the_red_is_not_evidence():
    lint = _lint()
    for body in ('RED no observado: el test no existía', 'RED sin observar: prosa', 'RED todavía no: pendiente',
                 '- RED nunca falló: ya pasaba', 'RED aún no (gap 6): luego', '**RED no observado**: x', 'RED ni siquiera: x'):
        assert not lint._RED_RE.search('\n' + body + '\n'), body
    for body in ('RED fix1 (gap 6): `t` falló', 'RED: `t` falló', 'RED intento 2 fix1: `t`', 'RED (fix2): `t`', '**RED**: `t`'):
        assert lint._RED_RE.search('\n' + body + '\n'), body


TASKS = ROOT / 'docs/roadmap/2026-11-09-plugin-audit-remediation/tasks.md'


def _block(tid, nxt):
    text = TASKS.read_text(encoding='utf-8')
    return text[text.index(f'### {tid} —'):text.index(f'### {nxt} —')] if nxt else text[text.index(f'### {tid} —'):]


def test_f4fix3_8_token_efficiency_describes_the_recipe_as_it_is():
    for rel, old, new in (('docs/TOKEN-EFFICIENCY.md', 'respeta esa', 'sin `CLAUDE_PLUGIN_ROOT`'),
                          ('docs/en/TOKEN-EFFICIENCY.md', 'honours that path', 'without `CLAUDE_PLUGIN_ROOT`')):
        text = (ROOT / rel).read_text(encoding='utf-8')
        assert old not in text and new in text, rel


def test_f4fix3_9_archivos_name_the_files_the_fix_cycles_touched():
    assert 'agent-kits/shared/outbox.py' in _block('T-20', 'T-21').split('**Criterios')[0]
    t21 = _block('T-21', None).split('**Criterios')[0]
    for name in ('agent-kits/shared/journal-capture.py', 'agent-kits/shared/progress-report.py'):
        assert name in t21, name
