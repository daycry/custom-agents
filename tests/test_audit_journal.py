import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import threading

import pytest

ROOT = Path(__file__).resolve().parents[1]
SHARED = ROOT / 'agent-kits/shared'


def load(name):
    spec = importlib.util.spec_from_file_location('audit_' + name.replace('-', '_'), SHARED / (name + '.py'))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def redirect(source, target):
    if os.name == 'nt':
        import _winapi
        _winapi.CreateJunction(str(target), str(source))
    else:
        source.symlink_to(target, target_is_directory=True)


def project(tmp_path):
    root = tmp_path / 'project'; (root / 'docs/roadmap').mkdir(parents=True)
    return root


def test_r23_capability_probe_does_not_write_backend_bytecode_or_leak_global_flag(tmp_path):
    code = """
import importlib.util,json,sys
s=importlib.util.spec_from_file_location('probe',sys.argv[1]);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
sys.dont_write_bytecode=False
assert m._graphiti_modo({'mode':'shadow'})=='shadow'
print(json.dumps({'flag':sys.dont_write_bytecode}))
"""
    cache = tmp_path / 'cache'
    result = subprocess.run([sys.executable, '-I', '-S', '-X', 'pycache_prefix=' + str(cache), '-c', code, str(SHARED / 'capabilities.py')],
                            capture_output=True, text=True, encoding='utf8', timeout=30)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['flag'] is False
    assert not list(cache.rglob('graphiti*.pyc'))


def test_r24_default_queue_cannot_follow_a_junction(tmp_path):
    mod = load('journal-capture'); root = project(tmp_path)
    (root / '.claude').mkdir(); outside = tmp_path / 'outside'; outside.mkdir()
    redirect(root / '.claude/journal', outside)
    result = mod.capture_end(str(root), {'session_id': 'audit', 'reason': 'other'})
    assert result is None
    assert list(outside.iterdir()) == []


def test_recovered_claiming_counter_is_a_recognized_queue_control_file(tmp_path):
    mod = load('journal-capture'); root = project(tmp_path)
    folder = root / '.claude/journal'; folder.mkdir(parents=True)
    (folder / '.claiming-recuperados').write_text('1', encoding='utf8')
    assert mod.capture_end(str(root), {'session_id': 'after-recovery', 'reason': 'other'}) is not None


def test_r24_capture_does_not_append_to_hardlinked_gitignore(tmp_path):
    mod = load('journal'); root = project(tmp_path); (root / '.claude').mkdir()
    outside = tmp_path / 'canary'; outside.write_bytes(b'Unrelated ignore data.\n')
    os.link(outside, root / '.claude/.gitignore')
    try:
        mod.capture(str(root), {'session_id': 'audit', 'prompt': 'Synthetic prompt.'})
    except (OSError, ValueError):
        pass
    assert outside.read_bytes() == b'Unrelated ignore data.\n'
    assert not list((root / '.claude').glob('session-prompts-*'))


def entry():
    return dict(fecha='2026-11-05', session_id='audit-session', iniciativa='sesion', resumen='Synthetic audit', reason='other',
                avisos=[], decisiones=[], pendientes=[], ficheros_tocados=[], tareas_cambiadas=[], marcadores_cerrados=[])


def test_r24_materialization_cannot_follow_journal_parent_junction(tmp_path):
    mod = load('journal'); root = project(tmp_path); (root / 'docs/knowledge').mkdir()
    outside = tmp_path / 'outside'; outside.mkdir(); (outside / 'README.md').write_bytes(b'External canary.\n')
    redirect(root / 'docs/knowledge/journal', outside)
    with pytest.raises((OSError, ValueError)):
        mod.write(str(root), entry())
    assert {p.name: p.read_bytes() for p in outside.iterdir()} == {'README.md': b'External canary.\n'}


def test_r24_unowned_readme_is_preserved_before_materialization(tmp_path):
    mod = load('journal'); root = project(tmp_path); folder = root / 'docs/knowledge/journal'; folder.mkdir(parents=True)
    (folder / 'README.md').write_bytes(b'Manual project notes.\n')
    with pytest.raises((OSError, ValueError)):
        mod.write(str(root), entry())
    assert {p.name: p.read_bytes() for p in folder.iterdir()} == {'README.md': b'Manual project notes.\n'}


def test_r24_entry_reader_is_bounded_and_rejects_hardlinks(tmp_path):
    mod = load('journal')
    valid = tmp_path / 'valid.md'; valid.write_text('---\nfecha: 2026-11-05\nsession_id: audit\n---\nBody.', encoding='utf8')
    alias = tmp_path / 'alias.md'; os.link(valid, alias)
    assert mod.parse_entry(str(alias)) is None
    large = tmp_path / 'large.md'; large.write_bytes(b'---\nfecha: 2026-11-05\nsession_id: audit\n---\n' + b'X' * (3 * 1024 * 1024))
    assert mod.parse_entry(str(large)) is None


