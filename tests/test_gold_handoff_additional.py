"""Gold remains a proposal; partial services and invalid receipts fail closed."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
from types import SimpleNamespace

import pytest

SOURCE = Path(os.environ.get('MEMORY_COVERAGE_SOURCE', Path(__file__).resolve().parents[1]))
SHARED = SOURCE / 'agent-kits/shared'


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def bridge():
    return load(SOURCE / 'skills/training-data-services/scripts/propose-from-case.py', 'gold_handoff_additional')


@pytest.fixture
def gold(bridge, tmp_path):
    root = tmp_path / 'project'
    config = {'version': 1, 'enabled': True, 'root': '../store', 'id_prefix': 'geo', 'bridge_to_curator': True}
    config_path = root / '.claude/knowledge-services/training.json'
    config_path.parent.mkdir(parents=True)
    config_path.write_text(json.dumps(config), encoding='utf-8')
    case = {'family': 'ramp', 'variant': 'steep', 'request': 'Bounded reproducible example.',
            'trajectory': [{'role': 'user', 'content': 'PRIVATE-TRAJECTORY'}], 'outcome': 'failure'}
    recorded = bridge.rec.grabar(case, dict(config, bridge_to_curator=False), str(root))
    bridge.rec.cambiar_estado(recorded['case_id'], recorded['version'], 'approved', config, str(root),
                             approved_by_human=True, reviewer_note='Reproduction confirmed.')
    return root, config, recorded['case_id']


def tree(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*') if p.is_file()}


@pytest.mark.parametrize('kind', ['syntax_error', 'non_callable', 'missing'])
def test_cli_partial_curation_bundle_never_uses_direct_writer(bridge, gold, tmp_path, monkeypatch, capsys, kind):
    root, _, identifier = gold
    partial = tmp_path / 'partial-shared'
    partial.mkdir()
    for filename in ('knowledge-schema.py', 'knowledge-taxonomy-local.py'):
        shutil.copyfile(SHARED / filename, partial / filename)
    if kind == 'syntax_error':
        (partial / 'knowledge-curation.py').write_text('def propose(:\n', encoding='utf-8')
    elif kind == 'non_callable':
        (partial / 'knowledge-curation.py').write_text('propose = None\n', encoding='utf-8')
    monkeypatch.setattr(bridge, '_dirs_shared', lambda: [str(partial)])
    before_project, before_store = tree(root), tree(root.parent / 'store')
    assert bridge.main([identifier, '1', '--category', 'GOTCHA', '--project-root', str(root)]) == 2
    output = capsys.readouterr()
    assert 'knowledge-curation.py' in output.err and 'Traceback' not in output.err
    assert not (root / 'docs').exists()
    assert tree(root) == before_project and tree(root.parent / 'store') == before_store


@pytest.mark.parametrize('defect', ['wrong_path', 'missing_hash', 'bad_hash', 'non_string_hash'])
def test_unconfirmed_service_handoff_never_becomes_success_or_raw_fallback(bridge, gold, monkeypatch, capsys, defect):
    root, _, identifier = gold
    reference = identifier + '@v001'
    expected = 'docs/knowledge/candidates/pending/' + bridge._nombre_candidato(reference)
    response = {'status': 'proposed', 'ruta': expected, 'sha256': 'a' * 64, 'errores': [], 'avisos': []}
    if defect == 'wrong_path':
        response['ruta'] = 'docs/knowledge/approved/forged.md'
    elif defect == 'missing_hash':
        del response['sha256']
    elif defect == 'bad_hash':
        response['sha256'] = 'not-a-sha256'
    else:
        response['sha256'] = 42
    calls = []

    def unconfirmed(*args, **kwargs):
        calls.append((args, kwargs))
        return response, 0

    monkeypatch.setattr(bridge, '_servicio_curacion', lambda: SimpleNamespace(propose=unconfirmed))
    before_project, before_store = tree(root), tree(root.parent / 'store')
    assert bridge.main([identifier, 'v001', '--category', 'GOTCHA', '--project-root', str(root)]) == 2
    output = capsys.readouterr()
    assert 'no confirma' in output.err and 'OK candidato' not in output.out
    assert len(calls) == 1 and tree(root) == before_project and tree(root.parent / 'store') == before_store
    assert not (root / 'docs').exists()


def test_real_gold_cli_preserves_taxonomy_and_store_and_redacts_service_warnings(bridge, gold, monkeypatch, capsys):
    root, _, identifier = gold
    taxonomy = root / '.claude/knowledge-services/taxonomy.json'
    taxonomy.write_text(json.dumps({'version': 1, 'categories': [
        {'key': 'RECETA', 'folder': 'recipes', 'min_evidence': 'validated_case'}]}), encoding='utf-8')
    service = bridge._servicio_curacion()
    real_propose = service.propose
    secret = 'ghp_a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6q7R8s9T0'
    calls = []

    def propose_with_warning(*args, **kwargs):
        result, code = real_propose(*args, **kwargs)
        calls.append((result.copy(), code))
        result['avisos'] = [{'mensaje': 'Provider note\n' + secret}, 'Legacy warning', {'mensaje': ''}]
        return result, code

    monkeypatch.setattr(service, 'propose', propose_with_warning)
    monkeypatch.setattr(bridge, '_servicio_curacion', lambda: service)
    before_store, before_policy = tree(root.parent / 'store'), taxonomy.read_bytes()
    assert bridge.main([identifier, 'v001', '--category', 'RECETA', '--project-root', str(root)]) == 0
    output = capsys.readouterr()
    assert len(calls) == 1 and calls[0][1] == 0
    pending = root / calls[0][0]['ruta']
    assert calls[0][0]['sha256'] in output.out
    assert secret not in output.out + output.err + pending.read_text(encoding='utf-8')
    assert 'aviso:' in output.err and 'redactado' in output.err and 'Legacy warning' in output.err
    assert 'category: RECETA' in pending.read_text(encoding='utf-8')
    assert b'PRIVATE-TRAJECTORY' not in pending.read_bytes() and b'estado:' not in pending.read_bytes()
    assert not (root / 'docs/knowledge/approved').exists()
    assert tree(root.parent / 'store') == before_store and taxonomy.read_bytes() == before_policy


@pytest.mark.parametrize('value', ['{ truncated', '{"version":1,"categories":[]}'])
def test_gold_cli_invalid_project_taxonomy_cannot_fall_back_to_default_category(bridge, gold, capsys, value):
    root, _, identifier = gold
    taxonomy = root / '.claude/knowledge-services/taxonomy.json'
    taxonomy.write_text(value, encoding='utf-8')
    before_project, before_store = tree(root), tree(root.parent / 'store')
    assert bridge.main([identifier, '1', '--category', 'GOTCHA', '--project-root', str(root)]) == 2
    output = capsys.readouterr()
    assert 'taxonomia' in output.err and 'Traceback' not in output.err
    assert tree(root) == before_project and tree(root.parent / 'store') == before_store
    assert not (root / 'docs').exists()


def test_gold_cli_shared_io_failure_is_pending_and_preserves_store(bridge, gold, monkeypatch, capsys):
    root, _, identifier = gold
    service = bridge._servicio_curacion()

    def fail(*args, **kwargs):
        raise OSError('fixture shared IO unavailable')

    monkeypatch.setattr(service, 'propose', fail)
    monkeypatch.setattr(bridge, '_servicio_curacion', lambda: service)
    before_project, before_store = tree(root), tree(root.parent / 'store')
    assert bridge.main([identifier, '1', '--category', 'GOTCHA', '--project-root', str(root)]) == 2
    output = capsys.readouterr()
    assert 'E/S' in output.err and 'Traceback' not in output.err and not output.out
    assert tree(root) == before_project and tree(root.parent / 'store') == before_store
    assert not (root / 'docs').exists()
