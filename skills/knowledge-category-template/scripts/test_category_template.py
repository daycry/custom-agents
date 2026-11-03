"""Synthetic projects only: no service startup, network or approved knowledge writes."""
import copy
import hashlib
import importlib.util
import json
import io
import subprocess
import sys
from types import SimpleNamespace
from pathlib import Path

import pytest

PATH = Path(__file__).with_name('category-template.py')
TEMPLATE = ('---\ncategory: meetings\nevidencia:\nfuentes:\ntags:\nfecha:\nparticipantes:\n---\n'
            '# Acta\n\n## Objetivo\n\n## Acuerdos\n')
DOCUMENT = ('---\ncategory: meetings\nevidencia: single_case\nfuentes: [docs/source.md]\n'
            'tags: [area:operations]\nfecha: 2026-11-03\nparticipantes: [Equipo]\n---\n'
            '# Acta\n\n## Objetivo\nRevisar el despliegue.\n\n## Acuerdos\nConservar el procedimiento.\n')


@pytest.fixture
def api():
    spec = importlib.util.spec_from_file_location('category_workflow_test', PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def root(tmp_path):
    taxonomy = {'version': 1, 'id_prefix': 'owned', 'utility_scoring': False,
                'categories': [{'key': 'DECISION', 'folder': 'adr', 'min_evidence': 'single_case', 'routing': {'kwipu': False}}],
                'backends': {'kwipu': {'type': 'markdown-export', 'enabled': False, 'config': {'export_dir': 'published'}}}}
    p = tmp_path / '.claude/knowledge-services/taxonomy.json'
    p.parent.mkdir(parents=True)
    p.write_text(json.dumps(taxonomy, indent=2), encoding='utf-8')
    return tmp_path


@pytest.fixture
def definition():
    return {'category': {'key': 'meetings', 'folder': 'meetings', 'min_evidence': 'single_case',
                         'template': 'config/knowledge-templates/meeting.md', 'inbox': 'docs/meetings',
                         'allowed_producers': ['human'], 'required_metadata': ['fecha', 'participantes'],
                         'required_sections': ['Objetivo', 'Acuerdos']}, 'template_text': TEMPLATE}


def tree(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*') if p.is_file()}


def setup(api, root, definition):
    preview = api.configure(root, definition)
    assert preview['status'] == 'preview', preview
    result = api.configure(root, definition, apply=True, expected_sha256=preview['expected_sha256'])
    assert result['status'] == 'configured', result
    return result


def add_document(root, text=DOCUMENT):
    p = root / 'docs/meetings/acta.md'
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(text.encode('utf-8'))
    return p


@pytest.mark.parametrize('example,origin', [('meetings', 'human'), ('faq', 'agent'),
                                          ('mixed', 'human'), ('mixed', 'agent')])
def test_shipped_examples_can_configure_check_and_propose(api, root, example, origin):
    definition = json.loads((PATH.parents[3] / 'docs/examples/memory/categories' / (example + '.json')).read_text(encoding='utf-8'))
    setup(api, root, definition)
    cat = definition['category']
    fm = {'category': cat['key'], 'content_origin': origin, 'evidencia': cat['min_evidence'],
          'fuentes': ['docs/example.md'], 'tags': ['area:example']}
    fm.update({key: 'Example value' for key in cat['required_metadata']})
    body = '\n'.join('## ' + title + '\nVerified example.\n' for title in cat['required_sections'])
    source = root / cat['inbox'] / 'example.md'
    source.parent.mkdir(parents=True)
    source.write_text(api._load('knowledge-curation.py')._render(fm, body), encoding='utf-8')
    before = tree(root)
    preview = api.check_category(root, cat['key'], origin=origin)
    assert preview['valid'] and preview['complete'], preview
    assert tree(root) == before
    result = api.check_category(root, cat['key'], origin=origin, propose=True,
                                expected_sha256=preview['expected_sha256'])
    assert result['written'] and result['valid'], result
    assert source.read_bytes() == before[source.relative_to(root).as_posix()]
    assert not (root / 'docs/knowledge/approved').exists()


@pytest.mark.parametrize('changed', ['policy', 'source'])
def test_proposal_rejects_change_after_preview_validation(api, root, definition, monkeypatch, changed):
    setup(api, root, definition)
    source = add_document(root)
    preview = api.check_category(root, 'meetings')
    original_read = api._read
    fired = False

    def racing_read(project, relative, *args, **kwargs):
        nonlocal fired
        if '/pending/' in relative and not fired:
            fired = True
            service = api._load('knowledge-curation.py')
            with service._locked(root):
                if changed == 'source':
                    source.write_text(DOCUMENT + '\nChanged source.\n', encoding='utf-8')
                else:
                    path = root / api.TAXONOMY
                    data = json.loads(path.read_text(encoding='utf-8'))
                    data['categories'][-1]['required_sections'].append('New requirement')
                    path.write_text(json.dumps(data), encoding='utf-8')
        return original_read(project, relative, *args, **kwargs)

    monkeypatch.setattr(api, '_read', racing_read)
    result = api.check_category(root, 'meetings', propose=True, expected_sha256=preview['expected_sha256'])
    assert fired
    assert not result.get('valid', False), result
    assert not list((root / 'docs/knowledge/candidates/pending').glob('*.md'))


def test_configuration_rejects_serialized_taxonomy_over_read_budget(api, root, definition):
    path = root / api.TAXONOMY
    config = json.loads(path.read_text())
    config['backends']['kwipu']['config']['preferences'] = {str(i): 'x' for i in range(14000)}
    path.write_text(json.dumps(config, separators=(',', ':')), encoding='utf-8')
    before = tree(root)
    assert path.stat().st_size < api.MAX_DOCUMENT
    result = api.configure(root, definition)
    assert result['status'] == 'taxonomy_budget', result
    assert tree(root) == before


def test_B2_proposals_work_when_valid_taxonomy_omits_id_prefix(api, root, definition):
    path = root / api.TAXONOMY
    config = json.loads(path.read_text())
    del config['id_prefix']
    path.write_text(json.dumps(config), encoding='utf-8')
    setup(api, root, definition)
    # Omission is valid independently of the configuration helper.
    config = json.loads(path.read_text())
    config.pop('id_prefix', None)
    path.write_text(json.dumps(config), encoding='utf-8')
    add_document(root)
    preview = api.check_category(root, 'meetings')
    assert preview['valid'], preview
    result = api.check_category(root, 'meetings', propose=True, expected_sha256=preview['expected_sha256'])
    assert result['valid'] and result['written'], result


@pytest.mark.parametrize('backend_name,group', [('graphiti', None), ('other-memory', None),
                                              ('other-memory', 'explicit-group')])
def test_B2_policy_snapshot_supports_all_graphiti_defaults_without_config_writes(api, root, definition, backend_name, group):
    setup(api, root, definition)
    path = root / api.TAXONOMY
    config = json.loads(path.read_text())
    default = api._load('knowledge-schema.py').default_taxonomy()
    backend = copy.deepcopy(next(b for b in default['backends'].values() if b['type'] == 'graphiti'))
    backend['enabled'] = False
    backend['config'].pop('group_id', None)
    if group is not None:
        backend['config']['group_id'] = group
    config['backends'][backend_name] = backend
    config.pop('id_prefix', None)
    path.write_text(json.dumps(config), encoding='utf-8')
    original = path.read_bytes()
    add_document(root)
    preview = api.check_category(root, 'meetings')
    assert preview['valid'], preview
    result = api.check_category(root, 'meetings', propose=True, expected_sha256=preview['expected_sha256'])
    assert result['valid'] and result['written'], result
    assert path.read_bytes() == original


def test_D2_proposals_reuse_the_original_policy_bytes_snapshot(api, root, definition, monkeypatch):
    setup(api, root, definition)
    add_document(root)
    second = root / 'docs/meetings/second.md'
    second.write_text(DOCUMENT, encoding='utf-8')
    digest = hashlib.sha256((root / api.TAXONOMY).read_bytes()).hexdigest()
    service = api._load('knowledge-curation.py')
    original = service.propose
    snapshots = []

    def recording_propose(*args, **kwargs):
        assert kwargs['expected_policy_sha256'] == digest
        snapshots.append(kwargs['expected_policy_sha256'])
        return original(*args, **kwargs)

    monkeypatch.setattr(service, 'propose', recording_propose)
    preview = api.check_category(root, 'meetings')
    result = api.check_category(root, 'meetings', propose=True, expected_sha256=preview['expected_sha256'])
    assert result['valid'] and result['written'] and snapshots == [digest, digest], result


def test_explicit_absent_policy_snapshot_cannot_accept_an_existing_file(api, root):
    service = api._load('knowledge-curation.py')
    path = root / api.TAXONOMY
    original_sha = hashlib.sha256(path.read_bytes()).hexdigest()
    result, code = service.propose(root, 'absent.md', DOCUMENT, producer='human', expected_policy_sha256=None)
    assert code and result['status'] == 'changed_policy'
    path.unlink()  # Only this synthetic project's configuration file.
    result, code = service.propose(root, 'missing.md', DOCUMENT, producer='human', expected_policy_sha256=original_sha)
    assert code and result['status'] == 'changed_policy'
    result, code = service.propose(root, 'absent.md', DOCUMENT, producer='human', expected_policy_sha256=None)
    assert code == 0 and result['status'] == 'proposed', result


@pytest.mark.parametrize('operation,args,expected', [
    ('template', ['--category', 'meetings'], 'ok'),
    ('check', ['--category', 'meetings'], 'checked'),
    ('configure', [], 'preview'),
])
def test_cli_dispatch_returns_json_without_mutating_inputs(api, root, definition, monkeypatch, capsys, operation, args, expected):
    setup(api, root, definition)
    add_document(root)
    before = tree(root)
    monkeypatch.setattr(sys, 'stdin', SimpleNamespace(buffer=io.BytesIO(json.dumps(definition).encode())))
    code = api.main([operation, '--root', str(root), *args])
    result = json.loads(capsys.readouterr().out)
    assert code == 0 and result['status'] == expected, result
    assert tree(root) == before


@pytest.mark.parametrize('budget,limit', [('MAX_FILES', 0), ('MAX_TOTAL', 1), ('MAX_DEPTH', 0)])
def test_exhausted_inventory_budget_blocks_proposals(api, root, definition, monkeypatch, budget, limit):
    setup(api, root, definition)
    source = add_document(root)
    if budget == 'MAX_DEPTH':
        nested = source.parent / 'nested'
        nested.mkdir()
        source.rename(nested / source.name)
    monkeypatch.setattr(api, budget, limit)
    result = api.check_category(root, 'meetings')
    assert not result['complete'] and result['issues'], result
    result = api.check_category(root, 'meetings', propose=True, expected_sha256=result['expected_sha256'])
    assert result['status'] == 'incomplete_inventory' and not result['written']


def test_invalid_operations_fail_without_creating_files(api, root, definition):
    before = tree(root)
    assert api.configure(root, definition, apply=True)['status'] == 'expected_sha256_required'
    assert api.configure(root, {})['status'] == 'invalid_request'
    assert api.read_template(root, 'unknown')['status'] == 'category_not_found'
    assert api.read_template(root, 'DECISION')['status'] == 'template_not_configured'
    assert api.check_category(root, 'DECISION')['status'] == 'inbox_not_configured'
    assert api.check_category(root, 'DECISION', origin='robot')['status'] == 'invalid_origin'
    assert api.check_category(root, 'DECISION', propose=True)['status'] == 'expected_sha256_required'
    assert tree(root) == before


def test_preview_is_read_only_and_configuration_preserves_other_preferences(api, root, definition):
    before = tree(root)
    snapshot = copy.deepcopy(definition)
    preview = api.configure(root, definition)
    assert preview['status'] == 'preview' and tree(root) == before
    assert definition == snapshot
    result = api.configure(root, definition, apply=True, expected_sha256=preview['expected_sha256'])
    assert result['status'] == 'configured', result
    after = json.loads((root / '.claude/knowledge-services/taxonomy.json').read_text(encoding='utf-8'))
    original = json.loads(before['.claude/knowledge-services/taxonomy.json'])
    assert after['categories'][:-1] == original['categories']
    assert after['backends'] == original['backends']
    assert after['categories'][-1]['routing'] == {}
    assert (root / definition['category']['template']).read_text(encoding='utf-8') == TEMPLATE
    assert api.read_template(root, 'meetings')['text'] == TEMPLATE


def test_apply_rejects_stale_preview_without_creating_template(api, root, definition):
    preview = api.configure(root, definition)
    p = root / '.claude/knowledge-services/taxonomy.json'
    p.write_text(p.read_text(encoding='utf-8') + '\n', encoding='utf-8')
    before = tree(root)
    result = api.configure(root, definition, apply=True, expected_sha256=preview['expected_sha256'])
    assert result['status'] == 'changed_inputs' and tree(root) == before, result


def test_apply_requires_preview_token(api, root, definition):
    before = tree(root)
    result = api.configure(root, definition, apply=True)
    assert result['status'] == 'expected_sha256_required' and tree(root) == before


def test_foreign_template_is_never_overwritten(api, root, definition):
    p = root / definition['category']['template']
    p.parent.mkdir(parents=True)
    p.write_text('Owned by the project.', encoding='utf-8')
    before = tree(root)
    result = api.configure(root, definition)
    assert result['status'] == 'template_exists' and tree(root) == before


@pytest.mark.parametrize('key,path', [('template', '../outside.md'), ('template', '.claude/settings.json'),
                                     ('template', '/tmp/external.md'), ('inbox', '../outside')])
def test_unsafe_paths_are_rejected_before_writes(api, root, definition, key, path):
    definition['category'][key] = path
    before = tree(root)
    assert api.configure(root, definition)['status'] == 'invalid_taxonomy'
    assert tree(root) == before


def test_template_directory_symlink_cannot_escape_project(api, root, definition, tmp_path):
    external = tmp_path.parent / (tmp_path.name + '-outside')
    external.mkdir()
    try:
        (root / 'config').symlink_to(external, target_is_directory=True)
    except OSError:
        pytest.skip('symlink privilege unavailable')
    result = api.configure(root, definition)
    assert result['status'] == 'unsafe_template', result
    assert list(external.iterdir()) == []


def test_read_template_reports_missing_and_oversized_files(api, root, definition):
    setup(api, root, definition)
    p = root / definition['category']['template']
    p.unlink()
    assert api.read_template(root, 'meetings')['status'] == 'template_not_found'
    p.write_bytes(b'x' * 65537)
    assert api.read_template(root, 'meetings')['status'] == 'template_too_large'


def test_check_is_read_only_and_human_origin_is_assigned_by_flow(api, root, definition):
    setup(api, root, definition)
    add_document(root)
    before = tree(root)
    report = api.check_category(root, 'meetings')
    assert report['status'] == 'checked' and report['complete'] is True, report
    assert report['files'][0]['state'] == 'valid'
    assert report['origin'] == 'human' and tree(root) == before
    assert api.check_category(root, 'meetings', origin='agent')['files'][0]['state'] == 'invalid'


def test_missing_sections_are_reported_without_changes(api, root, definition):
    setup(api, root, definition)
    add_document(root, DOCUMENT.replace('## Acuerdos\nConservar el procedimiento.\n', ''))
    before = tree(root)
    report = api.check_category(root, 'meetings')
    assert report['files'][0]['state'] == 'invalid'
    assert any(e['campo'] == 'required_sections' for e in report['files'][0]['errors'])
    assert tree(root) == before


def test_propose_uses_existing_curation_service_preserves_source_and_never_approves(api, root, definition):
    setup(api, root, definition)
    original = add_document(root)
    raw = original.read_bytes()
    preview = api.check_category(root, 'meetings')
    result = api.check_category(root, 'meetings', propose=True, expected_sha256=preview['expected_sha256'])
    assert result['status'] == 'proposed', result
    row = result['files'][0]
    candidate = root / row['candidate']
    assert candidate.is_file() and original.read_bytes() == raw
    text = candidate.read_text(encoding='utf-8')
    assert 'content_origin: human' in text and 'source_sha256: ' + hashlib.sha256(raw).hexdigest() in text
    assert 'estado:' not in text
    assert not (root / 'docs/knowledge/approved').exists()


def test_stale_check_does_not_propose_changed_sources(api, root, definition):
    setup(api, root, definition)
    p = add_document(root)
    preview = api.check_category(root, 'meetings')
    p.write_bytes(p.read_bytes() + b'\nChanged.\n')
    before = tree(root)
    result = api.check_category(root, 'meetings', propose=True, expected_sha256=preview['expected_sha256'])
    assert result['status'] == 'changed_inputs' and tree(root) == before


def test_incomplete_inventory_is_not_authorized_for_proposal(api, root, definition, monkeypatch):
    setup(api, root, definition)
    add_document(root)
    monkeypatch.setattr(api, 'MAX_FILES', 1)
    add_document(root).with_name('other.md').write_text(DOCUMENT, encoding='utf-8')
    report = api.check_category(root, 'meetings')
    assert report['complete'] is False
    before = tree(root)
    result = api.check_category(root, 'meetings', propose=True, expected_sha256=report['expected_sha256'])
    assert result['status'] == 'incomplete_inventory' and tree(root) == before


def test_partial_configuration_can_resume_without_overwriting_template(api, root, definition, monkeypatch):
    preview = api.configure(root, definition)
    original = api._replace_taxonomy
    def fail(*args):
        raise OSError('synthetic interruption')
    monkeypatch.setattr(api, '_replace_taxonomy', fail)
    failed = api.configure(root, definition, apply=True, expected_sha256=preview['expected_sha256'])
    assert failed['status'] == 'partial' and failed['template_created'] is True
    monkeypatch.setattr(api, '_replace_taxonomy', original)
    resumed = api.configure(root, definition)
    result = api.configure(root, definition, apply=True, expected_sha256=resumed['expected_sha256'])
    assert result['status'] == 'configured' and result['template_created'] is False


def test_backup_is_exact_and_excluded_from_git_by_owned_directory(api, root, definition):
    old = (root / '.claude/knowledge-services/taxonomy.json').read_bytes()
    setup(api, root, definition)
    folder = root / '.claude/knowledge-services/.category-backups'
    backups = list(folder.glob('*.json'))
    assert len(backups) == 1 and backups[0].read_bytes() == old
    assert (folder / '.gitignore').read_text(encoding='utf-8') == '*\n'


def test_repeated_proposal_reports_existing_candidate_without_duplicate(api, root, definition):
    setup(api, root, definition)
    add_document(root)
    preview = api.check_category(root, 'meetings')
    first = api.check_category(root, 'meetings', propose=True, expected_sha256=preview['expected_sha256'])
    assert first['files'][0]['state'] == 'proposed'
    candidate = first['files'][0]['candidate']
    before = tree(root)
    second = api.check_category(root, 'meetings', propose=True, expected_sha256=preview['expected_sha256'])
    assert second['files'][0]['state'] == 'already_proposed', second
    assert second['files'][0]['candidate'] == candidate and tree(root) == before


def test_cli_check_emits_valid_json_and_keeps_sources_unchanged(api, root, definition):
    setup(api, root, definition)
    add_document(root)
    before = tree(root)
    result = subprocess.run([sys.executable, str(PATH), 'check', '--root', str(root), '--category', 'meetings'],
                            capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=10)
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report['status'] == 'checked' and len(report['expected_sha256']) == 64
    assert tree(root) == before


def test_template_contract_mismatch_is_read_only(api, root, definition):
    definition['template_text'] = TEMPLATE.replace('## Acuerdos\n', '')
    before = tree(root)
    assert api.configure(root, definition)['status'] == 'template_contract_mismatch'
    assert tree(root) == before


def test_configuration_is_idempotent(api, root, definition):
    setup(api, root, definition)
    before = tree(root)
    setup(api, root, definition)
    assert tree(root) == before


def test_cr_only_document_preserves_raw_binding(api, root, definition):
    setup(api, root, definition)
    path = add_document(root, DOCUMENT.replace('\n', '\r'))
    report = api.check_category(root, 'meetings')
    assert report['files'][0]['state'] == 'valid', report
    assert report['files'][0]['sha256'] == hashlib.sha256(path.read_bytes()).hexdigest()


def test_installed_bundle_cannot_be_used_to_store_project_templates(api, root, definition, monkeypatch):
    bundle = root / 'installed-bundle'
    (bundle / '.codex-plugin').mkdir(parents=True)
    (bundle / '.codex-plugin/plugin.json').write_text('{}', encoding='utf-8')
    monkeypatch.setattr(api, 'BUNDLE_ROOT', bundle, raising=False)
    definition['category']['template'] = 'installed-bundle/meeting.md'
    before = tree(root)
    assert api.configure(root, definition)['status'] == 'template_in_plugin'
    assert tree(root) == before


def test_shared_writer_failure_is_reported_as_partial(api, root, definition, monkeypatch):
    preview = api.configure(root, definition)
    def fail(*args):
        raise api._load('knowledge-curation.py')._Failure('changed_publication', 2)
    monkeypatch.setattr(api, '_replace_taxonomy', fail)
    result = api.configure(root, definition, apply=True, expected_sha256=preview['expected_sha256'])
    assert result['status'] == 'partial' and result['issue'] == 'changed_publication'


def test_partial_portable_installation_returns_json_without_traceback(tmp_path):
    import shutil
    isolated = tmp_path / 'skills/knowledge-category-template/scripts/category-template.py'
    isolated.parent.mkdir(parents=True)
    shutil.copyfile(PATH, isolated)
    result = subprocess.run([sys.executable, str(isolated), 'template', '--root', str(tmp_path), '--category', 'meetings'],
                            capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=10)
    assert result.returncode != 0
    data = json.loads(result.stdout)
    assert data['complete'] is False and 'Traceback' not in result.stderr
