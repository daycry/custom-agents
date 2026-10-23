"""Only current canonical policy can authorize an explicit documental query."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import time

import pytest

HERE = Path(__file__).parent


def load_context():
    path = HERE / 'knowledge-read-context.py'
    assert path.is_file(), 'canonical read authorization is absent'
    spec = importlib.util.spec_from_file_location('tested_knowledge_read_context', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def project(root):
    cfg = {'export_dir': 'projection', 'health': {'url': 'http://127.0.0.1:8080/health'},
           'read': {'enabled': True, 'timeout_ms': 1200},
           'router': {'intents': {'documental': True}}}
    taxonomy = {'version': 1, 'id_prefix': 'synthetic',
        'backends': {'docs': {'type': 'markdown-export', 'enabled': True, 'config': cfg}},
        'categories': [{'key': 'DECISION', 'folder': 'adr', 'min_evidence': 'observation',
                        'routing': {'docs': True}}]}
    policy = root / '.claude/knowledge-services/taxonomy.json'
    policy.parent.mkdir(parents=True)
    policy.write_text(json.dumps(taxonomy), encoding='utf-8')
    entry = root / 'docs/knowledge/approved/adr/decision.md'
    entry.parent.mkdir(parents=True)
    raw = (b'\xef\xbb\xbf---\r\nid: synthetic.DECISION.one\r\nversion: 7\r\n'
           b'category: DECISION\r\nestado: aprobado\r\nevidencia: observation\r\n'
           b'tags: [area:billing]\r\n---\r\n\r\n# Decision\r\nCanonical body.\r\n')
    entry.write_bytes(raw)
    return cfg, taxonomy, policy, entry


def test_authorization_binds_current_policy_raw_canon_and_same_refresh_deadline(tmp_path):
    cfg, taxonomy, policy, entry = project(tmp_path)
    module = load_context()
    original = copy.deepcopy(cfg)
    result = module.prepare(tmp_path, 'docs', 'documental', expected_config=cfg)
    assert result['status'] == 'ok' and result['reason'] == ''
    context = result['context']
    assert context['backend_enabled'] is True and context['backend_id'] == 'docs'
    assert context['intent'] == 'documental' and context['filters_authorized'] is True
    assert context['entries'][0]['canonical_sha256'] == hashlib.sha256(entry.read_bytes()).hexdigest()
    assert context['entries'][0]['canonical_text'] == entry.read_bytes().decode('utf-8-sig')
    assert context['entries'][0]['estado'] == 'aprobado' and context['entries'][0]['version'] == 7
    refreshed = context['refresh']()
    assert refreshed['fingerprint'] == context['fingerprint']
    assert refreshed['deadline'] == context['deadline'] and cfg == original
    assert time.monotonic() < context['deadline'] <= time.monotonic() + 1.2
    entry.write_bytes(entry.read_bytes().replace(b'Canonical', b'Modified!'))
    assert context['refresh']()['fingerprint'] != context['fingerprint']


@pytest.mark.parametrize('change', ['enabled', 'intent', 'read', 'routing', 'version', 'private', 'config'])
def test_authorization_rejects_disabled_stale_or_forged_policy_before_adapter(tmp_path, change):
    cfg, taxonomy, policy, entry = project(tmp_path)
    module = load_context()
    original = copy.deepcopy(cfg)
    if change == 'enabled': taxonomy['backends']['docs']['enabled'] = 1
    elif change == 'intent': cfg['router']['intents']['documental'] = 1
    elif change == 'read': cfg['read']['enabled'] = False
    elif change == 'routing': taxonomy['categories'][0]['routing']['docs'] = False
    elif change == 'version': entry.write_bytes(entry.read_bytes().replace(b'version: 7', b'version: 0'))
    elif change == 'private': cfg['_read_context'] = {'entries': ['forged']}
    elif change == 'config': cfg['export_dir'] = 'changed-projection'
    policy.write_text(json.dumps(taxonomy), encoding='utf-8')
    result = module.prepare(tmp_path, 'docs', 'documental', expected_config=original)
    assert result['status'] == 'unavailable' and result['context'] is None and result['reason']


def test_all_documental_sources_must_satisfy_filters_before_inference(tmp_path):
    cfg, taxonomy, policy, entry = project(tmp_path)
    module = load_context()
    filters = {'tipo': 'adr', 'area': 'billing', 'iniciativa': '', 'claves': []}
    seen = []
    def accept(meta, requested):
        seen.append((meta['version'], requested['area']))
        return 'area:billing' in meta['tags']
    result = module.prepare(tmp_path, 'docs', 'documental', expected_config=cfg,
                            filters=filters, accept_entry=accept)
    assert result['status'] == 'ok' and seen == [(7, 'billing')]
    assert result['context']['filters_authorized'] is True
    filters['area'] = 'operations'
    denied = module.prepare(tmp_path, 'docs', 'documental', expected_config=cfg,
                            filters=filters, accept_entry=lambda *_: False)
    assert denied['status'] == 'unavailable' and denied['reason'] == 'filters_not_supported'
    no_checker = module.prepare(tmp_path, 'docs', 'documental', expected_config=cfg, filters=filters)
    assert no_checker['status'] == 'unavailable' and no_checker['reason'] == 'filters_not_supported'


def test_expired_deadline_fails_before_loading_any_reader(tmp_path, monkeypatch):
    module = load_context()
    monkeypatch.setattr(module, '_load', lambda *_: pytest.fail('expired authorization must not read'))
    result = module.prepare(tmp_path, 'docs', 'documental', expected_config={}, deadline=time.monotonic() - 1)
    assert result['status'] == 'unavailable' and result['reason'] == 'read_deadline'


def test_authorization_stops_new_local_io_when_deadline_expires(tmp_path, monkeypatch):
    cfg, taxonomy, policy, first = project(tmp_path)
    for number in range(40):
        raw = first.read_bytes().replace(b'synthetic.DECISION.one', f'synthetic.DECISION.item{number}'.encode())
        (first.parent / f'item{number}.md').write_bytes(raw)
    module = load_context()
    clock = [100.0]
    monkeypatch.setattr(time, 'monotonic', lambda: clock[0])
    started_io = []
    original_load = module._load
    def load(name):
        loaded = original_load(name)
        if name == 'knowledge-view.py':
            original_view_load = loaded._load
            def view_load(filename):
                reader = original_view_load(filename)
                if filename == 'local-read.py':
                    for attribute in ('read_text', 'list_names'):
                        original = getattr(reader, attribute)
                        def observed(*args, _original=original, **kwargs):
                            started_io.append(clock[0])
                            value = _original(*args, **kwargs)
                            clock[0] += 0.1
                            return value
                        monkeypatch.setattr(reader, attribute, observed)
                return reader
            monkeypatch.setattr(loaded, '_load', view_load)
        return loaded
    monkeypatch.setattr(module, '_load', load)
    result = module.prepare(tmp_path, 'docs', 'documental', expected_config=cfg)
    assert result['status'] == 'unavailable' and result['reason'] == 'read_deadline'
    assert started_io and max(started_io) < 101.2, started_io
    assert len(started_io) <= 13


def test_missing_helper_degrades_instead_of_raising(tmp_path, monkeypatch):
    cfg, _, _, _ = project(tmp_path)
    module = load_context()
    monkeypatch.setattr(module, '_load', lambda *_: (_ for _ in ()).throw(RuntimeError('PRIVATE_DEPENDENCY')))
    result = module.prepare(tmp_path, 'docs', 'documental', expected_config=cfg)
    assert result == {'status': 'unavailable', 'reason': 'canonical_unavailable', 'context': None}


def test_remote_root_rejects_before_loading_or_probing_reader(tmp_path, monkeypatch):
    module = load_context()
    monkeypatch.setattr(module, '_load', lambda *_: pytest.fail('remote root must not load a reader'))
    result = module.prepare('//synthetic-server/share/project', 'docs', 'documental', expected_config={})
    assert result['status'] == 'unavailable' and result['reason'] == 'root_unavailable'


def test_refresh_rechecks_actual_policy_and_never_resets_deadline(tmp_path):
    cfg, taxonomy, policy, _ = project(tmp_path)
    module = load_context()
    context = module.prepare(tmp_path, 'docs', 'documental', expected_config=cfg)['context']
    taxonomy['backends']['docs']['enabled'] = False
    policy.write_text(json.dumps(taxonomy), encoding='utf-8')
    assert context['refresh']() == {'error': 'policy_changed'}


def test_callback_observes_all_routed_meta_even_without_filters(tmp_path):
    cfg, _, _, _ = project(tmp_path)
    module = load_context()
    seen = []
    def accept(meta, requested):
        seen.append(meta['frontmatter']['id'])
        return True
    result = module.prepare(tmp_path, 'docs', 'documental', expected_config=cfg, accept_entry=accept)
    assert result['status'] == 'ok' and seen == ['synthetic.DECISION.one']


@pytest.mark.parametrize('filters', [[], {'unknown': ''}, {'claves': 'billing'},
    {'claves': ['x'] * 129}, {'area': 7}, {'area': 'x' * 513}, {'claves': ['a\x80b']}])
def test_invalid_filter_shapes_never_load_a_corpus_reader(tmp_path, monkeypatch, filters):
    module = load_context()
    monkeypatch.setattr(module, '_load', lambda *_: pytest.fail('invalid filters started local IO'))
    result = module.prepare(tmp_path, 'docs', 'documental', expected_config={}, filters=filters)
    assert result == {'status': 'unavailable', 'reason': 'canonical_unavailable', 'context': None}


@pytest.mark.parametrize('deadline', [True, 'tomorrow', float('nan'), float('inf')])
def test_non_numeric_or_non_finite_deadline_never_loads_a_reader(tmp_path, monkeypatch, deadline):
    module = load_context()
    monkeypatch.setattr(module, '_load', lambda *_: pytest.fail('invalid deadline started local IO'))
    result = module.prepare(tmp_path, 'docs', 'documental', expected_config={}, deadline=deadline)
    assert result['context'] is None and result['reason'] == 'read_deadline'


@pytest.mark.parametrize('backend,intent', [('', 'documental'), (None, 'documental'),
    ('docs', None), ('docs', 'Documental'), ('docs', 'documental\n')])
def test_invalid_policy_selectors_fail_before_reader(tmp_path, monkeypatch, backend, intent):
    module = load_context()
    monkeypatch.setattr(module, '_load', lambda *_: pytest.fail('invalid selector started local IO'))
    result = module.prepare(tmp_path, backend, intent, expected_config={})
    assert result['context'] is None and result['reason'] == 'policy_invalid'


def test_disabled_read_and_excess_deadline_fail_before_corpus_snapshot(tmp_path, monkeypatch):
    cfg, _, _, _ = project(tmp_path)
    module = load_context()
    original = module._load
    def policy_only(name):
        assert name != 'knowledge-view.py', 'denied request started a corpus snapshot'
        return original(name)
    monkeypatch.setattr(module, '_load', policy_only)
    cfg['read']['enabled'] = False
    assert module.prepare(tmp_path, 'docs', 'documental', expected_config=cfg)['reason'] == 'read_disabled'
    cfg['read']['enabled'] = True
    assert module.prepare(tmp_path, 'docs', 'documental', expected_config=cfg,
                          deadline=time.monotonic() + 10)['reason'] == 'read_deadline'


def test_unreadable_canonical_document_withholds_authority_and_preserves_bytes(tmp_path, monkeypatch):
    import os
    cfg, _, _, entry = project(tmp_path)
    module = load_context()
    raw = entry.read_bytes()
    original_open = os.open
    attempts = []
    def denied(path, *args, **kwargs):
        if Path(path) == entry:
            attempts.append(str(path))
            raise PermissionError('PRIVATE_DENIED_PATH')
        return original_open(path, *args, **kwargs)
    monkeypatch.setattr(os, 'open', denied)
    result = module.prepare(tmp_path, 'docs', 'documental', expected_config=cfg)
    assert result == {'status': 'unavailable', 'reason': 'canonical_incomplete', 'context': None}
    assert attempts and entry.read_bytes() == raw and 'PRIVATE_' not in json.dumps(result)


def test_empty_canon_never_mints_an_authorizing_context(tmp_path):
    cfg, _, _, entry = project(tmp_path)
    entry.unlink()
    result = load_context().prepare(tmp_path, 'docs', 'documental', expected_config=cfg)
    assert result == {'status': 'unavailable', 'reason': 'canonical_empty', 'context': None}


def test_predicate_cannot_extend_deadline_or_mutate_canonical_policy(tmp_path, monkeypatch):
    cfg, _, _, entry = project(tmp_path)
    module = load_context()
    clock = [100.0]
    monkeypatch.setattr(time, 'monotonic', lambda: clock[0])
    before = entry.read_bytes()
    def slow_accept(meta, filters):
        meta['texto'] = 'forged'
        filters['area'] = 'forged'
        clock[0] = 102.0
        return True
    result = module.prepare(tmp_path, 'docs', 'documental', expected_config=cfg, accept_entry=slow_accept)
    assert result['reason'] == 'read_deadline' and result['context'] is None
    assert entry.read_bytes() == before


def test_snapshot_without_raw_digest_cannot_authorize_a_document(tmp_path, monkeypatch):
    cfg, _, _, entry = project(tmp_path)
    module = load_context()
    original = module._load
    def incomplete_snapshot(name):
        helper = original(name)
        if name == 'knowledge-view.py':
            snapshot = helper.snapshot
            def without_digest(*args, **kwargs):
                observed = snapshot(*args, **kwargs)
                observed['source_digests'].pop(entry.relative_to(tmp_path).as_posix())
                return observed
            monkeypatch.setattr(helper, 'snapshot', without_digest)
        return helper
    monkeypatch.setattr(module, '_load', incomplete_snapshot)
    result = module.prepare(tmp_path, 'docs', 'documental', expected_config=cfg)
    assert result == {'status': 'unavailable', 'reason': 'canonical_incomplete', 'context': None}
