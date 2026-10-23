"""Reject synthetic backup/restore path aliases before changing any fixture bytes."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import time

import pytest


SUPPORT = Path(__file__).with_name('memory_local_recovery_support') / 'protocol.py'
SPEC = importlib.util.spec_from_file_location('recovery_link_protocol', SUPPORT)
protocol = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(protocol)


def _record(path, value):
    path.write_text(json.dumps(value, sort_keys=True, ensure_ascii=False) + '\n', encoding='utf-8')


def _inside(path, own):
    resolved = path.resolve()
    assert resolved == own or own in resolved.parents
    return resolved


def _alias(link, destination, own, records):
    """Only this test's filesystem helper may launch a native junction creator."""
    assert link.is_absolute() and destination.is_absolute()
    _inside(link.parent, own)
    _inside(destination, own)
    assert not link.exists() and not link.is_symlink()
    intent = {'link': str(link), 'destination': str(destination),
              'parent_pid': os.getpid(), 'registered_utc_ns': time.time_ns()}
    _record(records / 'link-intent.json', intent)
    if os.name != 'nt':
        os.symlink(destination, link, target_is_directory=True)
        _record(records / 'link-result.json', dict(intent, operation='os.symlink', completed=True))
        return
    executable = Path(os.environ['COMSPEC'])
    if not executable.is_absolute() or not executable.is_file():
        raise protocol.InfrastructureError('absolute COMSPEC is unavailable')
    argv = [str(executable), '/d', '/c', 'mklink', '/J', str(link), str(destination)]
    intent.update(argv=argv, executable_sha256=hashlib.sha256(executable.read_bytes()).hexdigest())
    _record(records / 'link-intent.json', intent)
    process = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    receipt = dict(intent, pid=process.pid, started_utc_ns=time.time_ns())
    try:
        _record(records / 'link-parent-registration.json', receipt)
        stdout, stderr = process.communicate(timeout=10)
    except BaseException:
        if process.poll() is None:
            process.kill()
        process.wait(timeout=5)
        raise
    (records / 'link-stdout.bin').write_bytes(stdout)
    (records / 'link-stderr.bin').write_bytes(stderr)
    receipt.update(returncode=process.returncode, finished_utc_ns=time.time_ns(),
                   stdout_sha256=hashlib.sha256(stdout).hexdigest(),
                   stderr_sha256=hashlib.sha256(stderr).hexdigest())
    _record(records / 'link-result.json', receipt)
    if process.returncode != 0 or not link.is_junction():
        raise protocol.InfrastructureError('native junction creation failed; see raw receipts')


def _tree(root):
    """Observe links themselves and ordinary files without traversing an alias."""
    result = {}
    def visit(path):
        info = path.lstat()
        relative = path.relative_to(root).as_posix()
        entry = {'mode': info.st_mode, 'mtime_ns': info.st_mtime_ns}
        if path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction()):
            entry['link'] = os.readlink(path)
        elif stat.S_ISDIR(info.st_mode):
            entry['directory'] = True
            for child in sorted(path.iterdir()):
                visit(child)
        elif stat.S_ISREG(info.st_mode):
            raw = path.read_bytes()
            entry.update(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
        else:
            entry['nonregular'] = True
        result[relative] = entry
    visit(root)
    return result


def _corpus(root):
    document = root / 'docs/knowledge/approved/adr/toy.md'
    document.parent.mkdir(parents=True)
    document.write_text('Synthetic protocol byte sentinel.\n', encoding='utf-8')


@pytest.mark.parametrize('case', [
    'source-leaf', 'source-ancestor', 'snapshot-leaf', 'snapshot-ancestor',
    'target-dangling-leaf', 'target-ancestor',
])
def test_reject_path_alias_before_mutation(tmp_path, case):
    own = tmp_path / 'fixture'
    own.mkdir()
    records = tmp_path / 'native-records'
    records.mkdir()
    source = own / 'source'
    _corpus(source)
    snapshot = own / 'snapshot'
    target = own / 'restored'
    if case.startswith('source-'):
        if case == 'source-leaf':
            link, destination, operation_source = own / 'source-alias', source, own / 'source-alias'
        else:
            parent = own / 'sources'
            parent.mkdir()
            source.rename(parent / 'corpus')
            link, destination = own / 'sources-alias', parent
            operation_source = link / 'corpus'
        _alias(link, destination, own, records)
        operation = lambda: protocol.backup_drill(operation_source, snapshot, own=own)
    else:
        if case == 'snapshot-ancestor':
            parent = own / 'snapshots'
            parent.mkdir()
            snapshot = parent / 'snapshot'
        protocol.backup_drill(source, snapshot, own=own)
        if case == 'snapshot-leaf':
            link, destination = own / 'snapshot-alias', snapshot
            operation_snapshot = link
        elif case == 'snapshot-ancestor':
            link, destination = own / 'snapshots-alias', snapshot.parent
            operation_snapshot = link / 'snapshot'
        elif case == 'target-dangling-leaf':
            link, destination = own / 'target-alias', own / 'target-not-created'
            operation_snapshot, target = snapshot, link
        else:
            parent = own / 'destinations'
            parent.mkdir()
            link, destination = own / 'destinations-alias', parent
            operation_snapshot, target = snapshot, link / 'new-target'
        _alias(link, destination, own, records)
        operation = lambda: protocol.restore_drill(operation_snapshot, target, own=own)
    before = _tree(own)
    _record(records / 'fixture-before.json', before)
    rejection = None
    try:
        operation()
    except (protocol.InfrastructureError, protocol.RestoreRejected) as exc:
        rejection = type(exc).__name__ + ': ' + str(exc)
    after = _tree(own)
    _record(records / 'fixture-after.json', after)
    _record(records / 'observation.json', {'case': case, 'rejection': rejection,
                                         'unchanged': after == before})
    assert after == before, 'alias operation changed source/backup/destination/staging/link evidence'
    assert rejection is not None, 'alias must be rejected before any write'
