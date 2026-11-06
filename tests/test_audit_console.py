"""Native recovery, authorization limits and canonical plan routing regressions."""
import hashlib
import io
import sys
import time
import threading
from types import SimpleNamespace

from test_console_sessions import manager, ready, load
from test_console_opencode import driver
from test_ledger_write import BASE
import pytest


def test_r13_failed_turn_allows_a_new_explicit_message(manager):
    m, made = manager
    session = ready(m)
    made[0].emit({'type': 'status', 'status': 'failed', 'error': 'native_turn_failed'})
    m.send('one', session['id'], 'Continue with a different approach.', 'b' * 32)
    deadline = time.monotonic() + 2
    while not made[0].sent and time.monotonic() < deadline:
        time.sleep(.01)
    assert made[0].sent == ['Continue with a different approach.']


def test_r13_dead_driver_is_closed_and_detached_before_resuming(manager):
    m, made = manager
    session = ready(m)
    made[0].emit({'type': 'status', 'status': 'disconnected', 'error': 'native_closed'})
    deadline = time.monotonic() + 2
    while not m.get('one', session['id'])['can_resume'] and time.monotonic() < deadline:
        time.sleep(.01)
    assert made[0].closed
    assert m.get('one', session['id'])['can_resume']
    assert m._connection_count() == 0
    made[0].emit({'type': 'status', 'status': 'running'})
    assert m.get('one', session['id'])['status'] == 'disconnected'


def test_r13_verified_idle_poll_recovers_after_transient_monitor_failure(tmp_path):
    d, client, events = driver(tmp_path)
    try:
        d.start()
        d.refresh()
        assert events[-1]['status'] == 'idle'
        assert not d.inflight
    finally:
        d.close()


def test_idle_poll_cannot_release_a_message_waiting_for_driver_admission(manager, monkeypatch):
    m, made = manager; session = ready(m)
    entered = threading.Event(); release = threading.Event()
    def blocked(text):
        entered.set(); release.wait(timeout=10)
    monkeypatch.setattr(made[0], 'send', blocked)
    try:
        m.send('one', session['id'], 'First explicit message.', 'c' * 32)
        assert entered.wait(timeout=5)
        made[0].emit({'type': 'status', 'status': 'idle', 'source': 'poll'})
        with pytest.raises(ValueError, match='session_busy'):
            m.send('one', session['id'], 'Second explicit message.', 'd' * 32)
    finally:
        release.set()


def test_opencode_rejects_a_second_turn_until_the_first_finishes(tmp_path):
    d, client, events = driver(tmp_path)
    try:
        d.start(); d.send('First message.')
        with pytest.raises(ValueError, match='native_busy'):
            d.send('Second message.')
        assert len([row for row in client.calls if row[1].endswith('/prompt')]) == 1
    finally:
        d.close()


def test_p1_oversized_approval_is_not_scrubbed_under_the_session_lock(manager, monkeypatch):
    m, made = manager
    session = ready(m)
    mod = sys.modules.get(type(m).__module__)
    common = m.emit.__globals__['C']
    real = common.scrub
    sizes = []
    def scrub(text, *args, **kwargs):
        sizes.append(len(text))
        assert len(text) <= 2001, 'An unbounded approval entered the scrubber.'
        return real(text, *args, **kwargs)
    monkeypatch.setattr(common, 'scrub', scrub)
    made[0].emit({'type': 'approval', 'id': 'large', 'title': 'Inspect request',
                  'preview': 'X' * 500000, 'choices': ['allow', 'deny']})
    pending = m.get('one', session['id'])['pending'][0]
    assert pending['truncated'] and pending['choices'] == ['deny']


def test_p2_pipe_reader_uses_bounded_buffer_fills(tmp_path):
    mod = load('console_transport.py')
    payload = b'{"text":"' + b'X' * 65536 + b'"}\n'
    class Raw(io.RawIOBase):
        def __init__(self):
            super().__init__(); self.buffer = io.BytesIO(payload); self.calls = 0
        def readable(self): return True
        def readinto(self, target):
            self.calls += 1
            return self.buffer.readinto(target)
    raw = Raw(); rows = []
    process = mod.LineProcess([sys.executable], tmp_path, rows.append, lambda _: None)
    process.process = SimpleNamespace(stdout=raw)
    process._fail = lambda _: setattr(process, 'closing', True)
    process._read()
    assert len(rows) == 1 and len(rows[0]['text']) == 65536
    assert raw.calls < 32, 'The pipe performs approximately one raw read per byte.'


def test_r14_long_plan_name_routes_to_the_canonical_directory(tmp_path):
    mod = load('console_service.py'); registry = load('console_workspaces.py')
    folder = '2026-11-05-' + 'long-plan-' * 12 + 'audit'
    path = tmp_path / 'docs/roadmap' / folder
    path.mkdir(parents=True)
    (path / 'tasks.md').write_text(BASE, encoding='utf8')
    (path / 'improvement-plan.md').write_text('# Plan\n\nCanonical plan.', encoding='utf8')
    ident = hashlib.sha256(folder.encode()).hexdigest()[:16]
    service = mod.Service({'one': registry.Workspace('one', 'One', tmp_path, ())}, sessions=SimpleNamespace(close=lambda: None))
    try:
        assert service.document('one', ident, 'plan')['source'] == f'docs/roadmap/{folder}/improvement-plan.md'
        result = service.prepare('one', ident, 'continue', None)
        assert f'docs/roadmap/{folder}/tasks.md' in result['sources']
    finally:
        service.close()
