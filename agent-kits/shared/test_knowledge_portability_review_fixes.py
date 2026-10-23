"""Independent-review regressions M25-A01/A02: actual owner and isolated files."""
from pathlib import Path
import pytest
from test_knowledge_portability import import_, note, roots, service, transfer, tree

@pytest.mark.parametrize('reserved', ['.git', '.GIT'])
def test_export_git_metadata_is_rejected_before_policy_or_io(service, roots, monkeypatch, reserved):
    source, _ = roots
    source_id, _ = note(source)
    before = tree(source)
    calls = []
    actual_policy = service._policy
    def policy(root):
        calls.append(root)
        return actual_policy(root)
    monkeypatch.setattr(service, '_policy', policy)
    response, code = service.export_package(str(source), source_id='p', ids=[source_id],
                                           out=reserved + '/refs/heads/portable')
    assert code == 2 and response['status'] == 'protected_output', response
    assert response['written'] is False and calls == [], response
    assert tree(source) == before
    assert not (source / reserved).exists()

def test_stage_failure_before_creation_has_no_announced_write(service, roots, monkeypatch):
    _, raw = transfer(service, roots)
    _, destination = roots
    # Existing lock/infra excludes a newly created lock from the observed effects.
    with service._locked(str(destination)):
        pass
    before = tree(destination)
    attempts = []
    def before_stage(root, relative, payload, **kwargs):
        attempts.append(relative)
        assert not (Path(root) / relative).exists()
        raise OSError('fault before entering stage creation')
    monkeypatch.setattr(service, '_stage', before_stage)
    response, code = import_(service, destination, raw)
    assert code == 2 and len(attempts) == 1, response
    assert response['written'] is False, response
    assert response['entries'][0]['import_operation_id'] is None
    assert response['entries'][0]['import_receipt_path'] is None
    assert tree(destination) == before
    assert not (destination / attempts[0]).exists()
def test_stage_open_failure_preserves_unknown_effects(service, roots, monkeypatch):
    ids, raw = transfer(service, roots)
    _, destination = roots
    # The documented request binding lets the fixture prepare empty parents, so
    # this case observes only uncertain file creation, not new directory effects.
    import hashlib
    from test_knowledge_portability import IMPORT_BASE, canonical, sha
    _, policy_sha = service._policy(str(destination))
    binding = dict(package_sha256=sha(raw), destination_project_id='destination-project',
                   root_identity=service._identity(destination.lstat()),
                   destination_policy_sha256=policy_sha, producer='import')
    request = sha(canonical(binding))
    key = hashlib.sha256(ids[0].encode('utf-8')).hexdigest()
    directory = destination / IMPORT_BASE / 'operations' / request / key
    directory.mkdir(parents=True)
    with service._locked(str(destination)):
        pass
    before = tree(destination)
    actual_open = service.os.open
    attempts = []
    def fail_creation(path, flags, *args, **kwargs):
        if Path(path).name.startswith('.proposal-'):
            attempts.append(Path(path))
            raise PermissionError('OS open failed; creation outcome is not asserted by product')
        return actual_open(path, flags, *args, **kwargs)
    monkeypatch.setattr(service.os, 'open', fail_creation)
    response, code = import_(service, destination, raw)
    assert code == 2 and len(attempts) == 1, response
    assert response['written'] is None, response
    assert tree(destination) == before
    assert not attempts[0].exists()
