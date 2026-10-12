import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

SHARED = Path(__file__).resolve().parents[1] / 'agent-kits/shared'
CANDIDATE = 'docs/knowledge/candidates/pending/example.md'
TEXT = '---\ncategory: GOTCHA\nevidencia: validated_case\nfuentes: [docs/reproduction.md]\ntags: [area:testing]\n---\n# Evidence\nConcrete reproducible observation.\n'
META = {'id': 'ca.gotcha.test', 'category': 'GOTCHA', 'version': 1, 'estado': 'aprobado'}


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, SHARED / filename)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


@pytest.fixture
def service():
    return load('resume_test_service', 'knowledge-curation.py')


@pytest.fixture
def project(tmp_path, service):
    root = tmp_path / 'project'
    policy = root / '.claude/knowledge-services/taxonomy.json'
    policy.parent.mkdir(parents=True)
    policy.write_text(json.dumps({'version': 1, 'id_prefix': 'ca', 'categories': [
        {'key': 'GOTCHA', 'folder': 'gotchas', 'min_evidence': 'validated_case'}]}), encoding='utf-8')
    result, code = service.propose(root, 'example.md', TEXT, producer='documenter')
    assert code == 0
    return root, result['sha256']


def snapshot(root):
    return {p.relative_to(root).as_posix(): (p.read_bytes(), p.stat().st_mtime_ns)
            for p in root.rglob('*') if p.is_file()}


def write_ledger(root, digest, *, operation=None):
    path = root / 'docs/roadmap/2026-10-10-demo/tasks.md'
    path.parent.mkdir(parents=True, exist_ok=True)
    reference = {'candidate': CANDIDATE, 'sha256': digest}
    if operation:
        reference['operation_id'] = operation
    path.write_text('---\nestado: en-progreso\n---\n## Fase 1 — Work\n### T-01 — Continue\n'
                    '- **Estado**: en-progreso\n\n```curation-refs-v1\n' + json.dumps([reference]) + '\n```\n', encoding='utf-8')
    return path


def test_pending_reference_is_observed_without_mutation(service, project):
    root, digest = project
    before = snapshot(root)
    result = service.inspect_reference(root, CANDIDATE, digest)
    assert result['status'] == 'pending'
    assert result['candidate'] == CANDIDATE and result['expected_sha256'] == digest
    assert snapshot(root) == before


@pytest.mark.parametrize('stage', ['prepared', 'published', 'source_removed'])
def test_interrupted_operation_visible_and_explicit_recovery_receipt(service, project, monkeypatch, stage):
    root, digest = project
    prepared = []
    def interrupt(at, operation):
        if at == stage:
            prepared.append(operation['operation_id'])
            raise OSError('OWN interruption')
    monkeypatch.setattr(service, '_checkpoint', interrupt)
    response, code = service.apply_decision(root, CANDIDATE, 'approve', expected_sha256=digest,
        metadata=META, reason='Fixture independently reviewed.')
    assert code == 2 and response['operation_id'] == prepared[0]
    before = snapshot(root)
    view = service.inspect_reference(root, CANDIDATE, digest)
    assert view['status'] == 'pending' and view['operation_id'] == prepared[0]
    assert view['recovery_pending'] is True and snapshot(root) == before
    monkeypatch.setattr(service, '_checkpoint', lambda *_: None)
    recovered, code = service.recover(root, prepared[0])
    assert code == 0
    before = snapshot(root)
    view = service.inspect_reference(root, CANDIDATE, digest)
    assert view['status'] == 'completed' and view['reason'] == 'completed_receipt_observed'
    receipt = root / view['receipt_path']
    assert view['receipt_sha256'] == hashlib.sha256(receipt.read_bytes()).hexdigest()
    assert view['target_sha256'] == recovered['sha256']
    assert view['target_content_verified'] is False and snapshot(root) == before


def test_inspection_is_readonly_even_when_operation_has_owned_staging(service, project, monkeypatch):
    root, digest = project
    def interrupt(stage, operation):
        if stage == 'prepared':
            raise OSError('stop')
    monkeypatch.setattr(service, '_checkpoint', interrupt)
    result, code = service.apply_decision(root, CANDIDATE, 'approve', expected_sha256=digest,
        metadata=META, reason='Examined.')
    assert code == 2
    operation_path = service._operation_directory(CANDIDATE) + '/' + result['operation_id'] + '.json'
    record = json.loads((root / operation_path).read_bytes())
    staged = root / record['record_publication']['staged']
    service.os.link(root / operation_path, staged)
    before = snapshot(root)
    def denied(*args, **kwargs):
        pytest.fail('inspection attempted a write/lock/recovery')
    for name in ('_locked', 'recover', 'apply_decision', '_complete'):
        monkeypatch.setattr(service, name, denied)
    monkeypatch.setattr(service.os, 'link', denied)
    real_open = service.os.open
    def readonly_open(path, flags, *args, **kwargs):
        assert flags & (service.os.O_CREAT | service.os.O_WRONLY | service.os.O_RDWR) == 0
        return real_open(path, flags, *args, **kwargs)
    monkeypatch.setattr(service.os, 'open', readonly_open)
    monkeypatch.setattr(Path, 'mkdir', denied)
    monkeypatch.setattr(Path, 'unlink', denied)
    result = service.inspect_reference(root, CANDIDATE, digest)
    assert result['status'] == 'pending' and staged.exists()
    assert snapshot(root) == before


