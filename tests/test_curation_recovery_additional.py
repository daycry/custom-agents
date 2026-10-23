"""IO, CLI and receipt recovery boundaries without subprocesses or outside files."""
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import threading

import pytest

SOURCE = Path(os.environ.get('MEMORY_COVERAGE_SOURCE', Path(__file__).resolve().parents[1]))
TEXT = '''---
category: GOTCHA
evidencia: validated_case
fuentes: [docs/reproduction.md]
tags: [area:testing]
---
# Concrete evidence
The reproducible case retains its reference.
'''
META = {'id': 'ca.gotcha.recovery', 'category': 'GOTCHA', 'version': 1, 'estado': 'aprobado'}
PENDING = 'docs/knowledge/candidates/pending/example.md'
APPROVED = 'docs/knowledge/approved/gotchas/example.md'


@pytest.fixture
def service():
    path = SOURCE / 'agent-kits/shared/knowledge-curation.py'
    spec = importlib.util.spec_from_file_location('curation_recovery_additional', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def root(tmp_path):
    project = tmp_path / 'project'
    policy = project / '.claude/knowledge-services/taxonomy.json'
    policy.parent.mkdir(parents=True)
    policy.write_text(json.dumps({'version': 1, 'id_prefix': 'ca', 'categories': [
        {'key': 'GOTCHA', 'folder': 'gotchas', 'min_evidence': 'validated_case'}],
        'denylist': ['chain-of-thought']}), encoding='utf-8')
    return project


def tree(root, *, while_locked=False):
    # Windows forbids reading the locked byte; observe content and durable records,
    # then include the lock again in the full snapshot after the owner releases it.
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*')
            if p.is_file() and not (while_locked and p.name == '.curation-lock')}


def propose(service, root, text=TEXT):
    result, code = service.propose(root, 'example.md', text, producer='documenter')
    assert code == 0 and result['ruta'] == PENDING
    assert result['sha256'] == hashlib.sha256((root / PENDING).read_bytes()).hexdigest()
    return result['sha256']


def apply(service, root, digest):
    return service.apply_decision(root, PENDING, 'approve', expected_sha256=digest,
                                  metadata=dict(META), reason='Reproduction independently examined.')


def receipt_path(service, root, operation):
    return root / service.RECEIPTS / (operation + '.json')


def test_cli_propose_corrected_approval_and_recovery_bind_persisted_bytes(service, root, monkeypatch, capsys):
    monkeypatch.setattr(sys, 'stdin', io.TextIOWrapper(io.BytesIO(TEXT.encode()), encoding='utf-8'))
    assert service.main(['propose', '--root', str(root), '--filename', 'example.md', '--producer', 'documenter']) == 0
    proposal = json.loads(capsys.readouterr().out)
    assert proposal['sha256'] == hashlib.sha256((root / PENDING).read_bytes()).hexdigest()
    replacement = TEXT + '\nReviewed correction without direct candidate edits.\n'
    monkeypatch.setattr(sys, 'stdin', io.TextIOWrapper(io.BytesIO(replacement.encode()), encoding='utf-8'))
    assert service.main(['apply', PENDING, '--root', str(root), '--decision', 'approve',
        '--expected-sha256', proposal['sha256'], '--reason', 'Evidence examined.',
        '--metadata-json', json.dumps(META), '--replacement-stdin']) == 0
    approved = json.loads(capsys.readouterr().out)
    assert b'Reviewed correction' in (root / APPROVED).read_bytes()
    assert not (root / PENDING).exists()
    assert approved['sha256'] == hashlib.sha256((root / APPROVED).read_bytes()).hexdigest()
    before = tree(root)
    assert service.main(['recover', approved['operation_id'], '--root', str(root)]) == 0
    assert json.loads(capsys.readouterr().out) == approved
    assert tree(root) == before


@pytest.mark.parametrize('payload', [b'\xff\xfe', b'x' * (256 * 1024 + 1)], ids=['invalid_utf8', 'over_limit'])
def test_cli_rejects_non_utf8_and_oversized_stdin_without_proposal(service, root, monkeypatch, capsys, payload):
    before = tree(root)
    monkeypatch.setattr(sys, 'stdin', io.TextIOWrapper(io.BytesIO(payload), encoding='utf-8'))
    assert service.main(['propose', '--root', str(root), '--filename', 'example.md', '--producer', 'documenter']) == 2
    result = json.loads(capsys.readouterr().out)
    assert result['status'] in ('invalid_encoding', 'payload_limit')
    assert tree(root) == before


