"""Generated journal guidance must hand learning to the shared curation flow."""
import copy
import importlib.util
from pathlib import Path

import pytest


@pytest.fixture
def journal():
    spec = importlib.util.spec_from_file_location('journal_curation_handoff', Path(__file__).with_name('journal.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_candidates_keep_legacy_state_and_evidence_but_name_the_current_decisor(journal):
    candidates = [{'estado': 'propuesta', 'texto': 'Conservar la fuente de cada decisión',
                   'campo': 'decisiones', 'entradas': 2,
                   'evidencia': [{'fecha': '2026-10-01', 'fichero': 'first.md'},
                                 {'fecha': '2026-10-02', 'fichero': 'second.md'}]}]
    before = copy.deepcopy(candidates)
    text = journal.render_candidatas(candidates)
    assert candidates == before
    assert '[propuesta]' in text and 'first.md' in text and 'second.md' in text
    assert 'knowledge-curator' in text and 'propose' in text
    assert 'revisión de dos lentes o el usuario' not in text
    assert '[aceptada]' not in text and '[aprobado]' not in text


def test_entry_guidance_requires_candidate_handoff_before_approved_doctrine(journal):
    entry = {'fecha': '2026-10-01', 'session_id': 'synthetic-session', 'iniciativa': 'fixture',
             'resumen': 'Una decisión con su fuente', 'decisiones': ['Conservar la fuente'],
             'pendientes': [], 'ficheros_tocados': [], 'tareas_cambiadas': [], 'marcadores_cerrados': []}
    before = copy.deepcopy(entry)
    text = journal.render(entry, 'manual')
    assert entry == before
    assert '**citas**' in text and 'Conservar la fuente' in text
    assert 'knowledge-curator' in text and 'propose' in text and 'approved/' in text
    assert 'se promueve a `adr/`' not in text


def test_generated_index_explains_the_same_handoff_without_creating_memory(journal, tmp_path):
    directory = tmp_path / 'docs' / 'knowledge' / 'journal'
    directory.mkdir(parents=True)
    result = journal.index(str(tmp_path))
    assert Path(result) == directory / 'README.md'
    text = Path(result).read_text(encoding='utf-8')
    assert 'knowledge-curator' in text and 'propose' in text and 'approved/' in text
    assert 'se promueve a `adr/`' not in text
    assert sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob('*.md')) == [
        'docs/knowledge/journal/README.md']
