"""Audit H-44: the internal notes of /doctor live in docs/, not in every invocation."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel):
    return (ROOT / rel).read_text(encoding='utf-8')


def test_command_keeps_only_the_summary_and_a_pointer():
    command = read('commands/doctor.md')
    assert len(command) <= 8000
    assert 'docs/reference/doctor.md' in command
    assert 'ℹ️' in command and 'No confundir con `/setup`' in command


def test_notes_moved_with_their_content_and_have_an_english_mirror():
    notes = read('docs/reference/doctor.md')
    for marker in ('Ocho bloques', 'Automatizaciones: configuración, no ejecución', 'Memoria de grafo',
                   'CA-14 de knowledge-services', 'La versión del plugin es sin red por diseño'):
        assert marker in notes, marker
    english = read('docs/en/reference/doctor.md')
    for marker in ('Eight blocks', 'Automations: configuration, not execution', 'graph memory',
                   'CA-14 of knowledge-services', 'The plugin version check is offline by design'):
        assert marker.lower() in english.lower(), marker
    for line in notes.splitlines():
        if 'CA-14' in line:
            assert 'knowledge-services' in line, line
