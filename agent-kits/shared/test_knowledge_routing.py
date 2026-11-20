"""Publication and retrieval share a pure, fail-closed entry selection."""
import copy
import importlib.util
from pathlib import Path
import pytest


spec = importlib.util.spec_from_file_location('routing_taxonomy_test', Path(__file__).with_name('knowledge-taxonomy-local.py'))
taxonomy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(taxonomy)


def fixtures():
    config = {'categories': [
        {'key': 'DECISION', 'routing': {'docs': True}},
        {'key': 'SUMMARY', 'routing': {'docs': 'summary'}},
        {'key': 'PRIVATE', 'routing': {'docs': False}},
        {'key': 'UNDECLARED'},
    ]}
    def entry(category):
        return {'category': category, 'version': 3, 'folder': 'adr', 'enlaces': [],
                'evidencia': 'validated_case', 'fuentes': ['case:1'], 'tags': ['area:billing'],
                'cuerpo': 'Full decision with evidence.', 'resumen': 'Explicit summary.',
                'ruta': 'docs/knowledge/approved/adr/decision.md'}
    records = {key: entry(category) for key, category in (
        ('Z.summary', 'SUMMARY'), ('A.decision', 'DECISION'),
        ('C.private', 'PRIVATE'), ('D.undeclared', 'UNDECLARED'))}
    return config, records


def test_routing_selection_is_pure_preserves_summary_and_excludes_private(monkeypatch):
    config, records = fixtures()
    original = copy.deepcopy((config, records))
    def forbidden(*args, **kwargs):
        raise AssertionError('selection must not open files or load adapters')
    monkeypatch.setattr('builtins.open', forbidden)
    entries, errors, omitted = taxonomy.entradas_enrutadas(config, 'docs', records)
    assert errors == []
    assert [e['id'] for e in entries] == ['A.decision', 'Z.summary']
    assert omitted == ['C.private', 'D.undeclared']
    assert entries[0]['modo'] == 'completo'
    assert entries[1]['modo'] == 'resumen'
    assert entries[1]['resumen'] == 'Explicit summary.'
    assert entries[0]['cuerpo'] == 'Full decision with evidence.'
    assert entries[0]['fuentes'] == ['case:1'] and entries[0]['tags'] == ['area:billing']
    assert (config, records) == original


@pytest.mark.parametrize('invalid', [1, 'true', None, [], {}])
def test_invalid_routing_cannot_authorize_any_entry(invalid):
    config, records = fixtures()
    config['categories'][0]['routing']['docs'] = invalid
    entries, errors, omitted = taxonomy.entradas_enrutadas(config, 'docs', records)
    assert entries == []
    assert errors and errors[0]['campo'].endswith('routing.docs')
    assert sorted(omitted) == sorted(records)


@pytest.mark.parametrize('numeric', [0, 1, 0.0, 1.0])
def test_taxonomy_routing_rejects_numeric_boolean_aliases(numeric):
    config = taxonomy.default_taxonomy()
    config['backends'] = {'docs': {'type': 'adaptador-prueba'}}
    config['categories'][0]['routing'] = {'docs': numeric}
    errors = taxonomy.validar(config)
    assert any(error['campo'] == 'categories[0].routing.docs' for error in errors)