@pytest.mark.parametrize('damage', ['partial_json', 'wrong_hash', 'wrong_status'])
def test_receipt_damage_never_claims_completed(service, project, monkeypatch, damage):
    root, digest = project
    result, code = service.apply_decision(root, CANDIDATE, 'approve', expected_sha256=digest,
        metadata=META, reason='Examined.')
    assert code == 0
    receipt = root / service.RECEIPTS / (result['operation_id'] + '.json')
    if damage == 'partial_json':
        receipt.write_bytes(b'{')
    else:
        payload = json.loads(receipt.read_bytes())
        payload['target_sha256' if damage == 'wrong_hash' else 'status'] = 'altered'
        receipt.write_text(json.dumps(payload), encoding='utf-8')
    before = snapshot(root)
    view = service.inspect_reference(root, CANDIDATE, digest)
    assert view['status'] in ('corrupt', 'unknown')
    assert snapshot(root) == before


def test_missing_explicit_id_never_uses_another_operation(service, project):
    root, digest = project
    result, code = service.apply_decision(root, CANDIDATE, 'approve', expected_sha256=digest,
        metadata=META, reason='Examined.')
    assert code == 0
    view = service.inspect_reference(root, CANDIDATE, digest, operation_id='0' * 64)
    assert view['status'] == 'missing' and 'operation_id' not in view


def test_changed_candidate_and_absence_are_distinct(service, project):
    root, digest = project
    (root / CANDIDATE).write_bytes(b'changed')
    assert service.inspect_reference(root, CANDIDATE, digest)['status'] == 'changed'
    (root / CANDIDATE).unlink()
    assert service.inspect_reference(root, CANDIDATE, digest)['status'] == 'missing'


def test_incomplete_bucket_is_unknown(service, project):
    root, digest = project
    directory = root / service._operation_directory(CANDIDATE)
    directory.mkdir(parents=True)
    for n in range(17):
        (directory / ('.curation-' + format(n, '032x') + '.tmp')).write_bytes(b'{}')
    view = service.inspect_reference(root, CANDIDATE, digest)
    assert view['status'] == 'unknown' and view['reason'] == 'incomplete'


@pytest.mark.parametrize('runtime', ['claude', 'codex', 'opencode'])
def test_resume_uses_explicit_ledger_reference_and_displays_exact_operation(service, project, monkeypatch, runtime):
    root, digest = project
    write_ledger(root, digest)
    other, code = service.propose(root, 'other.md', TEXT, producer='architect')
    assert code == 0
    def interrupt(stage, operation):
        if stage == 'prepared':
            raise OSError('No operation response received by owner')
    monkeypatch.setattr(service, '_checkpoint', interrupt)
    applied, code = service.apply_decision(root, CANDIDATE, 'approve', expected_sha256=digest,
        metadata=META, reason='Examined.')
    assert code == 2
    progress = load('resume_test_progress', 'progress-report.py')
    before = snapshot(root)
    result = progress.resume(root, initiative='2026-10-10-demo', runtime=runtime)
    assert result['curation']['status'] == 'ok'
    refs = result['curation']['references']
    assert len(refs) == 1 and refs[0]['operation_id'] == applied['operation_id']
    assert refs[0]['candidate'] == CANDIDATE and refs[0]['status'] == 'pending'
    output = progress.resume_text(result)
    assert applied['operation_id'] in output and 'other.md' not in output
    assert snapshot(root) == before
    monkeypatch.setattr(service, '_checkpoint', lambda *_: None)
    assert service.recover(root, applied['operation_id'])[1] == 0
    result = progress.resume(root, initiative='2026-10-10-demo', runtime=runtime)
    assert result['curation']['references'][0]['status'] == 'completed'
    assert result['curation']['references'][0]['receipt_sha256'] in progress.resume_text(result)


@pytest.mark.parametrize('damage', ['duplicate_block', 'partial_block', 'duplicate_key', 'extra_key', 'duplicate_reference', 'too_many'])
def test_bad_reference_block_is_not_silently_ignored_or_merged(service, project, damage):
    root, digest = project
    path = write_ledger(root, digest)
    text = path.read_text(encoding='utf-8')
    if damage == 'duplicate_block':
        text += text[text.index('```curation-refs-v1'):]
    elif damage == 'partial_block':
        text = text[:-4]
    elif damage == 'duplicate_key':
        text = text.replace('"sha256":', '"sha256":"' + digest + '","sha256":')
    else:
        reference = {'candidate': CANDIDATE, 'sha256': digest}
        if damage == 'extra_key':
            reference['status'] = 'approved'
        refs = [reference] * (9 if damage == 'too_many' else 2 if damage == 'duplicate_reference' else 1)
        text = text[:text.index('```curation-refs-v1')] + '```curation-refs-v1\n' + json.dumps(refs) + '\n```\n'
    path.write_text(text, encoding='utf-8')
    progress = load('bad_block_progress', 'progress-report.py')
    result = progress.resume(root, initiative='2026-10-10-demo')
    assert result['ledger'] is not None
    assert result['curation']['status'] == 'corrupt' and result['curation']['references'] == []


