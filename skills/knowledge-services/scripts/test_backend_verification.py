"""Read-only verification must distinguish persisted content from filenames/health."""
import importlib.util
import json
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def exported(tmp_path):
    adapter = load(HERE.parent / 'backends/markdown_export.py', 'verify_export_fixture')
    helper = load(HERE / 'test_backend_markdown_export.py', 'verify_http_fixture')
    cfg = {'export_dir': str(tmp_path / 'export'), 'health': {'timeout_ms': 2000}}
    entry = {'id': 'owned.rule', 'version': 1, 'category': 'RULE', 'cuerpo': 'Approved.',
             'title': 'Approved title', 'tags': ['area:testing']}
    ops = adapter.plan([entry], cfg)
    adapter.apply(ops, cfg)
    return adapter, helper, cfg, ops[0]['hash']


def verify(exported, nodes):
    adapter, helper, cfg, _ = exported
    body = json.dumps({'nodes': nodes}).encode()
    with helper._ServidorFixturasContext({'/graph/snapshot': (200, body)}) as server:
        cfg['health']['url'] = server.base_url + '/health'
        return adapter.verify(cfg)


def chunk(hash_=None, **fm):
    if hash_ is not None:
        fm['hash'] = hash_
    return {'type': 'chunk', 'file_name': 'owned.rule.md', 'fm': fm}


def test_native_frontmatter_hash_is_compared(exported):
    result = verify(exported, [chunk(exported[3], knowledge_id='owned.rule')])
    assert result['ok'] is True
    assert result['comparacion'] == 'hash'


def test_legacy_top_level_hash_is_still_compared(exported):
    node = dict(chunk(), hash=exported[3])
    result = verify(exported, [node])
    assert result['ok'] is True
    assert result['comparacion'] == 'hash'


def test_stale_native_hash_cannot_pass_by_filename(exported):
    result = verify(exported, [chunk('old', knowledge_id='owned.rule')])
    assert result['ok'] is False
    assert result['desfase'][0]['knowledge_id'] == 'owned.rule'


def test_missing_hash_is_incomplete_not_green(exported):
    result = verify(exported, [chunk(knowledge_id='owned.rule')])
    assert result['ok'] is False
    assert result['estado'] == 'incompleto'
    assert result['no_verificado'] == 1


def test_foreign_hash_does_not_hide_missing_own_hash(exported):
    foreign = {'type': 'chunk', 'file_name': 'another.md', 'hash': 'foreign'}
    result = verify(exported, [chunk(knowledge_id='owned.rule'), foreign])
    assert result['ok'] is False
    assert result['estado'] == 'incompleto'


def test_foreign_identity_with_same_basename_cannot_verify_ours(exported):
    result = verify(exported, [chunk(exported[3], knowledge_id='foreign.rule')])
    assert result['ok'] is False


@pytest.mark.parametrize('reverse', [False, True])
def test_conflicting_chunks_are_not_overwritten_by_last_basename(exported, reverse):
    nodes = [chunk('old', knowledge_id='owned.rule'),
             chunk(exported[3], knowledge_id='owned.rule')]
    result = verify(exported, nodes[::-1] if reverse else nodes)
    assert result['ok'] is False


def test_multiple_chunks_with_matching_hash_are_valid(exported):
    node = chunk(exported[3], knowledge_id='owned.rule')
    assert verify(exported, [node, node])['ok'] is True


def test_conflicting_native_and_legacy_hashes_are_rejected(exported):
    node = dict(chunk('old', knowledge_id='owned.rule'), hash=exported[3])
    assert verify(exported, [node])['ok'] is False


@pytest.mark.parametrize('invalid', [3, [], {}])
def test_invalid_native_hash_is_not_reported_verified(exported, invalid):
    assert verify(exported, [chunk(invalid, knowledge_id='owned.rule')])['ok'] is False


@pytest.mark.parametrize('metadata', [{'project': 'foreign'}, {'scope': 'global'},
                                     {'version': 2}, {'category': 'OTHER'}])
def test_inconsistent_declared_metadata_is_not_green(exported, metadata):
    result = verify(exported, [chunk(exported[3], knowledge_id='owned.rule', **metadata)])
    assert result['ok'] is False


def test_remedy_requires_explicit_index_rebuild(exported):
    adapter = exported[0]
    assert 'regenerar' in adapter.REMEDIO.lower()


def test_graphiti_without_publication_reports_zero_verified_content(tmp_path):
    adapter = load(HERE.parent / 'backends/graphiti.py', 'verify_empty_graphiti')
    result = adapter.verify({'_root': str(tmp_path), 'group_id': 'owned',
                             'endpoint': 'http://127.0.0.1:1', 'mode': 'shadow'})
    assert result['publicacion'] == 'sin_publicacion_local'
    assert result['verificados'] == 0
    assert result['aviso']
    assert list(tmp_path.iterdir()) == []
