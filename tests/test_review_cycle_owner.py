"""H-24 / H-25 (auditoría 2026-11-09): el «seguir» tras el 3.er intento es un camino ejecutable y el
commit tiene un único dueño y un único procedimiento."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def plain(rel):
    return ' '.join((ROOT / rel).read_text(encoding='utf-8').split())


def test_h24_dev_cycle_y_la_skill_describen_el_ciclo_nuevo_con_el_writer():
    for rel in ('commands/dev-cycle.md', 'skills/adversarial-review/SKILL.md', 'agent-kits/shared/ledger-write.md'):
        text = plain(rel)
        assert '--new-cycle-ok' in text, rel
        assert 'ciclo' in text and 'OK del usuario' in text, rel


def test_h25_un_solo_dueno_del_commit():
    implementer = plain('agents/implementer.md')
    core = plain('commands/dev-cycle.md')
    # El procedimiento vive una vez, en el implementer; la Fase 6 solo verifica y remite a él.
    assert 'commit-selection.py' in implementer and 'dueño único de los commits' in implementer
    fase6 = core[core.index('2. **Commits ordenados**'):][:900]
    assert 'commit-selection.py' not in fase6 and 'implementer' in fase6 and 'P4' in fase6, fase6
