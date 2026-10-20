"""Regression boundaries for shared local metadata storage, without clients."""
import importlib.util
import os
from pathlib import Path
import time

import pytest

HERE = Path(__file__).resolve().parent


class Failure(Exception):
    pass


def need(ok, reason):
    if not ok:
        raise Failure(reason)


def load(filename):
    spec = importlib.util.spec_from_file_location(filename.replace('-', '_'), HERE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def owner():
    return load('local-state.py').StateIO(load('local-read.py'), need,
        lambda deadline: need(time.monotonic() < deadline, 'deadline_expired'), maximum=4096)


def test_exclusive_leaf_never_overwrites(tmp_path):
    io = owner()
    path = tmp_path / 'state.json'
    path.write_bytes(b'foreign')
    with pytest.raises(FileExistsError):
        io.write(path, b'new', time.monotonic() + 2)
    assert path.read_bytes() == b'foreign'
    assert sorted(p.name for p in tmp_path.iterdir()) == ['state.json']


def test_owned_update_matches_observed_generation(tmp_path):
    io = owner()
    path = tmp_path / 'state.json'
    io.write(path, b'one', time.monotonic() + 2)
    _, signature = io.read(path, 10)
    io.write(path, b'two', time.monotonic() + 2, expected=signature)
    assert io.read(path, 10)[0] == b'two'


def test_changed_leaf_is_not_adopted(tmp_path):
    io = owner()
    path = tmp_path / 'state.json'
    path.write_bytes(b'one')
    _, signature = io.read(path, 10)
    path.write_bytes(b'changed')
    with pytest.raises(Failure, match='unsafe_state'):
        io.write(path, b'new', time.monotonic() + 2, expected=signature)
    assert path.read_bytes() == b'changed'


def test_hardlink_rejected_before_read_and_write(tmp_path):
    io = owner()
    path = tmp_path / 'state.json'
    path.write_bytes(b'private')
    os.link(path, tmp_path / 'alias')
    with pytest.raises(Failure, match='unsafe_state'):
        io.read(path, 10)
    assert path.read_bytes() == b'private'


def test_read_is_bounded(tmp_path):
    io = owner()
    path = tmp_path / 'state.json'
    path.write_bytes(b'x' * 11)
    with pytest.raises(Failure, match='invalid_state'):
        io.read(path, 10)


def test_write_budget_checked_before_temp(tmp_path):
    io = owner()
    with pytest.raises(Failure, match='state_budget'):
        io.write(tmp_path / 'state.json', b'x' * 4097, time.monotonic() + 2)
    assert list(tmp_path.iterdir()) == []


def test_expired_deadline_does_not_write(tmp_path):
    io = owner()
    with pytest.raises(Failure, match='deadline_expired'):
        io.write(tmp_path / 'state.json', b'one', time.monotonic() - 1)
    assert list(tmp_path.iterdir()) == []


def test_directory_leaf_rejected(tmp_path):
    io = owner()
    path = tmp_path / 'state.json'
    path.mkdir()
    with pytest.raises(Failure, match='unsafe_state'):
        io.read(path, 10)


def test_redirected_parent_rejected(tmp_path):
    io = owner()
    real = tmp_path / 'real'
    real.mkdir()
    link = tmp_path / 'link'
    try:
        link.symlink_to(real, target_is_directory=True)
    except OSError:
        pytest.skip('OS symlink creation unavailable')
    with pytest.raises(Failure, match='unsafe_state'):
        io.write(link / 'state.json', b'one', time.monotonic() + 2)
    assert list(real.iterdir()) == []


def test_missing_lock_not_created_by_read_mode(tmp_path):
    io = owner()
    with pytest.raises(Failure, match='invalid_state'):
        with io.locked(tmp_path, time.monotonic() + 2, initialize=False):
            pytest.fail('missing lock accepted')
    assert list(tmp_path.iterdir()) == []


def test_competing_locks_fail_bounded_and_release(tmp_path):
    io = owner()
    with io.locked(tmp_path, time.monotonic() + 2, initialize=True):
        with pytest.raises(Failure, match='state_busy'):
            with io.locked(tmp_path, time.monotonic() + 2, initialize=False):
                pytest.fail('competing lock accepted')
    with io.locked(tmp_path, time.monotonic() + 2, initialize=False):
        pass


def test_failed_fsync_leaves_no_leaf_or_temp(tmp_path, monkeypatch):
    io = owner()
    monkeypatch.setattr(os, 'fsync', lambda fd: (_ for _ in ()).throw(OSError('fault')))
    with pytest.raises(Failure, match='durability_degraded'):
        io.write(tmp_path / 'state.json', b'one', time.monotonic() + 2)
    assert list(tmp_path.iterdir()) == []


def test_directory_flush_policy_is_injected_for_existing_owner(tmp_path):
    calls = []
    io = load('local-state.py').StateIO(load('local-read.py'), need,
        lambda deadline: need(time.monotonic() < deadline, 'deadline_expired'),
        maximum=4096, sync=lambda path: calls.append(path))
    io.write(tmp_path / 'state.json', b'one', time.monotonic() + 2)
    assert calls == [tmp_path]


# ---- panel-redesign T-43 / P-EI-3: a single attempt without waiting (lock and replace) ----------
def test_lock_wait_zero_is_a_single_attempt_without_sleeping(tmp_path, monkeypatch):
    module = load('local-state.py')
    io = module.StateIO(load('local-read.py'), need,
        lambda deadline: need(time.monotonic() < deadline, 'deadline_expired'), maximum=4096)
    state = tmp_path / 'state'
    state.mkdir()
    sleeps = []
    monkeypatch.setattr(module.time, 'sleep', lambda s: sleeps.append(s))
    with io.locked(state, time.monotonic() + 1, True):
        with pytest.raises(Failure) as busy:
            with io.locked(state, time.monotonic() + 1, False, wait=0):
                pass
        assert str(busy.value) == 'state_busy' and sleeps == []
        with pytest.raises(Failure):
            with io.locked(state, time.monotonic() + 1, False):  # the default still waits (up to 100 ms)
                pass
        assert sleeps


def test_replace_retry_can_be_disabled(tmp_path, monkeypatch):
    module = load('local-state.py')
    io = module.StateIO(load('local-read.py'), need,
        lambda deadline: need(time.monotonic() < deadline, 'deadline_expired'), maximum=4096)
    target = tmp_path / 'state.json'
    io.write(target, b'one', time.monotonic() + 2)
    expected = io.file(target)
    calls = []

    def replace(*args):
        calls.append(args)
        error = PermissionError(13, 'sharing violation')
        error.winerror = 32
        raise error

    monkeypatch.setattr(module.os, 'replace', replace)
    monkeypatch.setattr(module.time, 'sleep', lambda s: None)
    with pytest.raises(PermissionError):
        io.write(target, b'two', time.monotonic() + 2, expected=expected, retry=False)
    assert len(calls) == 1
    assert target.read_bytes() == b'one' and [p.name for p in tmp_path.iterdir()] == ['state.json']


# T-43 fix2 (2-1): byte 1 of `.lock` is the intent of a waiting priority writer (another process holds it here)
_INTENT = ('import os,sys\nfd=os.open(sys.argv[1],os.O_RDWR)\n'
    'if os.name=="nt":\n import msvcrt;os.lseek(fd,1,0);msvcrt.locking(fd,msvcrt.LK_NBLCK,1)\n'
    'else:\n import fcntl;fcntl.lockf(fd,fcntl.LOCK_EX|fcntl.LOCK_NB,1,1,0)\n'
    'print("held",flush=True);sys.stdin.read()\n')


def test_fix2_yield_waits_for_an_announced_intent_and_the_rest_ignore_it(tmp_path):
    import subprocess
    import sys
    io = owner()
    with io.locked(tmp_path, time.monotonic() + 1, True):
        pass
    child = subprocess.Popen([sys.executable, '-I', '-c', _INTENT, str(tmp_path / '.lock')],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    try:
        assert child.stdout.readline().strip() == 'held'
        with pytest.raises(Failure, match='state_busy'):
            with io.locked(tmp_path, time.monotonic() + 1, False, wait=0, priority='yield'):
                pass
        for priority in (None, 'claim'):  # the historical lock and other claimants are not blocked
            with io.locked(tmp_path, time.monotonic() + 1, False, priority=priority):
                pass
        with io.intent(tmp_path) as held:
            assert held is False  # one attempt, no wait
    finally:
        child.communicate('', timeout=10)
    with io.intent(tmp_path) as held:
        assert held is True
    with io.intent(tmp_path / 'absent') as held:
        assert held is False  # no `.lock` yet: nothing to announce, nothing created
    assert not (tmp_path / 'absent').exists()
    with io.locked(tmp_path, time.monotonic() + 1, False, wait=0, priority='yield'):
        pass
