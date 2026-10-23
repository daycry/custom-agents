"""Minor B-T01 failure-path isolation, with actual OWN Python children."""
import subprocess
import sys

import pytest

from test_plan_review import owned
import test_plan_review_feedback_contract as target


def hanging_child(o, line='ready'):
    script = o.root/'cleanup_child.py'
    script.write_text("import threading\n"+("print("+repr(line)+",flush=True)\n" if line else '')+
                      "threading.Event().wait()\n", encoding='utf8')
    return subprocess.Popen([sys.executable, '-I', '-X', 'utf8', '-B', str(script)],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def external_cleanup(children):
    """Probe fallback only: red assertions cannot leak into the next test."""
    for child in children:
        if child.poll() is None: child.kill()
        child.communicate(timeout=15)


def first_communication_times_out(child, monkeypatch):
    original = child.communicate; first = [True]
    def communicate(input=None, timeout=None):
        if first[0]:
            first[0] = False
            return original(input, timeout=0.05)  # Actual timeout, fixture-only.
        return original(input, timeout=timeout)
    monkeypatch.setattr(child, 'communicate', communicate)


def test_minor_b_t01_finish_timeout_kills_and_drains(owned, monkeypatch):
    child = hanging_child(owned)
    first_communication_times_out(child, monkeypatch)
    try:
        with pytest.raises(subprocess.TimeoutExpired): target.finish(child, b'{}')
        assert child.poll() is not None
        assert child.stdout.closed and child.stderr.closed
    finally: external_cleanup([child])


def test_minor_b_t01_holder_readiness_timeout_closes_reader_and_child(owned):
    child = hanging_child(owned, line=None)
    try:
        with pytest.raises(subprocess.TimeoutExpired): target.readiness_line(child, timeout=0.05)
        assert child.poll() is not None and child.stdout.closed and child.stderr.closed
    finally: external_cleanup([child])


@pytest.mark.parametrize('fault', ['second_popen', 'barrier'])
def test_minor_b_t01_pair_failed_setup_or_barrier_closes_all(owned, monkeypatch, fault):
    children = []
    def spawn(*args):
        if fault == 'second_popen' and children: raise OSError('OWN second Popen setup failure')
        child = hanging_child(owned); children.append(child); return child
    monkeypatch.setattr(target, 'cli', spawn)
    if fault == 'barrier':
        class BrokenBarrier:
            def __init__(self, parties): pass
            def wait(self, timeout=None): raise target.threading.BrokenBarrierError('OWN barrier failure')
            def abort(self): pass
        monkeypatch.setattr(target.threading, 'Barrier', BrokenBarrier)
    try:
        with pytest.raises((OSError, target.threading.BrokenBarrierError)):
            target.test_f07_two_real_cli_processes_and_restart(owned, 'result', False)
        assert len(children) == (1 if fault == 'second_popen' else 2)
        assert all(child.poll() is not None and child.stdout.closed and child.stderr.closed for child in children)
    finally: external_cleanup(children)


def test_minor_b_t01_holder_bad_setup_and_communication_timeout_closes(owned, monkeypatch):
    children = []; original_popen = subprocess.Popen
    def spawn(argv, **kwargs):
        if str(argv[5]).endswith('lock_holder.py'):
            # Real fixture process prints a wrong setup line and then ignores stdin.
            script = owned.root/'bad_holder.py'
            script.write_text("import threading\nprint('wrong',flush=True)\nthreading.Event().wait()\n", encoding='utf8')
            child = original_popen([sys.executable, '-I', '-X', 'utf8', '-B', str(script)], **kwargs)
            first_communication_times_out(child, monkeypatch); children.append(child); return child
        return original_popen(argv, **kwargs)
    monkeypatch.setattr(subprocess, 'Popen', spawn)
    try:
        with pytest.raises((AssertionError, subprocess.TimeoutExpired)):
            target.test_f23_real_cross_process_lock_busy_and_recovery(owned, 'result')
        assert len(children) == 1
        assert children[0].poll() is not None and children[0].stdout.closed and children[0].stderr.closed
    finally: external_cleanup(children)


def test_minor_a_t02_done_before_reader_exit_does_not_kill_valid_holder(owned, monkeypatch):
    """Force the exact normal interleaving: set completed, but wait for join to exit."""
    child = hanging_child(owned, line='locked')
    original_event = target.threading.Event; original_thread = target.threading.Thread
    release_reader = original_event(); done_seen = original_event(); reader_pending = [False]
    class DoneBeforeExit(original_event):
        def set(self):
            done_seen.set(); super().set()
            assert release_reader.wait(timeout=15)
    class JoinReleasesReader(original_thread):
        def __init__(self, *args, **kwargs):
            self.readiness_probe = getattr(kwargs.get('target'), '__name__', None) == 'read'
            super().__init__(*args, **kwargs)
        def join(self, timeout=None):
            if self.readiness_probe:
                reader_pending[0] = self.is_alive() and done_seen.is_set()
                release_reader.set()
            return super().join(timeout)
    # Thread.__init__ also needs an ordinary startup Event: patch only the helper's
    # first Event allocation, then immediately restore normal Event construction.
    def allocate_done():
        monkeypatch.setattr(target.threading, 'Event', original_event)
        return DoneBeforeExit()
    monkeypatch.setattr(target.threading, 'Event', allocate_done)
    monkeypatch.setattr(target.threading, 'Thread', JoinReleasesReader)
    try:
        assert target.readiness_line(child).rstrip(b'\r\n') == b'locked'
        assert reader_pending[0] is True and done_seen.is_set() and release_reader.is_set()
        assert child.poll() is None and not child.stdout.closed and not child.stderr.closed
    finally:
        release_reader.set(); external_cleanup([child])
