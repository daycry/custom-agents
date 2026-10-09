"""Synthetic read-only memory contracts; never use consumer data or services."""
import importlib.util
import json
from pathlib import Path
import pytest

HERE = Path(__file__).parent


def load(name):
    spec = importlib.util.spec_from_file_location('test_' + name.replace('-', '_'), HERE / (name + '.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def view():
    return load('knowledge-view')


def entry(root, name='ADR-001', *, folder='adr', state='aceptada', title='Cache segura', body='cache local', approved=False, extra=''):
    rel = 'docs/knowledge/' + ('approved/' if approved else '') + folder + '/' + name + '.md'
    target = root / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    text = f'---\nid: {name}\nestado: {state}\ntitulo: {title}\narea: Cache\n' + ('version: 2\ncategory: DECISION\nevidencia: human_confirmed_rule\n' if approved else '') + extra + '---\n\n# ' + title + '\n' + body
    target.write_text(text, encoding='utf-8', newline='')
    return target


def test_search_shared_ranking_compact_and_no_write(view, tmp_path):
    entry(tmp_path)
    entry(tmp_path, 'ADR-002', title='Otra cosa', body='cache cache cache cache')
    before = sorted(str(p.relative_to(tmp_path)) for p in tmp_path.rglob('*'))
    data = view.query(tmp_path, text='cache')
    assert data['status'] == 'ok' and data['complete']
    assert data['entries'][0]['id'] == 'ADR-001'
    assert all('texto' not in e for e in data['entries'])
    assert data['source'] == 'canonical_knowledge' and data['version'] == 1
    assert data['selected'] is None and data['related'] is None
    assert data['budget']['bytes'] > 0
    assert before == sorted(str(p.relative_to(tmp_path)) for p in tmp_path.rglob('*'))


def test_show_and_related_same_source(view, tmp_path):
    path = entry(tmp_path, extra='sucesor: ADR-002\n')
    entry(tmp_path, 'ADR-002')
    show = view.query(tmp_path, operation='show', id='ADR-001')
    assert show['selected']['texto'] == path.read_bytes().decode('utf-8')
    assert len(show['selected']['source_sha256']) == 64
    rel = view.query(tmp_path, operation='related', id='ADR-001')
    assert rel['selected'] is None
    assert rel['related']['sucesion'][0]['id'] == 'ADR-002'
    assert 'texto' not in json.dumps(rel)


def test_approved_authority_full_id_and_candidates_excluded(view, tmp_path):
    name = 'project.DECISION.long-identity.v2'
    entry(tmp_path, name, approved=True, state='aprobado')
    entry(tmp_path, 'bad', approved=True, state='propuesta')
    entry(tmp_path, 'CANDIDATE', folder='candidates/pending')
    data = view.query(tmp_path, operation='show', id=name)
    assert data['status'] == 'partial' and not data['complete']
    assert data['selected'] is None  # invalid approved snapshot fails closed
    assert 'approved_invalid' in data['issues']
    (tmp_path / 'docs/knowledge/approved/adr/bad.md').unlink()
    data = view.query(tmp_path, operation='show', id=name)
    assert data['status'] == 'ok'
    assert data['selected']['id'] == name and data['selected']['origen'] == 'approved'
    assert data['selected']['version'] == 2


def test_collision_never_selects_first(view, tmp_path):
    entry(tmp_path)
    entry(tmp_path, approved=True, state='aprobado')
    for operation in ('show', 'related'):
        data = view.query(tmp_path, operation=operation, id='ADR-001')
        assert data['status'] == 'ambiguous' and data['selected'] is None and data['related'] is None


@pytest.mark.parametrize('arguments', [dict(operation='delete'), dict(limit=True), dict(limit=21), dict(limit=0), dict(id='x'*257, operation='show'), dict(text='a'*1001), dict(text=[]), dict(area=1), dict(operation='show'), dict(operation='show',id='ADR-001',text='x')])
def test_invalid_inputs_without_reads(view, tmp_path, monkeypatch, arguments):
    monkeypatch.setattr(view, 'snapshot', lambda *a, **kw: pytest.fail('invalid input read corpus'))
    assert view.query(tmp_path, **arguments)['status'] == 'invalid_request'


def test_no_corpus_is_explicit(view, tmp_path):
    data = view.query(tmp_path)
    assert data['status'] == 'not_found' and data['complete'] and data['entries'] == []


@pytest.mark.parametrize('failure', ['oversize', 'encoding', 'redirect'])
def test_omitted_sources_are_partial(view, tmp_path, failure):
    path = entry(tmp_path)
    if failure == 'oversize': path.write_bytes(b'x' * (256*1024+1))
    elif failure == 'encoding': path.write_bytes(b'\xff')
    else:
        path.unlink()
        outside = tmp_path / 'outside.md'
        outside.write_text('PRIVATE OUTSIDE')
        try: path.symlink_to(outside)
        except OSError: pytest.skip('symlink privilege unavailable')
    data = view.query(tmp_path)
    assert data['status'] == 'partial' and not data['complete'] and data['issues']
    assert 'PRIVATE OUTSIDE' not in json.dumps(data)


def test_scan_file_byte_and_depth_budgets(view, tmp_path):
    for i in range(150): entry(tmp_path, f'ADR-{i:03}')
    data = view.query(tmp_path)
    assert data['status'] == 'partial'
    assert data['budget']['files'] <= 128 and data['budget']['entries'] <= 256 and data['budget']['bytes'] <= 2*1024*1024


def test_body_and_labels_redacted_before_clip(view, tmp_path):
    secret = 'sk-' + 'A'*30
    entry(tmp_path, title='x'*155 + ' ' + secret, body='x'*11995+' '+secret+' '+'x'*200)
    data = view.query(tmp_path, operation='show', id='ADR-001')
    assert secret not in json.dumps(data)
    assert len(data['selected']['texto']) <= 12000
    assert data['status'] == 'partial' and 'text_budget' in data['issues']
    assert len(json.dumps(data, ensure_ascii=False).encode('utf-8')) <= 65536


def test_missing_helper_is_unavailable_without_detail(view, tmp_path, monkeypatch):
    monkeypatch.setattr(view, '_load', lambda *a: (_ for _ in ()).throw(OSError('private path secret')))
    data = view.query(tmp_path)
    assert data['status'] == 'unavailable' and 'private path' not in json.dumps(data)


def test_ordinary_find_uses_snapshot_and_never_caches_partial(view, tmp_path, monkeypatch):
    find = load('knowledge-find')
    entry(tmp_path).write_bytes(b'x'*(256*1024+1))
    monkeypatch.setattr(find, 'construir_indice', lambda *a: pytest.fail('partial snapshot cached'))
    entries, path, info = find.abrir_corpus(str(tmp_path))
    assert entries == [] and path is None
    assert info['corpus_read']['complete'] is False


def test_unknown_legacy_state_partial(view, tmp_path):
    entry(tmp_path, state='nonsense')
    data = view.query(tmp_path)
    assert data['status'] == 'partial' and 'unknown_state' in data['issues']


def test_legacy_namespaced_id_is_not_shortened(view, tmp_path):
    entry(tmp_path, 'fixture.ADR-001.v2')
    data = view.query(tmp_path, operation='show', id='fixture.ADR-001.v2')
    assert data['selected']['id'] == 'fixture.ADR-001.v2'


def test_cumulative_byte_budget_and_large_output(view, tmp_path):
    for i in range(12): entry(tmp_path, f'ADR-{i:03}', body='文'*85000)
    data = view.query(tmp_path)
    assert data['status'] == 'partial' and not data['complete']
    assert data['budget']['bytes'] <= view.MAX_BYTES
    assert len(json.dumps(data, ensure_ascii=False).encode('utf-8')) <= view.MAX_OUTPUT_BYTES


def test_approved_depth_budget(view, tmp_path):
    entry(tmp_path, 'deep.DECISION.1', approved=True, state='aprobado', folder='adr/' + '/'.join('x' for _ in range(9)))
    data = view.query(tmp_path)
    assert data['status'] == 'partial' and 'depth_budget' in data['issues']


def test_malformed_taxonomy_never_loads_services(view, tmp_path):
    entry(tmp_path)
    cfg = tmp_path / '.claude/knowledge-services/taxonomy.json'
    cfg.parent.mkdir(parents=True)
    cfg.write_text('{"version":1,"categories":"invalid","backends":{"network":{"type":"malicious"}}}')
    data = view.query(tmp_path)
    assert data['status'] == 'partial' and 'taxonomy_invalid' in data['issues']
    assert data['entries'][0]['origen'] == 'legacy'


def test_related_collision_is_unresolved_and_has_no_body(view, tmp_path):
    entry(tmp_path, 'ADR-002', extra='sucesor: ADR-001\n')
    entry(tmp_path)
    entry(tmp_path, approved=True, state='aprobado')
    data = view.query(tmp_path, operation='related', id='ADR-002')
    assert data['status'] == 'partial'
    assert data['related']['sucesion'][0]['entry'] is None
    assert 'unresolved_relation' in data['issues']


def test_duplicate_taxonomy_keys_are_corruption(view, tmp_path):
    entry(tmp_path, 'fixture.DECISION.1', approved=True, state='aprobado')
    cfg = tmp_path / '.claude/knowledge-services/taxonomy.json'
    cfg.parent.mkdir(parents=True)
    cfg.write_text('{"version":99,"version":1,"categories":[{"key":"DECISION","folder":"adr","min_evidence":"human_confirmed_rule"}]}')
    data = view.query(tmp_path)
    assert data['status'] == 'partial' and 'taxonomy_invalid' in data['issues']
    assert not data['entries']


def test_reader_stops_metadata_after_file_budget(view, tmp_path, monkeypatch):
    entry(tmp_path)
    original = view._load
    reader = original('local-read.py')
    events = []
    original_read, original_list = reader.read_text, reader.list_names
    def read(*args, **kwargs):
        events.append('read')
        return original_read(*args, **kwargs)
    def listing(*args, **kwargs):
        events.append('list')
        return original_list(*args, **kwargs)
    reader.read_text, reader.list_names = read, listing
    monkeypatch.setattr(view, '_load', lambda name: reader if name == 'local-read.py' else original(name))
    monkeypatch.setattr(view, 'MAX_FILES', 2)
    snap = view.snapshot(tmp_path)
    assert events == ['list', 'read', 'list', 'read']
    assert snap['corpus_read']['budget']['files'] == 2
    assert 'file_budget' in snap['corpus_read']['issues']


def test_unresolved_successor_explicit(view, tmp_path):
    entry(tmp_path, extra='sucesor: ADR-099\n')
    data = view.query(tmp_path, operation='related', id='ADR-001')
    assert data['related']['sucesion'][0]['id'] == 'ADR-099'
    assert data['related']['sucesion'][0]['entry'] is None
    assert data['status'] == 'partial' and 'unresolved_relation' in data['issues']


def test_invalid_operation_is_not_echoed(view, tmp_path):
    data = view.query(tmp_path, operation='secret-' + 'A'*100000)
    assert data['status'] == 'invalid_request'
    assert data['operation'] == '' and len(json.dumps(data)) < 1000


def test_relations_have_cumulative_result_limit(view, tmp_path):
    for i in range(25): entry(tmp_path, f'ADR-{i:03}', extra='iniciativa: fixture\n')
    data = view.query(tmp_path, operation='related', id='ADR-000')
    assert sum(len(rows) for rows in data['related'].values()) <= 20
    assert 'result_budget' in data['issues']


def test_output_bytes_limit_is_explicit(view, tmp_path):
    for i in range(20):
        path = entry(tmp_path, f'fixture.DECISION.{i}', approved=True, state='aprobado', title='😀'*160)
        path.write_text(path.read_text(encoding='utf-8').replace('evidencia: human_confirmed_rule', 'evidencia: ' + '😀'*1000), encoding='utf-8', newline='')
    data = view.query(tmp_path, limit=20)
    assert data['status'] == 'partial' and 'output_budget' in data['issues']
    assert len(data['entries']) < 20
    assert len(json.dumps(data, ensure_ascii=False).encode('utf-8')) <= 65536


def test_ordinary_collision_not_cached_and_canonical_successor_unresolved(view, tmp_path, monkeypatch):
    find = load('knowledge-find')
    entry(tmp_path)
    entry(tmp_path, approved=True, state='aprobado')
    entry(tmp_path, 'ADR-002', extra='sucesor: ADR-001\n')
    monkeypatch.setattr(find, 'construir_indice', lambda *a: pytest.fail('collided snapshot cached'))
    entries, cache, info = find.abrir_corpus(str(tmp_path))
    assert not info['corpus_read']['complete'] and cache is None
    base = find.buscar_id(entries, 'ADR-002')
    assert find.relaciones(entries, base)['sucesion'][0][1] is None


@pytest.mark.parametrize('identifier', [[], None, 'x'*257, ''])
def test_invalid_selector_uses_shared_validation_without_reads(view, tmp_path, monkeypatch, identifier):
    monkeypatch.setattr(view, 'snapshot', lambda *a, **kw: pytest.fail('invalid selector read'))
    assert not view.valid_request(operation='show', id=identifier)
    assert view.query(tmp_path, operation='show', id=identifier)['status'] == 'invalid_request'


def test_path_shaped_selector_is_only_literal_identity(view, tmp_path):
    entry(tmp_path)
    secret = tmp_path / 'escape'
    secret.write_text('PRIVATE FILE NOT CORPUS')
    assert view.valid_request(operation='show', id='../escape')
    data = view.query(tmp_path, operation='show', id='../escape')
    assert data['status'] == 'not_found'
    assert 'PRIVATE FILE NOT CORPUS' not in json.dumps(data)


def test_unicode_legacy_selector_supported(view, tmp_path):
    entry(tmp_path, '記憶-001.v2')
    assert view.valid_request(operation='show', id='記憶-001.v2')
    assert view.query(tmp_path, operation='show', id='記憶-001.v2')['selected']['id'] == '記憶-001.v2'


def test_approved_markdown_named_directory_is_traversed(view, tmp_path):
    entry(tmp_path, 'fixture.DECISION.1', approved=True, state='aprobado', folder='adr/history.md')
    data = view.query(tmp_path, operation='show', id='fixture.DECISION.1')
    assert data['status'] == 'ok' and data['selected']['origen'] == 'approved'


def test_legacy_declared_version_evidence_and_category_remain_legacy(view, tmp_path):
    entry(tmp_path, extra='version: 7\nevidencia: validated_case\ncategory: DECISION\n')
    data = view.query(tmp_path, operation='show', id='ADR-001')
    assert data['selected']['version'] == 7
    assert data['selected']['evidencia'] == 'validated_case'
    assert data['selected']['category'] == 'DECISION'
    assert data['selected']['origen'] == 'legacy' and data['selected']['estado'] == 'aceptada'


def test_invalid_legacy_version_explicit(view, tmp_path):
    entry(tmp_path, extra='version: wrong\n')
    data = view.query(tmp_path, operation='show', id='ADR-001')
    assert data['status'] == 'partial' and 'version_invalid' in data['issues']
    assert data['selected']['version'] is None


@pytest.mark.parametrize('missing', ['knowledge-local.py', 'knowledge-taxonomy-local.py'])
def test_missing_approved_helper_preserves_legacy(view, tmp_path, monkeypatch, missing):
    entry(tmp_path)
    original = view._load
    def loading(name):
        if name == 'knowledge-local.py':
            if missing == name: raise FileNotFoundError('own missing helper')
            local = original(name)
            local._TAXONOMY = None
            return local
        return original(name)
    monkeypatch.setattr(view, '_load', loading)
    data = view.query(tmp_path, text='cache')
    assert data['status'] == 'partial' and not data['complete']
    assert data['entries'][0]['id'] == 'ADR-001'
    assert 'approved_helper_unavailable' in data['issues']


@pytest.mark.parametrize('short_peer', [False, True])
def test_namespaced_relations_use_full_identity_and_reverse(view, tmp_path, short_peer):
    entry(tmp_path, 'project.ADR-001.v2', extra='sucesor: project.ADR-002.v2\n')
    entry(tmp_path, 'project.ADR-002.v2', extra='sustituye: project.ADR-001.v2\n')
    if short_peer: entry(tmp_path, 'ADR-002')
    data = view.query(tmp_path, operation='related', id='project.ADR-001.v2')
    target = data['related']['sucesion'][0]
    assert target['id'] == 'project.ADR-002.v2'
    assert target['entry']['id'] == 'project.ADR-002.v2'
    reverse = view.query(tmp_path, operation='related', id='project.ADR-002.v2')
    assert reverse['related']['sucesion'][0]['entry']['id'] == 'project.ADR-001.v2'


def test_missing_full_relation_never_uses_short_near_identity(view, tmp_path):
    entry(tmp_path, 'project.ADR-001', extra='sucesor: project.ADR-002.v2\n')
    entry(tmp_path, 'ADR-002')
    data = view.query(tmp_path, operation='related', id='project.ADR-001')
    assert data['status'] == 'partial'
    target = data['related']['sucesion'][0]
    assert target['id'] == 'project.ADR-002.v2' and target['entry'] is None


def test_full_relation_lookup_casefold_and_reverse(view, tmp_path):
    entry(tmp_path, 'Project.ADR-001.V2', extra='sucesor: PROJECT.ADR-002.V2\n')
    entry(tmp_path, 'project.ADR-002.v2')
    data = view.query(tmp_path, operation='related', id='Project.ADR-001.V2')
    assert data['related']['sucesion'][0]['entry']['id'] == 'project.ADR-002.v2'
    reverse = view.query(tmp_path, operation='related', id='project.ADR-002.v2')
    assert reverse['related']['sucesion'][0]['entry']['id'] == 'Project.ADR-001.V2'


@pytest.mark.parametrize('approved', [False, True])
@pytest.mark.parametrize('version,expected', [(-1, None), (0, None), (9007199254740993, '9007199254740993'), (7, 7)])
def test_projected_versions_preserve_exact_value(view, tmp_path, approved, version, expected):
    path = entry(tmp_path, approved=approved, state='aprobado' if approved else 'aceptada', extra='' if approved else f'version: {version}\n')
    if approved: path.write_text(path.read_text(encoding='utf-8').replace('version: 2', f'version: {version}'), encoding='utf-8', newline='')
    data = view.query(tmp_path, operation='show', id='ADR-001')
    assert data['selected']['version'] == expected
    if version <= 0: assert data['status'] == 'partial' and 'version_invalid' in data['issues']
    else: assert data['status'] == 'ok'


def test_changed_read_probe_reserves_cumulative_byte(view, tmp_path, monkeypatch):
    entry(tmp_path)
    original = view._load
    reader = original('local-read.py')
    max_values = []
    def read(root, relative, max_bytes):
        max_values.append(max_bytes)
        return {'status': 'changed_path', 'text': None, 'bytes': max_bytes + 1}
    reader.read_text = read
    monkeypatch.setattr(view, '_load', lambda name: reader if name == 'local-read.py' else original(name))
    monkeypatch.setattr(view, 'MAX_BYTES', 50)
    data = view.query(tmp_path)
    assert data['budget']['bytes'] <= 50
    assert max_values == [49]
    assert data['status'] == 'partial' and 'byte_budget' in data['issues']


def test_many_empty_declared_folders_budget_physical_scans(view, tmp_path, monkeypatch):
    entry(tmp_path)
    cfg = tmp_path / '.claude/knowledge-services/taxonomy.json'
    cfg.parent.mkdir(parents=True)
    cfg.write_text(json.dumps({'version': 1, 'categories': [
        {'key': str(i), 'folder': str(i), 'min_evidence': 'single_case'} for i in range(3000)
    ]}), encoding='utf-8')
    assert cfg.stat().st_size < view.MAX_FILE_BYTES
    original = view._load
    reader = original('local-read.py')
    original_list = reader.list_names
    calls = []
    def listing(*args, **kw):
        calls.append(args[1])
        return original_list(*args, **kw)
    reader.list_names = listing
    monkeypatch.setattr(view, '_load', lambda name: reader if name == 'local-read.py' else original(name))
    data = view.query(tmp_path)
    assert len(calls) <= 256 and data['budget']['scans'] == len(calls)
    assert data['status'] == 'partial' and 'scan_call_budget' in data['issues']
    assert data['entries'][0]['id'] == 'ADR-001'


def test_relation_parser_does_not_alias_route_tokens(view):
    find = load('knowledge-find')
    assert find._ids_en('https://example.test/project.ADR-002.v2') == []
    assert find._ids_en('folder/project.ADR-002.v2') == []
    assert find._ids_en('obsoleta (sustituida por ADR-002).') == ['ADR-002']


def test_opaque_declared_relations_and_approved_target(view, tmp_path):
    old = entry(tmp_path, 'ADR-001', extra='sucesor: project.DECISION.foo.v2\n')
    old.write_text(old.read_text(encoding='utf-8').replace('id: ADR-001', 'id: project:DEC-001/variant'), encoding='utf-8', newline='')
    entry(tmp_path, 'project.DECISION.foo.v2', approved=True, state='aprobado')
    data = view.query(tmp_path, operation='related', id='project:DEC-001/variant')
    assert data['related']['sucesion'][0]['entry']['id'] == 'project.DECISION.foo.v2'
    reverse = view.query(tmp_path, operation='related', id='project.DECISION.foo.v2')
    assert reverse['related']['sucesion'][0]['entry']['id'] == 'project:DEC-001/variant'


def test_route_shaped_declaration_is_full_unresolved_not_near_id(view, tmp_path):
    entry(tmp_path, 'ADR-001', extra='sucesor: folder/ADR-002.md\n')
    entry(tmp_path, 'ADR-002')
    data = view.query(tmp_path, operation='related', id='ADR-001')
    assert data['status'] == 'partial'
    assert data['related']['sucesion'][0]['id'] == 'folder/ADR-002.md'
    assert data['related']['sucesion'][0]['entry'] is None


def test_full_identity_with_spaces_wins_over_short_prose_alias(view, tmp_path):
    source = entry(tmp_path, 'ADR-001', extra='sucesor: ADR-002 variant\n')
    target = entry(tmp_path, 'ADR-003')
    target.write_text(target.read_text(encoding='utf-8').replace('id: ADR-003', 'id: ADR-002 variant'), encoding='utf-8', newline='')
    entry(tmp_path, 'ADR-002')
    data = view.query(tmp_path, operation='related', id='ADR-001')
    assert data['related']['sucesion'][0]['entry']['id'] == 'ADR-002 variant'


@pytest.mark.parametrize('declared,expected', [
    ('[project:DEC-001/variant, project.DECISION.foo.v2]', ['project:DEC-001/variant', 'project.DECISION.foo.v2']),
    ('["label,comma", plain]', ['label,comma', 'plain']),
    ('- project:DEC-001/variant - project.DECISION.foo.v2', ['project:DEC-001/variant', 'project.DECISION.foo.v2']),
    ('ADR-002 (aceptada)', ['ADR-002']),
    ('project.ADR-002.v2 (unknown)', ['project.ADR-002.v2 (unknown)']),
    ("[Don't, another]", ["Don't", 'another']),
])
def test_structured_reference_parser_preserves_literals(declared, expected):
    find = load('knowledge-find')
    assert find._declared_relation_ids([declared]) == expected


def test_overlong_relation_identifier_is_omitted_not_clipped(view, tmp_path):
    entry(tmp_path, extra='sucesor: ' + 'x'*257 + '\n')
    data = view.query(tmp_path, operation='related', id='ADR-001')
    assert data['status'] == 'partial' and 'identity_invalid' in data['issues']
    assert data['related']['sucesion'] == []


def test_literal_identity_whitespace_never_aliases_near_id(view, tmp_path):
    target = entry(tmp_path, 'ADR-002')
    target.write_text(target.read_text(encoding='utf-8').replace('id: ADR-002', "id: ' custom'"), encoding='utf-8', newline='')
    near = entry(tmp_path, 'ADR-003')
    near.write_text(near.read_text(encoding='utf-8').replace('id: ADR-003', 'id: custom'), encoding='utf-8', newline='')
    entry(tmp_path, 'ADR-001', extra="sucesor: ' custom'\n")
    data = view.query(tmp_path, operation='show', id=' custom')
    assert data['selected']['id'] == ' custom'
    related = view.query(tmp_path, operation='related', id='ADR-001')
    assert related['related']['sucesion'][0]['entry']['id'] == ' custom'
    find = load('knowledge-find')
    entries = find.cargar_corpus(str(tmp_path))
    assert find.buscar_id(entries, ' custom')['id'] == ' custom'


def test_unicode_lookup_uses_same_casefold_in_view_and_cli(view, tmp_path):
    path = entry(tmp_path, 'ADR-001')
    path.write_text(path.read_text(encoding='utf-8').replace('id: ADR-001', 'id: İ'), encoding='utf-8', newline='')
    data = view.query(tmp_path, operation='show', id='i\u0307')
    assert data['selected']['id'] == 'İ'
    find = load('knowledge-find')
    assert find.buscar_id(find.cargar_corpus(str(tmp_path)), 'i\u0307')['id'] == 'İ'


@pytest.mark.parametrize('literal', ['[ADR-002]', '- ADR-002', 'ADR-002 (literal)', 'ADR-002 # literal', 'ADR-002 "literal"'])
def test_quoted_relation_scalar_never_becomes_short_alias(view, tmp_path, literal):
    entry(tmp_path, 'ADR-001', extra="sucesor: '" + literal + "'\n")
    target = entry(tmp_path, 'ADR-003')
    target.write_text(target.read_text(encoding='utf-8').replace('id: ADR-003', "id: '" + literal + "'"), encoding='utf-8', newline='')
    entry(tmp_path, 'ADR-002')
    data = view.query(tmp_path, operation='related', id='ADR-001')
    assert data['status'] == 'ok' and data['complete']
    assert data['related']['sucesion'][0]['id'] == literal
    assert data['related']['sucesion'][0]['entry']['id'] == literal
    reverse = view.query(tmp_path, operation='related', id=literal)
    assert reverse['related']['sucesion'][0]['entry']['id'] == 'ADR-001'


@pytest.mark.parametrize('literal', ['[ADR-099]', '- ADR-099', 'ADR-099 (literal)', 'ADR-099 # literal'])
def test_missing_quoted_relation_scalar_preserves_full_label(view, tmp_path, literal):
    entry(tmp_path, extra="sucesor: '" + literal + "'\n")
    data = view.query(tmp_path, operation='related', id='ADR-001')
    assert data['status'] == 'partial' and not data['complete']
    assert data['related']['sucesion'][0]['id'] == literal
    assert data['related']['sucesion'][0]['entry'] is None


@pytest.mark.parametrize('declaration', [
    'sucesor: ["[ADR-002]", "- ADR-002", ADR-002]\n',
    "sucesor:\n  - '[ADR-002]'\n  - '- ADR-002'\n  - ADR-002\n",
])
def test_real_relation_lists_preserve_quoted_items_and_reverse(view, tmp_path, declaration):
    entry(tmp_path, extra=declaration)
    for filename, literal in [('ADR-003', '[ADR-002]'), ('ADR-004', '- ADR-002'), ('ADR-002', 'ADR-002')]:
        path = entry(tmp_path, filename)
        path.write_text(path.read_text(encoding='utf-8').replace('id: ' + filename, "id: '" + literal + "'"), encoding='utf-8', newline='')
    data = view.query(tmp_path, operation='related', id='ADR-001')
    assert {item['id'] for item in data['related']['sucesion']} == {'[ADR-002]', '- ADR-002', 'ADR-002'}
    assert all(item['entry'] is not None for item in data['related']['sucesion'])
    for literal in ['[ADR-002]', '- ADR-002', 'ADR-002']:
        reverse = view.query(tmp_path, operation='related', id=literal)
        assert reverse['related']['sucesion'][0]['id'] == 'ADR-001'


def test_old_cached_short_relation_rebuilds_for_quoted_identity(tmp_path):
    find = load('knowledge-find')
    if not find.fts5_disponible(): pytest.skip('sqlite without FTS5')
    entry(tmp_path, extra="sucesor: '[ADR-002]'\n")
    target = entry(tmp_path, 'ADR-003')
    target.write_text(target.read_text(encoding='utf-8').replace('id: ADR-003', "id: '[ADR-002]'"), encoding='utf-8', newline='')
    entry(tmp_path, 'ADR-002')
    sources = find.ficheros_corpus(str(tmp_path))
    old_entries = find.parsear_corpus(sources)
    find.buscar_id(old_entries, 'ADR-001')['sucesores'] = ['ADR-002']
    current_version = find.INDICE_VERSION
    find.INDICE_VERSION = '4'
    find.construir_indice(find.ruta_indice(str(tmp_path)), old_entries, find.hash_corpus(sources))
    find.INDICE_VERSION = current_version
    rebuilt, _, state = find.abrir_corpus(str(tmp_path))
    assert state['indice'] == 'reconstruido'
    assert find.buscar_id(rebuilt, 'ADR-001')['sucesores'] == ['[ADR-002]']
    cached, _, state = find.abrir_corpus(str(tmp_path))
    assert state['indice'] == 'cache'
    assert find.buscar_id(cached, 'ADR-001')['sucesores'] == ['[ADR-002]']
    assert find._relaciones_sucesion(cached, find.buscar_id(cached, '[ADR-002]'))[0][2] == 'ADR-001'


@pytest.mark.parametrize('declaration', [
    'sucesor: ["ADR-099 (literal)"]\n',
    "sucesor:\n  - 'ADR-099 (literal)'\n",
])
@pytest.mark.parametrize('resolved', [False, True])
def test_quoted_relation_list_item_never_aliases_annotation(view, tmp_path, declaration, resolved):
    literal = 'ADR-099 (literal)'
    entry(tmp_path, extra=declaration)
    entry(tmp_path, 'ADR-099')
    if resolved:
        target = entry(tmp_path, 'ADR-003')
        target.write_text(target.read_text(encoding='utf-8').replace('id: ADR-003', "id: '" + literal + "'"), encoding='utf-8', newline='')
    data = view.query(tmp_path, operation='related', id='ADR-001')
    relation = data['related']['sucesion'][0]
    assert relation['id'] == literal
    if resolved:
        assert data['status'] == 'ok' and relation['entry']['id'] == literal
        reverse = view.query(tmp_path, operation='related', id=literal)
        assert reverse['related']['sucesion'][0]['id'] == 'ADR-001'
    else:
        assert data['status'] == 'partial' and relation['entry'] is None


@pytest.mark.parametrize('resolved', [False, True])
@pytest.mark.parametrize('form', ['scalar', 'inline', 'block'])
@pytest.mark.parametrize('quote,slashes,escaped_quote', [
    ("'", 0, False), ("'", 1, False), ("'", 2, False), ("'", 3, False),
    ('"', 0, False), ('"', 2, False), ('"', 4, False),
    ('"', 1, True), ('"', 3, True),
])
def test_relation_quote_delimiters_preserve_backslashes(view, tmp_path, quote, slashes, escaped_quote, form, resolved):
    # IDs retain their literal spelling; this flat reader does not decode YAML escapes.
    literal = 'ADR-002 # inside ' + '\\' * slashes
    if escaped_quote:
        literal += '" # still inside'
    quoted = quote + literal + quote
    declaration = {
        'scalar': 'sucesor: ' + quoted + ' # external comment\n',
        'inline': 'sucesor: [' + quoted + ', ADR-004] # external comment\n',
        'block': 'sucesor:\n  - ' + quoted + '\n  - ADR-004\n',
    }[form]
    entry(tmp_path, extra=declaration)
    entry(tmp_path, 'ADR-002')  # A near ID must never win over the opaque declaration.
    if form != 'scalar':
        entry(tmp_path, 'ADR-004')
    if resolved:
        target = entry(tmp_path, 'ADR-003')
        target.write_text(target.read_text(encoding='utf-8').replace('id: ADR-003', 'id: ' + quoted), encoding='utf-8', newline='')
        shown = view.query(tmp_path, operation='show', id=literal)
        assert shown['status'] == 'ok' and shown['selected']['id'] == literal
    data = view.query(tmp_path, operation='related', id='ADR-001')
    rows = {item['id']: item for item in data['related']['sucesion']}
    assert set(rows) == ({literal} if form == 'scalar' else {literal, 'ADR-004'})
    assert data['status'] == ('ok' if resolved else 'partial')
    assert data['complete'] is resolved
    assert rows[literal]['entry'] is None if not resolved else rows[literal]['entry']['id'] == literal
    if not resolved:
        assert 'unresolved_relation' in data['issues']
    for identifier in ([literal] if resolved else []) + (['ADR-004'] if form != 'scalar' else []):
        reverse = view.query(tmp_path, operation='related', id=identifier)
        assert reverse['related']['sucesion'][0]['id'] == 'ADR-001'


@pytest.mark.parametrize('resolved', [False, True])
def test_single_quote_trailing_backslash_external_comment(view, tmp_path, resolved):
    literal = 'ADR-002\\'
    entry(tmp_path, extra="sucesor: '" + literal + "' # external comment\n")
    entry(tmp_path, 'ADR-002')
    if resolved:
        target = entry(tmp_path, 'ADR-003')
        target.write_text(target.read_text(encoding='utf-8').replace('id: ADR-003', "id: '" + literal + "'"), encoding='utf-8', newline='')
        assert view.query(tmp_path, operation='show', id=literal)['selected']['id'] == literal
    data = view.query(tmp_path, operation='related', id='ADR-001')
    row = data['related']['sucesion'][0]
    assert row['id'] == literal
    assert data['status'] == ('ok' if resolved else 'partial')
    assert row['entry'] is None if not resolved else row['entry']['id'] == literal
    if resolved:
        reverse = view.query(tmp_path, operation='related', id=literal)
        assert reverse['related']['sucesion'][0]['id'] == 'ADR-001'
