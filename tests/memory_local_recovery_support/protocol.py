"""Synthetic acceptance drill, never a distributed backup implementation."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import stat
import time

MAX_FILES = 128
MAX_BYTES = 2 * 1024 * 1024
MAX_FILE_BYTES = 256 * 1024
MAX_PROCESSES = 40
CHILD_SECONDS = 25
MAX_OUTPUT_BYTES = 256 * 1024
MANIFEST_NAME = 'snapshot.complete.json'


class InfrastructureError(RuntimeError):
    """Execution/precondition failure, not an observed product regression."""


class RestoreRejected(ValueError):
    pass


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def within(path, root):
    path, root = Path(path).absolute(), Path(root).absolute()
    # Observe lexical leaves/ancestors before resolve discards link identity.
    # lstat also sees dangling links; Windows junctions are reparse points.
    for candidate in (path, root):
        for entry in (candidate, *candidate.parents):
            try:
                info = entry.lstat()
            except FileNotFoundError:
                continue  # New backup/restore destinations may not exist yet.
            if (stat.S_ISLNK(info.st_mode)
                    or getattr(info, 'st_file_attributes', 0)
                    & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400)):
                raise InfrastructureError('linked path in registered OWN')
    path, root = path.resolve(), root.resolve()
    if path != root and root not in path.parents:
        raise InfrastructureError('path outside registered OWN')
    return path


def regular(path):
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or path.is_symlink():
        raise InfrastructureError('nonregular fixture input')
    return info


def atomic_record(path, record):
    path = Path(path)
    temporary = path.with_name(path.name + '.own-tmp')
    with temporary.open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(record, handle, ensure_ascii=False, sort_keys=True)
        handle.write('\n')
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def memory_path(relative):
    """Only declared synthetic state; caches/active locks/unfinished temporaries excluded."""
    path = Path(relative)
    parent, name = path.parent.as_posix(), path.name
    if relative in ('.claude/journal/.claim.lock', '.claude/journal/.replay.lock'):
        return False
    if parent == '.claude' and re.fullmatch(r'session-prompts-[A-Za-z0-9._-]+\.log\.lock', name):
        return False
    # Match producer formats in their own locations; '.tmp-' inside canonical
    # document names is ordinary evidence and must survive backup/restoration.
    if (parent == '.claude/journal' or parent.startswith('.claude/journal/')) and re.fullmatch(r'\.tmp-[a-z0-9_]{8}\.json', name):
        return False
    if parent == 'docs/knowledge/journal' and re.fullmatch(r'.+\.md\.tmp-[0-9]+', name):
        return False
    if parent == '.claude' and re.fullmatch(r'session-prompts-[A-Za-z0-9._-]+\.log\.tmp-[a-z0-9_]{8}', name):
        return False
    return (relative.startswith('docs/knowledge/')
            or relative.startswith('.claude/journal/')
            or relative.startswith('.claude/session-prompts-')
            or relative in ('.claude/dev.json', '.claude/.gitignore',
                            '.claude/knowledge-services/taxonomy.json'))


def inventory(root):
    """Quiescent byte inventory with bounds and original timestamps for recovery."""
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise InfrastructureError('fixture root is unavailable or linked')
    result, cost = {}, 0
    for directory, directories, names in os.walk(root, followlinks=False):
        directories.sort()
        for name in directories:
            if (Path(directory) / name).is_symlink():
                raise InfrastructureError('linked fixture directory')
        for name in sorted(names):
            path = Path(directory) / name
            relative = path.relative_to(root).as_posix()
            if not memory_path(relative):
                continue
            info = regular(path)
            if len(result) >= MAX_FILES or info.st_size > MAX_FILE_BYTES:
                raise InfrastructureError('fixture file budget exceeded')
            with path.open('rb') as handle:
                raw = handle.read(MAX_FILE_BYTES + 1)
                after = os.fstat(handle.fileno())
            cost += len(raw)
            if len(raw) > MAX_FILE_BYTES or cost > MAX_BYTES:
                raise InfrastructureError('fixture byte budget exceeded')
            if (info.st_size, info.st_mtime_ns, info.st_ino) != (
                    after.st_size, after.st_mtime_ns, after.st_ino):
                raise InfrastructureError('fixture changed during observation')
            result[relative] = {'sha256': digest(raw), 'bytes': len(raw),
                                'mtime_ns': info.st_mtime_ns,
                                'mode': stat.S_IMODE(info.st_mode)}
    return result


def pause(spec, frontier, path=None):
    """One child announces a reached frontier; only its registered parent may kill it."""
    control = Path(spec['control'])
    record = {'schema': 1, 'nonce': spec['nonce'], 'pid': os.getpid(),
              'parent_pid': os.getppid(), 'frontier': frontier,
              'script_sha256': spec.get('script_sha256'),
              'reached_utc_ns': time.time_ns(), 'path': str(path) if path else None}
    atomic_record(control / 'ready.json', record)
    stop = time.monotonic() + CHILD_SECONDS
    while not (control / 'release').exists():
        if time.monotonic() >= stop:
            raise InfrastructureError('barrier not released within safety deadline')
        time.sleep(0.01)


def backup_drill(source, destination, *, own, barrier=None):
    """New destination only. Completion manifest is last; no online snapshot claim."""
    source, destination = within(source, own), within(destination, own)
    if destination.exists():
        raise InfrastructureError('backup destination already exists')
    before = inventory(source)
    if not before:
        raise InfrastructureError('empty fixture backup')
    destination.mkdir()
    for relative, meta in before.items():
        target = destination / 'data' / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        with (source / relative).open('rb') as handle:
            raw = handle.read(MAX_FILE_BYTES + 1)
        if len(raw) != meta['bytes'] or digest(raw) != meta['sha256']:
            raise InfrastructureError('source changed while copying')
        with target.open('xb') as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(target, meta['mode'])
        os.utime(target, ns=(meta['mtime_ns'], meta['mtime_ns']))
    if before != inventory(source) or before != inventory(destination / 'data'):
        raise InfrastructureError('unstable or incomplete copy')
    if barrier:
        pause(barrier, 'backup_before_complete_manifest')
    atomic_record(destination / MANIFEST_NAME,
                  {'schema': 1, 'complete': True, 'synthetic_only': True,
                   'files': before, 'excluded': ['SQLite cache', 'active locks', 'temporaries']})
    return before


def verified_backup(snapshot):
    snapshot = Path(snapshot)
    try:
        regular(snapshot / MANIFEST_NAME)
        raw = (snapshot / MANIFEST_NAME).read_bytes()
        if len(raw) > MAX_FILE_BYTES:
            raise RestoreRejected('manifest too large')
        manifest = json.loads(raw)
        if (manifest.get('schema') != 1 or manifest.get('complete') is not True
                or manifest.get('synthetic_only') is not True):
            raise RestoreRejected('manifest is incomplete')
        if not isinstance(manifest.get('files'), dict) or not manifest['files']:
            raise RestoreRejected('manifest files absent')
        if manifest['files'] != inventory(snapshot / 'data'):
            raise RestoreRejected('snapshot inventory differs')
        return manifest['files']
    except (OSError, KeyError, ValueError, InfrastructureError) as exc:
        raise RestoreRejected('snapshot cannot be verified') from exc


def restore_drill(snapshot, target, *, own):
    """Validate before any destination mutation, stage anew, publish to a new root."""
    snapshot, target = within(snapshot, own), within(target, own)
    files = verified_backup(snapshot)
    if target.exists():
        raise RestoreRejected('restore destination must be new')
    stage = target.with_name(target.name + '.restore-staging')
    if stage.exists():
        raise RestoreRejected('restore staging already exists')
    stage.mkdir()
    for relative, meta in files.items():
        path = stage / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with (snapshot / 'data' / relative).open('rb') as handle:
            raw = handle.read(MAX_FILE_BYTES + 1)
        if len(raw) != meta['bytes'] or digest(raw) != meta['sha256']:
            raise RestoreRejected('snapshot changed during restoration')
        with path.open('xb') as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(path, meta['mode'])
        os.utime(path, ns=(meta['mtime_ns'], meta['mtime_ns']))
    if inventory(stage) != files:
        raise RestoreRejected('restoration incomplete')
    if target.exists():
        raise RestoreRejected('restore destination appeared')
    # Single-parent OWN protocol, no hostile concurrent destination writer permitted.
    os.rename(stage, target)
    return files