def test_cli_invalid_metadata_does_not_consume_candidate(service, root, capsys):
    digest = propose(service, root)
    before = tree(root)
    assert service.main(['apply', PENDING, '--root', str(root), '--decision', 'approve',
        '--expected-sha256', digest, '--reason', 'Reviewed.', '--metadata-json', '{ partial']) == 2
    result = json.loads(capsys.readouterr().out)
    assert result['status'] == 'io_or_shared_unavailable'
    assert tree(root) == before


@pytest.mark.parametrize('boundary', ['destination_link', 'source_retirement', 'receipt_link'])
def test_real_io_failure_leaves_recoverable_operation_and_never_loses_evidence(service, root, monkeypatch, boundary):
    digest = propose(service, root)
    original = (root / PENDING).read_bytes()
    real_link, real_unlink = service.os.link, Path.unlink
    failures = []

    def fail_link(source, destination, **kwargs):
        relative = Path(destination).relative_to(root).as_posix()
        should_fail = ((boundary == 'destination_link' and relative == APPROVED)
                       or (boundary == 'receipt_link' and relative.startswith(service.RECEIPTS + '/') and relative.endswith('.json')))
        if should_fail:
            failures.append(relative)
            raise PermissionError('fixture IO denied at publication boundary')
        return real_link(source, destination, **kwargs)

    def fail_unlink(path, *args, **kwargs):
        if boundary == 'source_retirement' and path == root / PENDING:
            failures.append(PENDING)
            raise PermissionError('fixture source retirement denied')
        return real_unlink(path, *args, **kwargs)

    monkeypatch.setattr(service.os, 'link', fail_link)
    monkeypatch.setattr(Path, 'unlink', fail_unlink)
    result, code = apply(service, root, digest)
    assert code == 2 and len(failures) == 1 and result['operation_id']
    assert (root / PENDING).exists() == (boundary != 'receipt_link')
    assert (root / APPROVED).exists() == (boundary != 'destination_link')
    if (root / PENDING).exists():
        assert (root / PENDING).read_bytes() == original
    monkeypatch.setattr(service.os, 'link', real_link)
    monkeypatch.setattr(Path, 'unlink', real_unlink)
    recovered, code = service.recover(root, result['operation_id'])
    assert code == 0 and recovered['status'] == 'complete'
    assert not (root / PENDING).exists()
    final_bytes = (root / APPROVED).read_bytes()
    assert recovered['sha256'] == hashlib.sha256(final_bytes).hexdigest()
    receipt = json.loads(receipt_path(service, root, result['operation_id']).read_bytes())
    assert receipt['source_sha256'] == digest and receipt['target_sha256'] == recovered['sha256']
    assert receipt['status'] == 'complete'
    stable = tree(root)
    assert service.recover(root, result['operation_id']) == (recovered, 0)
    assert tree(root) == stable


@pytest.mark.parametrize('damage', ['partial_json', 'non_object', 'wrong_status', 'bad_publication'])
def test_recovery_refuses_corrupt_or_partial_receipt_without_rewriting_it(service, root, damage):
    digest = propose(service, root)
    result, code = apply(service, root, digest)
    assert code == 0
    receipt = receipt_path(service, root, result['operation_id'])
    if damage == 'partial_json':
        receipt.write_bytes(b'{"operation_id":')
    elif damage == 'non_object':
        receipt.write_bytes(b'[]')
    else:
        record = json.loads(receipt.read_bytes())
        if damage == 'wrong_status':
            record['status'] = 'complete-but-modified'
        else:
            record['record_publication'] = {'staged': 'outside', 'identity': [0, 0, 0]}
        receipt.write_text(json.dumps(record), encoding='utf-8')
    before = tree(root)
    recovered, code = service.recover(root, result['operation_id'])
    assert code == 2 and recovered['status'] != 'complete'
    assert tree(root) == before and (root / APPROVED).exists()