def test_legacy_ledger_does_not_infer_candidates_and_history_only_stays_separate(service, project, capsys):
    root, digest = project
    path = write_ledger(root, digest)
    path.write_text(path.read_text(encoding='utf-8').split('```curation-refs-v1')[0], encoding='utf-8')
    progress = load('legacy_progress', 'progress-report.py')
    result = progress.resume(root, initiative='2026-10-10-demo')
    assert result['curation'] == {'status': 'not_registered', 'references': []}
    assert progress.main(['resume', '--root', str(root), '--initiative', '2026-10-10-demo', '--history-only']) == 0
    assert capsys.readouterr().out == ''


def test_budget_and_identity_projection_cannot_manufacture_usable_reference(service, project):
    root, digest = project
    write_ledger(root, digest)
    assert service.inspect_reference(root, CANDIDATE, digest, _budget={'remaining': 1})['status'] == 'unknown'
    progress = load('projection_progress', 'progress-report.py')
    journal = progress._load_module('projection_journal', 'journal.py')
    item = {'candidate': CANDIDATE, 'expected_sha256': digest, 'status': 'pending', 'operation_id': 'a' * 64,
            'target': 'docs/knowledge/approved/ghp_' + 'A' * 40 + '.md'}
    result = progress._resume_result('ok', curation={'status': 'ok', 'references': [item]})
    projected = progress._public_resume(result, journal)
    visible = projected['curation']['references'][0]
    assert visible['identity_resolvable'] is False and 'target' not in visible
    assert 'ghp_' not in json.dumps(projected)


def test_multiple_operations_are_not_selected_by_receipt_or_recency(service, project, monkeypatch):
    root, digest = project
    def interrupt(stage, operation):
        if stage == 'prepared':
            raise OSError('stop')
    monkeypatch.setattr(service, '_checkpoint', interrupt)
    first, code = service.apply_decision(root, CANDIDATE, 'approve', expected_sha256=digest,
        metadata=META, reason='Reviewed.')
    assert code == 2
    relative = service._operation_directory(CANDIDATE) + '/' + first['operation_id'] + '.json'
    original = json.loads((root / relative).read_bytes())
    payload = {key: value for key, value in original.items() if key not in ('operation_id', 'record_publication')}
    stage, path, identity, _, raw = service._prepare_record(root, service._operation_directory(CANDIDATE), payload, operation=True)
    service._publish_stage(root, stage, path, identity, hashlib.sha256(raw).hexdigest())
    before = snapshot(root)
    result = service.inspect_reference(root, CANDIDATE, digest)
    assert result['status'] == 'unknown' and result['reason'] == 'ambiguous'
    result = service.inspect_reference(root, CANDIDATE, digest, operation_id=first['operation_id'])
    assert result['status'] == 'pending' and result['operation_id'] == first['operation_id']
    assert snapshot(root) == before


def test_readonly_staging_preserved_then_default_recovery_settles_it(service, project, monkeypatch):
    root, digest = project
    def interrupt(stage, operation):
        if stage == 'prepared':
            raise OSError('stop')
    monkeypatch.setattr(service, '_checkpoint', interrupt)
    first, code = service.apply_decision(root, CANDIDATE, 'approve', expected_sha256=digest,
        metadata=META, reason='Reviewed.')
    assert code == 2
    path = root / service._operation_directory(CANDIDATE) / (first['operation_id'] + '.json')
    record = json.loads(path.read_bytes())
    staged = root / record['record_publication']['staged']
    service.os.link(path, staged)
    assert service.inspect_reference(root, CANDIDATE, digest)['status'] == 'pending'
    assert staged.exists()
    monkeypatch.setattr(service, '_checkpoint', lambda *_: None)
    assert service.recover(root, first['operation_id'])[1] == 0
    assert not staged.exists()


def test_completed_view_never_reads_approved_body(service, project, monkeypatch):
    root, digest = project
    result, code = service.apply_decision(root, CANDIDATE, 'approve', expected_sha256=digest,
        metadata=META, reason='Reviewed.')
    assert code == 0
    reader = service._module('local-read.py')
    real_read = reader.read_bytes
    calls = []
    def observed(root, relative, **kwargs):
        assert not relative.startswith('docs/knowledge/approved/')
        calls.append(relative)
        return real_read(root, relative, **kwargs)
    monkeypatch.setattr(reader, 'read_bytes', observed)
    view = service.inspect_reference(root, CANDIDATE, digest)
    assert view['status'] == 'completed' and view['target_content_verified'] is False
    assert set(calls) <= {CANDIDATE, view['operation_path'], view['receipt_path']}
