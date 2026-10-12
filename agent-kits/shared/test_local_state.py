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
