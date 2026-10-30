"""Shared bounded I/O for locally owned metadata under a cooperative lock.

Callers validate ownership and schemas. Identity checks observe boundaries;
they do not provide a sandbox against concurrent directory replacement.
"""
import contextlib
import os
from pathlib import Path
import stat
import tempfile
import threading
import time


def sync_dir(path):
    """Flush directory metadata where portable; Windows uses file fsync only."""
    if os.name == 'nt':
        return
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


class StateIO:
    """Reuse the canonical local reader and caller's errors/deadline policy."""

    def __init__(self, reader, need, guard, *, maximum, sync=None):
        self.reader, self.need, self.guard, self.maximum = reader, need, guard, maximum
        self.sync = sync_dir if sync is None else sync

    def dirs(self, path):
        path = Path(path)
        for entry in [*reversed(path.parents), path]:
            info = entry.lstat()
            self.need(stat.S_ISDIR(info.st_mode) and not self.reader._redirected(info), 'unsafe_state')

    def file(self, path):
        info = Path(path).lstat()
        self.need(stat.S_ISREG(info.st_mode) and info.st_nlink == 1
            and not self.reader._redirected(info), 'unsafe_state')
        return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns

    def read(self, path, maximum, *, changed_status=None):
        path = Path(path)
        self.dirs(path.parent)
        before = self.file(path)
        row = self.reader.read_bytes(path.parent, path.name, max_bytes=maximum)
        if changed_status is not None:
            self.need(row['status'] != 'changed_path', changed_status)
        self.need(row['status'] == 'ok', 'invalid_state')
        self.need(self.file(path) == before, changed_status or 'unsafe_state')
        return row['data'], before

    def write(self, path, raw, deadline, expected=None, retry=True, mode=None):
        """Exclusive creation or observed owned-leaf replacement; no overwrite fallback.
        `retry=False` makes a single `os.replace` attempt (no sharing-violation backoff)."""
        path = Path(path)
        self.need(type(raw) is bytes and len(raw) <= self.maximum, 'state_budget')
        self.guard(deadline)
        self.dirs(path.parent)
        fd, name = tempfile.mkstemp(prefix='.tmp-', dir=path.parent)
        temporary = Path(name)
        try:
            with os.fdopen(fd, 'wb') as handle:
                if mode is not None:
                    os.chmod(temporary, mode)
                handle.write(raw)
                handle.flush()
                try:
                    os.fsync(handle.fileno())
                except OSError:
                    self.need(False, 'durability_degraded')
            self.guard(deadline)
            self.dirs(path.parent)
            if expected is None:
                os.link(temporary, path, follow_symlinks=False)
            else:
                for attempt in range(4 if retry else 1):
                    self.guard(deadline)
                    self.dirs(path.parent)
                    self.need(self.file(path) == expected, 'unsafe_state')
                    try:
                        os.replace(temporary, path)
                        break
                    except OSError as error:
                        if (os.name != 'nt' or getattr(error, 'winerror', None) not in (5, 32, 33)
                                or attempt == 3 or not retry):
                            raise
                        self.guard(deadline)
                        time.sleep(min(0.02 * 2 ** attempt, max(0, deadline - time.monotonic())))
            if temporary.exists():
                temporary.unlink()
            try:
                self.sync(path.parent)
            except OSError:
                self.need(False, 'durability_degraded')
        finally:
            if temporary.exists():
                temporary.unlink()  # Only this invocation's exact private temporary.

    @contextlib.contextmanager
    def intent(self, state):
        """Announce a priority writer (byte 1 of an existing `.lock`) before its unlocked preparation,
        so `priority='yield'` writers stop entering; one attempt, never waits. Yields whether it is held."""
        path = Path(state) / '.lock'
        fd = release = None
        try:
            with contextlib.suppress(OSError):
                before = self.file(path)
                fd = os.open(path, os.O_RDWR | getattr(os, 'O_NOFOLLOW', 0))
                info = os.fstat(fd)
                if (info.st_dev, info.st_ino) == before[:2]:
                    release = _byte_lock(fd, 1)
            yield release is not None
        finally:
            if release:
                with contextlib.suppress(OSError):
                    release()
            if fd is not None:
                _close(fd)

    @contextlib.contextmanager
    def locked(self, state, deadline, initialize, wait=0.1, priority=None):
        """Bounded cooperative process lock; never remove another writer's lock.
        `wait=0` is a single attempt without sleeping. Byte 0 of `.lock` is the lock; byte 1 is
        the intent of a waiting priority writer: `priority='claim'` announces it while waiting,
        `priority='yield'` never takes byte 0 while someone announces it (it waits, or fails at once)."""
        state = Path(state)
        self.guard(deadline)
        self.dirs(state)
        path = state / '.lock'
        if not path.exists():
            self.need(initialize, 'invalid_state')
            try:
                with path.open('xb') as handle:
                    # Both platforms lock byte ranges beyond EOF. Publish an
                    # empty leaf in its final generation: a later marker write
                    # races observers between exclusive creation and acquisition.
                    handle.flush()
                    os.fsync(handle.fileno())
                self.sync(state)
            except FileExistsError:
                pass
        before = self.file(path)
        fd = os.open(path, os.O_RDWR | getattr(os, 'O_NOFOLLOW', 0))
        unlock = intent = None
        try:
            info = os.fstat(fd)
            self.need((info.st_dev, info.st_ino) == before[:2]
                and self.file(path) == before, 'unsafe_state')
            stop = min(deadline, time.monotonic() + wait)
            while True:
                self.guard(deadline)
                try:
                    if priority == 'claim' and intent is None:
                        with contextlib.suppress(OSError):
                            intent = _byte_lock(fd, 1)  # taken by another claimant: compete as before
                    if priority == 'yield':
                        _byte_lock(fd, 1)()  # raises while a priority writer waits
                    unlock = _byte_lock(fd, 0)
                    break
                except OSError:
                    self.need(time.monotonic() < stop, 'state_busy')
                    time.sleep(min(0.005, max(0, stop - time.monotonic())))
            if intent:
                with contextlib.suppress(OSError):
                    intent()
                intent = None
            self.dirs(state)
            self.need(self.file(path) == before, 'unsafe_state')
            yield
        finally:
            for release in (intent, unlock):
                if release:
                    with contextlib.suppress(OSError):
                        release()
            _close(fd)


