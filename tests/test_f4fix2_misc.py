"""Fase 4, intento 2 de la revisión (fix2): gaps menores sueltos (6, 10, 11, 12, 13) y tests de los gaps 5 y 14 del intento 1."""
import importlib.util
import os
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[1]


def _module(rel, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_f4fix2_6_the_outbox_is_drained_oldest_first(tmp_path):
    ob = _module('agent-kits/shared/outbox.py', 'f4fix2_outbox')
    queue = str(tmp_path / 'q')
    claves = ['ffff', 'aaaa', 'mmmm']          # name order is NOT chronological order
    for age, clave in zip((300, 200, 100), claves):
        ob.escribir(queue, clave, {'k': clave})
        path = os.path.join(queue, 'outbox', clave + '.json')
        os.utime(path, (time.time() - age, time.time() - age))
    order = []
    while True:
        item = ob.reclamar(queue)
        if item is None:
            break
        order.append(item['clave'])
        ob.completar(item, {'ok': True})
    assert order == claves


def test_f4fix2_10_the_red_line_accepts_several_words_before_the_parenthesis():
    lint = _module('agent-kits/shared/ledger-lint.py', 'f4fix2_lint')
    for body in ('RED fix1 (gap 6): `t` falló', 'RED (fix2): `t`', 'RED fix1: `t`', '- RED fix1 (gaps 1, 2): `t`',
                 '**RED fix1 (gap 6)**: `t`', 'RED intento 2 fix1: `t`'):
        assert lint._RED_RE.search('\n' + body + '\n'), body
    for body in ('REDUCE: algo', 'RED fix1 (gap 6) sin dos puntos', 'RED'):
        assert not lint._RED_RE.search('\n' + body + '\n'), body


def test_f4fix2_11_conventions_document_the_quoted_line_the_only_valid_one_and_the_precedence():
    for rel, valid, precedence in (('docs/CONVENTIONS.md', 'única línea de kit válida', 'Precedencia'),
                                   ('docs/en/CONVENTIONS.md', 'only valid kit line', 'Precedence')):
        text = (ROOT / rel).read_text(encoding='utf-8')
        assert "SHAREDKIT='<" in text and 'SHAREDKIT="<' not in text, rel
        assert valid in text and precedence in text, rel


def test_f4fix2_13_the_english_doctor_mirror_names_where_the_command_points():
    text = (ROOT / 'docs/en/reference/doctor.md').read_text(encoding='utf-8')
    assert '`$R/agent-kits/shared/doctor-reference.md`' in text and 'a pointer here' not in text
