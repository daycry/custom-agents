"""panel-redesign T-43 fix3 (gap 3-2): one lock type on POSIX for both bytes of `.lock`.

fix2 took byte 0 with `flock` and byte 1 (intent of a lifecycle writer) with `fcntl.lockf`. On
macOS/BSD both kinds live in the same lock manager with different owners (`flock` belongs to the open
file description, `lockf` to the process), and on Linux over NFS `flock` is emulated with `fcntl`: the
intent on byte 1 then blocks the same process's `flock` of the whole file, and every SubagentStart/Stop
ends in `state_busy`. These tests run anywhere (also on Windows) with a deterministic model of those
semantics injected into `local-state.py`: a fake `fcntl` with one shared lock table and an `os` whose
`close` drops every record lock of the process on that file, as POSIX does.
Run: python -m pytest -q tests/test_local_state_fix3.py
"""
import errno
import importlib.util
import os
from pathlib import Path
import sys
import threading
import time

import pytest

SHARED = Path(__file__).resolve().parents[1] / 'agent-kits' / 'shared'
INF = float('inf')


def load(name):
    spec = importlib.util.spec_from_file_location(name.replace('-', '_') + '_fix3', SHARED / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BSDLocks:
    """`flock` owned by the open file description, `lockf` by the process; one table, so they collide."""
    LOCK_SH, LOCK_EX, LOCK_NB, LOCK_UN = 1, 2, 4, 8

    def __init__(self):
        self.table, self.calls, self.guard = [], [], threading.Lock()

    @staticmethod
    def inode(fd):
        info = os.fstat(fd)
        return info.st_dev, info.st_ino

    def _take(self, inode, owner, start, end):
        for lock in self.table:
            if lock[0] == inode and lock[1] != owner and lock[2] < end and start < lock[3]:
                raise BlockingIOError(errno.EAGAIN, 'Resource temporarily unavailable')
        self.table.append((inode, owner, start, end))

    def _drop(self, inode, owner, start=0, end=INF):
        self.table = [lock for lock in self.table
                      if not (lock[0] == inode and lock[1] == owner and lock[2] < end and start < lock[3])]

    def flock(self, fd, operation):
        with self.guard:
            self.calls.append('flock')
            inode, owner = self.inode(fd), ('ofd', fd)
            if operation & self.LOCK_UN:
                return self._drop(inode, owner)
            self._take(inode, owner, 0, INF)

    def lockf(self, fd, operation, length=0, start=0, whence=0):
        with self.guard:
            self.calls.append(('lockf', start, length))
            inode, owner = self.inode(fd), ('proc', os.getpid())
            end = start + length if length else INF
            if operation & self.LOCK_UN:
                return self._drop(inode, owner, start, end)
            self._take(inode, owner, start, end)

    def close(self, fd):
        with self.guard:
            inode = self.inode(fd)
            self._drop(inode, ('proc', os.getpid()))  # POSIX: any close drops the process's record locks
            self._drop(inode, ('ofd', fd))
        os.close(fd)

    def held(self, start):
        return [lock for lock in self.table if lock[2] <= start < lock[3]]


class PosixOs:
    """The real `os` seen as POSIX by `local-state.py`, with the model's `close`."""
    name = 'posix'

    def __init__(self, model):
        self._model = model

    def close(self, fd):
        self._model.close(fd)

    def __getattr__(self, attribute):
        return getattr(os, attribute)


@pytest.fixture
def bsd(monkeypatch):
    """Install the model in a module that loads `local-state.py` (the store, or the helper itself)."""
    model = BSDLocks()
    monkeypatch.setitem(sys.modules, 'fcntl', model)

    def install(state_module):
        monkeypatch.setattr(state_module, 'os', PosixOs(model))
        monkeypatch.setattr(state_module, 'sync_dir', lambda path: None)  # no directory fsync on Windows
        return state_module
    model.install = install
    return model


class Failure(Exception):
    pass


def _need(ok, reason):
    if not ok:
        raise Failure(reason)


def owner(state_module):
    return state_module.StateIO(load('local-read'), _need,
        lambda deadline: _need(time.monotonic() < deadline, 'deadline_expired'), maximum=4096)


@pytest.fixture
def project(tmp_path):
    root = tmp_path / 'project'
    (root / '.claude').mkdir(parents=True)
    (root / '.claude' / 'dev.json').write_text('{"sesion":{"actividad":true}}', encoding='utf-8')
    return root


def native(root, event, agent):
    return {'hook_event_name': event, 'session_id': 'session-secret-id', 'agent_id': agent,
            'agent_type': 'custom-agents:qa', 'cwd': str(root)}


# ---- 1. on POSIX nothing calls `flock` any more ---------------------------------------------------
def test_posix_never_calls_flock(bsd, tmp_path):
    io = owner(bsd.install(load('local-state')))
    with io.locked(tmp_path, time.monotonic() + 1, True):
        pass
    with io.intent(tmp_path) as held:
        assert held is True
        with io.locked(tmp_path, time.monotonic() + 1, False, priority='claim'):
            pass
    with io.locked(tmp_path, time.monotonic() + 1, False, wait=0, priority='yield'):
        pass
    assert 'flock' not in bsd.calls, bsd.calls
    assert ('lockf', 0, 1) in bsd.calls and ('lockf', 1, 1) in bsd.calls
    assert bsd.table == []  # everything released


def test_posix_store_lifecycle_and_tool_paths_never_call_flock(bsd, project):
    api = load('agent-activity-store')
    bsd.install(api._state_io)
    for event, agent in (('SubagentStart', 'agent-one'), ('SubagentStop', 'agent-one')):
        assert api.capture(project, runtime='claude', payload=native(project, event, agent))['status'] == 'ok'
    row = dict(runtime='claude', scope='subagent', session='session-secret-id', agent='agent-one', role='qa',
               tool='Bash', resumen='git status', duracion_ms=12, resultado='ok', window=None, nowait=False)
    assert api.record(project, row)['status'] == 'ok'
    assert 'flock' not in bsd.calls, bsd.calls
    assert bsd.table == []


# ---- 2. BSD semantics: the lifecycle path (intent on byte 1, then the lock) writes -------------------
def test_bsd_model_lifecycle_signal_with_intent_writes_instead_of_state_busy(bsd, project):
    api = load('agent-activity-store')
    bsd.install(api._state_io)
    # The first capture creates `.lock` (no intent yet); the second announces its intent on byte 1 first.
    assert api.capture(project, runtime='claude', payload=native(project, 'SubagentStart', 'agent-one'))['status'] == 'ok'
    second = api.capture(project, runtime='claude', payload=native(project, 'SubagentStop', 'agent-one'))
    assert second == {'status': 'ok', 'reason': None}, second
    third = api.capture(project, runtime='claude', payload=native(project, 'SubagentStart', 'agent-two'))
    assert third == {'status': 'ok', 'reason': None}, third
    assert len(api.history(project)['runs']) >= 2


def test_bsd_model_another_process_on_byte_0_still_excludes(bsd, tmp_path):
    io = owner(bsd.install(load('local-state')))
    with io.locked(tmp_path, time.monotonic() + 1, True):
        pass
    stat = (tmp_path / '.lock').stat()
    bsd.table.append(((stat.st_dev, stat.st_ino), ('proc', -1), 0, 1))  # a foreign process holds byte 0
    with pytest.raises(Failure, match='state_busy'):
        with io.locked(tmp_path, time.monotonic() + 1, False, wait=0):
            pass
    bsd.table.clear()
    bsd.table.append(((stat.st_dev, stat.st_ino), ('proc', -1), 1, 2))  # a foreign intent on byte 1
    with pytest.raises(Failure, match='state_busy'):
        with io.locked(tmp_path, time.monotonic() + 1, False, wait=0, priority='yield'):
            pass
    with io.locked(tmp_path, time.monotonic() + 1, False, wait=0):  # byte 0 is independent of byte 1
        pass


# ---- record locks are per process: threads must still exclude, and no close may drop a held lock --------
def test_threads_of_one_process_still_exclude_and_a_close_does_not_drop_the_holder(bsd, tmp_path):
    io = owner(bsd.install(load('local-state')))
    with io.locked(tmp_path, time.monotonic() + 1, True):
        pass
    entered, release, errors = threading.Event(), threading.Event(), []

    def holder():
        try:
            with io.locked(tmp_path, time.monotonic() + 5, False):
                entered.set()
                assert release.wait(5)
        except BaseException as error:  # noqa: BLE001
            errors.append(error)
    worker = threading.Thread(target=holder)
    worker.start()
    try:
        assert entered.wait(5)
        with pytest.raises(Failure, match='state_busy'):  # same process, other thread: busy, like flock
            with io.locked(tmp_path, time.monotonic() + 1, False, wait=0):
                pass
        with io.intent(tmp_path):  # opens and closes another descriptor of `.lock`
            pass
        assert bsd.held(0), bsd.table  # the holder's byte 0 survives both closes
    finally:
        release.set()
        worker.join(5)
    assert not worker.is_alive() and errors == []
    assert bsd.table == []


def test_nested_lock_in_the_same_thread_is_busy_as_before(bsd, tmp_path):
    io = owner(bsd.install(load('local-state')))
    with io.locked(tmp_path, time.monotonic() + 1, True):
        with pytest.raises(Failure, match='state_busy'):
            with io.locked(tmp_path, time.monotonic() + 1, False, wait=0):
                pass
        assert bsd.held(0)
    with io.locked(tmp_path, time.monotonic() + 1, False, wait=0):
        pass
    assert bsd.table == []
