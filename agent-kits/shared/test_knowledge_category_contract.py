"""Project category contracts: format and declared provenance, never identity proof."""
import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).parent


def test_large_heading_whitespace_has_bounded_processing_time():
    code = ("import importlib.util; "
            "s=importlib.util.spec_from_file_location('rules', 'agent-kits/shared/knowledge-curation-rules.py'); "
            "m=importlib.util.module_from_spec(s); s.loader.exec_module(m); "
            "assert m._section_content('## Objective'+' '*64000+'x\\nBody.\\n')")
    subprocess.run([sys.executable, '-c', code], cwd=HERE.parents[1],
                   check=True, timeout=8, capture_output=True)


def load(name):
    spec = importlib.util.spec_from_file_location('category_test_' + name.replace('-', '_'), HERE / name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def category(**values):
    return dict(key='meetings', folder='meetings', min_evidence='single_case',
                allowed_producers=['human'], required_metadata=['fecha', 'participantes'],
                required_sections=['Objetivo', 'Acuerdos'], **values)


def config(cat=None):
    return {'version': 1, 'id_prefix': 'owned', 'categories': [cat or category()]}


def metadata(**values):
    result = {'category': 'meetings', 'evidencia': 'single_case',
              'fuentes': ['docs/meeting-source.md'], 'tags': ['area:operations'],
              'content_origin': 'human', 'fecha': '2026-11-03', 'participantes': ['Equipo']}
    result.update(values)
    return result


BODY = '# Acta\n\n## Objetivo\nRevisar el despliegue.\n\n## Acuerdos\nConservar el procedimiento vigente.\n'


def errors(fm=None, body=BODY, cat=None):
    rules = load('knowledge-curation-rules.py')
    cat = cat or category()
    return rules.validar_aprobacion(fm or metadata(), body, cat, config(cat), 'candidate.md',
                                    ['observation', 'single_case'], 'taxonomy.json')


@pytest.mark.parametrize('key,value', [
    ('allowed_producers', []), ('allowed_producers', 'human'),
    ('allowed_producers', ['robot']), ('allowed_producers', ['human', 'human']),
    ('required_metadata', ['']), ('required_metadata', ['fecha', 'fecha']),
    ('required_metadata', 'fecha'), ('required_metadata', ['nested.field']),
    ('required_sections', ['']), ('required_sections', ['Objetivo', 'Objetivo']),
    ('required_sections', ['## Objetivo']), ('required_sections', ['a\nb']),
    ('template', '../outside.md'), ('template', '/outside.md'),
    ('template', 'C:/outside.md'), ('template', 'config/template.json'),
    ('template', 'config./template.md'), ('template', 'config /template.md'),
    ('template', 'config/CON.md'), ('template', 'config/NUL/template.md'),
    ('inbox', '../private'), ('inbox', 'docs/knowledge/approved/meetings'),
    ('inbox', 'docs/knowledge/candidates/pending'), ('inbox', '.git'),
])
def test_taxonomy_rejects_invalid_category_contract(key, value):
    cat = category()
    cat[key] = value
    result = load('knowledge-taxonomy-local.py').validar(config(cat))
    assert any(key in item['campo'] for item in result), result


def test_taxonomy_accepts_optional_project_contract_and_legacy_category():
    module = load('knowledge-taxonomy-local.py')
    cat = category(template='config/knowledge-templates/meeting.md', inbox='docs/meetings')
    assert module.validar(config(cat)) == []
    legacy = {'key': 'DECISION', 'folder': 'adr', 'min_evidence': 'single_case'}
    assert module.validar(config(legacy)) == []


@pytest.mark.parametrize('field,value', [('fecha', ''), ('participantes', []), ('participantes', [' '])])
def test_required_metadata_cannot_be_empty(field, value):
    assert any(item['campo'] == field for item in errors(metadata(**{field: value})))


def test_missing_required_metadata_is_reported():
    fm = metadata()
    del fm['fecha']
    assert any(item['campo'] == 'fecha' for item in errors(fm))


@pytest.mark.parametrize('body', [
    '# Acta\n\n## Objetivo\nAlgo.\n',
    '# Acta\n\n## Objetivo\nAlgo.\n\n## Acuerdos\n\n',
    '# Acta\n\n## Objetivo\nAlgo.\n\n```markdown\n## Acuerdos\nSolo un ejemplo.\n```\n',
    '# Acta\n\n## Objetivo\nAlgo.\n\n    ## Acuerdos\n    Codigo indentado.\n',
    '# Acta\n\n## Objetivo\nAlgo.\n\n## Acuerdos\n<!-- sin completar -->\n',
    '# Acta\n\n## Objetivo\nAlgo.\n\n<!--\n## Acuerdos\nOculto.\n',
])
def test_required_section_must_have_real_content_outside_code(body):
    assert any(item['campo'] == 'required_sections' for item in errors(body=body))


def test_human_category_rejects_agent_and_missing_origin():
    assert any(item['campo'] == 'content_origin' for item in errors(metadata(content_origin='agent')))
    fm = metadata()
    del fm['content_origin']
    assert any(item['campo'] == 'content_origin' for item in errors(fm))


def test_contract_allows_declared_human_and_does_not_mutate_input():
    fm = metadata()
    before = copy.deepcopy(fm)
    assert errors(fm) == []
    assert fm == before


def test_legacy_category_does_not_require_new_metadata():
    cat = {'key': 'meetings', 'folder': 'meetings', 'min_evidence': 'single_case'}
    fm = {k: v for k, v in metadata().items() if k not in ('content_origin', 'fecha', 'participantes')}
    assert errors(fm, body='Plain approved knowledge.', cat=cat) == []


def project(tmp_path, cat=None):
    folder = tmp_path / '.claude/knowledge-services'
    folder.mkdir(parents=True)
    (folder / 'taxonomy.json').write_text(json.dumps(config(cat)), encoding='utf-8')
    return tmp_path


def candidate(origin=None, body=BODY):
    fm = metadata()
    fm.pop('content_origin')
    if origin:
        fm['content_origin'] = origin
    # Render with the existing service, rather than another fixture YAML writer.
    return load('knowledge-curation.py')._render(fm, body)


def test_propose_enforces_declared_producer_policy_before_writing(tmp_path):
    root = project(tmp_path)
    service = load('knowledge-curation.py')
    result, code = service.propose(str(root), 'meeting.md', candidate(), producer='documenter')
    assert code == 1 and result['status'] == 'producer_not_allowed', result
    assert not (root / 'docs/knowledge/candidates/pending/meeting.md').exists()


def test_human_import_is_labelled_and_approval_cannot_rewrite_origin(tmp_path):
    cat = category()
    cat['allowed_producers'] = ['human', 'agent']
    root = project(tmp_path, cat)
    service = load('knowledge-curation.py')
    result, code = service.propose(str(root), 'meeting.md', candidate('human'), producer='human')
    assert code == 0, result
    original = (root / result['ruta']).read_bytes()
    assert b'content_origin: human' in original
    applied, code = service.apply_decision(str(root), result['ruta'], 'approve',
        expected_sha256=result['sha256'], reason='Fuentes examinadas.', decider='knowledge-curator',
        metadata={'id': 'owned.meeting.one', 'content_origin': 'agent'})
    assert code != 0 and applied['status'] == 'changed_content_origin', applied
    assert (root / result['ruta']).read_bytes() == original


def test_approval_enforces_contract_using_existing_persistence_owner(tmp_path):
    root = project(tmp_path)
    service = load('knowledge-curation.py')
    proposed, code = service.propose(str(root), 'meeting.md', candidate('human', '# Incomplete\n'), producer='human')
    assert code == 0, proposed
    applied, code = service.apply_decision(str(root), proposed['ruta'], 'approve',
        expected_sha256=proposed['sha256'], reason='Revision.', decider='knowledge-curator',
        metadata={'id': 'owned.meeting.one'})
    assert code == 1 and applied['status'] == 'approval_validation_failed', applied
    assert not (root / 'docs/knowledge/approved/meetings/meeting.md').exists()


def test_approval_cannot_change_submitting_producer(tmp_path):
    root = project(tmp_path)
    service = load('knowledge-curation.py')
    result, code = service.propose(str(root), 'meeting.md', candidate('human'), producer='human')
    assert code == 0
    applied, code = service.apply_decision(str(root), result['ruta'], 'approve',
        expected_sha256=result['sha256'], reason='Revision.', decider='knowledge-curator',
        metadata={'id': 'owned.meeting.one', 'proposed_by': 'documenter'})
    assert code != 0 and applied['status'] == 'changed_proposed_by'


def test_proposal_rechecks_policy_under_existing_cooperative_lock(tmp_path, monkeypatch):
    from contextlib import contextmanager
    root = project(tmp_path)
    service = load('knowledge-curation.py')
    @contextmanager
    def changed_policy(_):
        path = root / '.claude/knowledge-services/taxonomy.json'
        policy = json.loads(path.read_text(encoding='utf-8'))
        policy['categories'][0]['allowed_producers'] = ['agent']
        path.write_text(json.dumps(policy), encoding='utf-8')
        yield
    monkeypatch.setattr(service, '_locked', changed_policy)
    result, code = service.propose(str(root), 'meeting.md', candidate('human'), producer='human')
    assert code != 0 and result['status'] == 'changed_policy'
    assert not (root / 'docs/knowledge/candidates/pending/meeting.md').exists()
