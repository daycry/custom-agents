"""CA-17 metadata survives publication, routing and semantic change detection."""
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest
import yaml

HERE = Path(__file__).resolve().parent


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def adapter():
    return load(HERE.parent / 'backends/markdown_export.py', 'metadata_adapter')


def entry(**metadata):
    return dict(id='demo.rule', version=1, category='RULE', evidencia='validated_case',
                cuerpo='Approved body.', modo='completo', **metadata)


def publish(adapter, tmp_path, record):
    cfg = {'export_dir': str(tmp_path / 'export')}
    adapter.apply(adapter.plan([record], cfg), cfg)
    text = (tmp_path / 'export/demo.rule.md').read_text(encoding='utf-8')
    return yaml.safe_load(text[4:].split('\n---\n', 1)[0]), cfg


def test_title_and_tags_exported_unchanged(adapter, tmp_path):
    record = entry(title='Despliegue: "rápido" y seguro',
                   tags=['plataforma:azure-app-service', 'area:despliegue'])
    fm, cfg = publish(adapter, tmp_path, record)
    assert fm['title'] == record['title']
    assert fm['tags'] == record['tags']
    assert adapter.plan([record], cfg)[0]['accion'] == 'sin_cambios'


@pytest.mark.parametrize('metadata', [{}, {'title': 'Only title'}, {'tags': ['area:ops']},
                                     {'title': None, 'tags': []}])
def test_optional_metadata_omitted_independently(adapter, tmp_path, metadata):
    fm, _ = publish(adapter, tmp_path, entry(**metadata))
    for key in ('title', 'tags'):
        if metadata.get(key):
            assert fm[key] == metadata[key]
        else:
            assert key not in fm


@pytest.mark.parametrize('title', ['A: "sí"', "L'équipe: 'café'", 'yes', '---\n# Título\n',
                                  'Unicode Ω y emoji 🚀', 'C:\\tools\\new', 'A\x85B\u2028C\u2029D'])
def test_yaml_scalar_roundtrip(adapter, tmp_path, title):
    tags = ['area:despliegue', 'nota:"sí", café', 'linea:uno\ndos']
    fm, _ = publish(adapter, tmp_path, entry(title=title, tags=tags))
    assert fm['title'] == title
    assert fm['tags'] == tags


@pytest.mark.parametrize('changed', [{'title': 'Changed'}, {'tags': ['area:new']},
                                   {'title': None}, {'tags': []}])
def test_metadata_changes_invalidate_hash_without_version_bump(adapter, tmp_path, changed):
    original = entry(title='Original', tags=['area:old'])
    before, cfg = publish(adapter, tmp_path, original)
    updated = {**original, **changed}
    op = adapter.plan([updated], cfg)[0]
    assert op['accion'] == 'upsert'
    assert op['hash'] != before['hash']
    after, _ = publish(adapter, tmp_path, updated)
    assert after['hash'] == op['hash']
    assert adapter.plan([updated], cfg)[0]['accion'] == 'sin_cambios'


def test_upgrade_rewrites_old_export_once(adapter, tmp_path):
    record = entry(title='Title', tags=['area:ops'])
    export = tmp_path / 'export'
    export.mkdir()
    old_hash = hashlib.sha256(b'demo.rule\n1\nRULE\nApproved body.').hexdigest()
    (export / 'demo.rule.md').write_text('---\nhash: ' + old_hash + '\n---\nApproved body.\n')
    (export / 'manifest.json').write_text(json.dumps({'version': 1, 'entries': {
        'demo.rule': {'hash': old_hash, 'ruta_relativa': 'demo.rule.md', 'version': 1,
                      'category': 'RULE'}}}))
    cfg = {'export_dir': str(export)}
    assert adapter.plan([record], cfg)[0]['accion'] == 'upsert'
    publish(adapter, tmp_path, record)
    assert adapter.plan([record], cfg)[0]['accion'] == 'sin_cambios'


@pytest.mark.parametrize('quoting', ['yaml', 'json'])
def test_real_sync_preserves_approved_title_and_tags(tmp_path, quoting, capsys):
    sync = load(HERE / 'knowledge-sync.py', 'metadata_sync')
    config = {'version': 1, 'id_prefix': 'demo', 'evidence_levels': ['validated_case'],
              'categories': [{'key': 'RULE', 'folder': 'rules', 'min_evidence': 'validated_case',
                              'routing': {'kwipu': True}}],
              'backends': {'kwipu': {'type': 'markdown-export', 'enabled': True,
                                    'config': {'export_dir': 'export'}}}}
    policy = tmp_path / '.claude/knowledge-services/taxonomy.json'
    policy.parent.mkdir(parents=True)
    policy.write_text(json.dumps(config), encoding='utf-8')
    approved = tmp_path / 'docs/knowledge/approved/rules/one.md'
    approved.parent.mkdir(parents=True)
    metadata = dict(id='demo.rule', version=1, estado='aprobado', category='RULE',
                    evidencia='validated_case', title='Despliegue: "rápido"',
                    tags=['plataforma:azure-app-service', 'area:despliegue', 'nota:"sí", café'])
    frontmatter = yaml.safe_dump(metadata, allow_unicode=True)
    if quoting == 'json':
        frontmatter = ''.join(key + ': ' + json.dumps(value) + '\n'
                              for key, value in metadata.items())
    approved.write_text('---\n' + frontmatter +
                        '---\n\nApproved body.\n', encoding='utf-8')
    assert sync.main(['--root', str(tmp_path), '--backend', 'kwipu', '--json']) == 0
    fm = yaml.safe_load((tmp_path / 'export/demo.rule.md').read_text(encoding='utf-8').split('---', 2)[1])
    assert fm['title'] == metadata['title']
    assert fm['tags'] == metadata['tags']
    helper = load(HERE / 'test_backend_markdown_export.py', 'metadata_http_fixture')
    health = (HERE / 'fixtures/kwipu-health-2026-09-18.json').read_bytes()
    snapshot = json.dumps({'nodes': [{'type': 'chunk', 'file_name': 'demo.rule.md',
                                    'hash': fm['hash'], 'fm': fm}]}).encode()
    with helper._ServidorFixturasContext({'/health': (200, health),
                                         '/graph/snapshot': (200, snapshot)}) as server:
        config['backends']['kwipu']['config']['health'] = {
            'url': server.base_url + '/health', 'timeout_ms': 2000}
        policy.write_text(json.dumps(config), encoding='utf-8')
        capsys.readouterr()
        assert sync.main(['--root', str(tmp_path), '--backend', 'kwipu', '--check', '--json']) == 0
        assert json.loads(capsys.readouterr().out)['verify']['ok'] is True


@pytest.mark.parametrize('metadata', [{'title': []}, {'tags': 'area:ops'}, {'tags': [3]}])
def test_invalid_metadata_rejected_before_publication(adapter, tmp_path, metadata):
    with pytest.raises(adapter.ConfigInvalida):
        adapter.plan([entry(**metadata)], {'export_dir': str(tmp_path / 'export')})
    assert not (tmp_path / 'export').exists()


def test_long_tag_list_does_not_break_idempotent_recovery(adapter, tmp_path):
    record = entry(title='Long tags', tags=['area:' + str(n) for n in range(80)])
    _, cfg = publish(adapter, tmp_path, record)
    assert adapter.plan([record], cfg)[0]['accion'] == 'sin_cambios'
