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
    config['categories'][0]['routing']['kwipu'] = numeric
    errors = taxonomy.validar(config)
    assert any(error['campo'] == 'categories[0].routing.kwipu' for error in errors)


def test_documental_read_defaults_disabled_and_accepts_explicit_bounded_policy():
    assert callable(getattr(taxonomy, 'documental_read_options', None)), 'read policy validation is absent'
    options, errors = taxonomy.documental_read_options({})
    assert errors == [] and options['enabled'] is False
    options, errors = taxonomy.documental_read_options({
        'read': {'enabled': True, 'timeout_ms': 900},
        'router': {'intents': {'documental': True}, 'default': 'local'}})
    assert errors == [] and options['timeout_ms'] == 900 and options['enabled'] is True


@pytest.mark.parametrize('read', [True, {'enabled': 1}, {'enabled': 'true'},
    {'timeout_ms': True}, {'timeout_ms': 30001}, {'timeout_ms': 1.5},
    {'max_request_bytes': 65537}, {'max_snapshot_bytes': 2097153}, {'unrecognized': 1}])
def test_documental_read_rejects_invalid_or_unbounded_options(read):
    assert callable(getattr(taxonomy, 'documental_read_options', None)), 'read policy validation is absent'
    options, errors = taxonomy.documental_read_options({'read': read})
    assert options is None and errors


@pytest.mark.parametrize('router', [True, {'intents': {'documental': 1}},
    {'intents': {'bad intent': True}}, {'intents': []}, {'default': 1}, {'fallback': 'remote'}])
def test_documental_read_router_is_strict(router):
    assert callable(getattr(taxonomy, 'documental_read_options', None)), 'read policy validation is absent'
    options, errors = taxonomy.documental_read_options({'router': router})
    assert options is None and errors


def test_complete_schema_applies_shared_documental_read_policy():
    spec = importlib.util.spec_from_file_location('read_policy_full_schema',
        Path(__file__).with_name('knowledge-schema.py'))
    schema = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(schema)
    config = taxonomy.default_taxonomy()
    config['backends']['kwipu']['config']['read'] = {'enabled': 1}
    errors = schema.validar(config)
    assert any(error['campo'] == 'backends.kwipu.config.read.enabled' for error in errors)


def test_documental_explicit_limit_keys_match_runtime_adapter():
    config = {'read': {'enabled': True, 'timeout_ms': 900, 'max_request_bytes': 512,
        'max_answer_chars': 700, 'max_source_nodes': 3,
        'max_response_bytes': 4096, 'max_snapshot_bytes': 8192}}
    options, errors = taxonomy.documental_read_options(config)
    assert errors == [] and options['max_answer_chars'] == 700
    path = Path(__file__).resolve().parents[2] / 'skills/knowledge-services/backends/markdown_export.py'
    spec = importlib.util.spec_from_file_location('read_runtime_policy_test', path)
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    assert adapter._read_options(config) == {key: value for key, value in options.items() if key != 'enabled'}