# POSIX: ONE lock type for both bytes (panel-redesign T-43 fix3, 3-2). fix2 mixed `flock` (byte 0) with
# `fcntl.lockf` (byte 1); on macOS/BSD both share one lock manager with different owners (open file vs
# process) and on Linux over NFS `flock` is emulated with `fcntl`, so a process's own intent on byte 1
# blocked its `flock` and every lifecycle signal ended in `state_busy`. Now both bytes are `lockf` ranges.
# Record locks belong to the PROCESS, so two rules restore what `flock` gave for free inside one process:
# byte 0 is also exclusive between `locked()` calls of the same process (threads, or a nested call), and
# a descriptor of `.lock` is closed only when the process holds no lock on it (closing ANY descriptor drops
# all of the process's record locks on that file). Windows (`msvcrt.locking`, per handle) is unchanged.
_HELD_GUARD = threading.Lock()
_HELD = {}  # (st_dev, st_ino) -> {'byte0': bool, 'count': locks held, 'closing': deferred descriptors}


def _key(fd):
    info = os.fstat(fd)
    return info.st_dev, info.st_ino


def _close(fd):
    """Close a descriptor of `.lock`; on POSIX, deferred while this process holds any lock on the file.
    Closed under the guard, so no other thread can take a lock between the check and the close."""
    if os.name == 'nt':
        os.close(fd)
        return
    with _HELD_GUARD:
        entry = _HELD.get(_key(fd))
        if entry is not None:
            entry['closing'].append(fd)
        else:
            os.close(fd)


def _byte_lock(fd, offset):
    """Non-blocking exclusive lock of one byte of `fd` (OSError when taken); returns its release.
    POSIX: `fcntl.lockf` for both bytes (one lock type); byte 0 also excludes the rest of this process."""
    if os.name == 'nt':
        import msvcrt
        os.lseek(fd, offset, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        def release():
            os.lseek(fd, offset, os.SEEK_SET)
            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        return release
    import fcntl
    with _HELD_GUARD:
        key = _key(fd)
        entry = _HELD.setdefault(key, {'byte0': False, 'count': 0, 'closing': []})
        try:
            if offset == 0 and entry['byte0']:
                raise BlockingIOError(11, 'byte 0 of .lock is held by this process')
            fcntl.lockf(fd, fcntl.LOCK_EX | fcntl.LOCK_NB, 1, offset, os.SEEK_SET)
        except OSError:
            if not entry['count']:
                del _HELD[key]
            raise
        entry['count'] += 1
        entry['byte0'] = entry['byte0'] or offset == 0
    released = []

    def release():
        if released:
            return
        released.append(True)
        with _HELD_GUARD:
            try:
                fcntl.lockf(fd, fcntl.LOCK_UN, 1, offset, os.SEEK_SET)
            finally:
                entry['count'] -= 1
                if offset == 0:
                    entry['byte0'] = False
                if not entry['count']:
                    pending, entry['closing'] = entry['closing'], []
                    _HELD.pop(key, None)
                    for descriptor in pending:
                        with contextlib.suppress(OSError):
                            os.close(descriptor)
    return release
