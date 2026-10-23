"""Controlled publication failures must retain the first infrastructure cause.

Only the real synthetic protocol/child run in this process. Product execution and
the OS process boundary are stubbed; no product module executes or child process launches.
"""
import errno
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

import pytest

SUPPORT = Path(__file__).with_name('memory_local_recovery_support')


def modules(monkeypatch):
    monkeypatch.setattr(sys, 'path', sys.path.copy())
    spec = importlib.util.spec_from_file_location('protocol', SUPPORT / 'protocol.py')
    protocol = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(protocol)
    monkeypatch.setitem(sys.modules, 'protocol', protocol)
    spec = importlib.util.spec_from_file_location('secondary_owned_child', SUPPORT / 'child.py')
    child = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(child)
    return protocol, child


@pytest.mark.parametrize('stage', ['fsync', 'replace'])
def test_first_publication_failure_is_infrastructure_with_original_cause(tmp_path, monkeypatch, stage):
    protocol, _ = modules(monkeypatch)
    path = tmp_path / 'audit.json'
    original_bytes = b'{"prior":"durable"}\n'
    path.write_bytes(original_bytes)
    record = {'nonce': 'a' * 32, 'attempts': [{'kind': 'git_unavailable'}]}
    first = PermissionError(errno.EACCES, 'controlled publication denial', str(path))
    operation = protocol.os.fsync if stage == 'fsync' else protocol.os.replace
    attempts = []

    def fail(*args, **kwargs):
        attempts.append(args)
        raise first

    monkeypatch.setattr(protocol.os, stage, fail)
    with pytest.raises(protocol.InfrastructureError) as caught:
        protocol.atomic_record(path, record)
    assert caught.value.__cause__ is first
    assert not isinstance(caught.value, OSError), 'owner _git must not swallow infrastructure as unavailable Git'
    identity = caught.value.record_failure
    assert identity['stage'] == stage
    assert identity['path'] == str(path)
    assert identity['temporary'] == str(path.with_name('audit.json.own-tmp'))
    assert identity['nonce'] == record['nonce']
    assert identity['pid'] == os.getpid() and identity['parent_pid'] == os.getppid()
    assert identity['errno'] == errno.EACCES
    assert len(attempts) == 1, 'no retry of failed publication'
    assert path.read_bytes() == original_bytes
    assert json.loads(path.with_name('audit.json.own-tmp').read_bytes()) == record
    monkeypatch.setattr(protocol.os, stage, operation)


def test_existing_temporary_is_preserved_and_classified_at_open(tmp_path, monkeypatch):
    protocol, _ = modules(monkeypatch)
    path = tmp_path / 'audit.json'
    temporary = path.with_name('audit.json.own-tmp')
    durable, evidence = b'{"durable":true}\n', b'{"failed_publication_evidence":true}\n'
    path.write_bytes(durable)
    temporary.write_bytes(evidence)
    with pytest.raises(protocol.InfrastructureError) as caught:
        protocol.atomic_record(path, {'nonce': 'b' * 32})
    assert isinstance(caught.value.__cause__, FileExistsError)
    assert caught.value.record_failure['stage'] == 'open'
    assert caught.value.record_failure['nonce'] == 'b' * 32
    assert path.read_bytes() == durable and temporary.read_bytes() == evidence


@pytest.mark.parametrize('owner_catches_oserror', [False, True])
def test_child_finally_propagates_first_audit_failure_without_second_write(tmp_path, monkeypatch, owner_catches_oserror):
    protocol, child = modules(monkeypatch)
    source, control, root = tmp_path / 'source', tmp_path / 'control', tmp_path / 'project'
    control.mkdir(); root.mkdir()
    script = source / 'agent-kits/shared/journal.py'
    script.parent.mkdir(parents=True)
    script.write_bytes(b'# Synthetic unused CLI sentinel; no product execution.\n')
    nonce = 'c' * 32
    relative = 'agent-kits/shared/journal.py'
    spec = {'own': str(tmp_path), 'control': str(control), 'root': str(root), 'source': str(source),
            'nonce': nonce, 'parent_pid': os.getppid(), 'mode': 'cli', 'script': str(script),
            'script_sha256': hashlib.sha256(script.read_bytes()).hexdigest(), 'arguments': [],
            'allowed_source_files': [relative], 'allowed_source_sha256': {relative: hashlib.sha256(script.read_bytes()).hexdigest()}}
    spec_path = tmp_path / 'spec.json'
    spec_path.write_text(json.dumps(spec), encoding='utf8')
    monkeypatch.setattr(sys, 'argv', [str(SUPPORT / 'child.py'), str(spec_path)])
    hooks = []
    monkeypatch.setattr(child.sys, 'addaudithook', hooks.append)
    first = PermissionError(errno.EACCES, 'controlled second audit publication denial', str(control / 'audit.json'))
    real_replace, real_record = protocol.os.replace, child.atomic_record
    records, failures, work_after_failure = [], [], []

    def replace(old, new, *args, **kwargs):
        if Path(new) == control / 'audit.json' and len(json.loads(Path(old).read_bytes())['attempts']) == 2:
            raise first
        return real_replace(old, new, *args, **kwargs)

    def observed_record(path, record):
        if Path(path) == control / 'audit.json':
            records.append(len(record['attempts']))
        try:
            return real_record(path, record)
        except BaseException as exc:
            failures.append(exc)
            raise

    monkeypatch.setattr(protocol.os, 'replace', replace)
    monkeypatch.setattr(child, 'atomic_record', observed_record)

    def synthetic_execution(*args, **kwargs):
        argv = ['git', '-C', str(root), 'status', '--porcelain']
        event = (None, child.subprocess.list2cmdline(argv), None, None) if os.name == 'nt' else ('git', argv, None, None)
        for number in range(2):
            try:
                hooks[0]('subprocess.Popen', event)
            except OSError:
                if number == 1 and not owner_catches_oserror:
                    raise
        work_after_failure.append(True)

    monkeypatch.setattr(child.runpy, 'run_path', synthetic_execution)
    with pytest.raises(protocol.InfrastructureError) as caught:
        child.main()
    assert len(failures) == 1, 'finally must not replace first cause with a temporal collision'
    assert caught.value is failures[0] and caught.value.__cause__ is first
    assert caught.value.record_failure['stage'] == 'replace'
    assert caught.value.record_failure['nonce'] == nonce
    assert records == [0, 1, 2], 'no attempted final audit rewrite after failure'
    assert work_after_failure == [], 'infrastructure must escape an owner OSError handler'
    assert len(json.loads((control / 'audit.json').read_bytes())['attempts']) == 1
    assert len(json.loads((control / 'audit.json.own-tmp').read_bytes())['attempts']) == 2
    assert not (control / 'finished.json').exists(), 'failed audit cannot acknowledge finished work'
