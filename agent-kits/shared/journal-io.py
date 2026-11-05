"""Bounded journal I/O. Redirected parents and shared leaves are never adopted.

This observes path identities at boundaries; it is not a sandbox against an
arbitrary concurrent writer replacing directories with filesystem privileges.
"""
import importlib.util
import os
from pathlib import Path
import stat
import sys
import time

MAX_BYTES = 2 * 1024 * 1024


def _load(name):
    spec = importlib.util.spec_from_file_location('journal_io_' + name.replace('-', '_'), Path(__file__).with_name(name + '.py'))
    module = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def guard(deadline):
    need(time.monotonic() < deadline, 'journal_io_deadline')


IO = _load('local-state').StateIO(_load('local-read'), need, guard, maximum=MAX_BYTES, io_errors=True)


def directory(path, create=False):
    path = Path(path).absolute()
    missing = []
    parent = path
    while not os.path.lexists(parent):
        missing.append(parent); parent = parent.parent
    IO.dirs(parent)
    if not create:
        return not missing
    for item in reversed(missing):
        item.mkdir(mode=0o700, exist_ok=True); IO.dirs(item)
    return True


def read(path, maximum=MAX_BYTES):
    path = Path(path).absolute()
    if not directory(path.parent) or not os.path.lexists(path):
        return None
    return IO.read(path, maximum)[0]


def write(path, raw, *, owned_prefix=None, allow_degraded_sync=False):
    path = Path(path).absolute(); IO.dirs(path.parent)
    previous = identity = None
    mode = 0o600
    if os.path.lexists(path):
        previous, identity = IO.read(path, MAX_BYTES)
        mode = stat.S_IMODE(path.stat().st_mode)
        need(owned_prefix is None or previous.startswith(owned_prefix), 'unowned_journal_index')
    IO.write(path, raw, time.monotonic() + 5, expected=identity, mode=mode, allow_degraded_sync=allow_degraded_sync)


def update(path, transform):
    """Retry observed cooperating conflicts without losing another writer's bytes."""
    path = Path(path).absolute()
    for attempt in range(12):
        IO.dirs(path.parent)
        try:
            identity = None; raw = b''; mode = 0o600
            if os.path.lexists(path):
                raw, identity = IO.read(path, MAX_BYTES)
                mode = stat.S_IMODE(path.stat().st_mode)
            replacement = transform(raw)
            if replacement == raw:
                return
            IO.write(path, replacement, time.monotonic()+5, expected=identity, mode=mode)
            return
        except FileExistsError:
            continue
        except ValueError as error:
            if str(error) != 'unsafe_state':
                raise
            # An exclusive atomic creation briefly has two links until its
            # private temporary is removed. Wait, but never read/adopt that
            # shared inode. Persistent hardlinks still exhaust this bound.
            IO.dirs(path.parent)
            if os.path.lexists(path):
                info = path.lstat()
                need(stat.S_ISREG(info.st_mode) and not IO.reader._redirected(info)
                     and info.st_nlink in (1, 2), 'unsafe_state')
            time.sleep(min(0.002 * 2 ** attempt, 0.02))
    raise ValueError('journal_update_conflict')


def tail(path, maximum):
    """Read only the requested suffix, with identity checks before and after I/O."""
    path = Path(path).absolute(); IO.dirs(path.parent)
    before = IO.file(path)
    fd = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0))
    with os.fdopen(fd, 'rb') as handle:
        info = os.fstat(handle.fileno())
        need(stat.S_ISREG(info.st_mode) and info.st_nlink == 1
             and (info.st_dev, info.st_ino) == before[:2], 'changed_journal_log')
        IO.dirs(path.parent); need(IO.file(path) == before, 'changed_journal_log')
        handle.seek(-min(before[2], maximum), os.SEEK_END)
        raw = handle.read(maximum)
        need(IO.file(path) == before, 'changed_journal_log')
    return raw, before


def append(path):
    path = Path(path).absolute(); IO.dirs(path.parent)
    before = IO.file(path) if os.path.lexists(path) else None
    flags = os.O_WRONLY | os.O_APPEND | getattr(os, 'O_NOFOLLOW', 0)
    if before is None:
        flags |= os.O_CREAT | os.O_EXCL
    fd = os.open(path, flags, 0o600)
    try:
        info = os.fstat(fd)
        need(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, 'unsafe_journal_log')
        observed = IO.file(path)
        need(observed[:2] == (info.st_dev, info.st_ino)
             and (before is None or observed[:2] == before[:2]), 'changed_journal_log')
        IO.dirs(path.parent)
        return os.fdopen(fd, 'a', encoding='utf8')
    except BaseException:
        os.close(fd)
        raise


def queue(path):
    """Validate structural components only; payloads are guarded when actually used.

    Completed history must not be walked on every capture or budgeted replay.
    """
    path = Path(path).absolute()
    if not directory(path):
        return
    with os.scandir(path) as listing:
        for item in listing:
            if item.name.startswith('.tmp-'):continue  # Never adopt another initializer's private temporary.
            target = Path(item.path); info = target.lstat()
            need(not IO.reader._redirected(info), 'unsafe_journal_queue')
            if stat.S_ISDIR(info.st_mode):
                IO.dirs(target)
            else:
                IO.file(target)


class GuardedOutbox:
    """Use the outbox owner's per-operation I/O seam, without changing its protocol."""
    def __init__(self, module):
        self.module = module

    def __getattr__(self, name):
        value = getattr(self.module, name)
        if not callable(value):return value
        def call(*args, **kwargs):
            with self.module.with_io(_self()):
                return value(*args, **kwargs)
        return call


def _self():
    # importlib consumers need not register their module in sys.modules.
    from types import SimpleNamespace
    return SimpleNamespace(IO=IO, read=read, write=write, append=append, directory=directory, MAX_BYTES=MAX_BYTES)