def test_r24_prompt_reader_does_not_follow_a_shared_log(tmp_path):
    mod = load('journal'); root = project(tmp_path); (root / '.claude').mkdir()
    outside = tmp_path / 'private-log'; outside.write_text('{"prompt":"Unrelated private prompt."}\n', encoding='utf8')
    os.link(outside, mod.log_path(str(root), 'audit'))
    assert mod.capturas(str(root), 'audit') == []


def test_journal_capture_cli_materializes_a_durable_envelope(tmp_path):
    root = project(tmp_path)
    result = subprocess.run([sys.executable, '-B', str(SHARED / 'journal-capture.py'), '--root', str(root)],
        input=json.dumps({'session_id': 'audit-cli', 'reason': 'other'}),
        capture_output=True, text=True, encoding='utf8', timeout=30)
    assert result.returncode == 0, result.stderr
    envelopes = list((root / '.claude/journal/outbox').glob('*.json'))
    assert len(envelopes) == 1, 'The informational CLI exited successfully without capturing anything.'
    assert json.loads(envelopes[0].read_bytes())['session_id'] == 'audit-cli'


def test_concurrent_first_prompts_both_survive_ignore_initialization(tmp_path, monkeypatch):
    mod = load('journal'); root = project(tmp_path)
    barrier = threading.Barrier(2)
    real = mod.JIO.IO.write
    entered = []; mutex = threading.Lock()
    def competing(path, *args, **kwargs):
        if Path(path).name == '.gitignore':
            with mutex:
                entered.append(str(path)); wait = len(entered) <= 2
            if wait: barrier.wait(timeout=10)
        return real(path, *args, **kwargs)
    monkeypatch.setattr(mod.JIO.IO, 'write', competing)
    results = []; failures = []
    def capture(sid):
        try: results.append(mod.capture(str(root), {'session_id': sid, 'prompt': 'Synthetic ' + sid}))
        except Exception as error: failures.append(type(error).__name__)
    threads = [threading.Thread(target=capture, args=(sid,)) for sid in ('one', 'two')]
    for thread in threads: thread.start()
    for thread in threads: thread.join(timeout=15)
    assert not any(thread.is_alive() for thread in threads)
    assert failures == [] and len(results) == 2, 'A first prompt was lost during concurrent ignore initialization.'
    assert mod.capturas(str(root), 'one') == ['Synthetic one']
    assert mod.capturas(str(root), 'two') == ['Synthetic two']


def test_capture_does_not_walk_completed_queue_history(tmp_path, monkeypatch):
    mod = load('journal-capture'); root = project(tmp_path)
    done = root / '.claude/journal/done'; done.mkdir(parents=True)
    (done / 'historic.json').write_text('{}', encoding='utf8')
    real = mod.JIO.os.scandir
    def scan(path):
        assert Path(path) != done, 'Every capture walks completed queue history.'
        return real(path)
    monkeypatch.setattr(mod.JIO.os, 'scandir', scan)
    assert mod.capture_end(str(root), {'session_id': 'new-session', 'reason': 'other'}) is not None


def test_queue_claim_does_not_touch_a_shared_envelope(tmp_path):
    mod = load('journal-capture'); root = project(tmp_path)
    queued = Path(mod.capture_end(str(root), {'session_id': 'claim', 'reason': 'other'}))
    outside = tmp_path / 'unrelated-envelope.json'
    queued.rename(outside); os.link(outside, queued)
    os.utime(outside, (1000000000, 1000000000))
    before = outside.stat().st_mtime_ns
    item = mod._outbox_mod().reclamar(str(root / '.claude/journal'))
    assert item is None
    assert outside.stat().st_mtime_ns == before
    assert queued.exists()


def test_guarded_outbox_file_sync_failure_publishes_and_reports_degradation(tmp_path, monkeypatch):
    mod = load('journal-capture'); root = project(tmp_path)
    assert mod.capture_end(str(root), {'session_id': 'warmup', 'reason': 'other'}) is not None
    def unavailable(_fd):
        raise OSError('synthetic unsupported file sync')
    monkeypatch.setattr(os, 'fsync', unavailable)
    path = mod.capture_end(str(root), {'session_id': 'degraded-sync', 'reason': 'other'})
    assert path is not None and Path(path).is_file(), 'Capture acknowledged an envelope that was never published.'
    queue = root / '.claude/journal'
    assert mod._outbox_mod().estado(str(queue))['durabilidad'] == 'degradada'


def test_outbox_console_setup_precedes_runtime_initialization():
    spec = importlib.util.spec_from_file_location('audit_console_contract', ROOT / 'tests/test_console_encoding.py')
    contract = importlib.util.module_from_spec(spec); spec.loader.exec_module(contract)
    assert contract.snippet_al_arrancar((SHARED / 'outbox.py').read_text(encoding='utf8'))


