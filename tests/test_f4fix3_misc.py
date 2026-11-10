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