def test_existing_pending_operation_must_be_recovered_before_new_decision(service, root, monkeypatch):
    digest = propose(service, root)

    def interrupt(stage, operation):
        if stage == 'prepared':
            raise OSError('fixture interrupted before publication')

    monkeypatch.setattr(service, '_checkpoint', interrupt)
    prepared, code = apply(service, root, digest)
    assert code == 2 and prepared['operation_id']
    monkeypatch.setattr(service, '_checkpoint', lambda *_: None)
    before = tree(root)
    rejected, code = service.apply_decision(root, PENDING, 'reject', expected_sha256=digest, reason='Different decision.')
    assert code == 1 and rejected['status'] == 'recover_existing_operation'
    assert tree(root) == before
    completed, code = service.recover(root, prepared['operation_id'])
    assert code == 0 and completed['ruta'] == APPROVED


def test_recovery_does_not_reconstruct_missing_source_and_destination(service, root, monkeypatch):
    digest = propose(service, root)

    def interrupt(stage, operation):
        if stage == 'prepared':
            raise OSError('fixture interruption')

    monkeypatch.setattr(service, '_checkpoint', interrupt)
    prepared, code = apply(service, root, digest)
    assert code == 2
    monkeypatch.setattr(service, '_checkpoint', lambda *_: None)
    (root / PENDING).unlink()
    before = tree(root)
    result, code = service.recover(root, prepared['operation_id'])
    assert code == 2 and result['status'] == 'source_and_target_unavailable'
    assert tree(root) == before and not (root / APPROVED).exists()


def test_cooperating_recovery_contender_cannot_change_operation_while_owner_applies(service, root, monkeypatch):
    digest = propose(service, root)
    reached, release = threading.Event(), threading.Event()
    pending, outputs = [], []

    def checkpoint(stage, operation):
        if stage == 'prepared':
            pending.append(operation['operation_id'])
            reached.set()
            assert release.wait(5), 'fixture release timeout'

    def worker_apply():
        try:
            outputs.append(apply(service, root, digest))
        except BaseException as exc:
            outputs.append(exc)

    monkeypatch.setattr(service, '_checkpoint', checkpoint)
    worker = threading.Thread(target=worker_apply, daemon=True)
    worker.start()
    try:
        assert reached.wait(5), 'owner did not reach prepared boundary'
        before = tree(root, while_locked=True)
        refused, code = service.recover(root, pending[0])
        assert code == 2 and refused['status'] == 'writer_busy'
        assert tree(root, while_locked=True) == before
    finally:
        release.set()
        worker.join(5)
    assert not worker.is_alive() and len(outputs) == 1
    assert not isinstance(outputs[0], BaseException) and outputs[0][1] == 0
    stable = tree(root)
    assert service.recover(root, pending[0]) == outputs[0]
    assert tree(root) == stable


@pytest.mark.parametrize('metadata', [None, [], dict(META, version=2), dict(META, tags=[]),
                                    dict(META, source={'nested': 'value'}), dict(META, **{'bad-key': 'value'})])
def test_approval_metadata_is_representable_or_candidate_remains_unconsumed(service, root, metadata):
    digest = propose(service, root)
    before = (root / PENDING).read_bytes()
    result, code = service.apply_decision(root, PENDING, 'approve', expected_sha256=digest,
        metadata=metadata, reason='Evidence examined.')
    assert code != 0 and result['status'] != 'complete'
    assert (root / PENDING).read_bytes() == before and not (root / APPROVED).exists()


def test_declared_producer_and_final_id_cannot_be_relabelled(service, root):
    before = tree(root)
    result, code = service.propose(root, 'example.md', TEXT.replace('category:', 'proposed_by: qa\ncategory:', 1), producer='documenter')
    assert code == 1 and result['status'] == 'conflicting_producer_label' and tree(root) == before
    digest = propose(service, root, TEXT.replace('category:', 'id: ca.gotcha.original\ncategory:', 1))
    original = (root / PENDING).read_bytes()
    result, code = apply(service, root, digest)
    assert code == 1 and result['status'] == 'changed_declared_id'
    assert (root / PENDING).read_bytes() == original and not (root / APPROVED).exists()


def test_diagnostics_remain_generic_when_redactor_is_unavailable(service, root, monkeypatch):
    original_module = service._module

    def unavailable(filename):
        if filename == 'redact.py':
            raise ImportError('fixture secret diagnostic must not be returned')
        return original_module(filename)

    monkeypatch.setattr(service, '_module', unavailable)
    before = tree(root)
    result, code = service.propose(root, '../private-secret.md', TEXT, producer='documenter')
    assert code == 2 and result['status'] == 'invalid_filename'
    assert 'private-secret' not in json.dumps(result) and 'fixture secret' not in json.dumps(result)
    assert tree(root) == before