def test_non_outbox_metadata_still_requires_file_sync(tmp_path, monkeypatch):
    mod = load('journal-io')
    def unavailable(_fd):
        raise OSError('synthetic unsupported file sync')
    monkeypatch.setattr(os, 'fsync', unavailable)
    destination = tmp_path / 'strict-metadata'
    with pytest.raises(ValueError, match='durability_degraded'):
        mod.write(destination, b'synthetic metadata')
    assert not destination.exists()


def test_first_prompts_survive_the_atomic_link_publication_window(tmp_path, monkeypatch):
    mod = load('journal'); root = project(tmp_path)
    published, release = threading.Event(), threading.Event()
    link, file = os.link, mod.JIO.IO.file
    errors = []
    def paused_link(source, target, *args, **kwargs):
        result = link(source, target, *args, **kwargs)
        if Path(target).name == '.gitignore' and not published.is_set():
            published.set(); assert release.wait(5)
        return result
    def observe(path):
        try:
            return file(path)
        except ValueError:
            if Path(path).name == '.gitignore' and published.is_set(): release.set()
            raise
    monkeypatch.setattr(os, 'link', paused_link)
    monkeypatch.setattr(mod.JIO.IO, 'file', observe)
    def first():
        try: mod.capture(str(root), {'session_id': 'first-link', 'prompt': 'Synthetic first'})
        except Exception as error: errors.append(type(error).__name__)
    thread = threading.Thread(target=first); thread.start()
    try:
        assert published.wait(5)
        mod.capture(str(root), {'session_id': 'second-link', 'prompt': 'Synthetic second'})
    finally:
        release.set(); thread.join(timeout=10)
    assert not thread.is_alive() and not errors
    assert mod.capturas(str(root), 'first-link') == ['Synthetic first']
    assert mod.capturas(str(root), 'second-link') == ['Synthetic second']


@pytest.mark.skipif(os.name != 'nt', reason='native Windows exclusive file sharing')
@pytest.mark.parametrize('lock_point', ['entry-read', 'index-publication'])
def test_temporary_entry_lock_keeps_envelope_retryable(tmp_path, monkeypatch, lock_point):
    import ctypes
    from ctypes import wintypes
    import time
    mod = load('journal'); root = project(tmp_path)
    assert mod.capture_end(str(root), {'session_id': 'existing', 'reason': 'other'})
    assert mod.replay(str(root), ia='no')['materializados'] == 1
    entry_path = mod.entradas(str(root))[0]['_path']
    assert mod.capture_end(str(root), {'session_id': 'pending', 'reason': 'other'})
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
        wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]; kernel.CloseHandle.restype = wintypes.BOOL
    invalid = (None, ctypes.c_void_p(-1).value)
    handles = []
    def lock(path):
        handle = kernel.CreateFileW(str(path), 0x80000000, 0, None, 3, 0x80, None)
        deadline = time.monotonic() + 2
        while handle in invalid and ctypes.get_last_error() in (32, 33) and time.monotonic() < deadline:
            time.sleep(.01); handle = kernel.CreateFileW(str(path), 0x80000000, 0, None, 3, 0x80, None)
        assert handle not in invalid, ctypes.get_last_error()
        handles.append(handle)
    if lock_point == 'entry-read':
        lock(entry_path)
    else:
        write = mod.JIO.write
        def occupied_at_publication(path, *args, **kwargs):
            if Path(path).name == 'README.md' and not handles:
                lock(path)  # Real sharing conflict AFTER _check_index succeeds.
            return write(path, *args, **kwargs)
        monkeypatch.setattr(mod.JIO, 'write', occupied_at_publication)
    try:
        blocked = mod.replay(str(root), ia='no')
        assert blocked['reintentados'] == 1 and blocked['dead_letter'] == 0, blocked
    finally:
        for handle in handles: assert kernel.CloseHandle(handle)
    assert len(handles) == 1
    assert mod.replay(str(root), ia='no')['materializados'] == 0, 'Backoff must remain effective.'
    assert mod.replay(str(root), ia='no', reintentar_ahora=True)['materializados'] == 1
    assert {e['session_id'] for e in mod.entradas(str(root))} == {'existing', 'pending'}


@pytest.mark.parametrize('operation', ['read', 'write', 'update'])
def test_journal_read_distinguishes_io_unavailability_from_invalid_state(tmp_path, monkeypatch, operation):
    mod = load('journal-io'); path = tmp_path / 'regular'; path.write_bytes(b'synthetic')
    monkeypatch.setattr(mod.IO.reader, 'read_bytes', lambda *args, **kwargs: {'status': 'unreadable'})
    with pytest.raises(OSError):
        if operation == 'read': mod.read(path)
        elif operation == 'write': mod.write(path, b'replacement')
        else: mod.update(path, lambda raw: raw + b'replacement')
    assert path.read_bytes() == b'synthetic'
    strict = type(mod.IO)(mod.IO.reader, mod.IO.need, mod.IO.guard, maximum=mod.IO.maximum)
    with pytest.raises(ValueError, match='invalid_state'):
        strict.read(path, 1024)  # Other consumers retain the original strict contract.
